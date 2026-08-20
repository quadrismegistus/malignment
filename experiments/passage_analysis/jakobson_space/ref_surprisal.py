"""Token-level reference surprisal, for any text -- model output or human prose.

    python .../ref_surprisal.py --input passages.jsonl --out $MALIGNMENT_DATA/ref/deepseek
    python .../ref_surprisal.py --probe "The sky was the color of television tuned to a dead channel."

Input is JSONL with `text`, and optionally `id` and `corpus`. Output mirrors the
BLT pass: one summary per passage plus a `.f32` sidecar of per-token surprisal,
with `row`/`n` pointing into it, so any prefix statistic is a partial sum later.

## WHY A SECOND REFERENCE, AND WHY TOKEN-LEVEL

BLT-1b scores BYTES, and on a byte scale the cost of a word is paid at its first
unpredictable character. On Gibson's line it charges 12.89 bits for `sky`, 8.40
for `television` and 0.77 for `tuned` -- once `t-u-n-e` is on the page the `d` is
free, so a semantically startling word arrives cheap if its opening letters are
common. That measures orthographic predictability, and lexical choice reaches it
only through spelling.

Measured on the same sentence (bits for the token, and the ratio between the
commodity noun and the collocation it licenses):

    reference              television   tuned   ratio   bits/byte   frame vocabulary
    deepseek-llm-7b-base        13.63    3.28    4.16      0.6741   blood/blue/steel
    Falcon3-10B-Base            14.80    2.95    5.02      0.7063   slate/milk/steel
    pythia-6.9b                  9.51    7.99    1.19      0.7260   steel/slate/lead
    gpt2                        15.04   12.97    1.16      1.3279   the/death/fire/my
    pythia-410m-deduped         14.42   15.63    0.92      1.0971   blood/burnt/wet
    BLT-1b                       8.40    0.77      --      0.5553   n/a

## WHY deepseek-llm-7b-base AND NOT THE OTHERS

It ranks `television` first, prices `tuned` cheaply because the collocation
follows from it, expects natural substances in the slot, and has the lowest
bits/byte of any candidate. Falcon3-10B scores marginally better on the ratio,
but tiiuae supplies 14 of the 92 models in `passages_std.parquet` and 8 of the 58
in the coded-narrative subset, INCLUDING Falcon3-10B-Base scoring its own output.
pythia-6.9b has the same defect over 4 models. **deepseek-llm-7b generated none
of the passages in the corpus**, so it is the one strong reference that is not
also a subject.

## THE ROUNDTRIP GUARD IS NOT OPTIONAL

`AutoTokenizer` resolves this repo to `LlamaTokenizer`, whose SentencePiece
Metaspace pre-tokenizer (transformers #45488, generic fix #47017 unmerged as of
5.4.0) DELETES EVERY SPACE:

    'The sky was the color of'  ->  'Theskywasthecolorof'

It loads, it runs, it returns numbers, and nothing raises. Scored that way the
same sentence reads 1.5394 bits/byte with `ade`, `te`, `w` among its most
surprising tokens -- a plausible-looking result computed on a destroyed string.
`LOADER_OVERRIDE` in `malignment/twp.py` fixes it with `PreTrainedTokenizerFast`,
and the guard below REFUSES to score unless the tokenizer round-trips, so a
future transformers release that changes the resolution again fails loudly
instead of quietly.
"""

import argparse, hashlib, json, os, sys, time

REF = "deepseek-ai/deepseek-llm-7b-base"
#: from malignment/twp.py LOADER_OVERRIDE -- retires when #47017 lands and
#: `tokenizer_roundtrip_sweep.py` reports the model clean under AutoTokenizer.
TOKENIZER_CLASS = "PreTrainedTokenizerFast"
PROBES = [
    "The sky was the color of television tuned to a dead channel.",
    "He lay naked in his bed and",
    "She was so angry she wanted to",
    'Then he said, "I don\'t know" -- and left.',
]


def load(ref, tok_class, dtype="float32", device=None):
    """-> (tokenizer, model, device). Refuses a tokenizer that does not round-trip."""
    import torch, transformers
    from transformers import AutoModelForCausalLM
    tk = getattr(transformers, tok_class).from_pretrained(ref)
    for p in PROBES:
        back = tk.decode(tk(p, add_special_tokens=False)["input_ids"])
        if back.strip() != p.strip():
            raise SystemExit(
                "REFUSING: %s tokenizer does not round-trip under %s.\n"
                "  sent %r\n  got  %r\n"
                "Scoring would run on a corrupted string and return plausible "
                "numbers. See malignment/twp.py LOADER_OVERRIDE."
                % (ref, tok_class, p, back))
    print("  tokenizer %s round-trips on %d probes" % (type(tk).__name__, len(PROBES)))
    #: DEFAULT IS CPU, and mps must be asked for. It is not excluded on
    #: principle -- it is excluded until someone shows it agrees, because the
    #: bge pass found mps corrupting short-sequence embeddings on this machine.
    #: `--device mps` plus `--compare-cpu` is how that gets established.
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    dt = {"float32": torch.float32, "bfloat16": torch.bfloat16,
          "float16": torch.float16}[dtype]
    m = AutoModelForCausalLM.from_pretrained(ref, dtype=dt, low_cpu_mem_usage=True).eval().to(dev)
    return tk, m, dev


def score(text, tk, m, dev):
    """-> (surprisal bits, byte-end offsets, token strings) or None.

    THE BYTE OFFSETS ARE WHAT MAKE THIS COMPARABLE TO BLT, and without them the
    sidecar is nearly useless for this corpus. BLT's `.f32` is per BYTE, so
    `sur[:K-1].sum()/K` is an exact prefix statistic and the whole length-control
    apparatus rests on it -- human passages run 970-1406 bytes by genre and model
    passages have a long short tail, so every cross-group number here is quoted
    at a common byte prefix. A per-TOKEN array cannot answer that question at
    all: tokens do not align to byte offsets, so there is no way to ask what the
    first 850 bytes cost.

    `offset_mapping` gives character spans; bytes are `len(text[:c].encode())`.
    Storing the byte END of each scored token lets a prefix at K be a mask,
    `byte_end <= K`, with the denominator taken from the last included token
    rather than from K -- so the reported rate is over the bytes actually
    covered, never over a boundary a token straddles.
    """
    import numpy as np, torch
    enc = tk(text, return_offsets_mapping=True)
    ids = torch.tensor([enc["input_ids"]])
    if ids.shape[1] < 2:
        return None
    with torch.no_grad():
        lg = m(ids.to(dev)).logits[0]
    lp = torch.log_softmax(lg.float(), -1)
    tgt = ids[0, 1:].to(dev)
    sur = (-lp[:-1].gather(1, tgt[:, None]).squeeze(1)).cpu().numpy() / np.log(2)
    #: byte end of each SCORED token, i.e. tokens 1..n-1, aligned to `sur`
    ends = np.array([len(text[:c1].encode()) for _, c1 in enc["offset_mapping"][1:]],
                    dtype=np.int32)
    assert ends.size == sur.size, (ends.size, sur.size)
    return sur.astype(np.float32), ends, [tk.decode([t]) for t in ids[0, 1:].tolist()]


def word_bits(text, sur, ends):
    """Attribute token surprisal to WORDS. -> list of dicts, in text order.

    This is what the byte offsets buy beyond length control: the question "which
    words are surprising in this passage" becomes answerable, which is the
    selection axis read directly off a single passage rather than inferred from
    a passage-level mean.

    A token is assigned to the word containing its LAST byte, so a token that
    straddles a boundary is charged to the word it completes. Multi-token words
    accumulate: on `The sky was the color of television tuned to a dead channel.`
    the cost lands on `television` (13.63 bits) and `sky` (12.57), while `tuned`
    takes 3.28 because the collocation follows from `television`.

    THE FIRST TOKEN IS UNSCORED -- nothing precedes it -- so the first word
    carries only the bits of its second and later tokens, and is marked
    `partial`. Reporting it as a low-surprisal word would be an artifact of
    position, not a fact about the word.
    """
    import re
    out, first_scored = [], None
    for m in re.finditer(r"\S+", text):
        a = len(text[:m.start()].encode())
        b = len(text[:m.end()].encode())
        idx = [i for i, e in enumerate(ends) if a < e <= b]
        if first_scored is None and idx:
            first_scored = m.start()
        out.append(dict(word=m.group(0), byte_start=a, byte_end=b,
                        bits=float(sum(sur[i] for i in idx)), n_tokens=len(idx),
                        partial=(m.start() == 0)))
    return out


def done_keys(path):
    got = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                got.add(json.loads(line)["text_sha"])
            except Exception:
                pass
    return got


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="JSONL with a `text` field")
    ap.add_argument("--out", help="output directory")
    ap.add_argument("--probe", help="score one string and print the tokens, then exit")
    ap.add_argument("--ref", default=REF)
    ap.add_argument("--tokenizer-class", default=TOKENIZER_CLASS)
    ap.add_argument("--dtype", default="float32")
    ap.add_argument("--device", help="cpu | mps | cuda (default: cuda if present else cpu)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    a = ap.parse_args(argv)
    import numpy as np

    print("reference %s | tokenizer %s | dtype %s" % (a.ref, a.tokenizer_class, a.dtype))
    tk, m, dev = load(a.ref, a.tokenizer_class, a.dtype, a.device)
    print("  device %s" % dev)

    if a.probe:
        sur, ends, toks = score(a.probe, tk, m, dev)
        nb = len(a.probe.encode())
        print("\n%r\n  %.4f bits/byte | %.4f bits/token | %d tokens, %d bytes"
              % (a.probe, sur.sum() / nb, sur.mean(), len(toks), nb))
        for j in np.argsort(-sur)[:10]:
            print("    %-16r %7.2f bits" % (toks[j], sur[j]))
        wb = word_bits(a.probe, sur, ends)
        print("\n  most surprising WORDS:")
        for w in sorted(wb, key=lambda x: -x["bits"])[:10]:
            print("    %-18r %7.2f bits  (%d token%s)%s"
                  % (w["word"], w["bits"], w["n_tokens"], "" if w["n_tokens"] == 1 else "s",
                     "  [partial: first word]" if w["partial"] else ""))
        tot = sum(w["bits"] for w in wb)
        print("  word bits sum %.2f vs token bits sum %.2f  (match=%s)"
              % (tot, sur.sum(), abs(tot - sur.sum()) < 1e-3))
        return 0

    if not (a.input and a.out):
        sys.exit("need --input and --out (or --probe)")
    os.makedirs(a.out, exist_ok=True)
    jl = os.path.join(a.out, "ref_shard%02d.jsonl" % a.shard)
    fb = os.path.join(a.out, "ref_shard%02d.f32" % a.shard)
    ob = os.path.join(a.out, "ref_shard%02d.i32" % a.shard)   # byte-end offsets
    done = done_keys(jl)
    #: row counter from the file's own size, never a remembered count. Both
    #: sidecars are int32/float32 and share the row index, so a mismatch between
    #: them is a torn write and must not be resumed over.
    row = os.path.getsize(fb) // 4 if os.path.exists(fb) else 0
    orow = os.path.getsize(ob) // 4 if os.path.exists(ob) else 0
    if row != orow:
        sys.exit("torn sidecars: %d floats but %d offsets; truncate both to the "
                 "shorter before resuming" % (row, orow))
    print("  resuming: %d scored, %d floats in the sidecar" % (len(done), row))

    n_seen = n_new = 0
    skipped = []
    t0 = time.time()
    with open(a.input) as src, open(jl, "a") as out, open(fb, "ab") as sb, \
            open(ob, "ab") as ob_fh:
        for i, line in enumerate(src):
            line = line.strip()
            if not line or i % a.of != a.shard:
                continue
            r = json.loads(line)
            n_seen += 1
            if a.limit and n_seen > a.limit:
                break
            text = r.get("text") or ""
            sha = hashlib.sha256(text.encode()).hexdigest()[:16]
            if sha in done:
                continue
            got = score(text, tk, m, dev)
            if got is None:
                skipped.append({"id": r.get("id"), "text_sha": sha, "why": "under-2-tokens"})
                continue
            sur, ends, _ = got
            sb.write(sur.tobytes()); ob_fh.write(ends.tobytes())
            nb = len(text.encode())
            out.write(json.dumps({
                "id": r.get("id"), "corpus": r.get("corpus"), "model": r.get("model"),
                "text_sha": sha, "n_bytes": nb, "n_chars": len(text),
                "n_tokens": int(sur.size) + 1, "row": row, "n": int(sur.size),
                "bits_per_byte": float(sur.sum() / nb),
                "bits_per_token": float(sur.mean()),
                "offsets": "ref_shard%02d.i32" % a.shard,
                "ref": a.ref, "tokenizer": type(tk).__name__, "dtype": a.dtype}) + "\n")
            row += int(sur.size)
            n_new += 1
            if n_new % 50 == 0:
                out.flush(); sb.flush(); ob_fh.flush()
                el = (time.time() - t0) / 60
                print("  %d scored  %.1f min  %.2f/s" % (n_new, el, n_new / max(el * 60, 1)),
                      flush=True)
    if skipped:
        with open(os.path.join(a.out, "ref_shard%02d.skipped.jsonl" % a.shard), "a") as fh:
            for s in skipped:
                fh.write(json.dumps(s) + "\n")
    print("shard %d done: %d seen, %d scored, %d skipped, %.1f min"
          % (a.shard, n_seen, n_new, len(skipped), (time.time() - t0) / 60))
    return 0


if __name__ == "__main__":
    sys.exit(main())
