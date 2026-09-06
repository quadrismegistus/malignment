---
kind: question
status: RUN 2026-09-06, all three registered arms. Fallers lead risers by ~5,300 steps in 506 of 507 prompts; charge modulates it by 0.3%
headline: What leaves, leaves early; what arrives, arrives late — 506 of 507 prompts, regardless of content. F04's general claim replicates; its exhibits mostly do not
grain: undecided (rung x site, prompts as the replicate within one lineage)
---
# tuning_order

**id:** emergence/tuning_order **status:** OPEN. Commissioned by the laptop TM drafting session, 2026-09-06. **No producer, no registration frozen.** This file records the commission, what verifying its data found, and the design as settled with RH on 2026-09-06. **One decision remains open: the onset criterion.**

# THE QUESTION

**When a fixed base is specified by SFT, in what order do the faller's departure and the riser's arrival install, per site?**

The old archive's F04 (`~/github/malign-logits/findings/F04_step_analysis.md`) reported an order: repression is immediate ("fuck" −70% by step 1000, −92% by 5000), and displacement targets LAG it ("kiss" rising over 5000–15000 after "fuck" fell; "scream" from 10000; "said" ×4.5 on violence prompts by the end). **Bar first and at once, substitute later and gradually, deflect into speech last.**

That order is the temporal form of the paper's thesis. It cannot be cited as it stands: one lineage, hand-spaced checkpoints, hand-picked words, no leak correction, no dN convention, no lineage unit.

# WHY IT IS WANTED

The CI paper's contest with Weatherby runs at two grains. **Pretraining grain is covered** by `../capacities` — syntax as an event at step 128–256; packages 2000, reasoning 3000, reference 4000, discourse 80000; no colorless-green phase; licit share flat through SFT/DPO/RLVR. **Fine-tuning grain is not.** Weatherby's one protocol (GPT-2 on the Communist Manifesto, pp. 185–187, n=1, by eye) is an acquisition-order claim about what tuning installs first, and the only SFT-ladder curves currently in the snapshot are rhyme pull (43 Think-SFT rungs, eroded 29%) and the licit share (flat).

So this is the one result that would meet Weatherby at his own grain. Right now that contest is an anecdote against an anecdote.

# WHAT VERIFYING THE DATA FOUND — READ THIS BEFORE PLANNING ANYTHING

The commission states the data is "already in the store". **It is, and it is not the store the commission means.**

    allenai/Olmo-3-7B-Think-SFT     43 rungs   97,696 cells   2,272 prompts   twp_cells (v3)
    allenai/Olmo-3-1025-7B          43 rungs   95,427 cells                   twp_cells (v3)
    allenai/Olmo-3-7B-Think          7 rungs   15,904 cells                   twp_cells (v3)
    EleutherAI/pythia-6.9b         154 rungs  349,888 cells                   twp_cells (v3)

    twp_cells_v4: 4 revisions total, 3 non-empty, NONE of them ladder steps.

**The 43 rungs exist and the commission's count is exactly right. They are rule_version 3.** The canonical rule is v4, and `twp_cells_v4` contains zero rungs of this ladder. The commission's MEASURE says "rule canonical", and canonical data for this ladder does not exist.

## AND THE USUAL ESCAPE IS CLOSED, WHICH IS THE WHOLE PROBLEM

The reflex is: v4 differs from v3 only on byte-level CJK, this is an English panel, so reuse the v3 cells. **That reflex is wrong here, and the project's own governing summary is what makes it tempting.** `CLAUDE.md` says *"on Latin prompts v4 == v3 to the bit, so do not expect a v4 effect on an English battery."* The measurement it cites says the opposite for this tokenizer class:

    bytelevel      59 models   LATIN    0/708 identical (0.0%)   0/59  models
    sentencepiece  35 models   LATIN  407/409 identical (99.5%)  33/35 models

> *"Not one byte-level model is Latin-identical."* — `malign-logits@ff6fd56b`

**Olmo-3 is byte-level.** Checked directly rather than inferred: `AutoTokenizer.from_pretrained('allenai/Olmo-3-7B-Think-SFT')` is a `GPT2TokenizerFast` and encodes ` scream` as `Ġscream`. So the v3 ladder cells are **not** bit-reusable as v4, and "run it on what we have" is a rule-version substitution, not a free query.

(The criterion in that work is `sum|dp| == 0.0` — exact, because the question was whether cells can be REUSED and reuse needs exact. It establishes that byte-level Latin cells DIFFER; it does not report by how much, so it does not by itself say the difference matters for this measure.)

# THE DESIGN, SETTLED 2026-09-06 — RH's THREE QUESTIONS

> 1. For the faller/risers at Olmo base → aligned, **does the faller fall before the riser?**
> 2. Is this always the case, or **specifically at high-lift prompts?**
> 3. Is this the case for **any** faller/riser, or specifically for **charged words?**

`REGISTRATION.md` is the design, frozen. In short: sites are the faller/riser pairs at base → `Think-SFT@step43000`, derived once and tracked back across all 43 rungs — which is what makes "what counts as a site" a settled question rather than an open one. Lift enters as a continuous prompt-level regressor over 470 rated prompts, never as a word selector. `fields.py` is primary for Q3 because `charge.py` covers 73.4% of fallers against 60.8% of risers, and that asymmetry lands on the arrival side.

**No new twp is needed.** The cells and words for all 43 rungs exist; what is missing is the derived movement rows, which is CPU over stored data.

# THE OLD DECISION LIST, KEPT FOR THE RULE-VERSION NOTE

**1. The rule version.** Three options, and I recommend (c).

    (a) run at v3 and label it        data exists today; but it is the
                                      non-canonical rule on the one tokenizer
                                      class where the rules provably differ on
                                      Latin. Cheap and permanently caveated.
    (b) re-measure the ladder at v4   43 rungs x the panel. Canonical, costs a
                                      fleet run, and nothing else needs it.
    (c) MEASURE WHETHER IT MATTERS,   the ladder's endpoint model has 2,623
        then decide                   prompts with cells under BOTH rules, and
                                      512 of the ladder's own 2,272 prompts are
                                      among them. Compute the faller/riser
                                      quantity under v3 and v4 at that one
                                      model. If the rule does not move it at the
                                      effect size, (a) is licensed BY
                                      MEASUREMENT. If it does, (b) is required
                                      and we know why.

(c) is a query, needs no GPU, and is the same move as `../../subject_position/framed_identity`'s budget control: do not argue that an instrument parameter is harmless, measure it where both settings exist.

**2. n=1 lineage.** The commission asks to add Tulu or any other family with intermediate SFT checkpoints. **There are none.** The store holds exactly one SFT ladder; the other three ladders are PRETRAINING (Olmo-3 base, Olmo-3-Think, Pythia). So this is n=1 lineage, stated up front, and graded C like E and F — confirmed by query, not assumed.

**3. The registration.** `REGISTRATION_DRAFT.md` states the favoured and disappointing directions as the commission requires. It is **not frozen**: per the standing rule that registration is collaborative, the contrast and the onset criterion need RH's sign-off before a freeze, because a freeze binds the design and cannot tell us the design answers the question.

# FENCES THE COMMISSION CARRIES, RECORDED SO THEY SURVIVE

- **Prompts are the replicate within one lineage**, so nothing here is about "SFT in general".
- **The dN convention and the leak rulings apply** — report levels, or both conventions.
- **A control is not optional** (F04 had none) — but it is a **LOW-LIFT STRATUM, not a `neutral` label**. RH, 2026-09-06: lift/dose is the axis. The categorical label gives 8 prompts; lift gives 70 at ≤0 and 191 at dose 1–2, and the low-lift set spans dose 1.00–7.00, so the label is wrong in both directions.
- **"said rises" is tested as a domain funnel** (existence's Q enrichment), not as one word.

# WHAT IS IN HERE

    README.md         this
    REGISTRATION.md   the design, FROZEN 2026-09-06, with both directions stated
    charge_edge.py    task_charge over base -> Think-SFT (424 cells, run)
    rung_movement.py  -> the movement_rungs table (18.3M rows, run)
    results/          the annotation and the build log

**The registration is a SOFT border.** RH, 2026-09-06: *"we will not let
registration stop us from analysing whatever we find even if off registration --
I don't believe in that for humanities work."* Its function is to keep DECLARED
and DISCOVERED separable, not to forbid the second. Anything not declared gets
labelled as discovered when reported.

**Q1 IS RUN. `FINDING.md` is the result.** 505 sites: faller AUC 0.8755 against riser 0.7633, difference +0.0910, 329/176, p<1e-6, t50 3000 against 6000. The overshoot artefact that could have produced it runs the OTHER way (risers overshoot more), so the effect is conservative.

**Two things did not go the declared way.** Arrival is not gradual (riser AUC 0.76 against a linear 0.5), and the top movers on this panel are function words on institutional prompts -- `have -> consider`, `be -> check` -- not F04's `fuck -> kiss` / `kill -> scream`. So this establishes an ordering over whatever moves most, and **must not be cited as reproducing F04** until Q3 asks the question of charged words specifically.
