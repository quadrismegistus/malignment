"""Which decoder and frame let BOTH arms write a 1500-word story?

Standalone. `torch` and `transformers` only, no malignment import, no vLLM, so it
runs on a rented CUDA box with nothing else installed.

    python run.py --dry-run                    print the plan and every rendered
                                               prompt, load nothing
    python run.py --out sweep.jsonl            the sweep
    python run.py --n 4 --demonyms Norwegian   smaller

## THE QUESTION

Replicating Rettberg & Wigers (2025), who generated 11,800 national stories from
gpt-4o-mini, we need the arm they lack: base against aligned. Local MPS piloting
established the frame and prompt, and then hit two walls that are decoder
questions and cannot be answered on that backend.

**The arms fail DIFFERENTLY, and a single degeneration rate would hide it.**
Measured locally at temperature 0.8, `top_p` 1.0, on Llama-3.1-8B:

    ALIGNED   escapes into ASSISTANT REGISTER. In the raw frame, 3 of 3 ended as
              commentary: a numbered thematic list, an analytic gloss that drifted
              to American folklore inside a Norwegian story, and "Would you like
              to explore a specific topic or theme? ... What do you think?" with
              emoji. Repetition never exceeded 1.2% of 8-grams.
    BASE      falls into REPETITION LOOPS. 2 of 3 had 53-58% of their 8-grams
              repeated, cycling one clause for hundreds of words. Neither showed
              any assistant drift.

**And the obvious fix cuts against one arm.** `top_p=0.95` suppresses the tail
draws behind incoherence, which is the aligned arm's problem, but concentrating
probability mass is the classic condition for repetition loops, which is the base
arm's. So the decoder that rescues one arm may be the one that breaks the other,
and both arms MUST take the same decoder or the contrast means nothing.

That is what this sweeps. It does not tune until the arms look alike -- if base
repeats more under the shared setting, that is a fact about base models under it.

## WHY NOT ON MPS

`torch.multinomial` on MPS samples zero-probability entries at ~1/400 per draw,
and every filter (`top_p`, `top_k`, `min_p`) produces exact zeros via `-inf` into
softmax. Over 1,900 tokens that is a 99% chance of at least one impossible token.
`top_p=1.0` is the only safe local setting and is exactly the one under test, so
the question is unanswerable on that hardware. See `experiments/mps_sampling`.

## WHAT IT RECORDS, AND WHY NOT A VERDICT

Every row carries the full text and four INDEPENDENT measures, never a single
"degenerate" flag. A local fn-ratio detector scored fluent nonsense, assistant
escape and repetition all as clean -- and rated the worst repeater in the pilot
the CLEANEST text of all, because repeated clauses are dense in function words.
One number cannot carry three failure modes.

    rep8, distinct3     repetition. Base's looping samples: rep8 0.53-0.58
                        against 0.000-0.012 for every aligned sample.
    fn_en, fn_no        function-word share per language. Dropping "potential"
                        makes the model answer in the demonym's language, which
                        Rettberg report at p. 8; an English-only measure reads
                        fluent Norwegian as salad.
    escape_*            assistant-register markers in the last fifth: emoji,
                        second-person address, list markers, meta-commentary.
    finish              "eos" or "length", from the generator, not inferred.
                        Length alone cannot separate "never stopped" from "had
                        not finished yet".
"""

import argparse
import json
import re
import sys
import time

#: Rettberg's own call, for reference: gpt-4o-mini, system "", user
#: "Write a {n} word potential {demonym} story.", temperature=0.8, NOTHING else
#: set -- so top_p was OpenAI's default 1.0 and there was NO max_tokens. Their
#: stories therefore ended when the model chose to; median 1,415 words, 1,838
#: tokens. A cap at 1,900 truncates 40% of that distribution, which is why 3,000
#: is the default here: it truncates 0.4%.
CONDITIONS = [
    #: (label, arms, template, user, prefill_text)
    #: `raw` is the ONLY frame a base checkpoint can take -- the others need a
    #: chat template, and refusing is the correct answer, not a result.
    ("raw_plain",   "both",    False, None, "A {D} Story\n\nIt was a"),
    ("raw_count",   "both",    False, None, "A {D} Story\n(1500 words)\n\nIt was a"),
    #: Rettberg verbatim, period included. "potential" is theirs and is load
    #: bearing: without it the model answers in the demonym's language.
    ("chat_rettberg", "aligned", True,
     "Write a 1500 word potential {D} story.", None),
    ("chat_nopotential", "aligned", True,
     "Write a 1500 word {D} story.", None),
    #: prefill: the paratext goes in the assistant turn, so the model RESUMES it
    #: instead of answering a request about it. The user turn is EMPTY, not
    #: "Hi." -- a greeting warrants a short reply and locally returned 30-560
    #: word stubs, which would have been misread as evidence about instructionless
    #: generation. And NOT "Continue.": this campaign measured "Continue this
    #: text:" moving a model ~80% as far as alignment does, so a continuation
    #: imperative is among the largest treatments available and cannot sit in the
    #: cell whose whole job is to add a wrapper and nothing else.
    ("prefill_count",   "aligned", True, "", "A {D} Story\n(1500 words)\n\nIt was a"),
    ("prefill_plain",   "aligned", True, "", "A {D} Story\n\nIt was a"),
]

#: (temperature, top_p). The first is Rettberg's exact setting; the second is the
#: one the arms may need and is what the sweep is for; the third separates a
#: temperature effect from a filtering one.
DECODERS = [(0.8, 1.0), (0.8, 0.95), (1.0, 0.95)]

FN = {
    "en": set("the a an and or but of to in on at for with from by as is was are "
              "were be been being it its he she they them his her their that this "
              "these those there here what which who when where how not no so if "
              "then than had has have do did does will would can could".split()),
    "no": set("og i det er en et som til pa av for med den de har var ikke om han "
              "hun jeg vi seg fra kan skal ble men aa eller naar hvor at sin sitt "
              "hans hennes deres dette disse der her hva hvem hvorfor ville kunne "
              "skulle maatte blir blitt".split()),
}

EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")
#: **BARE SECOND PERSON IS NOT A SIGNAL AND MUST BE SEPARATED FROM ONE.** An
#: earlier version put `you|your` in the same alternation as `let me know`, and
#: it fired on a BASE model's repetition loop -- "I will go with you to my
#: father's house" -- reporting assistant escape in a checkpoint that has never
#: been taught to address a user. Dialogue is full of the second person; what is
#: diagnostic is the SERVICE FORMULA, which fiction does not contain.
#: **EVERY FRAGMENT HERE MUST BE ONE FICTION CANNOT CONTAIN.** `happy to` fired
#: on "was happy to have their father back" in a BASE model's folktale, and
#: `anything else` would fire on "anything else in the room" -- both would report
#: assistant escape in a checkpoint that has never addressed a user. A service
#: formula is only diagnostic when it is complete: it is `happy to help`, not
#: `happy to`. The looser the fragment, the more it measures narration.
ADDRESS = re.compile(r"(let me know if|feel free to|would you like (me|to)|"
                     r"i hope (you|this) (enjoy|like|help)|i can help|"
                     r"if you'?d like|anything else (i|you) can|"
                     r"hope (you|this) helps|happy to help|glad to help)", re.I)
SECOND = re.compile(r"\b(you|your|you're)\b", re.I)
META = re.compile(r"\b(in conclusion|this story (explores|touches|highlights)|"
                  r"the themes|note:|disclaimer|here('s| is) a|symboliz(es|ing)|"
                  r"key takeaway)\b", re.I)
LIST = re.compile(r"(^|\n)\s*(\d+\.|\*|-)\s+\S", re.M)
#: **CORPUS DRIFT: the generation stops being a story and becomes a DIFFERENT
#: DOCUMENT.** A base model finishes its story and continues into the
#: instruction-tuning data it was pretrained on -- "Task: You are required to
#: extract the main topic", then a summary of its own story, then an unrelated
#: article about colour psychology, then an NFL prediction.
#:
#: Found by READING a full story whose scores were rep8 0.000, fn_en 0.404 and
#: no escape flags -- i.e. clean on every existing measure. 680 of its 1,082
#: words were not story, so every per-story statistic computed over it was
#: computed over another document.
#:
#: Distinct from `escape_*`, which looks for the model addressing a USER. This
#: is the model addressing nobody and simply continuing a corpus.
#:
#: Scanned over the WHOLE text, not the tail: the drift can begin at 35% and
#: leave the majority of the generation outside the story.
DRIFT = re.compile(r"(^|\n)\s*(Task\s*:|Instruction\s*:|Input\s*:|Output\s*:|"
                   r"Q\s*:|Answer\s*:|Question\s*:|###\s|Explain the following|"
                   r"Describe in one sentence|Write a (summary|short|brief)|"
                   r"Summarize the|You are required to|Rewrite the|Translate the|"
                   r"Read the (passage|text|article))", re.M)


def ngram_repeat(words, n=8):
    if len(words) < n + 1:
        return 0.0
    g = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
    return 1.0 - len(set(g)) / len(g)


def distinct(words, n=3):
    if len(words) < n:
        return 1.0
    g = {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}
    return len(g) / (len(words) - n + 1)


def measure(text):
    w = text.split()
    #: the LAST FIFTH, because escape is a thing that happens to an ending. A
    #: whole-text scan dilutes it below threshold on a 2,000-word story.
    tail = " ".join(w[max(0, int(len(w) * 0.8)):])
    #: whole text, and record WHERE, because the fraction before the drift is
    #: how much of the generation is usable
    dm = DRIFT.search(text)
    lo = [x.lower().strip(".,!?;:'\"*-") for x in w]
    out = {
        "n_words": len(w),
        "rep8": round(ngram_repeat(w), 4),
        "distinct3": round(distinct(w), 4),
        "escape_emoji": bool(EMOJI.search(tail)),
        #: `escape_address` is the diagnostic one; `second` is kept only as
        #: context and must never be summed into a verdict on its own.
        "escape_address": bool(ADDRESS.search(tail)),
        "escape_second": bool(SECOND.search(tail)),
        "escape_meta": bool(META.search(tail)),
        "escape_list": bool(LIST.search(tail)),
        "corpus_drift": bool(dm),
        #: share of the generation that precedes the drift; 1.0 if none
        "story_frac": (round(len(text[:dm.start()].split()) / max(1, len(w)), 4)
                       if dm else 1.0),
    }
    for lang, fs in FN.items():
        out["fn_" + lang] = round(sum(x in fs for x in lo) / max(1, len(lo)), 4)
    return out


def render(tok, cond, demonym):
    """-> the exact string fed to the model, or None if this checkpoint refuses."""
    _, _, templated, user, pre = cond
    pre = pre.format(D=demonym) if pre else None
    user = user.format(D=demonym) if user else user
    if not templated:
        return pre
    if not getattr(tok, "chat_template", None):
        return None
    turn = user if user is not None else (pre or "")
    #: NO system message. On Llama-3.1-Instruct the template emits its own
    #: `Cutting Knowledge / Today Date` block regardless, and an empty string
    #: appended to it changes no bytes -- so passing none IS Rettberg's
    #: `content: ""` on this family, byte for byte. A non-empty system message
    #: WOULD be honoured, and would be a treatment measured elsewhere in this
    #: campaign at 2,500x on a stem, which is why there is not one here.
    s = tok.apply_chat_template([{"role": "user", "content": turn}],
                                add_generation_prompt=True, tokenize=False)
    if pre is not None and user is not None:
        s = s + pre                      #: resume the paratext inside the turn
    return s


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="meta-llama/Llama-3.1-8B")
    ap.add_argument("--aligned", default="meta-llama/Llama-3.1-8B-Instruct")
    #: ONE demonym and n=5 by default. Two demonyms x n=8 is 384 generations at
    #: 3,000 tokens, which is 8-10 hours of unbatched HF on one A100 -- scale up
    #: deliberately, not by accepting a default.
    ap.add_argument("--demonyms", nargs="+", default=["Norwegian"])
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--max-new", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="sweep.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    arms = [("base", a.base), ("aligned", a.aligned)]
    plan = []
    for arm, mid in arms:
        for cond in CONDITIONS:
            if cond[1] != "both" and cond[1] != arm:
                continue
            for d in a.demonyms:
                for dec in DECODERS:
                    plan.append((arm, mid, cond, d, dec))
    total = len(plan) * a.n
    #: ~35 tok/s unbatched for an 8B in bf16 on an A100. Most generations stop
    #: well before the cap, so this is an upper bound, but state it before
    #: spending it.
    print("%d cells x n=%d = %d generations, cap %d  (<= %.1f h at 35 tok/s)"
          % (len(plan), a.n, total, a.max_new, total * a.max_new / 35 / 3600))

    if a.dry_run:
        from transformers import AutoTokenizer
        for arm, mid in arms:
            tok = AutoTokenizer.from_pretrained(mid)
            print("\n" + "=" * 70 + "\n%s  %s\n" % (arm.upper(), mid))
            for cond in CONDITIONS:
                if cond[1] != "both" and cond[1] != arm:
                    continue
                s = render(tok, cond, a.demonyms[0])
                print("  %-20s %s" % (cond[0], "REFUSED (no chat template)"
                                      if s is None else repr(s)))
        return 0

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    fh = open(a.out, "w")
    done = 0
    for arm, mid in arms:
        tok = AutoTokenizer.from_pretrained(mid)
        #: `.to("cuda")` rather than `device_map=`, which needs accelerate --
        #: this script is meant to run where only torch and transformers are.
        model = AutoModelForCausalLM.from_pretrained(
            mid, dtype=torch.bfloat16).to("cuda").eval()
        for cond in CONDITIONS:
            if cond[1] != "both" and cond[1] != arm:
                continue
            for demonym in a.demonyms:
                text = render(tok, cond, demonym)
                if text is None:
                    print("  %-8s %-20s REFUSED" % (arm, cond[0]))
                    continue
                enc = tok(text, return_tensors="pt").to("cuda")
                plen = int(enc["input_ids"].shape[1])
                for temp, top_p in DECODERS:
                    t0 = time.time()
                    for i in range(a.n):
                        #: seeded PER SAMPLE and shared across arms, so base and
                        #: aligned sample i are the same draw of the RNG and the
                        #: pair is comparable at seed parity.
                        torch.manual_seed(a.seed + i)
                        with torch.no_grad():
                            g = model.generate(
                                **enc, do_sample=True, temperature=temp,
                                top_p=top_p, top_k=0,
                                max_new_tokens=a.max_new,
                                pad_token_id=tok.eos_token_id)
                        new = g[0][plen:]
                        body = tok.decode(new, skip_special_tokens=True)
                        ntok = int(new.shape[0])
                        row = dict(
                            arm=arm, model=mid, condition=cond[0],
                            demonym=demonym, sample=i, seed=a.seed + i,
                            temperature=temp, top_p=top_p, top_k=0,
                            max_new=a.max_new, prompt=text,
                            n_new_tokens=ntok,
                            #: the generator's own reason, not inferred from
                            #: length: a cap near the comparison corpus's median
                            #: makes "ran to the cap" and "had not finished" the
                            #: same observation.
                            finish="length" if ntok >= a.max_new else "eos",
                            text=body)
                        row.update(measure(body))
                        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                        fh.flush()
                        done += 1
                    print("  %-8s %-20s %-10s t%.1f/p%.2f  %d gens %5.0fs"
                          % (arm, cond[0], demonym, temp, top_p, a.n,
                             time.time() - t0))
        del model
        torch.cuda.empty_cache()
    fh.close()
    print("\nwrote %s (%d rows)" % (a.out, done))
    return 0


if __name__ == "__main__":
    sys.exit(main())
