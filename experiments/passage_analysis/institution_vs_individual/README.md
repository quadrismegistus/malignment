---
kind: question
subject: passage_analysis
question: When alignment answers a party to a dispute, does what it tells them to do depend on which side of the dispute they are on?
status: RUN 2026-09-23/24 -- F21 corpus coded (pass 1); 43-lineage 256-token regeneration run and coded; four declared predictions all supported on both units
headline: >-
  Alignment tells the institution to TALK and sends the individual ELSEWHERE.
  Aligned landlords, managers and officers are told to take it up directly with
  the other party (0.31 -> 0.75); aligned tenants, workers and patients are
  referred on -- to a regulator or collective (0.13 -> 0.33), and above all into
  the counterparty's own apparatus, its HR or billing department (0.09 -> 0.43).
  The institution side's referrals barely move.
---

# institution_vs_individual

## The finding

On a 256-token regeneration over **43 lineages × 18 disputes × both sides**, with the base model raw and the aligned model in chat, all four predictions declared before any regenerated text existed hold. Each is sign-tested by dispute (18) and by lineage (39), Holm-corrected over the four (`results/analysis_regen.md`):

| prediction | individual, base → aligned | institution, base → aligned | disputes | lineages |
|---|---|---|---|---|
| P1 individual sent **outward** (public authority or collective) | 0.133 → 0.328 | 0.042 → 0.052 | 15/3 | 34/5 |
| P2 institution given **direct voice** with the counterparty | 0.211 → 0.448 | 0.309 → 0.752 | 2/16 | 4/35 |
| P3 individual sent to bodies with **authority over the counterparty** | 0.139 → 0.318 | 0.051 → 0.060 | 15/3 | 33/5 |
| P4 individual sent into the **counterparty's own channels** (its HR, its billing) | 0.088 → 0.427 | 0.018 → 0.025 | 17/1 | 34/4 |

Holm p is 0.015–0.0006 by dispute and 5e-6–1e-6 by lineage. The shares are of coherent, on-topic continuation and advice texts that keep the prompt's speaker. Referrals count only when the text recommends them, or when a quiz item marks them correct.

Not predicted, but in the same direction: exit and self-help nearly disappear on both sides, and bringing in a third party as the main move rises only for the individual (0.34 → 0.46, against 0.18 → 0.11 for the institution). In-house help (speaker_side) rises on both sides, with no reliable difference between them.

Eight random pairs are in `results/examples_regen.md` (seeded, not selected). A typical one: RedPajama-Chat sends the tenant with broken winter heating to "your local housing office or the landlord ombudsman", and tells the landlord facing repair demands to have "a professional" inspect. falcon-7b-instruct offers the laid-off worker "freelance or remote work" (exit), and asks the manager who laid them off "have you tried to mediate the situation with your team?" (direct voice).

## Why this question, and not F21's

F21 (malign-logits `findings/F21_institutional_alignment.md`) claimed that alignment proceduralises individuals and not institutions. That claim depended on an undeclared cut and an undeclared arm. At its own units (`slot_ratings/institutional/f21_prompt_unit.py`), deference and agency rise equally on both sides, and the deference gap between the sides comes from pretraining.

Reading the generations (RH, 2026-09-23) suggested the asymmetry might lie in WHERE each side is sent, not how deferential it is. F21's scales score "contact the housing authority" (tenant) and "seek a legal consultation" (landlord) the same, both deference 4 and agency 4. One is an appeal to a body with power over the counterparty; the other is a call on the speaker's own apparatus. `task.py` codes that direction.

## The instrument (`task.py`, v2)

One pass per generation on `deepseek-flash`. The coder sees the prompt as context and the generation as text, plus the speaker and counterparty from the design. It is never told which side is individual or institution, which model wrote the text, or which arm it is. It codes:

- **form**: continuation, advice, user_request, quiz_item, web_boilerplate, other_language, degenerate. No F21 pass asked this. v2 added user_request, because aligned models run without a template were writing the USER's next turn.
- **perspective_kept**: whether the text keeps the prompt's speaker. About a fifth of institution-side texts re-voice the dispute from the other side, in base and aligned alike.
- **every referral**:
  - its relation to the speaker: speaker_side, counterparty_side, public_authority, collective, media_public, personal or other;
  - whether it has authority over the counterparty;
  - the text's stance toward it: recommended, listed, marked_correct, rejected or narrated.
- **primary move**: exit, voice_direct, third_party, self_help, accept or none (Hirschman's exit and voice, with self-help and referral separated).

Every categorical judgement carries a verbatim span, and 99.8% of spans are verbatim on the regeneration. The six worked examples are disputes outside the prompt set, checked.

## Pass 1: the F21 corpus as it stood (`run.py`, `analyse.py`)

The corpus is 20,389 F21 generations: 24 prompts (12 matched pairs), 10 open families at every stage plus 4 frontier chat models. They are ~100 tokens long (`generation.py` max_new_tokens=100) and were read from the malign-logits generation cache, since the CSV clips at 500 characters. Two predictions were declared before the codes were read: outward > 0, inward < 0.

- **v2 filters** (coherent, perspective kept; `results/analysis_v2.md`):
  - The institution gains direct voice: 12 of 12 pairs lean that way (p=0.0005), 9/10 families. This was not predicted, and it is what P2 became.
  - Individual outward: 9/1 families (p=0.02), 9/3 pairs (p=0.15).
  - Authority: 10/2 pairs, 9/1 families.
  - Channel: 11/0 pairs.
  - Inward: null.
- **The 100-token window hid the effect.** Advice was cut off before it named anyone (Sonnet's tenant answer ends at "Contact a **tenant rights"). The site was mixed too: only 6 of F21's 12 pairs end "I should" on both sides.
- **Frontier chat models** (no base; `results/analysis_v2.md`): the individual is sent outward and the institution almost never, 10/0 pairs (p=0.002). Sonnet 4.6 does so for 40% of individuals against 2% of institutions, Haiku 27% against 1%. Authority over the counterparty: 10/0.
- **Form** (`results/analysis.md`): aligned models write more quiz items, 9.4% → 13.6% (8/1 families). That is partly a symptom of running instruct models without their template.

## The regeneration (`prompts.py`, `fleet/`, `run_regen.py`, `analyse_regen.py`)

**Prompts** (`prompts/design.json`): 18 disputes × both sides, 36 prompts, all ending "I should", and none pre-resolved.
- The 6 clean F21 pairs are used verbatim.
- 12 M03 scenarios are rewritten to state the harm with no step taken and no verdict.

`m03_audit.md` shows why M03 as written would not do. In 14 of 18 scenarios the individual has already filed or objected. In 14 of 18 the institution states a verdict ("a refusal I consider correct"). Harm is softened in 7 of the 10 anchored scenarios. That pre-empts the referral contrast on both sides.

**Frame and decoder.**
- Base: raw continuation.
- Aligned: the prompt as the user message under the model's own template and default system prompt. That is the frame the frontier models were run in, and the frame alignment ships in. So **base against aligned compares weights and frame together**.
- `generate.DECODER`: t=1.0, top_p=1.0, top_k disabled, 256 new tokens, n=10, seeds 42+i.

**Fleet.** RunPod A100-80GB pods: `runpod/pytorch` image, `pip vllm==0.22.1`, transformers 4.57.1, `malignment.vllm_generate`. Fixed during the run, all in `vllm_generate` (`89cec931`, `dca22f16`, and falcon):
- **Templated prompts got a second BOS.** They were passed to vLLM as strings (Mistral-7B-Instruct measured `[1, 1, …]`). Rendering now uses the model's own tokenizer, with no added special tokens after a template, and passes token ids.
- **Eight aligned models silently got RAW prompts.** Authored template overrides never reached vLLM's tokenizer wrapper, rendering raised, and the code fell back to raw (AmberSafe, beaver, archangel, hh-dpo, RedPajama-Chat, AquilaChat2, bloomz, CT-LLM). A refused condition now fails the run instead.
- **The roster wrongly said three OLMo instruct models had no template.** Their chat prompts were skipped with exit 0. The tokenizer is now consulted.
- **Caught failures now reach the exit code.**
- **Specific models:**
  - Aquila2-7B is now loaded at the roster's revision pin.
  - gemma-2 and Falcon-H1 run in bfloat16. Falcon-H1-7B base wrote 360/360 empty passages at float16, with exit 0.
  - falcon-7b loads with remote code off, under transformers 5.10.2.
  - InternLM2 needs sentencepiece 0.2.1 with tiktoken removed.
- Every aligned passage carries `render=ids_v2`, which is also in its key. `run_regen.py` counts no aligned passage without it.

Engine facts are recorded in `roster/models/observations.json` (`engine_support.*.observed_2026_09_23`).

**Coverage: 43 of 50 lineages** (30,960 passages).
- **Not generated:** RWKV and recurrentgemma (vLLM 0.22.1 refuses both; transformers path only, very slow), OLMo-Hybrid (needs transformers ≥5 plus flash-linear-attention), MPT (config error).
- **Out of the test:** bloomz and CT-LLM-SFT-DPO ship no chat template and have no authored override, so the aligned arm cannot be framed. Teuken base samples ids beyond its tokenizer (250,880 rows against 250,680 pieces) and writes gibberish.

## What limits the finding

1. **The base arm rests on its on-topic minority.** At 256 tokens, 57% of base passages are degenerate. A further ~28% of the on-topic remainder is incoherent, and 18% of institution-side base texts switch perspective. Base shares come from the texts that stay on the dispute.
2. **Weights and frame move together** (raw base, chat aligned). That is declared, but no number here isolates the weights.
3. **One coder.** There is no second-coder agreement check yet. `deepseek-flash` is not a pinned version, and every row carries the served model string.
4. **Lineage n = 39 in the test.** 4 of the 43 had an empty cell after filtering.
5. **The prompts are Claude-written for 24 of 36.** RH has not yet reviewed the unresolved M03 rewrites.

## Next

- Frontier API passages on the same 36 prompts and decoder, so the frontier sits on the regeneration's ruler rather than F21's 100-token one.
- A second coder on a shared sample.
- The four missing lineages, if wanted, through the transformers path.

## Files

    task.py               the coder (v2), design table for F21's 24 prompts
    run.py / analyse.py   pass 1 on the F21 corpus (v1 and v2 codes; --v1 reproduces the first table)
    export_texts.py       F21 texts at full cached length (malign-logits venv)
    smoke.py              the 20-item smoke test
    m03_audit.md          why M03 as written pre-resolves the disputes
    prompts.py            the regeneration's 36 prompts -> prompts/{raw,chat}.jsonl, design.json
    fleet/                RunPod scripts: setup.sh, box.sh, box2.sh (fixed path), hf_box.py, shards
    run_regen.py          codes the regeneration (render rules, exclusions)
    analyse_regen.py      the declared test, committed before any regenerated text existed
    examples_regen.py     seeded random pairs
    results/              analysis.md (pass 1 v1), analysis_v2.md, analysis_regen.md, examples_regen.md

The coded outputs are 20 MB each and live in `~/malignment-data/institution_vs_individual/`.
