"""Within-domain vocabulary accretion, one prompt at a time. RH's triage.

    python accrete.py --build      what would run, nothing spent
    python accrete.py --prepare
    python accrete.py --ingest RUN_ID
    python accrete.py --report

## The shape, and why it beats what it replaces

RH's design: take two prompts from one domain, ask which of their constructs are
the same, collapse those, keep the rest, then fold in the third prompt, and so on
until the domain has a set of meta-categories. Repeat per domain. Cross-connect
domains only at the end.

This is better than the cross-prompt assignment design it replaces for one
specific reason. That design put a MIXED-DOMAIN vocabulary in front of the rater
from the first step, which is exactly where the topic shortcut is strongest: a
sexual item can be filed under a sexual entry without the operation being
considered. Accreting within a domain removes the shortcut by removing the
variance -- when everything concerns the same subject matter, subject matter
carries no information. Domains meet at the end, when each has perhaps ten
meta-categories and the comparison is a hundred pairs instead of thirty thousand.

It is also cheaper: one call per prompt per domain, so the whole pilot is six
agents rather than the thousands all-pairs merging would need.

## Path dependence, which is real and not fixed here

Greedy accretion cannot undo a merge. The vocabulary from prompts in one order
is not guaranteed to be the vocabulary from another, because step two's decision
is frozen before step seven's evidence arrives. The check is to re-run one
domain in a different order and compare; it is not part of the pilot and is
recorded as outstanding rather than waved away.

## Generation is separated from verification

One rater per step. Adding voters here would make the accretion more reliable in
a way that is unmeasured, whereas `assign.py` is now a calibrated instrument
(sonnet/xhigh: 0.95 on items whose home is present, 1.00 on refusing items whose
home is absent, against a chance of 0.11). So the merges this produces get
AUDITED with that instrument afterwards, rather than defended by a quorum here.
"""
import argparse
import json
import os
import re
import sys

import discriminate as D
import harmonise_prompt as HP
import run as R

HERE = os.path.dirname(os.path.abspath(__file__))
INSTRUMENT = os.path.join(HERE, "INSTRUMENT_accrete.md")
STATE = os.path.join(HERE, "results", "accrete_state.json")
MODEL, EFFORT = "sonnet", "xhigh"
MAX_EXEMPLARS = 3


def domains():
    """{domain: [prompt, ...]} for every prompt harmonised on MODEL, seeded order."""
    st = R._stash()
    dom = {}
    for k in st.keys():
        m = (st[k].get("meta") or {})
        if m.get("batch"):
            dom[m["frame_prompt"]] = m["domain"]
    have = {}
    for k in HP._stash().keys():
        #: Only prompts harmonised on THIS model. Mixing models inside one
        #: accretion would make the vocabulary a function of which model
        #: happened to harmonise which prompt.
        if k.get("model") == MODEL:
            have.setdefault(dom.get(k["frame_prompt"], "?"), set()).add(k["frame_prompt"])
    out = {}
    for d, ps in sorted(have.items()):
        out[d] = sorted(ps, key=lambda p: D._rng("accrete-order", d).random() if False else p)
    return out


def constructs_for(prompt):
    """Core constructs for one prompt under MODEL, with the harmonisers' own prose.

    CARRY `definition` AND `nearest`, NOT JUST THE NAME. Harmonisation already
    writes both, and the first accretion run passed neither: the merge step saw a
    name and some word lists and was asked to judge sameness with the reasoning
    withheld. It refused 36 merges of 40.

    `definition` is a subject-independent statement of the operation -- "One pole
    names verbs of ending one's involvement and withdrawing from a situation
    altogether; the other names verbs of remaining in place and directly voicing
    a grievance or demand" -- which is exactly the `basis` a cross-prompt
    comparison needs, and it was assumed not to exist.

    `nearest` is worth more still: it names the construct this one is CLOSEST to
    and says why it is not that one. A stated boundary is strictly better
    evidence than a boundary the reader has to reconstruct, and it is the only
    field in the pipeline that records a distinction someone actively considered
    and rejected.

    Both come from harmoniser 1, whose partition defines the cores. The other two
    harmonisers wrote their own and they are not merged: averaging prose produces
    prose nobody wrote, and the core already encodes where the three agreed.
    """
    st = HP._stash()
    recs = {k["harmoniser"]: st[k] for k in st.keys()
            if k["frame_prompt"] == prompt and k.get("model") == MODEL}
    if len(recs) != 3:
        return None, None
    _, items, _, _, _ = HP.shard(prompt[:26])
    rel = dict(items)
    S = {i: [(c["name"], frozenset(c["members"])) for c in recs[i]["result"]["constructs"]]
         for i in recs}
    prose = {c["name"]: (c.get("definition"), c.get("nearest"))
             for c in recs[1]["result"]["constructs"]}
    keep = {}
    for name, m in S[1]:
        core, ok = set(m), True
        for o in (2, 3):
            j, best = max(((len(m & q) / len(m | q), q) for _, q in S[o]), key=lambda t: t[0])
            if j < 0.5:
                ok = False
            core &= best
        if ok and core:
            keep[name] = (sorted(core), prose.get(name, (None, None)))
    return keep, rel


def plan():
    steps, skipped = [], []
    for d, prompts in domains().items():
        rows = []
        for p in prompts:
            cons, rel = constructs_for(p)
            if not cons:
                skipped.append((d, p))
                continue
            rows.append({"prompt": p, "constructs": [
                {"cid": "c%02d" % i, "name": n, "definition": pr[0], "nearest": pr[1],
                 "ex": [{"a": rel[r]["a_words"], "b": rel[r]["b_words"],
                         "s": rel[r]["sentence"]} for r in ids[:MAX_EXEMPLARS]],
                 "n_members": len(ids)}
                for i, (n, (ids, pr)) in enumerate(sorted(cons.items()))]})
        if len(rows) >= 2:
            steps.append({"domain": d, "prompts": rows})
    return steps, skipped


def prepare(build_only=False):
    steps, skipped = plan()
    if not steps:
        raise SystemExit("no domain has two prompts harmonised on %s yet" % MODEL)
    n_agents = sum(len(s["prompts"]) - 1 for s in steps)
    for s in steps:
        print("%-14s %d prompts, %d accretion step(s)" % (s["domain"], len(s["prompts"]),
                                                          len(s["prompts"]) - 1))
        for r in s["prompts"]:
            print("    %-52s %2d constructs" % (r["prompt"][:52], len(r["constructs"])))
    if skipped:
        print("\nnot harmonised on %s yet, skipped: %s"
              % (MODEL, [p[:34] for _, p in skipped]))
    print("\n%d agents, %s/%s, one rater per step" % (n_agents, MODEL, EFFORT))
    if build_only:
        return
    src = open(INSTRUMENT).read()
    tmpl = re.search(r"## PROMPT TEMPLATE\s*\n+```\n(.*?)\n```", src, re.S).group(1)
    schema = json.loads(re.search(r"## SCHEMA JSON\b.*?\n```json\n(.*?)\n```", src, re.S).group(1))
    json.dump({"steps": steps, "model": MODEL, "effort": EFFORT}, open(STATE, "w"), indent=1)
    js = SCRIPT % {"steps": json.dumps(steps), "schema": json.dumps(schema, indent=2,
                                                                   sort_keys=True),
                   "template": json.dumps(tmpl), "model": json.dumps(MODEL),
                   "effort": json.dumps(EFFORT)}
    out = os.path.join(HERE, "workflow_accrete.js")
    open(out, "w").write(js)
    for probe in ('"decisions"', MODEL, EFFORT, "{{vocab_section}}"):
        if probe not in js:
            raise SystemExit("generated script missing %r" % probe)
    print("  workflow %s\n\nNOT RUN." % out)


def ingest(run_id, output=None):
    import glob
    base = os.path.expanduser("~/.claude/projects")
    hits = glob.glob(os.path.join(base, "*", "*", "subagents", "workflows", run_id))
    if not hits:
        raise SystemExit("no transcript dir for %r" % run_id)
    #: THE FOLD IS NOT IN THE JOURNAL. Accretion is sequential, so the finished
    #: vocabulary exists only as the script's fold over the steps; the journal
    #: holds each agent's `decisions` array and nothing that reconstructs it.
    #: The workflow's RETURN VALUE is the artifact, and that lands in the task
    #: output file rather than the journal. Same lesson as the discriminate
    #: ingest, one level up: the journal records agents, not the orchestration.
    tail = None
    #: The task output directory is NOT under the workflow transcript root; it
    #: lives in the harness scratch tree, which is environment-specific. So the
    #: path is given rather than inferred, and an inferred fallback is offered
    #: only as a convenience.
    cands = [output] if output else sorted(
        glob.glob(os.path.join(os.path.dirname(hits[0]), "..", "..", "tasks", "*.output")),
        key=os.path.getmtime, reverse=True)
    for c in cands:
        try:
            d = json.load(open(c))
        except (ValueError, IOError):
            continue
        r = d.get("result")
        if isinstance(r, dict) and "vocabularies" in r:
            tail = r
            break
    if tail is None:
        raise SystemExit("no workflow return holding `vocabularies` found under %s; "
                         "pass the task output path explicitly" % tasks)
    json.dump(tail, open(os.path.join(HERE, "results", "accrete_result.json"), "w"), indent=1)
    print("stored vocabularies for %d domain(s)" % len(tail["vocabularies"]))


def report():
    p = os.path.join(HERE, "results", "accrete_result.json")
    if not os.path.exists(p):
        raise SystemExit("nothing ingested")
    v = json.load(open(p))
    for dom, entries in sorted(v["vocabularies"].items()):
        print("\n%s -- %d meta-categories from %d prompts"
              % (dom.upper(), len(entries), v["counts"].get(dom, 0)))
        for e in sorted(entries, key=lambda e: -len(e["sources"])):
            print("   %-38s %d prompt(s), %d construct(s)"
                  % (e["name"][:38], len({s.split("|")[0] for s in e["sources"]}),
                     len(e["sources"])))
    print("\nmerges refused (kept separate): %d   merges made: %d"
          % (v["counts"].get("new", 0), v["counts"].get("merged", 0)))
    print("\nSATURATION CURVE -- this, not the harmonisation run, is where it is measured.")
    print("A domain whose `fresh` column falls toward zero is saturating.")
    for dom, rows in sorted(v.get("curves", {}).items()):
        print("\n  %s" % dom)
        print("    step  cand  merged  fresh  vocab  prompt")
        for r in rows:
            print("    %4d  %4d  %6d  %5d  %5d  %s"
                  % (r["step"], r["candidates"], r["merged"], r["fresh"], r["vocab"],
                     r["prompt"][:40]))
    for l in v.get("logs", []):
        print("  NOTE %s" % l)


SCRIPT = """// GENERATED by accrete.py. Sequential within a domain, parallel across domains.
export const meta = { name: 'accrete',
  description: 'Within-domain vocabulary accretion, one prompt at a time',
  phases: [{ title: 'Accrete', detail: 'sequential steps per domain' }] }
const STEPS = %(steps)s
const SCHEMA = %(schema)s
const TMPL = %(template)s
const L = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

function fmtEx(e) {
  return `     A: ${e.a.join(', ')}\\n     B: ${e.b.join(', ')}\\n     ${e.s}`
}
function fmtVocab(v) {
  if (!v.length) return 'The vocabulary is empty; every candidate below starts it.'
  return 'CURRENT VOCABULARY:\\n\\n' + v.map((en, i) => {
    const src = [...new Set(en.sources.map((x) => x.split('|')[0]))]
    // THE OPERATION STATEMENT LEADS. It is the only part of an entry written to
    // survive a change of subject matter, and the first run showed the name and
    // the word lists and nothing else -- discarding the one field built for this
    // comparison. Words come last and are labelled as illustration, because
    // across sentences they are the variable and the operation is the invariant.
    let out = `ENTRY ${L[i]}  ${en.name}\\n`
    out += `  operation: ${en.basis}\\n`
    // The harmoniser's `nearest`: which construct this one was judged closest to
    // and why it is NOT that one. A boundary somebody actively considered and
    // rejected is stronger evidence than one the reader has to reconstruct, and
    // it is the only record in the pipeline of a distinction being tested.
    if (en.nearest) out += `  distinguished from: ${en.nearest}\\n`
    if (en.names.length > 1) out += `  also named: ${en.names.slice(1).join('; ')}\\n`
    // THE FRAME IS SHOWN IN FULL, NEVER ABBREVIATED. It was first added
    // truncated at 46 characters, which cut before the completion slot: the
    // reader could not tell what the example words completed, and the line still
    // read as though it had told them. The correction for a clip is the whole
    // string, not the deletion of it -- an entry resting on one exemplar is
    // underdetermined without its frame, and seeing that two entries come from
    // DIFFERENT frames is what makes "the words will not match" concrete rather
    // than an assertion in the instructions. Hiding the subject matter is not
    // what the validated instruments did: discrimination held it CONSTANT.
    out += `  seen in ${src.length} sentence(s):\\n`
    out += src.map((x) => `    "${x}"`).join('\\n') + '\\n'
    out += `  example words (illustration; they will NOT match across sentences):\\n`
    return out + en.ex.map(fmtEx).join('\\n\\n')
  }).join('\\n\\n')
}
function fmtCands(cs, prompt) {
  // Every candidate in a step comes from ONE sentence, so the frame is stated
  // once at the head rather than repeated on each candidate.
  return `All of the following describe completions of this sentence:\\n\\n    "${prompt}"\\n\\n` +
    cs.map((c) => `CANDIDATE ${c.cid}  ${c.name}\\n` +
      `  operation: ${c.definition}\\n` +
      (c.nearest ? `  distinguished from: ${c.nearest}\\n` : '') +
      `  example words (illustration; they will NOT match across sentences):\\n` +
      c.ex.map(fmtEx).join('\\n\\n')).join('\\n\\n')
}

const vocabularies = {}
const counts = { merged: 0, new: 0 }
const results = await parallel(STEPS.map((S) => async () => {
  // Seed the vocabulary with the FIRST prompt's constructs; no judgement needed.
  // Seed entries have no `basis`: nothing has judged them yet. They carry their
  // constituent name and source, and the field is left explicitly unstated rather
  // than back-filled from the name, which would fabricate an operation statement
  // no reader wrote.
  // Seed entries inherit the HARMONISER'S OWN prose. They are not unjudged:
  // three harmonisers grouped these relations and one wrote a definition and a
  // boundary statement for each. Treating them as blank was a bug, not a fact
  // about the data, and it made the first step of every domain compare names
  // and word lists with the reasoning withheld.
  let vocab = S.prompts[0].constructs.map((c) => ({
    name: c.name, ex: c.ex, basis: c.definition, nearest: c.nearest,
    names: [c.name], sources: [`${S.prompts[0].prompt}|${c.name}`] }))
  const log_ = []
  // THE SATURATION CURVE IS THIS ARRAY. Whether successive prompts stop adding
  // new constructs is the merge judgement, so it can only be counted where the
  // merge is made -- not by the file that harmonises prompts. One row per step:
  // candidates offered, how many merged into an existing entry, how many stayed
  // new, and the vocabulary size after.
  const curve = [{ step: 0, prompt: S.prompts[0].prompt, candidates: vocab.length,
                   merged: 0, fresh: vocab.length, vocab: vocab.length }]
  for (let i = 1; i < S.prompts.length; i++) {
    const P = S.prompts[i]
    const text = TMPL.replace('{{vocab_section}}', fmtVocab(vocab))
                     .replace('{{candidates}}', fmtCands(P.constructs, P.prompt))
    const r = await agent(text, { label: `${S.domain}-step${i}`, phase: 'Accrete',
                                  schema: SCHEMA, model: %(model)s, effort: %(effort)s })
      .catch(() => null)
    if (!r) { log_.push(`${S.domain} step ${i}: agent failed`); continue }
    let sMerged = 0, sFresh = 0
    for (const d of r.decisions) {
      const c = P.constructs.find((x) => x.cid === d.candidate)
      if (!c) { log_.push(`unknown candidate ${d.candidate}`); continue }
      const idx = L.indexOf(String(d.merge).trim().toUpperCase())
      if (d.merge !== 'new' && idx >= 0 && idx < vocab.length) {
        vocab[idx].sources.push(`${P.prompt}|${c.name}`)
        vocab[idx].name = d.name || vocab[idx].name
        // The merging reader's basis supersedes: it was written knowing BOTH
        // members, so it is the more general statement of the two.
        if (d.basis) vocab[idx].basis = d.basis
        // The absorbed construct's boundary statement referred to a distinction
        // from ANOTHER construct; once merged it may no longer hold, so it is
        // dropped rather than carried, and the merging reader's basis stands.
        vocab[idx].nearest = null
        if (!vocab[idx].names.includes(c.name)) vocab[idx].names.push(c.name)
        counts.merged++; sMerged++
      } else {
        // A merge naming an entry letter that does not exist is recorded as new
        // rather than dropped, but it is a malformed answer and is logged: a
        // silent fallback would report a refusal the rater never made.
        if (d.merge !== 'new' && !(idx >= 0 && idx < vocab.length))
          log_.push(`${S.domain} step ${i}: ${d.candidate} named entry ${d.merge}, out of range`)
        vocab.push({ name: d.name || c.name, ex: c.ex,
                     basis: d.basis || c.definition, nearest: c.nearest,
                     names: [c.name], sources: [`${P.prompt}|${c.name}`] })
        counts.new++; sFresh++
      }
    }
    curve.push({ step: i, prompt: P.prompt, candidates: r.decisions.length,
                 merged: sMerged, fresh: sFresh, vocab: vocab.length })
    log(`${S.domain} step ${i}: ${r.decisions.length} candidates, ${sMerged} merged, ` +
        `${sFresh} new, vocab ${vocab.length}`)
  }
  return { domain: S.domain, vocab, n_prompts: S.prompts.length, curve, log: log_ }
}))
const curves = {}, logs = []
for (const r of results.filter(Boolean)) {
  vocabularies[r.domain] = r.vocab
  counts[r.domain] = r.n_prompts
  curves[r.domain] = r.curve
  logs.push(...r.log)
}
return { vocabularies, counts, curves, logs,
  summary: Object.entries(vocabularies).map(([d, v]) =>
    `${d}: ${v.length} meta-categories -- ` + v.map((e) => e.name).join(' | ')) }
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--ingest", metavar="RUN_ID")
    ap.add_argument("--output", metavar="PATH", help="workflow task .output file")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.build:
        prepare(build_only=True)
    elif a.prepare:
        prepare()
    elif a.ingest:
        ingest(a.ingest, a.output)
    elif a.report:
        report()
    else:
        ap.print_help()
