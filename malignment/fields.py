"""Semantic-field membership and psycholinguistic norms for words.

    from malignment import fields
    fields.sources()                 what is on disk, and what is missing
    fields.rid("stabbed")            {'aggression', ...}
    fields.gi("stabbed")             {'Hostile', 'Negativ', ...}
    fields.k("cock")                 {'vulgarity': 7, 'bodily_harm': 1, ...}
    fields.norms("blood")            {'valence': .., 'concreteness': .., ...}
    fields.lemma("stabbed")          'stab'      (spaCy, contextual if given one)

    python -m malignment.fields --check       every source, present or absent
    python -m malignment.fields "some text"   score one string

## WHY THIS IS A MODULE AND NOT SIX LOOKUPS IN SIX SCRIPTS

`lexicons/fields/README.md` records that getting the lookup policy wrong returns
the WRONG SENSE rather than nothing: surface-form lookup sends `found` to
*establish*, `felt` to the fabric, `saw` to the cutting tool — and `found` is the
corpus's single most frequent riser. A policy in one importable place is a
policy; retyped in six analyses it is six policies.

## THREE THINGS THE ARCHIVE'S VERSION DID THAT THIS DOES NOT

**1. It DEGRADED instead of refusing.** `_byu()` opened with
`if not os.path.exists(BYU): return out` — an empty dict, indistinguishable from
"this word has no POS". So a missing lexicon produced *zero counts*, and a zero
count is a measurement. Here every source is declared in `SOURCES`, `sources()`
reports presence, and **a lookup against an absent source raises**. Absence and
emptiness are different answers and must not share a shape.

**2. It read two paths outside the repository** —
`~/Dropbox/.../norms_sources` and `~/Dropbox/Prof/Code/osp/worddb.byu.txt` — so
it was not reproducible from a clone, and the BYU file is not on this machine at
all. Everything now lives under `lexicons/`.

**3. It used BYU/COCA for lemma and POS.** BYU is a TYPE-level table: one lemma
per surface, no context, and 86,403 forms. spaCy is contextual and already
installed with `en_core_web_sm` and `zh_core_web_sm`. `saw` is the case that
decides it — BYU must answer with one of *see* or *saw*, and in
"she saw him" only one is right.

## COVERAGE IS RETURNED, NOT ASSUMED

A field count without the number of tokens that matched anything is a rate with
no denominator. The General Inquirer is a 1960s resource and its coverage of
explicit violence is thin — `raped`, `desecrated`, `stomped` are all absent — so
on this corpus GI silently drops the transgressive end of the vocabulary. A
caller comparing two texts on GI counts without reading `coverage` is comparing
how much of each text GI happens to know.

## THE K-RATINGS ARE NOT HUMAN NORMS

`k_ratings_en.json`'s own `_meta` says so: *"These are ONE MODEL's judgments at
ONE frozen instrument version -- not Warriner, not Brysbaert."* Two of its scales
carry warnings that survive into any analysis built on them:

    vulgarity          SPARSE. Variance on 463 of 27,242 words (1.7%).
                       "Its floor effects are NOT nulls."
    register_level     NOT ESTABLISHED. Inter-coder 0.60, rank stability 0.62.
                       "Usable as a descriptor, not as evidence."

`k_warnings()` returns these so a caller can print them beside a result rather
than rediscover them.
"""
import argparse
import collections
import csv
import functools
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEX = os.path.join(ROOT, "lexicons")
FIELDS = os.path.join(LEX, "fields")
NORMS = os.path.join(LEX, "norms")

#: EVERY SOURCE DECLARED IN ONE PLACE, so `--check` can answer "what is missing"
#: without importing anything, and so a lookup can refuse by name.
SOURCES = {
    "rid":       os.path.join(FIELDS, "rid_regressive_imagery.csv"),
    "gi":        os.path.join(FIELDS, "general_inquirer.json"),
    "wordnet":   os.path.join(FIELDS, "wordnet_verb_supersenses.json"),
    "usas":      os.path.join(FIELDS, "usas_semantic_lexicon_en.txt"),
    "usas_tags": os.path.join(FIELDS, "usas_tagset.tsv"),
    #: THE CHINESE USAS, added 2026-08-24. Same project, SAME TAGSET --
    #: `usas_tags` decodes both, so a zh field name and an en field name are
    #: the same field and are comparable. The pos vocabulary is NOT shared: zh
    #: uses noun/verb/pnoun/adj/adv/prep/intj/conj against English's UPOS, so
    #: any pos-conditioned read must branch on language. `usas_mwe_zh` is the
    #: multiword table and is not consumed yet.
    "usas_zh":     os.path.join(FIELDS, "usas_semantic_lexicon_zh.tsv"),
    "usas_mwe_zh": os.path.join(FIELDS, "usas_mwe_zh.tsv"),
    "k_en":      os.path.join(NORMS, "k_ratings_en.json"),
    "k_zh":      os.path.join(NORMS, "k_ratings_zh.json"),
    "warriner":  os.path.join(NORMS, "BRM-emot-submit.csv"),
    "brysbaert": os.path.join(NORMS, "Concreteness_ratings_Brysbaert_et_al_BRM.txt"),
    #: Brooke et al.'s formality SEEDS, not a scored lexicon -- see `_brooke`.
    "brooke_formal":   os.path.join(NORMS, "brooke_formality", "formal_seeds_100.txt"),
    "brooke_informal": os.path.join(NORMS, "brooke_formality", "informal_seeds_100.txt"),
    "brooke_pairs":    os.path.join(NORMS, "brooke_formality", "CTRWpairsfull.txt"),
}

TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]*")


class MissingSource(RuntimeError):
    """Raised instead of returning empty. See the module docstring, point 1."""


def sources():
    """{name: (path, present)}. Cheap; opens nothing."""
    return {k: (v, os.path.exists(v)) for k, v in SOURCES.items()}


def _need(name):
    path = SOURCES[name]
    if not os.path.exists(path):
        raise MissingSource(
            "%s is not on disk at %s. A lookup against an absent lexicon would "
            "return an empty result indistinguishable from a real zero, so this "
            "refuses instead. See fields.sources()." % (name, path))
    return path


# ---------------------------------------------------------------- lemma / POS

@functools.lru_cache(maxsize=2)
def _nlp(lang="en"):
    import spacy
    return spacy.load("en_core_web_sm" if lang == "en" else "zh_core_web_sm",
                      disable=["ner", "parser"])


def lemma(word, context=None, lang="en"):
    """Lemma, contextual when `context` is given.

    **THE REASON THIS IS NOT A TABLE.** BYU/COCA maps one surface to one lemma
    with no context. `saw` must then resolve to either *see* or *saw*, and in
    "she saw him" only one is right — while `lexicons/fields/README.md` records
    that the irregulars are exactly where a wrong answer is returned instead of
    none. Pass the sentence and the answer is contextual; pass the word alone and
    it is spaCy's type-level guess, which is BYU's situation but current.
    """
    doc = _nlp(lang)(context if context else word)
    if not context:
        return doc[0].lemma_.lower() if len(doc) else word.lower()
    for t in doc:
        if t.text.lower() == word.lower():
            return t.lemma_.lower()
    return doc[0].lemma_.lower() if len(doc) else word.lower()


def pos(word, context=None, lang="en"):
    doc = _nlp(lang)(context if context else word)
    for t in doc:
        if not context or t.text.lower() == word.lower():
            return t.pos_
    return None


CONTENT_POS = ("NOUN", "VERB", "ADJ", "ADV", "PROPN")


def is_content_word(word, context=None, lang="en"):
    return pos(word, context, lang) in CONTENT_POS


# ------------------------------------------------------------------ lexicons

@functools.lru_cache(maxsize=1)
def _rid():
    """[(regex, thinking, process, category, subcategory)]. RID is REGEXES.

    Martindale's dictionary is written as stems (`\\babsinth`, `\\bale\\b`), so a
    set-membership test against word surfaces would silently miss most of it.

    **`thinking` AND `process` ARE KEPT, AND WERE NOT.** An earlier version
    loaded only category and subcategory, which discarded the two columns
    Martindale's actual claim is about: primordial vs conceptual thinking, and
    primary vs secondary process. Those are the top of the hierarchy -- 1,828
    patterns primordial/primary, 714 conceptual/secondary, 609
    conceptual/emotions -- and no roll-up to them was possible through the API,
    so `count(fine=False)` had been truncating category NAMES at an underscore
    instead (`expressive_behavior` -> `expressive`), which is a string operation
    wearing a hierarchy's clothes.
    """
    out = []
    with open(_need("rid"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                out.append((re.compile(r["regex"], re.I), r.get("thinking", ""),
                            r.get("process", ""), r["category"],
                            r["subcategory"] or ""))
            except re.error:
                continue
    return out


@functools.lru_cache(maxsize=200000)
def rid(word, with_sub=False, level=None):
    """RID categories matching this word.

    **CACHED, AND IT IS THE DIFFERENCE BETWEEN 0.047 AND 0.014 SECONDS PER
    PASSAGE.** RID is 3,151 REGEXES rather than a dict, so every lookup scans
    all of them: measured at 0.000211 s/word against ~0.000001 for every other
    source, a factor of 200. With ~80 content words per passage and a lemma
    fallback doubling each, that is half a million regex searches per passage
    and it dominated the whole battery.

    The cache is on the WORD, and vocabulary is finite and heavily repeated --
    within a passage, and far more so across a corpus. 200,000 entries covers
    an English corpus of any size this project will see. `need/sex` and `emotions/aggression`
    are the two this project most often wants, and they come from ONE dictionary
    with one construction procedure — so a sex-vs-aggression contrast is not
    confounded by the axes having different provenance.

    `level="process"` returns Martindale's TOP classes instead --
    `primordial/primary`, `conceptual/secondary`, `conceptual/emotions` -- which
    is the split his primary-versus-secondary-process claim turns on and the
    one this project's Freudian reading actually needs.
    """
    out = set()
    for rx, think, proc, cat, sub in _rid():
        if not rx.search(word):
            continue
        if level == "full":
            out.add("/".join(x for x in (think, proc, cat, sub) if x))
        elif level == "process":
            out.add("%s/%s" % (think, proc) if think else cat)
        else:
            out.add("%s/%s" % (cat, sub) if with_sub and sub else cat)
    return out


@functools.lru_cache(maxsize=1)
def _gi():
    with open(_need("gi"), encoding="utf-8") as fh:
        return json.load(fh)


def gi(word):
    """General Inquirer categories. Coverage of explicit violence is THIN —
    `raped`, `desecrated`, `stomped` are absent — so an empty set here is as
    likely to be GI's 1960s vocabulary as a property of the word."""
    d = _gi()
    w = (d.get("words") or {})
    return set(w.get(word.upper()) or w.get(word.lower()) or w.get(word) or [])


@functools.lru_cache(maxsize=1)
def _wordnet():
    with open(_need("wordnet"), encoding="utf-8") as fh:
        return json.load(fh)


def wordnet(word, sense="all"):
    """WordNet verb supersenses for this word. -> set

    **THIS LOOKUP WAS DEAD AND RETURNED set() FOR ALL 11,529 LEMMAS.** The file
    is `{"meta": ..., "words": {...}}` and the accessor indexed the TOP level, so
    every lookup missed -- and it raised only when a passage contained the
    literal word `words`, which is how it was finally found: by `count()` being
    the first caller to run it over real prose rather than over a probe.

    A lookup that returns empty for everything is indistinguishable from a word
    genuinely absent from the lexicon, which is why nothing caught it. The
    `--check` output said the SOURCE was present, and it was; only the accessor
    was wrong.

    `sense="all"` is the default on the file's own instruction: its meta records
    that FIRST_SENSE_IS_UNRELIABLE -- `found` resolves to `social` (from "set up
    or found", not the past of find) and `felt` to `contact` (from "mat together,
    make felt-like"), and `found` is this corpus's single most frequent riser.

    The same meta records TOO_COARSE_FOR_SPEECH: `whispered`, `shouted`, `said`
    and `told` share the `communication` supersense while the first two rise and
    the last two fall in M01. That distinction is invisible here and this source
    cannot carry it.
    """
    v = _wordnet().get("words", {}).get(word.lower())
    if not v:
        return set()
    if sense == "first":
        return {v["first"]} if v.get("first") else set()
    return set(v.get("all") or [])


@functools.lru_cache(maxsize=1)
def _usas():
    out = collections.defaultdict(set)
    with open(_need("usas"), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                out[p[0].lower()].add(p[2].split()[0] if p[2] else "")
    return dict(out)


@functools.lru_cache(maxsize=1)
def _usas_names():
    """{code -> name} from the full USAS tagset, 232 base codes."""
    out = {}
    with open(_need("usas_tags"), encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2:
                out[p[0]] = p[1]
    return out


#: A USAS tag is a base code plus MODIFIERS, and the modifiers carry meaning:
#:   +/-   the pole of an antonym pair. `E3` is "Calm/Violent/Angry", so `E3-`
#:         is the VIOLENT end and `E3+` the calm one. Dropping the sign inverts
#:         the reading of every emotion and evaluation tag.
#:   m/f/n gender marking (`L2mn`)
#:   c/%/@ further subdivisions
#:   /     a PORTMANTEAU of two tags (`G2.1-/S3.2`), which must be split or the
#:         whole thing fails to resolve.
#: Measured on this corpus's own vocabulary: 5 of 9 codes produced by
#: stabbed/cock/kiss/blood/killed/raped/beat carry a modifier, so a bare
#: dictionary lookup resolves fewer than half.
_USAS_MOD = re.compile(r"^([A-Z]\d[\w.]*?)([+-]+|[mfnc%@]+)?$")


def usas(word, names=True):
    """USAS tags at the FINEST grain, as names by default.

    `names=False` returns the raw codes. With names, a modifier is preserved in
    brackets rather than discarded -- `E3-` becomes
    "Calm/Violent/Angry [-]" -- because the sign is the difference between
    calm and violent and this project needs exactly that distinction.

    The pole is NOT expanded into which side of the slash it means. USAS writes
    antonym pairs as "X/Y", but `S3.2` is "Relationship: Intimate/sexual", a
    single concept containing a slash. Guessing which slashes are poles would
    silently mislabel the ones that are not.
    """
    raw = set(_usas().get(word.lower(), set()))
    if not names:
        return raw
    T = _usas_names()
    out = set()
    for code in raw:
        for part in code.split("/"):          # portmanteau
            part = part.strip()
            if not part:
                continue
            if part in T:
                out.add(T[part])
                continue
            m = _USAS_MOD.match(part)
            if m and m.group(1) in T:
                out.add("%s [%s]" % (T[m.group(1)], m.group(2) or ""))
                continue
            #: still unresolved: peel trailing modifier chars one at a time
            base = part
            while base and base not in T:
                base = base[:-1]
            out.add("%s [%s]" % (T[base], part[len(base):]) if base else part)
    return out


# --------------------------------------------------------------- k-ratings

@functools.lru_cache(maxsize=2)
def _k(lang="en"):
    with open(_need("k_" + lang), encoding="utf-8") as fh:
        d = json.load(fh)
    return d["_meta"]["scales"], d["ratings"], d["_meta"]


def k(word, lang="en"):
    """{scale: 1-7} or None. See `k_warnings()` before using vulgarity."""
    scales, R, _ = _k(lang)
    v = R.get(word) or R.get(word.lower())
    return dict(zip(scales, v)) if v else None


def k_warnings():
    """The scale caveats, so they travel with the numbers instead of being
    rediscovered. Both are quoted from the archive's own analysis."""
    return {
        "vulgarity": ("SPARSE INDICATOR. Variance on 463 of 27,242 English words "
                      "(1.7%); 0.7% of this corpus's movement rows. "
                      "Its floor effects are NOT nulls."),
        "register_level": ("NOT ESTABLISHED. Inter-coder 0.60, rank stability "
                           "0.62 isolated, z 1.0 against its own null. "
                           "Usable as a descriptor, not as evidence."),
        "_all": ("NOT HUMAN NORMS: one model's judgments at one frozen "
                 "instrument version. Not Warriner, not Brysbaert."),
    }


# ------------------------------------------------------------------- norms

@functools.lru_cache(maxsize=1)
def _norms():
    """{word: {valence, arousal, dominance, concreteness}} from Warriner + Brysbaert."""
    out = collections.defaultdict(dict)
    with open(_need("warriner"), encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            w = (r.get("Word") or "").lower()
            if not w:
                continue
            for src, dst in (("V.Mean.Sum", "valence"), ("A.Mean.Sum", "arousal"),
                             ("D.Mean.Sum", "dominance")):
                try:
                    out[w][dst] = float(r[src])
                except (KeyError, TypeError, ValueError):
                    pass
    with open(_need("brysbaert"), encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            w = (r.get("Word") or "").lower()
            try:
                out[w]["concreteness"] = float(r["Conc.M"])
            except (KeyError, TypeError, ValueError):
                pass
    return dict(out)


@functools.lru_cache(maxsize=1)
def _brooke():
    """{word: +1 formal, -1 informal}. A SPARSE BINARY INDICATOR, not a score.

    **Brooke et al. ship SEEDS, not a lexicon.** 104 formal seeds
    (`admittedly`, `consequently`), 137 informal (`fuck`, `shit`), and 398
    informal/formal PAIRS (`digest/imbibe`, `sot/alcoholic`). Their method
    propagates a continuous score from these; the propagated lexicon is not in
    the source set, so what is loadable is roughly a thousand words carrying a
    SIGN and no magnitude.

    That makes formality here the same kind of object as `k_vulgarity`: a rate,
    not a level. Coverage will be low -- a percent or two of content words -- and
    a passage with no hits has NO MEASUREMENT rather than a formality of zero.
    Any caller that averages the sign over covered words must report the
    denominator, because floors are not nulls.

    Both sides of each CTRW pair are used: the pair file is `informal/formal`,
    so it contributes one word to each side rather than one relation.
    """
    out = {}
    for w in open(_need("brooke_formal"), encoding="utf-8", errors="replace"):
        w = w.strip().lower()
        if w:
            out[w] = 1
    for w in open(_need("brooke_informal"), encoding="utf-8", errors="replace"):
        w = w.strip().lower()
        if w:
            out[w] = -1
    for line in open(_need("brooke_pairs"), encoding="utf-8", errors="replace"):
        parts = line.strip().lower().split("/")
        if len(parts) == 2 and all(parts):
            #: `informal/formal`, in that order, per the file's own layout
            out.setdefault(parts[0], -1)
            out.setdefault(parts[1], 1)
    return out


def brooke(word):
    """+1 formal, -1 informal, None if the word is not a seed. Sparse."""
    return _brooke().get(word.lower())


def word_norms(word):
    """Continuous norms for ONE word. None if absent from both sources."""
    return dict(_norms().get(word.lower(), {})) or None


@functools.lru_cache(maxsize=1)
def norm_cuts():
    """Tertiles of each norm's OWN distribution.

    Cut at tertiles rather than a round number so "high" means high relative to
    English and the three bins are a priori equal. **A threshold nobody can see
    is a free parameter**, so this is a function rather than a constant.
    """
    import statistics
    N = _norms()
    out = {}
    for dim in ("valence", "arousal", "dominance", "concreteness"):
        vals = sorted(v[dim] for v in N.values() if dim in v)
        if len(vals) > 2:
            q = statistics.quantiles(vals, n=3)
            out[dim] = (round(q[0], 3), round(q[1], 3))
    return out


# ------------------------------------------------------- counting over a text

MFDIR = os.path.join(FIELDS, "metafields")

#: The 13 fields SHARED BY EVERY LEXICON, fixed here so a caller can enumerate
#: them without reading a CSV, and so a source mapping to something outside this
#: set is a loud KeyError rather than a quiet new column.
META_FIELDS = ("body_health", "cognition_mental", "communication_speech",
               "emotion_affect", "evaluation_modality", "existence_state",
               "other", "perception_sensation", "physical_action",
               "possession_exchange", "quantity_degree", "social_interpersonal",
               "time_aspect")

LOOKUP = {"rid": rid, "gi": gi, "wordnet": wordnet, "usas": usas}


@functools.lru_cache(maxsize=8)
def _map(name):
    """{native tag -> meta_field} for a lexicon, from metafields/<name>_map.csv."""
    path = os.path.join(MFDIR, "%s_map.csv" % name)
    if not os.path.exists(path):
        raise MissingSource("no meta-field map for %r at %s" % (name, path))
    out = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["category"]] = r["meta_field"]
    return out


@functools.lru_cache(maxsize=4)
def _fine(name):
    """{native tag -> human-readable group} from metafields/<name>.tsv.

    USAS's own taxonomy at full resolution -- `A1.1.2` -> "Damaging and
    destroying" -- which is finer than the 13 shared fields and is the level at
    which violence and sex are separable at all.
    """
    path = os.path.join(MFDIR, "%s.tsv" % name)
    if not os.path.exists(path):
        raise MissingSource("no fine-grain table for %r at %s" % (name, path))
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2:
                out[p[0]] = p[1]
    return out


def count(text, source="usas", lang="en", content_only=False):
    """{field: n} plus coverage, over the tokens of `text`.

    source = "usas" | "gi" | "wordnet" | "rid"   the lexicon's own tags.
                                                 USAS comes back as NAMES at the
                                                 finest grain, modifiers kept.
             "meta"                              the 13 SHARED fields, so usas,
                                                 gi and framenet counts are
                                                 directly comparable

    **COVERAGE IS RETURNED, NOT OPTIONAL.** A field count without the number of
    tokens that matched anything is a rate with no denominator. GI is a 1960s
    resource and misses `stabbed`, `raped`, `desecrated`; comparing two texts on
    GI counts alone compares how much of each GI happens to know.
    """
    toks = TOKEN.findall(text)
    if content_only:
        toks = [t for t in toks if is_content_word(t, text, lang)]
    hits, matched = collections.Counter(), 0
    for t in toks:
        if source == "meta":
            tags = set()
            #: THE META MAP IS KEYED ON CODES, so this asks usas for codes
            #: rather than names. A name-keyed lookup would silently match
            #: nothing and return a clean, wrong zero.
            m = _map("usas")
            tags |= {m[x] for x in usas(t, names=False) if x in m}
            g = _map("gi_primary")
            tags |= {g[x] for x in gi(t) if x in g}
        else:
            tags = LOOKUP[source](t)
        if tags:
            matched += 1
            hits.update(tags)
    return {"counts": dict(hits), "n_tokens": len(toks), "n_matched": matched,
            "coverage": round(matched / len(toks), 4) if toks else 0.0,
            "source": source}


def count_all(text, lang="en", content_only=False):
    """Every source in one call, each with its own coverage.

    Sources are NOT summed. They have different vocabularies and different
    senses of the same word -- `cock` is `L2mn` (a bird) and `G3` (weapons) to
    USAS, absent from RID and GI, and vulgarity 7 to the k-ratings. A total over
    them would be a number about the lexicons, not about the text.
    """
    out = {}
    for src in ("usas", "gi", "wordnet", "rid", "meta"):
        try:
            out[src] = count(text, src, lang, content_only)
        except MissingSource as e:
            out[src] = {"error": str(e)}
    ks = [k(t, lang) for t in TOKEN.findall(text)]
    ks = [x for x in ks if x]
    if ks:
        out["k"] = {"n_rated": len(ks),
                    "max": {s: max(x[s] for x in ks) for s in ks[0]},
                    "mean": {s: round(sum(x[s] for x in ks) / len(ks), 2) for s in ks[0]}}
    return out


# --------------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="*")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check or not a.text:
        print("  lexicons under %s\n" % os.path.relpath(LEX, ROOT))
        miss = 0
        for name, (path, ok) in sorted(sources().items()):
            miss += not ok
            print("     %-11s %-5s %s" % (name, "OK" if ok else "MISS",
                                          os.path.relpath(path, ROOT)))
        print("\n  %d missing. A lookup against a missing source RAISES rather "
              "than returning empty." % miss)
        if not miss:
            print("\n  k-rating caveats that travel with any result:")
            for k_, v in k_warnings().items():
                print("     %-16s %s" % (k_, v))
        return 0
    text = " ".join(a.text)
    for tok in TOKEN.findall(text):
        parts = []
        r = rid(tok, with_sub=True)
        if r:
            parts.append("rid=%s" % sorted(r))
        g = gi(tok)
        if g:
            parts.append("gi=%s" % sorted(g)[:4])
        kk = k(tok)
        if kk:
            hot = {s: v for s, v in kk.items() if v >= 5}
            if hot:
                parts.append("k>=5 %s" % hot)
        if parts:
            print("  %-16s %s" % (tok, "  ".join(parts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())


def as_word_map(source, scale=None, vocab=None):
    """{word: label} + kind, for joining a declared field to movement.

    THE ADAPTER `wordfield.WordField.from_fields` USES. It lives here, not there,
    because an absent source must raise `MissingSource` from the module that
    declares it -- `wordfield` reading these files itself would turn a missing
    lexicon into a clean empty join, and an empty join is a result of zero rather
    than an error. Absence and emptiness must not share a shape.

    **RID IS REGEXES, NOT A WORD LIST.** Martindale's dictionary is written as
    stems (`\\babsinth`, `\\bale\\b`), so it has no word map until it is applied
    to a vocabulary -- and THAT VOCABULARY IS THEN PART OF THE INSTRUMENT, because
    which words RID appears to cover depends entirely on which words you asked it
    about. `vocab` is therefore required for rid, and the caller must record it.

    Categorical sources return the word's FIRST category. A word carrying several
    (USAS routinely does) is represented once, which is LOSSY: for finer work
    build an explicit WordField from `usas(word, names=True)` and record what was
    kept. Returning one tag silently is the coarse-predicate/fine-fact error, so
    it is named here rather than discovered downstream.

        rid                         categorical, REQUIRES vocab
        gi / wordnet / usas         categorical
        k_en / k_zh                 continuous, `scale` required
        warriner / brysbaert        continuous, `scale` required
    """
    if source in ("k_en", "k_zh"):
        scales, R, _ = _k(source.split("_")[1])
        if scale not in scales:
            raise ValueError("scale must be one of %s" % (list(scales),))
        i = list(scales).index(scale)
        return ({w: float(v[i]) for w, v in R.items()
                 if v and v[i] is not None}, "continuous")
    if source in ("warriner", "brysbaert"):
        got = {w: d[scale] for w, d in _norms().items()
               if scale in d and d[scale] is not None}
        if not got:
            raise ValueError("no values for scale %r in %r; try norms(word).keys()"
                             % (scale, source))
        return {w: float(v) for w, v in got.items()}, "continuous"
    if source == "rid":
        if not vocab:
            raise ValueError("rid is a set of REGEXES and has no word map without a "
                             "vocabulary; pass vocab= and record it as part of the "
                             "instrument")
        pats = _rid()
        out = {}
        for w in vocab:
            for rx, cat, _sub in pats:
                if rx.search(w):
                    out[w] = cat
                    break
        return out, "categorical"
    if source == "gi":
        words = (_gi().get("words") or {})
        return ({w.lower(): (v[0] if isinstance(v, (list, tuple)) else v)
                 for w, v in words.items() if v}, "categorical")
    if source == "wordnet":
        # The file's OWN _meta says FIRST_SENSE_IS_UNRELIABLE, verified on this
        # corpus: `found` -> social (the first synset is "set up or found", not
        # the past of find) and `felt` -> contact. Those are the #1 riser and a
        # sink. It also says TOO_COARSE_FOR_SPEECH -- whispered/shouted/said/told
        # share `communication` while the first two rise and the last two fall.
        # Returned anyway, because refusing a source the caller declared is not
        # this function's decision, but the warning travels with the numbers.
        words = (_wordnet().get("words") or {})
        return ({w: d.get("first") for w, d in words.items() if d.get("first")},
                "categorical")
    if source == "usas":
        skip = {"lemma", "word", "pos"}          # the file's own header row
        out = {}
        for w, tags in _usas().items():
            if w in skip:
                continue
            good = sorted(t for t in tags if t and _USAS_MOD.match(t))
            if good:
                out[w] = good[0]
        return out, "categorical"
    raise ValueError("unknown source %r; declared: %s" % (source, sorted(SOURCES)))


# ---------------------------------------------------------------------------
# TWO ENTRY POINTS: one per KIND of source
# ---------------------------------------------------------------------------
#
# `norms(text)`  scalar sources -> MEANS      warriner, brysbaert, brooke, k
# `count(text)`  set sources    -> RATES      rid, gi, usas, wordnet
#
# They tokenise and lemmatise identically and differ only in what the sources
# ARE. A norm gives a word a NUMBER, so the summary is a mean over the words
# that have one. A field gives a word a MEMBERSHIP, so the summary is the share
# of words that have it. Putting both in one dict works and hides that: it
# invites averaging a rate or rating a count, and the key prefix is the only
# thing standing in the way. Two functions make the distinction structural.

#: which lookups take a LEMMA fallback -- all of them. Every source keys on base
#: forms, so `screamed`, `wanted` and `bodies` miss on the surface and hit on the
#: lemma. Without it a passage's coverage is roughly its share of uninflected
#: words, which is a fact about English morphology rather than about the
#: passage -- and it would differ BY ARM, since the arms differ in tense and
#: number usage. The miss is silent either way: a lookup returns None.
_LEMMA_FALLBACK = ("norms", "brooke", "k", "rid", "gi", "usas", "wordnet")

_SCALAR = ("norms", "brooke", "k")
_SET = ("rid", "gi", "usas", "wordnet")


def _lookup(kind, word, lem):
    """One source, surface first then lemma. -> value, or None/empty."""
    f = {"norms": word_norms, "brooke": brooke, "k": k, "rid": rid,
         "gi": gi, "usas": usas, "wordnet": wordnet,
         #: CODES, not names -- the dotted code is what carries the hierarchy
         "usas_codes": lambda x: usas(x, names=False)}[kind]
    v = f(word)
    if not v and lem and lem != word:
        v = f(lem)
    return v


def content_words(text, lang="en"):
    """[(surface, lemma)] for content words only. The shared front end.

    **Content words only** -- NOUN, VERB, ADJ, ADV by UPOS -- which is the rule
    M06's Plan C fixes. Function words carry no valence and belong to no
    semantic field, so including them would dilute every mean and every rate in
    proportion to syntactic complexity rather than to content.
    """
    #: `text` may be a spaCy Doc already parsed by `all_batch()`. Tagging is
    #: ~75% of the cost of a passage, so the batch path parses ONCE and hands
    #: the Doc down rather than re-parsing per source.
    doc = text if hasattr(text, "is_parsed") or type(text).__name__ == "Doc" \
        else _nlp(lang)(text)
    return [(t.text.lower(), (t.lemma_ or "").lower())
            for t in doc if t.is_alpha
            and t.pos_ in ("NOUN", "VERB", "ADJ", "ADV")], \
           sum(1 for t in doc if t.is_alpha)


def norms(text, lang="en", cw=None):
    """SCALAR sources, averaged. -> flat dict

        fields.norms("this is a good good good bad donkey")
        {'n_content': 5, 'warriner_valence': 6.64, 'warriner_coverage': 1.0, ...}

    Warriner (valence, arousal, dominance), Brysbaert (concreteness), Brooke
    (formality, +1/-1) and the seven K coder scales.

    ## EACH SOURCE AVERAGES OVER ITS OWN COVERED WORDS

    A word absent from Warriner contributes nothing to `warriner_valence` and is
    NOT counted as neutral. Treating a miss as a mid-scale value is how a
    coverage difference becomes a fake effect, so the denominators differ
    between sources on purpose and every source carries its own `*_coverage`.

    **Coverage is reported, never corrected.** It is expected to differ by arm --
    proper nouns are absent from the norms and NNP runs about 7 per 1000 words
    lower in the aligned arm -- and that is a property of the text.

    ## TWO SPARSE ONES, MARKED

    `brooke_formality` is a mean of +1/-1 over a 1,029-word seed list (Brooke
    ships SEEDS, not a scored lexicon) and `k_vulgarity` has variance on 463 of
    27,242 rated words. Both routinely cover a percent or two of a passage. A
    passage with no hits gets NO KEY rather than a 0.0: floors are not nulls.

    ## `valence_extremity` IS COMPUTED HERE, NOT LEFT TO THE CALLER

    It is mean|v - 5|, not |mean(v) - 5|, and the two differ whenever a passage
    mixes positive and negative words -- which is the case the plan's C.H1 is
    about. Computing it here removes the chance of a caller taking the second.
    `warriner_valence_sd` is the spread, which is a different claim again.
    """
    import statistics as _st
    words, n_tok = cw if cw is not None else content_words(text, lang)
    out = {"n_tokens": n_tok, "n_content": len(words)}
    if not words:
        return out
    acc, cov = collections.defaultdict(list), collections.Counter()
    for w, lem in words:
        n = _lookup("norms", w, lem)
        if n:
            if "valence" in n:
                cov["warriner"] += 1
            if "concreteness" in n:
                cov["brysbaert"] += 1
            for dim, v in n.items():
                acc["brysbaert_concreteness" if dim == "concreteness"
                    else "warriner_" + dim].append(v)
        b = _lookup("brooke", w, lem)
        if b is not None:
            acc["brooke_formality"].append(float(b)); cov["brooke"] += 1
        kk = _lookup("k", w, lem)
        if kk:
            cov["k"] += 1
            for dim, v in kk.items():
                acc["k_" + dim].append(float(v))
    for key, vals in acc.items():
        out[key] = round(_st.mean(vals), 4)
    v = acc.get("warriner_valence")
    if v:
        out["warriner_valence_extremity"] = round(
            _st.mean(abs(x - 5.0) for x in v), 4)
        if len(v) > 1:
            out["warriner_valence_sd"] = round(_st.stdev(v), 4)
    for src, c in cov.items():
        out[src + "_coverage"] = round(c / len(words), 4)
    return out


def all_fields(text, lang="en", cw=None):
    """`norms()` and `count()` merged, over ONE parse. -> flat dict

    The two functions each called `content_words()`, so a caller wanting both
    paid for tagging twice. Measured on 833-char passages: 17.9 ms per parse
    against 12.5 ms for every lookup in both families combined, so the second
    parse was the single largest line item in the whole measurement.
    """
    cw = cw if cw is not None else content_words(text, lang)
    out = norms(text, lang, cw=cw)
    out.update(count(text, lang, cw=cw))
    return out


def all_batch(texts, lang="en", batch_size=256):
    """`all_fields()` over many texts, parsing through `nlp.pipe`. -> iterator

    Batching amortises the tagger's matrix multiplies across documents. Measured
    on 300 corpus passages, one core:

        per-doc `nlp(text)`      0.0179 s   ->  56/s
        `nlp.pipe(batch_size=256)` 0.0116 s   ->  86/s
        `norms()` + `count()`    0.0483 s   ->  21/s   (two parses + lookups)

    So batch + shared parse is ~4x, and it is EXACT -- the same tagger on the
    same text, only grouped. A type-level lemma/POS table would be ~100x and is
    NOT used: on held-out corpus text it reproduces spaCy's content-word flag on
    only 91.2% of tokens (97.3% excluding the 6.3% out-of-vocabulary), and a
    misclassification rate that size could differ by arm, which would put an
    instrument artefact directly into the contrast this folder exists to make.
    """
    texts = list(texts)
    for t, doc in zip(texts, _nlp(lang).pipe(texts, batch_size=batch_size)):
        yield all_fields(doc, lang)


def _nest(kind, label):
    """Every level of a hierarchical label, outermost first. -> [str]

    RID is `thinking/process/category/subcategory` and USAS is a dotted code
    (`Q2.2` under `Q2` under `Q`), so both carry a hierarchy that a single
    chosen level throws away. Emitting all of them lets a caller pick by key
    prefix instead of by re-running with a different flag.
    """
    if kind == "rid":
        parts = [p for p in label.split("/") if p]
    elif kind == "usas":
        #: `Q2.2` -> Q, Q2, Q2.2. The letter is the top domain; each dot adds a
        #: level. Non-conforming codes fall through as a single level.
        m = re.match(r"^([A-Z])([0-9.]*)", label.upper())
        if not m:
            return [label]
        head, rest = m.group(1), m.group(2)
        parts, cur = [head], head
        for bit in [b for b in rest.split(".") if b]:
            cur = cur + ("." if cur != head else "") + bit
            parts.append(cur)
        return [p.replace(".", "_").lower() for p in parts]
    else:
        return [label]
    return ["_".join(parts[:i + 1]) for i in range(len(parts))]


def count(text, lang="en", cw=None):
    """SET sources, as rates. -> flat dict

        fields.count("she screamed and tore the bodies apart")
        {'n_content': 5, 'rid_aggression': 0.2, 'gi_hostile': 0.4, ...}

    RID (Martindale), General Inquirer, USAS and WordNet verb supersenses.

    ## RATES, AND WHAT THEY ARE OVER

    Each key is the SHARE OF CONTENT WORDS matching that category, so a rate of
    0.2 means one content word in five. **A word in several categories counts in
    all of them and the shares do not sum to 1** -- these are overlapping
    memberships, not a partition, and treating them as one would make every
    total meaningless.

    The denominator is content words, and `n_tokens` is returned beside it so a
    caller wanting a per-1000-words rate can renormalise without guessing what
    was divided by.

    ## EVERY LEVEL OF EVERY HIERARCHY, BY DEFAULT

    RID is four deep (`primordial / primary / need / orality`) and USAS is a
    dotted code (`Q2.2` under `Q2` under `Q`). Both are emitted at ALL levels,
    with the underscore showing the nesting:

        rid_primordial
        rid_primordial_primary
        rid_primordial_primary_need
        rid_primordial_primary_need_orality
        usas_q  usas_q2  usas_q2_2

    A caller selects a grain by key prefix rather than by re-running with a
    different flag, and the level Martindale's primary-versus-secondary-process
    claim turns on (`rid_primordial_primary` against `rid_conceptual_secondary`)
    is present without anyone having to know to ask for it.

    **THE LEVELS NEST, SO THEY MUST NEVER BE SUMMED ACROSS.** `rid_primordial`
    is the total of its own children, so adding it to `rid_primordial_primary`
    double-counts every word. Within one level the shares still do not sum to 1
    either, because memberships overlap. These are rates to be read, not parts
    of a partition.

    `*_coverage` is the share of content words found in that source AT ALL, which
    is the denominator any rate from it should be read against.
    """
    words, n_tok = cw if cw is not None else content_words(text, lang)
    out = {"n_tokens": n_tok, "n_content": len(words)}
    if not words:
        return out
    cat, cov = collections.Counter(), collections.Counter()
    for w, lem in words:
        for kind in _SET:
            got = _lookup(kind, w, lem)
            if not got:
                continue
            cov[kind] += 1
            if kind == "rid":
                #: the full path from the dictionary's own columns, so every
                #: level is available -- not a truncation of a category name.
                got = (rid(w, level="full") or rid(lem, level="full")) or got
            if kind == "usas":
                got = _lookup("usas_codes", w, lem) or got
            items = got if isinstance(got, (set, list, tuple)) else [got]
            for c in items:
                lab = str(c).replace(" ", "_").lower()
                for lvl in _nest(kind, lab if kind != "rid" else str(c)):
                    cat["%s_%s" % (kind, lvl)] += 1
    n = len(words)
    for src, c in cov.items():
        out[src + "_coverage"] = round(c / n, 4)
    for key, c in cat.items():
        out[key] = round(c / n, 4)
    return out
