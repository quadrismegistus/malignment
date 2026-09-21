"""Does kill -> scream happen link by link along a ladder, or in one stage?

    python -u run.py                        # the Figure 2 prompt, all ladders
    python -u run.py --ladder olmo3_7b --top 8
    python -u run.py --prompt "He hated her deeply and wanted to"

RH, glossing Freud: the idea acquires its substitute "along a chain of
connections determined in a particular way" (RSE 14:137). The seed-walk ego
graphs in `substitution_shape` do NOT draw that chain -- their paths past
radius one are stitched across different prompts, so they show a fan of
one-step moves rather than a chain (and `substitution_replicated.py` confirms
the lineages do not even agree on the pairings: 0 of 6,976 drawable pairs
survive BH). The chain that does belong to one idea runs along the RECIPE:
same prompt, same candidate words, base then SFT then DPO then the production
model.

## THE LADDERS ARE ORDERED RECIPES, NOT ROSTER SIBLINGS

`roster.lineages()` returns eight roots with four or more nodes, but most of
that breadth is SIBLINGS -- four archangel methods off one SFT, five Tulu data
ablations off one base, a Think branch beside an Instruct branch. A ladder here
is an ORDERED sequence a model actually passed through, and the ablations are
offered separately (`--ladder tulu_ablations`) because they are one stage
measured five ways, not five stages.

## topup=0 ONLY

`twp_words_v4` holds two passes and the campaign's rule is that they are
different instruments and must not be merged: pass 1 is beam-accumulated over
the full population, pass 2 (`topup=1`) is a single-path lower bound scoped to
the lineage union. Reading both returns a word twice at two probabilities.
"""
import argparse, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)

FIG2 = "She was so angry she wanted to"

#: ordered stages. The label is the STEP, the string is the checkpoint.
LADDERS = {
    "tulu_llama31": [
        ("base", "meta-llama/Llama-3.1-8B"),
        ("SFT", "allenai/Llama-3.1-Tulu-3-8B-SFT"),
        ("DPO", "allenai/Llama-3.1-Tulu-3-8B-DPO"),
        ("RLVR", "allenai/Llama-3.1-Tulu-3.1-8B"),
    ],
    "olmo3_7b": [
        ("base", "allenai/Olmo-3-1025-7B"),
        ("SFT", "allenai/Olmo-3-7B-Instruct-SFT"),
        ("DPO", "allenai/Olmo-3-7B-Instruct-DPO"),
        ("RLVR", "allenai/Olmo-3-7B-Instruct"),
    ],
    "olmo3_7b_think": [
        ("base", "allenai/Olmo-3-1025-7B"),
        ("SFT", "allenai/Olmo-3-7B-Think-SFT"),
        ("DPO", "allenai/Olmo-3-7B-Think-DPO"),
        ("RLVR", "allenai/Olmo-3-7B-Think"),
    ],
    "olmo3_32b": [
        ("base", "allenai/Olmo-3-1125-32B"),
        ("SFT", "allenai/Olmo-3.1-32B-Instruct-SFT"),
        ("DPO", "allenai/Olmo-3.1-32B-Instruct-DPO"),
        ("RLVR", "allenai/Olmo-3.1-32B-Instruct"),
    ],
    "olmo2_1b": [
        ("base", "allenai/OLMo-2-0425-1B"),
        ("SFT", "allenai/OLMo-2-0425-1B-SFT"),
        ("DPO", "allenai/OLMo-2-0425-1B-DPO"),
        ("RLVR", "allenai/OLMo-2-0425-1B-Instruct"),
    ],
    "olmoe_1b7b": [
        ("base", "allenai/OLMoE-1B-7B-0125"),
        ("SFT", "allenai/OLMoE-1B-7B-0125-SFT"),
        ("DPO", "allenai/OLMoE-1B-7B-0125-DPO"),
        ("RLVR", "allenai/OLMoE-1B-7B-0125-Instruct"),
    ],
    #: three stages only: zephyr's DPO is the last link and there is no RLVR
    "zephyr_mistral": [
        ("base", "mistralai/Mistral-7B-v0.1"),
        ("SFT", "HuggingFaceH4/mistral-7b-sft-beta"),
        ("DPO", "HuggingFaceH4/zephyr-7b-beta"),
    ],
    #: three stages, and the last is FOUR METHODS off one SFT -- a fan, not a
    #: ladder, so they are listed as alternatives and never averaged
    "archangel_pythia": [
        ("base", "EleutherAI/pythia-2.8b"),
        ("SFT", "ContextualAI/archangel_sft_pythia2-8b"),
        ("DPO", "ContextualAI/archangel_sft-dpo_pythia2-8b"),
    ],
}
#: NOT a ladder: one stage measured five ways. Kept so the contrast is
#: available and cannot be mistaken for a sequence.
ABLATIONS = [
    ("base", "meta-llama/Llama-3.1-8B"),
    ("SFT full", "allenai/Llama-3.1-Tulu-3-8B-SFT"),
    ("SFT -safety", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data"),
    ("SFT -wildchat", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data"),
    ("SFT -math", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-math-data"),
    ("SFT -persona", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-persona-data"),
]


def probs(prompt, models):
    """-> {model: {word: p}} from pass 1 only."""
    from malignment import ch
    q = ("SELECT model, word, p FROM {db}.twp_words_v4 "
         "WHERE prompt='%s' AND rule_version=4 AND frame='' AND topup=0 "
         "AND model IN (%s)"
         % (prompt.replace("'", "\\'"),
            ", ".join("'%s'" % m.replace("'", "\\'") for m in models)))
    out = collections.defaultdict(dict)
    for r in ch.query(q, limit_bytes=None):
        out[r["model"]][r["word"]] = float(r["p"])
    return out


def table(prompt, stages, top=6, words=None):
    """-> (ordered words, {word: [p per stage]}, missing stages)"""
    P = probs(prompt, [m for _, m in stages])
    missing = [lab for lab, m in stages if m not in P]
    live = [(lab, m) for lab, m in stages if m in P]
    if not live:
        return [], {}, missing
    if words is None:
        #: **RANKED ON THE BASE ARM, NOT ON ANY LATER ONE.** The question is
        #: what happens to the words the base offered; ranking on the union or
        #: on the last stage would let a word the base never had set the rows.
        base = P[live[0][1]]
        words = [w for w, _ in sorted(base.items(), key=lambda kv: -kv[1])[:top]]
    rows = {w: [P[m].get(w) for _, m in live] for w in words}
    return [lab for lab, _ in live], rows, missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", default=FIG2)
    ap.add_argument("--ladder", default=None, choices=sorted(LADDERS))
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--words", default=None,
                    help="comma-separated; overrides --top")
    ap.add_argument("--ablations", action="store_true")
    a = ap.parse_args(argv)
    ws = [w.strip() for w in a.words.split(",")] if a.words else None

    print("PROMPT: %r" % a.prompt)
    todo = ([("tulu_ablations(NOT A LADDER)", ABLATIONS)] if a.ablations
            else [(k, LADDERS[k]) for k in
                  ([a.ladder] if a.ladder else sorted(LADDERS))])
    for name, stages in todo:
        labs, rows, missing = table(a.prompt, stages, a.top, ws)
        print("\n== %s" % name)
        if missing:
            print("   NOT MEASURED on this prompt: %s" % ", ".join(missing))
        if not labs:
            continue
        print("   %-14s %s" % ("word", "".join("%10s" % l for l in labs)))
        for w, v in sorted(rows.items(), key=lambda kv: -(kv[1][0] or 0)):
            cells = "".join("%10s" % ("--" if x is None else "%.4f" % x)
                            for x in v)
            #: an absent word is NOT zero: `twp` stores nothing below theta,
            #: so the mass is somewhere in [0, 0.001) and "--" says so
            print("   %-14s %s" % (w, cells))
    return 0


if __name__ == "__main__":
    sys.exit(main())
