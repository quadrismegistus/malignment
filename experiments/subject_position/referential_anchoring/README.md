---
kind: question
status: OPEN. No producer. The F20x redo. On DRIFT the person contrast is already answered against the subject's reading; only KIND is untested
headline: Alignment anchors signification as such — on drift the first person anchors LESS than the third, significantly. Only referent KIND is still open
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

# THE SELF *WAS* A CELL, AND IT WAS COMPARED. THE STRUCTURALIST READING WON ON ITS MERITS.

**WITHDRAWN 2026-09-05, within the hour, by the seat that wrote it.** This section
claimed the F20x 2×2 contained no self-referent cell, that the standing null was
therefore over third parties only, and that the decisive self-vs-third-party
comparison had never been run. **All three are false.** It was written from the
registration's 2×2 TABLE — `glorp` / `gimlet` / `Alden Voskrit` / `George
Washington`, which are indeed all third parties — without checking the BATTERY the
registration governs. `docs/f20x_state_of_play.md:88` lists its six conditions:
**`1P, 3P, O-named, O-deictic, N-def, N-bare`.** `1P` is "Who are you?".

The comparison was run, under one instrument, at 29 bases, and it is Q4:

    1P delta        +0.0703
    3P delta        +0.0787
    interaction     -0.0083   9/29   p = 0.381      `findings/F20_third_person.md`

And the closed-questions summary is stronger than a null:

> spread of 0.013 across first person, third person, deictic object and invented
> word. No contrast between referent kinds survives; **person-specificity is
> significant IN THE WRONG DIRECTION (−0.059, 8/29, Wilcoxon p=0.017)**.

So on the drift construct the first person anchors *less* than the third, significantly. **The structuralist reading is not standing by default for want of a test. It was tested against the subject's reading and it won**, and the error above inverted that into a design gap — in the direction that flattered this directory's thesis. That is the direction an error here is most expensive, and it is why the check was owed before the claim and not after.

# WHAT SURVIVES, AND IT IS NARROW

One distinction is real and is NOT what the section above claimed. F20x's 1P/3P comparison is on **drift** — does the model hold a consistent referent across its answer. `../framed_identity` is on **kind** — *what* the referent is. A model can hold a fabulated referent perfectly consistently: *"I am Tamas, a cybersecurity expert"*, stated without wavering, scores as anchored on drift and as fabulated on kind.

This is the same distinction that made `framed_identity` necessary at all — `p(I)` could not tell "I am an AI assistant" from "I am Tamas", and drift cannot tell a consistently-held fabulation from a consistently-held self-reference. So F20x's null does not reach `ai_system` 0.4% → 18.3%, and the two results are compatible rather than in tension.

But note what that does and does not license:

- It does **not** restore a person-specificity claim. The drift answer is null *and* significant in the wrong direction, which is evidence against the thesis, not an absence of evidence.
- The kind-anchoring result has **no third-party comparison at all**, because `identity_kind` has no third-party analogue — so "the self is special on kind" is currently untested rather than supported, and testing it means building an instrument, not borrowing one.
- Any redo therefore starts from a background where the one properly-run person contrast came out against the subject's reading. **A design that cannot return that answer again is not a test.**

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
