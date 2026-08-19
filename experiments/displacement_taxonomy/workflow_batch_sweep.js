// GENERATED. Same 8 cells, same file, three model/effort settings.
// Baseline already measured: sonnet/medium batched, sonnet/medium unbatched,
// opus/(session effort) unbatched. Only model and effort vary here.
export const meta = {
  name: 'batch-sweep',
  description: 'Same 8 cells coded under three model/effort settings',
  phases: [{ title: 'Sweep', detail: 'one agent per setting' }],
}
const FILE = "/Users/rj416/github/malignment/experiments/displacement_taxonomy/results/inputs/batch_sonnet_8.txt"
const SCHEMA = {
  "additionalProperties": false,
  "properties": {
    "codings": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "cell_id": {
            "type": "string"
          },
          "confidence": {
            "enum": [
              "high",
              "medium",
              "low",
              "none"
            ],
            "type": "string"
          },
          "counterexamples": {
            "type": "string"
          },
          "kind": {
            "description": "short phrase of your own for what DIMENSION differs",
            "type": "string"
          },
          "notes": {
            "type": "string"
          },
          "reading": {
            "description": "FILL FIRST. One or two sentences on what you see in this movement, before committing to any relation.",
            "type": "string"
          },
          "relations": {
            "items": {
              "additionalProperties": false,
              "properties": {
                "a_words": {
                  "items": {
                    "type": "string"
                  },
                  "type": "array"
                },
                "b_words": {
                  "items": {
                    "type": "string"
                  },
                  "type": "array"
                },
                "confidence": {
                  "description": "how far you would defend THIS relation, independently of the others",
                  "enum": [
                    "high",
                    "medium",
                    "low"
                  ],
                  "type": "string"
                },
                "name": {
                  "description": "2-4 words of your own invention naming the relation",
                  "type": "string"
                },
                "sentence": {
                  "type": "string"
                }
              },
              "required": [
                "name",
                "sentence",
                "a_words",
                "b_words",
                "confidence"
              ],
              "type": "object"
            },
            "maxItems": 3,
            "type": "array"
          },
          "residue": {
            "additionalProperties": false,
            "properties": {
              "description": {
                "type": "string"
              },
              "words": {
                "items": {
                  "type": "string"
                },
                "type": "array"
              }
            },
            "required": [
              "words",
              "description"
            ],
            "type": "object"
          }
        },
        "required": [
          "cell_id",
          "reading",
          "relations",
          "kind",
          "residue",
          "counterexamples",
          "confidence",
          "notes"
        ],
        "type": "object"
      },
      "maxItems": 8,
      "minItems": 8,
      "type": "array"
    }
  },
  "required": [
    "codings"
  ],
  "type": "object"
}
const CONFIGS = [
  {
    "model": "sonnet",
    "effort": "high"
  },
  {
    "model": "sonnet",
    "effort": "xhigh"
  },
  {
    "model": "opus",
    "effort": "medium"
  }
]

const out = await parallel(CONFIGS.map((c) => () =>
  agent(
    `Read the file ${FILE} with the Read tool.\n\n` +
    `Its entire content is a task addressed to you. Follow it exactly and answer ` +
    `every numbered question in it, for EVERY cell it contains. Do not read any ` +
    `other file, do not run any command, and do not look for context beyond what ` +
    `that file contains.\n\n` +
    `Return your answer by calling StructuredOutput.`,
    { label: `${c.model}-${c.effort}`, phase: 'Sweep', schema: SCHEMA,
      model: c.model, effort: c.effort }
  ).then((r) => ({ cfg: `${c.model}/${c.effort}`, result: r })).catch(() => null)
))

const good = out.filter(Boolean).filter((x) => x && x.result)
log(`${good.length} of ${CONFIGS.length} settings returned`)
return {
  returned: good.length,
  summary: good.map((x) => `${x.cfg}: ${x.result.codings.length} cells, ` +
    `${(x.result.codings.reduce((a, c) => a + c.relations.length, 0) / x.result.codings.length).toFixed(2)} rel/cell`),
}
