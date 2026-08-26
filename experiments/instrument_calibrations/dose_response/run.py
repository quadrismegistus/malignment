"""Tag every English prompt in movement_v4 with wording B. Resumable.

    python -u run.py                  # all en prompts
    python -u run.py --limit 20       # smoke

Writes `results/tag_<sha12>.json`, ONE FILE PER PROMPT. Not an appended jsonl: the
pos_pass resume appended 4-column rows to a 3-column header and the table read as
1% VERB against the run's own 406,294, so a partial file that still parses is the
failure mode this layout exists to avoid. A prompt whose file exists is skipped.

## WHY WORDING B

Chosen by measurement, not argument (`pilot.py`, 60 hand-tagged prompts):

    wording  recall   prec   mass r   off-list words
       A      0.721   0.193   0.602        269
       B      0.688   0.237   0.894          3
       C      0.581   0.212   0.642          6

`mass r` is the correlation between hand-derived and model-derived
`base_naughty_mass` -- the quantity every downstream test consumes. A's named
categories made it GENERATE transgressive vocabulary rather than search the
candidates; words that are not in the list carry no mass and cannot enter a dose.

## AND WHY IT IS TRUSTED

Not word overlap. `validate.py` rebuilt `displacement_axis`'s displacement gradient
from model tags and from the author's, on identical cells:

    quartile      hand   model
    Q1            4.6%    7.6%
    Q2           13.9%   13.8%
    Q3           22.5%   23.3%
    Q4           36.3%   32.5%      prompt-level dose corr +0.779

Monotone in both, same shape, churn falling in step. The ordering transfers even
though the model tags ~3x as many words as the author (median 17 against 6), which
is the point: the gradient is robust to the exact word set, and word-level
agreement was never the criterion.

FENCES CARRIED FORWARD. It is more INCLUSIVE, not more accurate. The ends compress
-- Q1 up, Q4 down -- as imperfect recall predicts, so quartile RATES from a
model-derived dose must not be quoted against hand-derived ones; the ordering
transfers, the levels do not.

ENGLISH ONLY. zh candidate vocabularies do not converge: at N=400 the worst-covered
base model still holds only 0.742 of its mass in the union, and one prompt in four
never reaches 0.90 at any list length. That is segmentation divergence, not a list
that is too short, and a dose whose coverage floor is 0.20 on some prompts is worse
than no dose.
"""
import argparse, base64, collections, hashlib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "results")
CJK = re.compile(r"[一-鿿]")


def pid(p):
    return hashlib.sha1(p.encode("utf-8")).hexdigest()[:12]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", type=int, default=200)
    ap.add_argument("--wording", default="B")
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--batch", type=int, default=120, help="prompts per API map call")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)

    from malignment import ch, roster
    from task import task_for, render

    m = roster.endpoints(); m = m[0] if isinstance(m, tuple) else m
    inb = ",".join("'" + b.replace("'", "''") + "'" for b in sorted(m))
    prompts = [r["prompt"] for r in ch.query("SELECT DISTINCT prompt FROM movement_v4")]
    en = sorted(p for p in prompts if not CJK.search(p))
    os.makedirs(OUT, exist_ok=True)
    todo = [p for p in en if not os.path.exists(os.path.join(OUT, "tag_%s.json" % pid(p)))]
    if a.limit:
        todo = todo[:a.limit]
    print("movement_v4: %d prompts | en %d | already done %d | to run %d"
          % (len(prompts), len(en), len(en) - len(todo), len(todo)), flush=True)

    t = task_for(a.wording)
    done = 0
    for s in range(0, len(todo), a.batch):
        blk = todo[s:s + a.batch]
        CAND = {}
        for p in blk:
            b64 = base64.b64encode(p.encode()).decode()
            rows = ch.query("SELECT word, sum(p) s FROM twp_words_v4 "
                            "WHERE base64Encode(prompt)='%s' AND model IN (%s) "
                            "GROUP BY word ORDER BY s DESC LIMIT %d" % (b64, inb, a.cands))
            CAND[p] = [r["word"] for r in rows]
        live = [p for p in blk if CAND[p]]
        if not live:
            continue
        errs = []
        out = t.map([render(p, CAND[p]) for p in live], num_workers=a.workers, errors=errs)
        n_w = 0
        for p, r in zip(live, out):
            if r is None:
                continue
            cand = set(CAND[p])
            #: off-list words carry no mass and cannot enter a dose; recorded, not kept
            got = [w for w in (r.words or []) if w in cand]
            off = [w for w in (r.words or []) if w not in cand]
            rec = {"prompt": p, "wording": a.wording, "reading": r.reading,
                   "axis": r.axis, "any_loaded": bool(r.any_loaded),
                   "words": got, "off_list": off, "n_candidates": len(cand)}
            with open(os.path.join(OUT, "tag_%s.json" % pid(p)), "w", encoding="utf-8") as fh:
                json.dump(rec, fh, ensure_ascii=False, indent=1)
            n_w += len(got); done += 1
        print("  %5d/%-5d prompts | %d words this block | %d errors"
              % (done, len(todo), n_w, len(errs)), flush=True)
    print("\nDONE: %d prompts tagged -> %s" % (done, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
