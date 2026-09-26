"""Which evaluative words OUTSIDE inner-life vocabulary carry the base-to-aligned gap. (TheoryMachines, 2026-09-26:
"list the non-X/E evaluative words that carry the base-to-aligned gap")

    .venv/bin/python -u arc_fig5_eval_words.py   -> ARC_FIG5_EVAL_WORDS.md

WORDS: the figure's "+vector" evaluative lexicon (arc_valence_clean_components v2) minus every USAS X and E form
(arc_fig5_checks' lists), polar only (valence < 4 or > 6). Surface forms, no lemmatising.
TEXTS: the judged no-demonym national stories, one meta-text per model-condition (the figure's), content tokens as
arc_interiority defines them.
PAIRS: every (lineage, aligned condition) whose lineage also has a base text, POOLED across the three aligned
conditions. Per word: base rate and aligned rate = mean over pairs of its per-text rate (per content word);
CONTRIBUTION = mean over pairs of (aligned rate - base rate). Means rather than medians because means are additive:
the contributions of all words sum exactly to the mean evaluative gap, so a word's share of the gap is meaningful.
LINEAGES UP: per lineage, the word's aligned rate averaged over that lineage's aligned conditions, against its base
rate; k rising of n lineages (ties, usually both zero, count as not rising). No classification of the words. EXPLORATORY.
"""
import collections, os, re, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import arc_fig5_checks as C                                   # noqa: E402  (sets argv for the figure's 1700 config)
V, A, E = C.V, C.A, C.E

OUT = os.path.join(HERE, "ARC_FIG5_EVAL_WORDS.md")
TOP, FALL = 30, 10


def main():
    ex, sw, _ = A.lists_expanded()
    Ew, _ = C.e_list(sw)
    XE = ex["fullx"] | Ew
    lex = V.lexicons()[E.LEX]
    lex_all = {w: v for w, v in lex.items() if v < 4 or v > 6}
    lex_d = {w: v for w, v in lex_all.items() if w not in XE}
    M = pd.read_parquet(os.path.join(A.DATA, "prompt_check_national_judged_meta.parquet"))
    cnt, ncont, n_all = {}, {}, {}
    for r in M.itertuples():
        t = [w for w in re.findall(r"[a-z]+", r.text.lower()) if w not in sw]
        c = collections.Counter(t)
        cnt[(r.lineage, r.cond)] = {w: k for w, k in c.items() if w in lex_d}
        n_all[(r.lineage, r.cond)] = sum(k for w, k in c.items() if w in lex_all)
        ncont[(r.lineage, r.cond)] = len(t)
    rate = lambda key, w: cnt[key].get(w, 0) / ncont[key]
    aligned = [c for c in E.COND.values() if c != "base"]
    pairs = [(l, c) for (l, c) in cnt if c in aligned and (l, "base") in cnt]
    lins = sorted({l for l, _ in pairs})
    words = sorted({w for key in cnt for w in cnt[key]})
    rows = []
    for w in words:
        b = np.array([rate((l, "base"), w) for l, _ in pairs])
        a = np.array([rate((l, c), w) for l, c in pairs])
        up = sum(np.mean([rate((l, c), w) for ll, c in pairs if ll == l]) > rate((l, "base"), w) for l in lins)
        rows.append(dict(word=w, valence=lex_d[w], pole="positive" if lex_d[w] > 6 else "negative",
                         base=b.mean(), aligned=a.mean(), contrib=(a - b).mean(), up=up))
    D = pd.DataFrame(rows)
    gap_d = D.contrib.sum()
    gap_all = np.mean([n_all[(l, c)] / ncont[(l, c)] - n_all[(l, "base")] / ncont[(l, "base")] for l, c in pairs])
    #: additivity is the reason for means: the parts must sum to the whole they are a share of
    chk = np.mean([sum(cnt[(l, c)].values()) / ncont[(l, c)] - sum(cnt[(l, "base")].values()) / ncont[(l, "base")] for l, c in pairs])
    assert abs(gap_d - chk) < 1e-12, (gap_d, chk)
    R = ["# Evaluative words outside inner-life vocabulary that carry the base-to-aligned gap (EXPLORATORY)", "",
         "Producer `arc_fig5_eval_words.py` (method in its docstring). %d (lineage, aligned condition) pairs over %d lineages, "
         "aligned conditions pooled. Rates are per 1,000 content words; contribution is the mean paired difference, and the "
         "contributions of all words sum to the mean gap." % (len(pairs), len(lins)), "",
         "- Mean evaluative gap, whole lexicon: %+.2f per 1,000 content words." % (1000 * gap_all),
         "- Of which words outside USAS X and E: %+.2f (%.0f%%)." % (1000 * gap_d, 100 * gap_d / gap_all)]
    for pole in ("positive", "negative"):
        P = D[D.pole == pole]
        R.append("- %s pole, outside X and E: net %+.2f per 1,000 (%s forms occurring)." % (pole.capitalize(), 1000 * P.contrib.sum(), format(len(P), ",")))
    for pole in ("positive", "negative"):
        P = D[D.pole == pole].sort_values("contrib", ascending=False)
        top = P.head(TOP)
        R += ["", "## %s pole: top %d by contribution" % (pole.capitalize(), TOP), "",
              "These %d carry %+.2f per 1,000, %.0f%% of the gap outside X and E." % (TOP, 1000 * top.contrib.sum(), 100 * top.contrib.sum() / gap_d), "",
              "| word | valence | base | aligned | contribution | lineages up (of %d) |" % len(lins), "|---|---|---|---|---|---|"]
        R += ["| %s | %.1f | %.2f | %.2f | %+.3f | %d |" % (r.word, r.valence, 1000 * r.base, 1000 * r.aligned, 1000 * r.contrib, r.up) for r in top.itertuples()]
        low = P.tail(FALL).iloc[::-1]
        R += ["", "Largest %d falls on this pole:" % FALL, "", "| word | valence | base | aligned | contribution | lineages up |", "|---|---|---|---|---|---|"]
        R += ["| %s | %.1f | %.2f | %.2f | %+.3f | %d |" % (r.word, r.valence, 1000 * r.base, 1000 * r.aligned, 1000 * r.contrib, r.up) for r in low.itertuples()]
    open(OUT, "w").write("\n".join(R) + "\n")
    print("\n".join(R))


if __name__ == "__main__":
    main()
