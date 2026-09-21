"""Every prompt where `kill` is the biggest faller in a CROSSED pair, on all eight ladders.

    python -u sweep.py                 # -> results/kill_ladder_sweep.csv + a report
    python -u sweep.py --tables 3      # also print full stage tables for the first 3

Asked by the paper seat: does the SFT->DPO crossing seen on the Figure 2 prompt
survive more than one prompt? The answer decides whether the article gets a
stage figure with a named ladder or keeps the chain as a sentence.

## THE PROMPT LIST IS THE AVERAGED CORPUS'S, THE LADDERS ARE NOT

`faller` and `riser` come from `substitution_shape`, which averages fifty
lineages and then picks. The eight ladders are a DIFFERENT population -- eight
roots, not fifty endpoints -- so this asks whether each ladder reproduces a
pair the averaged corpus named. It is not a within-population test and a
ladder that fails is not thereby anomalous.

**AND THE SEVEN `scream` PROMPTS ARE NEAR-PARAPHRASES OF ONE FRAME** ("she was
so angry she wanted to", "my rage grew until I wanted to", ...). Seven
agreements among them are close to one agreement, and the roll-up says so.

## CLASSES

    displace     faller falls, riser rises, and the lines CROSS by the last
                 stage (riser above faller at the end, below it at the start)
    partial      both move the right way but never cross
    suppress     faller falls and the riser does not rise
    collapse     BOTH fall -- the candidate set is draining, not trading
    already      riser was at or above the faller in the base: no crossing
                 was available, so the ladder cannot be scored for one

An absent word is BELOW THETA, not zero: `twp` stores nothing under 0.001, so
it is treated as 0.0005 for ordering and marked `<t` in the tables.
"""
import argparse, collections, csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import run as R  # noqa: E402

THETA = 0.001
SUB = os.path.join(ROOT, "experiments", "displacement", "substitution_shape",
                   "results", "by_prompt_raw.csv")


def kill_prompts():
    """-> [(prompt, faller, riser)] where kill is the CROSSED biggest faller."""
    with open(SUB, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh)
                if r["crossing"] == "CROSSED" and r["faller"] == "kill"]
    #: scream first, then the rest, as asked
    rows.sort(key=lambda r: (r["riser"] != "scream", r["prompt"]))
    return [(r["prompt"], r["faller"], r["riser"]) for r in rows]


def classify(pf, pr):
    """-> (class, cross_stage_index or None, riser's largest-step index)"""
    v = lambda x: THETA / 2 if x is None else x
    bf, br, ff, fr = v(pf[0]), v(pr[0]), v(pf[-1]), v(pr[-1])
    cross = next((i for i in range(len(pf)) if v(pr[i]) > v(pf[i])), None)
    d = [v(pr[i + 1]) - v(pr[i]) for i in range(len(pr) - 1)]
    big = max(range(len(d)), key=lambda i: d[i]) if d else None
    if br >= bf:
        return "already", cross, big
    fell, rose = ff < bf, fr > br
    if fell and rose and fr > ff:
        return "displace", cross, big
    if fell and rose:
        return "partial", cross, big
    if fell and not rose:
        return "suppress", cross, big
    if not fell and not rose:
        return "collapse", cross, big
    return "other", cross, big


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tables", type=int, default=0)
    a = ap.parse_args(argv)

    prompts = kill_prompts()
    print("%d prompts where `kill` is the CROSSED biggest faller "
          "(%d of them to `scream`, near-paraphrases of one frame)\n"
          % (len(prompts), sum(1 for _, _, r in prompts if r == "scream")))

    out, byladder = [], collections.defaultdict(collections.Counter)
    stage_of = collections.defaultdict(collections.Counter)
    for pi, (p, f, r) in enumerate(prompts):
        line = []
        for name in sorted(R.LADDERS):
            labs, rows, _ = R.table(p, R.LADDERS[name], words=[f, r])
            if not labs:
                line.append((name, "nodata", None, None, labs))
                continue
            cls, cross, big = classify(rows[f], rows[r])
            line.append((name, cls, cross, big, labs))
            byladder[name][cls] += 1
            if cls == "displace":
                stage_of["cross"][labs[cross] if cross is not None else "?"] += 1
                stage_of["riser_step"][
                    "%s->%s" % (labs[big], labs[big + 1])] += 1
            out.append({"prompt": p, "faller": f, "riser": r, "ladder": name,
                        "class": cls,
                        "cross_at": labs[cross] if cross is not None else "",
                        "riser_biggest_step":
                            "%s->%s" % (labs[big], labs[big + 1]) if big is not None else "",
                        "stages": "|".join(labs),
                        "p_faller": "|".join("" if x is None else "%.4f" % x
                                             for x in rows[f]),
                        "p_riser": "|".join("" if x is None else "%.4f" % x
                                            for x in rows[r])})
        print("kill -> %-10s  %s" % (r, p[:62]))
        print("   " + "  ".join("%s=%s" % (n.split("_")[0][:6], c)
                                for n, c, _, _, _ in line))
        if pi < a.tables:
            for name in sorted(R.LADDERS):
                labs, rows, _ = R.table(p, R.LADDERS[name], top=5)
                if not labs:
                    continue
                al, arows, _ = R.table(p, R.LADDERS[name][-1:], top=5)
                ws = list(dict.fromkeys(list(rows) + list(arows)))
                labs, rows, _ = R.table(p, R.LADDERS[name], words=ws)
                print("     %-16s %s" % (name, "".join("%9s" % l for l in labs)))
                for w in ws:
                    print("       %-14s %s" % (w, "".join(
                        "%9s" % ("<t" if x is None else "%.4f" % x)
                        for x in rows[w])))
        print()

    cp = os.path.join(HERE, "results", "kill_ladder_sweep.csv")
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    with open(cp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print("wrote %s  (%d rows)\n" % (cp, len(out)))

    print("PER LADDER, over %d prompts" % len(prompts))
    print("  %-18s %9s %8s %9s %9s %8s"
          % ("ladder", "displace", "partial", "suppress", "collapse", "already"))
    for name in sorted(R.LADDERS):
        c = byladder[name]
        print("  %-18s %9d %8d %9d %9d %8d"
              % (name, c["displace"], c["partial"], c["suppress"],
                 c["collapse"], c["already"]))
    print("\n  ladders displacing on the MEDIAN prompt: %d of %d"
          % (sum(1 for n in R.LADDERS
                 if byladder[n]["displace"] > len(prompts) / 2), len(R.LADDERS)))
    print("\nWHERE THE LINES CROSS, on the displacing cases: %s"
          % dict(stage_of["cross"]))
    print("THE RISER'S LARGEST STEP, on the displacing cases: %s"
          % dict(stage_of["riser_step"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
