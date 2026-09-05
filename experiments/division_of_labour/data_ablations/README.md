---
kind: question
subject: data_ablations
status: "RUN 2026-09-04/05. Five Tulu-3 SFT checkpoints. jaccard_lift and how_it_differs run on all three edges (raw, framed, self); ablation.py is self-edge plus a raw control; semantics.py and funnel.py are RAW ONLY. EXPLORATORY throughout -- nothing here is registered."
question: Which SFT training corpus installs which part of the displacement operation?
headline: "Removing SAFETY data is the only ablation that funnels LESS to speech (-0.071, 614/767, p=4e-5) while every other cut funnels more -- safety data does not change how much moves (U_ladder) but does change where it goes. Removing WildChat is the only ablation that makes the landing LESS safe (transgressiveness +0.091, contextual scene +0.112, both p<0.01) and the only one whose sensation share drops (-2.12); it also changes WHICH words move on every edge. The full-mix norm and field results here are norm_change's, rediscovered at one checkpoint."
---

# data_ablations

**`division_of_labour` asks which alignment STAGE carries the displacement. This
asks which CORPUS does**, which is the same question moved one level down. It
sits beside `removal_rates` deliberately: that folder found SFT stripping 37.7%
of inherited sexual mass against 26.8% for frequency-matched neutral vocabulary,
and this one asks which of SFT's training sets is responsible.

Moved here from `displacement/rate_and_magnitude` on 2026-09-05, where the
material had outgrown a folder whose question is "how much mass moves and how
often".

## The instrument, and why it cannot be replicated

Tulu-3 ships four leave-one-out SFT checkpoints beside the full-mix one: same
base (`meta-llama/Llama-3.1-8B`), same recipe, one training source removed. Every
alternative explanation is held fixed by construction.

**No second suite exists.** `U_ladder` searched HuggingFace, arXiv and lab
post-training documentation and found none meeting the bar, confirmed these five
are the complete Tulu set (`-no-code-data`, `-no-if-data`, `-no-science-data`
were probed for and do not exist), and recorded the status as UNAVAILABLE rather
than PENDING. Meta's MobileLLM-Pro ran seven-domain leave-one-out ablations and
released none of the ablated checkpoints, which is the normal case.

**What each ablation removes**, from `allenai/tulu-3-sft-mixture` (939,343 rows,
19 sources, a `source` column the cuts are made on):

    wildchat    tulu_v3.9_wildchat_100k                      100,000   10.6%
    safety      wildguardmix + wildjailbreak + coconot       110,983   11.8%
    persona     five personahub sources                      284,919   30.3%
    math        numinamath + gsm8k + the personahub MATH     334,252   35.6%

`math` and `persona` OVERLAP -- 334,252 includes the three personahub maths sets
-- so they are not disjoint cuts. Slice definitions: Tulu 3, arXiv 2411.15124
§4.1/4.3, Tables 7 and 10. **The checkpoints themselves are undocumented**: all
three ablation model cards are the empty auto-generated HuggingFace template.

WildChat is the smallest cut and the only one that is real logged user traffic.
Its user turns are unstructured -- a one-line "Repeat this string" next to a
request for the introduction to a Turkish thesis on mine-detection circuitry --
against persona data's authored exercises with numbered parts and checkable
constraints ("exactly 5 sentences, include the keywords quiet, community,
ocean").

## Three producers, three edges

    raw       base_raw -> arm_raw          2,981 prompts
    framed    base_raw -> arm_framed         840, clean-slot population
    self      arm_raw -> arm_framed          840, base == aligned

All five checkpoints carry all three. On a self-edge the model is its own base
and has no lift, so the family base's lift is used -- `ladder.py`'s convention,
constant across arms, so it cannot manufacture an arm difference.

### `ablation.py` -- what raises frame responsiveness

Paired within prompt, full mix MINUS the ablated checkpoint:

    removed       d frame      t   d control      t    d dose      t    d mass      t
    no-math        -0.183   -1.2      -1.752  -13.6    -0.195   -1.1   -0.0042   -3.2
    no-persona     -0.501   -3.2      -1.711  -13.3    -0.113   -0.6   -0.0082   -6.4
    no-safety       0.240    1.4      -1.427  -11.8    -0.038   -0.2    0.0019    1.3
    no-wildchat     1.396    6.8      -0.842   -4.9    -0.684   -2.8    0.0136    7.6

**The control is what makes this an experiment.** Every ablation LOWERS it (t
-4.9 to -13.6) because removing training data lowers movement generally. Only
WildChat's frame column moves OPPOSITE its own control. And it is the smallest
cut, so a data-volume account predicts the smallest deviation and gets the
largest.

Threshold artifact closed: theta is a fixed 0.001 across all five, and
threshold-free mass reproduces the ordering (no-wildchat +0.0136, t=7.6, a 6.4%
rise in displaced total variation). Candidate-set sizes are 156.1-157.0.

### `jaccard_lift.py` -- WHICH words, on all three edges

Faller Jaccard against the full mix. `mean J` is the level; the paired contrast
is `J(no-wildchat) - mean J(other three)` on the same prompt.

    edge      n    no-math  no-persona  no-safety  no-wildchat   gap    slope     t
    raw     1839     0.574      0.570      0.566        0.360  -0.210  -0.0284  -3.1
    framed   763     0.721      0.699      0.670        0.566  -0.130  -0.0163  -1.9
    self     683     0.577      0.562      0.519        0.445  -0.108  -0.0070  -0.6

**The LEVEL difference survives every edge.** WildChat's removal changes which
words move whether the aligned arm is bare, framed, or held fixed while only the
template changes.

**The LIFT SLOPE does not.** The divergence grows with charge on the raw edge
(t=-3.1), marginally framed (t=-1.9), and not at all on self-edges (t=-0.6). So
the charge-dependence belongs to the weight change, not to the frame -- which is
what the self-edge is for.

Denominator control on the raw edge: union size is flat with lift for every arm
(t -0.2 to 0.9) and the full arm's own faller-set size is flat (t=0.3), so the
slope is in the numerator.

### `how_it_differs.py` -- and the one result that is raw-only

SEXUAL as a share of each side's uniquely-shed set, unit = the prompt:

    edge      arm            n     mean d    up/dn        p
    raw       no-wildchat  295    +0.0243    43/24   0.0271
    framed    no-wildchat  138    +0.0308    23/14   0.1877
    self      no-wildchat  115    -0.0155     8/12   0.5034

**Framed points the same way at the same size and does not reach significance at
half the prompts; self flips sign and is null.** Do not read the framed column as
a replication or as a failure -- it is underpowered, and saying which would need
the MDE computed rather than the p-value read.

The raw-edge picture, which is the only one that clears: removing WildChat
lowers the sexual share of what gets shed (+0.024), removing the two non-sexual
bulk slices RAISES it (no-math -0.092 p=0.003, no-persona -0.086 p=0.001), and
removing safety does nothing. That is consistent with the share tracking the
sexual density of the mix that remains -- **a corpus prediction nobody has
checked**, and `posttraining_corpus_analysis` is where it goes.

## `semantics.py` -- WHAT KIND OF WORD, ON THE RIGHT INSTRUMENT

`how_it_differs.py` asked what changes about the moved words using the per-prompt
`kind` rating, and that instrument is too coarse: `kind` sorts by HOW BAD, not by
WHAT ABOUT, so `kill` is VIOLENT and `scream` is NONE and the campaign's paradigm
case of displacement scores as suppression. `malignment/fields.py` supplies what
the question needs -- semantic FIELDS, plus type norms and contextual ones kept
apart.

### The full mix: riser minus faller, mass-weighted, unit = the prompt

    kind         scale                     mean d     up/dn        p     cov
    TYPE/human   warriner_valence          0.3143  1014/687   0.0000     57%
    TYPE/human   warriner_arousal         -0.3234  643/1059   0.0000     57%
    TYPE/human   warriner_dominance        0.0992   912/790   0.0033     57%
    TYPE/human   brysbaert_concreteness   -0.0583  930/1126   0.0000     80%
    TYPE/model   k_transgressiveness      -0.2359   490/763   0.0000     79%
    TYPE/model   k_charge                 -0.2324  913/1037   0.0053     79%
    TYPE/model   k_valence                 0.1022  1043/790   0.0000     79%
    TYPE/model   k_bodily_harm            -0.3102   407/613   0.0000     79%
    TYPE/model   k_concreteness           -0.2440  889/1149   0.0000     79%
    TYPE/model   k_register_level          0.0780   781/667   0.0030     79%
    CONTEXTUAL   scene                    -0.2893  886/1257   0.0000     79%

**What rises is less transgressive, less charged, less about bodily harm, less
aroused, and more positively valenced than what falls.** On human type norms, on
model type norms, AND on the contextual scene rating.

**THIS TABLE IS NOT NEW AND IS THE WEAKER VERSION** (RH). `displacement/norm_change`
already measures it, better: its quantity is the mass-weighted norm shift
`sum(dp(w) * norm(w))`, and since `sum(dp) ~ 0` that is this table's
riser-minus-faller difference multiplied by the moved mass. The two agree on
sign wherever they overlap -- register rises (+0.0063 there, +0.078 here),
valence rises (+0.0026 / +0.102), concreteness falls (-0.025 / -0.244) -- and
norm_change runs it over **50 endpoint lineages** with a per-lineage sign test
where this column has one checkpoint. **Cite norm_change for the norm result.**

What this table is for is the ABLATION contrast below, which norm_change does not
run. It does scan fields -- see below -- so that is not a difference either.

The type/contextual agreement matters: `scene` rates the same word differently
per prompt, so its agreement with `k_transgressiveness` says the safety gradient
is in the vocabulary and not only in the scene.

### And the FIELDS see the move the harm taxonomy could not

Share of moved mass, riser% minus faller%, full mix:

    RID   (coverage 31% faller / 33% riser)      USAS  (74% / 76%)
      sensation             +4.15                  Speech:- Communicative  +2.90
      instrumental_behavior +1.71                  Moving, coming, going   +1.17
      social_behavior       +1.39                  General actions, making +0.96
      abstraction           +1.21                  Location and direction  +0.06
      icarian_imagery       -0.99                  Putting, taking...      +0.20
      temporal_references   -0.70                  Getting and giving      -1.78
      aggression            -4.14                  Grammatical bin         -2.19

**Mass leaves the AGGRESSION field and lands in SENSATION and SPEECH.** That is
`kill -> scream` stated as a field displacement, on a 1960s regex lexicon and a
232-code tagset that know nothing about this project. **`displacement_taxonomy`'s
relation 2, BLOW BECOMES UTTERANCE, measured distributionally for the first
time.**

**AND THIS FIELD RESULT IS ALSO NOT NEW.** `norm_change` scans USAS at 362
targets over 50 lineages, raw AND framed, and already reports it -- with a second
instrument this folder does not have:

> The lexicon route gave `Q2.2 Speech acts` +0.0079 and `X3.2 Sensory: Sound`
> +0.0179 under dose; the LLM-coded contextual route gives `vocalisation` +0.386.
> **Where the base arm was transgressive, alignment moves toward speaking.** Two
> instruments, one direction, and neither was built to test the other.

Its field-level summary is the same shape as this one: *"alignment strips action
vocabulary (speech acts, warfare, obligation, bodily processes) and replaces it
with procedural, hedging, and safety language"*, with `L1-` (killing/dying)
leading. **Cite norm_change for the field result too.** RID is the only lexicon
here that norm_change does not use, and at 31% coverage it is the weaker one.

**SO WHAT IS ACTUALLY NEW IN THIS FILE IS THE ABLATION CONTRAST, AND NOTHING
ELSE.** The full-mix norms table and the full-mix field table are both
rediscoveries of `norm_change` at one checkpoint instead of fifty lineages. They
are kept because the ablation rows need a baseline computed the same way, not
because they add evidence.

### WHAT WOULD BE NEW FOR `adjacency.py`, AND IT IS NOT THIS

`norm_change` measures the MARGINAL field shift: aggression down, speech up,
across the whole distribution. `adjacency.py` asks a CONDITIONAL question --
given that the top faller is in field F, does the freed mass land in F, in
another field, or in no field at all? That is the displacement-vs-suppression
distinction, and a marginal shift cannot make it: "aggression falls and speech
rises" is equally true whether each aggression word's mass went to speech or
whether unrelated words moved in both fields.

**That conditional, on USAS fields instead of six harm categories, is the
instrument `existence/adjacency.py` should be using**, and its low-saturation
"reversal" is a strong candidate for `kill -> scream` misread as suppression.

Read RID's shares against 31% coverage. USAS at 74-76% is the better of the two
here and says the same thing.

### The ablations: WildChat is what makes the landing safe

Arm's (riser - faller) minus full's, paired by prompt id:

    scale                      no-math   no-persona    no-safety   no-wildchat
    warriner_valence           -0.0221      -0.0299     -0.0658*      -0.1334*
    warriner_arousal           -0.0157       0.0234      0.0260        0.1728*
    warriner_dominance         -0.0108*     -0.0217*    -0.0207*      -0.0989*
    brysbaert_concreteness     -0.0587*     -0.0685*    -0.0322*      -0.0846*
    k_transgressiveness        -0.0051:     -0.0116      0.0188        0.0905*
    k_charge                   -0.0072       0.0251      0.0246        0.0982
    k_valence                  -0.0133*     -0.0244*    -0.0220*      -0.0621*
    k_bodily_harm               0.0033       0.0089      0.0352        0.0552*
    k_concreteness             -0.1056*     -0.1327*    -0.0482:      -0.1637*
    k_register_level           -0.0076      -0.0340*    -0.0371:       0.0024
    scene                       0.0040       0.0082      0.0353        0.1118*

**`no-wildchat` is the only arm whose landing is LESS SAFE than the full mix's**,
and it says so on every axis that measures safety: transgressiveness +0.091,
bodily harm +0.055, arousal +0.173, valence -0.133, and the contextual scene
+0.112, all p<0.01. The other three arms are null or small on exactly those
scales while moving with it on concreteness and valence, which is what removing
any training data does.

In the field view the same arm shows `sensation` at **-2.12**, the largest single
field deviation of any ablation: removing WildChat costs the shift into sensation
that the full mix performs.

**This supersedes `how_it_differs.py` as the answer to "how does it differ".**
That file's sexual-share result was 2 to 9 percentage points on a contextual
label that turned out to be scene-level; this is the same question on continuous
norms with coverage reported, and it points the same way with far more of the
mass accounted for.

### Fences on this section

Coverage is printed and is not uniform: Warriner reaches 57% of moved mass, the
k-scales 79%, Brysbaert 80%, USAS 74-76%, **RID only 31%**.

The k_* scales are ONE MODEL's judgments at one frozen instrument version, not
human norms. `k_register_level` is NOT ESTABLISHED (inter-coder 0.60) and is
printed as a descriptor. `k_vulgarity` is a sparse indicator and is not used
here. `fields.k_warnings()` prints all three beside the numbers.

An earlier version of this table paired arms POSITIONALLY rather than by prompt
id, and reported medians where the k-scales are integers so the median read
0.0000 against a decisive sign test. Both fixed; the numbers above are the
corrected ones.

EXPLORATORY. One family. Nothing registered.

## `funnel.py` -- SAFETY DATA IS WHAT AIMS DISPLACEMENT AT SPEECH

`existence/field_matrix.py` shows freed mass routing to a small destination set
regardless of origin, narrowing toward speech under lift. `semantics.py` above
reports the MARGINAL field composition per arm, which is a different quantity:
"the speech share of riser mass rose" does not say a given faller's mass went to
speech. This runs the CONDITIONAL version, per arm, on the same availability
baseline `field_matrix.py` uses.

Enrichment = riser mass share of a domain divided by that domain's share of the
base distribution IN THE SAME CELL. Unit = the prompt, paired by prompt id.

    Q linguistic acts       full mix enrichment 1.272, over 2,162 prompts
        no-persona      +0.1159   753/624   p=0.00056  *
        no-math         +0.0491   762/612   p=0.00006  *
        no-wildchat     +0.0187   785/693   p=0.01790  :
        no-safety       -0.0713   614/767   p=0.00004  *   <-- ONLY ARM DOWN

    X psychological         full mix enrichment 1.126
        all four arms NEGATIVE and significant (-0.020 to -0.149)

    S social                full mix enrichment 0.948
        no-persona -0.0676 p=0.0002; the rest small or null

**Removing the safety corpus is the only ablation that funnels LESS to speech.**
Every other cut increases it. So safety data is what aims displacement at the
linguistic destination -- and `no-persona`, which removes 30% of the mixture,
moves it the other way by more than twice as much.

**THIS IS THE FIRST CLEAN POSITIVE RESULT FOR THE SAFETY CORPUS IN THE
CAMPAIGN, AND IT DOES NOT CONTRADICT `U_ladder`.** That finding is about
MAGNITUDE: every slice costs 10-12%, `no-safety` costs what `no-math` costs, so
safety data is not what produces displacement. That stands. This is about
DESTINATION, which nothing had asked. **Safety data does not change how much
moves; it changes where it goes.** Those are separable and the pair is the
result.

The `X psychological` column is the control that makes it readable: all four arms
lower it, so "removing any data lowers the funnel" is a real generic effect and Q
is the column where one arm departs from it in the opposite direction.

### Dosed, and honestly underpowered at the top

Same contrast inside lift bands, target Q:

    removed            L-lo     L-mid     L-hi
    no-math           0.056*    0.010    -0.102
    no-persona        0.140*    0.104    -0.191
    no-safety        -0.052*   -0.065:   -0.493
    no-wildchat       0.065*   -0.022    -0.476

**Every arm turns negative at high lift, including the three that are positive at
low lift, and not one L-hi cell clears p<0.05.** The magnitudes there are the
largest in the table, which is exactly the shape an underpowered cell produces.
**Do not read a dose reversal off this.** What is supported is the low-lift
column, where the sign pattern matches the pooled result.

FENCES. One family, no replication. Raw edge only -- the framed and self versions
are a cheap run and have not been done. USAS top-level domains, not fine codes.
EXPLORATORY, unregistered.

## THE SAME FIVE CHECKPOINTS, A DIFFERENT QUESTION (malign, docket [6632])

`subject_position/framed_identity` runs this instrument on self-identification
rather than on displacement, and finds **`no-persona` categorically replaces the
model's account of its own origin**:

    Tulu-3-8B-SFT              Ai2 30 / OpenAI  5      Ai2 35 / OpenAI  1
    SFT no-math-data           Ai2 20 / OpenAI  7      Ai2 32 / OpenAI  5
    SFT no-wildchat-data       Ai2 33 / OpenAI  1      Ai2 38 / OpenAI  0
    SFT NO-PERSONA-DATA        Ai2  0 / OpenAI 29      Ai2  0 / OpenAI 33

Zero of 67. Every other arm names Ai2 as its top answer at both system
conditions. Its own caveat, kept: one checkpoint per ablation, so this is a
reason to test rather than a result -- flagged because the effect is CATEGORICAL
where a checkpoint artefact would move a rate.

**WITHDRAWN, malign [6633].** This paragraph read `ablation.py`'s
`no-persona` frame-responsiveness column (-0.501, t=-3.2) as converging with
`framed_identity`'s "+15.0pp on names its maker, 13/15, p=0.007" and concluded
that persona data installs the assistant's framed self-presentation. **The
+15.0pp was pooled over three different manipulations.** Split by what the
template actually renders, the significant cell is the group where NO persona is
present in either condition (n=10, -15.0pp, 0/9, p=0.004); the four models that
do carry a persona give -25.0pp at 0/4, p=0.125, which four models cannot resolve
either way. So that number is about the system slot EXISTING, not about what is
in it, and there is no convergence to report.

The between-arm result is untouched: all five Tulu arms sit in the same group and
received the same manipulation, so `no-persona` naming Ai2 0 of 67 stands.

Note the division: **WildChat removal changes which WORDS move; persona removal
changes who the model says MADE it.** Different slices, different functions,
neither reducible to "less training data".

## Fences, and three things this folder got wrong first

**One family, one ablation set, no replication available or coming.**

**`kind` is CONTEXTUAL, not lexical.** Reading cells shows `said`, `spoke`,
`told`, `asked` rated SEXUAL inside a sexual scene. This supports a claim about
words that advance a sexual reading in context, not about a sexual lexicon.
`removal_rates` uses a blind-built lexical set against frequency-matched neutral
vocabulary and is the instrument for the lexical version.

**A raw COUNT test is confounded** -- the full mix sheds 1.27 more words per
prompt than `no-wildchat` (221/137, p<1e-4), so counts favour it in every
category. The share test above is the corrected one, about a tenth the size. A
per-category table is printed alongside because `NONE` being dead null at 88/87
is what shows the excess is not uniform.

**And a pooled word-level test got two arms backwards.** It is printed too. Four
aggregations were tried; the producer emits all of them rather than the
conclusion alone.

## Prior art, which came first

`malign-logits` `meta/M01_displacement/findings/U_ladder.md` ran these five
checkpoints in August on MAGNITUDE: every slice costs 10-12%, `no-safety` costs
what `no-math` costs, so **safety data is not what produces displacement.** That
stands, unamended by anything here.

`DISPLACEMENT_EVIDENCE.md` §197 had already singled WildChat out on WHICH words
move -- faller Jaccard 0.340 against 0.522-0.534 -- and summarised it "magnitude
normal, direction different". **This folder's Jaccard level result is the second
observation of a known singularity, not the first of a new one.** What is new is
the lift slope, the framed and self edges, and the frame-responsiveness column.

§197 also tested the reading that WildChat's divergence is about transgression,
using a binary neutral-vs-transgressive prompt split, and found it flat. **That
null is the weaker instrument**: the split is a dose-LEVEL contrast, and
`malignment/charge.py` documents dose as the wrong selector because response
saturates above frame 5. Recomputed against lift, §197's own outcome is not flat.
