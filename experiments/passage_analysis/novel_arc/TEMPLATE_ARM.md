---
question: Does the chat template move where aligned-model fiction sits on the historical curves (Figure 5), and does being addressed move it further?
status: "SPEC 2026-09-25, not registered, not run. RH: 'Maybe we just do all arms (B) -- base, aligned-raw, aligned-prefilled, aligned-chat. Can we spec that for the 41-empty-sysable lineages'."
---

# Figure 5 under the chat template: all four arms, 41 lineages, one engine

Figure 5 places model fiction on the novel's historical curves: concreteness (`rh_absconc_median`) and inner life (`usas_x`). The v6 plate stands on 25 lineages from f11_l2 (August, vLLM, raw, engine version unrecorded). Every aligned passage in it continues a bare text, so the plate says nothing about the model as deployed. This spec regenerates **every** arm on one engine, so a frame contrast never crosses an engine.

## WHY ALL FOUR ARMS (option B)

Option A would have reused the August base passages and generated only the aligned frames, putting two engines inside every base-vs-aligned contrast. Deciding between A and B after seeing the aligned passages would need a second rental to download the base checkpoints again (RH). So every arm is generated here. **The 22 lineages shared with the v6 plate give an engine replication for free:** new vs August base passages on all 22, and new vs August raw on the **18** whose aligned model is the same checkpoint (same models, same stems, same seeds). It is reported beside the plate and never pooled into it. If they disagree beyond the split-half band of the August passages, that is a finding about the engine, and the published v6 plate carries a note.

## POPULATION

`roster.population("framed_empty")`: **41 endpoint lineages** whose aligned model receives no system context under the template (byte test on the render; Llama-3.1-8B's date-only block admitted by RH). Producer `scripts/build_framed_empty.py`. Each lineage's `system_mode` (`empty`, or `default` where "" renders byte-identically to it) is read from that file and used for **both** templated frames, so the change from prefill to continue never moves the system message.

- 22 of the 41 are in the v6 plate. Its other 3 lineages stay out of the primary: SmolLM3 (system block names the model and instructs it), AmberSafe (Vicuna preamble), CT-LLM (no template). **Optional sensitivity:** SmolLM3 and AmberSafe in all four arms with their default system message, reported beside the primary.
- 19 are new to Figure 5.
- **On 4 of the 22 the aligned checkpoint changes.** v6 used OLMo-2-1B-DPO, OLMoE-DPO, Olmo-3-DPO and zephyr; this population takes the endpoint (OLMo-2-0425-1B-Instruct, OLMoE-1B-7B-0125-Instruct, Olmo-3-7B-Instruct, Mistral-7B-Instruct-v0.1).
- **The plate's population changes from 25 to 41.** The paper seat recommended staying at 25 (reasons: two engines under A, coding cost, essay space). The first falls away under B; the other two stand and are RH's to weigh.

## ARMS

The prompts are the **100 English f11_l2 strings**, all roles, the population Figure 5 already draws from (`f11_l2_population.json`, list sha256/16 `e5da397ff891af74`, en subset). n=20 per (model, prompt, arm).

    base       base model, raw text, NO TEMPLATE EVER (RH), even where a
               tokenizer ships one
    raw        aligned model, raw text, no template
    prefill    aligned model, template; system per system_mode; user "Hi.";
               the assistant turn opens with the stem (twp's and framed_y's
               prefill)
    continue   aligned model, template; system per system_mode; user
               "Continue this text: " + stem; no assistant prefix
               (framed_y's continue)

Thinking off via the vendor switch on every templated arm where one exists (Qwen3-8B, MiniCPM5-1B); `template_kwargs` enters the key.

## DECODER: f11_l2's, field for field

| setting | value |
|---|---|
| sampling | temperature 1.0, top_p 1.0, top_k −1, max_tokens 256, min_tokens 0, presence and frequency penalty 0, repetition penalty 1.0, no stop sequences |
| n | 20 per (model, prompt, arm) |
| seeds | `int(sha16(model+"\|"+prompt)[:8], 16) % 2**31` for `base`/`raw` (identical to f11_l2, so the replication shares seeds); `sha16(model+"\|"+arm+"\|"+prompt)` for templated arms |
| dtype | float16, except bfloat16 where `requirements.json` declares a compute dtype (gemma-2, Falcon-H1, Zamba2, falcon-mamba) |
| context | `max_model_len` 1024 |
| recorded per row | engine and **engine version**, GPU name, dtype, rendered-prompt sha, system_mode, template_kwargs, resolved sampling params. f11_l2's plan declared `engine_version` and its runner never wrote it; this one does. |

Runner: `malignment.vllm_generate` (`render_templated`, `SystemIgnored`, with the 23 Sep fixes for double BOS, raw fallback under a chat key, and skipped templates), extended with an f11_l2 prompt file and the seed formula above. The runner asserts that the decoder the engine resolved equals this table and refuses to generate otherwise.

## ENGINE CLASSES (all four arms of a lineage always on ONE engine)

| class | lineages | handling |
|---|---|---|
| standard vLLM | 29 | 22 of the 41 aligned models were in framed_y's vLLM 0.22.1 / A40 fleet; the rest are dense transformers of familiar architectures |
| Aug known-dead on vLLM | Baichuan2, Croissant, deepseek, internlm2 | preflight against `observations.json`; deepseek's verdict was stale (malign-logits 2a5640e1); drop only on an observed cause |
| SSM / hybrid kernels | Zamba2, Falcon-H1 1.5B + 7B, falcon-mamba, Olmo-Hybrid | the mamba-kernel profile (`project_image_revokes_a_capability`: wheels, `--no-deps`, torch 2.8), bf16 |
| no vLLM implementation | rwkv-raven, recurrentgemma | HF transformers on the box, same decoder; engine recorded; slow (~4 h each) |
| 32B | Olmo-3.1-32B | one A100 80GB (or 2×A40 with tensor parallelism) |

A lineage that fails is listed with its cause and dropped from every contrast. **No substitution.**

## NARRATIVE FILTER AND PLACEMENT (unchanged from v6, per model-arm)

1. passC classifier (char TF-IDF + 23 features) ranks a 714-draw sample; **top 200 per model-arm** go to the coder. Continue replies are stripped of assistant preambles ("Sure! Here's a continuation:") by a rule declared before any passage is read, and the strip rate per model is reported.
2. One Opus reading per passage via Workflow agents ($0 API): `narrative` true/false. **164 model-arms × 200 = 32,800 passages, about 3× passC.**
3. Scorer (`measure_lltk`) on narrative passages of **≥ 40 words** (primary). **Sensitivity: ≥ 150 words**, all lines. The reading rule: a frame difference present in the primary and absent at ≥ 150 words is length.
4. **Composition control** (paper seat): each arm's stem-family mix and **survival table** (family × arm) per model; a sensitivity that post-stratifies by stem family, taking per-model medians within family and reweighting to the **pooled base mix**.
5. Floor: ≥ 10 narrative passages in both arms of a contrast. Thin cells are listed, not boosted.

## CONTRASTS (paper seat's review folded in, 2026-09-25; to be registered with RH before any passage is read)

**Unit: the lineage** (one base and one aligned checkpoint each, so lineage = pair). **Measures:** per-model median concreteness (z) and inner life (`usas_x`, points), on narrative passages ≥ 40 words.

**One population for every line and every test.** PRIMARY: the lineages meeting the ≥ 10 floor in **all four arms**; every line and every step is computed over that same set, so a gap between lines is never a gap between populations. SENSITIVITY: each line over its own largest set meeting the floor.

**Three steps, within lineage, both measures:**

    alignment   base -> raw          the replication of v6's claim (aligned more
                                     abstract, more inner life); 2 tests
    template    raw -> prefill       frame test
    address     prefill -> continue  frame test

Two-sided sign tests on the per-lineage paired differences of per-model medians, ties dropped. **Holm across the four frame tests** (two steps × two measures); the alignment step is reported separately as the replication, with its own two tests. Effect size: the median paired difference (z; points). Crossing years (concreteness) and levels against the historical max (inner life) are **descriptive only**, never tested.

**Reading rules, both declared now:**
- **Length.** A frame difference present in the primary (≥ 40 words) and absent at ≥ 150 words reads as length.
- **Composition.** A frame difference present in the primary and absent after stem-family post-stratification reads as composition. Post-stratification: per-model medians within family, reweighted to the pooled base mix. A family cell under 3 passages is dropped and the weights renormalise over the remaining families.

**Priors, stated as expectations and not tested directionally** (the paper seat's). Both come from other corpora, so they are expectations, not replications:
- **National stories:** the template moved concreteness back toward the concrete (18 of 25, p = .043) and left inner life unchanged (15/25, p = .42). Source: `TheoryMachines/paper/theory-machines-v6-notes.md` note 59. Producer: `experiments/passage_analysis/national_story/ns_conc_int.py` (c6d0dc20; rerun 2026-09-25, report byte-identical; novel_arc Scorer over `national_story/conflict.sqlite`'s judged pure stories; endpoints only; Qwen3-8B's prefill cell dropped; 200-word chunks, story value = median over chunks). Caveat: that prefill cell used each model's DEFAULT system prompt, not framed_empty's `system_mode`.
- **frame_inversion** (`experiments/subject_position/frame_inversion`, `results/cache.jsonl`, run.py's own `paired()`/`report()`, recomputed 2026-09-24): inner life under the template up in 16 and down in 10 of 26, p = 0.33, without Qwen3-8B's prefill cell (16/11, p = 0.44 as committed). `TheoryMachines/paper/frame-additions.md` entry A.

**Survival, decomposed per model and arm:** generated → classifier top 200 → coded narrative → ≥ 40 words, with loss split into **refused**, not narrative, and too short, plus the stem-family survival table. Refusal is not a narrative-coder label, and the classifier's top-200 selection would rank refusals out before coding, so refusal is measured **before** selection: a separate agent read (framed_y's strict `assistant_refusal` definition) on a seeded random 100 of **every arm's** 714-draw sample, base and raw included so the refused column has a measured baseline rather than an assumed zero (41 × 4 × 100 = 16,400 reads, $0 API), with refusal_frame's regex over every templated passage beside it. The regex is **descriptive only**: on framed_y its precision/recall were 0.94/0.68 under continue but 0.48/0.13 under prefill (`framed_y/results/refusal_check.md`).

**Engine replication:** new vs August base (22 lineages) and raw (18 with the same aligned checkpoint), against the August split-half band. Descriptive, beside.

## COST

| item | size | estimate |
|---|---|---|
| downloads | 82 checkpoints, ~1.1 TB at fp16 | ~2.5 h wall at the measured ~125 MB/s, spread over boxes |
| generation | 41 × 4 arms × 100 × 20 = **328,000 passages**, ≤ 84M tokens | ~15–20 A40-hours at $0.49/h, plus ~2 h A100 for the 32B |
| **total, RunPod** | | **~$12–15; cap $25** |
| coding | 32,800 passages | Workflow agents, $0 API; about 3× passC's agent time |

The first box reports measured tok/s before the rest launch. Boxes are sharded by lineage (both checkpoints resident; purge after each lineage) and deleted after byte verification.

## GATES

1. RH: population (41 vs 25), the optional sensitivity, spend word.
2. Paper seat: contrasts and plate rules as above.
3. Registration committed. Preflight of all 82 checkpoints. First box. Fleet.
