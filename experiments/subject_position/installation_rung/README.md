---
kind: question
status: MEASURED. 43 nodes, 82 typed forward edges. P1 held, P2 split, P4 unresolved. Measures first-person MASS, not self-reference
headline: The rung at which first-person MASS is installed is SFT, and it is frame-bound
grain: edge
---
# installation_rung

**id:** subject_position/installation_rung **status:** MEASURED. Producers `run.py` (43 nodes, both frames, bare stem), `build_table.py`, `analyse.py`. Predictions in `PREDICTIONS.md` recorded before the run; outcomes in `RESULTS.md`. **There is no `FINDING.md` here** — `RESULTS.md` carries the outcomes against the recorded predictions, and the subject index cites it directly.

> **INSTRUMENT BOUND, added 2026-09-05 from `../framed_identity`.** This measures
> `p(I)` at one position. **It cannot distinguish "I am an AI assistant" from
> "I am Tamas, a cybersecurity expert" — both are ~1.0.** So what is shown to be
> installed at SFT is first-person **mass**, not self-reference and not a subject
> position. The two come apart: coded for KIND, `any I` is nearly flat across the
> arm (85% → 95%) while `ai_system` moves 0.4% → 18.3%. Cite this for **which
> rung moves the mass**; do not cite it for what the "I" refers to.

# THE QUESTION

If a subject position is installed, which training rung installs it?

# THE RESULT

Under the identical `Q:/A:` address (see `../pseudo_template/`), paired over 82 typed forward edges:

    sft        n=35  30 rise  5 fall  median +0.2296  p < 1e-4
    instruct   n=19  17 rise  2 fall  median +0.2662  p = 0.0007
    dpo        n=16  12 rise  4 fall  median +0.0579  p = 0.077
    rlvr       n= 4   3 rise  1 fall  median +0.0177  p = 0.625

DPO's parents start higher (0.711 vs 0.512), but matched inside the DPO parents' IQR, SFT still moves +0.124 (10/12, p=0.039) and DPO does not resolve.

## The categorical finding, which is the one that is not a rate

**11 of 14 bases refuse the chat frame outright.** That refusal is categorical where every other measurement here is continuous. The templateless base does not answer badly; **it has no mechanism for being asked.**

# WHAT IS IN HERE

    run.py             43 nodes, both frames, bare stem -> results/dists.jsonl
    build_table.py     -> results/p_first.csv, 231 rows, three conditions
    analyse.py         results against PREDICTIONS.md
    PREDICTIONS.md     recorded before the run, with two corrections also
                       recorded before any result was read
    RESULTS.md         P1 held, P2 split, P4 unresolved
    P5_PILOT.md        50 base generations: the base mostly does not answer at
                       all -- 66% continue the stem as a document

# WHAT IS NOT ESTABLISHED HERE

**P3** was withdrawn before any result was read: 11 of 14 bases ship no template, so a chat-frame base-to-SFT delta does not exist for most lineages. That is why the primary contrast runs under the pseudo-template address and not under the chat frame.
