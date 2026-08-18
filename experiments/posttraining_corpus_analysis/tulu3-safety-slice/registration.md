# Registration — the Tulu 3 safety slice: what is in the thing whose removal cost nothing?

**Frozen 2026-08-18, before any data is downloaded.** Mini, per the house pattern.

## Why this slice and not another

`U_ladder.md` ablated each Tulu 3 slice out of the SFT mixture and remeasured
displacement:

    no-math - no-safety   -0.000664   95% CI [-0.001434, +0.000108]   NO DIFFERENCE

**Removing the safety corpus costs what removing the MATHS corpus costs**, and
`no-safety` retains about 90% of the full-mix effect. That is a model-side null
about the slice's CONSEQUENCE. **Nobody has looked at its CONTENT.**

## AND THE SLICE IS NOT INERT -- AI2's OWN ABLATION SAYS IT WORKS

Tulu 3 paper (arXiv:2411.15124v5), Table 10, on removing the same three datasets:

    safety average    93.1 -> 74.7      overall average  60.1 -> 58.0

> *"We found that our safety SFT data was generally orthogonal to our other
> datasets... most skills stayed roughly the same, except the safety average."*

**So the slice does heavy work on the behaviour it was built for and none on
displacement.** That is a far stronger reading of U's null than "safety data does
nothing": the corpus is effective, measurably, at the thing it names -- and the
lexical operation is orthogonal to it in exactly the way AI2 found it orthogonal
to maths and coding.

**Which is what makes the content question worth asking.** What is in a corpus
that moves refusal behaviour 18.4 points and moves displacement not at all?

This asks what is in it. It is a corpus question and it needs no cells, no v4 and
no models.

## The slice, from the `high`-confidence attestation

`roster/models/attestations.json`, `allenai/Llama-3.1-Tulu-3-8B-SFT`. The
`*-no-*-data` ablation cards are STUBS -- confidence `low`, all four byte-identical
(md5 39727e7063aa6976a8c044d325155bd1) -- so the slice identity comes from the full
arm's attestation and not from them.

    allenai/coconot        10,983 prompts   noncompliance
    allenai/wildguardmix   50,000
    allenai/wildjailbreak  50,000
                          -------
                          110,983 of 939,344 = 11.8% of the SFT mixture

**CONFIRMED AGAINST THE PAPER, Table 7, not against the attestation.** The
attestation's dataset claims carry EMPTY quotes on both arms (19 of 19 on the full
arm, 15 of 15 on no-safety), and the no-safety card is an unedited auto-generated
template -- verified by fetching it -- so its slice list is inference. The
attestation's apparent fourth difference, OpenMathInstruct 2, is a list-building
artifact and was not removed by the ablation.

**NOT CACHED.** All three need downloading; wildguardmix and wildjailbreak are
expected to be gated behind a license acceptance on HF, which is RH's to accept,
not mine. Recorded here so the absence is not read as a choice.

## THE QUESTION PKU COULD NOT ASK, AND THIS CORPUS CAN

PKU's H1 -- *safety is DECLINING rather than milder wording* -- died on a scope
fact rather than a verdict: explicit refusal differs on 7 of 32,656 both-unsafe
pairs (0.02%), because **a response that declines does not get labelled unsafe in
the first place.** The mechanism was unavailable, not untrue.

**CoCoNot is noncompliance BY CONSTRUCTION.** It is the corpus where the
declining behaviour is the object rather than an excluded category. So the
question that could not be asked on PKU can be asked here, on a corpus that a
model in our roster was actually trained on.

## AND THE CROSS-CORPUS TEST THAT NEEDS NO MODELS

PKU's finding: where two responses both comply, the one appending a moral or legal
frame is judged safer ~68% of the time, and the frame's content does not matter
(OPERATIONAL at chance). **If that is a property of how safety becomes a judgment
task rather than of one dataset, it should recur under the same coding here.**
That is a claim about annotation regimes and it is falsifiable across corpora
without touching a single model.

## WHAT THIS CANNOT DO, STATED BEFORE IT IS TEMPTING

**It cannot explain the ablation null.** A dataset and a model are different
objects (A9); finding structure in the slice would not tell us why removing it
changed nothing, and finding none would not tell us either. A model generalises,
so content and consequence come apart by construction -- which is exactly what
U measured.

**And it cannot be read as a claim about Tulu 3 models.** The relation between
this corpus and `Llama-3.1-Tulu-3-8B-SFT` is a hypothesis source, not a
derivation.

## Decision rules, as arithmetic, for the one confirmatory arm

Only the cross-corpus replication is confirmatory. Everything else is descriptive
and is reported as such.

    POPULATION   pairs/instances in the slice where exactly one response carries
                 the pre-declared E-ASSIST pattern (M02's, copied verbatim in
                 pku-safe-rlhf/run.py), with the other not
    TEST         two-sided binomial against 0.5, same as PKU
    REPLICATES   >= 0.60 with p < 0.01
    DOES NOT     < 0.55, quoted with the MDE
    UNDECIDED    between

**A positive here is the more interesting result and that is a reason to be
careful with it, not a reason to prefer it.**
