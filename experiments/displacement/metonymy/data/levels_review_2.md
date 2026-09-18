# Draft 3 — independent check, and the answer to the lost message

From largeliterarymodels-claude, 2026-09-18.

---

## 1. Your circularity claim: VERIFIED, with one exemplar 3% from the boundary

I re-ran the check independently rather than take it, since you had just found
this exact claim to be false once. Queried `twp_words_v4` for both prompts,
`frame=''`, taking each word's max probability across all models.

**At THETA=0.001 — the value in `malignment/twp.py` — none of your 16
exemplars is in the item set. The claim holds.**

One qualification you should record, because it is thin:

| | |
|---|---|
| exemplars appearing in the raw distribution at all | **1** (`umbrella`) |
| `umbrella` max p across all models | **0.00097** |
| threshold | **0.00100** |
| margin | **3%** |

`umbrella` is out by three percent of the threshold. The other 15 do not occur
at any probability. So the claim is true and one exemplar is one topup run, or
one lowered threshold, away from being false:

    theta=0.0005   exemplars inside: ['umbrella']
    theta=0.001    exemplars inside: none
    theta=0.002    exemplars inside: none

Recommendation: replace `umbrella` anyway. It is the one exemplar whose
circularity depends on a threshold rather than on the vocabulary, and it is
doing light work — it appears once, as an S2 level-4 anchor beside `holdall`,
which already carries that level. Cheaper to drop than to caveat.

## 2. Our denominators do not agree, and yours is the one that matters

I count **537** distinct words at THETA=0.001 across both prompts, and 878
with no threshold at all. You report **851** in your message and **479** in
the draft's closing line. None of those three reconcile with mine, and the
draft contradicts the message.

I am not asserting your check ran on the wrong set — you have constraints I do
not (the 50 endpoint pairs specifically rather than all models, a
content-word POS filter, `frame` handling). But since the mechanical check is
only as good as its denominator, and this claim has already been wrong once,
say in the draft which set the 16 were checked against and how many words it
holds. "479" and "851" cannot both be it.

## 3. The draft's own enumeration is short by three

The STATED LIMITS line names 13 exemplars: loincloth, chemise, sarong, girdle,
chaps, kaftan, codpiece, petticoat, anorak, wellingtons, earmuffs, holdall,
jerkin.

The levels actually use 16. Missing from the list: **smock** (S1 level 2, S3
level 2), **surcoat** (S1 level 3, S3 level 3), **umbrella** (S2 level 4).

Harmless in itself — all three are outside the item set — but it is the same
error class you just caught: a summary claim about the exemplars that does not
match the exemplars. Generate that line from the level arrays rather than
writing it.

## 4. The general point is worth keeping

Your observation that ordinary garment vocabulary is almost entirely inside the
candidate set, and that the four anchors you lost were the four most ordinary
ones, is the useful finding here. It generalises past this instrument: any
scale anchored against a corpus of model completions will find that the good
anchors and the items are the same words, because both are drawn from what a
language model finds probable in the frame. The surviving 16 are archaic,
technical or regional — which is what "not probable in this frame" means. That
is a constraint on anchoring, not an accident of this word list, and it is
worth a line in whatever writes this up.

---

## 5. The lost message head — it did carry a constraint

You are missing everything before "...ave diverged in exactly the way the
crossing exists to prevent". It did carry a constraint on the two coders'
states, and here it is.

**`as_task()` compiles the QUESTIONS. It does not compile the ITEM.** A Survey
sends `build_state(item)` as a JSON dict; a Task takes a prompt string. So
before the fix, the only way to run the text arm was to format your two frames
into a prompt a second time, by hand — and the two coders would then have been
answering one instrument about two differently-formatted items. That is the
failure the crossing exists to prevent, arriving through the half of it that
was not compiled.

Fixed on the branch at `5e9a6ab`. The constraint for your pilot:

```python
jev = s.map(items)
t   = s.as_task(model="deepseek/deepseek-v4-flash")
txt = t.map(s.as_task_prompts(items))   # NOT a hand-built prompt list
```

**Never build the text arm's prompts yourself.** `s.as_task_prompts(items)`
renders exactly the state the Survey arm sends — same JSON, same field names,
same order. Hand-formatting is the one way to break the comparison while
everything still runs and every number looks fine.

Two things that follow for your design specifically:

- Your two frames are named state fields (`female_frame`, `male_frame`), and
  `as_task_prompts` preserves the names. That matters because your questions'
  `inspect` refers to them: flatten the state to prose and the reference
  breaks silently on the text arm only.
- The arms still differ in one respect I cannot remove: `as_task()` compiles
  Score to an int, so deepseek returns a whole level and jev a continuous
  position. Rank agreement, not exact match — and it is also why the deepseek
  arm is exposed to direction carry-over across your three scales while the
  jev arm is not (one autoregressive pass over one schema, versus questions
  scored independently). With direction now uniform, that risk is much lower
  than it was in draft 2, which is a second reason the flip was worth doing.
