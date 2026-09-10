---
kind: question
id: ren_sutherland_2025
question: Does the squeezing effect account for the displacement this campaign measures?
status: "RUN 2026-09-10. NO, at endpoint grain. The base argmax LOSES mass on average (-0.0068) and is the top gainer in 23.3% of 14,996 cells; gainers come from across the base distribution, 23.2% from outside the top ten. Scope limit stated: this does not test their mechanism in the DPO-training regime they studied."
headline: "The deflationary rival to F01 does not hold at endpoint grain. If displaced mass went to whatever was already winning, the semantic chain would be a gradient artifact -- it does not, and the reading note's own reconciliation (that gainers are already high-probability) fails too."
grain: claim
---

# Ren & Sutherland, "Learning Dynamics of LLM Finetuning" (ICLR 2025)

`arXiv:2407.10490`. Producer: `squeezing.py`. Reading note:
`Articles/TheoryMachines/reading/ren-squeezing-effect.md`.

---

## CLAIM 1 -- THE SQUEEZING EFFECT

### The claim

From the reading note's summary of the paper:

> "When you suppress a low-probability token via the negative gradient, softmax
> mechanics cause probability mass to concentrate on the ARGMAX -- the already-
> most-probable token. Running DPO too long makes even desired outputs less
> likely because the gradient continues squeezing mass toward the winner."

And the reading note's own statement of the stakes:

> "Their squeezing is MECHANICAL: mass goes to whoever was already winning in
> the distribution, regardless of semantic relationship. It's a consequence of
> the softmax gradient, not of content. Our F01 is STRUCTURED: mass goes to
> SEMANTIC SUBSTITUTES along a chain of proximity."

**This is the deflationary rival to F01.** If displaced mass simply lands on
whatever was already winning, "displacement" is softmax bookkeeping, the chain
`kill -> strangle` is a coincidence of embedding geometry, and every reading
built on the DIRECTION of the substitution is decoration on a gradient artifact.

### What would bear on it, written before measuring

Per (prompt, endpoint pair): is the base argmax the top gainer, and what is its
own delta? Squeezing says usually yes and positive.

### The measurement

`squeezing.py`, 300 prompts x 50 endpoint pairs, 14,996 cells:

    base argmax IS the top gainer     3,489   23.3%
    base argmax gains ANY mass        6,347   42.3%
    mean delta on the base argmax             -0.00679
    median delta on the base argmax           -0.01002

**The base argmax LOSES mass on average**, and is the top gainer in under a
quarter of cells.

### AND THE RECONCILIATION THE READING NOTE PROPOSES ALSO FAILS

That note offers a way for both accounts to be true:

> "The semantic structure of the displacement may arise because the semantically
> related alternatives are already high-probability in the base distribution --
> they are near the suppressed token in the embedding space, so they tend to be
> the ones the softmax gradient promotes."

If that held, top gainers should cluster at low base ranks. They do not:

    rank  1   23.3%      rank  6    4.3%
    rank  2   15.4%      rank  7    3.2%
    rank  3   10.2%      rank  8    2.8%
    rank  4    7.4%      rank  9    2.6%
    rank  5    5.4%      rank 10    2.2%
                         rank 11+  23.2%

**Nearly a quarter of top gainers come from outside the base top ten**, which is
the same share as come from rank 1. The receiving words are not drawn
preferentially from the high-probability neighbourhood.

### THE SCOPE LIMIT, AND IT IS NOT SMALL

**This does not test their mechanism in the regime they studied.** Their claim
is about DPO TRAINING DYNAMICS acting on a LOW-probability token. This measures
base->endpoint movement spanning SFT and preference tuning together, and our
fallers are typically HIGH-probability -- `kill` at `p_base` 0.798 on the
Aquila pair.

**So the defensible statement is: the squeezing effect does not ACCOUNT FOR the
displacement measured here. It is not shown to be absent from DPO training.**
Anyone quoting this as "we refuted Ren & Sutherland" has quoted it wrong.

### WHY IT IS WORTH HAVING ANYWAY

Because it is the objection a reviewer reaches for first, and it now has a
number attached instead of an argument. The mechanical account predicts
concentration on the winner; the winner loses mass.
