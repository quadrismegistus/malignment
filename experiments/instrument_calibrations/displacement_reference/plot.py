#!/usr/bin/env python
"""plot.py — mass movement speed across OLMo 3 7B's whole released run.

    python .../displacement_reference/plot.py          # -> figures/

Reads `results/curve.json` and plots nothing it computes itself. **The producer
computes, the plotter draws.** A figure that derives its own numbers is a second
producer with no registration, and the two drift.

## THE QUESTION THE FIGURE ANSWERS

Displacement per token decays within every phase -- early pretraining moves the
distribution ~54 JS/T, late SFT ~0.6. So "SFT is faster than pretraining" is true
of the AGGREGATES and tells you nothing about mechanism, because the aggregates
average over stretches of wildly different length.

**The plottable question is whether post-training lies ON the pretraining decay
or ABOVE it.** On it: alignment is just more training, and its apparent
efficiency is an artefact of arriving late and being short. Above it: alignment
moves the distribution at a rate pretraining never reaches at that point in the
run, and is a different kind of operation. The log-log panel is where that is
readable and the bar chart is where it is not.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, "figures")
CURVE = os.path.join(HERE, "results", "curve.json")
FULLVOCAB = os.path.join(HERE, "results", "curve_fullvocab.json")

PHASE_STYLE = {
    "stage1": ("#3b6ea5", "pretraining stage 1 (5.93T)"),
    "stage2": ("#7aa6c2", "midtraining stage 2 (100B)"),
    "stage3": ("#a8c4d8", "long context stage 3 (50B)"),
    "base->SFT": ("#c1440e", "base -> SFT, first 1,000 steps"),
    "SFT": ("#e07a5f", "Think SFT (45.4B)"),
}


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not os.path.exists(CURVE):
        raise SystemExit("no results/curve.json -- run `run.py --curve --write` first")
    doc = json.load(open(CURVE))
    iv = [r for r in doc["intervals"] if r.get("js_per_T")]
    os.makedirs(FIGS, exist_ok=True)

    fv = json.load(open(FULLVOCAB)) if os.path.exists(FULLVOCAB) else None
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.6, 5.2),
                                  gridspec_kw={"width_ratios": [1.5, 1]})

    #: **X IS TOKENS ELAPSED WITHIN THE PHASE, NOT CUMULATIVE, and the first
    #: version of this figure proved why.** On a cumulative axis stages 2 and 3,
    #: the base->SFT jump and all 42 SFT intervals collapse into a single
    #: vertical stripe at 6.08T -- 195B of tokens against a 6,080B run. The panel
    #: could not answer the question it was drawn for. Per-phase elapsed tokens
    #: put every phase on a comparable decay curve, which IS the comparison:
    #: does SFT decay like a continuation of pretraining, or start somewhere
    #: pretraining never was?
    for ph, (c, lab) in PHASE_STYLE.items():
        pts = [r for r in iv if r["phase"] == ph]
        if not pts:
            continue
        t0 = min(r["tokens_from"] for r in pts)
        x = [max((r["tokens_to"] - t0) / 1e9, 1e-3) for r in pts]
        y = [r["js_per_T"] for r in pts]
        ax.plot(x, y, "o-", color=c, ms=3.4, lw=1.1, label=lab, alpha=0.9)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("tokens elapsed WITHIN the phase (billions, log)")
    ax.set_ylabel("JS per trillion tokens (log)")
    ax.set_title("Mass movement speed — each phase from its own start",
                 loc="left", fontsize=11)
    ax.grid(alpha=0.25, which="both", lw=0.4)
    ax.legend(fontsize=7.5, frameon=False, loc="lower left")
    init = [r for r in iv if r["from"].endswith("step0")]
    ax.text(0.985, 0.965,
            "every phase decays.\nthe question is the HEIGHT it starts at",
            transform=ax.transAxes, ha="right", va="top", fontsize=7, color="#555")

    #: **RIGHT PANEL: twp AGAINST FULL VOCABULARY, which is the panel that
    #: changed a conclusion.** I predicted top-N truncation would HIDE alignment
    #: effects among rare words. It does the opposite: twp agrees with the full
    #: 100,278-token vocabulary on pretraining to within 8% and INFLATES SFT by
    #: ~50%, because alignment concentrates on exactly the high-probability words
    #: twp keeps while the untouched tail dilutes it at full vocabulary. Drawn
    #: rather than stated because the direction of a bias is what nobody guesses.
    import statistics as _st
    if fv:
        fvi = [r for r in fv["intervals"] if r.get("js")]
        key = lambda r: (r["from"], r["to"])
        tw = {key(r): r["js"] for r in iv}
        order = ["stage1", "stage2", "stage3", "base->SFT", "SFT"]
        labs, a_tw, a_fv, cols = [], [], [], []
        for ph in order:
            g = [r for r in fvi if r["phase"] == ph]
            paired = [(r["js"], tw[key(r)]) for r in g if key(r) in tw]
            if not paired:
                continue
            labs.append(PHASE_STYLE[ph][1].split(" (")[0])
            a_fv.append(_st.median([f for f, _ in paired]))
            a_tw.append(_st.median([t for _, t in paired]))
            cols.append(PHASE_STYLE[ph][0])
        y = range(len(labs))
        ax2.barh([v + 0.19 for v in y], a_tw, height=0.36, color=cols,
                 alpha=0.45, label="twp (top-N + tail)")
        ax2.barh([v - 0.19 for v in y], a_fv, height=0.36, color=cols,
                 label="full vocabulary (100,278)")
        for k, (t, f) in enumerate(zip(a_tw, a_fv)):
            ax2.text(max(t, f) * 1.1, k, "x%.2f" % (f / t), va="center", fontsize=7.5)
        ax2.set_yticks(list(y))
        ax2.set_yticklabels(labs, fontsize=8)
        ax2.invert_yaxis()
        ax2.set_xscale("log")
        ax2.set_xlabel("median interval JS (log)")
        ax2.set_title("truncation bias: twp vs full vocabulary", loc="left", fontsize=10)
        ax2.legend(fontsize=7, frameon=False, loc="lower right")
        ax2.grid(alpha=0.25, axis="x", which="both", lw=0.4)

    fig.suptitle("OLMo 3 7B: how fast training moves the word distribution  ·  "
                 "%d released intervals  ·  right panel %s"
                 % (doc["n_intervals"],
                    "400 prompts at full vocabulary" if fv else "twp only"),
                 fontsize=10.5, x=0.012, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = os.path.join(FIGS, "mass_movement_speed.png")
    fig.savefig(out, dpi=170)
    fig.savefig(out.replace(".png", ".svg"))
    print("  wrote %s (+ .svg)" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
