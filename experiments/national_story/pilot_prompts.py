"""Which prompt elicits a story, and does the aligned model ever stop?

    .venv/bin/python -u pilot_prompts.py                    aligned, all 8
    .venv/bin/python -u pilot_prompts.py --model M --n 5

## WHY THESE PARAMETERS

`top_p=1.0, top_k=0` is the ONLY MPS-safe sampler (see
experiments/instrument_calibrations/mps_sampling:
every filter zeroes logits, and MPS samples exact zeros at ~1/400 per draw, which
is 99% of a 1900-token generation). Unfiltered sampling draws the true tail --
4 in 300 beyond rank 5000 -- so text quality here is a FLOOR, not an estimate.
Read this pilot for register and stopping, not for prose quality.

Length is the full 1900 because a word-count instruction cannot be tested at 500.

## RETTBERG'S ACTUAL PARAMETERS

From `script/generate_stories.py` in AI-STORIES-ERC/GPT_stories, which the paper
does not cite: `gpt-4o-mini`, system message `""`, user message
`"Write a {n} word potential {demonym} story."`, `temperature=0.8`, and NOTHING
ELSE -- so `top_p` is OpenAI's default 1.0, and there is **no `max_tokens`**, no
stop sequence, no seed, no retry and no length check.

Two consequences. Their stories ended when the model emitted its own stop token,
so their lengths are the model's choice and any capped replication measures a
different thing. And 0.8 with an unfiltered `top_p` is BOTH the replication
setting and an MPS-safe one, since it filters nothing and so zeroes nothing --
the defect needs exact zeros. Matching them and avoiding the bug do not conflict.

## THE QUESTION UNDER THE PROMPT QUESTION

Six degenerate aligned samples in the earlier pilot contained ZERO end-of-turn
tokens and all ran to the cap, while the only two clean ones stopped early. All
six were RAW (the three labelled CHAT were untemplated -- `frame`/`template` was
never set). So the standing hypothesis is not that the model finishes and drifts,
it is that a raw-mode aligned model has no turn to end and therefore no stopping
behaviour to reach. `stopped` below is the discriminating column: if the CHAT
conditions stop early and the RAW ones do not, the hypothesis holds.
"""

import argparse
import json
import re
import sys

#: Rettberg & Wigers's own instruction, then the pieces of it removed one at a
#: time. "potential" is theirs and is odd; the word count may or may not carry
#: the length; the demonym may or may not need to be in an instruction at all.
PARA = "A {D} Story\n\nIt was a"

CONDS = [
    ("R1 raw ours",         dict(text=PARA, template=False)),
    ("R2 raw count-title",  dict(text="A {D} Story\n(1500 words)\n\n", template=False)),
    ("R3 raw count+open",   dict(text="A {D} Story\n(1500 words)\n\nIt was a", template=False)),
    ("C1 chat rettberg",    dict(text="Write a 1500 word potential {D} story.", template=True)),
    ("C2 chat no-potential", dict(text="Write a 1500 word {D} story.", template=True)),
    ("C3 chat no-count",    dict(text="Write a {D} story.", template=True)),
    ("C4 chat count-only",  dict(text="Write a story in 1500 words.", template=True)),
    ("C5 chat minimal",     dict(text="Write a story.", template=True)),
]

#: THE PREFILL BATTERY. `text` goes in a PREFILLED ASSISTANT turn and `user_msg`
#: becomes the user turn, so the model resumes our paratext from inside a chat
#: structure instead of answering a request about it.
#:
#: **P3 IS THE ISOLATING CONTRAST.** Its `text` is byte-identical to R1's and its
#: user turn is the neutral default, so R1 and P3 differ in exactly one thing:
#: whether a turn exists to end. Every other pairing here confounds the wrapper
#: with a change of instruction, which is why the earlier CHAT-vs-RAW comparison
#: could not have answered this even had it been templated.
PREFILL = [
    ("P1 pre rettberg",  dict(text=PARA, prefill=True,
                              user_msg="Write a 1500 word potential {D} story.")),
    ("P2 pre plain",     dict(text=PARA, prefill=True,
                              user_msg="Write a 1500 word {D} story.")),
    ("P3 pre bare-user", dict(text=PARA, prefill=True)),
    ("P4 pre count-para", dict(text="A {D} Story\n(1500 words)\n\nIt was a",
                               prefill=True, user_msg="Write a {D} story.")),
    #: **CELL 3 OF THE DESIGN, AND THE ONE CONDITION NOTHING HERE TESTED.**
    #: Its prefill is byte-identical to cell 1's raw prompt and its user turn is
    #: the campaign default, so cell 1 and cell 3 differ in exactly one thing:
    #: whether a turn wrapper exists. P3 had the neutral turn without the count,
    #: P4 had the count with an instruction; each holds one of the two properties
    #: and neither holds both, so the contrast they appear to support is not one
    #: either of them can make.
    #:
    #: What it has to show is that the paratextual count carries the LENGTH from
    #: inside an assistant turn. P3, which lacked it, returned 33-252 words. If
    #: that is what a neutral turn gives once the count is present too, cell 3
    #: is a stub and is comparable to cell 1 on nothing.
    ("P5 pre neutral-count", dict(text="A {D} Story\n(1500 words)\n\nIt was a",
                                  prefill=True)),
    #: **P6 IS CELL 3'S CANONICAL FORM, AND P5 IS NOW ITS CONTROL.**
    #: `"Hi."` is the campaign default but it is a GREETING, and a greeting
    #: warrants a short reply -- P3 returned 30-560 words and one sample ended
    #: "What would you like to do now?", which reads as the model completing a
    #: chitchat exchange rather than failing to write. If that is what happened,
    #: P3's stubs say nothing about instructionless generation and P5 inherits
    #: the same defect.
    #:
    #: An empty user turn renders as the header, no content, `<|eot_id|>`: the
    #: wrapper without a speech act, which is the only thing here that is
    #: actually zero. It is off-distribution and that is the cost.
    #:
    #: NOT `"Continue."`. This campaign measured `"Continue this text:"` moving a
    #: model roughly 80% as far as alignment does -- a continuation imperative is
    #: one of the largest treatments available, which is precisely what the cell
    #: isolating a wrapper cannot carry.
    ("P6 pre empty-user", dict(text="A {D} Story\n(1500 words)\n\nIt was a",
                               prefill=True, user_msg="")),
    #: completes the 2x2 over {greeting, empty} x {count, no count}. Without it
    #: P3's stubs have two candidate causes and the design cannot say which:
    #:
    #:     P3  "Hi."   no count      30-560 words
    #:     P5  "Hi."   count         ?
    #:     P6  empty   count         ?   <- cell 3
    #:     P7  empty   no count      ?
    #:
    #: P5-P3 is the count's effect under a greeting, P6-P5 is the greeting's
    #: effect with the count present, and P7 is what says whether the count is
    #: needed at all once the greeting is gone.
    ("P7 pre empty-nocount", dict(text="A {D} Story\n\nIt was a",
                                  prefill=True, user_msg="")),
]

#: **THE DETECTOR MUST KNOW WHICH LANGUAGE IT IS SCORING.** An English-only
#: function-word list rates fluent Norwegian at 0.02 -- indistinguishable from
#: token salad, and three C2 generations were misread exactly that way. The tell
#: was the HEAD ratio: real degeneration starts high and falls, so a text that
#: starts at 0.02 was never English to begin with.
#:
#: Dropping "potential" makes the model answer in the demonym's language, which
#: Rettberg & Wigers report at p. 8 and never pursue. So a national-story
#: instrument that cannot score non-English text is blind on the exact condition
#: their own paper flags as changing the output.
FN = {
    "en": set("the a an and or but of to in on at for with from by as is was "
              "are were be been being it its he she they them his her their "
              "that this these those there here what which who when where how "
              "not no so if then than had has have do did does will would can "
              "could".split()),
    "no": set("og i det er en et som til pa av for med den de har var ikke om "
              "han hun jeg vi seg fra kan skal ble men aa eller naar hvor at "
              "sin sitt seg hans hennes deres dette disse der her hva hvem "
              "hvorfor ville kunne skulle maatte blir blitt".split()),
}


def fnratio(words, lang="en"):
    """Function-word share against ONE language's list."""
    if not words:
        return 0.0
    f = FN[lang]
    return sum(w.lower().strip('.,!?;:\'"*-') in f for w in words) / len(words)


def detect(words):
    """-> (lang, head_ratio, tail_ratio). Language chosen on the HEAD, where the
    text is still whatever it set out to be; scoring the tail would let a
    collapsed ending pick the language for the passage that preceded it."""
    head = words[:100]
    best = max(FN, key=lambda k: fnratio(head, k))
    return best, fnratio(head, best), fnratio(words[-100:], best)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--demonym", default="Norwegian")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--max-new", type=int, default=1900)
    ap.add_argument("--out", default="pilot_prompts.jsonl")
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--set", default="main",
                    choices=("main", "prefill", "all", "raw", "compare"))
    a = ap.parse_args(argv)
    #: `raw` is the only set a BASE checkpoint can take -- the chat and prefill
    #: conditions need a chat template and FrameRefused is the correct answer,
    #: not a result. So a base arm is comparable to the aligned arm on R1-R3 and
    #: on nothing else, which is a property of the design and not a shortfall.
    conds = {"main": CONDS, "prefill": PREFILL, "all": CONDS + PREFILL,
             "raw": [c for c in CONDS if c[0].startswith("R")],
             #: the two cells of the intended comparison plus the BRIDGE. R3 and
             #: P6 carry byte-identical paratext -- P6's prefill IS R3's prompt --
             #: so R3-base against P6-aligned differs in the turn wrapper and the
             #: arm together. R3-ALIGNED is what separates them: it is the only
             #: place the wrapper's own effect can be measured, since P6-base
             #: cannot exist (no chat template on a base checkpoint).
             "compare": [c for c in CONDS if c[0].startswith("R3")]
                        + [c for c in PREFILL if c[0].startswith("P6")]}[a.set]

    from malignment import Checkpoint, generate as G

    ck = Checkpoint(a.model)
    ld = ck.load()
    tok = ld.tok
    fh = open(a.out, "w")
    print("%-22s %5s %6s %2s %9s  %-6s  %s"
          % ("condition", "tok", "words", "lg", "fn>fn", "finish", "opening"))
    for label, kw in conds:
        kw = dict(kw)
        text = kw.pop("text").format(D=a.demonym)
        if "user_msg" in kw:
            kw["user_msg"] = kw["user_msg"].format(D=a.demonym)
        try:
            #: `ck.generate`, NOT `G.generate`. The module function is the
            #: machinery and stashes NOTHING; the Checkpoint method is the handle
            #: that keys each draw, writes it to the generations stash, reads
            #: across every producer's, and fills only the shortfall. Calling the
            #: bare function cost this experiment three things at once: `finish`,
            #: so stopping had to be inferred from length against a cap sitting
            #: at Rettberg's median; the cache, so every rerun regenerated; and
            #: discoverability, so no other seat could find these passages by key.
            ps = ck.generate(text, n=a.n, seed=0, loaded=ld, **kw,
                             decoder={"max_new_tokens": a.max_new,
                                      "do_sample": True, "temperature": a.temp,
                                      "top_p": 1.0, "top_k": 0})
        except Exception as e:
            print("%-22s REFUSED %s: %s" % (label, type(e).__name__, e))
            continue
        for i, p in enumerate(ps):
            body = p.text if hasattr(p, "text") else str(p)
            #: MEASURED, not inferred. `finish` is the generator's own report of
            #: why it halted, and `n_new_tokens` is the true count -- re-encoding
            #: the decoded string does not round-trip. The earlier length rule
            #: could not distinguish "never stopped" from "had not finished yet",
            #: and with the cap at their median that ambiguity covered 40% of the
            #: comparison corpus.
            ntok = getattr(p, "n_new_tokens", None)
            fin = getattr(p, "finish", None)
            if ntok is None:
                ntok = len(tok.encode(body, add_special_tokens=False))
            w = body.split()
            stopped = (fin == "eos")
            lang, h, t = detect(w)
            print("%-22s %5d %6d %s %.2f>%.2f  %-6s  %s"
                  % (label if i == 0 else "", ntok, len(w), lang, h, t,
                     fin or ("STOP" if stopped else "cap"),
                     " ".join(w[:11])[:58]))
            fh.write(json.dumps({
                "condition": label, "prompt": text, "kw": {k: str(v) for k, v in kw.items()},
                "sample": i, "model": a.model, "demonym": a.demonym,
                "n_tokens": ntok, "n_words": len(w), "stopped": stopped,
                "finish": fin, "temp": a.temp, "max_new": a.max_new,
                "lang": lang, "fn_head": round(h, 4), "fn_tail": round(t, 4),
                "text": body}) + "\n")
            fh.flush()
    fh.close()
    print("\nwrote %s" % a.out)


if __name__ == "__main__":
    sys.exit(main())
