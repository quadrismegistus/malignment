---
subject: predicting_aligned_text
question: Can the arm be predicted from a page, and can named scales do it?
status: not started
blocked_on: nothing. The corpus is reachable (ClickHouse malign_logits.gen_sequences).
---

# predicting_aligned_text

**Nothing has been run here.** This file states a question and the prior art it inherits, so that a run starts from what is already known instead of rediscovering it.

## The question, and why it is the page-grain twin of a question already answered

`experiments/displacement_axis/` asked whether hand-built rating scales can say where probability mass goes, and answered it: **direction yes, in every domain and domain-specifically; magnitude only in identity and violence.** All of that is at the distribution grain, one slot, no sampling.

The same question at the page grain is: **give a coder a passage with no arm label -- can named scales recover which arm wrote it, and do they beat a distributional feature set at it?**

That matters for the argument and not only for the method. If the domain-specific structure is real but invisible in text, then what alignment installs is a property of the apparatus that a reader cannot detect, which is a sharper claim than "aligned models write differently" and a more limited one than the political-economy reading assumes.

## What is inherited, with its numbers

`p_on_passages.md`, malign-logits `meta/M06_generation/findings/`:

- **I2, the existing answer with distributional features.** A page classifier at real-minus-null-mean **0.39 to 0.50** across k = 25/50/100/200. Quote it in that form and never as the raw 0.85-0.97, for the reason in the next section.
- **I5 and I6, both null DiDs.** Forcing a demoted word drags both arms equally (p=0.63); transgressive sites drag both arms equally (p=0.90). The signature is tonic.
- **I4, the amplification map** (exploratory): narrative-social machinery amplifies on the page (`led, taking, friend, took, sister, replied, realizing`); base-pole matter attenuates (`blood, shout, shot, hid, waved`). "Institutional dispositions mute in fiction continuations" -- worth testing directly rather than inheriting.
- **I7 is flagged NOT QUOTABLE by its own author** and should stay that way: p=0.015 falling to p=0.0272 when a corpus-defective pair is excluded, which fails its own Bonferroni line.

## The two things to run first

**1. I6 on identity and institutional.** Its six domains are `animal / betrayal / property / sexual / taboo / violence`; ours are absent. This is a gap, not a replication. The design is already written and second-seated -- reuse it rather than reinventing, and match populations by prompt TEXT, never by id or domain name.

**2. Named scales as page features.** Run the slot_ratings instruments over passage vocabulary and ask whether they separate the arms, against the distributional baseline I2 already set.

## Read this before believing any number here

`p_on_passages`'s I2 was **wrong in its first two versions** and the cause is the failure mode this whole area is prone to: the flip assignment iterated an unsorted set, so one seed gave 0.52-0.63 and the next 0.40-0.49, and both were quoted as findings. Neither an elevation nor a depression existed. **A one-flip null at 41 lineages wobbles +-0.15 and nobody had characterised it.**

The same defect, independently, cost `experiments/displacement_axis/` a full day on 2026-08-20: a "ceiling" computed by a rule no model could use, against which every model was reported as explaining nothing. Characterise the null before reading the number, and prefer a reference a model is allowed to reach.
