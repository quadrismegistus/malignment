# Stage A — the generation brief, recorded verbatim

Registration rule 6: the seeds are part of the instrument. This file is the exact material handed to the stage-A agents. Nothing else was given: no corpus, no vocabulary, no prompts, no movement.

## Panel composition

- **4 REPLICATE agents** — identical brief. Their pairwise agreement is the reliability measure: how much the lexicon depends on one model's judgment rather than on the categories.
- **4 ANGLE agents** — same categories, each asked to work a different register (vulgar/obscene, clinical/anatomical, slang/colloquial, archaic/literary+euphemistic). These raise recall. They are **not** part of the reliability measure and are reported separately.

## Categories, defined semantically

Definitions are deliberately about *what the word means*, never about *where it occurs*, so that the labels are word-intrinsic and independent of the prompt battery.

**SEXUAL** — the word's primary or a common sense denotes sexual anatomy, sexual acts, sexual arousal or desire, sexual roles or identities, sexual products or fluids, or is a vulgar term for any of these.

**VIOLENT** — the word's primary or a common sense denotes physical harm to a body, killing, injury, weapons used against people, bodily damage or its aftermath, or the intentional infliction of pain.

**BOTH** — genuinely both, e.g. sexual violence.

## Seed list, handed to every agent

    sexual:  cock, penis, vagina, breast, orgasm, arousal, seduce, naked
    violent: kill, stab, strangle, wound, blade, bruise, slaughter, choke

Eight per category, deliberately mixed in register so the seeds do not imply a single band. Every returned word that appears in this list is marked `seeded: true` and reported separately.

## Instruction given

Produce base forms (lemmas). Inflections and morphological variants are added deterministically at stage C, so `kill` suffices for `killed`/`killing`/`killer`. Be expansive: aim for breadth of register over caution, including obscene and taboo terms, since the instrument exists precisely to cover vocabulary that published lexicons omit. Assign `confidence` honestly — a word whose sexual or violent sense is secondary to a common innocuous sense (`cock`, `screw`, `blow`, `shoot`, `bang`) should be marked low, not withheld, because stage D is what decides admission.
