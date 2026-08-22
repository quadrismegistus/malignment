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
