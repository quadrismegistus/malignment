"""Does a construct boundary survive being shown to someone who never saw the construct?

    python discriminate.py --build              triads only, nothing spent
    python discriminate.py --prepare            + the workflow
    python discriminate.py --ingest RUN --arm stripped
    python discriminate.py --report

## The question this answers, and the one it does not

A project-wide vocabulary needs cross-prompt merges, and there is no way to test
one by membership (disjoint by construction) or by name (three harmonisers gave
one identical partition three different vocabularies). What is left is ostensive:
define a construct by its exemplars, and make sameness a discrimination test.

This runs that test WHERE THE ANSWER IS KNOWN, within a single prompt, before
anyone spends on the cross-prompt version. Every relation in a triad completes
the same sentence, so topic is constant and cannot be the thing sorted on. If the
boundary is not recoverable here it is not recoverable anywhere, and that is worth
about a dozen agents rather than forty prompts of stage 2.

## Ground truth is the CORE, not one harmoniser's partition

Strict unanimity -- identical member sets in all three -- keeps only 4 of 7
constructs on the stroking prompt and 2 of 5 on the institutional one, and it
throws away both large constructs, because the disagreements are about MARGINAL
MEMBERS rather than about whether the construct exists. h2 put 11 relations in
`Transgressive to permitted` where h1 and h3 put the same 10.

So a construct's core is the INTERSECTION of the three harmonisers' versions of
it, matched by best Jaccard, and a construct whose match falls below 0.5 in
either direction is dropped whole: an overlap that small is not three readings of
one construct. `Spread collapses to hedge` goes out on that rule.

A relation the three assigned differently appears in NEITHER role. Using it as
the odd item would score a rater wrong for reproducing a disagreement the
harmonisers themselves had.

## Two arms, because a null would otherwise be unreadable

The harmonisers saw relation names. `stripped` hides them, `named` shows them.
If only the named arm recovers the boundaries, the stage-2 partition was driven
by name similarity and merging across prompts by name is circular. Run both:
without the named arm a failure of the stripped arm cannot be told apart from the
task simply being harder than harmonisation.

## Both error directions get measured

    negative control   2 from construct A, 1 from B     an odd item EXISTS
    positive control   3 from construct A               there is NO odd item

A rater forced to choose will choose, so an instrument that only ever says
"distinct" scores perfectly on negatives and is worthless. The positives, with
`none` offered and normalised in the instructions, are the only thing that
catches it.
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys

import harmonise_prompt as HP

HERE = os.path.dirname(os.path.abspath(__file__))
INSTRUMENT = os.path.join(HERE, "INSTRUMENT_discriminate.md")
STASH = os.path.join(HERE, "results", "discriminate_stash")
SEED = "discriminate-d1"
N_RATERS = 3
BATCHES = 2
N_POS, N_NEG = 8, 12
ARMS = ("stripped", "named")


def _stash():
    from hashstash import HashStash
    os.makedirs(STASH, exist_ok=True)
    return HashStash(root_dir=STASH, engine="jsonl", flat=True)


def _rng(*parts):
    """Deterministic per-purpose stream. Nothing here may depend on wall clock."""
    h = hashlib.sha256(("|".join([SEED] + [str(p) for p in parts])).encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def cores():
    """{prompt: {name: (core_ids, relations)}} over both harmonised prompts."""
    st = HP._stash()
    by = {}
    for k in st.keys():
        by.setdefault(k["frame_prompt"], {})[k["harmoniser"]] = st[k]
    out = {}
    for prompt, r in by.items():
        if len(r) != 3:
            print("skipping %r: %d harmonisers, need 3" % (prompt[:40], len(r)), file=sys.stderr)
            continue
        _, items, _, _, _ = HP.shard(prompt[:24])
        rel = dict(items)
        S = {i: [(c["name"], frozenset(c["members"])) for c in r[i]["result"]["constructs"]]
             for i in r}
        keep = {}
        for name, m in S[1]:
            core, ok = set(m), True
            for o in (2, 3):
                j, best = max(((len(m & q) / len(m | q), q) for _, q in S[o]),
                              key=lambda t: t[0])
                if j < 0.5:
                    ok = False
                core &= best
            if ok and core:
                keep[name] = (sorted(core), rel)
        out[prompt] = keep
    return out


def triads():
    """Positive and negative controls, seeded, with the odd position randomised."""
    C, pos, neg = cores(), [], []
    for prompt in sorted(C):
        for name, (core, _) in sorted(C[prompt].items()):
            if len(core) >= 3:
                rng = _rng("pos", prompt, name)
                seen = set()
                for _ in range(40):
                    t = tuple(sorted(rng.sample(core, 3)))
                    if t not in seen:
                        seen.add(t)
                        pos.append({"prompt": prompt, "kind": "pos", "a": name, "b": None,
                                    "ids": list(t), "odd": None})
            names = sorted(C[prompt])
            for other in names:
                if other == name or len(core) < 2:
                    continue
                ocore = C[prompt][other][0]
                rng = _rng("neg", prompt, name, other)
                pair = sorted(rng.sample(core, 2))
                odd = rng.choice(ocore)
                neg.append({"prompt": prompt, "kind": "neg", "a": name, "b": other,
                            "ids": pair + [odd], "odd": odd})
    #: Sample DOWN from every construct rather than taking the first N, so the set
    #: is not dominated by whichever construct sorts first. Positives are limited
    #: by how few constructs have a core of 3, and that limit is reported.
    _rng("pick-pos").shuffle(pos)
    _rng("pick-neg").shuffle(neg)
    chosen = pos[:N_POS] + neg[:N_NEG]
    #: BALANCE THE ODD POSITION, do not merely randomise it. A free shuffle gave
    #: 2/5/5 over the twelve negatives, and a rater biased toward the last item
    #: would then score above chance on layout alone. Position is a demonstrated
    #: response channel in this apparatus (r5 per-relation confidence was `low`
    #: at 0/9/68% by position), so it is assigned rather than left to luck.
    slots = [1, 2, 3] * (N_NEG // 3 + 1)
    slots = slots[:sum(1 for t in chosen if t["kind"] == "neg")]
    _rng("balance").shuffle(slots)
    out = []
    for t in chosen:
        rng = _rng("layout", t["prompt"], t["a"], t["b"], "".join(t["ids"]))
        ids = list(t["ids"])
        rng.shuffle(ids)
        if t["odd"]:
            want = slots.pop() - 1
            ids.remove(t["odd"])
            ids.insert(want, t["odd"])
        t["items"] = ids
        t["odd_pos"] = (ids.index(t["odd"]) + 1) if t["odd"] else None
        t["tid"] = "t" + hashlib.sha256(
            ("%s|%s" % (t["prompt"], "".join(t["ids"]))).encode()).hexdigest()[:6]
        out.append(t)
    _rng("interleave").shuffle(out)
    if len({t["tid"] for t in out}) != len(out):
        raise SystemExit("duplicate triad id")
    return out, C


def render(t, C, arm):
    rel = list(C[t["prompt"]].values())[0][1]
    lines = ["SET %s" % t["tid"]]
    for n, rid in enumerate(t["items"], 1):
        x = rel[rid]
        lines.append("  %d." % n)
        if arm == "named":
            lines.append("     name: %s" % x["name"])
        lines.append("     A: %s" % ", ".join(x["a_words"]))
        lines.append("     B: %s" % ", ".join(x["b_words"]))
        lines.append("     %s" % x["sentence"])
    return "\n".join(lines)


def prepare(build_only=False):
    ts, C = triads()
    npos = sum(1 for t in ts if t["kind"] == "pos")
    print("%d triads: %d positive (no odd item), %d negative" % (len(ts), npos, len(ts) - npos))
    src = {}
    for prompt in sorted(C):
        usable = {n: len(c) for n, (c, _) in C[prompt].items()}
        print("  %-34s cores %s" % (prompt[:34], usable))
        src[prompt] = usable
    from collections import Counter
    print("  odd position among negatives: %s"
          % dict(Counter(t["odd_pos"] for t in ts if t["kind"] == "neg")))
    print("  positives drawn from: %s" % sorted({t["a"] for t in ts if t["kind"] == "pos"}))
    if build_only:
        return
    text = open(INSTRUMENT).read()
    tmpl = re.search(r"## PROMPT TEMPLATE\s*\n+```\n(.*?)\n```", text, re.S).group(1)
    schema = json.loads(re.search(r"## SCHEMA JSON\b.*?\n```json\n(.*?)\n```", text, re.S).group(1))
    key = {}
    for arm in ARMS:
        for b in range(BATCHES):
            chunk = ts[b::BATCHES]
            body = "\n\n".join(render(t, C, arm) for t in chunk)
            p = os.path.join(HERE, "results", "inputs", "disc_%s_b%d.txt" % (arm, b))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write(tmpl.replace("{{n_triads}}", str(len(chunk)))
                                   .replace("{{triads}}", body))
            for t in chunk:
                if t["tid"] not in body:
                    raise SystemExit("triad %s missing from its own batch" % t["tid"])
            key[(arm, b)] = p
    json.dump({"triads": ts, "seed": SEED, "cores": src},
              open(os.path.join(HERE, "results", "disc_state.json"), "w"), indent=1)
    js = SCRIPT % {"raters": N_RATERS,
                   "files": json.dumps({"%s|%d" % k: os.path.abspath(v) for k, v in key.items()},
                                       indent=2),
                   "schema": json.dumps(schema, indent=2, sort_keys=True)}
    out = os.path.join(HERE, "workflow_discriminate.js")
    open(out, "w").write(js)
    print("\n  %d agents (%d arms x %d batches x %d raters)\n  workflow %s\n\nNOT RUN."
          % (len(ARMS) * BATCHES * N_RATERS, len(ARMS), BATCHES, N_RATERS, out))


def ingest(run_id):
    """Join journal results to their arm and batch through the agent transcripts.

    THE JOURNAL DOES NOT CARRY THE CALLER'S METADATA. Its `result` lines hold the
    agent's own return value and nothing else: `label` is None on every line, and
    `key` is an opaque `v2:<sha>`. The script's `.then((res) => ({...j, ...}))`
    wrapper runs in the workflow, not in the agent, so none of `arm`, `batch` or
    `rater` reaches the journal even though the script attached all three.

    What survives is `agentId`, and each agent's transcript contains the prompt
    it was given, which names its input file. So the arm and batch are recovered
    from the FILE PATH in `agent-<id>.jsonl`. Rater number is assigned by sorted
    agentId within a cell, which is arbitrary and legitimate because raters are
    exchangeable -- nothing distinguishes them but the draw.

    Any future ingest that needs to know which condition an agent was in has to
    go this way, or the workflow has to carry the condition back in its RETURN
    value. Do not expect a label.
    """
    import glob
    state = json.load(open(os.path.join(HERE, "results", "disc_state.json")))
    tids = {t["tid"] for t in state["triads"]}
    per_batch = {b: {t["tid"] for t in state["triads"][b::BATCHES]} for b in range(BATCHES)}
    base = os.path.expanduser("~/.claude/projects")
    hits = glob.glob(os.path.join(base, "*", "*", "subagents", "workflows", run_id))
    if not hits:
        raise SystemExit("no transcript dir for %r" % run_id)
    d0 = hits[0]
    cells = {}
    for line in open(os.path.join(d0, "journal.jsonl")):
        d = json.loads(line)
        if d.get("type") != "result" or not isinstance(d.get("result"), dict):
            continue
        aid = d["agentId"]
        tp = os.path.join(d0, "agent-%s.jsonl" % aid)
        if not os.path.exists(tp):
            raise SystemExit("no transcript for agent %s; cannot place it in a cell" % aid)
        m = re.search(r"disc_(\w+?)_b(\d)\.txt", open(tp).read(8000))
        if not m:
            raise SystemExit("agent %s transcript names no input file" % aid)
        arm, batch = m.group(1), int(m.group(2))
        if arm not in ARMS:
            raise SystemExit("agent %s read an unknown arm %r" % (aid, arm))
        bad = [a["triad"] for a in d["result"]["answers"] if a["triad"] not in tids]
        if bad:
            raise SystemExit("answers name %d triad(s) never issued: %s" % (len(bad), bad[:3]))
        #: The batch read off the path must match the triads actually answered,
        #: or a rater has been filed against a shard it never saw.
        got = {a["triad"] for a in d["result"]["answers"]}
        if not got <= per_batch[batch]:
            raise SystemExit("agent %s answered %d triad(s) outside batch %d"
                             % (aid, len(got - per_batch[batch]), batch))
        cells.setdefault((arm, batch), []).append((aid, d["result"]))
    st, n = _stash(), 0
    for (arm, batch), v in sorted(cells.items()):
        for i, (aid, res) in enumerate(sorted(v), 1):
            st[{"stage": "discriminate", "version": "d1", "seed": state["seed"],
                "arm": arm, "batch": batch, "rater": i}] = dict(res, agent_id=aid,
                                                                run_id=run_id)
            n += 1
    print("stored %d rater-batches for %s" % (n, run_id))
    print("  cells: %s" % {("%s/b%d" % k): len(v) for k, v in sorted(cells.items())})
    miss = [k for k in [(a, b) for a in ARMS for b in range(BATCHES)] if k not in cells]
    if miss:
        print("  MISSING cells: %s" % miss, file=sys.stderr)


def report():
    from collections import Counter
    state = json.load(open(os.path.join(HERE, "results", "disc_state.json")))
    T = {t["tid"]: t for t in state["triads"]}
    st = _stash()
    rows = []
    for k in st.keys():
        for a in st[k]["answers"]:
            t = T[a["triad"]]
            rows.append({"arm": k["arm"], "rater": k["rater"], "tid": a["triad"],
                         "kind": t["kind"], "odd_pos": t["odd_pos"], "said": a["odd"],
                         "conf": a["confidence"], "basis": a["basis"],
                         "a": t["a"], "b": t["b"]})
    if not rows:
        raise SystemExit("nothing ingested")
    print("%d answers\n" % len(rows))
    for arm in ARMS:
        R = [r for r in rows if r["arm"] == arm]
        if not R:
            continue
        neg = [r for r in R if r["kind"] == "neg"]
        pos = [r for r in R if r["kind"] == "pos"]
        hit = sum(1 for r in neg if r["said"] == str(r["odd_pos"]))
        miss_none = sum(1 for r in neg if r["said"] == "none")
        ok = sum(1 for r in pos if r["said"] == "none")
        print("%-9s NEGATIVE  %3d triads  hit %.2f (chance 0.33)  said none %.2f"
              % (arm, len(neg), hit / len(neg) if neg else 0,
                 miss_none / len(neg) if neg else 0))
        print("%-9s POSITIVE  %3d triads  said none %.2f  false split %.2f"
              % ("", len(pos), ok / len(pos) if pos else 0,
                 1 - ok / len(pos) if pos else 0))
        #: A clustered answer distribution means the panel measured layout. The
        #: r5 codings put `low` confidence at 0/9/68% by position, so this is a
        #: demonstrated failure mode of this apparatus and not a generic caution.
        print("%-9s answers by position: %s\n"
              % ("", dict(Counter(r["said"] for r in R))))
    #: A negative triad on which EVERY rater in BOTH arms says `none` is not a
    #: miss. It is the panel unanimously overturning a stage-2 boundary, and it
    #: is the property that makes this instrument worth having: one that only
    #: ever confirmed the harmonisers would be redundant with them. Reported
    #: separately, and the headline hit rate is given with and without, because
    #: scoring a rater wrong for a verdict the whole panel reached is not a
    #: measurement of the rater.
    per_t = {}
    for r in rows:
        if r["kind"] == "neg":
            per_t.setdefault(r["tid"], []).append(r)
    overturned = [t for t, v in per_t.items()
                  if len(v) >= 4 and all(x["said"] == "none" for x in v)]
    if overturned:
        print("OVERTURNED: every rater in both arms saw no boundary")
        for t in overturned:
            v = per_t[t][0]
            print("   %s  %r vs %r  (%d raters, unanimous)"
                  % (t, v["a"], v["b"], len(per_t[t])))
        for arm in ARMS:
            neg = [r for r in rows if r["arm"] == arm and r["kind"] == "neg"
                   and r["tid"] not in overturned]
            if neg:
                h = sum(1 for r in neg if r["said"] == str(r["odd_pos"]))
                print("   %-9s hit excluding overturned: %d of %d = %.2f"
                      % (arm, h, len(neg), h / len(neg)))
        print()
    #: Whether confidence is a usable gate matters more than the raw rate: the
    #: cross-prompt version has no ground truth to score against, so a
    #: self-reported filter is the only quality control available there.
    conf = {}
    for r in rows:
        if r["kind"] == "neg":
            conf.setdefault(r["conf"], []).append(r["said"] == str(r["odd_pos"]))
    print("negatives by self-reported confidence:")
    for c in ("high", "medium", "low"):
        v = conf.get(c)
        if v:
            print("   %-6s %3d answers, %.2f correct" % (c, len(v), sum(v) / len(v)))
    print("\nhardest negative pairs (lowest hit rate across raters and arms):")
    per = {}
    for r in rows:
        if r["kind"] == "neg":
            per.setdefault((r["a"], r["b"]), []).append(r["said"] == str(r["odd_pos"]))
    for (a, b), v in sorted(per.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))[:6]:
        print("   %.2f  %-28s vs %s" % (sum(v) / len(v), a[:28], b))


SCRIPT = """// GENERATED by discriminate.py. Odd-one-out validation, two arms.
export const meta = { name: 'discriminate-d1',
  description: 'Can a construct boundary be recovered without the construct?',
  phases: [{ title: 'Discriminate', detail: 'stripped and named arms' }] }
const FILES = %(files)s
const SCHEMA = %(schema)s
const jobs = []
for (const [k, path] of Object.entries(FILES)) {
  const [arm, batch] = k.split('|')
  for (let r = 1; r <= %(raters)d; r++) jobs.push({ arm, batch: Number(batch), rater: r, path })
}
const out = await parallel(jobs.map((j) => () =>
  agent(`Read the file ${j.path} with the Read tool.\\n\\nIts entire content is a ` +
    `task addressed to you. Follow it exactly and answer every set in it. Do not ` +
    `read any other file, do not run any command.\\n\\nReturn your answer by ` +
    `calling StructuredOutput.`,
    { label: `${j.arm}-b${j.batch}-r${j.rater}`, phase: 'Discriminate', schema: SCHEMA })
   .then((res) => ({ ...j, answers: res.answers })).catch(() => null)))
const g = out.filter(Boolean)
log(`${g.length} of ${jobs.length} returned`)
return { returned: g.length, answers: g.reduce((n, x) => n + x.answers.length, 0) }
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
