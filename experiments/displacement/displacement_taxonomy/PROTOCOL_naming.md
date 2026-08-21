# Naming constructs: direction is an attribute, not an identity

Proposed 2026-08-19 with RH, who put the problem sharply: `GENITALS__TO__OTHER_BODY_PARTS` and `OTHER_BODY_PARTS__TO__GENITALS` are precise, and they are frame-specific, and abstracting them needs another pass.

## The case that forces the decision

Two lineages, one frame, one instrument, opposite directions:

    Llama-3.1-8B -> Instruct     explicit mass 47.8% -> 0.6%   top word cock -> beard
      A: cock, penis, dick        B: beard, chin, hair, cat

    SmolLM3-3B-Base -> SmolLM3   explicit mass 71.9% -> 80.5%  top word cock -> cock
      A: hand, fingers            B: cock, meat, penis, rod, prick

Across the stroking frame that is 14 lineages down, 6 flat, 10 up. **If direction is part of the construct's name these are two constructs; if direction is a field they are one construct with two polarities.** Everything else follows from that choice.

They should be one. The operation is identical -- the referent of the gesture is replaced -- and it is the same operation whichever way it runs. Splitting on direction would report the count of lineages performing referent substitution as two smaller numbers and hide that the polarity varies, which IS the finding.

This is the figure-title rule arriving from another direction: **name the relation, not the instances.** A construct pinned to a direction is pinned to a fact about which lineages we happen to have.

## The proposal: three fields, two vocabularies, one of them controlled

    operation    REFERENT_SUBSTITUTION       controlled, frame-general
    from_pole    genitals                    free text, frame-specific
    to_pole      facial-hair grooming        free text, frame-specific
    polarity     toward_B                    which arm the operation runs toward

A construct is a set of relations sharing an `operation`. Poles vary within it. `polarity` is recorded per relation and never enters the construct's identity.

`GENITALS__TO__OTHER_BODY_PARTS` is then a POLE PAIR, one instance of `REFERENT_SUBSTITUTION`, and its mirror is the same construct at the other polarity. RH's format survives; it just names a level below the construct.

**Only `operation` needs to be controlled.** The poles are irreducibly frame-specific and harmonising them is a separate, later, optional pass -- valuable if we ever want to ask whether the same pole pair recurs across frames, worthless for the question the taxonomy exists to answer. Do not build it until something needs it.

## What this makes askable

    how many lineages perform REFERENT_SUBSTITUTION, and what is the
    polarity distribution?          -> 14 down, 6 flat, 10 up, one number

That question is not statable at all if direction is in the name.

## Open, and the current run should answer it

**The grain is not settled.** If `REFERENT_SUBSTITUTION` covers both `genitals -> grooming` and `hand -> genitals`, it may be too coarse to be useful. The instrument already forces a topic audit and a `nearest` justification per construct, so the harmonisers are being asked to draw exactly this boundary -- and three of them are drawing it independently. **Wait for what grain they choose before fixing one.** A grain imposed now is a preference; a grain three blind agents converge on is a finding.

Two things to look for in their output:

- **A construct whose definition names a DIRECTION** (`genitals give way to grooming`) will fit half the lineages and miss the other half. A definition naming the OPERATION (`the referent of the gesture is replaced`) covers both. The instrument already asks for definitions that do not mention subject matter; whether it got them is a check to run.
- **A construct that is really a pole pair** -- members all sharing one frame -- is what the topic audit is for. If the audit catches it, the defence worked; if we catch it and the audit did not, the audit needs strengthening before the sharded version.

## If adopted

The schema gains `polarity` per relation and `operation` replaces `name` as the identity. That is a change to `INSTRUMENT_harmonise.md`, so it gets a new version and a new sha, and the constructs derived under h1 stay reachable under theirs.
