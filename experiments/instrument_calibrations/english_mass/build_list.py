#!/usr/bin/env python
"""build_list.py — the English wordlist, and the frequency floor that defines it.

    python build_list.py                 # build, assert, write TSV
    python build_list.py --load          # ... and load into ClickHouse

Emits `results/english_words.tsv`: `word \t core \t wide \t zipf`, lowercased,
one row per distinct form. Two lists, not one, **because the choice of list is
the whole design and a single list hides it**. If they disagree about a model
the number is a property of the wordlist; if they agree it is a property of the
model. `zipf` is wordfreq's log10 frequency per billion (0.0 where wordfreq has
no entry) and rides along because `run.py` needs it for `zipf_mean`.

## SOURCES — all local, none fetched

    web2      /usr/share/dict/web2      234,456  Webster's 2nd Unabridged (1934),
                                                 shipped with macOS. HEADWORDS
                                                 ONLY -- no plurals, no -ed/-ing,
                                                 no contractions.
    coca      lexicons/external/         87,637  COCA/BNC word database (BYU,
              worddb.byu.txt                     Davies). Corpus forms + lemmas.
    wordfreq  the `wordfreq` package    319,938  Speer et al., corpus-derived
                                                 from web/subtitles/news/books.
                                                 Widest modern coverage AND the
                                                 dirtiest tail.

    core = web2 | coca | {wordfreq : zipf >= 2.0}     ~ 300k
    wide = core | wordfreq                            ~ 507k

## THE FLOOR IS THE DESIGN, AND IT WAS SET FROM THE DATA

The first version of this file split on SOURCE — `web2|coca` against
`+wordfreq` — on the theory that wordfreq's tail was the contamination risk. Run
against the corpus, that split turned out to be dominated by something else
entirely: the highest-mass forms only wordfreq had were **`didn't` (mass 490),
`don't` (244), `couldn't` (136), `it's`, `can't`, `I'm`** — contractions, which
neither a 1934 dictionary nor an apostrophe-splitting corpus list carries. A
"strict English" list that rejects `didn't` is not strict, it is broken, and it
would have marked exactly the conversational registers as least English.

The contamination is real but it is not the SOURCE, it is the FREQUENCY. In
wordfreq's English list every junk entry sits at the floor -- `osipov`, `otok`,
`osomatsu` (Russian and Japanese proper nouns), `originaly` (typo), `ou're`
(fragment) all at **zipf 1.38** -- while every form worth having is at 3.0 or
above (`isn` 3.05, `didn` 3.29, `covid` 3.86, `email` 4.68, `didn't` 5.68).
A floor at **zipf 2.0** drops 224,180 entries and costs nothing real. That is
where `core` cuts, and it is a threshold read off the data rather than chosen.

## WHAT THIS MEASURES, AND THE ONE THING IT CANNOT

`p_english` is mass-weighted, so it is decided by high-frequency words and is
insensitive to the marginalia the two lists argue about. It separates **English
from not-English**. It does NOT separate fluent English from degenerate English:
a model emitting `the the the the` scores ~1.0. It is a FLOOR on fluency, never
a ceiling. `run.py`'s `zipf_mean` and `top1` columns are what see that
difference, and they are reported beside it for that reason.
"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RESULTS = os.path.join(HERE, "results")
OUT = os.path.join(RESULTS, "english_words.tsv")
WEB2 = "/usr/share/dict/web2"
COCA = os.path.join(REPO, "lexicons", "external", "worddb.byu.txt")

ZIPF_FLOOR = 2.0

#: Forms carrying real mass that no source list holds. Every entry must be here
#: because it appeared in `run.py --rejects`, with its mass. Adding a word by
#: taste rather than by a reject listing turns a wordlist into a fitted
#: parameter. Empty is the correct state until the rejects say otherwise.
PATCH = {}


def _web2():
    if not os.path.exists(WEB2):
        raise SystemExit("no %s -- the macOS system dictionary is missing" % WEB2)
    return {l.strip().lower() for l in open(WEB2) if l.strip()}


def _coca():
    out = set()
    with open(COCA) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            for k in ("word", "lemma"):
                v = (r.get(k) or "").strip().lower()
                if v:
                    out.add(v)
    return out


def _wordfreq():
    import wordfreq
    full = [w.lower() for w in wordfreq.top_n_list("en", 400_000)]
    above = {w for w in full if wordfreq.zipf_frequency(w, "en") >= ZIPF_FLOOR}
    return above, set(full)


def build():
    web2, coca = _web2(), _coca()
    wf_above, wf_all = _wordfreq()
    core = web2 | coca | wf_above | set(PATCH)
    wide = core | wf_all
    print("  web2            %8d" % len(web2))
    print("  coca            %8d" % len(coca))
    print("  wordfreq >=%.1f  %8d  (%d new to core)"
          % (ZIPF_FLOOR, len(wf_above), len(wf_above - web2 - coca)))
    print("  wordfreq  all   %8d  (%d below the floor, kept only by `wide`)"
          % (len(wf_all), len(wf_all - wf_above)))
    print("  PATCH           %8d" % len(PATCH))
    print("  core            %8d" % len(core))
    print("  wide            %8d" % len(wide))

    #: A list that cannot spell `didn't` or `running` is broken in the way that
    #: matters, because those forms carry mass. Asserted, not eyeballed --
    #: the source-split version of this file failed exactly here.
    must = ["running", "ran", "cats", "isn", "isn't", "gonna", "ok", "okay",
            "laughed", "biggest", "quickly", "she", "the", "wasn", "didn",
            "didn't", "don't", "it's", "i'm", "someone", "email"]
    missing = [w for w in must if w not in core]
    if missing:
        raise SystemExit("core list misses common forms: %s" % missing)

    import wordfreq
    os.makedirs(RESULTS, exist_ok=True)
    with open(OUT, "w") as f:
        for w in sorted(wide):
            f.write("%s\t%d\t1\t%.4f\n"
                    % (w, 1 if w in core else 0, wordfreq.zipf_frequency(w, "en")))
    print("  wrote %s (%d rows)" % (OUT, len(wide)))


def load():
    sys.path.insert(0, REPO)
    from malignment import ch
    ch.execute("DROP TABLE IF EXISTS english_words")
    ch.execute("""CREATE TABLE english_words (
        word String, core UInt8, wide UInt8, zipf Float32
    ) ENGINE = MergeTree ORDER BY word""")
    ch._run("INSERT INTO english_words FORMAT TSV", stdin=open(OUT).read())
    print("  loaded english_words: %d rows, %d core"
          % (ch.scalar("SELECT count() FROM english_words"),
             ch.scalar("SELECT countIf(core) FROM english_words")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--load", action="store_true")
    a = ap.parse_args()
    build()
    if a.load:
        load()
    return 0


if __name__ == "__main__":
    sys.exit(main())
