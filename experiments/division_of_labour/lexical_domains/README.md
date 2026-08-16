# lexical_domains

**Question.** Is the division of labour content-dependent — does SFT do relatively more of the work on *sexual* words and the preference stage more on *violent* words — when measured on the words themselves rather than on prompt-domain labels?

**Status: RUN, 2026-08-16. L1 NOT SUPPORTED.** Lexicon `d542e7e2bb86bd00`, 18 chains over 16 bases, 2,190-prompt panel.

## Result

```
L1   share_sexual − share_violent
     CHAIN level   mean +0.0161 | 12/18 positive | sign p = 0.2379
     BASE  level   mean +0.0052 | 10/16 positive | sign p = 0.4545   <- DECIDES
```

**The claim is withdrawn.** *"SFT handles sex, DPO handles violence"* has now returned null at prompt level (H3: base p=0.077) and at word level (L1: base p=0.45), on two different measurements of two different quantities. The registration's stopping rule pre-committed this outcome: **it is not tested a third time with a third instrument.**

Note what the word-level test did to the effect. H3's base-level difference was +0.0086 at p=0.077 — a near-miss that invited another look. Measured on the words the claim is actually about, it is **+0.0052 at p=0.45**. The better instrument did not rescue the effect; it made it smaller and less certain.

## L2 — and this is the part that matters

The contrast, computed within prompt domain, base level, 16 bases:

| prompt domain | sexual − violent | positive | p |
|---|---|---|---|
| betrayal | +0.1475 | 13/16 | 0.021 |
| taboo | +0.1499 | 12/16 | 0.077 |
| property | +0.0600 | 12/16 | 0.077 |
| violence | +0.0322 | 9/16 | 0.80 |
| **sexual** | **−0.0499** | **6/16** | 1.00 |
| neutral | −0.0507 | 8/16 | 1.00 |

**Under sexual prompts the effect runs backwards.** In the one domain where "SFT handles sex" should be most visible, sexual-word mass is *less* SFT-dominated than violent-word mass, in 10 of 16 lineages. Whatever produced the positive chain-level mean, it is not a sexual-content effect.

Three cautions on this table, all of which cut against reading anything into it:

- **13 domains were tested.** At α=0.05 that is ~0.65 expected false positives, and `betrayal` at p=0.021 is one comparison of thirteen. Nothing here survives correction and nothing here is claimed.
- **`share` is a ratio and its mean is unstable.** `animal` shows +4.24 and `substance` +12.26 on 6/16 and 9/14 — those are small denominators, not large effects. The sign counts are the robust reading, and they are what the table is ordered on.
- **The panel is not composition-neutral.** It keeps 100% of `taboo` and `property` but 42% of `neutral` and 34% of `contradiction`.

## L3 — where the mass goes

Mean over 18 chains, per arm:

| category | arm | departed | arrived | net |
|---|---|---|---|---|
| sexual | SFT | 0.005444 | 0.002813 | **−0.002631** |
| sexual | pref | 0.005948 | 0.002895 | **−0.003053** |
| violent | SFT | 0.009316 | 0.005764 | **−0.003552** |
| violent | pref | 0.010483 | 0.006494 | **−0.003989** |

**Both categories lose net mass at both stages, and departure runs about twice arrival.** Mass is not migrating *into* sexual or violent vocabulary from elsewhere; it is leaving. At category granularity this looks like suppression, not displacement.

That bears directly on `register_shift`'s **R1**, which predicts a fall in vulgar-register sexual mass *matched by a rise* in clinical/euphemistic — a within-category migration. A within-category migration would show departed ≈ arrived for the category as a whole. It does not. This does not decide R1, which is a finer decomposition on a different axis, but it is the direction R1a-without-R1b would take, and it was registered as the outcome I would rather not see.

## Method

`run.py` is thin on purpose. The per-word JS term, the same-prompts-on-both-arms intersection, the base-level collapse and the conservation check live in `malignment/wordfield.py`, because `register_shift` and every `fields.py` source need the identical machinery with a different label column.

    js_w    = 0.5 * ( p·log₂(p/m) + q·log₂(q/m) ),  m = (p+q)/2
    js_C    = Σ js_w over words labelled C
    share_C = js_C(base→sft) / js_C(base→endpoint)

JS is a sum over words plus a tail, so a category's contribution is exact. Checked against `movement_cells.js_total − js_tail`, booked by a different producer: **worst |diff| 5.2 × 10⁻¹⁸** over 200 prompts.

## What this does not say

It does not say alignment ignores sexual content — the transgressive-mass results stand and are a different measurement. It says the *relative division of labour between training stages* does not differ by content type, at either granularity tested.

It also does not vindicate any alternative. A null is a null: the honest summary is that we cannot distinguish the stages' content specialisation from zero, on 16 lineages, with this panel.
