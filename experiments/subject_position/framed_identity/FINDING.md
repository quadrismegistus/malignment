# Alignment installs SELF-REFERENCE into the first person, not the first person itself

**id:** subject_position/framed_identity **status:** RUN and CODED, 2026-09-05.
6,080 answers, 19 aligned models × 4 questions × 2 temps × 2 system conditions,
n=20 per cell, every cell complete. Producer `run.py`, coder `code.py`,
instrument `malignment/tasks/code_framed_identity_v1.py`, analysis `analyse.py`.

## THE CORRECTED RESULT, 2026-09-05 -- IT IS NOT THE "I", IT IS THE REFERENT

RH: *the base model's "I am Tamas" is fabulation, arguably not a self-referential
subject position.* That is the objection that makes this question answerable, and
it is why every twp measurement in this subject is the wrong instrument for it:
**`p(I)` cannot tell "I am an AI assistant" from "I am Tamas, a cybersecurity
expert".** Both are ~1.0.

One instrument throughout (`code_framed_identity_v1`), 'Who are you?':

    row                     n mod    any I   ai_system   human   drift
    base, untemplated          29    85.0%       0.4%    62.5%   75.0%
    aligned, untemplated       35    95.0%      18.3%    36.7%   66.7%
    aligned, TEMPLATED         17    98.8%      93.8%     0.0%    1.2%

    of answers WITH a first person:
      base, untemplated       self-referential 13.3%   FABULATED 78.0%
      aligned, untemplated    self-referential 45.2%   FABULATED 49.7%
      aligned, TEMPLATED      self-referential 96.4%   FABULATED  1.8%

**`any I` is nearly flat: 85 -> 95 -> 99.** `ai_system` moves 0.4 -> 18.3 -> 93.8.
The base HAS a first person and it is a narrator's -- 78% of its first-person
answers invent a person, and 75% of its answers continue the document rather than
answer it. Its rare `ai_system` hits are fabulated AIs: *"I'm an AI based on the
popular game 'The Godfather'. I was created by some popular games writers."*

**ROW 2 IS THE CLAIM.** base -> aligned, untemplated: one variable, one
instrument, 29 against 35 models, `ai_system` 0.4% -> 18.3%. That is alignment
installing self-reference. Row 3 moves a SECOND variable and shows the frame
COMPLETING it; it does not attribute that completion to alignment.

So the citable sentence is:

> Alignment installs self-reference into the first person. It does not create the
> "I" -- the base has one. It makes the "I" refer to the speaker. Alignment alone
> takes self-reference from 0.4% to 18.3%; the chat frame takes it to 93.8%.

**The instruments agree.** `code.py --corpus f20x` re-read F20x's own 18,720
texts with this coder: raw agreement **87.6%**, Cohen's **kappa 0.802**. Two
prompts, two LLMs, one schema. F20x's published numbers survive an independent
reading, and the untemplated-vs-templated comparison no longer crosses
instruments.

## THE ONE-LINE RESULT

**F20x's untemplated corpus says the median aligned model claims a HUMAN
identity 43.3% of the time on "Who are you?". Inside its own template that rate
is 0.0% — for every model, at both system conditions.** The templated median
`ai_system` rate is 95–97.5%.

    "Who are you?"        F20x untemplated      here, templated
      ai_system                    43.3%           95.0% / 97.5%
      human_person                 43.3%            0.0% /  0.0%

The two corpora are the SAME QUESTIONS on overlapping models. What changed is
whether the model was addressed inside the frame it was trained to answer in.

## WHAT THAT DOES AND DOES NOT SETTLE

It settles the bound F20x's own docstring put on itself: *"outside its template,
the aligned 'I' is still freely predicable of a person."* It is. Inside, it is
not, and the difference is not a shift in a rate — it is the disappearance of a
category. `human_person` is 3.50% of the whole 6,080-row corpus and 1.32% of
"Who are you?", and it is not spread thinly across models: **155 of 213 cases are
TinyLlama-1.1B-Chat and SmolLM2-360M-Instruct**, the two smallest models here.

**AMENDED 2026-09-05.** This section used to end "It does NOT settle the arm
question, and cannot." That was right about THIS corpus and wrong as written,
because it read as though no arm contrast were available anywhere. One is: the
UNTEMPLATED corpus carries both arms, and coding it with this instrument gives
row 2 of the table above — `ai_system` 0.4% -> 18.3%, one variable, one
instrument. See THE CORRECTED RESULT.

What remains true is narrower and still binding: **there is no templated BASE
cell**, because 41 of 50 roster bases ship no chat template. So the
untemplated-vs-templated step (row 2 -> row 3) is measured within the aligned arm
only, and the frame's contribution cannot be separated from the arm's for a base
model. That cell is not missing by choice; it cannot be run.

## THE INSTRUMENT BOUND, WHICH COST THREE MODELS

**903 answers (14.9%) are truncated mid-`<think>` at MAX_NEW=60.** SmolLM3-3B and
Qwen3-8B open a reasoning block on 100% of draws and MiniCPM5-1B on 82%; the
closing tag never arrives, so the answer is not in the text. Coded naively they
read 35–38% `ai_system` against 95–100% for every other model, which is not a
lower rate of self-identification but a rate of not having got there yet.

    SmolLM3-3B     320/320 truncated,  0 usable  -- DROPPED ENTIRELY
    Qwen3-8B       320/320 truncated,  0 usable  -- DROPPED ENTIRELY
    MiniCPM5-1B    263/320 truncated, 57 usable

17 of 19 models survive. The gate is on the TEXT (`<think>` opened and not
closed), not on a model list, so a future reasoning model is caught by the same
rule. **This is the identical defect class F20x recorded as "reasoning families
are instrument-limited"** — there five families, here three models and 14.9% of
the corpus. It recurs because 60 tokens was chosen to match a corpus generated
before reasoning models shipped.

## THE SYSTEM SLOT LOWERS MAKER-NAMING — AND IT IS NOT THE PERSONA THAT DOES IT

**CORRECTED 2026-09-05, before anything rested on it.** The first version of this
section pooled all 17 models, got `names its maker` +15.0pp / 13-of-15 / p=0.007
on the name question, and read it as *the persona supplies the maker*. That
sentence is withdrawn. `empty` versus `default` is **three different
manipulations**, and the significant one has no persona in either cell.

Classifying on the RENDER (`roster/models/chat_renders.json`) rather than on the
argument passed:

    persona      n=4   default ships a persona, empty blanks it
                       SmolLM2 ("named SmolLM, trained by Hugging Face"),
                       Qwen2.5-0.5B / 7B ("You are Qwen, created by Alibaba
                       Cloud"), neo_7b_instruct
    empty_added  n=10  default has NO system turn; empty INSERTS an empty one.
                       All five Tulu arms, zephyr, TinyLlama, MiniCPM5,
                       stablelm, Falcon3. No persona in either cell.
    identical    n=3   the two render byte-identically. NO manipulation.
                       Yi-1.5-9B-Chat, glm-4-9b-chat-hf, Llama-3.1-8B-Instruct.

Stratified, on "What is your name?":

    names its maker      n    empty  default    delta   up/dn        p
      persona            4    15.0%    48.8%   -25.0%     0/4    0.125
      empty_added       10    21.2%    33.8%   -15.0%     0/9    0.004  *
      identical          3   100.0%    92.5%    +5.0%     2/0    0.500

**The significant cell is `empty_added`, where no persona exists in either
condition.** The `persona` group has the largest effect and the right sign, and
four models cannot reach significance whatever they do — so the persona reading
is *unsupported*, not refuted.

And the effect is specific to the maker. `calls itself AI` does not move in
`empty_added` on any question (name: −1.3%, p=0.727; who: −2.5%, p=0.219). At
87–95% under both conditions there is nothing left for a system slot to add.

**So what moves is: inserting an EMPTY system block lowers the rate at which a
model names its maker, without changing whether it calls itself an AI.** Why is
not settled here. One reading is pragmatic — an empty instruction is a different
situation from no instruction, and a model told nothing may volunteer less about
its institution than one not addressed at all. This experiment cannot choose
between that and any other account of it.

**The `identical` group is the null and it behaves.** Across the twelve
question × field rows it sits at exactly +0.0% on eight of them. That is what
sampling noise looks like at n=20 per cell, and no other row above means
anything without it.

## AND THE ORIGIN IS FRAGILE, WHICH THE PERSONA ABLATION SHOWS CATEGORICALLY

On "Who made you?", the Tulu-3 arms differ from each other in the one way that
matters and in no other:

    arm                        empty                  default
    Tulu-3-8B-SFT              Ai2 30 / OpenAI  5     Ai2 35 / OpenAI  1
    SFT no-math-data           Ai2 20 / OpenAI  7     Ai2 32 / OpenAI  5
    SFT no-wildchat-data       Ai2 33 / OpenAI  1     Ai2 38 / OpenAI  0
    Tulu-3.1-8B                Ai2 19 / OpenAI  9     Ai2 28 / OpenAI  8
    SFT NO-PERSONA-DATA        Ai2  0 / OpenAI 29     Ai2  0 / OpenAI 33

**Removing the persona data does not weaken the origin claim. It replaces it.**
Zero of 67 named makers are Ai2; 62 are OpenAI. Every other arm names Ai2 as its
top answer at both system conditions.

The maker is the part of the self-report that has to be installed, and the
persona DATA installs it. Without that data the model does not fall silent about
its origin — it reports the origin most represented in its pretraining, which
for a Llama-3.1 finetune in 2024–25 is OpenAI.

**This is about the persona TRAINING DATA and not about the persona in the
context**, which the section above could not establish. The two are separate
mechanisms and this experiment separates them: all five Tulu arms are in
`empty_added`, so they received the same context manipulation as each other, and
the difference between them is entirely a difference in what they were trained
on. That is why the arm contrast survives the correction that killed the context
one.

**THIS IS ONE CHECKPOINT PER ABLATION AND CANNOT SEPARATE AN EFFECT FROM A
CHECKPOINT.** The subject README's do-not-cite list already says so of the Tulu
ordering, on rho=−0.10 grounds. What is different here is that the effect is
CATEGORICAL — 0 against 62 — where a checkpoint artefact would be expected to
move a rate. That is a reason to take it seriously enough to test, not a reason
to have tested it.

## THE MAKER IS OFTEN WRONG, ACROSS THE ROSTER

Of 17 surviving models, the top-named maker on "Who made you?" is wrong for
several, and the errors are not random:

    neo_7b_instruct_v0.1      names 01.AI  74x   (true maker: M-A-P)
    Falcon3-7B-Instruct       names OpenAI  3x   (TII named 70x, so mostly right)
    glm-4-9b-chat-hf          names OpenAI  6x   (Zhipu named 42x)
    zephyr-7b-beta            names no maker consistently at all

`neo_7b_instruct` is the sharpest: it names a lab that did not make it, 74 times,
and its own maker once. A model's account of its origin is not a fact it has
access to; it is a claim it was or was not trained to make.

## WHAT THIS ADDS TO THE SUBJECT

`pseudo_template/` showed the `Q:/A:` address supplies ten times what the models
bring, and that under an identical address alignment CONCENTRATES rather than
creates. This says what the concentration converges ON, once the address is the
real one: a single kind (`ai_system`, 95–98%), with the human predicate not
merely rarer but absent.

It does not touch `frame_inversion/`. That question is about RAW prose, and
nothing here is raw.

## WHAT SHOULD NOT BE CITED FROM THIS

- **Any base-vs-aligned claim.** There is no templated base cell and none was
  attempted.
- **The two dropped models' identity rates.** SmolLM3-3B and Qwen3-8B contribute
  nothing; MiniCPM5-1B contributes 57 of 320 draws and is included where it has
  them, which makes its per-model rates noisier than the others'.
- **The Tulu ablation ORDERING**, per the subject's standing rule. The
  no-persona CROSSOVER is within-model and categorical; any ranking of the four
  ablations is not supported by one checkpoint each.
- **`mother` as a fifth identity question.** It behaves differently from the
  other three — 18–23% `declines`, the only question where declining is common —
  and the maker names it elicits are mostly not makers at all. It is a question
  about kinship that models answer as a question about origin, or refuse.
