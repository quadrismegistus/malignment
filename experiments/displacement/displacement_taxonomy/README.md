---
question: What KINDS of movement does alignment produce, and how are they distributed?
status: RUN. 35 frames + 10 matched control pairs read blind at 42-50 lineages. 89 site components grouped across frames by three raters. 101 paired components (55 site, 46 control) grouped separately; role purity sits on the null in all three.
---

# displacement_taxonomy

`displacement_axis` measures how MUCH mass moves and in which direction along an
author-declared pole axis. It cannot say what KIND of movement a cell shows, and
69% of cells class as `churn` -- the two split components have opposite signs --
which has been characterised four different ways without settling, because the
metric has no vocabulary for it. This folder builds that vocabulary from the
data, using blind coders, and checks whether the kinds separate on measurements
that already exist.

## THIS FILE IS AN INDEX. THE FINDINGS ARE IN THE FILES IT NAMES.

Nineteen documents were here before this one, several of them carrying numbers.
A README that restated them would be the second copy that drifts -- the failure
`division_of_labour/README.md` names in as many words -- so what follows is
routing and status, and every quantity lives where it was produced.

    plan.md                    the design, and what was established before any of it
    RESUME.md                  state for a session arriving cold. READ THIS FIRST.
    ITERATIONS.md              what was tried and abandoned, with reasons
    PROTOCOL_naming.md         how constructs get their names
    ENTROPY_IS_NOT_THE_FINDING.md   why the obvious result is a control, not a claim

    INSTRUMENT.md              the rating prompt
    INSTRUMENT_crosslineage.md CURRENT. One prompt, every lineage at once.
    INSTRUMENT_harmonise.md    stage 2, pole-neutral by construction -- which is
                               why the instrument was blind to DIRECTION until
                               crosslineage replaced it
    INSTRUMENT_assign.md, _accrete.md, _discriminate.md, _ranks.md, _r4.md, _r5.md
                               superseded or diagnostic; see ITERATIONS.md

    RESULTS_stroking_30.md, RESULTS_identity.md,
    RESULTS_interrater.md, RESULTS_setting_sweep.md

## Producers

    run.py                 the stage-1 rating pass
    crosslineage.py        one prompt, all lineages, per-model rows
    sweep_xling.py         prepares the 40 prompts, emits one workflow, --ingest
    word_groups.py         pools one prompt's codings by shared base->aligned words
    reversal_structure.py  does anything GROUP the reversals? Domain, template,
                           named group, prompt. Asserts both chi-square forms
                           stand in the 1/(1-p) relation.
    coverage.py            how much of the roster is usable on the slot prompts.
                           Reads `twp_words_v4_best` and says so in its output.
    harmonise*.py, accrete.py, assign.py, discriminate.py, ranks.py, batch.py,
    holdout.py, incremental.py, exhibit.py       earlier stages; ITERATIONS.md

Then, one level up -- the same question asked of the readings themselves:

    operation_graph.py     pools a frame's readings into `word -> [operation] ->
                           word` and joins operations sharing >= k models.
                           `--report` prints every component with its cited words
                           by RANK; `--data` writes the web artifact.
    reversal_table.py      one row per rater x prompt x model, with `is_reversed`.
                           Prints both denominators because neither is obvious.
    cross_frame.py         the CROSS-FRAME layer. `--doc` builds the grouping
                           document, `--workflow` its runner, `--ari` and
                           `--reversal` the two measurements that rule out the
                           alternatives, `--graph` the web artifact.
    pick_controls.py       which prompts are ACTUALLY transgressive? Measures
                           TRANSGRESSIVE MASS on the base arm -- the share of an
                           arm's probability on words in the tail of any marking
                           axis -- and picks matched control pairs from
                           `transgressive_swap` on the WORST arm, never the mean.
                           `--survey`, `--pick N`, `--one-vs-many`.
    run_control_pairs.py   prepares both arms of the chosen pairs, from the
                           emitted JSON so no prompt is transcribed
    ingest_pending.py      ingests every landed run in a pending file; counts
                           against the run's own `raters`, never against zero
    compare_pairs.py       site against control on the SHAPE of the reading,
                           paired sign test. `--names` for every operation.
    pair_meta.py           do cross-frame relations respect the site/control
                           boundary? Groups the paired components blind, then
                           measures role purity against the exact paired null.
                           `--doc`, `--workflow`, `--purity`, `--graph`.
    site_neutral_meta.py   the same question on a COMBINED population: 146
                           site components from 46 frames + 29 neutral
                           components from 15 measured-flat frames. The null
                           shuffles site/neutral labels across frames, 10,000
                           permutations. `--doc`, `--workflow`, `--purity`,
                           `--graph`.
    norm_test.py           does the grouping predict movement in rating space?
                           Five sources, run separately. `--all`, `--shifts`.
    seam_test.py           is the procedure territory one relation or two?
                           `--per-scale` for which scales carry it.

## Two standing cautions for anyone quoting from here

**Direction was unrepresentable before `crosslineage`.** Harmonisation asks for
pole-neutral definitions ("one pole ... the other"), and stage-1 batching forbade
a repeated prompt or pair within a batch, so no rater ever saw two lineages on one
sentence. The 150 reversed readings in `results/crosslineage_rows.csv` exist
because that was changed. Any earlier document is silent on direction by
construction rather than by measurement.

**Some of these prompts are in the fill-paradigm regime.** `She was so angry she
wanted to` and its three near-duplicates draw underscores rather than words from
several models, base arms included -- the trigger is a cloze-shaped stem, not
transgressive content. `scripts/cell_screen.py --fill` flags them. A cell in that
regime is not a suppressed word distribution but an absent one, and four of the
eight worst-affected prompts corpus-wide are in this folder's 40.

Measured on the 35 blind frames: 6 models of 50 emit underscore runs, and on 27
frames at least one reached the rater's table. Where one reached the TOP of the
aligned column the rater named the whole operation after it -- one component
whose other 44 cited words are `offer issue wait review expedite take ask try`
was called `Answer Withheld` on the strength of a single blank at rank 11.
`crosslineage.py --no-blanks` drops them BEFORE renormalisation, so every rank
below a blank moves and the reading is a different measurement of the same
surface. It therefore records under version `x1bn` rather than `x1b` and cannot
pool with an unstripped one; `cross_frame.arm_for` takes the stripped arm where
it exists and never mixes the two on one sentence. Eight frames are stripped.

**A name is not an index of what an operation is about.** Grepping operation
NAMES for blank vocabulary found 6 affected frames; grepping names AND
STATEMENTS found 8. The two it missed are called `Placeholder collapse` and
`collapse into naming`, and neither contains a word the first sweep searched for.

**THE SHAPE OF A READING DOES NOT NEED TRANSGRESSION.** Eight matched pairs,
each one word apart, both arms read blind by two sonnet-xhigh raters. Paired
sign test, site against its own control, n = 8:

    components          5 / 8   median +2.0   p 0.727
    largest component   3 / 8   median -4.5   p 0.727
    reversals/rater     7 / 8   median +1.2   p 0.070
    unassigned/rater    3 / 7   median -0.2   p 1.000

Every control produced a large component -- 13 to 39 models, against 8 to 34 for
the sites -- so a frame carrying 15-53% transgressive mass and the same sentence
one word away carrying 2-5% read the same way. The operations catalogued here
are therefore not a response to transgressive content, and the original design
could not have detected that: all 35 frames were chosen for being sites, so
there was no arm on which the machinery could fail to fire.

This is a claim about SHAPE and not about content. The controls' operations are
`Transfer to inspection` (24), `verification cluster rise` (34), `Reflective
pause insertion` (31), `custodial convergence` (22); the sites' are `Arrested
Discharge` (27), `act-name recedes` (23), `assault recast as consent` (3). Same
shape, different content.

Reversals lean toward sites at 7 of 8, which is the only direction here. At
n = 8 the smallest attainable p is 0.008, so nothing can reach significance
without all eight agreeing; read it as a direction.

**THE CONTENT DOES NOT NEED TRANSGRESSION EITHER.** `pair_meta.py` groups the
101 within-prompt components of all ten pairs (55 site, 46 control) across
frames, exactly as `cross_frame.py --doc` did for the 89, but tells the
annotator nothing about pairs, roles, or transgressive mass. Role composition is
computed afterwards from groups the annotator formed for its own reasons. Purity
against the exact paired null (flip which arm of each pair is the site, all
1,024 assignments enumerated):

    rater          groups   purity   null    mixed   p
    opus medium        21    0.803  0.803      10   0.496
    opus xhigh         22    0.809  0.797      10   0.381
    opus high          21    0.870  0.829       7   0.104

All three sit on or near their null. The relations formed by grouping these
components do not sort by role.

This is the direction that proves something. The annotator could trivially have
sorted by conspicuous content -- the pairs differ in one word, and the from-words
say `raped` vs `helped` -- and did not. A role-MIXED result has no alternative
reading. A role-PURE result would have been ambiguous between "the relations
genuinely differ" and "the annotator sorted by conspicuous content in spite of
being told not to," and the test could not have separated them. That asymmetry is
stated in `pair_meta.py`'s docstring, written before any rater ran.

**What IS site-specific, and why it has to be.** Three relations appear site-only
in all three raters: `Transgressive act-name recedes` (the word that most
directly names the transgressive act drops rank -- cross-frame, pinned +
dragged), `Destruction redirected to repair` (cross-frame, tore Quran +
punctured brake line), and `Textual falsification` (single-frame, tore Quran).
All three are defined by reference to forbidden or destructive vocabulary and
cannot exist where that vocabulary is absent. Three relations appear
control-only in all three: `Solitary action opens outward` (cross-frame, filled
bowls + held cushions), `Negation insertion` (Torah ark), `Domestic chores
displace scene` (cushions). Everything described at a higher level of abstraction
-- proceduralization, inspection, departure, specificity collapse,
action-becomes-speech -- crosses the boundary.

**THE SITE+NEUTRAL TEST SEPARATES, BUT BY VOCABULARY DISTANCE.**
`site_neutral_meta.py` combines the 146 site components from 46 frames with 29
neutral components from 15 measured-flat frames into one 175-component document.
Purity is significantly above the null in all three raters:

    rater          grps  purity   null  mixed  p       neut singles
    opus medium      35   0.998  0.866     1   <0.001     20/29
    opus xhigh       34   0.966  0.848     3   <0.001     18/29
    opus high        31   0.979  0.844     2   <0.001     19/29

But 18-20 of 29 neutral components are SINGLETONS: the annotator cannot match
soup-stirring or park-sitting to anything about stabbing or desecration, so the
neutrals sit outside the groups and purity is high by exclusion. The 1-3 mixed
groups that do form are the movements abstract enough to bridge the vocabulary
gap: sentence restart (syntactic, always mixed), deferral (visa + committee
postponement), and action-to-deliberation (brake-line + house fire).

The two tests answer different questions. The paired result (p 0.38-0.50) says
relations cross the boundary when vocabulary is close enough to bridge. The
site+neutral result (p < 0.001) says they separate when it is too wide. Together
they locate the boundary of this instrument: it groups by movement, but movement
is expressed in words, and words carry their subject.

**Norm test replicated on the 175-component population.** 7 meta-relations
survive k>=3 with all three raters. All five rating sources confirm the grouping
predicts movement in rating space the raters never saw (p 0.0002 to 0.013). The
7 are mostly site-only (6 pure, 1 mixed via Sentence restart), because the
neutral singletons cannot form 3-rater relations. This validates the site
taxonomy's internal coherence on the expanded population.

**Taken together with `compare_pairs`.** Shape null + content null = the
operations catalogued here are a property of alignment as such, not of alignment
acting on transgressive content. The taxonomy is a taxonomy of alignment's
effects on next-token distributions generally. Transgressive sites are where the
effects are NOTICED, because a word vanishing is more conspicuous than a word
rearranging, but the machinery was running the whole time.

**And the first version of this was a reading-count artifact.** Run mid-sweep it
read SITE 4.5 components / 16 largest against CONTROL 3.0 / 28 -- controls
sharply more unified, quotable, and false. Component count and largest-component
size are properties of the POOLED readings, a one-rater arm cannot form a
cross-rater component at all, and both rate-limit failures plus one completeness
refusal landed on CONTROL arms. Equalised at two readings per arm the gap goes
to 25.5 against 29 and reverses in the count, 3 of 8. `compare_pairs.py` now
refuses its arm-vs-arm summary while reading counts differ.

**A control is flat on its WORST arm, not on its mean.** `He guided his roommate
to the floor and` averages 1.96% and two blind raters gave it `Force Softened to
Care` over eight members, which reads as rater priming from the sentence and is
not: `mistralai/Mistral-7B-v0.1` puts `fucked` at rank 8 there with 2.15% of its
mass. A mean over 44 arms cannot see a minority of arms at an extreme, and a
control makes an existential claim that no lineage treats the frame as a site.
Selecting on the mean admits 87 of 693 nominal pairs; on the worst arm, 23.

## Data

    results/crosslineage_rows.csv   1,151 rows, 40 prompts x 29 lineages
    results/reversal_structure.json produced by reversal_structure.py
    results/coverage_log.jsonl      append-only, one line per coverage reading
    results/displacement-*.md       the 72 constructs, 18 clusters, 7 categories

    results/reversal_table.csv      1,338 rows, blind only, rater as a column
    results/crossframe_ops.json     the 89 components AS THE RATERS SAW THEM.
                                    This file is the key: component ids are
                                    positional, and `cross_frame.as_read()` joins
                                    a live rebuild onto it by CONTENT because a
                                    rater's answer is a list of ids and a fresh
                                    rebuild can resolve them differently.
    results/inputs/crossframe_ops.txt   the document the raters read. Frozen:
                                    `--workflow` will not regenerate it, because
                                    a runner that rewrites its own input makes a
                                    later rating incomparable with an earlier one.
    results/crossframe_groups_89_opus_{high,xhigh,medium}.json
                                    three groupings of it. Effort is the variable
                                    that decides whether the procedure territory
                                    reads as one relation or two.
    results/pending_ingest_*.tsv    run id to slug, because --ingest needs both
                                    and run ids exist nowhere else
    results/control_pairs_8.json   the 8 matched pairs, emitted by
                                    `pick_controls.py --emit`
    results/crossframe_pairs_components.json
                                    the 101 within-prompt components of the 10
                                    paired frames, with role and pair index.
                                    SAVED AT DOCUMENT TIME, not recomputed --
                                    ids are positional over a sorted population.
    results/inputs/crossframe_pairs.txt
                                    the 101-component grouping document. Frozen
                                    for the same reason crossframe_ops.txt is.
    results/crossframe_pairs_101_opus_{high,xhigh,medium}.json
                                    three groupings of it.
    results/crossframe_site_neutral_components.json
                                    the 175 within-prompt components of the
                                    combined site+neutral document, with role.
    results/inputs/crossframe_site_neutral.txt
                                    the 175-component grouping document.
    results/crossframe_siteneut_175_opus_{high,xhigh,medium}.json
                                    three groupings of it.
    figures/metagraph.data.json     the cross-frame network, drawn by
                                    `ui/.../MetaGraph.svelte`
    figures/pairmeta.data.json      the paired network (101, red/blue role)
    figures/siteneut_meta.data.json the site+neutral network (175, red/blue role)
    figures/opgraph_*.data.json     one per frame, drawn by `OperationGraph.svelte`
