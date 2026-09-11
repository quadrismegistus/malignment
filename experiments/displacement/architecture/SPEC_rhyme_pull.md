---
kind: spec
status: SPEC ONLY, nothing run. Written 2026-09-11 on RH's ask relayed by @lacan. No box rented, no cell measured.
question: Can the verse-slot instrument be extended across architectures, and what does it cost?
headline: "$5.27 of compute, 5.0 GPU-hours, one box, half a working day wall-clock — and the full 1,633-prompt slot manifest is cheaper than the meeting about whether to sample it. All three matched contrasts are coverable. Two things in the framing are wrong: the `ssm` profile is ALREADY set for the four models that need it, and it does NOT cover Olmo-Hybrid, which needs `flash-linear-attention` instead."
---

# SPEC — rhyme_pull across architectures

RH's ask, via @lacan: cost and wall-clock, number of prompts, which models, and whether the three matched contrasts can all be covered. **Nothing here has been run.** Every number below is labelled measured, transferred, or estimated.

## 0. THE HEADLINE, AND THE ONE DESIGN DECISION THAT IS NOT MINE

    compute          5.02 GPU-hours          $5.27 at $1.05/hr (A100 SXM4, vast)
    wall clock       ~5-7 h on ONE box       ~3 h on three boxes
    prompts          1,633 per model         the whole missing slot manifest
    models           11 to run, 1 already done
    contrasts        all three coverable

**Do not sample.** RH's ask allows one ("a sample is fine, the pilot used 12 primers plus 8 unrhymed"). The full manifest is 1,633 prompts per model at a median 0.62 s/cell, which is **twenty minutes of A100 time per model**. A 20-primer sample would save about $4.80 and cost the within-poem pairing that the whole design rests on. Sampling here is a false economy by roughly two orders of magnitude.

**The decision that is RH's, not mine, is §4: whether to run the plain twp route (cheap, reuses `verse_capacity.py` unchanged, and inherits a confound RH personally caught and refused in August) or the closure route (2-3x the cost, needs the rider that never ran, and is the design RH actually approved).**

## 1. WHAT IS ACTUALLY MISSING — verified, not inherited

@lacan's count reproduces and then sharpens. Against `source='raw/verse_fleet_merged'`, 11 of 12 are absent and only `allenai/Olmo-3-1025-7B` has all 1,786. But `verse_capacity.py`'s own read discipline selects **by the manifest's prompt set across all sources**, because the fleet's overlap rows sit under older labels — so the source filter is the wrong check. Run properly (manifest contexts intersected against every source in `twp_words`):

    model                        prompts in store   of the 1,786 manifest contexts
    allenai/Olmo-3-1025-7B                  4,428      502   (1,786 under the fleet label)
    allenai/Olmo-Hybrid-7B                  2,663      154
    allenai/OLMoE-1B-7B-0125                2,663      154
    RWKV/rwkv-4-7b-pile                     2,663      154
    tiiuae/Falcon3-7B-Base                  2,663      154
    tiiuae/Falcon-H1-1.5B-Base              2,653      154
    tiiuae/falcon-mamba-7b                  2,647      153
    tiiuae/Falcon-H1-7B-Base                2,647      153
    google/recurrentgemma-9b                2,647      153
    google/gemma-2-9b                       2,647      153
    Zyphra/Zamba2-7B                        2,579      148
    tiiuae/falcon-7b                        2,578      148

**The ~153 each already holds are entirely `prose` and `battery` calibration slots** — contexts that happen to coincide with the general 2,983-prompt battery. Checked on `falcon-mamba-7b`: 61 battery + 92 prose, and **zero** of any verse slot. So the absence is total where it matters and the overlap is free calibration, which is the good version of this news: the battery slots that price the single-token bias arrive already measured.

    per-model work   1,633 contexts
    missing by slot  called 178 | near 178 | end1 178 | end2 59 | end3 119
                     end_partner_prior 178 | mid1-mid4 178 each
                     (+ 37 battery, 10 prose not yet covered)

178 rather than 180 because the manifest declares context collisions; `context_collides_with` travels per cell and `verse_capacity.py` already pools collided slots as one.

## 2. THE MODELS, AND THE COST PER MODEL

Rates are `data/model_twp_rates.jsonl`, CUDA, pass 1 (`topup=False`), taking the largest-n observation per model and applying `MIN_CELLS=25`. Cost = `1,633 x s/cell + 240 s` cold load, at $1.05/hr — back-derived from the runbook's own Falcon-H1-7B figures (21.4 h → $22; 1.1 h → $1.16).

    model                        profile       s/cell   GPU-h      $   provenance of the rate
    allenai/Olmo-Hybrid-7B       default+fla    2.373    1.14   1.20   measured n=2,664 WITH fla
    allenai/OLMoE-1B-7B-0125     tf457          1.448    0.72   0.76   measured n=2,704, Quadro RTX 8000
    tiiuae/falcon-mamba-7b       ssm            1.318    0.66   0.70   measured n=2,983
    Zyphra/Zamba2-7B             ssm            0.956    0.50   0.53   measured n=2,983 WITH mamba kernels
    google/recurrentgemma-9b     default        0.755    0.41   0.43   measured n=2,983
    RWKV/rwkv-4-7b-pile          default        0.618    0.35   0.36   measured n=1,599
    tiiuae/Falcon-H1-7B-Base     ssm            0.603    0.34   0.36   measured n=2,961
    google/gemma-2-9b            bf16           0.447    0.27   0.28   TRANSFERRED from MPS at 0.50
    tiiuae/falcon-7b             tf457          0.345    0.22   0.23   measured n=2,982
    tiiuae/Falcon-H1-1.5B-Base   ssm            0.296    0.20   0.21   measured n=2,981
    tiiuae/Falcon3-7B-Base       default        0.293    0.20   0.21   measured n=2,704, A100
                                                TOTAL     5.02   5.27

**Ten of eleven rates are measured on this corpus at n >= 1,599 cells.** One is transferred: `gemma-2-9b` has no CUDA observation. `rates.estimate(['google/gemma-2-9b'], 'cuda')` returns **0.4477**, carried from its MPS 0.894 across **88 paired models** — the ratio is far better evidenced than `project_twp_rates` records (that memory says n=1 lineage, written when coverage was mps 115 / cuda 3). The spread is the caveat, not the n: **0.09..1.63 across those 88 pairs.** If this one is wrong by 2x the total moves by $0.28, so it is disclosed rather than resolved.

**Two rate rows in the file must not be used, and §9 records that the library returns them anyway.** `Falcon-H1-7B-Base` at 0.0677 s/cell is `retracted: true` — it wrote 2,981 cells with `tail == 1.0` on every one, a beam that expanded nothing because fp16 gave all-NaN logits, and a beam doing no work is fast. `Olmo-Hybrid-7B` at 19.2 s/cell is n=42 and is the **`fla`-fallback** measurement, not a rate; its 6.04 s/cell (the roster-wide ceiling quoted in `project_twp_rates`) is **MPS**. Its CUDA-with-`fla` rate is 2.373 and that is the one this fleet pays.

### The cost band, stated rather than hidden

These rates were measured on the **2,983-prompt general battery**, not on verse slots, and two properties differ in opposite directions:

    verse contexts are LONGER      median 88 chars vs 48   (1.8x)
    verse cells yield FEWER words  81.8 words/cell vs 125  (0.65x)

Prefill is one cached pass per slot; beam expansion is the dominant term and it scales with words clearing theta. So the word count says verse cells are **cheaper** and the length says marginally dearer, and the net is unknown. **Treat 5.0 GPU-h as a point estimate inside a [2.5, 10] band.** At the top of that band the fleet still costs $10.50, which is why this paragraph is a disclosure and not a planning risk.

## 3. WALL CLOCK, AND WHY IT IS NOT DRIVEN BY COMPUTE

Compute is five hours. The wall clock is provisioning, and the roster splits into **five environments**, which is the actual planning fact:

    profile       GPU-h  n  models
    ssm            1.71  4  falcon-mamba-7b, Falcon-H1-1.5B, Falcon-H1-7B, Zamba2-7B
    default+fla    1.14  1  Olmo-Hybrid-7B
    default        0.96  3  rwkv-4-7b-pile, recurrentgemma-9b, Falcon3-7B-Base
    tf457          0.95  2  OLMoE-1B-7B-0125, falcon-7b
    bf16           0.27  1  gemma-2-9b

**ONE BOX, three venvs, is the right shape.** `scripts/venvs.py` already derives the venv per model from the roster, so `tf457` and `default` and `bf16` are venv choices on one machine rather than three rentals. The A100 that carries the compiled mamba kernels can carry all of it.

    kernel compile (mamba-ssm + causal-conv1d, from source)   ~30 min
      TORCH_CUDA_ARCH_LIST=8.0 MAX_JOBS=48 --no-build-isolation  (mandatory)
    model downloads, ~150 GB nominal (params x 2 B, ESTIMATED)  ~30-60 min
    compute                                                     ~5 h
    ingest + verify                                             ~20 min
    ------------------------------------------------------------------
    ONE BOX                                                    ~6.5-7 h, ~$7
    THREE BOXES (ssm | default+fla+bf16 | tf457)               ~3 h,    ~$9

150 GB fits the `default` 300 GB disk without purging, so `bigdisk` is not needed.

**Add one casualty.** The runbook's own record: the L2 fleet lost 3 of 14 boxes and the grid lost 6 of 14, all in provisioning, all needing a human. On a one-box plan a casualty is a relaunch, not a partial corpus — which is a second argument for one box over three. Budget $15 and a day of attention, not $5.27 and an afternoon.

## 4. THE ROUTE DECISION — AND THE CONFOUND RH ALREADY REFUSED ONCE

There are two instruments here and they are not the same measurement.

**(A) Plain twp over the manifest contexts.** Writes `twp_words` at rule_version 3, consumed by `verse_capacity.py` with no code change: `class_pull` = target-rime-class mass minus `p(target word)`, nonpartner class as the control, censored share per cell. Costs exactly §2. This is the route @lacan's framing assumes.

**(B) The verse-fleet producer with the closure rider ON.** `verse_fleet_producer.py` already computes `p_close` per candidate — newline-family mass at the branch's final position — and **the rider never ran**; corrected at [6062], zero `close_given_class` / `p_close_actual` fields in any fleet jsonl. Turning it on gives `line_closure` x `rhyme_given_closure`. Cost: one batched forward over ~40 candidates per slot on top of the prefix pass, so **2-3x §2 — call it $11-16 and 10-15 GPU-h**, still trivial.

**Route A inherits the exact confound RH caught before any cell was measured.** `plan_rhyme.md`, 2026-08-13: *"a non-rhyming slot distribution may mean the model does not know THE LINE ENDS THERE (a metrical failure), not that it cannot rhyme."* The fix was a decomposition and it became the design.

**On the architecture question that confound is not a nuisance, it is the rival hypothesis.** A recurrent or SSM model that scores low on rime-class mass may be failing to count syllables to a line boundary — a working-memory claim about the state vector — rather than failing to anticipate a rime. Those are different findings about the same number, and only the second is about the paradigmatic axis Weatherby names. Route A cannot separate them; route B separates them by construction and yields two capacities from one instrument, `line_closure` (meter) and `rhyme_given_closure` (rhyme), which **may have different onsets and may differ by architecture in opposite directions.**

Route B additionally requires **re-running `allenai/Olmo-3-1025-7B`** for closure, since its existing 1,786 cells carry word mass only: +1,786 x 0.323 s = 0.16 GPU-h, $0.17. Not a reason to prefer A.

**Recommendation: route B.** The price difference is $6 and the design difference is whether the result answers the question.

## 5. PINS AND CORRECTIONS THE FLEET MUST CARRY

**Pin rule_version 3, not the canonical v4.** The Olmo-3 comparison cells are v3 — `rule_version` selects the TABLE, and the ladder exists only in `twp_words`. Running the 11 at v4 would put them in `twp_words_v4` and leave every cross-model contrast reading an empty join. This bites hardest here because several of these tokenizers are byte-level, which is precisely where `ff6fd56b` measured v4 diverging from v3.

**Two things in the framing as relayed are wrong, and both are already right in the roster.**

1. *"the SSM and hybrid models need env.profile ssm in roster/models/models.yaml"* — **already done.** All four that need it carry `profile: ssm` today: `falcon-mamba-7b`, `Falcon-H1-1.5B-Base`, `Falcon-H1-7B-Base`, `Zamba2-7B`. Nothing to add.

2. **`Olmo-Hybrid-7B` is NOT an `ssm` model and the `ssm` profile does not help it.** It is a Gated DeltaNet — linear attention, not Mamba — and its kernels come from `flash-linear-attention`, not `mamba-ssm`. The roster's own `packages_why` records the cost of getting this wrong: without `fla`, transformers **silently** substitutes a pure-PyTorch recurrence with no warning in any log, measured at **19.0 s/cell on an A100 with the GPU 6% busy** and 19.10 on MPS — identical on both devices, the signature of a path that reaches neither. That is 8x the 2.373 this spec budgets, and it cost ~2 h of A100 time before the cause was found. The assertion to make on the box is `transformers.models.olmo_hybrid.modeling_olmo_hybrid.is_fast_path_available`, not an import check on the mamba kernels, which pass cleanly while this fails.

   **`fla` is CUDA-only** (every backend extra needs triton; there is no Metal build), so Olmo-Hybrid cannot be done on the Mac at any version. It is the one model here that forces the rental.

**Per-model pins beyond the profile,** all from the roster's own `why` fields:

    Falcon-H1 x2    dtype bfloat16 -- fp16 gave ALL-NaN logits on 2,583/2,583
                    prompts, and NaN passes every structural gate: every
                    comparison against NaN is False, so nothing clears theta,
                    tail reads exactly 1.0, and conservation closes on a cell
                    that measured nothing. This has now cost the campaign twice.
    Falcon-H1 x2    transformers >=4.57,<5  -- a HOLE, not a floor: 4.57.1 works,
                    5.4.0 raises on use_cache, 5.14.1 works again
    Zamba2-7B       transformers >=4.57,<5  (v5 tie_weights_keys validation)
    OLMoE, falcon-7b, Olmo-3   tf457 -- transformers 5 rejects their configs
    Olmo-Hybrid     transformers >=5 -- model_type olmo_hybrid is ABSENT from
                    4.57.1's CONFIG_MAPPING_NAMES. The OLMo family splits across
                    the version boundary in OPPOSITE directions.
    gemma-2-9b      compute bf16, storage f16

**Verify the kernels are IN USE, not installed:** the check is that `"the fast path is not available"` is ABSENT from a load that SUCCEEDED. The runbook records that string appearing during a FAILED load with the kernels perfectly fine, which sends you to rebuild what already works.

## 6. THE THREE MATCHED CONTRASTS — ALL COVERABLE, AND ONE IS WEAKER THAN THE OTHER TWO

    1  CONTROLLED BY DESIGN (AI2)                       run   $
       allenai/Olmo-3-1025-7B     full         dense    have  --     (1,786 already)
       allenai/Olmo-Hybrid-7B     full+linear  hybrid   YES   1.20
       allenai/OLMoE-1B-7B-0125   full         moe      YES   0.76

    2  SAME PRETRAINING CORPUS (Google)
       google/gemma-2-9b          full         dense    YES   0.28
       google/recurrentgemma-9b   local+linear hybrid   YES   0.43

    3  ONE VENDOR, THREE BLOCK TYPES (TII, all ~7B)
       tiiuae/falcon-7b           full         dense    YES   0.23
       tiiuae/falcon-mamba-7b     none         ssm      YES   0.70
       tiiuae/Falcon-H1-7B-Base   full+ssm     hybrid   YES   0.36
       tiiuae/Falcon3-7B-Base     full         dense    YES   0.21

    OFF-CONTRAST, cheap, and worth carrying
       Zyphra/Zamba2-7B           full+ssm     hybrid   YES   0.53
       tiiuae/Falcon-H1-1.5B-Base full+ssm     hybrid   YES   0.21   (scale control on H1)
       RWKV/rwkv-4-7b-pile        linear       dense    YES   0.36

**Yes to all three. $6.27 for the contrast models, $1.10 for the three extras.**

**Contrast 3 is the weakest and should not be reported as the vendor control it looks like.** One vendor is not one corpus: `falcon-7b` is RefinedWeb, `Falcon3` and `Falcon-H1` are later and different mixtures, and `falcon-mamba` is different again. It is four models from one lab, which is weaker than contrast 1 (a deliberate layer swap) and weaker than contrast 2 (an asserted same-corpus pair). Contrast 1 is the only one where the architecture is the declared manipulation.

## 7. WHAT THIS BUYS, AND WHAT IT DOES NOT

**Buys:** a sharper instrument. Within each model the replicate is the poem — 178 distinct `called` contexts, 60 per scheme class (ABAB / AABB / unrhymed), paired within poem across models, sign tests over poems. That is real power on *whether a given model has rhyme pull*, and it measures the paradigmatic axis directly instead of through charge.

**Does not buy: more n on the architecture axis.** The between-architecture comparison is still 2, 2 and 4 models. The existing charge finding did not fail for want of precision on each model — it failed because *the two best-controlled contrasts disagreed in sign*, and 178 poems per model does not make two models into more than two. **If rhyme pull also disagrees in sign between contrast 1 and contrast 2, that is the same null arriving on a better instrument, and it should be read as evidence about the architecture axis rather than about the instrument.** Worth saying before the run, not after.

**Does not touch alignment.** These are eleven base models. Weatherby's claim is about the architecture, so a capacity read on bases is the right test — but nothing here says anything about where rhyme pull moves under SFT/DPO, which is `plan_rhyme.md`'s second question and a separate spend.

**The memorization fence is inherited and unresolved.** The primers are real poems and several of these models are Pile-trained, where Dunbar sits. `p_actual` is reported apart from class mass, and `plan_rhyme.md` nominates a constructed-primer arm as the memorization probe. **That arm has never been built.** A model that continues a real quatrain in rhyme and cannot continue a novel couplet is remembering, and nothing in this fleet distinguishes those. It is not a reason to delay — the constructed primers are free to write and can ride a later pass — but it should be a stated bound on the first result, not a discovery afterwards.

## 8. ONE ROUTE WARNING INHERITED FROM `verse_capacity.py`

The fleet's full-distribution `.f16` tier (58.9 GiB for the original 250 models) **is not reachable through the cache layer.** `data/logit_dir_resolution.json` maps `cloud_run_20260801` and `f11_twp` only; `data/logit_index_provenance.json` resolves basenames under `MALIGN_LOGIT_ROOT`, defaulting to `cloud_run`. Neither contains a `verse_fleet` entry, so `cache.get_logits` cannot see it. If this fleet writes a tier of its own, it must either extend the dirmap or be read directly — and whoever migrates it has to point the route at wherever it went.

## 9. TWO DEFECTS IN THE PLANNING INSTRUMENT THIS SPEC HAD TO WORK AROUND

Found while pricing, not looked for. Both make `malignment.rates` **overstate** cost, so neither endangers this fleet — but `scripts/fleet_shards.py` prices every shard through `rates.seconds()`, so both are live for any planner that trusts the library instead of reading the file.

**(a) A RETRACTION THAT WAS APPENDED RATHER THAN APPLIED.** `rates.py:344` correctly excludes `retracted` rows, and its comment says so. But the retraction was written as a NEW jsonl row beside the original, and **the original survives un-flagged at the same `observed` timestamp**:

    tiiuae/Falcon-H1-7B-Base      cuda  n=2981  0.0677  retracted=True   2026-08-20T18:56:09
    tiiuae/Falcon-H1-7B-Base      cuda  n=2981  0.0677  retracted=None   2026-08-20T18:56:09

Two such twins exist (`Falcon-H1-7B-Base`, `Falcon-H1-7B-Instruct`). So `rate_for('tiiuae/Falcon-H1-7B-Base', 'cuda')` returns **0.33525** — the median of the struck 0.0677 and the good 0.6028 — on a row whose own `retracted_why` ends *"rate_for() must not return this."* **The guard works; the data routed around it.** This spec uses 0.6028.

**(b) A LOAD-DOMINATED SAMPLE THAT CLEARS `MIN_CELLS`.** `rate_for('allenai/Olmo-Hybrid-7B', 'cuda')` returns **10.796**, the median of the n=42 `fla`-fallback observation (19.2193) and the n=2,664 real one (2.3734). `MIN_CELLS = 25` was set to kill the OLMoE 3-cell defect and 42 clears it, so the fallback measurement enters as an equal vote. A planner budgeting this fleet from the library would price Olmo-Hybrid at 4.9 GPU-h instead of 1.14 — **alone more than this entire fleet.** This spec uses 2.3734.

Neither is fixed here; both are one-line changes and the second is a judgement (raise `MIN_CELLS`, or weight by `n_cells`, or retract the n=42 row as a fallback measurement rather than a rate) that belongs to whoever owns `rates.py`.
