export const meta = {
  name: 'passb-pilot',
  description: 'Two blind coders judge 190 narrative passages on interiority mode, degree and drift',
  phases: [{ title: 'Code', detail: '2 coders x 4 batches, Opus high effort' }],
}

const RUBRIC = `You are reading continuations of a sentence fragment. Each was written by a language model, but that is not what you are judging. Judge the writing.

For each passage return four codes.

## span

Find the passage's most interior moment -- the place where a character's mind is most present -- and quote it verbatim, at most 25 words, copied exactly from the text. If no character's mental state appears anywhere, return an empty string.

## mode (NONE / TOLD / SHOWN)

Classify THE SPAN YOU QUOTED, not the whole passage.

    NONE    There was no span. No character's mental state appears anywhere:
            only what a camera would record -- actions, speech, appearances,
            events, facts.

    TOLD    The state is REPORTED. Named, asserted or summarised from outside.
            The reader is informed what the character feels or knows.
            "She was furious."  "He knew he had to talk to her."
            "She loves the process of creating."

    SHOWN   The state is RENDERED. The mind is given in motion rather than
            summarised -- thought as it occurs, deliberation, a question in the
            character's own idiom.
            "Was it possible he had never meant it?"
            "She told herself that she had fixed him. She'd known all along that
             love inside hate was no love at all."

If the span contains both, classify by what the span is mainly doing.

## degree (0-3)

Separately, how much of the passage is given over to a character's mind?

    0   None of it. Only external event, action, speech, appearance.
    1   A state named once and left there.
    2   Interiority present and developed, but not what the passage is about.
    3   The passage is substantially about a mind.

## drift (HOLDS / SHIFTS / UNMOORED)

Does the passage stay in one world?

    HOLDS      One scene or situation throughout. The people, place and time
               persist, even if the prose is clumsy.
    SHIFTS     Moves to a different situation and stays there. A cut, not a
               collapse: the new material is itself coherent.
    UNMOORED   Serial unrelated material. No situation survives.

This is not about whether the prose is good or the sentences parse. A badly written passage that stays in one scene HOLDS. A well-written passage that becomes an unrelated news report SHIFTS.

## Rules

- The mind must belong to a CHARACTER. A first-person narrator who takes part in the scene is a character. A document's author addressing a reader is not: a blog comment, an obituary, a review, an essay expressing the writer's own feelings has no character in it, so mode is NONE and degree is 0 however much feeling it contains.
- Judge the continuation on its own terms, never against the fragment. The fragment may already name a feeling ("She loved him deeply and wanted to"). A state in the continuation that only repeats the fragment's does not count as a span and does not raise the degree. Something must be added.
- Speech is not interiority. A character *saying* "I'm frightened" is an event, not a mind rendered.
- Bodily sensation on its own is not a mental state, unless the passage gives what it is the sensation *of*.
- Search the whole passage, not its opening.

## The passages

The file /Users/rj416/github/malignment/experiments/interiority_in_passages/results/passB_pilot.json holds 190 passages keyed b000 through b189. Read it. Each has a \`fragment\` (the opening the model was given) and a \`continuation\` (what it wrote). Ignore any field beginning with an underscore -- do not look at it, do not let it influence you.

CODE ONLY THE IDS LISTED BELOW. Return every one of them and nothing else.`

const SCHEMA = {
  type: 'object',
  properties: {
    codings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id:     { type: 'string' },
          mode:   { type: 'string', enum: ['NONE', 'TOLD', 'SHOWN'] },
          degree: { type: 'integer', minimum: 0, maximum: 3 },
          drift:  { type: 'string', enum: ['HOLDS', 'SHIFTS', 'UNMOORED'] },
          span:   { type: 'string' },
        },
        required: ['id', 'mode', 'degree', 'drift', 'span'],
        additionalProperties: false,
      },
    },
  },
  required: ['codings'],
  additionalProperties: false,
}

const N = 190
const BATCH = 48
const batches = []
for (let s = 0; s < N; s += BATCH) {
  const ids = []
  for (let i = s; i < Math.min(s + BATCH, N); i++) ids.push('b' + String(i).padStart(3, '0'))
  batches.push(ids)
}
log(`190 passages in ${batches.length} batches of <=${BATCH}, two coders each`)

phase('Code')
const jobs = []
for (const coder of ['A', 'B']) {
  batches.forEach((ids, bi) => {
    jobs.push(() => agent(
      `${RUBRIC}\n\nIDS TO CODE (${ids.length}): ${ids.join(', ')}`,
      { label: `coder${coder}:batch${bi}`, phase: 'Code', schema: SCHEMA, effort: 'high' }
    ).then(r => ({ coder, bi, rows: (r && r.codings) || [] })))
  })
}
const done = (await parallel(jobs)).filter(Boolean)

const out = { A: {}, B: {} }
const seen = { A: 0, B: 0 }
for (const d of done) {
  for (const r of d.rows) {
    out[d.coder][r.id] = { mode: r.mode, degree: r.degree, drift: r.drift, span: r.span }
    seen[d.coder]++
  }
}
const ids = Object.keys(out.A).filter(i => i in out.B).sort()
const agree = { mode: 0, degree: 0, drift: 0, within1: 0 }
for (const i of ids) {
  if (out.A[i].mode === out.B[i].mode) agree.mode++
  if (out.A[i].degree === out.B[i].degree) agree.degree++
  if (out.A[i].drift === out.B[i].drift) agree.drift++
  if (Math.abs(out.A[i].degree - out.B[i].degree) <= 1) agree.within1++
}
log(`coded A=${seen.A} B=${seen.B}, both=${ids.length} | mode ${agree.mode}/${ids.length} degree ${agree.degree}/${ids.length} drift ${agree.drift}/${ids.length}`)
return { coded: seen, both: ids.length, batches_returned: done.length, agree, A: out.A, B: out.B }
