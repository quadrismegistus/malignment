"""Export everything as LONG-FORM tables, one row per observation.

    python experiments/slot_ratings/tidy.py

The per-study JSONs are wide: one record per (prompt, lineage) with ~100 columns
holding every scale on both arms. That is convenient for the producers and wrong
for anyone else. This writes the same content in tidy form -- one row per
observation, every factor an explicit column -- so that a reader can compute any
gap, difference-in-differences or sign test themselves without reading our code,
and can plot without recomputing anything.

    levels_long.csv    one row per (study, prompt, lineage, arm, scale)
                       the atomic measurement: a mass-weighted level.
                       Every gap, delta and DiD in every README derives from
                       this table alone.

    words_long.csv     one row per (study, prompt, word)
                       the ratings, the net movement across lineages, and the
                       instrument that produced them.

    units_long.csv     one row per (study, prompt) -- the design.
                       which matched set, which cell, which corpus, which
                       lineages cover it.

COVERAGE IS A COLUMN, not a footnote: `cov` is the share of that arm's
probability mass held by the rated words, and a level is only as good as it.

Nothing is aggregated here and no test is run. Deliberately.
"""

import collections, csv, gzip, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "long")
#: identity/base_side.json stores the GROUP but not the prompt text, because its
#: producer only ever ran the one sweep. The template is recorded here so the
#: tidy export carries the actual sentence rather than a group name a reader
#: would have to guess the frame for.
SOURCES = [
    ("institutional", "f21", "institutional/results/base_side/f21.json", None),
    ("institutional", "m03", "institutional/results/base_side/m03.json", None),
    ("institutional", "slotpov", "institutional/results/base_side/slotpov.json", None),
    ("identity", "room", "identity/results/base_side.json",
     "Three %(group)s came into the room and started to"),
    #: the v6-era file, kept because it is the only saved source for those scales
    ("sexual", "gender_pairs_v6", "sexual/results/gender_pairs.json", None),
]


#: the sexual v2 study stores its atomic levels ALREADY LONG, one row per
#: (prompt, lineage, arm, scale), so it is appended directly rather than melted.
LONG_SOURCES = [("sexual", "gender_pairs_v2", "sexual/results/levels_cells.json")]


def scales_of(row):
    return sorted({k[5:] for k in row if k.startswith("base_")}
                  & {k[8:] for k in row if k.startswith("aligned_")})


LONG_README = """# long/

Tidy exports, one row per observation. Written by `../tidy.py`. Gzipped;
`pandas.read_csv` opens them directly.

`levels_long.csv.gz` is the atomic table: a mass-weighted level for one
(study, corpus, prompt, lineage, arm, scale). **Every gap, delta and
difference-in-differences in the three READMEs derives from this table and from
nothing else**, so any of them can be recomputed or disputed without reading the
producers.

`cov` is the share of that arm's probability mass held by the rated words. A
level is only as good as its coverage, which runs from about 0.24 to 0.82 across
studies, so it belongs in an analysis rather than in a footnote.

`units_long.csv` is the design: which prompt sits in which matched set and cell,
and how many lineages cover it.

`words_long.csv.gz` is the rating layer: one row per (prompt, word, scale) with
the net movement across lineages.

Nothing is aggregated and no test is run in these files.

## The order of reduction matters, and the READMEs use one order

Every published figure averages **within a lineage first, then across lineages**.
A flat mean over all (prompt, lineage) rows is NOT the same number when prompts
have unequal lineage coverage: F21 `mediation` base for the individual position
is 2.87 the first way and 2.89 the second. Neither is wrong; they weight prompts
differently. Anyone reproducing a README figure should reduce in that order, and
anyone doing something else should say so.

## Which corpus is which

    f21, m03, slotpov     institutional, the three position corpora
    room                  identity, the "Three <group> came into the room" sweep
    gender_pairs_v2       sexual, the 8 gender pairs on sexual_slot_en_v2
                          -- this is the one the sexual README reports
    gender_pairs_v6       the earlier v6 pass over the same prompts, kept
                          because it is the only saved source for those scales
"""


def main():
    os.makedirs(OUT, exist_ok=True)
    #: GZIPPED. The uncompressed table is 199 MB because the prompt text and the
    #: lineage string repeat in all 716,406 rows. Compressed it is around 12 MB
    #: and `pandas.read_csv` opens it directly, so nothing is lost and the
    #: alternative -- integer keys plus lookup tables -- would cost a reader a
    #: join before they could see anything.
    lv = gzip.open(os.path.join(OUT, "levels_long.csv.gz"), "wt", newline="")
    lw = csv.writer(lv)
    lw.writerow(["study", "corpus", "prompt", "unit", "cell", "lineage",
                 "base_model", "aligned_model", "arm", "scale", "value", "cov"])
    un = open(os.path.join(OUT, "units_long.csv"), "w", newline="")
    uw = csv.writer(un)
    uw.writerow(["study", "corpus", "prompt", "unit", "cell", "n_lineages", "extra"])
    n_lv = n_un = 0
    for study, corpus, path, tmpl in SOURCES:
        p = os.path.join(HERE, path)
        if not os.path.exists(p):
            print("  MISSING %s" % path); continue
        rows = json.load(open(p))["rows"]
        seen = collections.defaultdict(set)
        for r in rows:
            if "prompt" not in r:
                if not tmpl:
                    raise SystemExit("%s has no `prompt` and no template" % path)
                r = dict(r, prompt=tmpl % r)
            unit = r.get("cluster") or r.get("pair") or r.get("group") or ""
            cell = (r.get("position") or r.get("gender") or r.get("group") or "")
            extra = {k: r[k] for k in ("stratum", "role", "domain", "sweep")
                     if r.get(k) is not None}
            lin = r["lineage"]
            b, a = (lin.split(" -> ") + [""])[:2]
            seen[(r["prompt"], unit, cell, json.dumps(extra, sort_keys=True))].add(lin)
            for s in scales_of(r):
                for arm, key in (("base", "base_" + s), ("aligned", "aligned_" + s)):
                    v = r.get(key)
                    if v is None:
                        continue
                    lw.writerow([study, corpus, r["prompt"], unit, cell, lin, b, a,
                                 arm, s, "%.6f" % v,
                                 "%.4f" % r["cov_%s_%s" % (arm, s)]
                                 if r.get("cov_%s_%s" % (arm, s)) is not None else ""])
                    n_lv += 1
        for (prompt, unit, cell, extra), lins in sorted(seen.items()):
            uw.writerow([study, corpus, prompt, unit, cell, len(lins), extra])
            n_un += 1
        print("  %-14s %-12s %6d rows -> %d level rows" % (study, corpus, len(rows), n_lv))
    for study, corpus, path in LONG_SOURCES:
        q = os.path.join(HERE, path)
        if not os.path.exists(q):
            print("  MISSING %s" % path); continue
        cells = json.load(open(q))["rows"]
        seen = collections.defaultdict(set)
        for r in cells:
            b, a = (r["lineage"].split(" -> ") + [""])[:2]
            lw.writerow([study, corpus, r["prompt"], r["pair"], r["gender"],
                         r["lineage"], b, a, r["arm"], r["scale"],
                         "%.6f" % r["value"],
                         "%.4f" % r["cov"] if r.get("cov") is not None else ""])
            n_lv += 1
            seen[(r["prompt"], r["pair"], r["gender"],
                  json.dumps({"role": r["role"]}))].add(r["lineage"])
        for (prompt, unit, cell, extra), lins in sorted(seen.items()):
            uw.writerow([study, corpus, prompt, unit, cell, len(lins), extra])
            n_un += 1
        print("  %-14s %-16s %6d cells" % (study, corpus, len(cells)))
    lv.close(); un.close()

    ww = csv.writer(gzip.open(os.path.join(OUT, "words_long.csv.gz"), "wt", newline=""))
    ww.writerow(["study", "instrument", "prompt", "word", "net", "rise", "fall",
                 "scale", "value"])
    n_w = 0
    for study, inst, path, key in [
            ("sexual", "sexual_slot_en_v2",
             "sexual/results/rated_gender_pairs_v2.json", "rows"),
            ("sexual", "sexual_slot_en_v2",
             "sexual/results/undressing_v2.json", "words")]:
        p = os.path.join(HERE, path)
        if not os.path.exists(p):
            continue
        for r in json.load(open(p))[key]:
            if not r.get("ratable", True):
                continue
            for k, v in r.items():
                if isinstance(v, int) and k not in ("net", "rise", "fall") \
                        and not isinstance(v, bool):
                    ww.writerow([study, inst, r["prompt"], r["word"], r.get("net", ""),
                                 r.get("rise", ""), r.get("fall", ""), k, v])
                    n_w += 1
    print("\n  levels_long.csv  %8d rows" % n_lv)
    print("  units_long.csv   %8d rows" % n_un)
    print("  words_long.csv.gz  %8d rows" % n_w)
    for f in ("levels_long.csv.gz", "units_long.csv", "words_long.csv.gz"):
        print("    %-18s %8.1f MB" % (f, os.path.getsize(os.path.join(OUT, f)) / 1e6))
    open(os.path.join(OUT, "README.md"), "w").write(LONG_README)
    print("\n-> results/long/")


if __name__ == "__main__":
    main()
