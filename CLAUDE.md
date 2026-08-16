# CLAUDE.md — for a seat working in this repo

Read [`README.md`](README.md) for what this is, then
[`docs/HOWTO.md`](docs/HOWTO.md) for how to ask anything. **This file is only the
things that are not obvious from the code and that have cost something.**

---

## Before you write a query, check whether the question already has one answer

`docs/HOWTO.md` exists because *"how do I get base→endpoint pairs among
representatives"* was answered three different ways by three seats, and then four
more times in one afternoon by one seat, in shell heredocs, with a
case-sensitivity bug that silently found 4 of 6 OLMo lineages.

**If you find yourself writing SQL in an experiment, stop.** It belongs in
`malignment/corpus.py` or `malignment/wordfield.py`. The second copy is always
the one without the docstring — that is not a prediction, it is what happened to
`panel()` within hours of it being written.

## Read the artifact before reporting on it

Most of the day's wrong turns share one shape: a check that did not consult the
thing it was checking.

- `attest --promote` reported edges as "proposed new" without diffing
  `models.yaml`. Two of them had been declared for weeks.
- The same tool read **one** `method` claim where the attestation carried two,
  and reported a disagreement its own data resolved.
- I called a measurement unattributable while `twp_cells.revision` held the
  answer and `models.yaml` carried a comment written to pre-empt exactly that
  objection.

**Before saying a thing is missing, open the file that would hold it.**

## Absence is not evidence, and neither is a name

`direction: unknown` on 19 checkpoints did not mean "checked and standard"; it
meant nobody had looked, and four inverted models were found the first time
anyone did. A model named `uncensored` is a hint to go looking, never the
evidence. `aligned` in a corpus name often means *sentence-aligned parallel
text*.

**And the card is frequently not where the answer is.** `dolphin-2.6`'s
inversion lives in `configs/dolphin-dpo.yml` — `unalignment/toxic-dpo-v0.1`,
`type: toxic_apply_chatml` — and appears in neither the README nor the HF tags. A
later pass read three URLs, missed the file list, and reached the right verdict
with the wrong mechanism.

## A guard that cannot be shown to fire is not a guard

`roster.endpoints()` filters `direction: inverted`. It is **unreachable**: two
other rules mask it, and no current lineage exposes it. That is recorded in
`docs/HOWTO.md` rather than quietly enjoyed, and `test_howto.py` asserts the
unreachability so a future roster that *does* expose it breaks the test.

The same class, twice more: a burn-in exclusion that removed words from
denominators they were never in, and a `MIN_WORDS` threshold that no chain could
meet because a cell holds ~1 sexual word.

**When you add a check, construct the case where it fires.**

## Statistics

- **A null is quotable only as a bound.** `paired_stats` returns a bootstrap CI;
  `sign_mde` says what the test could have seen. A sign test at n=16 needs 13/16,
  so `p=0.45` on an effect of 0.089 reports the instrument, not the world.
- **The unit is the lineage.** 18 chains are 16 bases; chains sharing a base are
  not independent.
- **Ties are dropped from sign tests, never split.**
- **Report the population with the number.** `population.json` is a generated
  receipt so a population change is a git diff.

## Registrations

`experiments/README.md` holds the layout rules and the hypothesis register — the
table of every registered hypothesis and its status. **Update it in the same
commit as a new registration**, or the separation between instrument and
hypothesis registrations becomes scattering.

**Agree the CONTRAST and the BASELINE with RH before freezing.** Registration
binds a design; it cannot tell you the design answers the question. `lexical_domains`
was honestly pre-committed and still measured the wrong quantity — a symmetric
divergence, normalised by a path length that never touched the stage being
attributed.

## Editing the roster

`models.yaml` is **hand-edited, text only**. Never `yaml.safe_dump`. Run
`roster.check_authored()` afterwards — the strict parse found a duplicate `note:`
key that `safe_load` had been silently resolving, hiding the fact that MPT's
weights had been recovered from mirrors.

New attestations go through `attest.merge_claims()`, not `ingest()`: `ingest()`
replaces a whole checkpoint entry and would drop seven fields from a targeted
pass.

## Working with RH

- Do ordinary work; say plainly when something is wrong, then keep building.
- **Never `git add -A`** — stage by name.
- Cloud or API spend begins only on RH's explicit word.
- No session links in anything that leaves this machine.
- When RH questions a number, check the file before defending it. On the day this
  file was written, every one-line challenge — *"2 root demotions?"*, *"I thought
  we already changed the vague instructs"*, *"we only have 97 models?"* — was
  answered by a file that had not been opened.
