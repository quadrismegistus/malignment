"""Generation and next-token queries, on a checkpoint that is already loaded.

    from malignment import Checkpoint

    ck = Checkpoint("Qwen/Qwen2.5-7B-Instruct")
    ck.generate("She was ugly and she wanted to")            # one passage
    ck.generate(stem, n=4, frame="system", system="...")     # four, framed
    ck.next_token("The capital of France is", k=5)           # {' Paris': 0.71, ...}
    ck.next_word("The capital of France is")                 # the twp instrument

    ld = ck.load()                                           # hold it across calls
    ck.generate(stem, loaded=ld); ck.next_token(stem, loaded=ld)

## THIS IS A THIRD VERB ON THE SAME LOADER, NOT A SECOND LOADER

`runners.load_for_twp` is the one way a checkpoint reaches a device: it carries
the `LOADER_OVERRIDE` table (deepseek-llm-7b's `PreTrainedTokenizerFast`, HF
#45488/#47017; internlm2's boundary shift), the MPT native-impl exception, the
pinned revision reaching the TOKENIZER as well as the weights, the dtype
declared in the roster, rate-limit backoff and multi-GPU placement.

Every one of those was paid for once. `runners.py:321` records what happened the
last time a second load path existed: the archive's server never grew the MPT
override, the retry or the mask guard, so the app could load a model the runner
refuses. **A second loader is a second instrument.** So this module loads
nothing; it takes a `Loaded` and uses it.

The cost of that choice is honest and small: `load_for_twp` also builds the twp
prefix trie and byte masks, which generation does not need. Paying a trie load
to keep one loader is the right trade, and naming it here is cheaper than
discovering later that generation used a different tokenizer.

## EVERY DECODER PARAMETER IS PINNED, INCLUDING THE ONES THAT LOOK LIKE DEFAULTS

`DECODER` matches the f11_l2 corpus exactly -- temperature 1.0, top_p 1.0,
max_new_tokens 256 -- because a passage generated here is meant to be comparable
with one already in the store.

The rule, from that corpus's own plan
(`malign-logits/meta/M02_frame_exit/plans/f11_l2_generation.md:71`): HF
`generate()` MERGES the checkpoint's `generation_config`, so **a parameter not
named is a parameter the checkpoint chooses**. The roster spans 100+ checkpoints
from 40-odd organisations, and vendors ship different defaults for base and
instruct arms -- so an unpinned `top_p` is not a constant, it is a per-vendor
covariate ALIGNED WITH THE ARM CONTRAST. Naming every field is what stops the
decoder from becoming part of the finding.

`Passage.decoder` carries the RESOLVED values, so what actually ran is on the
row rather than in a default two layers away.

## FRAMES ARE NAMED, AND `raw` IS ONE OF THEM

    raw        the bare stem. What the corpus used, and the only frame a base
               model can take -- hand a base model "Continue this text:" and it
               continues that string rather than obeying it.
    chat       chat template, stem as the user turn, NO system message SUPPLIED
               -- which is not the same as no system message PRESENT. Many
               templates inject a vendor default: SmolLM2-360M-Instruct renders
               "You are a helpful AI assistant named Smol..." under this frame
               and under `continue`. So `chat` means "the model's own default
               framing", and for two of the eligible models the `system` frame
               REPLACES that default rather than adding to nothing.
    continue   chat template, ONE user turn: "Continue this text: " + stem.
               The archive's frame (`malign_logits/core.py:231`).
    system     chat template, a SYSTEM message plus the stem as its own user
               turn. The API models' frame (`generate_task.py:135,280`).

**`system` MINUS `chat` IS NOT ALWAYS "ADDING A SYSTEM PROMPT".** Where the
template ships a default, it is "replacing one system prompt with another", and
the contrast means something different. `frame_eligibility.py` reports this per
model as a NEGATIVE character delta -- salamandra-7b-instruct at -1333 and
SmolLM3-3B at -1087 -- so the two cases can be separated rather than pooled.

`chat`, `continue` and `system` all require a template, and `system` requires one
that does not silently drop the block -- `experiments/passage_analysis/
jakobson_space/frame_eligibility.py` settles that per model by BYTE COMPARISON,
because a template that discards a system message raises nothing and produces a
treatment arm that never received the treatment.

This module REFUSES rather than falling back: asking for a frame a model cannot
take returns an error naming the model, not a raw generation that will later be
counted as framed.
"""

import collections
import os

#: The f11_l2 corpus decoder, field for field. Change this and generated
#: passages stop being comparable with the store, so it is a module constant
#: with a citation rather than a call-site default.
#: **DO NOT SAMPLE ON MPS.** `experiments/mps_sampling` reproduces it:
#: SmolLM2-360M-Instruct, prompt "It was a", `top_k=50` so the permitted set is
#: exactly fifty ids -- at seed 159 MPS returns token 20341 (' nodded'), RANK
#: 29,516, p=1.17e-08. Deterministic 5/5; CPU at the same seed returns a top-50
#: token. It is NOT the filter: every method leaks the same token at the same
#: 1/400 rate, including the `top_k` and `min_p` that are widely recommended as
#: MPS-safe alternatives to `top_p`. It is the sampling step returning an
#: out-of-range index for particular RNG states.
#:
#: **THE DEFECT NEEDS EXACT ZEROS.** Model-free, 2000 draws on a 49,152 vector
#: with fifty entries at 0.02: tail at exactly 0.0 gives mps 2/2000, tail at
#: 1e-12 gives 0/2000. Every filter sets logits to -inf, which softmaxes to
#: exactly zero, which is why they all leak identically -- and why the pinned
#: `top_p=1.0, top_k=0` below is SAFE: it filters nothing.
#:
#: At 1/400 per draw, P(at least one) is 47% at 256 tokens and 99% at 1900. So
#: FILTERED long-form generation on mps is essentially always contaminated.
#: Fix: sample on cpu, or floor the distribution instead of zeroing it.
#: Forward-pass work -- twp, the logit lens, charge -- touches none of this.
DECODER = {"do_sample": True, "temperature": 1.0, "top_p": 1.0,
           #: **top_k=0 DISABLES IT, AND OMITTING IT DOES NOT.** transformers
           #: 5.4.0 applies an effective top_k=50 when the field is absent,
           #: while `GenerationConfig().top_k`, the checkpoint's own
           #: generation_config, and the merged `model.generation_config.top_k`
           #: ALL report None. Measured on SmolLM2-360M-Instruct, 2026-08-21:
           #: with top_p=1.0 alone, 200 draws never exceed rank 47; with
           #: top_p=1.0 AND top_k=0 they reach rank 7090, and the same
           #: distribution sampled by torch.multinomial reaches 1772 in 300.
           #:
           #: The consequence is not small. The nucleus at top_p 0.95/0.9/0.7
           #: is 436/223/53 tokens, so an unasked-for top_k=50 collapses ALL of
           #: them to one top-50 set -- a sweep over those values varies
           #: nothing at all. It also means the f11_l2 corpus, generated under
           #: vLLM (which REPLACES generation_config rather than merging and
           #: defaults top_k to disabled), was NOT truncated this way, so a
           #: local run without this line does not reproduce it.
           "top_k": 0,
           "max_new_tokens": 256}

FRAMES = ("raw", "chat", "continue", "system")

#: `$MALIGNMENT_DATA/generations/<model>/<producer>/`, the same shape as
#: `runners.TWP_OUT`. The producer segment is why two machines can rsync
#: together: `runners.py:207` records a 200-cell run silently overwriting a
#: 500-cell one when it was absent.
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
GEN_OUT = os.environ.get("MALIGNMENT_GEN_OUT", os.path.join(DATA, "generations"))


def gen_key(model_id, prompt, frame, system, decoder, seed, sample_idx,
            system_set=None):
    """The identity of ONE generated passage. Every field that changes it.

    ## SHAPE FROM THE STORE, EXTENDED WHERE THIS STASH IS FREER

    ClickHouse orders `gen_sequences` on
    `(corpus, model, prompt, forced_word, sample_idx)` and keeps `temp` and
    `seed` as FIELDS. That is right there and wrong here: that store holds one
    design at one temperature, so the decoder cannot vary within it. This stash
    will hold several frames and decoders side by side, and a `temp=0.7` draw
    colliding with a `temp=1.0` draw would be a cache that returns the wrong
    measurement. So the decoder is IN the key -- `Checkpoint.key`'s rule, that
    the instrument is part of the identity, applied to the generator.

    ## `sample_idx` IS WHAT MAKES n SAMPLES n OBSERVATIONS

    Without it, `n=10` at temperature 1 returns one cached draw ten times and
    silently shrinks n to 1. `generate_task.py` hit exactly this and had to vary
    `metadata` to get distinct samples out of a HashStash. It is the single most
    important field here and the easiest to leave out.

    ## `system_set` IS SEPARATE FROM `system_sha` AND MUST BE

    "No system message at all" and "an explicitly empty one" both hash to `""`,
    and they are the two conditions `conditions.py` measured 2,500x apart -- the
    template's own persona firing versus being overridden. For a while they were
    distinguished only by the derived `frame` label, so renaming a label would
    have silently collided them and served the wrong condition from cache.

    A key should carry the fact, not a name for it. `system_set` is the boolean
    itself: False for DEFAULT, True for any supplied string including empty.

    ## THE SYSTEM PROMPT IS STORED WHOLE, NOT HASHED

    An earlier version carried `sha256[:16]` on the reasoning that a key must
    stay short because it becomes a filename. **It does not.** The stash is
    `flat=True`: the key is written as a JSON object into `__key__` inside
    `data.jsonl`, so there is no length constraint and the hash bought nothing
    while making the stored key unreadable -- a row whose condition you can
    distinguish but cannot state.

    The full text is here. Reading `data.jsonl` now tells you what was asked,
    not merely that two things differed.
    """
    return {"model": model_id, "prompt": prompt, "frame": frame,
            #: the boolean, not a label that happens to encode it. Kept beside
            #: the text because "" and "no system message" both render as an
            #: empty string and are the two conditions measured 2,500x apart.
            "system_set": (bool(system) if system_set is None else bool(system_set)),
            "system": system or "",
            #: sorted so dict order can never make two identical decoders
            #: look like two different keys
            "decoder": {k: decoder[k] for k in sorted(decoder)},
            "seed": seed, "sample_idx": sample_idx}

def _passage(**kw):
    """-> passage.Passage. ONE class, not a namedtuple that resembles it.

    This module used to define its own `Passage` namedtuple whose fields
    happened to match `passage.Passage`'s, so a generated passage and a corpus
    passage interoperated by coincidence of naming. They are the same object
    now: anything that scores one scores the other, and adding a field in one
    place cannot silently diverge them.
    """
    from .passage import Passage
    return Passage(**kw)


class FrameRefused(Exception):
    """The model cannot take the frame asked for. Never a silent fallback."""


#: PASS NO SYSTEM MESSAGE AT ALL, so the template's own default fires. Distinct
#: from `system=""`, which asserts an empty one and OVERRIDES that default --
#: `conditions.py` measured a 2,500x swing on one stem between those two.
DEFAULT = object()


def render(loaded, text, system=DEFAULT, user=None, prefill=False,
           user_msg="Hi.", template=None):
    """Compose the three free slots into the string the model sees.

    ## THREE FREE PARAMETERS, NOT ONE

    `conditions.py` established this and it is not a stylistic point. On
    Olmo-3-7B-Instruct-DPO with one stem, the measured probability of the target
    word moved **2,500x** across combinations the caller never typed: default
    system .246, empty system .106, a persona .0001. Naming only the prefill
    lets the other two default to whatever the tokenizer ships, and a reversal
    booked as a frame effect turned out to be an instruction nobody declared.

        system   DEFAULT -> pass none, the template's own persona fires
                 ""      -> assert an empty one, OVERRIDING that persona
                 "..."   -> ours
        user     the user turn. None means `text` goes here (chat mode).
        prefill  True -> `text` goes in a prefilled ASSISTANT turn instead, and
                 the user turn takes `user_msg`. The model resumes a sentence it
                 is already writing, which is the only chat-mode position with a
                 word slot in it.
        user_msg what occupies the user turn under prefill. Default `"Hi."` is
                 the PRESENCE CONTROL: semantically empty on purpose, so that
                 instruction-minus-presence is the instruction's content rather
                 than the user turn merely being non-empty. An empty turn leaves
                 13.9% of mass on fill punctuation and ANY contentful turn
                 collapses it -- `Hi.` as much as an instruction.

    -> (rendered_text, sys_supported). `sys_supported` is False when the template
    REFUSED a system role and this fell back to user-only: a dropped system
    prompt is a different condition wearing the same name, so it is reported
    rather than absorbed.
    """
    tok = loaded.tok
    #: `template=None` is AUTO: raw when no slot was set, templated otherwise.
    #: Explicit True/False overrides, because "chat with the template's own
    #: defaults" and "raw, no template" set the SAME slots -- both leave system
    #: at DEFAULT, user at None and prefill off -- and auto alone cannot tell
    #: them apart. Asking for the naive chat call must be possible.
    if template is None:
        template = prefill or user is not None or system is not DEFAULT
    if not template:
        if prefill:
            raise ValueError("prefill needs a chat template; template=False "
                             "asks for none")
        return text, None                       #: raw: no template at all
    if not getattr(tok, "chat_template", None):
        raise FrameRefused("%s ships no chat template"
                           % getattr(tok, "name_or_path", "?"))
    turn = user_msg if prefill else (text if user is None else user)
    msgs = []
    if system is not DEFAULT:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": turn})
    sys_ok = True
    try:
        out = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                      tokenize=False)
    except Exception as e:
        if system is DEFAULT:
            raise FrameRefused("template refused: %s: %s" % (type(e).__name__, e))
        try:
            out = tok.apply_chat_template([{"role": "user", "content": turn}],
                                          add_generation_prompt=True,
                                          tokenize=False)
            sys_ok = False
        except Exception as e2:
            raise FrameRefused("template refused: %s: %s" % (type(e2).__name__, e2))
    #: **THE BYTE TEST MUST RUN FOR AN EMPTY SYSTEM TOO, AND IT DID NOT.**
    #: The guard read `... and system`, which is FALSY for `""` -- so the one
    #: value most likely to be silently ignored was the one value never checked.
    #:
    #: Measured 2026-08-22 across the 80 prefill-able checkpoints: **10 templates
    #: ignore a supplied system message entirely**, rendering byte-identical
    #: output for DEFAULT, `""` and `" "`. They include BOTH Llama-3.1-Instruct
    #: arms, SmolLM3-3B (which injects its own dated metadata block), Yi-1.5-Chat,
    #: gemma-2-9b-it, falcon-7b-instruct and glm-4-9b-chat-hf.
    #:
    #: Under the old guard every one of those returned `sys_ok=True` for
    #: `system=""`, so a cell would be STAMPED as an empty-system condition while
    #: actually carrying the vendor persona -- the stamp-declares-not-applies
    #: failure, in the field whose whole job is to say which condition ran.
    #:
    #: `out == bare` is the discriminating clause and it works for any value: if
    #: supplying a system message renders the same as supplying none, it had no
    #: effect. The content clause stays guarded, because `""[:24] not in out` is
    #: vacuously False and would never fire.
    if sys_ok and system is not DEFAULT:
        bare = tok.apply_chat_template([{"role": "user", "content": turn}],
                                       add_generation_prompt=True, tokenize=False)
        #: THE BYTE TEST for the DISCARD case, which throws nothing of its own.
        if out == bare or (system and system[:24] not in out):
            sys_ok = False
    if prefill:
        #: the stem inside the assistant turn, appended AFTER the generation
        #: prompt so the model continues it rather than answering about it.
        out = out + text
    return out, sys_ok


def encode(loaded, text_in, templated):
    """Tokenise with EXACTLY ONE leading BOS, whatever the model does.

    **NEITHER A BLANKET True NOR A BLANKET False IS CORRECT**, measured:

        Llama-3.1-Tulu-3-8B-DPO   template emits no BOS text; the tokenizer adds
                                  one -> add_special_tokens=False DROPS it
        SmolLM2-360M-Instruct     the template's own `<|im_start|>` IS the bos
                                  token; the tokenizer adds nothing -> either
                                  setting gives the same ids

    `conditions.py:134` takes `add_special_tokens=False` for every templated
    condition on the reasoning that a template carries its own BOS. That holds
    for SmolLM2 and not for Tulu, and getting it wrong shifts every position by
    one -- silently, since the ids still decode to plausible text.

    So this DETECTS instead: encode without specials, and prepend the BOS only
    if the model uses one, the string does not already start with it, and the
    tokenizer's own default would have added it.
    """
    ids = loaded.tok(text_in, add_special_tokens=False)["input_ids"]
    b = getattr(loaded.tok, "bos_token_id", None)
    if b is not None and (not ids or ids[0] != b):
        default = loaded.tok(text_in)["input_ids"]
        if default and default[0] == b:
            ids = [b] + list(ids)
    import torch
    t = torch.tensor([ids], device=loaded.dev)
    return {"input_ids": t, "attention_mask": torch.ones_like(t)}


def generate(loaded, text, n=1, system=DEFAULT, user=None, prefill=False,
             user_msg="Hi.", template=None, seed=None, decoder=None,
             keep_prompt=False):
    """Sample `n` continuations. -> [Passage]

    `seed` is per SAMPLE, derived as `seed + i`, so `n` samples are `n`
    observations rather than one repeated, and a rerun reproduces.
    """
    import torch
    dec = dict(DECODER)
    dec.update(decoder or {})
    text_in, sys_ok = render(loaded, text, system=system, user=user,
                             prefill=prefill, user_msg=user_msg,
                             template=template)
    templated = text_in != text
    enc = encode(loaded, text_in, templated)
    plen = int(enc["input_ids"].shape[1])
    out = []
    for i in range(n):
        if seed is not None:
            torch.manual_seed(seed + i)
        with torch.no_grad():
            g = loaded.model.generate(**enc, **dec,
                                      pad_token_id=loaded.tok.eos_token_id)
        new = g[0][plen:]
        #: DECODE ONLY THE NEW TOKENS. Slicing the decoded STRING by the prompt's
        #: character length breaks whenever a tokenizer normalises whitespace.
        txt = loaded.tok.decode(new, skip_special_tokens=True)
        out.append(_passage(
            text=(text_in + txt) if keep_prompt else txt,
            prompt=text, model=getattr(loaded.tok, "name_or_path", None),
            frame=frame_label(system, user, prefill, templated),
            seed=None if seed is None else seed + i,
            decoder=dict(dec), n_new_tokens=int(new.shape[0]),
            finish=("length" if int(new.shape[0]) >= dec["max_new_tokens"]
                    else "eos"),
            sys_supported=sys_ok,
            #: THE CONDITION, IN FULL, ON THE RECORD. The key carries
            #: `system_sha` because a key must stay short; the record carries
            #: the TEXT, because a stored generation whose system prompt is only
            #: a hash cannot be read later -- you can tell two conditions apart
            #: and cannot say what either one said.
            system=(None if system is DEFAULT else system),
            system_default=(system is DEFAULT),
            user=user, prefill=bool(prefill),
            user_msg=(user_msg if prefill else None), template=templated))
    return out


def frame_label(system, user, prefill, templated=None):
    """A short name for the slot combination, for the record and the key."""
    if templated is False:
        return "raw"
    if templated is None and not prefill and user is None and system is DEFAULT:
        return "raw"
    parts = ["prefill" if prefill else "chat"]
    parts.append("sysdefault" if system is DEFAULT else
                 "sysempty" if system == "" else "sys")
    if user is not None:
        parts.append("user")
    return "_".join(parts)


def next_token(loaded, text, k=10, system=DEFAULT, user=None, prefill=False,
               user_msg="Hi.", template=None):
    """The next-TOKEN distribution. -> ([(token_string, prob)], full_vocab_size)

    Tokens, not words. `next_word` is the word-level instrument and they answer
    different questions: `next_token` shows ` Par` where the word continues into
    another token, which is a fact about the tokenizer and not about the model's
    preference between words. Use `next_word` for anything about vocabulary.

    No sampling, no seed: this is the distribution itself, not a draw from it.
    """
    import torch
    text_in, _ = render(loaded, text, system=system, user=user,
                        prefill=prefill, user_msg=user_msg, template=template)
    enc = encode(loaded, text_in, text_in != text)
    with torch.no_grad():
        logits = loaded.model(**enc).logits[0, -1]
    p = torch.softmax(logits.float(), dim=-1)
    top = torch.topk(p, min(k, p.shape[0]))
    return ([(loaded.tok.decode([int(i)]), float(v))
             for v, i in zip(top.values, top.indices)], int(p.shape[0]))
