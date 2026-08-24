---
subject: norm_change
status: REGISTERED LIGHT, 2026-08-24. Seven directional hypotheses; everything else declared exploratory.
question: Across ~50 base->aligned endpoints, does alignment move the continuation distribution along word norms and semantic fields?
unit: the lineage
languages: en and zh, reported separately, never pooled
---

# norm_change — a LIGHT registration

**This is deliberately not a rigid registration, and the looseness is declared
rather than smuggled.** Seven hypotheses below carry a direction and a decision
rule. Everything else in this folder is EXPLORATORY and will be labelled so
wherever it is reported. RH, 2026-08-24: *"I don't want a rigid registration,
can we do a light one that explicitly licenses exploration?"*

What that licence does and does not cover:

- **Covered.** Looking at any scale, any field, any lexicon, any subset, in any
  order, and saying what is there. Reporting a surprise. Changing what looks
  interesting halfway through.
- **NOT covered.** Promoting an exploratory result to a headline without
  re-testing it on a declared design, or reporting an exploratory p-value as
  though the hypothesis preceded the look. An exploratory finding is a
  candidate for a registration, never a substitute for one.

The seven exist so that the exploration has something to be measured against.
If they all land, the exploration is decoration; if they all fail, the
exploration is the finding.

## THE QUESTION, AND WHY IT IS NOT M05's

**WHETHER, across ~50 endpoint pairs.** Not WHEN. M05's B and H ask when a norm
signature installs, across pretraining checkpoints on the few lineages that have
them (OLMo-3, Pythia). This asks whether alignment moves norms at all, at the
endpoint, on every lineage there is. Merging the two would blur the one
distinction that makes either readable, and an earlier proposal to do exactly
that was refused (RH, 2026-08-24).

## UNIT, POPULATION, TEST

    UNIT         the lineage. A pair is base -> aligned; ~50 exist in `movement`.
    STATISTIC    per lineage, the mass-weighted mean of a scale over the rated
                 words of the continuation distribution, base and aligned
    TEST         paired per lineage, sign test and Wilcoxon, two-sided
    LANGUAGES    en and zh SEPARATELY. Never pooled, never averaged. A zh
                 result that contradicts its en counterpart is a finding, not a
                 robustness failure -- M01 O_crosslingual already found the
                 affect signature does not travel while the substitution does.

## THE SEVEN

| # | hypothesis | instrument | direction |
|---|---|---|---|
| **H1** | concreteness FALLS | Brysbaert (en), Xu & Li (zh), `k_concreteness` | down |
| **H2** | register RISES | `k_register_level`, Brooke formality | up |
| **H3** | the interiority FIELD rises | USAS **X1** *Psychological actions, states and processes* | up |
| **H4** | valence becomes slightly MORE POSITIVE | Warriner valence, `k_valence` | up, small |
| **H5** | \|valence\| DECREASES — narrowing | Warriner valence, absolute deviation from the scale midpoint | down |
| **H6** | euphemism RISES | `euphemism`, sexual slot instrument, contextual | up |
| **H7** | mediation RISES | `mediation`, institutional slot instrument, contextual | up |

**H4 and H5 are the pair that matters and they are not the same claim.** M01's
`C_deextremification` confirmed de-extremification corpus-wide (+0.025
residualised, p=0.0012) and recorded that its sweetening hypothesis "was never
emitted" — i.e. H4 has never actually been tested here. H5 is the replication;
H4 is the new one. They can both hold: a distribution can shift slightly toward
the positive pole while its spread narrows.

**H3 names a specific field, not a construct.** USAS `X1` is
*"PSYCHOLOGICAL ACTIONS, STATES AND PROCESSES"*, with `X2` mental actions,
`X2.1` thought/belief, `X3` sensory, `X4` mental object, `X5` attention beneath
it. The declared test is X1; the finer codes are exploratory.

## THE CONTROL THAT IS NOT OPTIONAL, AND WHY IT IS BUILT IN RATHER THAN BOLTED ON

**Any continuous concreteness result must be reported with a function-word
decomposition beside it.** M01 `T_category_flow` §7 already measured what
happens without one:

    paired within-pair, verb-to-verb   MT-Conc -0.014  CI [-0.076,+0.048]
                                       MDE 0.088 -- a BOUNDED NULL
    all pairs, continuous mean         +0.107 p=7e-05 -- COMPOSITION
      faller is a function word          +0.381   n=3,156
      riser is a function word           -0.320   n=2,455
      two lexical verbs                  +0.021 -- nothing
    binned Concrete/Abstract/Neutral   Bowker p=2.6e-15 -- FIRES

Function words sit at the abstract extreme of every concreteness norm, so
swapping them in or out moves a mean without anything happening. **The
categorical route replicated; the continuous route did not survive the
control.** M05's H uses the continuous route and its riders never mention
composition.

So H1 is tested BOTH WAYS and both are reported:

    CONTINUOUS   mass-weighted mean, with the function-word decomposition
    CATEGORICAL  binned concrete / neutral / abstract, symmetry test

`fields.is_function_word(word, lang)` answers this in both languages —
spaCy for en, SUBTLEX-CH `Dominant.PoS` mapped through `fields.pos_map` for zh,
returning None for unknown words rather than False, because an unknown counted
as content inflates the very group the control protects.

## THE ONE GENUINELY NEW MOVE, AND IT IS EXPLORATORY

`slot_ratings` built per-domain instruments and applied each to its own domain:
the sexual instrument to sexual frames, the institutional one to institutional
frames. **Nobody has applied a domain instrument to every prompt it has ratings
for, regardless of the frame's declared domain.** RH, 2026-08-24: *"not sure
what it does to apply sexual norms to any prompt we have it for and not limit to
sexual domains explicitly marked, maybe worth a try because we didn't do that in
slot_ratings."*

H6 and H7 are therefore stated as directional but read against a hazard the
`slot_ratings` README names about itself: **instrument coverage runs in the
direction of the finding.** Institutional and sexual got bespoke instruments;
identity did not. A cross-domain application inherits that asymmetry and any
domain contrast has to be read with it in view.

## WHAT IS ALREADY BUILT

    fields.norms / norms_zh          continuous, per source coverage
    fields.count / count_zh          categorical fields; zh is USAS-only
    fields.usas(..., lang=)          shared tagset across languages
    fields.contextual_norms(prompt, word)   the (prompt, word) layer
    fields.slot_prompts()            534 prompts that HAVE contextual ratings
    fields.is_function_word          the control, both languages
    fields.freq / dominant_pos       SUBTLEX-US and SUBTLEX-CH

**Any contextual analysis restricts to `slot_prompts()`.** Joining without it
compares a rated subset against an unrated remainder and reports the difference
as an effect.

## STATED LIMITS, BEFORE ANY NUMBER EXISTS

- **The zh categorical battery is USAS only.** RID, General Inquirer and the
  WordNet supersenses have no Chinese counterpart in `lexicons/`. `count_zh`
  raises rather than returning an empty dict.
- **The zh USAS is not tag-ranked** the way the English one is, so it
  contributes every sense at fractional weight while English contributes its
  ranked first at full weight. The two are comparable in FIELD IDENTITY —
  same tagset — and not in tag density.
- **zh segmentation is dictionary maximum-matching** against twp's own word
  list, chosen for agreement with `twp_words` rather than for accuracy. It is
  not a trained segmenter.
- **The Chinese concreteness scale is published REVERSED** relative to
  Brysbaert. `fields` returns the aligned column; anyone reading the raw file
  must not.
- **`k_vulgarity` and `brooke_formality` are sparse** and stay marked.
- **This is a different instrument from M01's**, which used Lancaster
  sensorimotor, MRC, an MTurk concreteness set and Paivio over 37,563 words.
  Agreement with M01 is corroboration across instruments; disagreement is not
  automatically a failure to replicate.
