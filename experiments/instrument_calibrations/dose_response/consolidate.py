"""Fold the per-prompt tag files into one table. That table is the artifact.

The per-prompt JSONs are gitignored: `Task` already caches every call, so they were
never needed for resumability, and 2,578 tiny files is not a deliverable. This
writes `tags.csv.gz` -- one row per (prompt, word) -- plus a per-prompt summary,
and both are small enough to commit.
"""
import csv, glob, gzip, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")

rows, summ, off = [], [], 0
for f in sorted(glob.glob(os.path.join(OUT, "tag_*.json"))):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    off += len(d.get("off_list") or [])
    summ.append((d["prompt"], int(bool(d.get("any_loaded"))), len(d.get("words") or []),
                 d.get("n_candidates", 0), (d.get("axis") or "").replace("\t", " ")))
    for w in d.get("words") or []:
        rows.append((d["prompt"], w))
with gzip.open(os.path.join(HERE, "tags.csv.gz"), "wt", encoding="utf-8", newline="") as fh:
    w_ = csv.writer(fh, delimiter="\t"); w_.writerow(["prompt", "word"]); w_.writerows(rows)
with gzip.open(os.path.join(HERE, "tags_summary.csv.gz"), "wt", encoding="utf-8", newline="") as fh:
    w_ = csv.writer(fh, delimiter="\t")
    w_.writerow(["prompt", "any_loaded", "n_words", "n_candidates", "axis"])
    w_.writerows(summ)
print("prompts %d | tagged (prompt,word) rows %d | off-list discarded %d"
      % (len(summ), len(rows), off))
print("-> tags.csv.gz, tags_summary.csv.gz")
