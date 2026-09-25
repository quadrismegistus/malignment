"""Rate period-model neighbours of USAS X as interiority candidates, with an LLM, twice. (RH, 2026-09-25)

    .venv/bin/python -u interiority_candidates.py --pilot     three batches, printed
    .venv/bin/python -u interiority_candidates.py --run       both passes -> candidate_ratings_v1.parquet
    .venv/bin/python -u interiority_candidates.py --summary   -> INTERIORITY_CANDIDATES.md
    .venv/bin/python -u interiority_candidates.py --tiebreak   a THIRD pass over words whose two ratings
                                                              disagree -> *_pass3.parquet
    .venv/bin/python -u interiority_candidates.py --consensus  -> *_consensus_v1.csv, INTERIORITY_TIEBREAK.md
    add --seeds to any of these: rate the USAS X words THEMSELVES (3,225, every primary-sense X word
    less NLTK stopwords) -> usasx_ratings_v1.parquet, USAS_X_KINDS.md, with anchors that are not X words

WHERE THE CANDIDATES COME FROM. The abstraction seat took every USAS X word (primary sense, any POS entry)
as a seed in each models_century5 word2vec model, C16-C21, and kept stable nearest neighbours not already
in X (usasx_neighbours_candidates.csv, its scripts/usasx_neighbours.py). The pool rated here: corpus
count >= 500 and >= 5 non-perception seeds in some century -- 5,383 words. The embeddings propose by
ASSOCIATION, so the pool is dominated by argument and knowledge vocabulary (ratiocination, theoretical,
therefore); this pass separates the words that NAME a mental state from the ones that keep company with
them.

WHAT THIS IS AND IS NOT. A triage aid: it narrows 5,383 words to a shortlist a person vets. It is not a
norm and does not enter a score on its own. Note for the methods: the interiority panel is validated
against an LLM coder (interiority_in_passages), so a list vetted by an LLM is not independent of that
check; RH's own keep/reject remains the decision.

DESIGN. deepseek-v4-flash at temperature 0, 40 words a call, each word shown with the centuries it was
proposed from (so a period sense -- C18 `sensible`, capable of feeling -- can count). ROBUSTNESS: two
passes, each an independent shuffle into batches, so every word is rated twice among different
companions; agreement between a word's two ratings measures how much batch context moves the rater.
ANCHORS: four fixed words (think, wonder, door, walk -- none of them a candidate) in every batch; their ratings should never move.
"""
import json, os, random, sys

import numpy as np
from typing import List, Literal

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
from pydantic import BaseModel, Field                     # noqa: E402
from largeliterarymodels.task import Task                 # noqa: E402

SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
CAND = os.path.join(SHARED, "usasx_neighbours_candidates.csv")
OUT = os.path.join(SHARED, "candidate_ratings_v1.parquet")
BATCH, SEED = 40, 20260925
ANCHORS = {"think": "C16, C17, C18, C19, C20, C21", "wonder": "C16, C17, C18, C19, C20, C21",
           "door": "C16, C17, C18, C19, C20, C21", "walk": "C16, C17, C18, C19, C20, C21"}
MENTAL = ("cognition", "emotion", "volition", "perception", "attention")

SYSTEM_PROMPT = """You sort English words by whether they describe the INNER LIFE of a subject.

For each word, judge its ordinary sense(s) in English writing of the centuries given (a word's older
sense counts: in the 18th century "sensible" can mean capable of feeling).

interior (0-3): does the word NAME OR PREDICATE a mental state, process or act of a subject -- what
someone thinks, believes, knows, feels, wants, fears, perceives, attends to, or decides?
  0 = no mental sense: objects, places, bodies, physical actions, quantities, topics, and the vocabulary
      of argument or scholarship as such (therefore, theoretical, hypothesis, evidence, analysis);
  1 = only by association or rarely (husband, heart as an organ, success, freedom);
  2 = a mental sense is common but not the main one (sensible, reflect, sharp, moved, cold);
  3 = its main sense is a mental state or act (pity, dread, wonder, realize, doubtful, longing).

kind: the best label for the word's MAIN sense:
  cognition   thinking, believing, knowing, understanding, remembering, imagining
  emotion     feelings and moods, attitudes of feeling toward something
  volition    wanting, intending, resolving, preferring, trying
  perception  sensing and perceiving (seeing, hearing, feeling as touch)
  attention   noticing, heeding, interest, boredom
  argument    reasoning or knowledge as a discourse or discipline, not a subject's state (therefore,
              theoretical, deduce as a logical term, science, doctrine)
  other       anything else, including social acts, character traits described from outside, objects

Rate every word you are given, exactly once, spelled exactly as given."""


class WordRating(BaseModel):
    word: str = Field(description="the word exactly as given")
    interior: int = Field(ge=0, le=3, description="0-3, as defined")
    kind: Literal["cognition", "emotion", "volition", "perception", "attention", "argument", "other"]


class BatchRatings(BaseModel):
    ratings: List[WordRating]


class InteriorityCandidateTask(Task):
    name = "interiority_candidates_v1"
    schema = BatchRatings
    system_prompt = SYSTEM_PROMPT
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    usage_log = True


SEEDS = "--seeds" in sys.argv
if SEEDS:
    #: think and wonder ARE X words; the anchors must be outside the pool being rated
    ANCHORS = {"dread": "C16, C17, C18, C19, C20, C21", "grief": "C16, C17, C18, C19, C20, C21",
               "door": "C16, C17, C18, C19, C20, C21", "walk": "C16, C17, C18, C19, C20, C21"}
    OUT = os.path.join(SHARED, "usasx_ratings_v1.parquet")
X_JSON = os.path.expanduser("~/malignment-data/novel_arc/usas_fields_members.json")


def x_words():
    """{word: sorted X codes} for every primary-sense X member, NLTK stopwords dropped."""
    from nltk.corpus import stopwords
    sw = set(stopwords.words("english"))
    w = {}
    for code, x in json.load(open(X_JSON))["codes"].items():
        if code.startswith("X"):
            for m in x["members"]:
                if m["rank"] == 0 and m["word"] not in sw:
                    w.setdefault(m["word"], set()).add(code)
    return {k: sorted(v) for k, v in w.items()}


def pool():
    """-> [(word, 'C17, C18')] for the 5,383-word vetting pool, or with --seeds the 3,225 X words."""
    if SEEDS:
        out = sorted((w, "any period") for w in x_words())
        assert len(out) == 3225, len(out)
        assert not set(ANCHORS) & {w for w, _ in out}
        return out
    import pandas as pd
    c = pd.read_csv(CAND)
    p = c[(c["count"] >= 500) & (c.n_seeds_nonX3 >= 5)]
    cents = p.groupby("neighbour").century.apply(lambda s: ", ".join(sorted(set(s))))
    out = sorted(cents.items())
    assert len(out) == 5383, len(out)
    assert not set(ANCHORS) & {w for w, _ in out}
    return out


def batches():
    """Two passes, each an independent shuffle of the pool into batches of BATCH, anchors added."""
    words = pool()
    rng = random.Random(SEED)
    out = []
    for ps in (1, 2):
        w = list(words)
        rng.shuffle(w)
        for b in range(0, len(w), BATCH):
            chunk = w[b:b + BATCH] + list(ANCHORS.items())
            rng.shuffle(chunk)
            out.append(dict(pass_=ps, batch=b // BATCH, items=chunk))
    return out


def render(items):
    return ("Rate each word. Centuries show where it was proposed from.\n\n" +
            "\n".join("%s  (%s)" % (w, c) for w, c in items))


def rate(bs, workers=16):
    t = InteriorityCandidateTask()
    errs = {}
    res = t.map([render(b["items"]) for b in bs], metadata_list=[{"pass": b["pass_"], "batch": b["batch"]} for b in bs],
                num_workers=workers, errors=errs)
    rows, missing, extra = [], 0, 0
    for b, r in zip(bs, res):
        want = {w for w, _ in b["items"]}
        got = {}
        for x in (r.ratings if r else []):
            if x.word in want and x.word not in got:
                got[x.word] = x
            else:
                extra += 1
        missing += len(want - set(got))
        for w, x in got.items():
            rows.append(dict(word=w, pass_=b["pass_"], batch=b["batch"], interior=x.interior, kind=x.kind,
                             anchor=w in ANCHORS))
    return rows, missing, extra, len(errs)


def main():
    import pandas as pd
    bs = batches()
    if "--pilot" in sys.argv:
        rows, miss, extra, nerr = rate(bs[:3], workers=3)
        d = pd.DataFrame(rows)
        print("pilot: %d rows, %d missing, %d extra/duplicate, %d failed calls" % (len(d), miss, extra, nerr))
        print(d.sort_values(["interior", "kind"], ascending=[False, True]).to_string(index=False, max_rows=130))
        return
    if "--run" in sys.argv:
        assert not os.path.exists(OUT), "refusing to overwrite %s" % OUT
        rows, miss, extra, nerr = rate(bs)
        d = pd.DataFrame(rows)
        d.to_parquet(OUT, index=False)
        print("-> %s: %d rows from %d batches; %d missing, %d extra, %d failed calls" % (
            OUT, len(d), len(bs), miss, extra, nerr))
        return
    if "--summary" in sys.argv:
        seeds_summary() if SEEDS else summary()
    if "--tiebreak" in sys.argv:
        tiebreak()
    if "--consensus" in sys.argv:
        consensus_report()


def summary():
    import pandas as pd
    from scipy.stats import spearmanr
    d = pd.read_parquet(OUT)
    a = d[d.anchor]
    anc = a.groupby("word").agg(interior=("interior", lambda s: sorted(set(s))), kind=("kind", lambda s: sorted(set(s))),
                                n=("interior", "size"))
    w = d[~d.anchor].pivot_table(index="word", columns="pass_", values=["interior", "kind"], aggfunc="first")
    both = w.dropna()
    i1, i2 = both[("interior", 1)].astype(int), both[("interior", 2)].astype(int)
    k1, k2 = both[("kind", 1)], both[("kind", 2)]
    exact = float((i1 == i2).mean()); within1 = float(((i1 - i2).abs() <= 1).mean())
    kind_agree = float((k1 == k2).mean())
    rho = float(spearmanr(i1, i2)[0])
    mean_i = (i1 + i2) / 2
    mental = both[(k1.isin(MENTAL)) & (k2.isin(MENTAL))]
    short = mental[(mental[("interior", 1)] >= 2) & (mental[("interior", 2)] >= 2)]
    short_k = short[("kind", 1)].where(short[("kind", 1)] == short[("kind", 2)], "mixed")
    c = pd.read_csv(CAND)
    p = c[(c["count"] >= 500) & (c.n_seeds_nonX3 >= 5)]
    cents = p.groupby("neighbour").century.apply(lambda s: ", ".join(sorted(set(s))))
    from wordfreq import zipf_frequency
    sl = pd.DataFrame({"word": short.index, "interior_mean": mean_i.loc[short.index].values,
                       "kind": short_k.values, "centuries": cents.reindex(short.index).values})
    #: period spellings (surprize) and OCR errors (recouection) both score high; a modern-lexicon flag lets
    #: the vetter tell them apart at a glance -- zipf 0 means wordfreq has never seen the form
    sl["zipf_modern"] = [round(zipf_frequency(w, "en"), 2) for w in sl.word]
    sl = sl.sort_values(["interior_mean", "kind", "word"], ascending=[False, True, True])
    sl.to_csv(os.path.join(SHARED, "candidate_shortlist_v1.csv"), index=False)
    L = ["# LLM triage of period-model interiority candidates (EXPLORATORY)", "",
         "Producer `interiority_candidates.py`. %d candidates (USAS X period-model neighbours, count >= 500, >= 5 "
         "non-perception seeds), each rated twice by deepseek-v4-flash at temperature 0 in independently "
         "shuffled batches of %d, with four anchors in every batch. Ratings: %s. A triage aid for RH's vetting, "
         "not a norm; the interiority panel is validated against an LLM coder, so this list is not independent "
         "of that check. The API resolves the requested deepseek-v4-flash to a model it names "
         "deepseek-flash; that resolved id is the model of record." % (len(w), BATCH, OUT), "",
         "## Robustness", "",
         "- words rated in both passes: %d of %d" % (len(both), len(w)),
         "- interior (0-3): exact agreement %.1f%%, within one point %.1f%%, Spearman %.3f" % (
             100 * exact, 100 * within1, rho),
         "- kind: agreement %.1f%%" % (100 * kind_agree),
         "- anchors (should never move): " + "; ".join("%s interior %s kind %s (n=%d)" % (
             i, r.interior, r.kind, r.n) for i, r in anc.iterrows()), "",
         "## Distribution (pass 1)", "",
         "| interior | " + " | ".join(sorted(set(k1))) + " |", "|---|" + "---|" * len(set(k1))]
    for iv in range(4):
        L.append("| %d | " % iv + " | ".join(str(int(((i1 == iv) & (k1 == k)).sum())) for k in sorted(set(k1))) + " |")
    L += ["", "## Shortlist for vetting", "",
          "Both passes rate interior >= 2 AND a mental kind (%s) in both: %d words. Kind 'mixed' where the two "
          "passes chose different mental kinds. %d of them are forms modern English does not use (zipf 0: period "
          "spellings or OCR errors). Full list, with that flag: %s." % (
              ", ".join(MENTAL), len(sl), int((sl.zipf_modern == 0).sum()),
              os.path.join(SHARED, "candidate_shortlist_v1.csv")), ""]
    for k in list(MENTAL) + ["mixed"]:
        ws = sl[sl.kind == k].word.tolist()
        L.append("- **%s** (%d): %s" % (k, len(ws), ", ".join(ws[:60]) + (" ..." if len(ws) > 60 else "")))
    open(os.path.join(HERE, "INTERIORITY_CANDIDATES.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


OUT3 = OUT.replace("_v1.parquet", "_v1_pass3.parquet")


def two_pass():
    """-> wide table of passes 1 and 2 (non-anchor) and the words whose interior or kind disagree."""
    import pandas as pd
    d = pd.read_parquet(OUT)
    w = d[~d.anchor].pivot_table(index="word", columns="pass_", values=["interior", "kind"], aggfunc="first").dropna()
    dis = (w[("interior", 1)] != w[("interior", 2)]) | (w[("kind", 1)] != w[("kind", 2)])
    return w, sorted(w.index[dis])


def tiebreak():
    """Pass 3 over the disagreeing words only, in a fresh shuffle with the same anchors."""
    import pandas as pd
    assert not os.path.exists(OUT3), "refusing to overwrite %s" % OUT3
    _, dis = two_pass()
    cents = dict(pool())
    items = [(x, cents[x]) for x in dis]
    rng = random.Random(SEED + 3)
    rng.shuffle(items)
    bs = []
    for b in range(0, len(items), BATCH):
        chunk = items[b:b + BATCH] + list(ANCHORS.items())
        rng.shuffle(chunk)
        bs.append(dict(pass_=3, batch=b // BATCH, items=chunk))
    rows, miss, extra, nerr = rate(bs)
    pd.DataFrame(rows).to_parquet(OUT3, index=False)
    print("-> %s: %d words in %d batches; %d missing, %d extra, %d failed calls" % (
        OUT3, len(dis), len(bs), miss, extra, nerr))


def consensus():
    """Median interior of three, majority kind of three ('mixed' if all differ); two-pass agreement kept."""
    import collections
    import pandas as pd
    w, dis = two_pass()
    p3 = pd.read_parquet(OUT3)
    anc3 = p3[p3.anchor].groupby("word").agg(interior=("interior", lambda s: sorted(set(s))),
                                             kind=("kind", lambda s: sorted(set(s))), n=("interior", "size"))
    p3 = p3[~p3.anchor].set_index("word")
    rows = []
    for x in w.index:
        i = [int(w.loc[x, ("interior", 1)]), int(w.loc[x, ("interior", 2)])]
        k = [w.loc[x, ("kind", 1)], w.loc[x, ("kind", 2)]]
        third = x in p3.index
        if third:
            i.append(int(p3.loc[x, "interior"])); k.append(p3.loc[x, "kind"])
        top, n = collections.Counter(k).most_common(1)[0]
        rows.append(dict(word=x, interior=int(np.median(i)), kind=top if n >= 2 else "mixed",
                         n_ratings=len(i), tiebroken=third, ratings_interior=" ".join(map(str, i)),
                         ratings_kind=" ".join(k)))
    c = pd.DataFrame(rows)
    assert set(c.word[c.tiebroken]) == set(dis), "pass 3 does not cover exactly the disagreeing words"
    return c, anc3


def consensus_report():
    import pandas as pd
    L = ["# Tie-break pass and consensus ratings (EXPLORATORY)", "",
         "Producer `interiority_candidates.py --tiebreak / --consensus` (and `--seeds`). Where a word's two "
         "ratings disagreed on interior (0-3) or kind, a THIRD rating was taken in a fresh shuffle with the same "
         "task, prompt and anchors. Consensus: interior = median of the ratings; kind = the majority label, "
         "'mixed' if all three differ. Words whose first two ratings agreed keep them. Two-pass readouts: "
         "INTERIORITY_CANDIDATES.md, USAS_X_KINDS.md.", ""]
    for label, seeds in (("Candidates (period-model neighbours)", False), ("USAS X words", True)):
        global OUT, OUT3, ANCHORS, SEEDS
        SEEDS = seeds
        OUT = os.path.join(SHARED, "usasx_ratings_v1.parquet" if seeds else "candidate_ratings_v1.parquet")
        OUT3 = OUT.replace("_v1.parquet", "_v1_pass3.parquet")
        c, anc3 = consensus()
        dest = os.path.join(SHARED, ("usasx" if seeds else "candidate") + "_consensus_v1.csv")
        if seeds:
            xw = x_words()
            c["x_codes"] = [" ".join(xw[x]) for x in c.word]
        c.to_csv(dest, index=False)
        tb = c[c.tiebroken]
        mental = c[(c.interior >= 2) & c.kind.isin(MENTAL)]
        L += ["## %s" % label, "",
              "- words %d; tie-broken %d (%.1f%%); after the third rating, kind still 'mixed' (all three differ) for %d"
              % (len(c), len(tb), 100 * len(tb) / len(c), int((tb.kind == "mixed").sum())),
              "- pass-3 anchors: " + "; ".join("%s interior %s kind %s (n=%d)" % (
                  x, r.interior, r.kind, r.n) for x, r in anc3.iterrows()),
              "- consensus interior >= 2 with a mental kind: %d words (%s)" % (
                  len(mental), ", ".join("%s %d" % (k, int((mental.kind == k).sum())) for k in MENTAL)),
              "- consensus kinds, all words: " + ", ".join("%s %d" % (k, n) for k, n in c.kind.value_counts().items()),
              "- per word: %s" % dest, ""]
    open(os.path.join(HERE, "INTERIORITY_TIEBREAK.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def seeds_summary():
    """USAS X words by kind: which subfields are inner states and which are argument or other."""
    import pandas as pd
    from scipy.stats import spearmanr
    d = pd.read_parquet(OUT)
    xw = x_words()
    w = d[~d.anchor].pivot_table(index="word", columns="pass_", values=["interior", "kind"], aggfunc="first").dropna()
    i1, i2 = w[("interior", 1)].astype(int), w[("interior", 2)].astype(int)
    k1, k2 = w[("kind", 1)], w[("kind", 2)]
    agree_k = k1.where(k1 == k2, "mixed")
    t = pd.DataFrame({"word": w.index, "interior_mean": ((i1 + i2) / 2).values, "kind": agree_k.values,
                      "x_codes": [" ".join(xw[x]) for x in w.index]})
    t.to_csv(os.path.join(SHARED, "usasx_kinds_v1.csv"), index=False)
    a = d[d.anchor].groupby("word").agg(interior=("interior", lambda s: sorted(set(s))),
                                        kind=("kind", lambda s: sorted(set(s))), n=("interior", "size"))
    #: one row per (word, X code): a word in two subfields counts in both
    long = t.assign(code=t.x_codes.str.split()).explode("code")
    long["sub"] = long.code.str.extract(r"^(X\d+(?:\.\d)?)")[0]
    kinds = ["cognition", "emotion", "volition", "perception", "attention", "argument", "other", "mixed"]
    L = ["# USAS X words by kind (EXPLORATORY)", "",
         "Producer `interiority_candidates.py --seeds`. Every primary-sense USAS X word less NLTK stopwords, %d "
         "words (the abstraction seat's seed list was 2,826 under a rule not reproduced here), each rated twice by "
         "deepseek-v4-flash (resolved: deepseek-flash) at temperature 0 in shuffled batches of %d, the same "
         "InteriorityCandidateTask and prompt as the candidates, anchors dread, grief, door, walk. Ratings: %s; "
         "per word: %s." % (len(w), BATCH, OUT, os.path.join(SHARED, "usasx_kinds_v1.csv")), "",
         "- interior (0-3) between passes: exact %.1f%%, within one %.1f%%, Spearman %.3f; kind agreement %.1f%%" % (
             100 * float((i1 == i2).mean()), 100 * float(((i1 - i2).abs() <= 1).mean()),
             float(spearmanr(i1, i2)[0]), 100 * float((k1 == k2).mean())),
         "- anchors: " + "; ".join("%s interior %s kind %s (n=%d)" % (x, r.interior, r.kind, r.n) for x, r in a.iterrows()),
         "- mean interior over all X words: %.2f; share rated >= 2 in both passes: %.1f%%" % (
             float(t.interior_mean.mean()), 100 * float(((i1 >= 2) & (i2 >= 2)).mean())), "",
         "## X subfield by agreed kind (words; a word in two subfields counts in both)", "",
         "| subfield | n | mean interior | " + " | ".join(kinds) + " |", "|---|---|---|" + "---|" * len(kinds)]
    for sub, g in long.groupby("sub"):
        L.append("| %s | %d | %.2f | " % (sub, len(g), g.interior_mean.mean()) +
                 " | ".join(str(int((g.kind == k).sum())) for k in kinds) + " |")
    L += ["", "## X words the rater does not read as inner states (agreed kind argument or other, mean interior < 1.5)", ""]
    low = t[t.kind.isin(["argument", "other"]) & (t.interior_mean < 1.5)].sort_values("interior_mean")
    L.append("%d words, e.g.: %s" % (len(low), ", ".join(low.word.head(80))))
    open(os.path.join(HERE, "USAS_X_KINDS.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
