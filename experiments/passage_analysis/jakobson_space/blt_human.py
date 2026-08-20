"""BLT byte-level surprisal for the human anchor, on the model passages' scale.

    python .../blt_human.py --input $MALIGNMENT_DATA/jakobson_space/human_anchor.jsonl \
        --out $MALIGNMENT_DATA/jakobson_space/blt_human

Puts the 3,000 human passages on the SAME surprisal axis as the 358,633 model
passages in `passages.parquet`, so `alignment_smooths.md`'s result -- aligned
prose collapses onto 1.135 bits/byte where base prose spreads 0.9 to 2.4 -- can
finally be read against human writing instead of only against itself.

## THE SCORING IS COPIED VERBATIM FROM THE ARCHIVE, NOT REIMPLEMENTED

Lifted from `malign-logits/scripts/blt_cloud.py`, which produced every
`bits_per_byte` in the parquet. That file carries the campaign rule it was
written under -- a sibling implementation is not the source, [5697] -- and this
is the case the rule exists for: a number that means "human prose sits here
relative to models" is worthless if the two sides were scored by two functions.
The archive is read-only, so the code is COPIED here rather than imported
across repos (RH, 2026-08-20).

Three details decide comparability and all three are easy to lose:

  * **NO PROMPT CONDITIONING.** `ids = tk(text)`, and the `prompt` field is a
    dedup key only. The model passages were scored on their continuation alone.
    v1's `blt_human_corpora.py` passed `prompt_prefix=prompt`, which conditions
    the scorer -- so its human numbers were never on this axis.
  * **BYTES, NOT CHARS.** `bits_per_byte = sur.sum() / ln2 / len(text.encode())`.
    v1 divided by characters. For ASCII they coincide and for anything else they
    do not, which is precisely why byte-level was chosen: it is ONE scale across
    94 tokenizers and across scripts.
  * **THE DENOMINATOR COUNTS A BYTE THE NUMERATOR CANNOT.** `sur` holds n-1
    values, because the first byte has nothing to condition on, and it is
    divided by the FULL byte count. Dividing by `sur.size` instead would shift
    every value by a factor of n/(n-1) -- about 0.1% at 1,100 bytes, invisible,
    and enough to move a distributional claim.

## Two refusals, both recorded rather than silent

  under-2-bytes        nothing to predict
  not byte+4           a genuine byte-level tokenization is exactly
                       `[b + 4 for b in text.encode()]`. Anything else contains
                       a literal special-token string, which indexes past BLT's
                       byte vocabulary and, on CUDA, poisons the context so that
                       every later forward fails. The archive lost two shards to
                       this before the pre-check existed.

Human text should trip neither, and if it trips the second the passage is not
what it claims to be -- so the count is printed and the rows are written out.
"""

import argparse, hashlib, json, os, sys, time
import numpy as np

BLT = "itazap/blt-1b-hf"


def done_keys(path):
    """(prompt, text_sha) already scored in this output. -> set"""
    got = set()
    if os.path.exists(path):
        with open(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                got.add((r.get("prompt"), r.get("text_sha")))
    return got


def read_rows(path):
    """Accept the human anchor directly. -> iterator of dicts

    `human_anchor.jsonl` has no `prompt` -- human passages were not generated
    from one -- so it is set to "" and carries no meaning beyond the dedup key,
    which is exactly its role on the model side too.
    """
    opener = __import__("gzip").open if path.endswith(".gz") else open
    with opener(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            text = r.get("text") or ""
            yield {"prompt": r.get("prompt", "") or "",
                   "text": text,
                   "id": r.get("id"),
                   "corpus": r.get("corpus"),
                   "corpora": r.get("corpus"),
                   "n_bytes": len(text.encode()),
                   "n_chars": len(text),
                   "script": "en"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dtype", default="float32",
                    choices=["float32", "bfloat16", "float16"])
    a = ap.parse_args()

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    dt = {"float32": torch.float32, "bfloat16": torch.bfloat16,
          "float16": torch.float16}[a.dtype]
    #: DTYPE IS A LOGIT DIFFERENCE. The fleet ran float32 and so does this; a
    #: dtype delta between the two sides would be a scorer difference wearing
    #: the costume of a memory optimisation.
    print("device %s | compute dtype %s | shard %d/%d" % (dev, a.dtype, a.shard, a.of),
          flush=True)

    tk = AutoTokenizer.from_pretrained(BLT, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        BLT, trust_remote_code=True, dtype=dt).eval().to(dev)

    os.makedirs(a.out, exist_ok=True)
    jl = os.path.join(a.out, "blt_human%02d.jsonl" % a.shard)
    fb = os.path.join(a.out, "blt_human%02d.f32" % a.shard)
    done = done_keys(jl)
    #: ROW COUNTER FROM THE FILE'S OWN SIZE, never a remembered count.
    row = os.path.getsize(fb) // 4 if os.path.exists(fb) else 0
    print("resuming: %d already scored, %d floats in the sidecar" % (len(done), row),
          flush=True)

    n_seen = n_new = 0
    skipped = []
    t0 = time.time()
    with open(jl, "a") as out, open(fb, "ab") as sb:
        for i, r in enumerate(read_rows(a.input)):
            if i % a.of != a.shard:
                continue
            n_seen += 1
            if a.limit and n_seen > a.limit:
                break
            text, prompt = r["text"], r["prompt"]
            sha = hashlib.sha256(text.encode()).hexdigest()[:16]
            if (prompt, sha) in done:
                continue
            ids = tk(text, add_special_tokens=False)["input_ids"]
            if len(ids) < 2:
                skipped.append({"id": r["id"], "text_sha": sha,
                                "n_bytes": len(text.encode()), "n_ids": len(ids),
                                "why": "under-2-bytes (not scorable)"})
                continue
            if ids != [b + 4 for b in text.encode()]:
                skipped.append({"id": r["id"], "text_sha": sha,
                                "n_bytes": len(text.encode()), "n_ids": len(ids),
                                "max_id": max(ids),
                                "why": "not byte+4 (special-token literal)"})
                continue
            with torch.no_grad():
                lg = model(torch.tensor([ids], device=dev)).logits[0]
            lp = torch.log_softmax(lg.float(), -1)
            idx = torch.tensor(ids[1:], device=dev)
            sur = (-lp[:-1].gather(1, idx[:, None]).squeeze(1)).cpu().numpy().astype(np.float32)
            sb.write(sur.tobytes())
            nb = len(text.encode())
            out.write(json.dumps({
                "id": r["id"], "corpus": r["corpus"],
                "prompt": prompt, "text_sha": sha, "script": r.get("script"),
                "corpora": r.get("corpora"), "n_bytes": nb, "n_chars": r.get("n_chars"),
                "n_tokens": len(ids), "row": row, "n": int(sur.size),
                "bits_per_byte": float(sur.sum() / np.log(2) / nb),
                "ref": BLT, "dtype": a.dtype}) + "\n")
            row += int(sur.size)
            n_new += 1
            if n_new % 50 == 0:
                out.flush(); sb.flush()
                el = (time.time() - t0) / 60
                print("  %d scored  %.1f min  %.2f/s" % (n_new, el, n_new / max(el * 60, 1)),
                      flush=True)
    if skipped:
        sp = os.path.join(a.out, "blt_human%02d.skipped.jsonl" % a.shard)
        with open(sp, "a") as fh:
            for r in skipped:
                fh.write(json.dumps(r) + "\n")
        print("  REFUSED %d passage(s) as non-byte-level; recorded in %s"
              % (len(skipped), os.path.basename(sp)), flush=True)
    print("shard %d done: %d seen, %d newly scored, %d refused, %.1f min"
          % (a.shard, n_seen, n_new, len(skipped), (time.time() - t0) / 60), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
