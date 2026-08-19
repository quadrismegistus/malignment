"""Per-model twp throughput, recorded as OBSERVATIONS rather than as a constant.

    from malignment import rates
    rates.record(model=..., device="cuda", n_cells=277, load_s=141.0, compute_s=53.0)
    sec, why = rates.rate_for("bigscience/bloom-7b1", "cuda")

## WHY THIS EXISTS

The fleet planner carried `SEC_PER_CELL = 0.8`, then `0.19`, and BOTH were single
measurements on single models quoted as properties of the work:

    0.8    MPS, measured here, used to plan a CUDA fleet        4x too slow
    0.19   CUDA, measured on ONE model (kanana, 8B)             ~3x too fast
           for bloom-7b1, whose vocabulary is 250,880

Correcting the first to the second fixed the DEVICE and left the sampling error
untouched, which is how the same class of error survived its own correction. A
rate is not a property of twp. It is a property of (model x device x tranche),
and the only honest fix is to stop asserting one number and start recording what
we observe.

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

**`vocab_size`.** The plausible driver, and the only field here that lets us
PREDICT for a model we have never run -- which is most of them. twp expands a
beam over the token tree, so vocabulary is the mechanism, not a correlate. Stored
so the guess can later be checked rather than assumed.

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
#: What they actually are: cuda is roughly midway between the only two CUDA
#: numbers anyone has seen (0.19 on kanana-8B, ~0.6 on bloom-7b1 with its 250,880
#: vocabulary), and mps is the long-standing 0.8-1.9 range from this Mac. They
#: exist so a plan can be priced at all, and every caller that uses one is told.
#: Re-derive from real data with `summary()` once the store fills.
FALLBACK = {"cuda": 0.35, "mps": 1.2}


def record(model, device, n_cells, compute_s, load_s=None, gpu=None,
           vocab_size=None, rules=None, only=None, topup=False, path=PATH):
    """Append one observation. Never overwrites: rates drift with code and card.

    Append-only because a rate is an OBSERVATION, and the campaign's rule is that
    observations accumulate while verdicts are derived. Overwriting would make
    "we measured this twice and got different answers" unrepresentable, which is
    exactly the state that tells you the rate depends on something you are not
    recording.
    """
    if not n_cells or n_cells <= 0 or compute_s is None:
        return None
    obs = {"model": model, "device": device, "gpu": gpu, "vocab_size": vocab_size,
           "rules": rules, "only": only, "topup": bool(topup),
           "n_cells": int(n_cells), "load_s": None if load_s is None else round(load_s, 1),
           "compute_s": round(compute_s, 1),
           "sec_per_cell": round(compute_s / float(n_cells), 4),
           "observed": time.strftime("%Y-%m-%dT%H:%M:%S")}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obs) + "\n")
    return obs


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
    vals = sorted(o["sec_per_cell"] for o in cand)
    med = vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1]
                                                     + vals[len(vals) // 2]) / 2.0
    return med, ("median of %d obs, n_cells %d..%d"
                 % (len(cand), min(o["n_cells"] for o in cand),
                    max(o["n_cells"] for o in cand)))


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
