"""Rate period-model neighbours of USAS X as interiority candidates, with an LLM, twice. (RH, 2026-09-25)

    .venv/bin/python -u interiority_candidates.py --pilot     three batches, printed
    .venv/bin/python -u interiority_candidates.py --run       both passes -> candidate_ratings_v1.parquet
    .venv/bin/python -u interiority_candidates.py --summary   -> INTERIORITY_CANDIDATES.md

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


def pool():
    """-> [(word, 'C17, C18')] for the 5,383-word vetting pool."""
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
        summary()


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


if __name__ == "__main__":
    main()
