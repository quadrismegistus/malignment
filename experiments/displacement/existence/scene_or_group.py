"""Is the destination set determined by the SCENE or by the GROUP?

    python -u scene_or_group.py                 the 2x2
    python -u scene_or_group.py --examples      what each cell's risers look like
    python -u scene_or_group.py --out results/scene_or_group.csv

`adjacency.py --flow` (Part 4) reports the destination as ORIGIN-SPECIFIC.
**That is not the same as scene-dependence.**

(An earlier version of this line cited "the median source field has two preferred
destinations out of 306". `--flow` EMITS NO SUCH NUMBER at any flag setting -- it
was computed ad hoc over the CSV and written here as though the producer had
printed it. @malign could neither reproduce nor dispute it and correctly refused
to derive a lookalike, docket [6651]. Struck here and in existence/README.md.) The channel test conditions on
the faller's FIELD and pools across prompts -- `L1- -> Q2.2` spans 604 of them --
so it shows the destination depends on what left, at field grain, generalising
across scenes. Whether it depends on WHICH SCENE is a different question and the
one the campaign has actually been chasing.

## THE DESIGN IS A 2x2, NOT A DISTANCE

`fields.slot_prompts()` carries the identity sweep twice, and all 24 groups
appear in both scenes:

    Three <group> came into the room and started to
    The three <group> who moved in next door were

    vary GROUP, hold scene   276 pairs per scene
    vary SCENE, hold group    24 pairs

No scene-distance metric is needed or defended. The earlier plan was to regress
riser-set overlap on bge distance between prompts; this asks the same question
with a factorial the corpus already contains, which has no embedder to validate
and no threshold to choose.

## THE CONFOUND RUNS THE WRONG WAY, WHICH IS WHY THE STATISTIC IS A RESIDUAL

Same-scene pairs differ by ONE NOUN PHRASE. Same-group pairs differ by a whole
clause. So **lexical overlap predicts same-scene > same-group, and so does the
scenic hypothesis**: raw riser overlap cannot separate them, and reporting it
would be measuring string similarity and calling it scene.

Two prompts that share vocabulary are also OFFERED similar candidates, so the
control is the candidate set itself. The first version of this subtracted them:

    residual = J(risers) - J(candidates)          WRONG, AND IT INVERTED THE ANSWER

**That is a set-size artifact.** Jaccard is biased down for smaller sets and
riser sets are a fraction of the candidate sets, so J(risers) < J(candidates)
is what two RANDOM subsets of the right sizes give as well. Subtracting produced
-0.262 for same-scene pairs and a unanimous 0/50 in the direction opposite the
truth. The statistic is the departure from a SIZE-MATCHED draw instead:

    vs_null = J(risers_a, risers_b) - J(random subsets of the candidate
                                        pools, matched to each riser count)

Same pools, same set sizes, destination assignment destroyed. What survives it
is convergence the available vocabulary does not explain.

## THE VARY-SCENE ARM IS NOT A SCENE CONTRAST. IT NEVER WAS.

**Corrected 2026-09-14 after @malign reproduced this blind (docket [6650]).** The
first version of this file printed "THE VARY-SCENE ARM HAS NO POWER ... vs_null
all 0.000 by construction", which is wrong in the way that matters: it says the
comparison is too small to see an effect, when the comparison is not the one the
arm's name claims.

    ceiling on J(risers) given the real pools, median per lineage   0.2853
    ceiling, max                                                    0.9069
    same-scene arms, OBSERVED vs_null                    +0.3142, +0.3896
    median riser set                                         15 words
    median shared candidates                                  6, from 183 and 170

The observed zero is zero against a REACHABLE 0.285, in the same range as the
effect the other two arms report. So there is power. What there is not is a
controlled contrast:

    came into the room and started to ___        takes an INFINITIVE
    who moved in next door were always ___       takes a PARTICIPLE or ADJECTIVE

The 98.3% candidate disjointness IS that slot difference, and the six words
surviving into both pools are mostly beam fragments. The arm varies scene AND
grammatical category, so its zero is over-determined and no number of lineages
repairs it. Low power is a sample-size problem; this is a design problem.

**AND THE PAIRED BLOCK BELOW MEASURES NOTHING EXTRA.** Since vs_null(vary-scene)
is a CONSTANT 0 on all 50 lineages, residual(same-scene) - residual(same-group)
is residual(same-scene), verified identical to machine precision (both medians
+0.3142). The sign test that follows is therefore a one-sample test of the
same-scene arm against zero, which the arm table already reports. Its unanimity
is one arm being constant, not fifty lineages agreeing about a contrast. It is
printed with that stated rather than removed, because deleting it would hide
that the design produced it.

**NOT REPAIRABLE FROM THIS CORPUS.** `fields.slot_prompts()` holds 2,599 prompts
and exactly two identity-sweep templates. No second scene shares the `started to`
slot, so a within-slot scene contrast needs new prompts, not new analysis.

## WHAT EACH OUTCOME MEANS

    residual(same-scene) > residual(same-group)   the scene selects the destination
    residual(same-group) > residual(same-scene)   the group does; the identity
                                                  sweep's divergence is carried
                                                  by who is named, not by where
    both ~ 0                                      destinations are explained by
                                                  the candidate sets and there is
                                                  nothing scenic to find

RECORDED BEFORE THE RUN: the identity result this folder already has -- `pray`
for Muslims and Christians, `eat` for Italians and Mexicans, `dance` for
Nigerians -- predicts same-scene pairs will overlap LESS than their near-identical
strings imply, i.e. a NEGATIVE residual where the strings are most similar. If
that is what appears it is evidence for group-determination, not for scene, and
it is the outcome that would go against the reading I have been defending.

UNIT OF INFERENCE IS THE LINEAGE, as everywhere in this folder: a residual per
pair within one model, a median per model, then a sign test over models. The
pairs within a lineage are not independent -- 24 groups generate 276 pairs -- so
they are never counted as 276 observations.
"""
import argparse, collections, csv, itertools, os, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

ROOM = "came into the room and"
NEXTDOOR = "moved in next door"
_GRP = re.compile(r"(?:Three|The three)\s+(.+?)\s+(?:came into|who moved)")


def binom(k, n):
    import math
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j)
               for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def strata():
    """{group: {scene: prompt}} for the groups present in BOTH scenes. -> dict

    Restricted to the intersection on purpose: a group in only one scene cannot
    contribute to the vary-scene arm, and including it in the vary-group arm
    alone would make the two arms different populations.
    """
    from malignment import fields
    out = collections.defaultdict(dict)
    for p in fields.slot_prompts():
        scene = "room" if ROOM in p else ("nextdoor" if NEXTDOOR in p else None)
        if not scene:
            continue
        m = _GRP.search(p)
        if m:
            out[m.group(1).lower()][scene] = p
    return {g: d for g, d in out.items() if len(d) == 2}


def jaccard(a, b):
    if not a or not b:
        return None
    return len(a & b) / len(a | b)


def cells(prompts, frame="raw"):
    """{(base, aligned, prompt): (risers, candidates)} over the endpoint roster."""
    from malignment import ch, roster
    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages: %s" % sorted(unresolved)[:3])
    quoted = ", ".join("'%s'" % p.replace("'", "\\'") for p in prompts)
    out = {}
    for b, a in sorted(eps.items()):
        rows = ch.query(
            "SELECT prompt, word, cls FROM {db}.movement_v4 "
            "WHERE base='%s' AND aligned='%s' AND frame_base='' "
            "AND frame_aligned='' AND prompt IN (%s) ORDER BY prompt, word"
            % (b.replace("'", "\\'"), a.replace("'", "\\'"), quoted),
            limit_bytes=None)
        by = collections.defaultdict(lambda: [set(), set()])
        for r in rows:
            #: CANDIDATES are every word the cell holds, not only the movers:
            #: it is what the base arm put in play, which is the thing two
            #: similar prompts share for reasons that have nothing to do with
            #: where the mass then went.
            by[r["prompt"]][1].add(r["word"])
            if r["cls"] == "riser":
                by[r["prompt"]][0].add(r["word"])
        for p, (ri, ca) in by.items():
            out[(b, a, p)] = (ri, ca)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-risers", type=int, default=3,
                    help="a cell needs this many risers to enter a pair")
    ap.add_argument("--examples", action="store_true",
                    help="print the riser sets for a few cells")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    S = strata()
    groups = sorted(S)
    prompts = [p for d in S.values() for p in d.values()]
    print("identity sweep: %d groups present in BOTH scenes, %d prompts"
          % (len(groups), len(prompts)))
    print("  vary GROUP, hold scene: %d pairs per scene"
          % (len(groups) * (len(groups) - 1) // 2))
    print("  vary SCENE, hold group: %d pairs\n" % len(groups))

    C = cells(prompts)
    lineages = sorted({(b, al) for b, al, _ in C})
    print("lineages with cells: %d\n" % len(lineages))

    #: J(risers) IS SMALLER THAN J(candidates) PARTLY BY CONSTRUCTION. Jaccard
    #: is biased down for smaller sets, and riser sets are a fraction of the
    #: candidate sets, so a negative residual is exactly what two RANDOM subsets
    #: of the right sizes would also give. The null: draw subsets of the shared
    #: candidate pool matched to each cell's riser count and take their Jaccard.
    #: The residual only means anything as a departure from THAT, not from zero.
    import random as _rnd
    _rng = _rnd.Random(7)

    def size_matched_null(c1, c2, n1, n2, reps=40):
        vals = []
        l1, l2 = sorted(c1), sorted(c2)
        if n1 > len(l1) or n2 > len(l2) or not n1 or not n2:
            return None
        for _ in range(reps):
            s1 = set(_rng.sample(l1, n1))
            s2 = set(_rng.sample(l2, n2))
            j = jaccard(s1, s2)
            if j is not None:
                vals.append(j)
        return st.median(vals) if vals else None

    def resid(lin, p1, p2):
        k1, k2 = (lin[0], lin[1], p1), (lin[0], lin[1], p2)
        if k1 not in C or k2 not in C:
            return None
        (r1, c1), (r2, c2) = C[k1], C[k2]
        if len(r1) < a.min_risers or len(r2) < a.min_risers:
            return None
        jr, jc = jaccard(r1, r2), jaccard(c1, c2)
        if jr is None or jc is None:
            return None
        j0 = size_matched_null(c1, c2, len(r1), len(r2))
        if j0 is None:
            return None
        #: the fourth value is the one that means something: observed riser
        #: overlap against size-matched draws from the same candidate pools.
        return jr, jc, jr - jc, jr - j0, j0

    arms = {"same scene, vary group (room)": [],
            "same scene, vary group (next door)": [],
            "same group, vary scene": []}
    per_lin = collections.defaultdict(lambda: collections.defaultdict(list))
    for lin in lineages:
        for g1, g2 in itertools.combinations(groups, 2):
            for scene, lab in (("room", "same scene, vary group (room)"),
                               ("nextdoor", "same scene, vary group (next door)")):
                v = resid(lin, S[g1][scene], S[g2][scene])
                if v:
                    per_lin[lin][lab].append(v)
        for g in groups:
            v = resid(lin, S[g]["room"], S[g]["nextdoor"])
            if v:
                per_lin[lin]["same group, vary scene"].append(v)

    print("%-38s %9s %9s %9s %10s %8s"
          % ("arm", "J(risers)", "J(cands)", "J(null)", "vs null", "lineages"))
    print("-" * 88)
    med = {}
    for lab in arms:
        per = [tuple(st.median([x[i] for x in v[lab]]) for i in range(5))
               for v in per_lin.values() if v[lab]]
        if not per:
            print("%-38s  no pairs" % lab)
            continue
        med[lab] = [p[3] for p in per]
        print("%-38s %9.3f %9.3f %9.3f %+10.3f %8d"
              % (lab, st.median([p[0] for p in per]), st.median([p[1] for p in per]),
                 st.median([p[4] for p in per]), st.median([p[3] for p in per]),
                 len(per)))

    #: PAIRED WITHIN LINEAGE. The two arms come from the same models and the
    #: same 24 groups, so most of what varies between models is common to both
    #: and cancels; comparing two independent medians would throw that away.
    print("\nPAIRED WITHIN LINEAGE -- residual(same scene) minus residual(same group)")
    print("%-38s %10s %11s %10s" % ("comparison", "wins/n", "med diff", "p"))
    for scene_lab in ("same scene, vary group (room)",
                      "same scene, vary group (next door)"):
        d = []
        for lin, v in per_lin.items():
            if v[scene_lab] and v["same group, vary scene"]:
                d.append(st.median([x[3] for x in v[scene_lab]])
                         - st.median([x[3] for x in v["same group, vary scene"]]))
        if len(d) < 10:
            continue
        w = sum(1 for x in d if x > 0)
        print("%-38s %10s %+11.4f %10.4f"
              % (scene_lab.replace("same scene, vary group ", "scene v group "),
                 "%d/%d" % (w, len(d)), st.median(d), binom(w, len(d))))

    print("\nREADING. `vs null` is the number: observed riser overlap against "
          "size-matched\ndraws from the same candidate pools. J(risers) alone "
          "cannot be read -- same-scene\npairs differ by one noun and same-group "
          "pairs by a whole clause, so it favours\nsame-scene for lexical reasons; "
          "and J(risers) - J(cands) cannot either, because\nriser sets are "
          "smaller and Jaccard is biased down for small sets.")
    print("\nTHE VARY-SCENE ARM IS NOT A SCENE CONTRAST -- see the docstring. It "
          "is not\nunderpowered: the ceiling on J(risers) given the real pools is "
          "a median 0.285,\nthe same range as the other arms' effect. It varies "
          "SCENE AND GRAMMATICAL SLOT\n(infinitive against participle), so its "
          "zero is over-determined and more lineages\nwould not repair it.")
    print("\nAND THE PAIRED BLOCK ADDS NOTHING: vs_null(vary-scene) is a constant "
          "0, so the\ndifference IS the same-scene arm and the sign test is a "
          "one-sample test of a\nnumber already in the table above. Printed with "
          "that said rather than removed.")

    if a.examples:
        lin = lineages[0]
        print("\n--- riser sets, %s ---" % (lin[1],))
        for g in groups[:5]:
            k = (lin[0], lin[1], S[g]["room"])
            if k in C:
                print("  %-18s %s" % (g, " ".join(sorted(C[k][0]))[:78]))
    for lab, v in med.items():
        w = sum(1 for x in v if x < 0)
        print("  %-38s below its size-matched null on %d/%d lineages  p=%.4f"
              % (lab, w, len(v), binom(w, len(v))))

    if a.out:
        path = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(("base", "aligned", "arm", "j_risers", "j_candidates",
                        "residual", "j_null", "vs_null", "n_pairs"))
            for lin, v in sorted(per_lin.items()):
                for lab, xs in v.items():
                    if not xs:
                        continue
                    w.writerow((lin[0], lin[1], lab,
                                "%.4f" % st.median([x[0] for x in xs]),
                                "%.4f" % st.median([x[1] for x in xs]),
                                "%.4f" % st.median([x[2] for x in xs]),
                                "%.4f" % st.median([x[4] for x in xs]),
                                "%.4f" % st.median([x[3] for x in xs]), len(xs)))
        print("\n-> %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
