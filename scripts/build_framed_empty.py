#!/usr/bin/env python
"""The endpoint lineages whose aligned model can receive NO system context, and has prefill
cells in that state. -> roster/models/populations/framed_empty.json

    python scripts/build_framed_empty.py            # print, write nothing
    python scripts/build_framed_empty.py --write

Read by `roster.population("framed_empty")`. RH, 2026-09-25: "is there an easy way to get
those 40 so we don't forget".

WHY BY THE RENDER AND NOT THE LABEL. `system_mode` records what was PASSED. On 14 endpoints
"" renders byte-identically to the template's default, so their 'default' cells are empty
cells under another label; on others a template injects text whatever is passed.
`movement.clean_frame_pairs()` checks only the system SLOT and so admits templates whose
preamble sits outside it ("A chat between a curious user and an artificial intelligence
assistant..."). Here the prefill prompt (user "Hi.") is rendered through the template the
cells used -- the tokenizer's, else the roster's authored override -- and EVERYTHING before
the user turn is read.

THE RULE. With the tokenizer's special tokens removed, what precedes the user's "Hi." must be
at most MARKER_CHARS characters of non-whitespace (role labels such as "user", "USER:",
"Bob:", "### 指示:", "[INST]"). Longer residue is preamble or system content, and the
lineage is excluded with the residue recorded. The residue is kept for every lineage, so the
rule can be audited by reading it, not trusted.

CELLS. A lineage enters only if `twp_cells_v4` holds frame='prefill' cells at a system_mode
whose render is the clean one: 'empty' where present, else 'default' when "" and default
render byte-identically (or the template has no system role). Legacy blank-mode rows are
never used. `system_mode` for each lineage is recorded, so a consumer reads the right cells.
"""
import argparse, json, os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "roster", "models", "populations", "framed_empty.json")
MARKER_CHARS = 20


def modes():
    q = ("SELECT model, groupUniqArray(system_mode) m FROM twp_cells_v4 "
         "WHERE frame='prefill' GROUP BY model FORMAT JSONEachRow")
    out = subprocess.run(["clickhouse", "client", "-d", "malignment", "-q", q],
                         capture_output=True, text=True, check=True).stdout
    return {r["model"]: set(r["m"]) for r in map(json.loads, out.splitlines())}


def render_state(model):
    """-> dict: template source, residue before the user turn, and whether "" == default."""
    from types import SimpleNamespace
    from transformers import AutoTokenizer
    from malignment import generate as G
    from malignment.runners import _chat_template_override
    from malignment.vllm_generate import _trust
    tok = AutoTokenizer.from_pretrained(model, trust_remote_code=_trust(model))
    src = "tokenizer"
    if not getattr(tok, "chat_template", None):
        o = _chat_template_override(model)
        if not o:
            return {"template": None}
        tok.chat_template, src = o, "override"
    ld = SimpleNamespace(tok=tok)
    dflt, _ = G.render(ld, "The", system=G.DEFAULT, prefill=True, user_msg="Hi.")
    try:
        emp, _ = G.render(ld, "The", system="", prefill=True, user_msg="Hi.")
        same = emp == dflt
    except Exception as e:
        emp, same = None, "refused: %s" % type(e).__name__
    txt = emp if emp is not None else dflt
    pre = txt.split("Hi.")[0]
    residue = pre
    for s in sorted(set(getattr(tok, "all_special_tokens", []) or []), key=len, reverse=True):
        residue = residue.replace(s, " ")
    residue = re.sub(r"<\|[^|>]{0,40}\|>", " ", residue)       # role tags not registered as special
    return {"template": src, "pre_user": pre, "residue": " ".join(residue.split()),
            "empty_equals_default": same}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    from malignment import roster
    eps, _ = roster.endpoints()
    M = modes()
    keep, excluded = [], []
    for base, m in sorted(eps.items()):
        try:
            st = render_state(m)
        except Exception as e:
            excluded.append({"model": m, "base": base, "why": "render failed: %s" % str(e)[:80]})
            continue
        if not st.get("template"):
            excluded.append({"model": m, "base": base, "why": "no chat template (tokenizer or override)"})
            continue
        clean = len(re.sub(r"\s", "", st["residue"])) <= MARKER_CHARS
        have = M.get(m, set())
        mode = "empty" if "empty" in have else ("default" if "default" in have and st["empty_equals_default"] is not False else None)
        rec = dict(model=m, base=base, template=st["template"], residue=st["residue"],
                   pre_user=st["pre_user"][-200:], empty_equals_default=st["empty_equals_default"], system_mode=mode)
        if not clean:
            excluded.append(dict(rec, why="text before the user turn beyond role markers"))
        elif mode is None:
            excluded.append(dict(rec, why="no prefill cells at a clean system_mode (have: %s)" % sorted(have)))
        else:
            keep.append(rec)
    print("framed_empty: %d of %d endpoint lineages" % (len(keep), len(eps)))
    for r in excluded:
        print("  excluded %-46s %s | %r" % (r["model"], r["why"], r.get("residue", "")[:70]))
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump({"_about": "Endpoint lineages whose aligned model receives no system context under the "
                             "prefill frame, with prefill cells in that state. Producer "
                             "scripts/build_framed_empty.py; read by roster.population('framed_empty'). "
                             "Use each lineage's system_mode to select its cells.",
                   "marker_chars": MARKER_CHARS, "n": len(keep), "models": keep, "excluded": excluded},
                  open(OUT, "w"), indent=1, ensure_ascii=False)
        print("wrote", OUT)


if __name__ == "__main__":
    main()
