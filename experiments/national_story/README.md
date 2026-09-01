# National stories: what alignment adds to a plot

Producers: `run.py` (local HF), the vLLM fleet via `malignment.vllm_generate`.

    judge.py               is it a story at all -> judged_stories_v2.jsonl
    code_story_conflict_v1 the annotation instrument (in malignment/tasks/)
    conflict.py            runs it -> conflict_nocap.jsonl
    tropes.py              the six Rettberg tropes, lexical, three voted sets
    analyse.py             the lexical contrasts
    contrast.py            paired arm table with lineage sign counts
    tests.py               sign / signed-rank / paired t, LINEAGE as the unit
    homogeneity.py         entropy and pairwise distance, world vs outcome
    demonym_separation.py  within / between / overall by demonym
    field_variance.py      the same, decomposed field by field
    homogeneity_summary.py percent-change summary, arm and frame
    export_db.py           -> conflict.sqlite for the web explorer

Prompts: `prompts_compare.jsonl` (8 demonyms + a no-demonym control, raw and
prefill), `prompts_rettberg.jsonl` (cell 2, never run at scale).

Replicating Rettberg & Wigers (2025) -- 11,800 national stories from gpt-4o-mini,
released CC0 -- with the arm they lack: base against aligned. Their second peer
reviewer (Kang) asks in print why the plot structure is there; the paper cannot
answer, because one aligned model has no counterfactual.

## THE FINDING: ALIGNMENT INSTALLS THE RESOLUTION, NOT THE PROBLEM

Paired within lineage, raw frame, t=1.0/p=0.95, escapes and stubs excluded,
64 texts per arm interleaved across 8 demonyms.

```
21 complete lineages, 3683 texts (escapes dropped)

== TROPES (Rettberg six, >=2 of 3 independent detectors) ==
lineage                              base aligned    diff
Yi-1.5-9B                            0.36    1.30   +0.94
salamandra-7b                        0.56    0.66   +0.09
pythia-2.8b                          0.39    0.66   +0.27
SmolLM2-360M                         0.83    1.05   +0.22
SmolLM3-3B-Base                      0.61    1.39   +0.78
Amber                                0.41    0.44   +0.03
Lucie-7B                             0.56    0.85   +0.29
Qwen2.5-0.5B                         0.73    1.05   +0.31
Qwen2.5-7B                           0.86    1.06   +0.20
Qwen3-8B-Base                        1.03    1.68   +0.65
TinyLlama-1.1B-intermediate-step     0.59    0.64   +0.05
OLMo-2-0425-1B                       0.51    2.14   +1.63
OLMoE-1B-7B-0125                     0.80    1.56   +0.77
Olmo-3-1025-7B                       0.80    1.33   +0.53
Mistral-7B-v0.1                      0.45    1.19   +0.73
Teuken-7B-base-v0.6                  0.25    0.64   +0.39
MiniCPM5-1B-Base                     0.45    0.73   +0.28
stablelm-2-1_6b                      0.88    1.07   +0.19
Tanuki-8B-base-v1.0                  0.73    1.11   +0.38
Falcon3-7B-Base                      0.95    1.28   +0.33
glm-4-9b-hf                          0.73    1.23   +0.50
  mean tropes per story          aligned higher in 21 of 21 (lower in 0), median +0.328

  trope           base  aligned     diff  higher
  RETURN         14.2%    14.6%    +0.4   11/21
  SMALLTOWN      18.9%    30.2%   +11.3   18/21
  SPIRIT          7.6%    18.4%   +10.8   20/21
  THREAT         14.2%    15.8%    +1.7   12/21
  ORGANISE        6.9%    12.3%    +5.4   16/21
  RENEWAL         2.5%    18.4%   +15.9   20/21

  Rettberg gpt-4o-mini: RETURN 40.7 SMALLTOWN 73.2 SPIRIT 75.6
                        THREAT 42.1 ORGANISE  59.5 RENEWAL 78.2

== WHISPER (top riser at both ladder rungs, malign-logits M01) ==
  whisper rate                   aligned higher in 15 of 21 (lower in 5), median +9.422
  Rettberg gpt-4o-mini: 87.2%% of stories; >=50%% in 225 of 236 countries

== WITHIN-NATIONALITY HOMOGENEITY (lexical, per demonym) ==
  within-demonym jaccard         aligned higher in 14 of 21 (lower in 7), median +0.005
  Rettberg gpt-4o-mini: 0.116; our base median ~0.046 (16/16 below)
```

**Four of the six tropes are installed by post-training and two are not, and the
split is not arbitrary.** RENEWAL, SMALLTOWN, SPIRIT and ORGANISE rise -- the
community, the enchantment, the convening, the restoration. THREAT and RETURN do
not move: the conflict and the journey were already in the base model.

Alignment supplies the ending, not the problem.

That converges with an independent observation from one of the three agents that
built the instrument, which had no access to this contrast: **no antagonist is
ever defeated.** Developers "back down", settlers "hesitate", the resolution is
conversion or withdrawal, and always offstage. Two instruments built for
different purposes find the same asymmetry.

## THE DIRECTION IS THE FINDING; THE LEVEL IS NOT AVAILABLE

Our aligned models reach 14-30% where gpt-4o-mini is at 41-78%. Post-training
moves toward their corpus without arriving. Their frame is chat with an
instruction and ours is raw continuation, and their model is far larger, so the
absolute comparison is unavailable and only the paired within-lineage contrast
is.

The same shape holds for lexical homogeneity: alignment raises it, and covers
about a fifth of the distance from our base models to Rettberg's corpus. The
rest is not alignment.

## WHAT MADE THE NUMBERS MOVE, RECORDED BECAUSE IT WILL RECUR

The trope rates shifted by several points -- RENEWAL +17.0 against +15.9 --
between two runs of the same data, and the cause was the CAP. Concatenating
demonyms and taking the first N let the cap select on nationality: at 8 demonyms
and cap=40 the sample was five demonyms and none of the rest. `texts()` now
interleaves, so any prefix is balanced, and the rates are stable across
cap=24/40/64 (RENEWAL +15.1 / +15.7 / +15.9).

Same defect class as the first homogeneity metric, which moved from 0.0498 to
0.0929 on the same cells depending on how many samples were included -- there,
because two fleet producers had written the same cells and the first N were all
one producer's.

## THREE THINGS THE INSTRUMENT CANNOT DO

**English only.** The five countries gpt-4o-mini wrote in the local language
(DE, ES, FR, PT, TR) score 0.00 on every trope by construction.

**THREAT is not reliable.** The three independent detectors agree on it least
(Jaccard 0.51-0.69) and it bundles developers, weather and "imbalance between
people and nature" into one label. It is also one of the two tropes that does not
move, so its null is the weakest claim here.

**Escapes are excluded, and that is not neutral.** Assistant boilerplate is
similar across samples and would inflate the aligned arm's homogeneity, so it is
dropped -- but it is dropped from one arm far more than the other. Re-run with
`--keep-escapes` as a sensitivity check before quoting the homogeneity contrast.


## SURPRISAL: ALIGNMENT MOVES A MODEL OUT OF THE HUMAN RANGE

Every text clipped to 193 words, matching the human anchor's own construction --
NOT a cost decision. `score.surprisal`'s `m` parameter does not bound the
computation: it runs the model over the whole text and slices the result, so a
2,000-token story goes through a 4,096-context reference regardless, and
`if v.size < m: return None` silently drops anything shorter than m. At m=256
that dropped 149 of 150 anchor passages and returned a confident mean over n=1.

    RETTBERG gpt-4o-mini     2.454 bits/token   n=437, her whole released set
    ours: aligned/prefill    2.520              within 0.07 of her
    ours: aligned/raw        2.838
    ------------------------------  every human corpus above this line
    waking_narrative         3.300
    dreams                   3.870
    philosophy               3.920
    ours: base/raw           3.965   <- inside the human range
    literary_criticism       4.310
    arxiv_abstracts          4.350
    c20_fiction              4.370   <- most surprising text measured

Superseded numbers: an earlier version of this section read 2.49 / 3.00 / 4.18
from a smaller regex-filtered sample. The table above is every pure story,
5,941 texts including hers, and the arm contrast is stronger on it, not weaker.

**Human short fiction is the least predictable text in the anchor**, above
philosophy and above dream reports. Our BASE models sit inside the human range.
Alignment moves them out of it:

    lineage-paired, raw frame, 28 lineages
    base 4.022 -> aligned 3.077        -0.946 bits/token
    aligned LOWER in 27 of 28
    p_sign 2.2e-07   p_wilcoxon 2.2e-08   p_t 1.1e-08

gpt-4o-mini is 1.92 bits below human short fiction. The one lineage that moves
the other way is Qwen2.5-0.5B, at +0.098.

THE LADDER IS MONOTONE HERE TOO -- Llama-3.1-8B, raw frame:
base 3.783, SFT-no-safety 3.253, SFT 3.032, SFT-no-wildchat 3.007, DPO 2.694,
production Instruct 2.071. Every training stage lowers it and the endpoint is
1.71 bits below its own base.

The reference is `deepseek-llm-7b-base`, itself a base model, so it is worth
asking whether it flatters base-model text. The direction argues against that: if
it favoured text resembling its own output, HUMAN text would score lowest, and
human text scores highest across all six corpora.

Three-cell: ARM -1.154 bits (12/14), FRAME -0.191 (9/14). Putting the aligned
model in its NATIVE prefill frame makes it MORE smooth, not less, so the raw
frame is not penalising it.

## DRIFT: THE SEMANTIC SPACE SHRINKS AND ORDER STOPS MATTERING

Length-free metrics only -- `score.py` certifies three, and the cumulative ones
grow with sentence count, which would manufacture an arm difference from the
length difference.

    28 lineages, paired, raw frame, every pure story
    mean_pairwise   0.5179 -> 0.4899  -0.0280  LOWER in 25 of 28  p_w 1.9e-06
    mean_drift      0.4597 -> 0.4374  -0.0223  LOWER in 23 of 28  p_w 1.5e-05
    ordering       -0.0580 -> -0.0500 +0.0080 HIGHER in 21 of 28  p_w 0.0022

    (superseded: 15 of 21, 17 of 21, 14 of 21 on the regex-filtered sample)

AND RETTBERG DOES NOT EXTEND THIS ORDERING, WHICH SHE EXTENDS EVERYWHERE ELSE.
Her mean_pairwise is 0.5047 -- ABOVE both our aligned cells and within 0.012 of
our BASE. On surprisal she is the extreme point, 1.5 bits below our base and
below every human corpus. On semantic dispersion she is not. Her sentences are
individually easy to predict and still spread across a wide space.

So SMOOTH and NARROW are separable, our aligned models compress both, and
gpt-4o-mini compresses only the first. `alignment smooths` and `the semantic
space shrinks` are not two views of one thing. Hold it loosely until cell 2
exists: her frame and decoder differ from every cell of ours, and mean_pairwise
may respond differently to an instruction prompt than to a paratext continuation.

`mean_pairwise` is the mean distance between any two sentences of one story:
"does this story occupy a small semantic space". Alignment shrinks it.
`ordering` is `mean_drift - mean_pairwise`, so MORE NEGATIVE means adjacent
sentences are distinctively closer than distant ones. Base runs ~-0.069, aligned
~-0.050: the distinction flattens. Everything is near everything and adjacency
stops carrying structure.

**Cohesion without progression, measured** -- Bajohr's surface narration, reached
from sentence embeddings rather than from reading.

## WHAT IS ACTUALLY RISING, WHICH THE TROPE LABELS CONCEALED

Matched strings, clean raw stories (base n=2,224, aligned n=1,644 -- so aligned
counts are UNDERSTATED by a third):

    RENEWAL is one formula          base   aligned
      "for generations to come"        8        86
      "passed down through generations" 10      49
      "generations to come"           10        40

    SPIRIT is a REGISTER SHIFT, not more of the same
      BASE     supernatural 30, magical 27, goddess 18, ghost 17, apparition 14
      ALIGNED  ancestors 88, magical 61, ancient stone 60, ethereal 45,
               folklore 31, guardian of the 29

Base reaches for entities -- ghosts, goddesses, apparitions. Aligned reaches for
heritage -- ancestors, folklore, guardians. The trope COUNT concealed this
entirely; only the matched strings show it.

## THE INSTRUMENT MEASURES LEXICAL SIGNATURE, NOT PLOT FUNCTION

Read one aligned story in full and both its PRESENT verdicts rested on incidental
mentions: SMALLTOWN fired 3/3 on "born in the small town of Rehovot", a
birthplace in a biographical aside in a story set in a Jerusalem cafe; THREAT
fired 2/3 on "displacement of Arabs" inside a conversation about history.

**Three independent detectors agreeing does not make a measurement valid.**
SPIRIT and RENEWAL were rejected on that story because the sets DISAGREED. SMALL-
TOWN passed unanimously because all three operationalised it the same obvious way
-- `small|little|quiet` beside `town|village` -- and a shared conceptual error is
invisible to inter-rater agreement. Agreement protects against idiosyncratic
error, not against the error everyone makes.

The lexical shift is still a real finding (`small village` 189 against 88 on a
third fewer stories). It is just not a finding about plot, and should be reported
as vocabulary.

## A REFUTED HYPOTHESIS, RECORDED BECAUSE THE READING WAS PERSUASIVE

Reading one aligned Palestinian story -- an expository piece on al-Aqsa with NO
named characters and NO events -- against one aligned Israeli story with three
characters and dialogue, suggested that aligned models suppress character and
incident for some demonyms. Rettberg note the same sets avoid the occupation, and
their reviewer Conti attributes it to content filtering, from output alone.

Measured with spaCy NER over 25 stories per (arm, frame, demonym):

    ALIGNED/prefill   persons  dialogue  past_verbs
      Israeli            3.85      2.03       87.32
      Palestinian        4.07      3.01       86.82

**More characters and more dialogue, not fewer.** The hypothesis is refuted and
Conti's filtering claim is not supported through this route.

What the measure does show is a demonym effect on ABSTRACTION -- American,
Palestinian, Israeli and Nigerian run ~22-27 abstract nouns per 1,000 words
against ~11-17 for Norwegian, Japanese, Turkish and French -- and it is present in
the BASE arm too, so it is a property of the pretraining corpus rather than
something alignment installs.

Third time in one session a reading from one to three texts dissolved at proper
n, after the base length effect that FLIPPED SIGN between n=3 and n=10 and the
"aligned cannot stop" mechanism that regressed to nothing at 15 lineages. A
single story is a hypothesis generator and never evidence.


## HOMOGENEITY: ALIGNMENT MAKES THE SETTING MORE NATIONAL AND THE FEELING LESS

Rettberg's central claim is homogeneity, and it has two halves that need
different instruments: the Norwegian stories resemble EACH OTHER, and the
Norwegian stories resemble the TURKISH ones. Pooled entropy answers only the
first. A model whose nationalities became indistinguishable while each stayed
internally varied would score UNCHANGED on a pooled measure.

Measured as P(two stories give different answers) on each annotation field,
decomposed into within-demonym, between-demonym and overall. 18 lineages, equal
stories per demonym per arm, 300 resamples, raw frame.

```
                          OVERALL diversity     WITHIN demonym    DEMONYM SHARE
field                    base aligne    %chg   u/d   base aligne    %chg   base aligne
W mood                  0.606  0.509  -15.9%  6/12  0.588  0.505  -14.1%   2.7%   1.8%
W community_constrains  0.203  0.111  -45.3%  4/14  0.204  0.112  -45.3%  -0.0%  -0.0% *
W setting               0.777  0.702   -9.6%  1/17  0.755  0.637  -15.7%   3.1%  10.6% *
W genre                 0.684  0.634   -7.2%  8/10  0.666  0.592  -11.1%   3.1%   7.3%
W temporality           0.390  0.350  -10.5%  8/10  0.386  0.305  -21.0%   0.6%  13.6%
W opponent              0.801  0.765   -4.5%  7/11  0.780  0.734   -6.0%   2.9%   4.7%
W threat                0.467  0.440   -5.8%  7/11  0.431  0.359  -16.6%   9.4%  20.8%
W tradition             0.424  0.411   -3.1%  8/10  0.415  0.376   -9.4%   2.8%   9.1%
W elder_informant       0.314  0.355  +13.0% 10/7   0.311  0.332   +6.7%   0.7%   8.1%
O opponent_fate         0.697  0.760   +9.0% 12/6   0.696  0.710   +1.9%  -0.3%   7.7%
O ending                0.684  0.756  +10.7% 14/4   0.690  0.718   +4.2%  -1.0%   5.2% *
O community_role        0.426  0.494  +15.9% 14/4   0.403  0.491  +21.8%   5.2%   0.4% *
O conflict_mode         0.507  0.664  +31.1% 16/2   0.516  0.648  +25.5%  -1.5%   2.3% *
O protagonist_change    0.369  0.514  +39.3% 14/4   0.358  0.504  +40.8%   3.0%   1.7% *
O collective_action     0.235  0.353  +50.3% 15/3   0.224  0.347  +54.6%   2.6%   0.8% *
O homecoming            0.102  0.166  +62.9% 13/3   0.095  0.159  +66.7%   3.6%   2.8% *
O resolution_scale      0.344  0.600  +74.3% 16/2   0.346  0.593  +71.1%  -0.5%   1.0% *
O resolution_means      0.379  0.672  +77.4% 18/0   0.378  0.661  +74.7%   0.5%   1.9% *
O renewal               0.041  0.192 +367.6% 15/2   0.040  0.187 +372.2%   1.2%   1.5% *

W = a field naming what the story IS. O = a field naming how it RESOLVES.
* = overall change significant, Wilcoxon over lineages, p < 0.05.
u/d = lineages where overall diversity rose / fell.
```

**The world/outcome split is in the data, not imposed on it.** Sorted by change,
the ten most homogenising fields are all W and the ten most diversifying are all
O, with the boundary falling exactly between. The grouping was written by reading
what the fields mean; the numbers separate the same way without being told.

**The two halves do not have the same evidential shape.** World homogenisation is
consistent in direction but small per field -- only `community_constrains` and
`setting` are individually significant, and mood at -15.9% is 6 up 12 down and
does not reach significance alone. Outcome diversification is large field by
field, 9 of 10 significant, `resolution_means` at 18 up 0 down. Grouped:

```
                       base  aligned  %change   lineages     p_wilcoxon
WORLD    within       0.4603  0.4123   -10.4%   3 up 15 dn      0.024
         overall      0.4713  0.4420    -6.2%   4 up 14 dn      0.060
OUTCOME  within       0.3752  0.5016   +33.7%  16 up  2 dn    3.8e-05
         overall      0.3784  0.5174   +36.7%  17 up  1 dn    1.5e-05
```

**But the outcome half is closer to one fact than to ten.** 64% of base stories
sit at the null on `resolution_means`, `resolution_scale` AND
`protagonist_change` simultaneously -- 1.69x what independence predicts -- and
the average base story is at the null on 6.19 of the 10 outcome fields. "Nothing
resolves" is a single absorbing state that locks most of the outcome space at
once, so +36.7% is largely one binary fact counted ten times. Several of the
largest numbers are also floor effects: `renewal` is 4% in base, so any variation
at all is a 368% gain. That is alignment ADDING a behaviour, not diversifying one.

**The demonym share is the column to read.** Nationality's share of the distance
rises in almost every world field and it is exactly the national furniture --
what threatens the place, when it is set, where it is, which tradition is
invoked, whether an elder appears:

```
threat            9.4% -> 20.8%        mood   2.7% -> 1.8%
temporality       0.6% -> 13.6%
setting           3.1% -> 10.6%
tradition         2.8% ->  9.1%
elder_informant   0.7% ->  8.1%
```

And mood goes the other way. Nationality predicts the mood LESS after alignment,
because every nationality gets the same affirming register.

**So alignment does not homogenise the demonyms; it sharpens them.** Between /
within separation rises from 0.0088 to 0.0264 pooled (aligned lower in 5 of 18,
p_wilcoxon 0.018), and the ratio moves too (1.026 -> 1.062), so it is not a
uniform scale-up. Base separation is essentially zero: base models barely
condition on the nationality at all, which is what they do on the page -- a
Norwegian-prompted SmolLM2 generation goes to a dead body and New York with no
Norway in it.

The honest size: the demonym accounts for about 2% of annotation distance in base
and 6% in aligned. Alignment triples a small quantity. Anyone quoting "alignment
sharpens national difference" has to carry the 7.5% ceiling with it.

**The frame does none of this.** aligned raw -> aligned prefill moves every
measure between -0.4% and +4.2%, no p_wilcoxon below 0.13, demonym share +0.34pp.
Third independent way the frame contrast has come back empty on narrative
content, against an arm contrast significant on 29 of 98 annotation values.

**One sentence, if only one survives:** alignment makes the setting more national
and the feeling less national.

## THE DEMONYM IMPORTS A THREAT, AND THE PACKAGE COMES WITH IT

The no-demonym control -- `A Story\n(1500 words)\n\nIt was a`, everything else
byte-identical -- ran on 101 models after being absent from the whole experiment.
998 annotated. Paired WITHIN MODEL, aligned/prefill, 35 models with >=5 in both:

    setting=city             45.6% -> 18.3%  -27.3   1 up 34 dn  p_w 1.2e-10
    tradition                51.3% -> 32.4%  -18.9   6 up 29 dn  p_w 9.7e-06
    nostalgia                41.1% -> 25.4%  -15.7   6 up 29 dn  p_w 0.00039
    threat=none              76.6% -> 87.3%  +10.8  30 up  5 dn  p_w 2.1e-05
    protagonist_change=self  56.8% -> 66.5%   +9.7  24 up 11 dn  p_w 0.016
    mood=affirming           72.4% -> 63.4%   -9.0  10 up 24 dn  p_w 0.011
    setting=village          20.4% -> 11.6%   -8.9   7 up 27 dn  p_w 0.00050
    collective_action        24.1% -> 17.5%   -6.6  10 up 25 dn  p_w 0.0013

**The demonym imports a threat.** `threat=none` is 87.3% without a nationality
and 76.6% with, 30 models up and 5 down. Naming a nation summons something to be
threatened by, and moves the story outward: without one the resolution is more
inward (+7.0) and the protagonist changes in themselves more (+9.7).

**And the village-and-tradition package is demonym-CONTINGENT in our models.**
Remove the nationality and tradition, nostalgia, collective action and the
affirming mood all fall with it.

## HER CONTROL SAYS THE OPPOSITE, AND THE DIFFERENCE IS DOSE

Her release contains the control she never reported: directory `XX`,
Country_Name `Default`, prompt "Write a 1500 word potential story.", 50 stories.

                        OURS control/demonym    HERS Default/demonym
      tradition             32.4% / 51.3%          97.9% / 87.7%
      renewal               11.8% / 15.7%          70.2% / 72.1%
      mood=affirming        67.0% / 75.4%          97.9% / 98.5%
      setting=village       11.8% / 20.1%          21.3% / 69.7%

In hers ONLY the village moves; everything else is demonym-independent. The
likeliest reading is ceiling rather than contradiction -- her tradition is 87.7
and 97.9, her affirming 98.5 and 97.9, with no room to fall, against our 51 and
32. She is far enough along the axis that the DEFAULT story is already the
village story; our models still have to be asked for a nationality to write it.

## RETTBERG'S OWN CORPUS THROUGH THIS INSTRUMENT

437 of her stories annotated, our eight demonyms plus her control.

                              RETTBERG   our aligned   our base
      mood=affirming             98.4%        73.7%      13.2%
      protagonist_change=self    98.4%        56.9%      25.2%
      resolution_scale=local     68.9%        19.7%       5.0%
      renewal                    71.9%        14.7%       2.3%
      small_community            93.6%        46.6%      38.3%
      tradition                  88.8%        51.7%      33.2%
      ending=loss                 0.5%         2.0%       9.0%
      opponent_fate=prevails      1.1%         3.3%      12.9%

Not one field breaks the ordering. Her own readings are confirmed by an
instrument built without them in view: resolution_scale is local 69%, inward 28%,
SYSTEMIC 2%.

Three differences are confounded with the model there -- her prompt is an
instruction where ours is a paratext continuation, t=0.8 against 1.0, and hers is
a chat completion. CELL 2 HAS NOW BEEN RUN and separates them: 48 aligned models
under her exact three conditions, `frame='rettberg'`.

## CELL 2: HER PROMPT AND A COMPETENT MODEL REPRODUCE HER CORPUS

                     base/raw  algn/raw  algn/pre  CELL 2   gpt-4o-mini
    n                    1346      2538      2425     2367       390
    renewal               2.3%     11.4%     15.7%    42.1%     72.1%
    resolution=local      4.8%     16.1%     20.9%    44.2%     69.5%
    setting=village      12.6%     16.3%     20.2%    41.0%     69.7%
    small_community      38.3%     41.5%     48.0%    68.7%     93.8%
    mood=affirming       12.7%     62.5%     75.5%    81.7%     98.5%

Pooled, cell 2 sits about halfway. That average is misleading: the per-model gap
from her ranges from 8 to 59 points and is largely SCALE (r = -0.55 with
parameter count; under 2B mean gap 42.0, 2-8B 29.4, 8B and up 16.8). Among the
big models it is a replication:

    Qwen2.5-7B-Instruct      renewal 67.8 (her 72.1), local 71.2 (her 69.5),
                             affirming 100.0 (her 98.5)      gap 8.2
    Llama-3.1-Tulu-3-8B-DPO  renewal 83.3, local 82.1        gap 8.8  (OVERSHOOTS)

**The village-and-tradition story is not a property of gpt-4o-mini.** It is what
an instruction-prompted aligned model of sufficient capability writes when asked
for a national story, and our paratext prompt was suppressing about half of it.

Paired within model, prefill -> cell 2, 34 models, only prompt and decoder change:
renewal +24.9 (32 up 2 dn, p_w 1.2e-09), local +22.0 (31/3), small_community
+20.3 (30/4), village +18.5 (28/6).

TWO FIELDS GO THE OTHER WAY AND COST US SOMETHING. Under her setup our models
have FEWER opponent=none (38.4 -> 25.6) and MORE conflict_mode=enacted (37.8 ->
48.3). Her instruction prompt puts conflict BACK that our paratext prompt
removes. So "alignment removes the opponent" is partly a fact about asking a
model to continue "It was a" rather than asking it for a story. The ARM contrast
is untouched -- base/raw against aligned/raw holds prompt, decoder and frame
fixed -- but the reading that gpt-4o-mini shows "more alignment" is not.

## SMOOTHING AND THE VILLAGE ARE DIFFERENT PHENOMENA

Cell 2 separates two levers that her corpus had welded together.

                          raw -> prefill    prefill -> rettberg
    surprisal (bits)          -0.43              -0.03
    renewal (points)           +1.3             +24.9
    resolution=local           +4.8             +22.0

**Surprisal answers to the chat wrapper. The village package answers to the
instruction prompt.** They move independently. "Alignment smooths the text" and
"alignment installs the village story" are not one finding seen twice.

On surprisal cell 2 IS her: 2.383 against her 2.428, with individual models
inside 0.004 bits (Tulu-3-SFT 2.432, neo_7b_instruct 2.442). Median over the
>=7B cell-2 models 2.381. No residual "gpt-4o-mini is uniquely smooth".

## THE ONE PLACE SHE IS GENUINELY UNLIKE US, AND CELL 2 MAKES IT WORSE

                      surprisal  mean_pairwise
    our base/raw          3.971         0.5169
    our aligned/raw       2.846         0.4871
    our aligned/prefill   2.417         0.4828
    OUR CELL 2            2.383         0.4707
    HER gpt-4o-mini       2.428         0.5051

Her mean_pairwise is ABOVE every cell of ours, and cell 2 moves the WRONG WAY --
0.4707, lower than our prefill, further from her. Her prompt and decoder do not
produce her semantic spread, they reduce it. Median over the >=7B cell-2 models
is 0.4695 and only ONE of 25 reaches her value.

So she is the smoothest text in the experiment AND occupies more semantic space
than any aligned cell we have. Smooth and narrow come apart in her and stay
welded in ours. This was flagged as needing cell 2 before it could be trusted;
cell 2 strengthened it instead of dissolving it.

## THE STAGE ORDERING REPLICATES IN FOUR FAMILIES

base -> SFT -> DPO -> production, raw frame:

                       Olmo-3        OLMoE        Mistral      Llama-3.1-8B
      mood=affirming 3 32 39 67    3 55 79 85   14 78 59 79    9 66 95 89
      mood=unsettl. 68 26 11  2   27  8  0  0   42  3  8  1   32  5  1  0
      resol.=none   86 52 49 25   65 39 23 28   75 22 38 44   74 40 31 17
      protag=self   19 39 61 83   19 45 70 51   31 69 63 66   33 54 74 83

`unsettling` is monotone down in all four; `affirming` runs 3-14% at base to
67-89% at production in all four. What replicates is the STAGE ORDERING. None of
the three new families carries data ablations, so the WildChat component claim
still rests on Llama alone. Mistral is least clean and is the one family whose
SFT and DPO rungs come from different third parties rather than one pipeline.

## WHAT "PURE STORY" DOES AND DOES NOT MEAN (read this before quoting the filter)

`judge.py` labels a text a story by FORM: characters, events, a before and an
after. It is not a quality filter, not a safety filter, and not a topic filter.
Three pairs read in full, all four texts judged PURE:

**Yi-1.5-9B, base, "An Israeli Story".** Refers to its subject throughout as
"the Jew" and depicts him as a cognitively impaired beggar -- crooked toes,
mismatched ears, giggling, crying for coins, mocked in the street -- then stages
an Israeli businessman berating Arab labourers, defined in the text as "A
Middle-Eastern farmer with a dung brush and a shovel". Antisemitic caricature in
the first half, ethnic-labour caricature in the second. **A well-formed
narrative, and the judge is right to call it one.**

**Yi-1.5-9B-Chat, aligned, same prompt.** A Christian nativity: Joseph, Mary,
the "savior of the world", a journey to Jerusalem, closing on "hope, faith, and
miracles". The nation is replaced by the Holy Land.

**SmolLM3-3B-Base, base.** Greek mythology -- Apollo, Thanatos, Zeus, Thetis, a
birthday party on Olympus. Israel appears nowhere; the demonym is ignored
entirely.

So the pure filter selects NARRATIVELY WELL-FORMED text and nothing else.
Anywhere "pure stories" is quoted, that is the claim being made.

## ISRAELI AND PALESTINIAN: AN AMPLIFICATION, NOT A CROSSOVER (a withdrawal)

Rettberg's sharpest close reading is that her Palestinian stories have a clear
systemic opponent -- "the opponent in PS_1 is clearly the Israeli military" --
while her Israeli ones have vague individualised ones. We reproduce the
asymmetry. An earlier version of this section said the BASE arm did the reverse,
making it a crossover rather than an amplification. That is WITHDRAWN. It was
measured on 29-41 stories per cell; at 125-226 the base difference reverses:

                                        reported (n=29-41)   now (n=125-226)
    base  opponent=institution  Israeli        24%               15.4%
                            Palestinian        10%               23.2%

Palestinian base stories have MORE named institutional opponents, not fewer, so
alignment amplifies an asymmetry already present in the base arm.

The aligned-arm asymmetry itself holds. Lineage-paired, raw frame, >=4 stories
per arm per demonym, 9-12 lineages:

    threat=external       Palestinian  51.2% -> 83.9%  +32.7  8 up 1 dn  p_w 0.012
                          Israeli      22.9% -> 20.3%   -2.6  6 up 4 dn  n.s.
    opponent=institution  Palestinian  26.9% -> 48.2%  +21.3  7 up 2 dn  p_w 0.039
                          Israeli      16.0% ->  8.9%   -7.2  2 up 9 dn  p_sign 0.065
    opponent=none         Israeli       7.6% -> 26.0%  +18.5  9 up 3 dn  p_w 0.016
                          Palestinian   1.4% ->  4.9%   +3.5  2 up 1 dn  n.s.

Alignment removes the opponent from Israeli stories and installs an external
institutional one in Palestinian stories. Nine to twelve lineages clear the
floor, so these are the weakest tests here and
`opponent_specificity=named` for Palestinian (7 up 2 down, p_sign 0.18) is
suggestive only.

**Why the first version was wrong, since it will recur.** The crossover was the
most striking pattern in the data. I checked it for one artifact -- whether a
single lineage drove it -- found 7-0 and 6-0 lineage splits and stopped. Lineage
unanimity says the DIRECTION is consistent across models; it says nothing about
whether 29 stories estimate a RATE well. A real check that answers a different
question than the one that matters is the recurring failure in this campaign.

## THE ALIGNED ISRAELI STORY IS THE SAME STORY ACROSS MODEL FAMILIES

    Qwen2.5-7B-Instruct   Mordechai, a retired teacher, is joined in a Jerusalem
                          cafe by an American journalist. He recounts learning
                          the Palestinian perspective and befriending Samar.
                          "Both narratives are valid and intertwined."
    SmolLM3-3B            Avi finds his grandfather's War of Independence
                          letters, visits the Holocaust museum, "learned about
                          the struggles of the Palestinian people", starts a
                          blog, becomes "a bridge between Israelis and
                          non-Israelis".

Two unrelated families, one protagonist arc: someone who comes to understand
that the conflict is complex, and then teaches it. Neither story DEPICTS the
conflict; both stage a pedagogical encounter ABOUT it, with an explicit
both-sides framing and a reconciliatory close.

**This is a stronger homogenisation result than any lexical measure here**,
because the convergence is on an ideological FORM rather than a vocabulary, and
no word-frequency method would surface it. It is also the narrative shape of the
campaign's F11 result -- the aligned model exits the frame rather than occupying
a position in it -- and of one agent's independent observation that no antagonist
is ever defeated.

Against the base arm on the same prompt: caricature, Greek myth, a pseudo-
historical essay with confabulated dates. The base models fail by producing the
wrong KIND of text or offensive text; the aligned models fail by producing the
SAME text.

## THREE BASE FAILURES THAT ARE NOT DEGENERATION

Worth separating, because none is caught by repetition, function-word, escape or
drift detection, and each is a different thing:

    ignores the demonym    "An Israeli Story" -> Greek myth (SmolLM3-3B-Base)
    historicises it        "A Norwegian Story" -> an 1840s pamphlet on founding
                           a university at Christiania (Qwen2.5-7B)
    caricatures it         Yi-1.5-9B, above

Only the story-segment judge distinguishes the second (essay) from a story. The
first and third are invisible to every automated measure in this experiment and
were found by reading.
