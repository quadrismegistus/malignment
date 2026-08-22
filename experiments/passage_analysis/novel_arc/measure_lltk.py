"""Score an lltk corpus's passages on three instruments, at the LLM grain.

    python .../measure_lltk.py --corpus chadwyck --workers 8
    python .../measure_lltk.py --corpus chicago  --workers 8

Runs in the LLTK venv (`~/github/lltk/.venv/bin/python`), which is the only one
holding lltk, spacy and pyarrow at once; `malignment` is added to sys.path and
RH's norms are read from a parquet export, so no cross-process plumbing.

## WHICH CORPORA, AND WHY EACH

`chadwyck` (1,333 dated texts, 1593-1954) is the spine: it is the only corpus in
`lltk.passages` spanning the whole arc. It thins badly after 1875 -- 66 texts in
1875-99, then 2, 78, 100, 87 per quarter-century -- so it cannot carry the C20.

`chicago` (9,089 texts, ALL Fiction, ALL English, 1880-2000) covers exactly that
gap, and densely: 113/190/372/423/472/656/679/487/493/834/1554/2465/351 texts by
decade from the 1880s. It has NO rows in `lltk.passages`, so it is chunked from
`txt` on the fly like everything else here -- the passage table is a convenience,
not the source.

## WHY chadwyck IS THE SPINE

`lltk.passages` covers 1450-2011, but corpus identity is COLLINEAR with period:
litlab, ecco and earlyprint all stop at 1800, chadwyck carries 1825-75 almost
alone, markmark carries everything after 1875. A trend crossing 1800 or 1875 in
the pooled table is indistinguishable from a corpus substitution. chadwyck is
the only corpus spanning the arc (1593-1954, present in every quarter-century),
which makes it the within-corpus control and the only defensible single series.

## TWO TOKEN STREAMS, BECAUSE THE INSTRUMENTS DISAGREE ABOUT ORTHOGRAPHY

    RH norms          RAW surface       no modernisation, no lemma fallback
    everything else   MODERNISED        + type-level lemma fallback

**RH's norms already carry the archaic variants** -- `shew` -0.693, `vertue`
-0.760, `chuse` -0.807 -- because the historical word2vec models were trained on
unmodernised corpora, so each variant has its own period-appropriate projection.
Modernising maps a C18 word onto a modern word's vector and discards exactly the
historical information the instrument exists to carry. Measured over the 61,551
MorphAdorner pairs where BOTH forms have a value, modernising shifts the score
**+0.192 z toward concrete** (median +0.192; the variant is less abstract in 63%
of pairs). Archaic variants concentrate in early texts, so that shift is
period-correlated and works AGAINST an abstraction rise into the C18 -- it would
flatten the very thing being measured.

**Brysbaert has no entry for any of them** (`shew`, `vertue`, `chuse`, `publick`,
`musick`, `antient`, `burthen`, `onely` are all absent), so leaving the stream
raw collapses its coverage in early texts instead. Both uniform choices bury an
artifact along the year axis; two streams is the only option that does not.

## LEMMAS ARE TYPE-LEVEL, AND MEASURED PER INSTRUMENT

In-context tagging separates noun from verb, which rarely separates content word
from function word and does not change a lemma lookup for the words that matter,
so lemmas come from ONE spaCy pass over the vocabulary rather than a pass over
every document. Coverage gain from the lemma fallback, on 39,644 chadwyck tokens
across 60 texts spanning 1600-1950:

    warriner        27.60% -> 41.11%   +13.51   necessary
    gi              51.15% -> 62.24%   +11.09   necessary
    brysbaert       84.20% -> 91.37%    +7.17   necessary
    usas            91.98% -> 95.21%    +3.23
    k_ratings       87.33% -> 88.99%    +1.66
    RH norms        32.44% -> 32.75%    +0.31   NOT necessary

RH's norms sit at 32% because they hold NO function words -- 0 of the 20
commonest are present -- so they are already a content-word instrument and need
neither a lemma fallback nor a POS filter. The other instruments get both.

## SIGN, WHICH IS THE EASIEST THING HERE TO GET BACKWARDS

RH's scale is z-scored with **HIGH = CONCRETE, NEGATIVE = ABSTRACT** (`stone`
+1.611, `table` +0.884 against `virtue` -1.776, `justice` -1.615). So a RISE in
abstraction is a FALL in `rh_absconc`. Brysbaert runs the other way, 1-5 with
high = concrete, and the two are NOT on a common scale.

## WHICH NORM COLUMN, AND WHY NOT THE PER-CENTURY ONES

`Abs-Conc.Median.median` -- median over the 8 rating sources and over the 6
century columns. Every trend-fitting entry point in the abstraction codebase
defaults to it (`corpus_correction.py:23`, `analysis.py:948`, `analysis.py:1236`).
The per-century columns are each independently z-scored on their own vocabulary
(measured means +0.000/-0.003/-0.017/+0.014/+0.023/+0.000, sds ~1.0 for C16-C21),
so across-century level differences are zeroed BY CONSTRUCTION and a series built
on period-matched norms has its reference frame re-centred at every century
boundary. They are carried here as a DIAGNOSTIC -- `norm_period` as a fixed
effect -- never as the measurement.

## COVERAGE IS A COLUMN, NOT A FOOTNOTE

Every instrument emits its own `*_cov`, and `variant_rate` records the share of
tokens the modernizer rewrote. Coverage must be plotted against year BEFORE any
construct: the modernisation gradient sits INSIDE chadwyck, so orthographic
drift is collinear with year, which is the axis the slope lives on. If coverage
trends, part of any curve is an orthography curve.
"""

import argparse, collections, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
#: RESULTS GO TO $MALIGNMENT_DATA, NOT THE REPO. The chadwyck table is 128 MB
#: and chicago is ~760 MB; `results/` here is untracked but was not ignored, so
#: a single careless `git add` on the folder would have swept them in.
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                   os.path.expanduser("~/malignment-data")),
                    "novel_arc")
MALIGNMENT = "/Users/rj416/github/malignment"
if MALIGNMENT not in sys.path:
    sys.path.insert(0, MALIGNMENT)

#: contractions stay WHOLE. `[A-Za-z]+` splits "don't" into "don"+"t" and
#: "I've" into "I"+"ve", and the modernizer then maps those fragments to
#: real words -- t->to 61x, s->S 54x, ve->we 11x, d->worser 9x in one text.
TOK = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")
PID = re.compile(r"^W(\d+)_(\d+)$")

#: set-membership keys carried from the LLM contrast: every one replicated at
#: q<.05 on BOTH disjoint corpora there, so they arrive with a prior direction.
#: EXACT case, from `category_sizes`. `EMOT` is uppercase while its
#: neighbours are not, and spelling it `Emot` returns a silent flat zero
#: rather than an error -- which is what the pilot produced.
GI_KEYS = ["Positiv", "Pstv", "Passive", "EnlTot", "EnlOth", "EMOT", "Role", "Strong"]
USAS_KEYS = {"usas_x": "X", "usas_n5": "N5"}


def _norm_col(name):
    return "rh_" + name.replace("Abs-Conc.Median.", "absconc_").replace(".", "_").lower()


def load_rh():
    """word -> {col: value} for RH's concreteness norms. Surface forms, raw."""
    import pyarrow.parquet as pq
    p = os.path.expanduser("~/malignment-data/rh_norms/abs_conc_median.parquet")
    t = pq.read_table(p)
    cols = [c for c in t.column_names if c != "word"]
    words = t.column("word").to_pylist()
    out = {}
    series = {c: t.column(c).to_pylist() for c in cols}
    for i, w in enumerate(words):
        d = {}
        for c in cols:
            v = series[c][i]
            if v is not None and v == v:
                d[_norm_col(c)] = float(v)
        if d:
            out[w] = d
    return out, [_norm_col(c) for c in cols]


#: DOUBLE quotes only. Including the curly SINGLE quotes makes every
#: apostrophe in `don't` toggle the in-quote state, which is how the first
#: version of this reported 13.3% of base tokens as dialogue against a true
#: 1.9% median.
_DQ = set('"\u201c\u201d\u00ab\u00bb')


def _dialogue(txt):
    """Share of whitespace-delimited tokens sitting inside a quoted span.

    Carried as a COVARIATE, not a filter. Dialogue is where the deixis, proper
    names and concrete objects live, so it pulls on the concreteness axis
    directly -- and the populations differ sharply on it: base 11.5% mean,
    aligned 10.0%, the c20_fiction anchor 7.4%, but API only 0.81% with 87% of
    passages carrying none at all. Unfiltered historical fiction is heavier
    still than any of them, so placing model passages against a raw corpus
    distribution compares populations that differ on this before they differ on
    anything else.

    In non-fiction the quoted spans are CITATIONS rather than speech
    (literary_criticism 8.2%, philosophy 6.8%), so the number does not mean the
    same thing across genres and should not be read across them.
    """
    toks = txt.split()
    if not toks:
        return None
    inside, on = 0, False
    for ch in txt:
        if ch in _DQ:
            on = not on
        elif on and ch == " ":
            inside += 1
    return inside / len(toks)


class Scorer:
    """Both token streams, one object. Lemma cache is type-level and shared."""

    def __init__(self):
        from malignment import fields
        from lltk.tools.constants import _get_spelling_modernizer
        self.f = fields
        self.mod = _get_spelling_modernizer()
        self.rh, self.rh_cols = load_rh()
        self.known = self._known_vocab()
        self._lem = {}
        self._pos = {}
        self._nlp = None

    def _known_vocab(self):
        """Every surface form the MODERN lexicons already recognise."""
        f = self.f
        v = set(f._norms())
        v |= {w for w in f._k("en")[1] if w.isascii()}
        v |= set(f._usas())
        v |= {w.lower() for w in f._gi()["words"]}
        v |= set(f._brooke())
        return v

    def _modernise(self, w):
        """Rewrite ONLY when it converts a lexicon MISS into a HIT.

        MorphAdorner is a variant->standard map built for early modern text and
        it is NOT safe to apply to a modern token: measured on one 1869 text it
        rewrote 5.93% of tokens, including `got`->`God` 11x, `an`->`and` 50x,
        `red`->`read`, `heard`->`herd`, `sight`->`sighed`. Every one of those is
        a modern word the lexicons already knew, so the rewrite could only
        destroy a correct lookup.

        Guarding on "absent from the lexicons, and its rewrite is present"
        makes the operation exactly what it is for -- rescuing `shew`, `vertue`,
        `chuse` in early texts -- and makes it unable to corrupt a known word.
        """
        if w in self.known:
            return w
        m = self.mod.get(w)
        return m if m and m in self.known else w

    def _tag(self, types):
        """Fill the type-level lemma/POS cache for any types not yet seen."""
        new = [w for w in types if w not in self._lem]
        if not new:
            return
        if self._nlp is None:
            import spacy
            self._nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        for w, doc in zip(new, self._nlp.pipe(new, batch_size=1000)):
            if len(doc):
                self._lem[w] = (doc[0].lemma_ or "").lower()
                self._pos[w] = doc[0].pos_
            else:
                self._lem[w] = w
                self._pos[w] = "X"

    def score(self, txt):
        raw = [w.lower() for w in TOK.findall(txt)]
        if not raw:
            return None
        mod = [self._modernise(w) for w in raw]
        self._tag(set(mod))
        out = {"n_tokens": len(raw),
               "variant_rate": sum(1 for a, b in zip(raw, mod) if a != b) / len(raw),
               "dialogue_share": _dialogue(txt)}

        #: ---- STREAM A: RAW surface, RH norms only. No modernisation, no
        #: lemma fallback, no POS filter -- the lexicon holds no function words
        #: (0 of the 20 commonest), so it filters itself.
        acc = collections.defaultdict(list)
        for w in raw:
            d = self.rh.get(w)
            if d:
                for k, v in d.items():
                    acc[k].append(v)
        for c in self.rh_cols:
            v = acc.get(c)
            if v:
                out[c] = sum(v) / len(v)
                out[c + "_cov"] = len(v) / len(raw)

        #: ---- STREAM B: MODERNISED + type-level lemma fallback.
        lem = [self._lem.get(w, w) for w in mod]
        content = [(w, l) for w, l in zip(mod, lem)
                   if self._pos.get(w) in ("NOUN", "VERB", "ADJ", "ADV")]
        out["n_content"] = len(content)

        look = self.f._lookup
        scal = collections.defaultdict(list)
        for w, l in zip(mod, lem):
            n = look("norms", w, l)
            if n:
                for k, v in n.items():
                    scal["warriner_" + k if k != "concreteness"
                         else "brysbaert_concreteness"].append(v)
            kk = look("k", w, l)
            if kk:
                for k, v in kk.items():
                    scal["k_" + k].append(v)
        for k, v in scal.items():
            out[k] = sum(v) / len(v)
            out[k + "_cov"] = len(v) / len(mod)

        #: RATES over CONTENT words, matching the LLM contrast's denominator.
        if content:
            gi = collections.Counter()
            us = collections.Counter()
            for w, l in content:
                for t in (look("gi", w, l) or ()):
                    gi[t] += 1
                for t in (look("usas_codes", w, l) or ()):
                    head = re.match(r"^[A-Z][0-9]*", t)
                    if head:
                        us[head.group(0)] += 1
            n = len(content)
            for t in GI_KEYS:
                out["gi_" + t.lower()] = gi[t] / n
            for name, code in USAS_KEYS.items():
                out[name] = sum(c for k, c in us.items()
                                if k == code or k.startswith(code)) / n
        return out


def texts_with_years(corpus):
    """[(text_id, year)] for one corpus, dated only, stable order."""
    import lltk
    C = lltk.Corpus(corpus)
    out = []
    for t in C.texts():
        y = t.year
        try:
            y = int(y)
        except (TypeError, ValueError):
            continue
        if 1400 < y < 2020:
            out.append((t.id, y))
    return sorted(out)


def one_text(job):
    """(text_id, year, n, corpus) -> [row]. One worker, one text, own Scorer."""
    global _S
    tid, year, n, corpus = job
    try:
        S = _S
    except NameError:
        S = _S = Scorer()
    import lltk
    C = lltk.Corpus(corpus)
    rows = []
    try:
        tx = C.text(tid)
        for seq, p in enumerate(tx.passages(n=n).texts()):
            r = S.score(p.txt)
            if r is None:
                continue
            m = PID.match(p.id or "")
            r.update(text_id=tid, year=year, seq=seq, corpus=corpus,
                     w_start=int(m.group(1)) if m else None,
                     w_end=int(m.group(2)) if m else None)
            rows.append(r)
    except Exception as e:
        rows.append({"text_id": tid, "year": year, "seq": -1,
                     "corpus": corpus,
                     "error": "%s: %s" % (type(e).__name__, str(e)[:120])})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="chadwyck")
    ap.add_argument("-n", type=int, default=200, help="passage length in words")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default=DATA)
    a = ap.parse_args(argv)
    import pyarrow as pa, pyarrow.parquet as pq

    t0 = time.time()
    jobs = [(tid, y, a.n, a.corpus) for tid, y in texts_with_years(a.corpus)]
    if a.limit:
        jobs = jobs[:a.limit]
    os.makedirs(a.out, exist_ok=True)
    print("%d dated %s texts, n=%d words/passage"
          % (len(jobs), a.corpus, a.n), flush=True)

    if a.workers > 1:
        import multiprocessing as mp
        #: SPAWN, not fork. The parent initialises Metal the moment it imports
        #: lltk (which pulls spacy/thinc), and a forked child inherits a
        #: half-initialised MPSGraph: macOS refuses to continue and kills it.
        #: Pool then replaces the dead worker, which dies the same way, so the
        #: run does not fail -- it spins forever respawning while printing
        #: `+[MPSGraphObject initialize] ... Crashing instead` and never
        #: completing a single text. spawn re-imports cleanly per worker; each
        #: builds its own Scorer anyway (2.3 GB, and the box has 103 GB).
        pool = mp.get_context("spawn").Pool(a.workers)
        it = pool.imap_unordered(one_text, jobs, chunksize=1)
    else:
        pool, it = None, (one_text(j) for j in jobs)

    rows, done = [], 0
    for part in it:
        rows.extend(part)
        done += 1
        if done % 25 == 0 or done == len(jobs):
            el = time.time() - t0
            print("  [%d/%d] %s passages  %.0f/s  %.1f min elapsed"
                  % (done, len(jobs), "{:,}".format(len(rows)),
                     len(rows) / max(el, 1e-9), el / 60), flush=True)
    if pool:
        pool.close(); pool.join()

    #: SAY IT if any text failed. A silent short table is the defect this
    #: exists to avoid -- a missing text is a missing DECADE, not a missing row.
    bad = [r for r in rows if r.get("seq") == -1]
    rows = [r for r in rows if r.get("seq") != -1]
    keys = sorted({k for r in rows for k in r})
    fp = os.path.join(a.out, "%s_n%d.parquet" % (a.corpus, a.n))
    pq.write_table(pa.table({k: [r.get(k) for r in rows] for k in keys}),
                   fp, compression="zstd")
    print("-> %s  (%s passages, %d texts, %.1f min)"
          % (fp, "{:,}".format(len(rows)),
             len({r["text_id"] for r in rows}), (time.time() - t0) / 60))
    if bad:
        print("   %d TEXTS FAILED:" % len(bad))
        for r in bad[:10]:
            print("     %s (%s) %s" % (r["text_id"], r["year"], r.get("error")))


if __name__ == "__main__":
    main()
