// GENERATED. 16 blind judgments: 8 cells x 2 orderings, readings unlabelled.
export const meta = {
  name: 'judge-readings',
  description: 'Blind evaluation of unbatched-Opus vs batched-Sonnet readings',
  phases: [{ title: 'Judge', detail: 'counterbalanced, one judge per prompt' }],
}
const JOBS = [
  {
    "cell": "stroking__AmberSafe",
    "order": "opus_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_stroking__AmberSafe_opus_first.txt",
    "reading_one": "opus/unbatched"
  },
  {
    "cell": "stroking__AmberSafe",
    "order": "sonnet_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_stroking__AmberSafe_sonnet_first.txt",
    "reading_one": "sonnet/xhigh"
  },
  {
    "cell": "stroking__Baichuan2-7B-Chat",
    "order": "opus_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_stroking__Baichuan2-7B-Chat_opus_first.txt",
    "reading_one": "opus/unbatched"
  },
  {
    "cell": "stroking__Baichuan2-7B-Chat",
    "order": "sonnet_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_stroking__Baichuan2-7B-Chat_sonnet_first.txt",
    "reading_one": "sonnet/xhigh"
  },
  {
    "cell": "stroking__Llama-3.1-8B-Instruct",
    "order": "opus_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_stroking__Llama-3.1-8B-Instruct_opus_first.txt",
    "reading_one": "opus/unbatched"
  },
  {
    "cell": "stroking__Llama-3.1-8B-Instruct",
    "order": "sonnet_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_stroking__Llama-3.1-8B-Instruct_sonnet_first.txt",
    "reading_one": "sonnet/xhigh"
  },
  {
    "cell": "union__AmberSafe",
    "order": "opus_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_union__AmberSafe_opus_first.txt",
    "reading_one": "opus/unbatched"
  },
  {
    "cell": "union__AmberSafe",
    "order": "sonnet_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_union__AmberSafe_sonnet_first.txt",
    "reading_one": "sonnet/xhigh"
  },
  {
    "cell": "union__Baichuan2-7B-Chat",
    "order": "opus_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_union__Baichuan2-7B-Chat_opus_first.txt",
    "reading_one": "opus/unbatched"
  },
  {
    "cell": "union__Baichuan2-7B-Chat",
    "order": "sonnet_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_union__Baichuan2-7B-Chat_sonnet_first.txt",
    "reading_one": "sonnet/xhigh"
  },
  {
    "cell": "union__Llama-3.1-8B-Instruct",
    "order": "opus_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_union__Llama-3.1-8B-Instruct_opus_first.txt",
    "reading_one": "opus/unbatched"
  },
  {
    "cell": "union__Llama-3.1-8B-Instruct",
    "order": "sonnet_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_union__Llama-3.1-8B-Instruct_sonnet_first.txt",
    "reading_one": "sonnet/xhigh"
  },
  {
    "cell": "unzipped__AmberSafe",
    "order": "opus_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_unzipped__AmberSafe_opus_first.txt",
    "reading_one": "opus/unbatched"
  },
  {
    "cell": "unzipped__AmberSafe",
    "order": "sonnet_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_unzipped__AmberSafe_sonnet_first.txt",
    "reading_one": "sonnet/xhigh"
  },
  {
    "cell": "pal_affect__AmberSafe",
    "order": "opus_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_pal_affect__AmberSafe_opus_first.txt",
    "reading_one": "opus/unbatched"
  },
  {
    "cell": "pal_affect__AmberSafe",
    "order": "sonnet_first",
    "path": "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/judge_pal_affect__AmberSafe_sonnet_first.txt",
    "reading_one": "sonnet/xhigh"
  }
]
const SCHEMA = {
  "additionalProperties": false,
  "properties": {
    "better": {
      "enum": [
        "one",
        "two",
        "equivalent"
      ],
      "type": "string"
    },
    "confidence": {
      "enum": [
        "high",
        "medium",
        "low"
      ],
      "type": "string"
    },
    "missed": {
      "type": "string"
    },
    "reading_one": {
      "additionalProperties": false,
      "properties": {
        "n_over_read": {
          "type": "integer"
        },
        "n_supported": {
          "type": "integer"
        },
        "one_sided": {
          "type": "integer"
        },
        "weakest": {
          "type": "string"
        }
      },
      "required": [
        "n_supported",
        "n_over_read",
        "weakest"
      ],
      "type": "object"
    },
    "reading_two": {
      "additionalProperties": false,
      "properties": {
        "n_over_read": {
          "type": "integer"
        },
        "n_supported": {
          "type": "integer"
        },
        "one_sided": {
          "type": "integer"
        },
        "weakest": {
          "type": "string"
        }
      },
      "required": [
        "n_supported",
        "n_over_read",
        "weakest"
      ],
      "type": "object"
    },
    "why": {
      "type": "string"
    }
  },
  "required": [
    "reading_one",
    "reading_two",
    "missed",
    "better",
    "confidence"
  ],
  "type": "object"
}
const out = await parallel(JOBS.map((j) => () =>
  agent(
    `Read the file ${j.path} with the Read tool.\n\n` +
    `Its entire content is a task addressed to you. Follow it exactly and answer ` +
    `every numbered question in it. Do not read any other file, do not run any ` +
    `command, and do not look for context beyond what that file contains.\n\n` +
    `Return your answer by calling StructuredOutput.`,
    { label: `${j.cell}-${j.order}`, phase: 'Judge', schema: SCHEMA }
  ).then((r) => ({ ...j, result: r })).catch(() => null)
))
const good = out.filter(Boolean).filter((x) => x && x.result)
log(`${good.length} of ${JOBS.length} judged`)
return { judged: good.length,
  verdicts: good.map((x) => `${x.cell} [${x.order}] better=${x.result.better} ` +
    `(one=${x.reading_one}) conf=${x.result.confidence}`) }
