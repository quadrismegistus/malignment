"""Does TRANSGRESSIVE MASS IN THE BASE ARM predict what alignment changes?

    python -u dose.py                    # levels and fields, both languages
    python -u dose.py --lang en --top 25

## THE DESIGN, AND WHY IT DOES NOT SELECT ON THE OUTCOME

The predictor is the BASE arm's transgressive mass at a prompt, measured before
alignment touches anything. The outcome is how far some other scale moves,
`aligned - base`. A prompt heavy in transgressive mass could, from there, show a
rise, a fall or nothing on any given scale with equal ease -- the predictor
carries no information about the direction of the outcome, which is what makes
this a dose-response rather than a selection.

That distinction matters here because the alternative is exactly the trap this
campaign keeps booking: conditioning on words that MOVED, and then reporting
that moved words moved.

## WHY IT WAS ASKED FOR

The field table says speech mass FALLS under alignment. Restricted to movers,
speech words are net RISERS (+3272 mass, 418,323 riser rows against 379,653
faller rows) -- which is M01's kill->scream direction and the opposite reading.
Both are true and they are different quantities: a normalised SHARE of rated
mass can fall while absolute mass rises, if the denominator grows.

So the interesting question is not which way a field goes on average. It is
whether the frames carrying transgressive mass are the ones where a field like
speech moves at all. That is a slope, not a mean.

## THE STATISTIC

Per lineage, over its prompts:

    x  base-arm level of the DOSE scale (k_transgressiveness by default)
    y  aligned - base on the TARGET scale

an ordinary least-squares slope of y on x. Then the sign test over lineages,
the same unit every other test in this folder uses. A lineage needs MIN_PROMPTS
prompts with both x and y present, or it does not contribute -- a slope from
three points is not evidence and averaging it in as one would let the thinnest
lineages vote loudest.
"""

import argparse, collections, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
DATA = os.path.expanduser("~/malignment-data/norm_change")

MIN_PROMPTS = 25
DOSE_DEFAULT = "k_transgressiveness"


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def read(name, keep=None):
    """{(lang, lineage, prompt, scale): (base, aligned)}, streamed."""
    p = os.path.join(DATA, "%s_long.csv.gz" % name)
    if not os.path.exists(p):
        return None
    out = {}
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head):
                continue
            sc = v[ix["scale"]]
            if keep and sc not in keep:
                continue
            b, a = v[ix["base_level"]], v[ix["aligned_level"]]
            if not b or not a or b == "\\N" or a == "\\N":
                continue
            try:
                out[(v[ix["lang"]], v[ix["base"]] + ">" + v[ix["aligned"]],
                     v[ix["prompt"]], sc)] = (float(b), float(a))
            except ValueError:
                continue
    return out


def slope(xs, ys):
    """OLS slope, or None when x has no variance."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def index_by_scale(tbl, lang):
    """{scale: {(lineage, prompt): (base, aligned)}}, built ONCE.

    The first version rescanned the whole table for every target, which on the
    28M-row fields table is 232 full passes and does not finish. Indexing once
    turns the sweep from O(scales x rows) into O(rows + scales x prompts).
    """
    idx = collections.defaultdict(dict)
    for (lg, lin, pr, sc), v in tbl.items():
        if lg == lang:
            idx[sc][(lin, pr)] = v
    return idx


def dose_response(idx, dose_scale, target_scale):
    """{lineage: slope of (aligned-base on target) on (base level of dose)}."""
    by = collections.defaultdict(lambda: ([], []))
    doses = {k: v[0] for k, v in idx.get(dose_scale, {}).items()}
    for (lin, pr), (b, a) in idx.get(target_scale, {}).items():
        d = doses.get((lin, pr))
        if d is None:
            continue
        by[lin][0].append(d)
        by[lin][1].append(a - b)
    out = {}
    for lin, (xs, ys) in by.items():
        if len(xs) < MIN_PROMPTS:
            continue
        s = slope(xs, ys)
        if s is not None:
            out[lin] = s
    return out


def report(target, sl):
    import statistics as st
    v = list(sl.values())
    n = len(v)
    up = sum(1 for x in v if x > 0)
    dn = sum(1 for x in v if x < 0)
    if up + dn < 3:
        return None
    p = binom(up, up + dn)
    med = st.median(v)
    return (p, target, med, up, dn, n)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--dose", default=DOSE_DEFAULT)
    ap.add_argument("--table", default="both", choices=("levels", "fields", "both"))
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args(argv)

    langs = [a.lang] if a.lang else ["en", "zh"]
    tables = ["levels", "fields"] if a.table == "both" else [a.table]

    print("DOSE-RESPONSE: does base-arm %s predict what alignment changes?" % a.dose)
    print("unit = the lineage; slope of (aligned-base) on base dose, across prompts")
    print("min %d prompts per lineage" % MIN_PROMPTS)

    lv = read("levels")
    if lv is None:
        print("no levels_long -- run.py --run first")
        return 1
    #: the dose ALWAYS comes from levels, even when the target is a field --
    #: transgressiveness is a continuous norm and has no field counterpart.
    dose_rows = {k: v for k, v in lv.items() if k[3] == a.dose}
    if not dose_rows:
        print("dose scale %r not present in levels_long" % a.dose)
        return 1

    for name in tables:
        tbl = lv if name == "levels" else read("fields")
        if tbl is None:
            continue
        if name == "fields":
            tbl = dict(tbl)
            tbl.update(dose_rows)
        for lang in langs:
            idx = index_by_scale(tbl, lang)
            scales = sorted(set(idx) - {a.dose})
            rows = []
            for sc in scales:
                sl = dose_response(idx, a.dose, sc)
                r = report(sc, sl)
                if r:
                    rows.append(r)
            rows.sort()
            print()
            print("=" * 78)
            print("%s / %s  --  %d targets tested, %d significant"
                  % (lang.upper(), name, len(rows), sum(1 for r in rows if r[0] < 0.05)))
            print("=" * 78)
            print("  %-34s %11s %5s %5s %5s %9s" % ("target", "med slope", "up", "dn", "n", "p"))
            for p, sc, med, up, dn, n in rows[:a.top]:
                mark = "  <-" if p < 0.05 else ""
                print("  %-34s %+11.5f %5d %5d %5d %9.5f%s"
                      % (sc[:34], med, up, dn, n, p, mark))
    print()
    print("A POSITIVE slope means: the more transgressive mass the BASE arm put")
    print("at a prompt, the MORE that target rose under alignment. The dose is")
    print("measured before alignment and does not select on the outcome.")
    print()
    print("EXPLORATORY. Nothing here was registered; every row is a candidate")
    print("for a hypothesis, not a result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
