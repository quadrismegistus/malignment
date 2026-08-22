#!/usr/bin/env python
"""Which mined chatlog findings the record does NOT already cover.

    python scripts/mine_diff.py FINDINGS.json
    python scripts/mine_diff.py FINDINGS.json --new        only the uncovered
    python scripts/mine_diff.py FINDINGS.json --kind kernel

The half of the chatlog sweep that makes it repeatable. Mining alone produces
147 findings of which most are already known; run monthly, that is 147 things to
re-read every time. Diffed against the record it produces only what is new, and
**it gets quieter as the record gets better** -- the only part of this system
with that property.

## THE AGENT'S `already_recorded` IS A GUESS. THIS IS THE CHECK.

Each mining agent returned a self-assessment: 72 `no`, 54 `yes`, 21 `unknown`
out of 147. That field is the agent's impression from reading transcripts, not a
lookup, and an agent that has just read a long argument ABOUT a fact is the
worst-placed judge of whether the fact was ever written down. Everything here is
resolved against the actual files.

## WHAT "COVERED" MEANS, STATED NARROWLY BECAUSE IT IS WEAK

Covered means **the record holds a fact of that KIND for that MODEL** -- not
that it holds the same fact. A model with any `load_failed` observation covers a
mined `load_failed`, even about a different cause.

That is deliberately weak, and the alternative is worse. Matching the mined
prose against the recorded prose would be a similarity score dressed as a
verdict: it would call a fact covered because the wording resembles a different
fact, and it would call a genuine duplicate new because someone rephrased it.
A weak test whose weakness is declared beats a strong-looking one that is wrong
in both directions.

So: `NEW` is a reliable signal that nothing of that kind exists, and `covered`
is a hint that something might. Read the NEW list; spot-check the covered one.

## KINDS WITH NO STRUCTURED HOME ARE REPORTED AS SUCH, NOT AS COVERED

`ruling` and `other` have no field in any roster file, so they can be neither
confirmed nor denied. Calling them covered would hide them forever; calling them
new would resurface all of them every run. They get their own bucket, which is
also the list of schema gaps still worth closing.

**AND THE FIRST VERSION PUT `engine` AND `perf` IN THAT BUCKET TOO, WRONGLY.**
Both have homes -- `observations.json::engine_support` keyed by ARCHITECTURE
(8 entries, each with a status, the last vLLM version that hosted it, and a
recovery path) and `data/model_twp_rates.jsonl` keyed by (model x device), 595
observations. Sending 25 checkable findings into a bucket labelled "no field
exists" is worse than calling them NEW: it asserts the record COULD NOT hold
them, so nobody goes looking for where it already does.
"""
import argparse
import json
import os
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

R = lambda *p: os.path.join(ROOT, "roster", "models", *p)      # noqa: E731

OUTCOME_KINDS = {"load_ok": ("load_ok", "loads", "ok"),
                 "run_ok": ("load_ok", "loads", "ok", "runs"),
                 "load_failed": ("load_failed",),
                 "run_failed": ("run_failed",)}
#: **`engine` IS NOT SCHEMA-LESS AND THE FIRST VERSION SAID IT WAS.**
#: `observations.json` carries `engine_support`, keyed by ARCHITECTURE, with
#: eight entries each naming a status, the last vLLM version that hosted it, the
#: models it covers and a recovery path -- exactly the shape those findings have.
#: Listing `engine` here sent 10 real, checkable findings into a bucket labelled
#: "no field exists", which is worse than calling them NEW: it says the record
#: COULD NOT hold them, so nobody goes looking for where it already does.
#: `perf` likewise has a home: `data/model_twp_rates.jsonl`, 595 observations
#: keyed by (model x device), which `rates.rate_for` reads and `box_guard`
#: prices a whole fleet against. Two of the four kinds I called schema-less
#: had schemas; only `ruling` and `other` genuinely do not, and `package`
#: sits half-covered by the environments' packages_present/absent lists.
NO_SCHEMA = {"ruling", "other", "package"}


def load_record():
    obs = json.load(open(R("observations.json")))
    req = {r["model"]: r for r in json.load(open(R("requirements.json")))["requirements"]}
    vw = json.load(open(R("version_windows.json")))["models"]
    meas = json.load(open(R("measurements.json")))["sections"]
    by_model = {}
    for o in obs["observations"]:
        by_model.setdefault(o["model_id"], []).append(o)
    #: engine support is keyed by ARCHITECTURE; each entry also lists the
    #: models it covers, so membership answers it without an arch lookup.
    es = obs.get("engine_support") or {}
    eng_models, eng_arch = set(), set(es)
    for v in es.values():
        for mm in ((v or {}).get("models") or []):
            eng_models.add(mm)
    arch = {k: (v or {}).get("architectures")
            for k, v in ((meas.get("config_dtype") or {}).get("models") or {}).items()}
    try:
        from malignment import rates as _rates
        _r = {}
        for o in _rates.load():
            if o.get("sec_per_cell"):
                _r.setdefault(o["model"], []).append(o["sec_per_cell"])
    except Exception:                                            # noqa: BLE001
        _r = {}
    return {"obs": by_model, "req": req, "vw": vw, "rates": _r,
            "eng_models": eng_models, "eng_arch": eng_arch, "arch": arch,
            "repos": (meas.get("repos") or {}).get("models") or {},
            "tok": (meas.get("tokenizers") or {}).get("models") or {},
            "chat": (meas.get("chat_template") or {}).get("models") or {}}


#: `org/name` as HF writes it. Ids contain no spaces, so a bare `/` inside one
#: is unambiguous and a ` / ` between two is a separator.
_ID = __import__("re").compile(r"[A-Za-z0-9][\w.-]*/[\w.\-@]+")


def resolve_models(field, rec):
    """[roster ids] named by one finding's `model` field. Often more than one.

    **THE SCHEMA ASKED FOR ONE ID AND THE AGENTS WROTE SEVERAL.** 30 of 50
    unresolved findings crammed a group into the field --
    `"baichuan-inc/Baichuan2-7B-Base / -Chat"`,
    `"inceptionai/jais-family-6p7b (and -chat)"`,
    `"gl198976/mpt-7b (also applies to gl198976/mpt-7b-instruct)"` -- which is
    a reasonable thing to write about a finding that genuinely covers a pair,
    and reading it as one literal id reported the whole group as off-roster.
    An unresolved model is indistinguishable from an un-recorded fact, so the
    parse defect showed up as 50 phantom gaps.

    Bare suffixes (`-Chat`) are resolved against the org of an id already found
    in the same field, which is the only reading that makes them meaningful.
    """
    if not field:
        return []
    ids, out = _ID.findall(field), []
    for i in ids:
        if i in rec["req"] or i in rec["obs"]:
            out.append(i)
    for org in {i.split("/")[0] for i in ids}:
        for tail in __import__("re").findall(r"(?:^|[\s(/,])(-[\w.-]+)", field):
            for cand in (org + "/" + tail.lstrip("-"),):
                if cand in rec["req"] and cand not in out:
                    out.append(cand)
        #: `(and -chat)` after `jais-family-6p7b` means that model plus a
        #: suffix, not the org plus a suffix.
        for base in [i for i in ids if i.startswith(org + "/")]:
            for tail in __import__("re").findall(r"\(\s*(?:and|also)?\s*(-[\w.-]+)",
                                                 field):
                cand = base + tail
                if cand in rec["req"] and cand not in out:
                    out.append(cand)
    return out


def covered(f, rec, model=None):
    """(verdict, why) -- 'covered' | 'NEW' | 'no-schema' | 'unknown-model'."""
    m, kind = model or f.get("model"), f.get("kind")
    if not m:
        return "NEW", "no model on the finding"
    known = m in rec["req"] or m in rec["obs"]
    if not known:
        return "unknown-model", "not in the roster (alias or a retired id)"
    if kind in NO_SCHEMA:
        return "no-schema", "`%s` has no field in any roster file" % kind
    if kind in OUTCOME_KINDS:
        want = OUTCOME_KINDS[kind]
        hits = [o for o in rec["obs"].get(m, []) if o["outcome"] in want]
        return (("covered", "%d observation(s) with outcome in %s"
                 % (len(hits), "/".join(want))) if hits
                else ("NEW", "no observation with outcome in %s" % "/".join(want)))
    if kind == "perf":
        r = rec["rates"].get(m) or []
        if r:
            return "covered", ("%d rate observation(s), median %.3f s/cell"
                               % (len(r), sorted(r)[len(r) // 2]))
        return "NEW", "no recorded rate for this model in model_twp_rates.jsonl"
    if kind == "engine":
        if m in rec["eng_models"]:
            return "covered", "named in observations.json engine_support"
        a = rec["arch"].get(m)
        if a and a in rec["eng_arch"]:
            return "covered", "architecture %s has an engine_support ruling" % a
        return "NEW", ("no engine_support entry for %s (architecture %s)"
                       % (m.split("/")[-1], a or "unknown"))
    if kind == "blocked":
        st = (rec["repos"].get(m) or {}).get("state")
        return (("covered", "repos state=%s" % st) if st and st != "public"
                else ("NEW", "repos says %s -- no block on record" % (st or "unprobed")))
    if kind == "requirement":
        pts = rec["vw"].get(m) or {}
        n = sum(len(v.get("points") or []) for v in pts.values())
        r = rec["req"].get(m) or {}
        if n or r.get("transformers"):
            return "covered", "%d version point(s); pin %s" % (n, r.get("transformers"))
        return "NEW", "no version points and no pin"
    if kind == "kernel":
        r = rec["req"].get(m) or {}
        return (("covered", "kernels=%s" % r.get("kernels")) if r.get("kernels")
                else ("NEW", "requirements declares no kernels for this model"))
    if kind == "dtype":
        r = rec["req"].get(m) or {}
        return (("covered", "compute_dtype=%s" % r.get("compute_dtype"))
                if r.get("compute_dtype")
                else ("NEW", "no compute_dtype declared"))
    if kind == "revision":
        r = rec["req"].get(m) or {}
        st = (rec["repos"].get(m) or {}).get("state")
        if r.get("revision") or r.get("revision_ladder") or st == "revision_required":
            return "covered", "revision=%s ladder=%s repos=%s" % (
                r.get("revision"), r.get("revision_ladder"), st)
        return "NEW", "no revision pin, no ladder, repo not flagged"
    if kind == "tokenizer":
        if m in rec["tok"] or m in rec["chat"]:
            return "covered", "measured in tokenizers/chat_template"
        return "NEW", "no tokenizer or chat_template measurement"
    return "no-schema", "unhandled kind %r" % kind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings", help="JSON with a top-level `findings` list")
    ap.add_argument("--new", action="store_true", help="only uncovered")
    ap.add_argument("--kind", default=None)
    ap.add_argument("--include-superseded", action="store_true")
    a = ap.parse_args()
    doc = json.load(open(a.findings))
    F = doc.get("findings") if isinstance(doc, dict) else doc
    if not a.include_superseded:
        F = [f for f in F if not f.get("superseded")]
    if a.kind:
        F = [f for f in F if f.get("kind") == a.kind]
    rec = load_record()
    rows = []
    for f in F:
        #: One finding about a PAIR is two checks, not one. Collapsing them
        #: would let a fact recorded for the base cover its aligned sibling.
        ms = resolve_models(f.get("model"), rec)
        if not ms:
            rows.append(("unresolved", "no roster id in %r" % (f.get("model") or "")[:60], f, None))
            continue
        for m in ms:
            v, why = covered(f, rec, m)
            rows.append((v, why, f, m))
    c = Counter(v for v, _w, _f, _m in rows)
    print("findings considered %d   %s" % (len(rows), dict(c)))
    #: **THE AGENT'S GUESS AGAINST THE LOOKUP.** Printed because the gap is the
    #: point: a self-assessment is not a check, and the size of the disagreement
    #: is how much the check was worth.
    dis = Counter()
    for v, _w, f, _m in rows:
        g = f.get("already_recorded")
        if g in ("yes", "no"):
            dis[("agent=%s" % g, v)] += 1
    print("agent self-assessment vs lookup: %s"
          % {"%s -> %s" % k: n for k, n in sorted(dis.items())})
    for v, why, f, m in sorted(rows, key=lambda r: (r[0] != "NEW", r[2].get("kind") or "")):
        if a.new and v != "NEW":
            continue
        print("\n%-13s %-10s %s" % (v, f.get("kind"), m or f.get("model")))
        print("   %s" % (f.get("statement") or "")[:150])
        print("   why: %s" % why)
        if f.get("environment"):
            print("   env: %s" % f["environment"][:110])
        if f.get("recency"):
            print("   when: %s" % f["recency"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
