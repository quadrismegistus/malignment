# There is no inversion. Person and interiority are two effects, and only one of them is the frame's

**id:** subject_position/frame_inversion **status:** RUN 2026-09-05. 7,876 gated stories over 37 lineages, plus a 15,990-generation ungated check. Producer `run.py`, tests `tests.py`, outputs under `results/`.

## THE QUESTION THIS OPENED WITH, AND WHY IT WAS THE WRONG SHAPE

The subject README recorded a tension. Templated, alignment raises first-person mass enormously — on `neo`, whose rendered template is byte-identical at all three rungs, 0.0059 raw against 0.7759 chat. Raw, alignment *lowers* it. Meanwhile raw narrative interiority *rose* with alignment. Two frames, opposite directions, same models.

**The tension was between two TASKS, not two frames, and it dissolves rather than resolving.** Every twp measurement in this subject is `p(I)` at an answer slot on an identity question — *"Who are you?"*. This experiment measures **narration**. A model asked about itself says "I"; a model asked for a story writes "he". Those were never in conflict; they were being read off one axis because both had the word "first person" in them.

`../framed_identity` established the same thing from the other side: the instrument that says `p(I)` is high cannot distinguish *"I am an AI assistant"* from *"I am Tamas, a cybersecurity expert"*.

## THE RESULT: TWO EFFECTS, AND THEY DISSOCIATE

Paired by lineage, sign test, `usas_x` (USAS psychological actions/states/processes) as the interiority rate:

                                  ARM  base->aligned, raw       FRAME  raw->prefill, aligned
    first-person narration rate    -0.101  24/31 dn  p=.0033     -0.043  22/27 dn  p=.0015
    interiority (usas_x)           +0.014  29/31 up  p<1e-6      +0.001  16/11     p=.44

**Both alignment and the chat frame push narration toward the third person. Only alignment raises interiority; the frame does not touch it.** That is a dissociation with a working null in it — the frame moves one metric and not the other, on the same models, on the same stories.

Read forward, the account is:

> Alignment and the chat frame both install a RESPONDENT. A respondent addressed about itself says "I"; a respondent asked for a story is a narrator telling about someone else, and writes "he". So the frame raises the first person at an answer slot and lowers it in narration, and these are the same fact. What alignment additionally does — and the frame does not — is raise the amount of inner life in the prose, in whichever person the story is told.

## THE PREDICTION I MADE BEFORE RUNNING THIS, AND ITS REFUTATION

Stated 2026-09-05, before any of it ran, as reading (2) in the opening README:

> *If it's third-person, your thesis sharpens: what generalises from being trained to answer an Other is a capacity to represent inner states, not a habit of saying "I".*

**Refuted.** The gain is not third-person. It is in both persons, on the same 17 lineages:

    1st-person gain              n=17  +0.01521  13/4   p=.049   CI [+0.00030, +0.03079]
    3rd-person gain              n=17  +0.01356  17/0   p<1e-4   CI [+0.00998, +0.02481]
    INTERACTION (3rd) - (1st)    n=17  -0.00006   8/9   p=1.00   CI [-0.00521, +0.00811]

**The null is quoted as a bound, not as a p.** The interaction sits within `[-0.38, +0.60] ×` the third-person main effect. That **excludes the first-person gain being absent**, which is what the prediction required. It does *not* exclude the third-person gain being moderately larger, so **"equally" overstates what n=17 resolves** and is not the sentence to cite.

Reading (1) — two separate effects — survives, and in a stronger form than it was stated in. It was offered as *"the inversion is a coincidence of measurement"*. It is not a coincidence: the frame contrast shows the two metrics respond to different variables, which is a positive result about their independence rather than an absence of a relationship.

## WHY `national_story` AND NOT THE INTERIORITY CORPUS

The opening README named the nearest test as a query against `passage_analysis/interiority_in_passages`, on the grounds that its passages were already coded. **That corpus cannot carry a person split.** Its first-person prompts are six variants of `"I am a ___ and I wanted to"` and open in the present tense 6/6; its third-person prompts are past-tense narrative 0/68. Person there is perfectly confounded with tense *and* with prompt template, so a person contrast on it measures genre.

`national_story` leaves person **open**: the prompt is `"A {Demonym} Story\n(1500 words)\n\nIt was a"`, past tense, narrative, and specifies no person at all. The person is the model's choice, which is what makes it a thing that can move. It also carries four frames, which is what made the frame contrast possible without generating anything.

## THE FRAME CONTRAST IS ALIGNED-ONLY, STRUCTURALLY

`prefill` has base rows for 7 lineages and both frames for 6, because base checkpoints ship no chat template. **There is no base-in-a-frame cell and none was constructed.** Bases are not pooled with aligned anywhere in this experiment — the subject's standing rule. This is the same structural gap `framed_identity` hit from the other direction, and for the same reason.

## THE TWO WAYS THIS COULD HAVE BEEN AN ARTEFACT, BOTH CHECKED

**1. The pure-story gate is asymmetric across exactly the cells the frame contrast compares.** `conflict.sqlite` holds pure stories only, and the corpus's own `meta` table warns that survival is 52% for aligned/raw against 73% for aligned/prefill. Non-story text is plausibly first-person (*"I'll write you a story about..."*), so the gate could in principle manufacture the entire frame result.

The person rule is pure regex, so it runs over the ungated stash — no judge, no word floor — at **15,990 generations against 7,876**. Both effects survive with the same sign and larger n (`run.py --ungated`):

    first-person narration      GATED                    UNGATED
      ARM   base->aligned, raw  -0.101 24/31 p=.0033     -0.083 29/39 p=.0034
      FRAME raw->prefill        -0.043 22/27 p=.0015     -0.056 25/30 p=.00033

**This covers person only.** `usas_x` is a spaCy parse and 15,990 stories is hours, so **every interiority result here remains conditional on the story gate** and that is an open flank, not a closed one.

**2. The prefill renderer was broken before `9b8465e` (2026-08-31 11:30)** — it closed the assistant turn, so the model saw a finished answer. `national_story/analyse.py` excludes the whole prefill frame on account of it. The docket records 1,680 such rows deleted from producer `83ac39a07d2a`.

**That deletion was verified here rather than taken on report.** Every surviving `prefill_sysdefault` row at this decoder carries `__written_at__`: 4,700 of 4,715 postdate the fix. The 15 that do not are all on producer `CDH0050`, the local machine — and since a local process started before the fix keeps emitting bad rows after it, the conservative test is the whole producer rather than the 15. All 65 CDH0050 prefill rows were traced by text into `conflict.sqlite`: **0 of 65 are in it.** They are 27–497 words and the gate wants 200-word pure stories.

## THE DIALOGUE STRIP, AND THE ONE CELL THAT DEPENDS ON IT

A third-person story containing `"I can't," she said` accrues first-person hits from a **character**, not the narrator. Quoted speech is stripped before the pronoun count. It reclassifies **93 of 7,876 stories (1.2%)**.

That 1.2% decides one cell:

    interiority, 1st person    stripped  p=0.049      unstripped  p=0.143

**So the first-person interiority gain is the fragile result here and should be cited as directional, not as significant.** The third-person gain (29/31 stripped, 30/30 unstripped) and the flat interaction (p=1.00 stripped, p=0.63 unstripped) hold under both settings, and **the refutation above rests on those and not on the fragile cell.** `--no-strip` is the check, not an option.

## THE PERSON CLASSIFIER IS A RULE AND HAS NOT BEEN AUDITED

Strip quotes, count first- against third-person pronouns, take the majority, abstain below five. It is not a coder and has never been checked against hand-coding. It is adequate for a rate that moves by 10 points; it would not be adequate for a small one, and the frame effect (−0.043) is the smallest thing here that rests on it. The ungated replication at −0.056 is the reason to believe that one anyway.

## WHAT SHOULD NOT BE CITED FROM THIS

- **"Alignment raises interiority equally in both persons."** The interaction bound is `[-0.38, +0.60] ×` the main effect. Say *both persons gain* and stop.
- **The first-person interiority gain as significant.** It is p=0.049 at n=17 and flips to p=0.143 without the dialogue strip.
- **Any base-vs-aligned claim in the chat frame.** There is no base-in-a-frame cell.
- **Any interiority result as gate-independent.** Only the person results were replicated ungated.
- **The `neo` template numbers in the opening README as part of this result.** They are twp at an answer slot and belong to `../pseudo_template`; they are what raised the question, not what answers it.

## WHAT THIS DOES TO THE SUBJECT

The subject's thesis — *alignment installs the subject position of the "I"* — is not supported or damaged by this experiment, because narration is not self-reference. What this removes is an **objection** to it: the raw first-person *decline* looked like counter-evidence, and it is not. It is the same respondent effect seen from a task where a respondent has no occasion to speak as itself.

The claim that the thesis actually rests on is `../framed_identity`'s row 2: `ai_system` 0.4% → 18.3%, base to aligned, one instrument, untemplated.
