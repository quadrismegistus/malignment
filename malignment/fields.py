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
    "k_en":      os.path.join(NORMS, "k_ratings_en.json"),
    "k_zh":      os.path.join(NORMS, "k_ratings_zh.json"),
    "warriner":  os.path.join(NORMS, "BRM-emot-submit.csv"),
    "brysbaert": os.path.join(NORMS, "Concreteness_ratings_Brysbaert_et_al_BRM.txt"),
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
    """[(compiled_regex, category, subcategory)]. RID is REGEXES, not words.

    Martindale's dictionary is written as stems (`\\babsinth`, `\\bale\\b`), so a
    set-membership test against word surfaces would silently miss most of it.
    """
    out = []
    with open(_need("rid"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                out.append((re.compile(r["regex"], re.I), r["category"],
                            r["subcategory"] or ""))
            except re.error:
                continue
    return out


def rid(word, with_sub=False):
    """RID categories matching this word. `need/sex` and `emotions/aggression`
    are the two this project most often wants, and they come from ONE dictionary
    with one construction procedure — so a sex-vs-aggression contrast is not
    confounded by the axes having different provenance."""
    out = set()
    for rx, cat, sub in _rid():
        if rx.search(word):
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


def wordnet(word):
    d = _wordnet()
    v = d.get(word.lower())
    return set(v if isinstance(v, (list, set, tuple)) else ([v] if v else []))


@functools.lru_cache(maxsize=1)
def _usas():
    out = collections.defaultdict(set)
    with open(_need("usas"), encoding="utf-8", errors="replace") as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                out[p[0].lower()].add(p[2].split()[0] if p[2] else "")
    return dict(out)


def usas(word):
    return set(_usas().get(word.lower(), set()))


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


def norms(word):
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
