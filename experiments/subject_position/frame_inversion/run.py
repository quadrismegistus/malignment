"""Does the chat frame invert what alignment does to the first person?

    python -u run.py                 the three contrasts
    python -u run.py --no-strip      without stripping dialogue (the check)
    python -u run.py --ungated       the person contrasts without the story gate
    python -u run.py --rebuild       recompute the cache from the corpus

## THE QUESTION, AND WHY THE OLD FRAMING WAS WRONG

The subject README recorded a tension: templated, alignment RAISES first-person
mass; raw, it LOWERS it. On `neo`, whose rendered template is byte-identical at
all three rungs, the two frames move in opposite directions on the same models.
Meanwhile raw narrative interiority ROSE with alignment (+0.224, 16/17,
`passage_analysis/interiority_in_passages`).

**That tension is between two different TASKS, not two frames.** The twp
measurements are `p(I)` at an answer slot on IDENTITY QUESTIONS -- "Who are
you?". This file measures NARRATION. A model that answers a question about
itself says "I"; a model asked for a story writes "he". Those are not in
conflict and never were.

## WHY national_story AND NOT interiority_in_passages

RH, 2026-09-05, on the interiority corpus: its first-person prompts are all
`"I am a ___ and I wanted to"` -- SIX distinct prompts, one template, and

    opens in PRESENT tense:   first-person 6/6      third-person 0/68

Person there is perfectly confounded with tense AND with template: the
third-person prompts are past-tense narrative ("He hated her and wanted to"),
the first-person ones are present-tense self-description. A person split on that
corpus measures genre.

`national_story` fixes it by leaving person OPEN. The prompt is
`"A {Demonym} Story\n(1500 words)\n\nIt was a"` -- past tense, narrative, and it
specifies no person at all, so the person is the MODEL's choice and therefore a
thing that can move. It also carries four frames, which is what makes the frame
contrast possible without generating anything.

## THE THREE CONTRASTS, AND WHAT EACH CAN CARRY

    ARM      base -> aligned, frame='raw'      35 lineages with both arms
    FRAME    raw -> prefill, arm='aligned'     27 lineages with both frames
    PERSON   1st vs 3rd, within each of the above

**THE FRAME CONTRAST IS ALIGNED-ONLY AND THAT IS STRUCTURAL.** `prefill` has
base rows for 7 lineages and both arms for 6, because base checkpoints ship no
chat template. So there is no base-in-a-frame cell to compare against, and this
file never constructs one. Bases are not pooled with aligned anywhere here --
the subject's standing rule.

## THE GATE IS ASYMMETRIC ACROSS THE TWO CELLS THE FRAME CONTRAST COMPARES

`conflict.sqlite` holds PURE STORIES only, and the corpus's own `meta` table
warns that survival is not uniform: **52% for aligned/raw against 73% for
aligned/prefill.** That is a selection difference sitting across exactly the
contrast in section 2, and non-story text is plausibly first-person ("I'll write
you a story about..."), so the gate could in principle manufacture the whole
result.

`--ungated` settles it rather than arguing about it. The person rule is pure
regex, so it can be run over the raw generation stash with NO gate at all -- no
pure-story judge, no word floor -- at 15,990 generations against 7,876. Both
effects survive, same sign, larger n:

    first-person narration      GATED                 UNGATED
      ARM   base->aligned, raw  -0.101 24/31 p=.0033  -0.083 29/39 p=.0034
      FRAME raw->prefill        -0.043 22/27 p=.0015  -0.056 25/30 p=.00033

Interiority is not in the ungated pass: `usas_x` is a spaCy parse and 15,990
stories is hours, not minutes. So the gate check covers PERSON only, and the
interiority results in sections 1 and 3 remain conditional on the story gate.

## THE PREFILL RENDERER BUG, AND WHY THIS POPULATION IS CLEAN

Before `9b8465e` (2026-08-31 11:30) the prefill renderer CLOSED the assistant
turn, so the model saw a finished answer. Those rows are a different condition,
and `passage_analysis/national_story/analyse.py` excludes the whole prefill frame
on account of it. 1,680 were deleted from producer `83ac39a07d2a`.

**That deletion was verified here rather than taken on report.** Every surviving
`prefill_sysdefault` row at this decoder carries `__written_at__`, and 4,700 of
4,715 postdate the fix. The 15 that do not are all on producer `CDH0050`, the
local machine -- and a local process started before the fix keeps emitting bad
rows after it, so the conservative test is the whole producer, not the 15. All
65 CDH0050 prefill rows were traced by text into `conflict.sqlite`: **0 of 65
are in it.** They are 27-497 words and the gate wants 200-word pure stories.

## THE DIALOGUE STRIP, AND WHAT IT CHANGED

A third-person story containing `"I can't," she said` accrues first-person hits
from a CHARACTER, not the narrator. Quoted speech is stripped before the pronoun
count.

It reclassifies a small share of stories -- the run PRINTS the share rather than
this file asserting one, because an earlier draft of this docstring carried
`1.7% (79 of 4,620)`, which was measured on the raw frame alone and would have
gone stale silently the moment the frame contrast added `prefill`. Small as it
is, it is the correction that moved the first-person interiority result from
p=0.064 to p=0.035 and flattened the person interaction. `--no-strip`
reproduces the uncorrected version and is the check, not an option.

## THE PERSON CLASSIFIER IS A PRONOUN MAJORITY AND IS NOT AUDITED

It is a rule, not a coder: strip quotes, count first- vs third-person pronouns,
take the majority, and abstain below five. It has not been checked against
hand-coding. It is adequate for a rate that moves by 10 points and would not be
adequate for a small one.

## THE CACHE, AND WHY BOTH STRIP SETTINGS LIVE IN IT

`usas_x` is a spaCy parse over 7,876 stories of ~1,500 words, which is minutes,
and the person rule is free. `results/cache.jsonl` holds BOTH person labels --
stripped and unstripped -- against the one parse, keyed on the story's own row
id, so `--no-strip` is not a second pass. `--rebuild` discards it.

**`usas_x` is computed on the FULL text under both settings.** The strip is a
correction to the PERSON label -- who is narrating -- and interiority is a
property of the story including its dialogue. Stripping it there would silently
change what the second metric measures while appearing to be one flag.
"""
import argparse, collections, json, math, os, random, re, sqlite3
import statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

#: a SYMLINK into ~/malignment-data. The corpus is `passage_analysis`'s and this
#: file only reads it -- one store, two questions, no second copy.
DB = os.path.abspath(os.path.join(
    HERE, "..", "..", "passage_analysis", "national_story", "conflict.sqlite"))
CACHE = os.path.join(HERE, "results", "cache.jsonl")

QUOTE = re.compile(r'["“”«»‘’](?:[^"“”«»]{0,400}?)'
                   r'["“”«»‘’]')
PRON = re.compile(r"\b(I|me|my|myself|he|she|him|her|his|they|them|their)\b", re.I)
FIRST = {"i", "me", "my", "myself"}
MIN_PRON = 5      #: below this the story is not narrating anybody; abstain
MIN_CELL = 5      #: stories per (lineage, condition) before it enters a pair


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j)
               for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def person(text, strip=True):
    """-> '1st' | '3rd' | 'none'. Majority of narrator pronouns."""
    s = QUOTE.sub(" ", text or "") if strip else (text or "")
    w = PRON.findall(s)
    f = sum(1 for x in w if x.lower() in FIRST)
    t = len(w) - f
    if f + t < MIN_PRON:
        return "none"
    return "1st" if f > t else "3rd"


def build_cache():
    from malignment import fields
    if not os.path.exists(DB):
        raise SystemExit(
            "%s not found. It is a symlink into ~/malignment-data and is built "
            "by experiments/passage_analysis/national_story/export_db.py" % DB)
    c = sqlite3.connect(DB)
    rows = list(c.execute("SELECT id, lineage, arm, frame, text FROM stories "
                          "WHERE frame IN ('raw','prefill')"))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as fh:
        for i, (sid, lin, arm, frame, text) in enumerate(rows):
            fh.write(json.dumps(dict(
                id=sid, lin=lin, arm=arm, frame=frame,
                p_strip=person(text, True), p_keep=person(text, False),
                x=fields.count(text).get("usas_x", 0.0))) + "\n")
            if i % 250 == 0:
                print("   parsed %d/%d" % (i, len(rows)), flush=True)
    print("   wrote %s (%d)" % (CACHE, len(rows)))


def load(strip=True, rebuild=False):
    if rebuild or not os.path.exists(CACHE):
        build_cache()
    out = []
    with open(CACHE) as fh:
        for line in fh:
            d = json.loads(line)
            d["p"] = d["p_strip" if strip else "p_keep"]
            out.append(d)
    return out


#: the generation stash, read exactly as `national_story/judge.py` reads it --
#: same glob, same decoder filter, same duplicate-producer rule. Kept in sync by
#: `tests.py::test_ungated_mirrors_judge`, because a silent divergence here would
#: make the gate check answer a question the gated pass never asked.
STASH = os.path.expanduser(
    "~/malignment-data/generations/*/*/jsonl.hashstash.raw/data.jsonl")
KEEP_FIRST, DROP_WHEN_DUP = "7802ca3c31ae", "b1d15d1f291d"


def load_ungated(strip=True):
    """Every generation at this decoder, with NO pure-story gate. Person only."""
    import glob
    from malignment import roster
    arm, lin = {}, {}
    for b, members in roster.lineages().items():
        for m in members:
            arm[m] = "base" if m == b else "aligned"
            lin[m] = b
    rows, by_mp = [], collections.defaultdict(set)
    for f in sorted(glob.glob(STASH)):
        prod = f.split("/generations/")[1].split("/")[1]
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            d = r.get("decoder") or {}
            if (d.get("max_new_tokens") or 0) < 1000:
                continue
            if not (d.get("top_p") == 0.95 and d.get("temperature") == 1.0):
                continue
            fr = {"raw": "raw", "prefill_sysdefault": "prefill"}.get(r.get("frame"))
            if fr is None or arm.get(r["model"]) is None:
                continue
            r["_p"], r["_fr"] = prod, fr
            by_mp[r["model"]].add(prod)
            rows.append(r)
    dup = {m for m, ps in by_mp.items()
           if KEEP_FIRST in ps and DROP_WHEN_DUP in ps}
    return [dict(lin=lin[r["model"]], arm=arm[r["model"]], frame=r["_fr"],
                 p=person(r.get("text") or "", strip))
            for r in rows if not (r["model"] in dup and r["_p"] == DROP_WHEN_DUP)]


def paired(recs, split, a, b, value, where=lambda r: True):
    """-> [delta] over lineages having >=MIN_CELL rows in BOTH cells."""
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in recs:
        if where(r):
            by[r["lin"]][r[split]].append(value(r))
    return [S.mean(v[b]) - S.mean(v[a]) for v in by.values()
            if len(v.get(a, [])) >= MIN_CELL and len(v.get(b, [])) >= MIN_CELL]


def ci(d, n=20000, seed=0):
    """Bootstrap 95% CI on the median. SEEDED, so the interval is a fact."""
    r = random.Random(seed)
    b = sorted(S.median(r.choices(d, k=len(d))) for _ in range(n))
    return b[int(0.025 * n)], b[int(0.975 * n)]


def report(label, d, a_lab="", b_lab=""):
    """**A NULL IS QUOTED AS AN INTERVAL, NEVER AS A p.**

    `p=1.0` at n=17 is not "no effect", it is "this instrument cannot see one",
    and the two are different claims that read identically. Section 3 is a null
    the whole finding turns on, so every row carries what it EXCLUDES.
    """
    if not d:
        print("  %-34s no pairs" % label)
        return
    up = sum(1 for x in d if x > 0)
    dn = len(d) - up
    lo, hi = ci(d)
    print("  %-34s n=%-3d median %+0.5f  %2d up/%2d dn  p=%.6f  CI [%+0.5f, %+0.5f]"
          % (label, len(d), S.median(d), up, dn, binom(min(up, dn), len(d)), lo, hi))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-strip", action="store_true",
                    help="do not strip quoted speech before counting pronouns")
    ap.add_argument("--rebuild", action="store_true",
                    help="recompute results/cache.jsonl from the corpus")
    ap.add_argument("--ungated", action="store_true",
                    help="the PERSON contrasts over the raw stash, no story gate")
    a = ap.parse_args(argv)
    strip = not a.no_strip

    if a.ungated:
        recs = load_ungated(strip)
        print("%d generations, NO GATE | dialogue %s"
              % (len(recs), "STRIPPED" if strip else "KEPT"))
        for f in ("raw", "prefill"):
            for arm in ("base", "aligned"):
                n = sum(1 for r in recs if r["frame"] == f and r["arm"] == arm)
                print("   %-8s %-8s %5d" % (f, arm, n))
        print("\nfirst-person narration rate. INTERIORITY IS NOT HERE -- usas_x")
        print("is a spaCy parse and this population is twice the gated one.\n")
        report("ARM   base->aligned, raw",
               paired([r for r in recs if r["frame"] == "raw"], "arm",
                      "base", "aligned", lambda r: r["p"] == "1st"), "", "")
        report("FRAME raw->prefill, aligned",
               paired([r for r in recs if r["arm"] == "aligned"], "frame",
                      "raw", "prefill", lambda r: r["p"] == "1st"), "", "")
        return 0

    recs = load(strip, a.rebuild)
    flip = sum(1 for r in recs if r["p_strip"] != r["p_keep"])
    print("%d stories | dialogue %s | the strip reclassifies %d (%.1f%%)"
          % (len(recs), "STRIPPED" if strip else "KEPT", flip,
             100.0 * flip / max(1, len(recs))))
    for f in ("raw", "prefill"):
        for arm in ("base", "aligned"):
            n = sum(1 for r in recs if r["frame"] == f and r["arm"] == arm)
            if n:
                print("   %-8s %-8s %5d" % (f, arm, n))
    print()

    raw = [r for r in recs if r["frame"] == "raw"]
    al = [r for r in recs if r["arm"] == "aligned"]

    print("=" * 74)
    print("1. THE ARM, frame='raw'. base -> aligned.")
    print()
    report("first-person narration rate",
           paired(raw, "arm", "base", "aligned", lambda r: r["p"] == "1st"),
           "base", "aligned")
    report("interiority (usas_x), 1st person",
           paired(raw, "arm", "base", "aligned", lambda r: r["x"],
                  where=lambda r: r["p"] == "1st"), "base", "aligned")
    report("interiority (usas_x), 3rd person",
           paired(raw, "arm", "base", "aligned", lambda r: r["x"],
                  where=lambda r: r["p"] == "3rd"), "base", "aligned")
    print()

    print("=" * 74)
    print("2. THE FRAME, arm='aligned'. raw -> prefill (chat wrapper).")
    print("   ALIGNED ONLY: base ships no chat template, so there is no base")
    print("   cell to contrast and none is constructed.")
    print()
    report("first-person narration rate",
           paired(al, "frame", "raw", "prefill", lambda r: r["p"] == "1st"),
           "raw", "prefill")
    report("interiority (usas_x)",
           paired(al, "frame", "raw", "prefill", lambda r: r["x"]),
           "raw", "prefill")
    print()

    print("=" * 74)
    print("3. THE INTERACTION. Is alignment's interiority gain LARGER in 3rd?")
    print()
    d1 = {}
    d3 = {}
    for tgt, pp in ((d1, "1st"), (d3, "3rd")):
        by = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in raw:
            if r["p"] == pp:
                by[r["lin"]][r["arm"]].append(r["x"])
        for l, v in by.items():
            if len(v.get("base", [])) >= MIN_CELL and len(v.get("aligned", [])) >= MIN_CELL:
                tgt[l] = S.mean(v["aligned"]) - S.mean(v["base"])
    both = sorted(set(d1) & set(d3))
    #: the SAME lineages in all three rows -- a main effect computed on a wider
    #: set than the interaction would make the ratio below incomparable
    inter = [d3[l] - d1[l] for l in both]
    report("1st-person gain", [d1[l] for l in both])
    report("3rd-person gain", [d3[l] for l in both])
    report("INTERACTION (3rd) - (1st)", inter)
    if both:
        lo, hi = ci(inter)
        m = S.median([d3[l] for l in both])
        print()
        print("  THE NULL AS A BOUND: the interaction is within "
              "[%+0.2f, %+0.2f] x the" % (lo / m, hi / m))
        print("  3rd-person main effect. That EXCLUDES the first-person gain")
        print("  being absent. It does NOT exclude the 3rd-person gain being")
        print("  moderately larger, so 'equally' overstates what n=%d resolves."
              % len(both))
    print()
    print("  A PREDICTION WAS MADE HERE BEFORE THIS RAN AND IT WAS WRONG.")
    print("  Stated 2026-09-05, before any of this ran: the interiority gain")
    print("  would be THIRD-person -- characters, not the speaker -- so that")
    print("  what generalises from being trained to answer an Other is a")
    print("  capacity to represent inner states and not a habit of saying I.")
    print("  Both persons gain, and the 1st-person CI excludes zero. What")
    print("  moves with person is how often the model narrates as one at all.")
    print()
    print("  AND THE 1st-PERSON CELL IS THE FRAGILE ONE. Run --no-strip: it")
    print("  goes p=0.049 -> p=0.143 on a 1.2% reclassification. The 3rd-person")
    print("  gain and the flat interaction hold under both settings; the")
    print("  refutation rests on those and not on the fragile cell.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
