"""Export F21's generations at full cached length. -> ~/malignment-data/institution_vs_individual/f21_texts.jsonl

    ~/github/malign-logits/.venv/bin/python export_texts.py

Run with MALIGN-LOGITS' venv: the generation cache is read through its
`CacheManager`, whose package imports plotly, which this repo does not carry.
One row per row of `data/f21_institutional_generations.csv`, with the cached
text where the cache has it (`text_source` says which), because the CSV clips
at 500 characters. Read-only on the cache.
"""
import json, os, sys

import pandas as pd

ML = os.path.expanduser("~/github/malign-logits")
sys.path.insert(0, ML)
from malign_logits.cache import get_cache  # noqa: E402

SRC = os.path.join(ML, "data", "f21_institutional_generations.csv")
OUT = os.path.expanduser("~/malignment-data/institution_vs_individual/f21_texts.jsonl")


def main():
    df = pd.read_csv(SRC)
    cm = get_cache()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = {"cache": 0, "csv": 0}
    with open(OUT, "w") as fh:
        for r in df.itertuples():
            try:
                full = cm.get_generation(r.model_id, r.prompt, temp=1.0, idx=int(r.idx))
            except Exception:
                full = None
            if isinstance(full, str) and full.strip():
                text, src = full, "cache"
            else:
                text, src = (r.generation if isinstance(r.generation, str) else ""), "csv"
            n[src] += 1
            fh.write(json.dumps({"prompt_key": r.prompt_key, "prompt": r.prompt, "model_id": r.model_id,
                                 "family": r.family, "layer": r.layer, "idx": int(r.idx),
                                 "csv_text": r.generation if isinstance(r.generation, str) else "",
                                 "text": text, "text_source": src}) + "\n")
    print("wrote %d rows (%s) -> %s" % (len(df), n, OUT))


if __name__ == "__main__":
    main()
