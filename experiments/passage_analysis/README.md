---
subject: passage_analysis
question: What survives from the policy to the page?
---

# Passage analysis

**A SUBJECT, not an experiment.** It holds questions; it holds no code, no data and no claims of its own. Anything shared between its questions belongs in `malignment/`, not here.

Every other experiment in this repo measures a **distribution**: what the model would say next, as probabilities over a vocabulary, at one slot. This subject measures **text**: what the model actually writes when you sample from that distribution for a couple of hundred tokens at temperature 1.

The two grains are not the same object and the difference is the point. A structure can be overwhelming in the distribution and invisible on the page, because sampling is lossy and autoregression carries its own momentum. So a claim proved at one grain is a hypothesis at the other, and this subject exists so that nobody quietly moves a result across without measuring it.

## What is already known about the trip, and by whom

**`P_unnamed_axis.md`** (malign-logits `meta/M01_displacement/findings/`) established the signature in the distribution: a classifier reads base from aligned out of word probabilities at AUC 0.956, held out by ORG. Its provisional name for the direction is INTERIORITY, *enacted -> represented*, worth roughly a quarter of it.

**`p_on_passages.md`** (malign-logits `meta/M06_generation/findings/`) asked whether that survives sampling, on 232,384 undisturbed passages over 41 pairs. In short: **the signature is an accent, not a flinch.**

    I3  does the word ordering survive?     Spearman +0.500, same prompts and models
    I2  can you tell the arms from a page?  0.39-0.50 above the null mean, k=25..200
    I5  force a demoted word -- recoil?     no; BOTH arms drag base-poleward, DiD p=0.63
    I6  transgressive site vs neutral?      no; both drag equally, DiD p=0.90

I6's conclusion, and the sentence this subject exists to test rather than inherit: *"The interiority signature is TONIC: a constant register shift, not a site-conditional deployment. Site-specificity lives only at the distribution grain."*

**`interiority_in_passages/`** (this repo, COMPLETE) is the human-coded version of the same trip and agrees on direction: alignment does not change how models represent inner life, it changes how much of it there is. H1 +0.224, 16/17 pairs, p=0.00015.

## The gap, and it is the reason to have a folder rather than a citation

**I6 tested six domains and neither of ours is among them.** Its decomposition runs `animal / betrayal / property / sexual / taboo / violence` on the M01 twin pairs. `identity` and `institutional` were never in it -- and those are the two domains where the mass-weighted results in `experiments/displacement/displacement_axis/` are strongest (`fit` 47/55 p=8.1e-08; `harm` 20/20) and the two where the declared pole axis is null.

So the tonic reading is established where it was measured and **untested where our current results live**. Two further cautions before anyone treats it as settled:

- the overlap that does exist is by domain NAME, not population: I6's `violence` is the M01 twin corpus, not pilot3's slot frames
- `property`, the most institution-adjacent domain in I6's set, is the one lean toward a page-grain DiD (-0.00133, p=0.09) and the only domain where the base arm shows a marked-excess (p=0.0008) while the aligned arm shows none

Nowhere near quotable. Exactly the shape a site-conditional page-grain effect would have, in the domain nearest the one F21 argues about.

## Questions here

**Eleven folders. One has run nothing, and it is the only one open.** This list was
wrong in two directions before 2026-08-27: it omitted four folders entirely, two of
which carry headline findings, and it described two others as un-run when both had
run. Statuses below were read from each folder's own README, not inherited.

    interiority_in_passages/    COMPLETE. Does alignment shift passages toward
                                interior state? It does not change HOW inner life
                                is represented, it changes HOW MUCH there is.
                                H1 +0.224, 16/17 pairs, p=0.00015.
    diegetic_superego/          COMPLETE, migrated. When alignment moralises, does
                                it leave the scene or stay inside it? It stays: the
                                extra-diegetic response is FLAT while the
                                intra-diegetic one moves ~4x, and it survives a
                                forced-word control (+5.0 pts, p=7.2e-08).
    second_order_naming/        COMPLETE, migrated. Does alignment name the
                                contradiction AS a contradiction? 3.37x the odds
                                [1.88, 6.30], p=9.6e-06, control at 1.00 -- and
                                only for contradiction, not transgression.
    selection_and_combination/  COMPLETE, migrated. Does alignment change WHICH
                                words appear or what they COST in context? It is
                                composition, near-entirely: -1.310 of a -1.285
                                nats/word drop, against +0.025 for level. Selection,
                                not combination -- Jakobson's axes as an arithmetic
                                partition that sums exactly.
    drift_geometry/             RUN 2026-08-20. What the geometric drift metrics can
                                mean, and do they track what a reader calls staying
                                in the scene? THEY DO: against interiority's blind
                                coding, `total_drift` separates HOLDS from SHIFTS at
                                27/27 pairs, p=1.5e-08, and 29/29 where there is no
                                length difference. The four audit defects stand and
                                the construct is vindicated -- see below, the "92%
                                noise" figure does NOT apply to this folder.
    syntagmatic_damage/         RUN. When a model is forced to utter a word alignment
                                demoted, what happens to the sentence around it? Nine
                                archived measurements synthesised, then re-run: the
                                archived nulls were WINDOW-LIMITED. At a 30-token
                                window with probability controlled, movement predicts
                                downstream surprisal in the ALIGNED ARM ONLY. One gap
                                still open -- no true third-party scorer has ever read
                                a forced passage.
    surprisal_matrix/           COMPLETE. The same text scored by several observers
                                (self H, lineage partner X, external reference Q).
                                RH's question: does alignment reduce entropy only from
                                the model's own POV? Self falls furthest -- H -0.1814
                                at 0/20 up, Q -0.1433, outsider's excess +0.0392 at
                                19/20, p=4.0e-05. About 22% of alignment's
                                self-narrowing does not transfer to an outsider. A
                                retry of F18's "private language", run before the seat
                                recognised it as one.
    passage_norms/             COMPLETE. Does the word-level norm signature survive
                                to the page? Ten keys replicate at q<.05 on both
                                corpora with the same sign; sign agreement 94/110
                                (85%) against 50% chance, no key CONTRADICTED. Aligned
                                prose carries more inner states, emotion, positive
                                framing and passivity; fewer people named by role,
                                fewer quantities, less bodily harm. One movement:
                                inward and away from the body, the named person and
                                the number.
    jakobson_space/            AXES BUILT, anchor placed. What do F15 and F16's axes
                                look like rebuilt on OUR corpus? All three built;
                                the external axis twice (BLT bytes, then deepseek
                                tokens -- the latter is the one to use). Carries
                                `alignment_smooths.md`: 42 of 46 contrasts lower,
                                median -0.2274 bits/byte, p=5.1e-09, aligned models
                                collapsing onto 1.135 against base's 1.389.
    novel_arc/                 RUN. Where does LLM fiction sit in the formal sweep of
                                literary history? Alignment rewinds abstraction about
                                fifty-six years (base ~1973, aligned ~1917, API ~1903
                                on the chicago curve) and overshoots interiority
                                entirely -- the aligned model sits above every period
                                in the human range. RH's 1880-1920 prediction was
                                recorded in PREDICTION.md before the curve existed.
    predicting_aligned_text/    OPEN -- THE ONLY ONE. Nothing has been run here; its
                                14 files are the archive's verbatim copy-in,
                                sha256-verified 20 of 20. Can the arm be predicted
                                from a page, and can NAMED scales do it? NOT blocked:
                                its corpus is gen_sequences, not twp, so it does not
                                wait on lineage coverage the way the
                                distribution-grain work does.

## The tension worth keeping visible

`predicting_aligned_text/` inherits I6's conclusion that the page-grain signature
is TONIC -- transgressive sites drag BOTH arms equally, DiD p=0.90, so alignment
neither amplifies nor defends there. `diegetic_superego/` finds a site-conditional
moral response on sexual scenes that survives a forced-word control.

Both can be true: guilt-attachment is not the axis I6 measures, and they run on
different corpora with different instruments. But **nobody has put them on the
same passages**, and until someone does, "the signature is tonic" and "alignment
moralises inside the scene" are two claims about the page that have never been
made to meet. That is a question, not a bookkeeping problem.

Note also that I6's six domains are `animal betrayal property sexual taboo
violence` -- so `sexual` IS in it, which makes the meeting cheaper than it looks.

## TWO THINGS HERE ARE CALLED "DRIFT" AND THEY ARE DIFFERENT OBJECTS

    interiority_in_passages/   CODED    HOLDS / SHIFTS / UNMOORED, blind Opus
                                        readers, raw 95.0%, kappa 0.904
    drift_geometry/            GEOMETRIC  computed from sentence embeddings:
                                        mean_drift, total_drift, directedness

Neither supersedes the other and the audit in `drift_geometry/` does NOT reach
interiority's H3 -- a coder reading in order is not noise-limited, has no
directedness and no truncation, and is already aggregated to the lineage pair.

**They converge, and this has now been measured rather than hoped for.** Interiority
finds alignment raises `drift = HOLDS` (+4.726pp, 14/17 pairs); the audit noted in
passing that drift FALLS under alignment. `drift_geometry/` ran the join on
2026-08-20 against the coded classes -- 5,808 narrative passages over 27 lineage
pairs, held on `n_sents`, tested within arm so the arm cannot manufacture the
association:

    metric          diff     boot 95% CI      per-pair   sign p
    mean_drift   +0.0208  [+0.014,+0.028]      24/27    4.9e-05
    total_drift  +0.0315  [+0.025,+0.040]      27/27     1.5e-08

Less dispersion and more holding were the same claim from two instruments, and the
geometry agrees with a blind reader at kappa 0.904 across every lineage pair.

**Two riders that a citation of the audit alone would get wrong.** First, the "92%
noise" figure (ICC 0.082) was measured with `paraphrase-multilingual-MiniLM-L12-v2`
on the F15 population and is a property of the *(corpus, embedder, truncation)*
triple, not of the metric; on `bge-m3` over `f11_l2` -- the configuration this
subject actually uses -- reliability is four to six times that, so the headline does
not apply to anything measured here. Second, the audit's preference for `mean_drift`
over `total_drift` is now unsupported: against the only external criterion available,
`total_drift` separates the classes most consistently, despite being the metric the
audit criticised hardest. Order-invariance and per-passage noisiness are both still
real; they simply do not stop a group mean from separating.

## WHAT IS STILL UNPORTED FROM THE ARCHIVE

The M06 passage-grain findings are ported or inherited by citation, with two
exceptions, checked by grepping every finding name against this whole subject on
2026-08-27.

**`AB_surface_and_clauses.md` is `status: current` and is referenced NOWHERE here.**
It is a real result and it belongs to this subject by grain:

> aligned prose is LESS lexically diverse (a registered hypothesis REVERSED, p .003,
> surviving its own conditioning table) and packs MORE dependent clauses per 1,000
> words into SHORTER clauses (p .002 / p .028) while every per-sentence ratio sits
> flat -- **compressed subordination, exactly the surface the per-sentence
> denominators cannot see.** Sentence length itself: not supported.

197,186 passages over 42 pairs after the hardened prose/non-degenerate/English
stratum. Its own rider: single analysis pass, no cross-seat audit. It sits beside
`passage_norms/`'s "inward and away from the body" and `novel_arc/`'s abstraction
rewind and has never been read against either.

**`opening_matched.md` is WITHDRAWN at construction level** ([5811]) and is correctly
left behind. The forced word conditions the generation but appears in NEITHER the
prompt NOR the scored text, so forced rows are scored on a continuation carrying one
more word of context than undisturbed rows. Nothing in it is a result. It is named
here so that nobody ports it later on the strength of its title.

## One shape showing up at both grains

`selection_and_combination/` reports, from the page: direction predicts composition
(`net_fall` 36/36) and volatility does not (`pct_moved` 18/36, exact chance).
`experiments/displacement/displacement_axis/` reports, from the distribution and by a different
estimator: direction is nameable (`harm` 44/47 frames, p=2.5e-10) and magnitude is
not (every named scale negative alone). Neither knew about the other.

That is the asymmetry to carry into the writing, and it is stronger for having been
found twice: **alignment has a direction you can name and a magnitude you cannot.**
