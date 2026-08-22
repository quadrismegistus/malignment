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


SLOTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
                     "roster", "prompts", "slots")


def slot_items():
    """`[(domain, prompt)]` for the whole slot corpus.

    ## WHY THIS REPLACED A SCAN OF THE STAGE-1 CODINGS

    `tables()` used to resolve a prefix by searching `run._stash()` for BATCHED
    CODINGS and exiting with "no batched codings for a prompt starting X" when it
    found none. That confined this instrument to the ~40 prompts the older
    per-cell experiment happened to annotate, out of 302 that have full ~50-pair
    coverage in twp right now.

    It was never a real dependency. This function's own docstring says pairs come
    from the roster and topup coverage, NOT from stage-1 codings; the stash was
    used for exactly one thing, turning a prefix into a prompt string. So the
    prompt now comes from the corpus that defines prompts, and 262 frames stop
    being unreachable for a reason that had nothing to do with them.
    """
    import glob, yaml
    out = []
    for f in sorted(glob.glob(os.path.join(SLOTS, "*.yaml"))):
        if os.path.basename(f).startswith("quarantined"):
            continue
        d = yaml.safe_load(open(f))
        xs = d if isinstance(d, list) else (d.get("items") or d.get("slots") or [])
        for x in xs or []:
            if isinstance(x, dict) and x.get("prompt"):
                out.append((x.get("domain") or "?", x["prompt"]))
    return out


def resolve(prefix):
    """The one prompt a prefix names, or a refusal listing what it matched.

    ## AMBIGUITY IS A REFUSAL, NOT A CHOICE

    At 40 prompts a prefix was almost always unique and the old code took the
    first hit from a dict scan. At 302 it frequently is not: `Three ` alone
    matches seven identity frames. Taking the first would silently pick a
    population, which is the same defect as letting glob order choose a file --
    and it fails invisibly, because the run succeeds and reads the wrong prompt.
    """
    cands = sorted({p for _, p in slot_items()
                    if p.lower().startswith(prefix.lower())})
    if not cands:
        #: A handful of stage-1 frames predate the slot corpus, so it is still
        #: consulted -- second, and only when the corpus has nothing.
        st = R._stash()
        cands = sorted({(st[k].get("meta") or {}).get("frame_prompt") for k in st.keys()
                        if (st[k].get("meta") or {}).get("batch")
                        and str((st[k].get("meta") or {}).get("frame_prompt", ""))
                        .lower().startswith(prefix.lower())} - {None})
    if not cands:
        raise SystemExit("no prompt in the slot corpus or the stage-1 codings "
                         "starts with %r" % prefix)
    if len(cands) > 1:
        raise SystemExit("%r matches %d prompts; give more of it:\n  %s"
                         % (prefix, len(cands), "\n  ".join(repr(c) for c in cands[:8])))
    return cands[0]


def tables(prompt_prefix, want_rows=False):
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
    prompt = resolve(prompt_prefix)
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
    out, rowdata = [], {}
    for nick, b, a in pairs:
        if b not in W or a not in W:
            print("skip %s: an arm is missing from twp" % nick, file=sys.stderr)
            continue
        nb = {w: p / sum(W[b].values()) for w, p in W[b].items()}
        na = {w: p / sum(W[a].values()) for w, p in W[a].items()}
        txt, data = R._table_two_column(nb, na, rows=True)
        out.append((nick, txt))
        #: THE TABLE'S OWN NUMBERS, KEPT. Rendering and discarding them meant any
        #: later check of a rater against the table had to re-parse the string,
        #: which is a second implementation of the selection rules and disagreed
        #: with the first twice in one evening. `tables()` is where the data
        #: exists, so it is where it gets carried out.
        rowdata[nick] = data
    return (prompt, out, rowdata) if want_rows else (prompt, out)


def prepare(prefix, model=MODEL, effort=EFFORT, raters=1, blind=False):
    prompt, tbl, rowdata = tables(prefix, want_rows=True)
    src = open(INSTRUMENT).read()
    #: ── BLIND: NEUTRAL FRAMING *AND* NEUTRAL LABELS ─────────────────────────
    #: Swapping the framing paragraph alone is not a blind. The headings carry
    #: `-Instruct`, `-Chat`, `-DPO`, `_sft-dpo_`, `AmberSafe`, `beaver-7b`: a
    #: reader told only "A and B" still knows which process is under study, and
    #: `AmberSafe` says what to expect of that row. Both go, or neither does.
    #: Seeded on the PROMPT so a re-prepare is reproducible and no label carries
    #: meaning across prompts.
    label = {}
    if blind:
        import random
        order = sorted(n for n, _ in tbl)
        random.Random(prompt).shuffle(order)
        label = {n: "M%02d" % (i + 1) for i, n in enumerate(order)}
        tbl = [(label[n], t) for n, t in tbl]
    key = "## PROMPT TEMPLATE BLIND" if blind else "## PROMPT TEMPLATE"
    tmpl = re.search(re.escape(key) + r"\s*\n+```\n(.*?)\n```", src, re.S).group(1)
    schema = json.loads(re.search(r"## SCHEMA JSON\b.*?\n```json\n(.*?)\n```", src, re.S).group(1))
    body = "\n\n".join("=== MODEL %s ===\n%s" % (n, t) for n, t in tbl)
    text = (tmpl.replace("{{n_models}}", str(len(tbl)))
                .replace("{{fragment}}", prompt + " ___")
                .replace("{{tables}}", body))
    slug = re.sub(r"[^a-z0-9]+", "_", prompt.lower())[:40].strip("_")
    if blind:
        slug += "_blind"
    path = os.path.join(HERE, "results", "inputs", "xling_%s.txt" % slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)
    for n, _ in tbl:
        if ("=== MODEL %s ===" % n) not in text:
            raise SystemExit("model %s missing from its own task" % n)
    #: The roster is a moving target -- topped-up pairs went 21 to 25 within an
    #: hour as pass 2 ingested -- so the list is pinned in the state file and the
    #: ingest checks against THAT, not against a fresh query.
    ver = re.search(r"^# INSTRUMENT: \S+ (\S+)", src, re.M).group(1)
    #: `models` is what the RATER SEES -- the ingest assert must run over the
    #: names actually used. `unlabel` restores the real ones before anything
    #: reaches the stash, and `real_models` is what `lineages_sha` is taken over,
    #: so a blind and a sighted reading of the same roster share a sha and stay
    #: comparable. Hashing the labels would have made them different populations.
    state = {"prompt": prompt, "slug": slug, "models": [n for n, _ in tbl],
             "real_models": sorted(label) if label else [n for n, _ in tbl],
             "n_lineages": len(tbl), "blind": bool(blind),
             "unlabel": {v: k for k, v in label.items()},
             "model": model, "effort": effort, "path": path,
             "version": ver + ("b" if blind else "")}
    json.dump(state, open(os.path.join(HERE, "results", "xling_%s.json" % slug), "w"), indent=1)
    #: Written beside the task under the REAL model names, whatever labels the
    #: rater saw, so a consumer never has to know whether a run was blind.
    tpath = os.path.join(HERE, "results", "xling_%s.tables.json" % slug)
    json.dump({"prompt": prompt, "blind": bool(blind), "tables": rowdata},
              open(tpath, "w"), indent=1)
    js = SCRIPT % {"raters": raters,
                   "path": json.dumps(os.path.abspath(path)),
                   "schema": json.dumps(schema, indent=2, sort_keys=True),
                   "model": json.dumps(model), "effort": json.dumps(effort),
                   "slug": slug}
    out = os.path.join(HERE, "workflow_xling_%s.js" % slug)
    open(out, "w").write(js)
    for probe in (os.path.abspath(path), '"operations"', model, effort):
        if probe not in js:
            raise SystemExit("generated script missing %r" % probe)
    print("%r\n  %d lineages, %d chars of tables (~%d tokens), %d rater(s)"
          % (prompt, len(tbl), len(body), len(body) // 4, raters)
          + ("  BLIND: A/B framing, labels M01..M%02d" % len(tbl) if blind else ""))
    print("  task     %s" % path)
    print("  tables   %s" % tpath)
    print("  workflow %s\n\nNOT RUN." % out)


def ingest(run_id, slug):
    import glob
    state = json.load(open(os.path.join(HERE, "results", "xling_%s.json" % slug)))
    shown = set(state["models"])
    unlabel = state.get("unlabel") or {}
    real = state.get("real_models") or state["models"]
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
    refused, stored = [], []
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
            #: REFUSED PER RATER, NOT PER RUN. The completeness check is right and
            #: stays -- a dropped lineage looks exactly like a dissenting one --
            #: but the stash key carries `rater`, so raters are independent
            #: records and one bad reading should not discard a good one. It did:
            #: on wf_aaae2bd5-0a1 rater 1 dropped CT-LLM-SFT-DPO, rater 2 placed
            #: all 50, and NOTHING was stored.
            #:
            #: Still loud, and still non-zero at exit: a refusal that only prints
            #: is a refusal somebody misses.
            print("REFUSED rater %d: %d model(s) never placed %s ; %d not shown %s"
                  % (i, len(missing), missing[:4], len(extra), extra[:4]), file=sys.stderr)
            refused.append(i)
            continue
        if dupes:
            print("  rater %d: %d model(s) placed more than once: %s"
                  % (i, len(dupes), dupes[:4]), file=sys.stderr)
        #: LINEAGES_SHA IS PART OF THE KEY (RH's pairs_sha lesson, applied late).
        #: Which lineages were shown determines the answer: the same prompt read
        #: at 18 and at 29 lineages gave 3 operations and 7. Without this in the
        #: key the second run OVERWROTE the first and the comparison was lost --
        #: which is exactly what happened before this line existed.
        #: OVER THE REAL NAMES, always. Under `--blind` `state["models"]` holds
        #: M01..M50, and hashing those would give the same 50 lineages a
        #: different sha depending on how they were labelled -- two populations
        #: where there is one, and the comparison this key exists to protect
        #: would have been lost exactly as it was before the key existed.
        lsha = hashlib.sha256("\n".join(sorted(real)).encode()).hexdigest()[:12]
        if unlabel:
            for op in r["operations"]:
                for m in op["members"]:
                    m["model"] = unlabel.get(m["model"], m["model"])
            for x in r["reversed"] + r["unassigned"]:
                x["model"] = unlabel.get(x["model"], x["model"])
        st[{"stage": "crosslineage", "version": state["version"],
            "frame_prompt": state["prompt"], "model": state["model"],
            "effort": state["effort"], "lineages_sha": lsha,
            "n_lineages": len(real), "rater": i}] = dict(
                r, run_id=run_id, blind=bool(unlabel), models=real)
        stored.append(i)
    print("stored %d of %d reading(s) for %r"
          % (len(stored), len(res), state["prompt"][:52]))
    for i in stored:
        r = res[i - 1]
        print("  r%d: %d operations, %d reversed, %d unassigned, %s"
              % (i, len(r["operations"]), len(r["reversed"]),
                 len(r["unassigned"]), r["confidence"]))
    if refused:
        print("  REFUSED rater(s): %s -- rerun them, the stored ones stand"
              % ", ".join(str(i) for i in refused), file=sys.stderr)
        raise SystemExit(1)


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


SCRIPT = """// GENERATED by crosslineage.py. One prompt, every lineage, %(raters)d rater(s).
export const meta = { name: 'xling-%(slug)s',
  description: 'One sentence across all lineages at once',
  phases: [{ title: 'Read', detail: 'per-model assignments' }] }
const FILE = %(path)s
const SCHEMA = %(schema)s
// %(raters)d rater(s). The TASK is byte-identical for each; only the label
// differs, so they are blind replicates rather than N agents given N jobs. Any
// difference between them is rater variance on one document, which is the only
// thing that separates "the roster changed the reading" from "a second sample
// would have differed anyway".
const TASK = `Read the file ${FILE} with the Read tool.\\n\\nIts entire ` +
  `content is a task addressed to you. Follow it exactly and answer every ` +
  `numbered question in it. Do not read any other file, do not run any command.` +
  `\\n\\nReturn your answer by calling StructuredOutput.`
const rs = (await parallel(Array.from({ length: %(raters)d }, (_, i) => () =>
  agent(TASK, { label: `xling r${i + 1}`, phase: 'Read', schema: SCHEMA,
    model: %(model)s, effort: %(effort)s })))).filter(Boolean)
if (rs.length < %(raters)d)
  log(`WARNING: %(raters)d rater(s) requested, ${rs.length} returned`)
return { raters: rs.length, per_rater: rs.map((x) => ({
  operations: x.operations.length, reversed: x.reversed.length,
  unassigned: x.unassigned.length, confidence: x.confidence,
  names: x.operations.map((o) => `${o.name} (${o.members.length})`) })) }
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prepare", metavar="PROMPT_PREFIX")
    ap.add_argument("--ingest", metavar="RUN_ID")
    ap.add_argument("--slug")
    ap.add_argument("--report", action="store_true")
    #: RATERS ARE SET BY THE WORKFLOW, NOT BY INGEST. `ingest` already enumerates
    #: every result carrying `operations` as rater 1..N, so the only thing that
    #: was missing was a way to ask for more than one.
    ap.add_argument("--raters", type=int, default=1)
    ap.add_argument("--blind", action="store_true",
                    help="neutral A/B framing AND anonymised model labels")
    a = ap.parse_args()
    if a.prepare:
        prepare(a.prepare, raters=a.raters, blind=a.blind)
    elif a.ingest:
        if not a.slug:
            raise SystemExit("--ingest needs --slug")
        ingest(a.ingest, a.slug)
    elif a.report:
        report()
    else:
        ap.print_help()
