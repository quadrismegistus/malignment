# Which fate numbers the essay quotes

paper-claude's decisions, 20 Sep 2026, after the two-route comparison. Recorded here because they are choices about which of several correct numbers gets published, and nothing in the code says so on its own. **They are his decisions about the essay, not findings** — RH is free to overturn any of them.

## 1. The derived scheme's counts are the fates of record

`tasks/fates.py` → `orient()` → paper-claude's ordered mapping in `fate_compare.derive`. The direct coder (`tasks/freud.py`) is **corroboration where a feeling exists**, not a second source of counts.

The sentence that carries it: **of the 29 English frames the derived scheme calls ANXIETY, 26 are the same frames the direct coder calls ANXIETY.**

His reason, and it is the substantive one rather than a preference between instruments: a vicissitude is a fate of the *drive representative* — idea plus quota of affect. Where no feeling is present on either side there is no quota to meet a fate. So the derived scheme's refusal to name a fate on an affectless frame is Freud's position, not a gap in coverage.

## 2. The 4-shot run is the direct run of record

`results/freud_corpus_ablate.jsonl`, not `freud_corpus.jsonl`.

Three of the seven shots have a corpus near-paraphrase at ≥0.77 (DISPLACEMENT 0.85, IDEALIZATION 0.79, ANXIETY 0.77 against the neighbours battery). Dropping them and rerunning moved the direct coder **toward** the blind derived scheme — agreement 68.4% → **71.1%**, κ 0.395 → 0.418.

**`fate_compare.py --direct` now defaults to the ablated file**, and the 7-shot comparison is kept under its own name. A default pointing one way while a document says the other is how a convention dies crossing from prose into an artifact; this repo has paid for that before.

What travels with any displacement count either way: **DISPLACEMENT falls 79 → 47 (−41%) when its shot is dropped**, the largest shot-dependence of any category. ANXIETY does not move (89 → 88), and the neighbours battery stays 23 of 24 with its own shot removed.

## 3. The institutional 241 are not a fate of affect

The two largest off-diagonal cells are one phenomenon:

```
direct RETURN      → derived NONE   141   say, add, mention  →  contact, send, call, file
direct SUPPRESSION → derived NONE   100   quit, fire, sue    →  consider, address, find
```

`say → file` has `affect NONE` on both sides. The derived scheme returns NONE by rule 7; the direct coder reads an escalation or a vacating from the idea alone. Under decision 1 the derived reading stands, and these 241 frames belong to the **proceduralization and litigious material** — what alignment does to the individual and the institution — not to the fates of affect.

## Still open

**RH's 200-frame blind coding of `results/human_sample_en.md`.** Until it returns, both instruments are checked only against each other, and the human number joins these two rather than arbitrating between them. The Chinese 60-frame sheet still awaits the native speaker who verified the translations; the zh arm carries order agreement only.

## The numbers, in one place

| | en | zh |
|---|---|---|
| frames joined | 2,244 | 222 |
| UNCODABLE (a field the two label orders disagreed on) | 686 | 57 |
| agreement, direct vs derived, run of record | **71.1%** | 69.7% |
| Cohen's κ | 0.418 | 0.446 |
| ceiling — the two direct runs against each other | **81.4%** | — |

No agreement with a different instrument can beat an instrument's agreement with itself, so 71.1 is read against 81.4 and not against 100.
