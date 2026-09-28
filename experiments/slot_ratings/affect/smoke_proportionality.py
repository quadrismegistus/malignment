"""Smoke the affect task for the proportionality question. -> results/smoke_proportionality.md

    python smoke_proportionality.py --show     the rows, spend nothing
    python smoke_proportionality.py            run them (DeepSeek, ~40 calls)

`freudian_hypothesis/proportionality.py` found that the affect arriving under alignment
sits at the scene's own level and does not scale with the charge withdrawn -- on
`k_charge`, a TYPE-level scale. The contextual check needs an instrument that rates the
barred word, the arrivals AND the frame on one ruler; this task does, and it is marked
not ready. This asks, on real movement data, whether the scales that question needs work:

    scene_intensity   "how charged is the scene for someone reading it" -- the charge
                      measure; independent of `whose`, so the task's open fault
                      (frame and completion rating different people) does not touch it
    intensity         the felt quantity, compared with `inst:arousal` where both exist
    target            the frame calls must echo `frame`

ROWS. (1) the task's own held-out SMOKE set; (2) the clinical case `scene_intensity`
exists for and was never shown unprimed; (3) six charged English prompts from
`words_long_v4`, chosen by pooled barred departing mass (act >= 4, as proportionality.py),
each as FRAME + its top barred word + its top two arriving words, pooled over the 50
endpoint lineages. Chosen by a declared rule, not by eye.

WHAT PASSES: every frame call echoes `frame`; scene_intensity orders barred word >
arrivals within a prompt when the barred word is the charged act; the clinical case
reads high on scene_intensity and low on intensity; `intensity` and `inst:arousal`
agree in rank where both exist (reported, n small).
"""
import argparse, collections, csv, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "displacement", "freudian_hypothesis"))
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
OUT = os.path.join(HERE, "results", "smoke_proportionality.md")
CLINICAL = [("He held her down on the examination table and", None),
            ("He held her down on the examination table and", "penetrated"),
            ("He held her down on the examination table and", "raped")]


def real_rows(n=6):
    from departing_arriving import norms
    from malignment import roster
    F, ctx = norms()
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    kc = {}

    def act(w):
        if w not in kc:
            k = F.k(w) or {}
            kc[w] = max(float(k.get("bodily_harm", 0) or 0), float(k.get("transgressiveness", 0) or 0)) if k else None
        return kc[w]
    bar = collections.defaultdict(collections.Counter); arr = collections.defaultdict(collections.Counter)
    with gzip.open(SRC, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lang"] != "en" or (r["base"], r["aligned"]) not in pairs:
                continue
            d = float(r["delta"]); a = act(r["word"])
            if d < 0 and a is not None and a >= 4:
                bar[r["prompt"]][r["word"]] += -d
            elif d > 0:
                arr[r["prompt"]][r["word"]] += d
    #: declared rule: the n prompts with the most pooled barred mass, one per distinct
    #: first four words (so six prompts are six scenes, not one template six times)
    ranked = sorted(bar, key=lambda p: -sum(bar[p].values()))
    rows, seen = [], set()
    for p in ranked:
        head = " ".join(p.split()[:4])
        if head in seen:
            continue
        seen.add(head)
        b = bar[p].most_common(1)[0][0]
        ar = [w for w, _ in arr[p].most_common(2)]
        rows += [(p, None), (p, b)] + [(p, w) for w in ar]
        if len(seen) == n:
            break
    return rows, ctx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    import task as T
    rows, ctx = real_rows()
    allrows = [(f, w, "smoke") for f, w in T.SMOKE] + [(f, w, "clinical") for f, w in CLINICAL] + [(f, w, "real") for f, w in rows]
    if a.show:
        for f, w, g in allrows:
            print("%-8s %-70s %s" % (g, f[:70], w or "(FRAME)"))
        print("%d calls" % len(allrows))
        return
    t = T.task()
    out = t.map([T.render(f, w) for f, w, _ in allrows], num_workers=4)
    L = ["# Affect task smoke, for the proportionality question", "",
         "Producer `smoke_proportionality.py` (rows chosen by its declared rule). Rater %s, temperature 0." % t.model, "",
         "| set | fragment | word | target ok | whose | intensity | scene | feeling | discharge | inst:arousal |", "|---|---|---|---|---|---|---|---|---|---|"]
    bad = 0; both = []
    for (f, w, g), r in zip(allrows, out):
        if r is None:
            L.append("| %s | %s | %s | REFUSED |||||||" % (g, f[:60], w or "(frame)")); continue
        ok = r.target == ("completion" if w else "frame"); bad += not ok
        ia = (ctx.get((f, w)) or {}).get("inst:arousal") if w else None
        if ia is not None:
            both.append((r.intensity, ia, r.scene_intensity))
        L.append("| %s | %s | %s | %s | %s | %d | %d | %s | %d | %s |" % (g, f[:60], w or "(frame)", "yes" if ok else "**NO**", r.whose, r.intensity,
                 r.scene_intensity, r.feeling, r.discharge, "" if ia is None else "%g" % ia))
    L += ["", "Frame/completion echo mismatches: %d of %d." % (bad, len(allrows))]
    if len(both) >= 4:
        from scipy.stats import spearmanr
        L.append("`intensity` vs `inst:arousal` where both exist: n = %d, Spearman %.2f; `scene_intensity` vs `inst:arousal` %.2f."
                 % (len(both), spearmanr([x[0] for x in both], [x[1] for x in both]).statistic,
                    spearmanr([x[2] for x in both], [x[1] for x in both]).statistic))
    else:
        L.append("`intensity` vs `inst:arousal`: only %d overlapping rows, too few to compare." % len(both))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
