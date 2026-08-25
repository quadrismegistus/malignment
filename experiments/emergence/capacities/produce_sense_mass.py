"""Resolved twp mass by sense band per (checkpoint, prompt), from CH in bulk.

    python produce_sense_mass.py
    python produce_sense_mass.py --check

Mirrors `produce_class_mass.py` exactly: same populations, same bulk query
pattern, same cell discipline. The collapse key is the tier-3 sense verdict
instead of the POS class.

## BANDS

    natural / odd / ungrammatical / not_a_word   from the sense verdicts
    ungrammatical                                auto (both syntax coders illicit)
    format                                       PUNCT/X/SYM band
    unclassified                                 below both census floors

## INPUTS

    data/m05_sense_census.parquet    136,036 pairs with bucket assignment
    data/m05_sense_verdicts.parquet  118,129 JUDGE pairs with coder verdict
    Both frozen, copied from the archive.
"""
import argparse
import collections
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))

DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "m05_sense_mass.parquet")

ROLE_ORDER = {"base_step": 0, "base_endpoint": 1, "sft_step": 2,
              "sft_endpoint": 3, "dpo_endpoint": 4, "rlvr_step": 5}
STAGE_ORDER = {"stage1": 0, "stage2": 1, "stage3": 2}


def model_string(c):
    return (c["model_id"] if c["revision"] == "main"
            else "%s@%s" % (c["model_id"], c["revision"]))


def load_population(path):
    pop = json.load(open(path))["checkpoints"]
    return sorted(pop, key=lambda c: (ROLE_ORDER[c["role"]],
                                      STAGE_ORDER.get(c.get("stage"), 9),
                                      c.get("step", 0)))


def battery_texts():
    b = json.load(open(os.path.join(DATA, "m05_battery.json")))
    texts = []
    for blk in b["blocks"].values():
        for t in blk["texts"]:
            texts.append(t if isinstance(t, str) else
                         t.get("text", t.get("prompt")))
    return list(dict.fromkeys(texts))


def band_map():
    census = pd.read_parquet(os.path.join(DATA, "m05_sense_census.parquet"))
    verdicts = pd.read_parquet(os.path.join(DATA, "m05_sense_verdicts.parquet"))
    vmap = {(r.prompt, r.word): r.verdict for r in verdicts.itertuples()}
    bands = {}
    missing = 0
    for r in census.itertuples():
        k = (r.prompt, r.word)
        if r.bucket == "JUDGE":
            v = vmap.get(k)
            if v is None:
                missing += 1
                continue
            bands[k] = v
        elif r.bucket == "ungrammatical_auto":
            bands[k] = "ungrammatical"
        else:
            bands[k] = "format"
    if missing:
        print("WARNING: %d JUDGE pairs without a verdict" % missing)
    return bands


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    from malignment import vectors as V

    bands = band_map()
    texts = battery_texts()
    print("%d battery prompts, %d banded (prompt, word) pairs" % (len(texts), len(bands)))

    rows = []
    for ladder, path in [("olmo", os.path.join(DATA, "m05_checkpoint_population.json")),
                          ("pythia", os.path.join(DATA, "pythia_population.json"))]:
        pop = load_population(path)
        print("\n%s: %d checkpoints x %d prompts" % (ladder, len(pop), len(texts)))
        for idx, c in enumerate(pop):
            m = model_string(c)
            result = V.rows(
                "SELECT prompt, word, p FROM twp_words "
                "WHERE model = {m:String} AND prompt IN {pp:Array(String)}",
                m=m, pp=texts)
            by_prompt = collections.defaultdict(list)
            for r in result:
                by_prompt[r["prompt"]].append((r["word"], r["p"]))
            for p in texts:
                words = by_prompt.get(p)
                if words is None:
                    rows.append(dict(ladder=ladder, ckpt_idx=idx, model=m,
                                     role=c["role"], stage=c.get("stage"),
                                     step=c.get("step"), prompt=p,
                                     resolved_mass=0.0, n_rows=0,
                                     payload_empty=True, band="NONE", mass=0.0))
                    continue
                masses = collections.defaultdict(float)
                resolved = 0.0
                for w, prob in words:
                    masses[bands.get((p, w), "unclassified")] += prob
                    resolved += prob
                base = dict(ladder=ladder, ckpt_idx=idx, model=m,
                            role=c["role"], stage=c.get("stage"),
                            step=c.get("step"), prompt=p,
                            resolved_mass=resolved, n_rows=len(words),
                            payload_empty=(len(words) == 0))
                if not masses:
                    rows.append(dict(base, band="NONE", mass=0.0))
                else:
                    for band, mass in masses.items():
                        rows.append(dict(base, band=band, mass=mass))
            if (idx + 1) % 25 == 0 or idx == len(pop) - 1:
                print("  [%d/%d] %s" % (idx + 1, len(pop), m[:55]))

    df = pd.DataFrame(rows)
    if df.empty:
        print("NO CELLS ANSWERED.")
        return 1

    if a.check:
        old = pd.read_parquet(a.out)
        print("\n--- CHECK against %s ---" % a.out)
        print("old: %d rows" % len(old))
        print("new: %d rows" % len(df))
        key = ["ladder", "model", "prompt", "band"]
        merged = old.merge(df, on=key, suffixes=("_old", "_new"), how="outer")
        both = merged.dropna(subset=["mass_old", "mass_new"])
        diff = both[abs(both["mass_old"] - both["mass_new"]) > 1e-6]
        print("matched: %d  |  differing: %d  |  old-only: %d  |  new-only: %d"
              % (len(both), len(diff),
                 merged["mass_new"].isna().sum(), merged["mass_old"].isna().sum()))
        if len(diff):
            print("max abs diff: %.6f" % abs(diff["mass_old"] - diff["mass_new"]).max())
        return 0

    df.to_parquet(a.out, index=False)
    print("\nwrote %s: %d rows" % (a.out, len(df)))
    print("checkpoints: %s" % df.groupby("ladder").ckpt_idx.nunique().to_dict())
    uncl = df[df.band == "unclassified"].mass.sum() / max(df.mass.sum(), 1e-9)
    print("unclassified mass share: %.2f%%" % (100 * uncl))
    return 0


if __name__ == "__main__":
    sys.exit(main())
