"""Does nucleus truncation raise or lower drift? Measured, not argued.

    python .../top_p_sweep.py --model Qwen/Qwen2.5-7B-Instruct

## THE ARGUMENT THIS REPLACES

Our API arm ran with `top_p` UNSET and our open arm is pinned at 1.0, so
per-vendor truncation is a covariate aligned with the contrast. The direction of
its effect on drift was then argued rather than measured, and litmod
(largeliterarymodels) named the equivocation in the argument:

  "predictable per-step" is a property of the DISTRIBUTION; "drift" is a
  property of the TRAJECTORY, and the map between them is not monotonic.

Their mechanism: high entropy gives large per-step variance but LOW
autocorrelation -- the generation hovers and excursions partly cancel, a
diffusive walk whose displacement grows with sqrt(length). Truncation gives
small steps but HIGH autocorrelation -- the model commits to a direction and
keeps committing, a ballistic walk whose displacement grows linearly. Smaller
steps, further travelled.

**Whether that reaches OUR metric depends on which metric it is.** `mean_drift`
is `mean(1 - cos(sent_i, sent_i+1))` (`drift_metrics.py:100`) -- mean step-to-step
displacement, not opening-to-closing distance. On litmod's own account
truncation should LOWER that. Two mechanisms could still raise it: mode-seeking
decoding falls into formulaic scaffolding (headings, enumerations, summary
moves) whose adjacent sentences are topically distinct; and at heavy truncation
the classic failure is REPETITION, which is very low drift. Those trade places
at different depths, so the relationship need not be monotonic in top_p.

Three plausible mechanisms, two directions, one metric. That is a measurement.

## THE DESIGN

Raw frame only (`template=False`), so `top_p` is the single thing varying -- no
chat template, no system message, no interaction with the frame effect measured
in `frame_pilot.py`.

`top_p=1.0` COSTS NOTHING: the frame pilot's raw arm ran at exactly that key
(same stem, same seed, same decoder, `template=False`), so it is served from the
generations stash and the sweep adds only the truncated points.

Four points rather than two, because the non-monotonicity above is a real
possibility and two points cannot see it. 0.95 and 0.9 cover the plausible
vendor range; 0.7 is deliberately past it, to establish DIRECTION with a signal
large enough to read.

## WHAT IT CANNOT SETTLE

One stem, three open checkpoints of 0.4B to 7B. It measures how truncation moves
drift IN THESE MODELS, which is the mechanism question. It does not tell us what
any vendor's default actually is -- that is the probe, and for Anthropic the
number is undocumented anywhere, so it may not be knowable at all.
"""

import argparse, os, statistics, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

TOP_PS = (1.0, 0.95, 0.9, 0.7)
STEM = "She was ugly and misshapen and she wanted to"
SEED = 20260821


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--stem", default=STEM)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    from malignment import Checkpoint

    ck = Checkpoint(a.model)
    print("%s | stem %r | n=%d per top_p" % (a.model, a.stem[:44], a.n), flush=True)
    ld = ck.load()
    print("  loaded on %s in %.1fs" % (ld.dev, ld.load_s), flush=True)
    for tp in TOP_PS:
        t = time.time()
        ps = ck.generate(a.stem, n=a.n, seed=a.seed, loaded=ld,
                         template=False, decoder={"top_p": tp})
        print("  top_p %-5s %3d passages, %6.1fs, median %d new tokens, %s"
              % (tp, len(ps), time.time() - t,
                 statistics.median(p.n_new_tokens for p in ps),
                 {f: sum(1 for p in ps if p.finish == f)
                  for f in sorted({p.finish for p in ps})}), flush=True)
    print("  -> generations stash: %s" % ck.gen_dir(), flush=True)


if __name__ == "__main__":
    main()
