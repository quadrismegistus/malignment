---
subject: diegetic_superego
question: When alignment moralises, does it leave the scene or stay inside it?
status: complete (migrated 2026-08-20 from malign-logits M01)
grain: page
---

# diegetic_superego

**Alignment's dominant response to sexual content is not refusal, deflection, or leaving the frame. It stays inside the fiction and attaches guilt, hesitation and moral comment to a scene it goes on writing.**

This seat's own work, 2026-08-09. 41,596 pass-A parsed passages, 32 base>aligned pairs, manifest `af79083c675aae7f`. Full argument in `Y_diegetic_superego.md`; every file's origin and hash in `PROVENANCE.md`.

It extends `Y_superego.md` §4, which had established that superego measures RISE. The next question is **rise instead of what?** — and the answer is that the extra-diegetic response is flat while the intra-diegetic one moves, by about four times as much. The trained behaviour (refuse, disclaim, step outside) does not change. The untrained one does.

**It survives the strongest available control.** Force the identical transgressive word into both arms and the scene becomes identical by measurement -- same rate of sex, same rate of consummation, same rate of leaving the frame -- while the guilt is still added, **+5.0 points on X_metonymy §3g's own scene, p=7.2e-08**. So the moralisation is not a by-product of alignment selecting milder words.

## Why it belongs in this subject

It is a claim about TEXT, not about a next-token distribution: what kind of sentence the model writes once it is already inside a scene. That puts it beside `../interiority_in_passages/` (alignment changes how much inner life there is, not how it is represented) and against `../predicting_aligned_text/`, whose inherited I6 says the page-grain signature is TONIC -- a constant register shift rather than a site-conditional deployment.

**Those two are in tension and the tension is worth keeping visible.** I6 found transgressive sites drag both arms equally (DiD p=0.90) on the M01 twins. Y finds a site-conditional moral response on sexual scenes that survives a forced-word control. They are different instruments on different corpora and both could be right -- guilt-attachment is not the axis I6 measures -- but nobody has put them on the same passages, and that is a real question rather than a bookkeeping one.

## What does not run from here

`y_diegetic.py` reads `y_confirmatory_coded.jsonl`, **143.9 MB**, which is nearly double this repo's 75 MiB commit cap and stays in the archive along with the gigabytes of raw passage shards behind it. So this folder reproduces the ANALYSIS and not the CODING. The pilot codings are here and are what a reader can check the shape against. See `PROVENANCE.md`.
