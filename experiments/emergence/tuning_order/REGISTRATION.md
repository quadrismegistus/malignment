# tuning_order — REGISTRATION, FROZEN 2026-09-06

**FROZEN.** Written and agreed with RH before any curve was looked at. The data layer existed at freeze time (`b97752c`: 424 charge cells, 18.3M `movement_rungs` rows) and **no analysis had been run against it**.

## 0. WHAT THIS DOCUMENT IS, AND WHAT IT IS NOT

**RH, 2026-09-06, and it governs everything below:**

> *"We will not let registration stop us from analysing whatever we find even if off registration — I don't believe in that for humanities work. It's a soft border not a hard one."*

So this is **not** a pre-commitment that forbids other analyses. It is a **record of what was expected before looking**, and its entire function is to preserve one distinction that is unrecoverable afterwards:

    DECLARED     stated here before any curve was seen
    DISCOVERED   found by looking, and worth reporting

Both are legitimate. Only the first can be cited as a prediction that survived a test; the second is a pattern noticed, which in this field is often the more interesting object and is not diminished by being labelled. **A registration that is departed from and says so is honest; one that is silently departed from is worthless; one that prevents the departure is doing humanities badly.**

The single rule: **anything not declared here gets labelled as discovered when reported.** Not suppressed, not apologised for — labelled.

## 1. THE QUESTION

> 1. For the faller/risers at Olmo base → aligned, **does the faller fall before the riser?**
> 2. Is this always the case, or **specifically at high-lift prompts?**
> 3. Is this the case for **any** faller/riser, or specifically for **charged words?**

## 2. DECLARED EXPECTATION

**Favoured:** departure precedes arrival; departure step-like, arrival gradual.

**Disappointing directions, each a result:**

1. **Arrival first** — the substitute is installed and the transgressive word displaced by competition rather than barred. Inverts the paper's reading.
2. **Both at once** — one operation, not two. The paper drops "sudden" and drops the ordering.
3. **Neither resolves** — an **instrument statement**, not a finding about SFT, and must never be reported as (2).
4. **Lag present, both curves the same shape** — the order survives, the character of the two operations does not.

## 3. THE ONSET CRITERION — AREA-BASED (RH's call, 2026-09-06)

The earlier proposal was Finding E's "first rung whose CI clears zero **and stays clear to the end**". **Rejected**: F04 reports `kill` falling by step 5000 and recovering by 20000, and on such a curve that rule returns *no onset* for a real effect — converting a non-monotonic result into disappointing-direction 3, which is a statement about the instrument.

### The normalised progress curve

For each site, from `movement_rungs` where `kind='base_rooted'`:

    d(n)  = p(step n) - p(base)                    the cumulative delta
    T     = d(43000)                               total movement at the ladder end
    f(n)  = d(n) / T                               progress, 0 -> 1 for BOTH signs

Dividing by the signed total makes `f` run 0→1 for fallers and risers alike, so the two are directly comparable without sign handling.

### Primary statistic: AUC, which is threshold-free

    AUC = mean over the 43 rungs of f(n)

    AUC -> 1.0   all movement completed immediately (step-like)
    AUC ~ 0.5    movement accumulates linearly (gradual)
    AUC -> 0.0   all movement at the very end

**No threshold, no crossing, no "first rung".** A curve that overshoots and returns still has a well-defined AUC, which is exactly what the rejected criterion could not handle.

    Q1 test:  AUC(faller) > AUC(riser), paired per prompt, sign test over prompts
    SHAPE:    AUC itself IS the shape measure — step-like is high AUC

**`f` is NOT clamped to [0,1].** Non-monotonic and overshooting curves keep their real values, and the fraction of sites with `f(n) > 1` or `f(n) < 0` at any rung is **reported as a property of the ladder**, not cleaned away.

### Secondary, for reporting a step number

    t50 = the first rung at which f(n) >= 0.5

Interpretable and quotable ("half the fall is done by step X"), but **not the test statistic** — it reintroduces a threshold and a first-crossing. Reported alongside AUC, never instead of it.

### The unit and the pairing

**One faller and one riser per prompt** — the top of each by |delta| at the endpoint contrast, per the commission's "mass of the top faller(s) and the top riser(s)". That gives one paired comparison per prompt; **prompts are the replicate within one lineage**. Sign test, two-sided.

Sites come from base → `Think-SFT@step43000` under `CANONICAL` (`min_prob=0.003, fall_ratio=0.5, delta=0.003, null_test=True`), derived **once** and tracked back. Fixed at the endpoint, so a site cannot change identity along the ladder.

## 4. Q2 — LIFT AS A CONTINUOUS MODERATOR

`charge.lift(p)` = dose − frame, which the accessor names as *"the dose any displacement work wants, not `dose()`"* (corr with effect −0.261 against dose's −0.091). Regress the per-prompt lag (ΔAUC) on lift. **Continuous, not a two-bin contrast.**

**A `neutral` domain label is NOT the control.** It gives 8 prompts; lift gives 70 at ≤0 and 191 at dose 1–2, and the low-lift set spans dose 1.00–7.00 — charged frames that add nothing over themselves, which a label misclassifies in both directions.

## 5. Q3 — `fields.py` PRIMARY, `charge.py` SECONDARY

`fields.py` type-level norms cover every word by construction. `charge.py` is the better construct — it rates the completed scene, in context — but the new edge annotation covers **424 of 512** target prompts, and word-level coverage of endpoint sites was 73.4% of fallers against 60.8% of risers before this run.

**THE RULE THAT DECIDED THIS, AND IT BINDS ANY LATER CHOICE TOO:** *nothing that covers fallers and risers unequally may define the site set or the curves.* Any such asymmetry lands directly on the lag. Charge may moderate; it may not select.

Divergence between the two instruments is informative, not a problem.

## 5a. AMENDMENT, 2026-09-06 — Q3's INSTRUMENT. `fields.py` DROPPED.

**The frozen §5 is preserved above and is superseded by this. RH's call, same
day, after Q1 ran and before Q3 ran.**

§5 made `fields.py` primary *because* `charge.py` covered only 73.4% of fallers
and 60.8% of risers. **That reasoning was about the OLD annotation on the
Instruct edge**, and it no longer applies: `charge_edge.py` annotated THIS edge,
and the residual gap is not a coverage failure. Measured — the 102 top-fallers
that are unrated are:

    was 20, be 17, A 13, he 11, the 6, she 6, and 2, they 2, ...

**Function words, every one**, excluded by the content filter before rating
rather than missed by the rater. Over the words the question is about, the
annotation is effectively complete.

So the ground for a second instrument is gone, and RH: *"I don't want to add
another instrument."* `fields.py` is dropped from Q3 entirely. That also removes
a defect it would have introduced: type-level arousal rates `cry` at 5.45 and
would have admitted 24 `cry` sites to the charged panel, where in context `cry`
scores an increment of **0.0**. Loadedness is a property of a word AT A SLOT.

**AND NO CATEGORICAL FILTER.** An earlier proposal of mine was `kind != NONE`.
RH: *"why filter on kind?"* — correctly, because it repeats one step later the
error §4 had just corrected: `kind` is a label the same rater assigns alongside
`scene`, so filtering on it discards the degree information and reintroduces
exactly the category grain that `domain='neutral'` was rejected for.

**The Q3 moderator is `scene(w) - frame`, the faller's own increment over its
setup** — word-level lift, the same construct as Q2's prompt-level `charge.lift`,
unaggregated. It behaves:

    kill +4.0 (n=27)   fuck +4.5 (n=8)   die +2.0   scream +1.0
    cry   0.0 (n=35)   marry 0.0         have 0.0   said 0.0    check 0.0

**A BOUND ON IT, STATED BEFORE THE TEST IS CHOSEN.** The increment is heavily
zero-inflated: n=6,884, median 0, and EIGHT of ten deciles sit at exactly 0. So
"continuous regressor" overstates it -- this is a large null mass with a thin
charged tail, and a linear fit would be driven by the tail while reporting a
slope as though it described the whole. The test must be rank-based or must
report the zero mass and the tail separately. **Which of those is not yet
decided and is not decided here.**

Panel sizes are small in the tail: `kill` 27 sites, `fuck` 8. Per-word effects
there are individual prompts, not populations.

## 6. THE DATA, AS FROZEN

    movement_rungs      18,304,726 rows, 0 refused
      base_rooted       10,455,962   43 steps   2,272 prompts
      increment          7,872,764   42 steps   2,272 prompts
    charge_olmo_thinksft_v3.jsonl   424 cells, flash, v3 candidate lists

`rule_version=3` throughout — the ladder exists only in `twp_words`; `twp_cells_v4` holds zero rungs of it. All 43 rungs measured under the same rule, so a v3/v4 difference is a uniform level shift and every claim here is about onset, lag and shape, never a level.

1,802 of the 2,272 prompts are **verse prefixes** from the M05 rhyme fleet and are excluded at analysis time. They are in the table deliberately: a table silently holding part of a measured population is the harder defect to find later.

## 7. STATED BOUNDS

- **n=1 lineage, graded C.** Confirmed by query: the store holds exactly one SFT ladder; Olmo-3-base, Olmo-3-Think and Pythia-6.9b are all *pretraining* ladders.
- **Endpoint-arms-only charge misses transients**, measured: 4,043 of 13,559 word types (29.8%) carrying 2.31% of ladder mass, none reaching a 10% peak.
- **Nothing about SFT in general**, about DPO/RLVR ordering, or about causation.
- **Weatherby is met at the GRAIN, not on the case.** He fine-tuned GPT-2 on the Communist Manifesto; this is Olmo-3 on an instruction mixture.
- **`--no-clamp` non-monotonicity is reported, not corrected.**
