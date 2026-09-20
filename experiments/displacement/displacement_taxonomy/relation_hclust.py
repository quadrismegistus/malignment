"""Cluster the named relations by their base and aligned scores on the norms.

    python -u relation_hclust.py                     -> figure + results/relation_clusters.md
    python -u relation_hclust.py --institutional     adds that battery, n falls 88 -> 77
    python -u relation_hclust.py -k 8

## THE POINT: GROUPING WITHOUT A READER

Six agent regroupings of the 907 gave 28 to 200 groups and the count was a
property of the reader. The names are the reason -- `RESULTS_interrater.md`
measured raters agreeing on WHICH WORDS carry a difference at Jaccard 0.80
while "demonstrably need not" agreeing on what to call it, and the six
`Three ___ came into the room` frames reproduced it exactly: six names, one
relation.

So this groups on the MEASURED CONTRAST instead. Each relation is a vector of
what its two word lists score on every instrument, base and aligned kept as
separate features -- a relation running 6.4 -> 2.3 on charge is not the same
object as one running 3.1 -> 1.0, and a delta alone cannot tell them apart.

## THE REPLICATE FRAMES ARE AN ACCEPTANCE TEST, AND THEY COST NOTHING

The battery contains near-duplicate prompts: six `Three ___ came into the
room`, `The cop pinned her/him`, three `so angry/furious ... wanted to`. They
are the same relation by construction, so any grouping that splits them is
wrong INDEPENDENTLY OF ANYONE'S JUDGEMENT. That is the criterion the 907
exercise never had, and it is why six runs of it could disagree with no way to
call any of them worse. Reported at every k, not just the chosen one.

## FEATURES, SCALING AND WHY WARD

48 features: base and aligned for `task_charge`, the eleven lexical scales and
the twelve `v6` contextual scales. **Every column is z-scored first**, because
Warriner runs 1-9, Brysbaert 1-5 and the rest 1-7, and Euclidean distance on
raw values would weight a scale by its range. Ward linkage because the
question is "which relations are alike overall", not "which chain into each
other" -- single linkage on 88 points in 48 dimensions chains almost
everything into one group.

**COMPLETE CASES ONLY, NO IMPUTATION.** 88 of 93 relations carry `v6_*` (all
twelve scales on all 88 -- the battery is not ragged), 89 carry a contextual
charge, and the lexical scales are complete on 92. Imputing a norm would put a
made-up value into the distance that decides the grouping.

## WHAT THIS IS NOT

**Not a taxonomy of alignment operations.** The relations were written by a
reader told to find the CLEAREST contrast and to drop any word that would force
a hedge, so the vectors describe what separates the words a reader chose. A
cluster is a family of measured contrasts, not a family of things alignment
does.
"""
import argparse, collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import norm_shift as NS

#: paths carry the configuration. A default name shared by four runs is how a
#: level-mode figure ends up captioned as a delta-mode one.
def _paths(mode, strict):
    tag = "%s%s" % (mode, "_strict" if strict else "")
    return (os.path.join(HERE, "figures", "relation_hclust_%s.png" % tag),
            os.path.join(HERE, "results", "relation_clusters_%s.md" % tag))

LEX = [k for k, _ in __import__("relation_sheet").LEX]
V6 = ["v6_aggression", "v6_deliberation", "v6_directedness", "v6_fit",
      "v6_harm", "v6_hedged", "v6_interiority", "v6_makes_better",
      "v6_makes_worse", "v6_mundanity", "v6_superego", "v6_vocalisation"]
INST = ["slot_institutional_en_v3_" + s for s in
        ("abstraction", "agency", "arousal", "assertiveness", "collective",
         "deference", "delay", "mediation", "procedural", "specificity",
         "target", "termination", "vocalisation")]

#: near-duplicate prompts: the same relation by construction, so a grouping
#: that splits one of these is wrong on evidence rather than on taste
REPLICATES = [("Three ___ came into the room", r"^Three \w+ came into the room"),
              ("The cop pinned her/him", r"^The cop pinned (her|him)"),
              ("so angry / so furious", r"so (furious|angry) (he|she) wanted")]


def _pair(r, k, kind):
    if kind is None:
        return r["charge_base"], r["charge_aligned"]
    if kind == "lex":
        return r["base"].get(k), r["aligned"].get(k)
    v = r.get("ctx", {}).get(k)
    return (v[0], v[1]) if v else (None, None)


def _ok(v):
    return v is not None and v == v


def matrix(rs, strict=False, mode="level"):
    """-> (relations, feature names, 2-D list, notes)

    **THE POPULATION IS CHOSEN FIRST AND THE FEATURES SECOND.** RH, 2026-09-20:
    the 77 relations carrying BOTH contextual batteries. Requiring every scale
    instead let the WARRINER columns pick the population -- they are missing on
    12 relations, more than either battery drops, so a complete-case rule over
    everything silently selected on lexicon coverage and left 74. A scale that
    decides who is in the sample is not a feature, it is a filter.

    So: relations = those with all of `v6` and all of the institutional
    battery. Features = those 25 scales, plus `task_charge` and any lexical
    scale that is complete ON THAT SET. Anything incomplete there is dropped
    as a FEATURE and named, rather than dropping relations to keep it.
    """
    core = [(k, "ctx") for k in V6] + [(k, "ctx") for k in INST]
    #: `--strict`: require EVERY family -- lexical, task_charge, v6 and the
    #: institutional battery. Costs relations rather than features, which is
    #: the opposite trade and has to be paid for with a replicate family.
    if strict:
        core = core + [("charge", None)] + [(k, "lex") for k in LEX]
    sel = [r for r in rs if all(_ok(_pair(r, k, t)[0]) and _ok(_pair(r, k, t)[1])
                                for k, t in core)]
    extra, dropped = [], []
    for k, t in [("charge", None)] + [(k, "lex") for k in LEX]:
        if all(_ok(_pair(r, k, t)[0]) and _ok(_pair(r, k, t)[1]) for r in sel):
            extra.append((k, t))
        else:
            n = sum(1 for r in sel if not (_ok(_pair(r, k, t)[0])
                                           and _ok(_pair(r, k, t)[1])))
            dropped.append("%s (missing on %d of %d)" % (k, n, len(sel)))
    scales = core + extra
    if mode == "delta":
        #: **THE RELATION IS THE DELTA; THE LEVEL IS THE FRAME.**
        #: RH, 2026-09-20: "you're clustering the prompts". Correct, and it
        #: invalidated both acceptance tests as I had them. base/aligned LEVELS
        #: are dominated by what a frame is ABOUT -- a sexual frame scores high
        #: on charge on both sides -- so the six `Three ___` prompts grouped
        #: because they share a vocabulary, and the gender-swapped twins were
        #: mutual nearest neighbours because they are the same sentence. Both
        #: tests were confirming that near-duplicate PROMPTS have near-duplicate
        #: norms, which is true by construction and says nothing about whether
        #: the grouping found relations.
        #:
        #: Differencing removes the frame's level and leaves what the relation
        #: DID. The discriminating test then becomes the one that was never
        #: available under levels: do frames with different subject matter but
        #: the same relation land together.
        X = [[_pair(r, k, t)[1] - _pair(r, k, t)[0] for k, t in scales]
             for r in sel]
        feats = [k + "|delta" for k, _ in scales]
    else:
        X = [[v for k, t in scales for v in _pair(r, k, t)] for r in sel]
        feats = [k + s for k, _ in scales for s in ("|base", "|aligned")]
    return sel, feats, X, dropped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all-words", action="store_true")
    ap.add_argument("--mode", choices=("level", "delta"), default="delta",
                    help="delta clusters the RELATION (what moved); level "
                         "clusters the FRAME (what it is about)")
    ap.add_argument("--strict", action="store_true",
                    help="require lexical AND task_charge AND v6 AND institutional")
    ap.add_argument("-k", type=int, default=6, help="clusters to cut at")
    ap.add_argument("--fig", default=None)
    ap.add_argument("--list", action="store_true", help="print the frames kept")
    ap.add_argument("--dpi", type=int, default=300)
    #: the producer writes both copies in one run, as `relation_sheet` does, so
    #: a repo figure and a paper figure cannot drift into being different
    #: pictures under one name
    ap.add_argument("--also", default=None,
                    help="write a second copy of the figure here")
    ap.add_argument("--md", default=None)
    a = ap.parse_args(argv)
    dfig, dmd = _paths(a.mode, a.strict)
    a.fig, a.md = a.fig or dfig, a.md or dmd

    import numpy as np
    from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
    from scipy.spatial.distance import pdist, squareform
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rs = NS.rows(NS.ALLWORDS if a.all_words else NS.CONTENT, want_ctx=True)
    names, feats, X, dropped = matrix(rs, a.strict, a.mode)
    if dropped:
        print("features dropped as incomplete on this population: %s"
              % "; ".join(dropped))
    X = np.asarray(X, float)
    print("%d relations x %d features (%d scales, mode=%s)"
          % (X.shape[0], X.shape[1],
             X.shape[1] if a.mode == "delta" else X.shape[1] // 2, a.mode))
    #: z-scored per column: Warriner is 1-9, Brysbaert 1-5, the rest 1-7, and
    #: Euclidean distance on raw values would weight a scale by its range
    sd = X.std(axis=0)
    keep = sd > 0
    if not keep.all():
        print("dropped %d constant feature(s): %s"
              % ((~keep).sum(), ", ".join(f for f, k in zip(feats, keep) if not k)))
    Z = (X[:, keep] - X[:, keep].mean(axis=0)) / sd[keep]
    link = linkage(Z, method="ward", metric="euclidean")
    from scipy.cluster.hierarchy import cophenet
    coph, _ = cophenet(link, pdist(Z))
    print("cophenetic correlation %.3f" % coph)

    print("\nREPLICATE TEST -- same relation by construction, must not split")
    print("%-4s %s" % ("k", " ".join("%-34s" % lab for lab, _ in REPLICATES)))
    best = None
    for k in range(2, 13):
        lab = fcluster(link, k, criterion="maxclust")
        cells, score = [], 0
        for _nm, pat in REPLICATES:
            idx = [i for i, r in enumerate(names) if re.search(pat, r["frame"])]
            born = sum(1 for r in rs if re.search(pat, r["frame"]))
            cl = collections.Counter(lab[i] for i in idx)
            together = max(cl.values()) if cl else 0
            score += together - len(idx)
            #: `n of m in sample` is printed because an earlier version said
            #: "1 of 1 together" for the cop pair -- a PASS -- when one of the
            #: two had been filtered out upstream. A replicate family that
            #: loses members cannot test anything and must not read as a pass.
            cells.append("%d/%d together (%d of %d in sample)"
                         % (together, len(idx), len(idx), born))
        print("%-4d %s  (penalty %d)" % (k, " ".join("%-34s" % c for c in cells), -score))
        if best is None or score > best[1]:
            best = (k, score)
    print("\nbest replicate agreement at k=%d" % best[0])

    #: **A SECOND ACCEPTANCE TEST, FREE AND STRICTER THAN CLUSTER MEMBERSHIP.**
    #: The battery contains gender-swapped twins -- "She unzipped his" against
    #: "He unzipped her" -- found here by normalising pronouns rather than by a
    #: hand list, so the test cannot be tuned to pass. Two frames that differ
    #: only in who does it should be each other's NEAREST NEIGHBOUR in the
    #: feature space, which is a far harder bar than landing in one cluster of
    #: twenty. Visible in the dendrogram as adjacent leaves; measured here so
    #: it is not read off a picture.
    PRON = [(r"\bshe\b", "_S"), (r"\bhe\b", "_S"), (r"\bher\b", "_O"),
            (r"\bhis\b", "_O"), (r"\bhim\b", "_O"), (r"\bhers\b", "_O")]

    def skel(f):
        t = f.lower()
        for pat, rep in PRON:
            t = re.sub(pat, rep, t)
        return t

    twins = collections.defaultdict(list)
    for i, r in enumerate(names):
        twins[skel(r["frame"])].append(i)
    twins = {k: v for k, v in twins.items() if len(v) == 2}
    if twins:
        D = squareform(pdist(Z))
        np.fill_diagonal(D, np.inf)
        hit = sum(1 for (i, j) in twins.values()
                  if D[i].argmin() == j and D[j].argmin() == i)
        one = sum(1 for (i, j) in twins.values()
                  if D[i].argmin() == j or D[j].argmin() == i)
        print("\nGENDER-SWAPPED TWIN TEST (pronoun-normalised, not a hand list)")
        print("  %d twin pairs among the %d relations" % (len(twins), len(names)))
        print("  mutual nearest neighbours: %d of %d" % (hit, len(twins)))
        print("  nearest in at least one direction: %d of %d" % (one, len(twins)))
        print("  chance for a mutual pair is about 1 in %d" % (len(names) - 1))

    if a.list:
        print("\nTHE %d FRAMES IN THIS SUBSET" % len(names))
        for r in sorted(names, key=lambda r: r["frame"]):
            print("   %s" % r["frame"])

    lab = fcluster(link, a.k, criterion="maxclust")
    fig, ax = plt.subplots(figsize=(11, max(9, 0.22 * len(names))))
    lbl = ([r["name"][:54] for r in names] if a.mode == "delta"
           else [r["frame"][:46] for r in names])
    dendrogram(link, labels=lbl, orientation="left",
               color_threshold=link[-(a.k - 1), 2], ax=ax, leaf_font_size=6)
    ax.set_title("%s\n%d relations, %d features, Ward on z-scored columns"
                 % ("Relations clustered by what MOVED (delta on every norm)"
                    if a.mode == "delta" else
                    "Frames clustered by base and aligned norm LEVELS",
                    X.shape[0], int(keep.sum())), fontsize=9)
    ax.set_xlabel("Ward distance", fontsize=8)
    fig.tight_layout()
    os.makedirs(os.path.dirname(a.fig), exist_ok=True)
    for path in [a.fig] + ([a.also] if a.also else []):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fig.savefig(path, dpi=a.dpi)
        print("wrote %s (%d dpi)" % (path, a.dpi))

    groups = collections.defaultdict(list)
    for i, r in enumerate(names):
        groups[lab[i]].append(r)
    L = ["# Relations clustered by measured contrast, not by name", "",
         "%d relations, %d features (base and aligned on %d scales), Ward linkage "
         "on z-scored columns, cut at k=%d. Cophenetic correlation %.3f."
         % (len(names), int(keep.sum()), X.shape[1] // 2, a.k, coph), "",
         "The names below were written by blind readers and are NOT what grouped "
         "these — they are printed so a cluster can be read. Six frames that are "
         "the same relation by construction got six different names, which is why "
         "the grouping runs on the numbers.", ""]
    for c in sorted(groups):
        g = groups[c]
        L.append("## Cluster %d — %d relations" % (c, len(g)))
        L.append("")
        L.append("| frame | relation | charge base → aligned |")
        L.append("|---|---|---|")
        for r in sorted(g, key=lambda r: r["frame"]):
            cb, ca = r["charge_base"], r["charge_aligned"]
            ch = ("%.2f → %.2f" % (cb, ca)) if cb is not None else "not rated"
            L.append("| %s | %s | %s |"
                     % (r["frame"][:60], r["name"][:60], ch))
        L.append("")
    open(a.md, "w", encoding="utf-8").write("\n".join(L))
    print("wrote %s (%d clusters)" % (a.md, len(groups)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
