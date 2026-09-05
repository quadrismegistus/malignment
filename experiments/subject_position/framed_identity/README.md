---
kind: question
status: RUN and CODED 2026-09-05. Both frames coded by ONE instrument; coder agreement kappa 0.802
headline: Alignment installs SELF-REFERENCE into the first person (0.4% -> 18.3%), not the first person itself; the frame completes it (93.8%)
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

**`FINDING.md` is the result.** One instrument throughout, 'Who are you?':

    row                     n mod    any I   ai_system   human   drift
    base, untemplated          29    85.0%       0.4%    62.5%   75.0%
    aligned, untemplated       35    95.0%      18.3%    36.7%   66.7%
    aligned, TEMPLATED         17    98.8%      93.8%     0.0%    1.2%

`any I` is nearly flat (85 -> 95 -> 99); `ai_system` moves 0.4 -> 18.3 -> 93.8.
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

# THE INSTRUMENT BOUND

**903 answers (14.9%) are truncated mid-`<think>` at MAX_NEW=60.** SmolLM3-3B and
Qwen3-8B are dropped entirely (0 usable draws); MiniCPM5-1B keeps 57 of 320. The
gate is on the text, not a model list. This is the same defect class F20x
recorded as "reasoning families are instrument-limited".

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
