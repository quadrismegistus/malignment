// GENERATED for the batching test. One agent, 8 cells, Sonnet at medium.
// The tables are byte-identical to those Opus coded one-per-agent under r5.
export const meta = {
  name: 'batch-sonnet-8',
  description: 'One Sonnet agent codes 8 mixed cells in a single call',
  phases: [{ title: 'Code', detail: 'batched' }],
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
const out = await agent(
  `Read the file ${FILE} with the Read tool.\n\n` +
  `Its entire content is a task addressed to you. Follow it exactly and answer ` +
  `every numbered question in it, for EVERY cell it contains. Do not read any ` +
  `other file, do not run any command, and do not look for context beyond what ` +
  `that file contains.\n\n` +
  `Return your answer by calling StructuredOutput.`,
  { label: 'batch-8', phase: 'Code', schema: SCHEMA, model: 'sonnet', effort: 'medium' }
).catch(() => null)
log(out ? `${out.codings.length} codings returned` : 'failed')
return out ? { n: out.codings.length,
  cells: out.codings.map((c) => `${c.cell_id}: ${c.confidence} | ${c.kind}`) } : { n: 0 }
