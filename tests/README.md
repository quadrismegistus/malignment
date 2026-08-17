# tests/ — the discipline, before the tests

    python -m pytest tests/ -q          # everything
    python docs/test_howto.py           # the published numbers, separately

**Every test in here has been shown RED against a named commit or a constructed
case, and the receipt is in the test's own docstring.** That is not a style
preference. This campaign's recurring failure is not an untested code path, it is
**a checker that reads clean** — and a `tests/` directory full of green that has
never been red is worse than no directory, because it converts an unexamined
repo into an examined one on no evidence.

Three of those in one week, all found by something other than a test:

    _guard                      documented in a comment, never written. dario
                                found it by reading, not by running.
    repetition detector         a 20-char-window test read 3.6% max across the
                                roster and 0.8% on a model whose true rate is 79%.
    avgIf(1, cond)              averages the constant 1, so every row read
                                100.0% and the table looked uniform.

So: **no test is added here without a demonstration that it fails when the thing
it checks is broken.** If the defect is historical, name the commit and assert
against it. If it is not, construct the broken input inline.

## What belongs here, in the order the record says it matters

**1. CROSS-TIER INVARIANTS.** The roster has three trust tiers — AUTHORED
(`models.yaml`), OBSERVED (`measurements.json`), ATTESTED (`attestations.json`)
— and until now **nothing read any of them against another**. `attest.unsourced()`
checks attestations against themselves. That gap is where the fabricated stablelm
edge survived: the refutation was in the repo, quoted, twice, on both arms.

**2. DERIVED-STORE FRESHNESS.** `{db}.pairs` was stale for a day after
`distill_align` and the row count stayed plausible the whole time (146 was as
believable as 151). Counts do not detect staleness; recompute-and-diff does.

**3. KNOWN-POSITIVE FIXTURES FOR DETECTORS.** See the three failures above.
`generation_check.py --run` now gates on `--validate`; `slot_axis` check 3b builds
a sign-disagreement case and requires the flag to fire.

**4. PURE FUNCTIONS WHOSE WRONG ANSWER IS SILENT** — the arithmetic identities.
Genuinely worth asserting, and the least likely to be wrong. Last, not first.

## What does NOT belong here

Coverage of the 10,000+ lines of producers that talk to ClickHouse and GPUs.
Mocking those buys nothing and manufactures exactly the green control the record
keeps punishing. A producer is tested by running it and checking what it WROTE.

## Where the guard should actually live

**A test nobody runs is not a guard, and there is no CI here.** Tiers 1 and 2 are
therefore also called from the producers — `roster.check_derived()` runs inside
`roster --write` — so the refusal happens at the moment the wrong state would be
created, not at the moment somebody remembers to run pytest.
