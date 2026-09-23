"""Follow-ups to fig4_strata asked by the paper seat for RH, 2026-09-23.
-> results/followups.md

    python -u followups.py

(1) MULTIPLICITY. fig4_strata applies BH over the 14 rows within one
    (stratum, band). Here BH runs over EVERY non-pooled cell of a table at once
    (strata x bands x rows), for each aggregator. Does the DEGRADING reversal
    survive?
(2) (3) THE WORDS behind the DEGRADING valence/dominance reversal and the
    ILLICIT vocalisation loss. Per word: net delta = mean over the 50 endpoint
    lineages of the summed (p_aligned - p_base) across the stratum's prompts
    (absent counts 0), with the word's rating on the scale in question -- the
    type-level Warriner norm for valence/dominance, the in-frame v6 rating for
    vocalisation (mean over the stratum's prompts that rated it). `pull` =
    net delta x (rating - the stratum's mass-weighted mean rating), which is the
    sign a word pushes the level: a rising word below the mean pulls it down.
(4) CROSS-TAB of dominant kind against the paper seat's frame families
    (`freudian_hypothesis/directedness_frames.family`), and against slot POS.
"""
import collections, csv, gzip, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "displacement", "freudian_hypothesis"))
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
N = 15


def bh_all(ps, q=0.05):
    o = sorted(range(len(ps)), key=lambda i: ps[i])
    k = max([r for r, i in enumerate(o, 1) if ps[i] <= q * r / len(ps)], default=0)
    keep = set(o[:k])
    return [i in keep for i in range(len(ps))]


def multiplicity(L):
    L += ["## (1) BH over every non-pooled cell of a table", ""]
    for by in ("kind", "kind_pos"):
        for stat in ("", "_median"):
            d = json.load(open(os.path.join(HERE, "results", "fig4_strata_%s%s.json" % (by, stat))))
            cells = [(n, b, r) for n, bands in d["strata"].items() if n != "pooled"
                     for b, rs in bands.items() for r in rs if "p" in r]
            sig = bh_all([r["p"] for _, _, r in cells])
            pooled = {(b, r["scale"]): r for b, rs in d["strata"]["pooled"].items() for r in rs}
            L.append("**%s, %s** — %d cells, %d survive table-wide BH (were %d under per-(stratum, band) BH)"
                     % (by, "median" if stat else "mean", len(cells), sum(sig),
                        sum(r["bh"] for _, _, r in cells)))
            flips = [(n, b, r) for (n, b, r), s in zip(cells, sig)
                     if s and (r["z"] > 0) != (pooled[(b, r["scale"])]["z"] > 0)]
            L.append("")
            L.append("    significant table-wide AND opposite in sign to the pooled plate:")
            for n, b, r in flips:
                L.append("    %-5s %-14s %-20s %+.3f %d/%d  p=%.2g" % (b, n, r["scale"], r["z"], r["up"], r["down"], r["p"]))
            if not flips:
                L.append("    none")
            L.append("")


def movers(L, strata, kind, scale, rating_of, band_filter=None):
    from malignment import roster
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    ps = strata[kind]
    net = collections.defaultdict(float)
    pb = collections.defaultdict(float)
    per = collections.defaultdict(lambda: collections.defaultdict(float))
    with gzip.open(SRC, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lang"] != "en" or r["prompt"] not in ps or (r["base"], r["aligned"]) not in pairs:
                continue
            dd = float(r["delta"]) / len(pairs)
            net[r["word"]] += dd
            pb[r["word"]] += float(r["p_base"] or 0) / len(pairs)
            per[r["prompt"]][r["word"]] += dd
    rt = {w: rating_of(w, ps) for w in net}
    rated = {w: v for w, v in rt.items() if v is not None}
    mu = sum(pb[w] * v for w, v in rated.items()) / max(1e-12, sum(pb[w] for w in rated))
    pull = {w: net[w] * (v - mu) for w, v in rated.items()}
    L += ["## %s: the words behind `%s`" % (kind, scale), "",
          "%d prompts. Mass-weighted mean rating over the stratum's base mass: %.2f. Net delta summed over prompts, mean over lineages." % (len(ps), mu), ""]
    f = lambda w: "%s %+.3f (%s)" % (w, net[w], "—" if rt[w] is None else "%.1f" % rt[w])
    L.append("- **falls:** " + ", ".join(f(w) for w in sorted(net, key=net.get)[:N]))
    L.append("- **rises:** " + ", ".join(f(w) for w in sorted(net, key=net.get, reverse=True)[:N]))
    L.append("- **pull toward LOWER %s** (rated words): " % scale +
             ", ".join("%s %+.4f" % (w, pull[w]) for w in sorted(pull, key=pull.get)[:N]))
    L.append("- **pull toward HIGHER %s**: " % scale +
             ", ".join("%s %+.4f" % (w, pull[w]) for w in sorted(pull, key=pull.get, reverse=True)[:8]))
    L += ["", "<details><summary>per prompt</summary>", ""]
    for p in sorted(per):
        ws = per[p]
        L.append("- **%s**" % p)
        L.append("  - falls: " + ", ".join("%s %+.3f" % (w, ws[w]) for w in sorted(ws, key=ws.get)[:6] if ws[w] < 0))
        L.append("  - rises: " + ", ".join("%s %+.3f" % (w, ws[w]) for w in sorted(ws, key=ws.get, reverse=True)[:6] if ws[w] > 0))
    L += ["", "</details>", ""]


def main():
    from malignment import fields as F
    kind = {r["prompt"]: r["kind_base"] for r in csv.DictReader(open(os.path.join(HERE, "results", "prompt_kind_en.csv")))}
    pos = {r["prompt"]: (r["pos_base"], float(r["purity_base"])) for r in csv.DictReader(open(os.path.join(HERE, "results", "prompt_pos_en.csv")))}
    strata = collections.defaultdict(set)
    for p, k in kind.items():
        strata[k].add(p)
    L = ["# fig4_strata follow-ups (paper seat for RH, 2026-09-23)", "", "Producer: `followups.py`.", ""]
    multiplicity(L)

    wn = {}
    def warr(scale):
        def g(w, ps):
            if w not in wn:
                wn[w] = F.word_norms(w) or {}
            v = wn[w].get(scale)
            return None if v is None else float(v)
        return g
    idx = F._slot_index()
    def v6(scale):
        def g(w, ps):
            vs = []
            for p in ps:
                by = idx.get((p, w)) or {}
                for inst in ("v6", "slot_rating_en_v6"):
                    x = (by.get(inst) or {}).get(scale)
                    if isinstance(x, (int, float)) and not isinstance(x, bool):
                        vs.append(float(x)); break
            return float(np.mean(vs)) if vs else None
        return g
    L += ["## (2) DEGRADING", ""]
    movers(L, strata, "DEGRADING", "valence", warr("valence"))
    wn_dom = warr("dominance")
    movers(L, strata, "DEGRADING", "dominance", wn_dom)
    L += ["## (3) ILLICIT", ""]
    movers(L, strata, "ILLICIT", "vocalisation", v6("vocalisation"))

    import directedness_frames as DF
    L += ["## (4) Kind against frame family and slot POS", "",
          "Frame family: `directedness_frames.family` (grievance = ends \"I should\"; drive = ends \"wanted to\"/\"began to\"/\"started to\"; other). Counts are prompts with a kind rating.", ""]
    ct = collections.Counter((DF.family(p), k) for p, k in kind.items())
    fams = sorted({f for f, _ in ct})
    ks = ["NONE", "COERCIVE", "VIOLENT", "OTHER", "ILLICIT", "SEXUAL", "DEGRADING"]
    L.append("| family | " + " | ".join(ks) + " | total |")
    L.append("|---|" + "---|" * (len(ks) + 1))
    for f in fams:
        L.append("| %s | " % f + " | ".join(str(ct[(f, k)]) for k in ks) + " | %d |" % sum(ct[(f, k)] for k in ks))
    L.append("")
    pc = collections.Counter((pos[p][0] if pos[p][1] >= 0.6 else "(impure)", k) for p, k in kind.items() if p in pos)
    pp = ["VERB", "NOUN", "PRON", "DET", "(impure)"]
    L.append("| slot POS (purity ≥ 0.6) | " + " | ".join(ks) + " |")
    L.append("|---|" + "---|" * len(ks))
    for q in pp:
        L.append("| %s | " % q + " | ".join(str(pc[(q, k)]) for k in ks) + " |")
    other = sum(v for (q, _), v in pc.items() if q not in pp)
    L.append("")
    L.append("(%d prompts at other slot types omitted.)" % other)
    open(os.path.join(HERE, "results", "followups.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(l for l in L if not l.startswith("  -") and not l.startswith("- **") or "falls:**" in l or "rises:**" in l or "pull" in l))


if __name__ == "__main__":
    main()
