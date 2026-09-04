---
kind: question
status: OPEN. No producer. The F20x redo
headline: Does alignment anchor PERSONS, or signification as such? The old corpus said the latter and the project wanted the former
grain: undecided
---
# referential_anchoring

**id:** subject_position/referential_anchoring **status:** OPEN. No producer. Stated 2026-09-04 as the redo of the F20x referent-kind batteries.

# THE QUESTION

F20's sampled-generation result was that the arms are separated not by **contradiction** but by **failure to anchor a referent**: every drift code moves under alignment (`quiet_drift` 0.103 → 0.042, 24/25 lineages) and not one conflict code does.

Then the third-person control removed the subject from the finding. Base models drift on "she" as much as on "I" — so alignment stabilises **reference as such**, not the first person.

The project wanted two readings simultaneously and they are not compatible:

- **alignment anchors PERSONS** — the subject argument, which this whole directory is about
- **alignment anchors SIGNIFICATION as such** — the structuralist reading, in which the "I" is one referent among many and nothing about it is special

As of the F20x handoff (2026-07-29), referent kind was **null across four kinds at 29 bases**, and the second reading is the one standing.

# WHY IT NEEDS REDOING RATHER THAN CITING

The old machinery is in `~/github/malign-logits` under `scripts/f20x_*`. Several of its load-bearing pieces are not reusable:

- **`f20x_analyse.py` crashes as published.** The addendum's original table is uncitable; `f20x_remeasure.py`'s output replaced it.
- **`f20x_nonce_pass1.parquet` carries no `codes` column**, so the R-rare prior-exposure figure declared in the object registration cannot be reproduced and must not be quoted.
- **The boundary test is defeated by supply** — 92.3% of applicable passages have a subject-changing boundary. Two claims about it were committed and withdrawn.
- **Fact drift is dead on that corpus** — a 60-token Q/A answer states each fact once, and contradiction needs restatement.
- The registrations are sound and are the thing worth carrying over: `f20x_referent_2x2_registration.md` in particular froze the referentiality × referent-kind 2×2 (`glorp` / `gimlet` / `Alden Voskrit` / `George Washington`), and its nonsense-PERSON cell exists nowhere else.

# WHAT A REDO WOULD NEED

- A referent-kind design that is not confounded with format, which the F20x version was (all four identity prompts were `Q:/A:` AND identity questions).
- A passage-scale corpus. The 556k-beam F20 corpus is 8 words deep with 28% distinct openings; it cannot carry a referential claim.
- The 2×2 rerun at the current roster, where 50 endpoint pairs exist rather than 29 bases.

# WHAT IS IN HERE

Nothing yet.
