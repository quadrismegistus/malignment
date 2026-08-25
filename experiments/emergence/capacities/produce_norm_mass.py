"""K-scale composition of the resolved distribution per (checkpoint, prompt).

    python produce_norm_mass.py
    python produce_norm_mass.py --check

Per cell: for each of the seven K scales, the mass-weighted mean over
K-rated words, renormalised within rated mass. `k_rated_mass_share` is the
cell's coverage figure; unrated mass is censored, never zeroed.

## WHAT THIS IS FOR

Finding H: the norm signature installed by SFT, partially rebought by DPO,
re-suppressed by RLVR. This is the emergence-axis counterpart of
`experiments/displacement/norm_change`, which shows the endpoint result;
this shows WHEN each norm shift installs on the ladder.

The connection: `norm_change` says register rises at the endpoint (45/50,
p<1e-5) with no dose dependence (p=0.67). H says register installs at SFT
and DPO does not touch it (p=0.90), while concreteness falls at SFT,
rebounds at DPO, and falls again at RLVR. Two modules, opposite signs,
visible at checkpoint grain.

## REPLACES

`m05_norm_acquisition.py` in the archive, which called `word_probs` per
cell. This queries `twp_words` in bulk, one query per checkpoint.
"""
import argparse
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))

DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "m05_norm_mass.parquet")

ROLE_ORDER = {"base_step": 0, "base_endpoint": 1, "sft_step": 2,
              "sft_endpoint": 3, "dpo_endpoint": 4, "rlvr_step": 5}
STAGE_ORDER = {"stage1": 0, "stage2": 1, "stage3": 2}
K_SCALES = ("vulgarity", "register_level", "transgressiveness", "charge",
            "valence", "bodily_harm", "concreteness")


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


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    from malignment import vectors as V
    from malignment.fields import _k

    scales, ratings, _meta = _k("en")
    assert list(scales) == list(K_SCALES), "scale order mismatch: %s vs %s" % (scales, K_SCALES)
    print("%d k_ratings words, %d scales" % (len(ratings), len(scales)))

    texts = battery_texts()
    rows = []

    for ladder, path in [("olmo", os.path.join(DATA, "m05_checkpoint_population.json")),
                          ("pythia", os.path.join(DATA, "pythia_population.json"))]:
        pop = load_population(path)
        print("\n%s: %d checkpoints x %d prompts" % (ladder, len(pop), len(texts)))
        for ci, c in enumerate(pop):
            m = model_string(c)
            result = V.rows(
                "SELECT prompt, word, p FROM twp_words "
                "WHERE model = {m:String} AND prompt IN {pp:Array(String)}",
                m=m, pp=texts)
            by_prompt = {}
            for r in result:
                by_prompt.setdefault(r["prompt"], []).append((r["word"], r["p"]))
            for p in texts:
                words = by_prompt.get(p)
                if not words:
                    continue
                total = sum(pr for _, pr in words)
                if total <= 0:
                    continue
                sums = [0.0] * len(K_SCALES)
                rated_mass = 0.0
                n_rated = 0
                for w, pr in words:
                    r = ratings.get(w) or ratings.get(w.lower())
                    if r is None:
                        continue
                    rated_mass += pr
                    n_rated += 1
                    for i, v in enumerate(r):
                        sums[i] += pr * v
                row = {"ladder": ladder, "model": m,
                       "role": c["role"], "stage": c.get("stage"),
                       "step": c.get("step", 0), "prompt": p,
                       "resolved_mass": total,
                       "k_rated_mass_share": rated_mass / total,
                       "n_rated_words": n_rated}
                for i, sc in enumerate(K_SCALES):
                    row["dist_mean_k_%s" % sc] = (sums[i] / rated_mass
                                                  if rated_mass > 0 else None)
                rows.append(row)
            if (ci + 1) % 25 == 0 or ci == len(pop) - 1:
                print("  [%d/%d] %s  (%d rows so far)"
                      % (ci + 1, len(pop), m[:50], len(rows)))

    df = pd.DataFrame(rows)
    if df.empty:
        print("NO CELLS.")
        return 1

    if a.check:
        old = pd.read_parquet(a.out)
        print("\n--- CHECK ---")
        print("old: %d rows" % len(old))
        print("new: %d rows" % len(df))
        key = ["ladder", "model", "prompt"]
        merged = old.merge(df, on=key, suffixes=("_old", "_new"), how="outer")
        both = merged.dropna(subset=["resolved_mass_old", "resolved_mass_new"])
        sc_cols = ["dist_mean_k_%s" % s for s in K_SCALES]
        max_diff = 0.0
        n_diff = 0
        for col in sc_cols:
            co, cn = col + "_old", col + "_new"
            if co in merged and cn in merged:
                d = abs(merged[co] - merged[cn]).dropna()
                if len(d):
                    md = d.max()
                    nd = (d > 1e-6).sum()
                    max_diff = max(max_diff, md)
                    n_diff += nd
        print("matched: %d  |  differing scale values: %d  |  max diff: %.6f"
              % (len(both), n_diff, max_diff))
        return 0

    df.to_parquet(a.out, index=False)
    print("\nwrote %s: %d rows" % (a.out, len(df)))
    print("checkpoints: olmo %d, pythia %d"
          % (df[df.ladder == "olmo"].model.nunique(),
             df[df.ladder == "pythia"].model.nunique()))
    print("median k_rated_mass_share: %.3f" % df.k_rated_mass_share.median())
    return 0


if __name__ == "__main__":
    sys.exit(main())
