"""Stage 2 on one prompt at a time, over the batched corpus, WITH the results saved.

    python harmonise_prompt.py --prepare "He was written up..."   build shard + workflow
    python harmonise_prompt.py --ingest RUN_ID                     save the proposals

## WHY PER PROMPT

RH's design. Every relation in a shard comes from one sentence, so clustering by
subject matter is vacuous and a harmoniser has no option but to find operations.
The topic-clustering failure mode is eliminated by construction rather than by
instruction, and the result is a finding in its own right: across N lineages on
THIS sentence, here are the kinds of change and how far three readers agree.

## WHAT IS FILTERED OUT, AND WHY IT IS FILTERED HERE

Only DEFENDED, TWO-SIDED relations reach a harmoniser:

    dropped: confidence == low          the rater said it would not defend it
    dropped: an empty a_words or b_words  a relation names a group on each side;
                                          one side empty is a list

On the first institutional prompt that took 24 relations to 14. Precision over
recall (RH): an over-read relation becomes a construct, gets a name, gets applied
to further cells and enters every count of how many lineages perform it. Recall
errors leave gaps; precision errors propagate.

## THE RESULTS ARE STORED, WHICH THE FIRST RUN DID NOT DO

A harmonisation is an artifact, not a print-out. The first one-prompt run existed
only in its workflow journal -- durable, but findable only by someone who could
still name the run id. Proposals now go to their own stash keyed by
(stage, harmoniser version, prompt, harmoniser index), so three proposals on one
prompt are three addressable records and a re-run replaces rather than duplicates.
"""
import argparse
import hashlib
import json
import os
import re
import sys

import run

HERE = os.path.dirname(os.path.abspath(__file__))
INSTRUMENT = os.path.join(HERE, "INSTRUMENT_harmonise.md")
STASH = os.path.join(HERE, "results", "harmonise_stash")
N_HARMONISERS = 3
#: Names the admission rule in the key, so a later unfiltered harmonisation of
#: the same prompt and the same pairs is a separate record rather than a
#: replacement. Change the rule, change this string.
FILTER = "defended_two_sided"


def _stash():
    from hashstash import HashStash
    os.makedirs(STASH, exist_ok=True)
    st = HashStash(root_dir=STASH, engine="jsonl", flat=True)
    got = os.path.basename(getattr(st, "path_dirname", "") or "")
    if "jsonl" not in got:
        print("harmonise stash resolved to %r, expected jsonl" % got, file=sys.stderr)
    return st


def shard(prompt_prefix):
    """Defended two-sided relations for one prompt, with opaque ids."""
    st = run._stash()
    rows = []
    for k in st.keys():
        m = (st[k].get("meta") or {})
        if m.get("batch") and m["frame_prompt"].startswith(prompt_prefix):
            rows.append((m, st[k]["result"]))
    if not rows:
        raise SystemExit("no batched codings for a prompt starting %r" % prompt_prefix)
    prompt = rows[0][0]["frame_prompt"]
    items, mapping, n_all = [], {}, 0
    for m, r in rows:
        for i, x in enumerate(r["relations"]):
            n_all += 1
            if not (x.get("a_words") and x.get("b_words")):
                continue
            if x.get("confidence") == "low":
                continue
            rid = "r" + hashlib.sha256(
                ("%s|%s|%d" % (m["pair"], prompt, i)).encode()).hexdigest()[:7]
            items.append((rid, x))
            mapping[rid] = {"pair": m["pair"], "index": i,
                            "confidence": x.get("confidence"), "name": x["name"]}
    items.sort(key=lambda t: t[0])
    if len(mapping) != len(items):
        raise SystemExit("duplicate relation id in shard for %r" % prompt)
    #: WHICH MODELS WERE CONSIDERED IS PART OF THE SHARD'S IDENTITY (RH). A
    #: construct set is a function of the lineages that fed it: harmonising this
    #: prompt again after pass 2 adds pairs is a DIFFERENT reading of a DIFFERENT
    #: population, and if both are stored under the prompt alone the second
    #: silently replaces the first with nothing recording that the input moved.
    pairs = sorted(m["pair"] for m, _ in rows)
    if len(set(pairs)) != len(pairs):
        raise SystemExit("a pair coded this prompt twice; the shard would double-weight it")
    return prompt, items, mapping, pairs, n_all


def prepare(prefix):
    prompt, items, mapping, pairs, n_all = shard(prefix)
    n_cells = len(pairs)
    src = open(INSTRUMENT).read()
    ver = re.search(r"^# INSTRUMENT: \S+ (\S+)", src, re.M).group(1)
    tmpl = re.search(r"## PROMPT TEMPLATE\s*\n+```\n(.*?)\n```", src, re.S).group(1)
    schema = json.loads(re.search(r"## SCHEMA JSON\b.*?\n```json\n(.*?)\n```", src, re.S).group(1))
    body = "\n\n".join("%s  %s\n      %s\n      A: %s\n      B: %s"
                       % (i, x["name"], x["sentence"],
                          ", ".join(x["a_words"]), ", ".join(x["b_words"]))
                       for i, x in items)
    text = tmpl.replace("{{n_relations}}", str(len(items))).replace("{{relations}}", body)
    slug = re.sub(r"[^a-z0-9]+", "_", prompt.lower())[:40].strip("_")
    path = os.path.join(HERE, "results", "inputs", "harm_%s.txt" % slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)
    state = {"prompt": prompt, "slug": slug, "version": ver, "n_cells": n_cells,
             "pairs": pairs, "pairs_sha": hashlib.sha256("\n".join(pairs).encode()).hexdigest()[:12],
             "filter": FILTER, "n_relations_all": n_all, "n_relations_kept": len(items),
             "path": path, "mapping": mapping}
    json.dump(state, open(os.path.join(HERE, "results", "harm_%s.json" % slug), "w"), indent=1)
    js = SCRIPT % {"n": N_HARMONISERS, "slug": slug, "path": json.dumps(os.path.abspath(path)),
                   "schema": json.dumps(schema, indent=2, sort_keys=True),
                   "prompt": json.dumps(prompt[:60])}
    out = os.path.join(HERE, "workflow_harm_%s.js" % slug)
    open(out, "w").write(js)
    for probe in (os.path.abspath(path), '"constructs"'):
        if probe not in js:
            raise SystemExit("generated script missing %r" % probe)
    print("%r\n  %d lineages, %d relations, %d defended two-sided (%d dropped)"
          % (prompt, n_cells, n_all, len(items), n_all - len(items)))
    print("  shard    %s" % path)
    print("  workflow %s\n\nNOT RUN." % out)


def ingest(run_id, slug):
    import glob
    state = json.load(open(os.path.join(HERE, "results", "harm_%s.json" % slug)))
    base = os.path.expanduser("~/.claude/projects")
    hits = glob.glob(os.path.join(base, "*", "*", "subagents", "workflows", run_id))
    if not hits:
        raise SystemExit("no transcript dir for %r" % run_id)
    res = []
    for l in open(os.path.join(hits[0], "journal.jsonl")):
        d = json.loads(l)
        if d.get("type") == "result":
            res.append(d["result"])
    st = _stash()
    for i, r in enumerate(res, 1):
        #: every member id must be one the shard issued, or the proposal groups
        #: something we cannot map back and the record is unusable
        bad = [m for c in r["constructs"] for m in c["members"] if m not in state["mapping"]]
        if bad:
            raise SystemExit("harmoniser %d names %d id(s) the shard never issued: %s"
                             % (i, len(bad), bad[:3]))
        key = {"stage": "harmonise", "version": state["version"],
               "frame_prompt": state["prompt"], "pairs_sha": state["pairs_sha"],
               "filter": state["filter"], "harmoniser": i}
        #: `pairs` rides in the value so the sha in the key is resolvable without
        #: a join against a state file that may have been re-prepared since.
        st[key] = {"result": r, "run_id": run_id, "pairs": state["pairs"],
                   "n_relations": state["n_relations_kept"],
                   "n_relations_all": state["n_relations_all"],
                   "n_cells": state["n_cells"], "mapping": state["mapping"]}
    state.setdefault("runs", []).append(run_id)
    json.dump(state, open(os.path.join(HERE, "results", "harm_%s.json" % slug), "w"), indent=1)
    print("stored %d proposals for %r" % (len(res), state["prompt"][:56]))
    for i, r in enumerate(res, 1):
        print("  h%d: %d constructs, %d unassigned, %s"
              % (i, len(r["constructs"]), len(r["unassigned"]["ids"]), r["confidence"]))


def report(prefix):
    """Agreement between harmonisers on one prompt, read back from the stash.

    Membership is compared on RELATION IDS, never on names. Three harmonisers
    invent three vocabularies for the same operation and a name match would count
    `Generic verb to situated verb` against `Light verb, bound verb` as a
    disagreement when the members are identical, which they were.
    """
    st = _stash()
    recs = []
    for k in st.keys():
        if k.get("stage") == "harmonise" and k["frame_prompt"].startswith(prefix):
            recs.append((k, st[k]))
    if not recs:
        raise SystemExit("nothing harmonised for a prompt starting %r" % prefix)
    shas = {k["pairs_sha"] for k, _ in recs}
    if len(shas) > 1:
        #: Two populations under one prompt is exactly what the key exists to keep
        #: apart; pooling them here would undo it at the reading end.
        raise SystemExit("%d populations for this prompt: %s -- name one with "
                         "--pairs-sha" % (len(shas), sorted(shas)))
    recs.sort(key=lambda t: t[0]["harmoniser"])
    v = recs[0][1]
    print("%r\n  %d lineages, %d of %d relations admitted (%s), pairs %s\n"
          % (recs[0][0]["frame_prompt"], v["n_cells"], v["n_relations"],
             v["n_relations_all"], recs[0][0]["filter"], recs[0][0]["pairs_sha"]))
    sets = []
    for k, val in recs:
        cs = [(c["name"], frozenset(c["members"])) for c in val["result"]["constructs"]]
        sets.append(cs)
        print("h%d (%s)" % (k["harmoniser"], val["result"]["confidence"]))
        for n, m in sorted(cs, key=lambda t: -len(t[1])):
            print("   %2d  %s" % (len(m), n))
        print()
    for a in range(len(sets)):
        for b in range(a + 1, len(sets)):
            js = []
            for _, m in sets[a]:
                best = max((len(m & n) / len(m | n) for _, n in sets[b]), default=0.0)
                js.append(best)
            js.sort()
            mid = js[len(js) // 2] if len(js) % 2 else (js[len(js) // 2 - 1] + js[len(js) // 2]) / 2
            print("h%d vs h%d   median J %.2f   %d of %d matched >= 0.5"
                  % (recs[a][0]["harmoniser"], recs[b][0]["harmoniser"], mid,
                     sum(1 for x in js if x >= 0.5), len(js)))


SCRIPT = """// GENERATED by harmonise_prompt.py. %(n)d harmonisers on one prompt.
export const meta = { name: 'harm-%(slug)s',
  description: 'Constructs for %(prompt)s',
  phases: [{ title: 'Harmonise', detail: 'independent, same shard' }] }
const FILE = %(path)s
const SCHEMA = %(schema)s
const out = await parallel([1, 2, 3].map((i) => () =>
  agent(`Read the file ${FILE} with the Read tool.\\n\\nIts entire content is a task ` +
    `addressed to you. Follow it exactly and answer every numbered question in it. ` +
    `Do not read any other file, do not run any command.\\n\\nReturn your answer by ` +
    `calling StructuredOutput.`,
    { label: `h${i}`, phase: 'Harmonise', schema: SCHEMA })
   .then((r) => ({ h: i, result: r })).catch(() => null)))
const g = out.filter(Boolean).filter((x) => x && x.result)
log(`${g.length} of %(n)d`)
return { returned: g.length,
  names: g.map((x) => `h${x.h}: ` + x.result.constructs.map((c) => c.name).join(' | ')) }
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prepare", metavar="PROMPT_PREFIX")
    ap.add_argument("--ingest", metavar="RUN_ID")
    ap.add_argument("--report", metavar="PROMPT_PREFIX")
    ap.add_argument("--slug")
    a = ap.parse_args()
    if a.prepare:
        prepare(a.prepare)
    elif a.ingest:
        if not a.slug:
            raise SystemExit("--ingest needs --slug")
        ingest(a.ingest, a.slug)
    elif a.report:
        report(a.report)
    else:
        ap.print_help()
