---
kind: subject
status: "OPEN, created 2026-08-16"
headline: "Registrations for things that CANNOT FAIL."
---
# instrument_calibrations/

**Registrations for things that CANNOT FAIL.** An instrument registration
declares how something is BUILT — population, gates, construction rules — so the
construction is arguable and reproducible. A hypothesis registration declares
what would make a claim wrong. Mixing them puts a row in the hypothesis register
that no result can violate, which is the shape that lets a null read as a finding.

`experiments/README.md` already drew this line in prose — *"`sex_violence_lexicon`
appears nowhere in this table on purpose: it registers no hypothesis"* — and had
nowhere to put it. RH, 2026-08-16.

**This container was created with two occupants, not empty**, per the layout
rule: *"a container that exists before its contents will be filled by whatever is
nearby."* It is a CLASS axis, not the `<subject>/<question>` axis.

| directory | what it is | status |
|---|---|---|
| `sex_violence_lexicon` | the 1,063-word blind-rated lexicon. Five construction rules, one admission gate. Says nothing about what alignment does. | **ADMITTED**, sha `d542e7e2bb86bd00` |
| `displacement_reference` | how far training moves a model, per phase, per token — the *compared to what* the project never had | **BUILT** |
| `prompt_openness` | which of the 482 generated prompts leave the event to be invented and which name it. Two blind coders, agreement 0.909. Says nothing about what alignment does; it partitions the substrate any scene-kind question has to run on. | **BUILT**; 666 of 679 prompts resolved by two coders plus an anchored third on all 68 ties. **The subject-matter independence check FAILS at p=0.042, and the design cannot say whether that is coder leakage or transgressive prompts genuinely narrowing the continuation.** Any use conditioning on `pair_role` inherits it |
| `story_decoder` | which decoder and frame let BOTH arms write a story. Fixes `t=1.0/p=0.95` for `national_story`. Moved here from top level 2026-09-02. **Unlike everything else in this table it DOES say something about what alignment does** -- see the note below | **RUN**, 160 generations, docket [6576] |
| `mps_sampling` | MPS samples tokens the filter forbade, at ~1/400 per draw, and only when the distribution contains exact zeros. Sets a hard constraint every generation experiment inherits. Moved here from top level 2026-09-02, and given the README it never had | **RUN**; `top_k`/`min_p`, the published MPS-safe workarounds, measured and NOT safe |

## `story_decoder` is the one member that makes a claim about alignment

The rest of this table earns its place by saying nothing about what alignment
does -- that is the whole criterion, and `prompt_openness`'s entry states it
outright. `story_decoder` does not meet it. Its headline is **the two arms want
opposite decoders**: base loops below `t=1.0`, aligned turns to salad at
`p=1.0`, so `t=1.0/p=0.95` is a compromise and not an optimum, and it is still
the worse setting for the aligned arm considered alone. That is a finding about
what alignment does to the shape of the distribution, not a construction rule.

It is filed here anyway, on the other half of the criterion: it registers no
hypothesis, has no row in the hypothesis register, and would not want one. Its
function is to fix a parameter for another experiment.

**Recorded rather than smoothed over**, because the cheap thing would have been
to let it inherit the container's blanket disclaimer, and then the one entry
that carries an arm result would be the one entry a reader was told to ignore.

## Candidates, not yet built

Same kind, currently living as constants in code or sentences in a docket post,
where nobody can check how they were derived:

- **the slot instrument's gates** — `LEV_MOVER 0.1027`, `LEV_DEAD 0.0694`,
  `PURITY_FLOOR`, declared in `slot_axis.py`. A threshold read off a sorted
  excerpt is not a threshold read off a distribution, and that cost two wrong
  answers.
- **the pooled slot axis** — `||G|| = 0.388` over 61 items against a
  `1/sqrt(n) = 0.128` null. It decides whether a pooled mean `dN` means
  anything, and it exists only in a docket post.
- **the stimulus noise floor** — a nonsense word moves the measure 25x.
- **twp conservation** — per-word JS terms sum to `js_total - js_tail` at ~1e-17.
