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

## 6. A semantic space does not rescue it (`--space glove`)

The orthography result suggested the instrument was at fault, so the same battery was run over **GloVe 300d** — `glove-wiki-gigaword-300`, already on this machine and already read by `named_under_dose/embed.py`. Same word list, 18,007 of the 18,035 have a vector. GloVe is fitted on co-occurrence and has no tokenizer in it.

    space    orthography   kill -> scream   median   pension  accordion  sofa
    llama        50%            9 hops         8        7         8        9
    glove        28%            7 hops         7        6         8        8

**Orthography nearly halves, and nothing else moves.** `scream` sits at exactly the median distance, and `pension` is *still* closer to `kill` than `scream` is. The control survives the change of space, which is what makes it a control.

The GloVe path is worth quoting for what it reveals:

    kill -> killed -> wounded -> critically -> acclaimed -> masterpiece -> munch -> scream

**`munch → scream` is Edvard Munch's painting.** GloVe reaches `scream` through art criticism, because in a co-occurrence corpus that is where the word lives. A chain can be semantic, legible and about the wrong sense entirely.

`bge-m3` in context — embedding `"She was so angry she wanted to {word}"` and taking the word's own vectors — is the remaining instrument and would fix exactly that: it is the only one of the three in which `scream` has this prompt's sense rather than its corpus-wide one. It needs a declared candidate list (one forward pass per word), which is the cost the other two do not have.

## 7. The remaining instrument, run: `bge-m3` in context, and it says the same thing

Section 6 named `bge-m3` as the one space in which `scream` would carry *this prompt's* sense rather than its corpus-wide one, and the one that would not reach it through Edvard Munch. It was run. `embed.bge_in_context` encodes `"She was so angry she wanted to {word}"` for each candidate and takes the mean of the word's own token span, using `score._bge()` so this is the same encoder the campaign's passage work uses.

Two things had to be fixed before it could be read, and both are findings about the instrument.

**Centring.** Every vector is the same eight-token frame with one word changed, so the frame dominates: raw cosines run 0.70–0.97 for *everything*, with `accordion` at 0.715 against `scream` at 0.781. Subtracting the candidate mean leaves what the word contributes, and it moves `scream` from rank 230 to 409 of 466 — the difference between "mid-pack" and "one of the least similar words in the set". An uncentred contextual encoder measures the prompt.

**A dictionary, not a frequency floor** — see `lexicon.__doc__`. The candidate set is the above-theta completions, so it contains the word-boundary rule's fragments, and the first bge path ran `kill → shoot → sho → shou → scream`: a chain through two spellings of the word it starts from. `--min-fpm 1.0` does not fix this. It takes `sho` (0.961) but also takes `strangle`, `weep`, `shriek`, `gouge`, `pummel`, `wail`, `thrash` and `smite` — rare real verbs and common fragments occupy the same frequency band. Requiring a **WordNet** entry removes 31 of 372: 22 fragments and 9 closed-class words, and no content word at all.

On the 350 surviving candidates:

    THE FALSIFIER  scream ranks 302 of 350 by cosine to kill
    PATH           kill -> die -> suffocate -> choke -> shriek -> scream   5 hops
    MEDIAN         5
    CONTROL        eat 3,  write 4,  sit 5,  sleep 5,  read 5,  dance 6
    ORTHOGRAPHY    3%

**This is the best chain the experiment has produced and it changes nothing.** `die → suffocate → choke → shriek` is not art criticism and not spelling — it is the right sense of every word, in the right register, and it is exactly the shape section 3's beautiful path had. It is also exactly the median distance, and `eat` is two hops closer.

The llama space under the same filter is starker still:

    PATH           kill -> fight -> laugh -> scream   3 hops   (median 3)
    CONTROL        dance 2,  sit 3,  write 3,  eat 3,  sleep 4,  read 4
    ORTHOGRAPHY    2%

**`dance` is nearer to `kill` than `scream` is.**

So the instrument was not the fault. Three spaces — a decoder's input embedding, a co-occurrence space, and a sentence encoder reading the actual prompt — disagree about orthography (50% / 28% / 3%), about hop counts (9 / 7 / 5), and about which words are adjacent, and agree on the only thing being tested: **`scream` sits at the median distance from `kill`, and words with no relation to the prompt sit nearer.** The section 6 hypothesis that a semantic space would rescue the result is refuted, on the space that was nominated to do it.

The chain of connections is real and it is not a path to `scream`. Whatever selects `scream` out of `kill`'s neighbourhood is not neighbourhood structure, and this producer cannot see it.

    python run.py --vocab candidates --space bge      # the run of record here
    python run.py --vocab candidates --space bge --no-wordnet   # restores the fragment path
