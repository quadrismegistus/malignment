"""The coder-drift gate declared in README.md, run BEFORE any new rung is coded. -> results/drift_gate.md

    python -u drift_gate.py

40 of Y's pass-A passages, drawn at seed 20260924 from Y's confirmatory store,
re-coded today with Y's coder (`code_y_superego_v3`, unchanged, via its own
`prepare`), compared with the codes Y stored in August. The continuation is
recovered from Y's `tagged` field with the coder's own `strip_tags`.

Gate: SUPEREGO_IN_SCENE and sexual_scene each agree on >= 36 of 40. Pass ->
Y's stored codes are re-used for the ten ladders' base and aligned models. Fail
-> every re-used Y passage on those ladders is re-coded with the new rungs.
SUPEREGO_IN_SCENE is recomputed from today's fields with the same rule Y's
composite uses (moralisation, guilt/shame or consent hesitation inside a scene),
the rule `y_diegetic` applies to the stored rows.
"""
import importlib.util, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.expanduser("~/malignment-data/y_diegetic/y_confirmatory_coded.jsonl")
SHARD = os.path.expanduser("~/github/malign-logits/data/y_shard_00.json")
CODER = os.path.expanduser("~/github/malign-logits/malign_logits/tasks/code_y_superego_v3.py")
N, NEED, SEED = 40, 36, 20260924
SUPER = ("moralisation_in_scene", "guilt_or_shame", "consent_hesitation")


def coder():
    spec = importlib.util.spec_from_file_location("code_y_superego_v3", CODER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def superego(r):
    return any(r.get(f) == "YES" for f in SUPER)


def main():
    Y = coder()
    stems = {s["prompt_id"]: s["prompt"] for s in json.load(open(SHARD))["prompts"]}
    rows = [json.loads(l) for l in open(STORE)]
    rows = [r for r in rows if r.get("pass") == "A" and r.get("parsed") and r.get("tagged")]
    sample = random.Random(SEED).sample(rows, N)
    items = [Y.prepare(stems[r["prompt_id"]], r.get("word") or "", Y.strip_tags(r["tagged"])) for r in sample]
    errs = {}
    res = Y.SuperegoV3Task().map(items, num_workers=8, errors=errs)
    agree = {"sexual_scene": 0, "SUPEREGO": 0}
    n = 0
    rowsout = []
    for r, x in zip(sample, res):
        if x is None:
            continue
        n += 1
        new = x.model_dump()
        a1 = new.get("sexual_scene") == r.get("sexual_scene")
        a2 = superego(new) == superego(r)
        agree["sexual_scene"] += a1
        agree["SUPEREGO"] += a2
        rowsout.append((r["mid"], r.get("sexual_scene"), new.get("sexual_scene"), superego(r), superego(new)))
    ok = n == N and all(v >= NEED for v in agree.values())
    L = ["# Coder-drift gate", "",
         "Producer `drift_gate.py`, declared in README.md before any new rung was coded. %d of %d Y pass-A passages "
         "re-coded (seed %d); %d coder errors." % (n, N, SEED, len(errs)), "",
         "| field | agree | of | needed |", "|---|---|---|---|",
         "| sexual_scene | %d | %d | %d |" % (agree["sexual_scene"], n, NEED),
         "| SUPEREGO (moralisation / guilt / consent) | %d | %d | %d |" % (agree["SUPEREGO"], n, NEED), "",
         "**%s**: %s" % ("PASS" if ok else "FAIL",
                         "Y's stored codes are re-used." if ok else
                         "re-code every re-used Y passage on the ten ladders with the new rungs."), "",
         "| mid | sexual_scene Y / now | superego Y / now |", "|---|---|---|"]
    L += ["| %s | %s / %s | %s / %s |" % row for row in rowsout]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "drift_gate.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:9]))


if __name__ == "__main__":
    main()
