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

SPACY_MODEL = "en_core_web_sm"

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


def tagger_id(nlp=None, model=SPACY_MODEL):
    """Identity of the tagger that produced a POS, for the cache key."""
    nlp = nlp or get_nlp(model)
    meta = getattr(nlp, "meta", {}) or {}
    return "%s-%s" % (meta.get("name") or model, meta.get("version") or "?")


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


def get_pos(words, prompt, nlp=None, stash=None):
    """Contextual POS for each word at the end of `prompt`. Returns {word: pos}.

    Only misses are tagged, so a warm stash costs no spaCy calls at all.
    """
    st = stash if stash is not None else _stash()
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
        for w in misses:
            doc = nlp(prompt + " " + w)
            pos = doc[-1].pos_ if len(doc) > 0 else "X"
            st[{"tagger": tid, "prompt": prompt, "word": w}] = pos
            out[w] = pos
    assert len(out) == len(set(words)), "get_pos returned short: %d of %d" % (
        len(out), len(set(words)))
    return out
