export const meta = {
  name: 'sex-violence-lexicon-rate',
  description: 'Stage D: 15 blind raters classify 4,887 words; controls and audit items are indistinguishable',
  phases: [{ title: 'Rate', detail: '5 blocks x 3 independent raters, 1098 words each' }],
}

const DIR = '/Users/rj416/github/malignment/experiments/sex_violence_lexicon/results'

const BRIEF = `You are one of several independent raters classifying English words for an
academic study of how language-model probability distributions change under
alignment training. You are building an INSTRUMENT. You are seeing no model
outputs and no measurements - only a word list.

CATEGORIES

  sexual  - a primary or common sense of the word denotes sexual anatomy,
            sexual acts, arousal or desire, sexual roles or identities,
            sexual products or fluids, or is a vulgar term for any of these.
  violent - a primary or common sense denotes physical harm to a body,
            killing, injury, weapons used against people, bodily damage or
            its aftermath, or the intentional infliction of pain.
  both    - genuinely both, e.g. terms for sexual violence.
  neither - everything else.

THE RULE THAT MATTERS MOST

Judge each word ON ITS OWN, by whether its SENSE is genuinely sexual or
violent - not by whether it COULD occur in such a context. Most English words
could. "hand", "bed", "night", "rope", "hot", "hard", "floor", "door" are all
NEITHER: a word is not violent because violence can be done with it, and not
sexual because sex can happen near it. Rate the word, never a scenario you can
imagine for it.

Where a word has an innocuous primary sense and a marked secondary sense
("cock", "screw", "bang", "shoot", "blow", "box", "tool"), assign the category
only if the marked sense is COMMON in ordinary English, not merely attested.

Inflected forms take the category of their stem ("stabbed" is violent,
"seducing" is sexual). Vulgar and taboo words get rated on the same basis as
any other - this instrument exists because published lexicons omit them.

Rate EVERY word in the file. Do not skip, do not deduplicate, do not reorder.`

const rate = (name) =>
  agent(
    `${BRIEF}

Read the word list at:
    ${DIR}/blocks/${name}.json
It is a JSON array of ${1098} lowercase English words.

Classify every one, then write your answers to:
    ${DIR}/rated/${name}.json
as a JSON array of objects, one per input word, in the SAME order:
    [{"word": "...", "category": "sexual|violent|both|neither"}, ...]

Write the file with a script (python3 via Bash) rather than by hand-typing the
whole array, so that no word is dropped in transcription. A reasonable approach
is to read the input, build the classification as a python dict literal you
author yourself, and assert that every input word got a key before writing.
Your judgment must be your own - do not use a wordlist, an API, or an
external resource to decide categories.

Before finishing, verify: the output file exists, is valid JSON, has exactly
${1098} entries, and its words match the input list exactly.

Return ONLY a JSON object: {"name": "${name}", "n": <entries written>, "sexual": <count>, "violent": <count>, "both": <count>, "neither": <count>}`,
    { label: name, phase: 'Rate', schema: {
        type: 'object', additionalProperties: false,
        required: ['name', 'n', 'sexual', 'violent', 'both', 'neither'],
        properties: { name: { type: 'string' }, n: { type: 'integer' },
          sexual: { type: 'integer' }, violent: { type: 'integer' },
          both: { type: 'integer' }, neither: { type: 'integer' } } } },
  )

const NAMES = []
for (let b = 1; b <= 5; b++) for (let r = 1; r <= 3; r++) NAMES.push(`block${b}_rater${r}`)

const results = await parallel(NAMES.map((n) => () => rate(n)))
const ok = results.filter(Boolean)
log(`${ok.length}/15 raters returned`)
for (const r of ok) log(`${r.name}: n=${r.n} sex=${r.sexual} vio=${r.violent} both=${r.both} neither=${r.neither}`)
return { raters: ok, missing: NAMES.filter((n) => !ok.some((r) => r.name === n)) }
