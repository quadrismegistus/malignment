export const meta = {
  name: 'combined-smoke',
  description: 'Smoke test a merged Pass A+B form: six fields, one narrative question replacing three filter fields',
  phases: [{ title: 'Code', detail: '2 coders x 2 batches, Opus high effort' }],
}

const RUBRIC = `You are reading continuations of a sentence fragment. Each was written by a language model, but that is not what you are judging. Judge the writing.

For each passage return six codes.

## narrative (true / false)

Is this continuous imaginative prose throughout -- a scene or a story, however clumsy -- with nothing interrupting it?

Return false if ANY of the following is true, even for part of the passage:
  - words are mangled or are not words, or sentences do not mean anything
  - it is an essay, article, blog comment, obituary, review, list, Q&A pair,
    quiz item, exercise, or an assistant answering the fragment
  - it carries web or document furniture: a byline, a post date, a comment
    widget, share or like counts, a download link, markup tags, a navigation
    breadcrumb, a section heading that belongs to a document rather than a story
  - it begins as a scene and is then broken by material of any of those kinds

A story that is badly written, implausible, offensive, or ends mid-sentence is still narrative. Clumsiness does not disqualify it; interruption does.

## why (only when narrative is false; otherwise empty string)

    UNREADABLE    mangled words, non-words, or sentences that do not mean anything
    NOT_A_STORY   it is a document of another kind from the start
    INTERRUPTED   it is a scene broken by furniture or by other material

Pick the one that best describes the main reason.

## span

Find the passage's most interior moment -- the place where a character's mind is most present -- and quote it verbatim, at most 25 words, copied exactly from the text. If no character's mental state appears anywhere, return an empty string. Do this even when narrative is false.

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

## drift (HOLDS / SHIFTS / UNMOORED)

Does the passage stay in one world? Ask this even when narrative is false.

    HOLDS      One scene or situation throughout. The people, place and time
               persist, even if the prose is clumsy.
    SHIFTS     Moves to a different situation and stays there. A cut, not a
               collapse: the new material is itself coherent.
    UNMOORED   Serial unrelated material. No situation survives.

This is NOT the same question as \`narrative\`. A passage can be narrative
throughout and still cut from one scene to another, which is SHIFTS. A passage
can fail \`narrative\` for carrying a byline and still HOLD one scene.

## degree (0-3)

How much of the passage is given over to a character's mind?

    0   None of it. Only external event, action, speech, appearance.
    1   A state named once and left there.
    2   Interiority present and developed, but not what the passage is about.
    3   The passage is substantially about a mind.

## Rules

- The mind must belong to a CHARACTER. A first-person narrator who takes part in the scene is a character. A document's author addressing a reader is not: a blog comment, an obituary, a review, an essay expressing the writer's own feelings has no character in it, so mode is NONE and degree is 0 however much feeling it contains.
- Judge the continuation on its own terms, never against the fragment. The fragment may already name a feeling ("She loved him deeply and wanted to"). A state in the continuation that only repeats the fragment's does not count as a span and does not raise the degree. Something must be added.
- Speech is not interiority. A character *saying* "I'm frightened" is an event, not a mind rendered.
- Bodily sensation on its own is not a mental state, unless the passage gives what it is the sensation *of*.
- Search the whole passage, not its opening.

## The passages

The file /Users/rj416/github/malignment/experiments/interiority_in_passages/results/combined_smoke.json holds 60 passages keyed c000 through c059. Read it. Each has a \`fragment\` (the opening the model was given) and a \`continuation\` (what it wrote). Ignore any field beginning with an underscore -- do not look at it, do not let it influence you.

CODE ONLY THE IDS LISTED BELOW. Return every one of them and nothing else.`

const SCHEMA = {
  type: 'object',
  properties: {
    codings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id:        { type: 'string' },
          narrative: { type: 'boolean' },
          why:       { type: 'string', enum: ['', 'UNREADABLE', 'NOT_A_STORY', 'INTERRUPTED'] },
          mode:      { type: 'string', enum: ['NONE', 'TOLD', 'SHOWN'] },
          drift:     { type: 'string', enum: ['HOLDS', 'SHIFTS', 'UNMOORED'] },
          degree:    { type: 'integer', minimum: 0, maximum: 3 },
          span:      { type: 'string' },
        },
        required: ['id', 'narrative', 'why', 'mode', 'drift', 'degree', 'span'],
        additionalProperties: false,
      },
    },
  },
  required: ['codings'],
  additionalProperties: false,
}

const batches = [[], []]
for (let i = 0; i < 60; i++) batches[i < 30 ? 0 : 1].push('c' + String(i).padStart(3, '0'))
log('60 passages, 2 batches of 30, two coders each')

phase('Code')
const jobs = []
for (const coder of ['A', 'B']) {
  batches.forEach((ids, bi) => {
    jobs.push(() => agent(
      `${RUBRIC}\n\nIDS TO CODE (${ids.length}): ${ids.join(', ')}`,
      { label: `coder${coder}:batch${bi}`, phase: 'Code', schema: SCHEMA, effort: 'high' }
    ).then(r => ({ coder, rows: (r && r.codings) || [] })))
  })
}
const done = (await parallel(jobs)).filter(Boolean)
const out = { A: {}, B: {} }
for (const d of done) for (const r of d.rows) {
  out[d.coder][r.id] = { narrative: r.narrative, why: r.why, mode: r.mode, drift: r.drift, degree: r.degree, span: r.span }
}
const ids = Object.keys(out.A).filter(i => i in out.B).sort()
const agree = {}
for (const f of ['narrative', 'why', 'mode', 'drift', 'degree']) {
  agree[f] = ids.filter(i => out.A[i][f] === out.B[i][f]).length
}
log(`both=${ids.length} | narrative ${agree.narrative} mode ${agree.mode} drift ${agree.drift} degree ${agree.degree} why ${agree.why}`)
return { coded: { A: Object.keys(out.A).length, B: Object.keys(out.B).length }, both: ids.length, agree, A: out.A, B: out.B }
