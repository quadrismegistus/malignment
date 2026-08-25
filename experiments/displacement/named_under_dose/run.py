"""Assemble the word-level dataset: movement, dose, and the named norms.

    python -u run.py                       # both languages, default thresholds
    python -u run.py --lang en --min-cells 20
    python -u run.py --out ~/malignment-data/named_under_dose

One row per (lineage, prompt, word) where the word MOVED, carrying its direction,
the base-arm transgressive dose of the frame it moved in, and its named norms.
`analyse.py` does the held-out fitting; this file only joins and writes.

## WHAT IS JOINED, AND WHERE EACH PIECE COMES FROM

    movement            per (base, aligned, prompt, word): p_base, p_aligned, cls.
                        Restricted to roster.endpoints() -- 50 pairs -- because the
                        table holds 153 edges including rungs and transitive pairs,
                        and one base model would otherwise vote up to eleven times.
    levels_long         k_transgressiveness base_level per (lineage, prompt), from
                        norm_change. This is the DOSE, measured on the base arm.
    fields.norms        17 norms per word, cached per word rather than per row --
                        146k words against 3.4M rows, so the cache is the difference
                        between minutes and hours.

## THE DOSE IS PER (LINEAGE, PROMPT), NOT PER PROMPT

A frame's transgressive mass is a property of what a GIVEN BASE MODEL puts there,
so the same prompt carries a different dose on different lineages. Joining on prompt
alone would average that away and would silently reintroduce the pooling the
lineage-unit discipline exists to prevent.

## WORDS ARE NOT LOWERCASED OR STEMMED HERE

`movement`'s word column is the analysis key the store was built on. Normalising it
here would merge cells the upstream rules kept apart and would break the join back to
anything else. `fields.norms` does its own casing internally.
"""

import argparse, collections, csv, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

DOSE_SCALE = "k_transgressiveness"
LEVELS = os.path.expanduser("~/malignment-data/norm_change/levels_long.csv.gz")
OUT = os.path.expanduser("~/malignment-data/named_under_dose")

#: the norms carried per word. `*_coverage`, `n_tokens`, `n_content` are bookkeeping
#: from fields.py and are written so a later filter can use them, NOT as features.
BOOKKEEPING = {"k_coverage", "brysbaert_coverage", "warriner_coverage",
               "n_tokens", "n_content", "concreteness_zh_coverage", "n_words"}

#: THE TWO LANGUAGES DO NOT SHARE A FEATURE SET, and discovering that from a
#: header written on the first row seen cost a whole zh arm. English carries 12
#: usable norms (the 7 k_ratings, Brysbaert concreteness, four Warriner scales);
#: Chinese carries 7 (the k_ratings) plus concreteness_zh. Writing one header
#: from whichever language happened to appear first leaves the other language's
#: rows blank in five columns, and `analyse.load` drops any row with a blank
#: feature -- so every zh row vanished silently and the file still looked whole.
#: One file per language, each with its OWN schema, and never a pooled fit.


def load_dose(langs):
    """-> {(lineage, prompt): (dose, lang)} for the base arm."""
    if not os.path.exists(LEVELS):
        sys.exit("no levels_long at %s -- run norm_change first" % LEVELS)
    out = {}
    with gzip.open(LEVELS, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head) or v[ix["scale"]] != DOSE_SCALE:
                continue
            lg = v[ix["lang"]]
            if lg not in langs:
                continue
            b = v[ix["base_level"]]
            if not b or b == "\\N":
                continue
            try:
                out[(v[ix["base"]] + ">" + v[ix["aligned"]], v[ix["prompt"]])] = (float(b), lg)
            except ValueError:
                continue
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--chunk", type=int, default=200,
                    help="prompts per ClickHouse query; the table is 56M rows and "
                         "a single unchunked read has tripped the 2GB result guard")
    a = ap.parse_args(argv)
    langs = {a.lang} if a.lang else {"en", "zh"}

    from malignment import ch, roster, fields as F

    m = roster.endpoints()
    m = m[0] if isinstance(m, tuple) else m
    EP = {"%s>%s" % (b, al) for b, al in m.items()}
    print("endpoint pairs: %d" % len(EP))

    dose = load_dose(langs)
    print("dose rows: %d over %d prompts, langs %s"
          % (len(dose), len({p for _, p in dose}), sorted(langs)))
    prompts = sorted({p for _, p in dose})

    #: NORMS ARE CACHED PER WORD. 146k distinct words against 3.4M rows.
    cache = {}
    SCALES = None

    def norms_of(w, lang):
        v = cache.get((w, lang))
        if v is None:
            n = F.norms_zh([w]) if lang == "zh" else F.norms(w)
            v = {k: n.get(k) for k in n}
            cache[(w, lang)] = v
        return v

    os.makedirs(a.out, exist_ok=True)
    if not a.lang:
        sys.exit("--lang is required: en and zh have different norm sets and must "
                 "not share a header. Run once per language.")
    path = os.path.join(a.out, "cells_%s.csv.gz" % a.lang)
    pairs = " OR ".join("(base='%s' AND aligned='%s')"
                        % (b.replace("'", "''"), al.replace("'", "''"))
                        for b, al in m.items())

    n_rows = n_skip_dose = n_skip_norm = 0
    seen_words = set()
    fh = gzip.open(path, "wt", encoding="utf-8", newline="")
    w = None
    for i in range(0, len(prompts), a.chunk):
        block = prompts[i:i + a.chunk]
        #: PROMPT TEXT NEVER GOES INTO THE SQL. These prompts carry backslashes,
        #: newlines and both quote characters, and a `.replace("\'", "\'\'")` leaves
        #: the backslash to be read as an escape -- which is how this first ran and
        #: failed at position 4152 on a prompt containing `He\'d`. Matching on
        #: base64Encode(prompt) puts only [A-Za-z0-9+/=] in the query.
        import base64
        inlist = ",".join(
            "'" + base64.b64encode(p.encode("utf-8")).decode("ascii") + "'"
            for p in block)
        rows = ch.query(
            "SELECT base, aligned, prompt, word, p_base, p_aligned, cls "
            "FROM movement WHERE (%s) AND base64Encode(prompt) IN (%s) "
            "AND cls != 'still'" % (pairs, inlist))
        for r in rows:
            lin = "%s>%s" % (r["base"], r["aligned"])
            if lin not in EP:
                continue
            d = dose.get((lin, r["prompt"]))
            if d is None:
                n_skip_dose += 1
                continue
            dv, lang = d
            nm = norms_of(r["word"], lang)
            if not nm:
                n_skip_norm += 1
                continue
            if SCALES is None:
                SCALES = sorted(k for k in nm if k not in BOOKKEEPING)
                w = csv.DictWriter(
                    fh, delimiter="\t",
                    fieldnames=["lineage", "prompt", "word", "lang", "dose",
                                "direction", "p_base", "p_aligned"]
                    + SCALES + sorted(BOOKKEEPING & set(nm)))
                w.writeheader()
            row = {"lineage": lin, "prompt": r["prompt"], "word": r["word"],
                   "lang": lang, "dose": "%.6f" % dv,
                   "direction": 1 if r["cls"] == "riser" else -1,
                   "p_base": "%.8g" % float(r["p_base"]),
                   "p_aligned": "%.8g" % float(r["p_aligned"])}
            for k in SCALES:
                v = nm.get(k)
                row[k] = "" if v is None else ("%.6g" % v if isinstance(v, float) else v)
            for k in (BOOKKEEPING & set(nm)):
                v = nm.get(k)
                row[k] = "" if v is None else ("%.6g" % v if isinstance(v, float) else v)
            w.writerow(row)
            n_rows += 1
            seen_words.add(r["word"])
        if (i // a.chunk) % 5 == 0:
            print("  %d/%d prompts | %d rows | %d words"
                  % (min(i + a.chunk, len(prompts)), len(prompts), n_rows, len(seen_words)))
    fh.close()

    print("\nwrote %s" % path)
    print("  rows %d | words %d | skipped: no dose %d, no norms %d"
          % (n_rows, len(seen_words), n_skip_dose, n_skip_norm))
    print("  features: %s" % (", ".join(SCALES) if SCALES else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
