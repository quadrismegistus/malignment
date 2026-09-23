"""What part of speech does each prompt's slot summon, and is `directedness` just that?

    python -u run.py            -> results/prompt_pos_en.csv, results/summary.txt

RH, 2026-09-23: "Is directedness just a function of the part of speech at a
slot? Could we categorise our prompts by the predominantly-mass-weighted part of
speech it summons above theta?"

## SOURCE

`~/malignment-data/norm_change/words_long_v4.csv.gz`: one row per (endpoint
pair, prompt, word) with p_base, p_aligned and a CONTEXTUAL UPOS (spaCy on
prompt + word, `norm_change/run.py:contextual_pos`), English only here, the 50
base->endpoint pairs of `roster.endpoints()`. The rows are the words above theta
in either arm, so "summons above theta" is exactly this population.

## PROMPT POS PROFILE

Per prompt and lineage, each UPOS's share of the above-theta mass on each side;
then the MEDIAN over lineages. `pos_base` is the argmax of the base profile,
`purity_base` its share. `pos_aligned` likewise; `switch` is 1 where they differ.
Consumers stratify on the BASE side, so alignment cannot choose the stratum. A prompt whose argmax changes
is one where alignment moved mass across parts of speech (the "category shift"
of the first-generation taxonomy), which is itself a finding and not noise.

## DIRECTEDNESS AGAINST POS

`v6:directedness` (1-7, "how likely is this action to be directed AT SOMEONE",
rated per word IN ITS FRAME) is joined per (prompt, word). Reported: its mean by
UPOS, the share of its variance UPOS explains (eta squared), and the same within
prompts whose slot is predominantly VERB -- if directedness still varies there,
it is not the part of speech.
"""
import collections, csv, gzip, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
OUT = os.path.join(HERE, "results")
SCALE = "directedness"
#: **spaCy TAGS A SLOT-FINAL ARTICLE AS PRON.** Tagging "prompt + the" leaves
#: the article with no noun to govern, and at PRON-dominant slots "the" was 28%
#: of the PRON mass and "a" 4% (measured 2026-09-23). The articles are remapped
#: to DET here. Possessives (her, his, my) and demonstratives (this, that) stay
#: as tagged: "her" is a pronoun as often as a determiner at these slots, and a
#: closed list cannot tell which without the continuation.
ARTICLES = {"the", "a", "an"}
#: ONE RUBRIC FILED UNDER TWO KEYS, disjoint: `v6` (114,524 pairs, 2,188
#: prompts) and `slot_rating_en_v6` (21,544, 276). The first run read only the
#: second and measured a fifth of the rows; the paper seat caught it
#: (feature_pairs.py had the same defect). `v6full`/`v6_wide` are left out
#: because their equivalence to v6 is unchecked.
INSTRUMENTS = ("v6", "slot_rating_en_v6")


def eta2(vals, groups):
    vals = np.asarray(vals, float)
    tot = ((vals - vals.mean()) ** 2).sum()
    by = collections.defaultdict(list)
    for v, g in zip(vals, groups):
        by[g].append(v)
    btw = sum(len(x) * (np.mean(x) - vals.mean()) ** 2 for x in by.values())
    return btw / tot if tot else float("nan")


def main():
    from malignment import roster, fields as F
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    idx = F._slot_index()

    # (prompt, base) -> side -> upos -> mass
    mass = collections.defaultdict(lambda: {"b": collections.Counter(),
                                            "a": collections.Counter()})
    rated = {}       # (prompt, word) -> (upos, directedness)
    wmass = collections.defaultdict(float)   # (prompt, word) -> summed p_base
    n = 0
    with gzip.open(SRC, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lang"] != "en" or (r["base"], r["aligned"]) not in pairs:
                continue
            n += 1
            pr, w, u = r["prompt"], r["word"], r["upos"]
            if u == "PRON" and w.lower() in ARTICLES:
                u = "DET"
            pb, pa = float(r["p_base"] or 0), float(r["p_aligned"] or 0)
            m = mass[(pr, r["base"])]
            m["b"][u] += pb
            m["a"][u] += pa
            wmass[(pr, w)] += pb
            if (pr, w) not in rated:
                by = idx.get((pr, w)) or {}
                d = None
                for inst in INSTRUMENTS:
                    d = (by.get(inst) or {}).get(SCALE)
                    if d is not None:
                        break
                if isinstance(d, (int, float)) and not isinstance(d, bool):
                    rated[(pr, w)] = (u, float(d))
    lineages = {b for _, b in mass}
    if len(lineages) != 50:
        raise SystemExit("expected 50 lineages, got %d" % len(lineages))

    # prompt profiles: median share over lineages
    byp = collections.defaultdict(list)
    for (pr, b), m in mass.items():
        byp[pr].append(m)
    tags = sorted({u for ms in byp.values() for m in ms for s in "ba" for u in m[s]})
    rows = []
    for pr, ms in sorted(byp.items()):
        prof = {}
        for s in "ba":
            sh = []
            for m in ms:
                t = sum(m[s].values())
                sh.append([m[s][u] / t if t else np.nan for u in tags])
            prof[s] = np.nanmedian(np.array(sh), axis=0)
        ib, ia = int(np.nanargmax(prof["b"])), int(np.nanargmax(prof["a"]))
        rows.append({"prompt": pr, "n_lineages": len(ms),
                     "pos_base": tags[ib], "purity_base": prof["b"][ib],
                     "pos_aligned": tags[ia], "purity_aligned": prof["a"][ia],
                     "switch": int(ib != ia),
                     **{"base_" + u: prof["b"][i] for i, u in enumerate(tags)},
                     **{"aligned_" + u: prof["a"][i] for i, u in enumerate(tags)}})
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "prompt_pos_en.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        for r in rows:
            wr.writerow({k: ("%.4f" % v if isinstance(v, float) else v) for k, v in r.items()})

    L = []
    p = lambda *a: L.append(" ".join(str(x) for x in a))
    p("rows read (en, 50 endpoint pairs):", format(n, ","))
    p("prompts:", len(rows))
    p()
    p("PROMPTS BY DOMINANT (median-over-lineages, mass-weighted) POS, BASE SIDE")
    c = collections.Counter(r["pos_base"] for r in rows)
    for u, k in c.most_common():
        pur = [r["purity_base"] for r in rows if r["pos_base"] == u]
        p("  %-6s %4d prompts   purity median %.2f  [q25 %.2f, q75 %.2f]"
          % (u, k, np.median(pur), np.quantile(pur, .25), np.quantile(pur, .75)))
    p()
    ch = [r for r in rows if r["pos_base"] != r["pos_aligned"]]
    p("prompts whose dominant POS CHANGES base->aligned: %d of %d" % (len(ch), len(rows)))
    for u, k in collections.Counter((r["pos_base"], r["pos_aligned"]) for r in ch).most_common(8):
        p("   %s -> %s  %d" % (u[0], u[1], k))
    p()

    # directedness vs POS, per (prompt, word), unweighted and base-mass-weighted
    keys = list(rated)
    U = [rated[k][0] for k in keys]
    D = np.array([rated[k][1] for k in keys])
    dom = {r["prompt"]: r["pos_base"] for r in rows}
    p("v6 %s rated (prompt, word) pairs in this population: %s over %d prompts"
      % (SCALE, format(len(keys), ","), len({k[0] for k in keys})))
    p("  eta^2 of word UPOS (unweighted): %.3f" % eta2(D, U))
    p("  eta^2 of the PROMPT's dominant POS: %.3f" % eta2(D, [dom.get(k[0]) for k in keys]))
    p("  eta^2 of PROMPT identity (ceiling for any prompt-level variable): %.3f"
      % eta2(D, [k[0] for k in keys]))
    p()
    p("  mean %s by word UPOS:" % SCALE)
    for u, k in collections.Counter(U).most_common(8):
        x = D[np.array(U) == u]
        p("    %-6s n=%6d  mean %.2f  sd %.2f  share>=4 %.2f" % (u, k, x.mean(), x.std(), (x >= 4).mean()))
    p()
    vv = np.array([u == "VERB" and dom.get(k[0]) == "VERB" for u, k in zip(U, keys)])
    x = D[vv]
    p("  WITHIN VERB words at VERB-dominant slots: n=%d, mean %.2f, sd %.2f, share>=4 %.2f"
      % (len(x), x.mean(), x.std(), (x >= 4).mean()))
    pk = [k[0] for k, v in zip(keys, vv) if v]
    p("    eta^2 of prompt identity within that set: %.3f" % eta2(x, pk))
    # prompt-level: mass-weighted directedness vs verb share
    pm = collections.defaultdict(lambda: [0.0, 0.0])
    for k in keys:
        wgt = wmass[k]
        pm[k[0]][0] += wgt * rated[k][1]
        pm[k[0]][1] += wgt
    vs = {r["prompt"]: r.get("base_VERB", np.nan) for r in rows}
    pp = [pr for pr in pm if pm[pr][1] > 0 and pr in vs]
    a = np.array([pm[pr][0] / pm[pr][1] for pr in pp])
    b = np.array([vs[pr] for pr in pp])
    from scipy.stats import spearmanr
    rho = spearmanr(a, b)
    p()
    p("  prompt-level: rated-mass-weighted %s vs base VERB share, n=%d prompts: "
      "Spearman %.3f (p=%.2g)" % (SCALE, len(pp), rho.correlation, rho.pvalue))
    txt = "\n".join(L) + "\n"
    open(os.path.join(OUT, "summary.txt"), "w").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
