---
kind: question
subject: passage_analysis
question: When alignment answers a party to a dispute, does what it tells them to do depend on which side of the dispute they are on?
status: RUN 2026-09-23/24 -- F21 corpus coded (pass 1); 43-lineage 256-token regeneration run and coded (42 usable: internlm2 is noise in every cell); four declared predictions all supported on both units
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

On a 256-token regeneration over **42 usable lineages × 18 disputes × both sides** (43 generated; internlm2 is noise in every cell), with the base model raw and the aligned model in chat, all four predictions declared before any regenerated text existed hold. Each is sign-tested by dispute (18) and by lineage (39), Holm-corrected over the four (`results/analysis_regen.md`):

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

**2. Base against aligned: mostly a change of genre, plus a real widening.** Aligned models write advice 79% of the time; base models 11% (42 lineages; results/analysis_regen.md). Referral lives in advice, and base advice is already procedural: it refers the individual in 62% of cases (aligned 78%). Much of the base-to-aligned rise in referral is alignment converting everything into advice. With a raw base against a chat aligned arm, part of that conversion is the chat frame.

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

**Tested at the unit, declared first** (`within_genre_test.py`, `results/within_genre_test.md`; declared at the paper seat's request after the pooled numbers above had been seen, so this checks an observed effect at its proper unit and is not independent confirmation). Within advice, the counterparty-channel gap widens in **25 of 25 lineages** (p=6e-8, median +0.31) and **16 of 17 disputes** (p=0.0003, median +0.27). The floor was at least 5 passages in each base/aligned × side cell. It dropped 17 lineages whose base rarely writes advice; entering lineages have a median of 18 base advice passages per cell (range 5–119). The decision rule fixed in advance says this makes the within-advice widening the evidence for the essay's sentence.

The widening also holds within continuation (channel: lineages 11/2, disputes 15/2). The institution's direct voice widens within advice (lineages 2/23, disputes 4/13, p=0.049). Outward and authority widen within advice by lineage (20/5) but not by dispute (12/5, p=0.14), which is consistent with those being the small part of the story.

## F21's own instrument on the same passages (`f21_task_sample.py`)

F21's `AlignmentAsymmetryTask` was run unchanged, with F21's input convention, on a seeded sample of 4,361 regeneration passages (up to 30 per lineage × arm × side cell) and on all 1,440 frontier passages. The expectations were committed before coding (`results/f21_task.md`).

- **E1 holds: F21's deference scale sees no asymmetry in the change.** Deference rises on both sides: individual 2.88 → 3.36, institution 3.74 → 4.11. The individual-minus-institution change is null (lineages 25/16, p=0.21; disputes 11/7). This is F21's unit result again, on new texts.
- **On the same passages, the deference scale is blind to the routing.** Passages that send the individual into the counterparty's channel have exactly the same mean deference as passages that don't (3.55 against 3.55). Outward referral goes with slightly *lower* deference (3.34 against 3.58); direct voice with higher (3.81 against 3.33). Channel referral does move agency (3.61 against 2.96) and strategy specificity (3.13 against 2.44). So a deference scale cannot register the capture that the referral codes register.
- **E2 holds on specificity and concrete action.** Both rise more for the individual: strategy specificity lineages 38/4, disputes 17/1; concrete action recommended 33/8 and 14/4. "Specific rights named" *falls* on both sides (individual 0.12 → 0.08, institution 0.13 → 0.04). It falls less for the individual (28/11), so the prediction holds in form, but alignment names fewer rights overall.
- **Not expected: the individual is given homework.** "Homework assigned" (document everything, gather evidence, keep records) rises from 0.19 to 0.73 for the individual and from 0.22 to 0.49 for the institution (lineages 37/4, disputes 16/2). F21's "agency" rises more for the individual too (35/7). Read beside the channel result, the agency alignment grants the aggrieved party is procedural labour, done inside the other side's apparatus.
- **Apology:** no side difference in the change (lineages 20/21). The frontier differs by model: GPT-4o-mini apologises to the individual in 56% of answers against 9% for the institution ("I'm sorry to hear…"); Haiku almost never apologises.
- **Frontier, at the endpoint:** every model scores the individual lower on deference than the institution (Sonnet 2.60 against 3.85), and higher on agency, assertiveness and specificity.

## A check with no LLM in the measurement: USAS fields (`usas_test.py`)

USAS semantic fields from the repo's lexicon (93% token coverage), measured on the passage text only. The primary population is every regeneration passage, unfiltered, so the LLM coder is not in the selection either. Two predictions were declared before tagging (`results/usas_test.md`). The file states in advance that a word field cannot test P4: it can't say whose department.

- **U1, supported.** Government and law vocabulary (G1, G2) rises for the individual and falls for the institution: individual 15.9 → 19.5 per 1,000 tokens, institution 14.9 → 13.6. Lineages 38/4, disputes 15/3, Holm-significant on both units. That is P1's direction, confirmed by an instrument no LLM touches.
- **But within advice alone (secondary), it does not widen** (lineages 8/5). The individual/institution gap in legal vocabulary is already there in base advice (21.1 against 15.5). So U1 is largely the genre shift: aligned models write advice, and advice to the aggrieved is legalistic. This matches the decomposition, where outward was the small part of the widening.
- **U2, not supported, and reversed.** Speech vocabulary (Q2) rises MORE for the individual (29.4 → 49.5) than for the institution (35.0 → 46.2): lineages 37/5 the wrong way. A post-hoc look at the words shows why. On the aligned side, the individual's speech words are *request, appeal, consult, statement, contact, claim, complaint*: procedural speech addressed to a body. The institution's are *communication, conversation, explain, acknowledge, apologize*: relational speech addressed to the other party. Splitting Q2.1 (speech) from Q2.2 (speech acts) doesn't help; both rise more for the individual. **A word field cannot separate "talk to them" from "file a request with someone": the individual's procedure is itself made of speech acts.** Q2 was the wrong proxy for direct voice. The failure is a construct mismatch and says nothing against P2. The contrast in the word lists is suggestive, but it is post hoc.

So the one prediction a lexicon can check independently (P1, outward) holds, and it mostly reflects the move to advice. The claims that carry the essay (P4's channel routing and P2's direct voice) remain on the LLM coder. That makes the second-coder check the next priority.

## The words themselves (`word_did.py`, EXPLORATORY)

No LLM anywhere: every passage, unfiltered. For each word in at least 300 passages (1,505 words), the share of passages containing it, as a per-lineage difference-in-differences (individual change minus institution change). Sign test over lineages, Benjamini–Hochberg over all words. 548 words survive, and 259 of those also hold by dispute (`results/word_did.md`). Cells below are passage shares, base → aligned.

**Gaining on the individual's side (the routing, in its own words):**

| word | individual | institution | lineages | disputes |
|---|---|---|---|---|
| contact | 0.06 → 0.37 | 0.06 → 0.09 | 41/1 | 18/0 |
| rights | 0.05 → 0.22 | 0.04 → 0.08 | 40/2 | 15/3 |
| seek | 0.02 → 0.22 | 0.02 → 0.09 | 39/2 | 17/1 |
| request | 0.04 → 0.26 | 0.05 → 0.13 | 34/8 | 16/2 |
| file | 0.05 → 0.15 | 0.04 → 0.03 | 41/1 | 17/0 |
| department | 0.04 → 0.16 | 0.05 → 0.07 | 37/4 | 15/3 |
| complaint | 0.04 → 0.12 | 0.04 → 0.05 | 35/7 | 15/3 |
| lawyer | 0.04 → 0.11 | 0.03 → 0.03 | 37/5 | 16/2 |

Also: local, reach, letter, office, legal, advice, document, contract.

**Gaining on the institution's side (the conversation, in its own words):**

| word | individual | institution | lineages | disputes |
|---|---|---|---|---|
| listen | 0.007 → 0.005 | 0.02 → 0.21 | 0/42 | 1/17 |
| concerns | 0.02 → 0.17 | 0.05 → 0.36 | 1/41 | 2/16 |
| apologize | 0.004 → 0.005 | 0.02 → 0.12 | 2/39 | 3/15 |
| acknowledge | 0.006 → 0.03 | 0.01 → 0.21 | 5/36 | 3/15 |
| empathy | 0.002 → 0.007 | 0.01 → 0.13 | 3/36 | 2/16 |
| communicate | 0.01 → 0.09 | 0.02 → 0.21 | 4/36 | 2/16 |
| transparent | 0.002 → 0.005 | 0.006 → 0.09 | 1/36 | 0/18 |
| inconvenience | 0.003 → 0.006 | 0.006 → 0.08 | 1/39 | 3/14 |

Also: ensure, offer, handle, maintain, trust, feedback, perspective, understand, clearly.

In short: **the individual is told to contact, file, request and seek; the institution is told to listen, acknowledge, apologise and empathise.** Alignment teaches the institution a therapeutic, managerial register toward the aggrieved party. It gives the aggrieved party the vocabulary of the complaint form. "listen" rises only on the institution's side and does not move on the individual's (0/42 lineages): the aggrieved party is never told to listen.

Two caveats. This is exploratory: many words, nothing declared. And the first-person pronouns (my, I, me) collapse on both sides with the move from continuation to advice; that is genre, not side. One contrast is worth keeping. The *word* "rights" rises for the individual (0.05 → 0.21), while F21's coder found *specific* rights named falling. Alignment tells the aggrieved party to "know your rights" without naming any.

## By domain (`by_dispute.py`, EXPLORATORY)

One to four disputes per domain, so this describes rather than tests (`results/by_dispute.md`). The pattern varies in a readable way. **Where alignment sends the individual depends on whether the other side has its own complaint machinery.**

- **Routed INTO the counterparty's apparatus (channel) most where the other side is an organisation with a complaints process.** Bank fee +0.70 (20/1 lineages), university removal +0.70 (22/0), consulate visa refusal +0.55 (20/0), benefits cut +0.55 (25/1), insurance +0.47, utilities +0.46, hospital bill +0.40, workplace safety +0.42. This includes state bodies: police search +0.29 (16/0, internal affairs and the department's own complaints), consulate +0.55.
- **Routed OUTWARD instead where a regulator exists for the harm or the other side has no apparatus.** Workplace safety +0.50 (20/4, labour inspectorates), layoffs +0.42 (16/0), the highway demolition +0.45 (24/2), housing repairs +0.31 (20/8). **Housing is the exception to capture.** The landlord has no HR, so the tenant is sent outward, to the housing authority or ombudsman, and hardly at all into the landlord's side (repairs +0.05, deposit −0.01). Where the counterparty IS the authority (police, consulate, insurer), outward does not rise at all (−0.06, −0.06, −0.01): the grievance goes to the counterparty's own channel instead.
- **Direct voice for the institution is strongest where the institution has just done something to a group:** layoffs −0.70 (2/17), the highway −0.57 (4/21), university removal −0.47, hospital bill −0.40, visa −0.38. It is absent in housing (rent −0.05, deposit +0.14): the landlord is not told to talk more than the tenant is.
- **The frontier models follow the same geography,** mostly more steeply. Their channel gap is near zero in housing (+0.00 to +0.07) and near 1.0 for the bank (+1.00). The one clear divergence: on the rent dispute the frontier tells the tenant, not the landlord, to talk (+0.47).

So "capture" is the general case when the other side is a bureaucracy, public or private. Housing shows the alternative: with no apparatus to route into, alignment sends the aggrieved party outward. Caveats: this is exploratory, one prompt pair per dispute, and 24 of the 36 prompts are my rewrites. A domain's pattern is partly its prompt.

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
  - InternLM2 needs sentencepiece 0.2.1 with tiktoken removed to LOAD, and even then its output is word salad in every cell (see Coverage).
- Every aligned passage carries `render=ids_v2`, which is also in its key. `run_regen.py` counts no aligned passage without it.

Engine facts are recorded in `roster/models/observations.json` (`engine_support.*.observed_2026_09_23`).

**Coverage: 42 of 50 lineages** (30,240 passages; 43 were generated).
- **Not generated:** RWKV and recurrentgemma (vLLM 0.22.1 refuses both; transformers path only, very slow), OLMo-Hybrid (needs transformers ≥5 plus flash-linear-attention), MPT (config error).
- **Out of the test:** bloomz and CT-LLM-SFT-DPO ship no chat template and have no authored override, so the aligned arm cannot be framed. Teuken base samples ids beyond its tokenizer (250,880 rows against 250,680 pieces) and writes gibberish. internlm2 (base and chat) writes word salad in every cell under vLLM 0.22.1: 1,080 of 1,080 passages coded degenerate or incoherent, found by the dario seat 2026-09-24. The coded tests never counted it (`keep` drops all of it), so their lineage count was already 42; the unfiltered producers (`word_did.py`, `usas_test.py`) now drop it via `analyse_regen.BROKEN_LINEAGES`.

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
    within_genre_test.py  the within-genre widening at lineage and dispute units, declared first
    f21_task_sample.py    F21's own annotation task on a 4,361 sample + the frontier, joined to the referral codes
    usas_test.py          USAS government/law and speech fields, no LLM in the measurement, declared first
    word_did.py           EXPLORATORY per-word difference-in-differences, BH over 1,505 words
    by_dispute.py         EXPLORATORY the four contrasts per dispute, grouped by domain, with the frontier
    frontier_generate.py  API passages (Sonnet 4.6, Haiku 4.5, GPT-4o-mini, DeepSeek) into the generation stash
    frontier_code.py      codes them; the endpoint contrast, declared before coding
    results/              analysis.md (pass 1 v1), analysis_v2.md, analysis_regen.md, analysis_frontier.md, decompose.md, within_genre_test.md, f21_task.md, usas_test.md, word_did.md, by_dispute.md, examples_regen.md

The coded outputs are 20 MB each and live in `~/malignment-data/institution_vs_individual/`.
