"""The fates and the intensity result as INCREMENTS over the frame, in context, on one instrument. -> results/context_fates.md, .json

    python -u context_fates.py --write

Declared 2026-09-28 BEFORE `slot_ratings/affect/context_survey.py` v2 finished and before its
second-rater check existed. RH: the word-alone rating "doesn't totally make sense", the in-context
rater lends the scene's feeling to mild words, and function/common words are common everywhere.

## THE INSTRUMENT

Jev (`jev-latest`), IN CONTEXT, one call per item, two questions about the GRAMMATICAL SUBJECT:
`doer_feeling` (distribution over nine feelings) and `doer_intensity` (Score, 5 levels, a
probability-weighted position 0..4). Each of the 1,873 charged English frames is rated ALONE
(slot open) and each mover inside it. A word's contribution is its SHIFT from its own frame:
dF = F(frame + word) - F(frame), dI = I(frame + word) - I(frame). The scene's feeling and
intensity are in both terms and cancel -- the fix for the scene-lending the earlier in-context
rater showed.

## THE RELIABILITY GATE (nothing below is read unless it passes)

A second rater (Claude via Workflow, same questions in words) on 400 items (100 frames, 300 words:
the highest-mass barred and arriving words in those frames). PASS: feeling argmax agreement >=
0.70 AND kappa >= 0.60; intensity Spearman >= 0.60. Reported per question; a failing question's
results are not quoted.

## THE QUANTITIES, per (lineage, charged prompt), 50 endpoint lineages

    barred   departing words with act >= 4; arrivals: non-barred words with delta > 0
    dI_B, dI_A      |delta|- / delta-weighted mean intensity shift of barred / arriving words
    dF_B, dF_A      the same for the feeling shift (vectors)
    W        sum(|delta| * max(dI, 0)) over barred words: the intensity withdrawn
    gate     rated items carry >= 80% of the barred and of the arriving mass

    INTENSITY LEVEL        median dI_A and dI_B (arrivals add intensity to the frame, or not)
    PROPORTIONALITY        within lineage, Spearman of dI_A on W across prompts (Freud: > 0)
    CARRY                  cosine(dF_A, dF_B): do arrivals move the feeling the way the barred words did?
    KEPT                   dF_A[X], X = the feeling the barred words ADD most (argmax of dF_B, named)
    ANXIETY                dF_A[fear] where X != fear
    SUPPRESSION            dF_A[none]

Per lineage the mean over cells (>= 15); median over lineages, two-sided sign test, ties dropped.

## SENSITIVITIES, declared now

    CONTENT WORDS ONLY (RH: "selecting on content words")  arrivals restricted to upos NOUN, VERB,
        ADJ, ADV, PROPN, minus the light verbs LIGHT below; every quantity recomputed
    DOSE   within-lineage terciles of the barred words' lift (`charge.word_lift`) and of prompt
           charge (`charge.dose`); top minus bottom for each quantity
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
CTX = os.path.join(D, "context_survey.parquet")
OUT = os.path.join(HERE, "results", "context_fates")
OUT = OUT + os.environ.get("FH_TAG", "")
MIN_ACT, COVER = 4.0, 0.80
FEEL = ["anger", "fear", "grief", "desire", "disgust", "shame", "tenderness", "joy", "none"]
CONTENT = {"NOUN", "VERB", "ADJ", "ADV", "PROPN"}
#: declared before the run: auxiliaries and light / vehicle verbs whose content arrives in their complement
LIGHT = {"be", "is", "was", "were", "are", "been", "being", "have", "has", "had", "do", "does", "did", "done",
         "get", "got", "gets", "getting", "make", "made", "makes", "take", "took", "taken", "go", "went", "gone",
         "come", "came", "give", "gave", "given", "put", "let", "keep", "kept", "start", "started", "begin", "began",
         "try", "tried", "want", "wanted", "need", "needed", "seem", "seemed", "become", "became", "can", "could",
         "will", "would", "should", "might", "must", "may", "just", "then", "also"}


def sign_p(v):
    v = [x for x in v if x != 0]
    n = len(v); k = sum(1 for x in v if x > 0); k = min(k, n - k)
    return min(1.0, sum(comb(n, i) for i in range(k + 1)) * 2 / 2 ** n) if n else float("nan")


def summ(v):
    v = [x for x in v if x is not None and x == x]
    if len(v) < 4:
        return None
    q = st.quantiles(v, n=4)
    return dict(median=st.median(v), iqr=[q[0], q[-1]], pos=sum(x > 0 for x in v), neg=sum(x < 0 for x in v), n=len(v), p=sign_p(v))


def cos(a, b):
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na > 0 and nb > 0 else None


def load():
    import pyarrow.parquet as pq
    fr, wd = {}, {}
    for r in pq.read_table(CTX).to_pylist():
        if not r["ok"]:
            continue
        v = ([r["p_" + f] for f in FEEL], r["intensity"])
        (fr.__setitem__(r["prompt"], v) if r["word"] is None else wd.__setitem__((r["prompt"], r["word"]), v))
    return fr, wd


def cells(content_only=False):
    from departing_arriving import norms
    from malignment import roster
    F, _ = norms()
    fr, wd = load()
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    kc = {}

    def act(w):
        if w not in kc:
            k = F.k(w) or {}
            kc[w] = max(float(k.get("bodily_harm", 0) or 0), float(k.get("transgressiveness", 0) or 0)) if k else None
        return kc[w]
    Z = lambda: dict(t=0.0, r=0.0, dF=[0.0] * len(FEEL), dI=0.0, W=0.0)
    cell = collections.defaultdict(lambda: dict(b=Z(), a=Z(), bw=collections.Counter()))
    with gzip.open(SRC, "rt") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["lang"] != "en" or (row["base"], row["aligned"]) not in pairs or row["prompt"] not in fr:
                continue
            w = row["word"]; d = float(row["delta"]); x = act(w); barred = x is not None and x >= MIN_ACT
            if barred and d < 0:
                side, m = "b", -d
            elif not barred and d > 0:
                if content_only and (row["upos"] not in CONTENT or w.lower() in LIGHT):
                    continue
                side, m = "a", d
            else:
                continue
            c = cell[(row["base"], row["prompt"])]; s = c[side]
            s["t"] += m
            if side == "b":
                c["bw"][w] += m
            v = wd.get((row["prompt"], w))
            if v:
                f0, i0 = fr[row["prompt"]]
                s["r"] += m
                s["dF"] = [a + m * (b - z) for a, b, z in zip(s["dF"], v[0], f0)]
                s["dI"] += m * (v[1] - i0)
                if side == "b":
                    s["W"] += m * max(v[1] - i0, 0.0)
    out = []
    for (lin, pr), c in cell.items():
        b, a = c["b"], c["a"]
        if b["t"] <= 0 or a["t"] <= 0 or b["r"] < COVER * b["t"] or a["r"] < COVER * a["t"]:
            continue
        dFB = [x / b["r"] for x in b["dF"]]; dFA = [x / a["r"] for x in a["dF"]]
        X = max(range(len(FEEL) - 1), key=lambda i: dFB[i])
        out.append(dict(lin=lin, pr=pr, dIB=b["dI"] / b["r"], dIA=a["dI"] / a["r"], W=b["W"], carry=cos(dFA, dFB),
                        kept=dFA[X], anxiety=dFA[FEEL.index("fear")] if FEEL[X] != "fear" else None,
                        suppression=dFA[FEEL.index("none")], barred=dict(c["bw"])))
    return out


QTY = ("dIA", "dIB", "carry", "kept", "anxiety", "suppression")


def summarise(cs):
    from scipy.stats import spearmanr
    per = collections.defaultdict(list)
    for c in cs:
        per[c["lin"]].append(c)
    res = {q: summ([st.fmean([c[q] for c in v if c[q] is not None]) for v in per.values()
                    if len(v) >= 15 and any(c[q] is not None for c in v)]) for q in QTY}
    rho = []
    for v in per.values():
        if len(v) >= 15:
            r = spearmanr([c["W"] for c in v], [c["dIA"] for c in v]).statistic
            if r == r:
                rho.append(r)
    res["proportionality_rho"] = summ(rho)
    res["n_cells"] = len(cs); res["n_lineages"] = sum(1 for v in per.values() if len(v) >= 15)
    return res


def by_dose(cs):
    from malignment import charge
    wl = {}
    for c in cs:
        k = (c["pr"], c["lin"])
        if k not in wl:
            wl[k] = charge.word_lift(c["pr"], c["lin"])
        w = wl[k]; tot = sum(c["barred"].values()); have = {x: m for x, m in c["barred"].items() if x in w}
        c["lift"] = (sum(m * w[x] for x, m in have.items()) / sum(have.values())) if have and sum(have.values()) >= 0.5 * tot else None
        c["charge"] = charge.dose(c["pr"])
    out = {}
    for dose in ("lift", "charge"):
        per = collections.defaultdict(list)
        for c in cs:
            if c[dose] is not None:
                per[c["lin"]].append(c)
        diffs = {q: [] for q in QTY}
        for v in per.values():
            if len(v) < 30:
                continue
            v = sorted(v, key=lambda c: c[dose]); k = len(v) // 3
            lo, hi = v[:k], v[2 * k:]
            for q in QTY:
                a = [c[q] for c in lo if c[q] is not None]; b = [c[q] for c in hi if c[q] is not None]
                if len(a) >= 5 and len(b) >= 5:
                    diffs[q].append(st.fmean(b) - st.fmean(a))
        out[dose] = {q: summ(v) for q, v in diffs.items()}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    gp = os.path.join(D, "context_gate.json")
    gate = json.load(open(gp)) if os.path.exists(gp) else None
    allc = cells(False)
    res = {"all": summarise(allc), "content_only": summarise(cells(True)), "by_dose": by_dose(allc), "gate": gate}
    f = lambda s: "--" if not s else "%+.4f [%+.4f, %+.4f] +%d/-%d of %d, p=%.2g" % (s["median"], s["iqr"][0], s["iqr"][1], s["pos"], s["neg"], s["n"], s["p"])
    L = ["# Fates and intensity as increments over the frame, in context (Jev)", "",
         "Producer `context_fates.py` (declared before the ratings finished and before the gate).", "",
         "Gate: %s" % (json.dumps(gate) if gate else "NOT RUN"), ""]
    for arm in ("all", "content_only"):
        r = res[arm]
        L += ["## %s (%d cells, %d lineages)" % ("all arrivals" if arm == "all" else "CONTENT-WORD arrivals only", r["n_cells"], r["n_lineages"]), ""]
        for q in QTY + ("proportionality_rho",):
            L.append("- %s: %s" % (q, f(r[q])))
        L.append("")
    for dose, r in res["by_dose"].items():
        L += ["## by %s, top minus bottom tercile" % dose, ""] + ["- %s: %s" % (q, f(r[q])) for q in QTY] + [""]
    md = "\n".join(L) + "\n"; print(md)
    if a.write:
        json.dump(res, open(OUT + ".json", "w"), indent=1); open(OUT + ".md", "w").write(md)


if __name__ == "__main__":
    main()
