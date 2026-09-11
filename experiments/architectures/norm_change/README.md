---
subject: architectures
kind: question
status: "RUN 2026-09-11 as a lookup over displacement/norm_change per-lineage dose slopes, which required adding dose.py --per-lineage that day (the aggregate CSV had been collapsing the vector). Population is the 45 MATCHED pairs, not existence's 50: norm_change/README.md makes --match-framed non-optional. All 12 architecture-relevant models are in the 45."
question: Does alignment's movement along word norms depend on the attention mechanism?
headline: "It does not. falcon-mamba-7b, which computes no attention, agrees with the roster median on 12 of 12 top dose targets, where the roster agrees with itself on 38-40 of 45. The only two dissenters, rwkv-4-7b-pile (6/12, chance) and Falcon-H1-7B-Base (7/12), are also the two lowest |slope| in the existence table, so agreement tracks how much a model was ALIGNED rather than what it is built from."
---

# norm_change

**Does the dose-response `displacement/norm_change` measures depend on the architecture?** A second delta instrument on a different construct, and it agrees with the first.

## The second instrument agrees



`norm_change` asks a different question of the same roster: does the base arm's transgressive lift predict what alignment moves along word norms? Until 2026-09-11 it wrote only the aggregate, one row per target already collapsed over lineages, so no question could stratify it. `dose.py --per-lineage` now writes the vector beside it (the aggregate files are byte-identical under the same flags, checked).

Taking the top 12 targets by p and asking how often each model's slope has the same sign as the roster median:

    model                    attn           block     agree
    Falcon-H1-1.5B-Base      full+ssm       hybrid    12/12
    OLMoE-1B-7B-0125         full           moe       12/12
    falcon-mamba-7b          none           ssm       12/12
    Olmo-Hybrid-7B           full+linear    hybrid    11/12
    recurrentgemma-9b        local+linear   hybrid    11/12
    Zamba2-7B                full+ssm       hybrid     9/12
    Falcon-H1-7B-Base        full+ssm       hybrid     7/12
    rwkv-4-7b-pile           linear         dense      6/12

The roster itself agrees with its own median on 38 to 40 of 45 lineages per target, so 12/12 is the normal value and 6/12 is chance. **The model with no attention scores the maximum.**

And the two dissenters are the two weakest movers. `rwkv-4-7b-pile` and `Falcon-H1-7B-Base` are also the two lowest `|slope|` in the existence table above. Two instruments, built on different constructs, pick out the same two models, and the property they share is not an architecture, it is how little alignment did to them. That is the confound stated once and then confirmed independently.
