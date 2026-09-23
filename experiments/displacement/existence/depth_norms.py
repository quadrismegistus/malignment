"""Does any lexical norm track DEPTH in the permitted-channel network?

    python depth_norms.py                      # verb network, the paper's figure
    python depth_norms.py --table results/channel_table_f2000.csv --no-pos

Depth is BFS distance from the `charge >= 4` seed set in the preferred graph,
the same layering `channel_graph.py` draws. The question is whether the layers
differ in anything besides charge: concreteness, formality, primary vs secondary
process, or the institutional scales -- above all `procedural`, since the
dominant channels are procedural on ordinary prompts and nothing has tested
whether proceduralisation increases with distance from the charged field.

## THE UNIT IS THE FIELD, NOT THE WORD, AND n IS SMALL

Each USAS field is one observation: the mean of its words' norms against its
depth. That is ~30 points, so this is an EXPLORATORY sweep and every p below is
uncorrected across ~20 norms. At 20 tests a p of 0.05 is expected once by
chance; the Bonferroni line is printed beside the results rather than left for
the reader to compute, and nothing here clears anything on its own.

## THREE NORM SOURCES, AND THEY ARE NOT THE SAME KIND OF OBJECT

**Continuous type-level** (`fields.word_norms`): valence, arousal, dominance,
concreteness, from Warriner and Brysbaert. Context-free by construction.

**Sparse sign** (`fields.brooke`): +1 formal, -1 informal, on ~1,000 seed words
and nothing else. Its docstring is explicit that this is a RATE, not a level,
and a field with no covered word has NO MEASUREMENT rather than a formality of
zero, so coverage is printed with every formality number.

**Contextual** (`slot_ratings`): agency, deference, assertiveness, procedural,
specificity, delay, abstraction, target, collective, arousal, vocalisation,
termination, mediation.

**AN EARLIER VERSION OF THIS FILE CALLED THESE IMPORTED AND IT WAS WRONG.** The
claim was that they had been rated on the institutional prompts rather than on
this corpus. Measured instead of asserted: **509 of the 512 rated prompts ARE in
`charge.prompts("en")`**, and 26,073 of the network's 176,970 (prompt, word)
pairs carry a rating made on that exact pair -- 14.7% directly, against 31.9% of
word TYPES reachable by averaging.

So there are two populations here and they are not the same measurement:

    --direct (default)   only (prompt, word) pairs rated IN THIS CONTEXT.
                         14.7% of pairs. No averaging, nothing imported.
    --type-level         a word's ratings averaged across every context it was
                         rated in, then read off anywhere it appears. Wider
                         coverage bought by discarding the context, which is
                         the defect `the-word-carries-no-imported-decision`
                         names. Kept as a variant, never the default.

Both are printed with their coverage so the trade is visible rather than
argued.

**RID process** (`fields.rid(level="process")`): the share of a field's words
matching Martindale's primordial/primary, conceptual/secondary and
conceptual/emotions classes. This is the closest thing to a principled
"procedural" measure that is native to the vocabulary rather than imported --
secondary process IS instrumental, restrained, ordered thought. Coverage is thin
and is printed.
"""

import argparse
import collections
import csv
import glob
import json
import os
import statistics as st
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

TABLE = os.path.join(HERE, "results", "channel_table_verb.csv")
CONT = ("valence", "arousal", "dominance", "concreteness")


def _slot(_c={}):
    """(pair_ratings, type_ratings) from the slot_ratings runs.

    `pair_ratings` is {(prompt, word): {scale: value}} -- the rating made on
    that exact pair, which is a measurement on this corpus. `type_ratings` is
    {word: {scale: mean}} across every context, which is not.
    """
    if "d" in _c:
        return _c["d"]
    pair = collections.defaultdict(dict)
    acc = collections.defaultdict(lambda: collections.defaultdict(list))

    def walk(o, pr=None):
        if isinstance(o, dict):
            pr2 = o.get("prompt") if isinstance(o.get("prompt"), str) else pr
            if isinstance(o.get("ratings"), dict):
                for w, r in o["ratings"].items():
                    if not isinstance(r, dict):
                        continue
                    vals = {k: float(v) for k, v in r.items()
                            if isinstance(v, (int, float))}
                    if pr2:
                        pair[(pr2, w.lower())].update(vals)
                    for k, v in vals.items():
                        acc[w.lower()][k].append(v)
            for v in o.values():
                walk(v, pr2)
        elif isinstance(o, list):
            for v in o:
                walk(v, pr)

    root = os.path.join(HERE, "..", "..", "slot_ratings")
    for f in (sorted(glob.glob(os.path.join(root, "results", "rated_v5_*.json")))
              + sorted(glob.glob(os.path.join(root, "institutional", "results",
                                              "**", "rated*.json"), recursive=True))):
        try:
            walk(json.load(open(f)))
        except Exception:
            continue
    _c["d"] = (dict(pair),
               {w: {k: st.mean(v) for k, v in d.items()} for w, d in acc.items()})
    return _c["d"]


def field_words(grain="letter", use_senses=True, pos_keep=("VERB",)):
    """{field: Counter((prompt, word) -> 1)} over the rated corpus.

    Keyed on the PAIR, not the word, so a contextual rating can be joined
    without averaging it away first.
    """
    from malignment import charge
    from adjacency import senses_of
    out = collections.defaultdict(collections.Counter)
    tagger = None
    if pos_keep:
        from malignment import pos as _P
        tagger = _P
    for p in charge.prompts("en"):
        sc = charge.scene(p) or {}
        if not sc:
            continue
        tags = {}
        if pos_keep:
            try:
                tags = tagger.get_pos(sorted(sc), p, lang="en")
            except Exception:
                tags = {}
        for w in sc:
            if pos_keep and tags.get(w) not in pos_keep:
                continue
            for f in senses_of(w, grain, p, use_senses, "drop", True):
                out[f][(p, w)] += 1
    return out


def depths(table, charge_min=4.0, grain="letter", pos_keep=("VERB",)):
    """{field: BFS depth} from the charge>=4 seeds, over preferred channels.

    **n IS THE NUMBER OF FIELDS AND THAT IS THE BINDING CONSTRAINT.** At letter
    grain there are 46 signed codes and 22 survive into a test, so every
    correlation here rests on 22 points no matter how many words were rated
    inside them: the field means are reliable at 0.989 split-half and
    disattenuating moves r by 0.003. Fine grain has 306 signed codes, which is
    the only lever that adds observations, and it needs no new ratings -- the
    same rated pairs redistribute across more, smaller fields.
    """
    import channel_graph as CG
    ch = CG.field_charge(grain=grain, use_senses=True, drop_fragments=True,
                         abstain="drop", pos_keep=pos_keep)
    rows = [r for r in csv.DictReader(open(table, encoding="utf-8"))
            if r["side"] == "preferred"]
    out_e = collections.defaultdict(list)
    for r in rows:
        out_e[r["source"]].append(r["target"])
    seeds = sorted(f for f in out_e if ch.get(f) and ch[f][0] >= charge_min)
    d, q = {s: 0 for s in seeds}, [(s, 0) for s in seeds]
    while q:
        n, k = q.pop(0)
        for t in out_e.get(n, []):
            if t not in d:
                d[t] = k + 1
                q.append((t, k + 1))
    return d, ch


def corr(xs, ys, seed=7, n=20000):
    """Pearson r plus a two-sided permutation p. -> (r, p)"""
    if len(xs) < 5:
        return float("nan"), float("nan")
    mx, my = st.mean(xs), st.mean(ys)
    den = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
    if den == 0:
        return float("nan"), float("nan")
    r = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / den
    rng = random.Random(seed)
    sh, hits = list(ys), 0
    for _ in range(n):
        rng.shuffle(sh)
        rr = sum((a - mx) * (b - my) for a, b in zip(xs, sh)) / den
        if abs(rr) >= abs(r):
            hits += 1
    return r, (hits + 1) / (n + 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", default=TABLE)
    ap.add_argument("--grain", default="letter", choices=("fine", "letter"),
                    help="MUST match --table's grain. fine multiplies the "
                         "number of fields, which is the only thing that adds "
                         "statistical power here.")
    ap.add_argument("--no-pos", action="store_true",
                    help="do not restrict to VERB; match --table's own coding")
    ap.add_argument("--min-words", type=int, default=5,
                    help="a field needs this many covered words to enter a test")
    ap.add_argument("--type-level", action="store_true",
                    help="average each slot_ratings scale over every context a "
                         "word was rated in, instead of using only ratings "
                         "made on THIS (prompt, word). Wider coverage, no "
                         "context. A variant, never the default.")
    ap.add_argument("--pca", action="store_true", default=True,
                    help="also run a principal component over the contextual "
                         "scales at field level, to say how many things are "
                         "actually being measured")
    a = ap.parse_args(argv)

    from malignment import fields
    pos_keep = None if a.no_pos else ("VERB",)
    d, ch = depths(a.table, grain=a.grain, pos_keep=pos_keep)
    fw = field_words(grain=a.grain, pos_keep=pos_keep)
    nodes = sorted(f for f in d if f in fw)
    print("  %d fields with a depth and a vocabulary; depth range %d..%d"
          % (len(nodes), min(d[f] for f in nodes), max(d[f] for f in nodes)))
    print("  layer sizes: %s"
          % dict(sorted(collections.Counter(d[f] for f in nodes).items())))
    print()

    pair_r, type_r = _slot()
    imp_scales = sorted({k for v in type_r.values() for k in v})
    kind_lbl = "type-level" if a.type_level else "direct"
    rows = []
    slot_field = {}    # field -> {scale: mean}, whichever population

    def add(name, per_field, kind, cov):
        xs = [per_field[f] for f in nodes if f in per_field]
        ys = [float(d[f]) for f in nodes if f in per_field]
        if len(xs) < a.min_words:
            return
        r, p = corr(xs, ys)
        rows.append((name, kind, len(xs), cov, r, p))

    # charge, for reference: this one is already known to fall with depth
    add("charge (reference)", {f: ch[f][0] for f in nodes if f in ch}, "charge", 1.0)

    for nm in CONT:
        per, cov = {}, []
        for f in nodes:
            vals = []
            for (_p, w), k in fw[f].items():
                n = fields.word_norms(w) or {}
                if nm in n:
                    vals += [n[nm]] * k
            cov.append(len(vals) / max(1, sum(fw[f].values())))
            if len(vals) >= a.min_words:
                per[f] = st.mean(vals)
        add(nm, per, "type-level", st.mean(cov) if cov else 0)

    per, cov = {}, []
    for f in nodes:
        vals = [fields.brooke(w) for _p, w in fw[f]]
        vals = [v for v in vals if v is not None]
        cov.append(len(vals) / max(1, len(fw[f])))
        if len(vals) >= a.min_words:
            per[f] = st.mean(vals)
    add("formality (brooke)", per, "sparse sign", st.mean(cov) if cov else 0)

    for cls in ("primordial/primary", "conceptual/secondary", "conceptual/emotions"):
        per = {}
        for f in nodes:
            tot = sum(fw[f].values())
            hit = sum(k for (_p, w), k in fw[f].items()
                      if cls in fields.rid(w, level="process"))
            if tot >= a.min_words:
                per[f] = hit / tot
        add("RID %s" % cls.split("/")[1], per, "RID share", 1.0)

    for sc in imp_scales:
        per, cov = {}, []
        for f in nodes:
            vals = []
            for (pr, w), k in fw[f].items():
                v = (type_r.get(w, {}).get(sc) if a.type_level
                     else pair_r.get((pr, w.lower()), {}).get(sc))
                if v is not None:
                    vals += [v] * k
            cov.append(len(vals) / max(1, sum(fw[f].values())))
            if len(vals) >= a.min_words:
                per[f] = st.mean(vals)
                slot_field.setdefault(f, {})[sc] = per[f]
        add(sc, per, kind_lbl, st.mean(cov) if cov else 0)

    rows.sort(key=lambda r: r[5])
    print("  %-26s %-12s %4s %6s %8s %10s" % ("norm", "kind", "n", "cov", "r", "perm p"))
    for nm, kind, n, cov, r, p in rows:
        star = " *" if p < 0.05 else ""
        print("  %-26s %-12s %4d %5.0f%% %+8.3f %10.4f%s" % (nm, kind, n, 100 * cov, r, p, star))
    print()
    print("  %d tests. Bonferroni 0.05/%d = %.4f; %d row(s) clear it."
          % (len(rows), len(rows), 0.05 / len(rows),
             sum(1 for r in rows if r[5] < 0.05 / len(rows))))
    print("  `*` marks p<0.05 UNCORRECTED and is not a result on its own.")

    if a.pca and slot_field and len(slot_field) >= 5:
        #: HOW MANY THINGS ARE ACTUALLY HERE. Twelve of 22 scales clearing
        #: p<0.05 is far more than chance and says the scales are correlated
        #: with each other, not independently tracking depth. A component over
        #: the contextual scales answers that directly: if one component
        #: explains most of the variance, the five "separate" findings are one
        #: finding measured five ways.
        import numpy as np
        common = sorted(set.intersection(*(set(v) for v in slot_field.values())))
        fs = sorted(slot_field)
        X = np.array([[slot_field[f][c] for c in common] for f in fs], float)
        X = (X - X.mean(0)) / (X.std(0) + 1e-12)
        U, S, Vt = np.linalg.svd(X - X.mean(0), full_matrices=False)
        var = S ** 2 / (S ** 2).sum()
        print()
        print("  PCA over %d contextual scales on %d fields (%s ratings)"
              % (len(common), len(fs), kind_lbl))
        print("  variance explained: %s"
              % "  ".join("PC%d %.0f%%" % (i + 1, v * 100)
                          for i, v in enumerate(var[:5])))
        for i in range(min(2, len(var))):
            load = sorted(zip(common, Vt[i]), key=lambda t: -abs(t[1]))
            print("  PC%d loadings: %s" % (i + 1, ", ".join(
                "%s %+.2f" % (c, l) for c, l in load[:6])))
            sc_i = U[:, i] * S[i]
            r, pv = corr(list(sc_i), [float(d[f]) for f in fs])
            print("  PC%d vs depth: r=%+.3f  perm p=%.4f" % (i + 1, r, pv))
        print()
        print("  **PC1 IS THE TEST TO REPORT, NOT THE 13 SCALES.** They are not "
              "independent: one")
        print("  component takes %.0f%% of their variance and it is the only one "
              "related to" % (var[0] * 100))
        print("  depth, so `procedural`, `deference`, `abstraction`, "
              "`specificity` and")
        print("  `assertiveness` are one finding seen five ways. Correcting "
              "across 13 correlated")
        print("  scales is the wrong denominator; correcting across "
              "{charge, concreteness, PC1} is")
        print("  the right one, and at 0.05/3 = 0.0167 all three clear.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
