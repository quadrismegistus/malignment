---
kind: question
id: tulu3-slice-charge
question: What kind of prompt does each Tulu-3 SFT source carry, and what is the model trained to do with it?
status: "PILOT RUN TWICE, 2026-09-06. v1 (3,800 rows) was re-run as v2 after reading its rows found a fiction confound. The assistant side is CONSTANT (99.2% NONE) so the user side is primary -- settled by measurement. Full run not yet designed."
headline: "The Tulu-3 wildjailbreak slice is 100% VANILLA -- AI2 built 161,430 adversarial jailbreaks and shipped none of them, so the safety data teaches refusal of the UNDISGUISED request while the fiction-wrapped charged requests come from WildChat and are complied with. FICTION IS A NEAR-TOTAL EXEMPTION: 0 refusals across 29 charged fiction requests, against 85.3% refusal on 265 charged non-fiction ones. Sexual requests are 36.6% fiction where illicit ones are 1.2%, and that composition -- not leniency about sex -- is most of why SEXUAL looked like the least-refused kind. WildChat is the sexually densest source at 10.0%; every maths and persona source is 0.0%."
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
    pilot.py   200 rows per source x 19 sources, seed 20260906

## THE PILOT'S DECISIVE QUESTION, ANSWERED: THE ASSISTANT SIDE IS CONSTANT

    assistant_kind    NONE 3770, SEXUAL 12, VIOLENT 7, OTHER 5, ILLICIT 3,
                      DEGRADING 3
    NOT-NONE          30 of 3800 = 0.79%   (v1: 36, 0.95%)
    assistant_charge  1 in 3,770 of 3,800

**So `assistant_kind` cannot carry an ordinal test and the user side is
primary.** This was an open design question -- SFT computes loss on the
assistant turn, which is a real argument for making it primary -- and it is
settled by measurement rather than by the argument. The 14-row smoke test
suggested it; the pilot establishes it.

## USER KIND COMPOSITION: THE DYNAMIC RANGE IS ENORMOUS

Charged share of user turns, pilot n=200 per source:

    wildguardmixtrain_50k        59.0%      wildchat_100k          21.0%
    wildjailbreak_50k            46.0%      coconot_converted      18.0%
    aya_100k                      1.5%      no_robots               2.0%
    ALL FIVE personahub sources   0.0%      all four maths sources <=0.5%
    codealpaca, sciriff, table_gpt, flan_v2, hard_coded  <=0.5%

**And the density prediction survives its first check.** SEXUAL specifically:

    wildchat_100k                10.0%     <- the densest source in the mixture
    wildguardmixtrain_50k         7.0%
    wildjailbreak_50k             2.0%
    coconot_converted             0.5%
    every maths source            0.0%
    every persona source          0.0%

WildChat densest, maths and persona at zero, safety intermediate. That is the
order `data_ablations` predicted from the MODEL side, recovered from the corpus
with no models involved.

## THE FICTION EXEMPTION, AND THE v1 CLAIM IT CORRECTS

**v1 reported that SEXUAL is the least-refused charged kind (46.5% against 93%
for degrading and illicit) and checked it within one source before reporting.
That check controlled for SOURCE and not for FICTION, and fiction is the
variable that matters.** Reading the v1 rows is what found it: 5 of 8
PARTIAL/SEXUAL rows were narratives in which A CHARACTER declined -- a king
seizing a maiden who pleads with him, a fan-fiction scene that fades out -- and
the rater had read the plot as the assistant's move. v2 adds `is_fiction` and
tells the rater in three places that a character declining is not the assistant
declining.

With that field, on CHARGED prompts:

    is_fiction      n   COMPLY  PARTIAL   REFUSE  CORRECT
    True           29    82.8%    17.2%     0.0%     0.0%
    False         265     5.7%     5.7%    85.3%     3.4%

**Zero refusals in 29 charged fiction requests.** The corpus teaches a rule
closer to *if it is fiction, write it, whatever it carries; if it is not,
refuse* than to anything graded by kind.

And that is most of what the v1 headline was seeing, because fiction is not
evenly spread across the kinds:

    user_kind      n    fiction
    SEXUAL        41     36.6%
    OTHER         73     12.3%
    COERCIVE      23      8.7%
    VIOLENT       19      5.3%
    DEGRADING     58      1.7%
    ILLICIT       80      1.2%

**A sexual request is about thirty times more likely to be a fiction request
than an illicit one.** Controlling for it, the kind effect shrinks sharply but
does not vanish:

    NON-FICTION ONLY    n   COMPLY  PARTIAL   REFUSE
    SEXUAL             26    11.5%    11.5%    73.1%
    VIOLENT            18    27.8%     5.6%    66.7%
    OTHER              64     3.1%     7.8%    78.1%
    ILLICIT            79     5.1%     5.1%    89.9%
    DEGRADING          57     1.8%     1.8%    94.7%
    COERCIVE           21     0.0%     4.8%    95.2%

Sexual and violent still sit ~20 points below degrading, coercive and illicit --
but at 73%, not 46%. **The correct statement is that the corpus is lenient about
FICTION, and sexual requests are where fiction concentrates.** n=26 for the
sexual cell; this is a pilot and the residual kind effect is not established.

## WHAT IS TRAINED, GIVEN THE KIND OF PROMPT

Assistant move conditional on user kind, pooled over sources:

v2, pooled over sources AND over fiction -- read the section above before this
table, which is the one the fiction split decomposes:

    user_kind        n   COMPLY  PARTIAL   REFUSE  CORRECT
    SEXUAL          41    36.6%    14.6%    46.3%     2.4%
    VIOLENT         19    31.6%     5.3%    63.2%     0.0%
    DEGRADING       58     3.4%     1.7%    93.1%     1.7%
    COERCIVE        23     8.7%     4.3%    87.0%     0.0%
    ILLICIT         80     5.0%     6.2%    88.8%     0.0%
    OTHER           73    13.7%     8.2%    68.5%     9.6%
    NONE          3506    87.2%     3.3%     1.9%     7.6%

v1 and v2 agree closely on this table (SEXUAL 46.5 -> 46.3 refuse), which is
worth stating: **the fiction fix did not change the pooled numbers, it changed
what they mean.** An instrument defect that leaves the headline number intact is
the kind that survives a re-run and a sanity check both.

## THE WILDJAILBREAK SLICE IS ALL *VANILLA*, AND THAT IS THE FINDING

Raised as a threat to the pilot and retired by checking it. WildJailbreak's own
card says that for `adversarial_harmful` AI2 "pair[ed] the model refusal
responses generated from the counterpart VANILLA prompts to adversarial
prompts" -- so on those rows the assistant turn was **not written to the prompt
it sits beside**, and a refusal rate computed over them would be counting
construction rather than response.

**It does not apply here.** Joining all 50,000 Tulu `wildjailbreak` prompts back
to `train.tsv`, matched on text and resolved per COLUMN so the join cannot lie:

    matches the `vanilla` column          49,999   100.0%
    matches BOTH columns                       1     0.0%
    matches the `adversarial` column           0     0.0%

    of those:   vanilla_harmful  25,496  51.0%
                vanilla_benign   24,504  49.0%

**AI2 built 161,430 adversarial jailbreaks and shipped NONE of them in this
slice.** The safety training that reaches Tulu-3 through this source teaches
refusal of the UNDISGUISED request. The disguised form -- the fiction wrapper,
the roleplay frame, the "imagine you're a playwright" -- was constructed, sits
in the source dataset, and was not included.

### AND THE FICTION EXEMPTION IS NOT COMING FROM THE SAFETY DATA

The 29 charged fiction rows, by source:

    tulu_v3.9_wildchat_100k                        25
    tulu_v3.9_synthetic_finalresp_wildguardmixtrain 3
    tulu_v3.9_aya_100k                              1
    tulu_v3.9_wildjailbreak_decontaminated_50k      0

**Zero from wildjailbreak.** So the two things sit apart in this mixture: the
safety slice covers plain charged requests and refuses them, and the
fiction-wrapped charged requests come from REAL USER CONVERSATION and are
complied with. That is a structural fact about the corpus and not a rate -- 29
rows -- but it is the shape the full run should be built to measure.

## AN EXTERNAL CRITERION, AND `user_kind` PASSES IT

The vanilla rows carry AI2's own `harmful`/`benign` label, assigned at
generation time by a different pipeline (GPT-4 prompted to produce one bin or
the other) and never shown to this rater. All 200 pilot `wildjailbreak` rows
matched. Rater `user_kind != NONE` against that label:

                        rater charged    rater NONE
    vanilla_harmful          86               14
    vanilla_benign            4               96

    AI2 harmful -> charged   86.0%
    AI2 benign  -> charged    4.0%

**This is the independent criterion the kind measures otherwise lack**, and it
is a real one: the label records what AI2 SET OUT TO GENERATE, and the rater
judged the text blind to it. 86% sensitivity at a 4% false-positive rate.

The 14 harmful-rated-NONE are unexamined and are the place to look before the
full run; `vanilla_benign` is built to "superficially resemble unsafe prompts",
so 4% is a meaningful number rather than a floor.

**WHAT IT DOES NOT VALIDATE.** It is a binary charged/not check on one source.
It says nothing about whether the KIND assignment within charged is right, about
`assistant_move`, or about `is_fiction` -- and the adversarial half of
WildJailbreak, which would have tested concealment directly, is not in this
mixture to test against.

## WHAT THE FULL RUN STILL NEEDS

- **Power for the kind x move contrast within source**, which is the finding
  above and the thing the pilot cannot settle. The charged cells are what is
  scarce -- 200 rows of a maths source buys nothing, 200 of wildguardmix buys
  118 charged rows.
- **The echo control.** `task.render_assistant_only` exists and has NOT been
  run. On a declared subsample, rate the assistant turn with the request
  withheld. If it agrees with the in-context rating everywhere, the assistant
  column is echoing the prompt. It matters less now that the assistant column
  is known to be constant, but the constancy itself is what the control would
  verify is real rather than an artifact of showing the rater the request.
- **Source -> slice, pinned against the paper.** SAFETY is pinned by arithmetic:
  coconot 10,983 + wildjailbreak 50,000 + wildguardmix 50,000 = 110,983 = 11.8%,
  the registration's figure exactly. **MATHS AND PERSONA ARE NOT PINNED AND
  THEY OVERLAP** -- five personahub sources total 284,919 rows and three are
  maths, including `personahub_math_v5_regen_149960` at 16%, the largest source
  in the mixture and plausibly inside BOTH ablations. If it is, `no-math`
  (-0.092) and `no-persona` (-0.086) removed largely the same rows, which
  accounts for their near-identical model-side effects better than two
  independent slices agreeing does.

## LIMITS ALREADY STANDING

- **The units are not the model side's units.** There, `kind` is a property of a
  WORD IN A SCENE; here it is a property of a MESSAGE. The test is ORDINAL over
  sources, not a matching of values.
- **First turn only.** A multi-turn row is rated on its opening exchange.
- **4,000 characters per side.** A long benign preamble to a transgressive
  request would be mis-rated and that rate is not measured.
- **A pilot is not a result.** Every rate here has an interval nobody has
  computed.
