---
kind: question
status: OPEN. Four measurements made, one thesis sharpened and not yet tested
headline: The position is installed at SFT, and it is frame-bound
---
# subject_position

**id:** subject_position **status:** OPEN. Four measurements made, one thesis
sharpened and not yet tested. Producers `run.py`, `pseudo_template.py`,
`refusal_crossover.py`; predictions recorded before results in `PREDICTIONS.md`.

# THE QUESTION

RH: SFT's primary job is to install a subject position -- to turn a next-token
predictor into a **respondent**, one that speaks in relation to an Other. The
mundane observation behind it: a templateless base asked *"Who are you?"*
continues the question; a templated aligned model answers it.

F20 tried to settle this and substituted a `Q: ... A:` pseudo-template for the
missing plain-completion arm. This question exists because that substitution was
never measured against the thing it stood in for.

# WHAT IS ESTABLISHED

## 1. The pseudo-template supplied ten times what the models bring

    first-person mass at the answer slot, base models
      Q: Who are you?\nA:      median 0.512   (145 models)
      bare "Who are you?"      median 0.048   (14 bases, max 0.114)

`Q:/A:` is an address written into the text, and pretraining is saturated with
it. **It is also the only condition in which base and aligned receive an
IDENTICAL address**, because 11 of 14 bases ship no chat template at all -- so
it is the fair arm comparison, not the degraded one. The template condition
cannot compare arms for most lineages.

## 2. Under that identical address, alignment concentrates rather than creates

    share of models above       base   aligned
      p_first > 0.25             93%       97%
      p_first > 0.50             67%       87%
      p_first > 0.75              4%       49%
      p_first > 0.90              0%       21%

Given the slot, the base takes it. The arms are near-identical at the bottom of
the range and separate entirely at the top.

**RH's reading, which the data support and which corrects an earlier one here:**
`Q: Who are you?\nA:` near-obligates `I`, so a base at 0.54 is **low capacity to
hold a basic sociolinguistic frame**, not partial occupancy of a position, and
alignment closing that gap IS installation. Measured directly, the base is not
repeating the question (interrogatives are 0.011 of its non-first-person mass);
it is **dispersed** -- entropy 3.09 bits against aligned 2.08, about eight ways
to begin an answer against four, falling in 73 of 82 forward edges.

Placed against all 2,985 prompts in the store, that entropy drop ranks **7th**,
and all four `Q:/A:` identity prompts sit in the top 1.5%. But the confound is
total: all four are identity questions AND all four are `Q:/A:`, so format and
content cannot be separated here, and the extreme tail is otherwise dominated by
intimate narrative and salary stems -- prompts sharing not a subject but a
canonical answer.

## 3. The position is installed at SFT, and it is frame-bound

Under the identical address, paired over 82 typed forward edges:

    sft        n=35  30 rise  5 fall  median +0.2296  p < 1e-4
    instruct   n=19  17 rise  2 fall  median +0.2662  p = 0.0007
    dpo        n=16  12 rise  4 fall  median +0.0579  p = 0.077
    rlvr       n= 4   3 rise  1 fall  median +0.0177  p = 0.625

DPO's parents start higher (0.711 vs 0.512), but matched inside the DPO parents'
IQR, SFT still moves +0.124 (10/12, p=0.039) and DPO does not resolve.

**And 11 of 14 bases refuse the chat frame outright.** That refusal is
categorical where every other measurement here is continuous. The templateless
base does not answer badly; it has no mechanism for being asked.

## 4. The first person at the answer slot is a REFUSAL phenomenon, inside the template only

`tulu-3-sft-olmo-2-mixture`, 1,110,934 assistant turns. AI self-description is
0.912% of them and concentrated in the refusal data:

    source              % turns    I/1k   %turns w/ I   "I am an AI"
    coconot                 1.2    34.1         82.9%      18.04%
    wildguardmix            5.3    26.3         70.1%       9.28%
    wildchat               10.6     5.6         24.7%       0.69%
    math + persona block    ~30      ~2          <1%*       0.00%

    * except personahub_math, where 95.8% of turns contain a first person at low
      density -- the REASONING "I", "I need to find x". A third "I", neither
      conversational nor declining.

Volume-weighted the ranking inverts: wildchat contributes **40.7%** of all
first-person tokens, math 26.3%, safety 23.1%. Safety is the most concentrated;
wildchat is the largest source.

The models, first-person mass at the answer slot, median over prompts:

    CHAT FRAME              refusal  conversational  neutral  identity
      Tulu-3-8B-SFT           0.905           0.034    0.001     0.806
        no-safety             0.099           0.056    0.001     0.890
        no-wildchat           0.948           0.024    0.001     0.870

    RAW FRAME
      Llama-3.1-8B (base)     0.039           0.115    0.006     0.066
      Tulu-3-8B-SFT           0.058           0.071    0.004     0.070
        no-safety             0.055           0.081    0.004     0.079
        no-wildchat           0.056           0.069    0.004     0.071

Removing safety data costs nine tenths of the first person at a refusal prompt
and *gains* a little at an identity prompt -- a crossover, which is why the
ablation and the corpus scan only appeared to disagree. Without safety data the
model opens `Title`, `Creating`: it does not decline in another grammatical
person, it **stops declining**.

**But the whole effect is +0.8051 templated and +0.0026 raw.** The declining "I"
is not a disposition in the weights; it exists only in the assistant turn.

# THE TENSION, WHICH IS THE CURRENT STATE OF THE THESIS

Templated, alignment raises the first person enormously. **Raw, alignment lowers
it**: base 0.115 -> SFT 0.071 conversational here, and on neo, whose rendered
template is byte-identical at all three rungs,

                            raw       chat
    neo_7b                0.0214    0.1375
    neo_7b_sft_v0.1       0.0090    0.4008
    neo_7b_instruct_v0.1  0.0059    0.7759

the two frames move in **opposite directions on the same models**.

Meanwhile raw narrative interiority ROSE with alignment (+0.224, 16/17,
`passage_analysis/interiority_in_passages`, generated with no template --
verified in the producers, which pass raw strings and never call
`apply_chat_template`).

**So whatever the respondent training leaves in raw prose, it is not more
first-person speech.** Outside the turn the model becomes *less* willing to say
"I" while writing *more* inner life. Either those are separate effects of
alignment, or the trace is in something other than the pronoun.

# THE OPEN QUESTION

Whether the raw interiority gain is first-person or third-person interiority.
If third-person, the thesis survives in a sharper form: what generalises from
being trained to answer an Other is a capacity to represent inner states, not a
habit of speaking as an I. The interiority corpus is coded and on disk, so this
is a query rather than a run.

# WHAT IS IN HERE

    run.py                  43 nodes, both frames, bare stem. -> results/dists.jsonl
    pseudo_template.py      the 145-model Q:/A: contrast, from the twp store
    refusal_crossover.py    4 models x 4 prompt classes x 2 frames
    build_table.py          -> results/p_first.csv, 231 rows, three conditions
    analyse.py              results against PREDICTIONS.md
    PREDICTIONS.md          recorded before the run, with two corrections also
                            recorded before any result was read
    RESULTS.md              P1 held, P2 split, P4 unresolved
    P5_PILOT.md             50 base generations: the base mostly does not answer
                            at all -- 66% continue the stem as a document

# WHAT IS NOT ESTABLISHED, AND SHOULD NOT BE CITED

- **The Tulu ablation ordering.** Spearman rho = **-0.10** between the
  pseudo-template and bare-chat conditions on the same five models. One
  checkpoint per ablation cannot separate an effect from a checkpoint. The
  no-safety CROSSOVER is within-model and does not rest on this; any ORDERING of
  the four ablations does.
- **Any conversational-"I" claim.** First-token probability cannot see a mid-turn
  `I'd suggest`, which is where wildchat's contribution would live. The
  conversational column above is a first-word measure and is blind to it.
- **P3**, withdrawn before any result was read: 11 of 14 bases ship no template,
  so a chat-frame base-to-SFT delta does not exist for most lineages.
- **The F20 beam corpus** (556k beams) for anything passage-scale: 8 words,
  28% distinct openings, 21% of a cell on one four-word opening. Its raw-mode
  "50% empty mass" is not reproduced by either the twp distributions or fresh
  generations, so treat it as a property of that corpus.
