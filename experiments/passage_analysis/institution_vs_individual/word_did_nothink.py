"""word_did's table on the thinking-off rows, booked BESIDE results/word_did.md.

    python -u word_did_nothink.py     -> results/word_did_nothink.md

`thinking_off.md` (f4150fe0) replaced the aligned chat cells of Qwen3-8B,
SmolLM3-3B and MiniCPM5-1B in coded_regen.jsonl. results/word_did.md (malign's)
was computed on the old rows, so plate A3's booked-table assert refuses against
the current data, correctly. This runs malign's `word_did.main()` UNEDITED, with
its module-level output directory pointed at a scratch folder, and copies the
table in under a new name, so word_did.md stays as booked and the redrawn plate
(`plot.py split_nothink`) has a table to assert against. When malign regenerates
word_did.md on the current rows it should equal this file byte for byte.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import word_did as W  # noqa: E402

OUT = os.path.join(HERE, "results", "word_did_nothink.md")


def main():
    assert not os.path.exists(OUT), "refusing to overwrite %s" % OUT
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "results"))
        W.HERE = tmp
        W.main()
        shutil.copyfile(os.path.join(tmp, "results", "word_did.md"), OUT)
    print("   ->", os.path.relpath(OUT, HERE))


if __name__ == "__main__":
    main()
