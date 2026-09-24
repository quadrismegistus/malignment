---
kind: question
subject: syntax_and_rhythm
question: Does alignment change the syntax and rhythm of narrative prose, or only its content?
status: |
  REGISTERED LIGHT 2026-09-24 (registration.md frozen); full run started 2026-09-24, not yet analysed.
grain: sentence, window, passage
headline: "NONE STATED"
---

# syntax_and_rhythm: syntax, stress-grid rhythm and meter of base vs aligned prose

**Question.** Does alignment change *how sentences are built and how they sound*: dependency structure, head direction, Liberman & Prince stress-grid well-formedness, metrical uncertainty and tension? Or does it leave form alone and move only content (national_story: *"alignment installs the resolution, not the problem"*)? The hypotheses are in [`registration.md`](registration.md), a LIGHT registration. RH does not treat registrations as binding on what is reported; that file records what was declared before the data was seen.

**Producer:** `parse_passages_prosodic.py`, rather than LAYOUT's `run.py`. LAYOUT records that naming rule as unresolved and broken in 30 of 52 directories; RH chose this name.

**Instrument:** [prosodic](https://github.com/quadrismegistus/prosodic) with `keep_parse=True` (PR #194), a spaCy dependency parse that feeds Liberman & Prince phrasal stress, plus prosodic's metrical parser run on 10-syllable windows. It follows the antimetricality protocol (Heuser, Kiparsky & Anttila, draft Aug 2026) so windows sit beside the human baseline `data.2026.reparse.big_data.parquet` (468,066 lines, 1600–2015). Full definitions are in the producer's docstring; every row carries `instrument: syntax_and_rhythm-v1`.

**Scrambles:** each passage is also measured with its content words permuted within POS class (`shuffle_pos`) and across the passage (`shuffle_all`). Punctuation stays fixed and the original's sentence boundaries are imposed, so sentence lengths are identical. `orig − scramble` separates arrangement from word choice.

**Outputs, one file per grain:**

    results/by_passage.csv                                  (id, version)            tracked, no text
    ~/malignment-data/syntax_and_rhythm/by_sentence.csv     (id, version, sent_idx)  H1's grain
    ~/malignment-data/syntax_and_rhythm/by_window.csv       (id, version, win_idx)   H2's grain, carries window text
    population.json                                         the receipt: rule, ids, exclusions, prosodic sha

The sentence and window files are about 2M and 3.4M rows over all three versions, which is too large to track here. They are shared measurements for this experiment only.

**Environment:** prosodic is *not* a malignment requirement. It runs from `.venv-prosodic` (gitignored), which keeps it out of the shared measurement `.venv`: `run_v4.py` freezes that venv's contents into ENV.json beside every twp cell. To build it:

    uv venv -p 3.11 .venv-prosodic
    uv pip install -p .venv-prosodic/bin/python -e ~/github/prosodic pyyaml ruamel.yaml hashstash "spacy==3.8.15"
    uv pip install -p .venv-prosodic/bin/python --no-deps -e .
    .venv-prosodic/bin/python -m spacy download en_core_web_sm

If prosodic, spaCy or `keep_parse` is missing, the script says so and exits. The full run takes about 2 h at 6 workers on CPU; it needs no GPU.

**Population:** the national_story finding's own, imported rather than retyped: `analyse.load_raw(min_words=150, drop_escapes=True)` restricted to `_paired` lineages. As of 2026-09-24 that is **37 lineages and 6,938 texts**, not the 21 in national_story's README; the stash has grown since that run. Judge labels (`overall`, `pure_story`, `opens_as_story`) are joined by `md5(text)[:12]` and carried as columns, not filtered on. The no-demonym control is `demonym == ""` (733 texts).

**Order:** fixed-seed shuffle, appended row by row, resumable. Any prefix of the outputs is a random sample of the population. A failed passage is a row with `error` set, never an absence.

## Results

Not run.
