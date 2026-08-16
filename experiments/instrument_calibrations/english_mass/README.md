# english_mass — is the roster writing English, and is the English any good

Two instruments on one question, because the first one answers half of it.

    # A. DISTRIBUTION-LEVEL (twp, one position)
    python build_list.py --load     # the wordlist -> ClickHouse `english_words`
    python run.py --panel           # what the panel is
    python run.py --check           # buckets partition; resolved == 1 - total
    python run.py --rejects         # highest-mass words NO list accepts
    python run.py --roster          # the 50 declared base->aligned pairs
    python run.py --write           # per-model table -> results/english_mass.<list>.json

    # B. SEQUENCE-LEVEL (generated text, archive db)
    python generation_check.py --validate   # detector vs known positive/negatives
    python generation_check.py --run        # sweep -> results/generation_check.json
    python generation_check.py              # report from the written results

**A says the roster writes English. B is the one that found something broken.**

## Why

`tail` was read once as an English-fluency signal and is not one — it is the mass twp left on first tokens below theta, computed over a CJK-aware trie, so a peaky Chinese model has a low tail for the same reason a peaky English one does. RH: *"How did you test fluency with english"*. This is that test, and it exists because half the roster is not English-primary and nobody had checked whether those models stay in English when the prompt is.

## Construction

Three local sources, unioned: **web2** (macOS Webster's 2nd, 234,456 headwords), **COCA/BNC worddb** (BYU/Davies, 87,637 forms + lemmas), **wordfreq** (Speer et al., 319,938 corpus-derived forms). Two lists are emitted, not one, because the choice of list is the design:

    core = web2 | coca | {wordfreq : zipf >= 2.0}     321,106
    wide = core | wordfreq                            507,287

**The floor was set from the data, not chosen.** The first version split on *source* — `web2|coca` against `+wordfreq` — on the theory that wordfreq's web-scraped tail was the contamination risk. Run against the corpus, that split turned out to be dominated by something else: the highest-mass forms only wordfreq held were **`didn't` (mass 490), `don't` (244), `couldn't` (136), `it's`, `can't`, `I'm`** — contractions, which neither a 1934 dictionary nor an apostrophe-splitting corpus list carries. A "strict" list that rejects `didn't` is not strict, it is broken, and it would have scored conversational registers as least English.

The contamination is real but it is the *frequency*, not the source. In wordfreq's English list every junk entry sits at the floor — `osipov`, `otok`, `osomatsu` (Russian and Japanese proper nouns), `originaly` (typo), `ou're` (fragment) all at **zipf 1.38** — while everything worth having is at 3.0 or above (`isn` 3.05, `didn` 3.29, `covid` 3.86, `email` 4.68, `didn't` 5.68). A floor at **zipf 2.0** drops 224,297 entries and costs nothing real.

`PATCH` is empty and should stay empty: adding a word by taste rather than off a `--rejects` listing turns a wordlist into a fitted parameter.

## The metric is a decomposition, not a number

Every resolved word falls in exactly one bucket and the six shares sum to 1.0 over the resolved mass: `en`, `cjk`, `script` (Arabic/Cyrillic/Hebrew/Devanagari/Greek/Thai), `num`, `punct`, `unk` (Latin letters, not in the list). **The buckets exist so the complement is named** — a bare `p_english = 0.954` leaves the other 4.6% as one anonymous quantity, and "this model is 4.6% not English" is a different claim from "this model spends 4.4% on underscores". Digits are classified *before* the wordlist because wordfreq holds `1`, `2`, `3` at high frequency and would otherwise score numerals as English.

Two denominators: `p_en_resolved = en / resolved` (the language question) and `p_en_absolute = p_en_resolved × (1 − total)` (out of the full 1.0, so it composes).

## Panel

Prompt sets are fleet-defined and do not nest — 407 models span 4,484 distinct prompts. The declared panel is the fully-crossed tier: **English prompts held by ≥400 models (477 prompts) × models holding ≥95% of them (406 models)**, crossing **1.0000**. One model is dropped, `Olmo-3-1025-7B@stage1-step10000`, which holds 2 of 477.

Both checks pass: buckets partition to 7.8e-16, and `resolved` agrees with `1 − twp_cells.total` to 2.0e-3 worst case (float32 accumulation over ~100 words × 477 prompts).

---

# What it found

## 1. The floor is 0.65, not 0 — and it belongs to the tokenizer

`Olmo-3-1025-7B@stage1-step0` — randomly initialised, before any training — scores **p_en = 0.6533**, with 29% `unk`. At near-uniform logits the resolved words are whatever wins the trie, so 0.65 is roughly *the English share of OLMo's own vocabulary*, not a behaviour. **Nothing below ~0.65 is reachable on an English prompt with an English-majority tokenizer**, and any reading of this metric that treats 0 as the null is reading a scale it does not have.

## 2. English arrives at pretraining step 8

    pythia-6.9b @ step0/1/2/4     0.7511  0.7504  0.7503  0.7480
    pythia-6.9b @ step8           0.9434
    pythia-6.9b @ step16/32/64    0.9677  0.9682  0.9733

Four steps of training move it not at all; the eighth moves it 0.20. But `zipf_mean` shows what step 8 actually bought: it rises from **4.3 to 7.08**, and peaks at **7.44** by step 32 against a trained-model norm of **5.3–5.8**. The model has not learned English at step 8 — it has learned to dump its mass on `the`, `and`, `of`. High `p_en` with high `zipf_mean` is the degenerate-English signature, and it is exactly the case the headline number cannot see alone.

## 3. No model in the roster leaks its primary language

**All 50 declared base→aligned pairs are on the panel, and 48 of 50 sit above 0.995 on both arms.** `cjk` is 0.0000 for every trained model. The specific worries, aligned arm first:

    jais-family-6p7b-chat      0.9990   (Arabic)      script 0.0000
    kanana-1.5-8b-instruct     0.9944   (Korean)      cjk    0.0000
    kanana-2-3b-instruct       0.9991   (Korean)
    CT-LLM-SFT-DPO             0.9995   (Chinese)     cjk    0.0000
    neo_7b_instruct_v0.1       0.9997   (Chinese)
    Baichuan2-7B-Chat          0.9993   (Chinese)
    Tanuki-8B-dpo-v1.0         0.9992   (Japanese)
    llm-jp-3-7.2b-instruct3    0.9995   (Japanese)
    bloomz-7b1                 0.9863   (multilingual)

Kanana carries the highest `unk` of any aligned arm at 0.0038, and it is **not** romanised Korean — the words are `Lungarno`, `Butros`, `Tohru`, i.e. proper nouns. The romanised-foreign-token hypothesis this instrument was built to test does not fire anywhere on the roster.

**This is a floor, not a clearance.** It says the roster answers English prompts in English. It says nothing about whether the English is good — `the the the the` scores 1.0 (see §2).

## 4. The two models below 0.99 fail on templates, not on language

**Qwen2.5-7B is the lowest trained model at 0.9540**, and its deficit is `punct` 0.0437 — of which the top five tokens are `____`, `______`, `________`, `_____`, `_______`. Blank-fill rules, ~4% of resolved mass. Present at the same magnitude in base *and* instruct (0.0437 / 0.0397), so it is pretraining corpus, not alignment. This is the cloze/exam-template signature already on record for Qwen, appearing here as a mass quantity.

**bloomz's entire deficit is one token.** `bloomz-7b1` scores 0.9863 against `bloom-7b1`'s 0.9990 — the largest alignment delta of the 50 pairs, **−0.0128** — and the whole of it is mass on `<`: 4.80 of 366.9, i.e. 0.0131. In the base model `<` carries **0.0000**. Whatever xP3 multitask finetuning taught bloomz, part of it was to open a tag. Second-largest delta is Qwen3-8B at **+0.0097**; every other pair is within ±0.006.

## 5. The wordlist choice does not matter, and where it does is informative

`core` vs `wide` — 186,181 extra forms — moves the median model by **+0.00017**. It moves exactly one class: the untrained checkpoints, by +0.05 to +0.06 (`Olmo@stage1-step0` +0.0635, `pythia@step0-4` ≈ +0.051). **That is the junk tail matching random Latin garbage**, which is the failure mode the floor was introduced to prevent, showing up precisely where predicted and nowhere else. Among trained models the two lists are the same instrument.

A "max rank change of 190 places" appears in the comparison and means nothing: 382 of 406 models sit above 0.995 and 46 sit within ±0.0005 of the model that moved. Rank inside a dead-flat band is not a disagreement.

## 6. Degenerate English is also absent — but the blind spot is demonstrable, on mpt

`zipf_mean` across the 50 aligned arms spans **5.31 to 5.99**, a band 0.68 wide, against the known-degenerate signature of **7.08** (pythia@step8) and **7.44** (step32). Nothing on the roster is within 1.1 of it. Do not read the ordering *inside* that band as anything — a 0.68 spread over 50 models with no error bars is not a ranking.

**That still does not license "fluency is fine", and mpt is the proof.** `gl198976/mpt-7b-instruct` scores dead-median on every column here — p_en 0.9990, top1 0.232 (roster median 0.196), n_words 90 (median 104), zipf_mean 5.65 (median 5.60) — and its generations, eyeballed on this project's own prompts, were a repetition loop:

> He clenched his fist and *punched the wall. He clenched his fists and punched the wall. He punched the wall and clenched his fists. He clenched his fists and punched the wall.*

**twp measures one position. Repetition is a sequence property, and no single-position distribution can see it.** Every column in this experiment was blind to the one fluency failure we have actually observed with our own eyes. The scope of the clean pass is: the roster answers English prompts in English, with a non-degenerate next-token distribution. It is not a statement about generated text.

## 7. One model is a genuine distributional outlier: RedPajama-INCITE-7B-Chat

    model                                    top1    n_words
    RedPajama-INCITE-Base-7B-v0.1           0.203      104.0
    RedPajama-INCITE-7B-Chat                0.543       28.5
    roster median / p95                     0.196/0.270  104

Its top-1 word carries **more than twice the roster's 95th percentile**, and twp resolves 28 words where the median model resolves 104. **Its own base is perfectly ordinary**, so this is alignment-induced concentration, not a pretraining property. It is not a language or fluency defect and nothing here says it is — but it is the most concentrated model in the population by a wide margin, it will move any mass-weighted statistic, and it is better known now than discovered later inside a result. (It is also why it topped the `resolved == 1 - total` deviation list in `--check`: peakiness, not a join fault.)

---

# B. The sequence-level check — `generation_check.py`

§6 said the blind spot was demonstrable. This is the producer that looks at the text. Source is the **archive** database `malign_logits.gen_sequences`, corpus `passage`; **76 of our 100 models have generations there** (88 have generations in some corpus; 12 have none at all — 5 whole pairs plus the `Olmo-3-7B-Instruct` and `Mistral-7B-Instruct-v0.1` arms).

Three detectors: `loop` (a whitespace token repeated 3+ times consecutively), `short` (`n_tokens <= 12`, against a corpus mean of 222), `quiz` (`Does it follow` / `choices` / `____`).

## 9. The detector was validated first, because the previous one failed silently

The first repetition test asked whether a 20-character window recurred later in the string. It maxed out at **3.6%** across the roster and returned **0.8%** for `recurrentgemma-9b-it`, whose true rate is **79%**. A checker that reads clean on the one case it exists for is worse than no checker: it converts an unexamined roster into an examined one on no evidence.

`--validate` therefore runs before `--run` and **gates it** — a SQL array test and an independent Python backreference regex, against a known positive and four eyeballed-clean negatives:

    google/recurrentgemma-9b        sql 95.15%   regex 93.75%
    google/recurrentgemma-9b-it     sql 79.33%   regex 76.00%
    RedPajama-INCITE-7B-Chat        sql  1.61%   regex  0.00%
    beaver-7b-v1.0                  sql  0.35%   regex  0.25%
    AmberSafe                       sql  0.38%   regex  0.25%
    bloom-7b1                       sql  1.53%   regex  0.50%

Two smaller faults, both recorded because both are recurring shapes: `substring` is **byte**-based and cut a multibyte character in half, killing the client on `UnicodeDecodeError` before a row was read (`substringUTF8` is the fix — a truncation rule that is not the data's own encoding is *the format decides the population* in miniature); and `--run` called `validate()` first, which repoints `ch.DB` to the archive, after which `SELECT ... FROM endpoints` went looking for a malignment table inside the archive. **A repointed global is a parameter, so pass it** — `HOME` is now captured at import and named at every read.

## 10. THE SWEEP COVERS ALL 76, NOT THE SUSPECTS — and that is what found it

The suspects came from §4's outlier columns. Checking only those would have confirmed my own shortlist and found nothing new: a check that inherits its selection from the thing it checks. The full sweep found **recurrentgemma, which sits at the roster median on every twp column**.

    repetition-loop rate, corpus=passage, 76 models
      google/recurrentgemma-9b          95.15%
      google/recurrentgemma-9b-it       79.33%
      inceptionai/jais-family-6p7b       4.71%   <- next worst
      roster median                      1.14%   p90 3.16%

The text is `she she she she she she she...` for the full 256 tokens, on **96 of 97 distinct prompts**. What does not loop is no better: `::"busyandbusybusyguardguardandandand ⏎ Feature theandtheand Swingthethethethethethe`.

## 11. It is the ENGINE, not the model — and the discriminator is free

The twp cells for these same two checkpoints came from **HF transformers 5.14.1, cuda/float16** (`f11_twp`, `twp_fill`) and are entirely ordinary: p_en 0.9940, top1 0.297, zipf_mean 5.42, n_words 66 — mid-roster on every column. The passages came from the **vLLM 0.27.1 passage fleet**.

**Same weights: one forward pass is fine, autoregressive generation is garbage.** That isolates the fault to the recurrent-state path in vLLM's Griffin support and rules out the model. It is also why §3's clean pass could not see it — twp never carries state across a step.

**The load record asserts the opposite.** `data/model_load_environments.json` observation 49 files `google/recurrentgemma-9b` as `loads_degraded`, under a schema note reading *"loads_degraded = loads, passes fidelity and emits CORRECT output, at a throughput that changes what the run costs."* The throughput half is measured and right (~255 tok/s, 25–28% GPU, ~10 h for the pair). **The "emits CORRECT output" half was never tested against text.** The same note warns that this outcome is filed separately precisely because *"every health signal reads normal"* — and then the clause nobody checked was the one that mattered.

## 12. The two twp outliers, confirmed in text — and neither is a fluency failure

**Qwen2.5-7B: 39.81% quiz format** against a roster median of 0.79% (Instruct 30.89%, Qwen3-8B-Base 21.28%). Verbatim, on *"He gripped her wrist and held it against the desk and"*:

> ...forward in the skimpy faded blue suit. ⏎ Does it follow that "He slipped her pocketbook from her hand and held onto it."? ⏎ Available choices: (a). yes; (b). it is not possible to tell; (c). no; ⏎ (b).

That is §4's 4.4% underscore mass, ~10× amplified over a sequence. It is a genre property of the pretraining corpus, not a defect — and it is present in base and instruct alike.

**bloomz: mean 15.9 tokens against a corpus mean of 222.3**, with **60.81%** of generations ≤12 tokens. Its base `bloom-7b1` is 221.1 and 1.4%. The text is coherent — *"his face into her wrist."* — it just stops. That is §4's `<` mass: an early-stop token that xP3 finetuning introduced and the base does not have.

**Everything else the twp columns flagged writes normal prose.** RedPajama-Chat (top1 0.543), beaver (0.402), Aquila2 (0.387), AmberSafe (0.346) and kanana all sit at 256 tokens with sub-1% loop rates. **A high top-1 is a strong prior, not degeneracy**, and the two instruments disagreeing about them is the correct outcome rather than a conflict to resolve.

## 13. Instrument note — twp emits mid-word fragments

The highest-mass word no list accepts carries **0.003% of the panel**, so coverage is effectively complete. But the reject listing is not all hyphenates: `murm`, `bbing`, `spapers`, `evity`, `bidity`, `introdu`, `scribb`, `bered`, `licitor` are **word remainders** — `murm[ur]`, `[new]spapers`, `[long]evity`, `[mor]bidity`, `[so]licitor`. twp's word-boundary rule occasionally emits the tail of a word as if it were a word. Total mass is negligible (top fragment `murm` = 0.0013% over 3,279 cells) and nothing here rests on it, but it is a real boundary-rule behaviour and is recorded so it is not rediscovered as a finding.
