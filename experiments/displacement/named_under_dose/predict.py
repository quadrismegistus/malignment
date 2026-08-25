"""P's comparison -- named norms against a distributional embedding -- under dose.

    python -u predict.py --lang en
    python -u predict.py --lang en --draws 5 --k 50
    python -u predict.py --lang zh --encoders bge

Held out by WORD. Every model is scored against ITS OWN SHUFFLE, which is P's
metric, and the increment is expressed as a share of the headroom over base
probability. Reproduces P's table shape on our corpus, then splits it by dose.

## FOUR THINGS P'S RECORD SAYS WILL GO WRONG, AND WHAT IS DONE ABOUT EACH

1. **THE METRIC IS MODEL-MINUS-ITS-OWN-SHUFFLE.** P's 7% / 19% / 17% are each
   model's AUC minus the same model refit on SHUFFLED features, as a share of the
   headroom. `analyse.py` in this folder used `named+p` minus `log p_base`, a
   different numerator, so the norms row is RECOMPUTED here rather than carried
   across. Do not put an analyse.py number next to a predict.py number.

2. **HistGradientBoosting IS OpenMP-NONDETERMINISTIC.** Five identical
   invocations in P returned +0.0256, +0.0223, +0.0216, +0.0218, +0.0231 -- a
   spread of 0.0040 on a mean of 0.0229 -- and an earlier version of P's table
   quoted the top of that range. `--draws` defaults to 5 and the table prints
   mean and range; a single tree draw is never quoted. Logistic is byte-identical
   across runs and is printed beside it as the deterministic anchor, which is how
   P localised the cause.

3. **REPORT BOTH TERMS OF EVERY INCREMENT.** P caught a widening-gap artifact in
   Chinese where the logistic increment climbed +0.0221 -> +0.0788 across a k
   sweep while the real model was nearly flat (0.6406 -> 0.6536) and the SHUFFLE
   collapsed (0.6185 -> 0.5748). An increment that grows because both of its terms
   fall is not a model getting better. Real and shuffled AUC are both in the table.

4. **THE ENCODERS ARE NOT INTERCHANGEABLE AND ONE IS WEAK.** `embed.py` gates them
   on bare words: GloVe +0.400, bge-m3 en +0.138, bge-m3 zh +0.319. English leads
   with GloVe. GloVe has no Chinese, so a zh/bge number must never be set beside an
   en/GloVe one.

## THE HEADROOM

`emp_word` -- a word's majority direction from its OTHER cells -- is the reachable
word-level benchmark, and `log p_base` is the floor P measures headroom over. P's
headroom was +0.1207 with an ICC of 0.131: **82-87% of the fall/rise variance is
WITHIN a word across sites**, so a word-level theory tops out near AUC 0.70 by
construction. Nothing here can exceed that and a model near it has not failed.

## POPULATION

P ran on lexical verbs. This runs on all words by default and on verbs with
`--verbs-only`, which is the comparable population; both are printed when POS is
available, because the difference between them is a fact worth seeing rather than
a choice to bury.
"""

import argparse, collections, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
DATA = os.path.expanduser("~/malignment-data/named_under_dose")

DROP = {"lineage", "prompt", "word", "lang", "dose", "direction",
        "p_base", "p_aligned", "k_coverage", "brysbaert_coverage",
        "warriner_coverage", "n_tokens", "n_content",
        "concreteness_zh_coverage", "n_words"}


def auc(y, s):
    import numpy as np
    y = np.asarray(y); s = np.asarray(s, float)
    pos, neg = s[y > 0], s[y < 0]
    if not len(pos) or not len(neg):
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    r = np.empty(len(s), float)
    sv = s[order]
    i = 0
    while i < len(sv):
        j = i
        while j + 1 < len(sv) and sv[j + 1] == sv[i]:
            j += 1
        r[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return (r[y > 0].sum() - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def load(lang):
    p = os.path.join(DATA, "cells_%s.csv.gz" % lang)
    rows = []
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        feats = [k for k in head if k not in DROP]
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head) or v[ix["lang"]] != lang:
                continue
            try:
                d, y, pb = (float(v[ix["dose"]]), int(v[ix["direction"]]),
                            float(v[ix["p_base"]]))
            except ValueError:
                continue
            x, ok = [], True
            for k in feats:
                sv = v[ix[k]]
                if sv == "":
                    ok = False
                    break
                try:
                    x.append(float(sv))
                except ValueError:
                    ok = False
                    break
            rows.append((v[ix["word"]], d, y, pb, x if ok else None,
                         v[ix["prompt"]]))
    return rows, feats


def fit(X, y, groups, folds, kind, seed, shuffle=False, cell_keys=None):
    """Held-out-by-word predictions. -> pooled AUC."""
    import numpy as np
    rng = np.random.default_rng(seed)
    if shuffle and cell_keys is not None:
        #: CELL-LEVEL FEATURES NEED A CELL-LEVEL SHUFFLE. A contextual rating
        #: varies by (prompt, word), so permuting the WORD->feature link would
        #: assign one word's whole rating profile everywhere and destroy far more
        #: than the correspondence. Permute the (prompt, word) -> rating map
        #: instead: the marginal distribution of ratings is preserved exactly and
        #: only which cell gets which rating is destroyed.
        uk = sorted(set(cell_keys))
        perm = rng.permutation(len(uk))
        rep = {uk[i]: uk[perm[i]] for i in range(len(uk))}
        first = {}
        for k_, xi in zip(cell_keys, X):
            first.setdefault(k_, xi)
        X = np.array([first[rep[k_]] for k_ in cell_keys], float)
    elif shuffle:
        #: SHUFFLE THE WORD->FEATURE LINK, not the rows: the same permutation is
        #: applied to every cell of a word, so a shuffled model keeps the exact
        #: marginal structure and loses only the correspondence. Shuffling rows
        #: would also destroy the within-word repetition and make the null easy.
        uw = sorted(set(groups))
        perm = rng.permutation(len(uw))
        rep = {uw[i]: uw[perm[i]] for i in range(len(uw))}
        first = {}
        for g, xi in zip(groups, X):
            first.setdefault(g, xi)
        X = np.array([first[rep[g]] for g in groups], float)

    uw = sorted(set(groups))
    order = np.random.default_rng(seed).permutation(len(uw))
    fold_of = {uw[order[i]]: i % folds for i in range(len(uw))}
    f = np.array([fold_of[g] for g in groups])
    pred = np.zeros(len(y), float)
    for k in range(folds):
        tr, te = f != k, f == k
        if tr.sum() < 100 or te.sum() < 20:
            continue
        if kind == "logistic":
            from sklearn.linear_model import LogisticRegression
            mdl = LogisticRegression(max_iter=300, C=1.0)
        else:
            from sklearn.ensemble import HistGradientBoostingClassifier
            mdl = HistGradientBoostingClassifier(
                max_iter=100, learning_rate=0.1, random_state=seed)
        mdl.fit(X[tr], (y[tr] > 0).astype(int))
        pred[te] = mdl.predict_proba(X[te])[:, 1]
    return auc(y, pred)


def block(title, rows, feats, EMB, a, note=""):
    import numpy as np
    globals()["_SHARED"] = None
    print("\n" + "=" * 100)
    print("  %s%s" % (title, note))
    print("=" * 100)
    #: SUBSAMPLE IS DECLARED AND SEEDED. Uniform over cells, so the word-frequency
    #: profile is preserved; a per-word cap would change the estimand silently.
    if a.max_cells and len(rows) > a.max_cells:
        sel = np.random.default_rng(20260825).choice(len(rows), a.max_cells, replace=False)
        rows = [rows[i] for i in sorted(sel)]
        print("  SUBSAMPLED to %d cells (seeded, uniform)" % len(rows))
    words = [r[0] for r in rows]
    y = np.array([r[2] for r in rows], float)
    pb = np.log(np.clip(np.array([r[3] for r in rows], float), 1e-12, None))

    by = collections.defaultdict(lambda: [0, 0])
    for wi, yi in zip(words, y):
        by[wi][0] += yi
        by[wi][1] += 1
    emp = np.array([(by[w][0] - yi) / max(1, by[w][1] - 1) for w, yi in zip(words, y)])
    #: THE FLOOR IS A FITTED MODEL, NOT A RAW COLUMN. Scored raw, log p_base
    #: returned AUC 0.4151 -- ANTI-predictive, because low-probability words tend
    #: to rise and high-probability ones to fall. Treating 0.4151 as the floor says
    #: base probability carries no information when it carries a great deal with
    #: the sign flipped, and it inflated the headroom from ~0.095 to 0.265, which
    #: deflated every "% of headroom" by about 2.8x. Fitting it through the SAME
    #: held-out pipeline every model gets orients it by construction and satisfies
    #: this campaign's own rule: score the benchmark with the identical function
    #: the models are scored by.
    a_emp = auc(y, emp)
    a_p = fit(pb.reshape(-1, 1), y, words, a.folds, "logistic", 20260825)
    head = a_emp - a_p
    print("  cells %d | words %d | %.0f%% risers" % (len(y), len(set(words)), 100 * (y > 0).mean()))
    print("  emp_word (reachable) %.4f   log p_base FITTED %.4f (raw %.4f)   "
          "HEADROOM %+.4f" % (a_emp, a_p, auc(y, pb), head))
    print("\n  %-16s %5s %9s %9s %11s %9s  %s"
          % ("model", "dims", "real", "shuffled", "increment", "% headr", "draws"))

    def row(name, X, mask, keys=None):
        Xm, ym, gm = X[mask], y[mask], [w for w, m in zip(words, mask) if m]
        km = [k for k, m in zip(keys, mask) if m] if keys is not None else None
        if len(set(gm)) < 20 or len(ym) < 200:
            print("  %-16s  too few (%d cells, %d words)" % (name, len(ym), len(set(gm))))
            return
        for kind, nd in (("logistic", 1), ("trees", a.draws)):
            reals, shufs = [], []
            for d in range(nd):
                reals.append(fit(Xm, ym, gm, a.folds, kind, 20260825 + d,
                                 cell_keys=km))
                shufs.append(fit(Xm, ym, gm, a.folds, kind, 20260825 + d,
                                 shuffle=True, cell_keys=km))
            inc = [r - s for r, s in zip(reals, shufs)]
            mi = float(np.mean(inc))
            rng_s = ("%d, %+.4f..%+.4f" % (nd, min(inc), max(inc))) if nd > 1 else "1"
            print("  %-16s %5d %9.4f %9.4f %+11.4f %8.0f%%  %s"
                  % ("%s/%s" % (name, kind), Xm.shape[1], float(np.mean(reals)),
                     float(np.mean(shufs)), mi,
                     100 * mi / head if head > 1e-9 else float("nan"), rng_s))

    #: CONTEXTUAL NORMS -- the named vocabulary asked AT THE SITE. P's ICC of
    #: 0.131 says 82-87% of a word's rise/fall variance is WITHIN the word across
    #: sites, which a word-level feature cannot reach by construction. This is the
    #: named counterpart of P's section 3b: same vocabulary, cell-level grain.
    if a.contextual:
        from malignment import fields as F
        keys = [(r[5], r[0]) for r in rows]
        if getattr(a, "match_population", False):
            print("  --match-population: every model restricted to the shared cells")
        #: which prompts were rated WHEN. rated_v6_nn_* are the pilot3 originals,
        #: rated_v6_en_*/rated_v6zh_* are this session's dose-selected tiers.
        import glob as _g, json as _j
        src = {}
        for _f in _g.glob(os.path.join(HERE, "..", "..", "slot_ratings",
                                       "results", "*", "rated_*.json")):
            tag = "tier2" if "_en_" in os.path.basename(_f) or "_zh_" in os.path.basename(_f) \
                  else "original"
            try:
                for _r in _j.load(open(_f, encoding="utf-8")):
                    if isinstance(_r, dict) and _r.get("prompt"):
                        src.setdefault(_r["prompt"], tag)
            except Exception:
                continue
        cache = {}
        for pr in {k[0] for k in keys}:
            if a.ctx_source != "all" and src.get(pr) != a.ctx_source:
                cache[pr] = {}
                continue
            try:
                cache[pr] = F.contextual_norms(pr)
            except Exception:
                cache[pr] = {}
        if a.ctx_source != "all":
            print("  --ctx-source %s: %d of %d prompts kept"
                  % (a.ctx_source, sum(1 for v in cache.values() if v), len(cache)))
        #: AN EXPLICIT ALLOWLIST, NOT WHATEVER THE FIRST RECORD EXPOSED.
        #: `_slot_index` admits EVERY numeric field, and the pre-existing v6 files
        #: store the movement outcome beside the ratings -- v6_net, v6_rise,
        #: v6_fall, v6_net_rate. Taking the scale set from the first record sampled
        #: was an undeclared choice that returned 12 clean scales by luck in one run
        #: and 14 in another; a record carrying v6_net would have had the model
        #: predict direction FROM direction.
        V6 = ["harm", "aggression", "directedness", "makes_better", "makes_worse",
              "interiority", "deliberation", "superego", "vocalisation", "hedged",
              "fit", "mundanity"]
        scales = ["%s_%s" % (a.contextual, s) for s in V6]
        #: and refuse anything outcome-shaped, so a future scale name cannot slip in
        BAD = ("net", "rise", "fall", "eligible", "present", "lineage", "consist")
        leak = [s for s in scales if any(t in s for t in BAD)]
        if leak:
            sys.exit("refusing: outcome-derived keys in the scale set: %s" % leak)
        seen = {k for d in cache.values() for dd in d.values() for k in dd}
        missing = [s for s in scales if s not in seen]
        if missing:
            print("  contextual/%s: %d of %d scales absent (%s) -- skipping"
                  % (a.contextual, len(missing), len(scales), ", ".join(missing[:3])))
            scales = None
        if scales:
            Xc = np.zeros((len(rows), len(scales)))
            mc = np.zeros(len(rows), bool)
            for i, (pr, w_) in enumerate(keys):
                dd = cache.get(pr, {}).get(w_)
                if dd and all(sc in dd for sc in scales):
                    Xc[i] = [float(dd[sc]) for sc in scales]
                    mc[i] = True
            print("  contextual/%s: %d scales, %d of %d cells rated (%.1f%%)"
                  % (a.contextual, len(scales), int(mc.sum()), len(rows),
                     100.0 * mc.sum() / max(1, len(rows))))
            if getattr(a, "match_population", False):
                #: THE INTERSECTION IS THE POPULATION. Computed before any row is
                #: printed so no model is ever scored on cells another lacks.
                shared = mc.copy()
                shared &= np.array([r[4] is not None for r in rows])
                for _e, (_v, _E) in EMB.items():
                    shared &= np.array([w in _v for w in words])
                print("  shared cells across ctx + norms + %s: %d"
                      % ("+".join(EMB), int(shared.sum())))
                mc = shared
            if mc.sum() > 200:
                row("ctx_" + a.contextual, Xc, mc, keys)
                if getattr(a, "match_population", False):
                    globals()["_SHARED"] = mc
        else:
            print("  contextual/%s: no scales found" % a.contextual)

    #: BUILD THE MATRIX OVER ALL ROWS, THEN MASK. Intersecting `have` with the
    #: shared population while still filling from `[r for r in rows if r[4]]`
    #: mismatched 93,122 values into an 18,810-row slot -- numpy caught it, but a
    #: mask and its value array must be derived from the same predicate.
    notnone = np.array([r[4] is not None for r in rows])
    Xn = np.zeros((len(rows), len(feats)))
    if notnone.any():
        Xn[notnone] = np.array([r[4] for r in rows if r[4] is not None], float)
    have = notnone
    if globals().get("_SHARED") is not None:
        have = have & globals()["_SHARED"]
    if have.any():
        row("norms", Xn, have)
    for enc, (vocab, E) in EMB.items():
        idx = np.array([vocab.get(w, -1) for w in words])
        m = idx >= 0
        if globals().get("_SHARED") is not None:
            m = m & globals()["_SHARED"]
        if not m.any():
            continue
        Xe = np.zeros((len(rows), E.shape[1]), np.float32)
        Xe[m] = E[idx[m]]
        if a.k and a.k < E.shape[1]:
            #: reduce to k dims on the FITTING population only would leak across
            #: folds; P swept k as a model hyperparameter, so the SVD is over the
            #: feature matrix and is unsupervised -- it never sees y.
            U, S, Vt = np.linalg.svd(Xe[m] - Xe[m].mean(0), full_matrices=False)
            Xr = np.zeros((len(rows), a.k), np.float32)
            Xr[m] = (Xe[m] - Xe[m].mean(0)) @ Vt[:a.k].T
            Xe = Xr
        row(enc, Xe, m)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", choices=("en", "zh"))
    ap.add_argument("--encoders", default=None, help="comma list; default all found")
    ap.add_argument("--k", type=int, default=50, help="SVD dims, P's headline k=50")
    ap.add_argument("--draws", type=int, default=5,
                    help="tree draws; OpenMP makes a single one unquotable")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--min-cells", type=int, default=10)
    ap.add_argument("--content-only", action="store_true",
                    help="drop known function words (bare-word spaCy, coarse)")
    ap.add_argument("--ctx-source", default="all",
                    choices=("all", "original", "tier2"),
                    help="WHICH RATED PROMPTS. Tier-2 ratings were commissioned at "
                         "top-quartile dose, so with --ctx-source all the rating "
                         "coverage is CORRELATED WITH DOSE (21.8%% low vs 63.6%% "
                         "high) and a low-vs-high contrast confounds dose with "
                         "which prompt sample got rated. 'original' restricts to "
                         "prompts rated BEFORE any dose-based selection, where "
                         "coverage cannot be dose-correlated -- underpowered on the "
                         "high side, but unconfounded.")
    ap.add_argument("--match-population", action="store_true",
                    help="restrict EVERY model to the cells where all feature sets "
                         "are available. Without it each model is masked to its own "
                         "coverage and the rows are not comparable: ctx_v6 runs on "
                         "the 13%% of cells at rated prompts, which are the 276 "
                         "frames someone chose to build an instrument for, not a "
                         "random subset.")
    ap.add_argument("--contextual", default=None,
                    help="instrument prefix for fields.contextual_norms, e.g. v6. "
                         "Ratings made AT THE SITE, so the same word gets different "
                         "values at different prompts -- the only feature class that "
                         "can reach the 82-87%% of variance P's ICC puts WITHIN a "
                         "word. Restricts to rated prompts; see slot_prompts().")
    ap.add_argument("--verbs-only", action="store_true",
                    help="P'S POPULATION. Keeps a cell only where the word is a "
                         "VERB *at that slot*, via pos.get_pos(words, prompt), "
                         "which is contextual: `table` is VERB after \"he wanted "
                         "to\" and NOUN after \"on the\". Bare-word spaCy cannot "
                         "do this -- it calls `strangle` a NOUN -- and without the "
                         "restriction the norms partly proxy POS, which is why an "
                         "all-words run puts them at 72%% of headroom against P's "
                         "7%%.")
    ap.add_argument("--max-cells", type=int, default=150000,
                    help="uniform seeded subsample per block. P ran on 100,958 "
                         "cells; ours is 1.18M and 5 folds x 5 draws x real+shuffle "
                         "x 3 models does not fit. DECLARED, not silent: the n "
                         "actually used is printed in every block header.")
    a = ap.parse_args(argv)
    import numpy as np

    rows, feats = load(a.lang)
    if a.verbs_only:
        #: ONE get_pos CALL PER PROMPT, not per cell: it tags all of a prompt's
        #: words together and only misses cost spaCy, so this is ~2,700 calls
        #: rather than 2 million.
        from malignment import pos as POS
        byp = collections.defaultdict(list)
        for i, r in enumerate(rows):
            byp[r[5] if len(r) > 5 else None].append(i)
        keep = []
        done = 0
        for prompt, idxs in byp.items():
            ws = sorted({rows[i][0] for i in idxs})
            try:
                tag = POS.get_pos(ws, prompt)
            except Exception:
                tag = {}
            for i in idxs:
                if tag.get(rows[i][0]) == "VERB":
                    keep.append(rows[i])
            done += 1
            if done % 400 == 0:
                print("    tagged %d/%d prompts, %d verb cells so far"
                      % (done, len(byp), len(keep)))
        print("  --verbs-only: %d of %d cells are VERB AT THAT SLOT (%d words)"
              % (len(keep), len(rows), len({r[0] for r in keep})))
        rows = keep
    if a.content_only:
        from malignment import fields as F
        seen, keep = {}, []
        for r in rows:
            w = r[0]
            if w not in seen:
                try:
                    seen[w] = F.is_function_word(w, a.lang)
                except Exception:
                    seen[w] = None
            #: None means UNKNOWN and is dropped, not kept: an unknown word counted
            #: as content inflates exactly the group this control protects.
            if seen[w] is False:
                keep.append(r)
        print("  --content-only: %d of %d cells kept (%d of %d words)"
              % (len(keep), len(rows), sum(1 for v in seen.values() if v is False), len(seen)))
        rows = keep
    print("loaded %d moving cells, %d words, %d norms" %
          (len(rows), len({r[0] for r in rows}), len(feats)))

    EMB = {}
    for enc in (a.encoders.split(",") if a.encoders else ("glove", "bge")):
        p = os.path.join(DATA, "embed_%s_%s.npz" % (a.lang, enc))
        if not os.path.exists(p):
            print("  no %s -- skipping (run embed.py)" % os.path.basename(p))
            continue
        z = np.load(p, allow_pickle=True)
        EMB[enc] = ({str(w): i for i, w in enumerate(z["words"])}, z["E"])
        print("  %-6s %d words, %d dims, gate gap %+.4f, anisotropy %.4f"
              % (enc, len(z["words"]), z["E"].shape[1], z["syn_gap"], z["anisotropy"]))
    if not EMB:
        sys.exit("no encoders available")

    dose = np.array([r[1] for r in rows])
    cut = float(np.median(dose))
    block("POOLED -- P's TABLE ON OUR CORPUS", rows, feats, EMB, a)

    lo = [r for r in rows if r[1] <= cut]
    hi = [r for r in rows if r[1] > cut]
    cl, chh = collections.Counter(r[0] for r in lo), collections.Counter(r[0] for r in hi)
    shared = {w for w in cl if cl[w] >= a.min_cells and chh[w] >= a.min_cells}
    print("\n  dose median %.4f | %d words have >=%d moving cells in BOTH strata"
          % (cut, len(shared), a.min_cells))
    if len(shared) >= 50:
        block("LOW DOSE -- same words as HIGH", [r for r in lo if r[0] in shared],
              feats, EMB, a, "  (%d words)" % len(shared))
        block("HIGH DOSE -- same words as LOW", [r for r in hi if r[0] in shared],
              feats, EMB, a, "  (%d words)" % len(shared))
    print("\n" + "=" * 100)
    print("  increment = real minus THAT MODEL'S OWN SHUFFLE, P's metric.")
    print("  %% headr = increment as a share of (emp_word - log p_base).")
    print("  Tree rows are a MEAN over %d draws with the range printed; a single"
          % a.draws)
    print("  draw is not quotable (OpenMP thread-order, P section 3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
