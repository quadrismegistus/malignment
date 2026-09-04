"""What the bare stem says, against the predictions recorded before it ran.

    python .../analyse.py

Reads `results/dists.jsonl`. Every number here is the summed first-person mass
at the next-word slot of "Who are you?", in two frames.

## DEDUP, AND THE FREE DETERMINISM CHECK IT GAVE

Two processes wrote this file for its first three nodes -- one launch whose log
redirect failed on a relative path, read as a dead process and relaunched. The
duplicates are keyed identically, so they dedup on `(model, frame, prompt)`.

They also agreed to the last digit on all 6 affected keys, which is a
determinism check on the instrument that would not otherwise have been run. It
is reported rather than silently discarded, and this file FAILS LOUDLY if any
key ever carries two different values.

## THE REASONING TRAP

SmolLM3's chat template opens `<think>`, which takes 0.9998 of the slot. For
such a model the post-template next word is not the answer, it is the opening of
the reasoning block, and a first-person mass of 0.0000 there means "the slot is
not the answer" and NOT "the model does not say I". The roster's `reasoning`
flag marks 1 of 43 nodes and misses these, so they are detected from `p_think`
in the data and excluded from the chat-frame comparison with their number shown.
"""
import collections, json, math, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
SRC = os.path.join(HERE, "results", "dists.jsonl")
PSEUDO_BASE_MED = 0.512      # from FINDING_pseudo_template.md, for contrast
THINK = 0.5                  # p_think above this = the slot is a reasoning block


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def main():
    recs = [json.loads(l) for l in open(SRC)]
    uniq, clash = {}, []
    for d in recs:
        k = (d["model"], d["frame"], d["prompt"])
        if k in uniq:
            a, b = uniq[k].get("p_first"), d.get("p_first")
            if a != b:
                clash.append((k, a, b))
            continue
        uniq[k] = d
    print("records %d -> unique %d | duplicate keys disagreeing: %d"
          % (len(recs), len(uniq), len(clash)))
    if clash:
        print("  *** NON-DETERMINISTIC, the dedup is not safe ***")
        for k, a, b in clash:
            print("   ", k, a, b)
        return 1

    P = {}                                   # (model, frame) -> rec
    for (m, f, _), d in uniq.items():
        P[(m, f)] = d
    models = sorted({m for m, _ in P})
    role = {d["model"]: d["role"] for d in uniq.values()}
    base_of = {d["model"]: d["base"] for d in uniq.values()}

    think = [m for m in models
             if (P.get((m, "chat")) or {}).get("p_think", 0) > THINK]
    print("\nreasoning nodes detected from p_think > %.1f: %d" % (THINK, len(think)))
    for m in think:
        r = P[(m, "chat")]
        print("   %-50s p_think=%.4f  p_first=%.4f" % (m.split("/")[-1][:50],
                                                       r["p_think"], r["p_first"]))

    def val(m, f):
        r = P.get((m, f))
        if not r or "refused" in r:
            return None
        if f == "chat" and m in think:
            return None
        return r["p_first"]

    # ---------------------------------------------------------------- P1
    print("\n" + "=" * 74)
    print("P1  the raw base floor.  predicted: median < 0.10 (pseudo-template: %.3f)"
          % PSEUDO_BASE_MED)
    braw = sorted(v for m in models if role[m] == "base"
                  for v in [val(m, "raw")] if v is not None)
    print("  n=%d  median %.4f  min %.4f  max %.4f" % (len(braw), statistics.median(braw),
                                                       braw[0], braw[-1]))
    print("  VERDICT: %s" % ("HELD" if statistics.median(braw) < 0.10 else "FAILED"))
    print("  every base, raw:")
    for m in sorted((m for m in models if role[m] == "base"), key=lambda x: val(x, "raw") or -1):
        print("     %-50s %.4f" % (m.split("/")[-1][:50], val(m, "raw")))

    # ---------------------------------------------------------------- P2
    print("\n" + "=" * 74)
    print("P2  the interaction.  predicted: chat moves across the ladder, raw does not")
    for frame in ("raw", "chat"):
        rows = []
        for m in models:
            if role[m] == "base":
                continue
            b = base_of[m]
            x, y = val(b, frame), val(m, frame)
            if x is None or y is None:
                continue
            rows.append((m, role[m], x, y))
        if not rows:
            print("\n  %-5s no comparable pairs at all" % frame)
            continue
        d = sorted(y - x for _, _, x, y in rows)
        u = sum(1 for _, _, x, y in rows if y > x)
        f_ = sum(1 for _, _, x, y in rows if y < x)
        print("\n  %-5s n=%d  rises %d  falls %d  median %+.4f  sign p=%.4f"
              % (frame, len(rows), u, f_, d[len(d) // 2], binom(min(u, f_), u + f_)))
        byop = collections.defaultdict(list)
        for m, r, x, y in rows:
            byop[r].append(y - x)
        for op in sorted(byop, key=lambda o: -len(byop[o])):
            v = sorted(byop[op])
            print("      %-14s n=%2d  median %+.4f" % (op, len(v), v[len(v) // 2]))

    # ------------------------------------------------- the two clean lineages
    print("\n" + "=" * 74)
    print("THE WITHIN-LINEAGE INTERACTION, where the rendered frame is byte-identical")
    print("two lineages. reported as two lineages, never as a test.")
    for b in ("m-a-p/neo_7b", "openbmb/MiniCPM5-1B-Base"):
        print("\n  %s" % b)
        chain = [m for m in models if base_of[m] == b]
        chain.sort(key=lambda m: (role[m] != "base", m))
        print("     %-46s %9s %9s" % ("", "raw", "chat"))
        for m in chain:
            r, c = val(m, "raw"), val(m, "chat")
            print("     %-46s %9s %9s"
                  % (m.split("/")[-1][:46],
                     "%.4f" % r if r is not None else "--",
                     "%.4f" % c if c is not None else "--"))

    # ---------------------------------------------------------------- P4
    print("\n" + "=" * 74)
    print("P4  the Tulu ablations.  predicted: no-persona drops most; <0.05 spread = unresolved")
    ab = {m: (val(m, "raw"), val(m, "chat")) for m in models if "Tulu-3-8B-SFT" in m}
    full = "allenai/Llama-3.1-Tulu-3-8B-SFT"
    for m in sorted(ab, key=lambda x: (ab[x][1] is None, ab[x][1])):
        r, c = ab[m]
        tag = "  <-- full SFT" if m == full else ""
        dc = "" if (c is None or ab[full][1] is None) else "  d=%+.4f" % (c - ab[full][1])
        print("   %-52s raw %.4f  chat %s%s%s"
              % (m.split("/")[-1][:52], r, "%.4f" % c if c is not None else "--", dc, tag))
    cs = [c for (_, c) in ab.values() if c is not None]
    if len(cs) >= 2:
        spread = max(cs) - min(cs)
        print("   chat spread across the %d ablations: %.4f -> %s"
              % (len(cs), spread,
                 "UNRESOLVED (<0.05)" if spread < 0.05 else "resolved enough to order"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
