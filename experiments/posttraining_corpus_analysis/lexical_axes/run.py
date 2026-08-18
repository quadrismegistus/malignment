#!/usr/bin/env python
"""Does the model's alignment axis predict corpus preference? Registered `6625ec2`+A1-A3.

    python run.py --vector     inspect the model-side vector, no corpus touched
    python run.py --predict    the registered zero-parameter prediction test

## THE VECTOR IS SIGNED AND `auc` CARRIES THE SIGN

`k_word_auc.py` computes `roc_auc_score(y, C[:, j])` per word, so **auc is
DIRECTIONAL**: above 0.5 leans one arm, below 0.5 the other. Its own effect
measure is `abs(auc - .5) > .15`, two-sided.

**A3 records that the first run of this file's predecessor filtered `auc > 0.568`
and so DELETED all 2,013 base-leaning words**, then reported their absence as a
finding. `kill` sits at auc 0.1115 on all 92 models. The weight below is
`auc - 0.5` across both tails and there is a refusing assert to stop the
one-sided form returning.

## DENSITY, NOT SUM

A sum over matched tokens is a length proxy: `rho(raw score, length)` runs -0.42
to -0.89 across the five populations. The registered statistic is therefore the
per-token MEAN, and the length-matched replicate is reported beside it always.
"""
import argparse, csv, collections, glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
AUC_TSV = ("/Users/rj416/github/malign-logits/meta/M01_displacement/"
           "results/k/word_auc_en.tsv")
HH_CACHE = os.path.expanduser("~/.cache/huggingface/datasets/Anthropic___hh-rlhf")
TOKEN = re.compile(r"[a-z']+")
#: A3: two-sided, and 0.10 rather than the script's 0.15 to keep n usable.
#: Reported at 0.15 and 0.068 as a sensitivity in --vector.
EFFECT = 0.10


def vector(effect=EFFECT):
    """weight(word) = auc - 0.5, n_models-weighted across POS tags.

    THE ASSERT IS THE POINT. A one-sided vector is the defect A3 records, and it
    is invisible in the output -- every number stays plausible."""
    import numpy as np
    acc = collections.defaultdict(list)
    for r in csv.DictReader(open(AUC_TSV, encoding="utf-8"), delimiter="\t"):
        a = float(r["auc"])
        if abs(a - 0.5) <= effect:
            continue
        acc[r["word"].lower()].append((a - 0.5, int(r["n_models"])))
    w = {k: float(np.average([x[0] for x in v], weights=[x[1] for x in v]))
         for k, v in acc.items()}
    pos = sum(1 for v in w.values() if v > 0)
    neg = sum(1 for v in w.values() if v < 0)
    assert neg >= 0.2 * len(w), (
        "vector is one-sided (%d neg of %d) -- `auc` is DIRECTIONAL and a "
        "one-tailed filter deletes a pole. See A3." % (neg, len(w)))
    return w, pos, neg


def populations():
    """The five, never pooled. Each returns (chosen_text, rejected_text) pairs."""
    import pyarrow as pa, pyarrow.ipc as ipc
    out = {}
    for cfg, lab in (("default-52e03caf22ec705f", "hh-harmless"),
                     ("default-cfba128a0ab1b99f", "hh-helpful")):
        f = sorted(glob.glob(os.path.join(HH_CACHE, cfg, "**", "*train*.arrow"),
                             recursive=True))
        if not f:
            print("MISSING %s" % lab, file=sys.stderr); continue
        with pa.memory_map(f[0]) as s:
            d = ipc.open_stream(s).read_all().to_pydict()
        out[lab] = list(zip(d["chosen"], d["rejected"]))

    sys.path.insert(0, os.path.join(HERE, "..", "pku-safe-rlhf"))
    import run as R
    tr = R.load("train")
    mixed = [i for i in range(len(tr["prompt"]))
             if tr["is_response_0_safe"][i] != tr["is_response_1_safe"][i]]
    for lab, idx in (("pku-unsafe", R.both_unsafe(tr)), ("pku-mixed", mixed)):
        s = tr["safer_response_id"]
        out[lab] = [(tr["response_%d" % s[i]][i], tr["response_%d" % (1 - s[i])][i])
                    for i in idx]

    from datasets import load_dataset
    uf = load_dataset("HuggingFaceH4/ultrafeedback_binarized")["train_prefs"]
    tx = lambda m: m[-1]["content"] if isinstance(m, list) else str(m)
    out["ultrafeedback"] = [(tx(a), tx(b)) for a, b in zip(uf["chosen"], uf["rejected"])]
    return out


def predict():
    import numpy as np
    from scipy import stats
    w, pos, neg = vector()
    print("vector: %d words | aligned-leaning %d | base-leaning %d\n" % (len(w), pos, neg))

    def raw(t):
        return sum(w.get(x, 0.0) for x in TOKEN.findall(t.lower()))

    def dens(t):
        tk = TOKEN.findall(t.lower())
        return sum(w.get(x, 0.0) for x in tk) / len(tk) if tk else 0.0

    ln = lambda t: len(TOKEN.findall(t.lower()))
    rows = []
    print("%-16s %10s %10s %13s %14s %10s" %
          ("population", "raw", "DENSITY", "rho(raw,len)", "len-matched", "p"))
    for lab, pairs in populations().items():
        dr, dd, dl, S, L = [], [], [], [], []
        for c, r in pairs:
            dr.append(raw(c) - raw(r)); dd.append(dens(c) - dens(r))
            dl.append(ln(c) - ln(r)); S += [raw(c), raw(r)]; L += [ln(c), ln(r)]
        dr, dd, dl = map(np.asarray, (dr, dd, dl))
        acc = lambda a: (a[a != 0] > 0).mean()
        p = stats.binomtest(int((dd > 0).sum()), int((dd != 0).sum()), 0.5).pvalue
        rho = stats.spearmanr(S, L)[0]
        k = (np.abs(dl) <= 20) & (dd != 0)
        m = (dd[k] > 0).mean() if k.sum() >= 200 else float("nan")
        v = ("PASSES" if acc(dd) >= 0.58 and p < 0.01 else
             "NARROW" if acc(dd) >= 0.53 and p < 0.01 else "FAILS")
        print("%-16s %9.1f%% %9.1f%% %13.3f %13.1f%% %10.3g  %s"
              % (lab, 100 * acc(dr), 100 * acc(dd), rho, 100 * m, p, v))
        rows.append({"population": lab, "n": int((dd != 0).sum()),
                     "raw_acc": round(float(acc(dr)), 4),
                     "density_acc": round(float(acc(dd)), 4),
                     "rho_raw_len": round(float(rho), 4),
                     "density_acc_lenmatched": round(float(m), 4),
                     "n_lenmatched": int(k.sum()), "p": float(p), "verdict": v})
    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, "prediction.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); wr.writeheader()
        for r in rows: wr.writerow(r)
    print("\n  ->", out)


def inspect():
    import numpy as np
    rows = list(csv.DictReader(open(AUC_TSV, encoding="utf-8"), delimiter="\t"))
    auc = np.array([float(r["auc"]) for r in rows])
    print("source: %s\n  produced by k_word_auc.py FROM twp_words (NOT generations);"
          % AUC_TSV)
    print("  --prompts-from-corpus optionally restricts to a gen_sequences prompt set.")
    print("\n  %d words | below 0.5: %d | above 0.5: %d" %
          (len(auc), (auc < 0.5).sum(), (auc > 0.5).sum()))
    print("  auc: min %.3f  p5 %.3f  median %.3f  p95 %.3f  max %.3f"
          % (auc.min(), np.percentile(auc, 5), np.median(auc),
             np.percentile(auc, 95), auc.max()))
    for e in (0.15, 0.10, 0.068):
        w, p, n = vector(e)
        print("  |auc-0.5| > %.3f : %4d words  (%d aligned, %d base)" % (e, len(w), p, n))
    o = np.argsort(auc)
    print("\n  most BASE-leaning:  %s" %
          ", ".join("%s(%.3f)" % (rows[j]["word"], auc[j]) for j in o[:10]))
    print("  most ALIGNED-leaning: %s" %
          ", ".join("%s(%.3f)" % (rows[j]["word"], auc[j]) for j in o[-10:]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--vector", action="store_true")
    ap.add_argument("--predict", action="store_true")
    a = ap.parse_args()
    if a.vector:
        inspect()
    elif a.predict:
        predict()
    else:
        ap.print_help()
