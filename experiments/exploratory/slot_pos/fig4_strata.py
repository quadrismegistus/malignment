"""The Figure 4 z-plate statistics within prompt STRATA, one pass over the data.
-> results/fig4_strata_<by>.{json,txt}

    python -u fig4_strata.py --by pos         verb / noun slots
    python -u fig4_strata.py --by kind        dominant charge kind
    python -u fig4_strata.py --by kind_pos    kind x {verb, noun}

Same statistic as `norm_change/norms_levels_z.py` and the same test as
FIGURE3_OF_RECORD.md: per row, band and stratum, the lineage MEAN of the
per-row move (aligned - base level), then the median over the 50 lineages,
in z units of the POOLED norm sd so every stratum shares one ruler; up/down
counts of the lineage means, a two-sided sign test, BH at 0.05 over the
fourteen plate rows within each (stratum, band). Lift bands use the PUBLISHED
cuts. Strata come from `results/prompt_pos_en.csv` (base-side dominant UPOS,
purity >= --purity) and `results/prompt_kind_en.csv` (base-side mass-weighted
modal kind, NONE included) -- both grouped on the BASE side.

`fig4_within_pos.py` does the POS split through `norms_levels_z.build` itself
(one read per stratum); this reimplements the aggregation to read once, and
refuses to write unless its pooled stratum reproduces
`norm_change/results/norms_levels_z_en.json` on all fourteen rows.
"""
import argparse, collections, csv, gzip, json, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
NC = os.path.join(ROOT, "experiments", "displacement", "norm_change")
sys.path.insert(0, ROOT)
sys.path.insert(0, NC)
from gated_levels import GATE, SPARSE, SRC  # noqa: E402
from fig3_osgood import PICKS  # noqa: E402
from scipy.stats import binomtest  # noqa: E402

ROWS = list(PICKS)
BANDS = ("low", "all", "high")
MIN_PROMPTS = 20


def bh(ps, q=0.05):
    o = sorted(range(len(ps)), key=lambda i: ps[i])
    k = max([r for r, i in enumerate(o, 1) if ps[i] <= q * r / len(ps)], default=0)
    keep = set(o[:k])
    return [i in keep for i in range(len(ps))]


def strata_for(by, purity):
    pos = {r["prompt"]: (r["pos_base"], float(r["purity_base"]))
           for r in csv.DictReader(open(os.path.join(HERE, "results", "prompt_pos_en.csv")))}
    kind = {r["prompt"]: r["kind_base"]
            for r in csv.DictReader(open(os.path.join(HERE, "results", "prompt_kind_en.csv")))}
    slot = {p: t.lower() for p, (t, u) in pos.items() if t in ("VERB", "NOUN") and u >= purity}
    S = collections.defaultdict(set)
    for p in pos:
        if by == "pos" and p in slot:
            S[slot[p]].add(p)
        elif by == "kind" and p in kind:
            S[kind[p]].add(p)
        elif by == "kind_pos" and p in kind and p in slot:
            S["%s|%s" % (kind[p], slot[p])].add(p)
    return {k: v for k, v in sorted(S.items()) if len(v) >= MIN_PROMPTS}, \
        {k: len(v) for k, v in S.items() if len(v) < MIN_PROMPTS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--by", choices=("pos", "kind", "kind_pos"), required=True)
    ap.add_argument("--purity", type=float, default=0.6)
    a = ap.parse_args()
    from malignment import roster, charge
    eps, _ = roster.endpoints()
    keep = {"%s>%s" % (b, al) for b, al in eps.items()}
    lpl = charge.lifts_per_lineage()
    pub = json.load(open(os.path.join(NC, "results", "norms_levels_z_en.json")))
    lo, hi = pub["cuts"]
    pubz = {x["scale"]: x for x in pub["scales"]}
    S, dropped = strata_for(a.by, a.purity)
    member = collections.defaultdict(list)
    for name, ps in S.items():
        for p in ps:
            member[p].append(name)
    names = ["pooled"] + list(S)
    want = set(ROWS)

    # acc[stratum][scale][band][lineage] -> list of per-row moves
    acc = {n: {s: [collections.defaultdict(list) for _ in range(4)] for s in ROWS} for n in names}
    for table in ("levels", "contextual"):
        with gzip.open(SRC % table, "rt") as fh:
            head = fh.readline().rstrip("\n").split("\t")
            ix = {k: i for i, k in enumerate(head)}
            for line in fh:
                f = line.rstrip("\n").split("\t")
                if f[ix["lang"]] != "en":
                    continue
                sc = f[ix["scale"]]
                if sc not in want or sc in SPARSE:
                    continue
                lin = "%s>%s" % (f[ix["base"]], f[ix["aligned"]])
                if lin not in keep:
                    continue
                try:
                    b = float(f[ix["base_level"]]); al = float(f[ix["aligned_level"]])
                    cov = min(float(f[ix["base_cov"]]), float(f[ix["aligned_cov"]]))
                except ValueError:
                    continue
                if cov < GATE:
                    continue
                pr = f[ix["prompt"]]
                lift = lpl.get((pr, f[ix["base"]]))
                bands = (3,) if lift is None else (3, 0 if lift <= lo else (1 if lift <= hi else 2))
                for n in ["pooled"] + member.get(pr, []):
                    for k in bands:
                        acc[n][sc][k][lin].append(al - b)
        print("read", table, flush=True)

    out = {"by": a.by, "purity": a.purity, "cuts": [lo, hi], "min_prompts": MIN_PROMPTS,
           "dropped_small": dropped, "n_prompts": {n: len(S[n]) for n in S}, "strata": {}}
    for n in names:
        out["strata"][n] = {}
        for band in BANDS:
            k = {"low": 0, "mid": 1, "high": 2, "all": 3}[band]
            res = []
            for s in ROWS:
                dm = [st.fmean(v) for v in acc[n][s][k].values() if v]
                if not dm:
                    res.append({"scale": s, "n_lineages": 0}); continue
                up = sum(x > 0 for x in dm); dn = sum(x < 0 for x in dm)
                res.append({"scale": s, "n_lineages": len(dm),
                            "z": st.median(dm) / pubz[s]["sd"], "up": up, "down": dn,
                            "p": binomtest(up, up + dn).pvalue if up + dn else 1.0})
            ok = [r for r in res if "p" in r]
            for r, sig in zip(ok, bh([r["p"] for r in ok])):
                r["bh"] = sig
            out["strata"][n][band] = res
    # gate: pooled must reproduce the published plate
    for band in BANDS:
        for r in out["strata"]["pooled"][band]:
            pb = next(x for x in pubz[r["scale"]]["bands"] if x["band"] == band)
            if abs(r["z"] - pb["move_mean_z"]) > 1e-9 or r["up"] != pb["up_mean"]:
                raise SystemExit("refusing to write: pooled %s/%s does not reproduce" % (r["scale"], band))

    L = []
    p = lambda *x: L.append(" ".join(str(y) for y in x))
    p("by=%s  purity>=%.2f  strata with >= %d prompts; z in the pooled sd; * = BH 0.05 over 14 rows"
      % (a.by, a.purity, MIN_PROMPTS))
    p("pooled reproduces norms_levels_z_en.json (z and up counts, 14 rows x 3 bands)")
    p("prompts: " + ", ".join("%s %d" % (n, len(S[n])) for n in S))
    if dropped:
        p("dropped (< %d prompts): %s" % (MIN_PROMPTS, dropped))
    for band in BANDS:
        p()
        p("BAND %s" % band.upper())
        p("  %-20s" % "row" + "".join("%15s" % n[:14] for n in names))
        for i, s in enumerate(ROWS):
            cells = []
            for n in names:
                r = out["strata"][n][band][i]
                cells.append("%15s" % ("n/a" if "z" not in r else "%+.3f%s %2d/%-2d" % (
                    r["z"], "*" if r["bh"] else " ", r["up"], r["down"])))
            p("  %-20s" % s + "".join(cells))
    p()
    p("SIGNIFICANT CELLS WHOSE SIGN DISAGREES WITH THE POOLED PLATE:")
    nflip = 0
    for band in BANDS:
        for i, s in enumerate(ROWS):
            P = out["strata"]["pooled"][band][i]
            for n in names[1:]:
                r = out["strata"][n][band][i]
                if "z" in r and r["bh"] and (r["z"] > 0) != (P["z"] > 0):
                    nflip += 1
                    p("  %-5s %-18s %-20s %+.3f %d/%d  (pooled %+.3f%s)" % (
                        band, n, s, r["z"], r["up"], r["down"], P["z"], "*" if P["bh"] else ""))
    if not nflip:
        p("  none")
    txt = "\n".join(L) + "\n"
    open(os.path.join(HERE, "results", "fig4_strata_%s.txt" % a.by), "w").write(txt)
    json.dump(out, open(os.path.join(HERE, "results", "fig4_strata_%s.json" % a.by), "w"), indent=1)
    print(txt)


if __name__ == "__main__":
    main()
