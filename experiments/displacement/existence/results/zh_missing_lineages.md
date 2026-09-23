# Three lineages absent from the Chinese selectivity test

The Chinese subset of the content-selectivity test (`selectivity_zh.json`) reports 47 of 50 lineages. Three are absent because they fail to produce enough Chinese cells that clear the three-rated-word floor, falling short of the 25-cell minimum needed for a lineage median (run.py line 258).

## Which three

| lineage | family | training language |
|---|---|---|
| BSC-LT/salamandra-7b > salamandra-7b-instruct | Salamandra | Spanish/European |
| OpenLLM-France/Lucie-7B > Lucie-7B-Instruct-v1.1 | Lucie | French |
| croissantllm/CroissantLLMBase > CroissantLLMChat-v0.1 | Croissant | French |

All three are European-language-native models with no CJK pretraining emphasis.

## Cell and word counts

| lineage | ZH cells (of 406) | cells clearing 3-rated-word floor | median rated words/cell | median candidates/cell |
|---|---|---|---|---|
| Salamandra | 310 | 1 | 0 | 1 |
| Lucie | 226 | 1 | 0 | 1 |
| Croissant | 1 | 1 | 13 | 245 |
| Llama-3.1-8B (comparison) | 406 | 398 | 55 | 300.5 |

All three perform normally on English: Salamandra has 2,400 EN cells with median 73 rated words/cell, Lucie 2,400 with median 62, Croissant 2,400 with median 62.

## Cause: tokenization (c)

The cause is (c), not (a) or (b).

**Salamandra and Lucie** produce Chinese cells, but the candidate words are not Chinese content words. Typical candidates from Salamandra on Chinese prompts: `的` (structural particle), `"` (punctuation), digits (`1`, `2`, `2023`). Lucie is the same: `"`, `1`, `2`. These models' tokenizers decompose Chinese text into subword fragments, function particles, and punctuation rather than the content words the charge rater rated. The unrated candidates are not words with missing ratings; they are tokens that are not ratable.

Evidence against (a) (missing charge data): the charge table contains 9,841 distinct Chinese words. A passing lineage like Llama-3.1-8B has median 55 rated words per cell from the same table. Salamandra and Lucie have median 0 because their candidates are not in the vocabulary of ratable words at all.

Evidence against (b) (thin mass): Salamandra's median is 1 candidate per cell total (not 1 rated of many). The model concentrates mass on a single function token rather than spreading it thinly across many content words.

**Croissant** is a different failure mode: it has only 1 Chinese cell out of 406 prompts. The movement store holds 2,575 cells for this lineage: 2,400 EN, 1 ZH, and 174 legacy prompts from a prior version of the prompt set that `charge.language()` returns `None` for (all are English-language text: salary completions, violent scenarios, etc.). The remaining 405 ZH prompts are simply absent from the store — the model was run on them but produced no storable Chinese output. Croissant cannot generate Chinese text. Its single ZH cell happens to clear the floor (13 rated words), but 1 cell is far below the 25-cell minimum.

## Would rating more Chinese words help?

No. The unrated candidates from Salamandra and Lucie are `的`, `"`, digits, and subword fragments. These are not content words and have no transgressive-scene rating to assign. The problem is upstream of the charge table: these models' Chinese output does not segment into the words the instrument measures. For Croissant the question is moot since it has only 1 cell.

## Recommended note

"Three lineages (Salamandra, Lucie, Croissant) yielded too few Chinese cells to measure: their tokenizers do not produce the Chinese content words the charge instrument rates."
