# What already exists on drift, and what it costs to ignore it

RH, 2026-08-18: *"we should definitely save these passages and annotations --
see M06 on drift -- and F13 in original findings dir."* Written before the Pass B
pilot returns so the priors are on record first.

# THE CODED FIELD IS NOT WHAT M06 MEASURED

M06's drift is embedding geometry over sentence vectors. Pass B's `drift` is a
human judgement about referential continuity. They are close enough to be
confused and different enough that confusing them would be a defect.

`meta/M06_generation/findings/drift_metric_audit.md`, four measured defects:

    total_drift = 1 - min(pairwise cosine)     the DIAMETER of the sentence set

**It is ORDER-INVARIANT** -- verified by permutation, identical to four decimals
after shuffling. So no claim about how a passage MOVES can rest on it. Pass B's
`drift` is order-dependent by construction: SHIFTS and UNMOORED differ only in
whether the new material coheres, which a diameter cannot see.

**`directedness` is sentence count.** Spearman -0.923 against n_sents, R^2 0.795
against a bare 1.68/n. The whole apparent ordering of corpora was that abstracts
have 3.7 sentences and diary entries 6.1. Retired.

**Reliability is a property of the (corpus, embedder, truncation) triple, never
inherited.** The famous "92% noise" (ICC 0.082) was one corpus with
`paraphrase-multilingual-MiniLM-L12-v2`; on f11_l2 with `bge-m3` the same
decomposition gives 0.44-0.57. That is the correction, and it is why any
reliability number for a new instrument has to be computed for that instrument.

## THE PRIOR THAT MATTERS: THE SHAPE MEASURE IS NULL BETWEEN ARMS

    ordering = mean(successive distances) - mean(all pairwise distances)

A pure sequence measure -- same sentences, same n, only the order differs, so
composition and length are held fixed by construction. `crosslingual_arms.md`:
**four nulls**, two languages by two truncation regimes, each beside a positive
control. Raw directedness likewise null (zh +0.0099, en +0.0047, 15 up / 10
down, p 0.424).

**So the embedding instruments say alignment does not change how a passage
moves.** Pass B's coded drift should be read against that. A null agrees with
prior work. A positive means the coded field sees something embedding geometry
cannot, and that claim needs the two measured on the SAME passages before it is
worth making.

## DO NOT JOIN TO THE M06 ARTIFACTS BY KEY

`results/crosslingual_drift_en_full_cells.parquet` carries
`(lang, model, prompt, sample_idx)` -- apparently our exact key. It is not.

`scripts/m06_crosslingual_drift.py` selects `model, prompt, text` and **no
sample_idx column**. The field is re-derived:

    line  90   by_cell[(lang, model, prompt)].append(text)
    line 100   v = sorted(by_cell[k])          <- ALPHABETICAL
    line 103   for i, t in enumerate(v):       <- i becomes `sample_idx`

**`sample_idx` is the alphabetical rank of the text within its cell.** A join on
(model, prompt, sample_idx) lands in the right cell and the wrong sample, and
returns a plausible number every time. The artifact also holds 16,002 of ~119k
English passages -- capped and RNG-subsampled -- so reconstructing membership
means replaying a seed through a sort.

**Recompute instead.** bge-m3 over the 190 coded passages is minutes and has no
key to get wrong. That is what made the Pass A / E-ASSIST comparison work: the
machine measure computed on exactly the coded rows.

# F13 IS THE CONCEPTUAL PRECEDENT, AT WORD GRAIN

`findings/F13_jakobsonian_axes.md`. **Status `rescoped`, grade C: "QUANTITIES
NOT QUOTABLE pending registered re-analysis" (docket [399]/[400]).** Direction
survives, numbers do not. Cite the structure, never the correlations.

The structure is a trade-off between Jakobson's two axes when alignment
substitutes a foreclosed word:

    similarity        cosine between contextual embeddings   PARADIGMATIC
    syntagmatic_js    JS divergence of p(next token)         SYNTAGMATIC

    (a) a close substitute exists   "kill" -> "hurt"      the chain holds
    (b) none exists                 "fuck" -> "Options"   the model abandons
                                                          narrative for another
                                                          genre

**F13's `genre_change` is `drift` at word grain.** Its syntagmatic types
(category_shift, genre_change) cluster high on syntagmatic_js; its paradigmatic
types (register_shift, archaic) cluster low. Pass B codes the same distinction
at passage scale, by reading rather than by next-token divergence.

## WHAT THAT PREDICTS ABOUT INTERIORITY

The interiority hypothesis is a substitution claim: alignment puts a represented
state where base puts an enacted action. F13 asks what such a substitution costs
the chain.

    if TOLD interiority is a CLEAN PARADIGMATIC SUBSTITUTION
        aligned TOLD passages HOLD; the swap is invisible at the seam
    if it is a GENRE BREAK
        aligned interiority arrives with SHIFTS, and the mind appears exactly
        where the scene stops

The calibration cannot answer it -- mean degree was 1.08 / 1.07 / 1.33 across
HOLDS / SHIFTS / UNMOORED with UNMOORED at two passages. The 190-passage pilot
gives `mode x drift x arm`, which is the passage-scale form of F13's trade-off
and costs nothing extra: both fields are already in the form.

# STATE OF THE ARTIFACTS

    results/openpass_key.json        192 open-coding passages, keyed o000-o191
    results/open_coding.json           6 readers' proposed dimensions + anchors
    results/passA_key.json           880 pilot passages (ESCAPED text -- see below)
    results/passA_codings.json         2 coders x 880, four fields
    results/frame_exit.parquet    173,360 rows, M02's battery over f11_l2
    results/calib20.json              21 passages, clean text, seed 20260818
    results/calib20_codings.json       6 coders x 21, two rival schemes
    results/passB_pilot.json         190 English Pass A survivors, clean text

**`passA_key.json` holds ESCAPED text** -- literal `\n` in 82.4% and `\'` in
31.4%, no real newlines anywhere -- because it was extracted with
`FORMAT TabSeparated`. Symmetric across arms, so Pass A stands, but nothing
downstream should read text from it. `run.py:fetch_clean()` is the replacement.
