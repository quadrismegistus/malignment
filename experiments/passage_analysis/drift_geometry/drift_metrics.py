"""One row per passage: the drift family, keyed back to the passage sample.

    python experiments/passage_analysis/drift_geometry/drift_metrics.py
    python experiments/passage_analysis/drift_geometry/drift_metrics.py --verify

Consumes `$MALIGNMENT_DATA/drift_geometry/sentence_vecs/` (181,665 sentence
vectors over 13,557 coded passages, written by `embed_passages.py`) and emits a
LONG table -- every row a passage, every column either a key back to the sample
or a metric. Small enough to live in the repo; the vectors are not.

## The definitions are the ARCHIVE's, verbatim, and that is the point

Taken from `archive/embedding.py::drift_metrics_from_embeddings`. If these drift,
no number here is comparable to the audit's, which is the only reason to have
ported the archive at all:

    step_dists[i] = 1 - dot(sv[i], sv[i+1])     vectors are L2-normalised, so
                                                dot IS cosine
    mean_drift    = mean(step_dists)            ORDER-SENSITIVE
    max_drift     = max(step_dists)
    std_drift     = std(step_dists)
    total_drift   = 1 - min(sim_matrix)         the DIAMETER, order-INVARIANT
    path_length   = sum(step_dists)             == (n_sents - 1) * mean_drift
    directedness  = total_drift / path_length

And `ordering`, the audit's recommended replacement for `directedness`, from
`archive/m06_ordering_figs.py`:

    ordering = mean(successive distances) - mean(all pairwise distances)

**Zero in expectation under a shuffle of the passage's own sentences**, because
the expected successive distance under a random order IS the mean pairwise
distance. Composition and sentence count are held fixed by construction -- same
sentences, same n, only the order differs. That is what makes it n-controlled
where `directedness` is not.

## Two things carried from the archive rather than re-derived

**`min_sentences = 3`.** `archive/corpus_metrics.py` gated at three and so does
this. A two-sentence passage has one step distance, so `std_drift` is 0 and
`ordering` is exactly 0 by construction -- not a measurement. Passages below the
gate are EMITTED with null metrics and counted, never dropped silently.

**A null on `ordering` licenses "no consistent direction", never "no effect."**
Registrar [6216], on this seat's own English case: it is a centred statistic, so
zero is where a shuffled passage sits. `--verify` draws the shuffle null rather
than assuming it.

## What --verify does

Reproduces the audit's defect 1 on THIS corpus instead of inheriting it: shuffle
each passage's sentences, recompute, and confirm `total_drift` is unchanged while
`mean_drift` moves. A checker that has never been watched refusing is a belief.
"""

import argparse, glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                   os.path.expanduser("~/malignment-data")),
                    "drift_geometry")
VECS = os.path.join(DATA, "sentence_vecs")
OUT = os.path.join(HERE, "results", "drift_by_passage.csv")
#: **THE FLOOR IS PER-COLUMN, NOT PER-ROW, AND IT USED TO BE PER-ROW.**
#: `MIN_SENTS = 3` blanked the WHOLE metric row below 3 sentences, which
#: discarded 252 passages where the two metrics anyone actually uses are
#: perfectly well defined. At n_sents == 2 there is exactly one drift step, so:
#:
#:     mean_drift     = that step         DEFINED
#:     mean_pairwise  = that step         DEFINED
#:     std_drift      = 0                 degenerate
#:     max_drift      = mean_drift        degenerate
#:     path_length    = mean_drift        degenerate
#:     directedness   = 1 by construction degenerate
#:
#: A row-level floor applied to a column-level problem. And the loss was
#: ARM-DIFFERENTIAL -- aligned 462/6,800 = 6.8% against base 270/6,757 = 4.0%,
#: because aligned models emit twice as many single-sentence passages -- so
#: every drift result was computed on a population selected on a correlate of
#: the arm. `bloomz-7b1` was 189 of 196 blank, 96%, invisible in any aggregate.
#:
#: `mean_drift` and `mean_pairwise` are also the LENGTH-FREE pair (r with
#: n_sents -0.126 and -0.030 against +0.941 for path_length), i.e. exactly the
#: columns a length-sensitive floor should not have been deciding.
MIN_SENTS = 2                 #: rows below this have NO metrics at all
DEGENERATE_BELOW = 3          #: these columns stay blank below it
DEGENERATE = ("max_drift", "std_drift", "total_drift", "path_length",
              "directedness", "ordering")

KEYS = ["pid", "model", "arm", "pair", "prompt", "sample_idx",
        "narrative_A", "drift_A", "drift_B", "degree_A", "mode_A"]


def metrics(sv):
    """The archive's drift family plus `ordering`. sv: (n, dim) L2-normalised."""
    import numpy as np
    n = len(sv)
    if n < 2:
        return dict(n_sents=n)
    step = 1.0 - np.sum(sv[:-1] * sv[1:], axis=1)
    sim = sv @ sv.T
    total = float(1.0 - sim.min())
    path = float(step.sum())
    #: mean of all DISTINCT pairs, i.e. the upper triangle -- not the full matrix,
    #: whose diagonal of ones would drag the mean toward 0 distance.
    iu = np.triu_indices(n, k=1)
    mean_pairwise = float((1.0 - sim[iu]).mean())
    return dict(
        n_sents=n,
        mean_drift=round(float(step.mean()), 6),
        max_drift=round(float(step.max()), 6),
        std_drift=round(float(step.std()), 6),
        total_drift=round(total, 6),
        path_length=round(path, 6),
        directedness=round(total / path if path > 0 else 0.0, 6),
        mean_pairwise=round(mean_pairwise, 6),
        ordering=round(float(step.mean()) - mean_pairwise, 6),
    )


def passages():
    """Yield (keys, sv) per passage, one part at a time. Memory stays flat."""
    import numpy as np, pyarrow.parquet as pq
    seen = set()
    for f in sorted(glob.glob(os.path.join(VECS, "part-*.parquet"))):
        t = pq.read_table(f)
        cols = {c: t.column(c).to_pylist() for c in KEYS + ["sent_idx", "n_sents"]}
        V = np.asarray(t.column("vec").to_numpy(zero_copy_only=False).tolist(),
                       dtype=np.float32) if False else np.array(
            [r for r in t.column("vec").to_pylist()], dtype=np.float32)
        cur, rows = None, []
        for i, pid in enumerate(cols["pid"]):
            if pid != cur:
                if rows:
                    yield _emit(cols, rows, V, seen)
                cur, rows = pid, []
            rows.append(i)
        if rows:
            yield _emit(cols, rows, V, seen)


def _emit(cols, rows, V, seen):
    import numpy as np
    pid = cols["pid"][rows[0]]
    #: A PASSAGE MUST NOT SPAN TWO PARTS. embed_passages flushes on a passage
    #: boundary, so this holds by construction -- asserted rather than trusted,
    #: because a split passage would silently halve its own sentence count and
    #: n_sents is the variable the audit says everything else rides on.
    if pid in seen:
        raise SystemExit("pid %s spans parts -- the flush boundary broke" % pid)
    seen.add(pid)
    order = sorted(rows, key=lambda i: cols["sent_idx"][i])
    keys = {k: cols[k][order[0]] for k in KEYS}
    assert cols["n_sents"][order[0]] == len(order), (
        "%s: %d rows for n_sents=%d" % (pid, len(order), cols["n_sents"][order[0]]))
    return keys, V[order]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="draw the shuffle null and reproduce the audit's defect 1")
    ap.add_argument("--seed", type=int, default=20260820)
    a = ap.parse_args(argv)
    import numpy as np, csv, collections

    if a.verify:
        rng = np.random.default_rng(a.seed)
        same_total, moved_mean, moved_ord, n = 0, 0, 0, 0
        for keys, sv in passages():
            if len(sv) < 4:
                continue
            m0 = metrics(sv)
            m1 = metrics(sv[rng.permutation(len(sv))])
            n += 1
            same_total += abs(m0["total_drift"] - m1["total_drift"]) < 1e-4
            moved_mean += abs(m0["mean_drift"] - m1["mean_drift"]) > 1e-4
            moved_ord += abs(m0["ordering"] - m1["ordering"]) > 1e-4
            if n >= 500:
                break
        print("SHUFFLE TEST on %d passages of >=4 sentences\n" % n)
        print("  total_drift unchanged to 1e-4 : %4d/%d   %s"
              % (same_total, n, "ORDER-INVARIANT, as the audit says"))
        print("  mean_drift  moved             : %4d/%d" % (moved_mean, n))
        print("  ordering    moved             : %4d/%d" % (moved_ord, n))
        return

    out, skipped, partial = [], collections.Counter(), collections.Counter()
    for keys, sv in passages():
        m = metrics(sv)
        n = m.get("n_sents", 0)
        if n < MIN_SENTS:
            skipped[n] += 1
            m = dict(n_sents=n)
        elif n < DEGENERATE_BELOW:
            #: KEEP the defined columns, BLANK the degenerate ones. Writing 0.0
            #: for `std_drift` here would be a threshold reported as a
            #: measurement -- the value is not small, it does not exist.
            partial[n] += 1
            m = {k: v for k, v in m.items() if k not in DEGENERATE}
        keys.update(m)
        out.append(keys)
    if partial:
        print("  partial rows (defined columns only): %s"
              % dict(sorted(partial.items())))

    cols = KEYS + ["n_sents", "mean_drift", "max_drift", "std_drift",
                   "total_drift", "path_length", "directedness",
                   "mean_pairwise", "ordering"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow(r)

    scored = [r for r in out if r.get("mean_drift") is not None]
    print("passages: %d | scored: %d | under the %d-sentence gate: %d %s"
          % (len(out), len(scored), MIN_SENTS, sum(skipped.values()),
             dict(sorted(skipped.items())) if skipped else ""))
    print("  EMITTED WITH NULL METRICS, not dropped -- absence must read as absence\n")
    md = np.median([r["n_sents"] for r in out])
    print("  median sentences per passage: %d" % md)
    #: **EACH COLUMN OVER ITS OWN POPULATION.** Rows below `DEGENERATE_BELOW`
    #: carry `mean_drift` and not `total_drift`, so a single `scored` list is
    #: no longer one population -- summarising them together is the pooling
    #: defect this whole change exists to remove. `n` is printed per row for
    #: that reason: two columns with different denominators must say so.
    print("\n  %-14s %9s %9s %9s %8s" % ("metric", "median", "mean", "sd", "n"))
    for k in ("mean_drift", "mean_pairwise", "total_drift", "directedness", "ordering"):
        v = np.array([r[k] for r in out if r.get(k) is not None], float)
        if not v.size:
            print("  %-14s -- no rows --" % k); continue
        print("  %-14s %9.4f %9.4f %9.4f %8d"
              % (k, np.median(v), v.mean(), v.std(), v.size))
    print("\n  identity check, path_length == (n-1) * mean_drift:")
    d = [abs(r["path_length"] - (r["n_sents"] - 1) * r["mean_drift"])
         for r in out if r.get("path_length") is not None]
    print("    max deviation %.2e over %d rows" % (max(d), len(d)))
    print("\n-> results/drift_by_passage.csv  (%d rows, %d columns)" % (len(out), len(cols)))


if __name__ == "__main__":
    main()
