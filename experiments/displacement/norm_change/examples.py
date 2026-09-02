"""Show the WORDS behind a dose-only effect, at a real transgressive prompt.

    python -u examples.py --scale k_concreteness --lang en
    python -u examples.py --scale concreteness_zh --lang zh
    python -u examples.py --usas Q2.2 --lang en

A slope over 50 lineages says a scale moves where the frame is loaded. It does
not say WHICH WORDS carry it, and a table of slopes cannot be checked by
reading. This prints the prompt, its base-arm transgressive level, and the words
whose movement contributes most to the scale's change in that arm.

## THE PROMPT IS CHOSEN BY DOSE, NOT BY OUTCOME

Prompts are ranked by BASE-arm `k_transgressiveness` and one is taken from the
top decile. The selection therefore knows nothing about how the target scale
moved -- which is the same discipline `dose.py` rests on, and the reason an
example here is an illustration of the effect rather than a specimen chosen to
show it. `--rank` walks down the ranked list rather than always taking the
extreme, because the single most transgressive prompt in a corpus is usually
also its strangest.

## CONTRIBUTION, NOT MOVEMENT

A word is ranked by `(p_aligned - p_base) * value`, its signed contribution to
the mass-weighted mean, NOT by how far it moved. A large mover with a
middling rating changes the mean less than a small mover at the extreme, and it
is the mean the hypothesis is about.
"""

import argparse, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)

#: the DEFAULT dose. `--dose` overrides it, because the two doses this campaign
#: uses do not live in the same place and rank prompts differently:
#:
#:   k_transgressiveness   a per-PROMPT level, read from levels_long.csv.gz
#:   lift                  T_base - frame, per (prompt, LINEAGE), from
#:                         charge.lifts_per_lineage(). English only -- charge
#:                         ratings cover 2,400 English prompts.
#:
#: `dose.py` records why the second exists: lift predicts displacement 3x better
#: than the level (r=-0.261 against -0.091) because the level SATURATES above
#: frame 5. So the top decile by level and the top decile by lift are not the
#: same prompts, and an example drawn from one is not an example of the other.
DOSE = "k_transgressiveness"


def _q(v):
    return "'" + str(v).replace("'", "''") + "'"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", default=None, help="a continuous norm scale")
    ap.add_argument("--usas", default=None, help="a USAS field code instead")
    ap.add_argument("--lang", default="en", choices=("en", "zh"))
    ap.add_argument("--rank", type=int, default=0, help="which top-dose prompt")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--dose", default=DOSE,
                    help="scale used to RANK prompts. Any scale in "
                         "levels_long, or 'lift' for the per-lineage lift dose "
                         "(en only).")
    a = ap.parse_args(argv)
    if not (a.scale or a.usas):
        ap.print_help()
        return 0

    from malignment import ch, fields as F
    from analyse import endpoint_pairs
    import re
    CJK = re.compile(r"[一-鿿]")
    EP = endpoint_pairs()

    #: value per word for the target, in this language
    def value_of(w):
        lg = "zh" if CJK.search(w) else "en"
        if a.usas:
            raw = F.usas(w, names=False, lang=lg)
            codes = [F._zh_tag_base(p) if lg == "zh" else p
                     for c in raw for p in str(c).split("/")]
            codes = [c for c in codes if c]
            if not codes:
                return None
            return sum(1.0 for c in codes if c == a.usas) / len(codes)
        n = F.norms_zh([w]) if lg == "zh" else F.norms(w)
        v = n.get(a.scale)
        return float(v) if isinstance(v, (int, float)) else None

    #: RANK PROMPTS FROM levels_long, NOT by querying per prompt. The first
    #: version issued one ClickHouse query per prompt over ~4,000 prompts and
    #: did not finish. The dose is already computed and stored -- the base_level
    #: of k_transgressiveness per (lineage, prompt) -- so ranking is a read.
    import gzip
    import statistics as st
    LONG = os.path.expanduser("~/malignment-data/norm_change/levels_long.csv.gz")
    agg_d = collections.defaultdict(list)
    if a.dose == "lift":
        #: NOT in levels_long -- it is computed per (prompt, base) rather than
        #: stored per (lineage, prompt, scale), so it is read from its own
        #: source. Aggregated to the prompt the same way as a stored scale:
        #: median over lineages, minimum five, so one lineage cannot nominate a
        #: prompt.
        if a.lang != "en":
            print("lift dose is ENGLISH ONLY -- charge covers 2,400 en prompts")
            return 1
        from malignment import charge, roster
        ep, _ = roster.endpoints()
        for (pr, base), v in charge.lifts_per_lineage().items():
            al = ep.get(base)
            if al and "%s>%s" % (base, al) in EP:
                agg_d[pr].append(float(v))
    else:
      with gzip.open(LONG, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head) or v[ix["scale"]] != a.dose:
                continue
            if v[ix["lang"]] != a.lang:
                continue
            if v[ix["base"]] + ">" + v[ix["aligned"]] not in EP:
                continue
            try:
                agg_d[v[ix["prompt"]]].append(float(v[ix["base_level"]]))
            except ValueError:
                continue
    if not agg_d:
        print("no prompts carry dose %r in %s -- is it a scale in levels_long?"
              % (a.dose, a.lang))
        return 1

    #: **RANK ONLY OVER PROMPTS `movement` CAN ACTUALLY SERVE.** The dose and the
    #: word table are two populations and they are not the same one: 2,400
    #: prompts carry a lift dose, 4,482 are in `movement`, and the OVERLAP is
    #: 2,126 -- so 274 lift-dosed prompts have no words to show.
    #:
    #: The top-ranked prompt by lift is one of them. Without this filter the
    #: command prints a prompt, a dose, and "no rated words at this prompt", and
    #: the only way forward is walking `--rank` by hand until one lands. That is
    #: not a missing feature; it is an example selected by which prompts happen
    #: to be in a second table, which is a selection rule nobody declared.
    have = {r["prompt"] for r in ch.query("SELECT DISTINCT prompt FROM movement")}
    before = len(agg_d)
    agg_d = {k: v for k, v in agg_d.items() if k in have}
    if before != len(agg_d):
        print("dose %s: %d prompts, %d also in movement (%d dropped)"
              % (a.dose, before, len(agg_d), before - len(agg_d)))
    if not agg_d:
        print("no dosed prompt is in movement -- the two populations are disjoint")
        return 1
    scored = sorted(((st.median(v), pr) for pr, v in agg_d.items() if len(v) >= 5),
                    reverse=True)
    if not scored:
        print("no prompts scored in %s" % a.lang)
        return 1
    dose, prompt = scored[min(a.rank, len(scored) - 1)]
    print()
    print("=" * 78)
    print("PROMPT (rank %d of %d by median %s = %.3f over >=5 lineages)"
          % (a.rank + 1, len(scored), a.dose, dose))
    print("=" * 78)
    print("  %r" % prompt[:200])

    target = a.usas or a.scale
    print()
    print("TARGET: %s   |   contribution = (p_aligned - p_base) * value" % target)
    agg = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    got = ch.query(
        "SELECT base, aligned, word, p_base, p_aligned FROM movement "
        "WHERE prompt=%s AND cls != 'still'" % _q(prompt))
    for r in got:
        if "%s>%s" % (r["base"], r["aligned"]) not in EP:
            continue
        v = value_of(r["word"])
        if v is None:
            continue
        d = float(r["p_aligned"]) - float(r["p_base"])
        e = agg[r["word"]]
        e[0] += d * v
        e[1] += d
        e[2] = v
        e[3] += 1
    if not agg:
        print("  no rated words at this prompt")
        return 1
    rows = sorted(agg.items(), key=lambda kv: kv[1][0])
    print()
    print("  %-18s %12s %12s %8s %6s" % ("word", "contribution", "mass delta", "value", "n_lin"))
    print("  --- pulling the mean DOWN ---")
    for w, (c, d, v, n) in rows[:a.top]:
        print("  %-18s %+12.5f %+12.5f %8.2f %6d" % (w[:18], c, d, v, n))
    print("  --- pulling the mean UP ---")
    for w, (c, d, v, n) in rows[-a.top:][::-1]:
        print("  %-18s %+12.5f %+12.5f %8.2f %6d" % (w[:18], c, d, v, n))
    net = sum(v[0] for v in agg.values())
    print()
    print("  NET contribution at this prompt: %+.5f over %d rated words"
          % (net, len(agg)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
