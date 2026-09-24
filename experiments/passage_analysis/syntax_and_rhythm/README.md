---
kind: question
subject: syntax_and_rhythm
question: Does alignment change the syntax and rhythm of narrative prose, or only its content?
status: |
  RUN 2026-09-24. Registered LIGHT (registration.md, amendments A1-A2). 3,089 pure stories, 34 paired lineages. H1b and five of six H3 supported; H1a, H2a, H2b not; the draft's *s/unstressed measure goes against H2 (31/34). Sensitivities (a)-(c) run; (b), no judge filter, 37 lineages, holds and adds H3c.
grain: sentence, window, passage
headline: "Alignment makes clauses more uniform and prose less metrical, and pushes verse toward canonical iambic pentameter."
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

**Sensitivity.** (c) lineages with ≥ 10 pure stories per arm (27 lineages): the same results; H1b 23/27, H3 22–25/27 on the five supported. (a) the no-demonym control only (378 passages, about 7 per arm per lineage): H3b, H3d, H3e and H3f hold; H1b does not reach significance. (b) no judge filter: every parsed passage, 6,877 of them (3,739 base, 3,138 aligned), including essays, incoherent, repetitive and drifting texts, and all 37 lineages. Nothing reverses: H1b 31/37 (Holm p = 0.0002); all six H3 predictions hold, H3c included (26/37, Holm p = 0.02); H2 stays null; `*s/unstressed` still goes the other way (33/37). The judge filter removes far more base text than aligned (it is arm-asymmetric), but the results do not depend on it. One incoherent SmolLM2 passage failed with a RecursionError in prosodic's phrasal-stress tree and is recorded as an error row.

## Exploratory: verse, and history

Not registered. Added 2026-09-24 at RH's request. See `figures/meter-map.html`, from `plot.py`.

**Verse baselines** (`parse_verse_baselines.py`, `by_window_verse.csv`): the same window protocol over RH's *Generative Aesthetics* data (JCA 10.3, 2025). The key set is the continuations: base against instruct models continuing the same human poems after their first five lines (Llama-3.1-8B text/instruct and Mistral-7B text/instruct, 4-bit via ollama), with the poet's own continuation of the same lines. In every period, both model types continue a poem more metrically than its poet did, by about 1–3 MTS. They loosen for 20th-century poems but stop around 18th/19th-century human levels. Base and instruct have nearly identical tension throughout (MTS 4.75 and 4.70, poets 6.46), but instruct has lower metrical uncertainty (2.58 against 2.89; Wilcoxon p < 1e-4 in both pairs) and writes more canonical iambic pentameter (below).

**History** (the antimetricality reparse, 1600–1999, by 50-year period; prose dated by publication year, verse by author_dob + 30): base prose (MTS 9.42) is more metrical than human fiction in every period (10.1–11.6). Aligned prose (11.01) sits at fiction's high end and toward non-fiction. The prose-minus-verse tension gap is about 4.7 for base models and 6.3 for aligned ones. The human gap was largest in 1700–1749 (6.4) and fell to 0.8 by 1950–1999. On this measure alignment restores the verse/prose opposition of the early eighteenth century, from the prose side only.

**Canonical iambic pentameter.** uIP is the share of windows whose best parse is `wswswswsws` AND is the only viable scansion; puIP additionally requires zero violations. Human poetry peaks in 1700–1749 (uIP 28.8%, puIP 19.3%) and falls to 4.8% and 2.8% by 1950–1999; Pope's verse is 34.4% and 23.8%. Human prose is flat across four centuries (fiction 3.1% and 1.6%). In **prose**, uIP does not differ between base and aligned models (2.6% and 2.75%, both slightly below human fiction), but aligned prose has FEWER perfect pentameters (puIP 1.62% → 1.46%, lower in 25/34 lineages, sign p = 0.009). Base prose's pentameters are unusually clean: 62% of them are perfect, a verse-like share (human poetry 67%, fiction 52%). In **verse**, alignment raises canonical pentameter. Paired by poem against the poets' own continuations:

| tier | model | uIP % (poets) | puIP % (poets) |
|---|---|---|---|
| base | Llama-3.1-8B text | 13.1 (14.8) | 9.9 (9.9) |
| base | Mistral-7B text | 11.5 (15.2) | 8.8 (10.0) |
| open aligned | Llama-3.1-8B | 17.2 (14.8) | 11.9 (9.9) |
| open aligned | Mistral-7B | 16.3 (15.1) | 12.2 (10.0) |
| open aligned | OLMo-2 | 17.0 (15.4) | 11.7 (10.1) |
| API | GPT-3.5 | 16.2 (15.1) | 11.4 (10.2) |
| API | Claude-3-Sonnet | 26.8 (15.1) | 18.7 (10.1) |
| API | DeepSeek-chat | 29.8 (15.1) | 22.8 (10.4) |

Within the Llama and Mistral pairs, instruct exceeds base on both measures (Wilcoxon p ≤ 6e-5). Claude-3-Sonnet and DeepSeek write canonical pentameter at the 1700–1749 peak, approaching Pope (puIP p < 1e-34 against their poets). GPT-3.5 does not differ from the poets. The tiers are different model families, not stages of one model: only base → open aligned is paired within a model. Prompted poems order the same way: API models write more canonical pentameter than open aligned models under every prompt, most under "rhyme" (puIP 12.7% vs 8.0%). The API-tier and OLMo-2 completions were parsed with `parse_verse_baselines.py --tiers`.

**Original, within-POS scramble, full scramble (O/R/S).** Every text is measured as written (O), with its content words permuted within their part of speech so the syntactic frame is kept (R, `shuffle_pos`), and with all content words permuted (S, `shuffle_all`). O − R is the metrical work done by the writer's placement of words beyond the frame; (S − R)/(S − O) is the share of O's advantage over S that the frame alone supplies. The human texts are the antimetricality small data's LSA set, whose R and S were checked against the texts on 2026-09-24. R keeps the original's POS-sequence dependence (bigram MI 0.42–0.59 against 0.61–0.73 for O) and almost never produces function-word pairs like "the of" (0.3–1.4 per 1,000), while S destroys both (MI ≈ 0.02, 6–33 per 1,000). So R is the within-POS scramble and S the full one. LLM verse scrambles were parsed with `parse_verse_baselines.py --scramble`. Tension (MTS):

| text | O | R | S | O − R | frame share | uIP % O / R / S |
|---|---|---|---|---|---|---|
| Shakespeare (verse) | 5.22 | 10.99 | 11.66 | −5.78 | 0.10 | 20.4 / 4.0 / 1.1 |
| LLM verse, API | 5.04 | 10.71 | 12.47 | −5.67 | 0.24 | 25.3 / 4.6 / 2.1 |
| LLM verse, open aligned | 6.07 | 11.40 | 13.02 | −5.34 | 0.23 | 17.0 / 3.8 / 2.1 |
| poets' continuations | 6.53 | 11.04 | 12.46 | −4.51 | 0.24 | 16.5 / 3.5 / 2.1 |
| LLM verse, base | 4.76 | 7.96 | 9.71 | −3.20 | 0.35 | 12.7 / 3.6 / 1.7 |
| Dickens (fiction) | 9.08 | 11.52 | 12.53 | −2.44 | 0.29 | 3.8 / 2.3 / 1.4 |
| Dibble (utility prose) | 9.60 | 10.60 | 11.95 | −1.00 | 0.57 | 2.6 / 2.8 / 2.0 |
| Browne (art prose) | 10.84 | 11.60 | 13.87 | −0.76 | 0.75 | 4.4 / 3.0 / 2.8 |
| Ruskin (art prose) | 11.28 | 12.03 | 12.97 | −0.75 | 0.55 | 2.5 / 2.6 / 2.4 |
| LLM prose, base | 9.42 | 9.97 | 11.23 | −0.54 | 0.70 | 2.6 / 2.5 / 1.9 |
| LLM prose, aligned | 11.01 | 11.41 | 12.46 | −0.40 | 0.72 | 2.75 / 2.7 / 2.15 |
| Pater (art prose) | 11.26 | 11.49 | 13.25 | −0.23 | 0.88 | 3.6 / 2.1 / 2.2 |

In **prose**, base models sit at Dibble's level of tension, and aligned models at Pater's and Ruskin's. Both get their metricality mostly from the frame (0.70), as art prose does, not from Dickensian placement. Alignment reduces what little metrical placement there is (window-pooled here, −0.54 → −0.40; lineage-averaged, −0.61 → −0.33, aligned higher in 22/34, Wilcoxon p = 0.03).

In **verse**, the tiers separate on WHERE their meter comes from. Base models' verse is the most regular as written (4.76), but much of that survives shuffling within POS: R = 7.96, against 10.7–11.4 for every other verse source. So it lives in the vocabulary and frame (many monosyllables: 7.4 per window, against 6.3 for the poets). Open aligned and API models, like the poets and Shakespeare, get their meter from placement: shuffling within POS destroys it. By O − R, the API tier (−5.67) is nearly Shakespeare's (−5.78) and beyond the poets they continue (−4.51). Alignment moves verse meter from the words chosen to the way the words are placed.

The human side is one text per author, so these are points without error bars. The LLM verse tiers are pooled across different model families.

**Prompted poems** (all 16,980 in `genai_rhyme_promptings`, parsed with `--prompted-all`, scrambled with `--scramble`). These are poems written on request: `DO_rhyme` (e.g. "ballad stanzas", "heroic couplets"), `MAYBE_rhyme`, the neutral bucket ("Write a poem."), and `do_NOT_rhyme` (e.g. "that does NOT rhyme", "in blank verse"). There are no base models (a base model cannot follow "write a poem") and no poets' baseline. So there are two tiers, open aligned (Llama-3.1 8B/70B, OLMo-2 7B/13B, an OLMo-7B instruct, DeepSeek-R1-8B, two llama2-uncensored) and API (Claude-3 Haiku/Sonnet/Opus, GPT-3.5, GPT-4, Gemini-Pro, DeepSeek-chat), × three prompt types. "No metre prompts" drops the blank-verse, sonnet, couplet and pentameter prompts.

| tier | prompt | poems | uncertainty | tension | uIP % | puIP % | O − R (uncertainty) |
|---|---|---|---|---|---|---|---|
| open aligned | to rhyme | 3,184 | 2.70 | 5.72 | 13.9 | 9.0 | −1.48 |
| open aligned | neither | 1,846 | 2.95 | 6.90 | 10.9 | 6.7 | −1.31 |
| open aligned | not to rhyme | 3,172 | 3.67 | 9.50 | 8.1 | 4.9 | −0.68 |
| open aligned | not to rhyme, no metre prompts | 2,780 | 3.80 | 9.98 | 6.1 | 3.8 | |
| API | to rhyme | 2,827 | 2.75 | 6.28 | 16.8 | 12.2 | −1.46 |
| API | neither | 2,059 | 3.25 | 8.51 | 9.6 | 6.5 | −1.07 |
| API | not to rhyme | 3,891 | 3.43 | 8.73 | 10.5 | 6.5 | −0.87 |
| API | not to rhyme, no metre prompts | 3,550 | 3.55 | 9.17 | 8.5 | 5.2 | |

On uncertainty, poems prompted to rhyme land at an 18th-century level (human poetry: 1700–1749 2.44, 1750–1799 2.67). Poems prompted not to rhyme land between 1900 (3.25) and 1950 (3.84), the free-verse level. The tiers do NOT differ once models are the unit. Pooled over poems, the neutral bucket seems to separate them (open aligned 2.95, API 3.25), but that is composition: Llama-3.1 8B/70B are very metrical (2.35–2.40) and Claude-3 Sonnet/Haiku very unmetrical (4.06–4.30). Across models, the tier medians are equal (uncertainty 3.35 vs 3.41; uIP 8.99% vs 8.95%). The differences are model-specific, and they are clearest for the same model in both settings. Claude-3-Sonnet continuing a traditional poem writes more canonical pentameter than any model but DeepSeek (uncertainty 2.60, uIP 26.8%); asked to "Write a poem." it writes the least metrical verse of any model (4.30, 5.5%). GPT-3.5 (3.03 → 3.45) and OLMo-2 (2.94 → 3.40) loosen the same way, less sharply. DeepSeek (2.23 → 1.70, uIP 20.6% unprompted) and Llama-3.1-8B (2.54 → 2.35) are metrical by default. So for some models canonicity comes with the task of continuing a traditional poem, and for others it is the default. Across models the placement effect goes with metricality: DeepSeek −2.25, Llama-3.1 −1.87, Claude-3-Opus −1.86, down to Claude-3-Haiku −0.36 and Claude-3-Sonnet −0.43 on uncertainty. Poem-level tier tests are not reported: poems are nested in models. Metrical-form prompts raise canonical pentameter where present (API "to rhyme" uIP 16.8% with them, 11.4% without). The placement effect (O − R) is largest when rhyme is requested and smallest when it is refused, in both tiers. These are descriptive levels: prompted poems have no paired baseline, and the prompt mix differs across models (e.g. Gemini-Pro wrote 1,184 "not to rhyme" poems and 48 "to rhyme").

**Rewind to the Augustans, by the period of the poem continued** (`rewind_primers.py`, `plot.py`; lead section of the figure page). Every continued poem is dated (author_dob + 30). Uncertainty of continuations against human poetry of each period (reparse: 1700–1749 = 2.44, the minimum since 1600):

| poems from | human poetry | poets' own continuation | base | aligned | API (Claude-3-Sonnet, DeepSeek) |
|---|---|---|---|---|---|
| 1600–49 | 2.88 | 3.04 | 2.90 | 2.41 | 2.07 |
| 1650–99 | 2.77 | 2.89 | 2.71 | 2.42 | 2.10 |
| 1700–49 | 2.44 | 2.60 | 2.60 | 2.41 | 2.15 |
| 1750–99 | 2.67 | 2.55 | 2.62 | 2.36 | 2.20 |
| 1800–49 | 3.09 | 2.99 | 2.67 | 2.45 | 2.28 |
| 1850–99 | 2.92 | 2.75 | 2.71 | 2.36 | 2.14 |
| 1900–49 | 3.25 | 3.26 | 3.14 (≈ 1800–49) | 2.65 (≈ 1750–99) | 2.64 |
| 1950–99 | 3.84 | 3.80 | 3.43 (≈ 1900–49) | 3.10 (≈ 1800–49) | 3.23 |

The poets' own continuations stay near their time; for 20th-century poems they land on their own period. The models do not. Given a modernist poem, the base models already continue it about as regularly as a Romantic poet, and the aligned models as regularly as a poet of the late eighteenth century. Alignment's own contribution is the increment, about 50 years for 1900–49 poems and 100 for 1950–99. Given an older poem, the aligned models bring it to about the regularity of Augustan verse whatever its period. That holds for the two pairs pooled and for Llama; Mistral's aligned verse runs 2.39–2.68 before 1900 and sits above its base in 1800–49. Base and aligned are the Llama-3.1-8B and Mistral-7B pairs on the same 1,780 poems. The step is significant within each pair over all periods (Llama p = 2e-21, Mistral p = 2e-5); per-row differences are not separately tested. Before 1800 the human scale is not monotonic, so for earlier poems the reading is "at the Augustan level", not a number of years.

Against each poem's own 5-line primer (the lines the model was shown; `--primers`; `results/primer_deltas.csv`), the poets' continuations are about as metrical as their openings (Δ uncertainty ≈ 0). Base models make the continuation more determinate (−0.21, −0.36) and drop the opening's pentameter (uIP −2.7, −3.2). Aligned models do more (−0.57, −0.60) and add pentameter (+1.2). DeepSeek (−0.88; uIP +11.4) and Claude-3-Sonnet (−0.43; +8.7) do the most; GPT-3.5 behaves like the poets. Two attempts to express the rewind as a number of years are recorded in `results/`, for completeness. (1) A lookup against the poets' own curve is censored: for aligned and API models, in 75–88% of source periods no human period back to 1600 is as metrical. (2) A cross-fitted metrical dating model dates human verse poorly (R² 0.17, MAE 85 years; O/R/S features add little), so its "metrical years" (aligned 14–17, base 5–10, DeepSeek 13, GPT-3.5 −7 to −9) give the ordering, not a scale.

**Caveats.** Verse and prose come from different prompts and generation setups (4-bit ollama models for verse, full-precision HF generation for prose). The Olmo-3 base/SFT verse pilot (malign-logits `rhyme_pilot`, 12 primers) is on the page but is never quoted as a result. No sampled verse exists at pretraining checkpoints. National_story's `load_raw` deduplicates only within a (lineage, arm, demonym) cell: 60 texts recur under two demonyms. They are counted once here, and that folder's own per-demonym counts are affected.

## Method and files

**Producers:** `parse_passages_prosodic.py` (prose), rather than LAYOUT's `run.py`: LAYOUT records that naming rule as unresolved and broken in 30 of 52 directories, and RH chose this name. `parse_verse_baselines.py` (verse, exploratory). **Analysis:** `analyse.py` (registered tests), `plot.py` (the figure).

**Instrument:** [prosodic](https://github.com/quadrismegistus/prosodic) with `keep_parse=True` (PR #194), a spaCy dependency parse that feeds Liberman & Prince phrasal stress, plus prosodic's metrical parser run on 10-syllable windows. It follows the antimetricality protocol (Heuser, Kiparsky & Anttila, draft Aug 2026) so windows sit beside the human baseline `data.2026.reparse.big_data.parquet` (468,066 lines). Full definitions are in the producer's docstring; every row carries `instrument: syntax_and_rhythm-v1`.

**Scrambles:** each passage is also measured with its content words permuted within POS class (`shuffle_pos`) and across the passage (`shuffle_all`). Punctuation stays fixed and the original's sentence boundaries are imposed, so sentence lengths are identical. `orig − scramble` separates arrangement from word choice.

**Outputs:**

    results/by_lineage.csv                                   lineage x arm means       tracked
    results/tests.csv                                        every test, per population tracked
    population.json                                          receipt: rule, ids, exclusions, prosodic sha
    figures/meter-map.html, meter_points.json                the figure and every plotted value
    ~/malignment-data/syntax_and_rhythm/by_passage.csv       (id, version)             no text; moved out of git 2026-09-24 at 6,878 x 3 rows
    ~/malignment-data/syntax_and_rhythm/by_sentence.csv      (id, version, sent_idx)   H1's grain
    ~/malignment-data/syntax_and_rhythm/by_window.csv        (id, version, win_idx)    H2's grain, carries window text
    ~/malignment-data/syntax_and_rhythm/by_window_verse.csv  (source, model, arm, poem, win_idx)

**Environment:** prosodic is *not* a malignment requirement. It runs from `.venv-prosodic` (gitignored), which keeps it out of the shared measurement `.venv`: `run_v4.py` freezes that venv's contents into ENV.json beside every twp cell. To build it:

    uv venv -p 3.11 .venv-prosodic
    uv pip install -p .venv-prosodic/bin/python -e ~/github/prosodic pyyaml ruamel.yaml hashstash scipy pyarrow "spacy==3.8.15"
    uv pip install -p .venv-prosodic/bin/python --no-deps -e .
    .venv-prosodic/bin/python -m spacy download en_core_web_sm

If prosodic, spaCy or `keep_parse` is missing, the producer says so and exits. The prose run takes about 50 min at 6 CPU workers and needs no GPU.

**Population:** national_story's own, imported rather than retyped: `analyse.load_raw(min_words=150, drop_escapes=True)` restricted to `_paired` lineages. As of 2026-09-24 that is 37 lineages and 6,938 texts (6,878 unique), not the 21 in national_story's README; the stash has grown since that run. Judge labels are joined by `md5(text)[:12]`. Per amendment A1, the 3,089 pure stories were parsed first; the rest were then parsed with `--subset all` for sensitivity (b), so all 6,878 unique texts are measured. Any prefix of the outputs is a random sample, and a failed passage is a row with `error` set, never an absence.
