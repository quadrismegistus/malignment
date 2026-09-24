"""The two differences taken apart: individual vs institution, base vs aligned. -> results/decompose.md

    python -u decompose.py

POST HOC (2026-09-24), after the declared test (`analyse_regen.py`), at RH's
question "is the story 'base is already procedural' true?". Pooled over kept
passages (continuation + advice, coherent, perspective kept) in lineages with both
arms -- NOT the lineage-unit test. Three tables: all kept, advice only, and
continuation only, so that the base->aligned change can be separated from the
change of GENRE (aligned models write advice 77% of the time, base 11%).
"""
import collections, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402

O = ["any", "outward", "authority", "channel", "inward", "move_voice_direct",
     "move_third_party", "move_self_help", "move_exit"]


def table(sub, title):
    c = collections.defaultdict(list)
    for r in sub:
        o = A.outcomes(r["coded"])
        for n in O:
            c[(n, r["arm"], r["side"])].append(o[n])
    v = lambda n, a, s: np.mean(c[(n, a, s)]) if c[(n, a, s)] else float("nan")
    L = ["## " + title, "",
         "| outcome | base indiv | base inst | base gap | aligned indiv | aligned inst | aligned gap | change in gap |",
         "|---|---|---|---|---|---|---|---|"]
    for n in O:
        bi, bs, ai, as_ = v(n, "base", "individual"), v(n, "base", "institution"), v(n, "aligned", "individual"), v(n, "aligned", "institution")
        L.append("| %s | %.3f | %.3f | %+.3f | %.3f | %.3f | %+.3f | %+.3f |" % (n, bi, bs, bi - bs, ai, as_, ai - as_, (ai - as_) - (bi - bs)))
    L += ["", "n: base %d / %d, aligned %d / %d (individual / institution)." % tuple(
        len(c[("any", a, s)]) for a in ("base", "aligned") for s in ("individual", "institution")), ""]
    return L


def main():
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r.get("coded") and A.keep(r["coded"])]
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    rows = [r for r in rows if arms[r["lineage"]] == {"base", "aligned"}]
    L = ["# Decomposing the two differences (POST HOC, pooled over passages)", "",
         "Producer `decompose.py`. Not the declared test; see the module docstring.", ""]
    L += table(rows, "All kept passages")
    L += table([r for r in rows if r["coded"]["form"] == "advice"], "Advice only (both arms)")
    L += table([r for r in rows if r["coded"]["form"] == "continuation"], "Continuation only (both arms)")
    open(os.path.join(HERE, "results", "decompose.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
