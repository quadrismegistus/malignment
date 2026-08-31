# Tech debt

Known refactors that are worth doing but not urgent. Each entry says what's wrong, what the fix is, and what the risk of touching it is.

## 1. `load_for_twp` conflates two jobs

**What's wrong:** `runners.load_for_twp()` is the universal model loader — used by twp, generation, hidden state extraction, the data explorer, and logit lens. But it builds twp-specific infrastructure (boundary mask, prefix trie, CJK vocab, bos_policy) on every call, and every non-twp consumer ignores half the return value.

**Fix:** Split into `Checkpoint.load()` → `(model, tokenizer, device)` handling LOADER_OVERRIDE, compute_dtype, revision pins, trust_remote_code, chat template injection. Then `load_for_twp()` calls that and adds bmask/trie/cjk/bos_policy on top.

**Risk:** High. The loader is load-bearing with many edge cases (mpt config refusal, OLMoE tie_word_embeddings, dtype selection). Test against every model that has a LOADER_OVERRIDE or a known failure mode.

**Workaround:** `ck.load()` exists today and delegates to `load_for_twp`. The name is wrong but the code is right.

## 2. corpus.py is a re-export shim awaiting deletion

**What's wrong:** `corpus.py` was dissolved on 2026-08-28 — functions moved to `ch.py`, `prompts.py`, `movement.py`. The file now re-exports from the new homes for backward compat. Five runner functions (`topup_todo`, `pass1_todo`, `stash_union`, `lineage_union`, `_stash_words`) still live there because moving them to `runners.py` risks circular imports.

**Fix:** Move the 5 runner functions to `runners.py` (may need lazy imports to break the cycle), then delete `corpus.py`. Update the 3 experiment files that still import `from malignment import corpus`.

**Risk:** Low for the experiment imports (mechanical). Medium for the runner functions (circular import resolution).

## 3. `RULE_VERSION = 3` remnants

**What's wrong:** `movement.RULE_VERSION` was flipped to 4 on 2026-08-28, and `contrast()` updated to read `twp_words_v4_best`. But other modules may still carry v3 assumptions — `population.py` was updated to use `ch.retable()` but its `RULE_VERSION` constant may still be 3.

**Fix:** Grep for `RULE_VERSION` and `rule_version=3` across the codebase and update defaults where v4 is the full roster.

**Risk:** Low. Each site is independent.

## 4. `movement_rows` / `endpoint_movement` naming in the shim

**What's wrong:** `corpus.movement()` was renamed to `movement.movement_rows()` to avoid a module/function name collision. The shim re-exports `movement_pairs_list as movement_pairs`. These aliases exist only for backward compat and the names are confusing.

**Fix:** Once experiments are updated to import from `movement` directly, drop the aliases from the shim.

**Risk:** Low. Mechanical.

## 5. v3 `movement` table has no v4 equivalent for `endpoint_movement`

**What's wrong:** `movement_rows()` and `endpoint_movement()` now support `rule_version=4` via `movement_v4`, but the word-level movement table was built by `produce_movement` which may not have been rerun for all v4 pairs. The cell-level `movement_cells_v4` exists and is populated.

**Fix:** Verify `produce_movement` has been run for v4 across all endpoint pairs. The accessor code is ready.

**Risk:** Low — the code handles missing data gracefully (empty results).

## 6. `twp_words_v4_best` materialization must be re-run after ingest

**What's wrong:** `twp_words_v4_best` and `twp_cells_v4_best` were materialized from views into tables on 2026-08-28 for performance (queries went from minutes to <1s). But unlike the views, the tables don't auto-update on INSERT.

**Fix:** Run `python scripts/materialize_best.py` after any ingest. Could be automated as a post-ingest hook.

**Risk:** Low. Forgetting to rebuild gives stale data, not wrong data — new cells are missing, not corrupted. The view DDL is preserved in `views.py` and the script can recreate the table from scratch.
