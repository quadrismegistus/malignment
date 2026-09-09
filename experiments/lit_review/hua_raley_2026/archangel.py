#!/usr/bin/env python
"""The KL tether, isolated: one base, one data mixture, five objectives.

    python archangel.py

## WHY THIS SET

`ContextualAI/archangel_*_pythia2-8b` is the design CLAIM 2 needs and PKU's
ladder cannot supply. Same base, same preference mixture, objectives that differ
in whether they carry a tether to the reference model:

    sft        cross-entropy on demonstrations      NO KL
    sft-ppo    PPO-RLHF                             EXPLICIT KL penalty
    sft-dpo    DPO                                  implicit KL
    sft-kto    KTO                                  implicit KL, different loss
    sft-slic   SLiC, a ranking/calibration loss     NO KL

If the tether produces the conservatism, the tethered objectives should behave
differently from SLiC, from the same starting point.

## READ THE THRESHOLD, NOT THE VERDICT

**A first pass reported "0 to 11 fallers, too quiet to discriminate" and that was
a rule-gated count read as a movement measure.** CANONICAL calls a word a faller
only if `p_aligned < 0.5*p_base` AND `p_base >= 0.003`. At these magnitudes
almost nothing halves, so the count reports the RULE and not the distribution.

This file therefore prints raw `|delta|` quantiles and threshold counts, which
are not gated by any classification rule, alongside the llama ladder for scale.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

A = "ContextualAI/archangel_%s_pythia2-8b"
BASE = "EleutherAI/pythia-2.8b"
SFT = A % "sft"
STEPS = [("base->SFT   (no KL)", BASE, SFT),
         ("base->PPO   (both)", BASE, A % "sft-ppo"),
         ("SFT->KTO    (impl KL)", SFT, A % "sft-kto"),
         ("SFT->SLiC   (NO KL)", SFT, A % "sft-slic"),
         ("SFT->DPO    (impl KL)", SFT, A % "sft-dpo"),
         ("SFT->PPO    (EXPL KL)", SFT, A % "sft-ppo")]
SCALE = ("llama->alpaca", "huggyllama/llama-7b",
         "PKU-Alignment/alpaca-7b-reproduced")


def row(a, b):
    from malignment import vectors as V
    return V.rows(
        "SELECT max(abs(delta)) mx, quantile(0.999)(abs(delta)) q999, "
        "countIf(abs(delta)>0.05) big, countIf(abs(delta)>0.01) med, "
        "countIf(cls='faller') fall, count() n FROM movement_v4 "
        "WHERE base={a:String} AND aligned={b:String} AND rule='canonical' "
        "AND frame_base='' AND frame_aligned=''", a=a, b=b)[0]


def main():
    print("ARCHANGEL pythia2-8b -- the KL tether isolated")
    print("%-24s %9s %10s %9s %9s %9s" % ("step", "max|d|", "p99.9|d|",
                                          "|d|>0.05", "|d|>0.01", "fallers"))
    for name, a, b in STEPS:
        r = row(a, b)
        print("%-24s %9.4f %10.5f %9d %9d %9d"
              % (name, r["mx"], r["q999"], r["big"], r["med"], r["fall"]))
    r = row(SCALE[1], SCALE[2])
    print("%-24s %9.4f %10.5f %9d %9d %9d   <- for scale"
          % (SCALE[0], r["mx"], r["q999"], r["big"], r["med"], r["fall"]))
    print()
    print("READING: about 10 to 30x smaller than a full SFT, and NOT zero. The")
    print("faller column is the rule's threshold, not the movement -- compare it")
    print("against |d|>0.01 on the same row.")
    print()
    print("The posttraining ordering at |d|>0.01 puts the only EXPLICIT KL")
    print("lowest, weakly as the tether predicts. But KTO carries an implicit KL")
    print("and moves most, so the objectives do NOT separate on the tether.")
    print()
    from malignment import vectors as V
    print("largest single moves on base->PPO:")
    for x in V.rows("SELECT word, prompt, p_base, p_aligned, delta FROM movement_v4 "
                    "WHERE base={a:String} AND aligned={b:String} AND rule='canonical' "
                    "AND frame_base='' AND frame_aligned='' ORDER BY abs(delta) DESC "
                    "LIMIT 5", a=BASE, b=A % "sft-ppo"):
        print("   %-8s %.4f -> %.4f  (%+.4f)  %s"
              % (x["word"], x["p_base"], x["p_aligned"], x["delta"], x["prompt"][:44]))
    print("\n   `sex` and `beat` RISING under RLHF is not what a pure suppression")
    print("   story predicts. Two cells, not a finding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
