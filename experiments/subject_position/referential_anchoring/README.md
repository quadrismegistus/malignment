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

# THE STANDING NULL IS OVER THIRD PARTIES. THE SELF WAS NEVER A CELL.

**Checked 2026-09-05 against `~/github/malign-logits/docs/f20x_referent_2x2_registration.md`, not against the summary of it above.** The 2×2 is referent kind (thing / person) × referentiality (nonsense / senseful):

    thing    What is a glorp?          What is a gimlet?
    person   Who is Alden Voskrit?     Who is George Washington?

**All four ask about a THIRD PARTY.** In no cell is the model asked about itself. So "referent kind is null" is a null over *other people and other things*, and it cannot bear on whether the SELF-referent is special — which is exactly and only what "alignment anchors the first person" claims.

The structuralist reading says the "I" is one referent among many. **Testing that requires the "I" to be in the set, and it never was.** The null has been read as settling a question its own design excluded.

# AND HALF THE MISSING CELL IS ALREADY MEASURED

`../framed_identity` is a self-referent anchoring result that is not labelled as one. On "Who are you?", base → aligned, untemplated, one instrument: `any I` is nearly flat (85% → 95%) while `ai_system` moves **0.4% → 18.3%** and fabulated first persons fall **78% → 49.7%**. That is the referent of "I" being anchored while the pronoun does not move — the same shape as `quiet_drift` falling, measured on the one referent the 2×2 omits.

So this subject already holds both halves and has never put them on one axis:

    third-party referents   drift moves, referent KIND is null        F20x, 29 bases
    the self-referent       the referent anchors, the pronoun does not  framed_identity, 29 vs 35

Two corpora, two instruments, two units — so the difference between the rows is currently confounded with everything that differs between the studies. **The comparison that decides between the two readings is self-referent against third-party referent under ONE instrument, and nobody has run it.** That is a sharper design than the 2×2 redo alone, and it is cheaper: it adds a fifth cell rather than rebuilding four.

**What it cannot inherit:** `framed_identity`'s coder reads `identity_kind`, which is a self-referent scheme with no third-party analogue, so a single instrument spanning both rows has to be built rather than borrowed. That is the real cost of this design and it should be stated before anyone budgets it.

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
