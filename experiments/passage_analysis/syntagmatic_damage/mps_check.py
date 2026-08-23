"""Does mps give the same deepseek surprisal as CPU? Answer before trusting 41k numbers to it.

WHY THIS EXISTS

`score.py:_ref` picks `cuda` where present and CPU otherwise; it never
considered mps. The module's device rule is explicit that it binds the DRIFT
AXIS embedder and not this instrument:

    "device is not a free parameter for the drift axis and this module does
     not offer one. The surprisal model may use cuda where present, since it
     is a different instrument with a different history."

So accelerating surprisal is permitted. What is not permitted is assuming a
backend agrees. mps was caught corrupting short-sequence bge embeddings on
2026-08-21, and the failure mode there was silent plausible numbers, which is
the only failure mode that matters at this scale.

WHY IT DOES NOT CALL score.surprisal

`score.surprisal` is content-addressed on `sha(text)`. A second pass over the
same passages hits the cache and returns the FIRST pass's numbers, so a naive
CPU-then-mps comparison agrees perfectly no matter what mps does. That is a
check that cannot fire. This file replicates the inner loop instead and never
touches the store.

Both passes score the same texts with the same tokenisation; only the device
moves. Compared on the per-token bits vector, not on the passage mean, because
a mean can hide compensating per-token error.

    python -u mps_check.py --n 150
"""

import argparse, base64, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def vectors(texts, dev, tk, mdl):
    """Per-token surprisal in bits for each text, computed on `dev`."""
    import numpy as np, torch
    mdl = mdl.to(dev)
    out = []
    for t in texts:
        enc = tk(t, return_offsets_mapping=True)
        tid = torch.tensor([enc["input_ids"]])
        if tid.shape[1] < 2:
            out.append(np.zeros(0, np.float32))
            continue
        with torch.no_grad():
            lg = mdl(tid.to(dev)).logits[0]
        lp = torch.log_softmax(lg.float(), -1)
        tgt = tid[0, 1:].to(dev)
        sur = (-lp[:-1].gather(1, tgt[:, None]).squeeze(1)).cpu().numpy() / np.log(2)
        out.append(sur.astype(np.float32))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    a = ap.parse_args(argv)

    import numpy as np, torch
    from reference import _ch, MIN_TOKENS
    from malignment import score

    if not torch.backends.mps.is_available():
        print("mps NOT available on this machine -- nothing to check")
        return 1

    #: span the length range rather than taking the first N, so a defect that
    #: only bites short or only bites long cannot hide behind an average.
    ch = _ch()
    rows = ch.query(
        "SELECT base64Encode(text) AS t, n_tokens FROM malign_logits.gen_sequences "
        "WHERE corpus='passage' AND forced_word != '' AND n_tokens >= %d "
        "ORDER BY cityHash64(text) LIMIT %d" % (MIN_TOKENS, a.n))
    texts = [base64.b64decode(r["t"]).decode("utf-8", "replace") for r in rows]
    print("%d passages, %d-%d words" % (
        len(texts), min(len(t.split()) for t in texts),
        max(len(t.split()) for t in texts)), flush=True)

    tk, mdl, _ = score._ref()

    t0 = time.time()
    cpu = vectors(texts, "cpu", tk, mdl)
    t_cpu = time.time() - t0
    print("cpu  %6.1f s  (%.2f s/passage)" % (t_cpu, t_cpu / len(texts)), flush=True)

    t0 = time.time()
    mps = vectors(texts, "mps", tk, mdl)
    t_mps = time.time() - t0
    print("mps  %6.1f s  (%.2f s/passage)  -> %.1fx" % (
        t_mps, t_mps / len(texts), t_cpu / max(t_mps, 1e-9)), flush=True)

    worst_tok, worst_mean, means_c, means_m = 0.0, 0.0, [], []
    for c, m in zip(cpu, mps):
        if c.size == 0:
            continue
        worst_tok = max(worst_tok, float(np.abs(c - m).max()))
        means_c.append(float(c.mean()))
        means_m.append(float(m.mean()))
        worst_mean = max(worst_mean, abs(means_c[-1] - means_m[-1]))
    d = np.array(means_m) - np.array(means_c)

    print()
    print("AGREEMENT, bits")
    print("  worst single-token difference : %.6f" % worst_tok)
    print("  worst passage-mean difference : %.6f" % worst_mean)
    print("  mean signed difference        : %+.6f  (bias, not noise, if it is)" % d.mean())
    print("  passage means, cpu vs mps     : %.5f vs %.5f" % (np.mean(means_c), np.mean(means_m)))
    print("  correlation of passage means  : %.8f" % np.corrcoef(means_c, means_m)[0, 1])

    #: the tolerance is a JUDGEMENT and is stated so a reader can disagree with
    #: it. fp32 on two backends will not be bit-identical; what would matter is
    #: error comparable to the effect being measured. The [5,10) coefficient is
    #: -0.54 nats per unit delta on deltas of order 0.03-0.09, i.e. effects of
    #: order 0.02-0.05 nats = 0.03-0.07 bits per token.
    ok = worst_mean < 0.001 and abs(d.mean()) < 0.0005
    print()
    print("VERDICT: %s" % ("mps agrees with CPU at the passage grain; the effect "
                           "under measurement is 0.03-0.07 bits/token and the "
                           "disagreement is far below it" if ok else
                           "DISAGREEMENT IS NOT NEGLIGIBLE -- do not run on mps"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
