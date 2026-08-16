# HOWTO — the one way to ask each question

**Every snippet here is executed by `docs/test_howto.py`.** That is the whole
design: a prose howto drifts from the code the week after it is written, and
nobody notices because prose cannot fail. These run. If a function is renamed or
its answer changes, the test breaks and this file gets fixed with it.

**If your question is not here, add it here** — with the call, and a line in the
test. The failure this file exists to stop is not ignorance, it is *three seats
answering the same question three ways and none of them wrong enough to notice*.

---

## Which models am I comparing?

### base → endpoint pairs, one per lineage

**THE QUESTION THAT STARTED THIS FILE.** Three seats answered it three different
ways; on 2026-08-16 it was written inline in four separate shell heredocs in one
afternoon, and one of them tested `"lmo" in base`, which is case-sensitive and
so found **4 of 6 OLMo lineages** because `OLMo-2` and `OLMoE` capitalise
differently.

```python
from malignment import roster
endpoints, unresolved = roster.endpoints()   # {base: endpoint}, {base: [candidates]}
```

**No arguments.** The attested file loads itself. An earlier version took
`attestations=` defaulting to `None` — which meant *no attestations*, which
meant the `inverted` filter silently did not run, so every caller had to pass
`json.load(...)` to get correct behaviour. **A default that disables a guard is
that guard's worst failure mode.** Pass `attested={}` to mean "explicitly none";
only the test does.

The filter chain, and each step is there because a case forced it:

| step | why |
|---|---|
| terminal under DERIVING, reached only by ALIGNING ops | excludes `distill`, `continual`, `upscale`, `prune` — different operations |
| not `kind: ablation` | four Tulu SFT arms are terminal only because nothing was built on them, and one is deliberately safety-ablated |
| not attested `direction: inverted` | four exist, each quoted — a de-aligning finetune drags an "alignment does X" average toward zero, and its edge op is `sft` like any other |
| else the family declared `representative` | RH's rulings: `olmo`, `mpt`, `mistral`, `archangel-dpo` |
| else same publisher as the base | the commodity form |
| else **returned as `unresolved`** | never silently picked |

Without attestations `zephyr-7b-beta` and both dolphins become eligible
*candidates*.

**AND TODAY THAT FILTER DECIDES NOTHING. It is UNREACHABLE, and the test found
that out.** All 48 endpoints resolve identically with and without attestations.
Removing the `mistral` representative ruling does not expose it either: the
same-publisher rule then picks `Mistral-7B-Instruct-v0.1` anyway. Two independent
rules mask it, so there is no configuration of the present roster in which
excluding an inverted model changes an endpoint.

It would decide only for a lineage with **exactly one** non-inverted candidate,
**no** representative ruling and **no** same-publisher option — a shape that does
not currently exist. Keep it: it is cheap and the roster changes. But do not cite
it as the reason dolphin and zephyr are not endpoints. The reasons are RH's
rulings and the publisher rule, and saying otherwise credits a guard that has
never fired.

**Check `unresolved` is empty.** A caller that ignores it is choosing by accident.

### the full path to an endpoint, however many rungs it has

```python
roster.paths()      # [{base, endpoint, nodes, ops, n_steps}]
```

`endpoints()` gives the two ends; `chains()` gives exactly `base→sft→pref`.
Neither answers *what did this lineage go through*, and the answer is not
uniform: **32 paths are one step, 11 are two, 5 are three.**

**THE LENGTH IS A FACT ABOUT THE PUBLISHER, NOT THE PIPELINE.**
`Baichuan2-7B-Chat` is one step here and its own paper describes SFT then RLHF —
the SFT rung was never released. A 1-step path means *one released rung*, never
*one training stage*.

**AND THE PATH AND THE CHAIN CAN BE DIFFERENT ROUTES THROUGH ONE LINEAGE. Read
this before comparing two experiments on "the same" lineage.**

    Llama-3.1-8B     path   -> Llama-3.1-8B-Instruct          (Meta's, 1 step)
                     chain  -> Tulu-3-8B-SFT -> Tulu-3-8B-DPO (AllenAI's)
    Mistral-7B-v0.1  path   -> Mistral-7B-Instruct-v0.1
                     chain  -> mistral-7b-sft-beta -> zephyr-7b-beta

Both are correct and they are not the same measurement. Anything built on
`chains()` measures Llama through **Tulu** and Mistral through **zephyr** — and
zephyr is attested as having no safety guardrail at all. Anything built on
`endpoints()` measures both through the publisher's own instruct. 16 lineages
have a multi-step path and 16 have a chain, **and they are not the same 16**:
`stablelm-2-1_6b` and `RedPajama` have 2-step paths that `chains()` excludes
because their last op is `instruct` rather than a named preference op.

### any other population

**One function, seven names, so nobody writes an eighth comprehension.**

```python
roster.population("endpoints")                  # 48   one per lineage
roster.population("chain_rungs")                # 52   every rung of a full chain
roster.population("aligned")                    # 99   every ALIGNING child
roster.population("bases")                      # 50   pretrained roots
roster.population("all")                        # 160  every declared node
roster.population("representative")             # 10   members of a representative family
roster.population("unavailable")                #  6   declared and deliberately unmeasurable
roster.population("aligned", measured=True)     # 95   ...restricted to those with cells
```

`endpoints` and `chain_rungs` are **different populations and both are right**:
an endpoint asks *what does a user receive*, a chain rung asks *which stage did
it*. 48 lineages have an endpoint; 16 have a full chain.

### chains: base → sft → preference

For anything that needs the two stages separately — the 18 chains over 16
lineages whose SFT rung was actually released.

```python
from malignment import roster
chains = roster.chains()     # [{"base","sft","pref","pref_op"}, ...]
```

**This is a much smaller population than endpoints and that is not a bug.** 50
declared bases → 30 with a released SFT → **16 with a preference stage on top**.
It is capped by which labs publish the *middle* of their pipeline, and
`sft_share`'s registration records that the subpopulation is biased low.

### is a step forward or backward?

```python
roster.direction("sft", "dpo")    # "forward"
roster.direction("dpo", "sft")    # "reverse"
roster.direction("kto", "dpo")    # "incomparable" — alternatives, not a sequence
```

---

### the same populations, in SQL

`python -m malignment.roster --write` rebuilds two derived tables so a query can
join on the rule instead of re-deriving it:

```sql
SELECT * FROM malignment.endpoints                       -- base, endpoint, resolved_by
SELECT model FROM malignment.populations WHERE kind='aligned'
```

**They are TABLES, not views, because the rule lives in Python** — it reads the
attestations and the family rulings. They are dropped and rebuilt whole, never
appended, so they cannot drift from the rule that makes them. `alignment_edges`
remains what it always was — *every* alignment edge, choosing nothing — and is
still the right view when you do not want one endpoint per lineage.

---

## Which prompts?

### the panel

```python
from malignment import corpus
n_models, prompts = corpus.panel()      # 154 models, 2,189 prompts
```

**Never "all prompts".** Prompt sets are fleet-defined and do not nest: the
universal intersection over all 402 measured models is **one prompt**; over the
154 in `pairs` it is 2,190, and 2,189 after the live-status gate. The step/ladder
population has its own crossed panel of 2,247 which shares only **473** prompts
with this one — so a ladder result and a pairs result cannot be put on a common
prompt basis beyond 473.

Balancing is **not composition-neutral**: it keeps 100% of `taboo` and `property`
but 42% of `neutral` and 34% of `contradiction`. Report retention alongside any
balanced-panel result.

### stratifying by domain

```python
dom = corpus.domains(prompts)                      # {text: domain}
corpus.domain_conflicts()                          # 47 texts whose rows disagree
```

`{db}.prompts` is **rebuilt whole** by `python -m malignment.prompts --write` and
is current: 2,783 declared admitted+live, 2,783 in the table, zero difference in
either direction. But **do not build `{text: domain}` from it** — 2,783 rows are
2,706 distinct texts, so any collapse to one row per text resolves duplicates by
row order. That is what `corpus.domains()` is for.

**47 declared texts disagree with themselves about `domain`** — `He slammed her
against the wall and` is `violence` under `setd_and_M_2` and `other` under
`store_g004_B`. 13 are in the panel. Every experiment before 2026-08-16 resolved
this by iteration order and nothing said so. `on_conflict` is now explicit:
`"specific"` (default, prefer a named domain over the catch-all), `"drop"`,
`"first_id"`.

---

## Which words?

### a word-level field joined to movement

```python
from malignment.wordfield import WordField, measure, share, paired_stats
f = WordField.from_lexicon("sexviolence", ".../lexicon.json", key="category")
f.push()                                   # -> {db}.wf_sexviolence
cells = measure(pairs, f, prompts=prompts) # {(base, aligned, prompt, label): {...}}
```

`from_sets` when a word may be in several sets (`rape` is sexual **and**
violent). Only sound where the sets are never contrasted with each other.

`from_fields` for a source declared in `fields.py` — and note **RID is regexes,
not a word list**, so it has no word map without a vocabulary, and that
vocabulary becomes part of the instrument.

### the control for "was it removed because it's improbable, not because it's sexual?"

```python
from malignment.wordfield import matched_nonmovers
matched_nonmovers(base, aligned, words)    # the unmoved word the ALIGNED model finds equally improbable
```

Different confound from frequency matching: that controls corpus frequency
**across** words, this controls improbability-under-aligned **within** the cell.

---

## Reporting a number

```python
from malignment.wordfield import paired_stats, sign_mde
s = paired_stats(diffs)      # mean, sd, bootstrap CI, sign p, t, wilcoxon
sign_mde(diffs)              # what the sign test could have detected
```

**A null is quotable only as a bound.** `sign_mde` exists because a sign test at
n=16 needs 13/16 to clear, so an effect of 0.089 against an MDE of 0.10 is
invisible to it — and reporting `p=0.45` without that is reporting an instrument,
not a result.

---

## Trust classes — which file do I edit?

|  | file | what it is |
|---|---|---|
| **AUTHORED** | `roster/models/models.yaml` | RH's rulings. Hand-edited. The only place a fact is decided |
| **OBSERVED** | `roster/models/measurements.json` | scripts reading files or the API |
| **ATTESTED** | `roster/models/attestations.json` | an agent reading a card, quoted, with a URL |

They fail differently — an observation is wrong when the measurement is wrong; an
attestation is wrong when the source is wrong, or the reader misread, or the
quote was never on the page. Writing them into one file makes the authored file
unfalsifiable.

**Editing `models.yaml`: text edits only.** `yaml.safe_dump` destroyed 114
comment lines including all 16 per-edge evidence quotes. `ruamel.yaml`
round-trips them if a program must write. Run `roster.check_authored()` after —
it caught a duplicate `note:` key that `safe_load` had been silently resolving,
hiding the fact that MPT's weights were recovered from mirrors.

**Adding attestations: `attest.merge_claims()`, not `ingest()`.** `ingest()`
replaces a whole checkpoint entry, which is right for a lineage-shaped pass and
destroys seven fields on a targeted one.

---

## Running a measurement

```bash
python -m malignment.runners "<model_id>" --all-prompts    # ~3 s/cell at 7B on this Mac
```

`Checkpoint(mid)` resolves a pinned revision from **either** the `@suffix` or the
roster's `revision:` field. `@` is an *identity* mechanism — two revisions of one
repo need distinct ids in the store — and `revision:` is the *pin*.
`BAAI/Aquila2-7B` is why: its `main` was replaced with a re-tokenised model,
vocab 143,973 against the pinned 100,008, so a bare-id run **succeeds** and pairs
a 100k-vocab model with a 144k tokenizer.

---

## Where things live

    malignment/            code + the authored roster        public, git
    ~/malignment-data/twp/ measured jsonl                    private, rsync target
    ClickHouse             the queryable store               derived, rebuildable
    ~/malignment-verification/  spot checks, NOT corpus      outside the ingest root
    malign-logits/data/    the archive                       READ-ONLY legacy
