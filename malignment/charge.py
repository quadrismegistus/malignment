"""How transgressive is what a model is about to say? The `task_charge` ratings.

    from malignment import charge

    charge.dose("He hated her deeply and wanted to")      -> 4.61
    charge.lift(p)                                        -> dose - frame
    charge.scene(p)                                       -> {"kill": 6.4, ...}
    charge.T(charge.scene(p), {"kill": 0.03, "scream": 0.1})  -> (5.1, 0.13)
    charge.response(p)                                    -> {base_id: 0.084, ...}
    charge.sample(40, strata=5)                           -> dose-stratified prompts

and, keyed by MODEL rather than by prompt:

    charge.lineages()                 -> the 50 base ids
    charge.responses(base)            -> {prompt: T_base - T_aligned}
    charge.words(p, base)             -> {word: {scene, kind}}
    charge.snapshot(p, base)          -> the same, plus annotation-time masses
    charge.arms(p, base)              -> (T_base, T_aligned) as annotated

and, for anything living in ClickHouse, by delegation to `movement`:

    charge.masses(models, prompts)            -> movement.words_multi, one query
    charge.transgressiveness(models, prompts) -> {prompt: {model: (T, covered)}}

**THE PROMPT-KEYED CALLS ARE AGGREGATES OVER LINEAGES; THE MODEL-KEYED ONES ARE
NOT.** `scene()` averages a word's rating over every lineage that rated it, which
is right because the rating is a property of the word-in-frame. `words()` gives
one lineage's cell, and which words a cell even contains is a fact about what
that base arm offered, so those lists are not a common population.

**AND THIS MODULE OWNS RATINGS ONLY.** The annotation carries frozen `p_base` /
`p_aligned` for reproducing an annotated figure exactly (`snapshot()`), but
anything read live comes from `movement` -- `masses()` and `transgressiveness()`
are delegations to `movement.words_multi`, passing `rule_version` and `frame`
through rather than defaulting them away. A second path to the same table is how
two seats end up quoting numbers read under different rules.

**YOU DO NOT NEED TO KNOW ANYTHING ABOUT `dose_response` TO USE THIS.** The
experiment built the ratings; this module is the accessor. Everything is keyed by
prompt text, values are floats, and the only concept you must hold is the 1-7
scale below.

## WHAT WAS ANNOTATED

`task_charge` (sha `78d73c40f097761f`) is shown a prompt and its candidate
continuations and rates, on a 1-7 scale, **the completed scene** -- what the
sentence describes once that word is in it, not the word in isolation. It also
rates the `frame`, the setup alone, on the same scale, so `scene - frame` is the
word's increment rather than the sentence's level.

    charge_en50_flash.jsonl   109,593 cells = 2,400 English prompts x 50
                              endpoint pairs, deepseek-v4-flash

Every candidate word in every cell carries a `scene` rating and a `kind`
(SEXUAL, VIOLENT, DEGRADING, COERCIVE, ILLICIT, OTHER, NONE).

## THE TWO QUANTITIES ARE NOT THE SAME KIND OF THING

**`dose` is a property of the PROMPT.** Pairwise reliability across lineages
0.929; at n=50 lineages, 0.998. Averaging over lineages is therefore nearly free
and `dose()` does it.

**`response` is a property of the LINEAGE.** Reliability 0.094. It is `T_base -
T_aligned` for one pair on one prompt, and averaging it over prompts or over
lineages throws away the thing that varies. `response()` returns the per-lineage
dict, unaveraged, deliberately.

**AND THE RESPONSE SATURATES, WHICH MAKES `dose` THE WRONG SELECTOR.** Frames
rated 5-7 carry the highest dose and show essentially zero response. A
dose-response plot over the full range is not monotone, and selecting the
highest-dose prompts selects into the flat region: `corr(effect, dose) = -0.091`
against `corr(effect, lift) = -0.261`, where lift is `dose - frame`. **Use
`lift()` for anything asking whether alignment moves a distribution**; `dose` is
the level of the scene, which is a different question. See `lift()` for the
numbers and for why headroom (`7 - dose`) is not the same quantity and predicts
nothing.

## T, AND WHY IT IS NORMALISED

    T = sum(scene_w * p_w) / sum(p_w)

**The denominator is what makes it a measure of displacement rather than of
concentration.** An unnormalised sum falls whenever a distribution tightens
anywhere else, so it would score every sharpening as a reduction in
transgressiveness. `T` answers: given that the model reaches for one of the rated
words, how charged is the one it reaches for.

`T()` returns `(value, covered)` and callers must look at `covered`. A `T` over
3% of the distribution is a statement about 3% of the distribution. It is a pure
function of two dicts -- feed it output probabilities from the movement store,
per-layer probabilities from `lens.layer_probs`, or anything else keyed by word.

## WHAT IS NOT HERE

**One rating model, one language.** flash, English. Agreement with
deepseek-v4-pro is spearman 0.914 on dose and 0.913 on response over the charged
cells, but **that was measured on the Amber lineage only** -- it is not a
roster-wide agreement figure. The 407 Chinese prompts are unrated.

**The words are the model's candidates, not a lexicon.** Which words appear in a
cell is a fact about what that pair's base arm offered; `scene` only rates them.
Two prompts' vocabularies are not the same population, so word-level comparison
across prompts needs its own justification.
"""

import collections
import hashlib
import json
import os
import random
import statistics as st

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
#: **ONE INDEX OVER BOTH LANGUAGES, BECAUSE IT IS ONE INSTRUMENT.** The Chinese
#: corpus was rated by the same `task_charge` with the same seven ENGLISH shots,
#: deliberately: translating the shots would have made a second instrument with a
#: second sha, and the two languages' ratings would no longer sit on one scale.
#: Validated before the run -- on 63 translation pairs whose two sides describe
#: the same scene, `frame` agrees at pearson +0.933, against the English
#: within-language pairwise reliability of 0.929. Prompt text is the key and zh
#: and en texts never collide.
SOURCES = [
    os.path.join(DATA, "dose_response", "charge_en50_flash.jsonl"),
    os.path.join(DATA, "dose_response", "charge_zh50_flash.jsonl"),
]
SOURCE = SOURCES[0]                      # back-compat for callers that named it
INDEX = os.path.join(DATA, "dose_response", "charge_index.json")
INSTRUMENT_SHA = "78d73c40f097761f"
SCALE = (1, 7)

#: bumped whenever `_build` changes what it stores. **A SHA-VALID INDEX WITH AN
#: OLD SHAPE IS THE WORSE FAILURE** -- the source has not changed, so a digest
#: check passes and the new accessors raise KeyError on a cache that looks fresh.
SCHEMA = 3

_IX = None


def sources():
    """The source files that exist, in declared order."""
    return [p for p in SOURCES if os.path.exists(p)]


def _digest(paths=None):
    """One digest over every source present, so adding a language invalidates."""
    h = hashlib.sha256()
    for path in (paths if paths is not None else sources()):
        h.update(os.path.basename(path).encode())
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 22), b""):
                h.update(b)
    return h.hexdigest()[:16]


def _build():
    """Collapse the 230MB cell stream to a per-prompt index plus cell offsets.

    **THE OFFSETS ARE WHY THE PER-LINEAGE DETAIL IS NOT IN THE INDEX.** Keeping
    every cell's word masses would be ~16M floats and defeat the point of an
    index; keeping a byte offset per (prompt, lineage) is 120k integers and makes
    any single cell a seek plus one readline. The offsets are only valid for the
    exact bytes they were built from, which is what `source_sha` guards.
    """
    scene = collections.defaultdict(lambda: collections.defaultdict(list))
    kind = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    frame = collections.defaultdict(list)
    fkind = collections.defaultdict(collections.Counter)
    resp = collections.defaultdict(dict)
    offs = collections.defaultdict(dict)
    bases = set()
    n = 0
    lang = {}
    #: offsets are (file index, byte offset) now that there is more than one
    #: source -- a bare offset was only ever valid against a single file.
    for fi, src in enumerate(sources()):
        pos = 0
        for raw in open(src, "rb"):
            r = json.loads(raw)
            p = r["prompt"]
            offs[p][r["base"]] = [fi, pos]
            bases.add(r["base"])
            lang.setdefault(p, r.get("lang") or "en")
            pos += len(raw)
            n += 1
            if r.get("frame") is not None:
                frame[p].append(r["frame"])
            if r.get("frame_kind"):
                fkind[p][r["frame_kind"]] += 1
            if r.get("T_base") is not None and r.get("T_aligned") is not None:
                resp[p][r["base"]] = r["T_base"] - r["T_aligned"]
            for w in r["words"]:
                scene[p][w["word"]].append(w["scene"])
                kind[p][w["word"]][w["kind"]] += 1
    out = {}
    for p in scene:
        sc = {w: sum(v) / len(v) for w, v in scene[p].items()}
        out[p] = dict(
            scene=sc,
            kind={w: c.most_common(1)[0][0] for w, c in kind[p].items()},
            n_lineages=len(resp.get(p, {})) or max(len(v) for v in scene[p].values()),
            frame=(sum(frame[p]) / len(frame[p])) if frame.get(p) else None,
            frame_kind=fkind[p].most_common(1)[0][0] if fkind.get(p) else None,
            #: the mean over WORDS, so a prompt is not weighted by how many
            #: lineages happened to rate it.
            dose=sum(sc.values()) / len(sc) if sc else None,
            response=resp.get(p, {}),
            lang=lang.get(p, "en"),
        )
    return dict(sources=[os.path.basename(x) for x in sources()],
                source=os.path.basename(SOURCE), source_sha=_digest(),
                instrument_sha=INSTRUMENT_SHA, schema=SCHEMA, n_cells=n,
                lineages=sorted(bases), prompts=out, offsets=dict(offs))


def index(rebuild=False):
    """The per-prompt index, built once and cached beside the source.

    **THE CACHE CARRIES THE SOURCE'S DIGEST AND CHECKS IT.** A stale index that
    keeps answering is the failure mode that matters here -- a caller cannot tell
    a cached dose from a current one, and the source file grows as lineages are
    added. A digest mismatch rebuilds rather than warns.
    """
    global _IX
    if _IX is not None and not rebuild:
        return _IX
    if os.path.exists(INDEX) and not rebuild:
        try:
            ix = json.load(open(INDEX))
            if ix.get("source_sha") == _digest() and ix.get("schema") == SCHEMA:
                _IX = ix
                return _IX
        except (ValueError, KeyError):
            pass
    _IX = _build()
    tmp = INDEX + ".tmp"
    json.dump(_IX, open(tmp, "w"))
    os.replace(tmp, INDEX)
    return _IX


def _p(prompt):
    return index()["prompts"].get(prompt)


def prompts(lang=None):
    """Every prompt with ratings, sorted. `lang="zh"` or `"en"` to restrict."""
    ix = index()["prompts"]
    return sorted(p for p, d in ix.items() if lang is None or d.get("lang") == lang)


def dose(prompt):
    """Mean scene rating over the prompt's candidate words, 1-7, or None.

    A property of the PROMPT: reliability 0.929 pairwise across lineages, 0.998
    at n=50. This is the annotated dose, not a model's behaviour.
    """
    d = _p(prompt)
    return d["dose"] if d else None


def doses():
    """{prompt: dose} for every rated prompt."""
    return {p: d["dose"] for p, d in index()["prompts"].items() if d["dose"] is not None}


def scene(prompt):
    """{word: mean rating} for the prompt's candidate words, or {}."""
    d = _p(prompt)
    return dict(d["scene"]) if d else {}


def kinds(prompt):
    """{word: modal kind} -- SEXUAL, VIOLENT, DEGRADING, COERCIVE, ILLICIT, OTHER, NONE."""
    d = _p(prompt)
    return dict(d["kind"]) if d else {}


def lift(prompt):
    """dose - frame: how much the candidate words add OVER their setup, or None.

    **THIS IS THE DOSE ANY DISPLACEMENT WORK WANTS, NOT `dose()`.** Measured on
    593 prompts x ~35 endpoint pairs against the displacement each prompt
    produced:

        corr(effect, dose)          -0.091      the level
        corr(effect, dose - frame)  -0.261      the lift
          ... within frames below 5 -0.311
        corr(effect, 7 - dose)      +0.091      distance from the ceiling: nothing

    `dose` is the level of the finished scene and it barely predicts anything,
    because **the response saturates**: effect peaks at frames 2-4 and falls away
    above 5 while dose climbs monotonically. A frame already rated 6.4 has
    candidate words no more transgressive than the setup, so there is nothing for
    alignment to displace. The lift collapses with it -- mean `dose - frame` runs
    +0.38 at frame 2-3 to **-0.05** at frame 6-7 -- and it is the lift, not the
    level, that tracks the outcome.

    **AND LIFT IS NOT HEADROOM.** `corr(dose - frame, 7 - dose) = -0.004`: how
    much room is left below the ceiling is a different quantity and an
    uninformative one. Selecting on `7 - dose` selects on nothing.

    Selecting a 611-prompt population on `dose >= 4` produced ONE readable pair
    out of 32; `frame < 5 AND lift > 0.5` over the same measured prompts produced
    eight. Use `dose` when the question is how charged a scene is; use `lift`
    when the question is whether anything can move.
    """
    d = _p(prompt)
    if not d or d["dose"] is None or d["frame"] is None:
        return None
    return d["dose"] - d["frame"]


def lifts():
    """{prompt: lift} for every prompt carrying both a dose and a frame.

    This is the PROMPT-LEVEL lift — averaged over lineages. For per-lineage
    lift (T_base - frame), use `lift_per_lineage()`.
    """
    out = {}
    for p, d in index()["prompts"].items():
        if d["dose"] is not None and d["frame"] is not None:
            out[p] = d["dose"] - d["frame"]
    return out


def lift_per_lineage(prompt, base):
    """T_base - frame for a specific (prompt, lineage) pair, or None.

    **THIS IS THE PER-LINEAGE LIFT AND IT IS THE RIGHT PREDICTOR FOR
    PER-LINEAGE DISPLACEMENT.** `lift()` averages dose over lineages, which
    is valid because word scene ratings are reliable across lineages (0.929).
    But `T_base` weights those ratings by the BASE ARM'S OWN MASS
    DISTRIBUTION, which varies by model: two bases on the same prompt carry
    different candidate words at different probabilities, so their
    transgressiveness levels differ.

    The prompt-level lift (dose - frame) predicts at r=-0.261 across lineages
    pooled. The per-lineage lift uses each base arm's own T, which is the
    quantity that should predict that lineage's response because it is what
    alignment is actually displacing.

    Returns `T_base - frame`, or None if either is missing.
    """
    c = cell(prompt, base)
    if not c or c.get("T_base") is None:
        return None
    f = frame(prompt)
    if f is None:
        return None
    return c["T_base"] - f


def lifts_per_lineage(base=None):
    """{(prompt, base): lift} for every annotated cell, or for one lineage.

        lifts_per_lineage()                   # all 109k cells
        lifts_per_lineage("allenai/OLMo-3-1025-7B")  # one lineage

    Reads the source file directly (one pass) rather than seeking per cell.
    """
    import json as _json
    out = {}
    ix = index()
    frames = {p: d["frame"] for p, d in ix["prompts"].items()
              if d["frame"] is not None}
    with open(SOURCE, "rb") as fh:
        for raw in fh:
            r = _json.loads(raw)
            if base is not None and r["base"] != base:
                continue
            f = frames.get(r["prompt"])
            tb = r.get("T_base")
            if f is None or tb is None:
                continue
            out[(r["prompt"], r["base"])] = tb - f
    return out


def frame(prompt):
    """The setup alone on the same 1-7 scale, so `scene - frame` is the increment."""
    d = _p(prompt)
    return d["frame"] if d else None


def frame_kind(prompt):
    d = _p(prompt)
    return d["frame_kind"] if d else None


def response(prompt):
    """{base_model_id: T_base - T_aligned}, per lineage, UNAVERAGED.

    A property of the LINEAGE (reliability 0.094). Averaging this over lineages
    or prompts discards the quantity that varies; if you want a summary, decide
    and declare which one.
    """
    d = _p(prompt)
    return dict(d["response"]) if d else {}


def lineages():
    """The base model ids annotated, sorted. 50 endpoint pairs."""
    return list(index()["lineages"])


def language(prompt):
    """"en" or "zh" for a rated prompt, or None."""
    d = _p(prompt)
    return d.get("lang") if d else None


def cell(prompt, base):
    """One annotated cell in full, or None. A seek plus one readline.

    Keys: reading, axis, frame, frame_kind, words[{word, scene, kind, p_base,
    p_aligned}], notable, T_base, T_aligned, n_cand, complete, lang.
    """
    off = index()["offsets"].get(prompt, {}).get(base)
    if off is None:
        return None
    fi, pos = off if isinstance(off, (list, tuple)) else (0, off)
    with open(sources()[fi], "rb") as f:
        f.seek(pos)
        return json.loads(f.readline())


def words(prompt, base):
    """{word: {scene, kind}} -- one lineage's annotation, ratings only.

    Which candidates a cell contains is a fact about what that base arm offered,
    so this is per-lineage even though `scene` is a rating: two lineages on the
    same prompt do not have the same word list.
    """
    c = cell(prompt, base)
    if not c:
        return {}
    return {w["word"]: {"scene": w["scene"], "kind": w["kind"]}
            for w in c["words"]}


def snapshot(prompt, base):
    """{word: {scene, kind, p_base, p_aligned}} -- the masses AS OF ANNOTATION.

    **THESE MASSES ARE FROZEN, NOT CURRENT.** They are what the store held when
    `task_charge` ran, carried along so a cell is self-contained. Use them to
    reproduce an annotated `T_base`/`T_aligned` exactly; use `masses()` for what
    the store holds now. If the two disagree, the store has been reingested since
    the annotation and this module is not the place to reconcile them.
    """
    c = cell(prompt, base)
    if not c:
        return {}
    return {w["word"]: {k: w.get(k) for k in
                        ("scene", "kind", "p_base", "p_aligned")}
            for w in c["words"]}


def masses(models, prompts, rule_version=4, frame=""):
    """{prompt: {model: {word: p}}} from the movement store. ONE query.

    **THIS MODULE OWNS RATINGS AND NOTHING ELSE.** Anything in ClickHouse is
    `movement`'s; this is a delegation to `movement.words_multi`, not a second
    path to the same table. Two accessors on one store is how two callers end up
    quoting figures read under different rule versions or frames, so
    `rule_version` and `frame` are passed straight through rather than defaulted
    away.

    **AND IT IS BULK BY CONSTRUCTION.** `movement.word_probs` was retired
    precisely because cell-at-a-time is the shape ClickHouse is worst at -- 192
    ms/cell point-querying against 0.097 ms/cell in bulk. A one-prompt call is a
    list of length one; there is deliberately no scalar entry point to reach for
    inside a loop.
    """
    from malignment import movement
    ms = [models] if isinstance(models, str) else list(models)
    ps = [prompts] if isinstance(prompts, str) else list(prompts)
    if not ms or not ps:
        return {}
    return movement.words_multi(ms, ps, rule_version=rule_version, frame=frame)


def transgressiveness(models, prompts, rule_version=4, frame="", per_lineage=False):
    """{prompt: {model: (T, covered)}} over CURRENT store masses. ONE query.

    The composition most callers want: this module's ratings against
    `movement`'s distributions. Ratings default to the cross-lineage mean
    (`scene`); `per_lineage=True` uses each model's own annotated word list
    instead, which is the right choice when the question is about that model's
    candidates rather than about the frame.
    """
    got = masses(models, prompts, rule_version=rule_version, frame=frame)
    out = {}
    for p, bym in got.items():
        base_scene = scene(p)
        row = {}
        for m, probs in bym.items():
            sc = base_scene
            if per_lineage:
                w = words(p, m)
                sc = {k: v["scene"] for k, v in w.items()} or base_scene
            row[m] = T(sc, probs)
        out[p] = row
    return out


def arms(prompt, base):
    """(T_base, T_aligned) as annotated, or (None, None)."""
    c = cell(prompt, base)
    return (c["T_base"], c["T_aligned"]) if c else (None, None)


def responses(base):
    """{prompt: T_base - T_aligned} for ONE lineage across every prompt it rated.

    The transpose of `response()`. This is the model-keyed view, and it is the
    one to use when the question is about a model rather than about a frame --
    the response is a property of the lineage (reliability 0.094), so pooling it
    across lineages discards what varies.
    """
    out = {}
    for p, d in index()["prompts"].items():
        v = d["response"].get(base)
        if v is not None:
            out[p] = v
    return out


def T(scene_map, probs):
    """(mass-weighted mean rating, covered mass) over the words in both dicts.

    Pure. `probs` is {word: probability} from wherever -- the movement store,
    `lens.layer_probs`, a generation count. Words absent from either dict are
    dropped, so `covered` is the share of `probs`' total mass that was rateable
    and MUST be reported alongside the value.
    """
    tot = sum(probs.values()) or 0.0
    num = 0.0
    cov = 0.0
    for w, p in probs.items():
        s = scene_map.get(w)
        if s is None:
            continue
        num += s * p
        cov += p
    if cov <= 0:
        return float("nan"), 0.0
    return num / cov, (cov / tot if tot else 0.0)


def sample(n, strata=5, seed=0, among=None, min_words=8, by="dose"):
    """`n` prompts spread evenly across `strata` equal-count bands of `by`.

    **`by="lift"` IS ALMOST ALWAYS WHAT DISPLACEMENT WORK WANTS.** The default
    stays "dose" so existing callers are unchanged, but see `lift()`: selecting a
    population on dose gave 1 readable pair of 32 where lift gave 8, on the same
    measured prompts. If the question is whether alignment moves anything, band
    on lift.

    **SELECTING THE TOP-N BY DOSE SELECTS INTO THE SATURATED REGION** -- frames
    rated 5-7 carry the highest dose and show essentially zero response. A
    stratified draw keeps the low and middle bands, which is where the response
    lives. `among` restricts to a candidate set (e.g. the prompts a sidecar
    holds); `min_words` drops prompts with too few rated candidates to weight.
    """
    ix = index()["prompts"]
    key = (lambda p: ix[p]["dose"] - ix[p]["frame"]) if by == "lift" else (
        lambda p: ix[p]["dose"])
    pool = [p for p in (among if among is not None else ix)
            if p in ix and ix[p]["dose"] is not None
            and (by != "lift" or ix[p]["frame"] is not None)
            and len(ix[p]["scene"]) >= min_words]
    if not pool:
        return []
    pool.sort(key=key)
    rng = random.Random(seed)
    edges = [round(i * len(pool) / strata) for i in range(strata + 1)]
    bands = [pool[edges[i]:edges[i + 1]] for i in range(strata)]
    out = []
    for i in range(n):
        b = bands[i % strata]
        if b:
            out.append(b.pop(rng.randrange(len(b))))
    return sorted(set(out), key=key)


def stats():
    """A one-glance summary of what the index holds."""
    ix = index()
    d = sorted(v["dose"] for v in ix["prompts"].values() if v["dose"] is not None)
    k = collections.Counter(v["frame_kind"] for v in ix["prompts"].values())
    return dict(source=ix["source"], source_sha=ix["source_sha"],
                instrument_sha=ix["instrument_sha"], n_cells=ix["n_cells"],
                n_prompts=len(ix["prompts"]),
                dose_min=d[0], dose_med=st.median(d), dose_max=d[-1],
                frame_kinds=dict(k.most_common()))


if __name__ == "__main__":
    s = stats()
    print("%s  sha %s  instrument %s" % (s["source"], s["source_sha"],
                                         s["instrument_sha"]))
    print("%d cells | %d prompts | dose %.2f / %.2f / %.2f (min/med/max)"
          % (s["n_cells"], s["n_prompts"], s["dose_min"], s["dose_med"],
             s["dose_max"]))
    print("frame kinds: %s" % s["frame_kinds"])
    print()
    for p in sample(8, strata=4):
        print("  dose %.2f  frame %s  %r"
              % (dose(p), frame(p), p[:58]))
