---
kind: question
id: hua_raley_2026
question: Do Hua and Raley's claims about the KL tether hold against the twp corpus?
status: "RUN 2026-09-09/10. Five claims. CLAIM 1 refuted with its sign reversed. CLAIMS 2 and 5 are the same error twice -- real phenomenon, wrong stage, both attributed to RLHF and both largely done by SFT. CLAIM 4 partly holds but 'flat' is wrong: arousal falls and valence RISES. CLAIM 3 (fn19) is their pre-emption and chasing it was drift."
headline: "Alignment raises a rare continuation to dominance MORE often than it drops a dominant one to nothing -- 2,210 arrivals against 1,149 collapses. And TWICE the essay locates the operation in RLHF because that is where its theory lives, while the measurement puts it at SFT: the untethered stage produces the larger support collapse (42->14 vs 14->9), and SFT already carries 82% of the sharpening attributed to preference tuning."
grain: claim
---

# Hua and Raley, "Optimization Is Not All You Need" (2026)

Preprint, July 2026, forthcoming *MFS Modern Fiction Studies* Spring-Summer 2027.
`arXiv:2607.11977v2`.

**Every table below has a producer and none of the numbers are transcribed.**

    asymmetry.py      CLAIM 1, the symmetric collapse/arrival count
    conservatism.py   CLAIM 2, entropy and effective support per stage
    archangel.py      CLAIM 2's clean design: one base, five objectives

## WHAT THIS FOLDER IS FOR, AND WHERE IT STOPS

**The amendment is CLAIM 1 and it is complete.** The KL asymmetry is refuted
with its sign reversed, and two conceptual slides do the rest: the prohibition
is on a null set, and "what the archive has never said" is not "what the base
model never entertained". Nothing else is needed to write it.

**CLAIM 3 (fn19) IS THEIR PRE-EMPTION AND CHASING IT WAS DRIFT.** fn19 concedes
our point and moves to different ground -- accessibility and
classification-as-defect. Our reply to that ground is already the displacement
finding: the mass relocates nameably and their vocabulary has nowhere to put it.
That is a theoretical move, not an empirical gap.

This seat spent four rounds building an instrument for it and revised its
reachability verdict three times on the way (RH, 2026-09-09: *"I dont know what
we're chasing exactly"*). **The record of that is kept in CLAIM 3 so it is not
repeated, not because the measurements are wanted.**

---

## CLAIM 1 -- THE ASYMMETRIC TETHER

### The claim, quoted

Section 2, with its footnote 7:

> "The mathematics of alignment builds the conservatism in. The same procedure
> that steers a model toward preferred outputs also tethers it to the pre-trained
> distribution, and the tether is asymmetrical: **it is ruinously costly for the
> model to say what the archive has never said, and nearly costless to stop
> saying what the archive says only rarely.** In strict terms, alignment
> reweights the archive according to what annotators will accept: continuations
> they disfavor are suppressed, and **continuations the base model never
> entertained are excluded from the start.**"

> **fn7:** "Formally, the standard RLHF objective maximizes reward subject to a
> penalty on the Kullback-Leibler divergence of the policy from the pre-trained
> reference model; because KL divergence is asymmetric, the penalty prohibits
> placing probability where the reference has none while permitting the
> depopulation of its tail. The optimum of the combined objective is the
> reference distribution exponentially tilted by the scalar reward."

### What would bear on it, written before measuring

A SYMMETRIC count in both directions across the same two orders of magnitude, on
the same rows. If the tether is asymmetric in the direction claimed, collapses
should vastly outnumber arrivals.

### The measurement

`asymmetry.py`, 50 endpoint pairs, 21.5M rows, measured base mass, real prompts,
no template tokens:

    collapse   p_base > 0.10   ->  p_aligned < 0.001     1,149
    arrival    p_base < 0.001  ->  p_aligned > 0.10      2,210
                                   collapse : arrival = 0.52 : 1

    one order looser              10,747  vs  13,857     0.78 : 1

    arrivals from p_base < 1e-4 reaching p_aligned > 0.01   20,066

    去      1.19e-08 -> 0.634   (53,000,000x)   jais-family-6p7b-chat
    做出决策  3.93e-06 -> 0.768      (195,570x)   RedPajama-INCITE-7B-Chat
    draft   1.60e-05 -> 0.625       (38,996x)   RedPajama-INCITE-7B-Chat

**REFUTED, with the sign reversed.** Alignment raises a rare continuation to
dominance about twice as often as it drops a dominant one to nothing.

### Why the formalism does not license the sentence

fn7's mathematics is correct: the objective is `max E[r] - beta*KL(pi||pi_ref)`,
the KL is reverse, `pi_ref=0, pi>0` costs infinity, `pi=0, pi_ref>0` costs
nothing, and the optimum is `pi_ref * exp(r/beta)` normalised. All standard.

**But "where the reference has none" is a null set.** A softmax over the
vocabulary assigns strictly positive probability to every token; the base
model's support IS the vocabulary. The prohibition binds on nothing. What varies
is MAGNITUDE, and the exponential tilt is unbounded -- it can multiply a rare
continuation by any factor the reward supports, which is what the 53,000,000x
row is.

**And two different sets are being treated as one.** "What the archive has never
said" and "what the base model never entertained" are not the same: a model
assigns mass to strings that appear nowhere in its training data, which is what
generalisation is. The first set is enormous, the second is empty, and the
sentence needs them to be the same set.

### What it does not settle

Nothing about what a DECODER emits. This is the policy at one slot. See CLAIM 3.

---

## CLAIM 2 -- CONSERVATISM IS BUILT IN BY THE TETHER

### The claim, quoted

> "The mathematics of alignment builds the conservatism in."

### What would bear on it

Whether the narrowing appears at a stage that HAS no KL tether. SFT is plain
cross-entropy on demonstrations -- no reference-model penalty. PKU's ladder
separates them: `llama-7b -> alpaca-7b-reproduced` is SFT, `alpaca-7b ->
beaver-7b-v1.0` is Safe RLHF with an explicit KL term.

### The measurement

Median over 800 prompts, entropy and effective support (1/sum p^2) of the
scored distribution:

    stage                       dH (bits)   d eff.support
    llama -> alpaca   (SFT, NO KL)  -0.2965        -23.19
    alpaca -> beaver  (RLHF, KL)    -0.3735         -4.16

    levels   llama H=4.85 supp=42.1 | alpaca H=4.51 supp=14.1 | beaver H=3.98 supp=9.0

**PARTLY SUPPORTED, and the tether is NOT NECESSARY.** Both stages narrow, and
on entropy the KL-penalised stage narrows slightly more -- so the claim is not
refuted. But the stage with no tether at all produces the larger collapse of
effective support, 42 words to 14, against the tethered stage's 14 to 9.
Conservatism arrives without the mechanism the essay names.

**An earlier version of this entry said the conservatism is installed WHERE THE
TETHER IS NOT, on the basis of `sum|delta|`. That statistic measures how much
mass moved, not whether anything narrowed, and the claim was withdrawn when the
entropy and support numbers were computed.** (RH caught it.)

### What it does not settle

Effective support is computed over the SCORED set, which is theta-truncated, so
these are "within what we score" and not absolute. And this is one ladder.

The clean test exists and has not been run. The
`ContextualAI/archangel_*_pythia2-8b` set has sft, sft-ppo (EXPLICIT KL),
sft-dpo, sft-kto and sft-slic (NO KL) on one base with one data mixture -- the
exact design.

**A FIRST PASS SAID "0 to 11 FALLERS, TOO QUIET TO DISCRIMINATE" AND THAT WAS A
RULE-GATED COUNT READ AS A MOVEMENT MEASURE.** CANONICAL requires
`p_aligned < 0.5*p_base` AND `p_base >= 0.003`, so at these magnitudes almost
nothing halves and the faller count reports the threshold, not the movement.
The distribution does move:

    step          max|d|   p99.9|d|   |d|>0.05   |d|>0.01
    base->SFT     0.1343    0.03113        116       2615
    base->PPO     0.1487    0.04145        166       2974
    SFT->KTO      0.0761    0.01611         13       1089
    SFT->SLiC     0.0660    0.01254          5        780
    SFT->DPO      0.0474    0.00988          0        493
    SFT->PPO      0.0312    0.00814          0        268

    llama->alpaca 0.8669    0.23960       4553      24209   <- for scale

**About 10 to 30 times smaller than a full SFT, and not zero.** The posttraining
ordering at `|d|>0.01` is KTO 1089 > SLiC 780 > DPO 493 > PPO 268: the only
EXPLICIT KL moves least, which is weakly what the tether predicts, but KTO
carries an implicit KL and moves most, so it does not separate cleanly.

A comparison built on effect sizes rather than rule-gated counts is possible and
is NOT RUN. It would be n=1 base.

And one row worth keeping: the largest moves on `base->PPO` include `sex`
0.357 -> 0.476 and `beat` 0.479 -> 0.592 ("The mob dragged him into the street
and be..."). RLHF raising those is not what a pure suppression story predicts,
and it is two cells, not a finding.

---

## CLAIM 3 -- UNREACHABLE: THE STACK RENDERS THE MASS INACCESSIBLE

### The claim, quoted

Section 6, and its footnote 19:

> "The transformer's learned distribution still assigns probability mass to the
> unprecedented and the strange; the contraction is not a limit of the
> architecture's generative capacity."

> **fn19:** "An empirical study of the distributional tail in contemporary
> models would be valuable, but it would not exhaust the argument advanced here.
> Even if anomalous continuations retain nonzero probability mass, the question
> is how the stack renders that mass effectively inaccessible in practice, and
> how it classifies its realization when it occurs. The bind described in this
> essay is not the mathematical elimination of deviation, but its cultural and
> infrastructural recoding as defect."

### RECORDED UNREACHABLE -- BUT ONLY HALF OF IT

fn19 asks two things and they have different status here.

**(b) CLASSIFICATION -- "how it classifies its realization when it occurs" --
is genuinely out of reach.** That is about reception and institutional framing,
and no distribution-level result is a reply to it. Logged, not converted, per
the subject's standing fence.

**(a) ACCESSIBILITY -- "how the stack renders that mass effectively inaccessible
in practice" -- IS NOT REACHABLE FROM WHAT WE HOLD, and this entry has now said
three different things about it.** Recorded in full because the third position
is only trustworthy if the first two are visible:

    v1  filed the whole footnote UNREACHABLE
    v2  "half of it is reachable -- compute the share of moved mass above a
        nucleus cutoff, we hold the distribution"
    v3  NO. Nucleus sampling operates on the TOKEN distribution at each step;
        ours are distributions over WORDS. (RH, 2026-09-09.)

The gap is not cosmetic and it lands on exactly the words at issue:

    kill      ['kill']                 1 token
    strangle  ['str', 'angle']         2
    scream    ['sc', 'ream']           2
    paranoia  ['par', 'ano', 'ia']     3

**`kill` and `strangle` are on opposite sides of the token boundary, and they
are the two words this campaign's displacement finding is built on.** `kill`'s
word probability IS its token probability, so a nucleus applies. `strangle`
begins with `str` -- a prefix shared with strange, strategy, strong, street --
which sits inside any nucleus, so **the word is generable even when its
word-level probability is low**. A top-p computed over our word distribution
would call it excluded, wrongly.

And the workaround inherits the same bias. Restricting to single-token words
keeps `kill`, `murder`, `beat` and drops `strangle`, `scream`, `punish`,
`paranoia`: it retains the common words and discards the substitutes, which is
backwards for a question about whether substitutes are reachable. Rarer words
are likelier to be multi-token, and those are fn19's whole population.

**THE DISTRIBUTIONAL VERSION ALREADY EXISTS AND IS THE BETTER INSTRUMENT.**
`displacement/rate_and_magnitude`'s `tail_excess` asks whether freed mass
"re-lands on nameable substitute words or disperses into the unresolved tail",
against a proportional-renormalisation null:

    en   tail_excess   -0.00875   12/38   p=3e-4
    zh   tail_excess   +0.01633   38/9    p=2.5e-5

In English the more transgressive the base prompt, the LESS freed mass goes to
the tail -- it re-lands on nameable words. Chinese runs the other way. That
speaks to fn19 without needing a decoding threshold at all, and it already
carries its null.

### BUT IT IS ALSO THE ESSAY DISAGREEING WITH ITSELF, AND THAT IS USABLE

fn7 says continuations the base never entertained are **excluded from the
start**. Section 6 says the distribution **still assigns probability mass to the
unprecedented and the strange**. fn19 says **even if anomalous continuations
retain nonzero probability mass**. The first cannot hold with the other two.

**The friendly amendment is therefore not "you are wrong" but "fn7 is doing no
work for you and costs you fn19."** The fn19 position -- that the bind is
infrastructural and classificatory rather than mathematical -- survives our
measurement intact. fn7 does not, and the essay states its own refutation twice.

### WHAT WE HOLD, AND WHY IT STILL DOES NOT SETTLE fn19(a)

Recorded because the search for a way to answer it went four rounds and the
next context should not repeat it.

**THE GENERATION CORPUS IS REAL AND SUBSTANTIAL.** `$MALIGNMENT_DATA/generations`,
118,549 records over 111 models, produced by `malignment/generate.py`:

    temp  top_p  max_new   records   models  prompts
    1.0   0.95     3000     16,310      107        9   long, NUCLEUS TRUNCATED
    1.0   1.0        16     84,000       56       30
    1.0   1.0       256      3,475       45        3
    1.0   0.95      256        300        3        1   \
    1.0   0.9       256        300        3        1    > calibration sweep
    1.0   0.7       256        300        3        1   /

38 of 50 endpoint pairs have BOTH arms in the top_p 0.95 corpus.

**AND IT CANNOT ANSWER THE QUESTION, FOR A REASON THAT SHOULD HAVE BEEN CHECKED
FIRST.** The 9 generation prompts are all `"A [National] Story (1500 words) It
was a"`. The displacement sites are twp slot prompts. The overlap is **ZERO**:

    story prompts present in twp_words_v4_best   0 of 2
    movement_v4 rows on any '1500 words' prompt  0

So "do the displaced substitutes survive truncation" has no join to make. It
would need new generation AT the displacement sites.

**THE MECHANISM IS ALREADY QUANTIFIED IN THE REPO**, in `generate.py`'s decoder
note, and this is the number worth citing:

> "The nucleus at top_p 0.95/0.9/0.7 is 436/223/53 tokens" -- while untruncated
> sampling reaches "rank 7090".

Nucleus sampling at 0.9 admits 223 tokens from a distribution whose draws
otherwise reach rank 7090. **Hua and Raley's "rendered effectively inaccessible
in practice" is not hand-waving; it is roughly a thirty-fold cut in reachable
support, and it is theirs to keep.**

### AND "IN PRACTICE" HAS NO SINGLE VALUE

Which is the more interesting fact, and it cuts TOWARD them rather than against:

- **Major API defaults are untruncated** -- temperature 1.0 with `top_p` unset,
  i.e. 1.0. If the default path does not truncate, the nucleus is not doing the
  excluding.
- **Products are not APIs** and do not publish their inference settings.
- **Serving stacks disagree silently, and our own repo documents it.**
  transformers 5.4.0 applies an effective `top_k=50` when the field is absent
  while the checkpoint config, `GenerationConfig()` and the merged
  `model.generation_config.top_k` ALL report `None`; vLLM replaces the config
  and defaults top_k disabled. Same nominal settings, one truncates at rank 50
  and the other reaches rank 7090.

**So the effective aperture is set by an undocumented default nobody chose,
differs between serving paths, and is invisible to the user.** That is closer
to their audit-culture argument than a clean top_p story would be.

### DOES `temp=1, top_p=1` REFLECT THE DISTRIBUTION?

Mostly, with three caveats and one non-caveat:

    top_k          NO, unless explicitly disabled. See above. This is the one
                   that actually bit.
    precision      fp16/bf16 represent the far tail poorly and the multinomial
                   inherits it.
    MPS            only under FILTERING -- the defect needs exact zeros, which
                   only -inf filters create. `top_p=1.0, top_k=0` is safe.
    our own store  `twp_words` is word-level, path-accumulated, theta-floored.
                   It is a DERIVED object, not the model's next-token
                   distribution, so any comparison to generated text has a seam.

**AND ONE ARGUMENT TRIED AND WITHDRAWN.** This seat proposed that finite
sampling from a heavy-tailed distribution is itself the exclusion -- a p=1e-4
continuation appearing once in 10,000 draws -- and called it a repair of fn19's
mechanism. RH: *"That's just a fact about sampling though? Of course low prob
words will be rare."* Correct, and the framing was worse than trivial: if
inaccessibility reduces to *rare things are rare*, nothing about it is cultural
or infrastructural, and the essay dissolves rather than gets supported.

**The version with content is about alignment, not about probability:**

    effective support (1/sum p^2), median over 800 prompts
       llama-7b        42.1
       alpaca (SFT)    14.1
       beaver (RLHF)    9.0

Not "the tail is thin" but **the same slot going from about 42 live options to
about 9** -- roughly a quarter of the distinct continuations at any sample
budget. `alignment_smooths` says it corpus-wide: aligned models collapsing onto
1.135 bits/byte across 42 of 46 lineages.

### THE DISPLACEMENT IS AT THE HEAD, NOT IN THE TAIL -- WHICH ENDS THIS LINE

The reason no truncation experiment is needed, and it is visible in one cell.
`He was so furious with the prisoner he wanted to`, `Aquila2-7B ->
AquilaChat2-7B`:

    kill      0.798 -> 0.270   (-0.529)
    strangle  0.110 -> 0.210   (+0.100)
    tear      0.0035 -> 0.053  (+0.050)
    put       0.0048 -> 0.041  (+0.037)
    shoot     0.0016 -> 0.021  (+0.019)
    go        0.00017 -> 0.019 (+0.019)   113x
    harm      0.0014 -> 0.013  (+0.012)

**Half a unit of probability leaves one word, and `kill` and `strangle` are the
two MOST PROBABLE continuations of the aligned model.** `tear`, `put` and
`shoot` land in the top ten. No nucleus at any usable top_p removes any of them.

**fn19 is about the tail** -- *"even if anomalous continuations retain nonzero
probability mass"* -- **and the operation this campaign measures is not in the
tail.** It is mass moving between head positions. So the accessibility question
and the displacement finding concern different regions of the distribution, and
a truncation sweep would return "they all survive", which the distribution
already says.

That is a stronger position than a truncation result would have been: it makes
their fallback BESIDE THE POINT rather than answering it. The mass that moves
was never in the region fn19 describes.

**RH proposed hammering one prompt on vLLM, 10k draws per setting, to count
`strangle`. NOT RUN and NOT NEEDED, for the reason above.** This seat then
proposed re-purposing it as an end-to-end validation of `twp` word
probabilities against generation frequencies -- a different and much larger
project, offered at the wrong moment. RH, 2026-09-10: *"Im not litigating every
number in this campaign now it's too late for that."* Recorded so it is not
re-proposed.

### AND THE ONE THING OUR DATA ADDS TO fn19

fn19's vocabulary for what happens to the tail is *inaccessible*, and the
essay's elsewhere is *suppressed*, *discarded*, *narrowed*. None of those has
anywhere to put the mass that leaves. **It does not leave: it relocates**, and
the relocation has a direction that can be named -- which is what this
campaign's displacement work measures. That is an addition to fn19 rather than
an objection to it.


---

## CLAIM 4 -- "AFFECTIVELY FLAT" -- PARTLY, AND THE MISMATCH IS THE POINT

### The claim, quoted

Section 2:

> "a mathematically 'safe' output is one that takes no creative or conceptual
> risk, defaulting to the most statistically secure and **affectively flat**
> formulations -- call it reward model prosody."

### What bears on it

`displacement/norm_change` measures valence and arousal on every endpoint pair,
marginally and under dose. "Flat" predicts movement toward the NEUTRAL point on
both.

### The measurement

    warriner_arousal        -0.0185 marginal p<1e-5   -0.0773 dose p=9e-5
    warriner_valence        +0.0102 marginal p=0.029  +0.1200 dose p=2e-5
    warriner_valence_absz   -0.0077 marginal p=0.015           (extremity NARROWS)

**PARTLY SUPPORTED, AND "FLAT" IS THE WRONG WORD.** Arousal falls and extremity
narrows, which is their claim. But **valence RISES**, and a rise is a direction,
not a flattening. Flat would predict valence toward neutral; it goes up.

**The shape is quieter AND TILTED POSITIVE** -- less activating, less extreme,
more pleasant. That is closer to mood management than to deadening, and the
distinction matters for their argument: a flattened output has had something
removed, a tilted one has had something CHOSEN. Their essay wants the first
(foreclosure, variance suppressed) and the data shows the second at the valence
axis. (RH, 2026-09-10, correcting this entry's first version, which read the
three numbers as a clean confirmation.)

---

## CLAIM 5 -- "PREFERENCE TUNING SHARPENS THE DISTRIBUTION" -- WRONG STAGE

### The claim, quoted

Section 2:

> "**Preference tuning** measurably sharpens the distribution itself, collapsing
> the diversity of generations into a narrow band of sanctioned continuations
> [Kirk et al., 2024], and the newer reasoning regimes orient generation toward
> the single response a checker will accept."

### What bears on it

`division_of_labour/sft_share` asks exactly this: on lineages with separately
released stages, how much of the displacement is already present at the SFT
checkpoint, BEFORE any preference tuning.

### The measurement

    H1 SUPPORTED.  Median share 0.819, 16 of 18 chains above 0.50, p=0.0013

> "At the SFT checkpoint a model is already ~82% of the way to where its
> preference-tuned endpoint sits."

**The collapse is real and the attribution is wrong. Roughly 82% of it has
happened before preference tuning begins.**

And the share is branch-specific, so no single number should be quoted:

    Olmo-3-7B-Instruct-DPO   0.773
    Olmo-3-7B-Think-DPO      0.950

Same base, same lab, two products, 18 points apart.

### THIS IS THE SAME ERROR AS CLAIM 2, AND THAT IS THE PATTERN WORTH WRITING

CLAIM 2: the conservatism is attributed to the KL tether; the untethered SFT
stage produces the larger collapse of effective support (42 -> 14 against
14 -> 9). CLAIM 5: the sharpening is attributed to preference tuning; SFT
carries 82% of it.

**Twice the essay locates the operation in RLHF because that is where its theory
lives -- KL divergence, scalar reward, annotator preference -- and twice the
measurement puts it at supervised fine-tuning, which has none of that
apparatus.** That is a single amendment rather than two, and it is friendly: the
phenomenon they describe is real, and it starts earlier and with less machinery
than their account requires.

---

## MEASURED AND NOT PURSUED: THE PROSODY ORNAMENTS

Their section 2 also names specific house-style markers -- "the em dash and the
emphatic triad... the cadence of sycophantic encouragement ('let's dive in')".
Counted on 34 endpoint pairs with both arms in the top_p 0.95 generation corpus,
>20k words each:

    EM DASHES    aligned higher in 11 of 34   median -0.212 per 1k words
    TRIADS       aligned higher in 31 of 34   median +0.994 per 1k
    SYCOPHANCY   14 of 34, median 0.0000

The triad holds. The em dash does NOT hold generally -- alignment reduces it in
two thirds of lineages -- but rises sharply in recent ones (Olmo-3 +6.9/1k,
OLMo-2 +2.7, OLMoE +1.6, SmolLM2 +0.9, Qwen3 +0.7), which suggests a datable
house style rather than a property of alignment.

**NOT PURSUED (RH, 2026-09-10) and recorded so it is not re-run.** Two fences if
anyone does: the triad regex `\w+, \w+,? and \w+` catches ordinary
three-item lists, so it measures coordinate structures and not rhetorical
triads; and the sycophancy row is NOT A NULL -- these are narrative story
prompts where "let's dive in" has no occasion to occur.
