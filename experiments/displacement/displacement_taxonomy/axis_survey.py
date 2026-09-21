"""Score every relation on EVERY axis, graded, instead of assigning it to one.

    python -u axis_survey.py --smoke --n 20

## WHY THIS EXISTS

The 38-axis annotation asked each reader for "the single best-fitting axis", so
every relation carries a value on one axis and NOTHING on the other 37 -- 2,466
filled cells of 93,708, 2.6%. That is a partition, not a loading matrix: its
components recover the partition, and because membership of one axis forbids
membership of another, every pair of columns is negatively correlated BY
CONSTRUCTION. RH asked whether one or two factors lie behind the axes and the
honest answer was that the question had been asked of the wrong object.

`Survey` fixes both halves structurally rather than by a better prompt.

    COVERAGE   `build_questions` is per item and the response is keyed by the
               questions sent; `_complete()` refuses an answer set that drops,
               invents or duplicates a key. 38 questions in, 38 answers out.
               The matrix is dense because the key set is the contract.
    DEGREE     `Score` is "a position on ordered levels, probability-weighted
               ... it can fall BETWEEN levels, which is the point: a continuous
               measure with no threshold anywhere". `kill, murder, stab ->
               scream, shout` and `pushed -> leaned` stop being one answer.

## THE WORDS ARE THE SHOWN LIST, NOT THE PLACED LIST (RH)

Three populations were on offer: the words task 1 PLACED (`words_a`/`words_b`),
the words task 1 was SHOWN, and the base arm's full mass distribution.

Measured before choosing: task 1 placed every word it was shown on **1,893 of
2,466** relations (76.8%), dropping 2,810 words of ~37,700 in total, about 7%.
So the first two populations are nearly the same and the contamination argument
for preferring the shown list is weak.

The reason to prefer it anyway is that **the shown list has a stateable
inclusion rule** -- the words at least `MIN_AGREE` of fifty pairs moved -- and
the placed list's rule is "the words a DeepSeek coder chose to place". For 7%
more tokens the population can be written down.

The base arm's full mass distribution is a DIFFERENT EXPERIMENT and is not used
here: it is dominated by words that never moved, so asking which pole they sit
on answers what the base model favours, not what alignment changed.

**ATTESTATION TRAVELS WITH EACH WORD.** A word 39 of 50 pairs moved is not the
same evidence as one at 15, and neither the placed nor the shown list knows
that on its own. The counts are rendered beside the words so the rater can
weight them; it is the nearest thing available to the mass weighting the base
distribution would have given.

## BLINDED THE SAME WAY

`LIST 1` and `LIST 2`, order drawn per relation by `relation_group_input.flip`.
A rater told which side fell can answer from what it knows about alignment
without consulting the words. Direction is restored afterwards, by arithmetic.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "tasks")):
    if p not in sys.path:
        sys.path.insert(0, p)

#: five levels, symmetric, with the middle one meaning "this axis does not
#: separate them" -- the `unclear` of the assignment run, but now a POSITION
#: rather than a refusal, so it carries into a factor model instead of
#: dropping the row.
LEVELS = [
    "LIST 1 is clearly and wholly at the first pole, LIST 2 clearly at the second",
    "LIST 1 leans to the first pole and LIST 2 to the second, with exceptions on both sides",
    "the two lists do not separate on this contrast at all: either both sit at the same pole, or each straddles it",
    "LIST 2 leans to the first pole and LIST 1 to the second, with exceptions on both sides",
    "LIST 2 is clearly and wholly at the first pole, LIST 1 clearly at the second",
]


def vocabulary(seed=1):
    d = os.path.join(HERE, "results", "grouping_seed%d" % seed)
    return json.load(open(os.path.join(d, "vocabulary.json"), encoding="utf-8"))


def build(seed=1):
    from largeliterarymodels.survey import Survey
    from largeliterarymodels.questions import Score
    axes = vocabulary(seed)["axes"]

    class AxisSurvey(Survey):
        name = "relation_axes_v1"
        #: **OFF BY DEFAULT, AND A RUN WITHOUT A RECEIPT CANNOT BE COSTED.**
        #: The first smoke produced no usage log at all, so "what would 2,466
        #: relations cost" had no answer from the run that was supposed to
        #: answer it.
        usage_log = True

        def build_questions(self, item):
            qs = {}
            for a in axes:
                qs[a["id"]] = Score(
                    instructions=(
                        "Contrast: %s. The first pole is: %s. The second pole "
                        "is: %s. Do the two word lists separate on this "
                        "contrast, and if so which list sits at which pole? "
                        "Judge only from the words. Most contrasts will not "
                        "apply to most pairs; say so rather than forcing one."
                        % (a["definition"], a["pole_x"], a["pole_y"])),
                    criteria=LEVELS)
            return qs

        def build_state(self, item):
            st = {"fragment": item["frame"],
                  "list_1": item["list_1"], "list_2": item["list_2"]}
            if item.get("counts_are"):
                st["the number after each word is"] = item["counts_are"]
            return st

    return AxisSurvey(), axes


def attestation(frames):
    """{frame: {word: (this, n_pairs)}} -- how many pairs moved each word.

    **PARSED OUT OF `PT.table`'s OWN RENDERING, NOT RE-DERIVED.** The raw
    counter is a triple whose order depends on the column, and reading it
    directly means encoding that rule a second time. `pooled_relations.ROW` is
    the parser `shown()` already trusts to say what a rater was handed, so the
    counts shown here are by construction the counts task 1 was shown.
    """
    import pooled_tables as PT
    from pooled_relations import ROW, blind_for, SEED
    out = {}
    got = PT.pooled_many(list(frames), PT.MIN_AGREE)
    for f, v in got.items():
        if not v:
            continue
        cnt, n = v
        txt, _ = PT.table(cnt, 20, blind=blind_for(f, SEED))
        out[f] = ({m.group(1): int(m.group(2)) for m in ROW.finditer(txt)}, n)
    return out


def items(n=0, seed=1, frame=None, counts=True):
    """Relations as blinded two-list states, with attestation counts."""
    from relation_group_input import flip
    src = os.path.join(HERE, "results", "relations_for_grouping.jsonl")
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    rows = [r for r in rows if r["lang"] == "en"]
    if frame:
        rows = [r for r in rows if frame.lower() in r["frame"].lower()]
        if not rows:
            raise SystemExit("no frame matches %r" % frame)
    if n:
        step = max(1, len(rows) // n)
        rows = rows[::step][:n]
    att = attestation({r["frame"] for r in rows}) if counts else {}
    out = []
    for r in rows:
        #: **THE ATTESTATION TRAVELS WITH THE WORD** (RH). `kill` at 39 of 50
        #: pairs and a word at 15 read identically without it, and the rater
        #: was being asked to weigh a contrast it could not see the evidence
        #: for. This is the nearest available stand-in for the mass weighting
        #: the base arm's own distribution would give.
        a_c, n_p = att.get(r["frame"], ({}, None))
        def _fmt(ws):
            if not a_c:
                return ", ".join(ws)
            return ", ".join("%s (%s)" % (w, a_c[w]) if w in a_c else w
                             for w in ws)
        b, a = _fmt(r["base"]), _fmt(r["aligned"])
        one, two = (a, b) if flip(r["id"], seed) else (b, a)
        it = {"id": r["id"], "frame": r["frame"],
              "list_1": one, "list_2": two}
        if n_p:
            it["counts_are"] = ("how many of %d model pairs moved that word "
                                "into its own list" % n_p)
        out.append(it)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--show", action="store_true")
    #: a cached item returns no usage, so a costing run must force
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--frame", default=None, help="substring of one frame")
    #: **THE DEFAULT BREAKER KILLED A 2,244-ITEM RUN ON A TRANSIENT OUTAGE.**
    #: `fail_fast=5` aborts when the first five completions all fail; TypeSafe
    #: returned "no healthy upstream" for about a minute and the run stopped
    #: after 28 billed attempts. The breaker's own message says to check the
    #: inference, and the check was: the same item succeeded on retry minutes
    #: later, with and without the counts. A RATE breaker tolerates a blip and
    #: still stops a genuine outage, which is what the guard is for.
    ap.add_argument("--no-counts", action="store_true",
                    help="omit the attestation counts (the pre-RH state)")
    a = ap.parse_args(argv)

    sv, axes = build(a.seed)
    its = items(a.n if a.smoke else 0, a.seed, a.frame, not a.no_counts)
    print("%d relations x %d axes = %d judgements"
          % (len(its), len(axes), len(its) * len(axes)))
    if a.show:
        print(sv.state_text(its[0])[:600])
        q = sv.build_questions(its[0])
        k = sorted(q)[0]
        print("\nexample question [%s]:\n  %s" % (k, q[k].instructions[:300]))
        return 0

    import time
    t0 = time.time()
    #: the key lives in ~/.bash_profile, which a non-login shell does not read
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise SystemExit("TYPESAFE_API_KEY is not set. This key is exported by "
                         "~/.bash_profile, so run under `bash -lc`, or export "
                         "it first. Refusing to run and report zeros.")
    #: **`imap` YIELDS (index, Answers) AS EACH COMPLETES, CACHED FIRST** --
    #: not a list in input order. Zipping it against `its` pairs each answer
    #: with the wrong relation, and silently, because both are the right
    #: length. Collected by index instead.
    errs = {}
    per_item = {}
    out_by_i = {}
    for i, ans in sv.imap(its, model=a.model, num_workers=a.workers,
                          errors=errs, per_item_usage=per_item,
                          force=a.force, fail_fast={"rate": 0.5}):
        out_by_i[i] = ans
    rows, bad = [], 0
    for i, it in enumerate(its):
        ans = out_by_i.get(i)
        if ans is None:
            bad += 1
            continue
        #: **NO BARE `except` ROUND THE ANSWER READ.** The first version
        #: swallowed every failure into None and printed "20 answered, 0
        #: failed" over 760 nulls -- the run had never reached the API at all
        #: (no `TYPESAFE_API_KEY` in a non-login shell). An operation that
        #: completes without doing is the defect this repo pays for most, and
        #: a bare except is how it gets manufactured. Let it raise.
        rec = {"id": it["id"]}
        for ax in axes:
            a2 = ans[ax["id"]]
            rec[ax["id"]] = a2.value
            rec[ax["id"] + "__conf"] = getattr(a2, "confidence", None)
        rows.append(rec)
    print("%d answered, %d failed, %.0fs" % (len(rows), bad, time.time() - t0))
    if errs:
        print("errors: %s" % list(errs.items())[:2])
    tok = {}
    for it in (per_item or {}).values():
        for k, v in (it or {}).items():
            if "token" in k:
                tok[k] = tok.get(k, 0) + (v or 0)
    if tok:
        n = max(1, len(rows))
        print("usage: %s" % tok)
        print("  per relation: %s"
              % {k: round(v / n) for k, v in tok.items()})
        print("  projected for 2,244 English relations: %s"
              % {k: round(v / n * 2244) for k, v in tok.items()})
    out = os.path.join(HERE, "results", "axis_survey_en.jsonl")
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
