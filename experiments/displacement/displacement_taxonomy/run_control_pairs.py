"""Prepare a blind crosslineage task for every arm of the chosen control pairs.

    python run_control_pairs.py --pairs results/control_pairs_8.json

Reads the pair file `pick_controls.py --emit` writes and prepares BOTH arms of
each pair, so the site and its control are read by the same instrument at the
same settings and differ only in the swapped word.

## WHY THE PROMPTS COME FROM A FILE

`--pick`'s table truncates prompts at 52 characters and most of the qualifying
pairs are longer than that, so a runner that took its prompts off the display
would prepare a different sentence and succeed while doing it. The pair file
carries the full text; nothing here retypes a prompt.

## WHY `--no-blanks` ON ALL OF THEM

The swap frames carry almost no underscore mass -- 0 to 4 rows against 152 on
`She was so angry she wanted to` -- so stripping is nearly a no-op here. It is
applied anyway because it decides the VERSION: a stripped reading records as
`x1bn` and cannot pool with `x1b`, and the five frames already read on this
design are stripped. Mixing would make the comparison the pairs exist for
unavailable, for a difference of four rows.

## IT REFUSES RATHER THAN SKIPPING

A prompt with no topped-up lineage pair raises out of `crosslineage.tables`, and
that aborts the whole batch instead of quietly preparing fifteen. Half a matched
design is not a smaller version of the design; it is an unmatched one, and the
gap would only be visible to someone counting workflow files.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/rj416/github/malignment")
import crosslineage as X  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pairs", default=os.path.join(HERE, "results", "control_pairs_8.json"))
    ap.add_argument("--raters", type=int, default=2)
    a = ap.parse_args()
    pairs = json.load(open(a.pairs))
    todo = []
    for p in pairs:
        todo.append(("SITE", p["site"], p["site_mean"]))
        todo.append(("CONTROL", p["control"], p["ctrl_worst"]))
    print("%d prompt(s) from %d pair(s), %d rater(s) each -- %d agents\n"
          % (len(todo), len(pairs), a.raters, len(todo) * a.raters))
    rows = []
    for role, text, mass in todo:
        X.prepare(text, raters=a.raters, blind=True, no_blanks=True)
        slug = X.re.sub(r"[^a-z0-9]+", "_", text.lower())[:40].strip("_") + "_nb_blind"
        wf = os.path.join(HERE, "workflow_xling_%s.js" % slug)
        if not os.path.exists(wf):
            raise SystemExit("prepare wrote no workflow for %r (expected %s)" % (text, wf))
        rows.append((role, mass, slug, text))
        print()
    out = os.path.join(HERE, "results", "control_pairs_8_slugs.tsv")
    with open(out, "w") as f:
        f.write("role\tmass\tslug\tprompt\n")
        for role, mass, slug, text in rows:
            f.write("%s\t%.4f\t%s\t%s\n" % (role, mass, slug, text))
    print("\n%d workflow(s) written. Slug map: %s" % (len(rows), out))
    for role, mass, slug, _ in rows:
        print("  %-8s %6.2f%%  workflow_xling_%s.js" % (role, 100 * mass, slug))


if __name__ == "__main__":
    main()
