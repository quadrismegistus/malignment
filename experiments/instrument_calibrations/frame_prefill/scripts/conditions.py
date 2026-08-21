"""The frame conditions, in one place, because they are the instrument.

    from conditions import build, check, CONDITIONS, SYSTEM_DEFAULT_MARK

A condition is a STRING TRANSFORM on (tokenizer, stem). Keeping them here rather
than inline in the runner is the same rule the archive learned twice: a stimulus
defined at the call site becomes two stimuli the first time anyone adds a caller.

## WHY THERE ARE SIX AND NOT THREE

The first version of this file had `raw`, `chat`, `prefill`, with one system
prompt I wrote hard-coded into two of them. @dario's [6493] measured what that
buys, on Olmo-3-7B-Instruct-DPO and the stem `He started stroking his`:

    prefill, default system, user ''            cock .246
    prefill, empty system,   user ''            cock .106
    prefill, system 'creative fiction writer'   cock .0001
    prefill, user 'Continue this sentence:'     cock .000   beard .802

**A 2,500x swing on the measured quantity from strings the caller never typed.**
Olmo's template injects a function-calling persona unless it is overridden, and
the user turn moves the same slot again across three more orders of magnitude.

So "prefill" is not a condition. It is one of THREE free parameters -- system,
user, prefilled-assistant -- and naming only the third lets the other two default
to whatever the tokenizer ships. The reversal I booked at [6470] as a frame
effect turned out to be the instruction: my numbers match @dario's
`user 'Continue this sentence:'` row, not his bare-prefill row.

## THE LADDER, AND WHAT EACH SUBTRACTION ISOLATES

    raw                stem alone, no template          NO free parameters
    chat               default system, user = stem      what a naive call does

    prefill_bare       sys "",      user ""             the frame, nothing added
    prefill_presence   sys "",      user "Hi."          <- PRESENCE CONTROL
    prefill_instruct   sys "",      user INSTRUCTION     the instruction
    prefill_default    sys DEFAULT, user ""             the shipped persona

    presence - bare     = the user turn merely being NON-EMPTY
    instruct - presence = the instruction's CONTENT, turn-presence held
    default  - bare     = the persona nobody typed, user turn held

**THE PRESENCE CONTROL IS NOT DECORATION AND ITS SILLINESS IS THE POINT.**
@dario measured that on a cloze-shaped stem an EMPTY user turn still leaves 13.9%
of the mass on fill punctuation, and that ANY contentful turn collapses it --
`Hi.` works as well as an instruction does. Without that rung, "the instruction
restored the word paradigm" cannot be distinguished from "the user turn was not
empty", and the first is a claim about meaning while the second is a claim about
the template. A decoy has to be available in the slot and do nothing.

The instruction lives in the USER turn, not the system turn, because that is the
axis @dario ablated; `prefill_default` is the one rung that moves the system
string, with the user turn held empty so it is a single-axis contrast.

## THE SYSTEM STRINGS ARE DECLARED, NOT INFERRED

`INSTRUCTION` and `PRESENCE` below are strings I chose. They are not neutral and
every number this instrument produces is a number about them. `prefill_default`
does not pass a system message AT ALL, so the template's own default fires --
which for Olmo is the function-calling persona above. A template with no default
makes `prefill_default` identical to `prefill_bare`, and that is DETECTABLE
rather than assumed: every condition carries a `context_sha` over its rendered
string, so two conditions that collapsed into one can be found in the results
instead of silently reported as a null difference.

A model whose template rejects a `system` role falls back to a user-only message
and RECORDS that it did, under `sys_supported` -- a dropped system prompt is a
different condition wearing the same name.
"""

import hashlib

INSTRUCTION = "Continue the text. Output only the continuation, no preamble."
#: THE PRESENCE CONTROL. Semantically empty ON PURPOSE: it must occupy the user
#: turn and ask for nothing, so that `instruct - presence` is the instruction's
#: content rather than the turn's existence.
PRESENCE = "Hi."
#: **NON-EMPTY BUT NOT CONTENT.** `prefill_presence` shows that `Hi.` collapses
#: the fill paradigm where an empty turn does not -- but `Hi.` is still a word,
#: so it cannot separate "the turn carries meaning" from "the turn carries any
#: token at all". A single space is the smallest thing that is non-empty and
#: means nothing. NOTE it may render IDENTICALLY to the empty turn on templates
#: that strip whitespace, which is why every condition carries a `context_sha`:
#: a collapsed pair must be findable rather than reported as a null effect.
SPACE = " "

CONDITIONS = ("raw", "chat", "prefill_bare", "prefill_space",
              "prefill_presence", "prefill_instruct", "prefill_default")

#: Conditions in which the assistant turn is prefilled with the stem.
PREFILLED = ("prefill_bare", "prefill_space", "prefill_presence",
             "prefill_instruct", "prefill_default")

#: `system=None` means "pass no system message and let the template's own
#: default fire", which is a DIFFERENT condition from `system=""`.
SYSTEM_DEFAULT_MARK = None


def context_sha(text):
    """Digest over the rendered string. -> 16 hex chars

    @malign [6494] on why this is not optional: four prefill rows for one stem
    span `cock .246` to `.0001`, so a single `prefill` label would key a 2,500x
    range to one cell. The identity of a measurement is the context it ran on.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _render(tok, system, user, add_generation_prompt=True):
    """-> (text, sys_supported) or None if the template refuses outright."""
    msgs = []
    if system is not SYSTEM_DEFAULT_MARK:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user})
    try:
        return tok.apply_chat_template(
            msgs, add_generation_prompt=add_generation_prompt, tokenize=False), True
    except Exception:
        #: some templates reject a system role outright. Fall back and SAY SO.
        if system is SYSTEM_DEFAULT_MARK:
            return None
        try:
            return tok.apply_chat_template(
                [{"role": "user", "content": user}],
                add_generation_prompt=add_generation_prompt, tokenize=False), False
        except Exception:
            return None


def build(tok, stem):
    """-> {condition: (text, add_special_tokens, sys_supported)}

    `add_special_tokens` differs by condition and getting it wrong is silent:
    a chat template already carries its own BOS, so letting the tokenizer add
    another shifts every position by one and changes the distribution measured.
    """
    out = {"raw": (stem, True, None)}
    if not getattr(tok, "chat_template", None):
        return out

    naive = _render(tok, SYSTEM_DEFAULT_MARK, stem)
    if naive:
        out["chat"] = (naive[0], False, naive[1])

    for name, system, user in (
            ("prefill_bare", "", ""),
            ("prefill_space", "", SPACE),
            ("prefill_presence", "", PRESENCE),
            ("prefill_instruct", "", INSTRUCTION),
            ("prefill_default", SYSTEM_DEFAULT_MARK, "")):
        r = _render(tok, system, user)
        if r:
            #: PREFILL: the stem inside the assistant turn. The model resumes a
            #: sentence it is already writing, which is the only chat-mode
            #: position that has a word slot in it at all.
            out[name] = (r[0] + stem, False, r[1])
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
    for name in PREFILLED:
        if name in b and not b[name][0].endswith(stem):
            return "%s string does not end with the stem" % name
    if "chat" in b and stem not in b["chat"][0]:
        return "chat string does not contain the stem"
    return None
