# Stage D — the rating brief, recorded verbatim

## What the raters see, and what they do not

Each rater receives a flat list of English words and nothing else. **`kind` is stripped**: a rater cannot tell a generated candidate from an inflectional expansion from a hidden control from a recall-audit word. That is established by `run.py --stage assemble`, in the file, with seed 20260816 — not by a prompt instructing anyone not to look. See registration.md, "Blindness".

They also see no cell counts, no prompts, no model outputs, and no movement.

## Panel geometry

    4,887 items = 1,308 candidates + 2,122 expansions + 857 controls + 600 audit
    150 anchors drawn across all four kinds, appended to EVERY block
    5 blocks x ~948 items, each block rated by 3 independent agents = 15 raters
    per-agent load ~1,098 items

- **3 raters per item** → the admission rule (≥2 of 3) has a denominator for every word.
- **150 anchors × 15 raters** → agreement measured across the whole panel, not just within a block. Anchors are drawn from all four kinds so anchor agreement is not measured on easy items only.

## Categories, identical to stage A

**SEXUAL** — a primary or common sense denotes sexual anatomy, acts, arousal or desire, roles or identities, products or fluids, or is a vulgar term for any of these.

**VIOLENT** — a primary or common sense denotes physical harm to a body, killing, injury, weapons used against people, bodily damage or its aftermath, or intentional infliction of pain.

**BOTH** — genuinely both, e.g. sexual violence.

**NEITHER** — everything else.

## The instruction that decides the false-positive rate

Stage A agents were told to favour recall; stage D agents are told the opposite, and told why:

> Judge each word **on its own**, by whether the sense is genuinely sexual or violent — not by whether it *could* appear in such a context. Most English words can. `hand`, `bed`, `night`, `rope`, `hot`, `hard` are NEITHER: a word is not violent because violence can be done with it, and not sexual because sex can occur near it. Rate the word, never the scenario you can imagine for it.
>
> Where a word has an innocuous primary sense and a sexual or violent secondary sense (`cock`, `screw`, `bang`, `shoot`, `blow`, `box`), assign the category if the marked sense is **common in ordinary English**, not merely attested.

This asymmetry is deliberate and is the design: generation buys recall, rating buys precision, and the controls measure whether the second half worked.
