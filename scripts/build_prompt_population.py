#!/usr/bin/env python
"""The declared prompt set for the framed (prefill) measurement. Derived, not kept.

    python scripts/build_prompt_population.py
    python scripts/build_prompt_population.py --write

Writes `roster/prompts/populations/prefill.txt` (one prompt per line, the file a
fleet ships with `--prompts-file`) and `prefill.json` beside it carrying the
counts, the sources and the producer, so `check_record.py::derived_not_stale`
can tell when it has drifted.

## THE RULE IS `Prompts.framed_population()`. THIS ONLY SHIPS IT.

The union is defined once, in `prompts.py`, beside `all()` and `institutional()`
where a reader looking for a prompt population will find it. This script turns
it into the one-prompt-per-line file a fleet sends with `--prompts-file`, and
records the counts so drift is visible.

## WHY THIS IS NOT A FILE SOMEBODY SAVED

**THE CATALOGUE MOVES UNDER YOU.** `Prompts.all()` went 2,704 -> 2,983 in a
single day as slot prompts landed, and between scoping this set and building it
the entry count went 3,447 -> 3,110 while the distinct texts held at 2,983. A
prompt list saved once is a claim about a population that has since changed, and
nothing about the file would say so.

## THE UNION IS OVER DISTINCT STRINGS, WHICH IS NOT WHAT SUMMING GIVES

    F01       49      M03      252      PAIR105   210
    F21       51      SLOT     279      ------------------
                                        UNION     840

The parts sum to 841. **48 duplicate strings sit inside the slot corpus alone**
(327 entries, 279 texts), one inside F21, and one string is shared between F01
and SLOT. Summing the groups gives 890 and over-costs a fleet by 6%; summing
the DISTINCT parts gives 841 and is still wrong by one. Only the set union is
right, and it is taken over `.text`, because the corpus is keyed by the string.

Checked for near-duplicates differing only in case or whitespace: **zero**. That
mattered -- `"...took off her "` and `"...took off her"` would be two cells for
one prompt and neither would join the other's raw arm.

## ONE SOURCE IS IN THE ARCHIVE, AND THAT IS RECORDED RATHER THAN HIDDEN

The 105-pair transgressive sample lives at
`malign-logits/data/beam_sample_105.csv`, declared by a manifest carrying its
seed (20260805) and a membership sha. The archive is READ-ONLY and we read it;
the artifact this produces lives HERE, so the dependency is on a source we can
lose rather than on a file we cannot rebuild. If the archive goes, this file
still exists and the producer says exactly what it needed.
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

OUT_DIR = os.path.join(ROOT, "roster", "prompts", "populations")
TXT = os.path.join(OUT_DIR, "prefill.txt")
JSON_ = os.path.join(OUT_DIR, "prefill.json")
SOURCES = ["roster/prompts", "malign-logits/data/beam_sample_105.csv"]


def groups():
    """{name: set(text)} from `Prompts.framed_population()`.

    **THE RULE LIVES IN prompts.py AND THIS ONLY SHIPS IT.** The first version
    of this script had its own copy of the union, which is how the two would
    have disagreed the first time either was edited -- and the disagreement
    would be invisible, because both produce a plausible number of prompts.
    """
    from malignment.prompts import Prompts
    return OrderedDict(sorted(Prompts.framed_population().items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    gs = groups()
    if not gs["PAIR105"]:
        from malignment.prompts import PAIRS_CSV
        print("NOTE the archive pair sample is unreadable at %s -- the union "
              "below is 210 prompts short and must not be shipped as the "
              "declared set." % PAIRS_CSV)
    union = set().union(*gs.values())
    for k, v in gs.items():
        print("  %-9s %4d distinct" % (k, len(v)))
    print("  %-9s %4d   (parts sum to %d, so %d collapsed)"
          % ("UNION", len(union), sum(len(v) for v in gs.values()),
             sum(len(v) for v in gs.values()) - len(union)))

    #: A near-duplicate is TWO CELLS FOR ONE PROMPT, and neither joins the
    #: other's raw arm. Reported, never silently merged: which spelling is
    #: canonical is a judgement the catalogue owns, not this producer.
    norm = {}
    for t in union:
        norm.setdefault(" ".join(t.split()).strip().lower(), []).append(t)
    near = {k: v for k, v in norm.items() if len(v) > 1}
    print("  near-duplicates (case/whitespace only): %d" % len(near))
    for v in list(near.values())[:5]:
        print("     %r" % sorted(v))

    from malignment import corpus
    dm = corpus.domains()
    known = sum(1 for t in union if t in dm)
    print("  present in corpus.domains(): %d of %d" % (known, len(union)))

    if not a.write:
        print("\nDRY RUN -- pass --write.")
        return 0
    if not gs["PAIR105"]:
        raise SystemExit("refusing to write a short set")
    os.makedirs(OUT_DIR, exist_ok=True)
    #: Sorted, so a rebuild that changes nothing produces a byte-identical file
    #: and `git diff` means something.
    with open(TXT, "w") as fh:
        for t in sorted(union):
            #: A newline inside a prompt would silently become two prompts on
            #: the box. None today; refused rather than escaped, because a
            #: quietly-rewritten prompt is a different measurement.
            if "\n" in t or "\r" in t:
                raise SystemExit("prompt contains a newline and this format is "
                                 "one-per-line: %r" % t[:60])
            fh.write(t + "\n")
    json.dump(OrderedDict([
        ("_about", "The declared prompt set for the framed (prefill) "
                   "measurement. The .txt beside this is what a fleet ships "
                   "with --prompts-file."),
        ("_producer", "scripts/build_prompt_population.py"),
        ("_sources", SOURCES),
        ("n", len(union)),
        ("groups", OrderedDict((k, len(v)) for k, v in gs.items())),
        ("collapsed", sum(len(v) for v in gs.values()) - len(union)),
        ("near_duplicates", len(near)),
        ("in_corpus_domains", known),
    ]), open(JSON_, "w"), indent=1)
    open(JSON_, "a").write("\n")
    print("\nwrote %s (%d prompts)" % (TXT, len(union)))
    print("      %s" % JSON_)
    return 0


if __name__ == "__main__":
    sys.exit(main())
