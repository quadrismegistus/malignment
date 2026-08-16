# Registration — DOL, division of labour

**FROZEN 2026-08-16, before `run.py` was written or run.** Append-only: amendments go at the bottom with a date and a reason, and nothing above this line is edited. A pre-registration editable after seeing the result is a post-hoc rationalisation with better typography.

---

## H1 — SFT carries the majority of the displacement

**Predicts:** median `share = js(base→SFT) / js(base→endpoint)` > 0.50 across qualifying chains.

**Supported if** the median exceeds 0.50 with a sign test p < 0.05, unit = the CHAIN.
**Not supported if** the median falls at or below 0.50, or the sign test does not clear.
**This is the weak form and is expected to pass** — a pilot on 26 chains gave median 0.78. It is registered so the *strong* form below has something to be measured against.

## H2 — the ~90% figure does not replicate

**Predicts:** Olmo-3's Instruct chain sits materially below 0.90.

**Supported if** its share is < 0.85.
**Not supported if** it is ≥ 0.85.
**Pre-committed:** a pilot already measured **0.76**. Registering a hypothesis whose answer is known is only honest if the answer is stated here, so it is. What this run adds is whether 0.76 survives the corrected DPO population and the final measurement queue.

## H3 — the division of labour is CONTENT-DEPENDENT

**The claim under test:** *"SFT handles sex, DPO handles violence."*

**Predicts:** `share` computed per domain differs between `sexual` and `violence`, in the direction of **sexual having the HIGHER SFT share**.

**Supported if** the paired difference (share_sexual − share_violence, one row per chain) is positive with p < 0.05 by sign test, n = chains having ≥ 20 live prompts in BOTH domains.
**NOT SUPPORTED if** the difference is null, or negative.

**Declared before looking, because this is the hypothesis most likely to be talked into:**

- The **direction** is fixed here (sexual > violence). A significant difference in the *other* direction is NOT support; it is a different finding and must be reported as a surprise, not as confirmation.
- The **domain mapping is fixed here**: `sexual` means `domain == "sexual"` (n=157) and `violence` means `domain == "violence"` (n=552). **`taboo` (n=240) is NOT merged into `sexual`** even though it may cover related content. Merging it after seeing the result would be the specification search this registration exists to prevent. If the mapping is wrong, that is an amendment with a date, made before the numbers are looked at again.
- **n is small.** `sexual` has 157 live prompts across the whole corpus, and a chain needs ≥20 of them. If fewer than 5 chains qualify, H3 is **UNDERPOWERED AND WILL BE REPORTED AS SUCH**, not run at whatever n survives and quoted.

## What would make all three uninterpretable

- Any chain whose SFT or preference rung is not separately released — excluded by construction, and the exclusion is the selection effect named in the README.
- A `share` > 1.0 is a real reversal (the endpoint is closer to base than the SFT rung). These are **kept, not winsorised**, and reported separately; the pilot found 2 of 26.
- The population is **biased low**: lineages with a released preference stage carry lower base→endpoint JS than those without (0.1361 vs 0.1545). Every claim here is about the open-science subpopulation and says so.

## Unit and denominator

- **Unit = the CHAIN** (base → sft → preference), not the lineage and not the family. A base with two chains contributes two rows.
- Chains sharing a base are **not independent**; the count of distinct bases is reported alongside n, and if any base contributes more than two chains a cluster-robust check is reported too.
- pythia-2.8b's four archangel arms are **one chain, not four**: `archangel-dpo` is the declared representative, per `models.yaml`. Counting all four would quadruple one base's weight over a JS span of 0.0071–0.0081.

## Stopping rule

**One run, after the measurement queue drains.** Not re-run until it clears, and not re-run afterwards with a different domain mapping unless an amendment says so first.

---

## Amendments

*(none)*
