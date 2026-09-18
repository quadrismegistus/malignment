"""A reader's glossary for the 18 scales in the dose-vs-marginal figure.

    python -u norm_glossary.py                 print it
    python -u norm_glossary.py --write         -> results/norm_glossary.md

For each scale: where it comes from, how it is defined IN THE WORDS OF ITS OWN
INSTRUMENT, worked examples at high / middle / low, and the words whose mass
actually moves in the measured direction across the fifty lineages.

## WHY THE DEFINITIONS ARE QUOTED AND NOT PARAPHRASED

A scale means whatever its rater was asked, and the rater was asked in a
specific sentence. Every definition below is read at run time out of the
instrument that produced the numbers -- `rate_charge_v1.py` for `k_*`,
`slot_ratings/task.py` for `v6:*` -- so a rubric edit shows up here rather than
leaving a stale gloss behind. The two human lexicons are cited, not quoted,
because their definitions live in their papers.

## THE EXAMPLES ARE DRAWN FROM THE CORPUS VOCABULARY, NOT THE LEXICON

Sampling the lexicon would answer "what does this scale look like in English".
The question a reader of the figure has is "what does it look like among the
words these fifty models put probability on", which is also the population the
`_absz` z-scores are taken over. So every exemplar below appears in
`words_long_v4`, and is picked from the most frequently moving words in its band
rather than at random -- an unrecognisable word is a bad example even when it is
a correct one.

## FLOORED SCALES GET A COUNT, NOT THREE WORDS

`k_vulgarity` has variance on 1.7% of the lexicon and `k_bodily_harm` is 1 for
most words. Drawing "three low examples" from a floor is drawing three words at
random from 89% of English and presenting them as characteristic. Where a band
holds most of the vocabulary this file says so and gives the share.
"""
import argparse, collections, functools, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
CACHE = os.path.expanduser("~/malignment-data/norm_change/movers_en_cache.json")
OUT = os.path.join(HERE, "results", "norm_glossary.md")

#: the two instrument files the rubrics are READ OUT OF, so an edit there
#: cannot leave a stale paraphrase here
RUBRIC_K = os.path.join(os.path.dirname(ROOT), "malign-logits",
                        "malign_logits", "tasks", "rate_charge_v1.py")
RUBRIC_V6 = os.path.join(ROOT, "experiments", "slot_ratings", "task.py")

#: source, and the one-line gloss of WHAT KIND OF OBJECT the number is
SOURCE = {
    "warriner": ("Warriner, Kuperman & Brysbaert (2013), *Norms of valence, "
                 "arousal and dominance for 13,915 English lemmas*, "
                 "Behavior Research Methods 45:1191-1207. **Human** ratings, "
                 "1-9, ~20 raters per word, word out of context."),
    "k": ("OURS. `lexicons/norms/k_ratings_en.json` -- 27,242 words x 7 scales, "
          "rated 1-7 by deepseek-v4-flash at temperature 0, one word per call, "
          "OUT OF CONTEXT. Not human norms."),
    "v6": ("OURS. `slot_rating_en_v6` -- 12 scales rated 1-7 by "
           "deepseek-v4-flash at temperature 0, one call per (prompt, word), "
           "the word judged INSIDE ITS FRAME. The same word carries different "
           "numbers at different prompts, which is the point of the "
           "instrument."),
}


def rubric(path, scale):
    """Pull `  <scale>   <text>` out of an instrument's rubric block. -> str"""
    src = open(path).read()
    #: the k rubric is an indented two-column block in a triple-quoted string
    m = re.search(r"\n  %s\s+(.+?)(?=\n  [a-z_]+ {2,}|\n\nRULES|\n\"\"\")"
                  % re.escape(scale), src, re.S)
    if m:
        return " ".join(m.group(1).split())
    #: the v6 rubric is a pydantic Field description
    m = re.search(r"\n    %s: int = Field\(ge=1, le=7, description=\n(.*?)\)\n"
                  % re.escape(scale), src, re.S)
    if m:
        return " ".join(re.findall(r'"([^"]*)"', m.group(1)))
    return "(rubric not found for %r in %s)" % (scale, os.path.basename(path))


def load_cache():
    if not os.path.exists(CACHE):
        raise SystemExit(
            "no mover cache. Build it first:\n"
            "    python -u norm_glossary.py --build-cache")
    return json.load(open(CACHE))


def build_cache():
    """Stream words_long_v4 -> net mass change per word, the 50 endpoints only."""
    import gzip, csv
    from malignment import roster
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    src = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
    net_w = collections.defaultdict(float)
    nlw = collections.Counter()
    net_pw = collections.defaultdict(float)
    func = set()
    seen, n = set(), 0
    with gzip.open(src, "rt") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["lang"] != "en" or (row["base"], row["aligned"]) not in pairs:
                continue
            n += 1
            seen.add((row["base"], row["aligned"]))
            d, w = float(row["delta"]), row["word"]
            net_w[w] += d
            nlw[w] += 1
            net_pw[row["prompt"] + "\t" + w] += d
            #: carried so the DISPLAY lists can drop `the`, `is`, `50`. They
            #: carry real mass and stay in every mean; as examples of a norm
            #: they are noise, and a reader shown `50 1` for register learns
            #: that the corpus contains numerals.
            if row["is_function"] == "1":
                func.add(w)
    #: **50 OF 50 OR THE EXAMPLES ARE OFF-POPULATION.** `words_long_v4` holds
    #: 132 measured pairs; the figure is the 50 endpoint lineages, and an
    #: exemplar drawn from the other 82 is an exemplar from a different study.
    if len(seen) != 50:
        raise SystemExit("expected 50 endpoint lineages, matched %d" % len(seen))
    json.dump({"n_rows": n, "n_lineages": len(seen), "word": net_w,
               "word_n": nlw, "prompt_word": net_pw,
               "function": sorted(func)}, open(CACHE, "w"))
    print("%s rows, %d lineages -> %s" % (format(n, ","), len(seen), CACHE))


# ── the 18, with what each one needs that cannot be derived ───────────────
#
# `direction` is READ OFF THE FIGURE at build time, never typed here: see
# `scales()`. What is typed is only what no artifact carries -- the source key,
# the parent scale an `_absz` stands on, and a plain-English gloss of the
# quantity for a reader who will not chase the rubric.

PARENT = {
    "warriner_valence_absz": ("warriner_valence", "Valence"),
    "warriner_arousal_absz": ("warriner_arousal", "Arousal"),
    "warriner_valence_extremity_absz": ("warriner_valence_extremity",
                                        "Valence extremity"),
    "k_register_level_absz": ("k_register_level", "Register"),
}

#: ONE SENTENCE A READER CAN USE, per scale. Written here because no artifact
#: holds it: the rubric is addressed to a rater ("rate this 1-7"), and a caption
#: needs the construct ("how elevated the vocabulary is").
GLOSS = {
    "warriner_valence": "how pleasant the word is",
    "warriner_arousal": "how activating the word is, calm to excited",
    "warriner_dominance": "how much control the word implies, "
                          "controlled-by to in-control",
    "k_register_level": "how elevated the vocabulary is, street to learned",
    "k_vulgarity": "how coarse the word is AS LANGUAGE",
    "k_transgressiveness": "whether the word names the breaking of a rule",
    "k_bodily_harm": "whether the word implies damage to a body",
    "k_concreteness": "whether the referent can be perceived by the senses",
    "v6:vocalisation": "whether the action is made of speech or vocal sound",
    "v6:mundanity": "how ordinary the event is, as it plays out in this scene",
    "v6:fit": "whether the word BELONGS in this scene (not how likely it is)",
    "v6:directedness": "whether the action is done AT another person",
    "v6:makes_better": "how much the word improves the situation",
    "v6:makes_worse": "how much the word worsens the situation",
}
GLOSS_ABSZ = ("how FAR FROM TYPICAL the word is on %s, in either direction -- "
              "|z| against the corpus vocabulary, so a slot scores high whether "
              "its words are unusually high or unusually low")


def value_fns(cache):
    """{raw scale key: word -> float or None}, plus the z moments used. -> (fns, mom)

    **THE z POPULATION IS WORD TYPES IN THE CORPUS, NOT THE LEXICON**, matching
    `run.py:_add_z` -- "extreme among the words these models actually put mass
    on", not "extreme for English". Recomputed here over the English corpus
    vocabulary; it is used to CHOOSE EXAMPLE BANDS and to describe the scale,
    never to restate a figure value, so small population differences against
    the run cannot propagate into a number this file reports.
    """
    import statistics as st
    from malignment import fields as F
    vocab = list(cache["word"])

    def warr(dim):
        return lambda w: (F.word_norms(w) or {}).get(dim)

    def kk(dim):
        return lambda w: (lambda d: d.get(dim) if d else None)(F.k(w))

    def vext(w):
        v = (F.word_norms(w) or {}).get("valence")
        return None if v is None else abs(v - 5.0)

    base = {"warriner_valence": warr("valence"),
            "warriner_arousal": warr("arousal"),
            "warriner_dominance": warr("dominance"),
            "warriner_valence_extremity": vext,
            "k_register_level": kk("register_level"),
            "k_vulgarity": kk("vulgarity"),
            "k_transgressiveness": kk("transgressiveness"),
            "k_bodily_harm": kk("bodily_harm"),
            "k_concreteness": kk("concreteness")}
    mom = {}
    for k, fn in base.items():
        v = [x for x in (fn(w) for w in vocab) if x is not None]
        if len(v) >= 30 and st.pstdev(v) > 0:
            mom[k] = (st.fmean(v), st.pstdev(v), len(v))
    fns = dict(base)
    for key, (par, _) in PARENT.items():
        mu, sd, _n = mom[par]
        fns[key] = (lambda fn, mu=mu, sd=sd:
                    lambda w: (lambda x: None if x is None else abs((x - mu) / sd))(fn(w))
                    )(base[par])
    return fns, mom


def bands(vals):
    """Deciles of a scale's own distribution, plus its floor. -> dict

    **A BAND IS NOT THREE WORDS WHEN IT IS HALF THE VOCABULARY.** `floor_share`
    is the fraction of word types sitting on the single modal value; where that
    is large the bottom decile is a random draw from most of English, and the
    report says the share instead of pretending to characterise it.
    """
    import statistics as st
    s = sorted(vals)
    n = len(s)
    mode, cnt = collections.Counter(s).most_common(1)[0]
    hi = s[int(0.90 * n)]
    #: **A 90th PERCENTILE INSIDE THE FLOOR IS NOT A HIGH BAND.** 98% of the
    #: vocabulary scores 1 on vulgarity, so the 90th percentile is 1 and a band
    #: of [1, 7] fills with words scoring 1 -- six ordinary verbs presented as
    #: the coarse end of the scale. Where that happens the HIGH band starts at
    #: the smallest value ABOVE the modal one, which is what a reader means.
    if hi <= mode:
        above = [x for x in s if x > mode]
        hi = above[0] if above else hi
    return {"lo": s[int(0.10 * n)], "mid_lo": s[int(0.45 * n)],
            "mid_hi": s[int(0.55 * n)], "hi": hi,
            "min": s[0], "max": s[-1], "median": st.median(s), "n": n,
            "floor_value": mode, "floor_share": cnt / n}


_FUNC = set()


def displayable(k):
    """Is this a word a reader learns something from? -> bool

    Function words and bare numerals are dropped from EXAMPLE LISTS only. They
    stay in every mean, count and gate: they carry real probability mass and
    removing them from the statistic would be selecting on the outcome.
    """
    w = k.split("\t", 1)[1] if "\t" in k else k
    return w not in _FUNC and not re.fullmatch(r"[\W\d_]+", w)


def word_of(k):
    """`prompt\tword` -> `word`; a bare word unchanged."""
    return k.split("\t", 1)[1] if "\t" in k else k


def pick(items, lo, hi, n=6, by_value=False):
    """The n most-moved items whose value falls in [lo, hi]. -> [(key, value)]

    Ordered by WEIGHT -- lineages moved for a word-grain scale, absolute net
    mass moved for a contextual one -- so an exemplar is a word the reader has
    seen in the data rather than the rarest word that satisfies the band.

    **DEDUPED BY WORD.** A contextual scale rates (prompt, word), so the same
    word recurs across frames and an undeduped list spends all six slots on
    `ask` at six prompts -- which shows the reader the instrument's grain and
    nothing about the scale.
    """
    got = [(k, v, w) for k, v, w in items
           if lo <= v <= hi and displayable(k)]
    #: the HIGH band is ordered by VALUE, the others by weight. Ordering the top
    #: band by how much it moves fills it with the band's floor -- `thought 2,
    #: shoot 2, request 2` for vulgarity, which are the least vulgar words that
    #: clear the cut, presented as the coarse end.
    got.sort(key=lambda t: (-t[1], -t[2]) if by_value else (-t[2],))
    out, seen = [], set()
    for k, v, _w in got:
        if word_of(k) in seen:
            continue
        seen.add(word_of(k))
        out.append((k, v))
        if len(out) == n:
            break
    return out


def movers(items, net, modal=None, top=8):
    """Biggest net mass losers and gainers, with their scale value. -> dict

    `net` is summed over the fifty (base, aligned) pairs, so a word here is one
    that moves ACROSS the roster and not in one lineage. The mean-value contrast
    under `lost`/`gained` is the direction check: it is the same comparison the
    figure's y axis makes, done on words instead of on prompt-level means.
    """
    import statistics as st
    have = [(k, v) for k, v, _w in items if k in net]
    have.sort(key=lambda t: net[t[0]])
    if len(have) < 20:
        return None

    def dedupe(seq):
        out, seen = [], set()
        for k, v in seq:
            if word_of(k) in seen or not displayable(k):
                continue
            seen.add(word_of(k))
            out.append((k, v))
            if len(out) == top:
                break
        return out

    #: the MEANS are computed over the undeduped list, because the population
    #: being contrasted is the one the figure aggregates -- every (prompt, word)
    #: cell that carries mass. Only the DISPLAY is deduped.
    m = min(100, len(have) // 3)
    #: **ON A FLOORED SCALE THE PLAIN LIST IS ALL FLOOR.** 70% of the register
    #: vocabulary scores exactly 4, so the eight biggest movers all score 4 and
    #: the reader learns nothing about register. The off-modal pass shows the
    #: same ranking among the words that carry a value at all. It is a DISPLAY
    #: aid: the means above stay on the full population, because dropping the
    #: modal block would drop most of the mass the figure aggregates.
    off = [(k, v) for k, v in have if v != modal]
    return {"lost": dedupe(have), "gained": dedupe(have[::-1]),
            "lost_off": dedupe(off) if off else [],
            "gained_off": dedupe(off[::-1]) if off else [],
            "mean_lost": st.fmean(v for _k, v in have[:m]),
            "mean_gained": st.fmean(v for _k, v in have[-m:]),
            "m": m, "n": len(have)}


def scales():
    """The 18, as the figure selects them. -> rows, sorted by dose slope."""
    import plot_fields as P
    rows = P.load_xy(pmax=1.01, min_lin=0, panel="v6", gated=True,
                     sig="both", alpha=0.05, correct="bh")
    return sorted(rows, key=lambda r: -r["x"])


def items_for(key, cache, fns):
    """[(display key, value, n lineages moved)] for one scale. -> list, net dict

    Levels scales are keyed by WORD and contextual ones by (prompt, word),
    because that is the grain each instrument rates at. Mixing them would
    average a contextual rating over frames, which is the one thing the
    contextual instrument exists not to do.
    """
    from malignment import fields as F
    if key.startswith("v6:"):
        scale = key.split(":", 1)[1]
        idx = F._slot_index()
        net = cache["prompt_word"]
        out = []
        for (pr, w), by in idx.items():
            v = (by.get("v6") or {}).get(scale)
            if v is None or isinstance(v, bool):
                continue
            k = pr + "\t" + w
            if k in net:
                out.append((k, float(v), abs(net[k])))
        return out, net
    fn = fns[key]
    net, nlw = cache["word"], cache["word_n"]
    out = []
    for w in net:
        v = fn(w)
        if v is not None:
            out.append((w, float(v), nlw.get(w, 0)))
    return out, net


def show(k):
    """`prompt\\tword` -> `word  <- "...prompt tail"`; a bare word unchanged."""
    if "\t" not in k:
        return k
    pr, w = k.split("\t", 1)
    tail = pr if len(pr) <= 46 else "..." + pr[-43:]
    return '%s  <- "%s"' % (w, tail)


def build_dose():
    """Per-scale mean level change on a lineage's most- and least-charged prompts.

    **THE GATE IS THE FIGURE'S GATE.** `min(base_cov, aligned_cov) >= 0.20`,
    matching `dose_lift_v4_cov20`; a split computed over a wider set of prompts
    than the figure aggregates would be a different quantity wearing the same
    axis label.
    """
    import gzip, csv, statistics as st
    from malignment import roster, charge
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    lift = charge.lifts_per_lineage()
    want = {r["scale"] for r in scales()}
    acc = collections.defaultdict(list)
    for fn in ("contextual_long_v4.csv.gz", "levels_long_v4.csv.gz"):
        src = os.path.expanduser("~/malignment-data/norm_change/" + fn)
        n = 0
        with gzip.open(src, "rt") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                if row["lang"] != "en" or row["scale"] not in want:
                    continue
                if (row["base"], row["aligned"]) not in pairs:
                    continue
                if min(float(row["base_cov"]), float(row["aligned_cov"])) < 0.20:
                    continue
                lf = lift.get((row["prompt"], row["base"]))
                if lf is None:
                    continue
                n += 1
                acc[(row["base"], row["scale"])].append(
                    (lf, float(row["aligned_level"]) - float(row["base_level"])))
        print("%s: %s usable rows" % (fn, format(n, ",")), flush=True)
    by = collections.defaultdict(list)
    for (_lin, scale), rows in acc.items():
        if len(rows) < 30:
            continue
        rows.sort(key=lambda t: t[0])
        k = len(rows) // 3
        by[scale].append((st.fmean(d for _l, d in rows[:k]),
                          st.fmean(d for _l, d in rows[-k:]),
                          st.fmean(d for _l, d in rows[-k:])
                          - st.fmean(d for _l, d in rows[:k]),
                          len(rows), rows[k - 1][0], rows[-k][0]))
    out = {sc: {"n_lineages": len(v),
                "med_lo": st.median(x[0] for x in v),
                "med_hi": st.median(x[1] for x in v),
                "med_gap": st.median(x[2] for x in v),
                "n_prompts_med": st.median(x[3] for x in v),
                "lift_cut_lo": st.median(x[4] for x in v),
                "lift_cut_hi": st.median(x[5] for x in v)} for sc, v in by.items()}
    json.dump(out, open(DOSE_CACHE, "w"), indent=1)
    print("wrote %s for %d scales" % (DOSE_CACHE, len(out)))


DOSE_CACHE = os.path.expanduser("~/malignment-data/norm_change/dose_split_cache.json")


@functools.lru_cache(maxsize=1)
def dose_cache():
    return json.load(open(DOSE_CACHE)) if os.path.exists(DOSE_CACHE) else {}


def dose_split(key, r, L):
    """The x axis in plain units: the same scale at charged and uncharged prompts.

    **THIS IS AN ILLUSTRATION OF THE DOSE SLOPE, NOT THE SLOPE.** The figure's x
    is a per-lineage OLS slope of (aligned - base) on the prompt's lift,
    standardised by the between-lineage SD and then taken at the median. What is
    printed here is the same data cut into thirds -- the mean change on a
    lineage's most-charged third of prompts against its least-charged third,
    median over lineages -- which a reader can hold in mind and which cannot be
    substituted for the fitted value.
    """
    d = dose_cache().get(key)
    if not d:
        return
    a = L.append
    a("**The same scale at charged and uncharged prompts** (illustration of the "
      "dose slope, not the fitted value):")
    a("")
    a("    least-charged third of prompts   mean change %+.4f" % d["med_lo"])
    a("    most-charged third of prompts    mean change %+.4f" % d["med_hi"])
    a("    gap                              %+.4f  (scale points)" % d["med_gap"])
    a("")
    a("    medians over %d lineages, %d prompts each; the thirds split at lift "
      "%.2f and %.2f" % (d["n_lineages"], d["n_prompts_med"],
                         d["lift_cut_lo"], d["lift_cut_hi"]))
    a("")


def entry(i, r, cache, fns, mom, L):
    a = L.append
    key = r["scale"]
    src = ("v6" if key.startswith("v6:")
           else "k" if key.startswith("k_") else "warriner")
    par = PARENT.get(key)
    a("### %d. %s  (`%s`)" % (i, r["field"], key))
    a("")
    a("**Where it's from.** %s" % SOURCE[src])
    a("")
    if par:
        a("**What it measures.** " + GLOSS_ABSZ % par[1].upper() + ". It is a "
          "DERIVED scale: `|z|` of `%s` per word, standardised over the corpus "
          "vocabulary, then mass-weighted like any other. A slot scores high "
          "when the model's probability sits on words far from the middle of "
          "the scale; low when it sits on unremarkable ones." % par[0])
        a("")
        if par[0].startswith("k_"):
            a('**The parent asks the rater:** "%s"'
              % rubric(RUBRIC_K, par[0].split("_", 1)[1]))
        elif par[0] == "warriner_valence_extremity":
            a("**The parent is DERIVED TOO**, and this is the only two-step "
              "scale in the figure: `valence_extremity` is `|valence - 5|`, "
              "the distance from the neutral midpoint of Warriner's 1-9 scale, "
              "computed per word; this scale is then `|z|` of THAT. So it asks "
              "how unusually far from affectively neutral a word is -- and a "
              "word of exactly typical extremity scores 0 whether it is warm, "
              "cold or flat. Report it with that clause or not at all.")
        else:
            a("**The parent is Warriner's %s**, scored 1-9 by human raters."
              % par[1].lower())
    else:
        a("**What it asks the rater.** %s"
          % ('"%s"' % rubric(RUBRIC_V6, key.split(":", 1)[1])
             if src == "v6" else
             '"%s"' % rubric(RUBRIC_K, key.split("_", 1)[1]) if src == "k"
             else "Not a rubric we wrote -- see the citation above. Raters "
                  "placed each word on three 1-9 scales -- valence "
                  "unhappy-to-happy, arousal calm-to-excited, dominance "
                  "controlled-to-in-control -- following Bradley & Lang's ANEW "
                  "protocol, ~20 raters per word."))
        a("")
        a("**In one line.** %s." % GLOSS.get(key, "--"))
    a("")
    #: the caveats travel with the numbers, per `fields.k_warnings()`
    from malignment import fields as F
    warn = F.k_warnings()
    base_key = (par[0] if par else key)
    if base_key.startswith("k_"):
        nm = base_key[2:]
        meta = json.load(open(os.path.join(ROOT, "lexicons", "norms",
                                           "k_ratings_en.json")))["_meta"]
        iaa = meta["inter_annotator_r_vs_claude_haiku_4_5"].get(nm)
        cal = meta.get("calibration_vs_human_norms", {}).get(nm)
        bits = ["agreement with a second coder (Claude Haiku 4.5) r = %.2f" % iaa]
        if cal:
            bits.append("correlates r = %.2f with human %s norms (n = %d)"
                        % (cal["pearson_r"], cal["vs_human_norm"], cal["n"]))
        a("**Reliability.** %s." % "; ".join(bits))
        if nm in warn:
            a("")
            a("> **%s**" % warn[nm])
        a("")
    items, net = items_for(key, cache, fns)
    vals = [v for _k, v, _w in items]
    if not vals:
        a("*(no words carry this scale in the corpus)*")
        a("")
        return
    b = bands(vals)
    a("**In the figure.** dose slope **%+.2f**, marginal change **%+.2f** "
      "(SDs) -- %s with charge, %s with alignment. Measured on %s %s."
      % (r["x"], r["y"],
         "rises" if r["x"] > 0 else "falls",
         "rises" if r["y"] > 1e-9 else ("does not move" if abs(r["y"]) < 1e-9
                                        else "falls"),
         format(b["n"], ","),
         "(prompt, word) pairs" if key.startswith("v6:") else "word types"))
    a("")
    a("**Examples**, drawn from the corpus vocabulary, most-moved first:")
    a("")
    #: **A BAND THAT COINCIDES WITH ANOTHER IS NOT A BAND.** On a floored scale
    #: the 10th, 45th and 55th percentiles are the same number, and printing
    #: three identically-populated rows labelled HIGH / MIDDLE / LOW asserts a
    #: continuum the instrument does not have.
    done = {}
    for lab, lo, hi in (("HIGH", b["hi"], b["max"]),
                        ("MIDDLE", b["mid_lo"], b["mid_hi"]),
                        ("LOW", b["min"], b["lo"])):
        if (lo, hi) in done:
            a("    %-7s %-11s (identical to %s -- this scale has no distinct "
              "band here)" % (lab, "%.2g-%.2g" % (lo, hi), done[(lo, hi)]))
            continue
        done[(lo, hi)] = lab
        got = pick(items, lo, hi, 6, by_value=(lab == "HIGH"))
        a("    %-7s %-11s %s" % (lab, "%.2g-%.2g" % (lo, hi),
                                 ", ".join("%s %.2g" % (word_of(k), v)
                                           for k, v in got)))
        if key.startswith("v6:") and got and lab == "HIGH":
            for k, v in got[:4]:
                a("            %s" % show(k))
    if b["floor_share"] >= 0.25:
        a("")
        where = ("the bottom" if b["floor_value"] <= b["lo"] else
                 "the top" if b["floor_value"] >= b["hi"] else "the middle")
        a("    NOTE: %.0f%% of these score exactly %.2g, at %s of the scale. "
          "That band is not a characterisation, it is most of the vocabulary; "
          "read this scale as an indicator that fires against a large "
          "undifferentiated mass, not as a continuum."
          % (100 * b["floor_share"], b["floor_value"], where))
    a("")
    mv = movers(items, net, b["floor_value"], 8)
    if mv:
        a("**What actually moves**, net probability summed over the fifty "
          "lineages:")
        a("")
        a("    LOSING MASS   %s"
          % ", ".join("%s %.2g" % (word_of(k), v) for k, v in mv["lost"]))
        a("    GAINING MASS  %s"
          % ", ".join("%s %.2g" % (word_of(k), v) for k, v in mv["gained"]))
        if b["floor_share"] >= 0.25 and mv["lost_off"]:
            a("")
            a("    ...and among the words that are NOT at the modal value of "
              "%.2g:" % b["floor_value"])
            a("")
            a("    LOSING MASS   %s"
              % ", ".join("%s %.2g" % (word_of(k), v) for k, v in mv["lost_off"]))
            a("    GAINING MASS  %s"
              % ", ".join("%s %.2g" % (word_of(k), v) for k, v in mv["gained_off"]))
        a("")
        d = mv["mean_gained"] - mv["mean_lost"]
        a("    mean value of the %d biggest losers  %.2f" % (mv["m"], mv["mean_lost"]))
        a("    mean value of the %d biggest gainers %.2f   (%+.2f)"
          % (mv["m"], mv["mean_gained"], d))
        a("")
        #: **A ZERO MEDIAN HAS NO DIRECTION TO AGREE WITH.** `Vulgarity` and
        #: `Makes worse` sit at exactly 0.000 on the y axis because most
        #: lineages are tied; calling a word-level contrast "consistent" or
        #: "against" there invents a sign the figure does not carry.
        if abs(r["y"]) < 1e-9:
            a("    The marginal median is EXACTLY zero -- most lineages are "
              "tied -- so there is no y-axis direction for this contrast to "
              "agree or disagree with. This scale's result is on the DOSE "
              "axis; see the charge split below.")
        else:
            ok = (d > 0) == (r["y"] > 0)
            a("    %s the word-level contrast %s the figure's y axis."
              % ("CONSISTENT:" if ok else "NOTE:",
                 "runs the same way as" if ok else "runs AGAINST"))
    a("")
    dose_split(key, r, L)


def render(cache, fns, mom, rows):
    L = []
    a = L.append
    a("# The eighteen scales — a reader's glossary")
    a("")
    a("**Generated by `norm_glossary.py`. Do not hand-edit.** Every definition "
      "is read at run time out of the instrument that produced the numbers, and "
      "every example is drawn from the corpus the figure is built on.")
    a("")
    a("These are the scales in `figures/dose_vs_marginal_gated_both_bh05_pub.png` "
      "— the %d that clear both axes at a Benjamini-Hochberg false discovery "
      "rate of 5%%, within axis, over the 29 scales that clear the coverage "
      "gate." % len(rows))
    a("")
    a("**Three sources, and they are not the same kind of object.** Two are "
      "published human norms; two are ours, rated by one model at temperature "
      "zero. The `k_` and `v6:` prefixes exist to keep that visible at every "
      "call site, and no table here should be read as putting them on a level "
      "with Warriner.")
    a("")
    a("**Out of context versus in context.** `warriner_*` and `k_*` score a "
      "word ALONE — one number per word, the same at every prompt. `v6:*` "
      "scores a word INSIDE ITS FRAME, so `jump` is mundane in a park and not "
      "off a roof, and the same word carries different numbers at different "
      "prompts. A scale's grain is stated in each entry.")
    a("")
    a("**Why the same words recur in the contextual mover lists.** `whispered`, "
      "`watched`, `Paris` and `phone` head the gainers for vocalization, "
      "mundanity AND fit, because they are the corpus's biggest net gainers "
      "full stop — the ranking is by mass moved, not by the scale. The "
      "informative column is the NUMBER beside each word: the same gain counts "
      "as a rise in mundanity (7), a rise in fit (7) and nothing at all in "
      "vocalization (1). Where the modal value swamps a list, a second pass "
      "shows the same ranking among words that are off it.")
    a("")
    a("**Two scales have no y-axis direction.** `Vulgarity` and `Makes worse` "
      "sit at exactly 0.000 marginal change because most lineages are tied. "
      "Their result is the dose slope, and their entries say so rather than "
      "reporting a word-level contrast as agreement.")
    a("")
    a("## The eighteen at a glance")
    a("")
    a("    %-26s %-32s %7s %7s" % ("scale", "source", "dose", "marg"))
    for r in rows:
        src = ("ours, in context (v6)" if r["scale"].startswith("v6:")
               else "ours, out of context (k)" if r["scale"].startswith("k_")
               else "Warriner et al. 2013 (human)")
        a("    %-26s %-32s %+7.2f %+7.2f"
          % (r["field"], src, r["x"], r["y"]))
    a("")
    for i, r in enumerate(rows, 1):
        entry(i, r, cache, fns, mom, L)
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--build-cache", action="store_true")
    ap.add_argument("--build-dose", action="store_true")
    a = ap.parse_args(argv)
    if a.build_cache:
        return build_cache() or 0
    if a.build_dose:
        return build_dose() or 0
    cache = load_cache()
    global _FUNC
    _FUNC = set(cache.get("function", ()))
    fns, mom = value_fns(cache)
    rows = scales()
    out = render(cache, fns, mom, rows)
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w").write(out)
        print("wrote %s (%d scales)" % (OUT, len(rows)))
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
