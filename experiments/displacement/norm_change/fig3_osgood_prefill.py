"""Figure 3z with the prefilled aligned arm beside it. -> figures/fig3_norms_osgood_en_z_prefill.{png,pdf,caption.txt}

    python -u fig3_osgood_prefill.py --build   -> results/norms_levels_z_en_prefill30.json  (reads the long tables)
    python -u fig3_osgood_prefill.py           -> the plate, from that JSON only

RH, 2026-09-25: the published z plate (`fig3_osgood.py --z`, base -> aligned
RAW, 50 endpoint lineages) with OPEN equivalents of its three markers for base
-> aligned PREFILLED, on the SAME ruler.

## THE STATISTIC IS THE PUBLISHED ONE, IMPORTED

`norms_levels_z.build` does the work, unedited: per lineage the MEAN over its
gated prompts of (aligned - base), then the median over lineages (`move_mean_z`),
bands cut at the published lift tertiles (asserted equal to
`norms_by_lift_en.json`). Only its SOURCE and its LINEAGE SET change here.

## ONE RULER: THE PUBLISHED PLATE'S SD

`build` z-scores each scale by the SD of that scale's own pooled values, so a
prefilled build would divide by a different SD and its markers would sit on a
different ruler from the filled ones. Every open marker is converted back to
rating points with its own SD and divided by the PUBLISHED SD
(`norms_levels_z_en.json`), so one unit means the same thing for both.

## THE POPULATION IS 30 OF THE 50, AND THE FILLED MARKERS ARE STILL THE 50

The prefilled arm exists at `system_mode='empty'` for 30 endpoint lineages, all
of them rendering an empty slot (`movement.clean_frame_pairs`); 17 more exist
only at `default`, which is not poolable with `empty` ([6557]) and is not used.
RH: "take the 30 for now". The filled markers are the published plate's, 50
lineages; the caption also carries raw on the SAME 30, so a reader can tell a
frame effect from a population one.

## THE CONTROL

`--build` first runs the wrapper on the RAW table over all 50 and requires every
scale and band to equal the committed `norms_levels_z_en.json` exactly. A wrapper
that changed a cut or a lineage key would fail there rather than in the plate.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

#: --pop 30: RH's first cut, the 30 lineages with system_mode='empty' prefill cells (committed 5e7e3104).
#: --pop 40: malign's declared population, roster.population("framed_empty"): 29 lineages read at
#: 'empty' and 11 at 'default' whose render is byte-identical to empty (framed_empty.json records
#: the evidence). The JSON keys below say "30" for the PREFILL POPULATION in both, so the drawing
#: code reads one schema; "population" in the JSON says which.
POP = sys.argv[sys.argv.index("--pop") + 1] if "--pop" in sys.argv else "30"
assert POP in ("30", "40"), POP
OUT_JSON = os.path.join(HERE, "results", "norms_levels_z_en_prefill%s.json" % POP)
PUB_JSON = os.path.join(HERE, "results", "norms_levels_z_en.json")
FRAMED_SRC = os.path.expanduser("~/malignment-data/norm_change/%s_long_v4_framed.csv.gz")
BANDS = ("low", "all", "high")
N_PREFILL = int(POP)
FRAMED_EMPTY = os.path.join(ROOT, "roster", "models", "populations", "framed_empty.json")


def populations():
    """-> (keep50, keep30) as 'base>aligned' keys."""
    from malignment import roster, movement as M
    eps, unresolved = roster.endpoints()
    assert not unresolved
    E = set(eps.items())
    keep50 = {"%s>%s" % e for e in E}
    if POP == "40":
        fe = json.load(open(FRAMED_EMPTY))["models"]
        assert {m["model"] for m in fe} == set(roster.population("framed_empty"))
        thirty = {(m["base"], m["model"]) for m in fe}
        assert thirty <= E
        #: every lineage must hold prefill cells at the mode framed_empty records -- except beaver,
        #: whose 'empty' rows movement_v4 collapsed into byte-identical 'default' ones (no system
        #: mode in its sort key; malign). The long table has ONE mode per lineage, so a lineage
        #: filter selects the recorded cells.
        from malignment import ch
        got = {}
        for x in ch.query("SELECT DISTINCT base, aligned, system_mode_aligned m FROM {db}.movement_v4 "
                          "WHERE frame_aligned='prefill' AND base != aligned"):
            got.setdefault((x["base"], x["aligned"]), set()).add(x["m"])
        for m in fe:
            k = (m["base"], m["model"])
            assert len(got.get(k, ())) == 1, (k, got.get(k))
            if "beaver" in m["model"]:
                assert got[k] == {"default"} and m["system_mode"] == "empty", (k, got[k])
            else:
                assert got[k] == {m["system_mode"]}, (k, got[k], m["system_mode"])
    else:
        thirty = {(b, a) for b, a, m in M.clean_frame_pairs() if m == "empty" and (b, a) in E}
    assert len(thirty) == N_PREFILL, len(thirty)
    return keep50, {"%s>%s" % e for e in thirty}


def run(src, keep, lpl, cuts):
    """norms_levels_z.build over both tables from `src`, cuts fixed. -> {scale: rec}"""
    import norms_levels_z as NLZ
    NLZ.SRC, NLZ.CUTS = src, tuple(cuts)
    out = {}
    for table in ("levels", "contextual"):
        recs, n, nn = NLZ.build(table, lpl, keep)
        for r in recs:
            out[r["scale"]] = r
    assert NLZ.CUTS == tuple(cuts)          # build must not have re-cut
    return out


def build():
    import gated_levels as G
    from malignment import charge
    keep50, keep30 = populations()
    pub = {x["scale"]: x for x in json.load(open(PUB_JSON))["scales"]}
    cuts = json.load(open(os.path.join(HERE, "results", "norms_by_lift_en.json")))["cuts"]
    assert [round(c, 9) for c in cuts] == [round(c, 9) for c in json.load(open(PUB_JSON))["cuts"]]
    lpl = charge.lifts_per_lineage()

    #: THE CONTROL: raw over 50 must BE the committed JSON, every scale and band
    raw50 = run(G.SRC, keep50, lpl, cuts)
    bad = []
    for sc, p in pub.items():
        g = raw50.get(sc)
        if g is None or abs(g["sd"] - p["sd"]) > 1e-12:
            bad.append((sc, "sd"))
            continue
        gb = {b["band"]: b for b in g["bands"]}
        for b in p["bands"]:
            for k in ("move_mean_z", "move_z", "n_lineages"):
                if k in b and abs(gb[b["band"]].get(k, float("nan")) - b[k]) > 1e-12:
                    bad.append((sc, b["band"], k))
    if bad:
        raise SystemExit("refusing to write: the wrapper does not reproduce norms_levels_z_en.json: %s" % bad[:8])
    print("  CONTROL: raw over 50 reproduces norms_levels_z_en.json on %d scales" % len(pub))

    raw30 = run(G.SRC, keep30, lpl, cuts)
    pre30 = run(FRAMED_SRC, keep30, lpl, cuts)
    #: **THE PREFILLED ARM COVERS A SUBSET OF PROMPTS** (a median of ~827 English prompts a
    #: lineage against ~2,576 raw). So a fourth arm: RAW on the same 30 lineages AND the same
    #: (lineage, prompt) pairs the prefilled table holds, which separates the frame from the
    #: prompt subset. Built by filtering the raw tables to those pairs, then the same build.
    import gzip, tempfile, collections
    pairs, cov = set(), collections.defaultdict(lambda: [set(), set()])
    for table in ("levels", "contextual"):
        with gzip.open(FRAMED_SRC % table, "rt") as fh:
            ix = {k: i for i, k in enumerate(fh.readline().rstrip("\n").split("\t"))}
            for line in fh:
                f = line.rstrip("\n").split("\t")
                lin = "%s>%s" % (f[ix["base"]], f[ix["aligned"]])
                if lin in keep30 and f[ix["lang"]] == "en":
                    pairs.add((lin, f[ix["prompt"]])); cov[lin][1].add(f[ix["prompt"]])
    tmp = tempfile.mkdtemp(prefix="nlz_raw30p_")
    for table in ("levels", "contextual"):
        with gzip.open(G.SRC % table, "rt") as fi, gzip.open(os.path.join(tmp, "%s.csv.gz" % table), "wt") as fo:
            head = fi.readline(); fo.write(head)
            ix = {k: i for i, k in enumerate(head.rstrip("\n").split("\t"))}
            for line in fi:
                f = line.rstrip("\n").split("\t")
                lin = "%s>%s" % (f[ix["base"]], f[ix["aligned"]])
                if lin in keep30 and f[ix["lang"]] == "en":
                    cov[lin][0].add(f[ix["prompt"]])
                    if (lin, f[ix["prompt"]]) in pairs:
                        fo.write(line)
    raw30p = run(os.path.join(tmp, "%s.csv.gz"), keep30, lpl, cuts)
    import shutil
    shutil.rmtree(tmp)                                  # the filtered copies are rebuilt on every --build
    import statistics as st
    coverage = {"en_prompts_per_lineage_median_raw": st.median(len(v[0]) for v in cov.values()),
                "en_prompts_per_lineage_median_prefill": st.median(len(v[1]) for v in cov.values()),
                "prefill_prompts_also_raw": sum(len(v[1] & v[0]) for v in cov.values()),
                "prefill_prompts": sum(len(v[1]) for v in cov.values())}

    def on_pub_ruler(rec, sc):
        """per band: move in rating points (mean within lineage, median over lineages) / PUBLISHED sd"""
        return {b["band"]: {"move_pub_z": b["move_mean_z"] * rec["sd"] / pub[sc]["sd"],
                            "move_points": b["move_mean_z"] * rec["sd"],
                            "n_lineages": b["n_lineages"],
                            "up": b.get("up_mean"), "down": b.get("down_mean")}
                for b in rec["bands"] if b.get("n_lineages")}
    out = {"population": "framed_empty" if POP == "40" else "system_mode empty (clean_frame_pairs)",
           "cuts": cuts, "n_raw": len(keep50), "n_prefill": len(keep30), "coverage": coverage,
           "prefill_lineages": sorted(keep30),
           "ruler": "published sd per scale (norms_levels_z_en.json)",
           "scales": {}}
    for sc in pub:
        out["scales"][sc] = {"pub_sd": pub[sc]["sd"],
                             "raw50": on_pub_ruler(raw50[sc], sc),
                             "raw30": on_pub_ruler(raw30[sc], sc),
                             "raw30p": on_pub_ruler(raw30p[sc], sc),
                             "prefill30": on_pub_ruler(pre30[sc], sc),
                             "prefill_own_sd": pre30[sc]["sd"]}
    json.dump(out, open(OUT_JSON, "w"), indent=1)
    print("wrote %s" % os.path.relpath(OUT_JSON, HERE))


# ────────────────────────────── the union selection (RH, 2026-09-25): raw-significant OR prefill-significant
SEL_JSON = os.path.join(HERE, "results", "fig3_prefill_selection40.json")
PRE_DOSE_DIR = os.path.join(HERE, "results", "dose_lift_v4_framed_cov20")
#: the three native scales the prefilled arm adds under the published rule; pole names from the v6
#: rater's own definitions (experiments/slot_ratings/task.py), pole words from fig3_candidates'
#: rule (movers >= 50 cells, rated in >= 5 frames, most extreme 60 by rating, then most-moved),
#: chosen from the top of each list, none repeating a word already on the plate (check_picks)
EXTRA_POLES = {"v6:interiority": ("In the world", "In a mind"),
               "v6:hedged": ("Committed", "Hedged"),
               "v6:deliberation": ("Acts", "Deliberates")}
EXTRA_PICKS = {"v6:interiority": (("slapped", "yanked"), ("realized", "wondered")),
               "v6:hedged": (("grabbed", "opened"), ("tried", "wait")),
               "v6:deliberation": (("rushed", "hurried"), ("decided", "consider"))}
#: RH's choice from the same candidate lists (2026-09-25), drawn with --rh-picks as ..._union_v2.
#: "thought" was his first high-pole word for interiority; it is already concreteness's Abstract
#: example, so check_picks refused it and RH chose "realized" instead.
EXTRA_PICKS_RH = {"v6:interiority": (("yanked", "spat"), ("realized", "wondered")),
                  "v6:hedged": (("shouted", "grabbed"), ("consider", "wait")),
                  "v6:deliberation": (("quickly", "immediately"), ("carefully", "probably"))}


def select():
    """The published scatter's rule (both axes, BH 0.05 within axis, over the 29 gated scales) applied
    to the PREFILLED arm on the 40 lineages. -> results/fig3_prefill_selection40.json

    Dose axis: dose.py's own per-lineage lift slopes, `--frame prefill` with the published
    invocation, written to results/dose_lift_v4_framed_cov20/ (the raw run's sibling directory).
    Marginal axis: norms_levels_z.build's per-lineage median change, sign test, ties dropped --
    the counts that reproduce the scatter's marginal p on all 29 raw scales (checked below)."""
    import csv, collections, subprocess
    from scipy.stats import binomtest
    import plot_fields as PF
    from malignment import charge, roster
    assert POP == "40", "--select is defined on the 40-lineage population"
    fam = PF.load_xy(sig="none", correct="bh", alpha=0.05)
    raw_both = {r["scale"] for r in PF.load_xy(sig="both", correct="bh", alpha=0.05)}
    assert len(fam) == 29 and len(raw_both) == 18, (len(fam), len(raw_both))
    F = [r["scale"] for r in fam]
    keep50, keep40 = populations()
    sign = lambda xs: (lambda up, dn: (up, dn, binomtest(up, up + dn).pvalue if up + dn else 1.0))(
        sum(x > 0 for x in xs), sum(x < 0 for x in xs))

    def slopes(d, sfx, keep):
        out = collections.defaultdict(list)
        for t in ("levels", "contextual"):
            for r in csv.DictReader(open(os.path.join(d, "dose_lift%s__%s_en__by_lineage.csv" % (sfx, t)))):
                if r["lineage"] in keep:
                    out[r["target"]].append(float(r["slope"]))
        return out
    #: CONTROL, both axes, raw: the published p values rebuilt from their per-lineage inputs
    R = slopes(os.path.join(HERE, "results", "dose_lift_v4_cov20"), "_v4", keep50)
    Z = {x["scale"]: {b["band"]: b for b in x["bands"]} for x in json.load(open(PUB_JSON))["scales"]}
    for sc, r in zip(F, fam):
        assert abs(sign(R[sc])[2] - r["xp"]) < 1e-9, ("dose", sc)
        a = Z[sc]["all"]
        assert abs(binomtest(a["up"], a["up"] + a["down"]).pvalue - r["yp"]) < 1e-9, ("marginal", sc)
    print("  CONTROL: raw dose and marginal p rebuilt from per-lineage inputs on all %d scales" % len(F))

    if not os.path.isdir(PRE_DOSE_DIR):
        for t in ("levels", "contextual"):
            subprocess.run([sys.executable, "-u", os.path.join(HERE, "dose.py"), "--rule-version", "4",
                            "--lift-dose", "--min-cov", "0.2", "--lang", "en", "--table", t, "--per-lineage",
                            "--top", "0", "--frame", "prefill", "--out", PRE_DOSE_DIR], check=True, cwd=HERE)
    Pd = slopes(PRE_DOSE_DIR, "_v4_framed", keep40)
    cuts = json.load(open(os.path.join(HERE, "results", "norms_by_lift_en.json")))["cuts"]
    Pm = run(FRAMED_SRC, keep40, charge.lifts_per_lineage(), cuts)
    rows = []
    for sc in F:
        xu, xd, xp = sign(Pd.get(sc, []))
        a = {b["band"]: b for b in Pm[sc]["bands"]}["all"]
        yu, yd = a["up"], a["down"]
        rows.append(dict(scale=sc, dose_up=xu, dose_down=xd, xp=xp, n_slopes=len(Pd.get(sc, [])),
                         marg_up=yu, marg_down=yd, yp=binomtest(yu, yu + yd).pvalue if yu + yd else 1.0,
                         raw_xq=next(r["xq"] for r in fam if r["scale"] == sc),
                         raw_yq=next(r["yq"] for r in fam if r["scale"] == sc)))
    for ax in ("x", "y"):
        for r, q in zip(rows, PF._adjust([r[ax + "p"] for r in rows], "bh")):
            r[ax + "q"] = q
    pre_both = {r["scale"] for r in rows if r["xq"] < 0.05 and r["yq"] < 0.05}
    union_native = sorted(sc for sc in raw_both | pre_both if not sc.endswith("_absz"))
    #: booked from the first (scratch) pass, 2026-09-25: what the prefilled arm adds
    assert sorted(pre_both - raw_both) == ["k_concreteness_absz", "v6:deliberation", "v6:hedged",
                                           "v6:interiority"], sorted(pre_both - raw_both)
    json.dump({"rule": "both axes, BH 0.05 within axis over the 29 gated scales (plot_fields.load_xy)",
               "population_prefill": "framed_empty, 40 lineages", "family": F, "raw_both": sorted(raw_both),
               "prefill_both": sorted(pre_both), "union_native": union_native, "scales": rows},
              open(SEL_JSON, "w"), indent=1)
    print("wrote %s: raw %d, prefill %d, union (native) %d" % (os.path.relpath(SEL_JSON, HERE), len(raw_both),
                                                            len(pre_both), len(union_native)))


def draw():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.font_manager import FontProperties
    from malignment.figure import (PUB_SIZE, PUB_FONT_PT, PUB_INK, PUB_MID, PUB_GRAY, PUB_FAINT,
                                   PUB_RULE_PT, pub_font, missing_glyphs, save)
    import fig3_osgood as FO
    matplotlib.rcParams["font.family"] = pub_font()
    matplotlib.rcParams["font.sans-serif"] = [pub_font(), "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    #: V2 (RH, 2026-09-25, on the 40-lineage plate): open glyphs on the SAME line as the filled,
    #: no dashed prefilled range, rows by each row's most extreme glyph, legend All/Least/Most
    V2 = POP == "40"
    #: --offset (RH, after seeing the shared line): the prefilled glyphs back just below the raw ones
    #: with their lift range dashed, keeping V2's row order and legend
    OFFSET = (not V2) or "--offset" in sys.argv
    UNION = V2 and "--union" in sys.argv
    RH_PICKS = UNION and "--rh-picks" in sys.argv
    name = ("fig3_norms_osgood_en_z_prefill" + ("40" if V2 else "") + ("_offset" if V2 and OFFSET else "")
            + ("_union" if UNION else "") + ("_v2" if RH_PICKS else ""))
    for ext in (".png", ".pdf", ".caption.txt"):
        assert not os.path.exists(os.path.join(HERE, "figures", name + ext)), "refusing to overwrite " + name + ext

    D = json.load(open(OUT_JSON))
    sys.argv = [sys.argv[0], "--z"]                       # FO.rows reads its estimator flag from argv (OFFSET read above)
    if UNION:
        #: the rows are the union selection, read from the committed selection file; the three
        #: additions join FO's dictionaries AT RUNTIME (fig3_osgood.py is not edited)
        SEL = json.load(open(SEL_JSON))
        FO.POLES = dict(FO.POLES, **EXTRA_POLES)
        FO.PICKS = dict(FO.PICKS, **(EXTRA_PICKS_RH if RH_PICKS else EXTRA_PICKS))
        assert sorted(FO.POLES) == SEL["union_native"], (sorted(FO.POLES), SEL["union_native"])
    FO.check_picks()
    rs = FO.rows(orient=False, mode="z")                  # the published rows, order and values
    n = len(rs)
    #: the filled markers ARE the published plate's (or, for the added rows, the same published
    #: computation): the JSON's raw50 must equal FO.rows
    for sc, sq, lo, hi, sd, _ in rs:
        r = D["scales"][sc]["raw50"]
        for band, v in (("all", sq), ("low", lo), ("high", hi)):
            assert abs(r[band]["move_pub_z"] - v) < 1e-12, (sc, band)
    P = {sc: D["scales"][sc]["prefill30"] for sc, *_ in rs}
    if V2:
        #: the signed value of the row's most extreme glyph, filled or open; most negative at the
        #: top, which on matplotlib's upward y means sorted DESCENDING (row 0 is drawn lowest)
        ext = lambda r: max((r[1], r[2], r[3], P[r[0]]["all"]["move_pub_z"], P[r[0]]["low"]["move_pub_z"],
                             P[r[0]]["high"]["move_pub_z"]), key=abs)
        rs = sorted(rs, key=ext, reverse=True)
    psq = np.array([P[r[0]]["all"]["move_pub_z"] for r in rs])
    plo = np.array([P[r[0]]["low"]["move_pub_z"] for r in rs])
    phi = np.array([P[r[0]]["high"]["move_pub_z"] for r in rs])

    def lab(sc, side):
        return "%s\n(%s)" % (FO.POLES[sc][side], ", ".join(FO.PICKS[sc][side]))

    fig, ax = plt.subplots(figsize=(PUB_SIZE[0], 0.30 * n + 1.25), layout="constrained")
    y = np.arange(n)
    sq = np.array([r[1] for r in rs]); lo = np.array([r[2] for r in rs]); hi = np.array([r[3] for r in rs])
    e = np.concatenate([sq, lo, hi, psq, plo, phi])
    pad = 0.06 * (e.max() - e.min())
    #: the prefilled markers sit a hair below their row, the raw ones a hair above, so a
    #: coincident pair stays two marks; the row rule runs between them
    DY = 0.17 if OFFSET else 0.0
    OPEN_FACE = "white" if OFFSET else "none"  # on a shared line, an open glyph must not hide a filled one
    for i in range(n):
        ax.plot([e.min() - pad, e.max() + pad], [i, i], color=PUB_FAINT, linewidth=PUB_RULE_PT * 0.7,
                zorder=1, solid_capstyle="butt")
        ax.plot([lo[i], hi[i]], [i + DY] * 2, color=PUB_GRAY, linewidth=PUB_RULE_PT * 1.6, zorder=2,
                solid_capstyle="butt")
        if OFFSET:
            ax.plot([plo[i], phi[i]], [i - DY] * 2, color=PUB_GRAY, linewidth=PUB_RULE_PT * 0.9, zorder=2,
                    solid_capstyle="butt", linestyle=(0, (2, 1.2)))
    h_lo = ax.scatter(lo, y + DY, marker="v", s=17, facecolor=PUB_GRAY, edgecolor="none", zorder=3,
                      label="Least charged (lift)")
    h_sq = ax.scatter(sq, y + DY, marker="s", s=13, facecolor=PUB_MID, edgecolor="none", zorder=4,
                      label="All prompts")
    h_hi = ax.scatter(hi, y + DY, marker="^", s=19, facecolor=PUB_INK, edgecolor="none", zorder=5,
                      label="Most charged (lift)")
    #: OPEN equivalents: the same shape and the same gray, as an outline
    k_lo = ax.scatter(plo, y - DY, marker="v", s=17, facecolor=OPEN_FACE, edgecolor=PUB_GRAY, linewidth=0.8,
                      zorder=3, label="Least charged (lift), prefilled")
    k_sq = ax.scatter(psq, y - DY, marker="s", s=13, facecolor=OPEN_FACE, edgecolor=PUB_MID, linewidth=0.8,
                      zorder=4, label="All prompts, prefilled")
    k_hi = ax.scatter(phi, y - DY, marker="^", s=19, facecolor=OPEN_FACE, edgecolor=PUB_INK, linewidth=0.8,
                      zorder=5, label="Most charged (lift), prefilled")
    ax.axvline(0, color=PUB_INK, linewidth=PUB_RULE_PT, zorder=6)
    ax.set_yticks(y)
    ax.set_yticklabels([lab(r[0], 0) for r in rs], fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    r2 = ax.secondary_yaxis("right")
    r2.set_yticks(y)
    r2.set_yticklabels([lab(r[0], 1) for r in rs], fontsize=PUB_FONT_PT - 2.5, fontfamily=pub_font())
    r2.tick_params(length=0)
    r2.spines["right"].set_visible(False)
    ax.set_ylim(-0.75, n - 0.25)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=2, labelsize=PUB_FONT_PT - 2)
    for t in ax.get_xticklabels():
        t.set_fontfamily(pub_font())
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_linewidth(PUB_RULE_PT)
    ax.grid(axis="x", color=PUB_GRAY, linewidth=PUB_RULE_PT * 0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("←  Semantic pole toward which alignment moves  →",
                  fontsize=PUB_FONT_PT - 1, fontfamily=pub_font())
    #: two legend rows: filled = raw (base -> aligned, no template), open = prefilled
    leg_font = FontProperties(family=pub_font(), size=PUB_FONT_PT - 2)
    #: matplotlib fills legend COLUMNS first, so pairs go in column order: row 1 filled, row 2 open
    #: V2 (RH): row 1 solid, row 2 open, each in the order All, Least charged, Most charged
    order = ([(h_sq, "All prompts"), (k_sq, "All, prefilled"), (h_lo, "Least charged"),
              (k_lo, "Least charged, prefilled"), (h_hi, "Most charged"), (k_hi, "Most charged, prefilled")]
             if V2 else
             [(h_sq, "All prompts"), (k_sq, "All, prefilled"), (h_hi, "Most charged"),
              (k_hi, "Most charged, prefilled"), (h_lo, "Least charged"), (k_lo, "Least charged, prefilled")])
    fig.legend(handles=[h for h, _ in order], labels=[l for _, l in order],
               prop=leg_font, frameon=False, handlelength=0.9, loc="outside lower center", ncol=3,
               scatterpoints=1, columnspacing=1.2, handletextpad=0.35)

    gone = missing_glyphs("".join(t.get_text() for t in fig.findobj(matplotlib.text.Text)))
    if gone:
        raise SystemExit("refusing to write: missing glyphs %s" % gone)
    small = min(t.get_fontsize() for t in fig.findobj(matplotlib.text.Text) if t.get_text().strip())
    out = os.path.join(HERE, "figures", name + ".png")
    print("  wrote %s (smallest type %.1f pt)" % (save(fig, out), small))
    caption(out, rs, D, V2, OFFSET, UNION, RH_PICKS)


def union_text(rs, D, rh_picks=False):
    """The selection paragraph for the union plate, every count read from SEL_JSON."""
    SEL = json.load(open(SEL_JSON))
    by = {r["scale"]: r for r in SEL["scales"]}
    Z = D["scales"]
    add = [sc for sc in SEL["union_native"] if sc not in SEL["raw_both"]]
    lost = [sc for sc in SEL["raw_both"] if sc not in SEL["prefill_both"] and not sc.endswith("_absz")]
    d = by["v6:deliberation"]
    one = lambda sc: "%s (lift dose %d up / %d down, marginal %d / %d)" % (
        EXTRA_POLES[sc][1].lower(), by[sc]["dose_up"], by[sc]["dose_down"], by[sc]["marg_up"], by[sc]["marg_down"])
    return ("ROWS: THE UNION OF TWO SELECTIONS. The published fourteen are Figure 3's scatter rule -- significant "
            "on both the marginal sign test and the lift-dose slope, Benjamini-Hochberg at 0.05 within each axis "
            "over the 29 gated scales -- less its four absolute-deviation variants. The same rule applied to the "
            "PREFILLED arm over the %d lineages admits three native scales the raw arm does not: %s. Their pole "
            "words %s (moved in at least 50 cells, rated in at least 5 frames, none "
            "repeated). %d of the published fourteen do not pass the rule on the prefilled arm (%s), most failing "
            "one axis only; they stay. DELIBERATION CARRIES VOCALISATION'S CAVEAT: it is admitted by its MEDIAN "
            "sign test (%d up / %d down among untied lineages, the rest tied at zero) while the plate draws the "
            "MEAN, which sits at %+.3f prefilled and %+.3f raw -- most prompts barely move and a minority move "
            "toward deliberation, so the typical prompt and the net mass point opposite ways. Selection: "
            "results/fig3_prefill_selection40.json." % (
                D["n_prefill"], "; ".join(one(sc) for sc in add),
                "were chosen by RH from the candidates the plate's own rule produces" if rh_picks
                else "follow the plate's own rule", len(lost), ", ".join(lost),
                d["marg_up"], d["marg_down"], Z["v6:deliberation"]["prefill30"]["all"]["move_pub_z"],
                Z["v6:deliberation"]["raw50"]["all"]["move_pub_z"]))


def caption(out, rs, D, V2=False, OFFSET=True, UNION=False, RH_PICKS=False):
    import textwrap
    #: one line per paragraph, as fig3_osgood's captions (and RH: no hard-wrapping in prose files)
    W = lambda s: [s]
    S = D["scales"]
    #: against the MATCHED raw arm (same 30 lineages, same prompts), not the 50
    n_off = sum(1 for sc, *_ in rs if abs(S[sc]["prefill30"]["all"]["move_pub_z"]) > abs(S[sc]["raw30p"]["all"]["move_pub_z"]))
    C = D["coverage"]
    L = [
        "Figure 3z with the prefilled aligned arm%s. What alignment does to fourteen norm scales, raw and "
        "prefilled, on one ruler." % (" (%d lineages)" % D["n_prefill"] if V2 else ""),
        "",
        *W("FILLED markers are the published plate (fig3_norms_osgood_en_z), unchanged: base -> aligned "
           "with no template, per lineage the MEAN over its gated prompts of the change, then the median over "
           "the %d endpoint lineages, divided by the SD of that scale's own pooled values. Square: all prompts; "
           "triangles: lowest and highest third of charge lift, cut at %+.3f and %+.3f." % (
               D["n_raw"], D["cuts"][0], D["cuts"][1])),
        "",
        *W("OPEN markers are the same statistic for base -> aligned PREFILLED: the aligned model's chat "
           "template with an empty system message, the prompt's text prefilled at the start of the model's own "
           "turn (movement_v4, frame_aligned='prefill'). The base side is the same raw base. " + (
               ("They are drawn just below the filled ones on each row, their lift range dashed. " if OFFSET else
                "They are drawn as outlines on the same line as the filled ones; only the filled markers' lift "
                "range is drawn. ") +
               "Rows are ordered by each row's most extreme marker, filled or open, most negative at the top."
               if V2 else
               "They are drawn just below the filled ones on each row, their lift range dashed.")),
        "",
        *(W(union_text(rs, D, RH_PICKS)) + [""] if UNION else []),
        *W("ONE RULER. Each open marker is converted to rating points and divided by the PUBLISHED plate's "
           "SD for that scale, not by the prefilled build's own, so a unit means the same thing for both sets "
           "of markers."),
        "",
        *(W("POPULATION: %d OF THE 50, malign's declared framed_empty (roster.population('framed_empty'); "
            "roster/models/populations/framed_empty.json, which records the render evidence and every "
            "exclusion). A lineage qualifies if nothing precedes the user turn but role markers, BOS and empty "
            "system turns: 29 read at system_mode='empty', and 11 at 'default' whose template renders an empty "
            "system message byte-identically to the default (Yi-1.5-9B-Chat, glm-4-9b-chat-hf, "
            "falcon-7b-instruct and others) or refuses a system role (gemma-2-9b-it, recurrentgemma-9b-it). "
            "beaver-7b-v1.0 is read at 'default': its empty-mode rows collapsed into byte-identical default-mode "
            "ones in movement_v4, whose sort key carries no system mode. Excluded: templates that inject preamble "
            "text (jais, llm-jp, AmberSafe, Teuken, mpt-7b-instruct, Llama-3.1-8B-Instruct's date block; "
            "malign's sensitivity set), SmolLM3-3B's persona, and 3 lineages with no prefilled cells. The "
            "filled markers stay on all 50." % D["n_prefill"]) if V2 else
          W("POPULATION: 30 OF THE 50. The prefilled arm exists with system_mode='empty' for %d of the 50 "
           "endpoint lineages, all of which render an empty system slot; 17 more exist only with the default "
           "system message, which is not poolable with 'empty' ([6557]) and is not used; 3 have no prefilled "
           "cell. The filled markers stay on all 50. The 30 include jais-family-6p7b-chat and "
           "llm-jp-3-7.2b-instruct3, whose templates inject preamble text outside the system slot (malign "
           "would hold them to a sensitivity set), and omit beaver-7b-v1.0, whose empty-mode rows movement_v4 "
           "collapsed into byte-identical default-mode ones (its sort key carries no system mode)." % D["n_prefill"])),
        "",
        *W("AND A SUBSET OF PROMPTS. Prefilled cells cover a declared 874-prompt set (the transgressive and "
           "institutional batteries, the slot corpus and a 105-pair transgressive sample; "
           "roster/prompts/populations/prefill.json), not a sample of the raw prompts, so it over-represents "
           "charged and institutional stems. The prefilled arm was measured on a median of %d English prompts a "
           "lineage against %d raw; %d of its %d (lineage, prompt) cells are also raw cells. So the table "
           "below gives RAW three ways: all 50 lineages (the filled markers); the same %d; and the same %d "
           "on the SAME prompts as the prefilled arm, which is the comparison that isolates the frame." % (
               C["en_prompts_per_lineage_median_prefill"], C["en_prompts_per_lineage_median_raw"],
               C["prefill_prompts_also_raw"], C["prefill_prompts"], D["n_prefill"], D["n_prefill"])),
        "",
        *W("On %d of the 14 scales the prefilled all-prompts value sits further from zero than raw on the same "
           "%d lineages and the same prompts." % (n_off, D["n_prefill"])),
        "",
        *W("Control: the build reruns the published computation on the raw table over all 50 lineages and "
           "requires every scale and band to equal results/norms_levels_z_en.json exactly; the filled "
           "markers are then asserted equal to fig3_osgood.rows. Exploratory; lift bands are the published "
           "raw-arm cuts, applied to the prefilled rows unchanged."),
        "",
        "Per scale, on the published ruler (z): all prompts [least charged, most charged].",
        "  %-20s %-19s %-19s %-19s %-19s" % ("scale", "raw, 50", "raw, same %d" % D["n_prefill"],
                                              "raw, %d, same pr." % D["n_prefill"],
                                              "prefilled, %d" % D["n_prefill"]),
    ]
    for sc, *_ in rs:
        cell = lambda k: "%+.3f [%+.3f,%+.3f]" % (S[sc][k]["all"]["move_pub_z"], S[sc][k]["low"]["move_pub_z"],
                                                 S[sc][k]["high"]["move_pub_z"])
        L.append("  %-20s %-19s %-19s %-19s %-19s" % (sc[:20], cell("raw50"), cell("raw30"), cell("raw30p"),
                                                     cell("prefill30")))
    L += ["", "Producer: experiments/displacement/norm_change/fig3_osgood_prefill.py (imports norms_levels_z.build "
          "and fig3_osgood.rows unedited)."]
    open(out[:-4] + ".caption.txt", "w", encoding="utf-8").write("\n".join(L) + "\n")


if __name__ == "__main__":
    if "--build" in sys.argv:
        build()
    elif "--select" in sys.argv:
        select()
    else:
        draw()
