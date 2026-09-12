#!/usr/bin/env python
"""Does the SYNTAGMATIC axis depend on the attention mechanism?

    python run.py
    python run.py --corpus f11_l2 --min-sents 2

## WHY THIS QUESTION EXISTS, AND WHY IT SHOULD HAVE COME OUT THE OTHER WAY

The other questions in this subject all read the PARADIGMATIC axis: which word
goes in a slot. That is the unembedding matrix and the output softmax -- the
hidden state scored against every vocabulary item and normalised against all of
them -- and every model in the census has one, transformer or not. Their nulls
are therefore cheap: they read the architecturally invariant part.

**Attention is a COMBINATION mechanism.** It relates positions within a
sequence, items present together in the chain, Saussure's *in praesentia*. That
is the syntagmatic axis by definition, and it is the one place the census has an
actual reason to expect a difference. `jakobson_space` already measures it:
sentence-to-sentence drift through bge space, cohesion, directedness.

**The prediction was that architecture would show here and it does not.** Stated
before the run and recorded because a failed prediction is worth more than an
unstated one.

## THE JOIN KEY IS `prompt`, NOT `prompt_id`

`prompt_id` is assigned PER MODEL in this parquet: pairwise overlap between any
two of these models is exactly ZERO, and a join on it returns an empty frame
rather than an error. The prompt TEXT overlaps on 147-190. This cost one silent
empty result before it was noticed.

## ONLY THREE OF THE FIVE METRICS CLEAR THEIR OWN NOISE

Measured, across-model spread against the median within-model IQR over prompts:

    mean_drift      1.77x      mean_pairwise   1.95x     bits_per_byte  2.96x
    directedness    0.95x      ordering        0.66x     <- BELOW THE NOISE

`directedness` and `ordering` are reported and then not interpreted. On a first
pass `falcon-mamba-7b` ranked 1/6 and 6/6 on those two and it would have read as
the attention-free model being extreme; it is inside the prompt-to-prompt noise.
`drift_geometry/README.md` separately warns that only the length-free metrics
are comparable at all, which is why the cumulative ones are not here.
"""
import argparse
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))

PARQUET = os.path.expanduser("~/malignment-data/jakobson_space/passages_std.parquet")
#: length-free only. The first three clear their noise floor; the last two do not.
#: **`bits_per_byte` IS THE SUPERSEDED EXTERNAL AXIS AND IS LABELLED, NOT READ
#: AS "FLUENCY".** Two facts about it, both from
#: `passage_analysis/jakobson_space/README.md`, which should have been read
#: before this file was written:
#:
#:   1. It is not the generating model's perplexity. It is `itazap/blt-1b-hf`,
#:      one byte-latent reference scoring every row uniformly -- an external
#:      referee's opinion of the TEXT, not the generator's confidence.
#:   2. **It is not the campaign's surprisal axis any more.** That README's
#:      table reads "external BLT per BYTE: BUILT" and "external
#:      deepseek-llm-7b-base per TOKEN: BUILT -- the one to use", under a
#:      heading that says SUPERSEDED. BLT findings still stand on their own
#:      axis (`alignment_smooths.md`, 42/46 lineages); it is simply not the
#:      yardstick to reach for first.
#:
#: **THE DEEPSEEK AXIS CANNOT SERVE THIS QUESTION**, which is why the BLT
#: column is still here. It lives in `results/two_axes.csv` and
#: `results/quadrants.csv`, and of this subject's architecture set those hold
#: only OLMoE-1B-7B-0125, Olmo-3-1025-7B and Falcon3-7B-Base -- one MoE and two
#: dense transformers, no pure SSM, no hybrid, no Griffin, no RWKV. Worse for
#: this question, `quadrants.csv` carries `drift_residual`, drift net of
#: surprisal, which is exactly the fluency-orthogonal measure this folder wants
#: and cannot use for lack of models.
#:
#: `ref_surprisal.py` scores arbitrary text with deepseek and is roundtrip
#: guarded, so extending the axis to these passages is a compute job rather
#: than a new instrument. Until that runs, every number below carrying
#: `bits_per_byte` is a BLT-axis number and says so.
METRICS = ["mean_drift", "mean_pairwise", "bits_per_byte", "directedness", "ordering"]
INTERPRETABLE = 3


#: BOTH ARMS of four non-dense lineages live here as SEPARATE model rows, which
#: is why an arm pairing has to be declared rather than read off a column.
LINEAGES = [
    ("tiiuae/falcon-mamba-7b",        "tiiuae/falcon-mamba-7b-instruct"),
    ("tiiuae/Falcon3-Mamba-7B-Base",  "tiiuae/Falcon3-Mamba-7B-Instruct"),
    ("tiiuae/Falcon-H1-7B-Base",      "tiiuae/Falcon-H1-7B-Instruct"),
    ("allenai/OLMoE-1B-7B-0125",      "allenai/OLMoE-1B-7B-0125-DPO"),
    #: dense controls, same corpus, same slice
    ("allenai/Olmo-3-1025-7B",        "allenai/Olmo-3-7B-Instruct"),
    ("tiiuae/Falcon3-7B-Base",        "tiiuae/Falcon3-7B-Instruct"),
    ("google/gemma-2-9b",             "google/gemma-2-9b-it"),
]


DRIFT = os.path.expanduser("~/malignment-data/national_story/story_drift.jsonl")
NAME_BINS = [(400, 900), (900, 1600), (1600, 10 ** 9)]
IDS_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "passage_analysis", "syntagmatic_damage",
    "results", "reference_ids_base.jsonl")
#: words after the forced word. reference.py's own bins, so the two are readable
#: against each other.
#: **w0-1 IS STRUCTURALLY ZERO and is printed only to keep these bins readable
#: against reference.py's.** The scored text begins AFTER the forced word, so its
#: first word has no preceding context inside the span and deepseek assigns it
#: 0.0000 bits -- measured, not assumed. Every model reads 0.000 there.
WORD_BINS = [(0, 1), (1, 4), (4, 8), (8, 16), (16, 24), (24, 48)]
#: the imposed word's probability under the generating model, in log10 bands.
#: MATCHING ON THIS IS THE WHOLE DESIGN: the forced words DIFFER by lineage (they
#: were chosen against each pair's own movement), so models cannot be compared on
#: which word they got -- only on how they recovered from an imposition of equal
#: improbability.
Q_BINS = [(-6, -4), (-4, -3), (-3, -2), (-2, 0)]


def repair(a):
    """Does a model without attention recover worse from a forced word?

    ## THE PREDICTION

    Attention keeps the imposed word addressable at every later position; a
    recurrent state has to carry it forward inside a fixed-size vector, along
    with everything else. So an attention-free model should pay MORE for the
    clause after an imposition, and the gap should DECAY with distance as the
    anomaly stops mattering to either.

    This is the only probe in this subject that touches what attention is
    actually for. Selection lives in the unembedding and softmax, which every
    model here has -- hence the nulls elsewhere.

    ## WHY MATCHING ON q IS NOT OPTIONAL

    The forced words DIFFER by lineage: they were chosen against each pair's own
    faller/riser classification, so pairwise overlap between two models' forced
    vocabularies is only 0.31-0.37. Models therefore cannot be compared on which
    word they were given. What IS comparable is recovery from an imposition of
    equal improbability, so every comparison happens inside a band of log10 q.

    ## THE SCORER IS EXTERNAL AND THAT IS THE POINT

    `run.py` in syntagmatic_damage fits SELF-surprisal, where each arm is read by
    its own model. That cannot cross models: a tokenizer differs, a calibration
    differs, and a model reading its own output is measuring how well it predicts
    itself. deepseek reads every passage here, one tokenizer, one calibration.
    """
    import collections as _c
    import json
    import math
    import statistics as st
    from malignment import roster, score
    if not os.path.exists(IDS_BASE):
        print("no %s" % IDS_BASE)
        print("run: syntagmatic_damage/reference.py --arm base --plan then --run")
        return 1
    idx = score._index("surprisal")
    rows, unscored = _c.defaultdict(lambda: _c.defaultdict(list)), 0
    for line in open(IDS_BASE, encoding="utf-8"):
        r = json.loads(line)
        sc = idx.get(r["sha"])
        if not sc or not sc.get("scored"):
            unscored += 1
            continue
        q = r.get("q")
        if not q or q <= 0:
            continue
        base = r["pair"].split(">")[0]
        side = _side(base)
        if side is None:
            continue
        wb = score.word_bits(sc["text"])
        if len(wb) < WORD_BINS[-1][1]:
            continue
        lq = math.log10(q)
        for lo, hi in Q_BINS:
            if lo <= lq < hi:
                bits = [w["bits"] for w in wb]
                rows[(lo, hi)][base].append(
                    [st.mean(bits[b0:b1]) for b0, b1 in WORD_BINS])
                break
    print("RECOVERY AFTER A FORCED WORD, base arm, deepseek as a fixed reader.")
    print("%d rows not in the store.\n" % unscored)
    print("%-12s %-16s %s" % ("log10 q", "group",
                              " ".join("%7s" % ("w%d-%d" % b) for b in WORD_BINS)))
    for lo, hi in Q_BINS:
        d = rows[(lo, hi)]
        for want in ("attention-free", "has attention"):
            ms = [m for m in d if _side(m) == want and len(d[m]) >= 20]
            if not ms:
                continue
            #: median over MODELS of each model's median, so a model with many
            #: rows cannot set the band.
            cols = []
            for j in range(len(WORD_BINS)):
                cols.append(st.median([st.median([v[j] for v in d[m]]) for m in ms]))
            print("%-12s %-16s %s   (%d models)"
                  % ("%g..%g" % (lo, hi), want,
                     " ".join("%7.3f" % c for c in cols), len(ms)))
        af = [m for m in d if _side(m) == "attention-free" and len(d[m]) >= 20]
        ha = [m for m in d if _side(m) == "has attention" and len(d[m]) >= 20]
        if af and ha:
            gap = []
            for j in range(len(WORD_BINS)):
                A = st.median([st.median([v[j] for v in d[m]]) for m in af])
                B = st.median([st.median([v[j] for v in d[m]]) for m in ha])
                gap.append(A - B)
            print("%-12s %-16s %s"
                  % ("", "GAP", " ".join("%+7.3f" % g for g in gap)))
        print()
    print("POSITIVE gap = the attention-free model pays MORE after the")
    print("imposition. The prediction was a positive gap in the NEAR bins")
    print("decaying to zero. THE OBSERVED GAPS ARE NEGATIVE AND LARGEST FAR")
    print("FROM THE IMPOSITION -- attention-free models pay slightly LESS, and")
    print("most so at w8-48. That is not a weak version of the prediction, it")
    print("is the opposite shape, and it is not read as a finding either:")
    print()
    print("  n = 2 attention-free models against 39.")
    print("  Only 2 of 4 q-bands have any model clearing 20 rows.")
    print("  THE IMPOSITIONS ARE MILD: q median 0.0092, min 0.00098, and NONE")
    print("  below 1e-3. A word the model gives 1%% to is not a shock to a state")
    print("  vector, so this may test recovery from a nudge and not from a")
    print("  perturbation.")
    return 0


def _side(m):
    from malignment import roster
    at, bl = roster.architecture(m)
    return None if (at, bl) == ("unknown", "unknown") else (
        "attention-free" if at == "none" else "has attention")
#: capitalised tokens that are not names. Not exhaustive and does not need to be:
#: the same list applies to every model, so a miss is noise and not a bias.
_STOP = set("""The A An And But Or So Then Now When While If As At In On To For Of With
From By After Before Their His Her My Our Your It He She They We I You There Here This
That These Those What Who Why How All One Two Three First Last Next Every Some Many
God Lord Christ Jesus Bible Christian Christians Mr Mrs Miss Dr St Sir Lady
Monday Tuesday Wednesday Thursday Friday Saturday Sunday January February March April
May June July August September October November December""".split())


def _names(text):  # noqa: C901
    """Candidate character names: capitalised, mid-sentence, seen twice.

    MID-SENTENCE is the whole gate. A sentence-initial capital is grammar, not a
    name, and including them makes every text's 'cast' the first word of every
    sentence. SEEN TWICE drops one-off capitalised nouns.
    """
    import collections as _c
    import re
    out = _c.Counter()
    for sent in re.split(r"(?<=[.!?])\s+", text):
        toks = sent.split()
        for t in toks[1:]:                          # skip the sentence-initial
            w = t.strip('.,;:!?"\'()[]\u2014\u2019s')
            if len(w) > 2 and w[0].isupper() and w[1:].islower() and w not in _STOP:
                out[w] += 1
    return {w for w, n in out.items() if n >= 2}


def names(a):
    """Does an attention-free model lose its characters?

    ## THE PREDICTION, RECORDED BEFORE THE RUN

    Attention keeps every past token individually addressable; a recurrent state
    compresses the past into a fixed-size vector. So what an attention-free model
    should lose is EXACT RECALL OF ARBITRARY, HIGH-ENTROPY DETAIL. A character
    name is the purest case: not reconstructible from context, must be carried
    verbatim, and failure is visible. The GIST of a scene is low-entropy and can
    survive compression -- which is why every semantic measure in this folder
    came back null -- but a proper noun cannot.

    **carryover** = of the names established in the first third, what share
    reappear in the last third. Attention-free should be LOWER.

    The relevant quantity is not distance but INTERFERENCE: a name introduced at
    word 50 and needed at word 2,000 must survive 1,950 words written into the
    same fixed state. Published SSM failures appear at thousands to tens of
    thousands of tokens, so ~3,500 tokens is at the EDGE -- which is the reason
    to measure rather than assume, in either direction.

    ## WHAT A NULL HERE WOULD AND WOULD NOT MEAN

    A null means the regime is still too short, OR that carryover is not the
    thing compression costs. It would NOT mean the architectures are equivalent:
    the literature's separations are at far greater lengths than 3K words.
    """
    import collections as _c
    import statistics as st
    import sys as _sys
    _sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))),
        "passage_analysis", "national_story"))
    import analyse
    from malignment import roster
    G = analyse.load_raw()
    rows = _c.defaultdict(list)
    for (lin, arm, _dem), texts in G.items():
        for t in texts:
            w = t.split()
            if len(w) < a.min_words:
                continue
            k = len(w) // 3
            first, last = _names(" ".join(w[:k])), _names(" ".join(w[2 * k:]))
            if len(first) < 2:
                continue
            rows[lin].append((len(first & last) / len(first), len(w), len(first)))
    #: **BINNED BY LENGTH, because carryover is mostly a length statistic.**
    #: The first version ranked models raw and put falcon-mamba ABOVE the median
    #: at 0.367 -- but it writes 636 words median, and every other short-text
    #: model scored 0.500 while the 2,300-word models scored 0.26-0.29. Raw
    #: ranking measured output length.
    binned = _c.defaultdict(lambda: _c.defaultdict(list))
    for m, v in rows.items():
        for c, w, _n in v:
            for lo, hi in NAME_BINS:
                if lo <= w < hi:
                    binned[(lo, hi)][m].append(c)
                    break
    print("CARRYOVER AT MATCHED LENGTH. Unit = the model; a model needs %d texts"
          % MIN_IN_BIN)
    print("in a bin to appear in it.\n")
    print("%-14s %21s %23s %9s" % ("length bin", "attention-free", "has attention", "gap"))
    print("%-14s %10s %4s %6s %10s %4s %6s" % ("", "median", "mdl", "texts", "median", "mdl", "texts"))
    for lo, hi in NAME_BINS:
        d = binned[(lo, hi)]
        def side(want):
            g = [(st.median(vv), len(vv)) for mm, vv in d.items()
                 if _side(mm) == want and len(vv) >= MIN_IN_BIN]
            return ((st.median([x for x, _ in g]), len(g), sum(n for _, n in g))
                    if g else (float("nan"), 0, 0))
        a1, a2, a3 = side("attention-free")
        b1, b2, b3 = side("has attention")
        print("%-14s %10.3f %4d %6d %10.3f %4d %6d %+9.3f"
              % ("%d-%d" % (lo, hi if hi < 10 ** 8 else 9999),
                 a1, a2, a3, b1, b2, b3, a1 - b1))
    print()
    for lo, hi in NAME_BINS:
        ms = [mm.split("/")[-1] for mm, vv in binned[(lo, hi)].items()
              if _side(mm) == "attention-free" and len(vv) >= MIN_IN_BIN]
        print("   attention-free in %-12s %s"
              % ("%d-%d:" % (lo, hi if hi < 10 ** 8 else 9999), ms or "-- none --"))
    print()
    print("RAW RANKING BELOW, kept because it is the trap: carryover tracks")
    print("LENGTH, so ranking models without binning ranks how long they write.\n")
    print("CHARACTER-NAME CARRYOVER: of the names established in the first third,")
    print("what share reappear in the last third. >= %d words, >= 2 names.\n" % a.min_words)
    out = []
    for m, v in rows.items():
        if len(v) < 15:
            continue
        at, bl = roster.architecture(m)
        if (at, bl) == ("unknown", "unknown"):
            continue
        out.append((st.median([c for c, _, _ in v]), m, at, bl, len(v),
                    st.median([w for _, w, _ in v]), st.median([n for _, _, n in v])))
    out.sort()
    print("%-28s %-13s %-7s %9s %5s %7s %6s"
          % ("model", "attn", "block", "carryover", "n", "words", "names"))
    for c, m, at, bl, n, w, nm in out:
        tag = "  <-" if at == "none" else ""
        print("%-28s %-13s %-7s %9.3f %5d %7.0f %6.0f%s"
              % (m.split("/")[-1][:28], at, bl, c, n, w, nm, tag))
    if out:
        print("\nmedian over %d models: %.3f" % (len(out), st.median([o[0] for o in out])))
        af = [o[0] for o in out if o[2] == "none"]
        ha = [o[0] for o in out if o[2] != "none"]
        if af and ha:
            print("attention-free %.3f (n=%d)   has attention %.3f (n=%d)   gap %+.3f"
                  % (st.median(af), len(af), st.median(ha), len(ha),
                     st.median(af) - st.median(ha)))
    return 0
#: uneven bins: the mass sits at 600-1200 and above 2000, and equal-width bins
#: put 43 models in one and 4 in another.
MIN_IN_BIN = 5   #: a model needs this many texts in a bin to contribute to it
LEN_BINS = [(200, 600), (600, 1200), (1200, 2000), (2000, 10 ** 9)]


def long_context(a):
    """Does drift depend on attention WHERE LENGTH COULD EXERCISE IT?

    ## THE SLOPE VERSION OF THIS WAS WRONG AND IS KEPT AS THE WARNING

    The first pass regressed `mean_drift` on `n_words` per model and found the
    attention-free models at the top: `falcon-mamba-7b-instruct` had the highest
    slope of 56 models, +0.0866 against a roster median of +0.0007, which read as
    an attention-free model losing the thread faster as length grows -- in the
    predicted direction, in the regime where the prediction says it should.

    **It was RANGE RESTRICTION.** `falcon-mamba` writes 557 words median, and
    only 2 of its 57 raw generations exceed 1,200 words -- too few to estimate a
    bin median, which is not the same as none. (An earlier version of this
    docstring said ZERO, which is false: the longest is 2,362 words.) Its slope was fitted inside 200-1200 and
    compared against slopes fitted over 200-2500. Binning by length instead, and
    comparing only where both groups exist, reverses the sign: attention-free
    drift is LOWER in both bins it occupies.

    ## THE UNIT IS THE MODEL, NOT THE TEXT

    A model contributing 900 texts to a bin would otherwise set that bin's
    median. Each model reduces to one number per bin, and a model needs 5 texts
    in a bin to appear in it.

    ## AND SPLIT BY ATTENTION, NOT BY BLOCK

    The first pass grouped by block type and counted `OLMoE` as non-dense. OLMoE
    is a MIXTURE WITH FULL ATTENTION and cannot bear on this question at all;
    including it took the apparent n from one lineage to three.
    """
    import collections
    import json
    import statistics as st
    from malignment import roster
    rows = [json.loads(l) for l in open(DRIFT)]
    r = [x for x in rows if x.get("frame") == "raw"
         and isinstance(x.get("mean_drift"), (int, float))
         and (x.get("n_words") or 0) >= LEN_BINS[0][0]]

    def grp(m):
        at, bl = roster.architecture(m)
        return None if (at, bl) == ("unknown", "unknown") else (
            "attention-free" if at == "none" else "has attention")
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for x in r:
        g = grp(x["model"])
        if g is None:
            continue
        for lo, hi in LEN_BINS:
            if lo <= x["n_words"] < hi:
                by[(lo, hi)][x["model"]].append(x["mean_drift"])
                break
    print("LONG CONTEXT: national_story, raw frame, %d generations, %d models"
          % (len(r), len({x["model"] for x in r})))
    print("median length %d words, against %d for the passage corpus\n"
          % (st.median([x["n_words"] for x in r]), 188))
    print("%-12s %22s %22s %9s" % ("length bin", "attention-free", "has attention", "gap"))
    print("%-12s %9s %5s %6s %9s %5s %6s" % ("", "median", "mdl", "texts",
                                             "median", "mdl", "texts"))
    for lo, hi in LEN_BINS:
        d = by[(lo, hi)]
        def side(want):
            g = [(st.median(v), len(v)) for m, v in d.items()
                 if grp(m) == want and len(v) >= MIN_IN_BIN]
            return ((st.median([x for x, _ in g]), len(g), sum(n for _, n in g))
                    if g else (float("nan"), 0, 0))
        a1, a2, a3 = side("attention-free")
        b1, b2, b3 = side("has attention")
        lab = "%d-%d" % (lo, hi if hi < 10 ** 8 else 9999)
        print("%-12s %9.4f %5d %6d %9.4f %5d %6d  %+9.4f"
              % (lab, a1, a2, a3, b1, b2, b3, a1 - b1))
    print()
    for lo, hi in LEN_BINS:
        ms = [m.split("/")[-1] for m, v in by[(lo, hi)].items()
              if grp(m) == "attention-free" and len(v) >= MIN_IN_BIN]
        print("   attention-free in %-10s %s"
              % ("%d-%d:" % (lo, hi if hi < 10 ** 8 else 9999), ms or "-- none --"))
    print()
    print("ATTENTION-FREE DRIFT IS LOWER WHERE THE TWO GROUPS OVERLAP, and the")
    print("group is ABSENT from the long bins -- but read that carefully.")
    print("falcon-mamba DOES write long: 2 of its 57 raw generations exceed")
    print("1,200 words and the longest is 2,362. It is the MIN_IN_BIN filter")
    print("above that drops them, not the model. 'Cannot write long' and 'writes")
    print("long too rarely to estimate a bin median' are different claims and")
    print("the first one is false. What this corpus cannot do is MEASURE an")
    print("attention-free model at length; it is not evidence that none exists.")
    print()
    print("n IS ONE LINEAGE. Zamba2-7B is in national_story (23 and 27 raw rows)")
    print("but is a full+ssm HYBRID, and recurrentgemma-9b has ONE base row.")
    return 0


def score_pool(a):
    """Score this subject's passages through `malignment.score.surprisal`.

    **NOT `ref_surprisal.py` standalone, and the difference is reuse.** Both run
    the same model -- `score.REF` is `deepseek-ai/deepseek-llm-7b-base`, which is
    jakobson's reference -- but `score.surprisal` keys on `sha(text)` against a
    shared store that already holds 96,305 scored passages, skips anything
    present, and makes what it adds available to every other question. The
    standalone script writes a private sidecar keyed to one output directory.
    The first version of this file ran the standalone one; 0 of its 5,200
    passages were in the store, so nothing was duplicated, but nothing would
    have been reusable either.

    THE PREFIX IS 50, NOT jakobson's 200. A prefix mean is a length statistic
    if taken over everything, which is why a fixed M exists -- but
    `score.surprisal` DROPS a passage shorter than M rather than shortening the
    window, so M selects on length and length differs by model. At M=200
    `falcon-mamba-7b-instruct` retains 56% and `gemma-2-9b-it` 100%. See
    --prefix.
    """
    import pandas as pd
    from malignment import score
    d = pd.read_parquet(PARQUET, columns=["model", "arm", "prompt", "corpus",
                                          "script", "n_sents", "text", "text_sha"])
    want = [m for pair in LINEAGES for m in pair]
    d = d[(d["model"].isin(want)) & (d["script"] == a.script)
          & (d["corpus"] == a.corpus) & (d["n_sents"] >= a.min_sents)]
    #: a plain concat, not groupby.apply: apply drops the grouping column in
    #: this pandas, and the sample is per model by construction anyway.
    take = pd.concat([g.sample(n=min(a.per_model, len(g)), random_state=20260911)
                      for _, g in d.groupby("model")], ignore_index=True)
    texts = list(take["text"])
    idx = score._index("surprisal")
    todo = sum(1 for t in texts if score.sha(t) not in idx)
    print("%d passages over %d models; %d already in the shared store, %d to score"
          % (len(texts), take["model"].nunique(), len(texts) - todo, todo))
    print("prefix M=%d" % a.prefix)
    out = score.surprisal(texts, m=a.prefix)
    take = take.assign(surprisal=out)
    keep = take.dropna(subset=["surprisal"])
    dst = os.path.join(HERE, "results_surprisal.csv")
    keep[["model", "arm", "prompt", "text_sha", "n_sents", "surprisal"]].to_csv(dst, index=False)
    print("scored %d of %d (None = fewer than M scored tokens), wrote %s"
          % (len(keep), len(take), os.path.basename(dst)))
    return 0


def build_pool(a):
    """Write the deepseek input for this subject. Scored by ref_surprisal.py.

    SHUFFLED AND SEEDED, copying `build_ref_pool.py`'s reason verbatim: a run
    stopped early must be a SAMPLE and not a prefix. One file, so every model is
    scored by one reference on one device in one pass.
    """
    import json
    import random
    import pandas as pd
    d = pd.read_parquet(PARQUET, columns=["model", "arm", "prompt", "corpus",
                                          "script", "n_sents", "text", "text_sha"])
    want = [m for pair in LINEAGES for m in pair]
    d = d[(d["model"].isin(want)) & (d["script"] == a.script)
          & (d["corpus"] == a.corpus) & (d["n_sents"] >= a.min_sents)]
    rows, rng = [], random.Random(20260911)
    for m, g in d.groupby("model"):
        take = g.sample(n=min(a.per_model, len(g)), random_state=20260911)
        for r in take.itertuples():
            rows.append({"id": "%s|%s" % (m, r.text_sha), "pool": "architecture",
                         "model": m, "arm": r.arm, "prompt": r.prompt,
                         "text_sha": r.text_sha, "text": r.text})
    rng.shuffle(rows)
    with open(a.build_pool, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    got = {}
    for r in rows:
        got[r["model"]] = got.get(r["model"], 0) + 1
    print("wrote %d passages over %d models -> %s" % (len(rows), len(got), a.build_pool))
    for m in sorted(got):
        print("   %-36s %5d  %s" % (m.split("/")[-1][:36], got[m],
                                    "/".join(roster_arch(m))))
    print()
    print("now:  python experiments/passage_analysis/jakobson_space/ref_surprisal.py \\")
    print("          --input %s --out $MALIGNMENT_DATA/ref_pool/architecture" % a.build_pool)
    return 0


def roster_arch(m):
    from malignment import roster
    return roster.architecture(m)


def spread(a):
    """Where do the attention-free models fall in the WHOLE distribution?

    The 6-model paired set answers "are these six alike"; it cannot say whether
    a rank is unusual, because six models have no distribution. This ranks every
    base model with enough coverage on a common prompt core.
    """
    import pandas as pd
    from malignment import roster
    m3 = METRICS[:INTERPRETABLE]
    d = pd.read_parquet(PARQUET,
                        columns=["model", "arm", "prompt", "corpus", "script",
                                 "n_sents"] + m3)
    d = d[(d["arm"] == a.arm) & (d["corpus"] == a.corpus)
          & (d["n_sents"] >= a.min_sents) & (d["script"] == a.script)]
    cov = d.groupby("model")["prompt"].nunique()
    models = sorted(cov[cov >= a.min_prompts].index)
    d = d[d["model"].isin(models)]
    share = d.groupby("prompt")["model"].nunique()
    core = set(share[share >= int(len(models) * 0.9)].index)
    d = d[d["prompt"].isin(core)]
    print("%d models with >= %d prompts, %d common-core prompts, %d passages\n"
          % (len(models), a.min_prompts, len(core), len(d)))
    pm = d.groupby(["model", "prompt"])[m3].median().reset_index()
    g = pm.groupby("model")[m3].median()
    order = {c: list(g.sort_values(c).index) for c in m3}
    print("%-26s %-11s %-7s %s" % ("model", "attn", "block",
          " ".join("%9s %5s" % (c[:9], "rank") for c in m3)))
    rows = [(m, roster.architecture(m)) for m in g.index]
    nd = [(m, ab) for m, ab in rows if ab[1] != "dense"]
    for m, (at, bl) in sorted(nd, key=lambda x: g.loc[x[0], m3[0]]):
        print("%-26s %-11s %-7s %s" % (m.split("/")[-1][:26], at, bl,
              " ".join("%9.4f %4d/%d" % (g.loc[m, c], order[c].index(m) + 1, len(g))
                       for c in m3)))
    print("%-26s %-11s %-7s %s" % ("-- median of all %d --" % len(g), "", "",
          " ".join("%9.4f %5s" % (g[c].median(), "") for c in m3)))
    print()
    print("EXTREMES on %s, and every one of them is a DENSE transformer:" % m3[0])
    srt = g.sort_values(m3[0])
    for m in list(srt.index[:3]) + list(srt.index[-3:]):
        at, bl = roster.architecture(m)
        print("   %-28s %-11s %-7s %.4f" % (m.split("/")[-1][:28], at, bl, g.loc[m, m3[0]]))
    print()
    c = g[m3].corr(method="spearman")
    print("AND THE AXIS TRACKS THE BLT REFEREE (the SUPERSEDED external axis;")
    print("deepseek is the campaign's, and covers 3 of this subject's models).")
    print("Spearman across the %d models:" % len(g))
    print("   drift ~ pairwise   %+.3f" % c.loc[m3[0], m3[1]])
    print("   drift ~ bits/byte  %+.3f" % c.loc[m3[0], m3[2]])
    print("A model whose text BLT finds costly also drifts more between")
    print("sentences, so drift ranks models by an external quality judgement")
    print("first. Architecture would have to move that to register at all.")
    print("The clean test is quadrants.csv's drift_residual, drift NET of")
    print("surprisal -- which exists, on deepseek, for 3 of these models.")
    return 0


def main():
    import pandas as pd
    from malignment import roster
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default="passage")
    ap.add_argument("--arm", default="base")
    ap.add_argument("--min-sents", type=int, default=3)
    ap.add_argument("--models", default=None,
                    help="comma-separated override of the declared population")
    ap.add_argument("--repair", action="store_true",
                    help="RECOVERY AFTER A FORCED WORD, the memory probe. A base "
                         "model is made to utter a word it did not want, and the "
                         "cost of the following clause is read by a FIXED "
                         "external scorer. Attention can re-read the imposed word "
                         "at every later position; a recurrent state must carry "
                         "it forward compressed. Reads the 41,666 base-arm rows "
                         "scored by syntagmatic_damage/reference.py --arm base.")
    ap.add_argument("--names", action="store_true",
                    help="CHARACTER-NAME CARRYOVER: the sharpest formal probe "
                         "of an attention-free model available without new "
                         "generation. A name is arbitrary, high-entropy and not "
                         "reconstructible from context, so it must be carried "
                         "VERBATIM -- exactly what a fixed-size state should "
                         "lose and attention should keep. Gist survives "
                         "compression; a proper noun does not.")
    ap.add_argument("--long", action="store_true",
                    help="the LONG-CONTEXT regime, from national_story rather "
                         "than the passage corpus. Attention's distinctive "
                         "technical contribution is exact long-range recall, and "
                         "the passage corpus is 188 words median -- far too short "
                         "to exercise it. national_story generations are 1,503 "
                         "median, eight times longer, and story_drift.jsonl "
                         "already carries drift on them.")
    ap.add_argument("--spread", action="store_true",
                    help="rank the non-dense models against EVERY model with "
                         "enough coverage, instead of the 6-model paired set. "
                         "Drops models under --min-prompts, then keeps prompts "
                         "held by >=90%% of what remains, so the comparison is "
                         "on a common core rather than each model's own mix.")
    ap.add_argument("--min-prompts", type=int, default=150)
    ap.add_argument("--min-words", type=int, default=400)
    ap.add_argument("--build-pool", metavar="OUT.jsonl", default=None,
                    help="write a deepseek ref pool for THIS subject's models "
                         "and stop. The jakobson deepseek axis cannot reach "
                         "these architectures at any price -- its pool is gated "
                         "on a 58-model blind narrative coding over f11_l2, and "
                         "f11_l2 holds only 3 of this subject's models, all of "
                         "them dense or MoE. So the pool is rebuilt here, "
                         "self-contained: same scorer, same one-model-one-pass "
                         "discipline, NOT joinable to two_axes.csv because the "
                         "corpus and the coding differ.")
    ap.add_argument("--per-model", type=int, default=400)
    ap.add_argument("--score", action="store_true",
                    help="score this subject's passages with the reference model "
                         "THROUGH malignment.score, so the result lands in the "
                         "shared sha-keyed store (96,305 entries already) rather "
                         "than a private sidecar. Same model as jakobson's pass, "
                         "deepseek-llm-7b-base; nothing is rescored.")
    ap.add_argument("--prefix", type=int, default=50,
                    help="mean surprisal over the first M scored tokens. NOT "
                         "jakobson's M=200, and the difference is a confound: "
                         "score.surprisal returns None when a passage has FEWER "
                         "than M tokens, so the prefix SELECTS ON LENGTH, and "
                         "length varies by model. Measured retention at M=200: "
                         "falcon-mamba-7b-instruct 56%%, gemma-2-9b-it 100%% -- a "
                         "44-point differential on the one model that has already "
                         "failed two other screens. At M=50 it is 96%% and 100%%. "
                         "M=200 is right for jakobson, whose human corpora all "
                         "clear it; it is wrong for a cross-MODEL comparison.")
    ap.add_argument("--script", default="en",
                    help="ENGLISH ONLY BY DEFAULT (RH, 2026-09-11). The zh rows "
                         "go through a different pipeline entirely -- stanza-zh "
                         "segmentation and the zh bge variant, against nltk-en -- "
                         "so a sentence is not the same unit on both sides, and "
                         "this campaign already holds that bits/char is not "
                         "comparable across scripts. 48 of 99,786 rows in the "
                         "base/passage set are zh: too few to matter to a median "
                         "and no reason at all to carry.")
    a = ap.parse_args()

    if a.repair:
        return repair(a)
    if a.names:
        return names(a)
    if a.long:
        return long_context(a)
    if a.score:
        return score_pool(a)
    if a.build_pool:
        return build_pool(a)
    if a.spread:
        return spread(a)
    cols = ["model", "arm", "prompt", "corpus", "script", "n_sents"] + METRICS
    d = pd.read_parquet(PARQUET, columns=cols)
    d = d[(d["arm"] == a.arm) & (d["corpus"] == a.corpus)
          & (d["n_sents"] >= a.min_sents) & (d["script"] == a.script)]
    #: **THE POPULATION IS NAMED, NOT FILTERED.** Every non-dense architecture
    #: this parquet actually covers, plus dense controls. Taking "every model
    #: with >= 50 prompts" instead admits ~40 checkpoints, and requiring a
    #: prompt shared by ALL of them collapses the paired set from 147 to NINE.
    #: The pairing is the instrument here, so the set is declared.
    #:
    #: recurrentgemma-9b is DELIBERATELY absent and this is the finding that
    #: costs the most: it holds 38 rows at a median of ONE sentence, so drift
    #: is undefined for it, and the attested same-corpus contrast
    #: (gemma-2-9b vs recurrentgemma-9b) CANNOT BE RUN on this dataset. The
    #: best-controlled pair in the subject is the one the data cannot serve.
    #: Olmo-Hybrid, Zamba2, RWKV and falcon-7b are absent from the parquet.
    DEFAULT = ["tiiuae/falcon-mamba-7b",       # none / ssm
               "tiiuae/Falcon-H1-7B-Base",     # full+ssm / hybrid
               "allenai/OLMoE-1B-7B-0125",     # full / moe
               "allenai/Olmo-3-1025-7B",       # full+local / dense
               "google/gemma-2-9b",            # full / dense
               "tiiuae/Falcon3-7B-Base"]       # full / dense
    models = sorted(set(a.models.split(",")) if a.models else set(DEFAULT))
    missing = [m for m in models if m not in set(d["model"])]
    if missing:
        print("not in the parquet: %s" % ", ".join(missing))
    models = [m for m in models if m not in missing]
    d = d[d["model"].isin(models)]
    d = d[d["model"].isin(models)]
    have = d.groupby("prompt")["model"].nunique()
    keep = set(have[have == len(models)].index)
    d = d[d["prompt"].isin(keep)]
    print("SYNTAGMATIC axis, %s arm, corpus=%s, script=%s, n_sents>=%d"
          % (a.arm, a.corpus, a.script, a.min_sents))
    print("%d models, %d prompts held by ALL of them, %d passages\n"
          % (len(models), len(keep), len(d)))
    if not len(keep):
        print("no shared prompts -- are you joining on `prompt` and not `prompt_id`?")
        return 1

    #: per (model, prompt) first, so a model with more samples per prompt does
    #: not get more weight in the model-level median.
    pm = d.groupby(["model", "prompt"])[METRICS].median().reset_index()
    g = pm.groupby("model")[METRICS].median()
    print("%-22s %-11s %-7s %s"
          % ("model", "attn", "block", " ".join("%9s" % m[:9] for m in METRICS)))
    for m, r in g.sort_values(METRICS[0]).iterrows():
        at, bl = roster.architecture(m)
        print("%-22s %-11s %-7s %s"
              % (m.split("/")[-1][:22], at, bl,
                 " ".join("%9.4f" % r[c] for c in METRICS)))
    print()
    print("DOES THE SPREAD CLEAR THE NOISE IT SITS IN?")
    for i, c in enumerate(METRICS):
        across = g[c].max() - g[c].min()
        iqr = st.median([pm[pm["model"] == m][c].quantile(.75)
                         - pm[pm["model"] == m][c].quantile(.25) for m in models])
        flag = "" if i < INTERPRETABLE else "   <- BELOW NOISE, not interpreted"
        print("   %-14s across %.4f   within-model IQR %.4f   ratio %.2f%s"
              % (c, across, iqr, across / iqr if iqr else float("nan"), flag))
    print()
    #: the paired form, which is what actually identifies an outlier.
    piv = pm.pivot(index="prompt", columns="model", values="mean_drift")
    lo = g[METRICS[0]].idxmin()
    print("PAIRED on prompt: how often does each model exceed %s on mean_drift?"
          % lo.split("/")[-1])
    for m in models:
        if m == lo:
            continue
        both = piv[[m, lo]].dropna()
        w = (both[m] > both[lo]).sum()
        print("   %-24s %3d/%3d  (%.0f%%)"
              % (m.split("/")[-1][:24], w, len(both), 100.0 * w / len(both)))
    print()
    print("THE ONE ROBUST BETWEEN-MODEL EFFECT IS A DENSE FULL-ATTENTION MODEL,")
    print("and the attention-free model sits mid-pack on every metric that")
    print("clears its own noise. The prediction in the docstring failed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
