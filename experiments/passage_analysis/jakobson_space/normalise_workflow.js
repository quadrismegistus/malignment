export const meta = {
  name: 'normalise-human-pool',
  description: 'Orthographic normalisation of the six human corpora, one agent per batch',
  whenToUse: 'After build_human_pool.py and split_pool.py split; pass pending batch names as args',
  phases: [
    { title: 'Normalise', detail: 'one haiku agent per 15-passage batch' },
  ],
}

// The batch list is computed OUTSIDE and passed in, because the script cannot
// touch the filesystem and therefore cannot see which batches already have
// cleaned output. That keeps the pass resumable: re-running with only the
// pending names costs one agent per missing batch instead of the whole run.
// args is either a bare array of batch names, or {batches, model, outDir} so the
// same script can run a model comparison on one batch without the two runs
// writing over each other's output.
// `count: N` expands to batch-000..batch-(N-1) so a 240-batch run does not have
// to ship 240 names through the tool call. An explicit `batches` list still wins,
// which is what a resume uses to re-run only the ones that failed.
let batches = Array.isArray(args) ? args : (args?.batches || [])
if (!batches.length && args?.count) {
  batches = Array.from({ length: args.count }, (_, i) => `batch-${String(i).padStart(3, '0')}`)
}
const MODEL = (Array.isArray(args) ? null : args?.model) || 'haiku'
const OUTDIR = (Array.isArray(args) ? null : args?.outDir) || 'cleaned'
if (!batches.length) {
  log('no batches passed in args; nothing to do')
  return { done: 0 }
}

const SPEC = '/Users/rj416/github/malignment/experiments/passage_analysis/jakobson_space/normalise_spec.md'
const ROOT = '/Users/rj416/malignment-data/jakobson_space'

log(`normalising ${batches.length} batches with ${MODEL} -> ${OUTDIR}/`)

const prompt = (b) => `You are performing orthographic normalisation on human-written text passages for a research corpus.

1. Read the spec at ${SPEC} and follow it exactly.
2. Read the 15 passages in ${ROOT}/batches/${b}.jsonl (JSONL: one object per line, keys \`id\` and \`text\`).
3. Normalise each passage's orthography according to the spec.
4. Write ${ROOT}/${OUTDIR}/${b}.jsonl — JSONL, one object per line (NOT a JSON array), each with keys \`id\`, \`text\`, \`changes\`.

Critical constraints:
- Every input id must appear exactly once in your output, in the same order.
- Passages are cut at a fixed word count and most END MID-SENTENCE. Do not complete them, do not add a trailing period, do not trim back to the last complete sentence.
- Preserve word choice, syntax, grammar errors, dialect and content exactly. Fix only spelling and typography.
- Output length should be within a few words of input length.

Return only the single line: "${b}: N written" where N is the number of objects you wrote.`

// One flat fan-out. There is no second stage to pipeline into: verification is a
// deterministic script over the collated file, not an agent, because a checker
// that is another language model shares the failure mode it is checking for.
const results = await parallel(batches.map((b) => () =>
  agent(prompt(b), { label: `${b}:${MODEL}`, phase: 'Normalise', model: MODEL })
))

const ok = results.filter(Boolean)
log(`${ok.length} of ${batches.length} agents returned`)

return {
  requested: batches.length,
  returned: ok.length,
  failed: batches.filter((b, i) => !results[i]),
}
