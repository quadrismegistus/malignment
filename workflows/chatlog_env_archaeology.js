// SAVED COPY. The session-scoped original is deleted with its session.
// Run:  Workflow({scriptPath: 'workflows/chatlog_env_archaeology.js', args: <shards>})
// Then: scripts/mine_diff.py on the findings, which is the half that
// makes this repeatable -- raw mining returns 147 findings of which
// most are already known.
export const meta = {
  name: 'chatlog-env-archaeology',
  description: 'Mine ~/.claude chatlogs per model for environment facts we never recorded systematically',
  phases: [
    { title: 'Mine', detail: '27 agents, ~6 models each, newest-first over the last 10 days' },
    { title: 'Synthesise', detail: 'merge per model, flag contradictions and supersessions' },
  ],
}

const LOGDIR = '/Users/rj416/.claude/projects/-Users-rj416-github-malign-logits'

const SCHEMA = {
  type: 'object',
  required: ['findings', 'models_searched', 'method', 'notes'],
  properties: {
    models_searched: {
      type: 'array',
      description: 'Every model you searched, with the aliases you actually tried and the raw hit count for each. Include models where you found nothing.',
      items: {
        type: 'object',
        required: ['model', 'aliases_tried', 'hits'],
        properties: {
          model: {
            type: 'string',
            description: 'EXACTLY ONE full HuggingFace id, org/name. A finding '
              + 'that covers a pair must be returned TWICE, once per model. '
              + 'Do NOT write "Base / -Chat", "X (and -instruct)" or a '
              + 'comma-separated list: 30 of 50 unresolved findings did that '
              + 'last run, and an unresolved model is indistinguishable from '
              + 'an un-recorded fact, so a parse defect read as 50 missing '
              + 'facts.',
          },
          aliases_tried: { type: 'array', items: { type: 'string' } },
          hits: { type: 'integer' },
        },
      },
    },
    method: { type: 'string', description: 'How you actually searched: the commands/scripts that worked, and anything that did NOT work. Be concrete — the next agent will reuse this.' },
    notes: { type: 'string', description: 'What you could not determine and why. Anything that looked important but you could not verify.' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['model', 'kind', 'statement', 'quote', 'recency'],
        properties: {
          model: { type: 'string' },
          kind: {
            type: 'string',
            enum: ['load_failed', 'run_failed', 'load_ok', 'run_ok', 'blocked',
                   'requirement', 'tokenizer', 'engine', 'dtype', 'kernel',
                   'package', 'perf', 'revision', 'ruling', 'unrecorded',
                   'other'],
            description: 'blocked = THE REPO IS UNUSABLE (404, gated and '
              + 'refused). It is NOT "we never wrote this down" -- six '
              + 'findings last run used it that way and read as NEW against a '
              + 'public repo. Use `unrecorded` for a fact that exists but was '
              + 'never recorded, and `ruling` for a decision RH made.',
          },
          statement: { type: 'string' },
          environment: { type: 'string', description: 'transformers/torch version, device, GPU, docker image, venv — ONLY if the log states it. Empty string otherwise.' },
          cause: { type: 'string' },
          fix: { type: 'string' },
          quote: { type: 'string', description: 'VERBATIM excerpt. Copy actual characters. If you cannot copy it exactly, drop the finding.' },
          recency: { type: 'string', description: 'ISO date from the record timestamp, or "unknown"' },
          superseded: { type: 'boolean' },
          already_recorded: { type: 'string', enum: ['yes', 'no', 'unknown'] },
        },
      },
    },
  },
}

phase('Mine')
log(`mining ${args.length} shards over ${LOGDIR}`)

const prompt = (models, i) => `Mine Claude Code chat transcripts for facts about MODEL RUNTIME ENVIRONMENTS that were discussed but never written into any durable record.

## YOUR MODELS (shard ${i})
${models.map((m) => `  ${m}`).join('\n')}

**Work out the aliases yourself.** People type short names, not full HF ids: "Olmo" or "olmo-7b" for allenai/Olmo-3-1025-7B, "falcon-h1", "zamba", "OLMoE", "tulu-no-safety", "jais", "internlm2", "kanana". Try the org-stripped name, the family stem, lowercase, and any nickname you see used once you start reading hits. Iterate: a first pass will show you what people actually call it.

## WHERE
${LOGDIR}/ — ~300 .jsonl transcripts. The big one, 412328a9-b178-4724-9c75-eca7f1f0e80b.jsonl, is ~433MB and holds most of the material. More under subagents/ and subagents/workflows/.

## RECORD SHAPE (verified, so you do not have to rediscover it)
One JSON object per line. Relevant fields:
  type        'user' | 'assistant' | 'system' | others
  timestamp   ISO8601, present on most records — use it for recency
  message     {role, content}
  message.content   either a plain string, OR a list of blocks:
      {type:'text', text:...}
      {type:'thinking', thinking:...}
      {type:'tool_use', name:..., input:{...}}       <- commands that were RUN
      {type:'tool_result', content:...}              <- their OUTPUT, where
                                                        tracebacks and version
                                                        strings actually live
  toolUseResult  parallel field, often a dict with stdout/stderr

**Tool results are the richest source** — that is where a real traceback, a version string, or an OOM message appears. Do not search only prose.

## METHOD — YOUR CALL, BUT DO IT PROPERLY
Use grep/rg to find WHERE the density is, then stream the file in Python line by line (json.loads per line) to read the surrounding records properly with their role and timestamp. Do not try to load the file into memory, and do not print whole matching lines — a single record can be megabytes. A bare context-window regex will clip facts mid-sentence and lose who said it and when; use it to locate, not to extract.

## PRIORITISE RECENCY
Today is 2026-08-22. The last 10 days (since 2026-08-12) are the target; older material is context. Order files by mtime, and use the per-record \`timestamp\` field to sort what you find — do not assume byte offset equals time.

## WHAT COUNTS AS A FINDING
Anything that belongs in a durable environment record and probably is not in one:
- a transformers or torch VERSION that made it work or fail ("4.57.1 loads it, 5.x cannot")
- device / GPU / card, compute dtype (fp16 vs bf16), kernels (mamba-ssm, causal-conv1d)
- missing PACKAGES (sentencepiece, protobuf, einops) and the exact error
- tokenizer defects: deleted spaces, dropped CJK, wrong converter, loader overrides
- vLLM engine support: architectures removed, which image version works
- repos GONE, GATED, or permanently blocked
- revisions / checkpoint ladders behaving differently
- performance: seconds per cell, load time, OOM at a given VRAM
- anything RH (the human) said that reads as a RULING or a correction

## RULES
1. **quote is VERBATIM.** Copy the characters. If you cannot copy exactly, drop the finding.
2. **environment only if STATED.** Never infer "probably 5.4.0". Empty string when unstated.
3. **Supersession is everywhere in this project.** Claims get corrected days later — "OLMoE histc is MPS-only" became "(MPS x transformers 5)"; "OLMoE is 10-15 s/cell" became "1.9 s/cell, the 3-cell sample measured LOADING". If a later record corrects an earlier one, mark the earlier superseded=true AND record the correction as its own finding. **The later statement wins.**
4. Report models with zero hits in models_searched with hits:0. Absence means you looked, not that nothing happened.
5. **Read-only.** Do not run any model, rent anything, or spend money. Do not edit files outside your own output.

Quality over volume: one precise finding with a real quote and a date beats five vague ones.`

const mined = await pipeline(
  args.map((models, i) => ({ models, i })),
  ({ models, i }) => agent(prompt(models, i), {
    label: `mine:${i}:${models[0].split('/')[1].slice(0, 16)}`,
    phase: 'Mine',
    model: 'sonnet',
    schema: SCHEMA,
  }),
)

const good = mined.filter(Boolean)
const all = good.flatMap((r) => r.findings || [])
const searched = good.flatMap((r) => r.models_searched || [])
log(`${good.length}/${args.length} shards ok; ${all.length} findings; ${searched.filter((s) => !s.hits).length} models with zero hits`)

phase('Synthesise')
const live = all.filter((f) => !f.superseded)
const kinds = {}
for (const f of live) kinds[f.kind] = (kinds[f.kind] || 0) + 1
log(`live ${live.length}, superseded ${all.length - live.length}; kinds ${JSON.stringify(kinds)}`)

const chunks = []
for (let i = 0; i < live.length; i += 80) chunks.push(live.slice(i, i + 80))

const summaries = await parallel(chunks.map((c, i) => () =>
  agent(`Environment findings mined from chat transcripts, as JSON:

${JSON.stringify(c, null, 1)}

Group BY MODEL. For each model, a compact markdown block listing the durable facts, each with its evidence quote trimmed to the essential clause and its date. Explicitly flag any two findings that CONTRADICT each other, and any finding whose \`environment\` is empty but whose statement implies a version — those are the ones that need re-checking before they can be recorded. No preamble. Chunk ${i + 1}/${chunks.length}.`,
    { label: `synth:${i}`, phase: 'Synthesise', model: 'sonnet' })))

return {
  shards_ok: good.length,
  findings_total: all.length,
  findings_live: live.length,
  superseded: all.length - live.length,
  kinds,
  zero_hit_models: searched.filter((s) => !s.hits).map((s) => s.model),
  by_model: summaries.filter(Boolean),
  methods: good.map((r, i) => ({ shard: i, method: r.method })),
  shard_notes: good.map((r, i) => ({ shard: i, notes: r.notes })),
}
