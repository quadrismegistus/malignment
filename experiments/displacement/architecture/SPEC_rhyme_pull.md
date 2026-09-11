---
kind: spec
status: SPEC ONLY, nothing run. Written 2026-09-11 on RH's ask relayed by @lacan. No box rented, no cell measured.
question: Can the verse-slot instrument be extended across architectures, and what does it cost?
headline: "AMENDED by 22eb96d0 to the DELTA DESIGN ($10.86 route A / $23-33 route B, ~10 GPU-h): the recorded prediction is not testable on bases alone. Base-only was $5.27 of compute, 5.0 GPU-hours, one box, half a working day wall-clock — and the full 1,633-prompt slot manifest is cheaper than the meeting about whether to sample it. All three matched contrasts are coverable. Two things in the framing are wrong: the `ssm` profile is ALREADY set for the four models that need it, and it does NOT cover Olmo-Hybrid, which needs `flash-linear-attention` instead."
---

# SPEC — rhyme_pull across architectures

RH's ask, via @lacan: cost and wall-clock, number of prompts, which models, and whether the three matched contrasts can all be covered. **Nothing here has been run.** Every number below is labelled measured, transferred, or estimated.

## 0. THE HEADLINE, AND THE ONE DESIGN DECISION THAT IS NOT MINE

    AMENDED 2026-09-11 by 22eb96d0 -- see section 10. The recorded
    prediction needs BOTH ARMS, so the figure that matches it is the
    delta design, not the base-only one. Both are priced.

                          base only        + aligned arm (THE DELTA DESIGN)
    route A (plain twp)   5.02 GPU-h       10.34 GPU-h
                          $5.24            $10.79
    route B (+ closure)   $5.64            $11.62          <- RECOMMENDED
    wall clock            ~6.5 h, one box  ~9-11 h, one box
    prompts               ~1,621 per model, the whole missing slot manifest
    models                11 base to run (1 done) + 12 aligned
    contrasts             all three coverable, on either arm

    CORRECTED 2026-09-11, section 11. Route B was priced at 2-3x and is
    MEASURED at +9%. And the coverage table in section 1 was built on an
    unescaped TSV read; Olmo-3's 502 should be 1,786.

**Do not sample.** RH's ask allows one ("a sample is fine, the pilot used 12 primers plus 8 unrhymed"). The full manifest is ~1,621 prompts per model at a median 0.62 s/cell, which is **twenty minutes of A100 time per model**. A 20-primer sample would save about $4.80 and cost the within-poem pairing that the whole design rests on. Sampling here is a false economy by roughly two orders of magnitude.

**§4 framed the route as RH's decision on a cost trade-off. §11 removes the trade-off: the closure rider is measured at +9%, not the 2-3x stated there.** The design question stands and the price difference does not.

## 1. WHAT IS ACTUALLY MISSING — verified, not inherited

@lacan's count reproduces and then sharpens. Against `source='raw/verse_fleet_merged'`, 11 of 12 are absent and only `allenai/Olmo-3-1025-7B` has all 1,786. But `verse_capacity.py`'s own read discipline selects **by the manifest's prompt set across all sources**, because the fleet's overlap rows sit under older labels — so the source filter is the wrong check. Run properly (manifest contexts intersected against every source in `twp_words`):

    model                        of the 1,786 manifest contexts    to measure
    allenai/Olmo-3-1025-7B                    1,786                       0
    tiiuae/Falcon-H1-1.5B-Base                  166                   1,620
    RWKV/rwkv-4-7b-pile                         166                   1,620
    allenai/Olmo-Hybrid-7B                      166                   1,620
    allenai/OLMoE-1B-7B-0125                    166                   1,620
    tiiuae/Falcon3-7B-Base                      166                   1,620
    tiiuae/falcon-mamba-7b                      165                   1,621
    tiiuae/Falcon-H1-7B-Base                    165                   1,621
    google/recurrentgemma-9b                    165                   1,621
    google/gemma-2-9b                           165                   1,621
    Zyphra/Zamba2-7B                            160                   1,626
    tiiuae/falcon-7b                            160                   1,626
                                                        TOTAL        17,836

CORRECTED 2026-09-11 — an earlier version of this table read 502 for Olmo-3 and ~153 for the rest. See §11: the intersection was taken against `ch.raw()` TSV output without unescaping, so every multi-line context and every apostrophe failed to match. `FORMAT JSONEachRow` is the route that works.

**The ~165 each already holds are entirely `prose` and `battery` calibration slots** — contexts that happen to coincide with the general 2,983-prompt battery. Checked on `falcon-mamba-7b`: 61 battery + 92 prose, and **zero** of any verse slot. So the absence is total where it matters and the overlap is free calibration, which is the good version of this news: the battery slots that price the single-token bias arrive already measured.

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

## 10. ADDENDUM 2026-09-11 — THE PRE-COMMITMENT NAMES A PREDICTION THIS FLEET CANNOT TEST

Written after reading `dc463976` (the pre-commitment) and `51147165` (the local/global reading it pins). **Both are right to exist and this does not dispute either.** It reports a grain mismatch between the prediction and the fleet, found before the fleet ran, which is the only time it is cheap.

**The prediction, as recorded:** *"if global attention is what carries the operation, the same ordering should appear on the paradigmatic instrument."* The ordering it refers to is `-0.000159 -> -0.000257` and `-0.000498 -> -0.000114` — **displacement**, a base→aligned delta in charge-selectivity.

**The fleet, as specced in §1-§6, measures eleven BASE models.** There is no delta. `rhyme_pull` on a base model is a CAPACITY — does this model have rhyme pull — and a capacity has no ordering commensurable with a delta across an alignment edge. A base-only fleet returns a number for `gemma-2-9b` and a number for `recurrentgemma-9b`, and the difference between them is an architecture-plus-corpus fact about two base models, not the thing `-0.000498 -> -0.000114` measured.

This is the campaign's own rule and `plan_rhyme.md` states it first, in its anti-conflation clause: *"No sentence reads them against each other without a declared bridge."* It was written about slot-pull versus sustained form; it applies unchanged here.

**Two repairs, and they are not equivalent.**

**(i) Add the aligned arm.** `roster.endpoints()` resolves an aligned endpoint for all twelve — checked, none is `unresolved`:

    falcon-mamba-7b        -> falcon-mamba-7b-instruct      Zamba2-7B     -> Zamba2-7B-Instruct
    Falcon-H1-1.5B-Base    -> Falcon-H1-1.5B-Instruct       rwkv-4-7b-pile-> rwkv-raven-7b
    Falcon-H1-7B-Base      -> Falcon-H1-7B-Instruct         gemma-2-9b    -> gemma-2-9b-it
    recurrentgemma-9b      -> recurrentgemma-9b-it          falcon-7b     -> falcon-7b-instruct
    Olmo-Hybrid-7B         -> Olmo-Hybrid-Instruct-DPO-7B   Falcon3-7B    -> Falcon3-7B-Instruct
    OLMoE-1B-7B-0125       -> OLMoE-1B-7B-0125-Instruct     Olmo-3-1025-7B-> Olmo-3-7B-Instruct

None holds any verse slot either (each has the same ~150 prose/battery overlap), so each needs ~1,633. Priced the same way, eleven rates measured and `gemma-2-9b-it` transferred:

    ALIGNED ARM   5.32 GPU-h   $5.59      route A
                  ~$12-17                 route B

**So the delta design is ~$11 on route A and ~$23-33 on route B, against $5.27 and $11-16 for base-only.** The increment buys the thing the prediction is about. `Olmo-3-7B-Instruct` is in this arm and must run even though its base is already done, for the same reason route B has to re-run the base: the delta needs both ends measured the same way.

`Falcon-H1-7B-Instruct` is priced at **0.5550**, not the 0.310 `rate_for` returns — it carries the same appended-retraction defect as its base sibling (§9a), a struck 0.0659 medianed against the good rate. Both twins are the Falcon-H1 7B pair.

**(ii) Restate the prediction at capacity grain.** Free, and it changes what is under test: *"global attention supports rhyme capacity"* is a claim about architecture, while *"global attention carries the operation"* is a claim about what alignment does. The second is the one the folder is about and the one Weatherby's sentence is about. Restating is legitimate, but it has to be done **now and explicitly**, because a prediction quietly reinterpreted to fit the arm that was affordable is exactly the standing the pre-commitment exists to protect.

**Recommendation: (i), and it is not close.** The increment is $6 on route A and the pre-commitment's own point 4 — that the route out is models, not cells per model — argues for it directly: the aligned arm doubles the models without touching the n=2-per-contrast problem, but it is the difference between testing the recorded prediction and testing a different one.

**This does not reopen the pre-commitment.** Points 1, 2 and 4 are untouched. Point 3 is untouched in substance; what it needs is a sentence naming the grain at which "the same ordering" is read, and that sentence is cheaper to write today than to argue about once there are numbers.

### RESOLVED the same day, by `22eb96d0`

Point 3 is amended, before any cell: the prediction **requires both arms and is not testable on bases alone.** The amendment is better than the choice this section offered, because it declines it — repair (ii) is not needed and repair (i) is not a replacement:

> **Weatherby's claim is about the architecture**, so a base-only capacity read is the right test OF HIM. **The comparison with the charge instrument needs the delta.** The delta design answers both, because it contains the base arm.

That is right and this section was wrong to frame the two as alternatives. It also supplies the reason I only gestured at: **every number in the folder is a base→aligned delta** — `existence` regresses `(p_aligned - p_base)` on scene, `norm_change` regresses `(aligned - base)` on the base dose — so a base capacity has no grain in common with any of them.

**The live figure for RH is therefore the delta design**, $10.86 on route A and $23-33 on route B, not the base-only $5.27 / $11-16 that §0 led with before this amendment.

## 11. CORRECTIONS 2026-09-11, AND THE POPULATION QUESTION

Three things, on RH's questions (runpod / population / boxes / card). Two are corrections to this file.

### (a) THE CLOSURE RIDER IS +9%, NOT 2-3x. MEASURED.

§4 priced it at 2-3x on the assumption that each of the pilot's `TOP_K = 40` candidates costs a forward. Wrong on both counts: `verse_fleet_producer.closure_rider` batches, and it rides `N_RIDER_CLASS = 8` plus the actual word — **nine rows in ONE forward**, not forty.

Measured locally, SmolLM2-360M on MPS, over 12 real verse slots from the manifest:

    expand() forward calls   median 3   (range 2..6)   -- the beam is SHALLOW here
    words per cell           median 140
    expand()                 0.677 s
    closure rider            0.062 s    (9 rows, one batched forward)
    -----------------------------------------------------------------
    RIDER                    +9%        0.677 -> 0.739 s per slot

**The beam is the cost and it is only 2-6 passes at these contexts**, so one more batched forward is noise. Scope: one small model, one device, 12 slots; both terms are batched forwards over the same context, so the ratio should carry, but it is not measured at 7B on CUDA.

**So the route decision is now free.** Route B costs $5.64 against route A's $5.24 on the 12 bases, and $11.62 against $10.79 on the delta design. §0 and §4 are updated; the design argument in §4 is unaffected and is the whole argument.

### (b) THE COVERAGE TABLE IN §1 WAS BUILT ON AN UNESCAPED READ

`ch.raw()` returns TabSeparated, which escapes newlines and quotes. I intersected the manifest's contexts against those strings directly, so **every multi-line verse context failed to match**, and Olmo-3 — which has the complete set — scored 502 of 1,786. `ch.json` is the stdlib module, not a helper; the route that works is `FORMAT JSONEachRow`.

Corrected: Olmo-3 has **1,786 of 1,786**, the other eleven have 160-166 each, and the fleet is **17,836 cells**, not 11 x 1,633 = 17,963. The cost moves by under 1%. **What did not move by under 1% is the Olmo-3 row, which was wrong by 3.6x in a table whose column header said what it was counting.** The lesson is the campaign's own: a filter between the producer and the corpus is invisible from both ends, and here the filter was the transport encoding.

### (c) THE POPULATION. Four are defensible and they cost very differently.

`roster.population()` names them; there is no `endpoint_lineages`. Priced the same way, route B, corrected coverage:

    population                             models    cells     GPU-h        $
    12 architecture bases                      12   17,836       5.4     5.64
    + their aligned arm (the delta design)     24   37,303      11.1    11.62
    all bases + all endpoints ("50 x 2")      100  158,795      30.2    31.67
    every declared node                       160  252,575      45.3    47.57

Rate provenance holds up at every size: at n=160, **120 measured / 36 transferred / 0 guessed**.

**The verse fleet was NOT a breadth population and this is the thing to know before choosing.** Its 250 files are five repos' checkpoint ladders — `pythia-6.9b` x 155 rungs, `Olmo-3-1025-7B` x 43, `Olmo-3-7B-Think-SFT` x 44, `Olmo-3-7B-Think` x 7, `Think-DPO` x 1. It answered `plan_rhyme.md`'s question 1, WHEN rhyme installs, by depth in one lineage. The architecture question is question 2's shape and needs breadth. **They share the prompts and nothing else**, so this is a new population on an old manifest, not an extension of the fleet.

Given that, `all bases + all endpoints` at **$31.67** is the one I would argue for over the 24. Not because the architecture contest needs it — it does not, 24 answers that — but because it makes `rhyme_pull` a roster-wide instrument on the same footing as `existence` and `norm_change`, both of which run on 50 and 45 pairs. At n=100 the architecture models stop being eight positions asserted against a median computed on a different instrument and become eight positions in this instrument's own distribution. That is the pre-commitment's point 4 — the route out is models — bought for $20.

**`every declared node` at $47.57 is not worth the extra $16 here**, because the extra 60 are intermediates and ablations that answer a within-lineage question this instrument is not being pointed at.

### (d) BOXES AND CARD

**Yes, separate boxes, but fewer than five.** The 12 split across five environments (`ssm`, `default`+`fla`, `default`, `tf457`, `bf16`) and `scripts/venvs.py` derives the venv per model, so venv differences are free on one machine. The real cut is **kernels**: the `ssm` box compiles `mamba-ssm` + `causal-conv1d` from source (~30 min), and Olmo-Hybrid needs `flash-linear-attention` instead. Two boxes is the natural shape at n=12 or 24 — one with the mamba kernels, one without — and at n=100 shard by lineage per `scripts/fleet_shards.py`, whose measured finding is that all 50 endpoint lineages need exactly one venv each and that beyond ~12 boxes the wall clock stops moving.

**A 4090 is enough, and it is measured rather than argued.** The corpus was largely produced on consumer and workstation cards — 44 observations on RTX 4090, 48 on Quadro RTX 8000, 17 on RTX 6000 Ada, and only 5 on an A100. Specifically: `recurrentgemma-9b`, the worst VRAM case here at 9B with a **256,000** vocab, wrote 2,983 cells on an RTX 4090; `Zamba2-7B` ran on a 4090 **with** the mamba kernels; `falcon-7b` and `Olmo-3-1025-7B` likewise. The one caveat is compile target: the runbook's kernel build pins `TORCH_CUDA_ARCH_LIST=8.0`, which is Ampere — a 4090 is 8.9 and needs `8.9`, or the kernels build for the wrong card.

On runpod, live catalogue read 2026-09-11: **RTX 4090 $0.34/hr, A40 $0.35 (48 GB), L40S $0.79 (48 GB), A100 SXM 80 GB $1.39**, all stock `Low`. At $0.34 the 4090 is **4x cheaper than the A100 this spec priced at $1.05**, so every figure above is an upper bound: the delta design is **$3.76 on 4090s**, and all-bases-plus-all-endpoints is **$10.26**. If a 4090's 24 GB is tight for the two 9B models, the A40 at 48 GB is a cent dearer. **Nothing here needs an A100.**

### (e) RUNPOD: THE PRODUCER PORTS, THE ORCHESTRATION DOES NOT

`verse_fleet_producer.py`, `scripts/queue_v4.py` and `scripts/topup_lineage.py` are torch + transformers and care about nothing below them. What is vast-specific is the renting: `scripts/fleet_launch.py` takes vast offers, `malign cloud` wraps the vast CLI, and `data/cloud_profiles.json` describes machine shapes in vast's vocabulary (`gpu_name`, `min_reliability`, `cuda_max_good`, `min_inet_down_mbps`). Those are a provisioning layer to rewrite, not a measurement layer. **The preflight and the casualty discipline in `docs/cloud_runbook.md` are about what the box does after it exists and transfer unchanged** — including §2.13, and including the rule that the discriminator for a stalled box is HF cache growth rather than "instance running", which is the rental and not the work.

## 12. ONE RECORD TYPE, NOT TWO — RH's question, answered against the code

**Normal `~/malignment-data/twp` records. One extra top-level key on the verse cells. No second file, no second producer, no second rsync.**

    ~/malignment-data/twp/<org>__<model>/<host>/<hash>/...     unchanged layout
    record   {model, prompt, theta, device, rule_version, rows, residual,
              conservation, ...,                              <- normal, unchanged
              "closure": {"k": 40, "nl_ids": N,
                          "words": {w: p_close}}}             <- verse cells ONLY

### Why one and not two

- **Two files let closure arrive without its cell.** The `.f16` tier is this campaign's own example: 59 GiB collected, paid for, and holding zero live readers because nothing downstream could reach it. Inside one record they cannot separate.
- **Two producers mean two stamps.** `ingest._key_body_agree` exists because `run_v4.py` built a stamp and then became a thin wrapper around `Runner`, whose stamp did not know those fields — 2,706 cells correctly keyed and filed as something else.
- **The rsync already carries it.** `fleet_launch.py --pull-every` pulls `/root/malignment-data/twp` on a loop; closure is inside those files. A second path is a second thing to forget at 2h50m of a 3h shard.

### Why it is safe, checked rather than assumed

    ingest include predicate   needs rule_version + rows + residual; unknown
                               top-level keys are ignored       (asserted in the smoke, 30/30)
    _key_body_agree            compares only INSTRUMENT_FIELDS =
                               rule_version, dict_sha, rules, prompt_cache,
                               frame, system, system_set, user_msg
                               -- `closure` is not one of them
    the stash key              ck.key(p, rules, frame=..., ...) -- body keys
                               do not enter it

So **`ingest.py` needs no change at all** for the words. A second small ingester reads the same files for the `closure` key into the sidecar.

### The producer change is one place

`runners.run()` builds `rec = dict(stamp, model=..., prompt=p)`, expands, then `rec.update(rows=..., residual=..., conservation=...)` before `st[ck.key(...)] = rec`. Closure attaches at that same point: call `closure_rider` on the top-K surfaces and set `rec["closure"]`. Roughly six lines plus a flag to plumb through `run_v4.py` / `queue_v4.py`.

**Gated on the verse manifest, not on every prompt.** The rider costs +27% and means nothing at a non-verse slot, so the box is shipped the manifest's 1,786 context strings as a plain list — **a list of strings, no phonology**, consistent with §11's gate.

### The consequence a reader must not get wrong

`twp_closure` is SPARSE against `twp_words` by design, on two axes: only verse cells carry it, and within a cell only the top K=40 surfaces do. The ~165 prose/battery contexts each model already holds were measured without it and stay that way. **So absence is not zero**, and `k_rider` travels on every row so a consumer can tell "not measured" from "measured at 0". That is the same failure the lineage-union topup pass exists to prevent — a word a sibling cleared and this model did not, which a consumer would otherwise impute as zero.
