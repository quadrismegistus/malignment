"""Clean the polar Warriner valence lexicon of AMBIGUOUS words, with an LLM, twice. (RH, 2026-09-26)

    .venv/bin/python -u valence_lexicon_clean.py --pilot        two batches, printed
    .venv/bin/python -u valence_lexicon_clean.py --run          passes 1 and 2 -> valence_clean_ratings_v1.parquet
    .venv/bin/python -u valence_lexicon_clean.py --fill         re-rate items a pass lost -> valence_clean_ratings_v1_fill*.parquet
    .venv/bin/python -u valence_lexicon_clean.py --tiebreak     pass 3 where the passes disagree
    .venv/bin/python -u valence_lexicon_clean.py --consensus    -> valence_clean_keep_v1.csv, VALENCE_LEXICON_CLEAN.md

WHY. The negative-share smell test (ARC_NEGATIVE_EXAMPLES.md) found words carrying negative mass without negative
meaning in context: old (3.19, "old man"), late, court, cut, weight, distance; cried (the period speech tag); and
`means` / `meant` mapped by the lemma rule to `mean` (2.43, cruel). A hand list of ten is a robustness check, not
a lexicon.

THE STANDARD (RH): AMBIGUITY, not literalness. Keep a word whose rated connotation is unambiguous, or clearly the
dominant reading, in English fiction 1600-2000 -- descriptive and concrete words included (blood, corpse, grave,
sunshine, flower): "otherwise we lose the concrete valences". Reject a word if a COMMON sense of it carries no such
connotation (old, late, court, the verb cut in "cut the bread"), if it is a speech or dialogue tag (cried = said),
function-like, or a word whose sense has shifted so that period fiction commonly uses it without the connotation.
(dark 5.08 and cold 4.32 sit inside the neutral band 4-6 and are not rated here at all.)

ITEMS. (1) Every POLAR Warriner lemma (valence < 4 or > 6; 5,993), shown with its rated direction. (2) The mapped
forms that land on a polar lemma by a rule other than identity (arc_type_norms' map: WordNet lemma, British and old
spellings, long-s), the top 2,500 by arc_fiction token mass, shown as "form (counted as: lemma, rated negative)":
does the FORM usually carry that lemma's rated sense? (means -> mean: no.) Other mapped forms inherit their lemma's
decision.

(3) VECTOR NEGATIVE-POLE CANDIDATES (RH: "do we need positive tokens?" -- not for negative share, computed per
content word; the vector's positive pole is mostly names and function words and is skipped): words the plain vector
valence places beyond where Warriner 3 falls on its axis, not Warriner lemmas or mapped forms, >= 500 arc tokens
(4,121), shown as "word (inferred negative)": the rater must CONFIRM the direction before the ambiguity standard.
EVERY ITEM also gets a 1-9 VALENCE on Warriner's scale for its dominant sense in fiction, with Warriner words as rung
examples (RH: "a question to rank the word by valence"): values for the vector additions, a calibration against the
human ratings on the ~6,000 Warriner lemmas in the same pool, and a flag for words whose period valence departs
from the modern rating.

DESIGN as interiority_precision.py: deepseek-v4-flash at temperature 0, 40 items a call, two shuffled passes, fills
for lost items, a third pass where they disagree; four anchors in every batch (murder, sunshine: keep; old, late:
reject); a batch whose anchors flip does not vote; consensus = majority, ties rejected (when in doubt, drop).
EXPLORATORY; a triage aid, RH's vetting decides.
"""
import collections, io, os, random, sys
from typing import List, Literal, Optional

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
from pydantic import BaseModel, Field                     # noqa: E402
from largeliterarymodels.task import Task                 # noqa: E402

SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
OUT = os.path.join(SHARED, "valence_clean_ratings_v1.parquet")
OUT3 = os.path.join(SHARED, "valence_clean_ratings_v1_pass3.parquet")
FILLS = [os.path.join(SHARED, "valence_clean_ratings_v1_fill%s.parquet" % s) for s in ("", "2", "3", "4")]
KEEP_CSV = os.path.join(SHARED, "valence_clean_keep_v1.csv")
BATCH, SEED, N_FORMS, VEC_FLOOR = 40, 20260927, 2500, 500
ANCHORS = {"murder": "rated negative", "sunshine": "rated positive", "old": "rated negative", "late": "rated negative"}
ANCHOR_KEEP = {"murder": True, "sunshine": True, "old": False, "late": False}

SYSTEM_PROMPT = """You screen English words for a valence lexicon used to measure how negative or positive fiction is.
Each word has a human valence rating; you are told whether it was rated NEGATIVE or POSITIVE. Decide whether the word
reliably carries that connotation in English fiction written between 1600 and today.

KEEP the word if its rated connotation is unambiguous, or is clearly the dominant reading, in fiction. Concrete and
descriptive words count: "blood", "corpse", "grave", "wound" (negative) and "sunshine", "flower", "feast", "kiss"
(positive) carry their connotation even when used literally. Keep them.

REJECT the word if ANY COMMON sense of it carries no such connotation, so that counting it would often count a
neutral use: "old" ("the old man"), "late" ("late afternoon"), "court" (courtyard, courtship), "cut" ("cut the
bread"), "weight", "distance", "fire" ("by the fire"). Reject speech or dialogue tags ("cried" meaning "said"),
function-like words, and words whose sense has shifted so that older fiction commonly uses them neutrally.

Some items are inflected or respelled FORMS, shown as "form (counted as: lemma, rated ...)". Judge whether the FORM
as written usually carries the LEMMA's rated sense: "means (counted as: mean, rated negative)" is rejected, because
"means" is almost always "by means of", not "cruel".

Some items are marked "(inferred negative)": no human rated them; a statistical model guessed. KEEP one only if the
word really does carry a negative connotation AND meets the standard above. Reject it as wrong_direction if it is not
negative ("utterly", "together"), and reject proper names as proper_name.

ALSO RATE EVERY ITEM'S VALENCE on a 1-9 scale (1 = very negative, 5 = neutral, 9 = very positive), for its dominant
sense in fiction, whatever you decide about keeping it. Rungs, from human ratings: 1-1.5 murder, torture; 2 death,
pain, prison; 3 fear, loss, mistake; 4 fall, weight; 5 street, work, change; 6 way, little; 7 water, heart, book;
8 love, smile, peaceful; 8.5 happy, vacation. Decimals are fine.

When in doubt, reject: a wrong inclusion is costlier than a wrong exclusion. Return every item, its text exactly as
given before any parenthesis, with keep, a reason, the valence, and for a rejection the competing neutral sense."""


class ItemRating(BaseModel):
    form: str = Field(description="the word or form exactly as given, without the parenthesis")
    keep: bool
    reason: Literal["clear_connotation", "competing_neutral_sense", "speech_tag", "function_like", "period_shift",
                    "mapping_mismatch", "wrong_direction", "proper_name", "other"]
    valence: float = Field(description="1-9, Warriner's scale, dominant sense in fiction")
    competing_sense: Optional[str] = Field(default=None, description="for a rejection: the neutral sense, a few words")


class BatchItems(BaseModel):
    ratings: List[ItemRating]


class ValenceCleanTask(Task):
    name = "valence_lexicon_clean_v2"
    schema = BatchItems
    system_prompt = SYSTEM_PROMPT
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    usage_log = True


def items():
    """-> [(form, shown text, kind, lemma)]: polar lemmas and the top mapped forms by arc token mass."""
    import arc_interiority as A
    import arc_type_norms as N
    val = {w: d["warriner_valence"] for w, d in N.lexicons()["warriner"].items()}
    direction = lambda v: "rated negative" if v < 4 else "rated positive"
    lem = sorted(w for w, v in val.items() if v < 4 or v > 6)
    out = [(w, "%s (%s)" % (w, direction(val[w])), "lemma", w) for w in lem if w not in ANCHORS]
    M = pd.read_parquet(N.MAP)
    M = M[(M.source == "warriner") & (M.rule != "self")]
    M = M[M.entry.map(lambda e: val[e] < 4 or val[e] > 6)]
    M = M[~M.form.isin(set(lem))].drop_duplicates("form")
    sql = f"""SELECT k AS form, sum(v) AS n FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS}))
      ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v WHERE k IN (SELECT form FROM fm) GROUP BY form
      ORDER BY n DESC LIMIT {N_FORMS} FORMAT TSVWithNames"""
    T = pd.read_csv(io.StringIO(A.ch_query(sql, {"fm": ("form String", [(f,) for f in M.form])})), sep="\t", keep_default_na=False)
    ent = dict(zip(M.form, M.entry))
    out += [(f, "%s (counted as: %s, %s)" % (f, ent[f], direction(val[ent[f]])), "form", ent[f]) for f in T.form]
    import numpy as np
    V = pd.read_parquet(os.path.join(SHARED, "vad_norms.parquet"), columns=["VAD-Valence.Warriner.median"])["VAD-Valence.Warriner.median"]
    V = V[V.index.map(lambda w: isinstance(w, str) and w.isalpha() and w.islower())]
    common = [w for w in val if w in V.index]
    b, a = np.polyfit([val[w] for w in common], V.loc[common].values, 1)
    _, sw, _ = A.lists_expanded()
    allmapped = set(pd.read_parquet(N.MAP).query("source == 'warriner'").form)
    cand = V[(V < a + 3.0 * b) & ~V.index.isin(set(val) | allmapped | sw | set(ANCHORS))]
    sql = f"""SELECT k AS w, sum(v) AS n FROM (SELECT _id, freqs FROM lltk.text_freqs FINAL WHERE _id IN ({A.REPS}))
      ARRAY JOIN mapKeys(freqs) AS k, mapValues(freqs) AS v WHERE k IN (SELECT w FROM c) GROUP BY w HAVING n >= {VEC_FLOOR}
      FORMAT TSVWithNames"""
    C = pd.read_csv(io.StringIO(A.ch_query(sql, {"c": ("w String", [(w,) for w in cand.index])})), sep="\t", keep_default_na=False)
    have = {f for f, *_ in out}
    out += [(w, "%s (inferred negative)" % w, "vector", w) for w in sorted(C.w) if w not in have]
    assert len({f for f, *_ in out}) == len(out)
    return out


def render(chunk):
    return ("Screen each item. Return each word EXACTLY as given before its parenthesis.\n\n" + "\n".join(s for _, s in chunk))


def make_batches(its, passes=(1, 2), seed=SEED):
    rng = random.Random(seed)
    out = []
    for ps in passes:
        w = [(f, s) for f, s, *_ in its]
        rng.shuffle(w)
        for b in range(0, len(w), BATCH):
            chunk = w[b:b + BATCH] + [(a, "%s (%s)" % (a, d)) for a, d in ANCHORS.items()]
            rng.shuffle(chunk)
            out.append(dict(pass_=ps, batch=b // BATCH, items=chunk))
    return out


#: --workers N (RH, 2026-09-26: "run it workers=32"); the Task caches finished calls, so a restart reuses them
WORKERS = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4


def rate(bs, workers=None):
    workers = workers or WORKERS
    t = ValenceCleanTask()
    errs = {}
    res = t.map([render(b["items"]) for b in bs], metadata_list=[{"pass": b["pass_"], "batch": b["batch"]} for b in bs],
                num_workers=workers, errors=errs)
    rows, missing, extra = [], 0, 0
    for b, r in zip(bs, res):
        want = {f for f, _ in b["items"]}
        got = {}
        for x in (r.ratings if r else []):
            f = x.form.strip().lower()
            if f in want and f not in got:
                got[f] = x
            else:
                extra += 1
        missing += len(want - set(got))
        for f, x in got.items():
            rows.append(dict(form=f, pass_=b["pass_"], batch=b["batch"], keep=x.keep, reason=x.reason, valence=x.valence,
                             competing_sense=x.competing_sense, anchor=f in ANCHORS))
    return rows, missing, extra, len(errs)


def rated():
    return pd.concat([pd.read_parquet(x).assign(src=os.path.basename(x)) for x in [OUT] + FILLS if os.path.exists(x)])


def consensus(its):
    d = pd.concat([rated()] + ([pd.read_parquet(OUT3).assign(src=os.path.basename(OUT3))] if os.path.exists(OUT3) else []))
    key = list(zip(d.src, d.pass_, d.batch))
    a = d[d.anchor]
    fb = set(zip(*[a[a.form.map(ANCHOR_KEEP) != a.keep][c] for c in ("src", "pass_", "batch")]))
    nb = len(set(key))
    assert len(fb) <= 0.02 * nb, ("too many batches lost calibration", len(fb), nb)
    d = d[[k not in fb for k in key]]
    anc = d[d.anchor].groupby("form").keep.agg(lambda s: sorted(set(s)))
    for x, want in ANCHOR_KEEP.items():
        assert anc.get(x) == [want], ("anchor moved", x, anc.get(x))
    d = d[~d.anchor]
    g = d.groupby("form")
    n = g.keep.size()
    K = pd.DataFrame({"keep": g.keep.agg(lambda s: bool(sum(s) * 2 > len(s))),
                      "reason": g.reason.agg(lambda s: collections.Counter(s).most_common(1)[0][0]),
                      "competing_sense": g.competing_sense.agg(lambda s: next((x for x in s if x), None)), "n_ratings": n,
                      "llm_valence": g.valence.median()})
    meta = {f: (k, l) for f, _, k, l in its}
    K["kind"] = [meta[f][0] for f in K.index]
    K["lemma"] = [meta[f][1] for f in K.index]
    for x, want in ANCHOR_KEEP.items():
        K.loc[x] = dict(keep=want, reason="clear_connotation" if want else "competing_neutral_sense", competing_sense=None,
                        n_ratings=0, kind="lemma", lemma=x, llm_valence=float(a[a.form == x].valence.median()))
    assert not os.path.exists(KEEP_CSV), "refusing to overwrite " + KEEP_CSV
    K.reset_index().rename(columns={"index": "form"}).to_csv(KEEP_CSV, index=False)
    agree = d[d.pass_.isin([1, 2])].pivot_table(index="form", columns="pass_", values="keep", aggfunc="first").dropna()
    import arc_type_norms as N
    val = {w: dd["warriner_valence"] for w, dd in N.lexicons()["warriner"].items()}
    L = ["# Cleaning the polar Warriner valence lexicon of ambiguous words (EXPLORATORY)", "",
         "Producer `valence_lexicon_clean.py` (standard and design in its docstring). Per item: %s." % KEEP_CSV, "",
         "- pass 1 vs pass 2 agreement on keep: %.1f%%; ties rejected: %d; batches dropped for flipped anchors: %d of %d" % (
             100 * float((agree[1] == agree[2]).mean()), int((g.keep.sum() * 2 == n).sum()), len(fb), nb), ""]
    from scipy.stats import spearmanr, pearsonr
    lm = K[K.kind == "lemma"].copy()
    lm["warriner"] = [val.get(w) for w in lm.index]
    lm = lm.dropna(subset=["warriner", "llm_valence"])
    L += ["- CALIBRATION, LLM valence vs Warriner on %d polar lemmas: Spearman %.3f, Pearson %.3f, mean |diff| %.2f; on kept "
          "lemmas only: Spearman %.3f" % (len(lm), spearmanr(lm.llm_valence, lm.warriner)[0], pearsonr(lm.llm_valence, lm.warriner)[0],
                                          (lm.llm_valence - lm.warriner).abs().mean(), spearmanr(lm[lm.keep].llm_valence, lm[lm.keep].warriner)[0]),
          "- largest LLM-above-Warriner gaps (period or sense shift?): " + ", ".join("%s %.1f/%.1f" % (w, r.llm_valence, r.warriner) for w, r in lm.assign(d=lm.llm_valence - lm.warriner).nlargest(15, "d").iterrows()),
          "- largest LLM-below-Warriner gaps: " + ", ".join("%s %.1f/%.1f" % (w, r.llm_valence, r.warriner) for w, r in lm.assign(d=lm.llm_valence - lm.warriner).nsmallest(15, "d").iterrows()), ""]
    for kind, lab in (("lemma", "polar lemmas"), ("form", "mapped forms"), ("vector", "vector negative-pole candidates")):
        s = K[K.kind == kind]
        L.append("- %s: %d rated, %d kept (%.0f%%); rejections by reason: %s" % (lab, len(s), int(s.keep.sum()), 100 * s.keep.mean(),
                 ", ".join("%s %d" % (r, c) for r, c in s[~s.keep].reason.value_counts().items())))
    for sign, lab in ((-1, "negative"), (1, "positive")):
        s = K[(K.kind == "lemma") & K.index.map(lambda w: (val.get(w, 5) - 5) * sign > 1)]
        L += ["", "Rejected %s lemmas (sample): " % lab + "; ".join("%s (%s)" % (w, r.competing_sense or r.reason) for w, r in s[~s.keep].head(60).iterrows())]
    v = K[K.kind == "vector"]
    L += ["", "Vector candidates kept (most frequent first is not available here; alphabetical sample): " + ", ".join(
        "%s %.1f" % (w, r.llm_valence) for w, r in v[v.keep].head(60).iterrows())]
    f = K[K.kind == "form"]
    L += ["", "Rejected mapped forms (sample): " + "; ".join("%s -> %s (%s)" % (w, r.lemma, r.competing_sense or r.reason) for w, r in f[~f.keep].head(40).iterrows())]
    open(os.path.join(HERE, "VALENCE_LEXICON_CLEAN.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    its = items()
    print("items: %d (%s)" % (len(its), dict(collections.Counter(k for *_, k, _ in its))))
    if "--pilot" in sys.argv:
        rows, miss, extra, nerr = rate(make_batches(its)[:2], workers=2)
        d = pd.DataFrame(rows)
        print("pilot: %d rows, %d missing, %d extra, %d failed" % (len(d), miss, extra, nerr))
        print(d.sort_values(["keep", "reason"]).to_string(index=False))
    elif "--run" in sys.argv:
        assert not os.path.exists(OUT), "refusing to overwrite " + OUT
        rows, miss, extra, nerr = rate(make_batches(its))
        pd.DataFrame(rows).to_parquet(OUT, index=False)
        print("-> %s: %d rows; %d missing, %d extra, %d failed calls" % (OUT, len(rows), miss, extra, nerr))
    elif "--fill" in sys.argv:
        dest = next(x for x in FILLS if not os.path.exists(x))
        d = rated()
        d = d[~d.anchor]
        shown = {f: s for f, s, *_ in its}
        rows, stats = [], []
        for ps in (1, 2):
            got = set(d[d.pass_ == ps].form)
            sub = [(f, shown[f], None, None) for f in shown if f not in got]
            if not sub:
                continue
            r, miss, extra, nerr = rate(make_batches(sub, passes=(ps,), seed=SEED + 10 + ps))
            rows += r
            stats.append("pass %d: %d lost, %d still missing, %d failed" % (ps, len(sub), miss, nerr))
        if not stats:
            print("nothing lost; no fill written")
            return
        pd.DataFrame(rows).to_parquet(dest, index=False)
        print("-> %s\n  " % dest + "\n  ".join(stats))
    elif "--tiebreak" in sys.argv:
        assert not os.path.exists(OUT3), "refusing to overwrite " + OUT3
        d = rated()
        w = d[~d.anchor].pivot_table(index="form", columns="pass_", values="keep", aggfunc="first").dropna()
        dis = set(w.index[w[1] != w[2]])
        shown = {f: s for f, s, *_ in its}
        rows, miss, extra, nerr = rate(make_batches([(f, shown[f], None, None) for f in sorted(dis)], passes=(3,), seed=SEED + 3))
        pd.DataFrame(rows).to_parquet(OUT3, index=False)
        print("-> %s: %d items; %d missing, %d failed" % (OUT3, len(dis), miss, nerr))
    elif "--consensus" in sys.argv:
        consensus(its)


if __name__ == "__main__":
    main()
