"""Code and analyse the frontier API passages. -> results/analysis_frontier.md

    python -u frontier_code.py --run        code (cached) then analyse
    python -u frontier_code.py              analyse only

WRITTEN 2026-09-24 BEFORE ANY FRONTIER PASSAGE WAS CODED. The frontier models
have no base, so this is an ENDPOINT contrast, not a change: per model, the
individual-side share minus the institution-side share, on the regeneration's 36
prompts (`frontier_generate.py`: prompt as user message, vendor default system,
t=1.0, 256 tokens, 10 draws). The expected direction is the one pass 1 found on
F21's 100-token frontier passages and the one the open models' aligned arm shows
at the endpoint of the regeneration:

    outward, authority, channel   individual > institution
    move_voice_direct             institution > individual

Unit: the 18 disputes (sign test per model, and pooled over the four models).
Same filter and outcome definitions as `analyse_regen.py`. The open models'
ALIGNED arm is reported beside each model for comparison, on the same unit.

CAVEAT BUILT IN: deepseek/deepseek-v4-flash resolves server-side to
deepseek-flash, the coder's own model. Its row is reported, flagged, and left
out of the pooled test.
"""
import collections, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402
import task as T  # noqa: E402

DESIGN = json.load(open(os.path.join(HERE, "prompts", "design.json")))
BY_PROMPT = {d["prompt"]: (k, d) for k, d in DESIGN.items()}
MODELS = ["anthropic/claude-sonnet-4-6", "anthropic/claude-haiku-4-5",
          "openai/gpt-4o-mini", "deepseek/deepseek-v4-flash"]
SELF_CODED = {"deepseek/deepseek-v4-flash"}
OUT = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_frontier.jsonl")
OUTCOMES = ["outward", "move_voice_direct", "authority", "channel", "any", "inward",
            "move_third_party"]
EXPECT = {"outward": 1, "move_voice_direct": -1, "authority": 1, "channel": 1}


def population():
    from malignment.checkpoint import Checkpoint
    rows = []
    for m in MODELS:
        for st in Checkpoint(m).gen_stashes():
            for _, v in st.items():
                hit = BY_PROMPT.get(v.get("prompt"))
                if hit and v.get("render") == "api" and v.get("frame") == "chat_sysdefault":
                    rows.append({"model": m, "key": hit[0], "scenario": hit[1]["scenario"],
                                 "side": hit[1]["side"], "prompt": hit[1]["prompt"],
                                 "sample": v.get("sample_idx"), "text": v.get("text") or ""})
    return rows


def code(rows, workers=16):
    prompts = [T.render(r["prompt"], r["text"], DESIGN[r["key"]]["speaker"],
                        DESIGN[r["key"]]["counterparty"]) for r in rows]
    errors = {}
    res = T.task().map(prompts, num_workers=workers, errors=errors)
    with open(OUT, "w") as fh:
        for r, x in zip(rows, res):
            fh.write(json.dumps(dict(r, coded=x.model_dump() if x else None)) + "\n")
    print("coded %d of %d, failures %d" % (len(rows) - len(errors), len(rows), len(errors)))


def gaps(rows, name, key):
    """{group: [per-scenario (individual share - institution share)]}"""
    acc = collections.defaultdict(list)
    for r in rows:
        if r.get("coded") and A.keep(r["coded"]):
            acc[(key(r), r["scenario"], r["side"])].append(A.outcomes(r["coded"])[name])
    out = collections.defaultdict(dict)
    for (g, s, sd), v in acc.items():
        out[g].setdefault(s, {})[sd] = np.mean(v)
    return {g: {s: d["individual"] - d["institution"] for s, d in sc.items()
                if "individual" in d and "institution" in d} for g, sc in out.items()}


def main():
    if "--run" in sys.argv:
        code(population())
    rows = [json.loads(l) for l in open(OUT)]
    open_rows = [json.loads(l) for l in open(A.SRC)]
    open_rows = [dict(r, model="open aligned (pooled)") for r in open_rows
                 if r.get("coded") and r["arm"] == "aligned"]
    L = ["# Frontier API passages: individual minus institution at the endpoint", "",
         "Producer `frontier_code.py`, written before any frontier passage was coded. Same 36 prompts, "
         "256 tokens, t=1.0 (top_p pinned 1.0 on DeepSeek only; vendor default elsewhere), 10 draws. "
         "Cells: individual share / institution share (disputes with individual > institution / <). "
         "DeepSeek (*) is coded by its own model and is left out of the pooled test.", ""]
    L += ["| outcome | " + " | ".join(m.split("/")[-1] + ("*" if m in SELF_CODED else "") for m in MODELS)
          + " | open aligned | pooled 3 frontier: disputes +/- | p | expected |",
          "|---|" + "---|" * (len(MODELS) + 4)]
    for name in OUTCOMES:
        fr = gaps(rows, name, lambda r: r["model"])
        op = gaps(open_rows, name, lambda r: r["model"])
        lv = {}
        for m in MODELS + ["open aligned (pooled)"]:
            src = rows if m != "open aligned (pooled)" else open_rows
            sh = collections.defaultdict(list)
            for r in src:
                if r["model"] == m and r.get("coded") and A.keep(r["coded"]):
                    sh[r["side"]].append(A.outcomes(r["coded"])[name])
            lv[m] = (np.mean(sh["individual"]) if sh["individual"] else np.nan,
                     np.mean(sh["institution"]) if sh["institution"] else np.nan)
        cells = []
        for m in MODELS:
            d = fr.get(m, {})
            u = sum(x > 0 for x in d.values()); dn = sum(x < 0 for x in d.values())
            cells.append("%.2f / %.2f (%d/%d)" % (lv[m][0], lv[m][1], u, dn))
        od = op.get("open aligned (pooled)", {})
        ocell = "%.2f / %.2f (%d/%d)" % (lv["open aligned (pooled)"][0], lv["open aligned (pooled)"][1],
                                          sum(x > 0 for x in od.values()), sum(x < 0 for x in od.values()))
        pooled = [np.mean([fr[m][s] for m in MODELS if m not in SELF_CODED and s in fr.get(m, {})])
                  for s in sorted({s for m in MODELS if m not in SELF_CODED for s in fr.get(m, {})})]
        u, dn, p = A.sign(pooled)
        L.append("| %s | %s | %s | %d/%d | %.3g | %s |" % (name, " | ".join(cells), ocell, u, dn, p,
                 {1: "ind > inst", -1: "inst > ind"}.get(EXPECT.get(name), "")))
    ok = sum(1 for r in rows if r.get("coded")); L += ["", "Coded passages: %d." % ok]
    res = os.path.join(HERE, "results", "analysis_frontier.md")
    open(res, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
