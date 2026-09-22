---
subject: displacement
question: Is `kill -> scream` a short walk along a chain of connections in the model's own embedding geometry?
kind: question
status: RUN 2026-09-22, EXPLORATORY and unregistered. One model, one prompt.
headline: "**NO, ON THIS INSTRUMENT.** The question is real -- ` scream` ranks 1,738th of 128,256 tokens by cosine to ` kill`, so the substitute is nowhere near the geometry's nearest word -- but a chain does not explain it. Over the 380 candidate words above theta on the prompt, `kill -> fight -> laugh -> scream` is 3 hops against a MEDIAN of 3. Over 20,809 real words, `kill -> killed -> drown -> drowning -> sinking -> shrinking -> shrink -> shr -> shri -> scream` is 9 hops against a median of 8, i.e. LONGER than typical. **And the graph is about half orthographic**: 48 percent of 3-NN pairs share a three-letter prefix, so `perish -> cherish -> cher -> cheer` is a chain of spellings, not of associations. Input embeddings are the wrong instrument for this question and the next ones to try are the unembedding and a sentence embedder."
---

# Chain of connections

Freud, on repression: the idea acquires its substitute "by displacement [*Verschiebung*] along a chain of connections which is determined in a particular way," while the affect "has not vanished, but has been transformed" (RSE 14:137). If alignment operationalises repression, that sentence should explain why `kill` finds release in `scream`.

This asks whether such a chain is visible in the one place a model keeps its associations as geometry — the embedding matrix.

    python -u run.py                      # real-word vocabulary
    python -u run.py --vocab candidates
    python -u run.py --to cry --k 5

## 1. The falsifier fires the interesting way

If `scream` were simply the nearest thing to `kill` there would be no chain to look for. It is not. In `Llama-3.1-8B`'s input embeddings **` scream` ranks 1,738 of 128,256 by cosine to ` kill`**, and `kill`'s actual neighbours are its own inflections — `kills` 0.471, `killing` 0.398, `killed` 0.372 — then `destroy` 0.206 and `murder` 0.183. The roster's substitute is not the geometry's neighbour, so there is something to explain.

## 2. A connection is not an output

The first version restricted the graph to the prompt's own candidate set, which forces every waypoint to be a word some model would say at that blank. **That is the wrong constraint on a chain** (RH): the words a displacement passes *by* are precisely the ones that never surface. Both vocabularies are kept and `--vocab words` is the default.

    --vocab candidates   380 words above theta in >= 1 of the 100 arms here
    --vocab words        20,809 real English words in the tokenizer (zipf >= 2)

## 3. Chains exist, and they are not short

    vocab        path                                          hops  median
    candidates   kill -> fight -> laugh -> scream                  3       3
    words        kill -> killed -> drown -> drowning -> sinking
                 -> shrinking -> shrink -> shr -> shri -> scream   9       8

**`kill → scream` sits at exactly the typical distance in one graph and one hop worse than typical in the other.** Whatever connects them, it is not unusual proximity in this space at any number of hops.

## 4. And half the graph is spelling

**48 percent of 3-NN pairs over 400 sampled nodes share a three-letter prefix.** The paths show it plainly: `perish → cherish → cher → cheer`, `shrink → shr → shri`, `cherish → cher`. Input embeddings carry orthography heavily, so a walk through them is about half a walk through spellings — and `shr` (zipf 2.37), `shri` (3.58) and `cher` (3.36) all clear the real-word filter, because `wordfreq` assigns frequency to fragments that occur in corpora.

An earlier version with no frequency filter at all was worse still, routing `kill → murder → assass → cruc → kry → cry`.

## What this licenses, and what it does not

**A path in this graph is a fact about geometry, not a mechanism.** Nothing here shows a model traversing anything — a forward pass does not walk a k-NN graph. The strongest available reading was that a chain of short associative steps exists between the two words, and the null says it does not: the steps are neither short nor, half the time, associative.

**The instrument is the likely fault rather than the idea.** Two better ones, both already in this project: the **unembedding** (`lm_head`), which is what actually decides the output distribution and need not share the input space's orthographic bias; and **`bge-m3`**, a sentence embedder the campaign already uses for passage work, which would give a semantic space with no tokenizer in it. Either could be run over the same prompt and the same endpoints with the producer as written.

Exploratory, unregistered, one model, one prompt. `embed.py` reads a single tensor out of the safetensors shards rather than instantiating a model, so this costs about a gigabyte and eight seconds.
