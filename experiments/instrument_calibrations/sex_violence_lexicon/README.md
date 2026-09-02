---
id: sex_violence_lexicon
kind: calibration
question: "Can a blind LLM panel build a sexual/violent lexicon that covers the transgressive vocabulary in the twp corpus -- including the low-frequency vulgar tail -- at a *measured* false-positive rate and a *measured* miss rate?"
status: "BUILT AND ADMITTED, 2026-08-16. Lexicon sha `d542e7e2bb86bd00`, 1,063 words (394 sexual, 655 violent, 14 both). Cite by sha."
headline: "The design worked, and the audit says where it does not."
---

# sex_violence_lexicon

**Question.** Can a blind LLM panel build a sexual/violent lexicon that covers the transgressive vocabulary in the twp corpus — including the low-frequency vulgar tail — at a *measured* false-positive rate and a *measured* miss rate?

**Status: BUILT AND ADMITTED, 2026-08-16.** Lexicon sha `d542e7e2bb86bd00`, **1,063 words** (394 sexual, 655 violent, 14 both). Cite by sha.

## Result

| | |
|---|---|
| inter-rater reliability | **Fleiss κ = 0.929**, 135/150 anchors unanimous across all 15 raters |
| false-positive rate | **≤ 0.23%** (2/856 hidden controls) — gate was 5%, passed by 20× |
| miss rate | **0.34%** (2/596 audit) → ~236 estimated misses in the 70,391-word non-adjacent remainder (Poisson 95% ≈ 29–853) |
| supplied vs found | 14 of 1,063 admitted words were seed words we handed the panel |

**The design worked, and the audit says where it does not.** The two misses it found are `uncircum` (8 cells, a fragment) and `fvck` (1 cell, leetspeak). That is the blind spot of generate-then-verify stated precisely: an agent asked for vulgar terms produces `cunt` and `horny`, and does not think to produce deliberate misspellings or subword fragments. Both misses sit at the extreme rare end (1 and 8 cells), so the mass they carry is negligible — but a future build that wants them should scan the corpus for obfuscations rather than ask a model to imagine them.

**Two limits, declared in `registration.md` rather than discovered by a reader.** A control positive cannot be distinguished from a recall miss, so 0.23% is an upper bound (both control positives — `warworn`, `hitlist` — look genuinely violent on inspection, which would make the true FP rate 0). And 4,659 stem-adjacent words were never eligible for the audit, so the miss estimate covers the non-adjacent remainder only.

**Why it exists.** Every instrument already in `malignment/fields.py` is blind somewhere on this corpus, and each is blind differently: `cock` is absent from RID and the General Inquirer and read by USAS as a bird and a weapon; `stabbed` returns `gi=[]`; `k_ratings_en`'s `vulgarity` has variance on 1.7% of its words, so its zeros are a floor. The build is a response to a specific observed failure and `registration.md` records that, along with the exclusion it forces.

**Design in one line.** Generate then verify, not label-a-sample — because the words this instrument exists to catch are exactly the rare ones (`cunt` 137 cells, `maim` 132, `horny` 33), so any frequency cut selects against the target, and the uncut vocabulary is 224,919 words.

    A generate   8 blind agents, no corpus access        workflows/generate.md
    B intersect  keep what twp_words actually holds      run.py --stage assemble
    C expand     inflections present in the corpus       run.py --stage assemble
    D rate       3 raters per item + shared anchor block workflows/rate.md
    E audit      random remainder sample, same panel     run.py --stage score

Controls and audit items are mixed into the stage-D stream with `kind` stripped, so a rater cannot tell a candidate from a random word. That is what turns "the lexicon looks good" into a false-positive rate.

**The gates are declared, not chosen after.** Admission is ≥2 of 3 raters; a control false-positive rate above 5% means the lexicon is **not admitted** rather than retuned. `cock` and `stabbed` motivated the build, so they are flagged `burn_in` and barred from being cited as confirmation — but nothing is subtracted from any denominator on their account, because a generator-proposed word never reaches the control or audit pool in the first place. See `registration.md`.

**Scope.** English only. 97,804 of the 224,919 corpus words are pure `[A-Za-z]+`; the rest is largely CJK, and this instrument is blind on it by construction. Anything downstream must report the unlabelled share per family.

**Not in this directory.** Whether SFT represses sexual more than DPO represses violent. That is a different question with its own registration, kept apart so the instrument cannot be tuned toward it.
