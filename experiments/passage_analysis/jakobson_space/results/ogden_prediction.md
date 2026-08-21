# Registered before the scoring finished

Both predictions written 2026-08-21 while `ogden_axes.py` was still running, and
before either of us had seen a number. RH proposed first; lacan's reasoning is
below rather than a restatement of it.

## RH: lower drift, HIGHER surprise

## lacan: agree on both, with different confidence

**SURPRISAL HIGHER -- moderately confident, and it is the counter-intuitive one.**
The naive read is that simplification lowers surprisal: an 850-word vocabulary
means commoner words, and commoner words are more probable. That is true of the
words and false of the sentences. Ogden's constraint does not let the editor
choose a plain synonym; where no Basic word exists it forces CIRCUMLOCUTION, and
a circumlocution is a common-word sequence in an uncommon arrangement. The
observed substitutions already show it:

    "passed on the stairs"      ->  "went through on the flight of steps"
    "that kitty"                ->  "that young cat"
    "the padrone asked me"      ->  "the padrone requested me"

`young cat` is two frequent words in a bigram English almost never uses;
`requested` is RARER than the `asked` it replaces. Surprisal is per token in
context, so a model that expects the idiomatic continuation and receives a
paraphrase pays for it. Prediction: the arrangement effect beats the vocabulary
effect.

**DRIFT LOWER -- weakly confident, and it may be mostly mechanical.** Both sides
say the same things in the same order, so the semantic trajectory is nearly
fixed by construction. What differs is that Basic takes MORE words to cover the
same ground (45 of 47 groups), which if it also means more sentences puts more
steps across an unchanged path, and `mean_drift` is a per-step mean. Smaller
steps over the same distance. That is an argument about sentence count, not
about style, so I would not read a small negative as evidence of anything
stylistic without `n_sents` beside it -- which is why it is in the table.

## WHAT EITHER OUTCOME WOULD MEAN

The alignment step is **-0.8435 surprisal, -0.0254 drift** (22 lineages).

  * If simplification also lowers surprisal, alignment resembles a named human
    editorial operation and the two directions can be compared as one kind.
  * **If simplification RAISES surprisal, the two point opposite ways on that
    axis**, and alignment lowers surprisal WITHOUT being simplification in
    Ogden's sense. That is the outcome both of us predicted, and it is the more
    interesting one: it would mean the thing alignment does to predictability is
    not what an editor does when deliberately restricting vocabulary.

Registering that we expect the second, so it cannot later be told as a surprise.

## The fence

47 groups from three stories by three authors: the effective n is nearer 3 than
47. Neither prediction is quantitative and neither should be scored as though it
were -- the sign is the claim.
