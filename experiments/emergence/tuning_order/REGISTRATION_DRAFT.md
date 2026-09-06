# tuning_order — REGISTRATION, DRAFT AND NOT FROZEN

**Status: DRAFT, 2026-09-06. Not frozen, and it must not be frozen by the seat that wrote it alone.** Registration in this campaign is collaborative: a freeze binds the design, and it cannot tell us the design answers the question. The three items marked **[RH]** are the ones a freeze would lock in and that I should not lock alone.

## 0. WHY THIS NEEDS A REGISTRATION AT ALL

**There is an outcome we would rather see.** The paper's thesis has a temporal form — bar first and at once, substitute later and gradually — and F04 reported exactly that. A seat that already knows the shape it wants can find it in 43 rungs × many sites without meaning to, by choosing an onset criterion, a site set, or a smoothing window after seeing curves.

So the directions are stated before anything runs.

## 1. THE FAVOURED DIRECTION

**Departure onset precedes arrival onset**, per site, and the two have different shapes:

- **departure is step-like** — most of its total change within the first few percent of steps
- **arrival is gradual** — accumulating across the middle of the ladder

## 2. THE DISAPPOINTING DIRECTIONS, EACH OF WHICH IS A RESULT

Stated because the commission requires them, and because "we found the lag" is worth nothing unless these were live:

1. **Arrival first.** The riser's mass rises before the faller's mass drops. This inverts the paper's reading: the substitute is installed and the transgressive word is displaced by competition rather than barred.
2. **Both at once.** No resolvable lag at 43 rungs. Then the mechanism is one operation, not two, and the paper drops "sudden" and drops the ordering.
3. **No persistent onset at all.** Neither curve has a rung whose CI clears zero and stays clear. Then the ladder is too coarse or the sites too noisy, and the honest report is that the instrument cannot resolve the question — not that there is no order.
4. **Lag present but not step-like/gradual.** Both curves the same shape. The order survives; the *character* of the two operations does not, and the paper cannot say "at once" versus "gradually".

**Outcome 3 is the one to guard against reading as outcome 2.** Absence of a resolvable onset is an instrument statement, not a finding about SFT. See the campaign rule that a negative check is not a finding.

## 3. THE DESIGN

**Unit.** The rung × site. Prompts are the replicate **within one lineage** — n=1 lineage, graded C. Nothing here is about SFT in general.

**Ladder.** `allenai/Olmo-3-7B-Think-SFT@step*`, 43 rungs, base fixed at the ladder's own base. Verified present: 97,696 cells over 2,272 prompts. **No second SFT ladder exists in the store** — the other three ladders are pretraining.

**Frame.** Both arms raw.

**Measure.** Per rung, movement against the fixed base over the prompt panel; then per site two curves as a function of step:
- **departure** = mass of the top faller(s)
- **arrival** = mass of the top riser(s)

**[RH] Onset criterion.** Proposed: first rung whose bootstrap CI of the median sits past zero **and stays there to the end of the arm**, plus the coverage gate — as Finding E. The "stays there" clause is what makes it an onset rather than a first crossing, and it is the clause most likely to be wrong for a curve that bounces (F04 reported "kill" recovering by step 20000). **Needs sign-off: if a curve legitimately re-crosses, this criterion returns "no onset" for a real effect.**

**Domains.** sexual, violence, **neutral control** — the control is not optional; F04 had none.

**Report.** Departure onset, arrival onset, the lag between them, and the shape test, per domain. Sign tests over sites within the lineage. **Quote the shape and the onsets, never a constant.**

**Exhibits.** fuck/kiss, kill/scream, kill/said — as figures, and the third tested as a domain funnel (existence's Q enrichment) rather than as one word.

## 4. [RH] THE RULE VERSION, WHICH IS NOT A DETAIL

The ladder is **rule_version 3**. Canonical is v4, and `twp_cells_v4` holds **zero** rungs of it. Olmo-3 is byte-level (`GPT2TokenizerFast`, ` scream` → `Ġscream`), and the project's measurement of where v4 is bit-identical to v3 says **not one byte-level model is Latin-identical** (0/59 models, 0/708 prompts).

**Proposed: settle it by measurement before choosing.** The ladder's endpoint model has 2,623 prompts with cells under both rules, 512 of them shared with the ladder's own prompt set. Compute the departure/arrival quantity under v3 and v4 at that model. If the rule does not move it at the effect size, running the ladder at v3 is licensed by measurement; if it does, the ladder needs re-measuring at v4 and we know why.

**This runs BEFORE the registration freezes**, because its outcome changes what the registration is registering.

## 5. [RH] WHAT COUNTS AS A SITE

Not yet specified, and it is the choice most open to unintentional shaping. F04 used **hand-picked words**, which is one of the reasons it cannot be cited. Options, needing a decision rather than a default:

- the lexicon's existing sites (`project_lexicon_construction`: 25 words carry 88.7% of mass, ~97% violent — so a word-level site set is skewed by construction)
- per-prompt top-faller/top-riser, derived at the BASE and then held fixed across rungs
- a declared domain vocabulary

**Whatever is chosen must be fixed at the base and not re-derived per rung**, or "the top faller" changes identity along the ladder and the curve is a composite of different words.

## 6. WHAT THIS CANNOT ANSWER WHATEVER IT RETURNS

- **Anything about SFT in general.** One lineage.
- **Anything about DPO or RLVR ordering.** Different ladders, not in scope.
- **Whether the order is causal.** It is a description of when things move, on one recipe.
- **Weatherby's claim on his own object.** He fine-tuned GPT-2 on the Communist Manifesto; this is Olmo-3 on an instruction mixture. It meets him at the GRAIN, not on the case.
