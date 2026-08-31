"""P's question, conditioned on dose: held out by WORD, low-dose against high-dose.

    python -u analyse.py --lang en
    python -u analyse.py --lang en --min-cells 12 --folds 5

Fits on the named norms to predict a word's DIRECTION (+1 riser / -1 faller), holding
out by word, separately in a low-dose and a high-dose stratum, **on the same words**.

## THE PRIMARY TEST, AND THE CONTROL THAT MAKES IT MEAN ANYTHING

Dose is confounded with vocabulary: high-dose prompts contain different words, so a
naive low-vs-high comparison measures "are transgressive words easier to predict"
rather than "does a loaded frame help". Only the second is Findings P's question.

So a word enters only if it has `--min-cells` moving cells on BOTH sides of the dose
split, the word set is then FIXED, and only the dose varies. Any AUC difference is
attributable to the frame rather than to which words were in it.

The unrestricted comparison is printed too, labelled, because it answers the
vocabulary question and must not be read as answering P's.

## HELD OUT BY WORD, WHICH IS THE WHOLE POINT

GroupKFold on `word`: no word appears in both the fitting and the evaluation fold.
Without it a model memorises "the word `strangle` falls" and reports it as the norms
having predicted something, which is exactly the failure P's design exists to prevent.
The features are constant within a word, so a word-level leak is total.

## THE BENCHMARK IS REACHABLE AND SCORED BY THE SAME RULE

`emp_word` -- a word's own majority direction estimated on its OTHER cells within
the stratum -- is what a perfect word-level theory could achieve here, and it is
scored by the identical function the models are. **Never compare to 1.0 and never to
a ceiling fitted on the target**; that defect cost this campaign a day and is
documented in displacement_axis/README.md.

`p_base` alone is carried as the floor, because P's headroom is measured OVER base
probability rather than over chance.

## WHAT IS EXPLORATORY

The primary test is the shared-word conditional AUC. Per-language splits, per-norm
contributions, and which scales carry any conditioning are EXPLORATORY -- candidates
for a hypothesis, not results -- and are printed under that heading.
"""

import argparse, collections, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
DATA = os.path.expanduser("~/malignment-data/named_under_dose")

DROP = {"lineage", "prompt", "word", "lang", "dose", "direction",
        "p_base", "p_aligned", "k_coverage", "brysbaert_coverage",
        "warriner_coverage", "n_tokens", "n_content",
        "concreteness_zh_coverage", "n_words"}


def auc(y, s):
    """P(score of a +1 case > score of a -1 case), ties half. Chance 0.5."""
    pos = [x for x, t in zip(s, y) if t > 0]
    neg = [x for x, t in zip(s, y) if t < 0]
    if not pos or not neg:
        return None
    allv = sorted(pos + neg)
    rank = {}
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            rank[allv[k]] = r
        i = j + 1
    rp = sum(rank[x] for x in pos)
    return (rp - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def load(lang, want=None):
    #: PER-LANGUAGE FILE FIRST. en and zh carry different norm sets, so a shared
    #: file silently blanks one language's columns; see run.py's note.
    p = os.path.join(DATA, "cells_%s.csv.gz" % lang)
    if not os.path.exists(p):
        p = os.path.join(DATA, "cells.csv.gz")
    if not os.path.exists(p):
        sys.exit("no cells file in %s -- run run.py first" % DATA)
    rows = []
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        feats = [k for k in head if k not in DROP]
        if want == "k":
            feats = [k for k in feats if k.startswith("k_")]
        elif want:
            keep = {x.strip() for x in want.split(",")}
            feats = [k for k in feats if k in keep]
        if not feats:
            sys.exit("no features left after --features %s" % want)
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head):
                continue
            if v[ix["lang"]] != lang:
                continue
            try:
                d = float(v[ix["dose"]])
                y = int(v[ix["direction"]])
                pb = float(v[ix["p_base"]])
            except ValueError:
                continue
            x = []
            ok = True
            for k in feats:
                s = v[ix[k]]
                if s == "":
                    ok = False
                    break
                try:
                    x.append(float(s))
                except ValueError:
                    ok = False
                    break
            if not ok:
                continue
            rows.append((v[ix["word"]], d, y, pb, x, v[ix["prompt"]]))
    return rows, feats


def fit_eval(rows, feats, folds, scene_vals=None, seed=20260825):
    """GroupKFold on word. -> {model: auc} over the pooled held-out predictions.

    `scene_vals`: optional array of per-row scene ratings. When present, adds
    scene-only, named+scene, and scene+p models to the comparison.
    """
    import numpy as np
    words = sorted({r[0] for r in rows})
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(words))
    fold_of = {words[order[i]]: i % folds for i in range(len(words))}

    X = np.array([r[4] for r in rows], float)
    y = np.array([r[2] for r in rows], float)
    pb = np.array([r[3] for r in rows], float)
    w = [r[0] for r in rows]
    f = np.array([fold_of[x] for x in w])

    by = collections.defaultdict(lambda: [0, 0])
    for wi, yi in zip(w, y):
        by[wi][0] += yi
        by[wi][1] += 1
    emp = np.array([(by[wi][0] - yi) / max(1, by[wi][1] - 1) for wi, yi in zip(w, y)])

    models = [("named", None), ("named_p", None), ("logp", None)]
    if scene_vals is not None:
        models += [("scene", None), ("named+scene", None), ("scene+p", None)]

    out = {}
    preds = {k: np.zeros(len(y)) for k, _ in models}
    for k in range(folds):
        tr, te = f != k, f == k
        if tr.sum() < 50 or te.sum() < 20:
            continue
        mu, sd = X[tr].mean(0), X[tr].std(0)
        sd[sd == 0] = 1.0
        Z = (X - mu) / sd
        lp = np.log(np.clip(pb, 1e-12, None)).reshape(-1, 1)
        lp_n = (lp - lp[tr].mean()) / (lp[tr].std() or 1.0)
        Zp = np.hstack([Z, lp_n])

        build = [("named", Z), ("named_p", Zp), ("logp", lp_n)]
        if scene_vals is not None:
            sc = scene_vals.reshape(-1, 1)
            sc_n = (sc - sc[tr].mean()) / (sc[tr].std() or 1.0)
            build += [("scene", sc_n),
                      ("named+scene", np.hstack([Z, sc_n])),
                      ("scene+p", np.hstack([sc_n, lp_n]))]

        for name, M in build:
            A = np.hstack([M[tr], np.ones((tr.sum(), 1))])
            beta = np.linalg.solve(A.T @ A + 1.0 * np.eye(A.shape[1]), A.T @ y[tr])
            preds[name][te] = np.hstack([M[te], np.ones((te.sum(), 1))]) @ beta
    for name, v in preds.items():
        out[name] = auc(y, v)
    out["emp_word"] = auc(y, emp)
    out["_n"] = len(y)
    out["_words"] = len(words)
    out["_pos"] = float((y > 0).mean())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", choices=("en", "zh"))
    ap.add_argument("--min-cells", type=int, default=10,
                    help="moving cells a word needs IN EACH stratum to enter the "
                         "shared-word test")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--features", default=None,
                    help="comma-separated subset, or 'k' for the k_ratings only. "
                         "'k' is how en is made comparable to zh, which has no "
                         "Warriner or Brysbaert columns at all -- without it a "
                         "cross-language difference is confounded with a 12-vs-7 "
                         "feature-set difference.")
    ap.add_argument("--split-by", default="dose", choices=("dose", "lift"),
                    help="dose = k_transgressiveness (the level); "
                         "lift = charge.lift (dose - frame, the INCREMENT)")
    ap.add_argument("--scene", action="store_true",
                    help="add charge.scene as an in-context predictor alongside norms")
    a = ap.parse_args(argv)

    rows, feats = load(a.lang, a.features)
    if not rows:
        sys.exit("no rows for lang=%s" % a.lang)
    import numpy as np

    if a.split_by == "lift":
        from malignment import charge
        lifts = charge.lifts()
        new_rows, split_vals = [], []
        for r in rows:
            lf = lifts.get(r[5])  # r[5] is prompt
            if lf is not None:
                new_rows.append(r)
                split_vals.append(lf)
        print("  %d of %d rows have lift values" % (len(new_rows), len(rows)))
        rows = new_rows
    else:
        split_vals = [r[1] for r in rows]

    dose_arr = np.array(split_vals)
    cut = float(np.median(dose_arr))
    split_label = "lift (dose - frame)" if a.split_by == "lift" else "dose (k_transgressiveness)"
    print("=" * 92)
    print("P's QUESTION UNDER %s  --  lang=%s, %d moving cells, %d words, %d norms"
          % (a.split_by.upper(), a.lang, len(rows), len({r[0] for r in rows}), len(feats)))
    print("=" * 92)
    print("  split = %s; median split at %.4f" % (split_label, cut))
    print("  features: %s" % ", ".join(feats))

    # --- scene ratings as in-context predictor ---
    scene_map = {}
    if a.scene:
        from malignment import charge
        for r in rows:
            pr = r[5]  # prompt
            if pr not in scene_map:
                scene_map[pr] = charge.scene(pr)

    def scene_array(part):
        """Scene rating per row, or None if --scene not given."""
        if not a.scene:
            return None
        import numpy as np
        vals = []
        for r in part:
            sc = scene_map.get(r[5], {})
            s = sc.get(r[0])  # r[0] = word
            vals.append(s if s is not None else float("nan"))
        arr = np.array(vals)
        valid = ~np.isnan(arr)
        if valid.sum() < len(arr) * 0.5:
            return None
        arr[~valid] = np.nanmean(arr)
        return arr

    lo = [r for r, v in zip(rows, split_vals) if v <= cut]
    hi = [r for r, v in zip(rows, split_vals) if v > cut]

    cl = collections.Counter(r[0] for r in lo)
    ch_ = collections.Counter(r[0] for r in hi)
    shared = {w for w in cl if cl[w] >= a.min_cells and ch_[w] >= a.min_cells}
    print("\n  words with >=%d moving cells in BOTH strata: %d" % (a.min_cells, len(shared)))
    if len(shared) < 50:
        print("  TOO FEW for the primary test; lower --min-cells or widen the corpus")

    has_scene = a.scene
    def block(title, L, H, note=""):
        print("\n" + "-" * 92)
        print("  %s%s" % (title, note))
        print("-" * 92)
        hdr = "  %-12s %10s %10s %10s" % ("stratum", "named", "named+p", "log p_base")
        if has_scene:
            hdr += " %10s %10s %10s" % ("scene", "named+sc", "scene+p")
        hdr += "   %s" % "emp_word"
        print(hdr)
        res = {}
        for nm, part in (("LOW", L), ("HIGH", H)):
            if len(part) < 200:
                print("  %-12s  too few cells (%d)" % (nm, len(part)))
                continue
            sv = scene_array(part)
            r = fit_eval(part, feats, a.folds, scene_vals=sv)
            res[nm] = r
            line = "  %-12s %10.4f %10.4f %10.4f" % (nm, r["named"], r["named_p"], r["logp"])
            if has_scene and "scene" in r:
                line += " %10.4f %10.4f %10.4f" % (r["scene"], r["named+scene"], r["scene+p"])
            line += "   %10.4f      n=%d, %d words" % (r["emp_word"], r["_n"], r["_words"])
            print(line)
        if len(res) == 2:
            l, h = res["LOW"], res["HIGH"]
            diff = "\n  HIGH-LOW          %+9.4f %+9.4f %+9.4f" % (
                h["named"] - l["named"], h["named_p"] - l["named_p"],
                h["logp"] - l["logp"])
            if has_scene and "scene" in l:
                diff += " %+9.4f %+9.4f %+9.4f" % (
                    h.get("scene", 0) - l.get("scene", 0),
                    h.get("named+scene", 0) - l.get("named+scene", 0),
                    h.get("scene+p", 0) - l.get("scene+p", 0))
            diff += "   %+10.4f" % (h["emp_word"] - l["emp_word"])
            print(diff)
            for nm, r in (("LOW", l), ("HIGH", h)):
                head = r["emp_word"] - r["logp"]
                got_named = r["named_p"] - r["logp"]
                s = "  %-5s headroom = %+.4f; named %+.4f = %s" % (
                    nm, head, got_named,
                    ("%.0f%%" % (100 * got_named / head)) if abs(head) > 1e-6 else "n/a")
                if has_scene and "scene+p" in r:
                    got_scene = r["scene+p"] - r["logp"]
                    got_both = r.get("named+scene", r["named_p"]) - r["logp"]
                    s += "; scene %+.4f = %s; named+scene %+.4f = %s" % (
                        got_scene,
                        ("%.0f%%" % (100 * got_scene / head)) if abs(head) > 1e-6 else "n/a",
                        got_both,
                        ("%.0f%%" % (100 * got_both / head)) if abs(head) > 1e-6 else "n/a")
                print(s)
        return res

    if len(shared) >= 50:
        block("PRIMARY -- SAME WORDS IN BOTH STRATA",
              [r for r in lo if r[0] in shared], [r for r in hi if r[0] in shared],
              "  (%d words)" % len(shared))
    block("SECONDARY -- ALL WORDS (answers the VOCABULARY question, not P's)", lo, hi)

    print("\n" + "=" * 92)
    print("  emp_word is the REACHABLE benchmark: a word's majority direction from its")
    print("  own other cells in the same stratum, scored by the identical rule. It is")
    print("  the most a word-level theory can do here. Compare to it, never to 1.0.")
    print("  bge is not run as a rival here -- see README: it is a ceiling on naming.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
