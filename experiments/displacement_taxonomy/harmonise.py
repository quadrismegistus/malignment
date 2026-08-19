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
    """[(id, name, sentence)] interleaved across frames, plus the mapping."""
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
                (rid, rel["name"], rel["sentence"],
                 {"frame": meta.get("nickname"), "pair": meta.get("pair"),
                  "aligned": k.get("aligned"), "rater": k.get("rater"), "index": i}))
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
    body = "\n\n".join("%s  %s\n      %s" % (r[0], r[1], r[2]) for r in rows)
    prompt = (tmpl.replace("{{n_relations}}", str(len(rows)))
                  .replace("{{relations}}", body))

    inp = os.path.join(HERE, "results", "harmonise_input_%s.json" % instrument)
    json.dump({"instrument": instrument, "harmoniser_version": ver,
               "n_relations": len(rows),
               "n_cells": len({(r[3]["frame"], r[3]["pair"]) for r in rows}),
               "prompt": prompt,
               "mapping": {r[0]: r[3] for r in rows}}, open(inp, "w"), indent=1)

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
          % (len(rows), len({(r[3]["frame"], r[3]["pair"]) for r in rows}), instrument))
    print("frames     %s" % ", ".join(sorted({r[3]["frame"] for r in rows})))
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
    a = ap.parse_args()
    if a.prepare:
        prepare(a.instrument)
    else:
        ap.print_help()
