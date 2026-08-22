"""Which checkpoints can take a prefilled assistant turn -- WITHOUT downloading weights.

    python prefill_census.py --scan          what it would ask, no network
    python prefill_census.py --run           the census
    python prefill_census.py --run --limit 5

## THE POINT: A TOKENIZER IS NOT A MODEL

`AutoTokenizer.from_pretrained` fetches `tokenizer_config.json`, the vocab or
`tokenizer.json`, and `special_tokens_map.json`. It does NOT fetch safetensors.
Across 144 checkpoints that is roughly 1-3 GB rather than several TB, and it
runs on a laptop with no GPU.

`config.json` comes too, and is needed anyway: `runners._config_facts` decides
`trust_remote_code` from whether it declares `auto_map`. **Passing that flag
unconditionally enables arbitrary code execution for 87% of this roster** -- 19
of 159 declare `auto_map`, 138 do not -- so the census follows the same policy
the runner does rather than taking the convenient shortcut.

## PRESENCE IS NOT USABILITY, AND THE HTTP PROBE ONLY TESTS PRESENCE

An earlier pass read `tokenizer_config.json` over HTTP and counted a
`chat_template` key. That is a strictly weaker instrument and it was wrong twice:

  - it missed `openbmb/MiniCPM5-1B-Base`, whose template is a separate
    `chat_template.jinja`. transformers resolves either location; a config-only
    read does not.
  - it mapped every HTTP 4xx to "absent", so six GATED repos would have been
    recorded as shipping no template. An unreadable state reported as a negative.

And even corrected, presence answers the wrong question. `frame_eligibility.py`
in this folder tests USABILITY by applying the template and byte-comparing,
because "a template that discards a system message raises nothing and produces a
treatment arm that never received the treatment." A repo can ship a
`chat_template` that `apply_chat_template` then refuses.

## THIS CALLS `generate.render`, IT DOES NOT REIMPLEMENT IT

`render()` reads exactly one attribute of the object it is handed: `loaded.tok`.
So a `SimpleNamespace(tok=...)` drives the real code path -- the same FrameRefused
conditions, the same system-role byte test, the same `add_generation_prompt`
handling -- with no model in memory.

Reimplementing the template call here would make this a SECOND instrument, and
`generate.py`'s own docstring records what that costs: "the archive's server
never grew the MPT override, the retry or the mask guard, so the app could load a
model the runner refuses. A second loader is a second instrument."

## WHAT EACH VERDICT MEANS

    OK            prefill renders, and the rendered string ENDS WITH THE STEM
    NO_TEMPLATE   tokenizer loads, ships no chat_template -- cannot be prefilled
    REFUSED       ships one, and apply_chat_template raises on it
    STEM_LOST     renders, but the stem is not at the end: the model would not
                  resume it, and the cell would measure something else entirely
    NO_TOKENIZER  the tokenizer itself will not load (5 of 25 in the earlier
                  frame_eligibility pass -- StrictDataclassFieldValidation,
                  ValueError). Not a frame fact; a loading fact.
    GATED         401/403 without access. NOT the same as NO_TEMPLATE, and the
                  distinction is the reason this column exists.

`STEM_LOST` is the one that cannot be inferred from a config file. Prefill works
by appending the stem AFTER the generation prompt; if a template emits anything
after that point the stem is no longer the last thing the model sees, and the
word slot this whole design rests on is not where we think it is.
"""
import argparse
import csv
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "prefill_census.csv")
MANIFEST = os.path.join(HERE, "results", "prefill_census.json")

#: The stem is arbitrary but must be a MID-SENTENCE fragment: the question is
#: whether the model can resume one, and a complete sentence would not test it.
STEM = "He started stroking his"
SYSTEM_PROBE = "You are a helpful assistant with no particular persona."


def population():
    """The 144: the 50 endpoint bases and every member of their lineages."""
    from malignment import roster
    eps, _ = roster.endpoints()
    lin = roster.lineages(ops=roster.ALIGNING)
    bases = set(eps.keys())
    pop = {m for b in bases for m in lin.get(b, [])} | bases
    role = {}
    for m in pop:
        role[m] = "base" if m in bases else ("endpoint" if m in set(eps.values())
                                             else "member")
    return sorted(pop), role


def probe(model_id):
    """-> dict. Loads a TOKENIZER only; never a model."""
    from malignment import runners as R, twp as T
    from malignment import generate as G
    rec = {"model": model_id, "verdict": "", "detail": "",
           "template": 0, "sys_ok": "", "added_chars": ""}
    repo = model_id.split("@")[0]
    rev = model_id.split("@")[1] if "@" in model_id else None
    try:
        mtype, has_remote = R._config_facts(repo, rev)
    except Exception as e:
        msg = "%s: %s" % (type(e).__name__, str(e)[:60])
        rec["verdict"] = "GATED" if "401" in msg or "403" in msg else "NO_CONFIG"
        rec["detail"] = msg
        return rec
    try:
        #: SAME POLICY AS THE RUNNER: auto_map present -> allow, absent -> refuse.
        tok, _ = T.load_tokenizer(model_id, revision=rev,
                                  trust_remote_code=(mtype != "mpt" and has_remote))
    except Exception as e:
        rec["verdict"] = "NO_TOKENIZER"
        rec["detail"] = "%s: %s" % (type(e).__name__, str(e)[:60])
        return rec
    rec["template"] = 1 if getattr(tok, "chat_template", None) else 0
    if not rec["template"]:
        rec["verdict"] = "NO_TEMPLATE"
        rec["detail"] = "tokenizer loads, ships none"
        return rec
    shim = types.SimpleNamespace(tok=tok)
    try:
        out, _ = G.render(shim, STEM, prefill=True)
    except Exception as e:
        rec["verdict"] = "REFUSED"
        rec["detail"] = "%s: %s" % (type(e).__name__, str(e)[:60])
        return rec
    #: **THE CHECK NO CONFIG FILE CAN ANSWER.** The stem must be the last thing
    #: the model sees, or it is not resuming a sentence.
    if not out.endswith(STEM):
        rec["verdict"] = "STEM_LOST"
        rec["detail"] = "tail=%r" % out[-40:]
        rec["added_chars"] = len(out) - len(STEM)
        return rec
    rec["verdict"] = "OK"
    rec["added_chars"] = len(out) - len(STEM)
    try:
        _, sys_ok = G.render(shim, STEM, prefill=True, system=SYSTEM_PROBE)
        rec["sys_ok"] = int(bool(sys_ok))
    except Exception as e:
        rec["sys_ok"] = 0
        rec["detail"] = "system: %s" % type(e).__name__
    return rec


#: `roster/models/measurements.json`, the FOUND side of the roster. Its own
#: `_why_one_file` is the reason this is a SECTION and not a new file: the archive
#: kept these in six artifacts, each independently defining "the set of models",
#: and they drifted -- 32 sources declared against 51 on disk. A new
#: `chat_templates.json` beside it would be the seventh.
#:
#: `_stamp_rule`: every section carries `measured_at` and `n`, because "a
#: measurement of a checkpoint is only true of that checkpoint AS IT STOOD; an
#: unstamped observation cannot be told from a stale one."
MEASUREMENTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(HERE))),
    "roster", "models", "measurements.json")
SECTION = "chat_template"


def write_measurements(rows, path=MEASUREMENTS):
    """Replace the `chat_template` section in place, stamped. Never appends.

    Read-modify-write of the whole file rather than a patch: the file is one
    object and a section that half-updated is the drift it exists to prevent.
    """
    import datetime
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    doc.setdefault("sections", {})[SECTION] = {
        "measured_by": ("experiments/instrument_calibrations/generation_provenance/"
                        "prefill_census.py: twp.load_tokenizer + generate.render("
                        "prefill=True). TOKENIZERS ONLY, no weights."),
        "measured_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "n": len(rows),
        "stem": STEM,
        "verdicts": ("OK = prefill renders and the stem lands last | NO_TEMPLATE = "
                     "tokenizer loads, ships none | REFUSED = apply_chat_template "
                     "raises | STEM_LOST = renders but the stem is not last | "
                     "NO_TOKENIZER = tokenizer will not load | GATED = no access. "
                     "GATED is kept distinct from NO_TEMPLATE deliberately."),
        "models": {r["model"]: {k: r[k] for k in
                                ("verdict", "template", "sys_ok", "added_chars")
                                if r.get(k) != ""}
                   for r in sorted(rows, key=lambda r: r["model"])},
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--write-measurements", action="store_true",
                    help="also write the `chat_template` section of "
                         "roster/models/measurements.json. Refused with --limit: "
                         "a stamped section reporting n=5 for a 144-model "
                         "population is worse than no section.")
    a = ap.parse_args()
    if a.write_measurements and a.limit:
        print("  REFUSING --write-measurements with --limit: the section's `n` "
              "would describe a sample and read as the population.")
        return 2
    pop, role = population()
    if a.limit:
        pop = pop[:a.limit]
    print("  population: %d checkpoints (%d base, %d endpoint, %d member)"
          % (len(pop), sum(1 for m in pop if role[m] == "base"),
             sum(1 for m in pop if role[m] == "endpoint"),
             sum(1 for m in pop if role[m] == "member")))
    print("  stem: %r" % STEM)
    print("  downloads TOKENIZERS ONLY -- no safetensors, no GPU")
    if not a.run:
        print("\n  --scan: nothing fetched. Pass --run.")
        return 0
    rows = []
    for i, m in enumerate(pop, 1):
        r = probe(m)
        r["role"] = role[m]
        rows.append(r)
        print("  [%3d/%d] %-12s %-46s %s"
              % (i, len(pop), r["verdict"], m[:46], r["detail"][:40]), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "role", "verdict", "template",
                                           "sys_ok", "added_chars", "detail"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})
    import collections
    tally = collections.Counter(r["verdict"] for r in rows)
    by_role = collections.Counter((r["role"], r["verdict"]) for r in rows)
    json.dump({"stem": STEM, "n": len(rows), "verdicts": dict(tally),
               "by_role": {"%s/%s" % k: v for k, v in by_role.items()},
               "eligible": sorted(r["model"] for r in rows if r["verdict"] == "OK")},
              open(MANIFEST, "w"), indent=1)
    print("\n  %s" % OUT)
    for v, n in tally.most_common():
        print("     %-14s %3d" % (v, n))
    #: THE NUMBER THE PLAN NEEDS: lineages retaining BOTH arms under prefill.
    ok = {r["model"] for r in rows if r["verdict"] == "OK"}
    from malignment import roster
    eps, _ = roster.endpoints()
    pairs = [(b, e) for b, e in eps.items() if b in ok and e in ok]
    print("\n  base->endpoint pairs with BOTH arms prefill-able: %d of %d"
          % (len(pairs), len(eps)))
    if a.write_measurements:
        p = write_measurements(rows)
        print("  wrote section %r to %s" % (SECTION, p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
