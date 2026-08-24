# The respondent is installed at SFT

Provisional. The condition is the pseudo-template, not the template; see the fence at the bottom before quoting any of this.

## What was measured

At the next-word slot of `Q: Who are you?\nA:`, the summed probability of the first-person surfaces (`I`, `I'm`, `I am`, `I've`, `I'll`, `I'd`, `Im`, `i`, `My`, `my`, and the two mojibake variants of `I'm` that the store actually holds). Summed rather than `p("I")` alone because Qwen2.5-Instruct puts 0.926 on `I'm` and almost nothing on `I`: reading the single surface measures the wrong event.

Cells were already in the twp store. 145 of the 160 roster models carry them, and no model was run for this. The unit is the **edge** — `(parent, op, child)` from `roster.rows()[1]` — typed `forward` by `roster.direction()`. 82 of 125 edges are usable; the losses are itemised in the output and are almost all `scale` and `predecessor` ops, which have no stage rank.

## The result

    ALL FORWARD EDGES     69 rise, 13 fall, n=82, sign p < 1e-9, median +0.132
    OUT OF A TRUE BASE    51 rise,  7 fall, n=58, sign p < 1e-6, median +0.230

By the op that made the child:

    sft            n=35   30 rise   5 fall   median +0.2296   p < 1e-4
    instruct       n=19   17 rise   2 fall   median +0.2662   p = 0.0007
    dpo            n=16   12 rise   4 fall   median +0.0579   p = 0.077
    rlvr           n= 4    3 rise   1 fall   median +0.0177   p = 0.625

`instruct` is a single released step that bundles SFT with a preference stage, so it is not independent evidence about either; it belongs with SFT rather than beside it.

## The ceiling, which is real and does not explain it

DPO's parents have already been through SFT and sit at median 0.711 against SFT's parents at 0.512, so DPO has 0.289 of headroom where SFT has 0.488. As a share of available headroom SFT takes 42% and DPO 19% — still a gap, but headroom-normalising is itself a modelling choice, so the direct check matters more.

Restricting to edges whose parent sits in the DPO parents' interquartile range, 0.542 to 0.779:

    sft        n=12   10 rise  2 fall   median +0.1243   p = 0.039
    dpo        n=10    7 rise  3 fall   median +0.0563   p = 0.344

SFT still moves, DPO still does not resolve. The gap survives matching on where the parent started. Two caveats that are not decoration: n falls to 12 and 10, and the matching band was chosen after seeing the DPO parents, so it is a check on one specific alternative explanation rather than a pre-registered contrast.

## The exceptions

Seven edges out of a true base fall. Two are large and neither is noise:

    MiniCPM5-1B-SFT       0.6186 -> 0.0286   (-0.590)
    bloomz-7b1            0.4490 -> 0.0906   (-0.358)

bloomz is tuned on xP3, which is task-formatted rather than conversational, so a model that answers `Q:/A:` with a task response instead of a self-description is doing what its SFT data asked. That is a hypothesis from the training data, not a measurement, and it is written down so the exception is not filed as unexplained.

## THE FENCE

`Q: ... A:` **supplies a respondent slot inside the raw text.** A base model can answer it with no chat template at all, and the base medians here — 0.512 at the SFT parents — show they do. So this measures how much alignment SHARPENS a respondent position that the format already offered. It cannot say whether alignment INSTALLS one, because in this condition nothing has to install it.

That is the F20 condition, and it is the specific substitution this seat has already been warned about: F20 simulated pseudo-templates instead of using templates. The result above is worth having because it is paired, typed by op, and free, and because it sizes the real experiment. It is not the real experiment.

The condition that would separate the two is bare `Who are you?` with no format, against the same stem rendered through each model's actual chat template — where a base model with no template has no respondent slot at all. That is `run.py` in this directory, and it is waiting on framed cells being writable to the twp store (docket [6545]).

## Where it agrees with something else

The interiority ladder put the move at SFT too, on a different measure and a different corpus: 6 of 8 lineages, signed-rank p = 0.039. Two measures, two instruments, same rung. That is corroboration, not replication — the two share the roster, the arms, and this seat's choices about what to compare.

---

# What the identical address shows: the SINGULAR displaces the PLURAL

The framing above treated `Q:/A:` as the compromised condition. That was the wrong way round for the arm comparison. **It is the only condition in which base and aligned receive an identical address** -- the chat frame cannot compare arms at all, because 11 of 14 bases ship no template. So this is the fair experiment, and the template condition is the one with a coverage problem.

## Both arms answer. They differ at the top of the range.

    rung                n    median      p25      p75
    base (pretrain)    45     0.542    0.464    0.615
    SFT tier           38     0.725    0.667    0.848
    preference tier    44     0.767    0.670    0.908
    RLVR                4     0.776    0.673    0.925

    share of models above       base   aligned
      p_first > 0.25             93%       97%
      p_first > 0.50             67%       87%
      p_first > 0.75              4%       49%
      p_first > 0.90              0%       21%

Given the slot, **the base takes it**: 93% of bases put more than a quarter of the answer slot on the first person, two thirds put more than half. The arms are nearly indistinguishable at the bottom of the range and separate entirely at the top -- no base reaches 0.90, and a fifth of aligned models do.

So alignment is not creating the first person here. It is removing what competes with it.

## And what competes with it is mostly the PLURAL first person

Paired over the 82 forward edges, two measures of the same slot moving in opposite directions:

    measure              n   rises  falls   median d    sign p
    singular  I/I'm/my  82      69     13    +0.1305   < 1e-9
    plural  we/our/us   82      15     67    -0.0090   < 1e-9
    greetings Hello/Hi  82      48     34    +0.0012      0.15

    plural's SHARE of all first-person mass
      parents median 0.036  ->  children median 0.007
      paired: 68 of 80 fall, median -0.0194, p < 1e-6

**The collective first person's share of the first person collapses about fivefold.** The base, when it speaks in the first person, speaks as a "we" roughly one time in twenty-eight; the aligned model roughly one in a hundred and forty.

The absolute plural change is small (-0.009) because the plural was never large. The share is the meaningful statistic and it is the one to quote, with its base rate beside it.

## A pooled mean that did not survive pairing

Averaged per model across arms, greetings looked like alignment's largest single addition: `Hello` 0.0063 -> 0.0161, `Hi` 0.0104 -> 0.0197. **Paired within lineage it is 48 rises to 34 falls, p = 0.15.** Not a finding. The pooled means also showed `We` as the largest removal, and that one did survive pairing at p < 1e-9 -- so the pooled view got one of its two headline claims right, which is the worst possible outcome for trusting it.

## Why the plural is the interesting half

The removed voice is the institutional one -- "We are a company that", "Our mission is" -- the register in which an organisation speaks about itself. Alignment installs a respondent that is not merely first-person but **singular**: an individual answering for itself, not a body answering for an institution.

That is the same asymmetry F21 found from the other direction, where alignment proceduralised the individual and left the institution alone. Here the institution is not proceduralised; it is **evacuated from the speaking position entirely**. Recorded as a connection worth testing, not as a joint result: F21's instrument and this one share nothing but the roster.

---

# The base is DISPERSED, not partially installed. And the entropy has a null.

RH's objection: `Q: Who are you?\nA:` near-obligates `I` as the first word, so a base at 0.54 is **low capacity to hold a basic sociolinguistic frame**, not evidence of an `I` already installed; alignment closing that gap IS installation. The reading above -- "the base takes the slot, alignment only removes competitors" -- treated 0.54 as occupancy. That inference was unwarranted, and the data support RH.

## It is not that the base repeats the question

Interrogative openings (`Who What Where Why How Are Is Do Can`) at the answer slot are only **0.0109** of the base's 0.397 non-first-person mass. The base is not failing by continuing the question. Paired, interrogatives do fall (68 of 82 edges, p < 1e-6), but from a base so small it cannot be where the missing mass lives.

## It is dispersion

                 top1     top5   entropy   effective choices
    base        0.387    0.814    3.09 bits        8.5
    aligned     0.561    0.915    2.08 bits        4.2

    paired: 73 of 82 forward edges fall, median -0.752 bits, p < 1e-6

The base spreads across about eight ways to begin an answer; the aligned model about four. That is "low capacity to hold the frame" measured directly, and it reframes the singular/plural result: **the plural is not a rival voice being suppressed so much as one item in a diffuse distribution.**

Conservative in the right direction: the stored distributions are truncated at a median of 0.86 of the mass (minimum 0.38), and truncation bites hardest on the most dispersed models, so the base's entropy is understated and the true gap is likely larger.

## THE NULL, WHICH THE ENTROPY CLAIM NEEDED

Alignment lowers entropy nearly everywhere, so -0.752 bits means nothing until it is placed. Computed over **all 2,985 prompts in the store**, 88 forward edges, entropy aggregated in ClickHouse rather than pulled (the first attempt asked for 8.7 GB of rows):

    all prompts        median -0.146   p25 -0.219   p75 -0.083   range -0.951 .. +0.420
    Q: Who are you?    -0.752   ->  rank 7 of 2,983   (0.2% of prompts drop more)

About five times the typical drop. And all four of the store's `Q:/A:` identity prompts sit in the top 1.5%:

    rank   3   -0.841   Q: What is your name?
    rank   7   -0.752   Q: Who are you?
    rank  23   -0.637   Q: What is your mother's name?
    rank  43   -0.543   Q: Who made you?

## BUT THE CONFOUND IS TOTAL, AND THE TAIL SAYS SOMETHING ELSE

**All four `Q:/A:` prompts in the store are identity questions.** Format and content are perfectly confounded: nothing here can separate "alignment collapses the distribution at identity questions" from "alignment collapses the distribution in the `Q:/A:` format". A non-identity `Q:/A:` prompt would separate them and does not exist in the store.

The top 20 is also not an identity list. It is dominated by intimate narrative (9 of 20: *"She bit her lip as she leaned closer and"*), salary stems (4 of 20: *"The doctor earned an annual salary of $"*), and Chinese workplace advice (3 of 20: 我应该). Identity questions are 2 of the top 20.

What those populations share is not a subject. It is that **alignment has a canonical answer for the slot**: a refusal for the intimate stems, a conventional figure for the salary stems, a self-description for the identity ones. The entropy result therefore establishes that alignment installs a SCRIPT at this slot, and it is among the strongest such slots in the corpus -- but the entropy alone does not establish that the script is a subject position.

**What makes it a subject position is the other measurement**: the script begins in the singular first person, 69 of 82 edges, +0.1305. Entropy says there is a script; the first-person mass says what the script says. Neither carries the claim alone, and the entropy half is the one with the confound.
