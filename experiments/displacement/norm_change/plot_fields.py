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
#: `dose.py --min-cov 0.20 --out results/dose_lift_v4_cov20` writes here. The
#: gated tables live in their OWN DIRECTORY under the same filenames rather
#: than under suffixed ones: a suffix in a filename is a parameter encoded in a
#: path, and this folder already has `dose_lift__*` beside `dose_lift_v4__*`
#: with nothing in either name saying which is current.
#: **THE GATE IS PER TABLE, AND ONE NUMBER CANNOT SERVE BOTH.** `coverage`
#: means different things in the two tables. For a LEXICON norm it is the share
#: of the distribution the lexicon can rate at all -- 61-82%, so 0.20 is a mild
#: filter. For a USAS FIELD it is that single field's own share of the
#: probability mass, whose mean is 0.0136 and of which only 0.89% of rows clear
#: 0.20. Applying the levels gate to fields took 362 fields to 9, and the two
#: that carry the result -- `L1-` (killing) and `G3` (warfare) -- vanished
#: entirely while grammatical categories like `A9+` and `B1` survived, because
#: the gate was selecting for fields big enough to be function words.
#:
#: 0.01 keeps 127 fields at n>=40 and returns every field the story rests on at
#: the full 50 lineages. Both numbers are declared choices, not discoveries.
GATE_DIR = {"levels": "dose_lift_v4_cov20", "contextual": "dose_lift_v4_cov20",
            "fields": "dose_lift_v4_cov01"}
GATE_VAL = {"levels": 0.20, "contextual": 0.20, "fields": 0.01}

#: **THESE ARE NOT NORMS AND MUST NOT BE RANKED BESIDE THEM.** The contextual
#: table carries the v6 instrument's own bookkeeping alongside its ratings:
#: `n_eligible` is the eligibility COUNT that `slot_ratings/corpus.py` gates on
#: (`n_eligible >= 3`), `n_present` is how many of those were rated, and
#: `net` / `net_rate` / `rise` / `fall` count movers. They answer
#: `rate_and_magnitude`'s question -- how much moves and how often -- not this
#: folder's, which is what KIND of word the mass lands on.
#:
#: Left in, they dominate: `v6:fall` came out at -0.412 in the marginal
#: combined figure against -0.028 for `warriner_arousal`, because a count and a
#: 1-7 rating are different quantities and standardising by between-lineage SD
#: does not make them the same one. It ranked first and it is not a norm.
NOT_NORMS = {"net", "net_rate", "rise", "fall", "n_present", "n_eligible"}

#: **`_absz` IS A SECOND CLAIM ONLY WHERE THE NORM CAN DEVIATE BOTH WAYS.**
#: `|z|` is distance from the mean, so on a norm pinned at its floor it is the
#: level again with a sign flip. Measured per norm as the Pearson correlation
#: between the per-lineage values of `x` and `x_absz`:
#:
#:     k_vulgarity          base 1.00   r = 1.000   IDENTICAL
#:     k_bodily_harm        base 1.04   r = 0.997
#:     k_transgressiveness  base 1.05   r = 0.997
#:     k_register_level     base 3.94   r = -0.851
#:     k_valence            base 4.00   r = -0.119   distinct
#:     warriner_arousal     base 4.00   r = +0.121   distinct
#:     warriner_valence     base 5.40   r = -0.152   distinct
#:
#: Drawn together, the floor-bound pairs are ONE POINT PLOTTED TWICE -- they
#: overprint in the scatter and double-count in the falling cluster of every
#: ranked figure. Computed from the artifact rather than hand-listed, so a new
#: norm is classified by its own data and a norm that changes behaviour is
#: reclassified without anyone remembering to.
ABSZ_REDUNDANT_R = 0.95
#: **THE FIGURE CARRIES NO n AT ALL.** Two ways of putting it in were tried
#: and both rejected (RH, 2026-09-16): sizing the points needs a legend, which
#: is the crowding it was meant to avoid, and `(n=8)` in the label is noise on
#: a figure whose labels are already long. The per-scale detail goes in the
#: CAPTION instead -- `--table-out` prints it -- and the figure stays a
#: picture of two quantities.
#:
#: **AND n IS NOT THE WHOLE STORY OF THINNESS ANYWAY**, which is the argument
#: for prose over a mark: Vulgarity's 8 movers all point one way (p=0.008)
#: while Vocalization's 29 split 22 down against 7 up (p=0.008). Same n-band,
#: quite different evidence, and no single visual channel says that.

#: **THE SCALE NAMES ARE SOURCE IDENTIFIERS, NOT LABELS.** `k_bodily_harm` and
#: `warriner_valence` name the LEXICON as well as the construct, which a figure
#: needs when two lexicons disagree -- `k_concreteness` falls and
#: `brysbaert_concreteness` does not -- and which is noise everywhere else. So
#: the construct is the label and the source is parenthesised, kept rather than
#: dropped: "concreteness" alone would make the disagreement invisible.
#:
#: `_absz` becomes "spread", because |z| is DISPERSION and reading it as a
#: level is the misreading the suffix invites -- `valence` rising while
#: `valence spread` falls is sweetening AND narrowing, not a contradiction.
_SRC = {"k_": "k", "warriner_": "Warriner", "brysbaert_": "Brysbaert",
        "brooke_": "Brooke", "concreteness_zh": "zh"}
#: US spelling: the paper is for an American journal. Applied at the LABEL
#: only -- the scale id stays `v6:vocalisation`, because renaming the key would
#: break every join against the artifacts and the annotation.
_US = {"vocalisation": "vocalization", "normalisation": "normalization"}
_PRETTY = {"k_register_level": "register", "warriner_valence_extremity":
           "valence extremity", "v6:makes_better": "makes better",
           "v6:makes_worse": "makes worse", "v6:n_present": "n present"}


#: **ONE SOURCE PER CONSTRUCT, CHOSEN, NOT AVERAGED.** Two lexicons measure
#: valence and two measure concreteness. RH's ruling 2026-09-16: keep
#: Warriner's valence (the published norm) and the `k_` concreteness, and
#: footnote the concreteness discrepancy in the text rather than carrying two
#: dots for it. `brysbaert_concreteness` is NULL (p=0.48) where `k_` falls at
#: p=0.033, so this is a CHOICE and the figure must not be read as though the
#: measurement were unanimous.
DROP_SCALES = {"k_valence", "k_valence_absz",
               "brysbaert_concreteness", "brysbaert_concreteness_absz"}


def _constructs(scales):
    """{construct: n sources}. Which names need their source shown."""
    seen = collections.defaultdict(set)
    for sc in scales:
        nm = pretty(sc)                      # no disambiguation: the bare name
        nm = nm[:-7] if nm.endswith(" spread") else nm
        src = sc.split(":")[0] if ":" in sc else sc.split("_")[0]
        seen[nm.lower()].add(src)
    return {k for k, v in seen.items() if len(v) > 1}


def pretty(scale, disambiguate=frozenset()):
    """`k_bodily_harm_absz` -> `Bodily harm spread`.

    **THE SOURCE IS SHOWN ONLY WHERE TWO SOURCES MEASURE THE SAME CONSTRUCT.**
    `(k)` and `(Warriner)` on every label is noise a reader has to carry; on
    the two constructs that ARE measured twice it is the whole point, because
    the two sources DISAGREE -- `concreteness (k)` falls at p=0.033 while
    `concreteness (Brysbaert)` is null at p=0.48. Dropping the suffix there
    would silently merge a disagreement into one ambiguous dot; keeping it
    everywhere else buys nothing. `disambiguate` is the set of constructs the
    caller found duplicated, computed from the rows actually drawn rather than
    hardcoded, so a figure with only one concreteness in it says
    "Concreteness".
    """
    sc, spread = (scale[:-5], True) if scale.endswith("_absz") else (scale, False)
    src = None
    if ":" in sc:
        inst, sc = sc.split(":", 1)
        src = None if inst.startswith("v6") else inst
    else:
        for pre, nm in _SRC.items():
            if sc.startswith(pre) and pre.endswith("_"):
                sc, src = sc[len(pre):], nm
                break
    name = _PRETTY.get(scale, _PRETTY.get(sc, sc.replace("_", " ")))
    bare = name
    if spread:
        name += " spread"
    #: sentence case: the construct is a label, not an identifier, and a
    #: lowercase run-in reads as code in a figure that has no other code in it
    for k, v in _US.items():
        name = name.replace(k, v)
    name = name[:1].upper() + name[1:]
    return ("%s (%s)" % (name, src)
            if src and bare in disambiguate else name)


def _absz_redundant(gated=True):
    """{scale} whose `_absz` duplicates its parent. Measured, not declared."""
    import statistics as _st
    out = set()
    for table in ("levels", "contextual"):
        fp = os.path.join(HERE, "results", "%s_gated_en.json" % table)
        if not os.path.exists(fp):
            continue
        S = {r["scale"]: r for r in json.load(open(fp))["scales"]}
        for sc, r in S.items():
            b = S.get(sc + "_absz")
            if not b:
                continue
            ks = sorted(set(r["per_lineage"]) & set(b["per_lineage"]))
            if len(ks) < 10:
                continue
            a1 = [r["per_lineage"][k] for k in ks]
            a2 = [b["per_lineage"][k] for k in ks]
            m1, m2 = _st.fmean(a1), _st.fmean(a2)
            d1 = sum((x - m1) ** 2 for x in a1) ** .5
            d2 = sum((y - m2) ** 2 for y in a2) ** .5
            if not d1 or not d2:
                out.add(sc + "_absz")
                continue
            r_ = sum((x - m1) * (y - m2) for x, y in zip(a1, a2)) / (d1 * d2)
            if abs(r_) >= ABSZ_REDUNDANT_R:
                out.add(sc + "_absz")
    return out


def paths(table, gated=False):
    d = (os.path.join(HERE, "results", GATE_DIR[table]) if gated
         else os.path.join(HERE, "results"))
    return (os.path.join(d, "dose_lift_v4__%s_en__by_lineage.csv" % table),
            os.path.join(d, "dose_lift_v4__%s_en.csv" % table))


def load(table="fields", top=8, min_lin=40, pmax=0.001, drop_variants=True,
         panel=None, gated=False):
    BYLIN, SUMM = paths(table, gated)
    summ = {r["target"]: r for r in csv.DictReader(open(SUMM))}
    #: **THE CONTEXTUAL TABLE RATES ONE CONCEPT UNDER SEVERAL PANELS.**
    #: `directedness` appears as v6, v6_wide, v6full and slot_rating_en_v6 --
    #: four rows, one construct, three of them near-duplicates (-0.0252,
    #: -0.0513, -0.0525) and one that disagrees (-0.0159, p=0.55). Ranked
    #: together they occupy four of the top slots and read as four findings.
    #: One panel at a time, named on the axis, and the disagreement between
    #: panels is a fact about the instrument that belongs in its own check.
    if table == "contextual":
        summ = {t: r for t, r in summ.items()
                if t.split(":")[-1] not in NOT_NORMS
                and (not panel or t.split(":")[0] == panel)}
    if drop_variants:
        #: **ONE ROW PER NORM, NOT THREE.** Every scale ships as `x`, `x_z` and
        #: `x_absz`, and they are not independent: `x_z` is the same quantity
        #: standardised, so plotting both doubles a result. `absz` is a
        #: DIFFERENT claim -- distance from the mean, i.e. narrowing, not
        #: direction -- and it can point the opposite way to its own parent
        #: (register rises at +0.0063 while register_absz falls at -0.0082,
        #: meaning register rises AND narrows). Keeping all three in one
        #: ranking reads as sixteen findings where there are six.
        #: **DROP `_z`, KEEP `_absz`.** They are not the same kind of
        #: duplicate. `x_z` is x standardised -- the same claim twice, and
        #: plotting both doubles a result. `x_absz` is |z|, DISTANCE FROM THE
        #: MEAN, which is a different claim and can point the opposite way to
        #: its own parent: valence rises (+0.0114) while `valence_absz` falls
        #: (-0.0057), i.e. alignment sweetens AND narrows. Collapsing both
        #: suffixes together deleted the narrowing result from every figure in
        #: this file, which is H5 -- a declared hypothesis.
        _red = _absz_redundant()
        summ = {t: r for t, r in summ.items()
                if not t.endswith("_z") and t not in _red}
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
                  drop_variants=True, panel=None, gated=False):
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
    #: **THE GATED FILE IS A DIFFERENT POPULATION, NOT A CLEANER READING.**
    #: `norm_stats.json` is the DECLARED marginal artifact over every rated
    #: row; `levels_gated_en.json` keeps only rows where BOTH arms cover >=20%
    #: of the distribution, and drops `brooke_formality` by name. It carries
    #: its own `gate` and `excluded_by_name`, so a figure drawn from it must
    #: say so -- two points at the same p from these two files are not the same
    #: claim, and the gated one is computed on 61-82% of the prompts.
    if gated:
        #: **KEYED BY THE TABLE ASKED FOR.** This used to open levels_gated
        #: unconditionally and stamp every row `table="levels"`, so a caller
        #: asking for `contextual` matched nothing and got an EMPTY list back.
        #: `--combine --marginal --gated` then drew a levels-only chart under a
        #: name containing `v6`, with no error anywhere: an empty filter and a
        #: strict gate are indistinguishable in the output.
        gp = os.path.join(HERE, "results", "%s_gated_en.json" % table)
        if not os.path.exists(gp):
            raise SystemExit(
                "no gated artifact for table %r (%s).\n"
                "Build it:  python gated_levels.py --table %s" % (table, gp, table))
        g = json.load(open(gp))
        d = {"values": [dict(v, table=table, lang="en") for v in g["scales"]]}
    else:
        d = json.load(open(os.path.join(HERE, "results", "norm_stats.json")))
    _REDUNDANT = _absz_redundant() if drop_variants else set()
    rows = []
    for v in d["values"]:
        if v.get("table") != table or v.get("lang") != lang:
            continue
        sc = v["scale"]
        if drop_variants and sc.endswith("_z") and not sc.endswith("_absz"):
            continue
        if drop_variants and sc in _REDUNDANT:
            continue
        #: **THE PANEL FILTER IS FOR THE CONTEXTUAL TABLE ONLY.** Applied
        #: blind it also tests `warriner_valence`, which has no colon, so
        #: `split(":")[0]` returns the whole name and every LEVELS scale is
        #: silently dropped -- a combined figure that showed only contextual
        #: rows and reported no error.
        if table == "contextual" and sc.split(":")[-1] in NOT_NORMS:
            continue
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
        #: **A THIN ROW IS MARKED, NOT DELETED.** Dropping everything below
        #: `min_eff` is what made `v6:vocalisation` and `v6:harm` look like
        #: scales nobody had tested, when they had been tested and had tied.
        #: The count rides on the label so the reader discounts the row instead
        #: of never seeing it.
        _lab = sc if v.get("effective_n", 0) >= 40 else (
            "%s  (n=%d)" % (sc, v.get("effective_n", 0)))
        rows.append({"field": _lab, "med": v["median"],
                     "up": v.get("up", 0), "dn": v.get("down", 0),
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


def load_combined(marginal=False, top=999, pmax=1.01, min_lin=40, panel=None,
                  gated=False):
    """levels + contextual in one frame, standardised. -> rows

    **BOTH SIDES MUST SHARE A GATE OR THIS REFUSES.** The marginal artifact is
    coverage-gated at 0.20 by `gated_levels.py` and the dose tables are gated
    only when `dose.py --min-cov 0.20` has been run into `dose_lift_v4_cov20/`.
    Drawing one axis from a gated population and an ungated one puts two
    different denominators under one ranking, which is unreadable and looks
    fine. If the gated dose tables are absent, say so rather than quietly
    falling back to the ungated ones.
    """
    if gated and not marginal:
        missing = [t for t in ("levels", "contextual")
                   if not os.path.exists(paths(t, True)[0])]
        if missing:
            raise SystemExit(
                "--combine --gated needs the gated dose tables for %s.\n"
                "Build them:  python dose.py --lift-dose --rule-version 4 "
                "--table <t> --lang en --min-cov 0.20 --per-lineage "
                "--out results/dose_lift_v4_cov20" % ", ".join(missing))
    rows = []
    for table in ("levels", "contextual"):
        got, _, _ = (load_marginal(table=table, top=999, pmax=pmax,
                                   min_eff=min_lin, panel=panel, gated=gated)
                     if marginal else
                     load(table=table, top=999, pmax=pmax, min_lin=min_lin,
                          panel=panel, gated=gated))
        for r in got:
            r["table"] = table
        rows += got
    rows = _std(rows)
    rows.sort(key=lambda r: r["z"])
    if len(rows) > 2 * top:
        rows = rows[:top] + rows[-top:]
    return rows


def _adjust(ps, method):
    """Multiplicity-adjust one axis's p-values. -> list, same order

    **WITHIN AXIS, NOT ACROSS BOTH.** The 29 dose slopes are one family of
    tests and the 29 marginal sign tests are another; they are different
    statistics on different quantities and a scale enters the figure by
    clearing its own axis. Pooling all 58 would make a scale's admission
    depend on how many OTHER scales were measured on the other instrument.

    `holm` controls the family-wise error rate -- the chance of ANY false
    positive -- which is the guarantee you want when one claim rests on one
    test. This figure makes no per-scale claim, so `bh` (Benjamini-Hochberg,
    false discovery rate) is the fitted one: it asks what share of the points
    shown are expected to be spurious.
    """
    n = len(ps)
    if method == "none" or n == 0:
        return list(ps)
    if method == "holm":
        order = sorted(range(n), key=lambda i: ps[i])
        out, run = [0.0] * n, 0.0
        for k, i in enumerate(order):
            run = max(run, (n - k) * ps[i])
            out[i] = min(1.0, run)
        return out
    if method == "bh":
        #: step-UP from the largest p, enforcing monotonicity downward
        order = sorted(range(n), key=lambda i: ps[i], reverse=True)
        out, run = [0.0] * n, 1.0
        for k, i in enumerate(order):
            run = min(run, n * ps[i] / (n - k))
            out[i] = min(1.0, run)
        return out
    raise SystemExit("unknown correction %r" % method)


def load_xy(pmax=1.01, min_lin=0, panel="v6", gated=True, sig="either",
            alpha=0.01, correct="none"):
    """Every scale on BOTH axes: dose slope against marginal change. -> rows

    **THE TWO FIGURES WERE ALWAYS A PAIR AND THIS IS THE PAIR.** A dose slope
    says how alignment's effect on a norm SCALES with the prompt's lift; it
    says nothing about whether the norm moved at all, because `dose.py` fits
    slopes and never records an intercept. Read alone it gets glossed as
    "alignment promoted this", and for `k_charge` (marginal exactly 0.000,
    25/25) and `v6:vocalisation` (21 of 50 lineages tied, marginal median
    exactly 0.000) that is simply false. Plotting one against the other makes
    the four cases separable by eye.

    **THE TIE COUNT IS GATED-POPULATION.** This line said "44 of 50 tied",
    which is the UNGATED number; on the gated table this figure actually draws
    it is 21, and the effective n is 29 rather than 6. The claim survives
    either way -- the median is still exactly zero -- but the number quoted
    beside it has to come from the population the figure uses.

    **AND `x` IS NOT A SIZE.** It is `med_slope / sd(slopes)`, so a scale whose
    lineages all agree scores high whether or not the slope is large.
    `v6:vocalisation` is +1.13 on a raw median slope of +0.045 norm-points per
    unit lift with 45/50 lineages agreeing; `v6:mundanity` is +0.34 on +0.017
    with a wider spread. Read x as "how reliably does this scale answer to
    lift", never as "how far does alignment move it" -- that is y's job, and
    Figure 3's triangles are in y's units, not these.

    Both axes are in BETWEEN-LINEAGE SDs of their own quantity. They have to
    be: the raw units differ per scale (Warriner 1-9, k_* 1-7, v6 1-7) and also
    differ BETWEEN THE AXES -- x is norm-points per unit of lift, y is
    norm-points. Nothing here is a correlation; the two axes are two summaries
    of the same 50 lineages, not two variables over a sample.
    """
    out = []
    for table in ("levels", "contextual"):
        dose, _, _ = load(table=table, top=999, pmax=pmax, min_lin=min_lin,
                          panel=panel, gated=gated)
        marg, _, _ = load_marginal(table=table, top=999, pmax=pmax,
                                   min_eff=min_lin, panel=panel, gated=gated)
        M = {r["field"].split("  (")[0]: r for r in marg}
        for r in dose:
            k = r["field"].split("  (")[0]
            m = M.get(k)
            if not m or not r.get("sd") or not m.get("sd"):
                continue
            if k in DROP_SCALES:
                continue
            #: `n` is the MARGINAL effective n -- the lineages whose median
            #: change is non-zero, i.e. the ones the sign test on the y axis
            #: actually rests on. The dose side is ~50 for every scale (an OLS
            #: slope is never exactly zero), so it carries no information and
            #: sizing by it would be sizing by nothing.
            out.append({"field": k, "scale": k, "table": table,
                        "x": r["med"] / r["sd"], "y": m["med"] / m["sd"],
                        "xp": r["p"], "yp": m["p"],
                        "n": m.get("up", 0) + m.get("dn", 0)})
    #: **`either`, NOT `both`.** Requiring both axes drops exactly the cases
    #: the figure exists to show: `k_charge` and `v6:harm` have marginal
    #: p=1.000 -- they do not move on the typical prompt at all -- while
    #: carrying dose slopes at p=2e-05 and p=3e-08. A norm invisible on one
    #: axis and decisive on the other is the finding, not noise to filter out.
    #: `both` is offered for the conservative reading and named as such.
    #: labels resolved AFTER filtering, so the disambiguation set reflects the
    #: rows that survive: dropping one concreteness makes the other just
    #: "Concreteness"
    #: no source suffixes: with one source per construct there is nothing to
    #: disambiguate, and `(k)` on every label is a token the reader carries for
    #: no return
    for r in out:
        r["field"] = pretty(r["scale"])
    #: **THE ADJUSTMENT FAMILY IS THE SET THAT SURVIVED COVERAGE, not the set
    #: that survives the alpha cut**, so it is computed HERE -- after the
    #: gate and `DROP_SCALES`, before `sig`. Those are the tests actually
    #: performed; correcting over the survivors would be correcting over the
    #: outcome.
    for ax in ("x", "y"):
        for r, q in zip(out, _adjust([r[ax + "p"] for r in out], correct)):
            r[ax + "q"] = q
    if sig == "either":
        out = [r for r in out if r["xq"] < alpha or r["yq"] < alpha]
    elif sig == "both":
        out = [r for r in out if r["xq"] < alpha and r["yq"] < alpha]
    #: **alpha=0.01 WAS A GUESS AND IS NO LONGER THE DEFAULT ARGUMENT OF
    #: RECORD.** It entered as this parser's default on an informal
    #: multiple-comparisons argument -- 29 scales, uncorrected on both axes
    #: and not corrected alike, so tighten the cut -- which nobody ruled on.
    #: A guess standing in for a correction is not a correction: it is not
    #: stateable in a caption and it moved which scales appeared. Measured
    #: over the 29 gated scales, `both`-significant counts are
    #:
    #:     raw 0.05  18     holm 0.05  11
    #:     raw 0.01  15     bh   0.05  18
    #:     raw 0.001  8
    #:
    #: BH costs nothing against raw 0.05 here (the p-distribution is far from
    #: uniform) and is sayable, so `--correct bh --alpha 0.05` is the rule the
    #: published figure uses. Holm drops `vulgarity`, `vocalization`,
    #: `valence` and `makes better` -- including both exact-zero points the
    #: figure is read for -- because it guards a claim this figure is not
    #: making.
    return out


def draw_xy(rows, out_path, pub=False, label_all=False, square=True):
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_blank, geom_hline, geom_vline,
                          geom_abline, geom_point, geom_text, labs,
                          theme_minimal, theme, element_text,
                          ggtitle, scale_color_manual, scale_x_continuous,
                          scale_y_continuous)
    from malignment.figure import (PUB_INK, PUB_GRAY, PUB_RULE_PT,
                                   PUB_FONT_PT, PUB_SIZE, pub_theme, pub_font)
    f = pd.DataFrame(rows)
    #: LABEL WHAT A READER WOULD CHASE: anything that clears p<0.01 on either
    #: axis, or sits far from the origin. Labelling all 30 is unreadable at
    #: 4.8 in and labelling none makes the quadrants uninterpretable.
    #: the same quantity the FILTER used -- `xq`/`yq` are the adjusted values
    #: when a correction ran and a copy of the raw ones when it did not, so a
    #: labelled point and an admitted point cannot disagree
    xq = f["xq"] if "xq" in f else f["xp"]
    yq = f["yq"] if "yq" in f else f["yp"]
    f["show"] = label_all | ((xq < 0.05) | (yq < 0.05)
                             | (f["x"].abs() > 0.6) | (f["y"].abs() > 0.6))

    #: **SYMMETRIC AND SQUARE.** Both axes are the same quantity in the same
    #: units, so an asymmetric or unequal pair makes the origin visually
    #: off-centre and a 45-degree agreement line not 45 degrees. One limit,
    #: taken from the largest absolute value on either axis, plus 18% headroom
    #: -- labels are drawn up and to the right of their point and `v6:
    #: vocalisation` at x=+1.13 was being clipped by the panel edge.
    #: 1.32, not 1.18: the widest label is drawn FROM its point and the
    #: rightmost point is the extreme of the axis, so headroom sized to the
    #: dots still clips the text. Flipping the side (below) fixes the general
    #: case; the extra room keeps the flip from colliding with its neighbour.
    #: `square=False` lets each axis take its own data range. It uses the
    #: panel far better -- the pinned version spends most of its area on empty
    #: quadrant corners -- at the cost that the origin is no longer centred and
    #: the 45-degree agreement line is no longer at 45 degrees, so the visual
    #: impression of how far the two readings agree becomes a function of the
    #: aspect ratio rather than of the data. Fine for looking, wrong for
    #: quoting a slope off the picture.
    M = max(f["x"].abs().max(), f["y"].abs().max()) * 1.32
    #: **THE ZERO RULES ARE REFERENCE, NOT DATA.** At full weight they read as
    #: the heaviest marks on the panel and compete with the points; 0.6 of the
    #: rule weight keeps them legible and subordinate.
    #: OLS once, used by both the line and the reported R^2
    _mx, _my = f["x"].mean(), f["y"].mean()
    _sxy = float(((f["x"] - _mx) * (f["y"] - _my)).sum())
    _sxx = float(((f["x"] - _mx) ** 2).sum())
    _syy = float(((f["y"] - _my) ** 2).sum())
    _b1 = _sxy / _sxx if _sxx else 0.0
    _b0 = _my - _b1 * _mx
    _r2 = (_sxy ** 2 / (_sxx * _syy)) if _sxx and _syy else float("nan")
    zero = PUB_RULE_PT * 0.6
    p = (ggplot(f, aes("x", "y"))
         + geom_hline(yintercept=0.0, color="black", size=zero, alpha=0.666)
         + geom_vline(xintercept=0.0, color="black", size=zero, alpha=0.666)
         + (scale_x_continuous(limits=(-M, M)) if square else geom_blank())
         + (scale_y_continuous(limits=(-M, M)) if square else geom_blank())
         #: **NO FIT LINE.** It was added as illustrative and then dropped
         #: (paper-claude, 2026-09-16): an OLS line on 15 non-independent
         #: points invites exactly the reading it cannot support, and the
         #: quadrant structure carries the comparison without it. The slope,
         #: intercept and R^2 are still COMPUTED and printed on render, for
         #: our own orientation only -- they are not drawn and belong in no
         #: caption.
         #: **`geom_abline`, NOT `geom_smooth`.** A smooth is clipped to the
         #: DATA range, so the line stops at the leftmost and rightmost points
         #: and reads as a segment somebody drew between two dots rather than
         #: as a fit. An abline is defined by slope and intercept and is drawn
         #: across the whole panel, which is what a regression line means.
         #: Same OLS either way -- computed here so the figure and the R^2 the
         #: producer prints come from one calculation, not two.
         #: **WEIGHT THE DOT BY WHAT IT RESTS ON.** paper-claude, 2026-09-16:
         #: `Vulgarity` clears the filter on 8 non-tied lineages and `Bodily
         #: harm` on 43, and at one size they read as equally solid. Sizing by
         #: the marginal effective n makes the difference visible instead of
         #: needing a caption sentence, and it answers the same question for
         #: `Vocalization` (29) without raising it.
         #:
         #: Hollow below 15: a size ramp alone still reads as "a bit smaller",
         #: where an unfilled marker reads as provisional.
         + geom_point(color="black", size=0.9)
         #: labels are placed by `adjustText` after the figure is built -- see
         #: below. Nothing is drawn here.
         #: **THE COLOURS HAD NO KEY AND THE RULES REQUIRE ONE INSIDE THE
         #: FIGURE.** Red is a LEXICON norm -- a word list applied to whatever
         #: the model put mass on. Blue is a RATED construct -- the v6 panel
         #: judging the same cells. They share no machinery, so the two
         #: families landing in the same quadrants is corroboration and a
         #: reader cannot see that without being told which is which.
         #: **THE AXIS IS SIGNED, AND A ONE-SIDED LABEL MISREADS IT.** It said
         #: "right = rises more where lift is high", which implies left means
         #: "rises less" -- i.e. no response. It does not. Left is a NEGATIVE
         #: slope: the norm FALLS harder where charge is high. Both ends are
         #: strongly dose-responsive and the unresponsive scales sit in the
         #: MIDDLE, at zero. Bodily harm at -0.70 is not weakly charge-linked;
         #: it is suppressed in proportion to the charge present.
         #: **"charge" NAMED THE INSTRUMENT AND WAS READ AS THE QUANTITY.** The
         #: x axis is a slope per unit of LIFT -- the base candidates' charge
         #: above the frame's own -- which `dose.py:lift_dose_rows` computes and
         #: every row under `results/dose_lift_v4_cov20/` records in its `dose`
         #: column. `charge` is the module that rates both. Nothing on the plate
         #: says which, and paper-claude read "rises with charge" as the LEVEL
         #: dose and asked whether eighteen scales needed re-running under lift.
         #: They did not; the label did.
         #:
         #: TWO WORDS, NOT A CLAUSE (RH). "lift" alone names the quantity only
         #: to a reader who already knows this folder; "charge lift" says whose
         #: lift it is and still fits the line. `XLAB`'s "change per unit of
         #: lift" was the other candidate and would have cost the SIGNED reading
         #: the comment above exists to protect.
         + labs(x="Dose slope (SDs)\n"
                  "<-- Falls with charge lift  |  Rises with charge lift -->",
                y="Marginal change (SDs)\n"
                  "<-- Falls with alignment  |  Rises with alignment -->"))
    #: ONE COLOUR, NO LEGEND. Lexicon-vs-rated is documented outside the
    #: figure; a key costs a third of the panel width and, set before
    #: `pub_theme()`, was being overridden by it anyway -- the legend rendered
    #: on the right with its title still showing and squashed the square axes
    #: the symmetric limits exist to produce.
    p = p + (pub_theme(height=4.6, grid="both") if pub else
             (ggtitle("Dose response against marginal change")
              + theme_minimal() + theme(figure_size=(9, 7),
                                        plot_title=element_text(size=11, weight="bold"))))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    #: **`adjustText` NEEDS THE MATPLOTLIB AXES, SO THE FIGURE IS BUILT AND
    #: THEN EDITED.** plotnine has no repel geom; `geom_text` places a label at
    #: a fixed offset from its point and four points within 0.1 SD of each
    #: other overprint whatever offset is chosen. `p.draw()` returns the real
    #: figure, so the labels go on as matplotlib artists and the solver moves
    #: them off each other, drawing a hairline back to the point it left.
    #:
    #: The cost is that this render no longer goes through `p.save`, so the
    #: size and dpi are set here and must MATCH the theme -- they are read off
    #: `PUB_SIZE` rather than retyped.
    from adjustText import adjust_text
    fig = p.draw(show=False)
    ax = fig.axes[0]
    sub = f[f["show"]]
    texts = [ax.text(r.x, r.y, r.field, fontsize=PUB_FONT_PT - 1.5,
                     family=pub_font(), color="black")
             for r in sub.itertuples()]
    if texts:
        adjust_text(texts, x=list(sub["x"]), y=list(sub["y"]), ax=ax,
                    expand=(1.15, 1.3), force_text=(0.4, 0.6),
                    arrowprops=dict(arrowstyle="-", color="#9aa1a7",
                                    lw=PUB_RULE_PT * 0.8))
    #: **EXPLICIT SIZE, NOT `bbox_inches="tight"`.** Tight bounding trims to
    #: the ink, so the output width becomes a function of how long the labels
    #: happen to be -- the one thing a figure rendered at FINAL SIZE must not
    #: let vary. Set from PUB_SIZE so it cannot drift from the theme.
    fig.set_size_inches(PUB_SIZE[0], 4.6)
    from malignment.figure import save as _save
    _save(fig, out_path)
    print("  fit (ILLUSTRATIVE, not a result): y = %+.3f x %+.3f  R2 = %.3f  n = %d"
          % (_b1, _b0, _r2, len(f)))
    return out_path


def draw(rows, out_path, pub=False):
    import matplotlib
    matplotlib.use("Agg")
    import pandas as pd
    from plotnine import (ggplot, aes, geom_vline, geom_point, geom_errorbarh,
                          labs, scale_y_discrete, theme_minimal, theme,
                          element_text, ggtitle)
    from malignment.figure import PUB_INK, PUB_RULE_PT, pub_theme
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
    #: **ONE INK: DIRECTION IS ALREADY POSITION.** A point left of the zero
    #: rule falls and a point right of it rises, so colouring by direction
    #: encoded a variable the axis already carries -- and under the grayscale
    #: palette it degraded to two greys with no key, which is worse than
    #: redundant. Removed rather than re-tuned.
    p = p + scale_color_manual({"rises": PUB_INK, "falls": PUB_INK}, guide=None)
    p = p + (pub_theme(height=max(3.6, 0.16 * len(rows)), grid="none") if pub else
             (ggtitle("USAS fields responding to lift dose, 45 lineages")
              + theme_minimal() + theme(figure_size=(8, 5),
                                        plot_title=element_text(size=11, weight="bold"))))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    #: PNG and PDF together -- see malignment.figure.save
    from malignment.figure import save as _save
    return _save(p, out_path)[0]


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
    ap.add_argument("--xy", action="store_true",
                    help="scatter: dose slope on x, marginal change on y, one "
                         "point per norm, both in between-lineage SDs. The two "
                         "one-dimensional figures are a pair and this is it.")
    ap.add_argument("--sig", default="either",
                    choices=["either", "both", "none"],
                    help="xy only: keep scales significant on EITHER axis "
                         "(default), on BOTH, or no filter. `both` drops "
                         "k_charge and v6:harm, which are the point.")
    ap.add_argument("--alpha", type=float, default=0.01)
    ap.add_argument("--correct", default="none", choices=("none", "holm", "bh"),
                    help="xy only: multiplicity-adjust p WITHIN each axis "
                         "before --sig applies. `bh` (false discovery rate) "
                         "with --alpha 0.05 is what the published figure "
                         "uses; the bare 0.01 default was an unruled guess.")
    ap.add_argument("--free", action="store_true",
                    help="xy only: let each axis take its own range instead of "
                         "a shared symmetric one. Uses the panel better; the "
                         "origin stops being centred and a 45-degree line "
                         "stops meaning agreement.")
    ap.add_argument("--label-all", action="store_true")
    ap.add_argument("--combine", action="store_true",
                    help="levels AND contextual on one axis, standardised by "
                         "each scale's between-lineage SD because their raw "
                         "units are not commensurable")
    ap.add_argument("--all", action="store_true",
                    help="EXPLORATORY: every scale that clears the coverage "
                         "gate, no p filter and no top-N. For looking, not for "
                         "publishing -- the p column is uncorrected and the "
                         "sweep is 42 levels / 82 contextual scales wide.")
    ap.add_argument("--min-signed", type=int, default=40,
                    help="drop scales with fewer than this many NON-TIED "
                         "lineages. 0 shows everything, with the effective n "
                         "on the label. 40 is strict and is what hid "
                         "v6:vocalisation (29 signed) and v6:harm (1).")
    ap.add_argument("--gated", action="store_true",
                    help="coverage >= 0.20 on BOTH arms. Marginal: reads "
                         "results/levels_gated_en.json instead of "
                         "(coverage >= 0.20 on BOTH arms, brooke_formality "
                         "excluded by name) instead of the declared "
                         "norm_stats.json. A different population, not a "
                         "cleaner reading -- see gated_levels.py.")
    ap.add_argument("--marginal", action="store_true",
                    help="the UNDOSED change: median over prompts of "
                         "(aligned - base) per lineage, from norm_stats.json")
    ap.add_argument("--pub", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.all:
        a.pmax = 1.01
        a.top = 999
    if a.xy:
        #: **`load_xy` DEFAULTS `panel="v6"` AND THE CLI OVERRODE IT WITH None.**
        #: Running `--xy` without `--panel` silently drew SIX instruments at
        #: once -- `v6`, `v6_wide`, `v6full` and `slot_rating_en_v6` are four
        #: ids for the same panel, so "Mundanity" appeared FOUR TIMES on one
        #: plate and the 18-scale figure came out with 11 points. It did not
        #: raise; it produced a plausible figure of the wrong population, which
        #: is the shape this repo pays for most often. A sensible default in a
        #: function signature is not a default if the caller passes None over it.
        if a.panel is None:
            a.panel = "v6"
            print("--panel not given: using v6 (four ids rate the same panel; "
                  "drawing all of them counts one finding four times)")
        rows = load_xy(pmax=a.pmax, min_lin=a.min_signed, panel=a.panel,
                       gated=a.gated, sig=a.sig, alpha=a.alpha,
                       correct=a.correct)
        print("%d scales, sig=%s at alpha=%g (%s)"
              % (len(rows), a.sig, a.alpha,
                 {"none": "UNCORRECTED",
                  "holm": "Holm-adjusted within axis",
                  "bh": "Benjamini-Hochberg within axis"}[a.correct]))
        for r in sorted(rows, key=lambda r: -r["x"])[:6] + sorted(rows, key=lambda r: r["x"])[:6]:
            print("  %-28s dose %+6.2f (p=%.1e)   marginal %+6.2f (p=%.1e)"
                  % (r["field"], r["x"], r["xp"], r["y"], r["yp"]))
        #: the correction and the alpha are IN THE FILENAME. The 15-scale and
        #: the 18-scale figures differ only in a cut nobody can see in the
        #: image, and the earlier one was already embedded in the README.
        corr = ("_%s%02d" % (a.correct, round(a.alpha * 100))
                if a.correct != "none" else "")
        out = a.out or os.path.join(FIGURES, "dose_vs_marginal%s%s%s%s.png"
                                    % ("_gated" if a.gated else "",
                                       "_free" if a.free else "",
                                       ("_" + a.sig if a.sig != "either" else "")
                                       + corr,
                                       "_pub" if a.pub else ""))
        print("\nwrote %s" % draw_xy(rows, out, pub=a.pub,
                                      label_all=a.label_all,
                                      square=not a.free))
        return
    if a.combine:
        rows = load_combined(marginal=a.marginal, top=a.top, pmax=a.pmax,
                             panel=a.panel, gated=a.gated, min_lin=a.min_signed)
        n_all = n_keep = len(rows)
    elif a.marginal:
        rows, n_all, n_keep = load_marginal(
            table=a.table, top=a.top, pmax=a.pmax, min_eff=a.min_signed,
            drop_variants=not a.variants, panel=a.panel, gated=a.gated)
    else:
        rows, n_all, n_keep = load(table=a.table, top=a.top, pmax=a.pmax,
                               drop_variants=not a.variants, panel=a.panel,
                               gated=a.gated)
    print("%d fields swept, %d clear p<0.001 and >=40 lineages, showing %d"
          % (n_all, n_keep, len(rows)))
    print("%-8s %11s %9s %10s" % ("field", "med slope", "up/dn", "p"))
    for r in sorted(rows, key=lambda x: -x["med"]):
        print("%-8s %+11.5f %9s %10.1e"
              % (r["field"], r["med"], "%d/%d" % (r["up"], r["dn"]), r["p"]))
    XLAB[0] = (("Change, aligned − base" if a.marginal else
                "Dose slope, per unit of lift")
               + (" (between-lineage SDs)" if a.combine else "")
               + ((", coverage ≥ %g" % GATE_VAL.get(a.table, 0.20))
                  if a.gated else ""))
    out = a.out or os.path.join(
        FIGURES, ("%s%s_" + ("marginal" if a.marginal else "dose")
                  + ("_gated" if a.gated else "") + "%s.png")
        % ("combined" if a.combine else a.table,
           "_" + a.panel if a.panel else "", "_pub" if a.pub else ""))
    print("\nwrote %s" % draw(rows, out, pub=a.pub))


if __name__ == "__main__":
    main()
