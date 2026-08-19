"""Stage 2: assemble the relation corpus and generate the harmonisation workflow.

    python harmonise.py --instrument r4 --prepare     write input + workflow, do NOT run
    python harmonise.py --instrument r4 --ingest RUN   read a finished run
    python harmonise.py --instrument r4 --agree        compare the three proposals

## WHAT THIS DOES NOT DO

It does not run anything. `--prepare` writes two files and stops: the corpus with
its id mapping, and a workflow script. Launching is a separate act, deliberately,
because the harmonisation is the step that decides what the taxonomy IS and should
not happen as a side effect of a command that also builds things.

## THE ID MAPPING IS THE WHOLE DESIGN

A harmoniser sees `r0417  <name>  <sentence>` and nothing else -- no frame, no
model, no arm, no instrument. The mapping back lives in
`results/harmonise_input_<instrument>.json`, which is never shown to it. Any
grouping it produces is therefore a claim about the descriptions and not about
what we already know.

**Interleaved across frames deterministically.** Consecutive relations come from
different frames, so a harmoniser that clusters by subject matter produces groups
scattered through the list rather than contiguous blocks -- which is visible to us
afterwards and, more usefully, makes the topic reading feel wrong while reading.
Round-robin over frames sorted by name, not a shuffle, so the order reproduces
without a seed.
"""
import argparse
import collections
import hashlib
import json
import os
import sys

import run

HERE = os.path.dirname(os.path.abspath(__file__))
INSTRUMENT_MD = os.path.join(HERE, "INSTRUMENT_harmonise.md")
N_HARMONISERS = 3


def corpus(instrument):
    """[(id, name, sentence)] interleaved across frames, plus the mapping.

    **ORIENTATION MUST BE UNIFORM AND IS ASSERTED BELOW.** Column A is the base
    arm and column B the aligned arm on a `fwd` cell, and exactly the opposite on
    a `rev` one -- reversal is the same measurement read the other way, which is
    the point of running it. But the rater is never told which arm is which, so a
    relation reads `a_words -> b_words` with no direction attached, and a corpus
    mixing the two orientations asks a harmoniser to group "genitals give way to
    grooming" with "grooming gives way to genitals" as though they were one
    claim. It would either merge them, hiding a reversal, or split one construct
    in two. Neither failure announces itself.

    Normalising rev cells by swapping a_words and b_words would also work and is
    NOT done, because the swap would have to be trusted rather than checked and
    the relation SENTENCES would still read backwards.
    """
    st = run._stash()
    byframe = collections.defaultdict(list)
    for k in st.keys():
        if k.get("instrument") != instrument:
            continue
        meta = st[k].get("meta") or {}
        for i, rel in enumerate(st[k]["result"]["relations"]):
            #: The id is a hash of what identifies the relation, so re-running
            #: `--prepare` gives the same ids and two harmonisation runs can be
            #: compared. Not a counter, which would renumber if a cell were added.
            #: THE RATER IS PART OF THE IDENTITY. Without it two raters' relation
            #: 0 on one cell hash to the same id, the mapping dict keeps one, and
            #: the corpus silently ships a duplicate id -- which would also have
            #: destroyed the construct-agreement measurement, since the whole
            #: point is that the harmoniser sees both raters' relations as
            #: separate items and may or may not group them together.
            seed = "%s|%s|%s|r%s|%d" % (instrument, meta.get("nickname"),
                                        meta.get("pair"), k.get("rater"), i)
            #: 7 hex chars, not 5. At 438 relations a 5-char space (16^5) has a
            #: ~9% chance of at least one birthday collision and produced one; 7
            #: chars drops that to ~4e-4. The assert below is what actually
            #: guarantees it, since a wider id only makes collisions rarer.
            rid = "r" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:7]
            byframe[meta.get("nickname")].append(
                (rid, rel["name"], rel["sentence"], rel.get("a_words") or [],
                 rel.get("b_words") or [],
                 {"frame": meta.get("nickname"), "pair": meta.get("pair"),
                  "aligned": k.get("aligned"), "rater": k.get("rater"), "index": i}))
    ors = {k.get("orientation") for k in st.keys()
           if k.get("instrument") == instrument}
    if len(ors) > 1:
        raise SystemExit(
            "instrument %r has codings in %d orientations (%s). Column A is the "
            "base arm on fwd and the aligned arm on rev, the rater is not told "
            "which, so relations from both cannot be harmonised together. Prepare "
            "one orientation at a time." % (instrument, len(ors), ", ".join(sorted(map(str, ors)))))
    frames = sorted(byframe)
    for f in frames:
        byframe[f].sort(key=lambda x: x[0])
    out, i = [], 0
    while any(len(byframe[f]) > i for f in frames):
        for f in frames:
            if len(byframe[f]) > i:
                out.append(byframe[f][i])
        i += 1
    return out


def prepare_per_prompt(instrument, n_raters=3):
    """One shard per PROMPT: all lineages, all raters, one sentence frame.

    RH's design, and better than the interleaved whole-corpus version it replaces
    for three reasons.

    **The topic-clustering failure mode is eliminated by construction, not by
    instruction.** Interleaving was a defence: mix the frames so a topic cluster
    comes out scattered and feels wrong. If a shard IS one prompt there is only
    one topic, so clustering by it is vacuous and the agent has no option but to
    find operations. Nothing has to be trusted.

    **It forces the polarity ruling rather than leaving it to chance.** Within
    `He started stroking his`, Llama runs cock -> beard and SmolLM3 runs hand ->
    cock. Both are in the shard. The harmoniser must decide whether opposite
    directions are one construct, which is exactly the question PROTOCOL_naming.md
    declines to settle by fiat.

    **The per-prompt result is a finding, not a stage.** "Across 11 lineages on
    this prompt, here are the kinds of change and how far they agree" answers
    something never asked here: is displacement a property of the prompt or of the
    model? A whole-corpus harmonisation cannot see that question.

    n_raters harmonisers per shard, so agreement is measured within a shard as
    well as across them. At 277 shards that would be 831 agents and one per shard
    is the sane setting; cross-shard replication carries the evidence then.
    """
    import re
    rows = corpus(instrument)
    byframe = collections.defaultdict(list)
    for r in rows:
        byframe[r[5]["frame"]].append(r)
    src = open(INSTRUMENT_MD).read()
    ver = re.search(r"^# INSTRUMENT: \S+ (\S+)", src, re.M).group(1)
    tmpl = re.search(r"## PROMPT TEMPLATE\s*\n+```\n(.*?)\n```", src, re.S).group(1)
    schema = json.loads(re.search(r"## SCHEMA JSON\s*\n+```json\n(.*?)\n```", src, re.S).group(1))
    os.makedirs(os.path.join(HERE, "results", "inputs"), exist_ok=True)
    shards, mapping = [], {}
    for f in sorted(byframe):
        rs = sorted(byframe[f], key=lambda r: r[0])
        body = "\n\n".join(
            "%s  %s\n      %s\n      A: %s\n      B: %s"
            % (r[0], r[1], r[2], ", ".join(r[3]) or "(none)", ", ".join(r[4]) or "(none)")
            for r in rs)
        prompt = (tmpl.replace("{{n_relations}}", str(len(rs)))
                      .replace("{{relations}}", body))
        path = os.path.join(HERE, "results", "inputs", "harmonise_%s_%s.txt" % (instrument, f))
        open(path, "w").write(prompt)
        shards.append({"frame": f, "path": path, "n": len(rs),
                       "lineages": len({r[5]["pair"] for r in rs})})
        mapping.update({r[0]: r[5] for r in rs})
    inp = os.path.join(HERE, "results", "harmonise_input_%s_perprompt.json" % instrument)
    json.dump({"instrument": instrument, "harmoniser_version": ver, "mode": "per_prompt",
               "n_raters": n_raters, "shards": shards, "mapping": mapping},
              open(inp, "w"), indent=1)
    js = os.path.join(HERE, "workflow_harmonise_%s_perprompt.js" % instrument)
    open(js, "w").write(PP_SCRIPT % {
        "name": "harmonise-%s-perprompt" % instrument, "raters": n_raters,
        "shards": json.dumps([{"frame": s["frame"], "path": s["path"]} for s in shards], indent=2),
        "schema": json.dumps(schema, indent=2, sort_keys=True),
        "total": len(shards) * n_raters})
    gen = open(js).read()
    for s_ in shards:
        if s_["path"] not in gen:
            raise SystemExit("generated script is missing shard %r" % s_["frame"])
    print("%d shards, %d harmonisers each = %d agents" % (len(shards), n_raters, len(shards) * n_raters))
    for s_ in shards:
        print("   %-12s %3d relations from %2d lineages  %s"
              % (s_["frame"], s_["n"], s_["lineages"], os.path.basename(s_["path"])))
    print("mapping    %s" % inp)
    print("workflow   %s" % js)
    print("\nNOT RUN.")


PP_SCRIPT = """// GENERATED BY harmonise.py --per-prompt. Do not hand-edit.
// %(total)d agents: %(raters)d independent harmonisers per prompt shard.
export const meta = {
  name: '%(name)s',
  description: 'Per-prompt controlled vocabulary from Stage 1 relations',
  phases: [{ title: 'Harmonise', detail: 'one shard per prompt, independent raters' }],
}

const SHARDS = %(shards)s
const SCHEMA = %(schema)s

// Every relation in a shard comes from ONE sentence frame, so clustering by
// subject matter is vacuous and the agent must find operations. Each harmoniser
// sees only its own shard and never another's answer.
const out = await parallel(SHARDS.flatMap((s) =>
  Array.from({ length: %(raters)d }, (_, i) => () =>
    agent(
      `Read the file ${s.path} with the Read tool.\n\n` +
      `Its entire content is a task addressed to you. Follow it exactly and answer ` +
      `every numbered question in it. Do not read any other file, do not run any ` +
      `command, and do not look for context beyond what that file contains.\n\n` +
      `Return your answer by calling StructuredOutput.`,
      { label: `${s.frame}-h${i + 1}`, phase: 'Harmonise', schema: SCHEMA }
    ).then((r) => ({ frame: s.frame, harmoniser: i + 1, result: r })).catch(() => null)
  )
))

const good = out.filter(Boolean).filter((x) => x && x.result)
log(`${good.length} of %(total)d returned`)
return {
  returned: good.length,
  per_shard: good.map((x) => `${x.frame} h${x.harmoniser}: ` +
    `${x.result.constructs.length} constructs, ${x.result.unassigned.ids.length} unassigned, ${x.result.confidence}`),
  names: good.map((x) => `${x.frame} h${x.harmoniser}: ` +
    x.result.constructs.map((c) => c.name).join(' | ')),
}
"""


def prepare(instrument):
    rows = corpus(instrument)
    if not rows:
        raise SystemExit("no codings under instrument %r in the stash" % instrument)
    #: IDS MUST BE UNIQUE OR THE MAPPING SILENTLY LOSES RELATIONS. A duplicate id
    #: means the corpus ships two different relations under one label, the mapping
    #: dict keeps whichever was written last, and every grouping the harmoniser
    #: makes on that id is unattributable afterwards. Caught this way: 438
    #: relations resolved to 231 distinct ids because the seed omitted the rater.
    ids = [r[0] for r in rows]
    if len(set(ids)) != len(ids):
        dup = [i for i in set(ids) if ids.count(i) > 1]
        raise SystemExit("%d duplicate relation id(s) out of %d: %s -- the corpus "
                         "cannot ship" % (len(dup), len(ids), dup[:5]))
    src = open(INSTRUMENT_MD).read()
    import re
    ver = re.search(r"^# INSTRUMENT: \S+ (\S+)", src, re.M).group(1)
    tmpl = re.search(r"## PROMPT TEMPLATE\s*\n+```\n(.*?)\n```", src, re.S).group(1)
    schema = json.loads(re.search(r"## SCHEMA JSON\s*\n+```json\n(.*?)\n```", src, re.S).group(1))
    #: THE WORDS GO IN, THE PROMPT DOES NOT. RH, 2026-08-19: the sentences are
    #: sometimes ambiguous without examples of words. They are -- and raters
    #: already quote them into the sentences much of the time, so printing
    #: a_words/b_words costs about 78 chars per relation and almost nothing in
    #: leakage. The PROMPT is a different matter: the words are the evidence the
    #: relation is about, the prompt is the topic, and handing over the topic
    #: makes cluster-by-frame trivially available, which is the documented
    #: failure mode. A harmoniser can tell genitals-to-grooming from
    #: obligation-to-threat from the words alone.
    body = "\n\n".join(
        "%s  %s\n      %s\n      A: %s\n      B: %s"
        % (r[0], r[1], r[2], ", ".join(r[3]) or "(none)", ", ".join(r[4]) or "(none)")
        for r in rows)
    prompt = (tmpl.replace("{{n_relations}}", str(len(rows)))
                  .replace("{{relations}}", body))

    inp = os.path.join(HERE, "results", "harmonise_input_%s.json" % instrument)
    json.dump({"instrument": instrument, "harmoniser_version": ver,
               "n_relations": len(rows),
               "n_cells": len({(r[5]["frame"], r[5]["pair"]) for r in rows}),
               "prompt": prompt,
               "mapping": {r[0]: r[5] for r in rows}}, open(inp, "w"), indent=1)

    txt = os.path.join(HERE, "results", "inputs", "harmonise_%s.txt" % instrument)
    os.makedirs(os.path.dirname(txt), exist_ok=True)
    open(txt, "w").write(prompt)

    js = os.path.join(HERE, "workflow_harmonise_%s.js" % instrument)
    open(js, "w").write(SCRIPT % {
        "name": "harmonise-%s" % instrument, "n": N_HARMONISERS,
        "path": txt, "schema": json.dumps(schema, indent=2, sort_keys=True),
        "src": instrument, "nrel": len(rows)})
    #: verify the generator's OUTPUT, not that it parses
    gen = open(js).read()
    for probe in (txt, '"constructs"', '"topic_audit"'):
        if probe not in gen:
            raise SystemExit("generated script is missing %r" % probe)
    print("corpus     %d relations from %d cells, instrument %s"
          % (len(rows), len({(r[5]["frame"], r[5]["pair"]) for r in rows}), instrument))
    print("frames     %s" % ", ".join(sorted({r[5]["frame"] for r in rows})))
    print("prompt     %d chars  -> %s" % (len(prompt), txt))
    print("mapping    %s   (the harmoniser never sees this)" % inp)
    print("workflow   %s   %d independent harmonisers" % (js, N_HARMONISERS))
    print("\nNOT RUN. Launch with Workflow({scriptPath: %r}) when you want it." % js)


SCRIPT = """// GENERATED BY harmonise.py --prepare. Do not hand-edit.
// %(n)d independent harmonisers over %(nrel)d relations from instrument %(src)s.
export const meta = {
  name: '%(name)s',
  description: 'Propose a controlled vocabulary from Stage 1 relation descriptions',
  phases: [{ title: 'Harmonise', detail: 'independent proposals, no shared context' }],
}

const FILE = '%(path)s'
const SCHEMA = %(schema)s

// Each harmoniser reads the same file and never sees the others. Agreement
// between their proposals is the measurement; a single clustering is a preference.
const out = await parallel(Array.from({ length: %(n)d }, (_, i) => () =>
  agent(
    `Read the file ${FILE} with the Read tool.\\n\\n` +
    `Its entire content is a task addressed to you. Follow it exactly and answer ` +
    `every numbered question in it. Do not read any other file, do not run any ` +
    `command, and do not look for context beyond what that file contains.\\n\\n` +
    `Return your answer by calling StructuredOutput.`,
    { label: `harmoniser-${i + 1}`, phase: 'Harmonise', schema: SCHEMA }
  ).then((r) => ({ harmoniser: i + 1, result: r })).catch(() => null)
))

const good = out.filter(Boolean).filter((x) => x && x.result)
log(`${good.length} of %(n)d harmonisers returned`)
return {
  returned: good.length,
  constructs: good.map((x) => `h${x.harmoniser}: ${x.result.constructs.length} constructs, ` +
    `${x.result.unassigned.ids.length} unassigned, ${x.result.confidence}`),
  names: good.map((x) => `h${x.harmoniser}: ` + x.result.constructs.map((c) => c.name).join(' | ')),
}
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--instrument", default="r4")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--per-prompt", action="store_true", dest="per_prompt",
                    help="one shard per prompt (RH's design); implies --prepare")
    ap.add_argument("--raters", type=int, default=3)
    a = ap.parse_args()
    if a.per_prompt:
        prepare_per_prompt(a.instrument, a.raters)
    elif a.prepare:
        prepare(a.instrument)
    else:
        ap.print_help()
