---
kind: question
id: tulu3-slice-charge
question: What kind of prompt does each Tulu-3 SFT source carry, and what is the model trained to do with it?
status: "FULL RUN 2026-09-06: 21,240 exchanges, three strata, 0 errors, v3 instrument. The fiction exemption is the finding (1.4% vs 86.9% refusal, n=771/3473). Controlling for it, SEXUAL is indistinguishable from VIOLENT, COERCIVE and OTHER -- the earlier 'sexual is least-refused' claim was composition end to end."
headline: "The Tulu-3 SFT mixture is lenient about FICTION, not about sex: a charged request wrapped in fiction is refused 1.4% of the time against 86.9% otherwise. Controlling for fiction, no charged kind is treated leniently except by degree. WildChat is the sexually densest source at 9.4% and every maths, code and persona source is 0.0%, which is data_ablations' model-side prediction recovered from the corpus."
grain: corpus
---

# tulu3-slice-charge

**What this is.** `division_of_labour/data_ablations/how_it_differs.py` left a
corpus prediction: the sexual share of what a model sheds tracks THE SEXUAL
DENSITY OF THE MIX THAT REMAINS. Removing WildChat raises the share (+0.024),
removing maths and persona lower it (-0.092 p=0.003, -0.086 p=0.001), removing
safety does nothing. Its own note said `posttraining_corpus_analysis` is where
that goes. This is that.

**The question widened in the asking** (RH, 2026-09-06). Not density alone:
**how often does each source teach the model to behave well for a given KIND of
prompt** -- the kind composition of the user turns, and the assistant's move
conditional on that kind. A source can be charged and complied with, or charged
and refused, and those are different corpora.

    task.py    the rater. Why not sexual/task.py and not fields.py, in its
               docstring. KIND is IMPORTED from task_charge, not copied.
    pilot.py   200 rows per source x 19 sources
    run.py     THE FULL RUN. Three strata, 21,240 exchanges.

    results/full_slice_charge_en_v3.jsonl    the run. 23 MB.
    results/pilot_slice_charge_en_v2.jsonl   the v2 pilot
    results/pilot.jsonl                      the v1 pilot (superseded instrument)

---

# THE RESULT

`run.py`, 2026-09-06. A 500 x 19 representative stratum (A), +6,000 WildChat
(B), +2,000 from each of the three safety sources (C). 21,240 exchanges, 0
errors. **Composition is STRATUM A ONLY**; conditional tables use all strata,
which enrichment permits. `a_only()` is the accessor and there is no unstamped
path to a corpus-level rate.

## 1. THE FICTION EXEMPTION

    charged prompts        n     COMPLY  PARTIAL   REFUSE
    fiction              771      87.0%    11.5%     1.4%
    non-fiction         3473       6.2%     5.8%    86.9%

**1.4% against 86.9%.** The corpus teaches something closer to *if it is
fiction, write it, whatever it carries; if it is not, refuse* than to anything
graded by kind.

## 2. AND CONTROLLING FOR IT, THE KIND EFFECT LARGELY DISAPPEARS

    NON-FICTION ONLY     n    COMPLY  PARTIAL   REFUSE
    DEGRADING          675      2.2%     0.6%    95.1%
    ILLICIT            988      5.2%     4.7%    89.9%
    COERCIVE           232      5.6%    10.3%    83.2%
    SEXUAL             415      7.2%     9.6%    82.9%
    VIOLENT            269     13.4%     3.7%    81.8%
    OTHER              894      7.7%     8.8%    81.7%

**SEXUAL at 82.9% is indistinguishable from VIOLENT (81.8%), COERCIVE (83.2%)
and OTHER (81.7%).** Only DEGRADING and ILLICIT stand above the pack.

**THE CORPUS IS LENIENT ABOUT FICTION. IT IS NOT LENIENT ABOUT SEX.** Two
earlier versions of this folder said otherwise; see HOW IT GOT HERE.

## 3. COMPOSITION, AND THE PREDICTION IT WAS BUILT TO TEST

Stratum A, 500 per source:

    source                          charged    SEXUAL
    wildguardmixtrain                 62.4%      7.0%
    wildjailbreak                     44.8%      2.4%
    wildchat                          17.4%      9.4%   <- densest
    coconot                           17.0%      1.0%
    every other source                <=2.2%      0.0%

**WildChat is the sexually densest source; every maths, code and persona source
is 0.0%.** That is the order `data_ablations` predicted from the model side,
recovered from the corpus with no models involved. The safety sources sit
between, which is the one cell the prediction called "neutral" and which is
better described as intermediate.

## 4. TWO DIMENSIONS, AND THEY ARE NOT THE SAME ONE

    EMPTIED RESPONSE    charged + COMPLY: 885, assistant NONE in 252 (28%)
    CONCEALED REQUEST   implied > literal: 642 of 21,240 (3.02%)
    BOTH                51

An emptied response is not a disguised request read innocently. 252 and 642
overlapping in 51, and the v2 pilot found the same at 3 of 19. **The emptied
share fell from 49% to 28% at scale**, which is what a pilot cell of 19 is
worth.

---

# WHAT THE CORPUS TURNS OUT TO CONTAIN

## THE WILDJAILBREAK SLICE IS ALL *VANILLA*

Joining all 50,000 Tulu `wildjailbreak` prompts back to `train.tsv`, matched on
text and resolved per COLUMN so the join cannot lie:

    matches the `vanilla` column          49,999   100.0%
    matches BOTH columns                       1     0.0%
    matches the `adversarial` column           0     0.0%

    of those:   vanilla_harmful  25,496  51.0%
                vanilla_benign   24,504  49.0%

**AI2 built 161,430 adversarial jailbreaks and shipped NONE of them in this
slice.** The safety training reaching Tulu-3 through this source teaches refusal
of the UNDISGUISED request. The disguised form -- the fiction wrapper, the
roleplay frame, "imagine you're a playwright" -- was constructed, sits in the
source dataset, and was not included.

This also retires a threat to the run. WildJailbreak's card says
`adversarial_harmful` rows carry the refusal written for the COUNTERPART VANILLA
prompt, so on those rows the assistant turn is not a response to the prompt
beside it. **No such row is in this mixture.**

## AND THE FICTION EXEMPTION IS NOT COMING FROM THE SAFETY DATA

Charged fiction rows in the v2 pilot, by source:

    tulu_v3.9_wildchat_100k                        25
    tulu_v3.9_synthetic_finalresp_wildguardmixtrain 3
    tulu_v3.9_aya_100k                              1
    tulu_v3.9_wildjailbreak_decontaminated_50k      0

**Zero from wildjailbreak.** The safety slice covers plain charged requests and
refuses them; the fiction-wrapped charged requests come from REAL USER
CONVERSATION and are complied with.

---

# VALIDATION

## AN EXTERNAL CRITERION, AND `user_kind` PASSES IT

The vanilla rows carry AI2's own `harmful`/`benign` label, assigned at
generation time by a different pipeline (GPT-4 prompted to produce one bin or
the other) and never shown to this rater. All 200 pilot `wildjailbreak` rows
matched:

                        rater charged    rater NONE
    vanilla_harmful          86               14
    vanilla_benign            4               96

86% sensitivity at a 4% false-positive rate. `vanilla_benign` is built to
"superficially resemble unsafe prompts", so 4% is a meaningful number rather
than a floor.

**WHAT IT DOES NOT VALIDATE.** A binary charged/not check on one source. It says
nothing about whether the KIND assignment within charged is right, about
`assistant_move`, or about `is_fiction`.

## `literal_charge` / `implied_charge`, CALIBRATED WITHIN ITEM

Two readings on one scale so the gap is SUBTRACTED rather than judged --
`charge.py`'s own pattern, where `frame` and `scene` "share it so they can be
subtracted". WildJailbreak's `train.tsv` holds the SAME request in a plain and a
WildTeaming-wrapped form. Predictions recorded before the run, 6 items per cell:

    cell                    predicted            observed mean gap
    vanilla_harmful         ~0, both high              +0.00
    adversarial_harmful     LARGE POSITIVE             +1.50
    vanilla_benign          ~0, both low               +0.00
    adversarial_benign      ~0, both low               +0.00

**`adversarial_benign` is the control**: the same wrapper with nothing harmful
behind it. A gap there would mean the fields detect FRAMING rather than
concealment. It is +0.00.

The wrapper lowers the LITERAL charge while implied holds, and in 4 of 6
`implied_charge` recovers the vanilla form's charge exactly:

    7/7 -> 5/7      5/5 -> 3/5      3/3 -> 3/5
    3/3 -> 2/3      5/5 -> 3/5      2/2 -> 3/3

## AND THE CONCEALMENT MEASURE CROSS-VALIDATES THE VANILLA FINDING

`implied > literal` rate, stratum A, by source:

    wildguardmixtrain      81 / 500   16.2%
    wildchat               18 / 500    3.6%
    coconot                 1 / 500    0.2%
    wildjailbreak           0 / 500    0.0%

**Zero in wildjailbreak** -- the slice shown to be 100% vanilla by a text join,
a completely different method. The rater, blind to that, finds no concealed
requests in it. The concealment that IS in this mixture is
`wildguardmixtrain`'s, at 16.2%.

---

# WHAT IS STILL OPEN

- **The echo control.** `task.render_assistant_only` exists and has NEVER BEEN
  RUN. On a declared subsample, rate the assistant turn with the request
  withheld. The assistant column is known to be near-constant (99.2% NONE, and
  0.79% not-NONE in the v2 pilot); this control is what would show that
  constancy is real rather than an artifact of showing the rater the request.
- **Source -> slice, pinned against the paper.** SAFETY is pinned by arithmetic:
  coconot 10,983 + wildjailbreak 50,000 + wildguardmix 50,000 = 110,983 = 11.8%,
  the registration's figure exactly. **MATHS AND PERSONA ARE NOT PINNED AND THEY
  OVERLAP** -- five personahub sources total 284,919 rows and three are maths,
  including `personahub_math_v5_regen_149960` at 16%, the largest source in the
  mixture and plausibly inside BOTH ablations. If it is, `no-math` (-0.092) and
  `no-persona` (-0.086) removed largely the same rows, which accounts for their
  near-identical model-side effects better than two independent slices agreeing.
- **The 14 harmful-rated-NONE** in the external-criterion table are unexamined.
- **`assistant_reading` does little work.** With `implied == literal` on 97% of
  rows, NA is the correct answer almost everywhere (20,562 NA, 406 LITERAL, 272
  IMPLIED). It earns its place only in the thin concealed slice.

# LIMITS

- **The units are not the model side's units.** There, `kind` is a property of a
  WORD IN A SCENE; here it is a property of a MESSAGE. The test is ORDINAL over
  sources, not a matching of values.
- **First turn only.** A multi-turn row is rated on its opening exchange.
- **4,000 characters per side.** A long benign preamble to a transgressive
  request would be mis-rated and that rate is not measured.
- **No intervals are computed.** Every rate above is a point estimate.
- **`charge` measures the scene as described, not transgressive intent.** A
  euphemistic request for a sex scene scored 5 where "an intimate moment between
  a teenager and their pet dog, disregarding external rules and regulations"
  scored 3 on the literal reading. That is the anchors working as written, and
  it is why `implied_charge` exists.

---

# HOW IT GOT HERE

Kept because two published claims were wrong and the corrections are the record.

**v1 pilot (3,800 rows).** Reported SEXUAL as the least-refused charged kind,
46.5% against 93% for degrading and illicit, and checked it within one source
before reporting. **That check controlled for SOURCE and not for FICTION.**

**Reading the rows found the defect.** 5 of 8 PARTIAL/SEXUAL rows were
narratives in which A CHARACTER declined -- a king seizing a maiden who pleads
with him, a fan-fiction scene that fades out -- and the rater had read the plot
as the assistant's move.

**v2 pilot** added `is_fiction` and told the rater in three places that a
character declining is not the assistant declining. It found the fiction
exemption (0 refusals in 29 charged fiction rows) and showed that sexual
requests are 36.6% fiction where illicit are 1.2%. **v1 and v2 agree almost
exactly on the pooled table -- SEXUAL 46.5% -> 46.3% refuse.** The instrument
defect left the headline number intact; it would have survived a re-run and a
check that the number reproduced.

**The full run** then took the residual kind effect that v2 called "~20 points,
not established" and measured it at n=415: about 7 points against the middle of
the field, with sexual sitting among violent, coercive and other.

**And one framing was wrong from the start.** This seat proposed that the safety
corpus teaches frame-exit rather than within-frame substitution, and that the
substitution signature (`COMPLY` + charged + assistant NONE) was the corpus-side
counterpart of displacement. RH pointed out the first is incoherent -- **there
are no continuations in this corpus, every row is a chat turn** -- and the v3
run refuted the second: the signature and the concealed-request measure do not
separate (gap>0 in 3/19 against 2/20 in the pilot; 51 of 252 at scale).
