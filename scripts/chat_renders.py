#!/usr/bin/env python
"""What each checkpoint's chat template ACTUALLY RENDERS. -> roster/models/chat_renders.json

    python scripts/chat_renders.py            classify every model in the framed store
    python scripts/chat_renders.py --all      every model in the roster
    python scripts/chat_renders.py --show     print the table, write nothing

## WHY THIS FILE EXISTS

**The tokenizers have been "checked" many times and the answer was never written
down.** Each check loaded ~50 tokenizers, rendered a probe, printed a verdict to
a terminal, and threw it away -- so the next question about templates started
from zero. RH, 2026-09-03. This is that check with an artifact on the end.

## THE DISTINCTION IT RECORDS, WHICH `system_mode` DOES NOT

`twp_cells_v4.system_mode` records THE ARGUMENT PASSED (`empty` / `default`).
It does not record THE TREATMENT RECEIVED, and the two disagree in both
directions:

    Qwen2.5-7B-Instruct   system_mode=empty    renders 151 ch WITH a system turn
    salamandra-7b-instr   system_mode=empty    renders 1491 ch WITH a system turn
    gemma-2-9b-it         system_mode=default  renders 63 ch, NO system turn
    glm-4-9b-chat-hf      system_mode=default  renders 37 ch, NO system turn

So "restrict to prefill/empty" does not give a population with an empty system
slot, and "exclude default" throws away models that have one. The only sound
predicate is on the RENDERED STRING, which is what this file stores.

## WHY THE STRING AND NOT JUST A HASH

`twp_cells_v4.render_sha` is `sha256[:16]` of the rendered prompt and the string
itself is not persisted anywhere (runners.py:751, confirmed by malign [6625]).
A hash proves two renders differ; it cannot say WHAT either was, so it cannot
answer "does this render carry a system turn". Storing the probe render costs a
few KB and answers it forever.

The stored `probe_sha` is over the PROBE render, not over any cell -- the two are
different strings because a cell's render carries its own prompt. It is here so a
later run can tell whether a template changed under it.

## THE PROBE IS FIXED AND BORING ON PURPOSE

One user turn containing "Hi." Anything longer risks the template branching on
content; anything shorter risks an empty-message special case. The question is
what SCAFFOLD the model gets, not what it says about the content.

## TWO VENVS, BECAUSE NO SINGLE `transformers` LOADS THE ROSTER

15 tokenizers refuse to load under the default venv -- every OLMo/OLMoE/Olmo-3
and the Falcon-H1s. `scripts/venvs.py which MODEL` names the venv a checkpoint
needs; this script records `venv` per row and reports what it could not load, so
a partial classification is visibly partial rather than quietly short.

Run it once per venv and the rows merge on `model`:

    .venv/bin/python scripts/chat_renders.py
    .venv-tf457/bin/python scripts/chat_renders.py
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT = os.path.join(ROOT, "roster", "models", "chat_renders.json")
TPL = os.path.join(ROOT, "roster", "models", "chat_templates.json")

#: one user turn, no content the template can branch on. See the docstring.
PROBE = [{"role": "user", "content": "Hi."}]
PROBE_EMPTY = [{"role": "system", "content": ""},
               {"role": "user", "content": "Hi."}]


def _authored():
    if not os.path.exists(TPL):
        return {}
    d = json.load(open(TPL, encoding="utf-8"))
    out = {}
    for k, v in d.items():
        if k.startswith("_"):
            continue
        out[k] = v if isinstance(v, str) else (v or {}).get("template")
    return out


def classify(model_id, authored):
    """-> dict for one model, or None if the tokenizer will not load here."""
    from transformers import AutoTokenizer
    try:
        tk = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    except Exception as e:
        return {"model": model_id, "error": type(e).__name__,
                "error_detail": str(e)[:160]}
    src = "shipped"
    if not getattr(tk, "chat_template", None):
        t = authored.get(model_id)
        if not t:
            return {"model": model_id, "template": None, "source": "none"}
        tk.chat_template = t
        src = "authored"
    try:
        render = tk.apply_chat_template(PROBE, add_generation_prompt=True,
                                        tokenize=False)
    except Exception as e:
        return {"model": model_id, "source": src, "error": type(e).__name__,
                "error_detail": str(e)[:160]}
    #: can the template carry an EXPLICITLY EMPTY system message, and does it
    #: survive? `generate.py:316`'s byte test: if it renders the same as bare,
    #: the message had no effect and the writer refuses the cell.
    try:
        r_empty = tk.apply_chat_template(PROBE_EMPTY, add_generation_prompt=True,
                                         tokenize=False)
        empty_state = ("distinct" if r_empty != render else "discarded")
    except Exception as e:
        empty_state = "refused:%s" % type(e).__name__
        r_empty = None
    low = render.lower()
    return {
        "model": model_id,
        "source": src,
        "render": render,
        "render_len": len(render),
        "probe_sha": hashlib.sha256(render.encode("utf-8")).hexdigest()[:16],
        #: THE PREDICATE. `<<SYS>>` is Llama-2's marker and contains no ascii
        #: "system", so a substring test alone misses it.
        "has_system_turn": ("system" in low) or ("<<SYS>>" in render),
        "empty_system": empty_state,
        "venv": os.path.basename(os.path.dirname(os.path.dirname(sys.executable))),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="every roster model, not just the framed ones")
    ap.add_argument("--show", action="store_true", help="print, write nothing")
    a = ap.parse_args(argv)

    from malignment import ch
    if a.all:
        from malignment import roster
        ep, _ = roster.endpoints()
        models = sorted(set(list(ep) + list(ep.values())))
    else:
        models = [r["model"] for r in ch.query(
            "SELECT DISTINCT model FROM twp_cells_v4 WHERE frame='prefill' "
            "ORDER BY model")]

    authored = _authored()
    #: MERGE, never overwrite. A second venv classifies what the first could
    #: not, and a run that replaced the file would delete its sibling's rows.
    old = {}
    if os.path.exists(OUT):
        old = {r["model"]: r for r in json.load(open(OUT, encoding="utf-8"))
               .get("models", [])}

    new, failed = dict(old), []
    for m in models:
        r = classify(m, authored)
        if r.get("error"):
            failed.append((m, r["error"]))
            #: keep a GOOD earlier row rather than replacing it with a failure
            if m in old and not old[m].get("error"):
                continue
        new[m] = r

    rows = [new[k] for k in sorted(new)]
    ok = [r for r in rows if r.get("render") is not None]
    clean = [r for r in ok if not r["has_system_turn"]]
    print("%-38s %-9s %6s %-10s %s" % ("model", "source", "chars",
                                       "empty", "system turn?"))
    for r in rows:
        if r.get("error"):
            print("%-38s %-9s %6s %-10s %s" % (r["model"].split("/")[-1][:38],
                  r.get("source", "-"), "-", "-", "LOAD FAIL " + r["error"]))
            continue
        if r.get("render") is None:
            print("%-38s %-9s %6s %-10s %s" % (r["model"].split("/")[-1][:38],
                  "none", "-", "-", "no template anywhere"))
            continue
        print("%-38s %-9s %6d %-10s %s" % (
            r["model"].split("/")[-1][:38], r["source"], r["render_len"],
            r["empty_system"], "HAS system turn" if r["has_system_turn"] else "clean"))
    print()
    print("classified %d | clean (no system turn) %d | could not load %d"
          % (len(ok), len(clean), len(failed)))
    if failed:
        print("  not loadable in this venv -- try the other:")
        for m, e in failed:
            print("     %-46s %s" % (m, e))

    if a.show:
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "_about": ("What each checkpoint's chat template RENDERS for a fixed "
                   "one-turn probe. `has_system_turn` is the predicate a framed "
                   "analysis should use; twp_cells_v4.system_mode records the "
                   "ARGUMENT PASSED and disagrees with the treatment received in "
                   "both directions. Produced by scripts/chat_renders.py."),
        "_probe": PROBE,
        "models": rows,
    }, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\nwrote %s (%d models)" % (OUT, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
