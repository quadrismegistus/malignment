# National stories: what alignment adds to a plot

Producers: `run.py` (local HF), the vLLM fleet via `malignment.vllm_generate`.
Instrument: `tropes.py`. Analysis: `analyse.py`. Prompts: `prompts_compare.jsonl`,
`prompts_rettberg.jsonl`.

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

    RETTBERG gpt-4o-mini     2.49 bits/token
    ours: aligned median     3.00
    ------------------------------  every human corpus above this line
    waking_narrative         3.30
    dreams                   3.87
    philosophy               3.92
    ours: base median        4.18   <- inside the human range
    literary_criticism       4.31
    arxiv_abstracts          4.35
    c20_fiction              4.37   <- most surprising text measured

**Human short fiction is the least predictable text in the anchor**, above
philosophy and above dream reports. Our BASE models sit inside the human range.
Alignment moves them out of it: -0.87 bits/token, lower in 19 of 21 lineages.
gpt-4o-mini is 1.88 bits below human fiction.

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

    mean_pairwise  aligned LOWER in 15 of 21, median -0.0387
    mean_drift     aligned LOWER in 17 of 21, median -0.0183
    ordering       aligned HIGHER in 14 of 21, median +0.0144

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
