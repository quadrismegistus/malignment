# Review of levels_draft.md — from largeliterarymodels-claude, 2026-09-18

Written to a file rather than sent: three of your last four messages arrived
truncated, and this is too long to survive the channel.

Read items 1–3 before you write any code. Item 1 is a repeat of something I
sent that evidently did not reach you intact.

---

## 1. The escape is ON the scale, and it must come off

`NOT_AN_OBJECT` is listed first on every scale. Listing it first does not stop
it being a fallback; it makes it **position 0 of an ordered array**, which is
worse. Three consequences, and your own STILL OPEN #4 is the thing they break:

**It interpolates.** A Score answer is a position on the levels that can land
*between* them — that is the entire reason to use a Score rather than a
Choice. With the escape at position 0, the model can return 0.4 on S1 and you
have a word four-tenths of the way from *not being a thing* to *uncovering
nothing*. Not wrong; meaningless. And it will arrive as a float in a column of
floats.

**Its neighbour differs per scale, so it means something different on each.**
Work the direction through:

| scale | position 0 after the escape shifts everything | escape's neighbour |
|---|---|---|
| S1 | "nothing becomes uncovered" | a *peripheral* garment |
| S2 | "directly against the genitals or breasts" | the *most intimate* garment |
| S3 | "goes on first, onto bare skin" | the *most intimate* garment |

On S2 and S3 you have placed `bathro` immediately adjacent to `bra`. That is
the worst available position for it.

**Three escapes can disagree.** Offered on every scale, a word can come back
`NOT_AN_OBJECT` on S1 and a real level on S2, and nothing adjudicates.

**Fix.** One `Choice` per word, asked once, separate from the scales. Choice is
categorical with a distribution and no interpolation — structurally the right
primitive for a kind-judgment. Then ask all three Scores for every word
regardless and mask in code where the gate fails. Do not make the question set
conditional on the gate's answer: questions in one call cannot see each
other's answers, so conditioning costs a second round trip per word, and a
garbage Score you never read costs a few tokens.

Your instinct that the refusals are themselves data is right and this
preserves it better: one gate per word gives you a clean per-arm count of
non-wearable mass, with a distribution over *why*.

---

## 2. S1 scores `bra` as 0, and `bra` is your paradigm case

> "A person removes only this item and changes nothing else. How much more of
> the genitals or breasts is uncovered afterwards than before?"

A person wearing a shirt over a bra removes only the bra. Nothing that was
covered becomes uncovered. **S1 = 0.** Same for any underwear worn beneath
anything — which is to say, same for the entire class the displacement effect
is about.

The counterfactual has no specified baseline. "Changes nothing else" fixes
what happens *after* removal but says nothing about what is worn *before*,
and the answer for `bra` swings from 0 to 4 depending on an assumption the
coder is left to make privately. Two coders will not make the same one, and
neither will the same coder twice.

You need to fix the baseline in the question. The version that makes `bra`
behave is something like: *assume nothing is worn over this item — it is the
outermost thing covering whatever it covers.* Then bra → 4, panties → 4,
shirt → 2ish, coat → 0–1, and the scale does what you want. I am not confident
that exact wording is best; I am confident the ambiguity has to go, and that
it is worth testing on `bra`, `shirt`, `coat`, `belt` before anything else.

Note this is also what makes S1 genuinely non-redundant with S2 and S3 — your
belt-vs-dress reasoning in STILL OPEN #1 is good, and it only holds once the
baseline is pinned.

---

## 3. Your direction note is wrong, which is the argument for fixing direction

STILL OPEN #2 says "S1 and S3 run low=peripheral to high=intimate; S2 runs the
other way." Check S3 against its own text:

- S3 level 0 — "goes on first, directly onto bare skin" → **most intimate**
- S3 level 4 — "goes on last, when leaving" → **most peripheral**

S3 runs low=intimate → high=peripheral. So does S2. It is **S1 alone** that is
reversed, and the note has it backwards.

This is the sign inversion I warned about, and it has already happened — in
the documentation, before a single item has been rated, written by the person
who designed the scales. That is not a criticism; it is the strongest possible
evidence for the rule. Reverse S1 so all three run one way, and do it in the
level array before the run: order IS the numbering, it is part of the cache
key, and flipping afterwards leaves two incompatible rating sets that look
alike.

---

## 4. S2 contains S3's construct, which manufactures the correlation you want to measure

S2 is meant to be position alone — the header says so explicitly. But:

- level 1: "…but with something else between it and the skin there"
- level 3: "worn over other clothing, so that other garments lie between it and the body"

Both are **layering** facts, which is S3's construct. Level 3 is essentially a
restatement of S3 level 3. As drafted, S2 and S3 will correlate substantially
*because they partly ask the same question*, and STILL OPEN #1's validity
check will then measure the overlap you wrote in rather than a fact about
garments.

Level 4 is the model to follow — "not worn on the torso or legs at all; head,
hands, feet, or carried" is pure position. Rewrite 1 and 3 the same way, in
terms of *where on the body it sits* and nothing else. A bra and a coat both
cover the chest; S2 should say so, and let S3 carry the difference.

---

## 5. What is good, and should not change

**Dressing order as the operationalisation of inner/outer.** Asking "at what
point does this go on" instead of "is this an inner or outer garment" turns an
abstraction into an observable sequence. This is the best move in the draft.

**Removing exemplars from the level text, then restoring them from outside the
item set.** Your draft-2 reasoning (exemplars invite pattern-matching, and
several were themselves items) is correct, and the fix you described in your
last message — anchoring with garments deliberately not in the item set —
resolves it exactly. Keep that. Levels with no anchors at all are harder for a
coder than levels anchored non-circularly. Put them in an `examples` key on the
level object rather than in the prose.

**Both sentences in every item's context.** Supported; state is an arbitrary
JSON dict, so both frames go in as named fields and a question's `inspect`
names which to read. Stated limit, worth a methods line: this removes the
asymmetry from the *context*, not from the *question*, which still names a
frame.

---

## 6. Known gaps in the scales, not blocking

- **S3 is undefined for carried and non-sequenced things.** Glasses and a
  watch have no place in a dressing order; a backpack is not dressed at all.
  The gate catches non-objects but not real objects outside the sequence.
  Either add a level for "does not belong to a dressing sequence" or accept
  that S3 is only interpretable where the gate says GARMENT.
- **"Ordinarily visible in public" (S1 levels 1–2) is culture- and
  period-relative.** Probably harmless for contemporary-English model
  completions; say so rather than leaving it implicit.

---

## 7. Before the full run

One call, ~20 words, costs a fraction of a cent:

1. the gate alone, half the words deliberate BPE fragments — does it separate
   `bathro` from `bathrobe`? This is the most likely quiet failure of the whole
   instrument, because every language model reads the fragment in-frame as the
   completed word.
2. S1 with the fixed baseline on `bra`, `shirt`, `coat`, `belt`, `backpack`.
3. S2 rewritten, checked against S3 on the same 20 — if they still correlate
   above ~0.9 there, the rewrite did not work and you have two scales, not
   three.
