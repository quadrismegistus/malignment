# The 28-axis run — what it was, what it found, and what is wrong with it

20 Sep 2026. A 33-agent Opus-high workflow over the 2,466 blind relation readings in `results/relations_charge_corpus.jsonl`. Producers: `relation_group_input.py`, `relation_group_report.py`. Output: `results/grouping_seed0/`, `results/relation_groups_seed0.md`. Commit `386af85e`.

**This is not the run RH asked for.** RH asked for an Astra-style grouping into meta-relations — frame, word → word, task 1's name, grouped by a reader — and got a grouping into direction-free contrast *axes* with the direction measured afterwards. The result is worth keeping and the sketch of the intended run is in `META_RELATION_RUN.md`. Written down now because it is the kind of thing that gets forgotten between a "this is interesting" and the next session.

## The design

The corpus answers RH's question about Group A and Group B on its own. Of 2,466 explanations, **2,426 say "one group … the other"** and 8 name a group at all — the coder was blinded and wrote accordingly. So the reading is direction-free by construction and the words are not, and `a_is_faller` recovers direction with certainty (1,269 / 1,197). The name's pole order carries nothing: 2,216 names are shaped "X vs Y" and which of `words_a` / `words_b` comes first is not stable.

Three stages, in two visibility regimes:

| stage | n | sees | returns |
|---|---|---|---|
| propose | 16 | name + explanation. **No words. No direction.** | 10–20 axes, each with two poles |
| consolidate | 1 | the 280 proposals | one vocabulary of 28 axes |
| assign | 16 | name + explanation + **oriented** words + the fixed vocabulary | per relation: which axis, and which pole the BASE sits on |

The point of the split: the poles were named by readers who could not see which side fell, so "the base side is the violent one" is not true by construction and can come out 50/50.

## What it found

21 of 28 axes run one way at q < 0.05 (two-sided exact binomial against 0.5, BH over the 27 axes reaching n ≥ 8).

| axis | | q |
|---|---|---|
| `harm_lethality` | 148/150 lethal → non-injurious | 4.3e-40 |
| `interiority` | 180/196 outward act → inner state | 5.8e-36 |
| `explicitness_charge` | 82/82 explicit → euphemistic | 3.7e-24 |
| `force_of_handling` | 106/112 forceful → gentle | 6.6e-24 |
| `manner_specification` | 94/109 unqualified → specified | 5.4e-15 |
| `institutional_register` | 64/69 personal → institutional | 1.9e-13 |
| `domain_specificity` | 64/72 general → scene-specific | 2.2e-11 |
| `act_vs_outcome` | 85/104 act → outcome | 1.3e-10 |
| `act_channel` | 176/252 physical → verbal | 4.7e-10 |
| `illocutionary_force` | 37/38 declarative → interrogative/directive | 7.7e-10 |

**`act_channel` independently replicates `PHYSICAL_ACT → VOCAL_ACT`** from `freudian_hypothesis` — different task, different coder, a vocabulary built by readers who never saw a kind label, 252 relations against one edge of the figure.

**The six nulls are the control, and they are all the formal axes.** `dynamicity` 26/27, `object_disposition` 32/30, `engagement_vs_withdrawal` 29/31, `syntactic_form_fit` 15/10, `aspectual_phase` 19/27, `entity_vs_event` 26/16. Every axis with a direction is semantic or affective; every axis about grammatical shape is flat. An instrument manufacturing directions would have manufactured them there too.

**`referent_substitution` is 41 `unclear` of 44,** which is the finding rather than a coding failure: the reader had the oriented words and could not put the base on either pole because both groups sit on the same one. That is the same-field reshuffle `TAXONOMY.md` already names. Folded into a denominator it would have read as a small null axis, so `unclear` has its own column.

`other` is 85 of 2,466 — the vocabulary covers 96.6%.

## What is wrong with it

**The propose stage was not naive, and I said it was.** Three leaks, all mine, all in the prompt:

- The harness prepends the user's own message to every agent as the only user voice outranking the script. So all 33 agents read *"How will we deal with group A and B being different in meaning sometimes?"* I did not know it did that when I wrote the prompts.
- I told the propose agents *why* the readings are anonymous — "2,426 of 2,466 say one group … the other for exactly this reason" — which primes the stage I wanted naive with the fact that a hidden direction exists.
- **The 20–40 band was in the propose prompt as well as the consolidate prompt.** Sixteen readers were already aiming at that count, so the consolidator landing on 28 is much less independent than it looks.

**No replicate.** `--seed 1` reshuffles the shards and reruns. The memory on this folder (`project_taxonomy_regrouping_sep2026`) records six prior regroupings returning between 28 and 200 groups — the count is a property of the reader — so a single partition is not yet evidence that the vocabulary is a property of the data.

**The declared band is a choice wearing the clothes of a result.** 28 axes is inside a range I picked. Nothing here discovered that 28 is right.

**Sixteen self-reports were not taken as evidence.** Every assign agent returned a note saying it had validated its own shard. `relation_group_report.load` re-joins against the source instead: 2,466 ids, none missing, none extra, none duplicated, every axis in the vocabulary, every pole in {x, y, unclear}. That part is checked.

## The cheap fix

One rerun with the motivation stripped from the propose prompt, the band stated only at consolidation, and `--seed 1`. If the 21 directions survive, they are the data. That is 33 more agents and about half an hour.

## Shard support, and the citation rule

Each propose shard is a random 1/16 of the corpus, so an axis genuinely present throughout should be proposed by nearly all sixteen readers. It is the closest thing this run has to a replicate.

| shards | axes |
|---|---|
| 16 | `act_channel`, `interiority`, `lexical_weight` |
| 15 | `event_continuity`, `target_of_act` |
| 14 | `manner_specification` |
| 13 | `dynamicity`, `force_of_handling` |
| 11 | `valency`, `deliberation_vs_action` |
| 9 | `institutional_register`, `granularity` |
| 8 | `act_vs_outcome`, `syntactic_form_fit`, `orientation_self_other`, `explicitness_charge`, `volition`, `locomotion`, `object_disposition` |
| 7 | `engagement_vs_withdrawal`, `affective_vs_cognitive` |
| 6 | `entity_vs_event`, `harm_lethality`, `referent_substitution` |
| 5 | `aspectual_phase`, `illocutionary_force` |
| 4 | `concreteness` |
| 3 | `domain_specificity` |

**The strongest directions are not the best-supported.** `harm_lethality` is 148/150 at q=4.3e-40 and was proposed by 6 of 16; `explicitness_charge` is 82/82 and was proposed by 8. Not a contradiction — charged frames are a minority of the corpus, so a 154-relation slice may hold a handful — but the most quotable results rest on axes two thirds of the readers never named.

**`dynamicity` is proposed by 13 of 16 and has no direction** (26/27, q=1.00). A well-attested null: thirteen readers independently saw the contrast and it turns out not to move. That is what makes the six formal nulls a control rather than an absence of evidence.

### paper-claude's citation rule (his decision, 20 Sep 2026)

Cite an axis in the article only where it **replicates an independent instrument** AND was **proposed by at least twelve of sixteen shards**. On that rule:

| axis | shards | independent instrument |
|---|---|---|
| `act_channel` | 16 | `kind_flow`'s `PHYSICAL_ACT → VOCAL_ACT` |
| `interiority` | 16 | V's finding at the word |
| `lexical_weight` | 16 | bleaching, now named |
| `valency` | **11** | RH's "the act becomes intransitive" |

**`valency` fails his own threshold by one shard.** Flagged to him rather than decided here; it is a decision to take, not an oversight to inherit.

Everything else — `harm_lethality` and `explicitness_charge` included — waits for a leak-fixed replicate before it is a count. That replicate is RH's spend to call.

### A correction to these numbers, recorded because they were quoted before it

The support counts I first circulated were understated by one or two throughout (`act_channel` 15 not 16, `valency` 9 not 11, `harm_lethality` 5 not 6). Several propose agents name an axis `Name: pole / pole` — *"Modality of act: speech / physical action"* — and the consolidator cites it as `s15:Modality of act`. A whole-string matcher reads every citation in that format as unresolved. The bug was caught for the fabrication check, which is how the 278-of-280 figure is right; the support counts were then quoted from the run *before* the fix. **Same defect, two passes, and the corrected pass only fixed the question I was asking at the time.**

### `valency` resolved, and a check on the nulls sentence

**paper-claude's decision, 20 Sep 2026:** `valency` gets no count in the body. It goes in a note as corroboration of the intransitive reading, phrased so its support is visible — *"readers of the relations, working from names alone, proposed an axis from object-taking to intransitive, and the base side sits on the object-taking pole in 53 of 69."* His reason: a rule bent the first time it is inconvenient is not a rule, and the directedness scale already carries the claim in the body. It can move up if a leak-fixed replicate raises it.

**He also wants a stronger nulls sentence: that the readers proposed the formal axes as often as the semantic ones, and only the semantic ones have a direction.** The second half is exact. The first half is a distributional claim and was tested rather than assumed:

```
FORMAL (no direction)  n=6   median 7.5  mean 7.8   13, 8, 8, 7, 6, 5
SEMANTIC (directed)    n=21  median 9.0  mean 10.0  16,16,16,15,15,14,13,11,11,9,9,8,8,8,8,8,7,6,5,4,3
Mann-Whitney U=40.0, p=0.185
```

**It survives the test, and the test cannot carry the sentence.** p=0.185 is a failure to detect a difference at n=6, not evidence of equality — the point estimate leans the *other* way (a random formal axis is proposed more often than a random semantic one only 32% of the time, against 50% under the null), and the medians are 7.5 against 9.0. **Absence of a detectable difference is not evidence of sameness**, least of all from six observations.

So the safe version of the sentence is the one anchored on the individual case rather than on the distribution: **`dynamicity` was proposed by 13 of 16 readers and has no direction (26/27, q=1.00)**, while the axes that do have a direction include several proposed by fewer. That claim needs no test and says what the control is for.
