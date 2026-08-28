"""Contextual part-of-speech for a word AT A SLOT, cached per (tagger, prompt, word).

    from malignment.pos import get_pos
    pos = get_pos(["glasses", "dress", "slowly"], "She slowly took off her")
    # {'glasses': 'NOUN', 'dress': 'NOUN', 'slowly': 'ADV'}

Ported 2026-08-19 from `malign_logits/taxonomy.py:get_pos` (the READ-ONLY
archive). The function is carried over; the archive's 190MB `pos_context` stash
is NOT -- this one fills as it goes.

## WHY CONTEXTUAL, AND NOT A LOOKUP

An out-of-context tagger returns the most frequent reading of a word FORM. At a
site like "She began to ___" that labels `fall break kiss punch strike` as NOUNS.
The archive measured its own out-of-context lookup (`fields.py:_byu()`) at
**41.2% verbs inside its "noun" band**. This function exists so nothing has to
reach for that.

The text tagged is `prompt + " " + word` and the tag taken is the LAST token's --
the position the model was predicting.

## THIS FUNCTION CANNOT RETURN SHORT

`len(result) == len(words)`, always. A miss is TAGGED, never dropped.

The archive records what the alternative cost, on 2026-08-13: a TSV-backed POS
cache built from a duplicated table was COMPLETE for its own selection and SHORT
for the corrected one by 12,850 pairs, so a re-run measuring a dedup fix silently
excluded exactly the words the fix had promoted. **A cache miss and an ineligible
word look identical from inside**, so the only safe contract is one that never
returns fewer rows than it was asked for.

Consumers reading the stash directly do not get that guarantee. Go through this
function.

## THE TAGGER IS PART OF THE KEY

A tagger difference is a POS difference, so it is keyed rather than assumed --
the same refusal `cache.py` makes about dtype. Without it a stash filled by
`en_core_web_sm` would silently answer for `en_core_web_trf`.
"""

import os
import re

SPACY_MODEL = "en_core_web_sm"
#: only the two languages this corpus contains. A third would need its own
#: entry AND a detector that can tell it apart; `detect_lang` below is a
#: two-way test, not a general one, and says so.
LANG_MODEL = {"en": "en_core_web_sm", "zh": "zh_core_web_sm"}
#: the same range `jakobson_space/population.py` uses for `cjk_share`.
_CJK = re.compile(r"[\u3400-\u9fff]")
_LAT = re.compile(r"[A-Za-z]")
#: spaCy does not put spaces between Chinese tokens, and inserting one makes the
#: tagger see a token boundary the language does not have.
_JOIN = {"en": " ", "zh": ""}

#: Repo-level, shared: displacement_axis, displacement_taxonomy and slot_ratings
#: all want tags for the same (prompt, word) pairs. `data/` is gitignored
#: wholesale, so this never enters the public repo.
STASH_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "pos_context")

_NLP = {}
_STASH = {}


def get_nlp(model=SPACY_MODEL):
    """The shared spaCy pipeline, loaded once per process per model name."""
    if model not in _NLP:
        import spacy
        _NLP[model] = spacy.load(model)
    return _NLP[model]


def detect_lang(text):
    """-> 'zh' or 'en'. A TWO-WAY test, not language identification.

    This corpus is English and Chinese and nothing else, so the presence of CJK
    is sufficient and no dependency is needed. `langdetect` would answer a
    question nobody is asking and would misfire on the short, truncated stems
    this is called with -- `She slowly took off her` is not a sentence.

    Compared rather than thresholded: a zh prompt can carry Latin characters
    (`女性教师年薪为$`) and an en prompt can carry none, so the test is which
    script has MORE characters, which is stable at these lengths.
    """
    t = text or ""
    return "zh" if len(_CJK.findall(t)) > len(_LAT.findall(t)) else "en"


def tagger_id(nlp=None, model=SPACY_MODEL):
    """Identity of the tagger that produced a POS, for the cache key.

    **THE LANGUAGE IS IN THE KEY FOR EVERYTHING EXCEPT ENGLISH, AND THAT
    ASYMMETRY IS DELIBERATE.** spaCy's `meta["name"]` drops the language prefix,
    so `en_core_web_sm` and `zh_core_web_sm` BOTH report `core_web_sm` and both
    resolved to `core_web_sm-3.8.0`. The cache key is (tagger, prompt, word), so
    an English tag and a Chinese tag for one pair collided and whichever ran
    first answered for both -- silently, since a tag is never absurd on its face.

    Prefixing every id with its language would fix it and invalidate the whole
    existing stash, which holds 2,751,990 pairs from `contextual_norms/
    pos_pass.py`. English keeps its historical form and every other language
    gets a prefix, so old English entries stay readable and no non-English tag
    can ever land on one.
    """
    nlp = nlp or get_nlp(model)
    meta = getattr(nlp, "meta", {}) or {}
    name = "%s-%s" % (meta.get("name") or model, meta.get("version") or "?")
    lang = meta.get("lang")
    return name if (not lang or lang == "en") else "%s-%s" % (lang, name)


def _stash():
    """The jsonl store, with the resolution guard.

    `root_dir` is ABSOLUTE by construction: a bare name silently resolves to
    `~/.cache/hashstash/`, which is the trap CLAUDE.md warns about for this
    library. And hashstash can land somewhere other than the engine you asked
    for (an lz4 fallback did exactly that in `displacement_taxonomy/run.py`),
    so the engine is verified from hashstash's own answer rather than assumed.
    """
    if "st" not in _STASH:
        from hashstash import HashStash
        os.makedirs(STASH_DIR, exist_ok=True)
        st = HashStash(root_dir=STASH_DIR, engine="jsonl", flat=True)
        got = os.path.basename(getattr(st, "path_dirname", "") or "")
        if "jsonl" not in got:
            raise RuntimeError(
                "pos: stash resolved to %r, expected a jsonl store. Records are "
                "NOT going where you think." % (got or "?"))
        _STASH["st"] = st
    return _STASH["st"]


def get_pos(words, prompt, nlp=None, stash=None, lang=None):
    """Contextual POS for each word at the end of `prompt`. Returns {word: pos}.

    Only misses are tagged, so a warm stash costs no spaCy calls at all.

    `lang` selects the pipeline: `None` DETECTS it from the prompt, which is
    right for a mixed corpus and is why this is the default. Pass it explicitly
    to override. An explicit `nlp` wins over both -- a caller who built the
    pipeline knows what it is.
    """
    st = stash if stash is not None else _stash()
    if nlp is None:
        lang = lang or detect_lang(prompt)
        nlp = get_nlp(LANG_MODEL.get(lang, SPACY_MODEL))
    tid = tagger_id(nlp)

    out, misses = {}, []
    for w in words:
        hit = st.get({"tagger": tid, "prompt": prompt, "word": w})
        if hit is None:
            misses.append(w)
        else:
            out[w] = hit
    if misses:
        nlp = nlp or get_nlp()
        join = _JOIN.get((getattr(nlp, "meta", {}) or {}).get("lang"), " ")
        for w in misses:
            doc = nlp(prompt + join + w)
            pos = doc[-1].pos_ if len(doc) > 0 else "X"
            st[{"tagger": tid, "prompt": prompt, "word": w}] = pos
            out[w] = pos
    assert len(out) == len(set(words)), "get_pos returned short: %d of %d" % (
        len(out), len(set(words)))
    return out
