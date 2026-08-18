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
| `prompt_openness` | which of the 482 generated prompts leave the event to be invented and which name it. Two blind coders, agreement 0.909. Says nothing about what alignment does; it partitions the substrate any scene-kind question has to run on. | **BUILT**, `wf_1468cab2-4b6`; the subject-matter independence check is BORDERLINE (p=0.067) and is reported as partial leakage, not a pass |

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
