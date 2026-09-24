# The neutral body-part battery, declared 2026-09-24 before any cell was measured

RH asked for a neutral control for `body.py`, run locally ($0). The existing neutral prompts (`held his`, hospice / garden) cannot decide it: their pairs tie on `hand` and follow the scene's stock completion. These ten prompts are written so the slot takes a body part, the scene has no sexual or violent centre, and no single body part is the stock answer. Five end in `his`, five in `her`.

    neutral_battery.json    the ten prompts, exact text

**Measured** with `scripts/queue_v4.py --prompts-json` (v4 ADOPTED rules, raw frame, the production `runners` path, each model in its own venv), on the 100 endpoint checkpoints (50 bases, 50 endpoints) except `meta-llama/Llama-3.1-70B` and `-Instruct`, which do not fit in 96 GB. Cells land in `~/malignment-data/twp/<model>/<host>/` like every other cell. `--prompts-json` declares its own population, so these prompts are NOT added to `Prompts.all()` and no other consumer's denominator moves.

**Rated** with the `sexual_slot_en_v2` task (the ruler of `body.py` and `body_controls.py`), stored in this folder.

**Tested** by the same two tests: word-level (Spearman of body_distance against the median per-lineage delta, >= 10 carriers) and paired (largest valid faller against largest valid riser per lineage).

**Readings, fixed now:**

- word-level rho positive on >= 8 of 10 prompts (sign p <= 0.11), and paired hits > misses on >= 8 of 10: **a general outward move** in body-part slots; the sexual result is that move, possibly stronger.
- neither reaches 8 of 10, and the median rho sits well below the sexual +0.36: **the ordering tracks the scene's charge** (sexual > violent > neutral), and the paper may say so as a gradient.
- anything between: reported as it falls, with the sign-test MDE, and no gradient claim.

The prompts were written after the sexual, violent, liminal and hospice/garden results had been seen, and after I noted that controls follow stock completions; that is why "no stock answer" is a design criterion. They were not tried on any model before this file was committed.
