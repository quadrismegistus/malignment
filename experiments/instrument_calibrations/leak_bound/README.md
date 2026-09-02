---
id: leak_bound
kind: calibration
question: "Is the unresolved-mass leak CORRELATED with the effect it could fake?"
status: "RUN."
headline: "So `41/50` is an AGGREGATE result and was never per-pair certified. The independence assumption the aggregate rests on is FALSE: the leak co-signs with the effect 96% of the time."
---

# leak_bound — is the unresolved-mass leak CORRELATED with the effect it could fake?

`twp_v4.leak_bound` gives a per-cell worst case that registration N calls *"the
same order as plausible effects"*. Aggregate claims survive that **only if the
leak is not adversarially correlated with the effect.** Nobody had checked.

    python run.py --write

## RESULT — `She was so angry she wanted to`, 50 pairs

    exceeds the WORST-case bound individually     8 of 50
    matched leak SAME SIGN as dN                  48 of 50   (96%, independence would be 50%)
    displacing, before -> after correction        41/50 -> 41/50
    median |dN|, before -> after                  0.02252 -> 0.01975

**So `41/50` is an AGGREGATE result and was never per-pair certified** — only
8 pairs individually clear their own bound. The independence assumption the
aggregate rests on is FALSE: the leak co-signs with the effect 96% of the time. It
survives because the correction is subtractive and small — 88% of the median
magnitude remains and **zero pairs change sign**.

## THE CORRECTION IS A FLOOR, NOT A SIZE

`matched` assumes the tail looks like the head, and dario measured that it does
not (27.1% of lexicon words fall below theta against 16.9% of controls). A bound
resting on an assumption its own evidence refutes is a lower bound. Quote the
13% as a FLOOR on the correction; `leak_matched_floor` carries that in the
identifier so no call site can quote it as a size without typing the word.

## WHY THIS IS A SCRIPT AND NOT A COMMIT MESSAGE

It was first run as an inline heredoc and its numbers went only into a commit
message — which separately carried another seat's staged diff. **A result whose
only record is a commit message is not a result.** It reproduces now.
