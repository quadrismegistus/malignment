"""Can a cross-lineage reading be EXTENDED with new lineages, or must it be re-run?

    python incremental.py --prepare "He started stroking his"
    python incremental.py --ingest RUN_ID --slug <slug>

## The question, and why it gates everything downstream

The sweep runs at ~32 of 50 declared pairs. When the roster grows, either every
prompt is re-read from scratch or new lineages are folded into the existing
reading. At 177 prompts that is the difference between a re-run and an increment,
so it should be settled before the 177 are spent, not after.

## Why this is a known-answer test

`He started stroking his` has been read twice under the same instrument:

    18 lineages -> 3 operations, 3 reversed, 4 unassigned
    29 lineages -> 7 operations, 2 reversed, 2 unassigned   <- the standard

This shows the 18-lineage reading as a LEGEND plus only the 11 lineages it did
not contain, and asks for those 11 to be placed. If the result matches the
full-29 reading on those 11, extension works. If it does not, the sweep has to be
re-run whenever the roster moves and that cost is real and knowable now.

## The failure mode being tested for

Anchoring. A legend of three operations invites forcing eleven new lineages into
them, which would look like agreement while being an artifact of the legend. So
`new_operation` is a first-class answer with its own field, and the comparison
that matters is not "did it place them" but "did it place them WHERE THE FULL RUN
DID". A high placement rate with low agreement is the failure, and it is
distinguishable only because the full-29 reading exists.
"""

import argparse, collections, json, os, re, sys
import crosslineage as X, run as R

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL, EFFORT = "sonnet", "xhigh"

TMPL = """Below is a VOCABULARY of kinds of change already established for one sentence, \
then {{n_new}} further measurements that were not available when it was made.

Each measurement compares two versions of the same language model. Column A is \
the model before instruction tuning; column B is the same model after it. \
Position 1 is the likeliest completion under that condition; a dash means the \
word does not appear in that condition's list at all.

FRAGMENT: {{fragment}}

ESTABLISHED OPERATIONS

{{legend}}

NEW MEASUREMENTS

{{tables}}

For each new model, decide which established operation it performs, or whether it \
does something the vocabulary does not cover.

An operation is performed when the words the operation moves FROM are the ones \
this model's A column favours and the words it moves TO are the ones its B column \
favours. Judge the operation, not the vocabulary: these models were trained by \
different groups and their word lists will not match the examples.

Four answers are available for each model and all four are normal:

  an operation letter   it performs that operation in that direction
  REVERSED:<letter>     it performs that operation BACKWARDS -- the words the
                        operation moves away from are the ones its B column
                        favours. Check this before assigning a letter.
  NEW                   it does something none of the established operations
                        names. Say what, in `new_operation`. Do not force a
                        model into an established operation to avoid this.
  NONE                  its table shows no readable operation at all, e.g. every
                        movement is tiny, or the relevant vocabulary is absent.

Every new model must appear exactly once.
"""

#: `"type": "object"` is REQUIRED at every level and its absence is not a local
#: error: the API rejects the whole tool with
#: `tools.11.custom.input_schema.type: Field required`, naming a tool index
#: rather than the field, and the workflow then dies on `r.assignments` being
#: null. The instruments whose schema is parsed out of a markdown block carry it
#: because it was written out longhand there; this one was built in Python and
#: did not.
SCHEMA = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "assignments": {"type": "array", "items": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "model": {"type": "string"},
        "verdict": {"type": "string",
          "description": "an operation letter, REVERSED:<letter>, NEW, or NONE"},
        "new_operation": {"type": "string",
          "description": "if NEW, two to four words naming it; else empty"},
        "a_words": {"type": "array", "items": {"type": "string"}},
        "b_words": {"type": "array", "items": {"type": "string"}},
        "why": {"type": "string"},
        "confidence": {"enum": ["high", "medium", "low"], "type": "string"}},
      "required": ["model","verdict","new_operation","a_words","b_words","why","confidence"]}},
    "notes": {"type": "string"}},
  "required": ["assignments","notes"]}


def readings(prompt_prefix):
    st = X._stash(); out = {}
    for k in st.keys():
        if not k["frame_prompt"].startswith(prompt_prefix):
            continue
        v = st[k]
        out[k.get("n_lineages") or len(v.get("models") or [])] = v
    return out


def prepare(prefix):
    rd = readings(prefix)
    if len(rd) < 2:
        raise SystemExit("need two readings at different roster sizes; have %s" % sorted(rd))
    small, large = min(rd), max(rd)
    base, full = rd[small], rd[large]
    prompt, tbl = X.tables(prefix)
    have = set(base["models"])
    new = [(n, t) for n, t in tbl if n not in have]
    if not new:
        raise SystemExit("no lineages beyond the %d-model reading" % small)
    letters = "ABCDEFGHIJ"
    legend = []
    for i, op in enumerate(base["operations"]):
        L = ["OPERATION %s  %s" % (letters[i], op["name"]), "  %s" % op["statement"]]
        for m in op["members"][:2]:
            L.append("  e.g. %-24s A: %s" % (m["model"][:24], ", ".join(m["a_words"])[:52]))
            L.append("       %-24s B: %s" % ("", ", ".join(m["b_words"])[:52]))
        legend.append("\n".join(L))
    text = (TMPL.replace("{{n_new}}", str(len(new)))
                .replace("{{fragment}}", prompt + " ___")
                .replace("{{legend}}", "\n\n".join(legend))
                .replace("{{tables}}", "\n\n".join("=== MODEL %s ===\n%s" % (n, t) for n, t in new)))
    slug = re.sub(r"[^a-z0-9]+", "_", prompt.lower())[:40].strip("_")
    path = os.path.join(HERE, "results", "inputs", "incr_%s.txt" % slug)
    open(path, "w").write(text)
    json.dump({"prompt": prompt, "slug": slug, "base_n": small, "full_n": large,
               "new_models": [n for n, _ in new], "letters": letters[:len(base["operations"])],
               "base_ops": [o["name"] for o in base["operations"]]},
              open(os.path.join(HERE, "results", "incr_%s.json" % slug), "w"), indent=1)
    js = SCRIPT % {"path": json.dumps(os.path.abspath(path)),
                   "schema": json.dumps(SCHEMA, indent=2, sort_keys=True),
                   "model": json.dumps(MODEL), "effort": json.dumps(EFFORT), "slug": slug}
    out = os.path.join(HERE, "workflow_incr_%s.js" % slug)
    open(out, "w").write(js)
    print("%r\n  legend from the %d-lineage reading: %d operations"
          % (prompt, small, len(base["operations"])))
    print("  new lineages to place: %d" % len(new))
    print("  standard to compare against: the %d-lineage full reading" % large)
    print("  task     %s\n  workflow %s\n\nNOT RUN." % (path, out))


def ingest(run_id, slug):
    import glob
    s = json.load(open(os.path.join(HERE, "results", "incr_%s.json" % slug)))
    d0 = glob.glob(os.path.expanduser("~/.claude/projects/*/*/subagents/workflows/%s" % run_id))
    if not d0:
        raise SystemExit("no transcript dir for %r" % run_id)
    res = [json.loads(l)["result"] for l in open(os.path.join(d0[0], "journal.jsonl"))
           if json.loads(l).get("type") == "result"
           and "assignments" in (json.loads(l).get("result") or {})]
    if not res:
        raise SystemExit("no result carrying `assignments`")
    inc = {a["model"]: a for a in res[0]["assignments"]}
    rd = readings(s["prompt"][:26]); full = rd[s["full_n"]]
    #: WHERE THE FULL RUN PUT EACH NEW LINEAGE, as the standard.
    std = {}
    for op in full["operations"]:
        for m in op["members"]:
            std[m["model"]] = ("op", op["name"])
    for x in full["reversed"]:
        std[x["model"]] = ("rev", x["operation"])
    for x in full["unassigned"]:
        std[x["model"]] = ("none", "")
    print("INCREMENTAL (%d-lineage legend + %d new) vs FULL %d-lineage reading\n"
          % (s["base_n"], len(s["new_models"]), s["full_n"]))
    print("  %-28s %-22s %s" % ("model", "incremental", "full run"))
    agree = same_kind = 0
    for m in s["new_models"]:
        a = inc.get(m)
        if a is None:
            print("  %-28s %-22s MISSING FROM INCREMENTAL" % (m[:28], "--")); continue
        v = a["verdict"].strip()
        kind = ("rev" if v.upper().startswith("REVERSED") else
                "none" if v.upper() == "NONE" else
                "new" if v.upper() == "NEW" else "op")
        sk, sn = std.get(m, ("?", ""))
        ok = (kind == sk) or (kind == "new" and sk == "op")
        same_kind += (kind == sk)
        agree += ok
        print("  %-28s %-22s %s%s" % (m[:28], v[:22], sk + (" " + sn[:26] if sn else ""),
                                      "" if kind == sk else "   <-- differs"))
    n = len(s["new_models"])
    print("\n  same verdict KIND: %d of %d (%.0f%%)" % (same_kind, n, 100*same_kind/n))
    print("  compatible (counting NEW as a legitimate refusal): %d of %d (%.0f%%)"
          % (agree, n, 100*agree/n))
    print("\n  A high placement rate with LOW agreement would be the anchoring failure:")
    print("  eleven lineages forced into three legend operations.")


SCRIPT = """// GENERATED by incremental.py.
export const meta = { name: 'incr-%(slug)s',
  description: 'Extend a cross-lineage reading with new lineages',
  phases: [{ title: 'Extend' }] }
const r = await agent(`Read the file %(path)s with the Read tool.\\n\\nIts entire ` +
  `content is a task addressed to you. Follow it exactly. Do not read any other ` +
  `file, do not run any command.\\n\\nReturn your answer by calling StructuredOutput.`,
  { label: 'incr', phase: 'Extend', schema: %(schema)s,
    model: %(model)s, effort: %(effort)s })
return { n: r.assignments.length,
  verdicts: r.assignments.map((a) => `${a.model}: ${a.verdict}`) }
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prepare", metavar="PROMPT_PREFIX")
    ap.add_argument("--ingest", metavar="RUN_ID"); ap.add_argument("--slug")
    a = ap.parse_args()
    if a.prepare: prepare(a.prepare)
    elif a.ingest: ingest(a.ingest, a.slug)
    else: ap.print_help()
