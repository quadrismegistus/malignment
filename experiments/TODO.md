# TODO — what to re-do from the archive, organised by question

A scan of `~/github/malign-logits/meta/`: **6 campaigns, 70 findings docs, 49
registrations, 455 scripts.** This groups them by the QUESTION THEY ASK rather
than by the campaign letter they were filed under, because the letters are a
namespace and the namespace filled — `M01` alone holds 32 findings and 250
scripts, and the same question appears under three letters in two campaigns.

**Nothing here is a plan to run.** It is what exists, what is wrong with it, and
which v3 instrument it would land on.

## READ THIS BEFORE SEQUENCING ANYTHING

**THE BOUNDARY REPAIRS CHANGE EVERY CELL IN THE STORE.** `numeric_boundary`
established that `boundary_mask` reads the raw token key rather than the decoded
one, on 88 of 88 tokenizers, and malign's shadow-mask measurement puts the effect
at **+15-28% resolved mass on Chinese and +0.12% on English**. RH has ruled v4
proceeds because the instrument is wrong, not because a question needs it.

**So anything below that reads `twp_words` should wait for v4, or be run knowing
it will need re-running.** Two exceptions, and they are the cheap wins: work that
reads GENERATED TEXT (M06, passages) and work that reads LEXICONS AGAINST WORD
LISTS never touches the boundary mask.

## THE ARCHIVE'S OWN DEFECTS, WHICH DECIDE WHAT IS WORTH CARRYING

Three recur across the 70 and each disqualifies a different thing:

    hybrid_word_probs mixed scales   4 findings rest on it. Single-token words
                                     get true vocabulary probability, multi-token
                                     words get beam-set-relative values, and
                                     43-90% of multi-token entries violate the
                                     P(word) <= P(first token) ceiling.
                                     -> any ABSOLUTE threshold or cross-word
                                        ranking on it is void; ratios largely survive
    single lineage / single family   8+ findings. Three recipes on one pretraining
                                     run are not three observations.
    underpowered, MDE unstated       8+ findings report p without what the test
                                     could have detected.

---

# 1. WORD NORMS — the valence / arousal / concreteness axis

**The largest cluster and the best-supported. Five findings across three
campaigns asking one question: does alignment move words along affective scales,
and which scale.**

    M01 C_deextremification   de-extremification CONFIRMED corpus-wide
                              +0.025 residualised, p 0.0012. Flatter, not nicer:
                              the DOMINANCE contrast shows nothing.
    M01 E_gap_stratum         replicates on a blind stratum, 19 of 25 lineages,
                              p 0.0073
    M01 D_site_suite          the same at substitution sites: what moves is
                              EXTREMITY, not valence sign
    M01 K_word_properties     which word properties predict movement.
                              vulgarity 12/13 falling p 0.0034;
                              transgressiveness flat at +0.012
    M01 O_crosslingual        THE AFFECT SIGNATURE DOES NOT TRAVEL to Chinese
                              (the substitution does)
    M05 H_norm_acquisition    SFT installs the norm signature, DPO partially
                              rebuys it, and the rebound REVERSES the SFT sign.
                              A two-module dissociation at norm grain.
    M05 C_affective_convergence  site-specificity lives in affect; its SIGN under
                              alignment is not robust

**v3 route: ready now, and it does not touch the boundary mask.** `fields.py` is
ported (813 -> ~330 lines) with `lexicons/norms/` carrying Warriner (valence /
arousal / dominance), Brysbaert (concreteness) and `k_ratings` in **both en and
zh** — which is what O_crosslingual needs and did not have cleanly.

**Why re-do rather than cite:** `H_norm_acquisition` rests on `word_probs`, and
the O/zh arm is the one place the cluster has a real negative. The v3 port also
fixed the thing that made the archive version unreproducible — a missing lexicon
DEGRADED to an empty dict instead of raising, so an absent source and a measured
zero were indistinguishable.

**One question the cluster never asked:** every finding measures movement ALONG a
norm. None asks whether alignment changes the norm-to-frequency relationship,
which is the confound `matched_nonmovers` now exists to control.

---

# 2. SEMANTIC FIELDS — where the mass goes when it moves

**Three findings, three campaigns, and they disagree about scope.**

    M01 T_category_flow       where the mass goes. 70 of 94 testable pairs hold.
                              ITS OWN HEADER WARNS findings 1-9 use the weaker
                              unit and 5,976 rows are not 5,976 observations
    M05 B_field_flow          alignment DE-CONCRETIZES. But pretraining moves the
                              fields ~6x more than alignment does
                              (physical_action 0.001 -> 0.261 in pretraining;
                              largest alignment shift 0.04)
    M02 field_signature_not_contradiction_specific
                              39 of 79 fields move roster-wide;
                              0 of 79 are contradiction-specific

**These three are one finding and should be one experiment.** The M02 result is
the control the other two lack: a field signature that appears everywhere is not
evidence about any particular prompt type. **B_field_flow's 6x is the number that
reframes the cluster** — if pretraining does most of the field movement, an
alignment field effect needs the pretraining baseline in the same figure.

**v3 route: `fields.py` SOURCES (rid, general_inquirer, wordnet supersenses,
usas) + `wordfield.py`.** Coverage caveat carried from the archive: ~0.58,
because function-word mass is uncovered by content-word lexicons.

---

# 3. MASS OF MOVEMENT — how much moves, how often, how far

    M01 N_mass_migration      SUBSTITUTION CONFIRMED AT SCALE. 2,199 stimuli x
                              44 edges, 82,775 cells, 91% run in the substitution
                              direction. The CLUSTER is the unit (34).
                              The flagship result.
    M01 F_G_rate_magnitude    the pair that makes the claim precise:
                              RATE NULL (33 pair-sites, p 0.148 — transgressive
                              sites do not fire displacement more OFTEN)
                              MAGNITUDE CONFIRMED (d 0.748, p 0.00006 — when they
                              fire they displace HARDER)
    M06 propagation           the chain absorbs ~99% of an imposition
    M06 composition_not_level M01's displacement carries M06's passage effect;
                              composition held fixed BY CONSTRUCTION

**F/G is the cleanest pair in the archive** — a registered null and a registered
positive on one instrument, and together they say something neither says alone.
Carry both or neither.

**v3 route: `movement.py` + `produce_movement` + the `movement` table**, which is
already the roster-driven version. **Waits on v4** — this is all `twp_words`.

---

# 4. THE PRETRAINING LADDER — what installs when

    M05 A_acquisition     the prohibition is an EVENT, the substitution is a DRIFT
    M05 F_syntax_curve    syntax installs as an event, after an agrammatical spam
                          phase, BEFORE any capacity
    M05 G_sense_curve     sense installs WITH syntax; no colorless-green phase
    M05 E_pythia_capacity the Pythia ladder resolves the tie: packages first,
                          facts after phrases
    M05 pole_sep_is_not_about_poles   a NULL discharging an owed debt; floor at
                          step 256
    M01 U_ladder          SFT does the cutting; safety data is not what produces
                          displacement
    M03 D_ladder_selection  alignment SELECTS from a repertoire pretraining already
                          built — which is why the effect is sudden

**The most theoretically load-bearing cluster and the thinnest empirically.**
M05's phase-2 rests on OLMo alone; `MANIFEST.md` already records that SmolLM3-3B
is a second complete pretraining ladder — **118 revisions, different lab,
different corpus** — and that M05's "no family anywhere releases preference-stage
trajectories" was a survey of 8.

**v3 route: the roster holds pythia-2.8b + the archangel ladder (5 arms), 14 OLMo
nodes, and SmolLM3's revision container.** `Checkpoint` resolves a pinned
revision from `@suffix` or the roster's `revision:` field.

**Highest-value re-do in the whole list**, because the claim is about ORDER and a
second ladder is the only thing that can test it.

---

# 5. FRAME EXIT AND NAMING — M02

    second_order_naming        THE STRONGEST POSITIVE IN M02. Alignment names the
                               contradiction AS a contradiction, and only the
                               contradiction. Two instruments, replicated.
    naming_survives_form_control  survives a form-matched control
    contradiction_ratio_has_no_null   F11's ratio has no null and 1.0 is where
                               NEITHER pole lands
    ratio_moves_destination_unknown   the ratio moves; it cannot say toward what
    M02_eassist_ambient        aligned models emit the assistant frame UNBIDDEN,
                               17 of 18 movers
    depth_and_exit_do_not_join NULL, and informative

**`second_order_naming` + its form control is the carry.** The two ratio findings
are the same caution twice and should be one note, not two findings.

---

# 6. THE INSTITUTIONAL ARM — M03

    A_speaker_kernel     the largest factor is a HEDGE, not a position. Adding
                         `probably` moves alignment's valence shift +0.207 against
                         +0.077 for the whole individual/institutional contrast
    B_C_arm_and_reference_class   THE ARM EFFECT REVERSES F21's DIRECTION
    E_lexical_arm_contrast   the roster-wide version, 46 lineages

**`probably` outweighing the entire designed contrast 2.7x is the finding**, and
it is a warning about every prompt-pair design in the archive: a single modal
can dominate the manipulation. **B_C reversing F21 needs resolving before F21 is
cited anywhere.**

---

# 7. CROSS-LINGUAL — and it is a real cluster, not a robustness check

    M01 O_crosslingual        the substitution travels; THE AFFECT SIGNATURE DOES NOT
    M01 zh_sites_unit_limited a NEGATIVE WITH A STRUCTURAL CAUSE, not a null —
                              the cell cannot be filled by analysis
    M02 zh_guilt_pathology    direction survives two stages; specificity does not
    M06 zh_fluency_and_ordering   Chinese fluency is an ARM VARIABLE, and it
                              separates spread from ordering
    M06 crosslingual_arms     the same operation in both languages

**This cluster is now instrument-blocked in a way it was not before.** The CJK
boundary defect is +15-28% resolved mass on Chinese against +0.12% English, on 84
of 133 models — **so every cross-lingual comparison on stored cells is comparing
instruments.** Nothing here should be re-run until v4 lands, and the archive's
Chinese results should be read with that differential in mind.

**Exception: anything on generated text.** `zh_fluency_and_ordering` used bge
embeddings of generated passages, not cells, so it is unaffected.

---

# 8. GENERATION AND PASSAGES — M06

    AB_surface_and_clauses  the style of alignment is COMPRESSION, not
                            simplification
    f15_on_passages         the quadrant flow survives; the metonymic gain is general
    p_on_passages           the signature survives the trip; the drag is priming
    self_surprisal          the ALIGNED model is soothed by the vocabulary it
                            promoted. THE MIRROR IS HALF-ESTABLISHED
    drift_metric_audit      it measures SEMANTIC SPREAD, not trajectory
    offset_repair           the sign reverses
    opening_matched         WITHDRAWN at construction level — the comparison was
                            never opening-matched

**Reads generated text, so it does NOT wait on v4.** With `salary_probe` having
just shown `generate` walks past both twp blockers, this is the cluster that can
move first.

`drift_metric_audit` and `offset_repair` are instrument notes, not findings, and
belong in `instrument_calibrations/` if they come.

---

# 9. THE SUPEREGO AND THE SCENE — the theory-facing cluster

    M01 Y_diegetic_superego  alignment MORALISES INSIDE the scene it keeps writing,
                             and it survives the strongest available control
    M01 X_metonymy           the substitution runs down THE SCENE'S OWN SCALE
    M01 W_forced_continuation  estrangement without damage
    M01 X_safety_ablation    the prohibition corpus is not what does the prohibiting
                             — BUT ITS TITLE IS CONTESTED BY ITS OWN OUT-OF-SAMPLE
                             ARM (§4b, 2026-08-15). Do not cite the headline.

**Y and X_metonymy are the two findings the article leans on hardest and both are
marked `descriptive`.** X_safety_ablation is the one to resolve or retire: a
headline its own replication arm contradicts is worse than no finding.

---

# 10. DEPTH, ATTENTION, GEOMETRY — the mechanism cluster, mostly negative

    M01 H2_alignment_depth   alignment is DISTRIBUTED through the stack, not
                             concentrated in the last layers. The LINEAGE is the
                             unit, not the pair, and neither is the cell
    M01 J_arch_displacement  displacement does not need attention
    M01 V_embedding_regions  embedding geometry FAILS at the relation and
                             validates something else
    M04 attention_back_cross_own   a large pair-specific effect and NO effect of
                             alignment
    M04 A_post_utterance_shock
    M05 lens_ladder_instrument_note  the depth signature is HEAD-DEPENDENT

**Four negatives and a method note.** Worth carrying as a group precisely because
they are negatives: they bound where the mechanism is not, and `J` plus
`attention_back` together say the effect is not attentional.

---

# WHAT I WOULD DO FIRST, IF ASKED

1. **The norms cluster (1)** — ready now, no boundary dependency, best-supported,
   and the zh arm is a real open negative.
2. **The three field findings (2) as ONE experiment** with the pretraining
   baseline in the figure, since B_field_flow says pretraining does 6x more.
3. **The second pretraining ladder (4)** — highest theoretical value, and
   SmolLM3's 118 revisions are already in the roster.
4. **M06 (8)** — unblocked by v4 because it reads generated text.

**Everything on `twp_words` waits for v4.** That is clusters 3, 7, and most of 9
and 10.

## WHAT SHOULD NOT COME

`opening_matched` (withdrawn at construction). The two M02 ratio cautions as
separate findings. `B_frozen` (frozen, never ran). And the 42 findings the
archive's own README records as cited by nothing — **which is not the same set as
the weak ones, and should be checked against this list rather than assumed.**
