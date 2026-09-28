"""The fates of the barred affect in a CONTINUOUS feeling space. -> results/feeling_space.md, .json

    python -u feeling_space.py            print
    python -u feeling_space.py --write

Declared 2026-09-28 BEFORE the full Jev run and before the second-rater check existed (RH:
"continue with how you propose"). It replaces the label-based kind results (`feeling_carry.py`'s
type arms, `anxiety_fate.py`), which RH judged unreliable: the DeepSeek labels for act words
moved with the wording and the fates they gave lived on two hard boundaries (none vs named;
fear vs anger for vocal words).

## THE INSTRUMENT

`slot_ratings/affect/type_survey.py` v2: a Jev Survey (jev-latest, resolved `jev-1.13.0`), each
word ALONE, two Choice questions over the same nine feelings, each returning a PROBABILITY per
feeling -- `doer` (the grammatical subject, the one who does it; never the victim) and `evoked`
(a witness or reader). A word is a point in the 9-simplex. Function words (DeepSeek
`ratable = False` in `type_task.py`) are out of every side, as before.

## THE RELIABILITY GATE, AND NOTHING BELOW IS READ UNLESS IT PASSES

A SECOND RATER (Claude, via Workflow, the same question in words) labels the ~400 words carrying
the most barred + arriving mass. PASS, per reading: Jev's argmax agrees with Claude's label on
>= 70% of the 400 AND Cohen's kappa >= 0.60. Reported beside it, not gating: agreement on the
`none` boundary alone and on the fear/anger boundary alone -- the two boundaries the label
results failed on. A reading that fails the gate is reported as "instrument not validated"
and its fates are not quoted.

## THE QUANTITIES, per (lineage, charged English prompt), 50 endpoint lineages

    B, A, S    the |delta|- / delta- / p_base-weighted MEAN feeling distributions of the
               barred departing words (act >= 4), the arriving words, and the scene's own
               non-barred base words
    gate       rated words carry >= 80% of each side's mass (unratable words excluded first)

    CARRY          JS(B, S) - JS(B, A)     > 0: arrivals sit closer to what left than the
                                           scene's own words do
    SUPPRESSION    A[none] - S[none]       > 0: arrivals more affectless than the scene
    KEPT           A[X] - S[X], X = argmax of B over the NAMED feelings
    ANXIETY        A[fear] - S[fear], cells with X != fear

Per lineage the mean over cells (>= 15); median over lineages, two-sided sign test, ties
dropped. Levels (mean A, B, S on `none` and `fear`) reported beside each.

## BY DOSE (`--dose`), declared 2026-09-28 before it ran (RH: "is this dosed by charge? Or are
## we just reading ordinary prompts go to ordinariness ... dosed by LIFT especially but let's
## also use prompt charge separately")

    LIFT     PRIMARY. Per cell, the barred departing words' `charge.word_lift(prompt, lineage)`
             (scene - frame, the lineage's own annotation), |delta|-weighted; a cell enters only
             if lift exists for >= 50% of its barred mass
    CHARGE   SEPARATE. `charge.dose(prompt)`, the prompt's mean scene rating over its
             candidates -- a property of the prompt

Within each lineage its cells are cut into TERCILES of the dose (the lineage's own cuts); per
lineage each fate's mean in the TOP tercile minus the BOTTOM; median over lineages, sign test.
Per-tercile medians beside. Doer only (evoked failed the gate). If the pooled fates are just
"ordinary prompts stay ordinary", the high-dose tercile is where they change.
"""
import argparse, collections, csv, gzip, json, math, os, statistics as st, sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
#: the INPUT and an output TAG are switchable (RH, 2026-09-28: base -> aligned-raw AND base ->
#: aligned-prefilled): FH_WORDS=words_long_v4_matched.csv.gz FH_TAG=_rawmatched, or
#: FH_WORDS=words_long_v4_framed.csv.gz FH_TAG=_prefill. Default: the original, untagged.
SRC = os.path.expanduser(os.environ.get("FH_WORDS", SRC)) if "/" in os.environ.get("FH_WORDS", "/") else os.path.join(os.path.dirname(SRC), os.environ["FH_WORDS"])
D = os.path.expanduser("~/malignment-data/affect_proportionality")
JEV = os.path.join(D, "type_survey.parquet")
DS = os.path.join(D, "type_feeling.parquet")
OUT = os.path.join(HERE, "results", "feeling_space")
OUT = OUT + os.environ.get("FH_TAG", "")
MIN_ACT, COVER = 4.0, 0.80
FEEL = ["anger", "fear", "grief", "desire", "disgust", "shame", "tenderness", "joy", "none"]
NAMED = FEEL[:-1]


def sign_p(v):
    v = [x for x in v if x != 0]
    n = len(v); k = sum(1 for x in v if x > 0); k = min(k, n - k)
    return min(1.0, sum(comb(n, i) for i in range(k + 1)) * 2 / 2 ** n) if n else float("nan")


def summ(v):
    v = [x for x in v if x == x]
    if len(v) < 4:
        return None
    q = st.quantiles(v, n=4)
    return dict(median=st.median(v), iqr=[q[0], q[-1]], pos=sum(x > 0 for x in v), neg=sum(x < 0 for x in v), n=len(v), p=sign_p(v))


def js(p, q):
    m = [(a + b) / 2 for a, b in zip(p, q)]
    kl = lambda x, y: sum(a * math.log(a / b) for a, b in zip(x, y) if a > 0 and b > 0)
    return (kl(p, m) + kl(q, m)) / 2


def compute(reading):
    import pyarrow.parquet as pq
    from departing_arriving import norms
    from malignment import roster
    F, _ = norms()
    unrat = {r["word"] for r in pq.read_table(DS).to_pylist() if r["ok"] and not r["ratable"]}
    vec = {}
    for r in pq.read_table(JEV).to_pylist():
        if r["ok"]:
            v = [r["%s_feeling_p_%s" % (reading, f)] for f in FEEL]
            t = sum(v)
            if t > 0:
                vec[r["word"]] = [x / t for x in v]
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    kc = {}

    def act(w):
        if w not in kc:
            k = F.k(w) or {}
            kc[w] = max(float(k.get("bodily_harm", 0) or 0), float(k.get("transgressiveness", 0) or 0)) if k else None
        return kc[w]
    Z = lambda: dict(t=0.0, r=0.0, v=[0.0] * len(FEEL))
    cell = collections.defaultdict(lambda: dict(b=Z(), a=Z(), s=Z(), bw=collections.Counter()))
    with gzip.open(SRC, "rt") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["lang"] != "en" or (row["base"], row["aligned"]) not in pairs:
                continue
            w = row["word"]
            if w in unrat:
                continue
            d = float(row["delta"]); x = act(w); barred = x is not None and x >= MIN_ACT
            c = cell[(row["base"], row["prompt"])]
            sides = []
            if barred and d < 0:
                sides.append(("b", -d)); c["bw"][w] += -d
            elif not barred and d > 0:
                sides.append(("a", d))
            if not barred:
                sides.append(("s", float(row["p_base"] or 0)))
            v = vec.get(w)
            for side, m in sides:
                c[side]["t"] += m
                if v:
                    c[side]["r"] += m
                    c[side]["v"] = [a + m * b for a, b in zip(c[side]["v"], v)]
    percell = []
    acc = {k: collections.defaultdict(list) for k in ("carry", "suppression", "kept", "anxiety")}
    lv = collections.defaultdict(list)
    ncell = 0
    for (lin, pr), c in cell.items():
        if any(c[k]["t"] <= 0 or c[k]["r"] < COVER * c[k]["t"] for k in "bas"):
            continue
        ncell += 1
        B, A, S = ([x / c[k]["r"] for x in c[k]["v"]] for k in "bas")
        acc["carry"][lin].append(js(B, S) - js(B, A))
        i_none, i_fear = FEEL.index("none"), FEEL.index("fear")
        acc["suppression"][lin].append(A[i_none] - S[i_none])
        X = max(range(len(NAMED)), key=lambda i: B[i])
        acc["kept"][lin].append(A[X] - S[X])
        if X != i_fear:
            acc["anxiety"][lin].append(A[i_fear] - S[i_fear])
        for k, V in (("B", B), ("A", A), ("S", S)):
            lv[k + "_none"].append(V[i_none]); lv[k + "_fear"].append(V[i_fear])
        percell.append(dict(lin=lin, pr=pr, carry=js(B, S) - js(B, A), suppression=A[i_none] - S[i_none],
                            kept=A[X] - S[X], anxiety=(A[i_fear] - S[i_fear]) if X != i_fear else None,
                            barred=dict(c["bw"])))
    res = {k: summ([st.fmean(v) for v in d.values() if len(v) >= 15]) for k, d in acc.items()}
    res["n_cells"] = ncell
    res["levels"] = {k: st.fmean(v) for k, v in lv.items()}
    res["_cells"] = percell
    return res


FATES = ("carry", "kept", "anxiety", "suppression")


def by_dose(cells):
    """Tercile contrast of each fate, within lineage, on LIFT and on prompt CHARGE."""
    from malignment import charge
    wl_cache = {}
    for c in cells:
        key = (c["pr"], c["lin"])
        if key not in wl_cache:
            wl_cache[key] = charge.word_lift(c["pr"], c["lin"])
        wl = wl_cache[key]
        tot = sum(c["barred"].values())
        have = {w: m for w, m in c["barred"].items() if w in wl}
        c["lift"] = (sum(m * wl[w] for w, m in have.items()) / sum(have.values())) if have and sum(have.values()) >= 0.5 * tot else None
        c["charge"] = charge.dose(c["pr"])
    out = {}
    for dose in ("lift", "charge"):
        per = collections.defaultdict(list)
        for c in cells:
            if c[dose] is not None:
                per[c["lin"]].append(c)
        diffs = {f: [] for f in FATES}; lv = {f: {t: [] for t in ("low", "mid", "high")} for f in FATES}
        ncell = 0
        for lin, cs in per.items():
            if len(cs) < 30:
                continue
            cs = sorted(cs, key=lambda c: c[dose]); k = len(cs) // 3
            parts = {"low": cs[:k], "mid": cs[k:2 * k], "high": cs[2 * k:]}
            ncell += len(cs)
            for f in FATES:
                m = {t: [c[f] for c in part if c[f] is not None] for t, part in parts.items()}
                if all(len(v) >= 5 for v in m.values()):
                    for t in m:
                        lv[f][t].append(st.fmean(m[t]))
                    diffs[f].append(st.fmean(m["high"]) - st.fmean(m["low"]))
        out[dose] = dict(n_cells=ncell, n_lineages=len([l for l in per if len(per[l]) >= 30]),
                         contrast={f: summ(v) for f, v in diffs.items()},
                         levels={f: {t: (st.median(v) if v else None) for t, v in d.items()} for f, d in lv.items()},
                         dose_range={t: None for t in ()})
    return out


def report_dose(d):
    f = lambda s: "--" if not s else "%+.4f [%+.4f, %+.4f] +%d/-%d of %d, p=%.2g" % (s["median"], s["iqr"][0], s["iqr"][1], s["pos"], s["neg"], s["n"], s["p"])
    L = ["## BY DOSE (doer), within-lineage terciles, top minus bottom", ""]
    for dose, r in d.items():
        L += ["### %s (%d cells, %d lineages)" % ("LIFT of the barred words (primary)" if dose == "lift" else "prompt CHARGE (separate)", r["n_cells"], r["n_lineages"]), "",
              "| fate | low | mid | high | high - low |", "|---|---|---|---|---|"]
        for fate in FATES:
            l = r["levels"][fate]
            L.append("| %s | %s | %s | %s | %s |" % (fate, *("%+.4f" % l[t] if l[t] is not None else "--" for t in ("low", "mid", "high")), f(r["contrast"][fate])))
        L.append("")
    return "\n".join(L) + "\n"


def report(out, gate):
    f = lambda s: "--" if not s else "%+.4f [%+.4f, %+.4f] +%d/-%d of %d, p=%.2g" % (s["median"], s["iqr"][0], s["iqr"][1], s["pos"], s["neg"], s["n"], s["p"])
    L = ["# The fates of the barred affect in a continuous feeling space", "",
         "Producer `feeling_space.py` (declared before the full Jev run and the second-rater check). Jev `type_survey.py` v2, words alone.", ""]
    for reading, r in out.items():
        g = gate.get(reading) if gate else None
        L += ["## `%s`" % reading, "",
              "Reliability gate: %s" % ("NOT RUN" if not g else "%s (argmax agreement %.2f, kappa %.2f, n=%d; `none` boundary %.2f; fear/anger %.2f)"
                                        % ("PASS" if g["pass"] else "**FAIL -- instrument not validated; fates below are not to be quoted**",
                                           g["agree"], g["kappa"], g["n"], g.get("none_agree", float("nan")), g.get("fa_agree", float("nan")))), "",
              "%d gated cells." % r["n_cells"], "",
              "- CARRY  JS(B,S) - JS(B,A): %s" % f(r["carry"]),
              "- SUPPRESSION  A[none] - S[none]: %s" % f(r["suppression"]),
              "- KEPT  A[X] - S[X]: %s" % f(r["kept"]),
              "- ANXIETY  A[fear] - S[fear], X != fear: %s" % f(r["anxiety"]), "",
              "Mean levels: P(none) barred %.2f / scene %.2f / arriving %.2f; P(fear) barred %.2f / scene %.2f / arriving %.2f" % tuple(
                  r["levels"][k] for k in ("B_none", "S_none", "A_none", "B_fear", "S_fear", "A_fear")), ""]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--dose", action="store_true")
    a = ap.parse_args()
    gp = os.path.join(D, "reliability_gate.json")
    gate = json.load(open(gp)) if os.path.exists(gp) else None
    out = {rd: compute(rd) for rd in ("doer", "evoked")}
    cells = out["doer"]["_cells"]
    for rd in out:
        out[rd].pop("_cells", None)
    md = report(out, gate)
    dose = None
    if a.dose:
        dose = by_dose(cells)
        md += report_dose(dose)
    print(md)
    if a.write:
        json.dump({"gate": gate, "results": out, "by_dose": dose}, open(OUT + ".json", "w"), indent=1); open(OUT + ".md", "w").write(md)


if __name__ == "__main__":
    main()
