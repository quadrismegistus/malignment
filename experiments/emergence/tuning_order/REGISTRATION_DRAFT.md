# tuning_order — REGISTRATION, DRAFT AND NOT FROZEN

**Status: DRAFT, rewritten 2026-09-06 around RH's three questions.** Not frozen. **One item is open and it is the one that can silently turn a result into a null: the onset criterion (§5).** Everything else below is settled, and the things that settled it were measurements, recorded here so a later reader does not have to take them on trust.

## THE QUESTION, IN RH's FRAMING

> 1. For the faller/risers at Olmo base → aligned, **does the faller fall before the riser?**
> 2. Is this always the case, or **specifically at high-lift prompts?**
> 3. Is this the case for **any** faller/riser, or specifically for **charged words?**

That is the whole experiment. An earlier draft treated "what counts as a site" as a fourth open decision; it is not, and §2 says why.

## 1. WHY THIS NEEDS A REGISTRATION

**There is an outcome we would rather see.** The paper's thesis has a temporal form — bar first and at once, substitute later and gradually — and F04 reported exactly that. A seat that knows the shape it wants can find it across 43 rungs × many sites without meaning to, by choosing an onset criterion or a site set after seeing curves.

**Favoured direction:** departure onset precedes arrival onset; departure step-like (most of its total in the first few percent of steps), arrival gradual.

**Disappointing directions, each of which is a result:**

1. **Arrival first.** The substitute is installed and the transgressive word is displaced by competition rather than barred. Inverts the paper's reading.
2. **Both at once.** No resolvable lag at 43 rungs → one operation, not two. The paper drops "sudden" and drops the ordering.
3. **No persistent onset at all.** Neither curve resolves. **This is an instrument statement, not a finding about SFT**, and must not be reported as outcome 2.
4. **Lag present but both curves the same shape.** The order survives; the *character* of the two operations does not.

## 2. SITES — SETTLED, AND NOT A FREE CHOICE

**Sites are the faller/riser pairs at `allenai/Olmo-3-1025-7B` → `allenai/Olmo-3-7B-Think-SFT@step43000`, derived ONCE and then tracked back across all 43 rungs.**

Fixed at the endpoint, so "the top faller" cannot change identity along the ladder — which was the only real requirement. F04 did this by hand on three pairs (fuck/kiss, kill/scream, kill/said); this does it systematically.

**The endpoint MUST be the ladder's own end, not the released Think model.** Sites drawn from base → `Olmo-3-7B-Think` (post-DPO, post-RLVR) would include words that DPO moved and SFT never touched. Those sit flat across all 43 rungs, register as "no onset", and dilute both curves — shortening the apparent lag, which is the quantity under test.

**`step43000` IS the released SFT checkpoint**, checked rather than assumed: over 161,281 shared (prompt, word) cells, mean |Δp| = 4.9e-05, max 0.0073, r = 0.99999.

## 3. THE PANEL

    43 rungs, steps 1000..43000 in even 1000s, 2,272 prompts each — a COMPLETE
    rectangle. All 2,272 also present on the base. No gaps.

    of those 2,272:  1,802 are VERSE PREFIXES from the M05 rhyme fleet, the
                     wrong instrument here and excluded
                       470 carry charge ratings — the analysis panel
                       529 are in the prompts registry

Base is `allenai/Olmo-3-1025-7B`, the roster-declared lineage root. There is no `step0`.

## 4. THE THREE MEASURES

**Q1 — the main effect.** Per site, two curves over rung: mass of the endpoint faller, mass of the endpoint riser. Departure onset, arrival onset, lag = arrival − departure. Sign tests over sites **within the lineage**. Quote the shape and the onsets, never a constant.

**Q2 — moderation by prompt lift.** `charge.lift(p)` = dose − frame, which the accessor's own docstring names as *"the dose any displacement work wants, not `dose()`"* — corr(effect, dose) = −0.091 against corr(effect, lift) = −0.261, and −0.31 within frames below 5. **Continuous regressor over 470 rated prompts**, not a two-bin contrast.

**A `neutral` domain label is NOT the control.** Categorical `domain='neutral'` gives 8 prompts; lift gives 70 at ≤0, 179 at ≤0.10, 191 at dose 1–2. And the low-lift set spans dose 1.00–7.00 — prompts with a charged *frame* that add nothing over it, which a label gets wrong in both directions.

**Q3 — moderation by word charge. `fields.py` type-level norms are PRIMARY; `charge.py` is a secondary on its covered subset.** Charge is the better construct — it rates the completed scene, in context — but its coverage of endpoint sites is **73.4% of fallers against 60.8% of risers**, and risers are the arrival side. `fields.py` covers every word by construction, at the cost of being context-free. Divergence between them is informative, not a problem.

### THE RULE THAT GENERATED TWO OF THOSE THREE CHOICES

**Nothing that covers fallers and risers unequally may define the site set or the curves.** Any such asymmetry lands directly on the lag, which is the quantity under test. It is why charge is secondary rather than primary in Q3, and why lift may stratify prompts but must never select which words count as sites.

Lift passes the matching test at the prompt level, checked: rated-word coverage of top movers is **flat across the ladder** for fallers — 67.4% / 67.0% / 67.7% at steps 1000 / 20000 / 43000. On risers it drifts 67.2% → 60.7%, which is the same asymmetry again and the reason for the restriction.

## 5. [RH] THE ONSET CRITERION — THE ONE OPEN ITEM

Proposed (from Finding E): first rung whose bootstrap CI of the median sits past zero **and stays there to the end of the arm**, plus the coverage gate.

**The "stays there" clause is the problem.** F04 itself reported "kill" falling by step 5000 and **recovering by 20000**. On a curve that legitimately re-crosses, this criterion returns *no onset* for a real effect — and "no onset" is disappointing-direction 3, which is an instrument statement. So the clause converts a real non-monotonic effect into a null of a different kind.

Alternatives, none chosen:

- **first crossing only** — sensitive to a single noisy rung
- **first crossing that persists for k consecutive rungs** — k is a new free parameter
- **first crossing, with non-monotonicity reported separately** as a property of the curve rather than a disqualification

**This must be fixed before any curve is looked at.** It is the choice most able to manufacture the favoured answer or destroy a real one.

## 6. THE RULE VERSION

The ladder is `rule_version` 3; canonical is v4, which holds **zero** rungs of it. Olmo-3 is byte-level (`GPT2TokenizerFast`, ` scream` → `Ġscream`) and the project's own measurement says **not one byte-level model is Latin-identical** between v3 and v4 (0/59 models, 0/708 prompts).

**Lower risk than it first appears**, for a reason specific to this design: all 43 rungs are measured under the *same* rule, so a v3/v4 difference is largely a uniform level shift, and every claim here is about onset, lag and shape — never a level. The residual risk is the boundary rule changing *which word* is the top faller, which is checkable at the endpoint model (cells under both rules) and should be checked before the freeze.

**Note `rule='canonical'` in the movement tables is NOT a version stamp.** It names the faller/riser classification rule (`min_prob=0.003, fall_ratio=0.5, delta=0.003, null_test=True`), which did **not** change between v3 and v4. The twp version is carried by the table. An earlier draft called this a collision; it is not.

## 7. WHAT THIS CANNOT ANSWER WHATEVER IT RETURNS

- **Anything about SFT in general.** **n=1 lineage**, graded C — confirmed by query, not assumed: the store holds exactly one SFT ladder, and Olmo-3-base, Olmo-3-Think and Pythia-6.9b are all *pretraining* ladders.
- **Anything about DPO or RLVR ordering.** Not on this ladder.
- **Whether the order is causal.** It describes when things move, on one recipe.
- **Weatherby's claim on his own object.** He fine-tuned GPT-2 on the Communist Manifesto; this is Olmo-3 on an instruction mixture. It meets him at the **grain**, not on the case.
