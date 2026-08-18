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


GEN_SQL = """
SELECT g.pair AS pair, g.role AS role, c.pair_role AS stratum,
       arrayJoin(extractAll(lower(g.text), '[a-z]{2,}')) AS word
FROM malign_logits.gen_sequences g
INNER JOIN malign_logits.prompt_catalogue c ON g.prompt = c.prompt
WHERE g.corpus='passage' AND g.forced_word='' AND g.pair != ''
  AND g.role IN ('base','aligned') AND c.slot='NARR'
"""


def genvector(min_pairs=15, min_count=5):
    """RH's design. The control is the DESIGN, not the prompts: same prompts,
    same n, two arms. Three vectors from one contrast, partitioned by stratum.

        rate(w, pair, arm) = count / tokens      NORMALISED WITHIN ARM FIRST,
                                                  so arm verbosity cannot leak in
        delta(w, pair)     = rate_aligned - rate_base
        weight(w)          = share of pairs with delta > 0, minus 0.5

    The unit is the PAIR (42 of them), not the row -- U's lineage-clustering
    warning. MARKED/UNMARKED are NOT treated as minimal pairs: RH established
    that a one-word swap changes the scene and the transgressive half is bland.
    They are strata that differ in transgressiveness ON AVERAGE, and the question
    is only whether that changes the result."""
    import numpy as np, subprocess, collections
    from scipy import stats
    print("querying generations (unforced NARR passages, 42 pairs)...", flush=True)
    q = ("SELECT pair, role, stratum, word, count() AS n FROM (%s) "
         "GROUP BY pair, role, stratum, word HAVING n >= %d "
         "FORMAT TabSeparated" % (GEN_SQL, min_count))
    out = subprocess.run(["clickhouse", "client", "--query", q],
                         capture_output=True, text=True, timeout=3600)
    if out.returncode:
        raise SystemExit("clickhouse failed: %s" % out.stderr[:300])
    cnt = collections.defaultdict(int); tot = collections.defaultdict(int)
    for line in out.stdout.splitlines():
        p, role, strat, w, n = line.split("\t")
        n = int(n)
        cnt[(strat, w, p, role)] += n
        tot[(strat, p, role)] += n
    print("  %d (stratum, word, pair, arm) cells" % len(cnt))

    def build(strata, label):
        words = collections.defaultdict(list)
        pairs = sorted({p for (s, p, r) in tot if s in strata})
        for (s, w, p, role) in list(cnt):
            if s not in strata or role != "aligned":
                continue
            tb = tot.get((s, p, "base"), 0); ta = tot.get((s, p, "aligned"), 0)
            if not tb or not ta:
                continue
            ra = cnt[(s, w, p, "aligned")] / ta
            rb = cnt.get((s, w, p, "base"), 0) / tb
            words[w].append(1 if ra > rb else (0 if ra < rb else None))
        vec = {}
        for w, v in words.items():
            v = [x for x in v if x is not None]
            if len(v) >= min_pairs:
                vec[w] = float(np.mean(v)) - 0.5
        pos = sum(1 for x in vec.values() if x > 0); neg = sum(1 for x in vec.values() if x < 0)
        assert neg >= 0.1 * len(vec), "one-sided vector (%d neg of %d)" % (neg, len(vec))
        print("  %-22s %5d words on >=%d pairs | aligned-leaning %4d  base-leaning %4d"
              % (label, len(vec), min_pairs, pos, neg))
        return vec

    V = {"ALL": build({"MARKED", "UNMARKED"}, "ALL"),
         "MARKED": build({"MARKED"}, "MARKED"),
         "UNMARKED": build({"UNMARKED"}, "UNMARKED")}
    shared = set.intersection(*(set(v) for v in V.values()))
    print("  shared vocabulary across all three: %d words (the comparison set)" % len(shared))
    V = {k: {w: x for w, x in v.items() if w in shared} for k, v in V.items()}

    pops = populations()
    ln = lambda t: len(TOKEN.findall(t.lower()))
    print("\n%-15s %-9s %8s %8s %10s %11s %9s" %
          ("population", "vector", "acc", "p", "len-match", "n_matched", "verdict"))
    for lab, prs in pops.items():
        L = np.asarray([ln(c) - ln(r) for c, r in prs])
        for k in ("ALL", "MARKED", "UNMARKED"):
            vec = V[k]
            dens = lambda t: (sum(vec.get(x, 0.0) for x in TOKEN.findall(t.lower()))
                              / max(len(TOKEN.findall(t.lower())), 1))
            d = np.asarray([dens(c) - dens(r) for c, r in prs])
            nz = d != 0
            acc = (d[nz] > 0).mean()
            p = stats.binomtest(int((d[nz] > 0).sum()), int(nz.sum()), 0.5).pvalue
            m = (np.abs(L) <= 20) & nz
            lm = (d[m] > 0).mean() if m.sum() >= 200 else float("nan")
            v = ("PASSES" if lm >= 0.58 else "NARROW" if lm >= 0.53 else "FAILS")
            print("%-15s %-9s %7.1f%% %8.2g %9.1f%% %11d %9s"
                  % (lab if k == "ALL" else "", k, 100*acc, p, 100*lm, int(m.sum()), v))
    print("\n  the M-minus-U column is the question: does whatever transgressiveness")
    print("  is in MARKED change the result. It is NOT a clean transgression contrast.")


def reverse():
    """RH: can preference data predict the arm? The REVERSE of --genvector.

    NOT symmetric with the forward test, because the CEILINGS differ:
        forward ceiling  corpus preference is lexically predictable at AUC 0.683
                         (pku --h3, 13,820 terms). Our model vector got ~0.50.
        reverse ceiling  base-vs-aligned is predictable from a PAGE at 0.851-0.966
                         (M06 p_on_passages, fitted). Far more room to fail in.

    So a null here is the stronger claim: the preference signal cannot recover a
    distinction a fitted classifier gets at 0.9+, i.e. alignment is not a mirror
    of its preference data.

    Construction mirrors genvector exactly, roles swapped: rate normalised WITHIN
    RESPONSE, differenced within pair, sign-counted across pairs."""
    import numpy as np, subprocess, collections
    from scipy import stats
    ln = lambda t: len(TOKEN.findall(t.lower()))

    def corpus_vector(pairs, label, min_pairs=200):
        acc = collections.defaultdict(list)
        for c, r in pairs:
            tc, tr = TOKEN.findall(c.lower()), TOKEN.findall(r.lower())
            if not tc or not tr:
                continue
            nc, nr = collections.Counter(tc), collections.Counter(tr)
            for w in set(nc) | set(nr):
                a, b = nc[w] / len(tc), nr[w] / len(tr)
                if a != b:
                    acc[w].append(1 if a > b else 0)
        v = {w: float(np.mean(x)) - 0.5 for w, x in acc.items() if len(x) >= min_pairs}
        pos = sum(1 for x in v.values() if x > 0)
        print("  %-16s %5d words on >=%d pairs | chosen-leaning %4d  rejected-leaning %4d"
              % (label, len(v), min_pairs, pos, len(v) - pos))
        return v

    print("building corpus vectors (chosen vs rejected, normalised within response)...")
    CV = {k: corpus_vector(p, k) for k, p in populations().items()}

    #: RH: inspect the coefficients. hh-rlhf's top features turned out to be
    #: `https, http, html` -- formatting, not preference. Printed BEFORE any
    #: accuracy so the words are read on their own terms.
    MARKUP = {"https", "http", "html", "www", "com", "href", "src", "png", "jpg"}
    print("\n=== THE COEFFICIENTS ===")
    for k, v in CV.items():
        top = sorted(v.items(), key=lambda x: -x[1])
        mk = [w for w, _ in top[:40] if w in MARKUP] + [w for w, _ in top[-40:] if w in MARKUP]
        print("\n  %s" % k)
        print("    CHOSEN-leaning : %s" %
              ", ".join("%s %+.2f" % (w, x) for w, x in top[:14]))
        print("    REJECTED-leaning: %s" %
              ", ".join("%s %+.2f" % (w, x) for w, x in top[-14:][::-1]))
        print("    markup tokens in either tail: %s" % (", ".join(mk) if mk else "none"))

    print("\nfetching base/aligned passages (unforced NARR, matched by prompt)...")
    q = ("SELECT pair, role, prompt, text FROM malign_logits.gen_sequences "
         "WHERE corpus='passage' AND forced_word='' AND pair != '' "
         "AND role IN ('base','aligned') AND modulo(cityHash64(pair, prompt), 6) = 0 FORMAT TabSeparated")
    out = subprocess.run(["clickhouse", "client", "--query", q],
                         capture_output=True, text=True, timeout=3600)
    if out.returncode:
        raise SystemExit("clickhouse failed: %s" % out.stderr[:300])
    by = collections.defaultdict(dict)
    for line in out.stdout.splitlines():
        f = line.split("\t")
        if len(f) < 4:
            continue
        by[(f[0], f[2])][f[1]] = f[3]
    matched = [(v["base"], v["aligned"]) for v in by.values()
               if "base" in v and "aligned" in v]
    print("  %d matched base/aligned passage pairs (same pair, same prompt)" % len(matched))

    print("\n%-16s %8s %10s %10s %s" % ("corpus vector", "n", "arm acc", "p", "verdict"))
    print("  M06 fitted-classifier ceiling on this task: 0.851 - 0.966")
    for k, vec in CV.items():
        dens = lambda t: (sum(vec.get(x, 0.0) for x in TOKEN.findall(t.lower()))
                          / max(len(TOKEN.findall(t.lower())), 1))
        d = np.asarray([dens(a) - dens(b) for b, a in matched])
        d = d[d != 0]
        acc = (d > 0).mean()
        p = stats.binomtest(int((d > 0).sum()), len(d), 0.5).pvalue
        acc = max(acc, 1 - acc)
        v = "PREDICTS" if acc >= 0.60 else "WEAK" if acc >= 0.55 else "FAILS"
        print("%-16s %8d %9.1f%% %10.2g %s" % (k, len(d), 100 * acc, p, v))
    print("\n  accuracy is direction-free (max of acc, 1-acc): a corpus vector")
    print("  that predicts the arm BACKWARDS is still predicting it.")


def basepole():
    """RH: there is no such thing as base-generated assistant prose.

    The vector is a BASE-vs-ALIGNED contrast, and every response in every
    preference corpus comes from an instruction-tuned generator -- so both sides
    of every pair sit on the aligned pole and the axis is asked to discriminate
    where one of its poles cannot occur. The null was structural, not empirical.

    ONE EXCEPTION EXISTS. UltraFeedback's generator list contains `pythia-12b`,
    a base model, on 0.3% of completions. If the axis is real and the null is a
    domain restriction, it should fire exactly there and nowhere else."""
    import numpy as np
    from scipy import stats
    from datasets import load_dataset
    w, pos, neg = vector()
    dens = lambda t: (sum(w.get(x, 0.0) for x in TOKEN.findall(t.lower()))
                      / max(len(TOKEN.findall(t.lower())), 1))
    o = load_dataset("openbmb/UltraFeedback")["train"]
    r2m = {}
    for q in o:
        for c in q["completions"]:
            r2m.setdefault(c["response"].strip(), c["model"])
    uf = load_dataset("HuggingFaceH4/ultrafeedback_binarized")["train_prefs"]
    tx = lambda m: m[-1]["content"] if isinstance(m, list) else str(m)
    BASE, SFT = {"pythia-12b"}, {"alpaca-7b", "starchat"}
    groups = {"base on one side": [], "SFT-only on one side": [], "both chat/instruct": []}
    for a, b in zip(uf["chosen"], uf["rejected"]):
        c, r = tx(a), tx(b)
        mc, mr = r2m.get(c.strip()), r2m.get(r.strip())
        if not mc or not mr:
            continue
        d = dens(c) - dens(r)
        if d == 0:
            continue
        g = ("base on one side" if BASE & {mc, mr} else
             "SFT-only on one side" if SFT & {mc, mr} else "both chat/instruct")
        #: sign convention: does the ALIGNED-leaning text win? Where a base model
        #: is present it is nearly always the rejected side, so a working axis
        #: predicts the chosen response scores HIGHER.
        groups[g].append(d > 0)
    print("%-24s %8s %10s %-18s %s" % ("stratum", "n", "accuracy", "95% CI", "p"))
    for g, v in groups.items():
        if len(v) < 30:
            print("%-24s %8d   UNPOWERED" % (g, len(v))); continue
        k = int(np.sum(v)); t = stats.binomtest(k, len(v), 0.5)
        lo, hi = t.proportion_ci()
        print("%-24s %8d %9.1f%%  [%.3f, %.3f]  %-10.3g" %
              (g, len(v), 100 * k / len(v), lo, hi, t.pvalue))


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
    ap.add_argument("--basepole", action="store_true")
    ap.add_argument("--genvector", action="store_true")
    ap.add_argument("--reverse", action="store_true")
    a = ap.parse_args()
    if a.vector:
        inspect()
    elif a.predict:
        predict()
    elif a.basepole:
        basepole()
    elif a.genvector:
        genvector()
    elif a.reverse:
        reverse()
    else:
        ap.print_help()
