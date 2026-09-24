---
kind: question
subject: passage_analysis
question: When alignment answers a party to a dispute, does what it tells them to do depend on which side of the dispute they are on?
status: RUN 2026-09-23/24 -- F21 corpus coded (pass 1); 43-lineage 256-token regeneration run and coded; four declared predictions all supported on both units
headline: >-
  The individual/institution asymmetry is already in the BASE model -- the
  aggrieved party is referred about three times as often, the institution is
  told to talk. What alignment adds is a specific routing: the individual is
  sent into the COUNTERPARTY'S OWN APPARATUS (its HR, its billing office, the
  landlord's management). Within advice-form text on both arms, base already
  sends individuals to regulators and lawyers about as often as aligned does
  (0.27 vs 0.33); the counterparty-channel share more than doubles for the
  individual (0.22 -> 0.47) and stays flat for the institution. Institutions
  get the conversation (direct voice 0.49 -> 0.85 in institutional advice).
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

## The two differences, taken apart (`decompose.py`, POST HOC)

RH, 2026-09-24: "Is the story 'base is already procedural' true? We have two differences to account for." This decomposition was computed after the declared test and is pooled over passages, not tested at the lineage unit (`results/decompose.md`).

**1. Individual against institution: the asymmetry is in the base, in every direction.** Across kept passages, the base refers the individual about three times as often as the institution (outward 0.14 vs 0.05, authority 0.14 vs 0.05, counterparty channel 0.10 vs 0.02), and tells the institution to talk more (direct voice 0.30 vs 0.21). This is the same shape as F21's deference gap: pretraining carries the social pattern.

**2. Base against aligned: mostly a change of genre, plus a real widening.** Aligned models write advice 77% of the time; base models 11%. Referral lives in advice, and base advice is already procedural: it refers the individual in 62% of cases (aligned 78%). Much of the base-to-aligned rise in referral is alignment converting everything into advice. With a raw base against a chat aligned arm, part of that conversion is the chat frame.

Within the same genre, the gap still widens:

| change in the individual-minus-institution gap, base → aligned | within advice | within continuation |
|---|---|---|
| the counterparty's own channels | +0.26 (0.19 → 0.45) | +0.09 |
| direct voice (institution minus individual) | +0.18 (0.20 → 0.38) | +0.13 |
| sent outward | +0.10 | +0.05 |
| authority over the counterparty | +0.09 | +0.06 |

**The takeaway.** Individuals are routed into the other side's own apparatus. Base advice already sends them to regulators and lawyers about as often as aligned advice does (outward 0.27 against 0.33). What alignment adds is "take it to the company's HR, the hospital's billing office, your landlord's management": the counterparty-channel share more than doubles for the individual (0.22 → 0.47) and stays flat for the institution (0.03 → 0.02). Institutions, meanwhile, get the conversation: direct voice rises from 0.49 to 0.85 in institutional advice, against 0.29 to 0.46 for individuals.

The caveats are specific to this decomposition:
- It is post hoc and pooled.
- Base advice is a small, self-selected sample, about 600 texts per side: the base passages that happened to become answers, often forum-style.
- "Within continuation" is thin on the aligned side (472 and 721 texts).

The clean version is a declared lineage-unit test of the within-advice widening, not yet run.

## The frontier, on the same ruler (`frontier_generate.py`, `frontier_code.py`)

The same 36 prompts were run through the API: the prompt as the user message, the vendor's default system prompt, t=1.0, 256 tokens, 10 draws. top_p is pinned only on DeepSeek, where it is measured to be honoured; elsewhere it runs at the vendor default. There is no base, so this is the gap at the endpoint. The analysis was committed before coding (`results/analysis_frontier.md`). Shares are individual / institution:

| | Sonnet 4.6 | Haiku 4.5 | GPT-4o-mini | open aligned (43) |
|---|---|---|---|---|
| sent outward | 0.79 / 0.14 | 0.69 / 0.13 | 0.46 / 0.04 | 0.32 / 0.05 |
| direct voice with the counterparty | 0.19 / 0.74 | 0.25 / 0.74 | 0.42 / 0.95 | 0.45 / 0.80 |
| bodies with authority over the counterparty | 0.74 / 0.16 | 0.66 / 0.15 | 0.43 / 0.04 | 0.30 / 0.05 |
| the counterparty's own channels | 0.42 / 0.07 | 0.48 / 0.07 | 0.60 / 0.01 | 0.45 / 0.02 |

Pooled over the three frontier models, by dispute: outward 18/0 (p=8e-6), direct voice 1/15, authority 17/1, channel 17/0. **The frontier models carry the same asymmetry as the open aligned arm, and on referral they carry it harder.** Sonnet 4.6 sends the individual outward in 79% of answers and the institution in 14%, and gives the institution the conversation three times in four.

`deepseek-chat` now resolves to deepseek-v4-flash, which is served as `deepseek-flash`. That is the coder's own model, so its row is flagged and left out of the pooled test. Its direction agrees: outward 15/1, direct voice 4/12.

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
    decompose.py          POST HOC: the 2x2, and within-genre (advice / continuation)
    frontier_generate.py  API passages (Sonnet 4.6, Haiku 4.5, GPT-4o-mini, DeepSeek) into the generation stash
    frontier_code.py      codes them; the endpoint contrast, declared before coding
    results/              analysis.md (pass 1 v1), analysis_v2.md, analysis_regen.md, analysis_frontier.md, decompose.md, examples_regen.md

The coded outputs are 20 MB each and live in `~/malignment-data/institution_vs_individual/`.
