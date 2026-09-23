"""The prompts whose dominant slot POS changes base -> aligned, with their movers.
-> results/switchers_en.md

    python -u switchers.py

Reads `results/prompt_pos_en.csv` (switch == 1) and `words_long_v4`. Per word,
the MEAN delta (p_aligned - p_base) over the 50 endpoint lineages, a word absent
from a lineage's rows counting 0 there; the top fallers and risers by it, with
their contextual UPOS.
"""
import collections, csv, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
N = 6


def main():
    from malignment import roster
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    prof = {r["prompt"]: r for r in csv.DictReader(open(os.path.join(HERE, "results", "prompt_pos_en.csv")))
            if r["switch"] == "1"}
    d = collections.defaultdict(lambda: collections.defaultdict(float))
    u = {}
    with gzip.open(SRC, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lang"] != "en" or r["prompt"] not in prof or (r["base"], r["aligned"]) not in pairs:
                continue
            d[r["prompt"]][r["word"]] += float(r["delta"]) / len(pairs)
            t = r["upos"]
            u[(r["prompt"], r["word"])] = ("DET" if t == "PRON" and r["word"].lower()
                                           in ("the", "a", "an") else t)
    order = sorted(prof.values(), key=lambda r: (r["pos_base"] + ">" + r["pos_aligned"], r["prompt"]))
    c = collections.Counter(r["pos_base"] + " -> " + r["pos_aligned"] for r in order)
    L = ["# Prompts whose dominant slot POS changes base -> aligned (%d of 2,578)" % len(order), "",
         "Dominant = argmax of the mass-weighted contextual UPOS profile above theta, median over the 50 endpoint lineages (`run.py`). Movers: mean delta over lineages, contextual UPOS in brackets.", "",
         "    " + ", ".join("%s %d" % kv for kv in c.most_common()), ""]
    cur = None
    for r in order:
        k = r["pos_base"] + " -> " + r["pos_aligned"]
        if k != cur:
            L += ["", "## %s (%d)" % (k, c[k]), ""]
            cur = k
        ws = d[r["prompt"]]
        fall = sorted(ws, key=ws.get)[:N]
        rise = sorted(ws, key=ws.get, reverse=True)[:N]
        f = lambda w: "%s [%s] %+.3f" % (w, u[(r["prompt"], w)], ws[w])
        L.append("- **%s** — base %s %.2f, aligned %s %.2f" % (
            r["prompt"], r["pos_base"], float(r["purity_base"]), r["pos_aligned"], float(r["purity_aligned"])))
        L.append("  - falls: " + ", ".join(f(w) for w in fall if ws[w] < 0))
        L.append("  - rises: " + ", ".join(f(w) for w in rise if ws[w] > 0))
    open(os.path.join(HERE, "results", "switchers_en.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:5]))


if __name__ == "__main__":
    main()
