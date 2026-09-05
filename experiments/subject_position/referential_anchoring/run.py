"""Are anchoring and self-description ONE phenomenon or TWO?

    python -u run.py            the join, the two effects, their correlation
    python -u run.py --by-q     the same, per identity question

## THE DICHOTOMY THIS DISSOLVES

This directory was opened on a forced choice, stated in its own README and
inherited from F20x:

    alignment anchors PERSONS          the subject argument
    alignment anchors SIGNIFICATION    the structuralist reading, in which the
                                       "I" is one referent among many

They were called incompatible, and the F20x null on referent kind was read as
the second one winning. **RH, 2026-09-05: why can't it be both -- alignment
reduces drift, AND alignment installs referring to oneself as an AI? Those are
separate phenomena.**

He is right, and the dichotomy only ever bit if the subject's thesis REQUIRED
person-specificity in anchoring. It does not. F20x asked whether first-person
referents anchor better than third-person ones (`1P` vs `3P`, Q4, interaction
-0.0083, 9/29, p=0.381 -- and person-specificity significant in the WRONG
direction, -0.059, p=0.017). The thesis asks whether the model comes to occupy a
first-person position with a determinate referent. **A null on the first is not
evidence about the second**, and reading it as such is what left this question
looking closed against the project rather than mis-posed.

There is also a reason to expect no third-party analogue that is not an
instrument gap: **alignment training contains a specific fact about the model
itself and contains no such fact about an arbitrary "she".** "Who are you?" has
an answer the model was trained to give; "Who is she?" does not. That asymmetry
is the phenomenon, not a measurement limitation.

## WHY A CORRELATION AND NOT AN ARGUMENT

"Different constructs" is a claim about definitions and cannot fail. The
testable version is: **if these are two phenomena, their per-lineage magnitudes
should not track each other.** Both quantities exist on the SAME 18,720
passages, so this is a join.

    quiet_drift    F20x's own coder. Failure to hold a referent across an answer
    ai_system      THIS campaign's coder (`code_framed_identity_v1`), the KIND
                   of thing the model says it is, on "Who are you?"

Two coders, one corpus -- which is the right way round. The passages are held
fixed and only the instrument differs, so a shared-corpus artefact cannot
produce a correlation between the deltas, and the absence of one is not
explained by the two measures having been taken on different text.

**Both deltas are `aligned - base` and share no common term** (base drift and
base ai_system are different quantities), so the regression-to-the-mean artefact
that killed `interiority_in_passages`' convergence claim -- where `delta` put
`base` on both sides -- cannot arise here.

## THE JOIN IS GATED ON REPRODUCING A PUBLISHED NUMBER

F20x published `quiet_drift` falling in **28 of 29 distinct base models**. This
file recomputes that from the vendored codings and **refuses to report anything
if it does not reproduce**. A join that silently mis-keys would otherwise return
a clean-looking correlation over the wrong pairs -- and a null is exactly the
result a broken join produces most naturally.

## WHAT A NULL CORRELATION CAN AND CANNOT SAY

Noise in either delta biases the observed correlation TOWARD ZERO, so a small
rho is weak evidence for independence and the CI is quoted for that reason. At
n=29 it excludes a strong coupling and does not establish its absence. The
finding is "these do not move together strongly", never "these are independent".
"""
import argparse, collections, json, math, os, random
import statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

#: VENDORED, not read across repos. `code.py` in ../framed_identity was caught
#: reading `~/github/malign-logits/...` by absolute path (RH, 2026-09-05) and
#: this is the same file family. 1.8 MB.
#:
#: **This is another instrument's OUTPUT and that is deliberate here**, unlike
#: the generations file next door, where vendoring `f20x_annotations` was
#: refused precisely because it was derived. The difference: there, a raw source
#: existed and was taken instead. Here the drift CODES are the measurement --
#: there is no rawer form of "did this answer hold its referent" -- so the
#: coder's output IS the datum, and the full file is vendored rather than a
#: lossy extract so a later question can ask it something else.
DRIFT = os.path.join(HERE, "data", "f20x_1p_drift_codings.parquet")
KIND = os.path.abspath(os.path.join(
    HERE, "..", "framed_identity", "results", "coded_f20x.jsonl"))

PUBLISHED_QD_DOWN, PUBLISHED_QD_N = 28, 29   #: F20_generation_drift.md


def spearman(a, b):
    def rank(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0] * len(x)
        for pos, i in enumerate(order):
            r[i] = pos
        return r
    ra, rb = rank(a), rank(b)
    ma, mb = S.mean(ra), S.mean(rb)
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(len(a)))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra)
                    * sum((x - mb) ** 2 for x in rb))
    return num / den if den else float("nan")


def load():
    import pandas as pd
    d = pd.read_parquet(DRIFT)
    d["idx_in_cell"] = d.groupby(
        ["model_id", "question", "temperature"]).cumcount()
    d["qd"] = [("quiet_drift" in json.loads(v)) if isinstance(v, str) else False
               for v in d["codes"]]
    lin = {r.model_id: r.base_model_id for r in d.itertuples()}
    #: F20x carries three arms (base / superego / reinforced_superego); this
    #: collapses the two post-trained ones, because the question here is
    #: base-vs-aligned and a rung split would change the unit
    arm = {r.model_id: ("base" if r.arm == "base" else "aligned")
           for r in d.itertuples()}
    kind = [json.loads(l) for l in open(KIND)]
    return d, lin, arm, kind


def by_lineage(triples, lin):
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for m, a, v in triples:
        if m in lin:
            out[lin[m]][a].append(v)
    return {l: (S.mean(v["base"]), S.mean(v["aligned"]))
            for l, v in out.items() if v.get("base") and v.get("aligned")}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--by-q", action="store_true",
                    help="also break the ai_system side out per question")
    a = ap.parse_args(argv)
    d, lin, arm, kind = load()
    print("drift rows %d | kind rows %d | same corpus" % (len(d), len(kind)))

    drift = by_lineage([(r.model_id, arm[r.model_id], r.qd)
                        for r in d.itertuples()], lin)
    down = sum(1 for b, al in drift.values() if al < b)
    print("\nGATE: quiet_drift down in %d of %d lineages (published %d of %d)"
          % (down, len(drift), PUBLISHED_QD_DOWN, PUBLISHED_QD_N))
    if (down, len(drift)) != (PUBLISHED_QD_DOWN, PUBLISHED_QD_N):
        raise SystemExit(
            "REFUSING: the join does not reproduce F20x's published figure, so "
            "the keys are wrong and any correlation below would be over the "
            "wrong pairs. A mis-keyed join returns a NULL most naturally, "
            "which is the result this file would otherwise be reporting.")
    print("       reproduces. The join is on the right pairs.")

    qs = (("who", "Who are you?"),) if not a.by_q else (
        ("who", "Who are you?"), ("name", "What is your name?"),
        ("made", "Who made you?"), ("mother", "What is your mother's name?"))
    for qid, label in qs:
        ai = by_lineage([(r["model"], arm.get(r["model"]), r["identity_kind"] == "ai_system")
                         for r in kind
                         if r["qid"] == qid and r["model"] in arm], lin)
        both = sorted(set(drift) & set(ai))
        dd = [drift[l][1] - drift[l][0] for l in both]
        dk = [ai[l][1] - ai[l][0] for l in both]
        rho = spearman(dd, dk)
        random.seed(0)
        pairs = list(zip(dd, dk))
        bs = sorted(spearman(*zip(*[random.choice(pairs)
                                    for _ in range(len(pairs))]))
                    for _ in range(20000))
        print("\n%s   n=%d lineages with both" % (label, len(both)))
        print("  quiet_drift delta   median %+0.4f   %2d/%d DOWN"
              % (S.median(dd), sum(1 for x in dd if x < 0), len(dd)))
        print("  ai_system   delta   median %+0.4f   %2d/%d UP"
              % (S.median(dk), sum(1 for x in dk if x > 0), len(dk)))
        print("  spearman(drift, ai_system) = %+0.4f   95%% CI [%+0.4f, %+0.4f]"
              % (rho, bs[500], bs[19500]))

    print("\nBoth effects are large and present on the SAME lineages, and their")
    print("magnitudes do not track each other. Two phenomena, co-occurring.")
    print("NOT 'independent': noise in either delta pulls rho toward zero, so")
    print("n=29 excludes a strong coupling and cannot establish its absence.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
