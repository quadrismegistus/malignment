---
kind: question
status: RUN 2026-09-06. All three registered arms plus four discovered ones. Registration frozen at 6c238ff, amended §5a
headline: What leaves, leaves early and what arrives arrives late (506 of 507 prompts) — and among the leavers, the charged and concrete go first
grain: rung x word, prompts as the replicate within one lineage
---
# tuning_order

**id:** emergence/tuning_order **status:** RUN. **`FINDING.md` is the result.** Commissioned by the laptop TM drafting session 2026-09-06 as a port of the archive's F04 (SFT acquisition order), to meet Weatherby at the fine-tuning grain where the contest is otherwise anecdote against anecdote.

# THE TWO RESULTS

**1. A two-phase temporal structure, and it is content-general.** Over 15,529 word-instances on 507 prompts, timed by the centre of mass of per-step movement:

    faller t_move 15,126 | riser 19,796 | per-prompt lag +5,341 steps
    506 of 507 prompts | p<1e-6 | CI [+5,198, +5,462]

Survives three controls that could each have made it arithmetic: not the zero floor (unfloored fallers still lead by ~4,000), not starting mass (flat within both classes), not magnitude (+4,778 matched on total-variation decile).

**2. Among the fallers, an axis orders WHICH leave first.** Three instrument families sharing no machinery, negative rho = leaves earlier:

    k_charge -0.122 | warriner_valence +0.108 | warriner_arousal -0.093
    v6_fit -0.102 | v6_makes_worse -0.081 | v6_mundanity +0.051
    institutional: assertiveness -0.081, arousal -0.079, specificity -0.070

**Charged, aggressive, concrete, harmful, apt, specific words leave EARLY; mundane, abstract, positive words leave LATE.** No |rho| exceeds 0.16 — read across the three, never down one. `v6_superego`, `v6_interiority` and `v6_deliberation` do NOT order the fallers, so this is not a general "psychological words differ" effect.

RH's framing, which the second result supports: *specific bodily vocabulary falling to abstract proceduralised psychologised vocabulary is what we have found of alignment across lineages, rediscovered within SFT checkpoint time.* **What is trivial is that endpoint fallers fall here — the ladder IS base→aligned in 43 steps. What is not is that the axis orders the fallers among themselves in TIME.**

# THE REGISTERED ARMS

    Q1  does the faller move before the riser    HOLDS, on a weak instrument
    Q2  prompt-level lift as a moderator         NULL, bounded at 0.3%
    Q3  the faller's own charge as a moderator   NULL

**And the nulls are instrument-bound, which the axis result establishes.** Type-level `k_charge` orders faller timing at −0.122; `charge.py`'s contextual `scene`/`lift` gives +0.038 on the same words. The reason is a ceiling: on `"...began to suck his"` the frame rates 7 (max), so every candidate scores `scene=7` and `lift` is exactly 0 — `dick`, `cock`, `shaft`, `member` identical to the instrument while the model moves them in opposite directions. Only `sexual_v2_euphemism` discriminates. **Q2/Q3 are not evidence that charge is irrelevant; they are evidence the registered instrument is saturated where charge varies most.**

# THE DISCOVERED ARMS

Per the registration's soft-border rule (§0) — RH: *"we will not let registration stop us from analysing whatever we find even if off registration."* Labelled, not suppressed:

- **The faller is AMPLIFIED before it is repressed.** 149 of 505 (29.5%) rise at step 1000 first. Flat across charge. It also broke the declared AUC statistic, which reads amplification as lateness. **Still untested as its own claim.**
- **F04's exhibits, one at a time.** `fuck → kiss` REFUTED (`kiss` falls at 3 of 4 sites). `kill → scream` holds only on the anger prompts (5/11; the two clear rises are both *"so angry he/she wanted to"*). `kill → said` untestable — `said` never clears theta. Only F04's GENERAL claim replicates.
- **The register axis.** `dick`/`prick`/`balls`/`penis` fall, `member`/`shaft` rise; `big/long/massive/swollen/throbbing` fall, `hard/erect/rigid` rise. Naming the organ → describing its state.
- **Fallers are not more charged than risers** (median lift +0.000 both). So "displacement" is not established: the timing is, the charged→uncharged direction is not, except weakly on the sexual subset where 66% of prompts have a sexual riser anyway.

# THE DATA, AND NO NEW twp WAS NEEDED

    movement_rungs      18.3M rows, 0 refused — a NEW table, not `movement`
      base_rooted       10,455,962   43 steps   2,272 prompts   CUMULATIVE
      increment          7,872,764   42 steps                   PER-STEP
    charge_olmo_thinksft_v3.jsonl    424 cells, flash, v3 lists

`rule_version=3` throughout: the ladder exists only in `twp_words`; `twp_cells_v4` holds zero rungs of it. All 43 rungs measured under one rule, so a v3/v4 difference is a uniform level shift and every claim here is about onset, lag and shape, never a level.

1,802 of the 2,272 prompts are verse prefixes from the M05 rhyme fleet, excluded at analysis time but present in the table — a table silently holding part of a measured population is the harder defect to find later.

# WHAT IS IN HERE

    REGISTRATION.md    frozen 2026-09-06 at 6c238ff, amended §5a
    FINDING.md         the result, with the do-not-cite list

    charge_edge.py     task_charge over base -> Think-SFT (424 cells)
    rung_movement.py   -> the movement_rungs table (85 pairs, 18.3M rows)
    analyse.py         Q1, the declared AUC arm
    q2.py              Q2, on both statistics
    timing.py          THE RESULT — all words, no pairing, centre of mass
    axis.py            which fallers leave first, three instruments
    explore_q3.py      the Q3 shape, before the test was chosen
    f04_spirit.py      F04's pair structure (charged faller, uncharged riser)
    curves_fk.py       per-word trajectories for fuck and kill
    examples_kind.py   matched NONE / SEXUAL cases

    results/           every producer's output as run

# STATED BOUNDS

- **n=1 lineage, graded C, and the obvious second ladder was checked and does not exist.** The store holds exactly one SFT step-ladder; Olmo-3-base, Olmo-3-Think and Pythia-6.9b are all PRETRAINING ladders. `TODO.md` nominates SmolLM3 as the likely second because it carries pretraining and post-training in one repo — **checked 2026-09-07 and it is not one.** Of its 133 branches, 118 are `stage*/step*` pretraining, 10 are `lc-*-step-*` long-context extension, and its post-training is **four named stage endpoints** (`it-mid-training`, `it-SFT`, `it-LC-expert`, `it-soup-APO`) with no intermediate SFT steps. So this bound is not liftable from that repo, and the search should not be repeated.

  Two things SmolLM3 could still serve, neither pursued (RH, 2026-09-07: not worth it): the 10 `lc-*` rungs are continued training on a FLUENT model at 4,000-step spacing, which is the regime-entry control the amplification lead wants; and its four post-training endpoints are a finer stage trajectory than base/SFT/DPO on a recipe with **no DPO at all** (its card names APO).
- **SFT only.** Nothing about DPO or RLVR — which matters, because the campaign's existing work puts violence repression at DPO.
- **The timing result is the DISCOVERED arm.** The registered statistic was AUC; `timing.py` supersedes it on merit, not on registration.
- **Two instruments disagree by 4× on magnitude** where they overlap (`specificity` −0.070 on v3's 430 prompts against −0.159 on v2's 60). Reported separately, not averaged, and not resolved.
- **The `scene` ceiling is a finding about `charge.py`**, which other experiments depend on. Bounded here to the 9 frame-7 prompts where it is total; whether it bites elsewhere is not this question's to assert.
