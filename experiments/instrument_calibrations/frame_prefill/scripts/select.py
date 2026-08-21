"""Choose the cells the sweep will measure, and write them with their reason.

    python .../scripts/select.py            -> results/targets.json

Three strata, all restricted to models where `prefill` is DEFINED -- a model
without a chat template has no assistant turn, so two of the three conditions do
not exist for it and it cannot answer this question.

    A  reverser    dario's `reversed` cells, crosslineage_rows.csv @ 502ca92
    B  degenerate  cells whose raw word distribution is not a paradigm, screened
                   on twp_words rule_version=3 (the complete store)
    C  control     seeded random ordinary cells on the SAME models, matched per
                   model to that model's A+B count

C is not decoration. Without it the sweep can only report that odd cells behave
oddly, which is the shape of every result that fails to replicate.

## THE JOIN IS THE DANGEROUS PART AND IT REFUSES

dario's CSV holds BASENAMES (`Llama-3.1-8B-Instruct`); the roster holds full ids
(`meta-llama/Llama-3.1-8B-Instruct`). Mapping one to the other is exactly the
operation [6472] warned about -- **48 roster ids are a strict PREFIX of another**
-- and six of dario's 27 reversers are `-Instruct` where my parquet holds `-DPO`,
which a prefix-tolerant match would have silently conflated. A first attempt at
this join compared basenames against full ids and returned 0 of 150 reversed
cells as prefillable; the true answer is 99.

So: exact basename -> full id, built from the roster, and it ASSERTS that no
basename is ambiguous and that every reverser maps. If either stops holding the
script stops rather than guessing.
"""

import collections, csv, json, os, random, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "results", "targets.json")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
REVERSERS = os.path.join(REPO, "experiments", "displacement_taxonomy", "results",
                         "crosslineage_rows.csv")
PREFILLABLE = os.path.expanduser("~/malignment-data/prefillable_roster.json")

FILL = r"^[_\\-–—=.·•*~^]+$"
RULE_VERSION = 3           #: the complete store; v4 was mid-rebuild on 2026-08-21
FILL_MIN, NONLEX_MIN, THIN_MAX = 0.25, 0.50, 20


def ch(sql):
    r = subprocess.run(["clickhouse", "client", "--query", sql],
                       capture_output=True, text=True, timeout=3600)
    if r.returncode:
        raise SystemExit("clickhouse failed: %s" % r.stderr[:400])
    return r.stdout


def prefillable():
    pf = json.load(open(PREFILLABLE))
    full = {m for m, v in pf.items() if v is True}
    bn = collections.defaultdict(list)
    for m in pf:
        bn[m.split("/")[-1]].append(m)
    amb = {k: v for k, v in bn.items() if len(v) > 1}
    assert not amb, "ambiguous basenames in the roster, refusing to guess: %s" % amb
    return full, {k: v[0] for k, v in bn.items()}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--max-per-model", type=int, default=25,
                    help="cap per model per stratum, so one model cannot dominate")
    ap.add_argument("--max-models", type=int, default=24,
                    help="0 = no cap. Reverser models are always kept.")
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)

    full, bn = prefillable()
    print("prefillable roster nodes: %d" % len(full))

    #: ---- A. reversers
    rev = [(r["model"], r["prompt"]) for r in csv.DictReader(open(REVERSERS))
           if r["status"] == "reversed"]
    unmapped = sorted({m for m, _ in rev} - set(bn))
    assert not unmapped, "reverser basenames absent from the roster: %s" % unmapped
    A = [(bn[m], p) for m, p in rev if bn[m] in full]
    print("  A reversers    %4d cells on %2d models (of %d reversed total)"
          % (len(A), len({m for m, _ in A}), len(rev)))

    #: ---- B. degenerates, screened on the COMPLETE store
    ids = ",".join("'%s'" % m.replace("'", "\\'") for m in sorted(full))
    sql = ("WITH cell AS (SELECT model, prompt, sum(p) AS mass, "
           "sumIf(p, match(word, '%s')) AS fill, "
           "sumIf(p, NOT match(word, '[a-zA-Z\\\\p{Han}\\\\p{Cyrillic}\\\\p{Arabic}]')) AS nonlex, "
           "count() AS n_surf FROM malign_logits.twp_words "
           "WHERE rule_version=%d AND model IN (%s) GROUP BY model, prompt) "
           "SELECT model, prompt, round(fill/mass,4), round(nonlex/mass,4), n_surf "
           "FROM cell WHERE mass > 0 AND (fill/mass > %f OR nonlex/mass > %f OR n_surf < %d) "
           "FORMAT TabSeparated" % (FILL, RULE_VERSION, ids, FILL_MIN, NONLEX_MIN, THIN_MAX))
    B, why_b, n_thin = [], {}, 0
    for line in ch(sql).splitlines():
        f = line.split("\t")
        if len(f) != 5:
            continue
        fill, nonlex, n_surf = float(f[2]), float(f[3]), int(f[4])
        #: THIN IS NOT A DEGENERACY CRITERION ON ITS OWN, and including it as one
        #: was wrong. Measured on the first pass: `n_surf < 20` alone contributed
        #: 2,118 of 3,560 selected cells, spread evenly over 89 models with
        #: Olmo-3-Think-DPO, Aquila2, salamandra and Dolphin at 32-38 each. A cell
        #: with few surfaces is usually a CONFIDENT cell -- the model knows what
        #: comes next -- which is the opposite of the thing being screened for.
        #: It is kept as a co-occurring FLAG because thin AND non-lexical is a
        #: different object from either alone.
        if not (fill > FILL_MIN or nonlex > NONLEX_MIN):
            n_thin += 1
            continue
        B.append((f[0], f[1]))
        why_b[(f[0], f[1])] = dict(fill=fill, nonlex=nonlex, n_surf=n_surf,
                                   thin=n_surf < THIN_MAX)
    print("  B degenerates  %4d cells on %2d models  (%d thin-only cells rejected)"
          % (len(B), len({m for m, _ in B}), n_thin))

    #: MODEL COUNT IS THE COST, NOT CELL COUNT. A 7B load on mps is ~1-2 min and
    #: a forward pass is ~0.2s, so 90 models x 40 cells is dominated by loading.
    #: Reverser models are kept unconditionally -- they are the question -- and
    #: the remaining slots go to the models carrying the most degenerate cells.
    if a.max_models:
        keep_m = {m for m, _ in A}
        rest = collections.Counter(m for m, _ in B if m not in keep_m)
        for m, _ in rest.most_common(max(0, a.max_models - len(keep_m))):
            keep_m.add(m)
        A = [(m, p) for m, p in A if m in keep_m]
        B = [(m, p) for m, p in B if m in keep_m]
        print("  scoped to %d models (%d reversers kept unconditionally)"
              % (len(keep_m), len({m for m, _ in A})))

    #: cap per model per stratum
    def cap(cells):
        by = collections.defaultdict(list)
        for m, p in cells:
            by[m].append((m, p))
        out = []
        for m, v in by.items():
            rng.shuffle(v)
            out += v[:a.max_per_model]
        return out
    A, B = cap(A), cap(B)

    #: ---- C. controls, matched per model, drawn from cells in NEITHER stratum
    taken = set(A) | set(B)
    need = collections.Counter(m for m, _ in A) + collections.Counter(m for m, _ in B)
    C = []
    for m, k in need.items():
        rows = ch("SELECT DISTINCT prompt FROM malign_logits.twp_words "
                  "WHERE rule_version=%d AND model='%s' FORMAT TabSeparatedRaw"
                  % (RULE_VERSION, m.replace("'", "\\'"))).splitlines()
        pool = [(m, p) for p in rows if p.strip() and (m, p) not in taken]
        rng.shuffle(pool)
        C += pool[:k]
    print("  C controls     %4d cells on %2d models" % (len(C), len({m for m, _ in C})))

    rows = ([dict(model=m, prompt=p, stratum="reverser") for m, p in A]
            + [dict(model=m, prompt=p, stratum="degenerate", **why_b.get((m, p), {}))
               for m, p in B]
            + [dict(model=m, prompt=p, stratum="control") for m, p in C])
    seen, keep = set(), []
    for r in rows:
        k = (r["model"], r["prompt"], r["stratum"])
        if k in seen:
            continue
        seen.add(k); keep.append(r)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(dict(seed=a.seed, rule_version=RULE_VERSION, max_per_model=a.max_per_model,
                   screen=dict(fill_min=FILL_MIN, nonlex_min=NONLEX_MIN, thin_max=THIN_MAX),
                   reversers_source="crosslineage_rows.csv @ 502ca92",
                   n=len(keep), targets=keep), open(OUT, "w"), indent=1)
    print("\n%-12s %6s %8s" % ("stratum", "cells", "models"))
    by = collections.defaultdict(list)
    for r in keep:
        by[r["stratum"]].append(r["model"])
    for k in ("reverser", "degenerate", "control"):
        print("%-12s %6d %8d" % (k, len(by[k]), len(set(by[k]))))
    print("\ntotal %d cells x 3 conditions = %d forward passes over %d models"
          % (len(keep), 3 * len(keep), len({r["model"] for r in keep})))
    print("-> %s" % OUT)


if __name__ == "__main__":
    main()
