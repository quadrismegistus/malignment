---
kind: question
id: hua_raley_2026
question: Do Hua and Raley's claims about the KL tether hold against the twp corpus?
status: "RUN 2026-09-09. Three claims tested, one recorded UNREACHABLE. The asymmetry claim is REFUTED with its sign reversed: arrivals outnumber collapses about 2:1."
headline: "Alignment raises a rare continuation to dominance MORE often than it drops a dominant one to nothing -- 2,210 arrivals against 1,149 collapses across the same two orders of magnitude. The essay's formal claim contradicts its own main text and its own footnote 19, and it does not need it."
grain: claim
---

# Hua and Raley, "Optimization Is Not All You Need" (2026)

Preprint, July 2026, forthcoming *MFS Modern Fiction Studies* Spring-Summer 2027.
`arXiv:2607.11977v2`. Producers: `asymmetry.py`.

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

The clean test exists and is out of reach for a different reason: the
`ContextualAI/archangel_*_pythia2-8b` set has sft, sft-ppo (EXPLICIT KL),
sft-dpo, sft-kto and sft-slic (NO KL) on one base with one data mixture -- the
exact design. **The models barely move on our prompts**: 29 fallers on
base->SFT against 50,861 for llama->alpaca, and 0 to 11 fallers on each
posttraining step. Too quiet to discriminate.

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

### RECORDED UNREACHABLE

This is a claim about decoding, interface, deployment and reception. **Our
instrument measures the policy at one slot and cannot reach any of it**, and the
subject's standing fence says such a claim is logged, not converted into one we
can answer. A distribution-level result is not a reply to it.

### BUT IT IS ALSO THE ESSAY DISAGREEING WITH ITSELF, AND THAT IS USABLE

fn7 says continuations the base never entertained are **excluded from the
start**. Section 6 says the distribution **still assigns probability mass to the
unprecedented and the strange**. fn19 says **even if anomalous continuations
retain nonzero probability mass**. The first cannot hold with the other two.

**The friendly amendment is therefore not "you are wrong" but "fn7 is doing no
work for you and costs you fn19."** The fn19 position -- that the bind is
infrastructural and classificatory rather than mathematical -- survives our
measurement intact. fn7 does not, and the essay states its own refutation twice.

### AND THE ONE THING OUR DATA ADDS TO fn19

fn19's vocabulary for what happens to the tail is *inaccessible*, and the
essay's elsewhere is *suppressed*, *discarded*, *narrowed*. None of those has
anywhere to put the mass that leaves. **It does not leave: it relocates**, and
the relocation has a direction that can be named -- which is what this
campaign's displacement work measures. That is an addition to fn19 rather than
an objection to it.
