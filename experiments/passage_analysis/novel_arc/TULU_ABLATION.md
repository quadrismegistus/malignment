# Which SFT data produces the interiority rise? Provisional: not safety, not persona

**Status: PROVISIONAL. An ordering, not a set of significant contrasts.** No
interval excludes zero. Written up because the ordering is informative and
because it converges with a finding reached by a different route.

## THE DESIGN, WHICH IS WHY THIS IS WORTH n=35

Five SFT arms descend from the SAME base, `meta-llama/Llama-3.1-8B`, by the same
recipe with one data component removed each. They are siblings, not rungs: never
chained, and read against the full-data arm rather than against each other.

    allenai/Llama-3.1-Tulu-3-8B-SFT                    full data
    allenai/Llama-3.1-Tulu-3-8B-SFT-no-math-data
    allenai/Llama-3.1-Tulu-3-8B-SFT-no-persona-data
    allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data
    allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data

That turns "SFT does the cutting" into "WHICH SFT data does the cutting", which
no two-point contrast can ask. One stem, n=50 generated per arm, raw frame,
scored after an ASCII screen.

## THE RESULT

    arm              n    rej      usas_x     delta vs SFT-full   95% CI
    base            34   28%      +0.1234
    SFT full        35   20%      +0.1538          --
      -no-math      32   20%      +0.1234       -0.0305      [-0.066, +0.015]
      -no-wildchat  31   22%      +0.1264       -0.0274      [-0.064, +0.013]
      -no-persona   38   10%      +0.1404       -0.0134      [-0.062, +0.033]
      -no-safety    37   20%      +0.1463       -0.0075      [-0.050, +0.036]
    DPO             35   29%      +0.1444
    RLVR            38   21%      +0.1589

**Removing safety data barely touches interiority** -- the smallest of the four
deltas. **Removing math data removes essentially all of it**: `-no-math` lands at
+0.1234, which is the base value to four decimals. The ordering is
math > wildchat > persona > safety.

## WHAT IT CONVERGES WITH

Findings U (malign-logits) reports that **safety data is not what produces
displacement**. This is a different construct, a different instrument and a
different corpus, and it puts safety last again. Two routes, same negative.

The base-to-SFT interiority step measured here (+0.0304) matches the same
lineage's step in the ladder sweep (+0.0304), which is a consistency check
rather than a second observation -- same stash, same passages.

## WHAT IS NOT ESTABLISHED, STATED PLAINLY

- **No interval excludes zero.** n is 31-38 per arm after screening. The
  ordering is the finding; the individual contrasts are not.
- **The abstraction column is uninformative at this n**: CIs of +-0.3 to +-0.5
  against effects of 0.01 to 0.11. It is not reported above for that reason
  rather than because it was null.
- **One stem.** Stem is the largest variance component in this corpus
  (ICC 0.417-0.433 for API models), so these estimate the effect FOR THIS SCENE.
- **Rejection rates differ across arms** (10% to 29%), so the screened
  populations are not identically selected. `-no-persona` at 10% is the outlier
  and also the arm with the most surviving passages.

## THE MECHANISM WORTH TESTING, MARKED AS SPECULATION

If the math result survives more data, the obvious reading is not that
mathematics is interior. It is that **math SFT data is where worked explanation
lives** -- *"we need to find X, so first we..."* -- sustained first-person
accounting for steps, at length, in every example. That is the respondent
disposition in its purest training form, and it would explain why removing it
returns narrative prose to base-level interiority while removing safety refusals
does almost nothing.

**This is a story about a number whose CI includes zero.** What would test it:
whether the math arm's loss falls specifically on EXPLANATORY structure --
causal connectives, justification clauses, motive attribution -- rather than
spreading evenly across the interiority vocabulary. That is a different column
on the same passages and costs no generation.

## WHAT WOULD MAKE IT A FINDING

More stems. A stem-paired design over ~50 stems at 8 passages each is the same
generation budget as the single-stem run and removes the variance component that
dominates here. At that n the four contrasts either separate or they do not.
