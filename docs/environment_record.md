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

## P1 — THE GATE. DONE. `scripts/check_record.py`, 8/8.

`scripts/check_record.py`, one command, **exits non-zero**. Nothing else on this list matters until something fails.

1. **No live script writes to the archive.** Static grep for the archive path in `scripts/` and `malignment/`. This is the defect that started it; it must not be able to recur silently.
2. **No derived file is older than its sources.** Generalises `model_requirements.json --check` to every derived artifact, and makes it a gate rather than a flag.
3. **Every (model × environment) with cells has an observation.** The corpus is the denominator; a gap is a missing row, not an unknown.
4. **No (model, environment) carries both a success and a `load_failed`** unless annotated as a repair-in-place (AmberSafe's is legitimate: it failed, packages went in, it loaded).
5. **Every profile's `launch:` box satisfies the `sizing:` rule.** Would have caught the three `Olmo-3.1-32B` arms declaring `launch: dense` (48 GB) against a rule demanding 80 — an OOM *after* paying for a 129 GB fp32 download.
6. **Every roster model resolves to an environment and a venv.**

6. **Revision traps are pinned** and **gated repos are measured** (below).

## P1b — RUNTIME GUARDS. DONE. `scripts/box_guard.py`, wired into `fleet_launch`.

The record and the gate both assume we already know the failure. These two do
not, and that is the point — they are **ignorant of mechanism**, so they catch
what nobody has written down yet.

    throughput_verdict   observed s/cell against the 595 recorded rates.
                         Zamba2 with idle kernels reads 191.8x and fires. Wired
                         into `_await`, where every other signal -- done,
                         failed, tmux, idle -- reads green because the box IS
                         producing. Also catches the wrong card, thermal and
                         contention, none of which it knows about.
    emptiness_verdict    fraction of stored cells holding no words. Falcon-H1 at
                         fp16 wrote 5,166 EMPTY cells satisfying conservation
                         EXACTLY (`sum([]) + 1.0 == 1.0`). Wired into the
                         DESTROY gate, because counting lines verifies TRANSFER
                         and not CONTENT.

`--selftest` watches both FIRE on those incidents and stay QUIET on a healthy
run, a 3-cell sample, and a 5x-slow shard inside the mix band.

**Why the kernels kept being rediscovered specifically:** the launcher already
refused to proceed if the kernels failed to INSTALL (rc=5). `environments.yaml`
said in bold that install is not use. Grepping the repo for that verification
returned nothing across four fleets — and the obvious implementation does not
work, because `is_mamba_ssm_available()` returned True throughout the failure
and the fast-path warning lies on a failed load. The rate answers what the
library cannot.

## P2 — SCHEMA: store OBSERVED POINTS, derive the bound. PARTLY DONE.

**Repo status: DONE.** `scripts/probe_repos.py` -> measurements.json `repos`.
160 models: 147 public, **11 gated_held** (all four meta-llama arms, both gemma
pairs, both jais, Zamba2 — a tokenless box fails on every one), 2
`revision_required`, 0 dead. The status code on `/api/models` is NOT the gate --
it returns 200 for gated repos, and the first draft therefore called 159/160
public. Gating bites on FILE access, so the probe reads `body["gated"]` for the
declared policy AND a HEAD on `resolve/main/config.json` anonymously and tokened
for what a box actually gets.

`SmolLM3-3B-checkpoints` is now a measured `revision_required`: its `main` holds
exactly `.gitattributes` and `README.md`, so the bare id resolves to **no model
at all** — the chatlogs called it "resolves to the wrong model", which
understates it, and calling it `dead` (the first classifier did) is wrong in the
other direction, since dead and revision-required want opposite responses.

**Version windows: DONE.** `scripts/build_version_windows.py` -> `roster/models/version_windows.json`. 385 observed points over 141 models. **One hole, found by the producer rather than by anyone remembering it:** `Olmo-3-1125-32B` — transformers 4.57.1 works, **4.57.6 fails, 5.4.0 fails**, 5.14.1 works. Falcon-H1's hole deliberately does NOT appear: the record holds 4.57.1=works and 5.4.0=fails, and the third point (5.14.1) exists only in a chatlog. Absence is not a point, so no hole is asserted — the schema now has somewhere to put it and the fact is genuinely missing.

A `mixed` point (one version both working and failing) is not a hole: AmberSafe loaded after two packages went in on the same box, and reading a repair-in-place as a version bound would invent a constraint out of a packaging fix.

**Edge facts: DONE.** `scripts/build_edge_facts.py` -> `roster/models/edge_facts.json`. 156 pairs, **21 vocab mismatches where six were remembered**, including `Aquila2-7B -sft-> AquilaChat2-7B` at **143973 vs 100008** — 43,965 tokens apart, so any base→aligned comparison there spans two vocabularies. Root→member pairs are generated as well as direct edges, because the motivating case is not a direct edge: `beaver-7b` was cross-scored against its lineage ROOT two hops up, and an edge-only derivation called the parent pair clean.

**These were the schema shapes:**

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

Tokenizer defect **scope** becomes a field rather than prose: Croissant and Teuken are CJK-class defects that are Latin-exact, and excluding them from Latin work threw away measurable cells. `trust_remote_code` likewise — remote code is refused unless the config declares `auto_map`, and 19 of our models declare it against 138 that do not.

## P3 — RE-DERIVE requirements from live sources. DONE.

`scripts/build_requirements.py` -> `roster/models/requirements.json`. 160 checkpoints, `params_b` for **all** of them, derived from models.yaml + environments.yaml + measurements.json + observations.json.

**No model name appears in the producer.** The archive builder decided kernels with `KERNELS = ("mamba", "zamba", "falcon-h1")` — a substring match on the id, which is the error class that keeps costing us: RWKV matches none of those and pattern-matches the SSM class on every other axis while needing no kernels. A model needing kernels now gets them by declaring `profile: ssm`.

`blocked` is 0, and that is verified rather than assumed: the archive's five blocked models all left the roster and were replaced with live mirrors (`gl198976/mpt-7b`).

**The staleness gate now points at a file we are permitted to fix.** Checking the archive copy could only ever report a failure nobody could clear, and a gate that cannot be satisfied is a gate people learn to ignore.

## P4 — BACKFILL the 132 mined findings

Triage by the `already_recorded` field the agents returned. Take the ones marked `no` that carry a verbatim quote and a date; re-verify the three the agents themselves flagged (`falcon-7b` RoPE/YaRN — doesn't say which checkpoint; `neo_7b` sentencepiece ImportError — no version; `Tanuki-8B` 404 — undated). Re-run the three zero-hit models (`Olmo-3.1-32B-Instruct-DPO/SFT`, `Olmo-Hybrid-Instruct-SFT-7B`) with better aliases — they were discussed at length the same day the sweep ran, so zero hits is a search gap, not silence.

**Do not bulk-insert.** These are chatlog claims, not verified facts, and the sweep ran over logs that include the session that produced half of them.

## P5 — MAKE THE MINING STANDING, NOT A ONE-OFF

The sweep found 132 facts in 26 minutes for 6.4M tokens. Run it on a schedule over a trailing window, **diff against the record, and surface only what is new**. That is the net that catches whatever P2's schema still cannot express — and it is the only item here that improves on its own as the record improves, because a better record makes the diff smaller.

---

## The one-line rule

**A fact that nothing checks is a fact you have already lost.** Recording it is the cheap half; making something fail without it is the half that works.
