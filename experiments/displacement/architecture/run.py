#!/usr/bin/env python
"""Does the displacement operation depend on the ATTENTION MECHANISM?

    python run.py

## WHY THIS EXISTS

Weatherby's *Language Machines* (2025) claims the transformer's attention
mechanism realises Jakobson's poetic function -- "the transformer architecture
gives us quantitative aboutness" (161-62) -- and that computation and language
"share form" as "a demonstrable technical fact". He hedges once: attention is
"probably just one way -- we do not yet know of any others -- to make this
function computationally manipulable" (155), and a note mentions Google's
Griffin, "RNNs with local attention" (227n26).

**That model is in this census, beside one with no attention at all.** If the
operation recurs without attention, the claim is architecture-general and the
transformer demonstrates nothing that autoregression had not.

## THE METADATA IS DECLARED HERE AND SOURCED

`roster/models/models.yaml` carries no architecture field. What it carries is
`env.profile`, an ENVIRONMENT requirement -- `ssm` means the model needs
mamba-ssm and causal-conv1d kernels -- which happens to pick out the SSM and
hybrid families exactly, with its own `why`. The rest comes from
`roster/models/attestations.json`, whose notes carry sourced architecture quotes
at `confidence: high`. Both are cited per model below.

**DEFAULT IS DENSE TRANSFORMER WITH FULL ATTENTION.** Only departures are coded.

## TWO AXES, BECAUSE THEY CROSS

    attn   full | full+linear | local+linear | full+ssm | linear | none
    block  dense | moe | ssm | hybrid

`recurrentgemma` is local attention AND linear recurrence; `Olmo-Hybrid` is full
attention AND linear attention. One axis would have to collapse them.

## THE FOUR MATCHED CONTRASTS, BEST FIRST

    1  Olmo-3-1025-7B vs Olmo-Hybrid-7B   CONTROLLED BY DESIGN. Same lab, same
       three-stage pipeline, same improved data mix, 5.93T vs 5.50T tokens, and
       the paper states the only architectural difference: "largely comparable
       to Olmo 3 7B but with the sliding window layers replaced by Gated
       DeltaNet layers" (arXiv:2604.03444, quoted in attestations.json). AI2
       built it as "a controlled, large-scale setting".
    2  gemma-2-9b vs recurrentgemma-9b    Same pretraining corpus, attested:
       "RecurrentGemma uses the same training data and data processing as used
       by the Gemma model family"; "The architecture is Griffin, not Gemma's
       transformer". The attestation flags this as an INDEPENDENCE problem;
       for this question it is the control.
    3  tiiuae at ~7B                      falcon-7b and Falcon3-7B (dense) vs
       falcon-mamba-7b (pure SSM) vs Falcon-H1-7B (hybrid). One vendor, three
       block types, comparable scale. Data not attested as shared.
    4  Olmo-3-1025-7B vs OLMoE-1B-7B      dense vs mixture-of-experts, one lab.

## WHAT THIS CAN AND CANNOT SHOW

**n is tiny on the side that matters: ONE pure SSM and ONE linear-attention-only
model in the endpoint roster.** This reports where each architecture sits in the
distribution of 50 and runs NO between-group test. "Attention-free" is also
confounded with vendor, scale, vintage and data everywhere except contrasts 1
and 2, which is why those two are first.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))

#: DEPARTURES FROM (dense, full attention). Everything unlisted is the default.
#: Each entry cites where the classification comes from.
ARCH = {
    "tiiuae/falcon-mamba-7b":
        ("none", "ssm",
         "models.yaml env.profile=ssm; Mamba SSM, no attention"),
    "tiiuae/Falcon-H1-1.5B-Base":
        ("full+ssm", "hybrid",
         "models.yaml env.profile=ssm; attestation: Mamba-attention hybrid"),
    "tiiuae/Falcon-H1-7B-Base":
        ("full+ssm", "hybrid",
         "models.yaml env.profile=ssm; 'NOT optional for hybrids' in its why"),
    "Zyphra/Zamba2-7B":
        ("full+ssm", "hybrid",
         "models.yaml env.profile=ssm; attestation: 'Mamba1 blocks have been "
         "replaced with Mamba2 blocks'"),
    "RWKV/rwkv-4-7b-pile":
        ("linear", "dense",
         "attestation: RWKV-4. WKV operator is time-decaying channelwise "
         "linear attention; no token-token dot product"),
    "google/recurrentgemma-9b":
        ("local+linear", "hybrid",
         "attestation quotes the paper: 'The architecture is Griffin, not "
         "Gemma's transformer'; Griffin = sliding-window attention + RG-LRU"),
    "allenai/Olmo-Hybrid-7B":
        ("full+linear", "hybrid",
         "attestation quotes arXiv:2604.03444: 'largely comparable to Olmo 3 "
         "7B but with the sliding window layers replaced by Gated DeltaNet "
         "layers'"),
    "allenai/OLMoE-1B-7B-0125":
        ("full", "moe",
         "OLMoE = OLMo Mixture-of-Experts, 1B active / 7B total"),
}
DEFAULT = ("full", "dense", "default: dense transformer, full attention")

CONTRASTS = [
    ("1 CONTROLLED BY DESIGN (AI2)", ["allenai/Olmo-3-1025-7B",
                                      "allenai/Olmo-Hybrid-7B"]),
    ("2 SAME PRETRAINING CORPUS", ["google/gemma-2-9b",
                                   "google/recurrentgemma-9b"]),
    ("3 ONE VENDOR, THREE BLOCKS", ["tiiuae/falcon-7b", "tiiuae/Falcon3-7B-Base",
                                    "tiiuae/falcon-mamba-7b",
                                    "tiiuae/Falcon-H1-7B-Base"]),
    ("4 DENSE vs MoE (AI2)", ["allenai/Olmo-3-1025-7B",
                              "allenai/OLMoE-1B-7B-0125"]),
]
SEL = os.path.join(HERE, "..", "existence", "results", "selectivity.json")


def arch(model):
    return ARCH.get(model, DEFAULT)


def existence():
    """{base: slope} from existence/results/selectivity.json. A LOOKUP."""
    d = json.load(open(SEL))
    return {r["lineage"].split(">")[0]: r["slope"]
            for r in d["overall"]["per_lineage"]}, d["overall"]


def magnitude(bases):
    """{base: sum|delta|} -- recomputed; rate_and_magnitude writes no results."""
    from malignment import roster, vectors as V
    ep, _ = roster.endpoints()
    out = {}
    for b in bases:
        a = ep.get(b)
        if not a:
            continue
        r = V.rows("SELECT sum(abs(delta)) s FROM movement_v4 "
                   "WHERE base={b:String} AND aligned={a:String} "
                   "AND rule='canonical' AND frame_base='' AND frame_aligned=''",
                   b=b, a=a)
        out[b] = float(r[0]["s"] or 0.0)
    return out


def main():
    import statistics as st
    slopes, overall = existence()
    print("EXISTENCE content-selectivity, per lineage (lookup)")
    print("negative slope = higher-T words lose more mass = the operation")
    print("grand: %d negative / %d positive, median %.6f\n"
          % (overall["neg"], overall["pos"], overall["med_slope"]))

    nondefault = [b for b in slopes if b in ARCH]
    mags = magnitude(sorted(set(nondefault) | {b for _, g in CONTRASTS for b in g}))
    med_slope = st.median(slopes.values())
    med_mag = st.median(magnitude([b for b in list(slopes)[:12]]).values())

    print("%-30s %-13s %-7s %11s %10s" % ("model", "attn", "block", "slope", "sum|d|"))
    for b in sorted(nondefault, key=lambda x: slopes[x]):
        at, bl, _ = arch(b)
        print("%-30s %-13s %-7s %+11.6f %10.0f"
              % (b.split("/")[-1][:30], at, bl, slopes[b], mags.get(b, 0)))
    print("%-30s %-13s %-7s %+11.6f %10.0f"
          % ("-- roster median --", "", "", med_slope, med_mag))

    print("\n%s\nTHE MATCHED CONTRASTS\n%s" % ("=" * 78, "=" * 78))
    for name, group in CONTRASTS:
        print("\n%s" % name)
        for b in group:
            if b not in slopes:
                print("   %-30s NOT AN ENDPOINT PAIR" % b.split("/")[-1][:30])
                continue
            at, bl, why = arch(b)
            print("   %-28s %-13s %-7s %+10.6f  %8.0f"
                  % (b.split("/")[-1][:28], at, bl, slopes[b], mags.get(b, 0)))
    print("\nNO BETWEEN-GROUP TEST IS RUN: one pure SSM and one linear-attention")
    print("model in the roster. These are positions in a distribution of 50.")
    print("\nnorm_change: per-lineage dose slopes are NOT on disk -- its CSVs are")
    print("already aggregated over lineages. Stratifying it needs that producer")
    print("to emit a per-lineage column. NOT DONE HERE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
