"""Rebuild pos_{en,zh}.csv.gz cleanly from the files, deduped and normalised.

The tables were damaged by the resume, in two ways that are worth recording
because both were invisible in the file's own totals:

  EN   the resumed run re-wrote every row it read from the stash cache, appending
       them on top of run 1's rows: ~1.02M duplicates on a 2.99M-row file. Correct
       data, doubled over the resumed span.
  ZH   run 1 died during English and never touched pos_zh.csv.gz, so the file was
       still the SMOKE TEST's 3-column version (prompt, word, pos) written before
       the `lang` column existed. The resume appended 4-column rows to it, and
       csv.DictReader takes line 1 as the header -- so every real row misparsed
       and `row["pos"]` returned the WORD. A recount said 1% VERB against the
       run's own 406,294.

Neither showed up as a read error. The tell was the file totals disagreeing with
what the run printed, which is why the recount was worth doing at all.

Rows are read positionally, normalised to (lang, prompt, word, pos), and deduped
on (prompt, word) keeping the LAST occurrence. The stash is unaffected -- it is
keyed, so the duplicate writes were idempotent.
"""
import csv, gzip, os, sys, collections, re

D = os.path.expanduser("~/malignment-data/contextual_norms")
CJK = re.compile(r"[一-鿿]")
POS = {"ADJ","ADP","ADV","AUX","CCONJ","DET","INTJ","NOUN","NUM","PART","PRON",
       "PROPN","PUNCT","SCONJ","SYM","VERB","X","SPACE"}

for lang in ("en", "zh"):
    src = os.path.join(D, "pos_%s.csv.gz" % lang)
    if not os.path.exists(src):
        continue
    keep, bad, seen3, seen4 = {}, 0, 0, 0
    with gzip.open(src, "rt", encoding="utf-8", newline="") as fh:
        for v in csv.reader(fh, delimiter="\t"):
            if not v or v[-1] == "pos":       # any header line, old or new
                continue
            #: POSITIONAL, and the POS tag is validated against the UPOS set --
            #: a 3-column row read as 4 (or vice versa) puts a WORD where a tag
            #: belongs, which is exactly how the zh file read as 1% VERB.
            if len(v) == 4 and v[3] in POS:
                lg, p, w, t = v; seen4 += 1
            elif len(v) == 3 and v[2] in POS:
                p, w, t = v; lg = lang; seen3 += 1
            else:
                bad += 1
                continue
            keep[(p, w)] = (lg, p, w, t)
    out = os.path.join(D, "pos_%s.clean.csv.gz" % lang)
    with gzip.open(out, "wt", encoding="utf-8", newline="") as fh:
        w_ = csv.writer(fh, delimiter="\t")
        w_.writerow(["lang", "prompt", "word", "pos"])
        for row in keep.values():
            w_.writerow(row)
    c = collections.Counter(r[3] for r in keep.values())
    content = sum(n for k, n in c.items() if k in ("NOUN","VERB","ADJ","ADV","PROPN"))
    print("%s: %d unique pairs (4col %d, 3col %d, unparseable %d)"
          % (lang, len(keep), seen4, seen3, bad))
    print("    VERB %d (%.0f%%) | content %d (%.0f%%) | PUNCT %d | NUM %d -> %s"
          % (c["VERB"], 100*c["VERB"]/len(keep), content, 100*content/len(keep),
             c["PUNCT"], c["NUM"], os.path.basename(out)))
