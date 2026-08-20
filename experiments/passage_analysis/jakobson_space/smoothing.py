"""Does alignment lower bits-per-byte, and is it register or generation quality?

    python experiments/passage_analysis/jakobson_space/smoothing.py

F15's headline was that alignment universally smooths, measured on 10 families with
a token-level reference. This runs it on `$MALIGNMENT_DATA/jakobson_space/
passages.parquet` -- 47 aligned-vs-base contrasts, 432k passages, en and zh -- with
BLT `bits_per_byte`, which is byte-level and therefore ONE SCALE ACROSS SCRIPTS.

## THE UNIT IS THE ALIGNED MODEL

Each aligned model has exactly one base, so one contrast each: no double counting,
and a base with several aligned children contributes several contrasts rather than
being collapsed. An earlier version keyed on `lineage` and got 66/76 -- but that
column mixes two naming schemes (ClickHouse's `base>aligned` for `passage`/`y`, the
roster's bare `base` for f11_l2), so all 29 f11_l2 lineages were counted TWICE.
The corrected figure is 39/47.

## Two confounds, both measured rather than assumed

**DEGENERACY.** `bits_per_byte` is contaminated by generation failure in BOTH
directions: a repetition loop is trivially predictable and reads as maximally
smooth, while token salad reads as maximally rough. Real examples from the two
largest reversals:

    recurrentgemma-9b   0.303 b/B  "no no no in in in the the the in the in the..."
    Llama-3.1-8B-Instr  3.263 b/B  "富有Prostit英語=a stainless steel water boiler..."

`_is_degenerate` from the archive is used, WITH A FIX: its first rule is
`len(text.split()) < 5`, which on unspaced Chinese returns one token for a whole
passage and flags **41.2% of the zh corpus**. Counting characters instead for zh
brings that to 0.5% while leaving en unchanged at 3.6%.

**SCRIPT.** Chinese runs 1.63x English on the same scorer (2.12 vs 1.30 bits/byte),
so no cross-script POOLED number means anything. Within-script contrasts are safe
because the level cancels.

Filtering both SHARPENS the result rather than dissolving it, so neither creates it.

## And a confound the filters cannot reach

Non-degenerate is not fluent. Blind Opus judges (kappa 0.776) found only **12% of
Chinese continuations fluent**, 71% broken or flawed -- among passages the
degeneracy rules clear at 99.5%. And `zh_fluency_and_ordering.md` finds alignment
improves fluency 20 pairs to 5, which would lower bits-per-byte on its own.

So the arm effect is tested WITHIN each fluency grade, joining those verdicts on
(model, prompt, sample_idx). It survives at every grade, which is what licenses a
register reading alongside the quality one.

**31 of 58 models have ZERO fluent verdicts.** The competent set is almost entirely
Chinese-origin. Any corpus-level Chinese number pools models that write the language
with models that fail at it.
"""

import collections, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import population as P
ARCHIVE = "/Users/rj416/github/malign-logits/meta/M06_generation/results"
PARQ = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                  os.path.expanduser("~/malignment-data")),
                    "jakobson_space", "passages.parquet")
OUT = os.path.join(HERE, "results", "smoothing.json")
CJK = re.compile(r"[㐀-鿿]")
LAT = re.compile(r"[A-Za-z]")


def degenerate(text, script):
    """The archive's rule, with its first clause made script-aware."""
    text = str(text)
    units = list(re.sub(r"\s+", "", text)) if script == "zh" else text.split()
    if len(units) < 5:
        return True
    if Counter(units).most_common(1)[0][1] / len(units) > 0.3:
        return True
    ch = [c for c in text if not c.isspace()]
    return bool(ch and Counter(ch).most_common(1)[0][1] / len(ch) > 0.3)


def fluency():
    """(model, prompt, sample_idx) -> verdict, over both judging rounds."""
    out = {}
    for vf, sf in (("zh_fluency_verdicts.json", "zh_fluency_sample.json"),
                   ("zh_fluency_verdicts_r2.json", "zh_fluency_sample_r2.json")):
        try:
            vd = json.load(open(os.path.join(ARCHIVE, vf)))
            tr = (json.load(open(os.path.join(ARCHIVE, sf))) or {}).get("truth") or {}
        except FileNotFoundError:
            continue
        for r in (vd if isinstance(vd, list) else vd.get("verdicts") or []):
            t = tr.get(r.get("key"))
            if t:
                out[(t["model"], t["prompt"], t["sample_idx"])] = r.get("verdict")
    return out


def main():
    import numpy as np, pyarrow.parquet as pq
    from scipy import stats
    from malignment import roster
    lin = roster.lineages()
    base_of = {m: b for b, ms in lin.items() for m in ms if m != b}
    arm_of = {m: ("base" if m == b else "aligned") for b, ms in lin.items() for m in ms}

    t = pq.read_table(PARQ, columns=["script", "arm", "model", "prompt",
                                     "sample_idx", "text", "bits_per_byte"])
    d = {c: t.column(c).to_pylist() for c in t.schema.names}
    N = len(d["text"])
    deg = [degenerate(d["text"][i], d["script"][i]) for i in range(N)]
    pure = []
    for i in range(N):
        nc, nl = len(CJK.findall(d["text"][i])), len(LAT.findall(d["text"][i]))
        r = nc / (nc + nl) if (nc + nl) else 0.0
        pure.append(r < 0.02 or r > 0.90)

    res = {}

    def contrasts(keep, label):
        bym = collections.defaultdict(list)
        for i in range(N):
            if d["bits_per_byte"][i] is None or not keep(i):
                continue
            bym[d["model"][i]].append(d["bits_per_byte"][i])
        per = {}
        for m, vs in bym.items():
            b = base_of.get(m)
            if b and b in bym and len(vs) >= 30 and len(bym[b]) >= 30:
                per[m] = float(np.median(vs) - np.median(bym[b]))
        if len(per) < 3:
            return None
        v = list(per.values()); dn = sum(1 for x in v if x < 0)
        p = float(stats.binomtest(max(dn, len(v) - dn), len(v), 0.5).pvalue)
        res[label] = dict(n=len(v), median=float(np.median(v)), lower=dn, p=p,
                          per_model=per)
        print("  %-34s %3d contrasts | %+.4f | %2d/%-2d lower | p=%.2g"
              % (label, len(v), np.median(v), dn, len(v), p))
        return per

    print("BLT bits_per_byte, ALIGNED minus BASE. Unit = the aligned model.\n")
    contrasts(lambda i: True, "all")
    contrasts(lambda i: not deg[i], "non-degenerate")
    contrasts(lambda i: not deg[i] and pure[i], "non-degenerate + single-script")
    #: RH's standing rule for this parquet: all-Latin, or all-Chinese from a
    #: Chinese-fluent model, degenerate output out of both. Every analysis on this
    #: file should sit on this population, so it is imported and never re-derived.
    fl = P.zh_fluent()
    std = [P.standard(d["model"][i], d["text"][i], d["script"][i], fluent=fl)
           for i in range(N)]
    contrasts(lambda i: std[i], "STANDARD (RH's rule)")
    #: and for a zh CONTRAST, both arms must be fluent -- otherwise the comparison
    #: is of capability, not register. bloomz LOSES Chinese (25% -> 0%) and
    #: MiniCPM5 GAINS it (0% -> 45%); either would masquerade as a register effect.
    cm = P.contrast_models()
    contrasts(lambda i: std[i] and d["script"][i] == "zh"
              and (d["model"][i] in cm or d["model"][i] in set(cm.values())),
              "  zh, BOTH arms fluent")
    print()
    for s in ("en", "zh"):
        contrasts(lambda i, s=s: d["script"][i] == s, "%s all" % s)
        contrasts(lambda i, s=s: d["script"][i] == s and not deg[i] and pure[i],
                  "%s non-deg + pure" % s)
    print("\n  removed: degenerate %d (%.1f%%) | mixed-script %d (%.1f%%)"
          % (sum(deg), 100 * sum(deg) / N, N - sum(pure), 100 * (N - sum(pure)) / N))

    V = fluency()
    bym = collections.defaultdict(Counter)
    for (m, _, _), v in V.items():
        bym[m][v] += 1
    zero = [m for m in bym if bym[m]["fluent"] == 0]
    print("\nFLUENCY BY MODEL: %d of %d models have ZERO fluent verdicts"
          % (len(zero), len(bym)))
    rates = {m: 100 * c["fluent"] / sum(c.values()) for m, c in bym.items() if sum(c.values())}
    for m in sorted(rates, key=lambda m: -rates[m])[:6]:
        print("    %-44s %5.1f%%" % (m[:44], rates[m]))
    res["fluency_by_model"] = rates
    res["models_zero_fluent"] = sorted(zero)

    bpb = {(m, p, s): v for m, p, s, v in
           zip(d["model"], d["prompt"], d["sample_idx"], d["bits_per_byte"])
           if v is not None}
    print("\nARM EFFECT WITHIN A FLUENCY GRADE (judged items in the parquet)")
    print("  %-14s %6s %10s %10s %10s" % ("verdict", "n", "base", "aligned", "diff"))
    grades = {}
    for g in ("fluent", "flawed", "broken", "not_chinese"):
        bb = [bpb[k] for k, v in V.items() if v == g and k in bpb and arm_of.get(k[0]) == "base"]
        aa = [bpb[k] for k, v in V.items() if v == g and k in bpb and arm_of.get(k[0]) == "aligned"]
        if len(bb) < 20 or len(aa) < 20:
            print("  %-14s too few (base %d, aligned %d)" % (g, len(bb), len(aa)))
            continue
        u = stats.mannwhitneyu(bb, aa)
        grades[g] = dict(n_base=len(bb), n_aligned=len(aa),
                         base=float(np.median(bb)), aligned=float(np.median(aa)),
                         diff=float(np.median(aa) - np.median(bb)), p=float(u.pvalue))
        print("  %-14s %6d %10.4f %10.4f %+10.4f  p=%.2g"
              % (g, len(bb) + len(aa), np.median(bb), np.median(aa),
                 np.median(aa) - np.median(bb), u.pvalue))
    print("\n  NB these pool passages across models, so the p-values are optimistic;")
    print("  the direction holding in every grade is the robust part.")
    res["within_fluency_grade"] = grades

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(dict(_what="alignment and bits_per_byte, with degeneracy, script and "
                         "fluency controls", **res), open(OUT, "w"), indent=1)
    print("\n-> results/smoothing.json")


if __name__ == "__main__":
    main()
