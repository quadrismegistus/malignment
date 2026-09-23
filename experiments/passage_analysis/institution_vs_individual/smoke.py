"""Smoke test of task.py on 20 F21 generations, chosen by rule, not by reading.
-> results/smoke.jsonl, printed as a table

    python -u smoke.py

Selection (deterministic, idx order): two matched pairs (housing_2, labor_2),
both sides, Tulu base and last stage (rlvr) and Qwen2.5 last stage (dpo), the
first generation of each = 12; the police pair from OLMo-3 last stage = 2; the
FIRST quiz-looking generation (regex) from two families = 2; Claude Sonnet 4.6
on the four housing/labor prompts = 4. Its purpose is to check the coder uses
the relation codes as defined, not to estimate anything.
"""
import json, os, re, sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import task as T  # noqa: E402

SRC = os.path.expanduser("~/github/malign-logits/data/f21_institutional_generations.csv")
QUIZ = r"(?:^|\s)[A-D][\.\)]\s.{2,}?\s[B-D][\.\)]\s|Answer\s*:"


def pick(df):
    rows = []
    def first(**kw):
        s = df
        for k, v in kw.items():
            s = s[s[k] == v]
        return s.sort_values("idx").iloc[0]
    for pr in ("housing_tenant_2", "housing_landlord_2", "labor_worker_2", "labor_mgmt_2"):
        for fam, lay in (("tulu", "base"), ("tulu", "rlvr"), ("qwen", "dpo")):
            rows.append(first(prompt_key="institutional_" + pr, family=fam, layer=lay))
    for pr in ("police_citizen_1", "police_officer_1"):
        rows.append(first(prompt_key="institutional_" + pr, family="olmo", layer="rlvr"))
    for fam, lay in (("tulu", "rlvr"), ("qwen", "base")):
        s = df[(df.family == fam) & (df.layer == lay) & df.generation.fillna("").str.contains(QUIZ, regex=True)]
        rows.append(s.sort_values(["prompt_key", "idx"]).iloc[0])
    for pr in ("housing_tenant_2", "housing_landlord_2", "labor_worker_2", "labor_mgmt_2"):
        rows.append(first(prompt_key="institutional_" + pr, family="anthropic/claude-sonnet-4-6-raw"))
    return pd.DataFrame(rows)


def main():
    df = pd.read_csv(SRC)
    s = pick(df)
    t = T.task()
    prompts = [T.render(p, g) for p, g in zip(s.prompt, s.generation)]
    errors = {}
    res = t.map(prompts, num_workers=8, errors=errors)
    out = open(os.path.join(HERE, "results", "smoke.jsonl"), "w")
    for (_, r), x, pr in zip(s.iterrows(), res, prompts):
        rec = {"prompt_key": r.prompt_key, "family": r.family, "layer": r.layer, "idx": int(r.idx),
               "generation": r.generation, "coded": x.model_dump() if x else None,
               "spans": T.check_spans(r.generation, x)[:2] if x else None}
        out.write(json.dumps(rec) + "\n")
        key = r.prompt_key.replace("institutional_", "")
        fam = r.family.split("/")[-1][:14]
        if not x:
            print("%-20s %-14s %-5s FAILED %s" % (key, fam, r.layer, errors.get(len(errors))))
            continue
        refs = "; ".join("%s=%s/%s%s" % (q.body[:28], q.relation, q.stance, "/AUTH" if q.authority_over_counterparty else "")
                         for q in x.referrals) or "-"
        print("%-20s %-14s %-7s form=%-15s move=%-12s spans %d/%d | %s -> %s | %s"
              % (key, fam, r.layer, x.form, x.primary_move, *rec["spans"], x.speaker, x.counterparty, refs))
    print("failures:", len(errors))


if __name__ == "__main__":
    main()
