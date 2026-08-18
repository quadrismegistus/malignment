"""Prepare inputs for a taxonomy workflow, and ingest what comes back.

    python run.py --prepare --frames union stroking --pairs llama smol
    python run.py --ingest  wf_ba79d894-172
    python run.py --list

## WHY A PREPARE/INGEST SPLIT AND NOT ONE SCRIPT

The coding is done by a workflow, which is a good fit while the instrument is
still moving: change the prompt, rerun, read the result. What a workflow does not
give is an artifact -- the transcripts are on disk under
`~/.claude/projects/.../subagents/workflows/<run>/`, keyed by an agent id nobody
chose, and the identity of the cell being coded survives only as a filename
mentioned inside the prompt text.

So this file owns both ends. `--prepare` writes the input JSONs AND a manifest
recording what each one is; `--ingest` reads a finished run's transcripts and
joins on that manifest. Recovering identity by regex over a prompt would work
today and break the first time the prompt wording changes.

## THE STASH, AND THE TRAP IN IT

`checkpoint.py`'s note, which this file inherits: **a bare `root_dir` silently
resolves to `~/.cache/hashstash/`**. Always absolute. `_stash()` asserts where it
actually landed rather than trusting the option, which is the guard `slot_axis`
learned after pinning options that were not honoured and never finding out.

    engine   jsonl    committable, diffable, greppable
    flat     True     one file, not a tree
    key      a DICT   {instrument, frame, base, aligned, orientation, rater}

A dict key is the point: runs from different workflows, instrument versions and
orientations land in one stash and stay addressable. Re-ingesting the same run is
idempotent -- same key, same value.

## WHAT IS STORED

Everything needed to audit a coding without the workflow:

    prompt     the FULL text the rater received, verbatim
    model      the model that actually answered, read from the transcript
    result     the structured object returned
    run_id     the workflow run, so the transcript can be found again
    agent_id   which agent within it

The prompt is stored per record rather than once per run because the instrument
changes between runs and a record whose prompt must be reconstructed from a
version number is a record that will eventually be reconstructed wrongly.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STASH_DIR = os.path.join(HERE, "results", "stash")
INPUT_DIR = os.path.join(HERE, "results", "inputs")
MANIFEST = os.path.join(INPUT_DIR, "manifest.json")
INSTRUMENT_LABEL = "v3"


def instrument_id(prompt):
    """Stable id for the PROMPT ACTUALLY SENT, not for a version anyone typed.

    `INSTRUMENT_LABEL` is hand-maintained and therefore drifts: edit
    INSTRUMENT.md, forget to bump the constant, and records get stamped with a
    version they were not produced under. The campaign has already paid for that
    class of error -- `k_bulk.py` records ratings moving when a scale set changed,
    and the same frame scored 0.714 and 1.500 under two prompt versions in one
    evening.

    So identity is a hash of the prompt text itself. Two runs sharing a prompt
    share a namespace automatically; a changed prompt gets a new one whether or
    not anyone remembered. A rule that executes rather than one to be recalled.

    NORMALISED FIRST, because the raw prompt carries the input path and the
    manifest name, which differ per cell and per machine and are not part of the
    instrument. What survives normalisation is the template. Note this works
    only because the fragment and word table are NOT in the prompt -- the agent
    is told to read them from a file -- so the prompt IS the template already.
    """
    t = re.sub(r'\S*\.json', '<INPUT>', prompt or '')
    t = re.sub(r'\s+', ' ', t).strip()
    return hashlib.sha256(t.encode('utf-8')).hexdigest()[:12]

PAIRS = {
    "llama": ("meta-llama/Llama-3.1-8B", "meta-llama/Llama-3.1-8B-Instruct"),
    "smol": ("HuggingFaceTB/SmolLM3-3B-Base", "HuggingFaceTB/SmolLM3-3B"),
    "gemma": ("google/gemma-2-9b", "google/gemma-2-9b-it"),
    "qwen3": ("Qwen/Qwen3-8B-Base", "Qwen/Qwen3-8B"),
    "yi": ("01-ai/Yi-1.5-9B", "01-ai/Yi-1.5-9B-Chat"),
}


def _stash():
    """The taxonomy stash. ABSOLUTE root_dir, and the resolution is checked.

    A bare name goes to ~/.cache/hashstash and nothing says so. And an option
    that is not honoured resolves somewhere else silently -- slot_axis pinned
    lz4 without it installed, landed elsewhere, and its guard could never fire
    because it tested for a directory that always exists. So compare against
    hashstash's own answer for where it put things.
    """
    from hashstash import HashStash
    os.makedirs(STASH_DIR, exist_ok=True)
    st = HashStash(root_dir=STASH_DIR, engine="jsonl", flat=True)
    got = os.path.basename(getattr(st, "path_dirname", "") or "")
    if "jsonl" not in got:
        print("run.py: stash resolved to %r, expected a jsonl store. Records are "
              "NOT going where you think." % (got or "?"), file=sys.stderr)
    return st


def _table(m, risers, fallers):
    """The v3 two-block format. ` -> ` as separator, never a bare `>`."""
    def block(ws):
        return "\n".join(
            "  %-12s %5.1f%% -> %5.1f%%  (%+5.1f)"
            % (w, 100 * m.pre.get(w, 0.0), 100 * m.post.get(w, 0.0), 100 * m.delta[w])
            for w in ws)
    return "HIGHER UNDER B\n%s\n\nHIGHER UNDER A\n%s" % (block(risers), block(fallers))


def prepare(frames, pair_names, orientations):
    from malignment import vectors as V
    from malignment.movement import movement, CANONICAL
    from malignment.slots import read_items, corpora

    items = {d["prompt"]: d for _, p in corpora() for d in read_items(p)}
    os.makedirs(INPUT_DIR, exist_ok=True)
    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}

    for fid, prefix in frames.items():
        hit = [p for p in items if p.startswith(prefix)]
        if not hit:
            print("no frame matching %r" % prefix, file=sys.stderr)
            continue
        prompt = hit[0]
        for pn in pair_names:
            b, a = PAIRS[pn]
            rows = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                          "FROM twp_words_v4 WHERE prompt={p:String} AND model IN "
                          "{ms:Array(String)} GROUP BY model", p=prompt, ms=[b, a])
            W = {r["model"]: dict(zip(r["ws"], r["ps"])) for r in rows}
            if b not in W or a not in W:
                print("skip %s/%s: arm missing in twp_words_v4" % (fid, pn), file=sys.stderr)
                continue
            R = {r["model"]: r["total"] for r in V.rows(
                "SELECT model, total FROM twp_cells_v4 WHERE prompt={p:String} "
                "AND model IN {ms:Array(String)}", p=prompt, ms=[b, a])}
            m = movement(W[b], W[a], CANONICAL,
                         residual_pre=R.get(b), residual_post=R.get(a))
            ris = sorted(m.risers, key=lambda w: -m.delta[w])
            fal = sorted(m.fallers, key=lambda w: m.delta[w])
            for o in orientations:
                #: REVERSED is not a different measurement, it is the same one
                #: read the other way: the blocks swap and the sign flips. With
                #: the conditions unlabelled a rater cannot tell, so a relation
                #: that survives reversal is not an artifact of knowing which
                #: direction the change runs.
                if o == "rev":
                    class _Flip:
                        pre, post = m.post, m.pre
                        delta = {w: -v for w, v in m.delta.items()}
                    tbl = _table(_Flip, fal, ris)
                else:
                    tbl = _table(m, ris, fal)
                name = "%s__%s__%s" % (fid, pn, o)
                json.dump({"fragment": prompt + " ___", "word_table": tbl},
                          open(os.path.join(INPUT_DIR, name + ".json"), "w"), indent=1)
                man[name] = {"instrument_label": INSTRUMENT_LABEL, "frame": fid, "prompt": prompt,
                             "pair": pn, "base": b, "aligned": a, "orientation": o,
                             "n_higher_b": len(ris), "n_higher_a": len(fal)}
                print("%-34s %2d higher-B  %2d higher-A" % (name, len(ris), len(fal)))
    json.dump(man, open(MANIFEST, "w"), indent=1)
    print("\nmanifest: %d entries -> %s" % (len(man), MANIFEST))


def _transcripts(run_id):
    base = os.path.expanduser("~/.claude/projects")
    hits = glob.glob(os.path.join(base, "*", "*", "subagents", "workflows", run_id))
    if not hits:
        raise SystemExit("no transcript dir for %r under %s" % (run_id, base))
    return hits[0]


def ingest(run_id, rater):
    man = json.load(open(MANIFEST))
    d = _transcripts(run_id)
    st = _stash()
    n = 0
    seen_instruments = {}
    for f in sorted(glob.glob(os.path.join(d, "agent-*.jsonl"))):
        lines = [json.loads(l) for l in open(f)]
        first = lines[0].get("message", {}).get("content")
        text = first if isinstance(first, str) else " ".join(
            x.get("text", "") for x in (first or []) if isinstance(x, dict))
        #: The manifest name appears in the prompt as `<dir>/<name>.json`. Match
        #: against manifest KEYS rather than parsing a path, so a changed input
        #: directory does not break the join.
        hit = [k for k in man if "/%s.json" % k in text or " %s.json" % k in text]
        if len(hit) != 1:
            print("skip %s: matched %d manifest entries" % (os.path.basename(f), len(hit)),
                  file=sys.stderr)
            continue
        model = next((r["message"].get("model") for r in lines
                      if r.get("type") == "assistant" and r.get("message")), None)
        result = None
        for r in reversed(lines):
            if r.get("type") != "assistant":
                continue
            c = r.get("message", {}).get("content") or []
            for blk in (c if isinstance(c, list) else []):
                if blk.get("type") == "tool_use" and "StructuredOutput" in str(blk.get("name", "")):
                    result = blk.get("input")
            if result:
                break
        meta = dict(man[hit[0]])
        #: The key carries the HASH of the prompt that was actually sent; the
        #: human label rides in the value. A record can therefore be wrong about
        #: its label and still be correctly addressed.
        iid = instrument_id(text)
        key = {"instrument": iid, "frame": meta["frame"],
               "base": meta["base"], "aligned": meta["aligned"],
               "orientation": meta["orientation"], "rater": rater}
        st[key] = {"prompt": text, "model": model, "result": result,
                   "instrument_label": meta.get("instrument_label"),
                   "run_id": run_id, "agent_id": os.path.basename(f)[6:-6],
                   "meta": meta}
        seen_instruments.setdefault(iid, meta.get("instrument_label"))
        n += 1
        print("%-34s rater=%d model=%s %s" % (hit[0], rater, model,
                                              "OK" if result else "NO RESULT FOUND"))
    print("\ningested %d records into %s" % (n, STASH_DIR))
    for iid, lab in seen_instruments.items():
        print("  instrument %s  (labelled %s)" % (iid, lab))
    if len(seen_instruments) > 1:
        print("  NOTE: this run used more than one prompt. That is not an error, "
              "but records under different instrument ids are not poolable.",
              file=sys.stderr)


def listing():
    st = _stash()
    ks = list(st.keys())
    print("%d records in %s" % (len(ks), STASH_DIR))
    labs = {}
    for k in ks:
        labs.setdefault(k.get("instrument"), (st[k] or {}).get("instrument_label"))
    for iid, lab in labs.items():
        print("  instrument %s = %s" % (iid, lab))
    print()
    for k in sorted(ks, key=lambda k: (k.get("frame", ""), k.get("aligned", ""), k.get("orientation", ""))):
        v = st[k]
        r = (v or {}).get("result") or {}
        rel = r.get("relations") or []
        print("  %-12s %-10s %-30s %-4s r%-2s %-8s %s"
              % (k.get("instrument"), k.get("frame"),
                 (k.get("aligned") or "").split("/")[-1],
                 k.get("orientation"), k.get("rater"), r.get("confidence", "?"),
                 " | ".join(x.get("name", "?") for x in rel)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--ingest", metavar="RUN_ID")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--rater", type=int, default=1)
    ap.add_argument("--pairs", nargs="+", default=["llama"])
    ap.add_argument("--orientations", nargs="+", default=["fwd"])
    ap.add_argument("--frames", nargs="+", default=["union"])
    a = ap.parse_args(argv)

    KNOWN = {
        "union": "Management learned that she had been talking to a union organizer",
        "stroking": "He started stroking his",
        "office": "They called him into the office on a Friday afternoon",
        "bailiffs": "The bailiffs came to carry out the eviction",
        "unzipped": "She unzipped his",
    }
    if a.prepare:
        prepare({f: KNOWN.get(f, f) for f in a.frames}, a.pairs, a.orientations)
    elif a.ingest:
        ingest(a.ingest, a.rater)
    elif a.list:
        listing()
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
