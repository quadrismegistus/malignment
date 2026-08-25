"""Resolved twp mass by POS class per (checkpoint, prompt), from CH in bulk.

    python produce_class_mass.py
    python produce_class_mass.py --check   # compare against the existing parquet

## WHAT THIS REPLACES

`m05_class_mass.py` in the archive called `word_probs` per cell: ~146k cells
at 192ms each. This queries `twp_words` in bulk, one query per checkpoint,
and joins onto the frozen tag table in Python.

## WHAT IT EMITS

`data/m05_class_mass.parquet`, one row per (ladder, checkpoint, prompt,
pos_class): mass (sum of p on words of that class), plus resolved_mass,
n_rows, payload_empty per cell.

## THE TAG TABLE IS FROZEN

`data/m05_syntax_tags.parquet` was built by `m05_syntax_tags.py` in the
archive using contextual POS from spaCy `en_core_web_sm` 3.8.14. A word's
POS depends on the prompt it follows (`fall` is VERB after `She began to`
but NOUN after `The autumn`), so the tags are per (prompt, word) and the
table is 338,092 rows over 584 prompts.

`get_pos` in `malignment.pos` implements the same tagger and caches in a
HashStash. If lacan's current run expands coverage beyond the battery, the
tag table can be rebuilt from that stash without rescoring.
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
OUT = os.path.join(DATA, "m05_class_mass.parquet")

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


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    from malignment import vectors as V

    tags = pd.read_parquet(os.path.join(DATA, "m05_syntax_tags.parquet"))
    tagmap = {(r.prompt, r.word): r.pos_class for r in tags.itertuples()}
    texts = battery_texts()
    print("%d battery prompts, %d tagged (prompt, word) pairs" % (len(texts), len(tagmap)))

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
                                     payload_empty=True,
                                     pos_class="NONE", mass=0.0))
                    continue
                masses = collections.defaultdict(float)
                resolved = 0.0
                for w, prob in words:
                    masses[tagmap.get((p, w), "UNTAGGED")] += prob
                    resolved += prob
                base = dict(ladder=ladder, ckpt_idx=idx, model=m,
                            role=c["role"], stage=c.get("stage"),
                            step=c.get("step"), prompt=p,
                            resolved_mass=resolved, n_rows=len(words),
                            payload_empty=(len(words) == 0))
                if not masses:
                    rows.append(dict(base, pos_class="NONE", mass=0.0))
                else:
                    for cls, mass in masses.items():
                        rows.append(dict(base, pos_class=cls, mass=mass))
            if (idx + 1) % 25 == 0 or idx == len(pop) - 1:
                print("  [%d/%d] %s" % (idx + 1, len(pop), m[:55]))

    df = pd.DataFrame(rows)
    if df.empty:
        print("NO CELLS ANSWERED.")
        return 1

    if a.check:
        old = pd.read_parquet(a.out)
        print("\n--- CHECK against %s ---" % a.out)
        print("old: %d rows, checkpoints %s" % (len(old), old.groupby("ladder").ckpt_idx.nunique().to_dict()))
        print("new: %d rows, checkpoints %s" % (len(df), df.groupby("ladder").ckpt_idx.nunique().to_dict()))
        key = ["ladder", "model", "prompt", "pos_class"]
        merged = old.merge(df, on=key, suffixes=("_old", "_new"), how="outer")
        both = merged.dropna(subset=["mass_old", "mass_new"])
        diff = both[abs(both["mass_old"] - both["mass_new"]) > 1e-6]
        print("matched: %d  |  differing mass: %d  |  old-only: %d  |  new-only: %d"
              % (len(both), len(diff),
                 merged["mass_new"].isna().sum(), merged["mass_old"].isna().sum()))
        if len(diff):
            print("max abs diff: %.6f" % abs(diff["mass_old"] - diff["mass_new"]).max())
        return 0

    df.to_parquet(a.out, index=False)
    print("\nwrote %s: %d rows" % (a.out, len(df)))
    print("checkpoints: %s" % df.groupby("ladder").ckpt_idx.nunique().to_dict())
    untag = df[df.pos_class == "UNTAGGED"].mass.sum() / max(df.mass.sum(), 1e-9)
    print("UNTAGGED mass share: %.2f%%" % (100 * untag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
