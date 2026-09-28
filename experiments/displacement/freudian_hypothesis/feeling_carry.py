"""Does the arriving mass keep the barred word's FEELING, or the scene's? -> results/feeling_carry.md, .json

    python -u feeling_carry.py            print
    python -u feeling_carry.py --write

The qualitative companion to `proportionality.py`, declared 2026-09-28 before it was run.
That file found the arriving affect sits at the scene's LEVEL whatever the barred word
carried. Level is not kind: an anger word could be replaced by an equally intense fear word.
`feeling_matrix.py` answers "what does the frame's feeling become, base -> aligned" at frame
grain from the fates coder; it cannot separate the barred word's feeling from the scene's,
because it has one feeling per side. The affect task (`slot_ratings/affect`, 56,060 ratings,
`run_proportionality.py`) names a feeling for the FRAME, for each BARRED departing word and for
each ARRIVAL, so the two can be set against each other.

## THE QUANTITIES, per (lineage, charged English prompt), 50 endpoint lineages

    b    barred departing mass (act >= 4) by named feeling, normalised
    a    arriving mass by named feeling, normalised
    f    the frame's own feeling (the fragment rated with no word)
    gate rated words carry >= 80% of the barred and of the arriving mass; frame rated;
         echo-correct, ratable rows only (the contextual arm's gate)

    CARRY     O = sum_k b_k a_k: a unit of what left and a unit of what arrived share a
              feeling
    SCENE     E = sum_k b_k abar_k, abar = the mean arriving distribution over this
              lineage's OTHER gated cells whose frame has the SAME feeling (leave-one-out):
              what the arrivals' feeling would match if it were set by the scene alone
    TEST      per lineage the mean of O - E over cells; median over lineages, two-sided
              sign test, ties dropped. O - E > 0: the barred word's feeling is carried
              beyond what the scene predicts. ~0: arrivals take the scene's feeling.

**THE DECISIVE CELLS** are those where the barred word's dominant feeling DIFFERS from the
frame's (e.g. an anger word in a fear scene): there, per lineage, the share of arriving mass
with the BARRED feeling against the share with the FRAME's feeling, sign test on the
difference. Freud's displacement carries the barred word's affect; a scene account carries
the frame's.

Reported beside: the pooled mass-weighted matrix barred feeling -> arriving feeling, and the
suppression share (arriving mass `none` where the barred mass carried a feeling).

## THE TYPE ARMS, declared 2026-09-28 before the type ratings existed (RH)

The contextual rater sees the fragment, so a mild substitute may be given the scene's feeling:
"takes the scene's feeling" and "has none of its own" read the same. `slot_ratings/affect/
type_task.py` rates each word ALONE, twice in one call -- `doer_feeling` (the person who
performs or undergoes it: the Freudian question, the barred subject's affect) and
`evoked_feeling` (what it provokes in a witness or reader) -- because no single wording fixed a
feeling for act words (`kill` came back anger, fear and none under three wordings). Each is a
separate arm; neither is pooled with the other or with the contextual arm.

    b, a       as above, from the words' TYPE feelings (ratable words only)
    s          the SCENE, now built from words too: the cell's NON-barred base words, p_base-
               weighted, by type feeling -- no frame rating exists at type level
    gate       rated words carry >= 80% of the barred, the arriving and the non-barred base mass
    CARRY      O - S, S = sum_k b_k s_k: arrivals share the barred word's type feeling beyond
               what the rest of the scene's own words share with it
    DECISIVE   cells where the barred mass's dominant NAMED feeling differs from the scene's
               dominant NAMED feeling (`none` excluded from both modes, since most words carry
               none): arriving share with the barred feeling minus share with the scene's

Freud's displacement (doer arm): CARRY > 0 and DECISIVE > 0 -- anger words replaced by anger
words even where the scene's words carry another feeling.
"""
import argparse, collections, csv, gzip, json, os, statistics as st, sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
AFFECT = os.path.expanduser("~/malignment-data/affect_proportionality/affect_proportionality.parquet")
OUT = os.path.join(HERE, "results", "feeling_carry")
MIN_ACT, COVER = 4.0, 0.80
FEEL = ["anger", "fear", "desire", "grief", "disgust", "shame", "tenderness", "joy", "none"]


def sign_p(v):
    v = [x for x in v if x != 0]
    n = len(v); k = sum(1 for x in v if x > 0); k = min(k, n - k)
    return min(1.0, sum(comb(n, i) for i in range(k + 1)) * 2 / 2 ** n) if n else float("nan")


def summ(v):
    v = [x for x in v if x == x]
    q = st.quantiles(v, n=4)
    return dict(median=st.median(v), iqr=[q[0], q[-1]], pos=sum(x > 0 for x in v), neg=sum(x < 0 for x in v), n=len(v), p=sign_p(v))


def compute():
    import pyarrow.parquet as pq
    from departing_arriving import norms
    from malignment import roster
    F, _ = norms()
    wf, ff = {}, {}
    for r in pq.read_table(AFFECT).to_pylist():
        if not r["ok"] or not r.get("echo_ok"):
            continue
        if r["word"] is None:
            ff[r["prompt"]] = r["feeling"]
        elif r.get("ratable"):
            wf[(r["prompt"], r["word"])] = r["feeling"]
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    kc = {}

    def act(w):
        if w not in kc:
            k = F.k(w) or {}
            kc[w] = max(float(k.get("bodily_harm", 0) or 0), float(k.get("transgressiveness", 0) or 0)) if k else None
        return kc[w]
    cell = collections.defaultdict(lambda: dict(bt=0.0, at=0.0, b=collections.Counter(), a=collections.Counter()))
    with gzip.open(SRC, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lang"] != "en" or (r["base"], r["aligned"]) not in pairs:
                continue
            d = float(r["delta"]); w = r["word"]; pr = r["prompt"]
            x = act(w)
            barred = d < 0 and x is not None and x >= MIN_ACT
            if not barred and d <= 0:
                continue
            c = cell[(r["base"], pr)]
            fe = wf.get((pr, w))
            if barred:
                c["bt"] += -d
                if fe:
                    c["b"][fe] += -d
            else:
                c["at"] += d
                if fe:
                    c["a"][fe] += d
    gated = collections.defaultdict(list)
    for (lin, pr), c in cell.items():
        if pr not in ff or c["bt"] <= 0 or c["at"] <= 0:
            continue
        sb, sa = sum(c["b"].values()), sum(c["a"].values())
        if sb < COVER * c["bt"] or sa < COVER * c["at"] or sb <= 0 or sa <= 0:
            continue
        b = {k: v / sb for k, v in c["b"].items()}; a = {k: v / sa for k, v in c["a"].items()}
        gated[lin].append((pr, ff[pr], b, a))
    per_lin, decisive, matrix, supp = {}, {}, collections.defaultdict(float), []
    for lin, cells in gated.items():
        byf = collections.defaultdict(list)
        for i, (_, f, _, a) in enumerate(cells):
            byf[f].append(i)
        diffs, dec = [], []
        for i, (pr, f, b, a) in enumerate(cells):
            others = [j for j in byf[f] if j != i]
            if not others:
                continue
            abar = collections.Counter()
            for j in others:
                for k, v in cells[j][3].items():
                    abar[k] += v / len(others)
            O = sum(b.get(k, 0) * a.get(k, 0) for k in FEEL)
            E = sum(b.get(k, 0) * abar.get(k, 0) for k in FEEL)
            diffs.append(O - E)
            db = max(b, key=b.get)
            if db != f:
                dec.append(a.get(db, 0) - a.get(f, 0))
            for kb, vb in b.items():
                for ka, va in a.items():
                    matrix[(kb, ka)] += vb * va
            fb = 1 - b.get("none", 0)
            if fb > 0.5:
                supp.append(a.get("none", 0))
        if len(diffs) >= 15:
            per_lin[lin] = st.fmean(diffs)
        if len(dec) >= 5:
            decisive[lin] = st.fmean(dec)
    return dict(carry=summ(list(per_lin.values())), decisive=summ(list(decisive.values())),
                n_cells=sum(len(v) for v in gated.values()), n_decisive_lineages=len(decisive),
                suppression_share_median=st.median(supp) if supp else None, n_supp_cells=len(supp),
                matrix={"%s->%s" % k: v for k, v in matrix.items()})


def report(r):
    f = lambda s: "%+.3f [%+.3f, %+.3f] +%d/-%d of %d, p=%.2g" % (s["median"], s["iqr"][0], s["iqr"][1], s["pos"], s["neg"], s["n"], s["p"])
    L = ["# Does the arriving mass keep the barred word's feeling, or the scene's?", "",
         "Producer `feeling_carry.py` (design in its docstring, declared before it ran). %d gated (lineage, prompt) cells." % r["n_cells"], "",
         "- **CARRY beyond the scene**, O - E per lineage: %s" % f(r["carry"]),
         "- **DECISIVE cells** (barred word's feeling differs from the frame's; %d lineages with >= 5): share of arriving mass with the BARRED feeling minus share with the FRAME's feeling: %s" % (r["n_decisive_lineages"], f(r["decisive"])),
         "- **Suppression**: where the barred mass carried a feeling (> 50%% named), median share of arriving mass rated `none`: %.2f over %d cells" % (r["suppression_share_median"], r["n_supp_cells"]), "",
         "Pooled matrix, barred feeling (rows) -> arriving feeling (columns), each cell's joint mass summed over cells, row-normalised:", "",
         "| barred \\ arriving | " + " | ".join(FEEL) + " | row mass |", "|---|" + "---|" * (len(FEEL) + 1)]
    M = collections.defaultdict(dict)
    for k, v in r["matrix"].items():
        a, b = k.split("->"); M[a][b] = v
    for a in FEEL:
        tot = sum(M[a].values())
        if tot <= 0:
            continue
        L.append("| %s | %s | %.0f |" % (a, " | ".join(("**%.2f**" if b == a else "%.2f") % (M[a].get(b, 0) / tot) for b in FEEL), tot))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    r = compute(); md = report(r); print(md)
    if a.write:
        json.dump(r, open(OUT + ".json", "w"), indent=1); open(OUT + ".md", "w").write(md)


if __name__ == "__main__":
    main()
