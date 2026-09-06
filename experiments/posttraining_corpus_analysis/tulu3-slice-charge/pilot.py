"""PILOT: does the user side carry a kind signal, and does the assistant side vary?

    python experiments/posttraining_corpus_analysis/tulu3-slice-charge/pilot.py --dry
    python experiments/posttraining_corpus_analysis/tulu3-slice-charge/pilot.py

## WHAT IT IS FOR, AND WHAT IT IS NOT

Two things must be true before the full run is worth buying, and neither is
known:

    1. `user_kind` has a measurable rate per source. WildChat is real user
       conversation, so charged material is a TAIL and not the mode; the tail
       rate is what sets the sample size for a rate comparison.
    2. `assistant_kind` VARIES AT ALL. In a 14-row smoke test it was NONE at
       charge 1 in 14 of 14. If SFT targets are essentially never transgressive
       -- plausible, they are curated -- that column is constant and cannot
       carry an ordinal test. This pilot is how that is settled rather than
       assumed.

**It is a pilot and no number from it is a result.** n per source is small by
design; report rates with their intervals or do not report them.

## SAMPLED BY SOURCE, NOT BY SLICE, AND THAT IS DELIBERATE

`source` is ground truth in the mixture. The four ABLATED SLICES are inference:
the ablation model cards are stubs (all four byte-identical, md5
39727e7063aa6976a8c044d325155bd1), so slice membership comes from the paper.

Safety is pinned and checks out by arithmetic --

    coconot_converted                                       10,983
    tulu_v3.9_wildjailbreak_decontaminated_50k              50,000
    tulu_v3.9_synthetic_finalresp_wildguardmixtrain_...50k  50,000
                                                           -------
                                                           110,983  = 11.8%

which is the registration's figure exactly. **Math and persona are NOT pinned
and they overlap**: five personahub sources total 284,919 rows and three are
maths, including `personahub_math_v5_regen_149960` at 16% -- the single largest
source in the mixture and plausibly inside BOTH ablations. If so, `no-math`
(-0.092) and `no-persona` (-0.086) removed largely the same rows, which is a
better account of their near-identical model-side effects than two independent
slices agreeing.

Sampling by source keeps that question open. Aggregating source -> slice is a
later step, done once, against the paper.

## THE QUESTION THE FULL RUN WILL ASK

Not density alone. **How often does each source teach the model to behave well
for a given KIND of prompt** -- the kind composition of the user turns, and the
assistant's move CONDITIONAL on that kind. A source can be charged and complied
with, or charged and refused, and those are different corpora.
"""
import argparse
import collections
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

OUT = os.path.join(HERE, "results")
SEED = 20260906
PER_SOURCE = 200
SHARDS = 6


def rows_by_source():
    """{source: [(user, assistant)]} over the whole mixture. Shards are cached."""
    from huggingface_hub import hf_hub_download
    import pyarrow.parquet as pq
    by = collections.defaultdict(list)
    for i in range(SHARDS):
        p = hf_hub_download("allenai/tulu-3-sft-mixture",
                            "data/train-0000%d-of-00006.parquet" % i,
                            repo_type="dataset")
        for r in pq.read_table(p, columns=["source", "messages"]).to_pylist():
            m = r["messages"]
            #: FIRST TURN ONLY. A multi-turn row is rated on its opening
            #: exchange; the rate at which later turns differ is not measured
            #: and this is a declared limit, not a finding about the corpus.
            if len(m) >= 2 and m[0].get("role") == "user":
                by[r["source"]].append((m[0]["content"], m[1]["content"]))
    return by


def sample(by, per_source=PER_SOURCE, seed=SEED):
    rng = random.Random(seed)
    out = []
    for src in sorted(by):
        v = by[src]
        out += [(src, u, a) for u, a in rng.sample(v, min(per_source, len(v)))]
    return out


def report(recs):
    print("\n%s\nUSER KIND COMPOSITION BY SOURCE (pilot n, rates are indicative)"
          % ("=" * 100))
    KINDS = ("SEXUAL", "VIOLENT", "DEGRADING", "COERCIVE", "ILLICIT", "OTHER", "NONE")
    by = collections.defaultdict(list)
    for r in recs:
        by[r["source"]].append(r)
    print("%-58s %5s %s" % ("source", "n", " ".join("%6s" % k[:6] for k in KINDS)))
    for src in sorted(by):
        v = by[src]
        c = collections.Counter(x["user_kind"] for x in v)
        print("%-58s %5d %s" % (src[:58], len(v),
                                " ".join("%5.1f%%" % (100 * c[k] / len(v)) for k in KINDS)))

    print("\n%s\nDOES THE ASSISTANT SIDE VARY AT ALL? (the pilot's decisive question)"
          % ("=" * 100))
    ac = collections.Counter(r["assistant_kind"] for r in recs)
    ch = collections.Counter(r["assistant_charge"] for r in recs)
    print("  assistant_kind  : %s" % dict(ac.most_common()))
    print("  assistant_charge: %s" % dict(sorted(ch.items())))
    nn = sum(v for k, v in ac.items() if k != "NONE")
    print("  NOT-NONE: %d of %d (%.2f%%)" % (nn, len(recs), 100 * nn / max(len(recs), 1)))
    if nn == 0:
        print("  -> CONSTANT. The assistant column cannot carry an ordinal test.")

    print("\n%s\nWHAT IS TRAINED, GIVEN THE KIND OF PROMPT: move | user_kind"
          % ("=" * 100))
    MOVES = ("COMPLY", "PARTIAL", "REFUSE", "CORRECT")
    print("%-12s %6s %s" % ("user_kind", "n", " ".join("%8s" % m for m in MOVES)))
    for k in KINDS:
        v = [r for r in recs if r["user_kind"] == k]
        if not v:
            continue
        c = collections.Counter(r["assistant_move"] for r in v)
        print("%-12s %6d %s" % (k, len(v),
                                " ".join("%7.1f%%" % (100 * c[m] / len(v)) for m in MOVES)))

    print("\n%s\nREFUSAL RATE ON CHARGED PROMPTS, BY SOURCE" % ("=" * 100))
    print("%-58s %7s %9s %9s" % ("source", "charged", "refuse", "comply"))
    for src in sorted(by):
        v = [x for x in by[src] if x["user_kind"] != "NONE"]
        if not v:
            print("%-58s %7d %9s %9s" % (src[:58], 0, "--", "--")); continue
        c = collections.Counter(x["assistant_move"] for x in v)
        print("%-58s %7d %8.1f%% %8.1f%%"
              % (src[:58], len(v), 100 * c["REFUSE"] / len(v), 100 * c["COMPLY"] / len(v)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="report the job size, WRITE NOTHING")
    ap.add_argument("--per-source", type=int, default=PER_SOURCE)
    ap.add_argument("--report-only", action="store_true",
                    help="re-print the tables from results/pilot.jsonl")
    a = ap.parse_args(argv)
    path = os.path.join(OUT, "pilot.jsonl")

    if a.report_only:
        report([json.loads(l) for l in open(path, encoding="utf-8")])
        return 0

    import task as T
    by = rows_by_source()
    print("sources: %d, rows with a user-first pair: %d"
          % (len(by), sum(len(v) for v in by.values())))
    samp = sample(by, a.per_source)
    print("pilot jobs: %d  (%d per source, seed %d)" % (len(samp), a.per_source, SEED))
    if a.dry:
        return 0

    task = T.SliceChargeEN()
    errs = {}
    res = task.map([T.render(u, x) for _, u, x in samp],
                   metadata_list=[{"source": s} for s, _, _ in samp],
                   num_workers=32, errors=errs)
    print("errors: %d" % len(errs))
    recs = []
    for (s, u, x), r in zip(samp, res):
        if r is None:
            continue
        recs.append(dict(source=s, user=u[:400], assistant=x[:400],
                         reading=r.reading, user_kind=r.user_kind,
                         user_charge=r.user_charge, assistant_move=r.assistant_move,
                         assistant_kind=r.assistant_kind,
                         assistant_charge=r.assistant_charge))
    os.makedirs(OUT, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    print("-> results/pilot.jsonl (%d rows)" % len(recs))
    report(recs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
