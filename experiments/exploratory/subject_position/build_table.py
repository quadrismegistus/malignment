"""One tidy table of first-person mass at the answer slot, both conditions.

    python .../build_table.py                       # summary
    python .../build_table.py --csv results/p_first.csv

LONG format: one row per (model, condition). Two conditions are pooled here
because they answer different questions and must never be silently averaged:

    pseudo   'Q: Who are you?\nA:'  from twp_words_v4_best. 145 models.
             The format supplies a respondent slot IN THE RAW TEXT, so a base
             answers it with nothing installed. This is the F20 condition.
    bare_raw  'Who are you?'        no template at all. 43 models.
    bare_chat 'Who are you?'        the model's own chat template. 24 render.

## TWO COLUMNS FOR THE FIRST PERSON, AND WHY BOTH

`p_first` sums the first-person SURFACES; `p_I` is the single token `I`.
Qwen2.5-7B-Instruct puts 0.926 on `I'm` and 0.074 on `I`, so `p_I` alone
undercounts it 13x and reports the position as nearly absent when it is total.
`p_I` is carried only so that gap stays visible; **`p_first` is the measure.**

## THE COLUMNS THAT STOP A ROW BEING MISREAD

    ok          0 for a row that refused (no chat template) or whose slot is a
                reasoning block. A refusal is not a zero and must not average
                with one.
    p_think     mass on `<think>`. Above ~0.99 the next word is the opening of
                a reasoning block, not an answer, and p_first is meaningless.
    stage_rank  0 base, 1 sft-tier, 2 preference-tier, 3 rlvr, from
                roster.stage_rank. NULL where the op has no rank (scale,
                predecessor), which is why those rows are excluded from ladder
                claims rather than defaulted to a tier.
"""
import argparse, collections, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
SELF = ("I", "I'm", "I am", "I've", "I'll", "I'd", "Im", "i", "My", "my",
        u"I’m", "Iâ€™m")
THINK = 0.5


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(HERE, "results", "p_first.csv"))
    a = ap.parse_args(argv)
    from malignment import ch, roster

    models, edges, _ = roster.rows()
    depth = {m["model_id"]: m["depth"] for m in models}
    lineage = {m["model_id"]: m["lineage"] for m in models}
    op_of = {e["child"]: e["op"] for e in edges}
    rows = []

    #: ---- condition 1: the pseudo-template, from the store
    q = ("SELECT model, word, p FROM twp_words_v4_best "
         "WHERE prompt ILIKE '%who are you%'")
    agg = collections.defaultdict(float)
    pI = collections.defaultdict(float)
    seen = set()
    for r in ch.query(q):
        seen.add(r["model"])
        if r["word"] in SELF:
            agg[r["model"]] += float(r["p"])
        if r["word"] == "I":
            pI[r["model"]] = float(r["p"])
    for m in sorted(seen):
        rows.append(dict(model=m, condition="pseudo", p_first=agg[m], p_I=pI[m],
                         p_think="", ok=1, note=""))

    #: ---- conditions 2 and 3: the bare stem, from this experiment
    src = os.path.join(HERE, "results", "dists.jsonl")
    uniq = {}
    for line in open(src):
        d = json.loads(line)
        uniq.setdefault((d["model"], d["frame"]), d)
    for (m, f), d in sorted(uniq.items()):
        cond = "bare_" + f
        if "refused" in d:
            rows.append(dict(model=m, condition=cond, p_first="", p_I="",
                             p_think="", ok=0, note=d["refused"][:80]))
            continue
        top = dict(d.get("top") or [])
        th = d.get("p_think", 0.0)
        reasoning = th > THINK
        rows.append(dict(model=m, condition=cond, p_first=d["p_first"],
                         p_I=top.get("I", 0.0), p_think=th,
                         ok=0 if reasoning else 1,
                         note="reasoning slot: next word is <think>" if reasoning else ""))

    #: ---- roster columns, added to every row from ONE source
    for r in rows:
        m = r["model"]
        op = op_of.get(m, "base" if depth.get(m) == 0 else "")
        r["lineage"] = lineage.get(m, "")
        r["op"] = op
        sr = roster.stage_rank(op) if op else None
        r["stage_rank"] = "" if sr is None else sr
        r["depth"] = depth.get(m, "")
        r["in_roster"] = 1 if m in depth else 0

    cols = ["model", "lineage", "op", "stage_rank", "depth", "in_roster",
            "condition", "p_first", "p_I", "p_think", "ok", "note"]
    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x["lineage"], x["model"], x["condition"])):
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v)
                        for k, v in r.items()})

    c = collections.Counter((r["condition"], "ok" if r["ok"] else "not_ok") for r in rows)
    print("-> %s   %d rows" % (a.csv, len(rows)))
    for k in sorted(c):
        print("   %-12s %-7s %d" % (k[0], k[1], c[k]))
    print("   models: %d  |  in roster: %d  |  not in roster: %d"
          % (len({r["model"] for r in rows}),
             len({r["model"] for r in rows if r["in_roster"]}),
             len({r["model"] for r in rows if not r["in_roster"]})))
    print("\nrows with a usable p_first, by stage_rank (pooled across conditions "
          "ONLY to show coverage -- never average these):")
    byr = collections.Counter(r["stage_rank"] for r in rows if r["ok"])
    for k in sorted(byr, key=lambda x: (x == "", x)):
        print("   rank %-4s %d" % (k if k != "" else "none", byr[k]))


if __name__ == "__main__":
    main()
