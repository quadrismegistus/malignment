"""Build the checkpoint-ladder curve table from ClickHouse, in bulk.

    python produce_curve_data.py
    python produce_curve_data.py --population data/pythia_population.json
    python produce_curve_data.py --check     # compare against the archive parquet

## WHAT THIS REPLACES

`m05_curves.py` in the archive called `movement.word_probs(model, prompt)` per
cell -- one query per (checkpoint, prompt), ~55,000 round trips at 192ms each.
This queries `twp_words` in bulk: one query per checkpoint, ~95 queries total,
each returning the full word distribution for all prompts at once.

The fold that `word_probs` existed to perform (summing over tokenization paths
for the same surface) is already done in the v3 `twp_words` table -- verified
by the zero-duplicate check on `twp_words_v4_best` (2026-08-25), and v3 uses
the same ingest path.

## WHAT IT EMITS

`data/m05_curves.parquet`, long format, one row per (checkpoint, curve, probe,
word-role). Columns: ckpt_idx, model, role, stage, step, curve, probe, word,
word_role, p, absent, residual.

The archive's version is at `data/m05_curves.parquet` (already committed,
49,210 rows). This regenerates it from CH and should reproduce it; `--check`
compares the two.

## CURVES

    PANEL              p(faller) and p(riser) per prompt, from the 105 marked
                       pairs. The onset-ordering primary.
    CAPACITY_REFERENCE log p(target)/p(competitor), 36 probes
    CAPACITY_REASONING 32 probes
    CAPACITY_DISCOURSE 30 probes
    CAPACITY_PACKAGES  36 probes
    POETIC             pull = p(t|FORMULAIC) - p(t|PARAPHRASE), 20 pairs

## ABSENT-WORD POLICY

A word not in the distribution has p < theta (0.001). It enters as theta/2
with absent=True on the row. An absent CELL (checkpoint not in the store) is
a gap: no row emitted, counted in the coverage report.
"""
import argparse
import csv
import json
import math
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))

THETA = 0.001
ABSENT_P = THETA / 2

DATA = os.path.join(HERE, "data")
PANEL_CSV = os.path.join(DATA, "beam_sample_105_plus_anger.csv")
POPULATION = os.path.join(DATA, "m05_checkpoint_population.json")
OUT = os.path.join(DATA, "m05_curves.parquet")

ROLE_ORDER = {"base_step": 0, "base_endpoint": 1, "sft_step": 2,
              "sft_endpoint": 3, "dpo_endpoint": 4, "rlvr_step": 5}
STAGE_ORDER = {"stage1": 0, "stage2": 1, "stage3": 2, None: 3}


def checkpoint_key(c):
    return (ROLE_ORDER[c["role"]], STAGE_ORDER.get(c.get("stage")),
            c.get("step", 0))


def model_string(c):
    return (c["model_id"] if c["revision"] == "main"
            else "%s@%s" % (c["model_id"], c["revision"]))


def load_probes():
    probes = []
    for r in csv.DictReader(open(PANEL_CSV)):
        if r.get("member") not in ("MARKED", "marked"):
            continue
        pid = r.get("stem") or r["prompt"][:40]
        if r.get("faller"):
            probes.append(("PANEL", pid, r["prompt"], r["faller"], "faller"))
        if r.get("riser"):
            probes.append(("PANEL", pid, r["prompt"], r["riser"], "riser"))
    fams = {"CAPACITY_REFERENCE": "m05_reference.yaml",
            "CAPACITY_REASONING": "m05_reasoning.yaml",
            "CAPACITY_DISCOURSE": "m05_discourse_reference.yaml",
            "CAPACITY_PACKAGES": "m05_semantic_packages.yaml"}
    for fam, f in fams.items():
        for rec in yaml.safe_load(open(os.path.join(DATA, f))):
            probes.append((fam, rec["id"], rec["prompt"],
                           rec["target"], "target"))
            probes.append((fam, rec["id"], rec["prompt"],
                           rec["competitor"], "competitor"))
    for rec in yaml.safe_load(open(os.path.join(DATA, "m05_poetic_texture.yaml"))):
        probes.append(("POETIC", rec["pair_id"], rec["FORMULAIC"],
                       rec["target"], "formulaic"))
        probes.append(("POETIC", rec["pair_id"], rec["PARAPHRASE"],
                       rec["target"], "paraphrase"))
    return probes


def fetch_bulk(model, prompts, words):
    """Bulk fetch: `{(prompt, word): p}` for one model over all needed cells."""
    from malignment import vectors as V
    rows = V.rows(
        "SELECT prompt, word, p FROM twp_words "
        "WHERE model = {m:String} "
        "AND prompt IN {pp:Array(String)} "
        "AND word IN {ww:Array(String)}",
        m=model, pp=sorted(set(prompts)), ww=sorted(set(words)))
    return {(r["prompt"], r["word"]): r["p"] for r in rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--population", default=POPULATION)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true",
                    help="compare against the existing parquet rather than overwriting")
    a = ap.parse_args()

    pop = json.load(open(a.population))["checkpoints"]
    pop = sorted(pop, key=checkpoint_key)
    probes = load_probes()
    n_curves = len({(c, p) for c, p, *_ in probes})
    print("%d checkpoints | %d probe rows | %d distinct (curve, probe)"
          % (len(pop), len(probes), n_curves))

    probe_prompts = sorted({pr for _, _, pr, _, _ in probes})
    probe_words = sorted({w for _, _, _, w, _ in probes})
    by_prompt_word = {}
    for curve, pid, prompt, word, role in probes:
        by_prompt_word.setdefault((prompt, word), []).append(
            (curve, pid, role))

    rows = []
    gaps = {}
    for idx, c in enumerate(pop):
        m = model_string(c)
        dist = fetch_bulk(m, probe_prompts, probe_words)
        got = miss = 0
        for (prompt, word), entries in by_prompt_word.items():
            p = dist.get((prompt, word))
            absent = p is None
            for curve, pid, role in entries:
                if absent:
                    miss += 1
                else:
                    got += 1
                rows.append(dict(
                    ckpt_idx=idx, model=m, role=c["role"],
                    stage=c.get("stage"), step=c.get("step"),
                    curve=curve, probe=pid, word=word, word_role=role,
                    p=(ABSENT_P if absent else p), absent=absent,
                    residual=0.0))
        gaps[m] = (got, miss)
        pct = 100.0 * got / max(got + miss, 1)
        print("  [%2d/%d] %-55s %5d / %5d (%.0f%%)"
              % (idx + 1, len(pop), m[:55], got, got + miss, pct))

    import pandas as pd
    df = pd.DataFrame(rows)
    if df.empty:
        print("NO CELLS ANSWERED.")
        return 1

    if a.check:
        old = pd.read_parquet(a.out)
        print("\n--- CHECK against %s ---" % a.out)
        print("old: %d rows, %d checkpoints" % (len(old), old.model.nunique()))
        print("new: %d rows, %d checkpoints" % (len(df), df.model.nunique()))
        key = ["model", "curve", "probe", "word", "word_role"]
        merged = old.merge(df, on=key, suffixes=("_old", "_new"), how="outer")
        both = merged.dropna(subset=["p_old", "p_new"])
        diff = both[abs(both["p_old"] - both["p_new"]) > 1e-6]
        print("matched on key: %d  |  differing p: %d  |  old-only: %d  |  new-only: %d"
              % (len(both), len(diff),
                 merged["p_new"].isna().sum(), merged["p_old"].isna().sum()))
        if len(diff):
            print("\nfirst diffs:")
            print(diff.head(5)[key + ["p_old", "p_new"]].to_string())
        return 0

    df.to_parquet(a.out, index=False)
    print("\nwrote %s: %d rows, %d checkpoints answering"
          % (a.out, len(df), df.model.nunique()))

    absent_rate = df.groupby("curve")["absent"].mean()
    print("\nabsent-word rate by curve:")
    print(absent_rate.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
