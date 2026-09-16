"""Which USAS fields respond to DOSE? The field-level kill -> scream.

    python -u plot_fields.py --pub

## THE SOURCE IS THE LIFT-DOSE ARTIFACT, NOT THE TABLE IN THE README

`README.md`'s field table is n=153 under a TRANSGRESSIVENESS dose and the file
marks it **superseded and not to be cited** -- `dose.py` was restricted to
`endpoint_pairs()` and never re-run. This reads
`results/dose_lift_v4__fields_en__by_lineage.csv`: 45 lineages, 362 fields,
LIFT dose, current.

**AND THE TWO DISAGREE, WHICH THE FIGURE MUST NOT HIDE.** Of the eight fields
the README names, only the speech acts survive. `X3.2 Sensory: Sound` -- its
flagship, "which is what a scream IS" -- is a significant FALLER here
(-0.00067, 11/34, p=8e-04), and `T2++` flips sign too; `A10-` and `S3.2` go
flatly null (22/23, p=1.0). Different predictor and different n, so this is not
a refutation of that table -- but nothing from it may be quoted beside these
numbers, and no figure may mix them.

## WHAT SURVIVES IS STILL kill -> scream, THROUGH OTHER FIELDS

`L1-` (life and death, negative pole -- killing) is the largest faller of all
362 at -0.00766, 5 up / 40 down, p=7.9e-08, with `G3` warfare and `B1` anatomy
beside it; `Q2.1`/`Q2.2` speech acts are among the largest risers. The shape of
the claim is unchanged; the fields carrying it are not the ones on record.

## SELECTION IS DECLARED AND SYMMETRIC

Fields enter on p<0.001 AND coverage on at least 40 of the 45 lineages -- a
slope on 12 lineages is a fact about 12 models. Then the N largest risers and
the N largest fallers, which is a selection ON THE OUTCOME and is labelled as
one: these are the extremes of a 362-field sweep, not 2N independent tests.
"""
import argparse, csv, collections, json, math, os, random, statistics as st, sys

#: set by main() -- the axis must name which quantity was drawn, and the two
#: modes are different quantities, not two views of one
XLAB = ["Dose slope: change per unit of lift"]

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
FIGURES = os.path.join(HERE, "figures")
def paths(table):
    return (os.path.join(HERE, "results",
                         "dose_lift_v4__%s_en__by_lineage.csv" % table),
            os.path.join(HERE, "results", "dose_lift_v4__%s_en.csv" % table))


def load(table="fields", top=8, min_lin=40, pmax=0.001, drop_variants=True,
         panel=None):
    BYLIN, SUMM = paths(table)
    summ = {r["target"]: r for r in csv.DictReader(open(SUMM))}
    #: **THE CONTEXTUAL TABLE RATES ONE CONCEPT UNDER SEVERAL PANELS.**
    #: `directedness` appears as v6, v6_wide, v6full and slot_rating_en_v6 --
    #: four rows, one construct, three of them near-duplicates (-0.0252,
    #: -0.0513, -0.0525) and one that disagrees (-0.0159, p=0.55). Ranked
    #: together they occupy four of the top slots and read as four findings.
    #: One panel at a time, named on the axis, and the disagreement between
    #: panels is a fact about the instrument that belongs in its own check.
    if table == "contextual" and panel:
        summ = {t: r for t, r in summ.items() if t.split(":")[0] == panel}
    if drop_variants:
        #: **ONE ROW PER NORM, NOT THREE.** Every scale ships as `x`, `x_z` and
        #: `x_absz`, and they are not independent: `x_z` is the same quantity
        #: standardised, so plotting both doubles a result. `absz` is a
        #: DIFFERENT claim -- distance from the mean, i.e. narrowing, not
        #: direction -- and it can point the opposite way to its own parent
        #: (register rises at +0.0063 while register_absz falls at -0.0082,
        #: meaning register rises AND narrows). Keeping all three in one
        #: ranking reads as sixteen findings where there are six.
        summ = {t: r for t, r in summ.items()
                if not (t.endswith("_z") or t.endswith("_absz"))}
    per = collections.defaultdict(list)
    for r in csv.DictReader(open(BYLIN)):
        try:
            per[r["target"]].append(float(r["slope"]))
        except ValueError:
            pass
    keep = [t for t, s in summ.items()
            if float(s["p"]) < pmax and int(s["n"]) >= min_lin and t in per]
    keep.sort(key=lambda t: float(summ[t]["med_slope"]))
    #: **THE TWO SLICES OVERLAP WHEN THE SURVIVORS ARE FEWER THAN 2N.** On the
    #: levels table only 12 scales clear the gate, so `keep[:6] + keep[-6:]`
    #: returned six duplicated rows and pandas refused the categorical. It
    #: would otherwise have drawn each of them twice with no error at all.
    sel = keep if len(keep) <= 2 * top else keep[:top] + keep[-top:]
    rng = random.Random(23)
    out = []
    for t in sel:
        v = per[t]
        bs = sorted(st.median([v[rng.randrange(len(v))] for _ in v])
                    for _ in range(3000))
        out.append({"field": t, "med": st.median(v),
                    "sd": (st.pstdev(v) if len(v) > 1 else None),
                    "lo": bs[int(.025 * len(bs))], "hi": bs[int(.975 * len(bs)) - 1],
                    "up": int(summ[t]["up"]), "dn": int(summ[t]["dn"]),
                    "p": float(summ[t]["p"]), "n": len(v)})
    return out, len(summ), len(keep)


def load_marginal(table="levels", lang="en", top=8, pmax=0.01, min_eff=40,
                  drop_variants=True, panel=None):
    """The UNDOSED change, from `results/norm_stats.json`.

    **THE DECLARED STATISTIC, NOT A RECOMPUTATION.** Per lineage this is the
    MEDIAN OVER PROMPTS of `(aligned - base)` -- paired within prompt -- which
    is what `norm_stats.json` stores and what the README's result table reports.
    The arm-level figure (`plot_arms.py`) takes median(base) and median(aligned)
    separately because a slopegraph needs two drawable levels; the two are
    different statistics and this file uses the declared one.

    **TIES ARE EXCLUDED AND `effective_n` IS THE GATE.** A sparse scale can be
    tied on 38 of 50 lineages -- `brooke_formality` is -- and its sign test then
    rests on 12. Counting those ties as successes is the defect this folder
    fixed before its numbers were read, and a figure that ranked on `median`
    without reading `effective_n` would reintroduce it silently.
    """
    d = json.load(open(os.path.join(HERE, "results", "norm_stats.json")))
    rows = []
    for v in d["values"]:
        if v.get("table") != table or v.get("lang") != lang:
            continue
        sc = v["scale"]
        if drop_variants and (sc.endswith("_z") or sc.endswith("_absz")):
            continue
        #: **THE PANEL FILTER IS FOR THE CONTEXTUAL TABLE ONLY.** Applied
        #: blind it also tests `warriner_valence`, which has no colon, so
        #: `split(":")[0]` returns the whole name and every LEVELS scale is
        #: silently dropped -- a combined figure that showed only contextual
        #: rows and reported no error.
        if panel and table == "contextual" and sc.split(":")[0] != panel:
            continue
        if v.get("effective_n", 0) < min_eff or v.get("p_sign", 1) >= pmax:
            continue
        #: `per_lineage` is a {lineage: value} DICT, not a list -- indexing it
        #: positionally for the bootstrap silently drew lineage NAMES and died
        #: in the median. Values only.
        _pl = v.get("per_lineage") or {}
        per = [x for x in (_pl.values() if isinstance(_pl, dict) else _pl)
               if isinstance(x, (int, float))]
        if len(per) < 5:
            continue
        rng = random.Random(29)
        bs = sorted(st.median([per[rng.randrange(len(per))] for _ in per])
                    for _ in range(3000))
        rows.append({"field": sc, "med": v["median"],
                     "sd": (st.pstdev(per) if len(per) > 1 else None),
                     "lo": bs[int(.025 * len(bs))], "hi": bs[int(.975 * len(bs)) - 1],
                     "up": v["up"], "dn": v["down"], "p": v["p_sign"],
                     "n": v["effective_n"]})
    rows.sort(key=lambda r: r["med"])
    n_all = len(rows)
    if len(rows) > 2 * top:
        rows = rows[:top] + rows[-top:]
    return rows, n_all, n_all


def _std(rows):
    """Add `z`: the effect in units of its own BETWEEN-LINEAGE SD.

    **RAW SLOPES FROM DIFFERENT SCALES CANNOT SHARE AN AXIS.** Warriner runs
    1-9, Brysbaert concreteness 1-5, the k_* lexicons 1-7 and the v6 panel
    rates constructs 1-7 -- so -0.04 on `warriner_arousal` and -0.04 on
    `v6:harm` are different quantities wearing one number, and ranking them
    together silently ranks the scales' units. Dividing by the SD of that
    scale's own per-lineage values gives "how large against how much the
    lineages differ", which is comparable and is what the sign test is
    implicitly using anyway.

    It is NOT a correlation and NOT Cohen's d on a paired difference; it is a
    location over a spread, and a scale with 45 tight lineages will score
    higher than one with 45 loose ones at the same raw effect. That is the
    intended behaviour and it is the whole reason the axis is labelled in SDs.
    """
    out = []
    for r in rows:
        sd = r.get("sd")
        if not sd:
            continue
        out.append(dict(r, z=r["med"] / sd,
                        zlo=r["lo"] / sd, zhi=r["hi"] / sd))
    return out


def load_combined(marginal=False, top=999, pmax=1.01, min_lin=40, panel=None):
    """levels + contextual in one frame, standardised. -> rows"""
    rows = []
    for table in ("levels", "contextual"):
        got, _, _ = (load_marginal(table=table, top=999, pmax=pmax,
                                   min_eff=min_lin, panel=panel)
                     if marginal else
                     load(table=table, top=999, pmax=pmax, min_lin=min_lin,
                          panel=panel))
        for r in got:
            r["table"] = table
        rows += got
    rows = _std(rows)
    rows.sort(key=lambda r: r["z"])
    if len(rows) > 2 * top:
        rows = rows[:top] + rows[-top:]
    return rows


def draw(rows, out_path, pub=False):
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_vline, geom_point, geom_errorbarh,
                          labs, scale_y_discrete, theme_minimal, theme,
                          element_text, ggtitle)
    from malignment.figure import PUB_RED, PUB_BLUE, PUB_RULE_PT, pub_theme
    f = pd.DataFrame(rows)
    f["dir"] = ["rises" if x > 0 else "falls" for x in f["med"]]
    _key = "z" if "z" in f.columns else "med"
    #: the contextual rows keep their panel prefix so the two sources stay
    #: distinguishable on one axis without a second legend
    f["field"] = pd.Categorical(f["field"],
                                categories=list(f.sort_values(_key)["field"]))
    xcol = "z" if "z" in f.columns else "med"
    lo, hi = ("zlo", "zhi") if xcol == "z" else ("lo", "hi")
    p = (ggplot(f, aes(xcol, "field", color="dir"))
         #: zero is the claim's boundary, so it is a rule and not a gridline
         + geom_vline(xintercept=0.0, color="black", size=PUB_RULE_PT)
         + geom_errorbarh(aes(xmin=lo, xmax=hi), height=0.0,
                          size=PUB_RULE_PT)
         + geom_point(size=1.4)
         + labs(x=XLAB[0],
                y="", color="")
         + theme(legend_position="none"))
    from plotnine import scale_color_manual
    p = p + scale_color_manual({"rises": PUB_BLUE, "falls": PUB_RED}, guide=None)
    p = p + (pub_theme(height=max(3.6, 0.16 * len(rows)), grid="none") if pub else
             (ggtitle("USAS fields responding to lift dose, 45 lineages")
              + theme_minimal() + theme(figure_size=(8, 5),
                                        plot_title=element_text(size=11, weight="bold"))))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    p.save(out_path, dpi=300, verbose=False)
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--table", default="fields",
                    choices=["fields", "levels", "contextual"])
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--pmax", type=float, default=0.001)
    ap.add_argument("--panel", default=None,
                    help="contextual only: keep one rating panel (v6, v6_wide, "
                         "v6full, slot_rating_en_v6, slot_institutional_en_v3, "
                         "sexual_slot_en_v2). Several panels rate the SAME "
                         "construct and ranking them together counts one "
                         "finding up to four times.")
    ap.add_argument("--variants", action="store_true",
                    help="keep the _z and _absz variants of each norm")
    ap.add_argument("--combine", action="store_true",
                    help="levels AND contextual on one axis, standardised by "
                         "each scale's between-lineage SD because their raw "
                         "units are not commensurable")
    ap.add_argument("--all", action="store_true",
                    help="EXPLORATORY: every scale that clears the coverage "
                         "gate, no p filter and no top-N. For looking, not for "
                         "publishing -- the p column is uncorrected and the "
                         "sweep is 42 levels / 82 contextual scales wide.")
    ap.add_argument("--marginal", action="store_true",
                    help="the UNDOSED change: median over prompts of "
                         "(aligned - base) per lineage, from norm_stats.json")
    ap.add_argument("--pub", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.all:
        a.pmax = 1.01
        a.top = 999
    if a.combine:
        rows = load_combined(marginal=a.marginal, top=a.top, pmax=a.pmax,
                             panel=a.panel)
        n_all = n_keep = len(rows)
    elif a.marginal:
        rows, n_all, n_keep = load_marginal(
            table=a.table, top=a.top, pmax=a.pmax,
            drop_variants=not a.variants, panel=a.panel)
    else:
        rows, n_all, n_keep = load(table=a.table, top=a.top, pmax=a.pmax,
                               drop_variants=not a.variants, panel=a.panel)
    print("%d fields swept, %d clear p<0.001 and >=40 lineages, showing %d"
          % (n_all, n_keep, len(rows)))
    print("%-8s %11s %9s %10s" % ("field", "med slope", "up/dn", "p"))
    for r in sorted(rows, key=lambda x: -x["med"]):
        print("%-8s %+11.5f %9s %10.1e"
              % (r["field"], r["med"], "%d/%d" % (r["up"], r["dn"]), r["p"]))
    XLAB[0] = (("Change, aligned − base" if a.marginal else
                "Dose slope, per unit of lift")
               + (" (between-lineage SDs)" if a.combine else ""))
    out = a.out or os.path.join(
        FIGURES, ("%s%s_" + ("marginal" if a.marginal else "dose") + "%s.png")
        % (a.table, "_" + a.panel if a.panel else "", "_pub" if a.pub else ""))
    print("\nwrote %s" % draw(rows, out, pub=a.pub))


if __name__ == "__main__":
    main()
