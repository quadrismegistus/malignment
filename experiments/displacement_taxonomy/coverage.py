"""How much of the roster is usable on the slot prompts, and is the fleet still moving?

    python coverage.py           one line per state, plus the delta since last run
    python coverage.py --full    per-domain and the models still missing

RH's decision on 2026-08-20: WAIT FOR THE FLEET before re-running the cross-lineage
sweep. This is the instrument that says when that wait is over, so the answer is a
measurement rather than a judgement about whether enough has landed.

## What "done" looks like

The sweep ran at 26-29 pairs per prompt. The ceiling is the roster's 50 declared
pairs, and the binding constraint is now pass 1: pass 2 has nearly caught up, so
`topped` and `measured` sit within about a pair of each other and both move only
when a model is measured here for the first time.

So the two numbers to watch are `measured` (does the fleet still reach these
prompts) and `topped - measured` (is pass 2 keeping up). The fleet is done for our
purposes when `measured` stops rising across a few checks and `topped` has closed
on it -- not when it hits 50, which may never happen: the four 32B Olmo arms need
box profile `big80` and the two Llama-70B arms need `twogpu`, 141 GB at fp16
fitting neither a 4090 nor a single A100 (malign [6467]).

## Why it records its own history

A single reading cannot say whether anything is moving, and this seat has twice
compared two numbers taken hours apart from memory. Each run appends to
`results/coverage_log.jsonl` and prints the delta against the previous entry, so
"still climbing" is read off the file rather than recalled.
"""

import argparse, json, os, statistics as S, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "results", "coverage_log.jsonl")


def measure():
    from malignment import roster, vectors as V
    from malignment.slots import read_items, corpora
    slots = {}
    for _, p in corpora():
        for d in read_items(p):
            slots.setdefault(d["prompt"], d)
    ep, _ = roster.endpoints()
    ph = ",".join("'%s'" % p.replace("'", "\\'") for p in slots)
    topped = {r["prompt"]: set(r["ms"]) for r in V.rows(
        "SELECT prompt, groupUniqArray(model) AS ms FROM twp_words_v4_best "
        "WHERE merged=1 AND prompt IN (%s) GROUP BY prompt" % ph)}
    allm = {r["prompt"]: set(r["ms"]) for r in V.rows(
        "SELECT prompt, groupUniqArray(model) AS ms FROM twp_words_v4_best "
        "WHERE prompt IN (%s) GROUP BY prompt" % ph)}
    t = [sum(1 for b, a in ep.items() if b in topped.get(p, ()) and a in topped.get(p, ()))
         for p in slots]
    m = [sum(1 for b, a in ep.items() if b in allm.get(p, ()) and a in allm.get(p, ()))
         for p in slots]
    seen = set().union(*allm.values()) if allm else set()
    missing = sorted({x for b, a in ep.items() for x in (b, a) if x not in seen})
    return {"prompts": len(slots), "roster": len(ep),
            "topped_mean": round(S.mean(t), 2), "topped_median": S.median(t),
            "measured_mean": round(S.mean(m), 2), "measured_median": S.median(m),
            "at35": sum(1 for x in t if x >= 35), "at40": sum(1 for x in t if x >= 40),
            "models_never_here": len(missing), "missing": missing,
            "domains": {}, "slots": slots and None}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    now = measure()
    prev = None
    if os.path.isfile(LOG):
        with open(LOG) as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        prev = rows[-1] if rows else None
    d = lambda k: ("" if not prev else "  (%+.2f)" % (now[k] - prev[k])
                   if isinstance(now[k], float) else "  (%+d)" % (now[k] - prev[k]))
    print("%d slot prompts, roster of %d declared pairs\n" % (now["prompts"], now["roster"]))
    print("  topped per prompt      %6.2f  median %2d%s" % (now["topped_mean"], now["topped_median"], d("topped_mean")))
    print("  measured per prompt    %6.2f  median %2d%s" % (now["measured_mean"], now["measured_median"], d("measured_mean")))
    print("  pass-2 lag             %6.2f          (topped behind measured)" % (now["measured_mean"] - now["topped_mean"]))
    print("  prompts at 35+ topped  %6d%s" % (now["at35"], d("at35")))
    print("  prompts at 40+ topped  %6d%s" % (now["at40"], d("at40")))
    print("  roster models never measured here: %d%s" % (now["models_never_here"], d("models_never_here")))
    if a.full and now["missing"]:
        for x in now["missing"]:
            print("      %s" % x)
    if prev:
        moved = now["measured_mean"] > prev["measured_mean"]
        print("\n  %s" % ("STILL CLIMBING -- the fleet is reaching these prompts"
                          if moved else "measured did not move since the last check"))
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    row = {k: v for k, v in now.items() if k not in ("missing", "domains", "slots")}
    row["ts"] = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                               capture_output=True, text=True).stdout.strip()
    with open(LOG, "a") as fh:
        fh.write(json.dumps(row) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
