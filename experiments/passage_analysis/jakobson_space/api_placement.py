"""Place API models against the open roster and the human anchor, with CIs.

    python .../api_placement.py
    python .../api_placement.py --boot 4000

Reads whatever is complete under `$MALIGNMENT_DATA/api_passages/*_v4_ref` and
`*_v4_bge`, so it can be run while later models are still generating.

## THE MEDIAN NEEDS AN INTERVAL AND THE INTERVAL NEEDS CLUSTERING

Six samples of one stem are not six independent observations: measured ICC
within stem is **0.417 (deepseek-v4-flash) and 0.433 (v4-pro)** against **0.121**
for the open models on the same metric, so an API model's passages are about 3.5x
more stem-determined. A naive bootstrap over passages would understate the error
by roughly sqrt(deff) = 1.7x. This resamples STEMS with replacement.

## WHY BOTH AXES AND WHY THEY DISAGREE ABOUT WHAT IS RESOLVED

Per-passage SD is 0.34-0.41 on surprisal against a between-model range of ~0.6,
so at 600 passages the surprisal medians carry SE ~0.03 and the closest three
models overlap freely -- a 0.07 spread read through 0.03 error bars is not a
ranking. Drift's SE is ~0.002 against a between-model spread of ~0.03, an order
of magnitude better, and its clusters separate cleanly.

**So drift is the axis with resolving power at this n, and surprisal is not.**
That was not the expectation and it is the reason both are reported with
intervals rather than as points.

## PERCENTILES, NOT DISTANCE FROM A MEDIAN

The open ALIGNED per-model medians run 2.3591 to 5.0115 on surprisal. Quoting an
API model's distance from the aligned MEDIAN made five models look like a
distinctive low band when all five sit inside the aligned range between the 30th
and 70th percentile. A single summary standing in for a distribution, which is
the defect this file exists to not repeat.

## AND THE MODEL MEDIAN IS ITSELF A SINGLE SUMMARY

The same caution applies one level up, to this file's own output. A per-model
median is one point standing for that model's passages, and the passage
distribution behind it is not narrow: at the passage grain the two axes correlate
`+0.348` against `+0.749` between entities, and all four quadrants are occupied
where the entity plane is a diagonal.

So "which quadrant is this model in" and "where do this model's passages fall"
are different questions with different answers, and this file only answers the
first. `results/quadrants.csv` carries the second, one row per passage with the
text; `read_passage.py` renders a single one with its words and sentences marked.
"""

import argparse, collections, json, os, random, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
API = os.path.join(DATA, "api_passages")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

M_TOKENS = 200
#: label -> file slug. Kept explicit so a model absent from disk is a VISIBLE
#: gap in the output rather than a row that silently never appears.
MODELS = [
    ("deepseek-v4-flash", "deepseek_deepseek_v4_flash_v4"),
    ("deepseek-v4-pro", "deepseek_deepseek_v4_pro_v4"),
    ("gpt-5.4-nano", "gpt_5_4_nano_v4"),
    ("gpt-5.4-mini", "gpt_5_4_mini_v4"),
    ("gpt-5.4", "gpt_5_4_v4"),
    ("claude-haiku-4-5", "claude_haiku_4_5_v4"),
    ("claude-sonnet-5", "claude_sonnet_5_v4"),
    ("claude-opus-5", "claude_opus_5_v4"),
    ("gemini-3.6-flash", "google_gemini_3_6_flash_v5"),
    ("gemini-3.5-flash", "google_gemini_3_5_flash_v5"),
    ("gemini-3.5-flash-lite", "google_gemini_3_5_flash_lite_v5"),
]
HUMAN = [("literary_criticism", 4.4543, 0.4963), ("c20_fiction", 4.3558, 0.4833),
         ("arxiv_abstracts", 4.1581, 0.4496), ("philosophy", 4.0397, 0.4521),
         ("dreams", 3.8457, 0.4369), ("waking_narrative", 3.2884, 0.4211)]


def by_stem(slug):
    """-> ({stem: [bits/token]}, {stem: [mean_drift]}), either possibly empty."""
    import numpy as np
    meta_p = os.path.join(API, slug + ".jsonl")
    if not os.path.exists(meta_p):
        return {}, {}
    meta = {json.loads(l)["id"]: json.loads(l) for l in open(meta_p)}
    sur = collections.defaultdict(list)
    ref = os.path.join(API, slug + "_ref", "ref_shard00.jsonl")
    if os.path.exists(ref):
        s = np.fromfile(os.path.join(API, slug + "_ref", "ref_shard00.f32"),
                        dtype=np.float32)
        for line in open(ref):
            x = json.loads(line)
            if x["n"] >= M_TOKENS and x["id"] in meta:
                sur[meta[x["id"]]["stem"]].append(
                    float(s[x["row"]:x["row"] + M_TOKENS].mean()))
    dri = collections.defaultdict(list)
    dp = os.path.join(API, slug + "_bge", "drift.jsonl")
    if os.path.exists(dp):
        for line in open(dp):
            y = json.loads(line)
            if y.get("mean_drift") is not None and y["id"] in meta:
                dri[meta[y["id"]]["stem"]].append(y["mean_drift"])
    return sur, dri


def cluster_boot(bystem, boot, seed=20260821):
    """Median with a 95% CI, resampling STEMS. -> (median, se, lo, hi, n)"""
    if not bystem:
        return None
    keys = list(bystem)
    n = sum(len(v) for v in bystem.values())
    rng = random.Random(seed)
    meds = []
    for _ in range(boot):
        samp = []
        for _ in keys:
            samp.extend(bystem[rng.choice(keys)])
        meds.append(statistics.median(samp))
    meds.sort()
    return (statistics.median(meds), statistics.pstdev(meds),
            meds[int(0.025 * boot)], meds[int(0.975 * boot)], n)


def aligned_reference():
    """Per-model medians for the open ALIGNED arm, both axes. -> (surp, drift)"""
    import numpy as np, pyarrow.parquet as pq
    from malignment import roster
    D = os.path.join(DATA, "ref_pool")
    pool = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(D, "ref_pool.jsonl"))}
    s = np.fromfile(os.path.join(D, "deepseek", "ref_shard00.f32"), dtype=np.float32)
    t = pq.read_table(os.path.join(DATA, "jakobson_space", "passages_std.parquet"),
                      columns=["text_sha", "mean_drift"])
    d = {sh: v for sh, v in zip(t.column("text_sha").to_pylist(),
                                t.column("mean_drift").to_pylist()) if v is not None}
    al = roster.population("aligned")
    su, dr = collections.defaultdict(list), collections.defaultdict(list)
    for line in open(os.path.join(D, "deepseek", "ref_shard00.jsonl")):
        x = json.loads(line)
        p = pool.get(x["id"])
        if not p or p["pool"] != "model_narrative" or p.get("model") not in al:
            continue
        if x["n"] >= M_TOKENS:
            su[p["model"]].append(float(s[x["row"]:x["row"] + M_TOKENS].mean()))
        if x["text_sha"] in d:
            dr[p["model"]].append(d[x["text_sha"]])
    return (sorted(statistics.median(v) for v in su.values() if len(v) >= 5),
            sorted(statistics.median(v) for v in dr.values() if len(v) >= 5))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args(argv)
    S, D = aligned_reference()
    pct = lambda v, arr: 100 * sum(1 for x in arr if x < v) / len(arr)   # noqa: E731

    print("open ALIGNED per-model medians (the reference distribution)")
    for lab, arr in (("surprisal", S), ("drift", D)):
        print("  %-10s n=%2d  min %.4f  p25 %.4f  med %.4f  p75 %.4f  max %.4f"
              % (lab, len(arr), arr[0], arr[len(arr)//4], statistics.median(arr),
                 arr[3*len(arr)//4], arr[-1]))

    print("\n%-20s %9s %7s %-18s %4s | %9s %7s %-18s %4s %7s"
          % ("model", "surp", "SE", "95% CI", "pct", "drift", "SE", "95% CI", "pct", "n"))
    for lab, slug in MODELS:
        su, dr = by_stem(slug)
        bs, bd = cluster_boot(su, a.boot), cluster_boot(dr, a.boot)
        if not bs and not bd:
            print("%-20s -- not on disk --" % lab); continue
        sc = ("%9.4f %7.4f [%.4f,%.4f] %3.0f%%" % (bs[0], bs[1], bs[2], bs[3], pct(bs[0], S))
              if bs else "%9s %7s %-18s %4s" % ("--", "--", "", ""))
        dc = ("%9.4f %7.4f [%.4f,%.4f] %3.0f%%" % (bd[0], bd[1], bd[2], bd[3], pct(bd[0], D))
              if bd else "%9s %7s %-18s %4s" % ("--", "--", "", ""))
        print("%-20s %s | %s %7d" % (lab, sc, dc, (bs or bd)[4]))

    print("\nhuman anchor, for scale (no CI -- passage-level, n=500 each)")
    for lab, b, d in HUMAN:
        print("  %-20s %9.4f %31s %9.4f" % (lab, b, "", d))


if __name__ == "__main__":
    main()
