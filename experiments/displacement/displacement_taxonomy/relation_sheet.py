"""One page per frame: the relation, its words base -> aligned, and every norm.

    python -u relation_sheet.py                      -> results/relation_sheet.md
    python -u relation_sheet.py --also PATH          also write a copy there

## WHAT THIS IS

The 96 pooled frames, each with the relation a BLIND reader named, the words
that reader said carry it, and every norm we have on those two word lists --
lexical, contextual and `task_charge` -- laid out base -> aligned.

**THE READER NEVER SAW THE DIRECTION.** Columns are relabelled per frame;
`blind_for` fixes which is the faller block, a faller lost probability from
base to aligned, so that column is the BASE-favoured one. The orientation in
every section below was applied AFTER the reading and was never shown to
anyone rating anything.

## TWO RUNS, AND WHICH ONE A SECTION SHOWS

The same tables were read twice: once with every word, once with closed-class
words removed by in-frame spaCy POS. The content run reads better on the
replicate frames, so it is shown first where it exists, and the all-words
relation is named beneath it when the two differ. Neither supersedes the other
-- the closed-class words are real signal (0.83 concentration in one group,
77% faller) and one frame consists of nothing else.

## THE SELECTION BOUND GOVERNS EVERY NUMBER HERE

The reader was told to find the CLEAREST relation and to drop any word that
would force a hedge. These lists are therefore chosen for separability, and the
norm gaps measure what separates the words a reader used -- not what alignment
does to an arm. `covers N of M` on each section is how much of the frame the
relation reached; 10 of 24 and 23 of 23 are not the same kind of claim.

## THREE FRAMES CARRY NO RELATION AND ARE LISTED AT THE END

Two clear the threshold with a single word and nothing opposite it, so there is
nothing to relate and they were never sent. One is emptied by the content
filter alone. Listed rather than dropped: a document of 93 sections implying a
population of 93 is how a filtered population becomes the population.
"""
import argparse, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import norm_shift as NS
import pooled_tables as PT

OUT = os.path.join(HERE, "results", "relation_sheet.md")

LEX = [("warriner_valence", "valence (Warriner)"),
       ("warriner_arousal", "arousal (Warriner)"),
       ("warriner_dominance", "dominance (Warriner)"),
       ("brysbaert_concreteness", "concreteness (Brysbaert)"),
       ("k_charge", "charge (lexicon)"),
       ("k_transgressiveness", "transgressiveness (lexicon)"),
       ("k_vulgarity", "vulgarity (lexicon)"),
       ("k_bodily_harm", "bodily harm (lexicon)"),
       ("k_register_level", "register level (lexicon)"),
       ("k_concreteness", "concreteness (lexicon)"),
       ("k_valence", "valence (lexicon)")]


def fmt(x):
    return "%.2f" % x if isinstance(x, (int, float)) else "--"


def section(r, other_name=None):
    L = []
    L.append("## %s ___" % r["frame"].rstrip())
    L.append("")
    L.append("**%s** — confidence %s — covers %d of %d words"
             % (r["name"], r["confidence"], r["n_covered"], r["n_shown"]))
    if other_name and other_name != r["name"]:
        L.append("")
        L.append("*All-words reading of the same frame:* %s" % other_name)
    L.append("")
    L.append("| | words |")
    L.append("|---|---|")
    L.append("| **base** | %s |" % ", ".join(r["base_words"]))
    L.append("| **aligned** | %s |" % ", ".join(r["aligned_words"]))
    L.append("")
    L.append("| scale | base | aligned | delta |")
    L.append("|---|---|---|---|")
    if r["charge_base"] is not None:
        L.append("| **charge, in frame** (`task_charge`) | %s | %s | %+.2f |"
                 % (fmt(r["charge_base"]), fmt(r["charge_aligned"]),
                    r["charge_aligned"] - r["charge_base"]))
    for k, lab in LEX:
        if k in r["base"] and k in r["aligned"]:
            L.append("| %s | %s | %s | %+.2f |"
                     % (lab, fmt(r["base"][k]), fmt(r["aligned"][k]),
                        r["aligned"][k] - r["base"][k]))
    for k in sorted(r.get("ctx", {})):
        b, a, _c = r["ctx"][k]
        L.append("| `%s` | %s | %s | %+.2f |" % (k, fmt(b), fmt(a), a - b))
    L.append("")
    L.append("> %s" % r["explanation"].replace("\n", " "))
    return "\n".join(L)


def build():
    content = {r["frame"]: r for r in NS.rows(NS.CONTENT, want_ctx=True)}
    allw = {r["frame"]: r for r in NS.rows(NS.ALLWORDS, want_ctx=True)}
    frames = PT.frames()
    L = [NS.__doc__ and "" or ""]
    L = ["# Ninety-six frames, the relation in each, and every norm on its two sides",
         "",
         "Each section is one sentence with a blank, the relation a **blind** reader "
         "named between the two groups of words that move at that blank, and every "
         "norm we hold on those two lists. Fifty base/aligned model pairs are pooled "
         "per frame.",
         "",
         "**The reader was never told the direction.** The two groups are relabelled "
         "per frame and the reader sees only `GROUP A` and `GROUP B`. Which column is "
         "the base-favoured one is recomputed afterwards from the movement rule, so "
         "the `base -> aligned` orientation below was applied after every reading and "
         "shown to no one.",
         "",
         "**The reader was told to find the clearest relation and to drop any word "
         "that would force a hedge.** So these word lists are selected for "
         "separability, and the norm gaps say what separates the words a reader used "
         "— not what alignment does to a whole arm. `covers N of M` is how much of "
         "the frame each relation reached.",
         "",
         "Rows are: `task_charge` (a rating of the completed scene, in this frame), "
         "then the type-level lexicons, then the contextual slot-rating batteries "
         "(`v6`, `slot_institutional_en_v3`, `sexual_v2`) whose raters also saw the "
         "frame. A scale is absent where neither side had a rated word.",
         "",
         "---", ""]
    shown, missing = 0, []
    for f in frames:
        r = content.get(f) or allw.get(f)
        if not r:
            missing.append(f)
            continue
        L.append(section(r, (allw.get(f) or {}).get("name")
                         if f in content else None))
        L.append("")
        L.append("---")
        L.append("")
        shown += 1
    if missing:
        L.append("## Frames with no relation")
        L.append("")
        L.append("These clear the movement threshold with words on one side only, so "
                 "there are no two groups to relate and they were never put to a "
                 "reader. Listed rather than dropped.")
        L.append("")
        for f in missing:
            got = PT.pooled(f)
            n = len(got[0]) if got else 0
            L.append("- **%s ___** — %d word(s) clearing the threshold, one side empty"
                     % (f.rstrip(), n))
        L.append("")
    return "\n".join(L), shown, len(missing)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--also", default=None, help="write a second copy here")
    a = ap.parse_args(argv)
    md, shown, miss = build()
    for path in [a.out] + ([a.also] if a.also else []):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(md)
        print("wrote %s  (%d sections, %d frames with no relation, %d chars)"
              % (path, shown, miss, len(md)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
