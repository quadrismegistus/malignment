---
kind: question
subject: syntax_and_rhythm
question: Does alignment change the syntax and rhythm of narrative prose, or only its content?
status: |
  RUN 2026-09-24. Registered LIGHT (registration.md, amendments A1-A2). 3,089 pure stories, 34 paired lineages. H1b and five of six H3 supported; H1a, H2a, H2b not; the draft's *s/unstressed measure goes against H2 (31/34).
grain: sentence, window, passage
headline: "Alignment makes clauses more uniform and prose less metrical, and leaves verse meter where it was."
---

# syntax_and_rhythm: syntax, stress-grid rhythm and meter of base vs aligned prose

**Question.** Does alignment change *how sentences are built and how they sound*: dependency structure, head direction, Liberman & Prince stress-grid well-formedness, metrical uncertainty and tension? Or does it leave form alone and move only content (national_story: *"alignment installs the resolution, not the problem"*)? The hypotheses are in [`registration.md`](registration.md), a LIGHT registration. RH does not treat registrations as binding on what is reported; that file records what was declared before the data was seen.

## Results (registered)

Unit = lineage; aligned minus base; exact sign test, Holm within family. Population: judge `overall == story` AND `pure_story`, 3,089 passages (1,538 base, 1,551 aligned), 34 lineages with both arms (Teuken-7B, Tanuki-8B and RedPajama-7B have no pure base stories). Full table: `results/tests.csv`, from `analyse.py --write`.

| | prediction (aligned) | lineages in direction | Holm p |
|---|---|---|---|
| H1a stress-grid clash rate | lower | 17/34 | 1 |
| **H1b beat-interval CV** | lower | **28/34** | **0.0008** |
| H2a metrical uncertainty | lower | 15/34 | 1 |
| H2b metrical tension (MTS) | lower | 13/34 | 0.69 |
| **H3a relative clauses** | higher | **28/34** | **0.0006** |
| **H3b dependents before head** | lower | **32/34** | **4e-7** |
| H3c dependency distance | lower | 22/34 | 0.12 (Wilcoxon 0.01) |
| **H3d adverbs** | lower | **31/34** | **4e-6** |
| **H3e phrase-length CV** | lower | **27/34** | **0.002** |
| **H3f sentence-length CV** | lower | **31/34** | **4e-6** |

**Declared secondaries.** Against H2, the draft's own measure: the share of windows with any `*s/unstressed` tension is HIGHER in aligned prose in 31/34 lineages (p = 7.7e-7, monosyllable-stratified). On the grid, aligned prose alternates more (`alt2` higher 29/34) and lapses less (23/34), but clashes MORE at the primary-stress level (25/34) and the phrasal level (27/34). Stress density does not differ. The grid difference is word choice rather than order: a within-POS scramble leaves every lexical grid measure unchanged in both arms. Word order makes prose more metrical than its scramble in both arms, but less so for aligned models (MTS arrangement effect: aligned higher in 22/34, Wilcoxon p = 0.03).

**Sensitivity.** (c) lineages with ≥ 10 pure stories per arm (27 lineages): the same results; H1b 23/27, H3 22–25/27 on the five supported. (a) the no-demonym control only (378 passages, about 7 per arm per lineage): H3b, H3d, H3e and H3f hold; H1b does not reach significance. (b) no judge filter has not been run; it needs `--subset all`.

## Exploratory: verse, and history

Not registered. Added 2026-09-24 at RH's request. See `figures/meter-map.html`, from `plot.py`.

**Verse baselines** (`parse_verse_baselines.py`, `by_window_verse.csv`): the same window protocol over RH's *Generative Aesthetics* data (JCA 10.3, 2025). The key set is the continuations: base against instruct models continuing the same human poems after their first five lines (Llama-3.1-8B text/instruct and Mistral-7B text/instruct, 4-bit via ollama), with the poet's own continuation of the same lines. In every period, both model types continue a poem more metrically than its poet did, by about 1–3 MTS. They loosen for 20th-century poems but stop around 18th/19th-century human levels. Base and instruct are nearly identical throughout (MTS 4.75 and 4.70, poets 6.46), except that instruct has lower metrical uncertainty (2.58 against 2.89; Wilcoxon p < 1e-4 in both pairs).

**History** (the antimetricality reparse, 1600–1999, by 50-year period; prose dated by publication year, verse by author_dob + 30): base prose (MTS 9.42) is more metrical than human fiction in every period (10.1–11.6). Aligned prose (11.01) sits at fiction's high end and toward non-fiction. The prose-minus-verse tension gap is about 4.7 for base models and 6.3 for aligned ones. The human gap was largest in 1700–1749 (6.4) and fell to 0.8 by 1950–1999. On this measure alignment restores the verse/prose opposition of the early eighteenth century, from the prose side only.

**Caveats.** Verse and prose come from different prompts and generation setups (4-bit ollama models for verse, full-precision HF generation for prose). The Olmo-3 base/SFT verse pilot (malign-logits `rhyme_pilot`, 12 primers) is on the page but is never quoted as a result. No sampled verse exists at pretraining checkpoints. National_story's `load_raw` deduplicates only within a (lineage, arm, demonym) cell: 60 texts recur under two demonyms. They are counted once here, and that folder's own per-demonym counts are affected.

## Method and files

**Producers:** `parse_passages_prosodic.py` (prose), rather than LAYOUT's `run.py`: LAYOUT records that naming rule as unresolved and broken in 30 of 52 directories, and RH chose this name. `parse_verse_baselines.py` (verse, exploratory). **Analysis:** `analyse.py` (registered tests), `plot.py` (the figure).

**Instrument:** [prosodic](https://github.com/quadrismegistus/prosodic) with `keep_parse=True` (PR #194), a spaCy dependency parse that feeds Liberman & Prince phrasal stress, plus prosodic's metrical parser run on 10-syllable windows. It follows the antimetricality protocol (Heuser, Kiparsky & Anttila, draft Aug 2026) so windows sit beside the human baseline `data.2026.reparse.big_data.parquet` (468,066 lines). Full definitions are in the producer's docstring; every row carries `instrument: syntax_and_rhythm-v1`.

**Scrambles:** each passage is also measured with its content words permuted within POS class (`shuffle_pos`) and across the passage (`shuffle_all`). Punctuation stays fixed and the original's sentence boundaries are imposed, so sentence lengths are identical. `orig − scramble` separates arrangement from word choice.

**Outputs:**

    results/by_passage.csv                                   (id, version)             tracked, no text
    results/by_lineage.csv                                   lineage x arm means       tracked
    results/tests.csv                                        every test, per population tracked
    population.json                                          receipt: rule, ids, exclusions, prosodic sha
    figures/meter-map.html, meter_points.json                the figure and every plotted value
    ~/malignment-data/syntax_and_rhythm/by_sentence.csv      (id, version, sent_idx)   H1's grain
    ~/malignment-data/syntax_and_rhythm/by_window.csv        (id, version, win_idx)    H2's grain, carries window text
    ~/malignment-data/syntax_and_rhythm/by_window_verse.csv  (source, model, arm, poem, win_idx)

**Environment:** prosodic is *not* a malignment requirement. It runs from `.venv-prosodic` (gitignored), which keeps it out of the shared measurement `.venv`: `run_v4.py` freezes that venv's contents into ENV.json beside every twp cell. To build it:

    uv venv -p 3.11 .venv-prosodic
    uv pip install -p .venv-prosodic/bin/python -e ~/github/prosodic pyyaml ruamel.yaml hashstash scipy pyarrow "spacy==3.8.15"
    uv pip install -p .venv-prosodic/bin/python --no-deps -e .
    .venv-prosodic/bin/python -m spacy download en_core_web_sm

If prosodic, spaCy or `keep_parse` is missing, the producer says so and exits. The prose run takes about 50 min at 6 CPU workers and needs no GPU.

**Population:** national_story's own, imported rather than retyped: `analyse.load_raw(min_words=150, drop_escapes=True)` restricted to `_paired` lineages. As of 2026-09-24 that is 37 lineages and 6,938 texts (6,878 unique), not the 21 in national_story's README; the stash has grown since that run. Judge labels are joined by `md5(text)[:12]`. Per amendment A1, the 3,089 pure stories were parsed, plus 530 other passages parsed before the restriction. Any prefix of the outputs is a random sample, and a failed passage is a row with `error` set, never an absence.
