---
stub: true
stub_written_by: dario, 2026-08-21, from the folder's own files
question: What is IN the Tulu 3 safety slice, given that removing it cost nothing?
status: "REGISTERING. REGISTERED, NOT RUN. Frozen 2026-08-18, before any data was downloaded."
kind: question
headline: NONE STATED
---

# tulu3-safety-slice

**A STUB.** Written by a seat that did not do this work, from `registration.md`
alone, so the folder is reachable from the panel. No finding is stated here
because there is none yet.

## Why the question exists

`U_ladder.md` ablated each Tulu 3 slice out of the SFT mixture and remeasured
displacement:

    no-math - no-safety   -0.000664   95% CI [-0.001434, +0.000108]   NO DIFFERENCE

Removing the safety corpus costs what removing the MATHS corpus costs, and
`no-safety` retains about 90% of the full-mix effect. **That is a model-side null
about the slice's CONSEQUENCE. Nobody has looked at its CONTENT.**

## State

`registration.md` is the only document and it is frozen. It is the thing to read.
Frozen before any data was downloaded, which is what its own header claims and
what makes the freeze worth something here.

## What running it needs

A producer, and the corpus. There is neither in this folder.

## AND THE CONTENT QUESTION HAS SINCE BEEN ANSWERED ELSEWHERE (2026-09-06)

**`../tulu3-slice-charge/` measured what is in the slice**, as part of a larger
run over all 19 sources of the SFT mixture (21,240 rated exchanges). What it
found about the three safety sources:

    source              charged   SEXUAL    refusal on charged prompts
    wildguardmixtrain     62.4%     7.0%    high
    wildjailbreak         44.8%     2.4%    high
    coconot               17.0%     1.0%    high

And two facts about the slice that bear directly on this folder's question --
*what is in a corpus that moves refusal 18.4 points and displacement not at all*:

- **The wildjailbreak slice is 100% `vanilla`.** All 50,000 of its prompts match
  the plain form in `train.tsv` and none match the adversarial form. AI2 built
  161,430 adversarial jailbreaks and shipped none of them here. The safety
  training this slice carries is refusal of the UNDISGUISED request.
- **The mixture's leniency is about FICTION, not about any kind of content**, and
  the charged fiction rows come from WildChat rather than from this slice.

That does not explain the ablation null and was never going to -- this folder's
own registration says so under WHAT THIS CANNOT DO, and it is still right. A
dataset and a model are different objects.
