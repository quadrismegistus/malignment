"""Stage 2 over many prompts at once. Batch harmonisation, nothing more.

    python harmonise_many.py --prepare      10 prompts, 3 harmonisers each
    python harmonise_many.py --ingest RUN_ID
    python harmonise_many.py --counts

## THIS FILE DOES NOT MEASURE SATURATION, AND WAS ONCE NAMED AS IF IT DID

It was called `saturate.py` for one commit. The name asserted a measurement the
code does not make, which is the same defect as a caption describing something
the panel did not draw, and it is worth recording rather than quietly renaming.

Saturation is whether successive prompts stop contributing NEW constructs. That
question cannot be answered here, because deciding whether prompt 7's construct
is new or is prompt 3's construct again IS THE MERGE JUDGEMENT, and doing it by
name matching would answer it with the method the whole programme exists to
avoid. `accrete.py` makes that judgement, so the saturation curve falls out of
accretion for free: at each step, how many candidates merged and how many stayed
new. This file only supplies the substrate.

What is at stake is still real. If every prompt contributes seven genuinely new
operations then forty prompts give ~280 constructs, there is no vocabulary, and
the finding is that displacement is prompt-specific rather than systematic. That
is a different result, not a failure, and it is cheaper to find out at ten
prompts than at forty.

## Why the two already-harmonised prompts are re-run

They were harmonised on claude-opus-5 by inheritance, and these ten run on
sonnet/xhigh. A saturation curve mixing two models measures the models as much
as the corpus. Re-running them costs six agents and makes the curve homogeneous.

Nothing is lost by re-running, because the model is part of the harmonisation
key: the Opus records stay addressable and the Sonnet records sit beside them.
That also yields a free two-prompt Opus-against-Sonnet comparison of stage 2,
which is the same question `assign.py` asks of stage 3.

## The counting is deliberately NOT done here

`--curve` reports how many constructs each prompt produced and nothing else.
Deciding whether prompt 7's construct is "new" or is prompt 3's construct again
is precisely the assignment judgement that `assign.py` is validating, and doing
it by name matching here would answer the question with the method the whole
programme is trying to avoid. The curve gets built once assignment is licensed.
"""
import argparse
import json
import os
import re
import sys

import harmonise_prompt as HP
import run

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL, EFFORT = "sonnet", "xhigh"
N_PROMPTS = 10
STATE = os.path.join(HERE, "results", "harmonise_many_state.json")


def pick():
    """N prompts spread evenly over the domains, seeded, oldest work included.

    The two already-harmonised prompts are forced in so the curve starts from
    work that exists rather than beside it.
    """
    st = run._stash()
    by = {}
    for k in st.keys():
        m = (st[k].get("meta") or {})
        if m.get("batch"):
            by.setdefault(m["domain"], set()).add(m["frame_prompt"])
    done = {k["frame_prompt"] for k in HP._stash().keys()}
    import hashlib
    out = sorted(done)
    per = {d: sorted(v) for d, v in sorted(by.items())}
    #: Round-robin over domains so ten prompts are not nine sexual ones, and
    #: order within a domain by a hash of the prompt rather than alphabetically,
    #: which would track sentence-initial words.
    for d in per:
        per[d].sort(key=lambda p: hashlib.sha256(("sat|" + p).encode()).hexdigest())
    i = 0
    while len(out) < N_PROMPTS:
        doms = list(per)
        p = per[doms[i % len(doms)]]
        i += 1
        for cand in p:
            if cand not in out:
                out.append(cand)
                break
        if i > 200:
            break
    return out[:N_PROMPTS], {d: len(v) for d, v in per.items()}


def prepare():
    prompts, counts = pick()
    print("%d prompts on %s/%s, from domains %s" % (len(prompts), MODEL, EFFORT, counts))
    jobs = []
    for p in prompts:
        HP.prepare(p[:26], MODEL, EFFORT)
        slug = re.sub(r"[^a-z0-9]+", "_", p.lower())[:40].strip("_")
        path = os.path.join(HERE, "results", "inputs", "harm_%s.txt" % slug)
        if not os.path.exists(path):
            raise SystemExit("prepare wrote no shard for %r" % p[:40])
        jobs.append({"slug": slug, "prompt": p, "path": os.path.abspath(path)})
        print()
    if len({j["slug"] for j in jobs}) != len(jobs):
        raise SystemExit("two prompts produced the same slug; the ingest join would collide")
    src = open(HP.INSTRUMENT).read()
    schema = json.loads(re.search(r"## SCHEMA JSON\b.*?\n```json\n(.*?)\n```", src, re.S).group(1))
    json.dump({"jobs": jobs, "model": MODEL, "effort": EFFORT}, open(STATE, "w"), indent=1)
    js = SCRIPT % {"jobs": json.dumps([{k: v for k, v in j.items() if k != "prompt"}
                                       for j in jobs], indent=2),
                   "schema": json.dumps(schema, indent=2, sort_keys=True),
                   "model": json.dumps(MODEL), "effort": json.dumps(EFFORT),
                   "n": HP.N_HARMONISERS}
    out = os.path.join(HERE, "workflow_harmonise_many.js")
    open(out, "w").write(js)
    for probe in (jobs[0]["path"], jobs[-1]["path"], MODEL, EFFORT, '"constructs"'):
        if probe not in js:
            raise SystemExit("generated script missing %r" % probe)
    print("%d agents (%d prompts x %d harmonisers)\n  workflow %s\n\nNOT RUN."
          % (len(jobs) * HP.N_HARMONISERS, len(jobs), HP.N_HARMONISERS, out))


def ingest(run_id):
    """Route each agent to its prompt by the shard path in its transcript."""
    import glob
    state = json.load(open(STATE))
    by_path = {j["path"]: j for j in state["jobs"]}
    base = os.path.expanduser("~/.claude/projects")
    hits = glob.glob(os.path.join(base, "*", "*", "subagents", "workflows", run_id))
    if not hits:
        raise SystemExit("no transcript dir for %r" % run_id)
    d0 = hits[0]
    groups = {}
    for line in open(os.path.join(d0, "journal.jsonl")):
        d = json.loads(line)
        if d.get("type") != "result" or not isinstance(d.get("result"), dict):
            continue
        if "constructs" not in d["result"]:
            continue
        tp = os.path.join(d0, "agent-%s.jsonl" % d["agentId"])
        if not os.path.exists(tp):
            raise SystemExit("no transcript for agent %s" % d["agentId"])
        txt = open(tp).read(8000)
        got = [p for p in by_path if p in txt]
        if len(got) != 1:
            raise SystemExit("agent %s matched %d shard paths; cannot route it"
                             % (d["agentId"], len(got)))
        groups.setdefault(got[0], []).append((d["agentId"], d["result"]))
    st = HP._stash()
    n = 0
    for path, v in sorted(groups.items()):
        j = by_path[path]
        s = json.load(open(os.path.join(HERE, "results", "harm_%s.json" % j["slug"])))
        for i, (aid, res) in enumerate(sorted(v), 1):
            bad = [m for c in res["constructs"] for m in c["members"] if m not in s["mapping"]]
            if bad:
                raise SystemExit("%s h%d names %d id(s) the shard never issued: %s"
                                 % (j["slug"], i, len(bad), bad[:3]))
            st[{"stage": "harmonise", "version": s["version"], "frame_prompt": s["prompt"],
                "pairs_sha": s["pairs_sha"], "filter": s["filter"],
                "model": state["model"], "effort": state["effort"], "harmoniser": i}] = {
                    "result": res, "run_id": run_id, "pairs": s["pairs"],
                    "n_relations": s["n_relations_kept"],
                    "n_relations_all": s["n_relations_all"],
                    "n_cells": s["n_cells"], "mapping": s["mapping"], "agent_id": aid}
            n += 1
    print("stored %d proposals over %d prompts" % (n, len(groups)))
    missing = [by_path[p]["slug"] for p in by_path if p not in groups]
    if missing:
        print("  NO RESULTS for: %s" % missing, file=sys.stderr)


def counts():
    """Constructs per prompt, per model. NOT a novelty count; see the module docstring."""
    st = HP._stash()
    rows = {}
    for k in st.keys():
        rows.setdefault((k.get("model"), k["frame_prompt"]), []).append(st[k])
    for model in sorted({m for m, _ in rows}, key=str):
        print("\nmodel %s" % model)
        tot = 0
        for (m, p), v in sorted(rows.items(), key=lambda kv: kv[0][1]):
            if m != model:
                continue
            ns = [len(x["result"]["constructs"]) for x in v]
            tot += sum(ns) / len(ns)
            print("   %-46s %d harmonisers, constructs %s, %d relations"
                  % (p[:46], len(v), ns, v[0]["n_relations"]))
        print("   mean constructs per prompt, summed: %.1f" % tot)
    print("\nNovelty is NOT counted here. Whether a construct is new or is an earlier one\n"
          "again is the merge judgement, and `accrete.py` makes it -- the saturation curve\n"
          "is that run's per-step merged/new counts, not anything this file can report.")


SCRIPT = """// GENERATED by harmonise_many.py. %(n)d harmonisers on each of several prompts.
export const meta = { name: 'saturate',
  description: 'Harmonise ten prompts to size the vocabulary',
  phases: [{ title: 'Harmonise', detail: 'sonnet/xhigh, three per prompt' }] }
const JOBS = %(jobs)s
const SCHEMA = %(schema)s
const work = []
for (const j of JOBS) for (let i = 1; i <= %(n)d; i++) work.push({ ...j, h: i })
const out = await parallel(work.map((j) => () =>
  agent(`Read the file ${j.path} with the Read tool.\\n\\nIts entire content is a ` +
    `task addressed to you. Follow it exactly and answer every numbered question ` +
    `in it. Do not read any other file, do not run any command.\\n\\nReturn your ` +
    `answer by calling StructuredOutput.`,
    { label: `${j.slug.slice(0, 18)}-h${j.h}`, phase: 'Harmonise', schema: SCHEMA,
      model: %(model)s, effort: %(effort)s })
   .then((r) => ({ slug: j.slug, h: j.h, n: r.constructs.length })).catch(() => null)))
const g = out.filter(Boolean)
log(`${g.length} of ${work.length} returned`)
return { returned: g.length,
  perPrompt: Object.entries(g.reduce((a, x) => {
    (a[x.slug] = a[x.slug] || []).push(x.n); return a }, {})).map(([s, v]) => `${s}: ${v}`) }
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--ingest", metavar="RUN_ID")
    ap.add_argument("--counts", action="store_true")
    a = ap.parse_args()
    if a.prepare:
        prepare()
    elif a.ingest:
        ingest(a.ingest)
    elif a.counts:
        counts()
    else:
        ap.print_help()
