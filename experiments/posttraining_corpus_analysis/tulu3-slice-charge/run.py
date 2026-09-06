"""THE FULL RUN. Three strata, ~21,500 exchanges, v3 instrument.

    python experiments/posttraining_corpus_analysis/tulu3-slice-charge/run.py --dry
    python experiments/posttraining_corpus_analysis/tulu3-slice-charge/run.py

## WHY IT IS STRATIFIED, AND THE RULE THAT COMES WITH THAT

The pilot measured the charged rate per source and it ranges over two orders of
magnitude: wildguardmix 60.5%, wildjailbreak 45.0%, wildchat 20.0%, coconot
16.5%, and **thirteen of nineteen sources at or below 1.5%**. Uniform sampling
spends most of its budget on maths and code rows to buy a handful of charged
ones, and the cell carrying the compliance analysis is narrower still: charged
AND complied-with is overwhelmingly WildChat, because wildguardmix and
wildjailbreak refuse (3.4% and 1.1% comply) where WildChat complies at 54.8%.

    A  composition   500 x 19 sources     9,500   representative PER SOURCE
    B  compliance    +6,000 wildchat      6,000   charged + COMPLY, substitution
    C  refusal       +2,000 x 3 safety    6,000   move x kind on the refusing side
                                         ------
                                         21,500

**COMPOSITION RATES ARE COMPUTED ON STRATUM A ONLY.** B and C are enriched by
design, so a rate pooled over all three would say "the mixture is 30% charged"
because we chose to oversample the charged sources. Every table this file prints
stamps its stratum. `a_only()` is the accessor; there is no unstamped path to a
corpus-level rate.

Strata are disjoint: A is drawn first and B and C are drawn from what is left,
so no exchange is rated twice and an A-row is never double-counted in a
conditional table.

## WHAT IT MEASURES

    user_kind, literal_charge, implied_charge   the request
    is_fiction, assistant_move, assistant_reading, assistant_kind, assistant_charge

Two independent things, and they are NOT the same -- see the README's v3 section:
`implied - literal` is concealment in the REQUEST, calibrated within-item on
WildJailbreak's paired forms; `COMPLY + charged + assistant NONE` is an emptied
RESPONSE. The pilot showed the second does not imply the first (gap>0 in 3/19).

## RESUMABILITY

Chunked, appending after each chunk, and the task carries `cache_ttl="168h"`, so
a re-run after a crash re-reads cached ratings rather than re-buying them. The
output file is truncated only when a run starts from nothing.
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
WILDCHAT = "ai2-adapt-dev/tulu_v3.9_wildchat_100k"
SAFETY = ("ai2-adapt-dev/tulu_v3.9_synthetic_finalresp_wildguardmixtrain_"
          "decontaminated_50k",
          "ai2-adapt-dev/tulu_v3.9_wildjailbreak_decontaminated_50k",
          "ai2-adapt-dev/coconot_converted")
A_PER_SOURCE = 500
B_WILDCHAT = 6000
C_PER_SAFETY = 2000
CHUNK = 500

MOVES = ("COMPLY", "PARTIAL", "REFUSE", "CORRECT")
KINDS = ("SEXUAL", "VIOLENT", "DEGRADING", "COERCIVE", "ILLICIT", "OTHER", "NONE")


def build_sample():
    """[(stratum, source, user, assistant)] -- disjoint across strata."""
    from pilot import rows_by_source
    by = rows_by_source()
    rng = random.Random(SEED)
    jobs, used = [], collections.defaultdict(set)
    for src in sorted(by):
        v = by[src]
        idx = rng.sample(range(len(v)), min(A_PER_SOURCE, len(v)))
        used[src] = set(idx)
        jobs += [("A", src) + v[i] for i in idx]
    for src, n in [(WILDCHAT, B_WILDCHAT)] + [(s, C_PER_SAFETY) for s in SAFETY]:
        v = by.get(src) or []
        left = [i for i in range(len(v)) if i not in used[src]]
        idx = rng.sample(left, min(n, len(left)))
        used[src].update(idx)
        st = "B" if src == WILDCHAT else "C"
        jobs += [(st, src) + v[i] for i in idx]
    return jobs


def a_only(recs):
    """THE ONLY PATH TO A CORPUS-LEVEL RATE. See this file's docstring."""
    return [r for r in recs if r["stratum"] == "A"]


def report(recs):
    A = a_only(recs)
    print("\n%s\nSTRATUM A ONLY -- kind composition by source (representative)"
          % ("=" * 104))
    by = collections.defaultdict(list)
    for r in A:
        by[r["source"]].append(r)
    print("%-56s %5s %s" % ("source", "n", " ".join("%6s" % k[:6] for k in KINDS)))
    for src in sorted(by):
        v = by[src]
        c = collections.Counter(x["user_kind"] for x in v)
        print("%-56s %5d %s" % (src.split("/")[-1][:56], len(v),
                                " ".join("%5.1f%%" % (100 * c[k] / len(v)) for k in KINDS)))

    print("\n%s\nALL STRATA -- move x kind (conditional, so enrichment is allowed)"
          % ("=" * 104))
    print("%-12s %6s %s" % ("user_kind", "n", " ".join("%8s" % m for m in MOVES)))
    for k in KINDS:
        v = [r for r in recs if r["user_kind"] == k]
        if not v:
            continue
        c = collections.Counter(r["assistant_move"] for r in v)
        print("%-12s %6d %s" % (k, len(v),
                                " ".join("%7.1f%%" % (100 * c[m] / len(v)) for m in MOVES)))

    print("\n%s\nALL STRATA -- the fiction exemption, controlled" % ("=" * 104))
    for lab, sel in (("charged, fiction", lambda r: r["is_fiction"] and r["user_kind"] != "NONE"),
                     ("charged, non-fiction", lambda r: not r["is_fiction"] and r["user_kind"] != "NONE")):
        v = [r for r in recs if sel(r)]
        if not v:
            continue
        c = collections.Counter(r["assistant_move"] for r in v)
        print("  %-22s %6d %s" % (lab, len(v),
                                  " ".join("%7.1f%%" % (100 * c[m] / len(v)) for m in MOVES)))
    print("\n  by kind, NON-FICTION only:")
    print("  %-12s %6s %s" % ("user_kind", "n", " ".join("%8s" % m for m in MOVES)))
    for k in KINDS[:-1]:
        v = [r for r in recs if r["user_kind"] == k and not r["is_fiction"]]
        if len(v) < 10:
            continue
        c = collections.Counter(r["assistant_move"] for r in v)
        print("  %-12s %6d %s" % (k, len(v),
                                  " ".join("%7.1f%%" % (100 * c[m] / len(v)) for m in MOVES)))

    print("\n%s\nALL STRATA -- the two independent dimensions" % ("=" * 104))
    cc = [r for r in recs if r["assistant_move"] == "COMPLY" and r["user_kind"] != "NONE"]
    sub = [r for r in cc if r["assistant_kind"] == "NONE"]
    print("  EMPTIED RESPONSE  charged + COMPLY: %d, of which assistant NONE: %d (%.0f%%)"
          % (len(cc), len(sub), 100 * len(sub) / max(len(cc), 1)))
    gap = [r for r in recs if r["implied_charge"] - r["literal_charge"] > 0]
    print("  CONCEALED REQUEST implied > literal: %d of %d (%.2f%%)"
          % (len(gap), len(recs), 100 * len(gap) / max(len(recs), 1)))
    both = [r for r in sub if r["implied_charge"] - r["literal_charge"] > 0]
    print("  BOTH: %d  -- the pilot had 3 of 19; they are different things"
          % len(both))
    print("  assistant_reading: %s"
          % dict(collections.Counter(r["assistant_reading"] for r in recs).most_common()))
    print("\n  gap>0 rate by source (stratum A only):")
    for src in sorted(by):
        v = by[src]
        g = sum(1 for r in v if r["implied_charge"] - r["literal_charge"] > 0)
        if g:
            print("    %-54s %3d / %d" % (src.split("/")[-1][:54], g, len(v)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args(argv)
    import task as T
    path = os.path.join(OUT, "full_%s.jsonl" % T.SliceChargeEN.name)
    if a.report_only:
        report([json.loads(l) for l in open(path, encoding="utf-8")])
        return 0

    jobs = build_sample()
    n = collections.Counter(j[0] for j in jobs)
    print("strata: %s   total %d" % (dict(sorted(n.items())), len(jobs)))
    if a.dry:
        for st in ("A", "B", "C"):
            c = collections.Counter(j[1].split("/")[-1][:46] for j in jobs if j[0] == st)
            print("  %s: %s" % (st, dict(c.most_common(4))))
        return 0

    os.makedirs(OUT, exist_ok=True)
    done = set()
    if os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            r = json.loads(l)
            done.add((r["stratum"], r["source"], r["user"][:200]))
        print("resuming: %d already on disk" % len(done))
    todo = [j for j in jobs if (j[0], j[1], j[2][:200]) not in done]
    print("to rate: %d" % len(todo))

    task = T.SliceChargeEN()
    fh = open(path, "a", encoding="utf-8")
    total_err = 0
    for i in range(0, len(todo), CHUNK):
        blk = todo[i:i + CHUNK]
        errs = {}
        res = task.map([T.render(u, x) for _, _, u, x in blk],
                       metadata_list=[{"stratum": st, "source": s}
                                      for st, s, _, _ in blk],
                       num_workers=32, errors=errs)
        total_err += len(errs)
        ok = 0
        for (st, src, u, x), r in zip(blk, res):
            if r is None:
                continue
            ok += 1
            fh.write(json.dumps(dict(
                stratum=st, source=src, user=u[:400], assistant=x[:400],
                reading=r.reading, user_kind=r.user_kind,
                literal_charge=r.literal_charge, implied_charge=r.implied_charge,
                is_fiction=bool(r.is_fiction), assistant_move=r.assistant_move,
                assistant_reading=r.assistant_reading,
                assistant_kind=r.assistant_kind,
                assistant_charge=r.assistant_charge)) + "\n")
        fh.flush()
        print("  chunk %d/%d: %d written, %d errors (cumulative %d)"
              % (i // CHUNK + 1, (len(todo) + CHUNK - 1) // CHUNK, ok, len(errs), total_err),
              flush=True)
    fh.close()
    recs = [json.loads(l) for l in open(path, encoding="utf-8")]
    print("\n-> %s (%d rows)" % (os.path.basename(path), len(recs)))
    report(recs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
