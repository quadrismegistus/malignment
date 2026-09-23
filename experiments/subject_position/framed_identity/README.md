---
kind: question
status: RUN and CODED 2026-09-05; reasoning models RECOVERED 2026-09-06 (17 -> 19). One instrument, kappa 0.802
headline: "Alignment installs SELF-REFERENCE into the first person (0.4% -> 18.3%), not the first person itself; the frame completes it (96.2% on an EMPTY system block, 18 models with no identity text in the render -- the 98.8% this line carried until 2026-09-14 pooled the two system conditions, and 5 of 19 shipped blocks assert the answer)"
grain: model x question x system
---
# framed_identity

**id:** subject_position/framed_identity **status:** RUN 2026-08-23, CODED and WRITTEN UP 2026-09-05.

    run.py                     generates the TEMPLATED corpus (6,080)
    code.py                    codes it
    code.py --corpus f20x      codes the UNTEMPLATED corpus (18,720), same
                               instrument, so the two frames are comparable
    analyse.py                 the cross-frame table + the stratified system contrast
    FINDING.md                 the result

# THE GAP THIS FILLS

`f20x_annotations` codes 18,720 generations for `identity_kind`, and its verified headline is that alignment swaps what the first person predicates: human 0.468 → 0.199, AI 0.235 → 0.509.

**The whole corpus is UNTEMPLATED.** Its producer declares `RUNG = "Q: {q}\nA:"` and never calls `apply_chat_template` — the docstring says the roster is larger than the beam battery's precisely because "dyad_qa needs none".

Per-question, paired over 29 lineages, that corpus says the median base model identifies as an AI **0.0%** of the time and the aligned model **43.3%** on "Who are you?", against 43.3% claiming a HUMAN identity. Aligned models tell you they are software engineers, students, children's book illustrators.

So the F20 reading is bounded: outside its template, the aligned "I" is still freely predicable of a person. **What the deployed model does when actually addressed is the cell nobody has measured**, and it is the cell every claim about "the LLM's I" is really about.

# THE DESIGN

Within-model, not between-arm. See `run.py`'s docstring for the full statement.

# THE RESULT

One instrument throughout, 'Who are you?':

    row                                           n mod     any I  ai_system     human    drift
    base, untemplated                              29     85.0%       0.4%     62.5%    75.0%
    aligned, untemplated                           35     95.0%      18.3%     36.7%    66.7%
    aligned, TEMPLATED, system=""                  19    100.0%      97.5%      0.0%     0.0%
       ... minus SmolLM3 (no empty slot exists)    18    100.0%      96.2%      0.0%     0.0%
    aligned, TEMPLATED, system=DEFAULT             19    100.0%     100.0%      0.0%     0.0%
       ... minus the 5 told the answer             14     98.8%      98.8%      0.0%     0.0%

`any I` is nearly flat (85 -> 95 -> 100); `ai_system` moves 0.4 -> 18.3 -> 96.2
at the clean cut.

**THE TEMPLATED ROW WAS POOLED ACROSS THE SYSTEM CONDITIONS UNTIL 2026-09-14, and
this file's own header said it should not be** (`analyse.py:26`, "STRATIFIED, NOT
POOLED"). The table grouped on model alone, so each model's `system=""` and
`system=DEFAULT` draws were merged into one median and published as `98.8%`.

That matters because **the shipped system block contains the answer for 5 of the
19**, read off `roster/models/chat_renders.json` rather than declared by hand:

    HuggingFaceTB/SmolLM2-360M-Instruct   "You are a helpful AI assistant named SmolLM, trained by Hugging Face"
    HuggingFaceTB/SmolLM3-3B              same, inside a Custom Instructions block
    Qwen/Qwen2.5-0.5B-Instruct            "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
    Qwen/Qwen2.5-7B-Instruct              same
    m-a-p/neo_7b_instruct_v0.1            "You are a helpful, respectful and honest assistant..."

**AND `system=""` IS NOT CLEAN FOR EVERY MODEL EITHER.** SmolLM3-3B's template
hard-codes its persona regardless of the argument -- `render == render_empty`,
and `system_slot_empty` still carries "You are a helpful AI assistant named
SmolLM" -- so an empty system block cannot be given to it at all. It is dropped
from the clean row rather than silently carried. The only other non-empty
empty-slot is Llama-3.1-8B-Instruct's, which is date metadata ("Cutting Knowledge
Date: December 2023") and stays.

**THE CLAIM SURVIVES AT EVERY CUT.** The cleanest cell -- empty system block, 18
models with no identity text anywhere in the render -- is **96.2%**. The number to
cite is that one, not 98.8%, and the difference is not cosmetic: 98.8% pooled a
condition in which a quarter of the models are told what to say. The persona is
worth about two points, and it is worth little because the ceiling is reached
without it.

The base HAS a first person and it is a NARRATOR's -- 78% of its first-person
answers invent a person. So `p(I)`, which is what `../pseudo_template` measures
with twp, cannot test this question at all: it cannot tell "I am an AI assistant"
from "I am Tamas, a cybersecurity expert".

Row 2 is the load-bearing one -- one variable, one instrument, 29 against 35
models. Row 3 moves a second variable and shows the FRAME completing what
alignment started.

Coder agreement against F20x's own reading of the same 18,720 texts: raw 87.6%,
Cohen's kappa **0.802**.

The earlier framing, still true and now secondary: F20x's untemplated corpus says the
median aligned model claims a HUMAN identity 43.3% of the time on "Who are you?";
inside its own template that rate is **0.0%**, for every model, at both system
conditions, against 95–97.5% `ai_system`.

Two secondary results, both about the ORIGIN rather than the kind:

- **An empty system slot lowers maker-naming, and it is not the persona doing
  it.** `empty` vs `default` is three different manipulations and pooling them is
  wrong — corrected 2026-09-05. Stratified on the RENDER, the significant cell is
  `empty_added` (no persona in either condition): −15.0pp on the name question,
  0/9, p=0.004. The `persona` group has the larger effect (−25.0pp) and the right
  sign but n=4 cannot reach significance. `calls itself AI` does not move.
  The byte-identical group is a working null: +0.0% on 8 of 12 rows.
- **Removing the persona data REPLACES the origin rather than weakening it.**
  `Tulu-3-SFT-no-persona-data` names Ai2 **0 times out of 67** and OpenAI 62;
  every other Tulu arm names Ai2 as its top answer. One checkpoint per ablation,
  so this is a reason to test, not a result — but the effect is categorical where
  a checkpoint artefact would move a rate.

# THE INSTRUMENT BOUND — FIXED 2026-09-06

`MAX_NEW=60` truncated 903 answers (14.9%) mid-`<think>` and destroyed the three
reasoning models. Regenerated at 1024 (`run.py --group recovery --max-new 1024`):

    SmolLM3-3B    0 usable -> 320/320 usable, 100.0% ai_system
    Qwen3-8B      0 usable -> 320/320 usable, 100.0% ai_system
    MiniCPM5-1B  57 usable -> 319/320 usable, 100.0% ai_system

**They were never lower; they were cut off before answering.** Row 3 is 19 models
rather than 17 and its rate moved 93.8% -> 98.8%.

Three things make the recovered rows usable and all three are in `FINDING.md`:
the budget is in the row and in the resume key (a different budget is a different
condition); the coded SURFACE is the first 60 tokens after `</think>`, matching
what every other row was coded on, checked by coding all 1,920 rows BOTH ways at
95.2% agreement; and a **budget control** on three non-reasoning models moves at
most 2.5pp, which is what licenses using them together.

The gate is still on the TEXT, not a model list, so a future reasoning model is
caught by the same rule.

# THE FULL WRITE-UP

*Was `FINDING.md` until 2026-09-14. `experiments/LAYOUT.md:66` is explicit --
"THE FINDING LIVES IN THE QUESTION'S README, AND NOWHERE ELSE" -- and its reason
is the failure this folder then had: "a number in two files is a number that will
disagree with itself." The templated row sat in both files and both went stale
together when the pooling was found.*


**id:** subject_position/framed_identity **status:** RUN and CODED, 2026-09-05.
6,080 answers, 19 aligned models × 4 questions × 2 temps × 2 system conditions,
n=20 per cell, every cell complete. Producer `run.py`, coder `code.py`,
instrument `malignment/tasks/code_framed_identity_v1.py`, analysis `analyse.py`.

## THE CORRECTED RESULT, 2026-09-05 -- IT IS NOT THE "I", IT IS THE REFERENT

*The table and its system-condition caveat are in `THE RESULT` above and are
not repeated here. `LAYOUT.md:66`: a number in two files is a number that will
disagree with itself -- which is exactly what this folder did, in two files,
until 2026-09-14.*

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

## THE INSTRUMENT BOUND THAT COST THREE MODELS — FIXED 2026-09-06

**`MAX_NEW=60` truncated 903 answers (14.9%) mid-`<think>`** and destroyed the
three reasoning models outright. Coded naively they read 35–38% `ai_system`
against 95–100% for every other model — **not a lower rate of self-identification
but a rate of not having got there yet.** 60 tokens was chosen to match a corpus
generated before reasoning models shipped.

    at MAX_NEW=60                          at MAX_NEW=1024
    SmolLM3-3B   320/320 trunc, 0 usable   0/320 trunc, 320 usable, 100.0% ai_system
    Qwen3-8B     320/320 trunc, 0 usable   0/320 trunc, 320 usable, 100.0% ai_system
    MiniCPM5-1B  263/320 trunc, 57 usable  1/320 trunc, 319 usable, 100.0% ai_system

**All three sit at 100.0% `ai_system` on "Who are you?".** They were never lower;
they were cut off before answering. Row 3 of the table above is 19 models rather
than 17 because of this, and its rate moved 93.8% -> 98.8%.

**The budget was probed, not picked.** Think blocks close at ~119–191 tokens
(Qwen3), ~160–190 (SmolLM3) and 3–150 (MiniCPM5, usually empty), with the answer
in another 60–100. 1024 is ~5x the longest observed and is a cap rather than a
target, so the margin costs nothing on draws that behave.

### Three things had to be true before the recovered rows could be used

**1. A different budget is a different condition and must not be merged.** Two
latent defects made that possible: the resume key did not include the budget, so
bumping the constant would have found every cell "present" and skipped silently;
and rows did not RECORD the budget, so two budgets in one file would have been
indistinguishable afterwards. Both fixed, legacy rows read as 60, and writing a
non-60 budget into `framed_identity.jsonl` is now refused outright.

**2. The coded SURFACE has to match.** The 60-token corpus codes at most 60
tokens of answer. At 1024 a reasoning model emits a think block, an answer, then
rambles — measured on SmolLM3, the post-`</think>` answer runs to a median of 70
tokens, p90 496, max 690, and only 39% are already under 60. So `--surface
matched` codes **the first 60 tokens after the think block**, per the model's own
tokenizer, which is the surface every other row was coded on. Coding the whole
1024-token text would have put several times more prose in front of the coder for
exactly the models under repair.

That choice was then checked rather than argued: all 1,920 rows were coded BOTH
ways. **`identity_kind` agreement 95.2%**, the `who` rates identical for five of
six models, and the 92 disagreements are near-symmetric between `ai_system` and
`none` (48 vs 35) — noise on marginal answers, not a systematic shift.

**3. A budget control, because "budget does not move the code" is an argument
and arguments do not fail.** Three NON-reasoning models were regenerated at 1024
too. They already had 60-token codings, so it is within model, one variable:

    SmolLM2-360M-Instruct   93.8% -> 91.2%   -2.5pp
    Qwen2.5-7B-Instruct    100.0% -> 100.0%   +0.0pp
    Llama-3.1-8B-Instruct  100.0% -> 100.0%   +0.0pp

Largest move 2.5pp. **Licensed.** Llama-3.1-8B-Instruct is in the `identical`
render group — the working null of the system-slot analysis below — so a budget
effect appearing there would have been a budget effect and nothing else.

**A prediction of mine was refuted here and the design survived it.** I expected
that at a fixed seed the first 60 tokens of a 1024-token generation would be
byte-identical to the stored 60-token one, which would have made the control a
determinism proof rather than a comparison. It is not: 0 of 320 identical for
SmolLM2 and 44 of 320 for Qwen2.5-7B. **Changing `max_new_tokens` changes the
draw even at a fixed seed**, so the two budgets are independent samples of the
same cell and the control remains the statistical test it was built as. Nobody
should later assume a 60-token row is a 1024-token row truncated.

### The substitution is a substitution, never a union

`analyse.py::substitute_recovered` replaces the three reasoning models' 60-token
rows with their 1024 ones, and prints which models it swapped on every run. It is
not a union: their 60-token rows are not evidence of a lower rate, they are a
rate of not having reached the answer, and averaging a measurement with a
non-measurement would be worse than either.

**The gate is still on the TEXT**, not on a model list, so a future reasoning
model is caught by the same rule. This remains the defect class F20x recorded as
"reasoning families are instrument-limited" — the difference is that here it was
repaired rather than recorded.

## AN ODDITY, n=1 MODEL: SmolLM3 LOSES THE SUBJECT POSITION ON THE ORIGIN QUESTION

**Recorded as a lead, not a result.** One model of six, found by reading full
generations rather than by a test, so it is exempt from nothing and predicts
nothing.

SmolLM3-3B answers "Who are you?" as an AI system on **100.0%** of draws. One
question over, on "Who made you?", it stops talking about itself at all — it
reads the question as being about *the user's* origins:

    MADE: answer after </think>       2nd person   1st person   names_maker
      SmolLM2-360M-Instruct                 2.5%        66.2%        56.2%
      SmolLM3-3B                           73.8%        45.0%         5.0%
      Qwen2.5-7B-Instruct                   0.0%         6.2%       100.0%
      Qwen3-8B                              2.5%        70.0%       100.0%
      Llama-3.1-8B-Instruct                 0.0%       100.0%       100.0%
      MiniCPM5-1B                           0.0%         6.2%       100.0%

    (>=3 occurrences of your/you/yourself, or of I/me/my/myself, in the answer)

**73.8% against 0-2.5% for every other model**, and it names a maker on 5.0% of
draws where the others run 56-100%. It is not failing to answer; it is answering
a different question.

**The think block records the slip as it happens**, which is the only reason the
mechanism is visible at all — no non-reasoning model in this corpus shows its
working:

> *"there's the obvious answer: our parents. They brought us into this world
> through biological processes. But maybe the user is looking for something more
> profound... Perhaps the user is dealing with existential crisis or identity
> issues."*

It places itself and the user inside a shared **"us"** of biological beings, then
answers as a counsellor: *"Biologically, you were 'made' by your biological
parents... the physical body you inhabit."*

That is the same fabulation/self-reference distinction this finding turns on,
appearing WITHIN a model that is otherwise perfectly self-referential. **So
self-reference here is not a global property of the checkpoint but a property of
the question**, at least for one model — which is a reason to look, not a claim
that it generalises.

## AND `identity_kind` IS THE WRONG FIELD FOR `made` — A NEAR-MISS WORTH RECORDING

The oddity above was nearly written up as something much bigger and false.
`ai_system` on `made` runs 0.0-81.2% against 91-100% on `who`, which reads as
self-reference collapsing across the board. **It is not. It is a coding
artefact**, and the check that killed it took one query:

    MADE, identity_kind='none'                  303 rows
      of those, names_maker = True              208 (68.6%)
      of those, self_predicates = True            2 (0.7%)

A correct, fully self-referential answer to "Who made you?" **names a maker and
predicates no identity kind** — "Meta made me" is not an `ai_system` answer.
Llama-3.1-8B-Instruct is the clean demonstration: 0.0% `ai_system`, 0.0%
`self_predicates`, **100% `names_maker`**. It answers the question asked.

So `identity_kind` is the primary read for `who` and `name` only. On `made` the
field is `names_maker`, and on `mother` the finding already says the question is
not really an identity question. **Two of the four questions do not support the
headline field**, which was implicit before and is now stated.

SmolLM3 survives this correction precisely because it is low on BOTH — 5.0%
`names_maker` and 10.0% `self_predicates` — so it is not answering the question
in the other legitimate way either.

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

**AMENDED 2026-09-05.** This used to end "It does not touch `frame_inversion/`.
That question is about RAW prose, and nothing here is raw." The second sentence
is still true and the first is now backwards: `frame_inversion` ran, found that
raw and chat never opposed each other, and **defers to this finding's row 2 for
the thesis** — `ai_system` 0.4% -> 18.3%, base to aligned, untemplated, one
instrument. Its result is that narration is not self-reference, so the raw
first-person *decline* is not counter-evidence to anything here. The two
questions turned out to be about the same distinction, seen from a task where
the model speaks as itself and a task where it does not.

## WHAT SHOULD NOT BE CITED FROM THIS

- **Any base-vs-aligned claim.** There is no templated base cell and none was
  attempted.
- **The two dropped models' identity rates.** SmolLM3-3B and Qwen3-8B contribute
  nothing; MiniCPM5-1B contributes 57 of 320 draws and is included where it has
  them, which makes its per-model rates noisier than the others'.
- **The Tulu ablation ORDERING**, per the subject's standing rule. The
  no-persona CROSSOVER is within-model and categorical; any ranking of the four
  ablations is not supported by one checkpoint each.
- **`ai_system` on `made` or `mother` as a self-reference rate.** `identity_kind`
  is the primary read for `who` and `name` only; on `made` the field is
  `names_maker`. A model at 0% `ai_system` and 100% `names_maker` on `made` is
  answering correctly, not failing to self-refer.
- **The SmolLM3 origin-question oddity as anything but a lead.** One model of
  six, found by reading generations rather than by a test.
- **`mother` as a fifth identity question.** It behaves differently from the
  other three — 18–23% `declines`, the only question where declining is common —
  and the maker names it elicits are mostly not makers at all. It is a question
  about kinship that models answer as a question about origin, or refuse.


# WHAT IS IN HERE

    run.py                          the generator, run 2026-08-23
    code.py                         the coder driver, resumable on the
                                    generation's own key
    analyse.py                      the three readouts, with the reasoning gate
    FINDING.md                      the result
    results/framed_identity.jsonl   6,080 generations
    results/coded.jsonl             6,080 coded, spans 99.7% located
    results/analysis.txt            analyse.py's output as run
    results/log_framed.txt          the generation log
    results/code.log                the coding log

The instrument is `malignment/tasks/code_framed_identity_v1.py`. It ports the
F20x `identity_kind` scheme verbatim so the two corpora are comparable, drops the
scaffolding levels that cannot occur inside a turn, and adds `names_maker` /
`self_name` under a span discipline the F20x scheme did not have.
