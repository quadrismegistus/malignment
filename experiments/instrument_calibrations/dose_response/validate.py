"""Does the model-derived dose do the DOSE'S JOB? Gradient against gradient.

Word-level agreement with the hand tagging is not the test. `displacement_axis`
uses `base_naughty_mass` to produce a displacement gradient -- 3% / 11% / 27% / 37%
across dose quartiles on 15,150 cells -- and THAT is the property the instrument
has to reproduce. A rater could pick different words and give the same dose, or the
same words and give a different one.

So: tag all 255 hand-tagged prompts with wording B, compute the gradient twice --
once from the author's tags, once from the model's -- and compare. The outcome
comes from twp_words_v4 and the pole axis; nothing in it comes from the rater, so
there is no circularity.

WHAT IS NOT TESTED HERE, and why:

  MARKED/UNMARKED pairs. Dropped. Those arms are 3% of the transgressive range
  apart (`M01_RECONSIDERED.md`), which is WHY a continuous dose is being built.
  Validating the replacement against the contrast it replaces cannot separate a
  noisy rater from genuinely adjacent prompts -- 25 of 40 is what a GOOD instrument
  scores there. RH's objection; the earlier check is retained in `empty_check.py`
  as a record, not as evidence.

  `any_loaded`. Also dropped. The dose is continuous mass. An ordinary frame coming
  back `true` with 2% mass is a LOW DOSE, which is the right answer. The flag
  guarded against a partition task manufacturing a split, and this is a search task.
"""
import argparse, base64, json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", type=int, default=200)
    ap.add_argument("--wording", default="B")
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--run", default="pilot4", help="displacement_axis run for the outcome")
    a = ap.parse_args(argv)

    from malignment import ch, roster
    from malignment.slots import corpora, read_items
    from task import task_for, render
    import numpy as np

    items = [d for _, p in corpora() for d in read_items(p) if not d.get("quarantined")]
    hand = {}
    for d in items:
        if d.get("naughty"):
            hand.setdefault(d["prompt"], set()).update(d["naughty"])
    m = roster.endpoints(); m = m[0] if isinstance(m, tuple) else m
    inb = ",".join("'" + b.replace("'", "''") + "'" for b in sorted(m))

    #: the OUTCOME: signature per (prompt, base, endpoint) from displacement_axis
    cells = os.path.join(HERE, "..", "..", "displacement", "displacement_axis",
                         "results", a.run, "cells.jsonl")
    sig = collections.defaultdict(list)
    with open(cells, encoding="utf-8") as fh:
        for line in fh:
            c = json.loads(line)
            sig[c["prompt"]].append((c["base"], c.get("signature")))
    prompts = sorted(p for p in hand if p in sig)
    print("hand-tagged prompts with displacement cells: %d" % len(prompts))

    CAND, MASS = {}, {}
    for p in prompts:
        b64 = base64.b64encode(p.encode()).decode()
        rows = ch.query("SELECT model, word, sum(p) s FROM twp_words_v4 "
                        "WHERE base64Encode(prompt)='%s' AND model IN (%s) "
                        "GROUP BY model, word" % (b64, inb))
        by = collections.defaultdict(dict)
        agg = collections.Counter()
        for r in rows:
            by[r["model"]][r["word"]] = float(r["s"]); agg[r["word"]] += float(r["s"])
        MASS[p] = by
        CAND[p] = [w for w, _ in agg.most_common(a.cands)]

    t = task_for(a.wording); errs = []
    out = t.map([render(p, CAND[p]) for p in prompts], num_workers=a.workers, errors=errs)
    model_tags = {p: {w for w in (r.words or []) if w in set(CAND[p])}
                  for p, r in zip(prompts, out) if r is not None}
    print("tagged: %d prompts, %d errors | model words/prompt median %d, hand %d\n"
          % (len(model_tags), len(errs),
             int(np.median([len(v) for v in model_tags.values()])),
             int(np.median([len(hand[p]) for p in prompts]))))
    json.dump({p: sorted(v) for p, v in model_tags.items()},
              open(os.path.join(HERE, "tags_%s.json" % a.wording), "w"),
              ensure_ascii=False, indent=1)

    def dose(p, base, tags):
        per = MASS[p].get(base) or {}
        tot = sum(per.values()) or 1.0
        return sum(v for w, v in per.items() if w in tags) / tot

    def gradient(tagsrc, label):
        rows = []
        for p in prompts:
            tg = tagsrc(p)
            if tg is None:
                continue
            for base, s in sig[p]:
                if base in MASS[p]:
                    rows.append((dose(p, base, tg), s))
        if not rows:
            print("  %s: no cells" % label); return
        rows.sort()
        q = np.array_split(np.array(range(len(rows))), 4)
        print("  %-14s %7s %8s %8s %8s" % (label, "cells", "displ%", "churn%", "med dose"))
        for i, idx in enumerate(q, 1):
            sub = [rows[j] for j in idx]
            d = 100.0 * sum(1 for _, s in sub if s == "displacement") / len(sub)
            c = 100.0 * sum(1 for _, s in sub if s == "churn") / len(sub)
            print("     Q%d          %7d %7.1f%% %7.1f%% %8.4f"
                  % (i, len(sub), d, c, float(np.median([x for x, _ in sub]))))
    print("DISPLACEMENT RATE BY DOSE QUARTILE")
    gradient(lambda p: hand.get(p), "HAND-TAGGED")
    print()
    gradient(lambda p: model_tags.get(p), "MODEL-TAGGED")
    hv = [sum((MASS[p].get(b) or {}).get(w, 0) for w in hand[p]) for p in model_tags for b, _ in sig[p][:1]]
    mv = [sum((MASS[p].get(b) or {}).get(w, 0) for w in model_tags[p]) for p in model_tags for b, _ in sig[p][:1]]
    if len(hv) > 3:
        print("\n  corr(hand dose, model dose) over prompts = %+.3f"
              % float(np.corrcoef(hv, mv)[0, 1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
