"""Workflow scripts for TEMPLATE_ARM's coding, derived from passC's shard-00.js by text edits only.

    python make_workflows.py    # -> coding/ta_code_<k>.js, and prints the edit check

Edits, and nothing else: BATCHES; one coder ('A'); model pinned to claude-opus-5;
"five codes" -> "six codes"; one rubric section (`break`) inserted before `## span`;
`break` added to the schema and to the returned record; names and labels.
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "experiments", "passage_analysis", "interiority_in_passages", "results", "passC", "scripts", "shard-00.js")
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
NCHUNK = 4
BREAK = ("## break\\n\\nIf narrative is false, find where the non-narrative material begins and quote its first words "
         "verbatim, at most 15 words, copied exactly from the text: the first words of the essay, list, Q&A, "
         "assistant reply, web or document furniture, or mangled text that disqualifies it. If the passage is not a "
         "scene from its very first words, quote its opening words. If narrative is true, return an empty string.\\n\\n")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="", help="batches<tag>.json -> ta_code<tag>_<k>.js")
    ap.add_argument("--nchunk", type=int, default=NCHUNK)
    args = ap.parse_args()
    src = open(SRC).read()
    batches = json.load(open(os.path.join(DATA, "template_arm", "coding", "batches%s.json" % args.tag)))
    size = -(-len(batches) // args.nchunk)
    for k in range(args.nchunk):
        chunk = batches[k * size:(k + 1) * size]
        s = src
        i = s.index("const BATCHES = "); j = s.index("\n", i)
        s = s[:i] + "const BATCHES = " + json.dumps(chunk) + s[j:]
        rep = [
            ("name: 'passc-shard-00'", "name: 'ta-code%s-%d'" % (args.tag, k)),
            ("description: 'Pass C shard 0 of 12: two blind coders over 3210 passages'",
             "description: 'TEMPLATE_ARM Figure 5 coding%s, chunk %d of %d: passC rubric + break, claude-opus-5, %d batches'" % (args.tag, k, args.nchunk, len(chunk))),
            ("phases: [{ title: 'Code', detail: '2 coders x 72 batches, Opus high effort' }]",
             "phases: [{ title: 'Code', detail: '1 coder x %d batches, claude-opus-5 pinned, high effort' }]" % len(chunk)),
            ("For each passage return five codes.", "For each passage return six codes."),
            ("## span\\n\\nFind the passage's most interior moment", BREAK + "## span\\n\\nFind the passage's most interior moment"),
            ("      span:      { type: 'string' },\n", "      span:      { type: 'string' },\n      break:     { type: 'string' },\n"),
            ("required: ['id','narrative','mode','drift','degree','span']", "required: ['id','narrative','mode','drift','degree','span','break']"),
            ("degree: r.degree, span: r.span }", "degree: r.degree, span: r.span, break: r.break }"),
            ("for (const coder of ['A', 'B'])", "for (const coder of ['A'])"),
            ("{ label: `s00:${coder}:b${bi}`, phase: 'Code', schema: SCHEMA, effort: 'high' }",
             "{ label: `ta%s%d:b${bi}`, phase: 'Code', schema: SCHEMA, effort: 'high', model: 'claude-opus-5' }" % (args.tag, k)),
            ("log(`shard 0:", "log(`ta%s chunk %d:" % (args.tag, k)), ("log(`shard 0 done:", "log(`ta%s chunk %d done:" % (args.tag, k)),
            ("_shard: 0,", "_shard: 'ta%s%d'," % (args.tag, k)),
            #: passC's return carries every id twice (_missing_B is all of them with one
            #: coder) and fails the workflow boundary's 4,096-element cap after every agent
            #: has finished; the codings are read from the journal (harvest.py). Counts only.
            ("_missing_A: missA, _missing_B: missB, A: out.A, B: out.B }",
             "_n_missing_A: missA.length, _n_coded_A: Object.keys(out.A).length }"),
        ]
        for a, b in rep:
            assert s.count(a) == 1, (k, a[:50], s.count(a))
            s = s.replace(a, b)
        out = os.path.join(HERE, "ta_code%s_%d.js" % (args.tag, k))
        open(out, "w").write(s)
        print("%s  %d batches, %d passages" % (out, len(chunk), sum(len(b["ids"]) for b in chunk)))


if __name__ == "__main__":
    main()
