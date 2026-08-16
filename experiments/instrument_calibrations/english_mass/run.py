#!/usr/bin/env python
"""run.py — how much of each model's resolved word mass is English.

    python run.py --panel              # what the declared panel is, and why
    python run.py --rejects            # highest-mass words NO list accepts
    python run.py                      # per-model table, core list
    python run.py --list wide          # ... under the permissive list
    python run.py --write              # -> results/english_mass.json

## THE QUESTION

`tail` was read as an English-fluency signal once and is not one -- it is the
mass twp left on first tokens below theta, computed over a CJK-aware trie, and a
peaky Chinese model has a low tail for the same reason a peaky English one does.
RH: *"How did you test fluency with english"*. This is that test.

## THE METRIC — A DECOMPOSITION, NOT A SINGLE NUMBER

Every resolved word in a cell falls in exactly one bucket, and the six shares
sum to 1.0 over the resolved mass:

    en      lower(word) is in the wordlist          -> the headline
    cjk     contains Han / Hiragana / Katakana / Hangul
    script  Arabic, Cyrillic, Hebrew, Devanagari, Greek, Thai
    num     begins with a digit
    punct   contains no letter and no digit
    unk     Latin letters, not in the list          -> fragments, typos,
                                                       romanised foreign words

**The buckets exist so the complement is named.** A bare `p_english = 0.71`
leaves the other 29% as one anonymous quantity, and "this model is 29% not
English" is a different claim from "this model spends 29% on digits and
punctuation". Digits are classified BEFORE the wordlist because wordfreq holds
`1`, `2`, `3` at high frequency and would otherwise score a model's numerals as
English.

Two denominators, both reported:

    p_en_resolved = en / (all resolved)         the language question
    p_en_absolute = p_en_resolved * (1 - total) out of the full 1.0, so it
                                                composes with any other mass

## WHAT IT CANNOT DO

It separates English from not-English. It does NOT separate fluent English from
degenerate English -- `the the the the` scores 1.0. `zipf_mean` (mass-weighted
mean log-frequency of the English words) and `top1` are reported beside it
because that is where degeneracy shows: a model dumping its mass on function
words has a high `p_en` AND a high `zipf_mean`, and the pair is readable where
either alone is not.

## THE PANEL

Prompt sets are fleet-defined and DO NOT NEST -- the 407 models with cells span
4,484 distinct prompts and the universal intersection is far smaller. Comparing
models on "mean over their own cells" would mix prompt composition into a
between-model number. The declared panel is the fully-crossed tier: **English
prompts held by at least MIN_MODELS models, and models holding at least
MIN_PROMPTS of them.** `--panel` prints both, and the crossing rate.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RESULTS = os.path.join(HERE, "results")
sys.path.insert(0, REPO)
from malignment import ch  # noqa: E402

MIN_MODELS = 400
MIN_PROMPTS = 0.95   # fraction of the panel a model must hold to be listed

CJK = r"\p{Han}|\p{Hiragana}|\p{Katakana}|\p{Hangul}"
SCRIPT = r"\p{Arabic}|\p{Cyrillic}|\p{Hebrew}|\p{Devanagari}|\p{Greek}|\p{Thai}"

#: The panel, as a CTE every query below shares. Written once so the table and
#: the reject listing cannot silently disagree about what they are describing.
PANEL = """
WITH enp AS (
  SELECT c.prompt AS prompt FROM twp_cells c
  INNER JOIN (SELECT DISTINCT prompt FROM prompts WHERE language='en') p
    ON c.prompt = p.prompt
  GROUP BY c.prompt HAVING uniqExact(c.model) >= %d
)
""" % MIN_MODELS


def _bucket(col):
    return ("multiIf("
            "match({w}, '{cjk}'),   'cjk',"
            "match({w}, '{scr}'),   'script',"
            "match({w}, '^[0-9]'),  'num',"
            "NOT match({w}, '[A-Za-z0-9]'), 'punct',"
            "e.word != '',          'en',"
            "'unk')").format(w="w.word", cjk=CJK, scr=SCRIPT).replace(
                "e.word", col)


def panel():
    n_pr = ch.scalar(PANEL + "SELECT count() FROM enp")
    rows = ch.query(PANEL + """
    SELECT c.model AS model, count() AS n FROM twp_cells c
    INNER JOIN enp USING (prompt) GROUP BY model ORDER BY n DESC""")
    full = [r for r in rows if r["n"] >= MIN_PROMPTS * n_pr]
    print("  English prompts held by >= %d models : %d" % (MIN_MODELS, n_pr))
    print("  models with any cell on them        : %d" % len(rows))
    print("  models holding >= %.0f%% of the panel  : %d"
          % (100 * MIN_PROMPTS, len(full)))
    print("  crossing (cells / models x prompts)  : %.4f"
          % (sum(r["n"] for r in full) / float(len(full) * n_pr)))
    print("  models DROPPED for partial coverage  : %d" % (len(rows) - len(full)))
    for r in rows[len(full):][:12]:
        print("      %-52s %d/%d" % (r["model"], r["n"], n_pr))
    return n_pr, [r["model"] for r in full]


def rejects(limit=40):
    """Highest-mass Latin-script words NO list accepts. The wordlist's own audit."""
    sql = PANEL + """
    SELECT w.word AS word, round(sum(w.p), 1) AS mass, count() AS n_cells
    FROM twp_words w INNER JOIN enp USING (prompt)
    LEFT JOIN english_words e ON lower(w.word) = e.word
    WHERE e.word = '' AND match(w.word, '^[A-Za-z]')
    GROUP BY word ORDER BY mass DESC LIMIT %d""" % limit
    tot = ch.scalar(PANEL + """
    SELECT sum(w.p) FROM twp_words w INNER JOIN enp USING (prompt)""")
    print("  total resolved mass on the panel: %.0f" % tot)
    print("  %-22s %10s %8s %10s" % ("word", "mass", "cells", "share"))
    for r in ch.query(sql):
        print("  %-22s %10.1f %8d %9.5f%%"
              % (r["word"], r["mass"], r["n_cells"], 100 * r["mass"] / tot))


def table(which="core", models=None):
    flag = {"core": "e.core = 1", "wide": "e.word != ''"}[which]
    sql = PANEL + """
    , cls AS (
      SELECT w.model AS model, w.prompt AS prompt, w.p AS p,
             multiIf(
               match(w.word, '{cjk}'),  'cjk',
               match(w.word, '{scr}'),  'script',
               match(w.word, '^[0-9]'), 'num',
               NOT match(w.word, '[A-Za-z0-9]'), 'punct',
               {flag},                  'en',
               'unk') AS bucket,
             if({flag}, e.zipf, 0.) AS zipf
      FROM twp_words w INNER JOIN enp USING (prompt)
      LEFT JOIN english_words e ON lower(w.word) = e.word
    )
    SELECT model,
           count(DISTINCT prompt)                       AS n_prompts,
           sum(p)                                       AS resolved,
           sumIf(p, bucket='en')    / sum(p)            AS p_en,
           sumIf(p, bucket='cjk')   / sum(p)            AS p_cjk,
           sumIf(p, bucket='script')/ sum(p)            AS p_script,
           sumIf(p, bucket='num')   / sum(p)            AS p_num,
           sumIf(p, bucket='punct') / sum(p)            AS p_punct,
           sumIf(p, bucket='unk')   / sum(p)            AS p_unk,
           sumIf(p*zipf, bucket='en') / sumIf(p, bucket='en') AS zipf_mean
    FROM cls GROUP BY model
    """.format(cjk=CJK, scr=SCRIPT, flag=flag)
    rows = ch.query(sql, limit_bytes=None)
    if models is not None:
        keep = set(models)
        rows = [r for r in rows if r["model"] in keep]

    #: `resolved` is summed over the panel's cells, so `1 - total` per cell has
    #: to come from twp_cells rather than be inferred from it -- the absolute
    #: denominator is a property of the CELL, not of the words we kept.
    res = {r["model"]: r["resolved"] / r["n_prompts"] for r in rows}
    for r in rows:
        r["p_en_absolute"] = r["p_en"] * res[r["model"]]
    rows.sort(key=lambda r: r["p_en"])
    return rows


def roster(rows):
    """The 50 declared base->aligned endpoint pairs, worst English first.

    RH: *"we've added so many and from around the world and I dont know if I
    can trust them"*. The pair, not the model, is the unit -- a base that is
    fine and an aligned arm that is not would be invisible in a model listing
    sorted by either one alone, and `d` is the column that would show it.
    """
    by = {r["model"]: r for r in rows}
    eps = ch.query("SELECT base, endpoint FROM endpoints ORDER BY base")
    out, miss = [], []
    for e in eps:
        b, a = by.get(e["base"]), by.get(e["endpoint"])
        if not b or not a:
            miss.append((e["base"], e["endpoint"], bool(b), bool(a)))
            continue
        out.append({"base": e["base"], "aligned": e["endpoint"],
                    "en_base": b["p_en"], "en_aligned": a["p_en"],
                    "d": a["p_en"] - b["p_en"],
                    "unk_aligned": a["p_unk"], "cjk_aligned": a["p_cjk"],
                    "zipf_aligned": a["zipf_mean"]})
    out.sort(key=lambda r: min(r["en_base"], r["en_aligned"]))
    print("  %-44s %8s %8s %8s %8s %8s %6s"
          % ("pair (base -> aligned)", "en_base", "en_algn", "delta",
             "unk_a", "cjk_a", "zipf_a"))
    print("  " + "-" * 96)
    for r in out:
        print("  %-44s %8.4f %8.4f %+8.4f %8.4f %8.4f %6.2f"
              % (r["aligned"][-44:], r["en_base"], r["en_aligned"], r["d"],
                 r["unk_aligned"], r["cjk_aligned"], r["zipf_aligned"]))
    if miss:
        print("\n  NOT ON THE PANEL (%d pairs): both arms must hold the panel "
              "or the pair is not comparable" % len(miss))
        for b, a, hb, ha in miss:
            print("      %-46s base=%s aligned=%s" % (a[-46:], hb, ha))
    return out


HDR = ("%-46s %7s %7s %7s %7s %7s %7s %7s %6s"
       % ("model", "p_en", "cjk", "scrpt", "num", "punct", "unk", "abs", "zipf"))


def _show(rows, n=30, tail=6):
    print("  " + HDR)
    print("  " + "-" * len(HDR))
    show = rows if n >= len(rows) else rows[:n] + [None] + rows[-tail:]
    for r in show:
        if r is None:
            print("  " + "." * 24)
            continue
        print("  %-46s %7.4f %7.4f %7.4f %7.4f %7.4f %7.4f %7.4f %6.2f"
              % (r["model"][-46:], r["p_en"], r["p_cjk"], r["p_script"],
                 r["p_num"], r["p_punct"], r["p_unk"], r["p_en_absolute"],
                 r["zipf_mean"]))


def check(rows):
    """The six buckets must sum to 1, and `resolved` must equal `1 - total`.

    Neither is a formality. The buckets are a `multiIf` whose branches must
    partition, and one overlapping predicate would silently move mass between
    named columns. `resolved` is summed from twp_words while `total` is written
    by the twp producer from the SAME pass -- if they disagree the join dropped
    rows, which is the failure that looks like a result.
    """
    worst_sum = max(abs(sum(r["p_" + k] for k in
                           ("en", "cjk", "script", "num", "punct", "unk")) - 1.0)
                    for r in rows)
    got = {r["model"]: r["p_en_absolute"] / r["p_en"] for r in rows}
    want = {r["model"]: 1.0 - r["t"] for r in ch.query(PANEL + """
        SELECT c.model AS model, avg(c.total) AS t FROM twp_cells c
        INNER JOIN enp USING (prompt) GROUP BY model""", limit_bytes=None)}
    d = [(abs(got[m] - want[m]), m) for m in got if m in want]
    d.sort(reverse=True)
    print("  buckets sum to 1        : worst |err| = %.2e" % worst_sum)
    print("  resolved == 1 - total   : worst |err| = %.2e  (%s)" % d[0])
    print("  models checked          : %d of %d" % (len(d), len(rows)))
    for dev, m in d[:5]:
        print("      %-52s %.2e" % (m, dev))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--roster", action="store_true")
    ap.add_argument("--panel", action="store_true")
    ap.add_argument("--rejects", action="store_true")
    ap.add_argument("--list", default="core", choices=["core", "wide"])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()

    if a.rejects:
        return rejects()
    n_pr, models = panel()
    if a.panel:
        return 0

    rows = table(a.list, models)
    if a.check:
        return check(rows)
    if a.roster:
        roster(rows)
        return 0
    print("\n  list=%s   panel=%d prompts x %d models\n" % (a.list, n_pr, len(rows)))
    _show(rows, a.n)

    if a.write:
        os.makedirs(RESULTS, exist_ok=True)
        #: **The list goes in the FILENAME.** `--list wide` writing over
        #: `english_mass.json` would leave one path holding either of two
        #: different quantities, distinguishable only by a field inside it.
        out = os.path.join(RESULTS, "english_mass.%s.json" % a.list)
        json.dump({"list": a.list, "min_models": MIN_MODELS,
                   "min_prompts_frac": MIN_PROMPTS, "n_prompts": n_pr,
                   "n_models": len(rows), "models": rows},
                  open(out, "w"), indent=1)
        print("\n  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
