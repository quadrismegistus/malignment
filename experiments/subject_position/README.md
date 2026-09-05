---
kind: subject
status: SIX QUESTIONS, ALL MEASURED. The thesis holds as a claim about self-DESCRIPTION and not about anchoring
headline: SFT installs a respondent, and the position is FRAME-BOUND -- inside the template the human identity is gone, outside it the model narrates about someone else
---
# subject_position

**A SUBJECT, not an experiment.** Per `experiments/LAYOUT.md`: a subject directory contains a README that indexes its questions and nothing else — no code, no data, no claims. Anything shared between the questions belongs in `malignment/`.

Promoted from `exploratory/subject_position` on 2026-09-04, where one README carried five separable findings and five producers. The thesis and the tension below were written there and are reproduced here because they are what the questions are questions *about*; every number has moved to the question that owns it.

## THE THESIS

RH: SFT's primary job is to install a subject position — to turn a next-token predictor into a **respondent**, one that speaks in relation to an Other. The mundane observation behind it: a templateless base asked *"Who are you?"* continues the question; a templated aligned model answers it.

F20 tried to settle this and substituted a `Q: ... A:` pseudo-template for the missing plain-completion arm. This subject exists because that substitution was never measured against the thing it stood in for — and because, once measured, it turned out to be the *fair* arm comparison rather than the degraded one.

## THE QUESTIONS

    pseudo_template/         What does the address supply, as against the model?
                             MEASURED. Matched base-only, n=14: Q:/A: gives
                             0.5251 median first-person mass against 0.0483
                             bare -- 10.9x. It is also the only condition in
                             which base and aligned receive an IDENTICAL
                             address, because most bases ship no chat template.

    installation_rung/       Which training rung installs the position?
                             MEASURED. SFT: 30 rise / 5 fall, median +0.2296,
                             p < 1e-4. DPO does not resolve. Predictions recorded
                             before the run; P1 held, P2 split, P4 unresolved.

    refusal_and_the_I/       Is the templated "I" a refusal phenomenon?
                             MEASURED. Removing safety data costs nine tenths of
                             the first person at a refusal prompt and GAINS a
                             little at an identity prompt. The whole effect is
                             +0.8051 templated and +0.0026 raw.

    framed_identity/         What does the deployed model say when actually
                             addressed? MEASURED. Inside the template the human
                             identity is GONE -- F20x's untemplated corpus says
                             43.3% claim a HUMAN identity on "Who are you?";
                             templated it is 0.0% against 95-97.5% ai_system.
                             An empty system slot lowers maker-naming;
                             the persona reading was WITHDRAWN 2026-09-05.

    frame_inversion/         Why do raw and chat move in OPPOSITE directions on
                             the same models? MEASURED. THEY DO NOT -- the
                             tension was between two TASKS. In narration BOTH
                             alignment and the frame push toward the third
                             person; only alignment raises interiority. A
                             prediction stated before the run was refuted.

    referential_anchoring/   Does alignment anchor persons, or signification as
                             such? ANSWERED by refusing the dichotomy (RH).
                             BOTH, and they are separate phenomena: quiet_drift
                             -0.0387 at 28/29 down and ai_system +0.2833 at
                             22/29 up on the SAME 29 lineages, spearman +0.145
                             CI [-0.225, +0.493]. A gated join, no new run.

## WHERE THE SUBJECT LANDED, AND THE PATTERN IN HOW IT GOT THERE

**The thesis holds as a claim about self-DESCRIPTION and not as a claim about anchoring.**

> Alignment installs self-reference into a first person that already exists. It does not create the "I" — the base has one, and it is a narrator's. It makes the "I" refer to the speaker: `ai_system` 0.4% → 18.3% base to aligned untemplated, while `any I` moves only 85% → 95%.
>
> Separately and not by the same mechanism, alignment makes models hold a referent — any referent, with **no** advantage to the first person and if anything a disadvantage (person-specificity −0.059, 8/29, p=0.017 in the wrong direction).

**Twice this subject was stuck on a forced choice, and both times the choice was the error rather than the evidence.**

- `frame_inversion` asked why raw and chat move in opposite directions on the first person. They do not: the twp numbers are an ANSWER SLOT and the prose numbers are NARRATION, two tasks sharing a phrase.
- `referential_anchoring` asked whether alignment anchors persons *or* signification. RH, 2026-09-05: *why can't it be both — those are separate phenomena.* Measured on one corpus, they are: both effects large on the same 29 lineages, spearman +0.145, CI [−0.225, +0.493].

In both cases the resolution was to notice that two things had been filed under one name, and in both cases the seat had been arguing inside the dichotomy rather than at it. **A tension between two of this subject's results is worth checking for a shared word before it is worth an experiment.**

## THE TENSION, AND HOW IT DISSOLVED

Templated, alignment raises the first person enormously. **Raw, alignment lowers it.** On `neo`, whose rendered template is byte-identical at all three rungs:

                            raw       chat
    neo_7b                0.0214    0.1375
    neo_7b_sft_v0.1       0.0090    0.4008
    neo_7b_instruct_v0.1  0.0059    0.7759

Meanwhile raw narrative interiority ROSE with alignment (+0.224, 16/17, `passage_analysis/interiority_in_passages`, generated with no template — verified in the producers, which pass raw strings and never call `apply_chat_template`).

**So whatever the respondent training leaves in raw prose, it is not more first-person speech.** Outside the turn the model becomes *less* willing to say "I" while writing *more* inner life. Either those are separate effects of alignment, or the trace is in something other than the pronoun.

**RESOLVED 2026-09-05 by `frame_inversion/`, and the tension was never between two frames.** The numbers above are `p(I)` at an answer slot on IDENTITY QUESTIONS; the interiority result is NARRATION. A model asked about itself says "I"; a model asked for a story writes "he". Measured on one corpus that carries both frames and leaves person open (`national_story`), the chat frame **also** lowers first-person narration — so raw and chat do not oppose each other at all, and the apparent inversion was two different tasks read off one axis because both were called "first person".

                                  ARM  base->aligned, raw     FRAME  raw->prefill, aligned
    first-person narration rate    -0.101  24/31 dn p=.0033   -0.043  22/27 dn p=.0015
    interiority (usas_x)           +0.014  29/31 up p<1e-6    +0.001  16/11    p=.44

The first reading — separate effects — survives and is stronger than stated: they are not *coincidentally* separate, they respond to **different variables**. The second — that the interiority gain would be third-person — was **refuted**; both persons gain.

**This does not support or damage the thesis**, because narration is not self-reference. It removes an *objection*: the raw first-person decline looked like counter-evidence and is not. The claim the thesis rests on is `framed_identity/`'s base→aligned untemplated row, `ai_system` 0.4% → 18.3%.

## THE STANDING RULE: BASES ARE NOT POOLED WITH ALIGNED IN RESULTS

RH, 2026-09-05. Every statistic in this subject is either **base-only**,
**aligned-only**, or an explicit **paired contrast between them**. A median over
a set that mixes arms describes neither and is never the answer to a question
anyone asked.

It bit twice on the day the rule was written, both in `pseudo_template/`:

- A line read `median 0.512 (145 models)` under the heading "base models". `145`
  is the CORPUS — models with cells on that prompt — and pools 50 bases with 95
  post-trained checkpoints. `0.512` was not a base median at all; it was the
  median parent mass on SFT edges (n=35), lifted out of a headroom table.
  Base-only over all 50 is **0.5497**; matched to the 14 bases that also have a
  bare-prompt cell it is **0.5251**, and that matched figure is the citable one
  because the address is then the only variable. Pooled is 0.6955, which would
  have understated the address effect by inflating its own baseline.

- In `framed_identity/`, F20x's base rate was printed as a parenthetical beneath
  a table of templated ALIGNED rates. Nothing was pooled, but the adjacency
  invited the one comparison that is unreadable: base-untemplated against
  aligned-templated moves the arm AND the frame together. It now prints as a 2x2
  with the base-templated cell shown as **NO SUCH CELL**, which is the truth —
  41 of 50 roster bases ship no chat template, so it cannot be run.

**A base and an aligned model may sit in one table only when the table shows
which is which and one variable separates them.**

## THE INSTRUMENT BOUND: p(I) CANNOT TEST THE THESIS

RH, 2026-09-05, on the `framed_identity` numbers: *the base model's "I am Tamas" / an invented human is fabulation, arguably not a self-referential subject position.*

**That objection condemns an instrument three of these questions are built on.** `pseudo_template`, `installation_rung` and `refusal_and_the_I` all measure a next-word probability — twp, one position. **`p(I)` cannot tell "I am an AI assistant" from "I am Tamas, a cybersecurity expert". Both are ~1.0.**

On that instrument the thesis reads as REFUTED: 34 of 50 bases already put >0.5 on the first person when addressed at `Q:/A:`, so alignment would be "installing" something already present. Coded for KIND instead, it is supported — `any I` is nearly flat across the arm (85% → 95%) while `ai_system` moves **0.4% → 18.3%**.

So the three twp questions measure **how much first-person mass an address or a rung supplies**, which is a real quantity and their results stand as answers to that. None of them is evidence about self-reference. The scope sentence is now in each of their READMEs; it was added there rather than only here because a claim cited from a question's own folder never passes through this index.

## WHAT SHOULD NOT BE CITED, WHATEVER QUESTION IT APPEARS UNDER

- **The Tulu ablation ORDERING.** Spearman rho = **−0.10** between the pseudo-template and bare-chat conditions on the same five models. One checkpoint per ablation cannot separate an effect from a checkpoint. The no-safety CROSSOVER is within-model and does not rest on this; any ordering of the four ablations does.
- **Any conversational-"I" claim.** First-token probability cannot see a mid-turn `I'd suggest`, which is where wildchat's contribution would live.
- **P3**, withdrawn before any result was read: 11 of 14 bases ship no template, so a chat-frame base-to-SFT delta does not exist for most lineages.
- **The F20 beam corpus** (556k beams) for anything passage-scale: 8 words, 28% distinct openings, 21% of a cell on one four-word opening. Its raw-mode "50% empty mass" is not reproduced by either the twp distributions or fresh generations.
- **"Alignment raises narrative interiority equally in both persons."** The interaction is bounded within `[-0.38, +0.60] ×` the third-person main effect at n=17 — enough to exclude the first-person gain being *absent*, not enough to call them equal. Say *both persons gain*. And the first-person cell itself is p=0.049 stripped against p=0.143 unstripped, so cite it as directional only.
- **Any `frame_inversion/` interiority result as gate-independent.** Only the PERSON contrasts were replicated on the ungated stash; `usas_x` is a spaCy parse and stayed conditional on the pure-story gate, which admits 52% of aligned/raw against 73% of aligned/prefill.
- **Any pooled `system=""` vs `system=DEFAULT` contrast.** Added 2026-09-05 after `framed_identity` posted one and withdrew it. The two arguments produce THREE different treatments, and which one a model gets is a property of its template, not of the call: a persona is blanked (4 of 17 models here), an empty block is inserted where there was no system turn (10), or the template drops the empty system and the two render BYTE-IDENTICALLY (3). Pooling them mixes a manipulation with its own null. Classify on the RENDER — `roster/models/chat_renders.json`, `render != render_empty` — and report the identical group as the null it is. Note that `clean_via` in the same file answers a *different* question (can a clean slot be reached, and how) and does not separate the last two.
