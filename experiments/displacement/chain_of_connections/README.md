---
subject: displacement
question: Is `kill -> scream` a short walk along a chain of connections in the model's own embedding geometry?
kind: question
status: RUN 2026-09-22, EXPLORATORY and unregistered. One model, one prompt.
headline: "**NO, AND THE CONTROL IS WHY.** The question is real -- ` scream` ranks 1,738th of 128,256 tokens by cosine to ` kill`, so the substitute is nowhere near the geometry's nearest word. And a chain IS there, reading beautifully: `kill -> killed -> murdered -> murder -> revenge -> rage -> raging -> roaring -> roar -> scream`. **It means nothing.** The same walk reaches `pension` in 7 hops, `accordion` in 8 and `sofa` in 9 -- all as readable (`organ -> piano -> accordion`), and two of them CLOSER to `kill` than `scream` is. Median distance in the graph is 8 and `scream` sits at 9, longer than typical. In a small-world k-NN graph every pair has a plausible chain, which is exactly why a plausible chain is not evidence. Half the edges are orthographic besides (50 percent of 3-NN pairs share a three-letter prefix)."
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

## 3. A chain is there, and it reads beautifully

Vocabulary is SUBTLEX-US membership (RH), which is a word **list** where `wordfreq` is a frequency **model**: `wordfreq` gives any occurring string a frequency, so BPE fragments clear any floor (`shr` 2.37, `shri` 3.58, `kry` 1.55), while SUBTLEX simply does not contain them. 18,035 of the tokenizer's words survive. It is already in the repo at `lexicons/frequency/subtlex_us.tsv`; nothing was downloaded. BYU/COCA is **not** available and should not be — `fields.py` records that it never existed in the clone and that it is type-level, which is what retired it.

    kill -> killed -> murdered -> murder -> revenge -> rage -> raging -> roaring -> roar -> scream

Nine steps, each a near-neighbour, and it narrates itself: the killing becomes a murder, the murder a revenge, the revenge a rage, the rage a roar, the roar a scream. It is exactly the shape Freud's sentence predicts.

## 4. And it means nothing, which the control shows

The same walk, to words with nothing to do with the prompt:

    pension     7 hops   kill -> killed -> sacrificed -> sacrifices -> trade -> tariff -> tax -> pension
    accordion   8        kill -> killed -> dead -> corpse -> bodies -> organs -> organ -> piano -> accordion
    wallpaper   8        kill -> destroy -> destroyer -> catcher -> pitcher -> jug -> rug -> carpet -> wallpaper
    sofa        9        kill -> killed -> slaughtered -> slaughter -> auction -> sale -> salesman -> chairman -> chair -> sofa
    scream      9

**`pension` and `accordion` are CLOSER to `kill` than `scream` is**, and each chain reads as well as the real one — `organ → piano → accordion` is as good a displacement as `rage → roar → scream`. The median distance from `kill` to anything in this graph is 8; `scream` sits at 9, longer than typical.

**In a small-world k-NN graph every pair has a plausible chain**, because every step is a near-neighbour by construction. That is precisely why a plausible chain is not evidence, and why the control is the only part of this experiment that settles anything.

## 5. Half the edges are spelling

**50 percent of 3-NN pairs over 400 sampled nodes share a three-letter prefix**, and the control paths show it: `catcher → pitcher`, `jug → rug`, `chairman → chair`. Input embeddings carry orthography heavily. The known residue of the SUBTLEX filter is proper names — `cher` survives at 2.47 fpm because Cher appears in subtitles — and a frequency floor that removed it would take `perish` (2.59) and `cherish` (4.45) too, so the floor is zero and the residue is named instead.

## What this licenses, and what it does not

**A path in this graph is a fact about geometry, not a mechanism.** Nothing here shows a model traversing anything — a forward pass does not walk a k-NN graph. The strongest available reading was that a chain of short associative steps exists between the two words, and the control says it does not distinguish them: `scream` is farther than `accordion`.

**The seductive part is the readable path, and it is the part to distrust.** Had this experiment stopped at section 3 it would have produced a genuinely beautiful result — `murder → revenge → rage → roar → scream`, Freud's chain in a language model's own geometry — and it would have been an artefact of k-NN connectivity. The control cost four lines.

**The instrument is the likely fault rather than the idea.** Two better ones, both already in this project: the **unembedding** (`lm_head`), which is what actually decides the output distribution and need not share the input space's orthographic bias; and **`bge-m3`**, a sentence embedder the campaign already uses for passage work, which would give a semantic space with no tokenizer in it. Either could be run over the same prompt and the same endpoints with the producer as written.

Exploratory, unregistered, one model, one prompt. `embed.py` reads a single tensor out of the safetensors shards rather than instantiating a model, so this costs about a gigabyte and eight seconds.
