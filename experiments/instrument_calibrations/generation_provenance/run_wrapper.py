"""How far does "Continue this text:" move a model on these axes?

    python .../run_wrapper.py

`build_wrapper_pool.py` built and scored this pool and names this file as its
analyser. The file did not exist, so the pool sat scored on both axes and unread.

## WHY THIS IS NOT AN OPTIONAL EXTRA

**The API models in `two_axes.py` were generated behind a wrapper** -- a system
prompt asking for a continuation -- because a chat endpoint has no completion
mode. The open models were not. So every API-versus-open contrast in this folder,
including `stem_paired.py`'s `API - aligned` result, carries a difference in
DEPLOYMENT FRAME alongside the difference in model.

That confound cannot be designed away: a base model handed "Continue this text:"
continues that string rather than obeying it. But it can be ESTIMATED on models
where both conditions exist, and six of them do -- 59 shared prompts, raw and
`continue`, the same checkpoint in both. This file estimates it and states it in
the same units as the contrast it threatens.

## THIS IS NOT THE SAME FRAME AS THE API MODELS' AND CANNOT BE PORTED 1:1

Checked in the producers rather than assumed:

    wrapper pool   `core.py:231` -- ONE USER TURN, no system message:
                   [{"role": "user", "content": "Continue this text: " + stem}]
    the API models `generate_task.py:135,280` -- a SYSTEM message, stem as a
                   separate user turn: "Continue this text for 200-250 words.
                   Do not repeat the text you are given."

Three differences, not one: the instruction sits in a different role, the stem
sits in a different turn, and the API instruction carries two constraints this
one has no equivalent of -- a length target, and **"Do not repeat the text you
are given"**.

**That last one plausibly pushes drift in the OPPOSITE direction to what is
measured here.** An instruction not to repeat the given text is an instruction to
move away from it, and moving away from the opening is what the drift axis
measures. So this pool does not bound our frame's effect on drift even in sign.

What it therefore does and does not license:

    DOES    a magnitude statement -- frame effects on these axes are large,
            surprisal moving ~6x the entire API-aligned gap
    DOES    the general claim that an unestimated frame difference is a serious
            confound on any API-versus-open contrast, not a footnote
    DOES NOT any per-row verdict on `stem_paired.py`'s results, in either
            direction. "The API drift result survives because the wrapper pushes
            the other way" is NOT supported: it assumes a portability that the
            three differences above defeat.

Estimating OUR frame needs our frame run against a bare condition on models where
both are possible, which is what `../../instrument_calibrations/frame_prefill/`
is for and is not what this pool is.

## THE UNIT IS THE MODEL, AND THERE ARE SIX

Paired within (model, prompt), then one number per model, then a sign test over
six. **Six is small and the floor is visible: an exact two-sided sign test on
n=6 cannot go below p=0.03125**, which a 6-0 split reaches and nothing else does.
So this instrument can show a consistent direction and cannot show a small one,
and the effect SIZE relative to the API contrast is what it is for -- not its
p-value.

## THE PREFIX IS M=64 AND THAT LIMITS WHAT THE SIZING MEANS

Everything else here takes surprisal over the first 200 tokens. This pool was
generated at roughly 100, so M=200 retains NOTHING -- the run that discovered
this dropped all 4,437 passages and said so rather than returning a number. M=64
retains 94.7% of raw and 94.3% of continue.

So the wrapper DIFFERENCE is measured on a shorter prefix than the API contrast
it is sized against. Both sides of the difference use the same prefix, so the
difference is internally valid; the ratio against a 200-token contrast is an
order-of-magnitude comparison and is not a correction. Nothing is subtracted from
anything.

## THE QUADRANT REFERENCE IS THE ONE quadrants.csv USED

z-scores and the OLS line come from `results/quadrants.manifest.json`, so a
wrapper passage lands in the same plane as every other passage in this folder.
Re-centring on this pool would put its 4,437 rows in a private coordinate system
and make the comparison meaningless.
"""

import argparse, collections, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
#: this folder measures the INSTRUMENT; the corpus and its axes live in
#: `passage_analysis/jakobson_space`, and three things are read from there
#: rather than copied: the API system prompt (so a frame test tests THE frame),
#: `results/quadrants.csv` (the passage population) and its manifest (the
#: z-score reference the whole plane is centred on). Copying any of them would
#: make this folder's numbers drift from the ones they qualify.
JAK = os.path.abspath(os.path.join(HERE, "..", "..", "passage_analysis",
                                   "jakobson_space"))
sys.path.insert(0, JAK)

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
WRAP = os.path.join(DATA, "wrapper_confound")
MAN = os.path.join(JAK, "results", "quadrants.manifest.json")
#: **NOT 200.** This pool was generated at ~100 tokens, not the corpus's 256, so
#: the standard M=200 prefix retains ZERO passages in both conditions. M=64 keeps
#: 94.7% of raw and 94.3% of continue -- near-balanced, so differential retention
#: is not doing the work. The consequence is stated in the docstring: the LEVEL
#: of a surprisal over 64 tokens is not comparable to one over 200, though the
#: DIFFERENCE between two conditions measured at the same M is internally valid.
M_TOKENS = 64
QS = ["(+surp +drift)", "(+surp -drift)", "(-surp +drift)", "(-surp -drift)"]
NAME = {"(-surp +drift)": "metonymic", "(+surp -drift)": "metaphoric",
        "(+surp +drift)": "breakdown", "(-surp -drift)": "unmarked"}


def sign_test(v):
    v = [x for x in v if x != 0]
    n, up = len(v), sum(1 for x in v if x > 0)
    if not n:
        return 0, 0, 0, float("nan"), float("nan")
    k = max(up, n - up)
    return n, up, n - up, statistics.median(v), min(
        1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-per-cell", type=int, default=3)
    a = ap.parse_args(argv)
    import numpy as np

    man = json.load(open(MAN))
    mS, sS = man["mean"]["surprisal"], man["sd"]["surprisal"]
    mR, sR = man["mean"]["drift_residual"], man["sd"]["drift_residual"]
    a0, b0 = man["ols"]["intercept"], man["ols"]["slope"]

    pool = {}
    for line in open(os.path.join(DATA, "ref_pool", "ref_pool.jsonl")):
        j = json.loads(line)
        if j.get("pool") == "wrapper":
            pool[j["id"]] = j
    sur = np.fromfile(os.path.join(DATA, "ref_pool", "deepseek", "ref_shard00.f32"),
                      dtype=np.float32)
    drift = {}
    for line in open(os.path.join(WRAP, "bge", "drift.jsonl")):
        y = json.loads(line)
        if y.get("mean_drift") is not None:
            drift[y["id"]] = y["mean_drift"]

    rows, lost = [], collections.Counter()
    for line in open(os.path.join(DATA, "ref_pool", "deepseek", "ref_shard00.jsonl")):
        x = json.loads(line)
        p = pool.get(x["id"])
        if not p:
            continue
        if x["n"] < M_TOKENS:
            lost["under %d tokens" % M_TOKENS] += 1
            continue
        #: the bge sidecar keys on `wrapper_id` (`raw-*` / `continue-*`), not on
        #: the ref_pool `wrap-*` id. Joining on the wrong one returns 0 of 4,437
        #: -- which it did, loudly, before this line was right.
        d = drift.get(p["wrapper_id"])
        if d is None:
            lost["no drift row"] += 1
            continue
        s = float(sur[x["row"]:x["row"] + M_TOKENS].mean())
        zs = (s - mS) / sS
        zr = ((d - (a0 + b0 * s)) - mR) / sR
        q = ("(+surp +drift)" if zs > 0 and zr > 0 else "(+surp -drift)" if zs > 0
             else "(-surp +drift)" if zr > 0 else "(-surp -drift)")
        rows.append(dict(model=p["model"], prompt=p["prompt"], mode=p["mode"],
                         surprisal=s, drift=d, quadrant=q))

    print("wrapper pool: %s scored passages over %d models, %d prompts"
          % ("{:,}".format(len(rows)), len({r["model"] for r in rows}),
             len({r["prompt"] for r in rows})))
    for k, v in sorted(lost.items()):
        print("  dropped %-24s %d" % (k, v))
    print("  by mode: %s" % dict(collections.Counter(r["mode"] for r in rows)))

    #: paired within (model, prompt): only prompts the model ran BOTH ways.
    per = collections.defaultdict(lambda: collections.defaultdict(dict))
    for r in rows:
        per[r["model"]][r["prompt"]].setdefault(r["mode"], []).append(r)
    out = {}
    for m, byp in per.items():
        got = collections.defaultdict(list)
        for p, d in byp.items():
            if len(d.get("continue", [])) < a.min_per_cell \
               or len(d.get("raw", [])) < a.min_per_cell:
                continue
            for lab in ("surprisal", "drift"):
                got[lab].append(statistics.median(x[lab] for x in d["continue"])
                                - statistics.median(x[lab] for x in d["raw"]))
            for q in QS:
                got[q].append(
                    sum(1 for x in d["continue"] if x["quadrant"] == q) / len(d["continue"])
                    - sum(1 for x in d["raw"] if x["quadrant"] == q) / len(d["raw"]))
        if got:
            out[m] = {k: statistics.mean(v) for k, v in got.items()}
            out[m]["_n"] = len(byp)

    print("\nCONTINUE - RAW, paired within (model, prompt), %d models" % len(out))
    print("%-28s %10s %5s %5s %10s" % ("", "median", "up", "dn", "p"))
    for lab in ["surprisal", "drift"] + QS:
        n, up, dn, med, p = sign_test([out[m][lab] for m in out])
        nm = lab if lab in ("surprisal", "drift") else "%s %s" % (lab, NAME[lab])
        print("%-28s %+10.4f %5d %5d %10.3g" % (nm, med, up, dn, p))
    print("  the sign-test floor at n=6 is p=0.03125; only a 6-0 split reaches it.")

    #: Put the wrapper effect beside the contrast it threatens, in the same
    #: units. THIS IS A MAGNITUDE COMPARISON ONLY -- see the docstring: the two
    #: frames are not the same frame, so no per-row verdict is drawn from it.
    API = {"surprisal": -0.0852, "drift": +0.0085, "(-surp +drift)": +0.1569,
           "(+surp -drift)": -0.0923}
    if not out:
        print("\nno model had >= %d passages in both conditions on any prompt "
              "-- nothing to size." % a.min_per_cell)
        return
    print("\nSIZED AGAINST `stem_paired.py`'s API - ALIGNED contrast")
    print("(that contrast is measured at M=200 and this at M=%d; an "
          "order-of-magnitude read)" % M_TOKENS)
    print("%-28s %12s %12s %10s" % ("", "wrapper", "API-aligned", "ratio"))
    for lab, v in API.items():
        w = statistics.median([out[m][lab] for m in out])
        nm = lab if lab in ("surprisal", "drift") else "%s %s" % (lab, NAME[lab])
        print("%-28s %+12.4f %+12.4f %9.0f%%"
              % (nm, w, v, 100 * abs(w / v) if v else float("nan")))
    print("\nDO NOT READ THE SIGNS AS A VERDICT ON THE API ROWS. The two frames")
    print("differ in placement and in content (see the docstring), and one of the")
    print("differences plausibly acts on drift in the OPPOSITE direction to what")
    print("is measured here. What this table licenses is a magnitude statement:")
    print("frame effects on these axes are LARGE -- surprisal moves ~6x the whole")
    print("API-aligned gap -- so an unestimated frame difference is a serious")
    print("confound and not a footnote. It does not license a correction.")


if __name__ == "__main__":
    main()
