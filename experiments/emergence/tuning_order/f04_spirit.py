"""F04's claim in its own shape: does a CHARGED faller fall before an UNCHARGED riser rises?

    python -u f04_spirit.py

**DISCOVERED ARM.** Not in `REGISTRATION.md`. RH, 2026-09-06, after Q1 and Q3:
*"We want to know whether high scene/transgressive fallers fall before low
scene/untransgressive risers rise."* Labelled per the registration's soft-border
rule (§0) -- reported, not suppressed, and not citable as a surviving prediction.

## WHY THIS IS NOT Q1 OR Q3

Q1 selected BOTH words by |delta| and asked which moved earlier. Q3 kept that
selection and moderated by the faller's charge. **Neither is F04's structure.**
F04's claim is a JOINT condition on the pair: a charged word is barred and an
UNCHARGED substitute arrives -- `fuck` -> `kiss`, `kill` -> `scream`. The pair is
what carries the claim, so the pair is what must be selected.

    faller   the HIGHEST-scene faller in the prompt
    riser    the LOWEST-scene riser in the prompt
    gap      scene(faller) - scene(riser)   > 0 required

**The gap is what makes it DISPLACEMENT rather than movement.** Mass leaving a
charged word for an equally charged one is not what F04 described.

## scene OR scene-frame? IT DOES NOT MATTER HERE

Within a prompt the frame is a constant, so ranking words by `scene` and by
`scene - frame` gives the IDENTICAL ordering, and the gap is frame-independent
because the frame cancels. The distinction only bites across prompts, and nothing
here compares raw scene across prompts.

## WHAT WOULD FALSIFY IT

If charged-faller/uncharged-riser pairs show no earlier departure than the Q1
pairs did, then F04's ordering is not about charge at all -- which is what Q3
already suggested, and this is the sharper test of it.
"""
import collections, json, math, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from malignment import ch                                          # noqa: E402
from analyse import curves, auc, binom, ci, END                    # noqa: E402

ANN = os.path.join(HERE, "results", "charge_olmo_thinksft_v3.jsonl")


def rated():
    """-> {prompt: {word: scene}}, and the frame per prompt."""
    sc, fr = {}, {}
    with open(ANN) as fh:
        for line in fh:
            r = json.loads(line)
            sc[r["prompt"]] = {w["word"]: w["scene"] for w in r["words"]}
            fr[r["prompt"]] = r["frame"]
    return sc, fr


def pairs(min_gap=1):
    """-> per prompt, (highest-scene faller, lowest-scene riser) with a gap."""
    sc, fr = rated()
    q = ("SELECT prompt, word, delta, cls FROM {db}.movement_rungs "
         "WHERE kind='base_rooted' AND step_aligned=%d AND cls IN ('faller','riser') "
         "AND prompt IN (SELECT DISTINCT prompt FROM {db}.prompts WHERE prompt != '')"
         % END)
    by = collections.defaultdict(lambda: {"faller": [], "riser": []})
    for r in ch.query(q):
        if r["prompt"] in sc and r["word"] in sc[r["prompt"]]:
            by[r["prompt"]][r["cls"]].append((r["word"], sc[r["prompt"]][r["word"]]))
    out = []
    for p, d in by.items():
        if not d["faller"] or not d["riser"]:
            continue
        #: ties broken by |delta| order from the query, which is arbitrary --
        #: so break them deterministically on the word instead
        fw, fs = max(sorted(d["faller"]), key=lambda x: x[1])
        rw, rs = min(sorted(d["riser"]), key=lambda x: x[1])
        if fs - rs >= min_gap:
            out.append((p, fw, fs, rw, rs, fr[p]))
    return out


def main():
    print("DISCOVERED ARM -- not registered. F04's pair structure.")
    print()
    for gap in (1, 2, 3):
        pr = pairs(gap)
        if len(pr) < 5:
            print("  gap >= %d : n=%d, too few" % (gap, len(pr)))
            continue
        cv = curves([(p, fw) for p, fw, _, _, _, _ in pr]
                    + [(p, rw) for p, _, _, rw, _, _ in pr])
        rows = []
        for p, fw, fs, rw, rs, frm in pr:
            fa, ri = auc(cv.get((p, fw), {})), auc(cv.get((p, rw), {}))
            if fa and ri:
                rows.append((fa[0] - ri[0], fa[0], ri[0], fs, rs, p, fw, rw))
        if len(rows) < 5:
            continue
        d = [x[0] for x in rows]
        up = sum(1 for v in d if v > 0)
        lo, hi = ci(d)
        print("  CHARGE GAP >= %d   n=%d prompts" % (gap, len(rows)))
        print("    faller scene median %.1f | riser scene median %.1f"
              % (S.median([x[3] for x in rows]), S.median([x[4] for x in rows])))
        print("    faller AUC %.4f | riser AUC %.4f" %
              (S.median([x[1] for x in rows]), S.median([x[2] for x in rows])))
        print("    DIFF median %+0.4f   %d up/%d dn   p=%.6f   CI [%+0.4f, %+0.4f]"
              % (S.median(d), up, len(d) - up,
                 binom(min(up, len(d) - up), len(d)), lo, hi))
        print()
        if gap == 2:
            print("    the pairs at gap >= 2:")
            print("    %-30s %-10s %-10s %5s %5s" %
                  ("prompt", "faller", "riser", "fAUC", "rAUC"))
            for x in sorted(rows, key=lambda z: -(z[3] - z[4]))[:16]:
                print("    %-30s %-10s %-10s %5.2f %5.2f"
                      % (x[5].replace("\n", " ")[:30], x[6][:10], x[7][:10],
                         x[1], x[2]))
            print()
    print("  Compare Q1 (both words chosen by |delta|, no charge condition):")
    print("    n=505  DIFF +0.0910  329/176  p<1e-6  CI [+0.0671, +0.1115]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
