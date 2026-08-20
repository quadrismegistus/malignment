export const meta = {
  name: 'passA-instrument-pilot',
  description: 'Two blind coders judge 880 passages on lexical integrity, semantic integrity, repetition and frame irruption',
  phases: [
    { title: 'Coder A', detail: '22 batches of 40' },
    { title: 'Coder B', detail: 'independent second pass' },
  ],
}

const DIR = '/Users/rj416/github/malignment/experiments/interiority_in_passages/results'

const SCHEME = `You are reading CONTINUATIONS written by language models. Each was given a short
opening fragment and wrote what came next. The opening is shown for context.

**You are judging whether the text WORKS, not what it says.** Four independent judgments per
passage. Do not let one decide another: a passage can be perfectly lexical and total nonsense,
or word-salad without ever leaving the frame.

## 1. lexical — are the words real words?

  clean      every word is a real word (proper nouns and coinages that read as names are fine)
  mangled    occasional broken or fused forms, a handful
  nonwords   bursts of character-salad
             e.g. "she couldn't put her hands on the reason why, quite tlsxljsdoprhkowntright"
                  "one severely crispy and somewhat shrunken 15-inch double-wekforfda"

## 2. semantic — do the sentences mean anything?

  means      the sentences say things that could be true or false of some world
  stalls     GRAMMATICAL BUT MEANING STOPS ACCUMULATING -- clauses parse, reference does not
             e.g. "Only recently had she inserted the testicles that are common to the
                   male ChirimoDonkey" -- syntactically clean, referentially impossible
  salad      no propositional content recoverable
             e.g. "The agiarged achotic rverteen accumulating exemplifier blinds kept se
                   ringing, shrieked stopped or some apree substantial po crushing"

**A passage can be clean on words and salad on meaning, or mangled on words and means on
meaning. Judge them separately.**

## 3. repetition — does it loop?

  none       no repetition beyond ordinary prose
  phrase     a phrase or sentence frame restated several times
             e.g. thirteen sentences each built to contain the same word
  block      a verbatim block of its own earlier text reproduced

## 4. frame — does non-narrative apparatus irrupt?

  none       continuous prose throughout
  furniture  web/document paratext: bylines, post dates, ADVERTISEMENT, "Incoming search
             terms:", HTML tags, thread ids like ">> No.1658370", "A/N:", download links
  task       exercise or dataset format: "Options: - army - war - prison", cloze blanks,
             "Let's think step by step", "Answer:", multiple choice, translation pairs
  assistant  an assistant or chat frame: "<human>:", "You are an AI assistant",
             "It's important to note that...", a helpful respondent addressing a user

If more than one kind irrupts, record the FIRST one that appears.

## RULES

- Judge only the CONTINUATION. The opening is context and is never itself a fault.
- Passages are cut at a length cap, so most end mid-sentence. **That is not a fault and is
  not repetition, salad, or a frame break.**
- The values "none" and "clean" are the majority answers and are ordinary. Do not hunt for
  faults.
- Do not guess which model wrote what, or whether some are better. They are not groups.`

const SCHEMA = {
  type: 'object',
  required: ['codings'],
  properties: {
    codings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'lexical', 'semantic', 'repetition', 'frame'],
        properties: {
          id: { type: 'string' },
          lexical: { type: 'string', enum: ['clean', 'mangled', 'nonwords'] },
          semantic: { type: 'string', enum: ['means', 'stalls', 'salad'] },
          repetition: { type: 'string', enum: ['none', 'phrase', 'block'] },
          frame: { type: 'string', enum: ['none', 'furniture', 'task', 'assistant'] },
          note: { type: 'string', description: 'only if something is odd, a few words' },
        },
      },
    },
  },
}

const RANGES = []
for (let lo = 1; lo <= 880; lo += 40) RANGES.push([lo, Math.min(lo + 39, 880)])

function task(lo, hi) {
  return `${SCHEME}

Read lines ${lo} to ${hi} of the sample using:
  sed -n '${lo},${hi}p' ${DIR}/passA.jsonl
Each line is JSON with "id", "opening" and "continuation".

Code EVERY line you read, one entry per passage, using the exact "id" from the file.
Do not skip any. Do not read any other file in that directory.`
}

phase('Coder A')
const A = await parallel(RANGES.map(([lo, hi], i) => () =>
  agent(task(lo, hi), { label: `A-${i}`, phase: 'Coder A', schema: SCHEMA })))

phase('Coder B')
const B = await parallel(RANGES.map(([lo, hi], i) => () =>
  agent(task(lo, hi), { label: `B-${i}`, phase: 'Coder B', schema: SCHEMA })))

const flat = r => r.filter(Boolean).flatMap(x => x.codings || [])
const mA = {}, mB = {}
flat(A).forEach(x => { mA[x.id] = x })
flat(B).forEach(x => { mB[x.id] = x })
const both = Object.keys(mA).filter(i => mB[i])
const agree = {}
for (const f of ['lexical', 'semantic', 'repetition', 'frame']) {
  agree[f] = both.filter(i => mA[i][f] === mB[i][f]).length
}
return {
  coded: { A: Object.keys(mA).length, B: Object.keys(mB).length },
  both: both.length,
  batches_ok: { A: A.filter(Boolean).length, B: B.filter(Boolean).length },
  agreement: agree,
  A: mA, B: mB,
}
