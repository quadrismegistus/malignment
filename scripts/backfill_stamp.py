#!/usr/bin/env python
"""Copy the instrument fields from each record's `__key__` into its BODY.

    python scripts/backfill_stamp.py --dry
    python scripts/backfill_stamp.py --model Qwen/Qwen2.5-7B

**THE KEY HOLDS THE TRUTH; THE BODY WAS HALF-WRITTEN.** `run_v4.py` built a stamp
carrying `rules`/`prompt_cache` and then became a thin wrapper around `Runner`,
whose stamp did not know them -- so 21,661 cells across 8 models are correctly
KEYED and carry `rules: None` in the body. `ingest._key_body_agree` refuses them,
correctly, and `twp_cells_v4` puts `rules` in its SORTING KEY, so they would
otherwise have filed under an empty string.

This is the one case where rewriting a body is justified: the key is the
producer's own claim about the instrument, not an inference, so the repair is
deterministic and adds no information. It REFUSES to touch anything else.

**ORDER IS LOAD-BEARING AND IS PRESERVED BY CONSTRUCTION.** The stash files are
APPEND-ONLY: a delete leaves the record in place and a rewrite supersedes it, so
`ingest` resolves a repeated key by LAST WRITE WINS. This script makes a single
pass and appends every line -- modified or not -- in sequence, which is the only
reason it is safe to run over a file whose earlier records were superseded.

That is not hypothetical. Run over CT-LLM-Base it "fixed" 2,583 records that
were the CONTAMINATED topup cells, deleted from the stash hours earlier but
still present in the file. Had it reordered, those would have moved after their
corrected replacements and the next ingest would have booked the bad ones -- with
no error, and with a cell count that still looked right. Do not add sorting,
grouping, or dict-based accumulation here.

**Atomic per file**: writes a sibling and renames, so a kill leaves the original
intact rather than a half-file. Never run against a stash a producer is writing.
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from malignment.ingest import INSTRUMENT_FIELDS  # noqa: E402

CORPUS = os.environ.get("MALIGNMENT_CORPUS", os.path.expanduser("~/malignment-data"))


def repair(path, dry=True):
    fixed = kept = 0
    out = []
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except Exception:                                       # noqa: BLE001
            out.append(line.rstrip("\n"))
            kept += 1
            continue
        key = d.get("__key__")
        if isinstance(key, dict):
            bad = {f: key[f] for f in INSTRUMENT_FIELDS
                   if f in key and d.get(f) != key.get(f)}
            if bad:
                d.update(bad)
                fixed += 1
                out.append(json.dumps(d, ensure_ascii=False))
                continue
        kept += 1
        out.append(line.rstrip("\n"))
    if fixed and not dry:
        tmp = path + ".backfill"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out) + "\n")
        os.replace(tmp, path)
    return fixed, kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="append")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    pats = ([os.path.join(CORPUS, "twp", m.replace("/", "__"), "*", "jsonl.hashstash.raw", "data.jsonl")
             for m in a.model] if a.model else
            [os.path.join(CORPUS, "twp", "*", "*", "jsonl.hashstash.raw", "data.jsonl")])
    tot = 0
    for pat in pats:
        for f in sorted(glob.glob(pat)):
            n, kept = repair(f, dry=a.dry)
            if n:
                tot += n
                print("  %-46s %6d fixed / %6d kept%s"
                      % (f.split("/twp/")[1].split("/")[0][:46], n, kept,
                         "  (dry)" if a.dry else ""))
    print("%s %d records" % ("would fix" if a.dry else "FIXED", tot))


if __name__ == "__main__":
    sys.exit(main())
