"""Code every F21 generation with task.py. -> results/coded.jsonl

    python -u run.py --plan          counts, nothing sent
    python -u run.py --run           code everything (resumable: the Task stash
                                     caches each call, so a rerun costs nothing
                                     for items already coded)

POPULATION: every row of malign-logits `data/f21_institutional_generations.csv`
(20,389: 11 open families at every stage + 4 frontier chat models), with the
TEXT read from the generation cache, the source of record, not the CSV, which
clips at 500 characters. The generations themselves are ~100 tokens
(`generation.py` max_new_tokens=100, `api_generate.py` max_tokens=100), so this
pass measures where the first few sentences send a party. A 300-token
regeneration is the planned second pass.

Every stage is coded, not only base and last: which arm the analysis compares
is declared in the analysis, and coding more stages costs cents, not a choice.
"""
import argparse, json, os, sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import task as T  # noqa: E402

ML = os.path.expanduser("~/github/malign-logits")
SRC = os.path.join(ML, "data", "f21_institutional_generations.csv")
#: 20 MB, so outside the repo, beside the exported texts.
OUT = os.path.expanduser("~/malignment-data/institution_vs_individual/coded.jsonl")


TEXTS = os.path.expanduser("~/malignment-data/institution_vs_individual/f21_texts.jsonl")


def population():
    if not os.path.exists(TEXTS):
        raise SystemExit("run export_texts.py first, with malign-logits' venv")
    df = pd.DataFrame([json.loads(l) for l in open(TEXTS)])
    src = pd.read_csv(SRC, usecols=["prompt_key"])
    if len(df) != len(src):
        raise SystemExit("export has %d rows, the CSV %d: re-export" % (len(df), len(src)))
    df["generation"] = df.csv_text
    df["key"] = df.prompt_key.str.replace("institutional_", "", regex=False)
    bad = set(df.key) - set(T.DESIGN)
    if bad:
        raise SystemExit("prompt keys not in task.DESIGN: %s" % sorted(bad))
    df["side"] = df.key.map(lambda k: T.DESIGN[k][2])
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    df = population()
    print("rows %d | text from cache %d, csv %d | families %d | prompts %d"
          % (len(df), (df.text_source == "cache").sum(), (df.text_source == "csv").sum(),
             df.family.nunique(), df.key.nunique()))
    print("text chars: median %d, max %d; CSV-clipped rows recovered longer: %d"
          % (df.text.str.len().median(), df.text.str.len().max(),
             (df.text.str.len() > df.generation.fillna("").str.len()).sum()))
    if not a.run:
        return
    prompts = [T.render(p, t, *T.DESIGN[k][:2]) for p, t, k in zip(df.prompt, df.text, df.key)]
    errors = {}
    res = T.task().map(prompts, num_workers=a.workers, errors=errors)
    n_ok = 0
    with open(OUT, "w") as fh:
        for (_, r), x in zip(df.iterrows(), res):
            rec = {k: r[k] for k in ("prompt_key", "key", "side", "family", "layer", "model_id", "idx", "text_source")}
            rec["idx"] = int(rec["idx"])
            rec["text"] = r.text
            rec["coded"] = x.model_dump() if x else None
            if x:
                ok, tot, _ = T.check_spans(r.text, x)
                rec["spans_ok"], rec["spans_total"] = ok, tot
                n_ok += 1
            fh.write(json.dumps(rec) + "\n")
    print("coded %d of %d; failures %d -> %s" % (n_ok, len(df), len(errors), OUT))


if __name__ == "__main__":
    main()
