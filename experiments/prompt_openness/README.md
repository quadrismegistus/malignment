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

# NOT DONE

- **51 agreed prompts did not join the catalogue** and carry no source. They are
  in `results/openness.csv` with an empty source column, not dropped.
- The 44 contested prompts are recorded with `agreed=0` and were never
  adjudicated. A third coder would settle them; none was run.
