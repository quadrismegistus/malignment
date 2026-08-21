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
import hashlib
import os

#: The f11_l2 corpus decoder, field for field. Change this and generated
#: passages stop being comparable with the store, so it is a module constant
#: with a citation rather than a call-site default.
DECODER = {"do_sample": True, "temperature": 1.0, "top_p": 1.0,
           "max_new_tokens": 256}

FRAMES = ("raw", "chat", "continue", "system")

#: `$MALIGNMENT_DATA/generations/<model>/<producer>/`, the same shape as
#: `runners.TWP_OUT`. The producer segment is why two machines can rsync
#: together: `runners.py:207` records a 200-cell run silently overwriting a
#: 500-cell one when it was absent.
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
GEN_OUT = os.environ.get("MALIGNMENT_GEN_OUT", os.path.join(DATA, "generations"))


def gen_key(model_id, prompt, frame, system, decoder, seed, sample_idx):
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

    ## `system` IS HASHED, NOT STORED WHOLE

    A system prompt can be long, and the key is written into a jsonl filename.
    The text itself rides on the RECORD; the key carries `sha256[:16]` of it, so
    two different prompts can never share a cell and the key stays short.
    """
    return {"model": model_id, "prompt": prompt, "frame": frame,
            "system_sha": (hashlib.sha256(system.encode()).hexdigest()[:16]
                           if system else ""),
            #: sorted so dict order can never make two identical decoders
            #: look like two different keys
            "decoder": {k: decoder[k] for k in sorted(decoder)},
            "seed": seed, "sample_idx": sample_idx}

Passage = collections.namedtuple(
    "Passage", "text prompt model frame seed decoder n_new_tokens finish")


class FrameRefused(Exception):
    """The model cannot take the frame asked for. Never a silent fallback."""


def render(loaded, prompt, frame="raw", system=None):
    """Apply `frame` to `prompt`. -> the string the model actually sees.

    Raises `FrameRefused` when the template is missing or drops the system
    block. The DISCARD case is checked by rendering with and without the block
    and comparing bytes, because it throws no exception of its own.
    """
    if frame not in FRAMES:
        raise ValueError("frame must be one of %s, got %r" % (FRAMES, frame))
    if frame == "raw":
        return prompt
    tok = loaded.tok
    if not getattr(tok, "chat_template", None):
        raise FrameRefused("%s ships no chat template, so frame %r is impossible"
                           % (getattr(tok, "name_or_path", "?"), frame))
    if frame == "chat":
        msgs = [{"role": "user", "content": prompt}]
    elif frame == "continue":
        msgs = [{"role": "user", "content": "Continue this text: " + prompt}]
    else:
        if not system:
            raise ValueError("frame='system' needs a system= message")
        msgs = [{"role": "system", "content": system},
                {"role": "user", "content": prompt}]
    try:
        out = tok.apply_chat_template(msgs, tokenize=False,
                                      add_generation_prompt=True)
    except Exception as e:
        raise FrameRefused("template refused frame %r: %s: %s"
                           % (frame, type(e).__name__, e))
    if frame == "system":
        bare = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                       tokenize=False, add_generation_prompt=True)
        #: THE BYTE TEST. An equal render, or one missing the text, means the
        #: block was dropped -- and nothing raised.
        if out == bare or system[:24] not in out:
            raise FrameRefused(
                "template ACCEPTS a system role and DISCARDS it -- the rendered "
                "string is unchanged, so this arm would never receive the "
                "manipulation. Refused rather than run.")
    return out


def generate(loaded, prompt, n=1, frame="raw", system=None, seed=None,
             decoder=None, keep_prompt=False):
    """Sample `n` continuations. -> [Passage]

    `seed` is per SAMPLE, derived as `seed + i`, so `n` samples are `n`
    observations rather than one repeated -- and so a rerun with the same seed
    reproduces. Omit it and the sampler is left alone, which is right for
    exploration and wrong for anything that gets counted.
    """
    import torch
    dec = dict(DECODER)
    dec.update(decoder or {})
    text_in = render(loaded, prompt, frame=frame, system=system)
    enc = loaded.tok(text_in, return_tensors="pt").to(loaded.dev)
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
        #: character length is the version that breaks: a tokenizer that
        #: normalises whitespace makes the prompt render at a different length
        #: than it was given, and the passage silently loses or keeps a fragment.
        txt = loaded.tok.decode(new, skip_special_tokens=True)
        out.append(Passage(
            text=(text_in + txt) if keep_prompt else txt,
            prompt=prompt, model=getattr(loaded.tok, "name_or_path", None),
            frame=frame, seed=None if seed is None else seed + i,
            decoder=dict(dec), n_new_tokens=int(new.shape[0]),
            finish=("length" if int(new.shape[0]) >= dec["max_new_tokens"]
                    else "eos")))
    return out


def next_token(loaded, prompt, k=10, frame="raw", system=None):
    """The next-TOKEN distribution. -> ([(token_string, prob)], full_vocab_size)

    Tokens, not words. `next_word` is the word-level instrument and they answer
    different questions: `next_token` shows ` Par` where the word continues into
    another token, which is a fact about the tokenizer and not about the model's
    preference between words. Use `next_word` for anything about vocabulary.

    No sampling, no seed: this is the distribution itself, not a draw from it.
    """
    import torch
    text_in = render(loaded, prompt, frame=frame, system=system)
    enc = loaded.tok(text_in, return_tensors="pt").to(loaded.dev)
    with torch.no_grad():
        logits = loaded.model(**enc).logits[0, -1]
    p = torch.softmax(logits.float(), dim=-1)
    top = torch.topk(p, min(k, p.shape[0]))
    return ([(loaded.tok.decode([int(i)]), float(v))
             for v, i in zip(top.values, top.indices)], int(p.shape[0]))
