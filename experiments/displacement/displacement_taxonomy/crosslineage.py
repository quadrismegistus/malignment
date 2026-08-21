"""One sentence, every lineage at once, returning PER-MODEL rows.

    python crosslineage.py --prepare "He started stroking his"
    python crosslineage.py --ingest RUN_ID --slug <slug>
    python crosslineage.py --report

## Why the unit is the prompt

Stage 1 forbade a repeated prompt or pair within an agent's batch, so no rater
ever saw two lineages on one sentence. The consequence is that the direction
split -- seventeen lineages performing an operation and one running it backwards
-- was invisible at annotation time and is currently an artifact of pooling
rather than anyone's judgement. This puts the comparison in front of a reader.

## Why the output is rows and not prose

RH's requirement, and it is what makes the result usable: an operation is only
worth having if it resolves to which lineage instantiates it with which words.
So each operation carries one entry per member model with that model's own A and
B words, and the result joins straight onto `word_groups.csv` on (prompt, model).

## The assert that matters

Every model shown must appear exactly once across `operations`, `reversed` and
`unassigned`, and no model may appear that was not shown. Both directions are
checked because both fail silently and both destroy the finding: a dropped
lineage looks exactly like a dissenting one, and a hallucinated lineage would be
a reversal nobody measured.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import sys

import run as R

HERE = os.path.dirname(os.path.abspath(__file__))
INSTRUMENT = os.path.join(HERE, "INSTRUMENT_crosslineage.md")
STASH = os.path.join(HERE, "results", "crosslineage_stash")
MODEL, EFFORT = "sonnet", "xhigh"


def _stash():
    from hashstash import HashStash
    os.makedirs(STASH, exist_ok=True)
    return HashStash(root_dir=STASH, engine="jsonl", flat=True)


def tables(prompt_prefix):
    """Rebuild every lineage's two-column table for one prompt, from twp.

    Rebuilt rather than recovered from the stage-1 job files: those were written
    per batch of eight mixed cells and never per prompt, and the store is the
    authoritative input anyway. TOPUP is forced on for the same reason stage 1
    required it.
    """
    from malignment import vectors as V, roster
    R.TOPUP = 1
    globals_ = R.__dict__
    globals_["TOPUP"] = 1
    #: PAIRS COME FROM THE ROSTER AND TOPUP COVERAGE, NOT FROM STAGE-1 CODINGS.
    #: This instrument reads word tables from twp, so a lineage needs only both
    #: arms topped up on this prompt -- it does not need to have been annotated.
    #: Sourcing from the codings silently capped the roster at the 18 that stage
    #: 1 happened to use, while 25 were available, and the gap is growing as pass
    #: 2 ingests per arm. The seven extra include gemma-2-9b-it and a DPO pythia,
    #: which is exactly the kind of variation the direction question needs.
    st = R._stash()
    prompt = None
    for k in st.keys():
        m = (st[k].get("meta") or {})
        if m.get("batch") and m["frame_prompt"].startswith(prompt_prefix):
            prompt = m["frame_prompt"]
            break
    if prompt is None:
        raise SystemExit("no batched codings for a prompt starting %r" % prompt_prefix)
    ep, _ = roster.endpoints()
    #: `merged=1` IS A PROVENANCE FILTER, NOT A QUALITY ONE -- the view's own
    #: COMMENT says so. A cell has merged=1 where a topup exists and 0 where it
    #: does not, so this silently drops any model never topped up on this prompt.
    #: On 'He started stroking his' that is exactly one model,
    #: deepseek-ai/DeepSeek-R1-Distill-Qwen-7B (2,965 pass-1 cells, 0 topup), and
    #: 145 -> 144 is that and nothing else (malign, 2026-08-21).
    #:
    #: It happens to land on the 50-endpoint population, but BY ACCIDENT of one
    #: model never being topped up rather than by declaring anything. So the
    #: exclusion is named in the output: otherwise the next reader takes 144 to
    #: mean the roster and it means the roster minus whatever pass 2 missed.
    all_models = {r["model"] for r in V.rows(
        "SELECT DISTINCT model FROM twp_cells_v4_best "
        "WHERE prompt={p:String}", p=prompt)}
    have = {r["model"] for r in V.rows(
        "SELECT DISTINCT model FROM twp_cells_v4_best "
        "WHERE prompt={p:String} AND merged=1", p=prompt)}
    dropped = sorted(all_models - have)
    if dropped:
        print("merged=1 excludes %d of %d model(s) never topped up on this prompt: %s"
              % (len(dropped), len(all_models), ", ".join(dropped)), file=sys.stderr)
    pairs = sorted((a.split("/")[-1], b, a) for b, a in ep.items()
                   if b in have and a in have)
    if not pairs:
        raise SystemExit("no pair has both arms topped up on %r" % prompt)
    models = sorted({x for _, b, a in pairs for x in (b, a)})
    rows = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                  "FROM twp_words_v4_best WHERE prompt={p:String} "
                  "AND model IN {ms:Array(String)} AND merged=1 GROUP BY model",
                  p=prompt, ms=models)
    W = {r["model"]: dict(zip(r["ws"], r["ps"])) for r in rows}
    out = []
    for nick, b, a in pairs:
        if b not in W or a not in W:
            print("skip %s: an arm is missing from twp" % nick, file=sys.stderr)
            continue
        nb = {w: p / sum(W[b].values()) for w, p in W[b].items()}
        na = {w: p / sum(W[a].values()) for w, p in W[a].items()}
        out.append((nick, R._table_r4(nb, na)))
    return prompt, out


def prepare(prefix, model=MODEL, effort=EFFORT):
    prompt, tbl = tables(prefix)
    src = open(INSTRUMENT).read()
    tmpl = re.search(r"## PROMPT TEMPLATE\s*\n+```\n(.*?)\n```", src, re.S).group(1)
    schema = json.loads(re.search(r"## SCHEMA JSON\b.*?\n```json\n(.*?)\n```", src, re.S).group(1))
    body = "\n\n".join("=== MODEL %s ===\n%s" % (n, t) for n, t in tbl)
    text = (tmpl.replace("{{n_models}}", str(len(tbl)))
                .replace("{{fragment}}", prompt + " ___")
                .replace("{{tables}}", body))
    slug = re.sub(r"[^a-z0-9]+", "_", prompt.lower())[:40].strip("_")
    path = os.path.join(HERE, "results", "inputs", "xling_%s.txt" % slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)
    for n, _ in tbl:
        if ("=== MODEL %s ===" % n) not in text:
            raise SystemExit("model %s missing from its own task" % n)
    #: The roster is a moving target -- topped-up pairs went 21 to 25 within an
    #: hour as pass 2 ingested -- so the list is pinned in the state file and the
    #: ingest checks against THAT, not against a fresh query.
    state = {"prompt": prompt, "slug": slug, "models": [n for n, _ in tbl],
             "n_lineages": len(tbl),
             "model": model, "effort": effort, "path": path,
             "version": re.search(r"^# INSTRUMENT: \S+ (\S+)", src, re.M).group(1)}
    json.dump(state, open(os.path.join(HERE, "results", "xling_%s.json" % slug), "w"), indent=1)
    js = SCRIPT % {"path": json.dumps(os.path.abspath(path)),
                   "schema": json.dumps(schema, indent=2, sort_keys=True),
                   "model": json.dumps(model), "effort": json.dumps(effort),
                   "slug": slug}
    out = os.path.join(HERE, "workflow_xling_%s.js" % slug)
    open(out, "w").write(js)
    for probe in (os.path.abspath(path), '"operations"', model, effort):
        if probe not in js:
            raise SystemExit("generated script missing %r" % probe)
    print("%r\n  %d lineages, %d chars of tables (~%d tokens)"
          % (prompt, len(tbl), len(body), len(body) // 4))
    print("  task     %s" % path)
    print("  workflow %s\n\nNOT RUN." % out)


def ingest(run_id, slug):
    import glob
    state = json.load(open(os.path.join(HERE, "results", "xling_%s.json" % slug)))
    shown = set(state["models"])
    base = os.path.expanduser("~/.claude/projects")
    hits = glob.glob(os.path.join(base, "*", "*", "subagents", "workflows", run_id))
    if not hits:
        raise SystemExit("no transcript dir for %r" % run_id)
    res = []
    for line in open(os.path.join(hits[0], "journal.jsonl")):
        d = json.loads(line)
        if d.get("type") == "result" and isinstance(d.get("result"), dict) \
                and "operations" in d["result"]:
            res.append(d["result"])
    if not res:
        raise SystemExit("no result carrying `operations` in the journal")
    st = _stash()
    for i, r in enumerate(res, 1):
        seen = collections.Counter()
        for op in r["operations"]:
            for m in op["members"]:
                seen[m["model"]] += 1
        for x in r["reversed"] + r["unassigned"]:
            seen[x["model"]] += 1
        #: BOTH DIRECTIONS. A dropped lineage looks exactly like a dissenting one,
        #: and a hallucinated lineage would be a reversal nobody measured.
        missing = sorted(shown - set(seen))
        extra = sorted(set(seen) - shown)
        dupes = sorted(m for m, n in seen.items() if n > 1)
        if missing or extra:
            raise SystemExit("rater %d: %d model(s) never placed %s ; %d not shown %s"
                             % (i, len(missing), missing[:4], len(extra), extra[:4]))
        if dupes:
            print("  rater %d: %d model(s) placed more than once: %s"
                  % (i, len(dupes), dupes[:4]), file=sys.stderr)
        #: LINEAGES_SHA IS PART OF THE KEY (RH's pairs_sha lesson, applied late).
        #: Which lineages were shown determines the answer: the same prompt read
        #: at 18 and at 29 lineages gave 3 operations and 7. Without this in the
        #: key the second run OVERWROTE the first and the comparison was lost --
        #: which is exactly what happened before this line existed.
        lsha = hashlib.sha256("\n".join(sorted(state["models"])).encode()).hexdigest()[:12]
        st[{"stage": "crosslineage", "version": state["version"],
            "frame_prompt": state["prompt"], "model": state["model"],
            "effort": state["effort"], "lineages_sha": lsha,
            "n_lineages": len(state["models"]), "rater": i}] = dict(
                r, run_id=run_id, models=state["models"])
    print("stored %d reading(s) for %r" % (len(res), state["prompt"][:52]))
    for i, r in enumerate(res, 1):
        print("  r%d: %d operations, %d reversed, %d unassigned, %s"
              % (i, len(r["operations"]), len(r["reversed"]),
                 len(r["unassigned"]), r["confidence"]))


def report():
    st = _stash()
    ks = sorted(st.keys(), key=lambda d: (d["frame_prompt"], d["rater"]))
    if not ks:
        raise SystemExit("nothing ingested")
    for k in ks:
        v = st[k]
        print("\n%r  rater %d  (%s/%s, %s)"
              % (k["frame_prompt"], k["rater"], k["model"], k["effort"], v["confidence"]))
        print("  SURVEY: %s\n" % v["survey"][:400])
        for op in v["operations"]:
            print("  %-38s %d model(s)" % (op["name"][:38], len(op["members"])))
            print("     %s" % op["statement"][:150])
            for m in op["members"][:3]:
                print("       %-26s %s -> %s"
                      % (m["model"][:26], ", ".join(m["a_words"])[:34],
                         ", ".join(m["b_words"])[:34]))
            if len(op["members"]) > 3:
                print("       ... %d more" % (len(op["members"]) - 3))
        for x in v["reversed"]:
            print("  REVERSED  %-24s of %s" % (x["model"][:24], x["operation"][:30]))
            print("     A: %s" % ", ".join(x["a_words"])[:60])
            print("     B: %s" % ", ".join(x["b_words"])[:60])
            print("     %s" % x["how_you_know"][:180])
        for x in v["unassigned"]:
            print("  UNASSIGNED %-24s %s" % (x["model"][:24], x["why"][:70]))


SCRIPT = """// GENERATED by crosslineage.py. One prompt, every lineage, one rater.
export const meta = { name: 'xling-%(slug)s',
  description: 'One sentence across all lineages at once',
  phases: [{ title: 'Read', detail: 'per-model assignments' }] }
const FILE = %(path)s
const SCHEMA = %(schema)s
const r = await agent(`Read the file ${FILE} with the Read tool.\\n\\nIts entire ` +
  `content is a task addressed to you. Follow it exactly and answer every ` +
  `numbered question in it. Do not read any other file, do not run any command.` +
  `\\n\\nReturn your answer by calling StructuredOutput.`,
  { label: 'xling', phase: 'Read', schema: SCHEMA,
    model: %(model)s, effort: %(effort)s })
return { operations: r.operations.length, reversed: r.reversed.length,
  unassigned: r.unassigned.length, confidence: r.confidence,
  names: r.operations.map((o) => `${o.name} (${o.members.length})`) }
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prepare", metavar="PROMPT_PREFIX")
    ap.add_argument("--ingest", metavar="RUN_ID")
    ap.add_argument("--slug")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.prepare:
        prepare(a.prepare)
    elif a.ingest:
        if not a.slug:
            raise SystemExit("--ingest needs --slug")
        ingest(a.ingest, a.slug)
    elif a.report:
        report()
    else:
        ap.print_help()
