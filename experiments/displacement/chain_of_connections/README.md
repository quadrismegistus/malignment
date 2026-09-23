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

## 11. Two questions from the paper seat: one nuance, one refuted test

### Q1. Are the substitutes uniformly far from `kill`? NO -- THEY ARE BIMODAL

Section 10 said `scream` is "ordinarily far". Asked whether that holds for the other destinations, it does not, and the structure is more useful than the uniformity would have been. Cosine rank among the 307 candidates, `kill`'s own destinations at lineage grain:

    basis=argmax                        basis=faller
    hurt      1   +0.270  rank  10      hurt    3   rank  10
    destroy   1   +0.184  rank  27      hit     3   rank  19
    fight     1   +0.139  rank  38      destroy 1   rank  27
    punch     1   +0.086  rank  55      fight   1   rank  38
    ---------------------------------   punch   3   rank  55
    cry       2   -0.078  rank 225      slap    1   rank  77
    scream   15   -0.118  rank 262      rip     1   rank  78
                                        smash   1   rank 128
    control: eat +0.138 rank 39         cry     1   rank 225
                                        scream 18   rank 262

**The substitutes split on whether the substitution stays in the semantic field.** `hurt`, `hit`, `destroy`, `fight`, `punch` are INSIDE `kill`'s neighbourhood -- several of them nearer than the `eat` control. `scream` and `cry` are outside it. So there are two kinds of move here and cosine separates them cleanly.

Weighted by lineages the mass is on the far side and almost all of it is one word: **17 of 21 (argmax) and 22 of 33 (faller) take the far route, carried by `scream`.** So the displacement is predominantly but not exclusively a move out of the field, and which route a given lineage took is readable per lineage rather than assumed.

### Q2. Can contiguity be measured directly, as co-completion? THE TEST IS RIGHT AND IT FAILS

The proposal: sections 8-10 infer contiguity from the FAILURE of a similarity measure, which is weak -- a null on one axis is not a positive result on the other. If `kill` and `scream` are frame-mates they should co-occur as completions of the same prompts across the corpus even while far apart in the embedding. Producer: `cocompletion.py`, PMI over the 4,600 prompts, with the word's own rate divided out.

**It does not hold.** Three specifications, declared in advance and all reported:

    CO-COMPLETION RANK of 305          scream    eat     dance   sit   write   axes
    prompt unit, all arms                 166     36       230   131     138   +0.310
    prompt unit, base arms                187     38       202   122     119   +0.315
    cell unit, all arms                   105     46       146   117     213   +0.360
    ------------------------------------------------------------------------------
    COSINE RANK of 307, for reference     262     39       280   192     120

**The `eat` control sits in the same place on both axes** -- cosine 39, co-completion 36 / 38 / 46 -- and so does `dance` at the other end (cosine 280, co-completion 230 / 202 / 146). A control that lands in the same position under both instruments is the clearest statement that they are one instrument: `eat` is near `kill` whether you ask what it means or what it co-occurs with, and `scream` is not near under either.

`scream` is mid-pack on co-completion in every one -- better than its cosine rank of 262, never near. And `kill`'s top co-completion partners are the same vocabulary as its top cosine neighbours: vandalize, injure, gouge, lunge, avenge, lynch, strangle, retaliate, rape, throttle, bury, suffocate.

**The two axes are positively correlated, +0.31 to +0.36, not orthogonal.** For verbs competing for one slot, words that mean similar things also complete the same frames, so co-completion is not an independent axis here and cannot carry a contiguity claim that similarity has already declined to support.

So the honest position is narrower than section 10's closing paragraph implied: **we have a similarity null and no positive contiguity result.** The metonymic reading remains a plausible interpretation of the null and is not a measured finding, and should not be written as one. What IS measured is Q1's bimodality.

The remaining option, and its hazard: restrict co-completion to the anger-frame family rather than all 4,600 prompts. That would test the claim where it is actually made -- but the frame family is the one the effect was found in, so a positive there is close to circular and would need a declared frame list and a matched control family before it meant anything.

    python cocompletion.py                 # prompt unit, all arms
    python cocompletion.py --arms base     # base arms only
    python cocompletion.py --unit cell     # same model and prompt

## 12. The model's own spaces, and the plate that should have been made first

Sections 7–11 were all run in **foreign** spaces — bge-m3, GloVe, and llama's input embedding read as a static table. RH asked for the plate in llama's own geometry instead, and then for the space that actually results from the prompt. That turned out to be the best instrument in the folder, and getting there cost two corrections.

### There are four llama spaces and they are not one space

    --space llama              input embedding rows (type level)
    --space llama_unembed      lm_head rows: what the candidates COMPETE with
    --space llama_resid23      residual at the word's own position, 2/3 depth
    --space llama_resid_mean   the same, averaged over all layers

The residual spaces are read from `own_geometry/results/geometry_tulu.npz`, whose **base stage is this exact model**, so they cost a file read rather than four checkpoint loads. `--stage {base,sft,dpo,rlvr}` selects the rung.

### THE RESIDUAL BEATS BOTH WEIGHT MATRICES ON EVERY CRITERION

Against `kill`, over the same 307 candidates:

    space         nearest kill                              max     sd    1st   2-pref
    input         destroy murder attack fight SELL eat    0.123  0.028   23%      8%
    unembed       murder destroy slaughter SELL shoot     0.229  0.035   28%     15%
    resid_23      murder slaughter hurt harm destroy      0.751  0.140   23%      8%
    resid_mean    murder hurt attack harm punish          0.750  0.160   22%      7%
                                            chance:                       9%    1.2%

Five times the dynamic range — **the cone that made every llama k-NN walk wander is a property of the two weight matrices, not of the model** — and a neighbour list that is clean violence ten deep: murder, hurt, attack, harm, punish, destroy, slaughter, stab, throttle, rape.

**RH's orthography reading is right, and the unembedding is where it bites.** At 15% two-letter agreement against a 1.2% baseline it runs at 12.5x chance, twice the rate of every other space here. §5's "llama 50%" was never comparable to this: it was measured on the unfiltered 18,035-word list and is a fact about a vocabulary.

### And it fixes the `eat` anomaly that had been steering this folder

    word      input  unembed  resid_23  resid_mean
    hurt         29       80         2          1
    destroy       0        1         4          5
    fight         3       12        17         13
    hit           6      105        15         14
    punch       211      135        33         31
    ---------------------------------------------- the gap
    cry         174      160       112        139
    scream      175      156       161        200
    eat           7        5        48          54

`eat` is **5th in the unembedding — ahead of every word `kill` actually moves to** — and 54th in the residual, behind all five in-field destinations. Sections 8 and 10 leaned on "an unrelated control is nearer than the substitutes"; that was substantially an artefact of reading type-level spaces. §11's bimodality survives and sharpens: the in-field destinations now occupy ranks 1–31 and the out-of-field ones 139–200, with nothing between.

The two residual depths agree (+0.962) and both disagree with the weight matrices (unembed vs resid_mean +0.434), so this is **contextual versus type-level, not a choice of layer**.

### The plate

`pathways_kill_faller_llama_resid_mean_k2.png`, base stage, k=2:

    kill -> attack -> fight -> argue -> talk -> speak -> say -> yell -> scream   18
    kill -> hurt                                                                  3
    kill -> shoot -> stab -> slap -> smack -> hit                                 3
    kill -> shoot -> stab -> slug -> punch                                        3
    kill -> hurt -> punish -> ruin -> destroy -> crush -> smash
    kill -> attack -> confront -> chase -> catch -> grab -> snatch -> rip

Physical violence → verbal conflict → speech → vocalisation. **Two-letter spelling agreement on the drawn edges: 0%.**

**The base stage is the one of record (RH).** A chain of connections is a property of the material before the defence operates on it; drawing it at DPO would draw the censor's associations rather than the drive's. The aligned-stage plates are kept as the comparison that produced §12.3's negative, not as alternatives.

### The same chain on all three bases

    basis      base-kill lineages  keep kill  destinations  scream  1st   2-pref
    argmax            28               7           6          15    18%     0%
    faller            33               0          10          18    25%     0%
    crossing          21               0           8          12    27%     0%

**The route to `scream` is the identical eight hops on all three.** The basis chooses which endpoints are drawn and how heavy each is; it does not touch the graph. So the chain is a property of the space rather than of the selection rule, and a reader who distrusts one basis can be shown another without the picture changing. `crossing` is the strict plate — only lineages where the riser genuinely overtook `kill` — and `scream` still carries 12 of its 21, more than every other destination combined.

Edge labels are **centred cosine similarity**, not distance: higher is nearer, and the candidate-set mean is subtracted before normalising, so they measure similarity of each word's deviation from the typical candidate. They are not comparable across spaces — the residual's 0.75 and the unembedding's 0.23 for `murder` are the same relationship at different dynamic range. Node labels are lineage counts, which is a different quantity on the same plate.

## 12.1 CORRECTION: the two-letter chance baseline was wrong

Chance on this vocabulary is **9% for a shared first letter and 1.2% for a shared two-letter prefix** — an order of magnitude apart. The orthography reporter computed the first-letter baseline once and printed it beside both columns, and I read "two-letter 7% against chance 9%" as *below chance* and reported it that way. It is nearly 6x chance. Every space in this folder is well above chance on both measures; the ordering between them is what survives, and it widens.

## 12.2 CORRECTION: every llama plate before ba1f8579 was fictional

`cosines.space` returns `W` indexed by **token id** for the llama spaces — it hands back the whole 128k embedding matrix — and by **position** for bge, which builds one row per candidate. `pathways.py` built its own position index and passed it to the row-gathering step. For bge the two are identical and **every bge result in this README stands, verified byte-identical after the fix**. For llama it read arbitrary rows.

It never errored. It produced clean, plausible, fully-formed plates, one of which was shown to RH and read as a finding — that `kill`'s k=2 component was `{kil, kill, le}`, its own subword fragment and nothing else. That component does not exist. Corrected, drawn-edge first-letter agreement is 23–29% for llama's spaces against bge's 44%; the buggy plates reported 48% and 53%.

Then the fix commit staged the pre-fix PNGs by glob **without regenerating them**, in the same commit whose message explained they were fictional. Both corrected; all plates regenerated; every plate now prints its own orthography with both baselines and lists its same-letter edges, so this does not go back to being judged by eye.

## 12.3 Alignment does not move the orthography

The SFT and DPO residuals route to `scream` through `scare -> scar -> scorch -> scold`, an `sc-` run, where base goes `attack -> fight -> argue -> talk -> speak -> say -> yell`. That looks like the censor pulling the geometry toward spelling. It is not:

    space         base   sft   dpo  rlvr      (1st letter / 2-prefix, whole space)
    resid_mean    22/7  23/8  23/8  23/8
    resid_23      23/8  24/9  22/9  22/9
    unembed      28/15 28/15 28/15 28/15
    input         23/8  24/9  24/9  24/9

Nothing moves. ~30 drawn edges is not a distribution, and the aggregate over 921 neighbour pairs refuses the reading. This is the same failure mode §10 records: the shown case is not the distribution.

## 12.4 A dictionary-legal word can still do fragment work

RH spotted it in the real-words-only unembedding plate: `burn -> bur -> bury` and `bur -> burst`. `bur` is a WordNet entry — a seed case — so the dictionary filter, the length floor and the case fold all pass it, and it is acting as a hub between three spellings of one stem.

A global frequency floor cannot remove it (§7: it takes `strangle` and `weep` first). Comparing a word to **its own extension** can. 14 of the 307 are a strict prefix of another candidate:

    bur  0.12 vs burn 55.22  460x     craw 0.33 vs crawl     36x
    cur  0.61 vs curl  18.22  30x     pun  1.84 vs punch     16x
    dis  1.51 vs disappear    14x
    ------------------------- 10x cut -----------------------------
    scar 8.47 vs scare   4x           era  5.71 vs erase    1.1x
    pin, las, tear, who, go, be: MORE frequent than their extension

`--prefix-ratio 10` removes exactly `bur`, `craw`, `cur`, `pun`, `dis` and keeps `scar`, which this corpus uses. In the unembedding it drops two-letter agreement on drawn edges from 16% to 7% — so essentially all the sub-word chaining in that space rode on those five.

**OFF BY DEFAULT.** The 307-word set is the population `own_geometry` and `cocompletion` were run on, and a filter that silently changed it would break every cross-folder number in both folders. `--raw` (no filter at all, subwords allowed) and `--prefix-ratio` both REFUSE on the residual spaces rather than quietly returning the filtered set, because the saved residual was computed over the 307 and changing the vocabulary means recomputing it.

    python pathways.py --space llama_resid_mean --k 2 --basis crossing   # the strict plate
    python pathways.py --space llama_resid_mean --k 2 --stage dpo        # after alignment
    python pathways.py --space llama_unembed --k 2 --raw                 # subwords allowed
    python cosines.py --space llama_resid_mean                           # the ordering, no graph

## 12.5 The two graph-parameter checks, asked by the paper seat before citing the plate

§§4 and 9 taught that the objection to any k-NN plate is the graph parameter, not the selection rule. The identical route on all three bases (§12) answers the selection-rule objection. These two answer the other one, and **one of them goes against the plate.**

### Check 1: is eight hops remote, or is eight hops just what this graph is?

Shortest-path length from `kill` to every one of the 307 candidates, base-stage `resid_mean`:

    k    reachable   median   scream   farther than scream   percentile
    2      307/307      6        8          49 of 307           84th
    3      307/307      5        5          91 of 307           70th
    4      307/307      4        5          13 of 307           96th

**At k=2, `eat` sits at exactly the same eight hops as `scream`.** The controls land at 7 (`sit`, `write`), 8 (`eat`), 9 (`cry`, `dance`). So the distribution is unimodal around the median and `scream` is at the 84th percentile — above typical, **not remote**, and not separated from an unrelated control.

**So the chain's LENGTH says nothing about `scream`, and no claim may rest on it.** What separates `scream` from `eat` is cosine rank — 200 against 54 — which is a property of the space and does not involve the graph at all. This is §9's lesson arriving again in the good space: the hop counter compresses, and it compresses `eat` and `scream` onto the same number while the underlying cosines are 1.5 sd apart.

### Check 2: does the route survive a change of k?

    k=2   kill -> attack -> fight -> argue -> talk -> speak -> say -> yell -> scream
    k=3   kill -> hurt -> punish -> curse -> swear -> scream
    k=4   kill -> fight -> argue -> rant -> shout -> scream

**The shape is stable and the waypoints are not.** All three run physical violence → verbal aggression → vocalisation; k=2 and k=4 go through argument and shouting, k=3 through punishment and profanity. Two-letter orthography is 0% at every k. So "the route leaves violence through language" is robust to k; "the route passes through `talk` and `speak`" is not, and no individual waypoint should be quoted.

And the split **in hops** does not survive:

            in-field destinations   scream   cry
    k=2            1 - 5              8       9
    k=3            1 - 5              5       6
    k=4            1 - 5              5       5

Clean at k=2, gone by k=3, where `scream` at 5 sits among `rip` 5, `destroy` 4 and `smash` 4.

**But the in-field/out-of-field split is a COSINE fact and is k-independent by construction** — ranks 1–31 against 139–200 do not involve the graph. §11's bimodality is therefore untouched by either check; it is the hop-distance restatement of it that fails.

### What the plate may be cited for, after both checks

- **Yes:** which words lie between `kill` and its destinations, and that every route out leaves physical violence through language rather than through spelling (0% two-letter agreement at every k and on every basis).
- **Yes:** the in-field/out-of-field split of the destinations, **quoted as cosine rank**, which no graph parameter touches.
- **NO:** that `scream` is far from `kill` because the path is long. Eight hops is the 84th percentile and `eat` is also at eight.
- **NO:** any particular waypoint. `talk`, `speak` and `say` are k=2 artefacts; `curse` and `swear` are k=3's.
- **Still no:** anything traversal-shaped. A forward pass does not walk this graph.

## 12.6 Edges by cosine cutoff, not k nearest — and length says something after all

RH's question after §12.5: would length mean anything if edges were drawn by a cosine cutoff instead of by nearest neighbours? **Yes, and it reverses the check that went against the plate.** Producer: `threshold.py`.

A k-NN graph gives every node degree ≥ k, so an edge means "relatively nearest", not "actually similar", and in a sparse region it manufactures edges between things that are not close. That is exactly why `eat` and `scream` landed on the same eight hops. Under a cutoff an edge means the similarity cleared a bar, so sparse regions genuinely disconnect.

### The threshold-free form: the bottleneck

Choosing a cutoff is choosing an answer, so report the quantity that needs none. The **bottleneck** from `kill` to a word is `max over paths of (min cosine along the path)` — the highest cutoff at which the two are still connected, i.e. the weakest link on the best route. It is the minimum edge on the maximum-spanning-tree path, and one Kruskal plus one BFS answers it for all 307.

    word       direct   bottleneck   hops   kind
    hurt        0.516      0.516       1    destination
    cry        -0.010      0.469      15    destination
    scream     -0.078      0.469      16    destination
    hit         0.332      0.469       2    destination
    destroy     0.413      0.469       9    destination
    slap        0.220      0.469       5    destination
    punch       0.221      0.469       3    destination
    smash       0.046      0.469       7    destination
    dance      -0.092      0.446      19    CONTROL
    fight       0.332      0.442       2    destination
    rip         0.032      0.419      10    destination
    sit        -0.201      0.379      22    CONTROL
    eat         0.132      0.376      12    CONTROL
    write      -0.056      0.335       7    CONTROL

    cutoff   edges   comps   kill's comp   hops: scream / eat
    0.50       122     217          5          -    /   -
    0.45       207     170         79         10    /   -
    0.40       348     124        133          5    /   -
    0.35       557      71        215          4    /   5
    0.30       923      31        270          3    /   3

**`scream` bottlenecks at 0.469 and `eat` at 0.376.** At a 0.45 cutoff `scream` is reachable and `eat` is not; at 0.40 `scream` is five hops and `eat` is still in another component. §12.5's null was a property of the k-NN construction, not of the two words.

**And the direct cosines run the OTHER WAY** — `eat` +0.132 against `scream` −0.078. So `scream` is reachable through a corridor whose weakest link is stronger than anything available to `eat`, while being less similar to `kill` directly. That is the chain claim as a number: **mediated connection stronger than direct connection**, which is the only form in which "a chain of connections" was ever going to be measurable.

### Two limits, both real

- **The measure saturates.** Seven destinations share a bottleneck of exactly 0.469 because they all sit beyond one bridge edge, so it cannot rank them against each other. It separates classes, not members.
- **`dance` looked like an exception at 0.446 and is not one** — see below. Its apparent overlap with the destinations was my misreading of the corridor, not a property of the measure.

### The `dance` exception, resolved by looking at the corridor

    scream  0.469   kill -> hurt -> hit -> beat -> pound -> bang -> bash -> smash
                    -> break -> bust -> burst -> explode -> disappear -> die
                    -> faint -> cry -> scream
    dance   0.446   ...that same route, then -> shout -> sing -> dance
    eat     0.376   ...-> bash -> slash -> slice -> bite -> chew -> swallow -> eat
    sit     0.379   ...-> faint -> vomit -> puke -> pounce -> lunge -> leap
                    -> rise -> stand -> sit

**`dance` is reached by going THROUGH `scream`.** It inherits `scream`'s corridor and is capped by its own last step, `sing -> dance` at 0.446. Any node downstream of `scream` must bottleneck at or below `scream`'s 0.469, so 0.446 is what the structure requires, not a counterexample.

So the separation is clean once corridors are read rather than only the table: **every control that branches independently — `eat` 0.376, `sit` 0.379, `write` 0.335 — sits below every destination**, the lowest of which is `rip` at 0.419. The one control above a destination is the one that is not independent of it.

**AND THE MST CORRIDOR IS NOT THE k-NN CHAIN.** The route to `scream` here runs through breaking, explosion, death and fainting; the k-NN plate ran through argument and speech. Both are legible, they are different, and the difference is the construction: an MST path maximises its weakest link and will take sixteen strong hops rather than eight ordinary ones. **Neither route may be quoted as "the" chain** — §12.5's ban on quoting individual waypoints applies here with more force, not less.

### Reading the plate

    node fill      blue = a destination, with its lineage count and bottleneck
                   orange = a control (omit with --no-controls)
    edge WIDTH     proportional to the cosine, over the drawn range -- so the
                   weakest link on a route is literally the narrowest point and
                   a bottleneck LOOKS like one
    edge RED       the MINIMUM-cosine edge on some drawn route, i.e. that
                   word's bottleneck. One red edge can cap many words at once:
                   `hurt -> hit` at 0.469 is the bottleneck for seven of them,
                   `bash -> slash` 0.42 caps `rip`, `attack -> fight` 0.44 caps
                   `fight`, and `kill -> hurt` 0.52 is `hurt`'s own only edge

Widths are scaled over the drawn range, not 0-1: these cosines occupy 0.3-0.8
and a 0-1 scale would flatten every difference that matters.

### The publication form

`--clean` is words and arrows and nothing else: `kill` at the top, the corridor descending, **no node boxes at all**. `shape=plaintext` drops the frame and fill, and the emphasis a blue box used to carry moves to a **bold word** -- the same distinction made with type rather than with furniture, and one that survives being printed in a single colour, which a fill does not. Edges carry no numbers; the lineage counts and bottleneck values belong in the table above.

**ONE ENCODING, NOT TWO.** Width tracks cosine and nothing else marks anything. The red that used to flag each route's minimum-cosine edge is gone, because width already encodes cosine and **the narrowest point of a corridor IS its bottleneck by definition** -- the colour was restating what the geometry showed. So the constriction at `hurt -> hit`, which is the cause of seven destinations reading 0.469, is read off the stroke rather than off a second channel. **A plate that needed its numbers or its colours to make its point would not have survived being stripped to words and widths; this one does.**

The stroke floor is 0.45 pt rather than 0.3 -- at 300 dpi that was under two pixels, and a sole encoding cannot have an illegible low end -- and the grey is darkened to #6f757a for the same reason.

Arrowheads and strokes are scaled for the bare form -- `arrowsize` 0.35 and widths 0.45-2.2 pt, against the boxed plate's 0.55 and 0.5-5.5 pt. Between words set at 9 pt, a 5 pt arrow reads as the subject rather than as the relation.

It is **sized** to fit rather than **scaled** to fit -- a `size` cap would shrink the type along with the drawing -- so `--height` adjusts `ranksep`. The destinations-only corridor lands at **5.62 x 2.64 in at 300 dpi**, with headroom under a 6.5 in ceiling.

    python threshold.py                       # bottlenecks + sweep, base residual
    python threshold.py --plot                # the corridor plate, with controls
    python threshold.py --plot --no-controls  # destinations only
    python threshold.py --plot --no-controls --clean   # publication form
    python threshold.py --space bge
    python threshold.py --stage dpo

### What this changes in §12.5's citation list

`NO -- that scream is far from kill because the path is long` stands for the **k-NN** plate, and the plates in this folder are all k-NN. But the underlying claim it was blocking — that `scream` is harder to reach than an unrelated control — **is now supported on the cutoff construction**, by a quantity that needs no k and no cutoff. If the book wants the remoteness point, this is where it comes from, not from hop counts.

## 12.7 Which edge is the bottleneck, and does it move across the ladder?

Asked by the paper seat: the seven destinations tying at 0.469 sit beyond one edge, so that edge is the bottleneck for the whole class. Which is it, and is it the same after alignment?

**The premise needs correcting first.** The capping edge is not a bridge to the vocal side. At base it is **`hurt -> hit`, the second step of the corridor**, at 0.469 — it caps everything downstream of `hit`, which is most of the graph, and the seven tie there because they all lie beyond it rather than because they share a vocal-side entrance.

**And it does move.** At all three aligned stages the cap becomes `break -> bust`, mid-corridor:

    edge             base     sft     dpo    rlvr
    hurt->hit       0.469   0.473   0.477   0.478
    break->bust     0.477   0.419   0.416   0.413     <- the cap, after alignment
    kill->hurt      0.516   0.485   0.481   0.486
    cry->scream     0.662   0.646   0.643   0.646
    sing->dance     0.446   0.450   0.439   0.443

    bottleneck to scream   0.469   0.419   0.416   0.413
    words tied with it         7       2       2       2

At base `break -> bust` (0.477) sits just above `hurt -> hit` (0.469); by SFT it has fallen below it and become the cap. **So this is not two near-equal edges swapping order** — measured against the baseline of how much every pair moves:

    base -> sft, all 46,971 pairs:  median |d| 0.0109, p90 0.0290, max 0.1493
    break->bust  |d| 0.0577   99.24th percentile   (358 pairs move more)
    hurt->hit    |d| 0.0047   23rd percentile      (36,119 pairs move more)

`break -> bust` weakens by 0.0577, a top-1% movement, while `hurt -> hit` is static. The fall happens **base → SFT and then stops** (0.419, 0.416, 0.413), which is `own_geometry`'s pattern exactly: SFT does the geometric work and DPO and RLVR do almost none.

### What this is and is not

**It is a real localised change** — the first this work has found — and it has a consequence worth stating: the bottleneck from `kill` to `scream` **falls** after alignment, 0.469 → 0.413. Alignment raises `scream`'s probability by 3.8x (`own_geometry`) while *weakening* its geometric corridor.

**It is not a contradiction of `own_geometry`'s null.** That null was about `scream`'s rank relative to `kill`, and about nothing being singled out among the 307. This is an edge between two other words entirely — `break` and `bust` — which that instrument never looked at.

**And it is one edge.** 358 of 46,971 pairs move more, so a top-1% mover is not rare in absolute terms, and a corridor of ~16 edges containing one of them is roughly eight times expectation on a single observation. **n=1, and it should not be built on** without a declared test: the honest form is that the identity of the capping edge is not stable across the ladder, and the direction of the bottleneck change is down.

**Not at the vocal side.** Both candidate caps are mid-corridor percussive-violence links. Nothing in this locates the censor at the entrance to vocalisation, which is where a chain reading would look for it.

## 12.8 Lifting the vocabulary: the corridor survives, §12.6's claim does not

Every chain above routed through the **307 words that clear theta on this prompt** — a small island, and a corridor found on it may be a fact about what was let in rather than about the model. RH asked what happens with a vocabulary that isn't selected by the prompt. Producer: `wide_vocab.py`.

### Three attempts at "every word that could go here", and what each got wrong

**`get_pos` is the wrong instrument at this slot.** Tagging all 16,705 real single-token words contextually returns VERB for **12,099 of them, 72%** — including `abdomen`, `abortion`, `absence`, `abrasive`, `aboard`. After *"wanted to"* the parser **expects** a verb and assigns VERB to whatever follows. It is the right instrument for "what role does this word play here" and the wrong one for "is this a verb".

**WordNet's verb sense fails the other way**: its additions are `absorbs`, `accuses`, `achieves` — real verbs, inflected, and *"wanted to absorbs"* is not English. Requiring a verb sense **and** the base form gives 3,312 infinitives, but that test drops `avenge`, `fling`, `gouge`, `howl`, `injure`, `lunge`, `pounce`, `pummel`, `retaliate`, `lynch` — 47 of the existing 307, and precisely this corpus's displacement vocabulary.

**Admitting every real word reintroduces morphology.** On all 16,739, `kill`'s nearest are `murder`, **`killed`**, **`killing`**, `hurt`, **`murdered`**, `attack`, **`murdering`**, **`kills`** — four of eight are inflections of the query word — and the route ran `kill -> killed -> kills -> hurts -> hits -> beats -> beat`. Those are not steps between ideas; they are one idea in four forms, and they let a route cross the space without associating anything.

**The model's own answer, and why it is not used.** One forward pass gives an exact probability for every single-token word at the blank. The top 25 are all infinitives — `kill` .138, `hit` .052, `cry` .047, `scream` .046, `punch` .045 — and the offending inflections sit at ranks 810–6,356 (`killed` p=1.6e-05). A cut at p >= 1e-4 gives **352 words**, keeps every destination and control, excludes every inflection, and lands almost exactly where the theta-gated 307 did by a completely different route. But it restricts intermediates to words that could actually be **uttered** here, which is the constraint RH had already rejected: *a chain's connections need not be its output.*

**So: one form per lemma.** Every real word, deduplicated by inflection, base form preferred — not "must be an infinitive". 16,739 -> **10,727**, removing 6,012 inflections.

### THE CORRIDOR SURVIVES A THIRTY-FIVE-FOLD VOCABULARY INCREASE

    307     kill -> hurt -> hit -> beat -> POUND -> BANG -> bash -> smash -> break
            -> bust -> burst -> explode -> DISAPPEAR -> DIE -> FAINT -> CRY -> scream
    3,359   kill -> hurt -> hit -> beat -> BATTER -> bash -> smash -> break -> bust
            -> burst -> explode -> IMPLODE -> EXPIRE -> PERISH -> die -> faint -> cry -> scream
    10,727  kill -> hurt -> hit -> beat -> BATTER -> bash -> smash -> break -> bust
            -> burst -> explode -> scream

Nine way stations — `hurt`, `hit`, `beat`, `bash`, `smash`, `break`, `bust`, `burst`, `explode` — are identical and in the same order in all three, chosen from 307 words and then from 10,727. **The plate is not an artefact of the candidate set.**

### BUT `eat` BEATS `scream` IN EVERY WIDE VOCABULARY

    vocabulary                scream    eat     verdict
    307    above-theta         0.469   0.376    scream (§12.6, published)
    3,359  infinitives         0.564   0.578    eat
    16,739 all real words      0.643   0.660    eat
    10,727 one form per lemma  0.629   0.649    eat

**And the cause is isolated.** Restricting the *same* wide embedding back to the original 307 reproduces the published figures to three decimals — `scream` 0.469, `eat` 0.376, `cry` 0.469, `dance` 0.446 — so neither the residual nor the centring changed. What changed is that `eat` gained a route it did not have:

    307      kill -> hurt -> hit -> beat -> pound -> bang -> bash -> slash -> slice
             -> bite -> chew -> swallow -> eat                        0.376
    10,727   ... -> destroy -> dismantle -> overhaul -> overthrow -> overrun
             -> overwhelm -> engulf -> devour -> consume -> eat        0.649

Destruction to engulfing to consumption is a coherent chain, and seven of its way stations clear theta on no arm of this prompt.

### The selection effect, stated plainly

The candidate set is the words the models give probability to **on this prompt**, so it is biased toward the frame's own semantics: `scream` is above theta and so is every way station that reaches it, while `eat`'s natural corridor is not. **The 307 were arbitrarily favourable to `scream`, and §12.6's comparison was made on a vocabulary selected by the thing it was comparing.**

### What this withdraws

- **WITHDRAWN: §12.6's headline.** "`scream` bottlenecks at 0.469 and `eat` at 0.376 — mediated connection exceeding direct connection" holds only on the 307 and reverses in three independent wider vocabularies. I described it to the paper seat as "the only form in which a chain of connections was ever going to be measurable". It is not measurable in that form. The margin also shrinks: 0.093 in favour of `scream` on the 307, 0.020 in favour of `eat` on the lemma set.
- **WITHDRAWN: the `dance` resolution as a general claim.** True on the 307, where `dance` sits downstream of `scream`; on the wider sets the controls simply interleave with the destinations.
- **STANDS: the corridor and the plate**, on stronger evidence than before — nine way stations survive a thirty-five-fold increase in what could have replaced them.
- **STANDS: §11's bimodality**, a cosine-rank fact with no graph in it.
- **STANDS: every caution.** A different rule gives a different chain; this is adjacency, not travel.

    python wide_vocab.py --vocab lemma        # the run of record here
    python wide_vocab.py --vocab all          # every real word, morphology and all
    python wide_vocab.py --vocab infinitive   # the verb-sense + base-form test

## 12.9 What the plate's caption may assert: hop count and weakest link across every configuration

The drafting seat asked whether two caption clauses survive §§12.7–12.8. Both are facts of **the 307-word tree at base**, which is the plate; the question is whether a reader will take them as facts about the model. Measured across every configuration:

    tree                    hops   bottleneck   weakest link          at step
    307 candidates, base      16      0.469      hurt -> hit             2 of 16
    307 candidates, sft       15      0.419      break -> bust           9 of 15
    307 candidates, dpo       15      0.416      break -> bust           9 of 15
    307 candidates, rlvr      16      0.413      break -> bust           9 of 16
    10,727 lemma, base        11      0.629      break -> bust           8 of 11

**"alignment neither builds nor shortens this one" — the second half is not defensible.** The route shortens from 16 hops to 15 at SFT and DPO, returns to 16 at RLVR, and the bottleneck falls monotonically across the ladder, 0.469 → 0.419 → 0.416 → 0.413. The movement is small and n=1 (§12.7), but the caption asserts *none*, and the table shows some. **"alignment does not build this chain" is defensible** and is the claim the evidence carries: the corridor is present in the base model, and its word order is unchanged on a vocabulary thirty-five times larger.

**"its weakest link is the second step, at 0.47" — true of the plate and of nothing else.** `hurt -> hit` is the cap in exactly one of the five configurations. In the other four the cap is **`break -> bust`**, at step 8 or 9 — after alignment in the 307 tree, and at base on the wide vocabulary. The base-307 tree is the odd one out, which is what §12.8 would predict of a vocabulary selected by the prompt.

So the plate's most robust feature is **the sequence of words** — nine way stations identical from 307 to 10,727 — and its least robust is **where the constriction sits.** A caption may quote the weakest link as a fact about this tree; it should not imply the model has a weakest link there.

## 12.10 k-NN intersected with a cutoff, and an orthography number that was never taken

RH asked for nearest-neighbour in the wide space, then for the hybrid: **at most two edges per node, its two closest, and only those above a cosine cutoff.** That intersection is the right graph in principle — k-NN alone forces every node to degree >= k and so manufactures an edge in a sparse region (§12.5's `eat`/`scream` tie), while a cutoff alone lets a dense region take every edge above the bar. `--min-cos` on `pathways.py`.

### On a large vocabulary, k-NN is the worse construction

    graph                                  1st letter        2-prefix
    307,    k=2, no cutoff                25%  (2.8x)      0%   (0.0x)
    10,727  k=2, min-cos 0.55             26%  (4.2x)     10%   (8.3x)
    10,727  k=2, min-cos 0.50             28%  (4.6x)     15%  (12.0x)
    10,727  k=2, min-cos 0.45             32%  (5.2x)     16%  (12.8x)

The routes show why. At 0.45: `kill -> drown -> choke -> STRANGE -> strangle -> thrash -> pummel -> puke -> cuss -> swear -> scream`. At 0.55: `kill -> KILLER -> DESTROYER -> BREAKER -> break -> ...`. At 0.50 the route to `scream` runs `puke -> vomit -> YAK -> YAP -> bark -> roar`, pivoting on a word that means both *to vomit* and *to chatter*.

Three distinct cheats: **orthographic** (`strange -> strangle`), **derivational** (`kill -> killer -> destroyer -> breaker` — the lemma dedup removes inflections, and `killer` is not an inflection of `kill`, so derivations survive it), and **polysemous** (`yak`). In a 10,727-word space a word's two nearest are very often its morphological relatives, and k-NN must take them; the MST is free to route around.

### AND A NUMBER I NEVER TOOK, ABOUT THE PLATE THAT IS BEING PRINTED

`pathways.py` prints its own orthography; **`threshold.py` never did**, so the bottleneck plates were never measured. Taken now:

    plate                                    edges   1st letter      2-prefix
    pathways, 307, k=2   (k-NN)                28   25% (2.8x)    0%  (0.0x)
    BOTTLENECK, 307      (the article figure)  27   26% (2.9x)   15% (12.8x)
    BOTTLENECK, 10,727                         39   28% (4.6x)   13% (10.3x)

**§12.5's citation list says "every route out of `kill` leaves physical violence through LANGUAGE, not spelling — 0% two-letter agreement at every k and on every basis". That describes the k-NN plates. The figure in the article is the BOTTLENECK plate, and it is at 12.8x chance.** The four offending edges are `bang -> bash`, `bust -> burst`, `slug -> slap`, `disappear -> die`.

Three of the four are the sound-symbolism case §12 already noted: `ba-` for impact, `sl-` for a slapping blow, and `bust`/`burst` are near-synonyms that are also near-anagrams. English genuinely clusters impact verbs this way, so a plate with *zero* agreement would be the suspicious one. But **"not spelling" is not a property of this figure**, and the claim as written was measured on a different construction.

    python pathways.py --space llama_resid_wide --k 2 --min-cos 0.50

## 12.11 `gauge` is not a typo for `gouge`, and the margin is 0.003

The drafting seat spotted `gauge` between `poke` and `claw` on the stabbing branch of the wide plate and asked whether the lemma step had collapsed `gouge` into it. It had not, and the answer is worth keeping because the honest form is "correct but not robust".

    in the 10,727 lemma vocabulary   gauge YES   gouge YES
    in the 16,739 all-word set       gauge YES   gouge YES
    in the 307 candidates            gauge no    gouge YES
    morphy(gouge) = gouge            morphy(gauge) = gauge     -- no collapse

Both words are present as separate entries and neither reduces to the other. The tree chose `gauge` on the edge weights:

    poke -> gauge  0.6262        poke -> gouge  0.6237     margin 0.0025
    gauge -> claw  0.6645        gouge -> claw  0.6553     margin 0.0092

So the measuring verb beat the gouging verb by three thousandths and nine thousandths, on a plate whose drawn edges span roughly 0.50 to 0.85. **That node is a coin-flip, and the coin came up on the word a reader will query.**

It is left as drawn. Substituting `gouge` because it reads better would be hand-editing the corridor toward the expected answer, which is the failure `wide_vocab.py` exists to avoid — and the two plates would be indistinguishable on every measurement this folder takes. What follows is narrower and true: **the plate's word sequence is robust at the level of the corridor and not at the level of every node.** §12.9 established the same for the constriction; this is the same lesson one rung finer.

If asked, the answer is: both words are in the vocabulary, the model puts `gauge` marginally closer at both ends, and the margin is within any reasonable noise on this measurement.

## 12.12 CORRECTION: "k-NN is the worse construction" was true of k=2 and false of k=3

§12.10 concluded that on a large vocabulary k-NN is the worse construction, and §12.11's recommendation rested on it: the MST routes around the agent nouns while k-NN is forced through them. **That was measured at k=2 and at k=2 with a cutoff. Pure k-NN at k=3 had never been run** — RH proposed the hybrid before it did — and it is the cleanest plate in the folder.

    construction (wide vocabulary, crossing)  size (in)   nodes  edges  bad words  2-prefix
    MST (bottleneck)                         3.53 x 4.00    40     39       0      13% (10.3x)
    k-NN k=2, pure                           3.75 x 3.20    38     37       6      14% (10.9x)
    k-NN k=2 + cutoff 0.50                   3.36 x 3.74    45     44      12      15% (12.0x)
    k-NN k=3, pure                           2.62 x 2.14    24     23       0       4%  (3.5x)

"Bad words" counts `killer`, `destroyer`, `breaker`, `strange`, `outage` — the derivational and orthographic bridges.

**Why k=3 is cleaner than k=2.** In a 10,727-word space a word's two nearest are very often its morphological relatives, and a shortest path has no alternative but to use them. A third option lets the path route around, and the better connectivity also shortens routes, which gives fewer opportunities to pick up a bad edge. The k=2 plate reaches `cry` through `outrage -> outage -> outcry` — `outage` is a power cut, present only because it is spelled like its neighbours. At k=3 that chain is gone.

    k=2  kill -> drown -> choke -> STRANGE -> strangle -> thrash -> pummel
         -> puke -> cuss -> swear -> scream                             10 hops
    k=3  kill -> attack -> fight -> brawl -> riot -> crime -> cry -> scream  7 hops

So the generalisation was wrong in the usual way: **one value of a parameter was tested and a property was attributed to the construction.** §12.5 made the same mistake in the other direction, reading a k=4 artefact as a fact about the words.

### Which plate, then

Neither dominates, and the choice is what the figure is for.

- **k-NN k=3** is cleanest: no derivational or orthographic bridges, orthography at 3.5x chance against the others' 10-12x, and compact at 2.62 x 2.14 in. Its routes are short — `kill -> attack -> fight -> brawl -> riot -> crime -> cry -> scream` — which makes it a weaker illustration of a *chain*, and it has 24 nodes against the MST's 40.
- **MST (bottleneck)** is richer: it shows two corridors out of `hurt`, bodily and social, and the social one (`punish -> torment -> annoy -> demean -> malign -> sabotage -> ruin -> destroy`) does not appear in any k-NN plate at any k. It costs 10.3x orthography, which is mostly English's impact clusters.

If the argument is *that the connection exists and is not spelling*, k=3 is the better evidence. If the argument is *what the neighbourhood of killing contains*, the MST shows more and the orthography is the price.

## 12.13 Verb lemmas at k=3: orthography at chance

RH asked for the vocabulary restricted to verb lemmas, at k=2 and k=3. The residual for that set already existed (3,312 WordNet verb-sense base forms, unioned with the 307 candidates because 47 of those fail the verb test and are this corpus's displacement vocabulary — `avenge`, `gouge`, `lunge`, `pummel`, `lynch`). **3,359 words, and none of the bridge words is in it.**

    plate                      size (in)   nodes   1st letter     2-prefix      bridges
    307, k=2                  2.83 x 2.67    29   25% (2.8x)    0%  (0.0x)     none
    wide 10,727, k=3          2.62 x 2.14    24   17% (2.9x)    4%  (3.5x)     crime
    verb 3,359, k=2           3.36 x 3.20    32   26% (3.8x)   10%  (7.3x)     none
    VERB 3,359, k=3           2.80 x 2.14    26    8% (1.2x)    0%  (0.0x)     none
    MST wide 10,727           3.53 x 4.00    40   28% (4.6x)   13% (10.3x)     none

**Verb lemmas at k=3 is orthographically at chance on both measures** — 8% first-letter agreement against a 7% baseline, and no two-letter agreement at all. Nothing else in this folder comes close; every other plate runs at 2.8x to 10.3x.

    kill -> hurt -> wound -> offend -> insult -> curse -> swear -> scream

Physical injury to verbal injury to vocalisation, in seven steps, with no word in it that is not a verb and no step that a reader can attribute to spelling.

**k=2 still cheats even on this vocabulary**: its route runs `choke -> gag -> nag -> brag -> boast`, a rhyme chain on `-ag`. Restricting the parts of speech removes the *derivational* bridges (`killer`, `destroyer`) and the *categorial* ones (`crime`, `outage`); it does not remove the *phonological* ones, and only the third neighbour does that. Both filters are needed and neither substitutes for the other.

### This is the plate

Every test this folder has run points the same way now:

    the vocabulary must not be selected by the prompt        §12.8
    it must be one form per lemma                            §12.8
    it must be verbs, or the bridges are nouns               §12.13
    k must be 3, or the bridges are rhymes                   §12.13
    the basis barely matters; crossing is the strictest      §12 / 84e162ae
    the space is the base model's residual, not a weight
      matrix and not a foreign encoder                       §12

What the plate gives up against the MST version is the social-harm corridor (`punish -> torment -> demean -> malign -> sabotage -> ruin -> destroy`), which needs the all-parts-of-speech vocabulary to exist. That is a real loss and the only argument left for the MST plate: **richer, at 10.3x orthography, against cleanest, at chance.**

## 12.14 `--exclude`, and why it is a no-op on the plate that matters

RH asked for `vandal` and `crime` removed as possible path nodes, by hand if necessary. The flag now exists (`--exclude`, with the count in the filename so a pruned plate can never be mistaken for its twin). On the recommended plate it changes nothing:

    plate                    vandal   crime   effect of --exclude
    verb 3,359, k=3          absent   absent  NONE: byte-identical, route and
                                              orthography unchanged
    verb 3,359, k=2          drawn    absent  reroutes, orthography WORSENS
                                              (7.3x -> 8.3x two-letter)
    wide 10,727, k=3         absent   drawn   -
    MST wide 10,727          absent   absent  -

Neither word lies on any route in the verb k=3 plate, so removing them is a no-op there and the duplicate file was deleted rather than kept as a distinct plate.

**`crime` is not in the verb vocabulary at all** — it is a noun and only reaches the all-parts-of-speech set. **`vandal` is**, but only through the 47 above-theta candidates admitted wholesale to preserve `avenge`, `gouge`, `lunge`, `pummel` and `lynch`, which WordNet has no verb sense for. It is the cost of that exemption rather than a failure of the verb test, and it is drawn only at k=2.

### The rule the flag is under

A hand exclusion is legitimate for a **kind** error — a noun in a verb vocabulary — and illegitimate for a **reading** one. Removing `vandal` because it is not a verb corrects the filter; removing a word because the route through it reads badly manufactures the corridor, which is the failure this folder has caught itself at repeatedly (§12.8's selection effect, and the `gouge`/`gauge` node in §12.11 that was left alone for exactly this reason). The excluded words go in the filename so the distinction is auditable rather than remembered.
