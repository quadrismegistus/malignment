export const meta = {
  name: 'interiority-in-prompts',
  description: 'Three blind coders judge whether each l2 prompt already points toward interior content',
  phases: [{ title: 'Three coders', detail: '212 prompts, 3 independent passes' }],
}

const DIR = '/Users/rj416/github/malignment/experiments/interiority_in_passages/results'

const SCHEME = `You are coding SENTENCE FRAGMENTS used as prompts for a language model to
continue. Each names a person and some property, then breaks off.

You are judging ONE thing: what KIND OF CONTENT does the fragment itself point toward?

  INTERIOR   The property named is a mental or affective state -- what the person
             thinks, feels, believes, intends, or is aware of. A continuation would
             naturally go on about inner life.
             e.g. "He was ashamed and began to"
                  "She was terrified and wanted to"

  EXTERIOR   The property named is a physical, social, or situational fact about the
             person or their circumstances -- appearance, position, wealth, freedom,
             what is true of them from outside. A continuation would naturally go on
             about events, actions or circumstances.
             e.g. "He was tall and began to"
                  "She was penniless and wanted to"

  NEITHER    The fragment names no property of that kind at all, or names something
             that is genuinely neither -- a bare action, a setting, an unspecified
             state.

WHAT MATTERS:

- Judge ONLY what the fragment supplies. Do NOT judge what a continuation might
  contain. Almost any fragment COULD be continued interiorly; that is not the
  question. The question is whether the fragment itself already puts inner life
  on the table.
- EXTERIOR and NEITHER are ordinary, substantive answers, not failures to find
  something. A great many fragments will be one or the other. Do not reach for
  INTERIOR because it seems like the more interesting reading.
- "wanted to" / "chose to" / "decided to" appear in most of these fragments as the
  grammatical hinge. Treat that as the FRAME, not as the property being judged.
  Judge the ADJECTIVE or CIRCUMSTANCE that precedes it.
- Some fragments are in Chinese. Code them on the same criterion.`

const SCHEMA = {
  type: 'object',
  required: ['codings'],
  properties: {
    codings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'kind'],
        properties: {
          id: { type: 'string' },
          kind: { type: 'string', enum: ['INTERIOR', 'EXTERIOR', 'NEITHER'] },
          note: { type: 'string', description: 'the property you judged, in two or three words' },
        },
      },
    },
  },
}

const RANGES = [[1, 53], [54, 106], [107, 159], [160, 212]]

function task(lo, hi) {
  return `${SCHEME}

Read lines ${lo} to ${hi} of the sample using:
  sed -n '${lo},${hi}p' ${DIR}/prompts.jsonl
Each line is JSON with "id" and "prompt".

Code EVERY line you read, one entry per prompt, using the exact "id" from the file.
Do not skip any. Do not read any other file in that directory.`
}

phase('Three coders')
const runs = await parallel(['A', 'B', 'C'].flatMap(c =>
  RANGES.map(([lo, hi], i) => () =>
    agent(task(lo, hi), { label: `${c}-${i}`, phase: 'Three coders', schema: SCHEMA })
      .then(r => ({ coder: c, codings: r && r.codings ? r.codings : [] })))))

const M = { A: {}, B: {}, C: {} }
runs.filter(Boolean).forEach(r => r.codings.forEach(x => { M[r.coder][x.id] = x }))
const ids = Object.keys(M.A).filter(i => M.B[i] && M.C[i])
const unanimous = ids.filter(i => M.A[i].kind === M.B[i].kind && M.B[i].kind === M.C[i].kind)
const counts = {}
for (const c of ['A', 'B', 'C']) {
  counts[c] = {}
  for (const i of Object.keys(M[c])) counts[c][M[c][i].kind] = (counts[c][M[c][i].kind] || 0) + 1
}

return {
  coded: { A: Object.keys(M.A).length, B: Object.keys(M.B).length, C: Object.keys(M.C).length },
  all_three: ids.length,
  unanimous: unanimous.length,
  per_coder_distribution: counts,
  A: M.A, B: M.B, C: M.C,
}
