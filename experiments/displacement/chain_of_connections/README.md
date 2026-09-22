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

## 8. CORRECTION to section 7: the space was right and the GRAPH was the instrument at fault

Section 7 concluded "the instrument was not the fault" because three spaces agreed. RH asked what could possibly put `dance` nearer to `kill` than `scream`, and the answer is that **nothing did** — that was the llama space, and in the llama space nothing is near anything. Looking at the cosines directly, rather than at hop counts derived from them, reverses the reading.

**The llama input embedding is an anisotropic cone at this resolution.** Over the 316 candidates, cosine to `kill` runs 0.006 to 0.206, median 0.088, sd 0.036 — the whole vocabulary inside a fifth of the available range:

    kill's nearest:  destroy .206  murder .183  fight .181  attack .181  hit .173
                     burn .173  cut .169  shoot .168  SELL .168  catch .165  EAT .164
    scream  .082 (rank 180)      dance .091 (rank 153)      stab .079 (rank 191)

`sell` outranks `stab`. `eat` is 11th. The gap that put `dance` above `scream` is **0.009 in a space whose sd is 0.036** — a quarter of a standard deviation, i.e. noise. Over the full 128k vocabulary `kill`'s true neighbours are `kills`, `Kill`, `killing`, `killed`: this embedding encodes morphology, and past the inflections of the query word it has nothing left to say.

**bge is not bad. bge is right, and section 7 misread it.**

    NEAREST kill   KILL .92  murder .86  slaughter .79  die .62  lynch .41
                   shoot .40  stab .37  bury .34  punish .33  strangle .28  hurt .27
    FARTHEST kill  roll -.23  roar -.21  vent -.20  shake -.20  whoop -.20  splash -.20
                   burst -.19  swing -.18  pop -.18  wake -.18
    scream -.124 (302 of 350)   shout -.122 (300)   shriek -.099 (278)   cry -.077 (256)

That is a clean semantic ordering with an interpretable axis at both ends, and the far pole is a coherent cluster: **sudden noisy discharge** — roar, whoop, vent, burst, splash, and with them `scream`, `shout`, `shriek`, `cry`.

**So bge independently reconstructs the pole axis this project declared by hand.** The axis borrowed from `nn_shewantedto_scream-kill` for the `dN` measurement is naughty = kill/strangle/die/murder/shoot/cut/stab, nice = scream/cry/yell/shout. Shown nothing but this prompt and its own candidates, bge orders them the same way, with `slaughter` and `lynch` at one end and `roar` and `whoop` at the other.

### AND THAT LAST CLAIM DEPENDS ON THE CENTRING, WHICH IS A CHOICE

`cosines.py --raw` prints both, and they do not agree about `scream`:

    scream    RAW  0.781  rank 156 of 350      CENTRED  -0.124  rank 302 of 350
    dance     RAW  0.709  rank 343             CENTRED  -0.136  rank 315
    eat       RAW  0.814  rank  59             CENTRED  +0.137  rank  40
    murder    RAW  0.968  rank   2             CENTRED  +0.862  rank   2

Raw, `scream` is **mid-pack, not at the far pole**, and the far pole is a less coherent set (open, shake, Options, rock, laugh, dance, roll, sleep, wake). The clean vocalisation cluster at the bottom is a property of the centred space.

Centring is still the right instrument here -- raw cosines run 0.69-0.98 with sd 0.038, so raw similarity is overwhelmingly the shared eight-token frame -- but centred cosine is similarity of the **deviation from the typical candidate**, which is a different quantity and not a cleaned-up version of the same one. So:

- **Robust across both:** the violence cluster is nearest (murder, die, stab, strangle, shoot, hurt); `eat` is nearer to `kill` than `scream` is (+0.84 sd raw, +1.84 sd centred); and `dance` is FARTHER than `scream` in bge under both (-1.89 sd raw, -0.09 centred), so the `dance` result really is llama-only.
- **Centring-dependent:** that `scream` sits near the far pole, and that the far pole is the vocalisation cluster. Quote those as facts about deviation from the frame, or not at all.

**What survives without the choice is the weaker but sufficient claim: `kill -> scream` is not a short hop.** Under either reading `scream` is outside `kill`'s neighbourhood while a dozen violence verbs are inside it.

### What the hop graph did to this

The k-NN graph is k=4 and undirected over 350 nodes, so its diameter is 7 and **124 of the 350 words — 35% of the vocabulary — sit at exactly 5 hops.** Hop count discards magnitude:

    cos(kill, eat)     +0.137   ->  3 hops
    cos(kill, scream)  -0.124   ->  5 hops

A difference of 0.26 in a space with sd 0.14 is compressed into two steps of a counter. **The control did not refute the chain; it refuted the graph**, which is why it "survived" being carried from llama to GloVe to bge — an uninformative metric is robust to changing what it is computed on.

Producer for every number in this section: `cosines.py` (`--raw` for the comparison above).

Sections 4 and 5 stand as written: the path that reads beautifully is a k-NN artefact, and quoting one was the danger. What does not stand is section 7's "the instrument was not the fault". The instrument was the hop count. The space underneath it was measuring the right thing the whole time.

### And the idea the experiment was built on does not survive either, for a better reason

The premise was that `scream` would be reachable from `kill` by a chain of short associative steps. The measurement says `scream` is one of the *least* similar words to `kill` in the candidate set. Nothing in these spaces makes them neighbours, because **they are not similar words** — they are two things an angry person wants to do. The relation is the shared frame, not shared meaning: syntagmatic, not paradigmatic.

Which is the distinction this project already has an instrument for. A similarity space is the wrong place to look for Freud's chain of connections, and the right reading of this folder is not "the chain is not short" but "the chain is not a similarity relation at all".

## 9. The k sweep: still one component at k>=2, and k=4 was the wrong setting rather than merely a coarse one

RH asked whether the graph is still a single component at k=2 or 3, and whether `scream` is still reachable. Producer: `connectivity.py`.

**Yes to both, at every k>=2, in both spaces** — 350 of 350 reachable, one component. The graph only fragments at k=1, and that is where the neighbourhood question is answered outright:

    bge   k=1   85 components, kill's has 10:
                KILL, bury, die, hang, kill, lynch, murder, slaughter, smother, strangle
    llama k=1   56 components, kill's has 13:
                burn, destroy, die, divorce, drown, kill, marry, melt, murder,
                punish, rape, shoot, slaughter

`scream`, `shout`, `cry` and `shriek` are outside `kill`'s component in both — and so are `eat`, `dance`, `sit` and `write`, so this is not a control beating it: at the sparsest setting **nothing but killing is in `kill`'s neighbourhood.** bge's ten are a clean homicide cluster down to the method verbs (`hang`, `smother`, `strangle`, `lynch`) and the disposal (`bury`). llama's thirteen contain **`marry` and `divorce`**, which is the anisotropic cone of section 8 showing up as membership instead of as a number.

### Lowering k restores what the hop count is for

    k        hop distances in bge, kill -> ...
    2        murder 1, die 1, stab 2, strangle 2, shoot 2, eat 4, cry 8, hurt 9,
             dance 10, write 10, sit 11, SCREAM 12, shout 13, shriek 13
    4        murder 1, die 1, stab 1, strangle 2, shoot 1, eat 3, cry 5, hurt 6,
             dance 6, write 4, sit 5, SCREAM 5, shout 6, shriek 4

At k=2 the distribution runs 1 to 17 hops with a median of 9, and `scream` sits at 12 — **only 31 of the 350 words are farther.** At k=4 the same graph gives a median of 5 with `scream` at 5 and 35% of the vocabulary tied with it. The counter had not lost resolution by accident; k=4 glues the space into a ball in which every question has the same answer.

**So section 7's "the path is not short, it is the typical distance" was an artefact of k.** `scream` is not at the typical distance. It is in the far tail, which is what the cosine ranking (302 of 350) and the k=1 membership both said independently. Three instruments agree once the fourth stops compressing them.

### And the k=2 path is the chain the experiment was looking for

    kill -> murder -> stab -> bite -> chew -> choke -> vomit -> vent
         -> rant -> rage -> roar -> yell -> scream

Twelve steps from homicide to a scream, and the route is **through the mouth**: biting and chewing, then choking and vomiting, then venting, ranting, raging, roaring. An oral-aggression chain, arrived at by an encoder that was shown one prompt and a list of its own candidate continuations.

Sections 4 and 5 still apply and are the reason this is reported rather than quoted: **a legible path in a k-NN graph is the thing to distrust**, and this one is legible enough to be dangerous. What is load-bearing here is not the path but the three agreeing distance measurements, and what they say is that `kill -> scream` is a long move, not a short one.

That does not restore the original premise, it inverts it. The experiment asked whether `scream` is reachable from `kill` by a chain of short associative steps. It is reachable, and the chain is one of the longest in the candidate set.

    python connectivity.py                       # the sweep, both spaces
    python run.py --vocab candidates --space bge --k 2   # the path above

## 10. Pathways to the words the lineages actually chose — and a WITHDRAWAL of section 9's far-tail claim

RH's proposal: stop nominating `scream` in advance. Take the destinations from the measurement — on this prompt, at lineage grain, `kill`'s base arm goes to `scream` in 15 lineages, `cry` in 2, `hurt`/`punch`/`fight`/`destroy` in 1 each, and stays at `kill` in 7 — and draw the routes to all of them at once. Producer: `pathways.py`.

His own objection, and the answer: **a shared node is not an ambiguity.** The union of shortest paths from one source is a tree, so every node has exactly one parent on its route back to `kill`; two destinations meeting at a node means they genuinely share a prefix. Node weight is then the lineage mass flowing through it. The real ambiguity is ties between equal-length paths, which plain BFS resolves by vocabulary order — so the rule here is declared instead: **fewest hops, then greatest summed cosine, then alphabetical**, i.e. the strongest of the shortest.

### First it exposed two defects in the vocabulary

The first run routed `punch` through `bite -> BITE -> smite` and `destroy` through `gouge -> g -> p -> d -> dis`.

- **Case was making duplicate nodes.** 8 of the 9 non-lowercase candidates have a lowercase twin (`KILL`, `BITE`, `SCREAM`, `Scream`...), so a hop between two spellings of one word counted as a step.
- **Single letters pass every filter this folder had.** `g`, `p` and `d` are in SUBTLEX *and* have WordNet entries — gram, phosphorus, vitamin D. Neither the word list nor the dictionary removes them. Length does, and length is the only property that actually separates them: of the 39 candidates under three letters, **19 are single letters and 20 are two-letter fragments** (`cl`, `cr`, `fl`, `sl`, `sm`, `sn`, `sw`, `th`, `re`, `po`...) against exactly four real words, `be`, `do`, `go`, `up`, which are now a declared exception list.

Both fixes live in one new `run.candidate_words`, because `run.main` and `cosines.space` each had their own copy of the filter and had already drifted. Candidates: **466 -> 307** (116 not words, 39 too short, 8 folded). Residue named: `dis` and `las` are three-letter proper nouns and survive.

### AND THAT CHANGED THE ANSWER. Section 9's far-tail claim is WITHDRAWN.

Section 9 said `scream` sits at 12 hops against a median of 9 with only 31 of 350 words farther. On the cleaned vocabulary:

    k=2, bge      BEFORE (350 words)          AFTER (307 words)
    scream        12 hops, median 9           9 hops, median 9
    farther than  31 of 350                   125 of 307

**`scream` is at the median again, and the 12 hops were partly the debris padding the route.** The claim that it sits in the far tail was an artefact of the same fragments this section removed, and I reported it as a three-instrument agreement when one of the three was reading contaminated vocabulary.

### What actually survives, and it is a weaker and more honest claim

    cosine        scream -0.118, rank 262 of 307 -- the bottom 15%
    k=1 component kill's is NINE words: bury, die, hang, kill, lynch, murder,
                  slaughter, smother, strangle. scream, shout, cry, shriek are
                  out; so are eat, dance, sit, write
    k=2 hops      scream 9 = median. shout 10, dance 10, write 10, sit 11 are
                  FARTHER. eat 4, stab 2, strangle 2, shoot 2, murder 1, die 1

Cosine and hop count **disagree about `scream`** and the disagreement is not noise: cosine puts it in the bottom 15%, hops put it mid-pack. Both are right about different things. `kill`'s neighbourhood is very small and entirely homicidal — nine words at k=1, about ten above +0.27 by cosine — and everything else in the lexicon sits outside it at roughly comparable remove. So:

**`scream` is not specially far from `kill`. It is ORDINARILY far, and the notable fact is how near `eat` is** (+0.138, rank 39, 4 hops at k=2 against `scream`'s 9). The median hop distance is 9 because most of the vocabulary is far; being outside `kill`'s neighbourhood is not distinctive, because almost everything is.

That still refutes the premise the experiment was built on — there is no short associative chain from `kill` to `scream` — but it does so by showing the chain is *unremarkable*, not by showing it is *long*. The earlier reading made the negative result more interesting than it is.

### The plate

`pathways_kill_argmax_bge_k2.png`. All six destinations leave `kill` by the same three steps, and the branch point is `bite`:

    kill -> murder -> stab -> bite            21 of the 21 lineages that moved
      bite -> chew                            19
        chew -> laugh -> sing -> weep -> shriek -> scream   15
        chew -> laugh -> sing -> weep -> cry                 2
        chew -> chuck -> shove -> push -> pinch -> punch      1
        chew -> choke -> vomit -> dump -> dis -> destroy      1
      bite -> lick -> skin -> scar -> scare -> harm -> hurt   1
                                          harm -> injure -> attack -> fight  1

The mouth survives the cleaning and is now the whole structure rather than one path's flavour: every route out of `kill` goes through `bite`, and 19 of 21 continue through `chew` before anything else happens. From there the heavy branch is oral-to-vocal — `laugh`, `sing`, `weep`, `shriek`, `scream`.

**Read it as adjacency, not as travel.** Sections 4, 5 and 9 are the standing warning and this plate is made entirely of the thing they warn about; a forward pass does not walk a graph. What the plate shows is that the words alignment moves to are reached from `kill` through a narrow shared gate, and what it cannot show is any model doing so.

    python pathways.py                          # the plate above
    python pathways.py --basis faller           # 10 destinations instead of 6
    python pathways.py --min-lineages 2         # scream and cry only
