"""Movement across the 43 Think-SFT rungs -> the `movement_rungs` table.

    python -u rung_movement.py --plan
    python -u rung_movement.py --run
    python -u rung_movement.py --check

## WHY A SEPARATE TABLE AND NOT `movement`

`movement` holds 56.3M rows over 85 bases x 108 aligned, and **nothing in its
schema distinguishes a ladder rung from a declared alignment edge** -- the only
handle would be string-matching `@step` in `aligned`. Writing 85 pairs x 2,272
prompts into it adds ~17M rows to a table sixteen-odd scripts read, and every
unfiltered consumer query silently picks them up. There is no precedent either:
the only checkpoint-style rows in `movement` today are a single SmolLM3 pair.

So this is its own table, with the population explicit rather than implied by a
`NOT LIKE '%@step%'` that nobody currently writes.

## TWO EDGE KINDS, AND MOVEMENT IS NOT ADDITIVE

    kind='base_rooted'   base -> rung n      43 pairs   CUMULATIVE
    kind='increment'     rung n -> rung n+1  42 pairs   PER-STEP

**Both, because you cannot get one from the other.** `produce_movement`'s own
docstring makes the argument for rungs and transitive pairs and it carries over
unchanged: *a word can fall at one stage and rise at another*, so the
riser/faller classification of base -> rung 43 is NOT recoverable from summing
42 increments. The cumulative edge answers *how far has this word moved by step
n*; the increment answers *how much moved during this interval*.

The two are used for different halves of the question. Onset and lag are
statements about accumulated movement from a fixed reference, so they read off
`base_rooted`. "Step-like versus gradual" is a statement about where change
concentrates, so it reads off `increment`.

## rule_version IS A COLUMN HERE, AND `rule` IS NOT A VERSION

The ladder exists only in `twp_words` (v3); `twp_cells_v4` holds zero rungs of
it. So every row here is `rule_version=3`, stored explicitly rather than implied
by the table name, because this table has no v4 sibling to imply it against.

**`rule` is NOT the version.** It names the faller/riser CLASSIFICATION rule --
`CANONICAL(min_prob=0.003, fall_ratio=0.5, delta=0.003, null_test=True)` -- which
did not change between v3 and v4. An earlier draft of this experiment called
`rule='canonical'` appearing in both movement tables a collision; it is not, and
RH caught it. The two axes are independent and both are recorded.

## THE RESIDUAL IS REQUIRED, NOT OPTIONAL

`movement()` needs each arm's untruncated remainder: the renormalisation null
needs total mass and the scored words do not carry it. Omit it and `exact_null`
is False, *"which is a claim about the input, not a property of the data"* -- and
the rows would be quietly incomparable with every other movement row.

At v3 the residual is `twp_cells.total`. (At v4 it must be derived as
`tail+drop+open+mojibake`, because `total` there is the PASS-1 residual and using
it breaks the ledger. That path is not taken here and the distinction is recorded
so nobody ports this to v4 by changing one string.)

## POPULATION: ALL 2,272 PROMPTS, FILTERED AT ANALYSIS TIME

1,802 of the ladder's prompts are VERSE PREFIXES from the M05 rhyme fleet and are
the wrong instrument for a displacement question. They are built anyway and
excluded by the analysis, because a table that silently contains only part of a
measured population is the harder defect to notice later.
"""
import argparse, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

from malignment import ch                                          # noqa: E402
from malignment.ch import _lit                                     # noqa: E402
from malignment.movement import movement, CANONICAL, RESIDUAL_KEY  # noqa: E402
from malignment import produce_movement as PM                      # noqa: E402

BASE = "allenai/Olmo-3-1025-7B"
LADDER = "allenai/Olmo-3-7B-Think-SFT"
STEPS = list(range(1000, 44000, 1000))          #: 43 rungs, verified present
TABLE = "movement_rungs"
RULE_VERSION = 3

DDL = """
CREATE TABLE IF NOT EXISTS {db}.movement_rungs (
  kind          LowCardinality(String),
  base          String,
  aligned       String,
  step_base     UInt32,
  step_aligned  UInt32,
  prompt        String,
  word          String,
  p_base        Float32,
  p_aligned     Float32,
  delta         Float32,
  cls           LowCardinality(String),
  rule          LowCardinality(String),
  theta         Float32,
  rule_version  UInt8
) ENGINE = MergeTree ORDER BY (kind, step_aligned, prompt, word)
"""


def rung(step):
    return "%s@step%d" % (LADDER, step)


def pairs():
    """-> [(kind, base_model, aligned_model, step_base, step_aligned)]"""
    out = [("base_rooted", BASE, rung(s), 0, s) for s in STEPS]
    out += [("increment", rung(a), rung(b), a, b)
            for a, b in zip(STEPS, STEPS[1:])]
    return out


def build(kind, bm, am, sb, sa):
    """One pair -> rows, using the SAME arithmetic as `produce_movement`."""
    PM._RV["v"] = RULE_VERSION          #: selects the v3 residual path in _arm
    P, rp = PM._arm(bm)
    Q, rq = PM._arm(am)
    rows, refused = [], 0
    for prompt in set(P) & set(Q):
        if prompt not in rp or prompt not in rq:
            refused += 1
            continue
        #: NaN check, kept from the producer: a NaN residual passes an ingest
        #: gate that only rejects nulls, and poisons the null downstream
        if rp[prompt] != rp[prompt] or rq[prompt] != rq[prompt]:
            refused += 1
            continue
        mv = movement(P[prompt], Q[prompt], rule=CANONICAL,
                      residual_pre=rp[prompt], residual_post=rq[prompt])
        fall, rise = set(mv.fallers), set(mv.risers)
        for w, d in mv.delta.items():
            #: EXACT match, never a prefix. `w.startswith("__")` silently deletes
            #: `____`/`______`, the blank-fill template tokens that ARE the OLMo
            #: genre-collapse finding. Caught upstream by a ledger that would not
            #: close; the lesson travels with the code.
            if w == RESIDUAL_KEY:
                continue
            rows.append({
                "kind": kind, "base": bm, "aligned": am,
                "step_base": sb, "step_aligned": sa,
                "prompt": prompt, "word": w,
                "p_base": float(P[prompt].get(w, 0.0)),
                "p_aligned": float(Q[prompt].get(w, 0.0)),
                "delta": float(d),
                "cls": "faller" if w in fall else
                       ("riser" if w in rise else "still"),
                "rule": CANONICAL.name, "theta": CANONICAL.theta,
                "rule_version": RULE_VERSION,
            })
    return rows, refused


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--limit", type=int, help="first N pairs only, for a smoke")
    a = ap.parse_args(argv)

    ps = pairs()
    if a.limit:
        ps = ps[:a.limit]
    if a.plan:
        print("%d pairs: %d base_rooted + %d increment | rule_version %d -> %s"
              % (len(ps), sum(1 for p in ps if p[0] == "base_rooted"),
                 sum(1 for p in ps if p[0] == "increment"), RULE_VERSION, TABLE))
        for k, bm, am, sb, sa in ps[:3] + ps[-2:]:
            print("   %-12s %-38s -> %-38s" % (k, bm.split("/")[-1][:38],
                                               am.split("/")[-1][:38]))
        return 0
    if a.check:
        r = ch.query("SELECT kind, count() n, countDistinct(step_aligned) steps, "
                     "countDistinct(prompt) np FROM {db}.%s GROUP BY kind" % TABLE)
        for x in r:
            print("  %-12s %10d rows | %2d steps | %5d prompts"
                  % (x["kind"], x["n"], x["steps"], x["np"]))
        return 0
    if not a.run:
        ap.error("pass --plan, --run or --check")

    ch.execute(DDL)
    done = {(x["kind"], x["step_aligned"])
            for x in ch.query("SELECT DISTINCT kind, step_aligned FROM {db}.%s"
                              % TABLE)}
    print("%d pairs | %d already built | rule_version %d"
          % (len(ps), len(done), RULE_VERSION), flush=True)
    t0 = time.time()
    for i, (kind, bm, am, sb, sa) in enumerate(ps, 1):
        if (kind, sa) in done:
            continue
        rows, refused = build(kind, bm, am, sb, sa)
        if rows:
            ch.insert(TABLE, rows)
        print("  [%2d/%d] %-12s step %5d -> %5d  %8d rows  %d refused  (%.1f min)"
              % (i, len(ps), kind, sb, sa, len(rows), refused,
                 (time.time() - t0) / 60), flush=True)
    print("\ndone -> %s" % TABLE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
