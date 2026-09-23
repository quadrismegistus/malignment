"""Random example pairs from the regeneration. -> results/examples_regen.md

    python -u examples_regen.py

Drawn with a fixed seed from coded passages that pass the analysis filter
(continuation/advice, coherent, perspective kept), in lineages that enter the
test (both arms). K (lineage, dispute) cells are drawn at random from those where
BOTH aligned sides have a kept passage; within a cell one passage per side and
arm is drawn at random -- not selected for showing any effect, and not grouped by
prediction, since the draw is not targeted at one. The base passage for each side is drawn
the same way, for contrast. Each passage is shown with its coded move and
referrals so the reader can check the code against the text.
"""
import collections, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402

K = 8


def clip(t, n=900):
    t = re.sub(r"\s+", " ", t).strip()
    return t[:n] + ("..." if len(t) > n else "")


def show(r):
    c = r["coded"]
    refs = "; ".join("%s [%s, %s%s]" % (x["body"], x["relation"], x["stance"],
                                         ", authority" if x["authority_over_counterparty"] else "")
                     for x in c["referrals"]) or "none"
    return ("*%s, move: %s; referrals: %s*\n\n> %s" % (r["model"], c["primary_move"], refs, clip(r["text"])))


def main():
    rows = [json.loads(l) for l in open(A.SRC)]
    rows = [r for r in rows if r.get("coded") and A.keep(r["coded"])]
    cell = collections.defaultdict(list)
    for r in rows:
        cell[(r["lineage"], r["scenario"], r["side"], r["arm"])].append(r)
    arms = collections.defaultdict(set)
    for r in rows:
        arms[r["lineage"]].add(r["arm"])
    tested = {l for l, a in arms.items() if a == {"base", "aligned"}}
    both = sorted({(l, s) for (l, s, sd, a) in cell if l in tested
                   if cell.get((l, s, "individual", "aligned")) and cell.get((l, s, "institution", "aligned"))})
    design = json.load(open(os.path.join(HERE, "prompts", "design.json")))
    rnd = random.Random(20260924)
    L = ["# Example pairs, drawn at random (regeneration)", "",
         "Producer `examples_regen.py`, seed 20260924. Cells drawn at random from the %d (lineage, dispute) cells "
         "with a kept passage on both aligned sides; one passage per side drawn at random within the cell. "
         "Not selected for the effect. Base passages drawn the same way where the base has a kept passage." % len(both), ""]
    for (l, s) in rnd.sample(both, K):
        L += ["## %s: %s" % (l, s), ""]
        for side in ("individual", "institution"):
            pk = "%s__%s" % (s, side)
            L += ["**%s** (%s vs %s): *%s*" % (side.upper(), design[pk]["speaker"], design[pk]["counterparty"],
                                              design[pk]["prompt"]), ""]
            for arm in ("base", "aligned"):
                pool = cell.get((l, s, side, arm))
                L += ["- %s: %s" % (arm, show(rnd.choice(pool)) if pool else "*(no kept base passage)*"), ""]
    out = os.path.join(HERE, "results", "examples_regen.md")
    open(out, "w").write("\n".join(L) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
