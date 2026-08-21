"""All six surprisals on ONE scale, and the gap between H and Q.

    python .../h_vs_q.py

RH, 2026-08-21: *"we have 6 surprisals... compare the relation of H to Q, self-
to ref entropy."*

    H   the generator's surprisal at its own output      "how few options it had"
    X   the lineage partner's surprisal at that output   "what the other arm pays"
    Q   deepseek's surprisal at that output              "what an outsider pays"

    base output      H(b->b)    X(b->a)    Q(ref->b)
    aligned output   H(a->a)    X(a->b)    Q(ref->a)

## Q MINUS H IS THE QUANTITY, AND IT NEEDS A COMMON DENOMINATOR

`Q - H` is what an external observer pays OVER the generator's own view: a
one-sided, KL-like gap between the model's distribution and a third party's,
evaluated on the model's own samples. Its sign and movement answer the question
that self-entropy alone cannot:

  * **Q - H SHRINKS under alignment** -- the aligned model's output is not just
    more probable to itself, it is more probable to an outsider by nearly as
    much. Alignment moved it toward text that is generically likely.
  * **Q - H GROWS** -- alignment narrowed onto the model's OWN idiosyncrasies.
    Self-entropy fell and the outsider did not follow, so the two claims in the
    literature come apart and only the external one is about the text.

**Bits per BYTE, not per token.** H and X share the lineage's tokenizer
(verified: 99.51% of passages get identical token counts from both scorers), but
Q is deepseek's, a third one. A difference taken across tokenizers in bits/token
is not a quantity. The byte denominator is what `ref_surprisal.score` stored the
`.i32` byte-end offsets FOR, and it is the only reason `Q - H` is computable at
all.

## POPULATION

The narrative-coded passages that carry a deepseek score: `ref_pool.jsonl`'s
`model_narrative` pool, joined to `gen_scores` on (model, prompt, sample_idx).
Smaller than the 220,258 passages with self and cross, because only these were
scored by the reference -- and that is the binding constraint, not a choice.

Passages where the two lineage scorers disagree on token count are excluded
upstream by that join being on the reference pool, but the count is reported.
"""

import argparse, collections, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
LN2 = math.log(2)


def sign_test(d):
    v = [x for x in d if x != 0]
    n, up = len(v), sum(1 for x in v if x > 0)
    if not n:
        return 0, 0, 0, float("nan"), float("nan")
    k = max(up, n - up)
    return n, up, n - up, statistics.median(v), min(
        1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-passages", type=int, default=10)
    a = ap.parse_args(argv)
    import numpy as np
    os.environ["MALIGNMENT_CH_DB"] = "malign_logits"
    from malignment import ch, roster

    # ---- Q: deepseek bits/byte, from the reference sidecar
    pool = {}
    for line in open(os.path.join(DATA, "ref_pool", "ref_pool.jsonl")):
        j = json.loads(line)
        if j.get("pool") == "model_narrative":
            pool[j["id"]] = j
    sur = np.fromfile(os.path.join(DATA, "ref_pool", "deepseek", "ref_shard00.f32"),
                      dtype=np.float32)
    Q = {}
    for line in open(os.path.join(DATA, "ref_pool", "deepseek", "ref_shard00.jsonl")):
        x = json.loads(line)
        p = pool.get(x["id"])
        if not p or not x.get("n"):
            continue
        nb = len(p["text"].encode())
        if nb:
            #: bits/BYTE: total bits over the passage, divided by its bytes.
            #: Tokeniser-free by construction, which is the whole point.
            Q[(p["model"], p["prompt"], str(p["sample_idx"]))] = \
                float(sur[x["row"]:x["row"] + x["n"]].sum()) / nb
    print("deepseek-scored narrative passages: %s" % "{:,}".format(len(Q)))

    # ---- H and X: from gen_scores, same passages, same byte denominator
    rows = ch.query("""
        SELECT model, prompt, toString(sample_idx) AS si, scorer,
               -arraySum(logprobs) / %f AS bits, n
        FROM {db}.gen_scores
        WHERE corpus = 'f11_l2' AND scorable = 1 AND n > 0
    """ % LN2)
    nb = {k: len(pool_text.encode())
          for k, pool_text in ((( p["model"], p["prompt"], str(p["sample_idx"])),
                                 p["text"]) for p in pool.values())}
    HX = collections.defaultdict(dict)
    for r in rows:
        k = (r["model"], r["prompt"], r["si"])
        if k in nb and nb[k]:
            HX[k][r["scorer"]] = r["bits"] / nb[k]
    print("passages with self/cross AND a reference score: %s"
          % "{:,}".format(sum(1 for k in HX if k in Q)))

    # ---- per model, then per lineage
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    lin = roster.lineages()
    partner = {}
    for base, members in lin.items():
        for al in members:
            if al != base:
                partner[base] = partner.get(base, al)
                partner[al] = base
    for k, d in HX.items():
        m = k[0]
        if k not in Q or m not in partner:
            continue
        h, x = d.get(m), d.get(partner[m])
        if h is None or x is None:
            continue
        per[m]["H"].append(h); per[m]["X"].append(x); per[m]["Q"].append(Q[k])
    med = {m: {c: statistics.median(v) for c, v in d.items()}
           for m, d in per.items() if len(d["H"]) >= a.min_passages}
    print("models with >= %d such passages: %d\n" % (a.min_passages, len(med)))

    pairs = []
    for base, members in sorted(lin.items()):
        for al in [m for m in members if m != base]:
            if base in med and al in med:
                pairs.append((base, al, med[base], med[al]))
    if not pairs:
        print("no lineage has both arms"); return
    print("THE SIX, median over %d lineage pairs   (BITS PER BYTE)" % len(pairs))
    print("%-18s %10s %10s %10s %10s" % ("", "H self", "X partner", "Q deepseek", "Q - H"))
    for lab, i in (("base output", 2), ("aligned output", 3)):
        d = [p[i] for p in pairs]
        print("%-18s %10.4f %10.4f %10.4f %10.4f"
              % (lab, statistics.median(x["H"] for x in d),
                 statistics.median(x["X"] for x in d),
                 statistics.median(x["Q"] for x in d),
                 statistics.median(x["Q"] - x["H"] for x in d)))

    print("\nALIGNED - BASE, paired within lineage, sign test")
    print("%-40s %9s %5s %5s %10s" % ("", "median", "up", "dn", "p"))
    for lab, f in (("H  self-surprisal", lambda b, A: A["H"] - b["H"]),
                   ("Q  external (deepseek)", lambda b, A: A["Q"] - b["Q"]),
                   ("Q - H  the outsider's excess", 
                    lambda b, A: (A["Q"] - A["H"]) - (b["Q"] - b["H"]))):
        n, up, dn, m, p = sign_test([f(b, A) for _, _, b, A in pairs])
        print("%-40s %+9.4f %5d %5d %10.3g" % (lab, m, up, dn, p))
    print("""
Q - H SHRINKING under alignment means the outsider followed the model in: the
text became more probable to deepseek by about as much as it became more
probable to its own generator, so alignment moved it toward what is generically
likely. Q - H GROWING means self-entropy fell and the outsider did NOT follow --
alignment narrowed onto the model's own idiosyncrasies, and the two things the
literature calls "reducing entropy" would be different claims.""")


if __name__ == "__main__":
    main()
