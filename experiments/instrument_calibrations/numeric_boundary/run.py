#!/usr/bin/env python
"""numeric_boundary — may the boundary rule read context? Stage 1: tokenizers.

    python run.py --stage tokenizers            -> results/by_tokenizer.csv

**STAGE 1 LOADS NO WEIGHTS.** The question it answers is entirely about how a
tokenizer splits a string, and `twp.intra_word` is a pure function, so nothing
here needs a GPU, a fleet or a spend. Stages 2 and 3 do and are not implemented.

## WHAT IT ASKS, AND WHY THAT IS THE DECIDING FACT

`twp.intra_word` ALREADY implements the numeric rule at character level -- its
own docstring names `100` + `,000` -- and it is unreachable in practice:

    return len(tok_str) > 1 and tok_str[1].isalnum()

**It needs the separator to arrive INSIDE a token with something after it.** A
tokenizer that emits `,` alone hands it a one-character string and the test
fails at `len(tok_str) > 1`. So the rule is not missing; it is starved. This
stage measures how often it is starved, across the roster, per character class.

## THE CJK ARM IS THE SAME QUESTION WITH THE SIGN FLIPPED

Full-width `，` and `。` end a Chinese sentence and are NOT in the intra set, so
they behave correctly ONLY IF the mask treats them as boundaries. @malign's
[6423] reports it does not. Both arms are here because a patch to one that
ignores the other is how a classifier acquires two incompatible exceptions.

## FAILURES ARE RECORDED, NEVER DROPPED

A tokenizer that will not load is a row with a reason, not an absence. Roughly a
dozen roster entries are gated or need transformers 4.57, and a silently shorter
table would read as a cleaner result.
"""
import argparse, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS_FROM = None
RESULTS = os.path.join(HERE, "results")

#: Chosen so each isolates ONE decision. The salary case is the one that
#: motivated the commission; the decimal is the case `intra_word`'s own
#: docstring admits it fails; the CJK pair is the opposite-sign arm.
PROBES = [
    ("thousands", "a salary of $150,000 a year", ",", "150,000"),
    ("decimal",   "the value of pi is 3.14 exactly", ".", "3.14"),
    ("cjk_comma", "他很高兴，因为下雨了", "，", None),
    ("cjk_stop",  "他很高兴。下雨了", "。", None),
]


def probe(tok, sep, surface):
    """How does this tokenizer present `sep`, and can intra_word act on it?

    Returns (sep_alone, intra_fires, sample). `sep_alone` is the condition that
    starves the rule; `intra_fires` is measured by asking `intra_word` about
    every token of the string rather than reasoning about which one matters.
    """
    from malignment import twp
    ids = tok.encode(PROBE_TEXT, add_special_tokens=False)
    pieces = [tok.decode([i]) for i in ids]
    hits = [p for p in pieces if sep in p]
    if not hits:
        return None, None, ""
    sep_alone = any(p.strip() == sep for p in hits)
    intra = False
    if surface:
        intra = any(twp.intra_word(surface, p) for p in pieces)
    return sep_alone, intra, " | ".join(repr(p) for p in hits[:3])


def stage_tokenizers(limit=None):
    from malignment import roster, twp
    #: sorted() because population() returns a SET -- iteration order would be
    #: unstable between runs and the csv would diff for no reason.
    models = sorted(roster.population("all"))
    if limit:
        models = models[:limit]
    #: `--models-from` exists because the 24 failures of the first sweep were NOT
    #: a random 24: 23 were transformers-5 validation errors, i.e. the `tf457`
    #: cohort, which this repo keeps a second venv for. A sweep that drops a
    #: systematically-selected subset and reports 136/136 is reporting the venv.
    if MODELS_FROM:
        want = [l.strip() for l in open(MODELS_FROM) if l.strip()]
        models = [m for m in models if m in set(want)]
    rows, failed = [], 0
    for i, mid in enumerate(models, 1):
        try:
            tok, loader = twp.load_tokenizer(mid)
        except Exception as e:
            failed += 1
            rows.append({"model": mid, "loaded": 0,
                         "reason": type(e).__name__ + ": " + str(e)[:80]})
            continue
        row = {"model": mid, "loaded": 1, "reason": ""}
        for name, text, sep, surface in PROBES:
            global PROBE_TEXT
            PROBE_TEXT = text
            try:
                alone, intra, sample = probe(tok, sep, surface)
                row[name + "_sep_alone"] = "" if alone is None else int(alone)
                row[name + "_intra_fires"] = "" if intra is None else int(intra)
                row[name + "_sample"] = sample
            except Exception as e:
                row[name + "_sep_alone"] = "ERR"
                row[name + "_sample"] = str(e)[:50]
        rows.append(row)
        del tok
        if i % 20 == 0:
            print("  %d/%d" % (i, len(models)), file=sys.stderr)
    return rows, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="tokenizers", choices=["tokenizers"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--models-from", default=None,
                    help="file of model ids, one per line -- for the tf457 cohort")
    ap.add_argument("--out", default="by_tokenizer.csv")
    a = ap.parse_args()
    global MODELS_FROM
    MODELS_FROM = a.models_from
    os.makedirs(RESULTS, exist_ok=True)
    rows, failed = stage_tokenizers(a.limit)

    cols = ["model", "loaded", "reason"]
    for name, _, _, _ in PROBES:
        cols += [name + "_sep_alone", name + "_intra_fires", name + "_sample"]
    path = os.path.join(RESULTS, a.out)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    ok = [r for r in rows if r.get("loaded")]
    print("\ntokenizers: %d loaded, %d failed (recorded, not dropped)"
          % (len(ok), failed))
    for name, _, _, surface in PROBES:
        k = name + "_sep_alone"
        seen = [r for r in ok if r.get(k) not in ("", None)]
        alone = sum(1 for r in seen if r.get(k) == 1)
        fires = sum(1 for r in seen if r.get(name + "_intra_fires") == 1)
        print("  %-10s separator present in %3d | emitted ALONE in %3d | "
              "intra_word fires in %3d" % (name, len(seen), alone, fires))
    print("\n  ->", path)


if __name__ == "__main__":
    main()
