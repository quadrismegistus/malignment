# malignment

On the Psychopathology of Everyday AI

---

Comparing full-vocabulary probability distributions across the alignment
pipeline — base → SFT → preference → RLVR — to ask what post-training does to
the words a model was willing to say.

**This is v3.** `~/github/malign-logits` is the archive: read-only, 144 GB, still
the source of the twp corpus. This repo exists because that one reached 477
scripts and 46 findings, 42 of them cited by nothing, and *"nobody knows how our
own repository works"*.

## Start here

| you want | read |
|---|---|
| **how do I do X** | **[`docs/HOWTO.md`](docs/HOWTO.md)** — every snippet is executed by `docs/test_howto.py` |
| what an experiment must look like | [`experiments/README.md`](experiments/README.md) — and its hypothesis register |
| how results are stored | [`RESULTS.md`](RESULTS.md) |
| what crossed over from the archive and why | [`MANIFEST.md`](MANIFEST.md) |

```bash
pip install -r requirements.txt          # three lines suffice to ANALYSE
python docs/test_howto.py                # does the documentation still hold?
```

An analysis machine needs `pyyaml`, `pandas`, `hashstash` and `ruamel.yaml`.
`torch`/`transformers` are for *measuring* only — `Checkpoint` imports no torch,
and `runners` pulls it lazily inside `run_twp()`.

## The four places things live

    malignment/            code + the authored roster        public, git
    ~/malignment-data/twp/ measured jsonl                    private, rsync target
    ClickHouse             the queryable store               derived, rebuildable
    malign-logits/data/    the archive                       READ-ONLY legacy

**This repo is public and holds no measured data.** A twp jsonl carries its
prompts verbatim, transgressive battery included. `roster/prompts/` *is* tracked
and public — a stimulus nobody can read is not reproducible.

## Three kinds of claim, three files, three ways to be wrong

    roster/models/models.yaml         AUTHORED   RH's rulings, hand-edited
    roster/models/measurements.json   OBSERVED   scripts reading files or the API
    roster/models/attestations.json   ATTESTED   an agent reading a card, quoted

An observation is wrong when the measurement is wrong. An attestation is wrong
when the source is wrong, or the reader misread it, or — the failure no schema
prevents — the quote was never on the page. Writing them into one file makes the
authored file unfalsifiable: a ruling and a scraped sentence become
indistinguishable a month later.

## The populations, because they are not interchangeable

    50 lineages   base -> endpoint          roster.endpoints()
    18 chains     base -> sft -> preference roster.chains()   (16 distinct bases)
    2,189 prompts crossed over 154 models   corpus.panel()

The chain population is small because it needs a lab to release the **middle** of
its pipeline: 50 declared bases, 30 with a released SFT, 16 with a preference
stage on top. Every claim made on it is a claim about the open-science
subpopulation, and it is biased low.

## Why so much of this repo is comments

Most explain a specific failure, dated, with its cost. `yaml.safe_dump` destroyed
114 comment lines and 16 evidence quotes; a dict keyed on `w.lower()` let `Rape`
overwrite `rape` and made every frequency statement wrong; a guard written for
the model load sat one line below the tokenizer load that actually failed.

**The comment is there so the next reader does not pay again.** A rule whose
reason lives in another file is a rule someone deletes.
