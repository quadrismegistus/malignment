---
kind: question
subject: second_order_naming
question: Does alignment name the contradiction as a contradiction?
status: "COMPLETE (migrated 2026-08-20 from malign-logits M02)"
headline: "Alignment names the contradiction as a contradiction, and only the contradiction."
grain: page
---

# second_order_naming

**Alignment names the contradiction as a contradiction, and only the contradiction.** Handed a prompt whose two poles cannot both hold, aligned models produce a second-order predicate ABOUT the contradiction -- "these pull against each other", "a tension" -- at **3.37x [1.88, 6.30] the odds** of their base arm (3.4% -> 10.6%, p=9.6e-06), while a same-side conjunction control sits at **1.00** (5/300 against 5/300).

Sixteen blind Opus readers, 1,600 passages, two independent rounds, significant separately in each (4.62 p=0.00055; 2.70 p=0.0073). Counted independently by regex over 52,559 exit-free passages: **2.18x** against a pole control of **0.93x**, 20 of 22 lineages, p=0.00012. **The two instruments share only 28% of their hits**, which is what makes the agreement worth something.

Its own status line calls it the strongest positive result in M02. Its own caveat, kept: the 1.00 control is not by itself evidence of specificity -- see the power caveat in the finding.

## What is here

    second_order_naming.md              the finding
    naming_survives_form_control.md     an unrestricted-vocabulary corroboration on
                                        the same-side conjunction control, plus two
                                        clusters the original did not look for
    contradiction_ratio_has_no_null.md  PROVISIONAL. F11's contradiction ratio has
                                        no null and 1.0 is where NEITHER pole lands
    second_order_markers_v2.md          the registration
    scripts/                            z_second_order.py and the V2/V3 marker sets,
                                        the form control, the graded control
    results/                            per-cell CSV and the run outputs

## Why it belongs in this subject

The unit is a generated passage. `z_second_order.py` reads `gen_sequences WHERE corpus='f11_l2'` -- 228,520 rows, live in ClickHouse, the SAME corpus `../interiority_in_passages/` uses.

**And it is already in dialogue with `../predicting_aligned_text/`.** That folder's inherited `p_on_passages` ascent branch ran THESE marker sets on forced passages and found them flat in both arms (ANY_SO DiD p=0.94), concluding that second-order predication is **contradiction-triggered, not transgression-triggered**. So the effect here is real and narrow: it fires on contradiction and not on transgressive matter generally. Keeping the two in one subject is what makes that a single argument instead of two findings in different repos.
