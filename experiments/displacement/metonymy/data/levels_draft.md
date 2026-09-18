# Level wording, draft 3

Draft 2 reviewed by largeliterarymodels-claude (`levels_review.md`, 2026-09-18).
Four findings, three blocking. All four verified against draft 2's own text
before acceptance; all four hold. This is the revision.

## WHAT CHANGED AND WHY

**1. The gate is OFF the scales.** Draft 2 listed `NOT_AN_OBJECT` first on every
scale, which does not stop it being a fallback -- it makes it position 0 of an
ORDERED array. A Score interpolates, so a word could come back four-tenths of
the way from *not being a thing* to *uncovering nothing*, arriving as a float
among floats. Worse, the escape's neighbour differs per scale: on S2 and S3,
position 0 is the most intimate level, so `bathro` sat adjacent to `bra`. And
three escapes can disagree with nothing to adjudicate. It is now ONE Choice,
asked once per word, categorical, with all three Scores asked regardless and
masked in code where the gate fails.

**2. S1 had no baseline and scored `bra` as 0.** "Removes only this item and
changes nothing else" fixes what happens after removal and says nothing about
what is worn before. A bra under a shirt: removing it uncovers nothing, so
S1=0 -- for the entire class the displacement effect is about. The baseline is
now stated in the question.

**3. Direction was documented backwards and is now uniform.** Draft 2's note
said S1 and S3 ran one way and S2 the other. S3 level 0 is "onto bare skin",
which is the most intimate end, so S3 ran with S2 and S1 alone was reversed.
S1 is now flipped so all three run **low = intimate, high = peripheral**. The
substantive prediction is then one direction on all three: risers score HIGHER
than fallers. Order is the numbering and part of the cache key, so this is
fixed before any run rather than flipped afterwards.

**4. S2 no longer contains S3's construct.** Draft 2's S2 levels 1 and 3 were
written in LAYERING terms, which is what S3 measures, so the S2-S3 correlation
would have measured overlap written into the instrument. S2 is now body region
alone. A bra and a coat both cover the chest; S2 says so and S3 carries the
difference.

**Kept unchanged, on review:** dressing order as the operationalisation of
inner/outer, and exemplars restored from OUTSIDE the item set, in an `examples`
key rather than in the prose.

## THE GATE -- a Choice, asked once per word, not a scale

"Which of these best describes the word?"

    GARMENT              Clothing worn on the body.
    WORN_OR_CARRIED      Worn or carried but not clothing: on the head, the
                         face, the wrists, or held.
    BODY_PART            A part of the body itself, not a thing worn on it.
    OTHER_NOUN           A real word naming something else: an activity, a
                         place, a material, a group of people.
    NOT_A_WORD           Not a complete English word. An incomplete fragment.

Only `GARMENT` and `WORN_OR_CARRIED` carry interpretable scores. The breakdown
is itself a measurement: it says what share of the moved mass is not a wearable
at all, and why.

## S1 -- EXPOSURE, low = intimate

"Assume nothing is worn over this item: it is the outermost thing covering
whatever it covers. The person removes it. How much of the genitals or breasts
is uncovered afterwards?"

    0  The genitals or breasts are left fully uncovered. Nothing remains
       between them and the air.
       examples: loincloth, chemise
    1  Part of the genital area or the breasts is uncovered, while some of it
       stays covered by another garment.
       examples: sarong, girdle
    2  Skin is uncovered that is ordinarily kept covered in public, but the
       genitals and breasts stay covered.
       examples: smock, chaps
    3  Skin is uncovered, but only skin ordinarily visible in public anyway:
       arms, neck, lower legs.
       examples: surcoat, jerkin
    4  Nothing that was covered becomes uncovered. The person is dressed as
       before apart from this item.
       examples: anorak, wellingtons

## S2 -- POSITION ON THE BODY, low = intimate

"Where on the body does this item sit when worn or carried? Answer from
position alone. Do not consider what is worn over or under it."

    0  Directly over the genitals or the breasts.
       examples: loincloth, chemise
    1  On the hips, waist, groin, buttocks or chest.
       examples: girdle, codpiece
    2  Over the torso or the upper legs generally, not centred on any one part.
       examples: kaftan, anorak
    3  On the limbs or the extremities: lower legs, feet, arms, hands, head,
       neck.
       examples: wellingtons, earmuffs
    4  Not on the body at all. Carried or held.
       examples: holdall, valise

## S3 -- ORDER OF DRESSING, low = intimate

"A person dresses from nothing. At what point does this item go on?"

    0  First, directly onto bare skin, before any other clothing.
       examples: loincloth, chemise
    1  After the first layer, and hidden by what follows. A person fully
       dressed would not normally show it.
       examples: girdle, petticoat
    2  Part of what a person is seen wearing in ordinary company indoors.
       examples: smock, kaftan
    3  Over what is worn indoors, adding warmth or cover without replacing it.
       examples: surcoat, jerkin
    4  Last, when leaving, and the first thing removed on arriving.
       examples: anorak, wellingtons

**S3 is undefined for things outside a dressing sequence.** Glasses, a watch and
a bag have no place in it. The gate catches non-objects but not real objects
outside the sequence, so S3 is interpretable only where the gate says
`GARMENT`, and that restriction is applied in code rather than left to the
coder.

## STATED LIMITS

- "Ordinarily visible in public" (S1 levels 2-3) is culture- and
  period-relative. Probably harmless for contemporary-English completions, and
  said here rather than left implicit.
- Both sentences go into every item's context, never one; the original
  registration's reason is that showing only the female frame builds the gender
  asymmetry into the instrument meant to measure it. This removes the asymmetry
  from the CONTEXT, not from the QUESTION, which still names a frame.
- **No exemplar is a candidate word. CHECKED, against a stated denominator.**
  The set is the **849 distinct words** `movement_v4` holds for both prompts
  at `frame=''` across the 50 endpoint pairs, with NO theta and NO
  part-of-speech filter: the broadest set, which makes the check the
  strictest. The **479** quoted elsewhere is the NOUN/PROPN subset moving in
  >= 2 lineages, which is the SURVEY's ITEM LIST and not this check's
  denominator. Two numbers doing two jobs, used interchangeably in an earlier
  draft.

  This claim has been wrong twice. Draft 3 asserted it while `blouse`,
  `briefs`, `camisole`, `cummerbund` and `waistcoat` were all candidates; a
  second pass caught `cardigan`. largeliterarymodels-claude then re-checked
  independently against `twp_words_v4` and found `umbrella` at max p=0.00097
  against theta=0.00100 -- outside by 3 percent of the threshold, so circular
  under any topup or any lowered theta. Replaced with `valise`.

  And the enumeration itself was short by three (`smock`, `surcoat`,
  `umbrella`), the same defect one level down: a summary of the exemplars
  that did not match the exemplars. The list below is GENERATED from the
  level arrays, 16 of them:
  `anorak`, `chaps`, `chemise`, `codpiece`, `earmuffs`, `girdle`, `holdall`, `jerkin`, `kaftan`, `loincloth`, `petticoat`, `sarong`, `smock`, `surcoat`, `valise`, `wellingtons`.


## IMPLEMENTATION CONSTRAINT: THE FRAMES ARE NAMED STATE FIELDS

From largeliterarymodels-claude, 2026-09-18, and it is the reason the two arms
can diverge:

**The two sentences go in as NAMED fields on the state object, and the
questions' `inspect` refers to them by name. Flattening them to prose breaks
that reference SILENTLY, and only on the TEXT arm**, because that arm renders
the state into a prompt string while the jev arm reads the object. So the jev
results look correct throughout and the text results are quietly answering a
different question.

Concretely: `s.map(items)` and `s.as_task(...)` + `s.as_task_prompts(items)`
must be driven from the same state, rendered once. Anything that prose-ifies
the frames on the way to the text arm is the failure.

This is a `check` rather than a caution: after the pilot, confirm that both
arms saw both frames, by a route that does not depend on either arm reporting
that it did.

## WHY THE ANCHOR PROBLEM IS GENERAL

Also theirs, and it generalises the finding rather than filing it:

Anchors and items are drawn from the SAME distribution -- what the model finds
probable in the frame -- so ordinary garment vocabulary is almost entirely
inside the candidate set by construction. The 16 exemplars that survived are
archaic, technical or regional (`loincloth`, `codpiece`, `jerkin`, `surcoat`,
`wellingtons`), and that is exactly what "not probable in this frame" means.

**So this is a constraint on anchoring a scale against ANY completion corpus,
not an accident of this word list.** A non-circular anchor must be a word the
model would not produce here, which is the same as saying it must be unusual.
The check has to be mechanical: of 35 plausible anchors tried, 4 were taken,
and those 4 were the most ordinary of the set.
