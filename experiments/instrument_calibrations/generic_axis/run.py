#!/usr/bin/env python
"""Is a bare minimum naughty/nice vector sufficient?

The slot axis is built from the AUTHOR'S TAGS: `vg - vn`, the centroid of the
declared naughty poles minus the centroid of the declared nice poles, every word
embedded as `prompt + sep + word`. Tagging is the expensive step in authoring an
item and it is the step that makes `s(w)` a property of `(item, word)` rather
than of a word. So the question is what a generic lexical antonym pair -- one
`naughty` against one `nice`, no tagging at all -- would buy or lose.

This measures it over all 86 items of `round3_slots.yaml`.

## THE THREE OBJECTS, AND WHY FRAMING IS A SEPARATE AXIS FROM TAGGING

    A   BARE DECLARED    centroid(naughty words) - centroid(nice words), no prompt
    B   FRAMED DECLARED  the same, each word embedded as `prompt + sep + word`
                         -- this is the instrument `slot_axis.Axis` actually runs
    L   LEXICAL          embed(g) - embed(n) for an antonym pair, in both
                         variants: bare, and framed in the item's own prompt

`cos(L_bare, A)` and `cos(L_framed, B)` are the two correlations asked for.
`cos(A, B)` is reported alongside because it separates the two things a generic
axis could be failing at: if framing barely moves the declared axis, then the
prompt is doing little work and the tagging is what matters; if it moves it a
lot, a lexical pair that ignores the frame is disqualified before its own
cosine is read.

## DIRECTION AND ORIGIN FAIL SEPARATELY, AND ONLY ONE OF THEM MATTERS FOR RANK

An axis is a direction and an origin. `s(w) = (v_w - origin) . axis`, so
replacing the origin adds THE SAME CONSTANT to every word: **Spearman between
two scorings is invariant to the origin and depends only on the direction.**
The sign split -- which words land on the naughty side of zero -- depends on
both. So a lexical pair can rank the candidates correctly and still put the
whole item on one side of zero, and a single headline number would hide that.
Reported separately:

    spearman        direction only; is the ORDERING preserved
    purity_generic  direction + generic origin; do declared poles land right
    purity_mixed    generic direction, DECLARED origin; isolates the origin

## THE CONTROL, WITHOUT WHICH NO COSINE HERE MEANS ANYTHING

A cosine of 0.6 between a lexical pair and the declared axis is unreadable until
you know what the declared axis scores against ITSELF. So each item's poles are
split in half at random -- half the naughty words and half the nice words build
one axis, the complements build another -- and `cos` between those two halves is
the instrument's own split-half reliability, its noise ceiling. A lexical pair
at the ceiling is as good as tagging; a lexical pair far below it is worse than
the instrument's own sampling error.

Items with fewer than 4 words on either side cannot be split into two halves
that each have 2 words a side, and are reported as `nan` rather than dropped
silently, with the count printed.

## CACHING

Framed vectors go through `slot_axis.embed_cached`, so they land in the same
`|slot-word` store the app and the screens use, and this run warms it for them.
Bare vectors are embedded in one batch and NOT stored: the store's key is the
final string, a bare word's key would be that word alone, and the namespace is
documented as words IN A PROMPT FRAME. A bare `dress` and a framed `dress` are
different objects and merging them into one namespace is unrecoverable.
"""
import argparse
import collections
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from malignment import slot_axis  # noqa: E402

#: NAMED, NEVER GLOBBED. The round-3 battery is the population the slot
#: instrument was built on and the only tagged battery in either repo.
SLOTS = "/Users/rj416/github/malign-logits/pair_drafts/round3/round3_slots.yaml"

#: Naughty pole first, so a positive score means the naughty side under every
#: pair, matching `Axis`. Twelve pairs spanning the registers an author might
#: reach for: the moral, the sexual-explicit, the decorous, the dirty.
LEXICAL_PAIRS = [
    ("naughty", "nice"),
    ("bad", "good"),
    ("vice", "virtue"),
    ("obscene", "decent"),
    ("explicit", "innocent"),
    ("indecent", "proper"),
    ("vulgar", "polite"),
    ("dirty", "clean"),
    ("taboo", "acceptable"),
    ("immoral", "moral"),
    ("offensive", "inoffensive"),
    ("violent", "gentle"),
]
#: The pooled axis: every pair normalised, then averaged. This is the "bare
#: minimum" a careful author might build once and reuse, as against the single
#: pair a careless one would.
POOLED = "POOLED(%d pairs)" % len(LEXICAL_PAIRS)

SPLIT_HALF_REPEATS = 20
SEED = 20260817


def load_items(path):
    """The 86 items. Poles are COMMA STRINGS in this file, not YAML lists."""
    import yaml
    with open(path) as fh:
        raw = yaml.safe_load(fh)
    out = []
    for d in raw:
        naughty = [w.strip() for w in str(d["naughty"]).split(",") if w.strip()]
        nice = [w.strip() for w in str(d["nice"]).split(",") if w.strip()]
        out.append({"item_id": d["item_id"], "prompt": d["prompt"],
                    "domain": d.get("domain", ""),
                    "naughty": naughty, "nice": nice})
    return out


def cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-8 or nb < 1e-8:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def unit(a):
    n = np.linalg.norm(a)
    return a / n if n > 1e-8 else a


def spearman(x, y):
    from scipy.stats import spearmanr
    if len(x) < 3:
        return float("nan")
    return float(spearmanr(x, y).statistic)


def pearson(x, y):
    """Correlation of the two SCORINGS, which is the cosine that matters.

    `s = (F - o) . u`, so correlating two scorings over an item's words is the
    cosine between the two axes AFTER PROJECTING BOTH ONTO THE SUBSPACE THE
    WORDS ACTUALLY SPAN -- and, like `spearman`, it is invariant to the origin.
    The raw 1024-dim cosine counts every direction equally, including the ~1010
    along which no candidate in this item varies. That is why the two numbers
    diverge by a factor of five here and why the raw cosine, read alone, would
    condemn an axis that ranks correctly.
    """
    from scipy.stats import pearsonr
    if len(x) < 3:
        return float("nan")
    return float(pearsonr(x, y).statistic)


def embed_bare(model, words, cache):
    """One batch, no store. See the module docstring on why these are not cached."""
    missing = [w for w in words if w not in cache]
    if missing:
        V = np.asarray(model.encode(missing, normalize_embeddings=True,
                                    show_progress_bar=False, batch_size=64),
                       dtype=np.float32)
        for w, v in zip(missing, V):
            cache[w] = v
    return np.stack([cache[w] for w in words])


def split_half(rng, naughty, nice, framed, F, words):
    """The instrument's agreement with ITSELF, on all three scales at once.

    Half the naughty tags and half the nice tags build one axis, the complements
    build another, and both score every word in the item. Resampling the
    author's own words is the only noise model available here, and it is the
    ceiling every generic axis below has to be read against: a lexical pair that
    matches the declared axis as well as the declared axis matches itself has
    lost nothing that is measurable.

    Returned on the same three scales as `score_pair`, because they answer
    different questions and diverge sharply -- see the module docstring.
    """
    if len(naughty) < 4 or len(nice) < 4:
        return float("nan"), float("nan"), float("nan")
    cs, ps, ss = [], [], []
    for _ in range(SPLIT_HALF_REPEATS):
        gi = rng.permutation(len(naughty))
        ni = rng.permutation(len(nice))
        gh, nh = len(naughty) // 2, len(nice) // 2
        cent = lambda sel: np.stack([framed[w] for w in sel]).mean(0)
        halves = []
        for gsel, nsel in (((gi[:gh]), (ni[:nh])), ((gi[gh:]), (ni[nh:]))):
            vg = cent([naughty[i] for i in gsel])
            vn = cent([nice[i] for i in nsel])
            halves.append((vg - vn, (vg + vn) / 2.0))
        (a, oa), (b, ob) = halves
        cs.append(cos(a, b))
        sa, sb = (F - oa) @ unit(a), (F - ob) @ unit(b)
        ps.append(pearson(sa, sb))
        ss.append(spearman(sa, sb))
    return float(np.mean(cs)), float(np.mean(ps)), float(np.mean(ss))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=0,
                    help="first N items only, for a smoke run")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    args = ap.parse_args()

    items = load_items(SLOTS)
    if args.limit:
        items = items[:args.limit]
    print("items            %d  (%s)" % (len(items), os.path.basename(SLOTS)))
    print("lexical pairs    %d" % len(LEXICAL_PAIRS))

    model = slot_axis._model()
    bare_cache = {}
    rng = np.random.default_rng(SEED)

    lex_words = sorted({w for p in LEXICAL_PAIRS for w in p})
    embed_bare(model, lex_words, bare_cache)

    per_item, per_pair_rows = [], []
    for n, it in enumerate(items, 1):
        naughty, nice = it["naughty"], it["nice"]
        words = naughty + nice
        prompt = it["prompt"]

        #: FRAMED, through the shared store.
        F = slot_axis.embed_cached(prompt, words)
        framed = dict(zip(words, F))
        vg_f = np.stack([framed[w] for w in naughty]).mean(0)
        vn_f = np.stack([framed[w] for w in nice]).mean(0)
        B = vg_f - vn_f
        origin_declared = (vg_f + vn_f) / 2.0

        #: BARE, one batch, unstored.
        Vb = embed_bare(model, words, bare_cache)
        bare = dict(zip(words, Vb))
        A = (np.stack([bare[w] for w in naughty]).mean(0)
             - np.stack([bare[w] for w in nice]).mean(0))

        #: The declared instrument's own scores, the reference ordering.
        s_declared = (F - origin_declared) @ unit(B)

        #: The lexical poles IN THIS ITEM'S FRAME. One embed_cached call for all
        #: 24 pole words at once rather than per pair.
        LF = slot_axis.embed_cached(prompt, lex_words)
        lex_framed = dict(zip(lex_words, LF))

        sh_cos, sh_r, sh_rho = split_half(rng, naughty, nice, framed, F, words)
        row = {"item_id": it["item_id"], "domain": it["domain"],
               "prompt": prompt, "n_naughty": len(naughty), "n_nice": len(nice),
               "cos_A_B": cos(A, B), "split_half_cos": sh_cos,
               "split_half_pearson": sh_r, "split_half_spearman": sh_rho}

        pooled_bare = np.zeros_like(A)
        pooled_framed = np.zeros_like(B)
        pooled_origin = np.zeros_like(B)
        for g, ni_ in LEXICAL_PAIRS:
            L_bare = bare_cache[g] - bare_cache[ni_]
            L_framed = lex_framed[g] - lex_framed[ni_]
            L_origin = (lex_framed[g] + lex_framed[ni_]) / 2.0
            pooled_bare += unit(L_bare)
            pooled_framed += unit(L_framed)
            pooled_origin += L_origin

            per_pair_rows.append(dict(
                item_id=it["item_id"], pair="%s-%s" % (g, ni_),
                **score_pair(L_bare, L_framed, L_origin, A, B, F, words,
                             naughty, nice, s_declared, origin_declared)))

        pooled_origin /= len(LEXICAL_PAIRS)
        per_pair_rows.append(dict(
            item_id=it["item_id"], pair=POOLED,
            **score_pair(pooled_bare, pooled_framed, pooled_origin, A, B, F,
                         words, naughty, nice, s_declared, origin_declared)))
        per_item.append(row)
        if n % 10 == 0 or n == len(items):
            print("  %3d/%d  %s" % (n, len(items), it["item_id"]))

    write(args.out, items, per_item, per_pair_rows)


def score_pair(L_bare, L_framed, L_origin, A, B, F, words, naughty, nice,
               s_declared, origin_declared):
    """Everything measured for one (item, lexical pair)."""
    u = unit(L_framed)
    s_generic = (F - L_origin) @ u
    s_mixed = (F - origin_declared) @ u
    idx = {w: i for i, w in enumerate(words)}
    sign_ok = lambda s: (sum(1 for w in naughty if s[idx[w]] > 0)
                         + sum(1 for w in nice if s[idx[w]] < 0)) / len(words)
    return {
        "cos_bare_A": cos(L_bare, A),
        "cos_framed_B": cos(L_framed, B),
        "pearson": pearson(s_declared, s_generic),
        "spearman": spearman(s_declared, s_generic),
        "purity_generic": sign_ok(s_generic),
        "purity_mixed": sign_ok(s_mixed),
    }


def write(out, items, per_item, per_pair):
    import csv
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "per_item.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(per_item[0]))
        w.writeheader()
        w.writerows(per_item)
    with open(os.path.join(out, "per_item_pair.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(per_pair[0]))
        w.writeheader()
        w.writerows(per_pair)

    by = collections.defaultdict(list)
    for r in per_pair:
        by[r["pair"]].append(r)
    metrics = ["cos_bare_A", "cos_framed_B", "pearson", "spearman",
               "purity_generic", "purity_mixed"]
    agg = []
    for pair, rows in by.items():
        d = {"pair": pair, "n_items": len(rows)}
        for m in metrics:
            v = np.array([r[m] for r in rows], dtype=float)
            v = v[~np.isnan(v)]
            d[m + "_mean"] = float(v.mean()) if len(v) else float("nan")
            d[m + "_median"] = float(np.median(v)) if len(v) else float("nan")
        agg.append(d)
    #: Ranked on `pearson`, the scale the docstring argues is the readable one.
    agg.sort(key=lambda d: -d["pearson_mean"])
    with open(os.path.join(out, "per_pair.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(agg[0]))
        w.writeheader()
        w.writerows(agg)

    ab = np.array([r["cos_A_B"] for r in per_item], dtype=float)
    sh = {k: np.array([r["split_half_" + k] for r in per_item], dtype=float)
          for k in ("cos", "pearson", "spearman")}
    summary = {
        "slots_file": SLOTS,
        "n_items": len(items),
        "n_lexical_pairs": len(LEXICAL_PAIRS),
        "split_half_repeats": SPLIT_HALF_REPEATS,
        "seed": SEED,
        "embedder": slot_axis.EMBEDDER,
        "n_items_split_half_measurable": int((~np.isnan(sh["cos"])).sum()),
        "split_half": {k: {"mean": float(np.nanmean(v)),
                           "median": float(np.nanmedian(v))}
                       for k, v in sh.items()},
        "cos_A_B_mean": float(np.nanmean(ab)),
        "cos_A_B_median": float(np.nanmedian(ab)),
        "per_pair": agg,
    }
    #: The ceiling comparison, done here so nobody has to eyeball two tables.
    #: A pair AT the ceiling has lost nothing measurable to dropping the tags.
    for d in agg:
        for k in ("pearson", "spearman"):
            c = summary["split_half"][k]["mean"]
            d[k + "_vs_ceiling"] = (d[k + "_mean"] / c) if c else float("nan")
    with open(os.path.join(out, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print("\nCEILING  the declared axis against ITSELF, split-half over the")
    print("         author's own tags (%d of %d items have >=4 words a side)"
          % (summary["n_items_split_half_measurable"], len(items)))
    for k in ("cos", "pearson", "spearman"):
        print("    %-9s mean %.3f   median %.3f"
              % (k, summary["split_half"][k]["mean"],
                 summary["split_half"][k]["median"]))
    print("FRAMING  cos(A bare declared, B framed declared)")
    print("         mean %.3f   median %.3f" % (summary["cos_A_B_mean"],
                                                summary["cos_A_B_median"]))
    print("\n%-22s %6s %6s %6s %6s %6s %6s   %5s %5s" % (
        "lexical pair", "cosA", "cosB", "r", "rho", "pur_g", "pur_m",
        "r/ceil", "rho/c"))
    for d in agg:
        print("%-22s %6.3f %6.3f %6.3f %6.3f %6.3f %6.3f   %5.2f %5.2f" % (
            d["pair"], d["cos_bare_A_mean"], d["cos_framed_B_mean"],
            d["pearson_mean"], d["spearman_mean"], d["purity_generic_mean"],
            d["purity_mixed_mean"], d["pearson_vs_ceiling"],
            d["spearman_vs_ceiling"]))
    print("\ncosA/cosB are RAW 1024-dim cosines and are not the readable scale;")
    print("r is the correlation of the two SCORINGS. See the module docstring.")
    print("wrote %s" % out)


if __name__ == "__main__":
    main()
