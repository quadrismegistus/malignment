"""norm_change: build the long-form table. Statistics live in analyse.py.

    python -u run.py --plan          # vocabulary and coverage, writes nothing
    python -u run.py --run           # build results/long/*.csv.gz
    python -u run.py --run --lang zh

## WHAT THIS PRODUCES, AND WHY IT IS SPLIT FROM THE STATISTICS

One row per (lineage, prompt, lang, source, scale, arm): the mass-weighted mean
of that scale over the rated words of that arm's continuation distribution, with
the coverage that produced it. Every hypothesis in `registration.md` and every
exploratory read is a `groupby` over this table and nothing else, so a number can
be disputed without rerunning anything.

    long/levels_long.csv.gz    the atomic table, continuous scales
    long/fields_long.csv.gz    the same shape for categorical field mass
    long/words_long.csv.gz     one row per (lineage, prompt, word) with p_base,
                               p_aligned, delta, cls and the word's own
                               attributes -- the layer the function-word
                               decomposition needs

## THE SHAPE OF THE COMPUTATION

`movement` is 56,280,403 rows over 153 lineages, 4,482 prompts and 178,273
distinct words. Resolving norms per row in Python would be 56M lexicon lookups.
Instead the VOCABULARY is resolved once (178,273 words, seconds) and pushed back
as a temp table, and the mass-weighting happens in SQL. That is the same route
`verse_capacity.py` takes and for the same reason: point-querying the store is
the access shape ClickHouse is worst at.

## COVERAGE TRAVELS, ALWAYS

A mass-weighted mean over rated words is only as good as the share of mass those
words hold. Every row carries `cov`. A source that covers 3% of a distribution
and one that covers 80% produce numbers of the same dtype and not of the same
worth, and nothing downstream can recover that if it is dropped here.

## LANGUAGE IS A PARTITION, NOT A COLUMN TO AVERAGE OVER

416 of the 4,482 prompts are Chinese and 4,066 are English, classified on the
prompt (a CJK character anywhere). They are written to the same table with a
`lang` column and MUST be grouped by it. M01 O_crosslingual found the affect
signature does not travel to Chinese while the substitution does, so a pooled
mean here would average a real effect against a real non-effect.
"""

import argparse, collections, gzip, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
OUT = os.path.join(HERE, "results", "long")

CJK = re.compile(r"[一-鿿㐀-䶿]")

#: The continuous scales, by the accessor that serves them. `norms` returns a
#: flat dict whose keys are already source-prefixed, so the source is recovered
#: from the key rather than declared twice and allowed to drift.
EN_NORM_PREFIXES = ("warriner_", "brysbaert_", "brooke_", "k_")

#: H3 names USAS X1. The finer codes ride along as exploration -- see the
#: registration, which declares X1 as the test and X2..X5 as exploratory.
INTERIORITY = ("X1", "X2", "X2.1", "X3", "X4", "X5")


def _lang(prompt):
    return "zh" if CJK.search(prompt or "") else "en"


def vocabulary(ch):
    """Every word in `movement`, with its language guessed from the word itself."""
    rows = ch.query("SELECT DISTINCT word FROM movement")
    return [r["word"] for r in rows]


def resolve(words):
    """word -> {(source, scale): value} and word -> {field: weight}.

    Resolved ONCE for the whole vocabulary. A word absent from a source simply
    has no entry for it -- never a zero, which would enter a mean as a real
    mid-scale observation and is the defect `fields.norms` documents at length.
    """
    from malignment import fields as F
    cont, cats, attrs = {}, {}, {}
    for w in words:
        lang = "zh" if CJK.search(w) else "en"
        c = {}
        if lang == "en":
            n = F.norms(w)
            for k, v in n.items():
                if k.endswith("_coverage") or k == "n_content":
                    continue
                if isinstance(v, (int, float)) and k.startswith(EN_NORM_PREFIXES):
                    c[k] = float(v)
        else:
            n = F.norms_zh([w])
            for k, v in n.items():
                if k.endswith("_coverage") or k == "n_words":
                    continue
                if isinstance(v, (int, float)):
                    c[k] = float(v)
        if c:
            cont[w] = c
        #: categorical fields, fractional so one word is worth one unit in
        #: either language -- see fields._usas_zh on why zh needs that.
        try:
            raw = F.usas(w, names=False, lang=lang)
        except Exception:
            raw = set()
        codes = [F._zh_tag_base(p) if lang == "zh" else p
                 for code in raw for p in str(code).split("/")]
        codes = [c2 for c2 in codes if c2]
        if codes:
            cats[w] = {c2: 1.0 / len(codes) for c2 in codes}
        attrs[w] = {"lang": lang, "freq": F.freq(w, lang)}
    return cont, cats, attrs


def contextual_pos(ch, limit_lang=None):
    """(prompt, word) -> UPOS for every MOVER. -> dict

    **CONTEXTUAL, AND THAT IS NOT A REFINEMENT.** `pos.get_pos` tags
    `prompt + " " + word` and takes the last token, because an out-of-context
    lookup returns the most frequent reading of a word FORM: at "She began to
    ___" it labels `fall break kiss punch strike` as NOUNS, and the archive
    measured its own out-of-context lookup at **41.2% verbs inside its "noun"
    band**. Those are exactly the words the function-word control has to
    separate, so tagging them out of context would corrupt the control rather
    than merely blur it.

    Cached per (tagger, prompt, word), so this is slow once and free after --
    and the TAGGER IS IN THE KEY, which is what makes running two models safe.

    BOTH LANGUAGES ARE TAGGED IN CONTEXT. `zh_core_web_sm` was installed
    2026-08-24 for exactly this: an earlier version fell back to SUBTLEX-CH
    `Dominant.PoS` for Chinese, a per-WORD tag with no context in it, which
    would have put a contextual control on one arm and a lookup on the other
    and then compared them. It emits UPOS directly, so no mapping is needed on
    this path -- 她/PRON 慢慢/ADV 脱下/VERB 了/PART 的/PART 衣服/NOUN.

    `fields.pos_map` and SUBTLEX's `Dominant.PoS` remain for word-level work
    where no frame exists; they are not used here.
    """
    import spacy
    from malignment.pos import get_pos
    NLP = {"en": None, "zh": spacy.load("zh_core_web_sm")}
    rows = ch.query("SELECT prompt, groupUniqArray(word) AS ws FROM movement "
                    "WHERE cls != 'still' GROUP BY prompt")
    out, n_en, n_zh = {}, 0, 0
    for i, r in enumerate(rows, 1):
        pr, ws = r["prompt"], list(r["ws"] or [])
        lg = _lang(pr)
        if limit_lang and lg != limit_lang:
            continue
        try:
            tags = get_pos(ws, pr, nlp=NLP[lg])
        except Exception:
            tags = {}
        for w, t in tags.items():
            out[(pr, w)] = t
        if lg == "en":
            n_en += len(tags)
        else:
            n_zh += len(tags)
        if i % 500 == 0:
            print("    pos %d/%d prompts (en %s, zh %s)"
                  % (i, len(rows), format(n_en, ","), format(n_zh, ",")), flush=True)
    return out


def push(ch, name, rows, cols):
    """Replace a temp table with `rows`. DDL + JSONEachRow, the twp route."""
    import json
    ch.execute("DROP TABLE IF EXISTS %s" % name)
    ch.execute("CREATE TABLE %s (%s) ENGINE = MergeTree ORDER BY tuple()"
               % (name, ", ".join("%s %s" % c for c in cols)))
    B = 50000
    for i in range(0, len(rows), B):
        ch.execute("INSERT INTO %s FORMAT JSONEachRow" % name,
                   stdin="\n".join(json.dumps(r, ensure_ascii=False)
                                   for r in rows[i:i + B]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    a = ap.parse_args(argv)
    if not (a.plan or a.run):
        ap.print_help()
        return 0

    from malignment import ch
    os.makedirs(OUT, exist_ok=True)

    words = vocabulary(ch)
    print("vocabulary: %s distinct words" % format(len(words), ","), flush=True)
    cont, cats, attrs = resolve(words)
    n_zh = sum(1 for w in words if CJK.search(w))
    print("  zh words %s | en words %s" % (format(n_zh, ","), format(len(words) - n_zh, ",")))
    print("  with a continuous norm : %s (%.1f%%)"
          % (format(len(cont), ","), 100 * len(cont) / max(len(words), 1)))
    print("  with a USAS field      : %s (%.1f%%)"
          % (format(len(cats), ","), 100 * len(cats) / max(len(words), 1)))
    print("  POS is resolved CONTEXTUALLY per (prompt, word), not per word --"
          " see contextual_pos()")
    scales = sorted({k for v in cont.values() for k in v})
    print("  continuous scales: %d %s" % (len(scales), scales[:8]))

    if a.plan:
        print()
        print("--plan: nothing written. Re-run with --run.")
        return 0

    #: word -> scale rows, long, for the SQL join
    srows = [{"word": w, "scale": s, "value": v}
             for w, d in cont.items() for s, v in d.items()]
    frows = [{"word": w, "field": f, "weight": v}
             for w, d in cats.items() for f, v in d.items()]
    print("resolving contextual POS (cached; slow only the first time)...", flush=True)
    pos = contextual_pos(ch, a.lang)
    from malignment import fields as _F
    arows = [{"prompt": pr, "word": w, "upos": t,
              "is_function": 0 if t in _F.CONTENT_POS else 1,
              "freq": float((attrs.get(w) or {}).get("freq") or 0.0)}
             for (pr, w), t in pos.items()]
    print("  tagged %s (prompt, word) pairs" % format(len(arows), ","))
    print()
    print("pushing lookups: %s scale rows, %s field rows, %s attr rows"
          % (format(len(srows), ","), format(len(frows), ","), format(len(arows), ",")), flush=True)
    push(ch, "nc_scale_tmp", srows,
         [("word", "String"), ("scale", "String"), ("value", "Float64")])
    push(ch, "nc_field_tmp", frows,
         [("word", "String"), ("field", "String"), ("weight", "Float64")])
    push(ch, "nc_attr_tmp", arows,
         [("prompt", "String"), ("word", "String"), ("upos", "String"),
          ("is_function", "UInt8"), ("freq", "Float64")])

    #: THE MASS-WEIGHTING, in SQL. One row per (lineage, prompt, scale, arm),
    #: with coverage as the share of that arm's mass the rated words hold.
    print("aggregating levels...", flush=True)
    q = """
    SELECT m.base AS base, m.aligned AS aligned, m.prompt AS prompt,
           s.scale AS scale,
           sum(m.p_base   * s.value) / nullIf(sum(m.p_base),   0) AS base_level,
           sum(m.p_aligned* s.value) / nullIf(sum(m.p_aligned),0) AS aligned_level,
           sum(m.p_base)    AS base_cov,
           sum(m.p_aligned) AS aligned_cov,
           count() AS n_words
    FROM movement m INNER JOIN nc_scale_tmp s ON m.word = s.word
    GROUP BY base, aligned, prompt, scale
    FORMAT TabSeparatedWithNames"""
    _write(ch, q, os.path.join(OUT, "levels_long.csv.gz"), a.lang)

    print("aggregating fields...", flush=True)
    qf = q.replace("nc_scale_tmp s ON m.word = s.word", "nc_field_tmp s ON m.word = s.word") \
          .replace("s.scale AS scale", "s.field AS scale") \
          .replace("s.value", "s.weight")
    _write(ch, qf, os.path.join(OUT, "fields_long.csv.gz"), a.lang)

    print("writing the word layer...", flush=True)
    qw = """
    SELECT m.base AS base, m.aligned AS aligned, m.prompt AS prompt,
           m.word AS word, m.p_base AS p_base, m.p_aligned AS p_aligned,
           m.delta AS delta, m.cls AS cls,
           a.upos AS upos, a.is_function AS is_function, a.freq AS freq
    FROM movement m INNER JOIN nc_attr_tmp a
      ON m.word = a.word AND m.prompt = a.prompt
    WHERE m.cls != 'still'
    FORMAT TabSeparatedWithNames"""
    _write(ch, qw, os.path.join(OUT, "words_long.csv.gz"), a.lang)

    print()
    print("-> %s" % OUT)
    return 0


def _write(ch, q, path, lang=None):
    """Stream a TSV result to gzip, adding `lang` from the prompt."""
    out = ch.raw(q)
    lines = out.splitlines()
    if not lines:
        print("  EMPTY: %s" % os.path.basename(path))
        return
    head = lines[0].split("\t")
    ip = head.index("prompt")
    kept = 0
    with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(head + ["lang"]) + "\n")
        for line in lines[1:]:
            p = line.split("\t")
            if len(p) != len(head):
                continue
            lg = _lang(p[ip])
            if lang and lg != lang:
                continue
            fh.write(line + "\t" + lg + "\n")
            kept += 1
    print("  %-22s %s rows" % (os.path.basename(path), format(kept, ",")))


if __name__ == "__main__":
    sys.exit(main())
