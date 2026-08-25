#!/usr/bin/env python
"""One tidy per-rung capacity table, for plotting ease (RH, 2026-08-14).

    uv run python experiments/emergence/capacities/aggregate_capacities.py

Everything the campaign has measured per pretraining rung, ONE file, ONE
schema — so a ladder figure is a filter + a groupby, never a re-derivation:

    ladder    pythia | olmo             (never pooled: [5425](b)/[5430])
    model     full model string
    ckpt_idx  the ladder's canonical ordinal (from the curves parquets;
              verse and sense join it BY MODEL STRING)
    role, stage, step
    family    capacity_reference | capacity_reasoning | capacity_discourse
              | capacity_packages | poetic | panel
              | verse_rhymed_pre-1900 | verse_rhymed_1900+
              | verse_unrhymed_* | sense
    measure   family-specific, uniform within family:
              M05 battery: mean_p_target / mean_p_competitor / absent_rate
                (mean over ALL probes; absent rows carry theta/2 as stored)
              verse:       called_pull / null / pull_delta_median /
                           frac_positive / copy / censored
              sense:       natural_share
    value, n

Sources (this file DERIVES, never re-measures):
  data/pythia_curves.parquet, data/m05_curves.parquet   (M05 battery)
  results/verse_capacity_rungs.parquet
  results/sense_curve.json           (Pythia only)
  data/m05_class_mass.parquet + m05_licit_sets*.json    (syntax: the
    per-rung strict/permissive licit share recomputed with
    m05_syntax_curve.py's own conventions — format band, equivalences,
    payload_empty censored, median over prompts. syntax_curve.json
    stays the ONSET authority; it never persisted the curve itself.)
NOT here: m05_norm_mass.parquet (norms, not capacities — Findings H
plots it directly); the verse closure decomposition (.f16 not
ingested); OLMo sense (its 22 ckpts are the sense study's own roster,
no model ids in the JSON — unjoinable until its producer emits them).

Output: results/capacities_by_rung.parquet
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
#: MIGRATED 2026-08-24: ROOT was the archive repo root; it is now this
#: experiment folder, so data/ results/ figures/ sit beside this file.
ROOT = HERE
os.chdir(ROOT)

OUT = "results/capacities_by_rung.parquet"
FAM = {"CAPACITY_REFERENCE": "capacity_reference",
       "CAPACITY_REASONING": "capacity_reasoning",
       "CAPACITY_DISCOURSE": "capacity_discourse",
       "CAPACITY_PACKAGES": "capacity_packages",
       "POETIC": "poetic"}
# PANEL dropped: its roles are faller/riser — a movement panel, not a
# capacity family. Role->measure is PER FAMILY: POETIC's target-like
# role is the poet's FORMULAIC word ([5379] design), which a bare
# target/competitor test mislabeled in this file's first version
# (poetic drew 0 target rows; caught by its absence from fig26).
ROLE2MEAS = {"target": "mean_p_target", "competitor": "mean_p_competitor",
             "formulaic": "mean_p_target", "paraphrase": "mean_p_competitor"}


def battery(path, ladder):
    d = pd.read_parquet(path)
    d["family"] = d.curve.map(FAM)
    d = d[d.family.notna()]
    rows = []
    for (fam, ck, wr), g in d.groupby(["family", "ckpt_idx", "word_role"]):
        meta = g.iloc[0]
        meas = ROLE2MEAS.get(wr)
        if meas is None:
            continue
        rows.append(dict(ladder=ladder, model=meta.model,
                         ckpt_idx=int(ck), role=meta.role,
                         stage=str(meta.stage), step=str(meta.step),
                         family=fam, measure=meas,
                         value=float(g.p.mean()), n=len(g)))
        if meas == "mean_p_target":
            rows.append(dict(ladder=ladder, model=meta.model,
                             ckpt_idx=int(ck), role=meta.role,
                             stage=str(meta.stage), step=str(meta.step),
                             family=fam, measure="absent_rate",
                             value=float(g.absent.mean()), n=len(g)))
    return pd.DataFrame(rows)


def rung_key(curves):
    k = (curves[["model", "ckpt_idx", "role", "stage", "step"]]
         .drop_duplicates("model").set_index("model"))
    k["stage"] = k.stage.astype(str)
    k["step"] = k.step.astype(str)
    return k


def verse(keys):
    s = pd.read_parquet(
        "results/verse_capacity_rungs.parquet")
    s["family"] = ("verse_" + s.rhymed.map({True: "rhymed",
                                            False: "unrhymed"})
                   + "_" + s.era)
    s["called_pull"] = s.called_mean - s.copy_called_mean
    rows = []
    for r in s.itertuples():
        if r.model not in keys.index:
            continue
        k = keys.loc[r.model]
        for meas, val in (("called_pull", r.called_pull),
                          ("null", r.null_mean),
                          ("pull_delta_median", r.pull_delta_median),
                          ("frac_positive", r.frac_positive),
                          ("copy", r.copy_called_mean),
                          ("censored", r.censored_called_mean)):
            rows.append(dict(ladder=r.ladder, model=r.model,
                             ckpt_idx=int(k.ckpt_idx), role=k.role,
                             stage=k.stage, step=k.step,
                             family=r.family, measure=meas,
                             value=float(val), n=int(r.n_poems)))
    return pd.DataFrame(rows)


def sense(keys_by_ladder):
    """Natural share per rung, BOTH LADDERS, from the sense mass parquet.

    The first version read from `sense_curve.json` (Pythia only) because
    that JSON lacked model ids for OLMo and joining by index compressed
    the series onto the wrong rungs. `produce_sense_mass.py` now writes
    `m05_sense_mass.parquet` with proper model strings for both ladders,
    so the join is on model and the index compression cannot recur.
    """
    sm = pd.read_parquet("data/m05_sense_mass.parquet")
    sm = sm[~sm.payload_empty]
    rows = []
    for ladder in ("olmo", "pythia"):
        keys = keys_by_ladder[ladder].reset_index().set_index("model")
        sub = sm[sm.ladder == ladder]
        for (model, ckpt_idx), g in sub.groupby(["model", "ckpt_idx"]):
            classified = g[g.band.isin(["natural", "odd", "ungrammatical", "not_a_word"])]
            total = classified.mass.sum()
            if total <= 0:
                continue
            natural = g[g.band == "natural"].mass.sum()
            if model not in keys.index:
                continue
            k = keys.loc[model]
            k = k.iloc[0] if isinstance(k, pd.DataFrame) else k
            rows.append(dict(ladder=ladder, model=model,
                             ckpt_idx=int(ckpt_idx),
                             role=k.role, stage=k.stage, step=k.step,
                             family="sense", measure="natural_share",
                             value=float(natural / total), n=0))
    return pd.DataFrame(rows)


FORMAT_BAND = {"PUNCT", "X", "SYM"}
EQUIV = [{"ADP", "PART"}, {"NUM", "NOUN"}, {"AUX", "VERB"}]
CODERS = {"deepseek-v4-flash": ("data/m05_licit_sets.json",
                                "strict_licit_share"),
          "claude-haiku-4-5": ("data/m05_licit_sets_haiku.json",
                               "strict_licit_share_haiku")}


def _expand(classes):
    out = set(classes)
    for g in EQUIV:
        if out & g:
            out |= g
    return out


def syntax():
    cm = pd.read_parquet("data/m05_class_mass.parquet")
    cm = cm[~cm.payload_empty & (cm.resolved_mass > 0)].copy()
    # stage/step are NaN on post-training rungs and groupby DROPS NaN
    # keys silently — the first run of this function lost all 53 OLMo
    # post-base rungs that way. astype(str) alone did NOT fix it: the
    # columns are Arrow-backed strings whose NA survives the cast, so
    # fill explicitly before casting.
    cm["stage"] = cm.stage.fillna("none").astype(str)
    cm["step"] = cm.step.fillna(-1).astype(str)
    rows = []
    for coder, (path, meas) in CODERS.items():
        tab = json.load(open(path))["prompts"]
        mem = [dict(prompt=p, pos_class=c)
               for p, v in tab.items()
               for c in _expand({w["pos"] for w in v["licit"]})]
        mem = pd.DataFrame(mem).assign(licit=True)
        m = cm.merge(mem, on=["prompt", "pos_class"], how="left")
        cell = (m.groupby(["ladder", "ckpt_idx", "model", "role",
                           "stage", "step", "prompt", "resolved_mass"])
                .apply(lambda g: g[g.licit.notna()].mass.sum(),
                       include_groups=False)
                .rename("lic").reset_index())
        cell["share"] = cell.lic / cell.resolved_mass
        med = (cell.groupby(["ladder", "ckpt_idx", "model", "role",
                             "stage", "step"])
               .agg(value=("share", "median"), n=("share", "size"))
               .reset_index())
        for r in med.itertuples():
            rows.append(dict(ladder=r.ladder, model=r.model,
                             ckpt_idx=int(r.ckpt_idx), role=r.role,
                             stage=str(r.stage), step=str(r.step),
                             family="syntax", measure=meas,
                             value=float(r.value), n=int(r.n)))
    return pd.DataFrame(rows)


def main():
    #: `--out` ADDED ON MIGRATION, for the reason it was needed: this wrote
    #: straight to results/capacities_by_rung.parquet and, on the first
    #: verification run after the migration, REPLACED the archived copy the
    #: README quotes. It was recoverable only because the file was committed.
    #: A producer whose default output is the record it is being checked against
    #: destroys the comparison by running.
    global OUT
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT,
                    help="output parquet (default: results/, the archived copy)")
    OUT = ap.parse_args().out

    py = pd.read_parquet("data/pythia_curves.parquet")
    ol = pd.read_parquet("data/m05_curves.parquet")
    keys = {"pythia": rung_key(py), "olmo": rung_key(ol)}
    allkeys = pd.concat([keys["pythia"], keys["olmo"]])

    parts = [battery("data/pythia_curves.parquet", "pythia"),
             battery("data/m05_curves.parquet", "olmo"),
             verse(allkeys), sense(keys), syntax()]
    out = pd.concat(parts, ignore_index=True)
    out.to_parquet(OUT)
    print(f"wrote {OUT}: {len(out):,} rows")
    print(out.groupby(["ladder", "family"]).size().unstack(0,
          fill_value=0).to_string())
    missing = set(pd.read_parquet(
        "results/verse_capacity_rungs.parquet"
    ).model) - set(allkeys.index)
    if missing:
        print(f"\nverse models with NO ckpt_idx (not in curves "
              f"parquets, dropped): {len(missing)}")
        for m in sorted(missing)[:6]:
            print("  ", m)


if __name__ == "__main__":
    main()
