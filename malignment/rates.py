"""Per-model twp throughput, recorded as OBSERVATIONS rather than as a constant.

    from malignment import rates
    rates.record(model=..., device="cuda", n_cells=277, load_s=141.0, compute_s=53.0)
    sec, why = rates.rate_for("bigscience/bloom-7b1", "cuda")

## WHY THIS EXISTS

The fleet planner carried `SEC_PER_CELL = 0.8`, then `0.19`, and BOTH were single
measurements on single models quoted as properties of the work:

    0.8    MPS, measured here, used to plan a CUDA fleet        4x too slow
    0.19   CUDA, measured on ONE model (kanana, 8B), then
           applied to 144 models spanning 0.155 to 6.04 s/cell

Correcting the first to the second fixed the DEVICE and left the sampling error
untouched, which is how the same class of error survived its own correction. A
rate is not a property of twp. It is a property of (model x device x tranche),
and the only honest fix is to stop asserting one number and start recording what
we observe.

**CORRECTED 2026-08-19, same session.** This paragraph first explained the 0.19
vs 0.855 gap by bloom-7b1's 250,880-token vocabulary. Both halves were wrong:
0.19 is CUDA and 0.855 is MPS, so it was a CROSS-DEVICE comparison explained by a
model property -- and the vocabulary claim is refuted on our own data. Measured
over 107 MPS observations with a local config:

    r(log params, log sec/cell)  =  +0.541
    r(log vocab,  log sec/cell)  =  -0.050

Size is the driver; vocabulary carries nothing. Qwen2.5-0.5B has a 151,936-token
vocabulary and runs at 0.233, Mistral-7B has 32,000 and runs at 2.757. The claim
had been asserted in three places before anyone tested it, including in the
docstring of the function built to stop exactly this.

RH: *"why don't we store model-specific twp rates?"*

## WHAT AN OBSERVATION MUST CARRY, AND WHY EACH FIELD IS THERE

**`n_cells`, always, next to the ratio.** The OLMoE deferral this morning came
from three-cell samples read as throughput: at n=3 a cold load is most of the
wall clock, so the ratio measured `load/3` and wore a `s/cell` label. It removed
four models from a roster. **A ratio that does not carry its own sample size
cannot be doubted by the person reading it**, so `rate_for` REFUSES below
`MIN_CELLS` rather than returning a number with a caveat attached -- a caveat is
not load-bearing and gets dropped at the first paraphrase.

**`load_s` and `compute_s` separately, never summed.** Same defect, at the
source. Load is paid once per arm; compute is paid per cell. A fleet plans on
compute and budgets load as a constant, and a single blended number cannot answer
either question.

**`vocab_size`.** Stored as a CANDIDATE predictor so the guess could be checked
rather than assumed -- and it was checked, and it failed (r = -0.05 in log-log
over 107 models). Kept because a refuted predictor is worth keeping refuted, and
because the field costs nothing. **Parameter count is the one that carries signal
(r = +0.54), and it is not stored here yet** -- it comes from the config, which
this module does not read. That is the honest state, not a plan.

**`device` and `gpu`.** MPS and CUDA differ ~4x, and cards differ among
themselves.

**`only`.** The CJK tranche costs more per cell than Latin -- deeper beams on
byte-level surfaces. A rate measured on slots does not transfer to a full run.

## WHAT THIS DELIBERATELY DOES NOT DO

It does not average across devices, and it does not fall back silently. A caller
that gets `None` is told WHY in the same return, and the fleet planner prints the
models it had to guess for. **An estimate whose provenance is invisible is how a
3-cell sample reached a governing document in the first place.**
"""
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(os.path.dirname(HERE), "data", "model_twp_rates.jsonl")

#: Below this, a run is mostly cold load and the ratio is not a throughput. 25 is
#: the heartbeat interval in `runners.run`, so it is also the smallest sample the
#: producer can report having actually timed over more than a couple of loads.
MIN_CELLS = 25

#: **THESE ARE GUESSES AND THE ONLY HONEST THING TO SAY ABOUT THEM IS THAT.** The
#: first draft of this line claimed they were the "median over recorded
#: observations" -- written at a moment when the store held ZERO observations, so
#: the provenance was invented in the same file whose whole purpose is that a rate
#: must carry where it came from. Caught by running the planner, which printed
#: `0 of 144 models have a RECORDED rate`.
#:
#: What they actually are: `cuda` sits between the only two CUDA numbers anyone
#: has seen (0.199 on kanana-8B; ~0.6 inferred from the bloom-7b1 box's poll
#: deltas, which is coarse), and `mps` is the median of the 115 stash-derived MPS
#: observations. They exist so a plan can be priced at all, and every caller that
#: uses one is told. Re-derive with `summary()` as the store fills.
#:
#: A third version of this comment explained the CUDA spread by bloom's
#: vocabulary. Refuted -- see the module docstring. **Two files were corrected
#: before anyone re-read this line**, which is why a withdrawal has to be a grep
#: for the claim's EFFECTS and not only for the sentence that stated it.
FALLBACK = {"cuda": 0.35, "mps": 1.2}


def record(model, device, n_cells, compute_s, load_s=None, gpu=None,
           vocab_size=None, rules=None, only=None, topup=False,
           median_delta=None, path=PATH):
    """Append one observation. Never overwrites: rates drift with code and card.

    Append-only because a rate is an OBSERVATION, and the campaign's rule is that
    observations accumulate while verdicts are derived. Overwriting would make
    "we measured this twice and got different answers" unrepresentable, which is
    exactly the state that tells you the rate depends on something you are not
    recording.

    **`median_delta` WINS OVER `compute_s / n_cells` WHEN PRESENT**, and the
    fallback is kept only for callers that cannot supply it. `compute_s / n_cells`
    telescopes to the MEAN of the inter-cell deltas, and across this corpus the
    mean is not a throughput at all: 86 of 108 stash files carry a gap over 60 s
    and the largest is 79 hours, so on SmolLM2-360M the mean reads 317 s/cell
    against a true 0.131. A cancelled-and-resumed run is the normal case here.
    """
    if not n_cells or n_cells <= 0 or compute_s is None:
        return None
    spc = median_delta if median_delta else compute_s / float(n_cells)
    obs = {"model": model, "device": device, "gpu": gpu, "vocab_size": vocab_size,
           "rules": rules, "only": only, "topup": bool(topup),
           "n_cells": int(n_cells), "load_s": None if load_s is None else round(load_s, 1),
           "compute_s": round(compute_s, 1),
           "sec_per_cell": round(spc, 4),
           "estimator": "median_delta" if median_delta else "mean_span",
           "observed": time.strftime("%Y-%m-%dT%H:%M:%S")}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obs) + "\n")
    return obs


def from_stash(root=None, path=PATH, write=True, min_cells=MIN_CELLS):
    """Derive observations from `__written_at__`, for every model ever measured.

    **RH: "is the box writing to the jsonl stash? each key a __created_at__?"** It
    is -- `__written_at__`, a float epoch on every record, all distinct. Which
    means this was never a going-forward problem: the timing for all 106 measured
    models has been on disk the whole time.

    I checked ClickHouse, found `mtime` was per-FILE, concluded "the corpus cannot
    answer this" and built a forward-only recorder. The stash is the PRODUCER'S OWN
    OUTPUT and I did not open it -- the exact rung this campaign's own rule names,
    applied to the wrong store one step earlier in the pipeline.

    ## THE MEDIAN OF CONSECUTIVE DELTAS, NOT (last - first) / n

    Deltas between consecutive writes measure per-cell cost DIRECTLY, and the
    median of them is immune to the two things that wreck a span average:

        the cold load          sits before the first record, so it is not in any
                               delta at all -- the OLMoE defect cannot occur here
        pauses and requeues    a run resumed hours later contributes ONE huge
                               delta, which a median ignores and a mean does not

    So this is a better instrument than the one `run()` records live, and it needs
    no cooperation from the producer. `p90` is kept beside it because a model whose
    p90 is far above its median is one whose cost depends on the PROMPT, and a
    single number will mislead whoever plans with it.
    """
    import glob
    root = root or os.path.expanduser(
        os.environ.get("MALIGNMENT_DATA", "~/malignment-data") + "/twp")
    out = []
    for f in sorted(glob.glob(os.path.join(root, "*", "*", "jsonl.hashstash.raw",
                                           "data.jsonl"))):
        by = {}
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            t = d.get("__written_at__")
            if not isinstance(t, (int, float)):
                continue
            k = d.get("__key__") or {}
            by.setdefault((d.get("model") or k.get("model"),
                           d.get("device"),
                           k.get("rules") or d.get("rules"),
                           bool(k.get("topup"))), []).append(t)
        for (model, device, rules, topup), ts in by.items():
            if not model or len(ts) < min_cells:
                continue
            ts.sort()
            dl = sorted(ts[i + 1] - ts[i] for i in range(len(ts) - 1))
            if not dl:
                continue
            med = dl[len(dl) // 2]
            obs = {"model": model, "device": device, "gpu": None,
                   "vocab_size": None, "rules": rules, "only": None,
                   "topup": topup, "n_cells": len(ts), "load_s": None,
                   "compute_s": round(med * len(ts), 1),
                   "sec_per_cell": round(med, 4),
                   "p90_sec_per_cell": round(dl[int(len(dl) * 0.9)], 4),
                   "source": "stash:__written_at__",
                   "observed": time.strftime("%Y-%m-%dT%H:%M:%S",
                                             time.localtime(ts[-1]))}
            out.append(obs)
    if write and out:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        #: **REWRITTEN, not appended.** Every row here is DERIVED from the stash,
        #: so re-running must not multiply them -- unlike `record()`, whose rows
        #: are live observations that legitimately accumulate. Live rows are
        #: preserved: only stash-derived ones are replaced.
        keep = [o for o in load(path) if o.get("source") != "stash:__written_at__"]
        with open(path, "w", encoding="utf-8") as fh:
            for o in keep + out:
                fh.write(json.dumps(o) + "\n")
    return out


def load(path=PATH):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def rate_for(model, device, only=None, min_cells=MIN_CELLS, obs=None):
    """(sec_per_cell, provenance) for this model on this device, or (None, why).

    **Returns the MEDIAN of qualifying observations, not the mean and not the
    latest.** The mean is dragged by one slow box on a shared card; the latest
    throws away every earlier measurement for no reason but recency.
    """
    obs = load() if obs is None else obs
    cand = [o for o in obs
            if o.get("model") == model and o.get("device") == device
            and not o.get("topup") and (o.get("n_cells") or 0) >= min_cells
            and (only is None or o.get("only") == only)]
    if not cand:
        seen = [o for o in obs if o.get("model") == model]
        if seen:
            return None, ("no qualifying observation for %s on %s (have %d on %s, "
                          "largest n=%d)" % (model, device, len(seen),
                                             sorted({o.get("device") for o in seen}),
                                             max(o.get("n_cells", 0) for o in seen)))
        return None, "never measured: %s" % model
    #: **A `mean_span` ROW IS DROPPED IF ANY DELTA-BASED ROW EXISTS.** They are not
    #: two measurements of one quantity: across this corpus the span mean runs
    #: thousands of times the true rate whenever a run was resumed, so averaging
    #: the two estimators together would import that error at reduced strength
    #: rather than removing it.
    good = [o for o in cand if o.get("estimator") != "mean_span"]
    cand, dropped = (good, len(cand) - len(good)) if good else (cand, 0)
    vals = sorted(o["sec_per_cell"] for o in cand)
    med = vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1]
                                                     + vals[len(vals) // 2]) / 2.0
    return med, ("median of %d obs, n_cells %d..%d%s"
                 % (len(cand), min(o["n_cells"] for o in cand),
                    max(o["n_cells"] for o in cand),
                    "; %d mean_span row(s) dropped" % dropped if dropped else ""))


def estimate(models, device, only=None, fallback=True):
    """{model: (sec, provenance)} plus the list of models that had to be guessed.

    The guessed list is RETURNED, not logged, so a caller cannot use the estimate
    without being handed the fact that part of it is a default.
    """
    obs = load()
    out, guessed = {}, []
    for m in models:
        sec, why = rate_for(m, device, only=only, obs=obs)
        if sec is None:
            if not fallback:
                out[m] = (None, why)
                guessed.append(m)
                continue
            sec = FALLBACK.get(device, FALLBACK["cuda"])
            why = "FALLBACK %s (%s)" % (device, why)
            guessed.append(m)
        out[m] = (sec, why)
    return out, guessed


def summary(obs=None):
    """Per (model, device) rows, for eyeballing and for re-deriving FALLBACK."""
    obs = load() if obs is None else obs
    by = {}
    for o in obs:
        if o.get("topup") or (o.get("n_cells") or 0) < MIN_CELLS:
            continue
        by.setdefault((o["model"], o["device"]), []).append(o)
    rows = []
    for (m, d), os_ in sorted(by.items()):
        v = sorted(x["sec_per_cell"] for x in os_)
        rows.append({"model": m, "device": d, "n_obs": len(os_),
                     "cells": sum(x["n_cells"] for x in os_),
                     "vocab_size": next((x.get("vocab_size") for x in os_
                                         if x.get("vocab_size")), None),
                     "min": v[0], "median": v[len(v) // 2], "max": v[-1]})
    return rows
