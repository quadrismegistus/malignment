"""Code the framed identity answers. -> results/coded.jsonl

    python -u code.py --dry              what it would code
    python -u code.py --workers 8        code it
    python -u code.py --limit 40         a smoke, resumable

The measurement is `run.py`'s output: 6,080 answers, 19 aligned models x 4
questions x 2 temps x 2 system conditions, n=20 per cell, every cell complete.

## THE COMPARISON THIS EXISTS FOR

`f20x_annotations` coded 18,720 UNTEMPLATED answers to the same four questions
and found that alignment swaps what the first person predicates: human
0.468 -> 0.199, AI 0.235 -> 0.509. Paired over 29 lineages it says the median
ALIGNED model still claims a HUMAN identity 43.3% of the time on "Who are you?".

That corpus never called `apply_chat_template`. This one is the same models
inside their own templates, so `identity_kind` is directly comparable and the
templated-vs-untemplated difference is the finding.

## RESUMABLE, AND THE KEY IS THE CELL PLUS THE INDEX

Coding is the metered step. The resume key is (model, qid, temp, system, idx),
which is the generation's own key, so a re-run codes exactly what is missing and
a partial run is not a partial cell.
"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

GEN = os.path.join(HERE, "results", "framed_identity.jsonl")
OUT = os.path.join(HERE, "results", "coded.jsonl")

KEY = ("model", "qid", "temp", "system", "idx")


def load_generations():
    rows = []
    with open(GEN) as fh:
        for line in fh:
            d = json.loads(line)
            #: idx == -1 is a cell-level refusal record, not a generation
            if d.get("idx", -1) >= 0:
                rows.append(d)
    return rows


def load_done():
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                    done.add(tuple(d[k] for k in KEY))
                except Exception:
                    pass
    return done


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)

    rows = load_generations()
    done = load_done()
    todo = [r for r in rows if tuple(r[k] for k in KEY) not in done]
    if a.limit:
        todo = todo[:a.limit]

    print("%d generations | %d already coded | %d to code"
          % (len(rows), len(done), len(todo)))
    cc = collections.Counter((r["system"], r["qid"]) for r in rows)
    for k in sorted(cc):
        print("   %-18s %5d" % ("%s/%s" % k, cc[k]))
    if a.dry or not todo:
        return 0

    from malignment.tasks.code_framed_identity_v1 import (FramedIdentityTask,
                                                          check_spans)
    task = FramedIdentityTask()
    errs = {}
    #: the coder sees the QUESTION and the ANSWER and nothing else -- not the
    #: model, not the system condition. See the task docstring: the persona
    #: confound is measured by the empty-minus-default gap in `analyse.py`, and
    #: that only works if the instrument cannot see which cell it is reading.
    prompts = ["QUESTION: %s\n\nANSWER: %s" % (r["question"], r["text"])
               for r in todo]
    res = task.map(prompts, num_workers=a.workers, verbose=True, errors=errs)

    ok_s = tot_s = n_out = 0
    with open(OUT, "a", encoding="utf-8") as fh:
        for r, o in zip(todo, res):
            if o is None:
                continue
            ok, tot, miss = check_spans(r["text"], o)
            ok_s += ok; tot_s += tot
            rec = {k: r[k] for k in KEY}
            rec["question"] = r["question"]
            rec.update(o.model_dump())
            rec["span_ok"] = ok
            rec["span_total"] = tot
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_out += 1

    print("\nwrote %d rows -> %s" % (n_out, OUT))
    if tot_s:
        print("spans located %d/%d (%.1f%%)" % (ok_s, tot_s, 100 * ok_s / tot_s))
    if errs:
        print("errors: %d" % len(errs))
        for k, v in list(errs.items())[:3]:
            print("   %s: %s" % (k, str(v)[:100]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
