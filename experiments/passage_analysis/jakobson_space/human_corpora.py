"""Human text for the anchor, at the model passages' own length. Cleans OCR first.

    python experiments/passage_analysis/jakobson_space/human_corpora.py --per 500

The space is currently model-relative: `alignment_smooths.md` establishes that
aligned prose is smoother than base prose and CANNOT say whether either is smooth
compared to human writing. That is what F16 was for and what this rebuilds.

## Six text types, four inherited and two new

    arxiv abstracts   500   median 172 words   formulaic expository
    dreams            500          136         personal narrative
    waking (hippo)    500          231         personal narrative, register control
    C20 fiction       500          508         literary narrative
    philosophy        new                      DISCURSIVE ARGUMENT
    literary crit     new                      DISCURSIVE ARGUMENT

The last two fill a real gap. The inherited four are expository-formulaic or
narrative; none of them is argument that hedges, qualifies and concedes -- which is
the register aligned models actually produce when they explain. If aligned prose is
converging on something, criticism and philosophy are the plausible target, and the
space had no way to test it.

Source: `~/backup/ordinary-style-philosophy`, 90,403 JSTOR articles keyed by
`data/metadata.csv` (Philosophy 32,783 / Literature 25,343 / Other 32,277,
1887-2021, median 1981). Journals: Synthese, J. Philosophy, PMLA, Modern Language
Review.

## LENGTH IS TAKEN, NOT IMPOSED, EXCEPT WHERE IT HAS TO BE

Model passages sit at median 186 words (p90 213), and three of the four inherited
corpora are ALREADY there -- 90% of abstracts and 95% of dreams fall in 100-260
words. They are used unchanged. Longer abstracts do not exist: the sample maxes at
286 words and the genre is capped, so there is nothing to fetch.

C20 fiction is the exception at median 508, and is carried at its natural length
with a truncated-to-200 copy beside it as a sensitivity, not as the primary.

Articles are book-length, so a window IS imposed there -- ~200 words from the
MIDDLE of each article, at sentence boundaries. The middle avoids title, abstract,
acknowledgements and references, and for expository prose a mid-argument window is
a far less damaging cut than it would be for a dream report.

## The OCR cleaning, and why it is not optional

Raw text carries three artifacts that would each inflate surprisal and make human
prose look artificially rough against model output:

    "legal and political theor- ists"     line-break hyphenation
    "the right to vote,1 the right"       inline footnote markers
    "The Autonomy Defense* Susan J."      front matter and starred notes

De-hyphenation is the load-bearing one: `theor- ists` is two nonsense tokens to any
scorer. Footnote digits are stripped only where they follow punctuation directly
attached to a word, so genuine numerals survive.
"""

import argparse, csv, glob, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.expanduser("~/backup/ordinary-style-philosophy")
META = os.path.join(ROOT, "data", "metadata.csv")
TXT = os.path.join(ROOT, "data", "raw", "txt")
ARCHIVE = "/Users/rj416/github/malign-logits/data"
OUT = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                  os.path.expanduser("~/malignment-data")),
                   "jakobson_space", "human_passages.jsonl")

HYPHEN = re.compile(r"(\w)-\s+(\w)")
#: `(?<!\d)` because without it this ate thousands separators: `some 1,500 people`
#: became `some 1, people`, and `cost $3,400` became `cost $3,`. The guard requires
#: the character before the punctuation to be a non-digit, which a footnote marker
#: always has (`vote,1`) and a formatted number never does.
FOOTNOTE = re.compile(r"(?<!\d)([.,;:!?])\d{1,3}(?=\s|$)")
WS = re.compile(r"\s+")
ORPHAN = re.compile(r"\s\.\s")
#: A footnote block is not prose. Older journals print notes at page bottoms and
#: the OCR interleaves them into the body, so a mid-article window can land in
#: pure bibliography: "(London, 1981), pp. 25-26; Billington (n. 7 above), p. 71."
#: Measured before fixing: 9.4% of literary criticism windows, 2.6% of philosophy,
#: 0.0% of every narrative corpus.
CITE = re.compile(r"\b(pp?\.|Ibid|ed\.|vol\.|chap\.|trans\.|cf\.|op\. cit|no\.)\s", re.I)
#: ENGLISH PROSE, NOT QUOTED FOREIGN PROSE. Literature journals quote French,
#: German and Russian at length, and OCR renders Cyrillic as Latin lookalikes --
#: "JsBe npoTHBOnoJIoKHeHHbIe HaeH He MOFyT" is Pushkin in PMLA. Those would score
#: enormous surprisal and are not English. Measured before fixing: 5.0% of
#: philosophy and 4.0% of literary criticism windows fall below a 0.15
#: function-word share, against 0.0% of every narrative corpus. The floor is
#: arxiv's own 1st percentile, 0.18, so technical English survives.
STOP = set("the of and to in a is that it for as with was on by an be are this or "
           "from at not but which have has had were their its his her he she they "
           "we you i".split())
ENGLISH_MIN = 0.18
#: `able` and `ally` were here and are ORDINARY ENGLISH WORDS, so the rejoin fired
#: on ordinary prose: `was able` -> `wasable`, `were able` -> `wereable`,
#: `a close ally` -> `a closeally`, and `not able` -> `notable`, which is a
#: different word. Every entry here must be a fragment that never stands alone.
SUFFIX = ("tion", "tions", "ing", "ment", "ments", "ance", "ence", "ity", "ities",
          "ness", "ible", "ical", "ized", "ised", "sion")


def _rejoin(t):
    """Repair a hyphenation whose hyphen the OCR dropped: `conversa tion`.

    HYPHEN only catches splits that kept their dash. This catches the ones that
    did not, conservatively: a lowercase fragment of 3+ chars followed by a known
    suffix fragment, joined only when the fragment is not itself a word. Nothing
    is joined across punctuation or a capital.
    """
    out, toks = [], t.split(" ")
    i = 0
    while i < len(toks):
        a = toks[i]
        b = toks[i + 1] if i + 1 < len(toks) else ""
        if (b in SUFFIX and a and a[-1].isalpha() and a[:1].islower()
                and len(a) >= 3 and a.isalpha()):
            out.append(a + b); i += 2; continue
        out.append(a); i += 1
    return " ".join(out)


def english_share(t):
    w = [x.strip(".,;:!?\"'()[]").lower() for x in t.split()]
    w = [x for x in w if x]
    return sum(1 for x in w if x in STOP) / max(len(w), 1)


def is_citation_block(t):
    w = max(len(t.split()) / 100.0, 1.0)
    ch = [c for c in t if not c.isspace()]
    digits = sum(c.isdigit() for c in ch) / max(len(ch), 1)
    return (len(CITE.findall(t)) / w) >= 2.0 or digits >= 0.04


def clean(t):
    t = HYPHEN.sub(r"\1\2", str(t))       # theor- ists -> theorists
    t = FOOTNOTE.sub(r"\1", t)            # vote,1 -> vote,
    t = WS.sub(" ", t).strip()
    return _rejoin(t)                     # conversa tion -> conversation


def window(text, target=200):
    """~target words from the MIDDLE, at REAL sentence boundaries. -> str or None

    A regex split on `[.!?]\s+` is fooled by OCR'd citations -- `Vol. 12`, `ed. by`,
    `p. 44` -- so 13-16% of academic windows began mid-sentence against 0.6-5% for
    narrative prose. Measured, then fixed: a window must START at something that
    looks like a sentence (capital or quote) and must not open on an orphan period.
    Windows that fail are DROPPED and another article is drawn, which is affordable
    at 32,783 philosophy and 25,343 literature articles.
    """
    sents = re.split(r"(?<=[.!?])\s+", text)
    if len(sents) < 8:
        return None
    lo = int(len(sents) * 0.30)
    for start in range(lo, min(lo + 12, len(sents) - 4)):
        first = sents[start].strip()
        if not first or not re.match(r'["\u201c(]?[A-Z]', first):
            continue                      # not a real sentence start
        out, n = [], 0
        for s in sents[start:]:
            out.append(s); n += len(s.split())
            if n >= target:
                break
        w = " ".join(out)
        if not (100 <= n <= 400):
            continue
        if ORPHAN.search(w) or is_citation_block(w):
            continue                      # broken boundary, or a footnote block
        if english_share(w) < ENGLISH_MIN:
            continue                      # quoted French/German/Russian, or OCR
        return w
    return None


def articles(kind, per, seed):
    rows = [r for r in csv.DictReader(open(META, encoding="utf-8", errors="replace"))
            if r["id"].split("/")[0] == kind]
    rng = random.Random(seed); rng.shuffle(rows)
    out = []
    for r in rows:
        if len(out) >= per:
            break
        p = os.path.join(TXT, r["id"] + ".txt")
        if not os.path.exists(p):
            continue
        try:
            raw = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        w = window(clean(raw))
        if w:
            out.append(dict(text=w, corpus=kind, title=r.get("title"),
                            author=r.get("author"), year=r.get("year"),
                            journal=r.get("journal"), source_id=r["id"]))
    return out


def inherited():
    out = []
    def add(rows, name, col):
        for r in rows:
            t = clean(r.get(col) or "")
            if len(t.split()) >= 60:
                out.append(dict(text=t, corpus=name))
    try:
        add(list(csv.DictReader(open(os.path.join(ARCHIVE, "arxiv_abstracts_500.csv"),
            encoding="utf-8", errors="replace"))), "arxiv_abstracts", "text")
        add(list(csv.DictReader(open(os.path.join(ARCHIVE, "dreams_sample_500_cleaned.csv"),
            encoding="utf-8", errors="replace"))), "dreams", "text")
        add(list(csv.DictReader(open(os.path.join(ARCHIVE, "hippocorpus_sample_500.csv"),
            encoding="utf-8", errors="replace"))), "waking_narrative", "story")
    except FileNotFoundError as e:
        print("  missing inherited corpus: %s" % e)
    p = os.path.join(ARCHIVE, "markmark_c20_narration_500.jsonl")
    if os.path.exists(p):
        for line in open(p):
            d = json.loads(line)
            t = clean(d.get("text") or "")
            if len(t.split()) >= 60:
                out.append(dict(text=t, corpus="c20_fiction", author=d.get("author"),
                                title=d.get("title"), year=d.get("year")))
                #: the truncated copy is a SENSITIVITY, carried beside the natural
                #: one and never instead of it -- fiction is the only inherited
                #: corpus outside the model range (median 508 against 186)
                w = window(t, 200)
                if w:
                    out.append(dict(text=w, corpus="c20_fiction_trunc200",
                                    author=d.get("author"), title=d.get("title")))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20260820)
    a = ap.parse_args(argv)
    import numpy as np
    rows = inherited()
    for kind, name in (("phil", "philosophy"), ("lit", "literary_criticism")):
        got = articles(kind, a.per, a.seed)
        for g in got:
            g["corpus"] = name
        rows += got
        print("  %-20s %d passages" % (name, len(got)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print("\n  %-22s %6s %8s %8s %8s" % ("corpus", "n", "p10", "median", "p90"))
    import collections
    by = collections.defaultdict(list)
    for r in rows:
        by[r["corpus"]].append(len(r["text"].split()))
    for k in sorted(by):
        v = np.array(by[k])
        print("  %-22s %6d %8d %8d %8d"
              % (k, len(v), np.percentile(v, 10), np.median(v), np.percentile(v, 90)))
    print("\n-> %s  (%d passages)" % (OUT, len(rows)))


if __name__ == "__main__":
    main()
