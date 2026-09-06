"""EXPLORATORY. The per-word curves behind the fuck/kill split.

    python -u curves_fk.py            fuck and kill
    python -u curves_fk.py --word X   any faller

**NOTHING HERE IS DECLARED.** `explore_q3.py` found that the Q3 relation is flat
across charge but that the charged tail SPLITS: `fuck` is textbook F04 (barred
immediately, substitute gradual) while `kill` mostly runs the other way. n=8 and
n~12 -- individual prompts, not populations. This prints the trajectories so the
split can be looked at rather than inferred from two AUC numbers.

Raw mass, not the normalised `f`, because F04's own claims are in raw terms
("fuck -70% by step 1000, -92% by 5000") and the normalisation is exactly what
hides a curve that overshoots and returns.
"""
import argparse, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from malignment import ch                                          # noqa: E402
from analyse import sites, END                                     # noqa: E402

SHOW = [1000, 2000, 3000, 5000, 8000, 12000, 20000, 30000, 43000]


def series(pairs):
    """-> {(prompt, word): {step: p_aligned}} plus the base level."""
    inl = ",".join("(%s,%s)" % (ch._lit(p), ch._lit(w)) for p, w in pairs)
    q = ("SELECT prompt, word, step_aligned, p_base, p_aligned "
         "FROM {db}.movement_rungs WHERE kind='base_rooted' "
         "AND (prompt, word) IN (%s)" % inl)
    out = collections.defaultdict(dict)
    base = {}
    for r in ch.query(q):
        k = (r["prompt"], r["word"])
        out[k][int(r["step_aligned"])] = float(r["p_aligned"])
        base[k] = float(r["p_base"])
    return out, base


def bar(v, mx):
    """A crude sparkline so a trajectory is readable without a plot."""
    if mx <= 0:
        return " " * 8
    n = int(round(8 * v / mx))
    return ("#" * n).ljust(8)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--word", action="append",
                    help="faller word(s); default fuck and kill")
    a = ap.parse_args(argv)
    words = a.word or ["fuck", "kill"]

    st = sites(False)
    for w in words:
        hits = [(p, r) for p, r in st.items() if r["faller"] == w]
        print("=" * 96)
        print("FALLER: %-10s  %d sites" % (w, len(hits)))
        print("=" * 96)
        if not hits:
            continue
        ser, base = series([(p, r["faller"]) for p, r in hits]
                           + [(p, r["riser"]) for p, r in hits])
        print("  raw mass at step; 'base' is the pretrained value")
        print("  %-30s %-9s %7s %s" % ("prompt", "word", "base",
                                       " ".join("%7d" % s for s in SHOW)))
        for p, r in sorted(hits, key=lambda x: x[0]):
            for role, wd in (("F", r["faller"]), ("R", r["riser"])):
                s = ser.get((p, wd), {})
                if not s:
                    continue
                print("  %-30s %s %-7s %7.4f %s"
                      % (p.replace("\n", " ")[:30] if role == "F" else "",
                         role, wd[:7], base.get((p, wd), 0.0),
                         " ".join("%7.4f" % s.get(k, float("nan")) for k in SHOW)))
            print()
        #: the aggregate F04 actually stated, recomputed on OUR data
        fs = [(p, r["faller"]) for p, r in hits]
        b = [base[k] for k in fs if k in base]
        for step in (1000, 5000, 20000, END):
            v = [ser[k].get(step, 0.0) for k in fs if k in ser]
            if b and v:
                tot_b, tot_v = sum(b), sum(v)
                print("  pooled %-5s mass %.4f -> %.4f   (%+.0f%% from base)"
                      % ("@%d" % step, tot_b, tot_v,
                         100 * (tot_v - tot_b) / tot_b if tot_b else float("nan")))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
