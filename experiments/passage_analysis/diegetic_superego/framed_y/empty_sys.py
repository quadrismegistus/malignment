"""Which framed-Y checkpoints honour an EMPTY system message? -> results/empty_sys.json

    python -u empty_sys.py [models...]

Byte test on the render path `vllm_generate` uses (tokenizer template, else the
roster's authored override): prefill with user "Hi.", rendered with NO system
message and with {"role": "system", "content": ""}. EMPTY-ABLE = the empty render
is accepted AND differs from the default one. A template that raises on a system
role, or renders the empty case byte-identically (a vendor block that always
fires), cannot take an empty system message. Tokenizers only; no weights.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "empty_sys.json")


def probe(m):
    from transformers import AutoTokenizer
    from malignment.runners import _chat_template_override
    from malignment.vllm_generate import _trust
    tok = AutoTokenizer.from_pretrained(m, trust_remote_code=_trust(m))
    src = "tokenizer"
    if not getattr(tok, "chat_template", None):
        o = _chat_template_override(m)
        if not o:
            return {"template": None, "empty_able": False, "why": "no template"}
        tok.chat_template, src = o, "override"
    user = [{"role": "user", "content": "Hi."}]
    d = tok.apply_chat_template(user, tokenize=False, add_generation_prompt=True)
    try:
        e = tok.apply_chat_template([{"role": "system", "content": ""}] + user, tokenize=False, add_generation_prompt=True)
    except Exception as x:
        return {"template": src, "empty_able": False, "why": "system role refused: %s" % str(x)[:80]}
    return {"template": src, "empty_able": e != d, "why": "renders differ" if e != d else "empty renders byte-identical to default",
            "default_chars": len(d), "empty_chars": len(e)}


def main():
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for m in sys.argv[1:]:
        try:
            res[m] = probe(m)
        except Exception as x:
            res[m] = {"error": "%s: %s" % (type(x).__name__, str(x)[:120])}
        print("%-46s %s" % (m, res[m]), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
