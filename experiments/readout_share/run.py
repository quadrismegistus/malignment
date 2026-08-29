"""Does alignment change the representation or the readout? The 2x2, at every layer.

    .venv/bin/python -u run.py                    every pair with both arms archived
    .venv/bin/python -u run.py --pairs meta-llama/Llama-3.1-8B
    .venv/bin/python -u run.py --top 12 --floor 0.20

Four combinations of a state and a readout, at every layer of every pair:

    h_base    x readout_base      the base model
    h_base    x readout_aligned   base state, aligned readout
    h_aligned x readout_base      aligned state, base readout
    h_aligned x readout_aligned   the aligned model

`readout` is the final norm AND the unembedding. They are also swapped
separately (`T_bw`, `T_bn`) so the unembedding's contribution can be told apart
from the normalisation's.

WRITES
    results/by_pair.csv         one row per pair: shares, dW, onset
    results/by_pair_layer.csv   one row per (pair, prompt, layer): all four
                                combinations plus coverage on both arms
    population.json             the pairs, prompts, words and sidecar bytes used
"""

import argparse
import collections
import csv
import hashlib
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

from malignment import lens, roster  # noqa: E402

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
CHARGE = os.path.join(DATA, "dose_response", "charge_en50_flash.jsonl")
RESULTS = os.path.join(HERE, "results")

#: the depths reported in the README's tables. Dense at the top because that is
#: the only region where the lens has mass to read -- see FLOOR.
FRACTIONS = (0.0, 0.25, 0.5, 0.75, 0.875, 0.9375, 1.0)

#: **A LAYER BELOW THIS COVERAGE IS NOT ELIGIBLE TO BE AN ONSET.** The target
#: words hold ~0 of the distribution below three-quarters depth on every model
#: measured, so "the gap reached half its final value" is satisfied there by the
#: ratio of two vanishing numbers. Without the floor, Llama-3.1-8B onsets at 0.20
#: of the stack; with it, at 0.92, which is F05's SFT figure.
FLOOR = 0.20

#: below this the pair's final-layer coverage is too low to read at all.
MIN_COVERAGE = 0.30

#: **A SHARE OF A NEAR-ZERO EFFECT IS NOT A QUANTITY.** glm-4-9b-hf's full effect
#: is -0.033 and its readout swap is -0.355, which divides out to a readout share
#: of 1086%; granite's +0.073 gives 355%. Both are arithmetically correct and
#: neither is a fact about the model. A pair is eligible for a SHARE only if its
#: full effect is displacement of at least this size in the expected direction --
#: the components are still reported for every pair, as differences.
MIN_FULL = 0.15


def ratings(prompts):
    """{prompt: {word: mean scene rating}} averaged over every lineage that rated it.

    Averaging over lineages makes the weight a property of the word-in-frame
    rather than of one rater call.
    """
    want = set(prompts)
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    for line in open(CHARGE):
        r = json.loads(line)
        if r["prompt"] in want:
            for w in r["words"]:
                agg[r["prompt"]][w["word"]].append(w["scene"])
    return {p: {w: sum(v) / len(v) for w, v in d.items()} for p, d in agg.items()}


def onset(gap, cov, floor):
    """F05's shape: the first ELIGIBLE layer with the final sign and >=50% of the
    final gap, as a fraction of depth. None when there is no final gap to halve."""
    fin = gap[-1]
    if fin != fin or abs(fin) < 0.05:
        return None
    n = len(gap)
    for i in range(n):
        if cov[i] < floor or gap[i] != gap[i]:
            continue
        if gap[i] * fin > 0 and abs(gap[i]) >= 0.5 * abs(fin):
            return i / (n - 1)
    return 1.0


def pair(base, aligned, top, floor, torch, AutoTokenizer):
    """One pair's cells, or None with a reason."""
    HB, pl = lens.hidden(base)
    HA, pla = lens.hidden(aligned)
    if pl != pla:
        return None, "prompt lists differ"
    WB, nwB, nbB, usedB, cB = lens.head(base)
    WA, nwA, nbA, usedA, cA = lens.head(aligned)
    if WB.shape != WA.shape:
        if WB.shape[1] != WA.shape[1]:
            return None, "d_model differs %d vs %d" % (WB.shape[1], WA.shape[1])
        #: CroissantLLM's aligned arm appends two tokens to the END of the
        #: vocabulary. Rows 0..31999 are the same tokenizer, so truncating to the
        #: common prefix swaps over identical ids -- but ONLY because the added
        #: ids are the trailing ones, and `single_token(vocab=)` then drops any
        #: target at or above the cut rather than silently misindexing it.
        n = min(WB.shape[0], WA.shape[0])
        WB, WA = WB[:n], WA[:n]
    vocab = WB.shape[0]
    gm = lens.is_gemma(base)
    tok = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
    R = ratings(pl)
    dose = {p: (sum(d.values()) / len(d) if d else 0.0) for p, d in R.items()}
    #: highest-dose prompts first. A trajectory on a frame with nothing charged
    #: is a flat line and says nothing about where alignment acts.
    pick = sorted(dose, key=lambda p: -dose[p])[:top]

    #: the two arms' readouts, as (W, norm_w, norm_b, cfg) so a swap is one
    #: argument tuple rather than four positional arguments in the right order.
    RB = (WB, nwB, nbB, cB)
    RA = (WA, nwA, nbA, cA)
    #: bw = base norm, ALIGNED unembedding. bn = ALIGNED norm, base unembedding.
    BW = (WA, nwB, nbB, cA)
    BN = (WB, nwA, nbA, cB)

    cells = []
    for p in pick:
        i = pl.index(p)
        ids, keep = lens.single_token(R[p], tok, vocab=vocab)
        if len(keep) < 8:
            continue
        wt = torch.tensor([R[p][w] for w in keep])
        hb = torch.from_numpy(HB[i])
        ha = torch.from_numpy(HA[i])

        def T(h, rd):
            W, nw, nb, cfg = rd
            P = lens.layer_probs(h, W, nw, nb, cfg, ids, gemma=gm, torch=torch)
            s = P.sum(-1)
            #: **NORMALISING BY THE COVERED MASS IS WHAT MAKES THIS COMPARABLE.**
            #: An unnormalised sum falls whenever the distribution concentrates
            #: anywhere else, so it would read every sharpening as displacement.
            v = (P * wt).sum(-1) / s
            return [float(x) for x in v], [float(x) for x in s]

        t_bb, cov_b = T(hb, RB)
        t_ba, _ = T(hb, RA)
        t_ab, _ = T(ha, RB)
        t_aa, cov_a = T(ha, RA)
        t_bw, _ = T(hb, BW)
        t_bn, _ = T(hb, BN)
        cells.append(dict(prompt=p, dose=dose[p], n_words=len(keep),
                          n_layers=len(t_bb) - 1, words=keep,
                          T_bb=t_bb, T_ba=t_ba, T_ab=t_ab, T_aa=t_aa,
                          T_bw=t_bw, T_bn=t_bn, cov_b=cov_b, cov_a=cov_a))
    if not cells:
        return None, "no cell reached 8 single-token rated words"
    dW = float((WA.float() - WB.float()).abs().mean()
               / WB.float().abs().mean())
    return dict(base=base, aligned=aligned, unembed=usedB, vocab=vocab,
                d_model=int(WB.shape[1]), dW=dW, cells=cells,
                cap=cB.get("final_logit_softcapping"),
                scale=cB.get("logits_scaling")), None


def summarise(r, floor):
    """One pair's row: the shares at the output, and the onset of the full effect."""
    last = lambda k: st.mean([c[k][-1] for c in r["cells"]])  # noqa: E731
    full = last("T_aa") - last("T_bb")
    ons = [o for c in r["cells"]
           if (o := onset([c["T_aa"][i] - c["T_bb"][i] for i in range(len(c["T_bb"]))],
                          c["cov_b"], floor)) is not None]
    cov = st.median([c["cov_b"][-1] for c in r["cells"]])
    #: a share is reported only where there is displacement to apportion AND the
    #: lens can read the output. Both gates are recorded, not just their product,
    #: so a reader can see which one excluded a pair.
    readable = cov > MIN_COVERAGE and full <= -MIN_FULL
    return dict(
        base=r["base"], aligned=r["aligned"], n_cells=len(r["cells"]),
        n_layers=r["cells"][0]["n_layers"], coverage=cov,
        dW=r["dW"], full=full,
        readout=last("T_ba") - last("T_bb"),
        state=last("T_ab") - last("T_bb"),
        unembed_only=last("T_bw") - last("T_bb"),
        norm_only=last("T_bn") - last("T_bb"),
        share_readable=int(readable),
        readout_share=(last("T_ba") - last("T_bb")) / full if readable else float("nan"),
        state_share=(last("T_ab") - last("T_bb")) / full if readable else float("nan"),
        onset=st.median(ons) if ons else float("nan"), n_onset=len(ons))


def main(argv=None):
    import torch
    from transformers import AutoTokenizer
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="*", help="base ids; default every archived pair")
    ap.add_argument("--top", type=int, default=6, help="highest-dose prompts per pair")
    ap.add_argument("--floor", type=float, default=FLOOR, help="onset coverage floor")
    a = ap.parse_args(argv)

    man = lens.manifest()
    eps, _ = roster.endpoints()
    todo = a.pairs or [b for b in sorted(eps) if b in man and eps[b] in man]
    print("pairs with both arms archived: %d" % len(todo))

    out, skipped = [], []
    for b in todo:
        try:
            r, why = pair(b, eps[b], a.top, a.floor, torch, AutoTokenizer)
        except Exception as e:
            r, why = None, "%s: %s" % (type(e).__name__, str(e)[:60])
        if r is None:
            skipped.append((b, why))
            print("  %-24s SKIPPED %s" % (b.split("/")[-1][:24], why), flush=True)
            continue
        s = summarise(r, a.floor)
        out.append((r, s))
        pct = lambda k: ("%3.0f%%" % (100 * s[k])) if s["share_readable"] else "  --"  # noqa: E731
        print("  %-24s cov %.2f | dW %.3f | full %+.3f | readout %+.3f (%s) | "
              "state %+.3f (%s) | onset %.2f"
              % (b.split("/")[-1][:24], s["coverage"], s["dW"], s["full"],
                 s["readout"], pct("readout_share"),
                 s["state"], pct("state_share"), s["onset"]), flush=True)

    os.makedirs(RESULTS, exist_ok=True)
    cols = list(out[0][1]) if out else []
    with open(os.path.join(RESULTS, "by_pair.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for _, s in out:
            w.writerow(s)
    with open(os.path.join(RESULTS, "by_pair_layer.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["base", "aligned", "prompt", "dose", "n_words", "layer",
                    "frac", "T_bb", "T_ba", "T_ab", "T_aa", "T_bw", "T_bn",
                    "cov_b", "cov_a"])
        for r, _ in out:
            for c in r["cells"]:
                n = c["n_layers"]
                for L in range(n + 1):
                    w.writerow([r["base"], r["aligned"], c["prompt"],
                                "%.4f" % c["dose"], c["n_words"], L,
                                "%.4f" % (L / n)]
                               + ["%.6f" % c[k][L] for k in
                                  ("T_bb", "T_ba", "T_ab", "T_aa", "T_bw",
                                   "T_bn", "cov_b", "cov_a")])

    #: the receipt. Sidecar bytes are hashed because the archive repo is
    #: read-only but not immutable, and a rerun that silently reads different
    #: states would otherwise be indistinguishable from one that did not.
    man_path = os.path.join(lens.ARCHIVE, "hidden_manifest.json")
    pop = dict(
        floor=a.floor, top=a.top, charge=os.path.basename(CHARGE),
        charge_sha=hashlib.sha256(open(CHARGE, "rb").read()).hexdigest()[:16],
        manifest_sha=hashlib.sha256(open(man_path, "rb").read()).hexdigest()[:16],
        archive=lens.ARCHIVE, skipped=[dict(base=b, why=w) for b, w in skipped],
        pairs=[dict(base=r["base"], aligned=r["aligned"], unembed=r["unembed"],
                    vocab=r["vocab"], d_model=r["d_model"], dW=r["dW"],
                    n_layers=r["cells"][0]["n_layers"], cap=r["cap"],
                    scale=r["scale"],
                    prompts=[dict(prompt=c["prompt"], dose=c["dose"],
                                  n_words=c["n_words"], words=c["words"])
                             for c in r["cells"]])
               for r, _ in out])
    json.dump(pop, open(os.path.join(HERE, "population.json"), "w"), indent=1)

    ok = [(r, s) for r, s in out if s["coverage"] > MIN_COVERAGE]
    if not ok:
        return
    sh = [(r, s) for r, s in out if s["share_readable"]]
    if sh:
        #: **TWO AGGREGATES, BOTH REPORTED, BECAUSE PICKING ONE IS A CHOICE.**
        #: The pooled share weights by effect size, so recurrentgemma's -1.32
        #: dominates; the median treats each pair as one observation, so
        #: Llama's outlying 88% cannot carry it. They answer different
        #: questions and here they agree, which is worth being able to see.
        print("\nACROSS %d PAIRS WITH DISPLACEMENT TO APPORTION "
              "(coverage > %.2f, full <= -%.2f)" % (len(sh), MIN_COVERAGE, MIN_FULL))
        tot = sum(s["full"] for _, s in sh)
        print("  summed full effect     %+.3f" % tot)
        for k, lab in (("readout", "readout swap"), ("state", "state swap"),
                       ("unembed_only", "unembedding only"),
                       ("norm_only", "final norm only")):
            v = sum(s[k] for _, s in sh)
            print("  %-22s %+.3f  pooled %3.0f%%   median per pair %3.0f%%"
                  % (lab, v, 100 * v / tot,
                     100 * st.median([s[k] / s["full"] for _, s in sh])))

    hdr = "  ".join("%6s" % ("%.2f" % f) for f in FRACTIONS)
    for k, lab in (("T_aa", "FULL EFFECT (each arm, own readout)"),
                   ("T_ba", "READOUT SWAP (base state, aligned readout)"),
                   ("T_ab", "STATE SWAP (aligned state, base readout)")):
        print("\n%s BY DEPTH" % lab)
        print("  %-22s %s" % ("pair", hdr))
        for r, _ in ok:
            n = r["cells"][0]["n_layers"]
            row = []
            for fr in FRACTIONS:
                i = min(n, int(round(fr * n)))
                v = [c[k][i] - c["T_bb"][i] for c in r["cells"]
                     if c[k][i] == c[k][i] and c["T_bb"][i] == c["T_bb"][i]]
                row.append(st.mean(v) if v else float("nan"))
            print("  %-22s %s" % (r["base"].split("/")[-1][:22],
                                  "  ".join("%+6.2f" % v for v in row)))

    print("\nTARGET-WORD COVERAGE BY DEPTH (base arm)")
    print("  %-22s %s" % ("pair", hdr))
    for r, _ in ok:
        n = r["cells"][0]["n_layers"]
        row = [st.mean([c["cov_b"][min(n, int(round(fr * n)))] for c in r["cells"]])
               for fr in FRACTIONS]
        print("  %-22s %s" % (r["base"].split("/")[-1][:22],
                              "  ".join("%6.3f" % v for v in row)))

    print("\nONSET OF THE FULL EFFECT, BY COVERAGE FLOOR")
    print("  %-22s %s" % ("pair", "  ".join("%6s" % ("%.2f" % f)
                                            for f in (0.0, 0.05, 0.10, 0.20))))
    for r, _ in ok:
        row = []
        for fl in (0.0, 0.05, 0.10, 0.20):
            v = [o for c in r["cells"]
                 if (o := onset([c["T_aa"][i] - c["T_bb"][i]
                                 for i in range(len(c["T_bb"]))],
                                c["cov_b"], fl)) is not None]
            row.append("%.2f" % st.median(v) if v else "  -")
        print("  %-22s %s" % (r["base"].split("/")[-1][:22],
                              "  ".join("%6s" % x for x in row)))
    print("\n  F05 for comparison: SFT 0.92, DPO 0.96, RLVR 0.98")
    print("\n-> results/by_pair.csv, results/by_pair_layer.csv, population.json")


if __name__ == "__main__":
    main()
