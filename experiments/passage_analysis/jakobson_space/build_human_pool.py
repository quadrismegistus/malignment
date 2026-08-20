"""Assemble the six human corpora into one JSONL for the normalisation pass.

    python experiments/passage_analysis/jakobson_space/build_human_pool.py --per 600

Emits `$MALIGNMENT_DATA/jakobson_space/human_pool_raw.jsonl`, which
`normalise_pool.py` then cleans. Selection and windowing helpers come from
`human_corpora.py`, which stays the module for those; this file supersedes its
`main()` and the 500-per-type design behind it.

## RH'S RULING, 2026-08-20, AND WHAT IT OVERTURNS

    "completely and totally normalise orthography to clean text: no text junk
     AND no typos. Otherwise we are not measuring the underlying semantics and
     syntax of these text types but just surface level features of how quickly
     someone typed out their dream."

The previous design kept human orthography and stripped only archive artifacts.
That was incoherent in practice: dreams had ALREADY been part-normalised by an
earlier pass (apostrophes and casing fixed on 34 of 500 rows, 1.214% of bytes)
while `missee`, `amd` and `acar` were left in, so the corpus obeyed no statable
rule. And the confound RH names is real and asymmetric: dreams were typed into a
web form in one pass, philosophy was typeset and proofread by a publisher. That
is a difference in PRODUCTION CONTEXT, not in genre, and it lands directly on the
axis, because BLT is byte-level and `thats` against `that's` is a byte difference
and nothing else.

So every corpus is normalised to the same target state, and the pass is uniform.

**Dreams are therefore drawn from RAW `dreams.csv`, never from
`dreams_sample_500_cleaned.csv`**, which would be normalised twice and by two
different rules.

## LENGTH IS IMPOSED, MID-SENTENCE, BECAUSE THE MODELS ARE CUT OFF MID-SENTENCE

Measured on the 357,236 English model passages: only **17.7%** end in terminal
punctuation, and 26.0% carry `finish_reason='length'` outright. A model passage
is a 256-token slice that stops wherever the cap falls. So human passages are cut
at a WORD COUNT and not at a sentence boundary -- a sentence-boundary cut would
give human text a completeness the model text does not have, on a measure
sensitive to exactly that.

Target is 193 words, the median of model passages that ran to the 256-token cap.

## THE ORDER: WINDOW WIDE, CLEAN, THEN CUT

Sources are windowed at ~210 words, cleaned, and only then truncated to 193.
Truncation last is not a detail -- it is what makes the output robust to the
cleaner rather than dependent on its obedience:

  * normalisation legitimately changes word count (`conversa tion` -> one word,
    `alot` -> two), so cutting first would not give 193 words out;
  * a passage ending mid-sentence invites a model to COMPLETE it, and completion
    past word 193 is discarded by construction instead of by instruction.

## Pool depth at >=193 words, measured

    dreams (raw dreams.csv)   2,840    of 30,799
    waking (hippoCorpusV2)    5,372    of  6,854
    c20 fiction                 476    of    500   median 508 -> two chunks each
    philosophy               32,783 articles, windowed mid-article
    literary criticism       25,343 articles, windowed mid-article
    arxiv abstracts             179    of    500   -> `fetch_arxiv.py` supplies more

Fiction is the one corpus that cannot reach 600 in distinct texts. It takes a
second, non-overlapping chunk from as many texts as the shortfall needs and
records `chunk_idx`, so the non-independence is visible to anything downstream
rather than hidden in the count.
"""

import argparse, collections, csv, hashlib, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from human_corpora import english_share, is_citation_block, ORPHAN  # noqa: E402

#: NO DETERMINISTIC PRE-PASS. RH's instruction, 2026-08-20, and the reason is in
#: the two bugs that prompted it. `human_corpora.clean` repaired OCR splits whose
#: hyphen was lost, and without context it joined ordinary prose: `was able` ->
#: `wasable`, `not able` -> `notable`, a different word. Its footnote rule ate
#: thousands separators: `some 1,500 people` -> `some 1, people`.
#:
#: Both are the same failure. Every repair worth making here needs the sentence in
#: front of it, and a regex does not have one. Splitting the work between a
#: deterministic pass and a contextual one also means two rules operating on the
#: text, which is precisely the incoherence that made the old dreams corpus
#: unstatable. One pass, one rule, applied with context.
#:
#: So text reaches the cleaner EXACTLY as the source holds it, whitespace and all.
#: Nothing below modifies a byte; it only SELECTS which bytes to send.

WORDS = re.compile(r"\S+")
SENT = re.compile(r"(?<=[.!?])\s+")


def head(text, n):
    """First n words as a RAW SLICE, preserving original whitespace. -> str

    `" ".join(text.split()[:n])` would be shorter and would silently normalise
    every newline and double space in the corpus -- a deterministic whitespace
    pass wearing the costume of an extraction. Slicing at the offset where the
    nth word ends preserves the source exactly.
    """
    m = list(WORDS.finditer(str(text)))
    if not m:
        return ""
    return str(text)[: m[min(n, len(m)) - 1].end()]


def window(text, target):
    """~target words from mid-article, at a real sentence start. -> str or None

    Same selection logic as `human_corpora.window` and the same quality
    predicates, but it returns a SLICE of the source rather than sentences
    rejoined with single spaces.
    """
    text = str(text)
    bounds = [0] + [m.end() for m in SENT.finditer(text)]
    if len(bounds) < 8:
        return None
    lo = int(len(bounds) * 0.30)
    for si in range(lo, min(lo + 12, len(bounds) - 4)):
        start = bounds[si]
        first = text[start:start + 60].lstrip()
        if not first or not re.match(r'["“(]?[A-Z]', first):
            continue                                  # not a real sentence start
        w = head(text[start:], target)
        n = len(w.split())
        if not (100 <= n <= 400):
            continue
        if ORPHAN.search(w) or is_citation_block(w):
            continue                                  # broken boundary, footnotes
        if english_share(w) < ENGLISH_MIN_LOCAL:
            continue                                  # quoted French/German/Russian
        return w
    return None


ENGLISH_MIN_LOCAL = 0.18

ARCHIVE = "/Users/rj416/github/malign-logits/data"
KAGGLE = os.path.expanduser(
    "~/.cache/kagglehub/datasets/saurabhshahane/hippocorpus/versions/2/hippoCorpusV2.csv")
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
OUT = os.path.join(DATA, "jakobson_space", "human_pool_raw.jsonl")
ARXIV_RAW = os.path.join(DATA, "jakobson_space", "arxiv_raw.jsonl")

TARGET = 193          #: model median at the 256-token cap
SEND = 210            #: buffer given to the cleaner, cut back to TARGET after
MIN_SRC = 193         #: a source shorter than the target can never fill it

csv.field_size_limit(10 ** 7)


def pid(corpus, text):
    return "%s-%s" % (corpus, hashlib.sha256(text.encode()).hexdigest()[:12])


def _rows_from_csv(path, col, corpus, rng, per, extra=()):
    rows = list(csv.DictReader(open(path, encoding="utf-8", errors="replace")))
    cand = [r for r in rows if len((r.get(col) or "").split()) >= MIN_SRC]
    rng.shuffle(cand)
    out = []
    for r in cand[:per]:
        t = head(r[col], SEND)
        d = dict(text=t, corpus=corpus, chunk_idx=0)
        for k in extra:
            if r.get(k):
                d[k] = r[k]
        out.append(d)
    return out, len(cand)


def dreams(rng, per):
    #: RAW dreams.csv. dreams_sample_500_cleaned.csv is already part-normalised
    #: and would be cleaned twice under two different rules.
    return _rows_from_csv(os.path.join(ARCHIVE, "dreams.csv"),
                          "dreams_text", "dreams", rng, per)


def waking(rng, per):
    #: the full Kaggle corpus, not hippocorpus_sample_500.csv, which drops memType
    return _rows_from_csv(KAGGLE, "story", "waking_narrative", rng, per,
                          extra=("memType", "AssignmentId"))


def fiction(rng, per):
    src = [json.loads(l) for l in
           open(os.path.join(ARCHIVE, "markmark_c20_narration_500.jsonl"))]
    long_enough = [d for d in src if len(d["text"].split()) >= MIN_SRC]
    rng.shuffle(long_enough)
    out = []
    for d in long_enough[:per]:
        out.append(dict(text=head(d["text"], SEND), corpus="c20_fiction",
                        chunk_idx=0, author=d.get("author"), title=d.get("title"),
                        year=d.get("year")))
    #: SHORTFALL -> a second, non-overlapping chunk. Recorded, never hidden.
    short = per - len(out)
    if short > 0:
        second = [d for d in long_enough if len(d["text"].split()) >= SEND * 2 + 40]
        rng.shuffle(second)
        for d in second[:short]:
            #: raw slice, offsets not token rejoin, so whitespace survives
            m = list(WORDS.finditer(d["text"]))
            w = d["text"][m[SEND + 40].start(): m[min(SEND * 2 + 40, len(m)) - 1].end()]
            out.append(dict(text=w, corpus="c20_fiction", chunk_idx=1,
                            author=d.get("author"), title=d.get("title"),
                            year=d.get("year")))
    return out, len(long_enough)


def abstracts(rng, per):
    """arXiv, preferring the fresh multi-category fetch over the archived slice."""
    cand = []
    if os.path.exists(ARXIV_RAW):
        for line in open(ARXIV_RAW):
            d = json.loads(line)
            a = (d.get("abstract") or "").strip()
            if len(a.split()) >= MIN_SRC:
                cand.append(dict(text=a, category=d.get("category"),
                                 arxiv_id=d.get("arxiv_id"), year=(d.get("published") or "")[:4]))
    n_fresh = len(cand)
    if len(cand) < per:
        #: fall back to the archived 500 only to top up, and say so
        p = os.path.join(ARCHIVE, "arxiv_abstracts_500.csv")
        if os.path.exists(p):
            for r in csv.DictReader(open(p, encoding="utf-8", errors="replace")):
                if len((r.get("text") or "").split()) >= MIN_SRC:
                    cand.append(dict(text=r["text"], category="ARCHIVED"))
    rng.shuffle(cand)
    out = []
    for r in cand[:per]:
        d = dict(text=head(r["text"], SEND), corpus="arxiv_abstracts", chunk_idx=0)
        for k in ("category", "arxiv_id", "year"):
            if r.get(k):
                d[k] = r[k]
        out.append(d)
    return out, n_fresh


def academic(kind, name, rng, per):
    """Mid-article windows. Draws until `per` SURVIVE the quality filters."""
    from human_corpora import META, TXT
    rows = [r for r in csv.DictReader(open(META, encoding="utf-8", errors="replace"))
            if r["id"].split("/")[0] == kind]
    rng.shuffle(rows)
    out, tried = [], 0
    for r in rows:
        if len(out) >= per:
            break
        tried += 1
        p = os.path.join(TXT, r["id"] + ".txt")
        if not os.path.exists(p):
            continue
        try:
            raw = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        w = window(raw, SEND + 20)
        if not w or len(w.split()) < MIN_SRC:
            continue
        out.append(dict(text=head(w, SEND), corpus=name, chunk_idx=0,
                        title=r.get("title"), author=r.get("author"),
                        year=r.get("year"), journal=r.get("journal"),
                        source_id=r["id"]))
    return out, tried


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=600)
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)

    rows, avail = [], {}
    for name, fn in (("dreams", dreams), ("waking_narrative", waking),
                     ("c20_fiction", fiction), ("arxiv_abstracts", abstracts)):
        got, n = fn(rng, a.per)
        rows += got
        avail[name] = n
        print("  %-22s %4d selected  (%d available at >=%d words)"
              % (name, len(got), n, MIN_SRC))
    for kind, name in (("phil", "philosophy"), ("lit", "literary_criticism")):
        got, tried = academic(kind, name, rng, a.per)
        rows += got
        avail[name] = tried
        print("  %-22s %4d selected  (%d articles examined)" % (name, len(got), tried))

    for r in rows:
        r["id"] = pid(r["corpus"], r["text"])
        r["n_words_raw"] = len(r["text"].split())

    #: an id collision means two identical passages, which is a real duplicate
    seen = collections.Counter(r["id"] for r in rows)
    dup = [k for k, v in seen.items() if v > 1]
    if dup:
        print("\n  dropping %d duplicate passages" % len(dup))
        keep, used = [], set()
        for r in rows:
            if r["id"] in used:
                continue
            used.add(r["id"]); keep.append(r)
        rows = keep

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    print("\n  %-22s %6s %8s %8s %8s" % ("corpus", "n", "min", "median", "max"))
    by = collections.defaultdict(list)
    for r in rows:
        by[r["corpus"]].append(r["n_words_raw"])
    for k in sorted(by):
        v = sorted(by[k])
        print("  %-22s %6d %8d %8d %8d" % (k, len(v), v[0], v[len(v) // 2], v[-1]))
    short = [k for k in by if len(by[k]) < a.per]
    if short:
        print("\n  BELOW QUOTA: %s" % ", ".join("%s=%d" % (k, len(by[k])) for k in short))
    print("\n-> %s  (%d passages)" % (a.out, len(rows)))


if __name__ == "__main__":
    main()
