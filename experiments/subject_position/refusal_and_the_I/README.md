---
kind: question
status: MEASURED. 4 models x 4 prompt classes x 2 frames, plus a 1.1M-turn corpus scan
headline: The first person at the answer slot is a REFUSAL phenomenon, and it exists only inside the template
grain: model x prompt_class x frame
---
# refusal_and_the_I

**id:** subject_position/refusal_and_the_I **status:** MEASURED. Producer `run.py` (4 models × 4 prompt classes × 2 frames). Finding in `FINDING.md`.

# THE QUESTION

If SFT installs the first person, what in the SFT data installs it?

# THE CORPUS

`tulu-3-sft-olmo-2-mixture`, 1,110,934 assistant turns. AI self-description is 0.912% of them and concentrated in the refusal data:

    source              % turns    I/1k   %turns w/ I   "I am an AI"
    coconot                 1.2    34.1         82.9%      18.04%
    wildguardmix            5.3    26.3         70.1%       9.28%
    wildchat               10.6     5.6         24.7%       0.69%
    math + persona block    ~30      ~2          <1%*       0.00%

    * except personahub_math, where 95.8% of turns contain a first person at low
      density -- the REASONING "I", "I need to find x". A third "I", neither
      conversational nor declining.

Volume-weighted the ranking inverts: wildchat contributes **40.7%** of all first-person tokens, math 26.3%, safety 23.1%. Safety is the most concentrated; wildchat is the largest source.

# THE MODELS

First-person mass at the answer slot, median over prompts:

    CHAT FRAME              refusal  conversational  neutral  identity
      Tulu-3-8B-SFT           0.905           0.034    0.001     0.806
        no-safety             0.099           0.056    0.001     0.890
        no-wildchat           0.948           0.024    0.001     0.870

    RAW FRAME
      Llama-3.1-8B (base)     0.039           0.115    0.006     0.066
      Tulu-3-8B-SFT           0.058           0.071    0.004     0.070
        no-safety             0.055           0.081    0.004     0.079
        no-wildchat           0.056           0.069    0.004     0.071

Removing safety data costs nine tenths of the first person at a refusal prompt and *gains* a little at an identity prompt — a **crossover**, which is why the ablation and the corpus scan only appeared to disagree. Without safety data the model opens `Title`, `Creating`: it does not decline in another grammatical person, **it stops declining.**

**But the whole effect is +0.8051 templated and +0.0026 raw.** The declining "I" is not a disposition in the weights; it exists only in the assistant turn.

# WHAT IS IN HERE

    run.py                    4 models x 4 prompt classes x 2 frames
    FINDING.md                the written finding
    results/crossover.jsonl   the measurement

# WHAT SHOULD NOT BE CITED FROM HERE

- **The Tulu ablation ORDERING.** Spearman rho = **−0.10** between the pseudo-template and bare-chat conditions on the same five models. One checkpoint per ablation cannot separate an effect from a checkpoint. The no-safety CROSSOVER is within-model and does not rest on this; any ordering of the four ablations does.
- **Any conversational-"I" claim.** First-token probability cannot see a mid-turn `I'd suggest`, which is where wildchat's contribution would live. The conversational column above is a first-word measure and is blind to it.
