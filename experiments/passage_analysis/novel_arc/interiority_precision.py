"""Precision-first re-rating of the interiority word lists, spelling variants included. (RH, 2026-09-25)

    .venv/bin/python -u interiority_precision.py --pilot       two batches, printed
    .venv/bin/python -u interiority_precision.py --run         passes 1 and 2 -> precision_ratings_v2.parquet
    .venv/bin/python -u interiority_precision.py --fill        re-rate forms a pass lost -> precision_ratings_v2_fill.parquet
    .venv/bin/python -u interiority_precision.py --tiebreak    pass 3 where the two disagree on keep
    .venv/bin/python -u interiority_precision.py --consensus   -> precision_keep_v2.csv, INTERIORITY_PRECISION.md

WHY A SECOND RATING. The first triage (interiority_candidates.py, v1) asked whether a word CAN describe a
mind, and let through words whose commonest use is not mental: `bright` (clever / shining), `like`
(to like / the preposition), `would` (to wish / the modal). Over the arc_fiction history the candidate
list's tokens were dominated by exactly these (ARC_INTERIORITY.md: would 7.9%, like 4.4%, say 2.6%), and
text_freqs counts surface forms, which cannot tell the senses apart. RH: go for PRECISION, not recall.

THE RULE the rater applies: KEEP a form only if EVERY common sense of it, in English writing of the
period, names or predicates a subject's mental state, process or act. Reject any form with a common
non-mental sense, and always reject function words, modals and auxiliaries, speech and communication
verbs (say, tell, ask, answer), and generic verbs (get, find, go). The rater names the competing sense
when it rejects, for audit.

ITEMS: every base word of clean X (1,526) and the period candidates (2,161), and every MorphAdorner
variant that spells one of them (11,414), each variant shown with the word it spells so it is rated AS A
FORM (MorphAdorner lists `red` as an old spelling of `read`; `red` is rejected on its own senses). Long-s
OCR readings are mechanical and inherit their base form's decision downstream (arc_interiority.py).
RH's hand removals are hard exclusions whatever the rating (RH_REMOVED).

DESIGN as v1: deepseek-v4-flash (resolved server-side to deepseek-flash) at temperature 0, 40 forms a
call, two independently shuffled passes, a third where they disagree on keep; four anchors in every
batch (regretted, dreaded: keep; bright, would: reject). Consensus keep = majority of the ratings.
A triage aid; RH's vetting decides.
"""
import collections, json, os, random, sys
from typing import List, Literal, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
from pydantic import BaseModel, Field                     # noqa: E402
from largeliterarymodels.task import Task                 # noqa: E402

SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
OUT = os.path.join(SHARED, "precision_ratings_v2.parquet")
OUT3 = os.path.join(SHARED, "precision_ratings_v2_pass3.parquet")
#: forms a pass lost (13 calls failed on DeepSeek's balance-based concurrency cap of 5; the rater also
#: echoed some old spellings back modernised, so their rows did not match), re-rated under the same pass
#: the first fill ran into an exhausted DeepSeek balance (402) with pass 2 still 1,006 short, so fills are
#: numbered and each re-rates what the run and every earlier fill left missing
FILLS = [os.path.join(SHARED, "precision_ratings_v2_fill%s.parquet" % s) for s in ("", "2", "3", "4")]
OUT_FILL = FILLS[0]


def rated():
    import pandas as pd
    return pd.concat([pd.read_parquet(x) for x in [OUT] + FILLS if os.path.exists(x)])
KEEP_CSV = os.path.join(SHARED, "precision_keep_v2.csv")
BATCH, SEED = 40, 20260926
#: keep-anchors are OUTSIDE the pool (think and grief are in it); the reject-anchors bright and would
#: are in the pool but on RH's removal list, so rating them only as anchors loses nothing
ANCHORS = {"regretted": None, "dreaded": None, "bright": None, "would": None}
ANCHOR_KEEP = {"regretted": True, "dreaded": True, "bright": False, "would": False}
#: RH, 2026-09-25, from the top 200 candidates by token mass: 1-24 (would .. fear), then certainly,
#: loved, ought, seem, wait, waiting, smiled, trying, bright
RH_REMOVED = set("""would like say looked get tell look love asked seemed told find sure looking answered mean
says read ask happy need answer certain fear certainly loved ought seem wait waiting smiled trying
bright""".split())

SYSTEM_PROMPT = """You screen English word forms for a list that must contain ONLY words of inner life.
Precision matters far more than recall: a wrong inclusion is costly, a wrong exclusion is not.

KEEP a form only if EVERY common sense of it, in English writing from the 1600s to today, names or
predicates a subject's mental state, process or act: thinking, believing, knowing, remembering,
imagining, feeling an emotion, wanting, intending, perceiving, attending, deciding.

REJECT a form if ANY common sense of it is not mental. Examples: "bright" (shining), "like" (the
preposition, "similar to"), "cold" (temperature), "moved" (physical motion), "red" (the colour),
"sense" (meaning of a word), "mind" (to look after), "feeling" (touching).
ALWAYS REJECT: function words (pronouns, prepositions, conjunctions, articles); modal and auxiliary
verbs (would, should, might, ought, can, will, do, have, be); speech and communication verbs (say,
tell, ask, answer, reply, remark, explain); generic verbs (get, find, go, make, take, seem, look); and
words for outward expressions of feeling (smile, frown, laugh, sigh, weep).

Some forms are old spellings of a modern word; the modern word is given. Judge THE FORM AS WRITTEN: if the
old spelling is also an ordinary word with another meaning (red, as a spelling of read), reject it.

For every form return keep (true/false), kind (the main sense), and, when you reject a word that has a
mental sense, the competing non-mental sense in a few words."""


class FormRating(BaseModel):
    form: str = Field(description="the form exactly as given")
    keep: bool
    kind: Literal["cognition", "emotion", "volition", "perception", "attention", "function", "speech", "other"]
    competing_sense: Optional[str] = Field(default=None, description="for a rejected form with a mental sense: the non-mental sense")


class BatchForms(BaseModel):
    ratings: List[FormRating]


class InteriorityPrecisionTask(Task):
    name = "interiority_precision_v2"
    schema = BatchForms
    system_prompt = SYSTEM_PROMPT
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    usage_log = True


def items():
    """-> [(form, spelling_of or None, source)] : base words of clean X and candidates, and their MorphAdorner variants."""
    import arc_interiority as A
    B = A.base_lists()
    base = {w: "cleanx" for w in B["cleanx"]}
    base.update({w: "cand" for w in B["cand"]})
    var = collections.defaultdict(set)
    for line in open(A.MORPH, encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 2 and p[0].isalpha() and p[1].isalpha():
            v, m = p[0].lower(), p[1].lower()
            if m in base and v not in base:
                var[v].add(m)
    out = [(w, None, s) for w, s in sorted(base.items())]
    out += [(v, ", ".join(sorted(ms)), "variant:" + "+".join(sorted({base[m] for m in ms}))) for v, ms in sorted(var.items())]
    assert len(out) == 15101, len(out)
    assert not {"regretted", "dreaded"} & {f for f, _, _ in out}, "a keep-anchor is inside the pool"
    assert {"bright", "would"} <= RH_REMOVED
    return out


def render(chunk, echo=False):
    return ("Screen each form." + (" Return each form EXACTLY as given, old spelling unchanged." if echo else "")
            + "\n\n" + "\n".join(
        f if not of else "%s  (old spelling of: %s)" % (f, of) for f, of in chunk))


def make_batches(its, passes=(1, 2), seed=SEED, echo=False):
    rng = random.Random(seed)
    out = []
    for ps in passes:
        w = [(f, of) for f, of, _ in its if f not in ANCHORS]
        rng.shuffle(w)
        for b in range(0, len(w), BATCH):
            chunk = w[b:b + BATCH] + [(a, None) for a in ANCHORS]
            rng.shuffle(chunk)
            out.append(dict(pass_=ps, batch=b // BATCH, items=chunk, echo=echo))
    return out


def rate(bs, workers=4):
    t = InteriorityPrecisionTask()
    errs = {}
    res = t.map([render(b["items"], b.get("echo", False)) for b in bs], metadata_list=[{"pass": b["pass_"], "batch": b["batch"]} for b in bs],
                num_workers=workers, errors=errs)
    rows, missing, extra = [], 0, 0
    for b, r in zip(bs, res):
        want = {f for f, _ in b["items"]}
        got = {}
        for x in (r.ratings if r else []):
            if x.form in want and x.form not in got:
                got[x.form] = x
            else:
                extra += 1
        missing += len(want - set(got))
        for f, x in got.items():
            rows.append(dict(form=f, pass_=b["pass_"], batch=b["batch"], keep=x.keep, kind=x.kind,
                             competing_sense=x.competing_sense, anchor=f in ANCHORS))
    return rows, missing, extra, len(errs)


def main():
    import pandas as pd
    its = items()
    if "--pilot" in sys.argv:
        bs = make_batches(its)[:2]
        rows, miss, extra, nerr = rate(bs, workers=2)
        d = pd.DataFrame(rows)
        print("pilot: %d rows, %d missing, %d extra, %d failed" % (len(d), miss, extra, nerr))
        print(d.sort_values(["keep", "kind"]).to_string(index=False))
    elif "--run" in sys.argv:
        assert not os.path.exists(OUT), "refusing to overwrite " + OUT
        rows, miss, extra, nerr = rate(make_batches(its))
        pd.DataFrame(rows).to_parquet(OUT, index=False)
        print("-> %s: %d rows; %d missing, %d extra, %d failed calls" % (OUT, len(rows), miss, extra, nerr))
    elif "--fill" in sys.argv:
        dest = next(x for x in FILLS if not os.path.exists(x))
        d = rated()
        d = d[~d.anchor]
        pool = [f for f, _, _ in its if f not in ANCHORS]
        of = {f: o for f, o, _ in its}
        rows, stats = [], []
        for ps in (1, 2):
            got = set(d[d.pass_ == ps].form)
            sub = [(f, of[f], None) for f in pool if f not in got]
            if not sub:
                continue
            r, miss, extra, nerr = rate(make_batches(sub, passes=(ps,), seed=SEED + 10 + ps, echo=True))
            rows += r
            stats.append("pass %d: %d lost, %d still missing, %d extra, %d failed calls" % (ps, len(sub), miss, extra, nerr))
        pd.DataFrame(rows).to_parquet(dest, index=False)
        print("-> %s\n  " % dest + "\n  ".join(stats))
    elif "--tiebreak" in sys.argv:
        assert not os.path.exists(OUT3), "refusing to overwrite " + OUT3
        d = rated()
        w = d[~d.anchor].pivot_table(index="form", columns="pass_", values="keep", aggfunc="first").dropna()
        dis = set(w.index[w[1] != w[2]])
        of = {f: o for f, o, _ in its}
        sub = [(f, of[f], None) for f in sorted(dis)]
        rows, miss, extra, nerr = rate(make_batches(sub, passes=(3,), seed=SEED + 3))
        pd.DataFrame(rows).to_parquet(OUT3, index=False)
        print("-> %s: %d forms; %d missing, %d extra, %d failed calls" % (OUT3, len(dis), miss, extra, nerr))
    elif "--consensus" in sys.argv:
        consensus(its)


def consensus(its):
    import pandas as pd
    d = pd.concat([rated()] + ([pd.read_parquet(OUT3)] if os.path.exists(OUT3) else []))
    #: a batch whose anchors flipped has lost its calibration and does not vote (2 of 73 tie-break batches,
    #: which hold only forms the two passes split on and push the rater stricter: `regretted` rejected as
    #: "also to express regret, a speech act"); the guard below still holds over what remains
    a = d[d.anchor]
    flipped = a[a.form.map(ANCHOR_KEEP) != a.keep]
    fb = set(zip(flipped.pass_, flipped.batch))
    #: pass 1/2 batch numbers are reused by fills (same pass_ label, new call), so a flip there cannot be
    #: localised by (pass_, batch); none has occurred, and the assert keeps it that way
    assert all(ps == 3 for ps, _ in fb), ("anchor flip outside the tie-break", sorted(fb))
    n3 = d[d.pass_ == 3].batch.nunique()
    assert len(fb) <= 0.05 * n3, ("too many tie-break batches lost calibration", len(fb), n3)
    d = d[[(ps, b) not in fb for ps, b in zip(d.pass_, d.batch)]]
    anc = d[d.anchor].groupby("form").keep.agg(lambda s: sorted(set(s)))
    for a, want in ANCHOR_KEEP.items():
        assert anc.get(a) == [want], ("anchor moved", a, anc.get(a))
    d = d[~d.anchor]
    src = {f: s for f, _, s in its}
    of = {f: o for f, o, _ in its}
    g = d.groupby("form")
    keep = g.keep.agg(lambda s: bool(sum(s) * 2 > len(s)))
    kind = g.kind.agg(lambda s: collections.Counter(s).most_common(1)[0][0])
    comp = g.competing_sense.agg(lambda s: next((x for x in s if x), None))
    n = g.keep.size()
    agree12 = d[d.pass_.isin([1, 2])].groupby("form").keep.agg(lambda s: len(set(s)) == 1)
    K = pd.DataFrame({"keep_llm": keep, "kind": kind, "competing_sense": comp, "n_ratings": n})
    K["source"] = [src[f] for f in K.index]
    K["spelling_of"] = [of[f] for f in K.index]
    K["rh_removed"] = [f in RH_REMOVED for f in K.index]
    K["keep"] = K.keep_llm & ~K.rh_removed
    K.reset_index().rename(columns={"index": "form"}).to_csv(KEEP_CSV, index=False)
    base = K[K.spelling_of.isna()]
    var = K[K.spelling_of.notna()]
    L = ["# Precision-first re-rating of the interiority lists (EXPLORATORY)", "",
         "Producer `interiority_precision.py`. %d forms: %d base words (clean X %d, period candidates %d) and %d "
         "MorphAdorner variants rated as forms. Keep only if every common sense is mental; function words, modals, "
         "speech and generic verbs always rejected. deepseek-v4-flash (resolved deepseek-flash), temperature 0, "
         "two shuffled passes and a third where they disagree on keep; consensus = majority. RH's hand removals "
         "(%d) are excluded whatever the rating. Per form: %s." % (
             len(K), len(base), int((base.source == "cleanx").sum()), int((base.source == "cand").sum()), len(var),
             len(RH_REMOVED), KEEP_CSV), "",
         "- pass 1 vs pass 2 agreement on keep: %.1f%% (%d forms tie-broken)" % (
             100 * float(agree12.mean()), int((~agree12).sum())),
         "- ties (equal keep and reject ratings, the tie-break having missed the form) rejected, precision "
         "first: %d" % int((g.keep.sum() * 2 == n).sum()),
         "- tie-break batches dropped because an anchor flipped: %d of %d" % (len(fb), n3),
         "- anchors stable: " + ", ".join("%s %s" % (a, anc.get(a)) for a in ANCHOR_KEEP), "",
         "| | forms | kept | kept % |", "|---|---|---|---|"]
    for lab, sub in (("clean X, base words", base[base.source == "cleanx"]), ("candidates, base words", base[base.source == "cand"]),
                     ("MorphAdorner variants", var)):
        L.append("| %s | %d | %d | %.1f%% |" % (lab, len(sub), int(sub.keep.sum()), 100 * float(sub.keep.mean())))
    L += ["", "Rejected base words with a named competing sense (sample): " + "; ".join(
        "%s (%s)" % (f, r.competing_sense) for f, r in base[~base.keep & base.competing_sense.notna()].head(40).iterrows()),
          "", "Kept base words by kind: " + ", ".join("%s %d" % (k, int(n)) for k, n in base[base.keep].kind.value_counts().items())]
    open(os.path.join(HERE, "INTERIORITY_PRECISION.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
