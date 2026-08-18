# HOWTO — the one way to ask each question

**Every snippet here is executed by `docs/test_howto.py`.** That is the whole
design: a prose howto drifts from the code the week after it is written, and
nobody notices because prose cannot fail. These run. If a function is renamed or
its answer changes, the test breaks and this file gets fixed with it.

**If your question is not here, add it here** — with the call, and a line in the
test. The failure this file exists to stop is not ignorance, it is *three seats
answering the same question three ways and none of them wrong enough to notice*.

---


## Which corpus am I reading? (v3 vs v4)

**There are two twp corpora and the analysis surfaces default to the older one.**

    rule_version 3  ->  twp_cells,    twp_words        full roster
    rule_version 4  ->  twp_cells_v4, twp_words_v4     23 models as of 2026-08-18

`corpus.retable(sql, rule_version)` rewrites a v3-literal query to point at either. The modules that read the corpus carry a module-level `RULE_VERSION`, defaulting to **3**:

    from malignment import similarity
    similarity.RULE_VERSION = 4
    similarity.build_panel()

`similarity`, `movement` and `population` are wired. `views.py` builds ClickHouse VIEWS over v3 only and is deliberately not switchable — see its header. `vectors.py` is the vector store and is unwired.

**Why the default is 3 and not 4.** v4 covers 23 models against v3's full roster, so flipping the default would silently shrink every panel rather than announce anything.

**Why this section exists.** Until 2026-08-18 the v4 corpus was effectively write-only: `ingest` and `corpus` were the only modules that knew `twp_*_v4` existed, so any query for twp data returned a well-formed answer from the wrong corpus. That is worse than an empty result — an empty one at least looks like something is missing, whereas a full result from the previous instrument looks like success and nothing prompts a second reading.


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
| else an authored `rulings.endpoint` entry | a person's choice, applied **only** where the chain abstained |
| else **returned as `unresolved`** | never silently picked |

**THE RULING STEP IS LAST ON PURPOSE.** It can settle a case the rules cannot and
can never overturn one they can, so a ruling is incapable of silently overriding
a derivable answer. `endpoints(apply_rulings=False)` returns what the chain alone
decides — today **49 resolved, 1 unresolved** against the ruled view's 50 — and
`{db}.endpoints.resolved_by` says which decided each row (`roster.endpoints` or
`rulings.endpoint`). A ruling naming a non-candidate **raises**; a ruling the
chain no longer needs is reported by `check_authored()`, because a ruling that
decides nothing still reads as being in force.

It exists because `stablelm` has two terminal arms that are both `stabilityai`
and both attested `direction: standard`, so steps 2, 3 and 5 all abstain. The
only alternatives were to declare one arm an `ablation` or attest it `inverted`
— **both false of it**. Encoding a ruling as a fact about the model would have
put a wrong claim into the file every other consumer reads.

Without attestations `zephyr-7b-beta` and both dolphins become eligible
*candidates*.

**`distill` and `distill_align` are different operations and the difference is
two lineages.** Until 2026-08-16 one op carried both, and the cost was that
`Qwen/Qwen3-8B` and `openbmb/MiniCPM5-1B` — both fully measured, neither missing
a cell — were invisible to `endpoints()`, which stood at 48 while
`population("bases")` stood at 50. **That two-number gap was the symptom and
nobody read it**; it was found by asking why the roster would not reach an even
50, not by any check.

    distill        another lab's base, retrained on a third model's traces.
                   DeepSeek-R1-Distill-Llama-8B <- Llama-3.1-8B. Not alignment.
    distill_align  the model's OWN base, KL to a teacher, and it IS the
                   post-training. Qwen3-8B, MiniCPM5-1B.

The tell that the fix is right rather than merely bigger: `bases` was **already**
50, and closing the op distinction closed the gap exactly, with `unresolved`
still empty. A change that had widened a rule instead would have moved endpoints
past bases or left a candidate unresolved.

**AND TODAY THAT FILTER DECIDES NOTHING. It is UNREACHABLE, and the test found
that out.** All 50 endpoints resolve identically with and without attestations.
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
uniform: **34 paths are one step, 11 are two, 5 are three.**

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
have a multi-step path and 16 have a chain, **and they are not the same sixteen**:
`MiniCPM5-1B-Base` (`sft` → `distill_align`) and `RedPajama-INCITE-Base-7B-v0.1`
(`sft` → `sft`) have 2-step paths that `chains()` excludes, because neither ends
in a named preference op.

*Corrected 2026-08-17.* This example used to name `stablelm-2-1_6b` as a 2-step
path and gave the reason as "their last op is `instruct`". Both were wrong, and
for different causes: stablelm's second step was a **fabricated edge** (docket
[6371] — `chat` and `zephyr` are siblings off the base, not a chain), and neither
surviving example ever ended in `instruct`. A doc example is a claim.

### any other population

**One function, seven names, so nobody writes an eighth comprehension.**

```python
roster.population("endpoints")                  # 50   one per lineage
roster.population("chain_rungs")                # 52   every rung of a full chain
roster.population("aligned")                    # 101  every ALIGNING child
roster.population("bases")                      # 50   pretrained roots
roster.population("all")                        # 160  every declared node
roster.population("representative")             # 10   members of a representative family
roster.population("unavailable")                #  6   declared and deliberately unmeasurable
roster.population("aligned", measured=True)     # 101  ...restricted to those with cells
```

`endpoints` and `chain_rungs` are **different populations and both are right**:
an endpoint asks *what does a user receive*, a chain rung asks *which stage did
it*. 50 lineages have an endpoint; 16 have a full chain.

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
roster.direction("sft", "distill_align")  # "forward" — MiniCPM5 ran sft, then OPD
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
n_models, prompts = corpus.panel()      # 159 models, 2,189 prompts
```

**Never "all prompts".** Prompt sets are fleet-defined and do not nest: the
universal intersection over all 402 measured models is **one prompt**; over the
159 in `pairs` it is 2,190, and 2,189 after the live-status gate. The step/ladder
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

## What does this checkpoint need, and what do I rent for it?

```python
from malignment import roster
roster.environment("Zyphra/Zamba2-7B")          # merged: profile floors + its overrides
roster.environment("BAAI/Aquila2-7B", engine="0.27.1")   # + the (arch x engine) ruling
roster.fleet(roster.population("endpoints"))    # -> {boxes, blocked, unassigned}
```

**Nine sources across two repos, and a caller reads none of them.** The archive
held this in `model_requirements.json`, `model_load_environments.json`,
`vllm_engine_support.json`, `cloud_profiles.json`, `weights_audit.csv`,
`twp.py`'s `LOADER_OVERRIDE`, `build_fleet.py`'s `LAUNCH_PROFILE` and two prose
docs — and the map between the two profile vocabularies existed only as a dict
literal on line 78 of a script.

### three fact classes, three keys, and they do not fold into each other

| class | keyed by | lives in |
|---|---|---|
| REQUIREMENT | CHECKPOINT | `models.yaml` `nodes[m].env` |
| OUTCOME | (MODEL × ENVIRONMENT) | `observations.json` `observations` |
| SUPPORT | (ARCHITECTURE × ENGINE) | `observations.json` `engine_support` |

**`environment()` has no `ok` field and never will.** "Will this load?" has no
answer keyed on the model alone: seven models carry both a `load_failed` and a
`loads`, and `LLM360/AmberSafe` did both **on one box, twenty minutes apart**,
either side of `pip install sentencepiece protobuf`. `observations` comes back
as a list, possibly contradictory, never collapsed to a verdict. Absence means
UNTESTED, never "works".

Likewise `engine` is an argument, not a field. `BAAI/Aquila2-7B` is not broken —
vLLM **deleted** `AquilaForCausalLM` after v0.24.0, so the same model is
`usable=False` at 0.27.1 and `usable=True` at 0.22.1, with `recovery_box`
naming where to run it.

### TWO VOCABULARIES SHARE THE WORD `default`, AND THEY ARE DIFFERENT HARDWARE

    PROFILE `default`   what 127 models NEED   -> launches on box `dense`  (48GB)
    BOX     `default`   a shape you can rent      300GB A100, 80GB          (80GB)

`malign cloud launch --profile default` and a model whose requirement profile is
`default` do not name the same machine. Say **box** or **profile** every time.

### every checkpoint declares, and that is enforced

```python
roster.check_environments()    # [] when clean
```

160 of 160 carry `env:`, every override carries its own `why`, and every box
physically holds the models routed to it. **A coverage claim that is not a gate
decays silently**: the next model added would land in `default` and a fleet
would pay for a download it cannot use.

Four defects were found by that gate on its first run, each of which had been
sitting in the archive:

- `gl198976/mpt-7b` inherited `blocked: repo_dead` from the **dead** `mosaicml`
  repo it mirrors — three live checkpoints excluded from every plan, with a
  reason that reads perfectly true and is about a different repository.
- Zamba2 was profiled `tf457`, which launches on `dense` — **a box with no
  kernels**, while its own row demanded `mamba-ssm`. Measured hybrid penalty for
  missing kernels: 19.3×. It would have run ~19× slow and reported nothing.
- The Olmo-3-32B quartet sat on a 48 GB box needing 80. `build_fleet.py` emits
  `launch_profile: dense` and `min_vram_gb: 80` **into the same dict and never
  compares them**.
- `phi-4`'s `no_base_released` — a POPULATION ruling — was filed as an
  ENVIRONMENT block, so `fleet()` skipped three checkpoints that run fine.

### sizing is derived, never transcribed

`min_vram_gb`/`gpus` are a step function of **measured** `params_b`, so they are
computed, not written onto 160 checkpoints. `needs_vram_gb` is `None` when
nothing has measured the model — **unknown size is not small.** The first
version read the wrong JSON level, got `None` for all 160, and `(params_b or 0)`
turned every one into 24 GB / 1 GPU, including the 70B pair. It planned cleanly
and would have OOMed after a 140 GB download.

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
