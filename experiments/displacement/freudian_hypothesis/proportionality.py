"""Does the affect that arrives scale with the charge that left? -> results/proportionality.json, .md

    python -u proportionality.py            print
    python -u proportionality.py --write

**Conservation made testable** (paper seat, 2026-09-28). The total mass summing to one
proves nothing (`departing_arriving.py` says why), so the conserved quantity has to be
affect. Freud's economic account predicts that the affect which arrives is diminished but
PROPORTIONATE to the charge that was withdrawn; a cooling account predicts no slope, or a
negative one, since more dangerous scenes should get calmer substitutes. The pooled arm
grain (`departing_arriving.py`) and the tercile dose split (`annotated_pairs.py --dose`)
cannot say which: this is the prompt-level slope, within lineage.

## THE QUANTITIES, per (lineage, English prompt), from `words_long_v4` (base vs endpoint)

    BARRED    departing words (delta < 0) with act >= 4, act = max(k_bodily_harm,
              k_transgressiveness) -- `disjunction.py`'s definition and cut, TYPE-level,
              so which words count as barred is fixed by the IDEA scale and never by the
              affect scale the slope is read on
    W         charge withdrawn:   sum(|delta| * affect) over barred departing words
    A         arriving intensity: sum(delta * affect) / sum(delta) over arriving words
    B         the frame's own level: sum(p_base * affect) / sum(p_base) over the prompt's
              NON-BARRED words -- what the rest of the scene makes available before
              alignment moves anything. **NOT over all words** (the first run, same day):
              the barred words sit inside an all-word B with high affect and high p_base,
              so the more charge they carry the higher B and the more there is to
              withdraw, and A - B falls with W by construction. B_all is reported beside
              it to show the size of that coupling.
    M         barred MASS withdrawn: sum(|delta|) over barred departing words (reported
              beside W: W mixes how much left with how intense it was)

**THE CONTROL IS B, AND WITHOUT IT A POSITIVE SLOPE IS FREE.** Across prompts, W and A
share a common cause -- the scene. A violent frame's whole candidate vocabulary is more
intense, so arrivals are hotter wherever more charge left even if nothing is conserved.
The primary response is therefore A - B (what arrives, over what the scene already
offered); raw A is reported beside it so the scene's share is visible.

## THE AFFECT INSTRUMENTS

    inst:arousal       SEPARATE, beside k_charge. slot_institutional_en_v3: "How much emotional INTENSITY does
                       the completion carry, regardless of whether it is positive or
                       negative?" 1-7, rated IN CONTEXT per (prompt, word)
    k_charge           PRIMARY (RH). type-level, "affective intensity, in either direction";
                       covers every word

`inst:arousal` rates a SUBSET of each prompt's words. **COVERAGE GATE, per scale:** a
(lineage, prompt) enters only if rated words carry >= 80% of its barred departing mass,
>= 80% of its arriving mass and >= 80% of its base mass. Coverage is reported, so a slope
fitted on whichever words happened to be rated is visible as such.

## THE TEST

Per lineage with >= 15 qualifying prompts: Spearman rho of (A - B) on W across prompts.
Over lineages: the median rho and a two-sided sign test on its sign. Reported beside it:
rho of raw A on W, and of (A - B) on M. Freud: positive. Cooling: zero or negative.
**A null is quoted as a bound** (the interquartile range of per-lineage rho), never as
"no slope".

Population: the 50 endpoint lineages (`roster.endpoints()`), English, as
`departing_arriving.py`, so the arm-grain and prompt-grain answers are about the same pairs.
"""
import argparse, collections, csv, gzip, json, os, statistics as st, sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
OUT = os.path.join(HERE, "results", "proportionality")
#: RH, 2026-09-28: "I'd prefer if we used charge, or both separately." k_charge PRIMARY,
#: inst:arousal beside it, never pooled. warriner_arousal dropped from this producer.
SCALES = ["k_charge", "inst:arousal"]
MIN_ACT, COVER, MIN_PROMPTS = 4.0, 0.80, 15


def sign_p(v):
    n = len(v); k = sum(1 for x in v if x > 0); k = min(k, n - k)
    return min(1.0, sum(comb(n, i) for i in range(k + 1)) * 2 / 2 ** n) if n else float("nan")


def spearman(x, y):
    from scipy.stats import spearmanr
    r = spearmanr(x, y).statistic
    return None if r != r else float(r)


def compute():
    from malignment import roster
    from departing_arriving import norms
    F, ctx = norms()
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    kcache, wcache = {}, {}

    def vals(pr, w):
        v = {}
        c = ctx.get((pr, w))
        if c and "inst:arousal" in c:
            v["inst:arousal"] = c["inst:arousal"]
        if w not in kcache:
            kcache[w] = F.k(w) or {}
        k = kcache[w]
        if "charge" in k:
            v["k_charge"] = float(k["charge"])
        if w not in wcache:
            wcache[w] = F.word_norms(w) or {}
        if "arousal" in wcache[w]:
            v["warriner_arousal"] = float(wcache[w]["arousal"])
        act = max(float(k.get("bodily_harm", 0) or 0), float(k.get("transgressiveness", 0) or 0)) if k else None
        return v, act

    #: (lineage, prompt) -> accumulators; per scale: [Wsum, barred_rated_mass, Asum, arr_rated_mass, Bsum, base_rated_mass]
    cell = collections.defaultdict(lambda: {"barred": 0.0, "arr": 0.0, "base": 0.0,
                                            "s": collections.defaultdict(lambda: [0.0] * 8)})
    seen = set()
    with gzip.open(SRC, "rt") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["lang"] != "en" or (row["base"], row["aligned"]) not in pairs:
                continue
            seen.add(row["base"])
            pr, w = row["prompt"], row["word"]
            d, pb = float(row["delta"]), float(row["p_base"] or 0)
            v, act = vals(pr, w)
            c = cell[(row["base"], pr)]
            c["base"] += pb
            barred = d < 0 and act is not None and act >= MIN_ACT
            if barred:
                c["barred"] += -d
            if d > 0:
                c["arr"] += d
            for s, x in v.items():
                a = c["s"][s]
                a[4] += pb * x; a[5] += pb
                if not (act is not None and act >= MIN_ACT):
                    a[6] += pb * x; a[7] += pb
                if barred:
                    a[0] += -d * x; a[1] += -d
                if d > 0:
                    a[2] += d * x; a[3] += d
    if len(seen) != 50:
        raise SystemExit("expected 50 endpoint lineages, matched %d" % len(seen))

    res, cover = {}, {}
    for s in SCALES:
        per_lin = collections.defaultdict(list)
        ncell = ngate = 0
        cov_b, cov_a, cov_p = [], [], []
        for (lin, pr), c in cell.items():
            if c["barred"] <= 0 or c["arr"] <= 0:
                continue
            ncell += 1
            a = c["s"].get(s)
            if not a:
                cov_b.append(0); cov_a.append(0); cov_p.append(0); continue
            cb, ca, cp = a[1] / c["barred"], a[3] / c["arr"], (a[5] / c["base"] if c["base"] else 0)
            cov_b.append(cb); cov_a.append(ca); cov_p.append(cp)
            if min(cb, ca, cp) < COVER or a[3] <= 0 or a[7] <= 0:
                continue
            ngate += 1
            W, A, B, M, Ball = a[0], a[2] / a[3], a[6] / a[7], c["barred"], a[4] / a[5]
            per_lin[lin].append((W, A, B, M, Ball))
        rows = {}
        for lin, v in per_lin.items():
            if len(v) < MIN_PROMPTS:
                continue
            W = [x[0] for x in v]; A = [x[1] for x in v]; B = [x[2] for x in v]; M = [x[3] for x in v]
            Ba = [x[4] for x in v]
            rows[lin] = dict(n=len(v), rho_AmB_W=spearman(W, [a - b for a, b in zip(A, B)]),
                             rho_A_W=spearman(W, A), rho_AmB_M=spearman(M, [a - b for a, b in zip(A, B)]),
                             rho_B_W=spearman(W, B), rho_AmBall_W=spearman(W, [a - b for a, b in zip(A, Ba)]),
                             #: THE LEVEL, which the slope cannot give: do arrivals sit AT the rest
                             #: of the scene's intensity (preservation of the field) or below it by
                             #: a constant (uniform cooling)? And the departing barred words' own level.
                             lvl_AmB=st.median([a - b for a, b in zip(A, B)]), lvl_A=st.median(A), lvl_B=st.median(B),
                             lvl_barred=st.median([x[0] / x[3] for x in v]))
        out = {"cells_with_barred_departure": ncell, "cells_past_coverage_gate": ngate,
               "lineages": len(rows), "per_lineage": rows}
        for key in ("rho_AmB_W", "rho_A_W", "rho_AmB_M", "rho_B_W", "rho_AmBall_W", "lvl_AmB", "lvl_A", "lvl_B", "lvl_barred"):
            v = [r[key] for r in rows.values() if r[key] is not None]
            if v:
                q = st.quantiles(v, n=4) if len(v) >= 4 else [min(v), st.median(v), max(v)]
                out[key] = dict(median=st.median(v), iqr=[q[0], q[-1]], positive=sum(x > 0 for x in v),
                                n=len(v), p_sign=sign_p(v))
        res[s] = out
        cover[s] = dict(median_barred=st.median(cov_b) if cov_b else None, median_arriving=st.median(cov_a) if cov_a else None,
                        median_base=st.median(cov_p) if cov_p else None)
    return res, cover


def report(res, cover):
    L = ["# Does the affect that arrives scale with the charge that left?", "",
         "Producer `proportionality.py` (spec in its docstring). Per (lineage, English prompt): W = charge withdrawn "
         "from barred departing words (act >= %.0f), A = intensity of arriving mass, B = the frame's own base-weighted "
         "level. Per lineage (>= %d prompts past an %.0f%% coverage gate), Spearman rho across prompts; median over "
         "lineages, two-sided sign test. **Freud: rho(A-B, W) > 0. Cooling: <= 0.**" % (MIN_ACT, MIN_PROMPTS, 100 * COVER), "",
         "| scale | cells (charged / past gate) | lineages | rho(A-B, W) | rho(A, W), no control | rho(B, W), the scene | rho(A-B, M), mass only | rho(A-B_all, W), coupled control |",
         "|---|---|---|---|---|---|---|---|"]

    def f(r):
        if not r:
            return "--"
        return "%+.3f [%+.2f, %+.2f] %d/%d p=%.2g" % (r["median"], r["iqr"][0], r["iqr"][1], r["positive"], r["n"], r["p_sign"])
    for s in SCALES:
        r = res[s]
        L.append("| `%s` | %d / %d | %d | %s | %s | %s | %s | %s |" % (s, r["cells_with_barred_departure"], r["cells_past_coverage_gate"],
                 r["lineages"], f(r.get("rho_AmB_W")), f(r.get("rho_A_W")), f(r.get("rho_B_W")), f(r.get("rho_AmB_M")), f(r.get("rho_AmBall_W"))))
    L += ["", "**Levels** (per lineage the median over prompts, then median over lineages [IQR]; positive/n is lineages with arrivals ABOVE the scene):", "",
          "| scale | barred departing | rest of scene (B) | arriving (A) | A - B |", "|---|---|---|---|---|"]
    for s in SCALES:
        r = res[s]
        g = lambda k: ("%.2f" % r[k]["median"]) if r.get(k) else "--"
        L.append("| `%s` | %s | %s | %s | %s |" % (s, g("lvl_barred"), g("lvl_B"), g("lvl_A"), f(r.get("lvl_AmB"))))
    L += ["", "Each cell: median rho [interquartile range over lineages], lineages positive / lineages, sign-test p.", "",
          "Coverage of rated words (median over charged cells, share of mass): " +
          "; ".join("`%s` barred %.2f, arriving %.2f, base %.2f" % (s, c["median_barred"] or 0, c["median_arriving"] or 0, c["median_base"] or 0)
                    for s, c in cover.items())]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    res, cover = compute()
    md = report(res, cover)
    print(md)
    if a.write:
        json.dump({"results": res, "coverage": cover}, open(OUT + ".json", "w"), indent=1)
        open(OUT + ".md", "w").write(md)


if __name__ == "__main__":
    main()
