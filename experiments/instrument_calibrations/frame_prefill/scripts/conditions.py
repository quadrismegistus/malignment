"""The three frame conditions, in one place, because they are the instrument.

    from conditions import build, SYSTEM_PROMPT, CONDITIONS

A condition is a STRING TRANSFORM on (tokenizer, stem). Keeping them here rather
than inline in the runner is the same rule the archive learned twice: a stimulus
defined at the call site becomes two stimuli the first time anyone adds a caller.

## THE THREE

    raw       stem, no template. What `twp` uses. Defined for every model.
    chat      apply_chat_template([system, user=stem], add_generation_prompt)
              The model is at the START of a reply.
    prefill   the same string, with the stem appended after the generation
              prompt, so the model is MID-SENTENCE in its own assistant turn.

`chat` and `prefill` are NOT a pair of settings on one condition. Measured on
Llama-3.1-8B-Instruct they share 1 of 50 top tokens with `raw` and 27 of 50
respectively; `chat`'s top prediction is `'...'` and its next entries are word
fragments with no leading space, because it is answering rather than continuing.
Pooling them would average a word distribution with a not-word distribution.

## THE SYSTEM PROMPT IS PART OF THE CONDITION

`SYSTEM_PROMPT` below is a string I chose. It is not neutral, it was not
piloted against alternatives, and every number this instrument produces is a
number about it. It is declared here so a later reader can see what was asked
rather than infer it from an effect size.

A model whose template rejects a `system` role falls back to a user-only
message and RECORDS that it did, under `sys_supported`, rather than silently
dropping the instruction -- a dropped system prompt is a different condition
wearing the same name.
"""

SYSTEM_PROMPT = "Continue the text. Output only the continuation, no preamble."
CONDITIONS = ("raw", "chat", "prefill")


def build(tok, stem, system=SYSTEM_PROMPT):
    """-> {condition: (text, add_special_tokens, sys_supported)}

    `add_special_tokens` differs by condition and getting it wrong is silent:
    a chat template already carries its own BOS, so letting the tokenizer add
    another shifts every position by one and changes the distribution being
    measured.
    """
    out = {"raw": (stem, True, None)}
    if not getattr(tok, "chat_template", None):
        return out

    msgs, sys_ok = [{"role": "system", "content": system},
                    {"role": "user", "content": stem}], True
    try:
        base = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    except Exception:
        #: some templates reject a system role outright. Fall back and SAY SO.
        sys_ok = False
        base = tok.apply_chat_template([{"role": "user", "content": stem}],
                                       add_generation_prompt=True, tokenize=False)
    out["chat"] = (base, False, sys_ok)
    #: PREFILL: the stem again, inside the assistant turn. The model resumes a
    #: sentence it is already writing, which is the only chat-mode position with
    #: a word slot in it.
    out["prefill"] = (base + stem, False, sys_ok)
    return out


def check(tok, stem):
    """Refuse a cell whose conditions are not what they claim. -> None or reason

    Two failures worth catching before a forward pass, both silent otherwise:
    a template that does not actually place the stem, and a tokenizer that does
    not round-trip it (transformers #45488 deletes every space on some repos and
    returns plausible numbers on the wreckage).
    """
    if tok.decode(tok(stem, add_special_tokens=False)["input_ids"]).strip() != stem.strip():
        return "tokenizer does not round-trip the stem"
    b = build(tok, stem)
    if "prefill" in b and not b["prefill"][0].endswith(stem):
        return "prefill string does not end with the stem"
    if "chat" in b and stem not in b["chat"][0]:
        return "chat string does not contain the stem"
    return None
