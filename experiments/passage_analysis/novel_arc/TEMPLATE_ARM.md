---
question: Does the chat template move where aligned-model fiction sits on the historical curves (Figure 5), and does being addressed move it further?
status: "REGISTERED 2026-09-25, before any passage exists. RH: 'Maybe we just do all arms (B) -- base, aligned-raw, aligned-prefilled, aligned-chat. Can we spec that for the 41-empty-sysable lineages', then 'go ahead and run, Y + f11_l2 in the way you suggest ... stick to A40s where possible'. Contrasts reviewed by the paper seat."
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

Two prompt sets, every arm, every lineage (`template_arm/build.py` -> `template_arm/prompts/<model>.jsonl`):

- **f11**: the **100 English f11_l2 strings**, all roles, the population Figure 5 draws from (the distinct `en` prompts of `f11_l2_full.parquet`; `f11_l2_population.json`, list sha256/16 `e5da397ff891af74`). **n = 20.**
- **y**: **Y's 34 cells** (`superego_stages/prompts/y_cells.jsonl`: 5 stems, each bare and with 6 forced words). **n = 50**, as Y and framed_y, because Y's coding draws 20 per cell from passages that ran the full 256 tokens and templated arms stop early. RH, 2026-09-25: the checkpoints are downloaded once, so Y's cells ride on this rental; coding them is a separate decision (DeepSeek, paid).

**606,800 passages**: f11 41 × 4 × 100 × 20 = 328,000; y 41 × 4 × 34 × 50 = 278,800. The Y arms are framed exactly as framed_y's (same user turns, same system rule), so they join framed_y's cells and extend Y to the 19 lineages it never had.

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
| n | 20 per (model, f11 stem, arm); 50 per (model, Y cell, arm) |
| seeds | per condition `int(sha256(model+"\|"+arm+"\|"+stem)[:8], 16) % 2**31`; sample i uses seed + i (one SamplingParams per sample). **One scheme for both sets.** f11_l2 drew n=20 from ONE seed per cell and Y's seeds came from Python's per-process-randomised `hash()`, so neither can be reproduced draw for draw on another engine anyway; the replication against August is distributional (split-half band), never token-identical. |
| dtype | float16, except bfloat16 where `requirements.json` declares a compute dtype (gemma-2, Falcon-H1, Zamba2, falcon-mamba) |
| context | `max_model_len` 1024 |
| recorded per row | engine and **engine version**, GPU name, dtype, rendered-prompt sha, system_mode, template_kwargs, resolved sampling params. f11_l2's plan declared `engine_version` and its runner never wrote it; this one does. |

Runner: `malignment.vllm_generate` (`render_templated`, `SystemIgnored`, with the 23 Sep fixes for double BOS, raw fallback under a chat key, and skipped templates), extended 2026-09-25 with per-condition `n` and `seed` in the prompts file and every sampling field named explicitly. It asserts that the decoder the engine resolved equals this table and refuses to generate otherwise. vLLM 0.22.1 on RunPod A40s (`template_arm/fleet/`: 6 single-A40 pods by parameter load, one 4×A40 pod at tp=4; each checkpoint purged after its run).

## ENGINE CLASSES (all four arms of a lineage always on ONE engine)

| class | lineages | handling |
|---|---|---|
| standard vLLM | 29 | 22 of the 41 aligned models were in framed_y's vLLM 0.22.1 / A40 fleet; the rest are dense transformers of familiar architectures |
| ran on this exact setup in the institution fleet (23-24 Sep) | Baichuan2, Croissant, deepseek, Zamba2, Falcon-H1 1.5B, falcon-mamba, gemma-2, falcon-7b (tf 5.10.2, placed last on its pod and re-pinned after) | bf16 where `requirements.json` declares it (gemma-2, Falcon-H1, Zamba2, falcon-mamba) |
| batched HF (`template_arm/hf_batch.py`, one A40 each) | rwkv (vLLM refuses), recurrentgemma (vLLM refuses), Olmo-Hybrid (tf ≥ 5 + fla), internlm2 (word salad in every cell under vLLM 0.22.1) | same prompts, `generate.DECODER` (top_k=0), `generate.render`/`encode`; ONE `generate` per condition with num_return_sequences=n after `torch.manual_seed(seed)`, so `batch_seed` is on the record; **bf16** (fp16 HF sampling hit NaN probabilities in the smoke test); key `render="hf_batch"` |
| 4×A40, tp=4 | Olmo-3.1-32B (fp16 does not fit one card), Falcon-H1-7B (OOMs at engine init on one A40) | `NCCL_P2P_DISABLE=1 NCCL_IB_DISABLE=1`, without which NCCL init hangs at 100% util |

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
| generation | **606,800 passages**, ≤ 155M tokens | ~30 A40-hours at $0.49/h (6 vLLM pods, 4 HF pods, one 4×A40 pod at $1.96/h) |
| **total, RunPod** | | **~$20–25; cap $35** |
| coding, Figure 5 | 32,800 passages + 16,400 refusal reads | Workflow agents, $0 API |
| coding, Y | not authorised by this registration | DeepSeek `code_y_superego_v3`, ~$0.0001–0.0003 per call; RH decides after generation |

The first box reports measured tok/s before the rest launch. Boxes are sharded by lineage (both checkpoints resident; purge after each lineage) and deleted after byte verification.

## GATES

1. RH: 41 lineages, run (2026-09-25). The optional SmolLM3/AmberSafe sensitivity is **not** generated.
2. Paper seat: contrasts and plate rules as above (reviewed 2026-09-25).
3. Preflight: every vLLM checkpoint here ran on vLLM 0.22.1 / A40 with this render path in the institution fleet (23-24 Sep), except the four routed to batched HF. The first pod's first model is read (a stored passage's frame, template, render fields and text) before the rest are trusted.

## AMENDMENT 1, before any template-arm passage was coded (2026-09-25)

RH: "only 40+", and "just add the 'where does it break off, return a span of first non-narrative text' to the workflow we run now". Selection and coder, replacing the corresponding lines above:

- **Selection** (`template_arm/select_for_coding.py`): f11 stems; continue replies stripped of a leading assistant preamble by one declared regex (0.7% of continue passages, almost all MiniCPM5-1B, 0 elsewhere; flagged per row); **>= 40 words**; ranked by passC's classifier (`template_arm/triage.py`, recovered verbatim, reproduces triage.parquet exactly) over ALL passages in the cell, not a 714 draw (the spec above misdescribed passC); top 200, or all where fewer qualify. 31,831 passages over 161 cells; 4 cells have under 200 eligible (prefill: kanana-2-3b 43, Llama-3.1-8B 106, Qwen2.5-0.5B 117, AquilaChat2 165).
- **Coder**: passC's rubric and per-batch prompt, verbatim, with ONE added code, `break`, and "five codes" -> "six codes". Single coder, effort high, **model pinned to claude-opus-5** (`template_arm/coding/CALIBRATION.md`: neither 5.5 nor pinned opus-5 matches August's coder A, so no old coding enters the template-arm Figure 5). The fragment shown is the STEM in every arm; arm and frame are never shown. Batches of 45, shuffled across models and arms.
- **The survival table** gains a column: among non-narrative passages, those whose `break` quote is found AFTER the passage's opening (fiction, then interruption) against those non-narrative from the first words; the words of fiction before the break are reported per arm.

## AMENDMENT 2, before any placement was read (2026-09-25)

**Pre-break prefix sensitivity** (RH: "Sure"). On the first 14,580 coded passages, 31-45% of non-narrative passages per arm carry at least 40 words of fiction before their `break` quote (base 45%, raw 40%, prefill 42%, continue 31%; the narrative share would rise base 0.38 -> 0.66, raw 0.56 -> 0.73, prefill 0.58 -> 0.76, continue 0.73 -> 0.82). Each arm is placed a second time with those prefixes added: the text before the first occurrence of the break quote, when it has >= 40 words. The primary stays whole-passage. Prefixes are short by construction, so a line difference that appears only here must also survive the >= 150-word version before it is read as more than length. Answers whether a line's placement depends on keeping only the passages that stay fiction to the end, which the stricter coder makes a real question for base.

RH, same message: "registrations are not binding, truth is." This file records what was decided before which data were seen, so a later departure is visible as one; it does not forbid it.

## AMENDMENT 3: the RWKV lineage is DROPPED (RH, 2026-09-25, before any placement was read)

Batched HF generation of RWKV/rwkv-4-7b-pile and rwkv-raven-7b in bf16 (the HF class's dtype, chosen after fp16 hit NaN probabilities in the smoke test) is degenerate: 88% and 90% of 256-token samples are a repeated-word loop ("destroy destroy destroy ...", "kill kill kill ..."). The other three HF lineages, same runner and dtype, pass the same check (0 loops). The pod then went unreachable before raven's templated arms synced, and was terminated unverified. RH: "Terminate it and drop rwkv." fp32 is untested. **Population: 40 lineages.** The two rwkv raw-arm cells already in `coding/selection.parquet` are coded but excluded from every analysis by lineage. Environment facts, including internlm2's split transformers requirement (base 4.45.2, chat 4.47.1, plain load), are in `roster/models/observations.json`.
