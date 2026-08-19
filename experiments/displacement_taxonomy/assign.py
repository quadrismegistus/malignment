"""Can a rater place a relation in an existing vocabulary? The question that decides scale.

    python assign.py --build
    python assign.py --prepare
    python assign.py --ingest RUN_ID
    python assign.py --report

## Why this and not more pairwise work

Forty prompts give roughly 250 constructs. All-pairs merging is ~31,000
comparisons; name-blocked candidates still run to ~750 pairs and thousands of
agents. Neither is affordable. The linear alternative is assignment: hold the
vocabulary as it stands and ask where each new construct goes, which is one call
per prompt instead of one per pair, and makes the whole programme O(prompts).

Everything downstream rests on raters being able to do that, and nothing so far
shows they can. `discriminate.py` validated a THREE-way choice with topic held
constant, since every relation in a triad completed the same sentence.
Assignment is many-way AND cross-prompt, so topic varies and is available as a
shortcut for the first time. That gap is the reason this file exists.

## What is being scored

    home present   the item's own construct is in the vocabulary   -> that letter
    home withheld  its construct was removed entirely              -> `new`

Both, because a rater who assigns everything somewhere scores perfectly on the
first kind alone, and a vocabulary that cannot refuse an item is not a
vocabulary.

## The topic shortcut

A sexual-domain item sent to a sexual-domain entry can be right for the wrong
reason. Two things catch it: the vocabulary contains an institutional and a
sexual entry that are plausibly ONE operation, so an operation-reader can cross
domains where a topic-reader cannot; and `basis` is required, which is the only
channel that distinguishes a hit from a hit obtained by matching subject matter.
Read the bases. The rate alone cannot see this.

## Models are arms, not a setting

The first stage-2 and stage-3 runs inherited claude-opus-5 because no model was
named in the workflow, so every number booked so far is an Opus number. The
scaled sweep is the expensive part and wants the cheaper model, so this runs
each model as its own arm over identical inputs and the model is part of the
stash key.
"""
import argparse
import hashlib
import json
import os
import re
import sys

import discriminate as D

HERE = os.path.dirname(os.path.abspath(__file__))
INSTRUMENT = os.path.join(HERE, "INSTRUMENT_assign.md")
STASH = os.path.join(HERE, "results", "assign_stash")
SEED = "assign-a1"
N_RATERS = 3
ARMS = [("sonnet", "xhigh"), ("opus", None)]
LETTERS = "ABCDEFGHIJKLMNOP"


def _stash():
    from hashstash import HashStash
    os.makedirs(STASH, exist_ok=True)
    return HashStash(root_dir=STASH, engine="jsonl", flat=True)


def build():
    """Vocabulary entries, held-out items, and the answer key."""
    C = D.cores()
    #: One flat pool across both prompts. This is the point: the vocabulary is
    #: cross-prompt, which is what introduces the topic shortcut the design has
    #: to survive.
    cons = []
    for prompt in sorted(C):
        for name, (core, rel) in sorted(C[prompt].items()):
            cons.append({"prompt": prompt, "name": name, "ids": list(core), "rel": rel})
    #: Home-withheld items come from SMALL constructs. Withholding a large one
    #: strips most of the vocabulary's exemplars and makes every other item
    #: easier, which would inflate the rate this run exists to measure.
    small = [c for c in cons if len(c["ids"]) == 2]
    rng = D._rng("withhold")
    withheld = {id(c) for c in rng.sample(small, min(2, len(small)))}
    vocab, items, key = [], [], {}
    for c in cons:
        #: Hold out MORE from a large construct. Only six constructs have a core
        #: of 2 or more, so one item each gives four scored home-present answers
        #: and a rate on four items is not a rate. Taking three from a core of
        #: ten still leaves seven exemplars defining the entry.
        n_hold = 3 if len(c["ids"]) >= 8 else (2 if len(c["ids"]) >= 5 else
                                               (1 if len(c["ids"]) >= 2 else 0))
        held = D._rng("hold", c["prompt"], c["name"]).sample(sorted(c["ids"]), n_hold)
        if id(c) in withheld:
            #: Removed entirely; its held-out items' correct answer is `new`.
            items.extend((h, c, "new") for h in held)
            continue
        vocab.append(c)
        items.extend((h, c, None) for h in held)
    D._rng("vocab-order").shuffle(vocab)
    for n, c in enumerate(vocab):
        c["letter"] = LETTERS[n]
    out_items = []
    for held, c, forced in items:
        iid = "i" + hashlib.sha256(("%s|%s" % (c["name"], held)).encode()).hexdigest()[:6]
        out_items.append({"iid": iid, "rid": held, "home": c["name"],
                          "prompt": c["prompt"],
                          "answer": forced or c.get("letter")})
        key[iid] = out_items[-1]["answer"]
    D._rng("item-order").shuffle(out_items)
    return vocab, out_items, key


def _fmt(rel, rid):
    x = rel[rid]
    return "     A: %s\n     B: %s\n     %s" % (", ".join(x["a_words"]),
                                                ", ".join(x["b_words"]), x["sentence"])


def prepare(build_only=False):
    vocab, items, key = build()
    held = {i["rid"] for i in items}
    print("%d vocabulary entries, %d items (%d with home present, %d withheld -> new)"
          % (len(vocab), len(items), sum(1 for i in items if i["answer"] != "new"),
             sum(1 for i in items if i["answer"] == "new")))
    for c in vocab:
        print("   %s  %-30s %d exemplar(s)  [%s]"
              % (c["letter"], c["name"], len([i for i in c["ids"] if i not in held]),
                 c["prompt"][:22]))
    for i in items:
        print("   item %s -> %-4s  from %r" % (i["iid"], i["answer"], i["home"][:34]))
    if build_only:
        return
    src = open(INSTRUMENT).read()
    tmpl = re.search(r"## PROMPT TEMPLATE\s*\n+```\n(.*?)\n```", src, re.S).group(1)
    schema = json.loads(re.search(r"## SCHEMA JSON\b.*?\n```json\n(.*?)\n```", src, re.S).group(1))
    vb = []
    for c in vocab:
        lines = ["ENTRY %s" % c["letter"]]
        for rid in [i for i in c["ids"] if i not in held]:
            lines.append(_fmt(c["rel"], rid))
            lines.append("")
        vb.append("\n".join(lines).rstrip())
    #: Look the relation map up BY PROMPT. An item can come from a withheld
    #: construct, and it can come from the prompt that no vocabulary entry
    #: happens to sit first under, so indexing off `vocab` order raises on the
    #: cross-prompt case -- which is the case this whole instrument is about.
    relmap = {}
    for prompt, d in D.cores().items():
        for _, (_, rel) in d.items():
            relmap[prompt] = rel
    ib = ["ITEM %s\n%s" % (i["iid"], _fmt(relmap[i["prompt"]], i["rid"])) for i in items]
    text = (tmpl.replace("{{n_entries}}", str(len(vocab)))
                .replace("{{n_items}}", str(len(items)))
                .replace("{{vocabulary}}", "\n\n".join(vb))
                .replace("{{items}}", "\n\n".join(ib)))
    path = os.path.join(HERE, "results", "inputs", "assign_a1.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)
    for i in items:
        if i["iid"] not in text:
            raise SystemExit("item %s missing from its own task" % i["iid"])
    #: The answer key must not travel with the task.
    for c in vocab:
        if c["name"] in text:
            raise SystemExit("construct name %r leaked into the task text" % c["name"])
    json.dump({"vocab": [{k: v for k, v in c.items() if k != "rel"} for c in vocab],
               "items": items, "key": key, "seed": SEED, "arms": ARMS},
              open(os.path.join(HERE, "results", "assign_state.json"), "w"), indent=1)
    jobs = [{"model": m, "effort": e, "rater": r}
            for m, e in ARMS for r in range(1, N_RATERS + 1)]
    js = SCRIPT % {"path": json.dumps(os.path.abspath(path)),
                   "jobs": json.dumps(jobs, indent=2),
                   "schema": json.dumps(schema, indent=2, sort_keys=True)}
    out = os.path.join(HERE, "workflow_assign.js")
    open(out, "w").write(js)
    for probe in (os.path.abspath(path), '"assignments"', "sonnet", "xhigh"):
        if probe not in js:
            raise SystemExit("generated script missing %r" % probe)
    print("\n  task     %s\n  %d agents (%d arms x %d raters)\n  workflow %s\n\nNOT RUN."
          % (path, len(jobs), len(ARMS), N_RATERS, out))


def ingest(run_id):
    """Arm comes back in the RESULT here, not from a transcript join.

    `discriminate.py` had to recover its condition from the agent transcript
    because the journal carries no caller metadata. The cleaner fix, used here,
    is to make the agent itself echo its arm: the schema cannot carry it, so the
    workflow returns per-job records and the run's summary is read from the
    journal's LAST line rather than per-agent. Both routes are legitimate; this
    one is cheaper and does not depend on the prompt text being greppable.
    """
    import glob
    state = json.load(open(os.path.join(HERE, "results", "assign_state.json")))
    iids = {i["iid"] for i in state["items"]}
    base = os.path.expanduser("~/.claude/projects")
    hits = glob.glob(os.path.join(base, "*", "*", "subagents", "workflows", run_id))
    if not hits:
        raise SystemExit("no transcript dir for %r" % run_id)
    d0 = hits[0]
    recs = []
    for line in open(os.path.join(d0, "journal.jsonl")):
        d = json.loads(line)
        if d.get("type") != "result" or not isinstance(d.get("result"), dict):
            continue
        if "assignments" not in d["result"]:
            continue
        #: Read the model from the assistant turns' own `message.model`, not by
        #: grepping the file for a "model" string: the prompt text and tool
        #: payloads also contain that word, and a regex over the raw bytes
        #: matched nothing usable while the field was sitting there parsed.
        tp = os.path.join(d0, "agent-%s.jsonl" % d["agentId"])
        seen = set()
        if os.path.exists(tp):
            for l in open(tp):
                try:
                    e = json.loads(l)
                except ValueError:
                    continue
                mv = (e.get("message") or {}).get("model") or e.get("model")
                if mv:
                    seen.add(mv)
        if len(seen) > 1:
            raise SystemExit("agent %s ran on %d models: %s" % (d["agentId"], len(seen), seen))
        recs.append((d["agentId"], seen.pop() if seen else None, d["result"]))
    st, n = _stash(), 0
    seen = {}
    for aid, model, res in sorted(recs):
        bad = [a["item"] for a in res["assignments"] if a["item"] not in iids]
        if bad:
            raise SystemExit("answers name %d item(s) never issued: %s" % (len(bad), bad[:3]))
        model = model or "unknown"
        seen[model] = seen.get(model, 0) + 1
        st[{"stage": "assign", "version": "a1", "seed": SEED,
            "model": model, "rater": seen[model]}] = dict(res, agent_id=aid, run_id=run_id)
        n += 1
    print("stored %d rater-runs: %s" % (n, seen))
    if "unknown" in seen:
        print("  could not read the model for %d agent(s); the arm is unresolved"
              % seen["unknown"], file=sys.stderr)


def report():
    from collections import Counter
    state = json.load(open(os.path.join(HERE, "results", "assign_state.json")))
    key = state["key"]
    home = {i["iid"]: i["home"] for i in state["items"]}
    st = _stash()
    rows = []
    for k in st.keys():
        for a in st[k]["assignments"]:
            rows.append(dict(a, model=k["model"], rater=k["rater"],
                             truth=key[a["item"]], home=home[a["item"]]))
    if not rows:
        raise SystemExit("nothing ingested")
    print("%d assignments\n" % len(rows))
    for model in sorted({r["model"] for r in rows}):
        R = [r for r in rows if r["model"] == model]
        pres = [r for r in R if r["truth"] != "new"]
        newi = [r for r in R if r["truth"] == "new"]
        hp = sum(1 for r in pres if r["assign"] == r["truth"])
        hn = sum(1 for r in newi if r["assign"] == "new")
        forced = sum(1 for r in newi if r["assign"] != "new")
        print("%-8s HOME PRESENT %2d  correct %.2f  (chance ~%.2f)"
              % (model, len(pres), hp / len(pres) if pres else 0,
                 1 / max(1, len(state["vocab"]))))
        print("%-8s HOME WITHHELD %2d  said new %.2f  forced into an entry %.2f"
              % ("", len(newi), hn / len(newi) if newi else 0,
                 forced / len(newi) if newi else 0))
        conf = {}
        for r in R:
            ok = (r["assign"] == r["truth"])
            conf.setdefault(r["confidence"], []).append(ok)
        print("%-8s by confidence: %s\n"
              % ("", {c: "%d/%d" % (sum(v), len(v)) for c, v in sorted(conf.items())}))
    #: An answer distribution piled on one or two letters means the panel found a
    #: default rather than a home, exactly as a clustered position distribution
    #: would in d1.
    print("answers by entry letter: %s" % dict(Counter(r["assign"] for r in rows)))
    print("\nitems no rater placed correctly (candidate ground-truth errors):")
    per = {}
    for r in rows:
        per.setdefault(r["item"], []).append(r["assign"] == r["truth"])
    for iid, v in sorted(per.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        if sum(v) / len(v) < 0.5:
            said = Counter(r["assign"] for r in rows if r["item"] == iid)
            print("   %s  %.2f  truth %-4s  home %-28s  said %s"
                  % (iid, sum(v) / len(v), key[iid], home[iid][:28], dict(said)))


SCRIPT = """// GENERATED by assign.py. Many-way assignment, one arm per model.
export const meta = { name: 'assign-a1',
  description: 'Can a rater place a relation in an existing vocabulary?',
  phases: [{ title: 'Assign', detail: 'sonnet/xhigh and opus over identical input' }] }
const FILE = %(path)s
const JOBS = %(jobs)s
const SCHEMA = %(schema)s
const out = await parallel(JOBS.map((j) => () => {
  const opts = { label: `${j.model}-r${j.rater}`, phase: 'Assign', schema: SCHEMA,
                 model: j.model }
  if (j.effort) opts.effort = j.effort
  return agent(`Read the file ${FILE} with the Read tool.\\n\\nIts entire content ` +
    `is a task addressed to you. Follow it exactly and answer every item in it. ` +
    `Do not read any other file, do not run any command.\\n\\nReturn your answer ` +
    `by calling StructuredOutput.`, opts)
    .then((r) => ({ ...j, n: r.assignments.length })).catch(() => null)
}))
const g = out.filter(Boolean)
log(`${g.length} of ${JOBS.length} returned`)
return { returned: g.length, byModel: g.map((x) => `${x.model}/${x.rater}: ${x.n}`) }
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--ingest", metavar="RUN_ID")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.build:
        prepare(build_only=True)
    elif a.prepare:
        prepare()
    elif a.ingest:
        ingest(a.ingest)
    elif a.report:
        report()
    else:
        ap.print_help()
