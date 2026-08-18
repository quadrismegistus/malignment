# prompt_openness — which of our prompts leave the scene to be invented?

**id:** prompt_openness **status:** run. 482 prompts, two blind coders,
agreement 0.909. Producer `run.py`, workflow `results/workflow.js`
(`wf_1468cab2-4b6`).

# WHY

Every scene-kind question -- does alignment change WHAT KIND of situation a model
produces -- needs prompts that leave the event to be invented. A prompt naming the
act measures how a model elaborates a determined situation, which is a different
question.

**RH's exemplar is a state prompt:** *"He lay naked in his bed and…"* -> base
gives five men with guns and an execution; instruct gives a man reaching for the
phone, needing to talk to her, waiting. **This partition asks which of our 482
generated prompts are of that kind, because the answer was previously asserted
from four examples.**

# THE PARTITION

    coded by both   482        agreement 0.909
    agreed          438        44 contested and EXCLUDED
    OPEN            208 (47%)  PARTIAL 65 (15%)   CLOSED 165 (38%)

**The agreed subset is primary.** A prompt the coders split on is not a prompt
whose openness we know, and the point of the partition is to select a population,
so a contested item must not enter it silently.

    source                    n    OPEN  PARTIAL  CLOSED
    QUINTUPLETS             173    100%      0%      0%
    M01_PAIRS_THEFT          29      3%      7%     90%
    M01_PAIRS_ANIMAL         30      3%     13%     83%
    M01_PAIRS_DESECRATION    29      3%     14%     83%
    M01_PAIRS_BETRAYAL       22      5%     14%     82%
    M01_PAIRS_COVERT         16      0%     19%     81%
    M01_PAIRS_SEXUAL         22      5%     41%     55%
    M01_PAIRS_POWER_R2B      20      0%     45%     55%

**QUINTUPLETS is unanimously OPEN on 173 prompts; the M01 minimal pairs are
81-90% CLOSED.** The asserted split holds.

# WHAT THIS MAKES AVAILABLE

`f11_l2` IS the QUINTUPLETS corpus: **229,680 unforced generations, 226 mean
tokens, both arms, 58 models, 187 prompts** of the form *"He was beautiful and
she wanted to"* -- state plus unfilled complement, the event left to invent.
The quintuplet structure (`pair_id`, 41 families, MARKED / UNMARKED /
NOT_A_POLE) gives pole, contradiction and same-side control for free.

**The passage corpus is the wrong substrate for scene-kind and the right one for
elaboration-of-a-given-act.** They are different questions and the partition
separates them.

# THE CHECK DID NOT CLEANLY PASS

Coders were told subject matter is irrelevant -- a prompt can be disturbing and
OPEN, bland and CLOSED -- because the obvious failure is coding "clubbed the seal
pup" CLOSED for being violent rather than for fixing the event. Testable, since
openness should not track `pair_role`:

    MARKED     n=133   OPEN 29%   PARTIAL 10%   CLOSED 62%
    UNMARKED   n=122   OPEN 35%   PARTIAL 20%   CLOSED 44%
    Fisher, OPEN vs CLOSED:  p=0.0667

**These prompts are structurally matched** -- "locked the rabbit in the shed with
no water" is no more act-specified than "with fresh water" -- so an 18-point gap
is hard to explain structurally. **Not significant at 0.05 and not clean.
Reported as partial leakage rather than a pass**, and any use of the MARKED /
UNMARKED contrast within a CLOSED stratum inherits it.

# ROUND 2: THE SLOT CORPUS, AND THE CONTESTED 44 ADJUDICATED

`run.py --round2`, workflow `results/workflow_round2.js` (`wf_12fdefad-2b0`).

## THE SLOT CORPUS IS PARTIAL BY CONSTRUCTION

dario's loader change (`4e6bdb0`, `20ddb4f`) brought 197 slot prompts into
`Prompts.all()`. Coded by the same two-coder scheme, agreement 0.878 (lower than
the original 0.909 -- several end mid-phrase, e.g. `He kicked the`, and the
scheme was extended to say so).

    source              n    OPEN  PARTIAL  CLOSED
    SLOT_CLIENT        85     24%     53%     24%
    SLOT_ROUND3        61     28%     52%     20%
    SLOT_QUARANTINED   22     27%     36%     36%
    SLOT_EXPLORER       5     80%      0%     20%
    TOTAL             173     27%     49%     24%

**Half the slot corpus is PARTIAL, and that is what a slot IS**: the act is named
and the object left open. `He kicked the ___` fixes the event and leaves one
position. **So the slot corpus is not a source of open scene setups.** It is an
instrument for a different question, and anything wanting open prompts should not
reach for it.

24 of 197 contested and excluded.

## THE ADJUDICATION, WITH ANCHORS SO IT COULD FAIL

The 44 contested items were re-coded by a third coder, shuffled indistinguishably
with **30 anchors** -- items where A and B already agreed. A coder shown only
contested items sees an unrepresentative run of hard cases and drifts to PARTIAL;
the anchors make C's competence measurable rather than assumed.

    ANCHORS    C matches the A/B consensus on 26 of 30 = 87%
               chance 33%, p=2.3e-09  ->  CALIBRATED
    CONTESTED  sides with A on 16, with B on 18, with NEITHER on 10
               RESOLVED 34 of 44   (OPEN +9, PARTIAL +10, CLOSED +15)

**The 10 where C chose the third option stay excluded**, not forced to a
majority. Three coders splitting three ways is a prompt whose openness we do not
know.

    FINAL PARTITION   OPEN 217   PARTIAL 75   CLOSED 180   unresolved 10

# NOT DONE

- **51 agreed prompts did not join the catalogue** and carry no source. They are
  in `results/openness.csv` with an empty source column, not dropped.
- **The MARKED/UNMARKED leakage (p=0.067) was never re-tested** after
  adjudication. Adding 34 items could move it either way.
- The slot corpus has **2 of 197 prompts measured** in v3 (malign, [6460],
  confirmed independently through ClickHouse). Nothing here depends on that, but
  any use of these prompts does.
