# The environment record: what we know about each checkpoint, and why we keep losing it

Governing doc for the (model × environment) record. Written 2026-08-22 after an audit found the record had forked across two repos, that a live script was writing into a read-only one, and that a 27-agent sweep of the chat logs surfaced 132 facts — most of which had been established, discussed, and then dropped.

## THE PROBLEM IS NOT MEMORY. IT IS THAT NOTHING FAILS.

Every fact lost this month was lost in one of six ways. None of them involved anyone forgetting to care:

1. **The write target drifted.** `scripts/record_successes.py` lives in this repo and wrote to `~/github/malign-logits/data/model_load_environments.json` — a repo RH has declared read-only. Facts landed where nothing reads them. *Fixed 2026-08-22.*
2. **The path out was a one-shot.** `ingest_environments.py` refuses to run twice, by design, because it hand-authored `environments.yaml`. So once it had run, the archive→live route was closed and the two files diverged in **both** directions: 131 observations there against 72 here, neither a superset. *Fixed by `merge_environment_record.py`.*
3. **Derived files go stale silently.** `data/model_requirements.json` is dated 15 Aug and derived from five sources, **all of them in the archive**. It carries a `--check` that exits non-zero when a source is newer. Nobody runs it.
4. **The schema could not hold the fact.** Falcon-H1 loads at 4.57.1, FAILS at 5.4.0, loads again at 5.14.1 — *a hole, not a floor or a ceiling*, and no field can say that. `beaver-7b` dies cross-scoring against `llama-7b` on a 32000-vs-32001 vocab mismatch — a per-EDGE fact in a store keyed on (model × environment). Facts with no field get discussed and dropped.
5. **Success is invisible.** A failure interrupts you, so you record it. A success does not, so you do not. On 18 Aug the record held 64 observations of which 38 were failures, while 52 models had cells nobody had written down.
6. **Corrections do not propagate.** `cloud_runbook.md` still calls the llm-jp `--eager` fix "unproven"; a probe proved it the same day and never wrote back. Of 147 mined findings, **15 were already superseded** by a later message in the same logs.

**The common shape: at no point does anything exit non-zero.** A lost fact and a recorded fact produce identical output from every command we run.

## THE THREE STORES ARE DISJOINT IN KIND. NEVER FOLD ONE INTO ANOTHER.

Established 2026-08-22 by measurement, after a proposal to derive the failure log from the corpus:

    model_requirements.json   MODAL        what a checkpoint NEEDS: pins as
                              (necessity)  SPECIFIERS, min_vram, kernels,
                                           packages, weights, blocked
    observations.json         FAILURE      (model x environment) outcomes with
                              + CAUSE      cause and fix, packages present/absent
    twp cells                 EXISTENTIAL  weighted success at high resolution;
                              (sufficiency) 107 models the JSON has never seen

**A success proves sufficiency and never necessity.** 85 models have cells under exactly one transformers version and **zero** have cells under two — so "requires 4.57.1" and "happened to run on 4.57.1" produce identical cell data. Deriving pins from cells would invent 18 false ceilings and miss 9 real ones. See `[[feedback-success-only-cannot-ground-necessity]]`.

---

# The plan

## P0 — DONE 2026-08-22

- `scripts/merge_environment_record.py` — archive → live, additive, re-runnable, byte-identical across three runs. 72 → 147.
- `record_successes.py` repointed to `roster/models/observations.json`.
- **Local and cloud separated.** The environment is now derived from the cells (`device`, `transformers_version`, `torch_version`), not from `venv_for(model)`. The old two-entry venv map stamped every success `local_mps`, including 38 cuda-only models; for `Llama-3.1-70B-Instruct` it would have written `local_mps | load_ok` directly beside `local_mps | load_failed | CAPACITY: ~140GB bf16 against 96GB unified memory`. Now 368 observations over 157 models and 20 environments — local 207/124, cloud 161/131.

## P1 — THE GATE. Highest value, do this first.

`scripts/check_record.py`, one command, **exits non-zero**. Nothing else on this list matters until something fails.

1. **No live script writes to the archive.** Static grep for the archive path in `scripts/` and `malignment/`. This is the defect that started it; it must not be able to recur silently.
2. **No derived file is older than its sources.** Generalises `model_requirements.json --check` to every derived artifact, and makes it a gate rather than a flag.
3. **Every (model × environment) with cells has an observation.** The corpus is the denominator; a gap is a missing row, not an unknown.
4. **No (model, environment) carries both a success and a `load_failed`** unless annotated as a repair-in-place (AmberSafe's is legitimate: it failed, packages went in, it loaded).
5. **Every profile's `launch:` box satisfies the `sizing:` rule.** Would have caught the three `Olmo-3.1-32B` arms declaring `launch: dense` (48 GB) against a rule demanding 80 — an OOM *after* paying for a 129 GB fp32 download.
6. **Every roster model resolves to an environment and a venv.**

## P2 — SCHEMA: store OBSERVED POINTS, derive the bound.

The version-hole problem dissolves if we stop storing ranges. A range is a claim; a point is an observation.

    version_observations   (model, package, version, outcome, evidence)
                           Falcon-H1 becomes three rows -- 4.57.1 ok, 5.4.0
                           failed, 5.14.1 ok -- and the HOLE is simply what the
                           rows say. The specifier in model_requirements.json
                           becomes DERIVED from these, which is the right
                           direction: existential rows, modal conclusion.

    edges                  (base, aligned, property, value, cause)
                           cross_score false + vocab 32000 vs 32001. Six roster
                           pairs need this and none has anywhere to live.

    repos                  (model, gated, exists, trust_remote_code, revision_trap)
                           jais/gemma x4/Zamba2 gated; mpt-7b 404; SmolLM3-3B-
                           checkpoints `main` resolves to the WRONG weights;
                           remote code refused unless config declares auto_map
                           (19 of our models declare it, 138 do not).

Tokenizer defect **scope** becomes a field rather than prose: Croissant and Teuken are CJK-class defects that are Latin-exact, and excluding them from Latin work threw away measurable cells.

## P3 — RE-DERIVE requirements from live sources

`model_requirements.json` has five `_sources` and every one is in the archive. Rebuild it against the live roster plus P2's new blocks, land it in `roster/`, and let P1.2 keep it honest. Until then it will keep reporting `none-local` for 50 checkpoints that have thousands of cells on disk.

## P4 — BACKFILL the 132 mined findings

Triage by the `already_recorded` field the agents returned. Take the ones marked `no` that carry a verbatim quote and a date; re-verify the three the agents themselves flagged (`falcon-7b` RoPE/YaRN — doesn't say which checkpoint; `neo_7b` sentencepiece ImportError — no version; `Tanuki-8B` 404 — undated). Re-run the three zero-hit models (`Olmo-3.1-32B-Instruct-DPO/SFT`, `Olmo-Hybrid-Instruct-SFT-7B`) with better aliases — they were discussed at length the same day the sweep ran, so zero hits is a search gap, not silence.

**Do not bulk-insert.** These are chatlog claims, not verified facts, and the sweep ran over logs that include the session that produced half of them.

## P5 — MAKE THE MINING STANDING, NOT A ONE-OFF

The sweep found 132 facts in 26 minutes for 6.4M tokens. Run it on a schedule over a trailing window, **diff against the record, and surface only what is new**. That is the net that catches whatever P2's schema still cannot express — and it is the only item here that improves on its own as the record improves, because a better record makes the diff smaller.

---

## The one-line rule

**A fact that nothing checks is a fact you have already lost.** Recording it is the cheap half; making something fail without it is the half that works.
