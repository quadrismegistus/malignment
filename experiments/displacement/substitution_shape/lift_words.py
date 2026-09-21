"""Rank substitution_shape's words by their own charge lift. -> results/words_by_lift.csv

    python -u lift_words.py
    python -u lift_words.py --min-prompts 3 --top 40

`charge.word_lift(prompt, base)` is a word's rating over the frame's own, per
lineage. **AGGREGATING IT TAKES TWO DECISIONS AND THIS FILE MAKES BOTH VISIBLE
RATHER THAN CHOOSING**: within a prompt, over the lineages that offered the
word; then across the prompts the word appears in. Both stages are emitted with
median and mean, so `lift_med_max` is "median over lineages, then the largest
such prompt" and `lift_mean_med` is "mean over lineages, then the typical
prompt". They disagree and the disagreement is informative.

## THE POPULATION IS THIS FOLDER'S WORDS AND THIS FOLDER'S PROMPTS

Words: every faller and riser in `by_prompt_{raw,framed}.csv`, across ALL four
crossing classes -- those columns are populated whether or not the lines cross,
so restricting to CROSSED would silently answer a narrower question.

Prompts: the 2,400 this folder measured, not every prompt `charge` has rated. A
word's lift is then comparable to its behaviour here; mixing in prompts the
substitution run never saw would put two populations in one row.

## A HIGH LIFT IS NOT A LARGE MOVEMENT

Lift is a property of the WORD AND ITS SETUP, measured on the base arm's
candidates before alignment touches anything. It says the word is more
transgressive than the frame that set it up, not that alignment did anything
about it. `n_faller` / `n_riser` are in the file so the two can be read
together rather than conflated.
"""
import argparse, collections, csv, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

ARMS = ("raw", "framed")


def roles():
    """-> ({word: Counter(role)}, {prompt: True}) over both arms, all classes."""
    role = collections.defaultdict(collections.Counter)
    prompts = {}
    for arm in ARMS:
        p = os.path.join(HERE, "results", "by_prompt_%s.csv" % arm)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding="utf-8")):
            prompts[r["prompt"]] = True
            for k in ("faller", "riser"):
                if r[k]:
                    role[r[k]][k] += 1
                    if r["crossing"] == "CROSSED":
                        role[r[k]]["crossed_" + k] += 1
    return role, prompts


def per_prompt(prompts):
    """-> {word: [(prompt, med_lift, mean_lift, n_carriers)]}

    One pass over the prompts, not one per word: `word_lifts` reads a cell per
    lineage, so asking it per word would reread the same 50 cells 48 times.
    """
    from malignment import charge
    out = collections.defaultdict(list)
    done = miss = 0
    for p in prompts:
        acc = collections.defaultdict(list)
        for b in charge.bases(p):
            for w, L in charge.word_lift(p, b).items():
                acc[w].append(L)
        if not acc:
            miss += 1
            continue
        done += 1
        for w, v in acc.items():
            out[w].append((p, st.median(v), st.fmean(v), len(v)))
    print("  %d prompts carried charge ratings, %d did not" % (done, miss))
    return out


def bands(rows, min_prompts=10):
    """Does a word's own lift predict whether alignment REMOVES it? -> prints

    The role counts are already in the file, so this costs nothing and answers
    the question the file exists to raise. Restricted to words seen in at least
    `min_prompts` prompts: a word rated once has a median that is one cell.
    """
    v = [r for r in rows if r["n_prompts"] >= min_prompts]
    def band(L):
        for lo, name in ((3, ">= 3"), (2, "2 to 3"), (1, "1 to 2"),
                         (0, "0 to 1")):
            if L >= lo:
                return name
        return "< 0"
    g = collections.defaultdict(list)
    for r in v:
        g[band(r["lift_med_med"])].append(r)
    print("\n  WHO FALLS, BY THE WORD'S OWN LIFT (%d words in >= %d prompts)"
          % (len(v), min_prompts))
    print("  %-10s %6s %8s %8s %11s" % ("lift", "words", "faller", "riser",
                                        "faller share"))
    for k in (">= 3", "2 to 3", "1 to 2", "0 to 1", "< 0"):
        b = g.get(k)
        if not b:
            continue
        F = sum(r["n_faller"] for r in b)
        S = sum(r["n_riser"] for r in b)
        print("  %-10s %6d %8d %8d %10.0f%%"
              % (k, len(b), F, S, 100.0 * F / max(1, F + S)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-prompts", type=int, default=1,
                    help="drop words appearing in fewer prompts than this")
    ap.add_argument("--top", type=int, default=25, help="how many to print")
    a = ap.parse_args(argv)

    role, prompts = roles()
    print("%d words appear as a faller or riser; %d prompts in this folder"
          % (len(role), len(prompts)))
    byw = per_prompt(prompts)

    rows = []
    for w, rc in role.items():
        v = byw.get(w)
        if not v or len(v) < a.min_prompts:
            continue
        med = [x[1] for x in v]
        mean = [x[2] for x in v]
        hi = max(v, key=lambda x: x[1])
        rows.append({
            "word": w, "n_prompts": len(v),
            "lift_med_med": round(st.median(med), 4),
            "lift_med_mean": round(st.fmean(med), 4),
            "lift_med_max": round(max(med), 4),
            "lift_mean_med": round(st.median(mean), 4),
            "lift_mean_mean": round(st.fmean(mean), 4),
            "lift_mean_max": round(max(mean), 4),
            "carriers_median": int(st.median([x[3] for x in v])),
            "n_faller": rc["faller"], "n_riser": rc["riser"],
            "n_crossed_faller": rc["crossed_faller"],
            "n_crossed_riser": rc["crossed_riser"],
            "prompt_at_max": hi[0][:90].replace("\n", " "),
        })
    #: **SORTED ON THE TWO-MEDIAN COLUMN**, the most conservative of the six:
    #: median over lineages, median over prompts. A max-of-max ordering is a
    #: ranking of single cells and would put a word rated once at the top.
    rows.sort(key=lambda r: (-r["lift_med_med"], -r["n_prompts"], r["word"]))

    out = os.path.join(HERE, "results", "words_by_lift.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    print("  wrote %s  (%d words)" % (out, len(rows)))

    bands(rows)
    print("\n  %-14s %6s %8s %8s %8s %6s %6s" % (
        "word", "n_pr", "med/med", "mean/med", "med/max", "fall", "rise"))
    for r in rows[:a.top]:
        print("  %-14s %6d %+8.3f %+8.3f %+8.3f %6d %6d"
              % (r["word"], r["n_prompts"], r["lift_med_med"],
                 r["lift_mean_med"], r["lift_med_max"],
                 r["n_faller"], r["n_riser"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
