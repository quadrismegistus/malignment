export const meta = {
  name: 'interiority-open-coding',
  description: 'Six independent readers propose dimensions on which model continuations of the same prompt differ',
  phases: [{ title: 'Open coding', detail: '6 readers, 32 passages each, no imposed vocabulary' }],
}

const DIR = '/Users/rj416/github/malignment/experiments/interiority_in_passages/results'

const TASK = `You are reading CONTINUATIONS written by language models. Several different
models were each given the same short opening fragment and wrote what came next. Your
batch contains continuations of a few different fragments, several continuations per
fragment.

YOUR TASK IS TO PROPOSE A VOCABULARY, NOT TO APPLY ONE.

Read them and answer: **on what dimensions do continuations of the SAME fragment differ
from one another?** Not how they differ from other fragments' continuations -- within a
fragment, holding the opening constant, what varies?

Propose between 5 and 9 dimensions. For each:
  - a short name
  - what it distinguishes, in one sentence
  - the two or three values it can take
  - a brief quotation from one passage at each end of it

WHAT MAKES A GOOD DIMENSION HERE:
- It must actually VARY in what you read. Do not propose something all the passages
  share, and do not propose something you expect to matter in general.
- It must be judgeable from the passage alone by someone who has not read the others.
- Prefer dimensions you can point at with a quotation over dimensions you can only
  describe.

DO NOT try to work out which model wrote which, or whether some are "better". The
passages are unlabelled and the labels are not the point. You are building a
descriptive vocabulary for a corpus, the way a corpus linguist would.

Some passages break off mid-sentence, repeat themselves, or degenerate. If that
variation is real, it is a legitimate dimension; say so.`

const SCHEMA = {
  type: 'object',
  required: ['dimensions'],
  properties: {
    dimensions: {
      type: 'array',
      items: {
        type: 'object',
        required: ['name', 'distinguishes', 'values'],
        properties: {
          name: { type: 'string' },
          distinguishes: { type: 'string' },
          values: { type: 'array', items: { type: 'string' } },
          example_low: { type: 'string' },
          example_high: { type: 'string' },
        },
      },
    },
    note: { type: 'string', description: 'anything that struck you that the dimensions do not capture' },
  },
}

const RANGES = [[1, 32], [33, 64], [65, 96], [97, 128], [129, 160], [161, 192]]

phase('Open coding')
const R = await parallel(RANGES.map(([lo, hi], i) => () =>
  agent(`${TASK}

Read lines ${lo} to ${hi} of the sample using:
  sed -n '${lo},${hi}p' ${DIR}/openpass.jsonl
Each line is JSON with "id", "prompt" and "continuation".

Do not read any other file in that directory.`,
    { label: `reader-${i}`, phase: 'Open coding', schema: SCHEMA })))

const ok = R.filter(Boolean)
return {
  readers: ok.length,
  total_dimensions: ok.reduce((n, r) => n + (r.dimensions || []).length, 0),
  proposals: ok.map((r, i) => ({ reader: i, dimensions: r.dimensions, note: r.note })),
}
