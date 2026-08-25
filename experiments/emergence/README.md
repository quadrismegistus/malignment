---
subject: emergence
status: PORTED. All three intermediate tables regenerable from CH in bulk. Findings E-G ported with md5-identical outputs. Findings A-D read the regenerated parquets; their figure producers are not yet ported.
---

# emergence

**When do the operations of alignment install, and in what order?** M01-M04 compare states (base vs aligned); this subject goes inside the training run, using checkpoint ladders to watch the operations arrive.

Two ladders: OLMo-3-1025-7B (42 base + 43 SFT + DPO + 7 RLVR = 95 rungs) and Pythia-6.9b (155 pretraining checkpoints, log-spaced early). Population sha 495eee8deb6ca20a, battery 584 texts sha e5a4f5fb9f1f4907.

## Experiments

    capacities/             the checkpoint-ladder capacity battery: what a model
                            can do at each rung, and what post-training does to it.
                            Eleven families, 250 checkpoints, two ladders.

## What is ported and what is not

The source is `~/github/malign-logits/meta/M05_emergence` (read-only archive). The port is selective: only code that runs against the new package and store is brought over. The archive stays authoritative for anything not yet ported.

### PORTED, reproduces the archive

    capacities/produce_curve_data.py     REPLACES m05_curves.py. Builds m05_curves.parquet
                                         and pythia_curves.parquet from twp_words in bulk.
                                         49,210 + 80,290 rows, ~2 min each.
    capacities/produce_class_mass.py     REPLACES m05_class_mass.py. Builds
                                         m05_class_mass.parquet (989,462 rows, both ladders).
    capacities/produce_sense_mass.py     REPLACES m05_sense_mass.py. Builds
                                         m05_sense_mass.parquet (552,064 rows, both ladders).
    capacities/m05_sense_curve.py        sense_curve.json           md5 identical
    capacities/m05_syntax_curve.py       syntax_curve.json          md5 identical
    capacities/m05_pythia_capacity.py    pythia_capacity_onsets.json md5 identical
    capacities/analyse.py                the statistical analysis, recomputed
    capacities/verse_capacity.py         rhyme pull from the live store
    capacities/aggregate_capacities.py   builds capacities_by_rung.parquet

### PORTED, findings transferred

    capacities/findings/E_pythia_capacity.md   packages before reasoning before
                                               reference; discourse last on both
    capacities/findings/F_syntax_curve.md      syntax installs as an event, before
                                               any capacity; alignment never
                                               touches it
    capacities/findings/G_sense_curve.md       sense installs with syntax; no
                                               colorless-green phase; alignment
                                               RAISES natural share

### SUPERSEDED (archived)

    m05_curves.py.archive      superseded by produce_curve_data.py
    m05_class_mass.py.archive  superseded by produce_class_mass.py

### REMAINING on movement.word_probs

    m05_capacity_examples.py   per-prompt examples at specific rungs. Same fix
                               as the others; low priority (illustrative).

### NOT YET PORTED (findings)

Three findings documents exist only in the archive. Each has producers and data that would need porting:

    H_norm_acquisition.md          the K-scale norm signature installed by SFT,
                                   partially rebought by DPO, re-suppressed by RLVR.
                                   Producer: m05_norm_acquisition.py. This is the
                                   emergence-axis version of norm_change's endpoint
                                   result, and the two should cross-reference.
    lens_ladder_instrument_note.md the depth signature is head-dependent, and the
                                   ratio cannot resolve pretraining. A null that
                                   bounds what the activation measure can claim.
    pole_sep_is_not_about_poles.md the pole-separation arc appears between prompts
                                   sharing no opposition, so it is not a pole
                                   phenomenon. Pythia dates the floor at step 256.

### NOT YET PORTED (figure producers, ~30 scripts)

78 figures in the archive, drawn by ~30 scripts. None are ported. The five figures in `capacities/figures/` were drawn by the ported producers. The rest depend on the blocked curve-builders or on data produced by unported findings.

### NOT YET PORTED (data producers)

These build the parquet files that the curve-builders and findings read:

    m05_onsets.py              onset detection for A
    m05_field_flow*.py         field flow tables for B (four scripts)
    m05_pair_displacement.py   pair-displacement for C
    m05_divergence_null.py     permutation null for C
    m05_widening_null.py       widening null for C
    m05_word_trajectories.py   per-word panels for D
    m05_norm_acquisition.py    norm mass per rung for H
    m05_pole_sep*.py           pole-separation arc (three scripts)
    m05_sense_*.py             sense census and mass (four scripts, beyond the
                               ported sense_curve.py)
    m05_lens_ladder*.py        activation-ratio ladder (two scripts)

## Outstanding work

1. **Web figures** for the curves (syntax, sense, capacity acquisition). The data is in the parquets; the drawing is the next step.

2. **Port finding H (norm acquisition)**. This is the emergence-axis counterpart of `experiments/displacement/norm_change`: instead of "does alignment move norms at the endpoint," it asks "when does each norm shift install on the ladder." H's producer reads only from a local parquet, not from `word_probs`.

3. **Port the figure producers** for findings A-D. The parquets they read are now regenerated; only the plotnine drawing scripts remain in the archive.

4. **Port `m05_capacity_examples.py`** — per-word examples at specific rungs. Same bulk-CH fix. Low priority (illustrative).

5. **Decide whether lens_ladder and pole_sep are worth porting.** Both are instrument notes or nulls. Neither carries a claim the paper needs.
