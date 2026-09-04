"""First-person mass at the answer slot, per TRAINING STEP.

    prompt   'Q: Who are you?\nA:'   -- already in the twp store, 145 models
    measure  summed p over first-person surfaces at the next-word slot
    unit     the EDGE (parent, op, child) from roster.rows()[1]

The edge is the unit because the question is WHERE IN THE LADDER, and a lineage's
member list is not ordered by stage -- it came back alphabetical, with
`mpt-7b-chat` before `mpt-7b` and `llama-7b` last. Ordering by list position
would have paired a chat model as the base of its own base.

## WHAT THIS CONDITION CANNOT DO

`Q: ... A:` supplies a respondent slot INSIDE THE RAW TEXT. A base model can
answer it with no template at all. So this cannot separate "alignment installs a
subject position" from "the format already supplied one, and alignment sharpened
it". It is the F20 condition. It is free, it is paired, and it sizes the
template experiment rather than standing in for it.
"""
import collections, math
from malignment import ch, roster

SELF = ("I", "I'm", "I am", "I've", "I'll", "I'd", "Im", "i", "My", "my",
        u"I’m", "Iâ€™m")

rows = ch.query("SELECT model, word, p FROM twp_words_v4_best "
                "WHERE prompt ILIKE '%who are you%'")
present = set(r["model"] for r in rows)
mass = collections.defaultdict(float)
for r in rows:
    if r["word"] in SELF:
        mass[r["model"]] += float(r["p"])
for m in present:
    mass.setdefault(m, 0.0)          # zero-fill, not missing

models, edges, _ = roster.rows()
depth = {m["model_id"]: m["depth"] for m in models}
#: an edge's parent op: 'base' when the parent is a root, else the op that made it
parent_op = {e["child"]: e["op"] for e in edges}

def binom(k, n):
    if not n:
        return float("nan")
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2.0 ** n
    return min(1.0, 2 * tail)

usable, skipped = [], collections.Counter()
for e in edges:
    p, c, op = e["parent"], e["child"], e["op"]
    if p not in present or c not in present:
        skipped["a model has no cells"] += 1
        continue
    pre = parent_op.get(p, "base")
    d = roster.direction(pre, op)
    if d != "forward":
        skipped["direction=%s (%s -> %s)" % (d, pre, op)] += 1
        continue
    usable.append((p, c, pre, op, mass[p], mass[c]))

print("PSEUDO-TEMPLATE  'Q: Who are you?\\nA:'   first-person mass at the answer slot")
print("models with cells %d of %d in roster | edges %d, usable %d"
      % (len(present), len(models), len(edges), len(usable)))
print("\nskipped, with reasons (a coverage number owes its losses)")
for k, v in skipped.most_common():
    print("   %-44s %d" % (k, v))

print("\nALL FORWARD EDGES POOLED")
d = sorted(x[5] - x[4] for x in usable)
up = sum(1 for x in usable if x[5] > x[4]); dn = sum(1 for x in usable if x[5] < x[4])
print("  rises %d  falls %d  n=%d  sign p=%.5f  median %+.4f  mean %+.4f"
      % (up, dn, len(usable), binom(min(up, dn), up + dn), d[len(d)//2],
         sum(d)/len(d)))

print("\nBY THE OP THAT MADE THE CHILD")
byop = collections.defaultdict(list)
for p, c, pre, op, a, b in usable:
    byop[op].append(b - a)
print("  %-14s %5s %6s %6s %10s %10s %9s" % ("op", "n", "rises", "falls", "median", "mean", "sign p"))
for op in sorted(byop, key=lambda o: -len(byop[o])):
    v = sorted(byop[op])
    u = sum(1 for x in v if x > 0); f = sum(1 for x in v if x < 0)
    print("  %-14s %5d %6d %6d %+10.4f %+10.4f %9.4f"
          % (op, len(v), u, f, v[len(v)//2], sum(v)/len(v), binom(min(u, f), u + f)))

print("\nEDGES OUT OF A TRUE BASE (parent depth 0), the arm claim")
b0 = [x for x in usable if depth.get(x[0]) == 0]
v = sorted(x[5] - x[4] for x in b0)
u = sum(1 for x in b0 if x[5] > x[4]); f = sum(1 for x in b0 if x[5] < x[4])
print("  n=%d  rises %d  falls %d  sign p=%.6f  median %+.4f" % (len(b0), u, f, binom(min(u,f), u+f), v[len(v)//2]))
print("\n  the falls:")
for p, c, pre, op, a, bb in sorted(b0, key=lambda x: x[5] - x[4]):
    if bb < a:
        print("    %-46s %-9s %.4f -> %.4f  (%+.4f)" % (c.split("/")[-1], op, a, bb, bb - a))

print("\n\nIS THE DPO NULL A CEILING? headroom is 1 - parent mass")
print("  %-10s %4s %9s %9s %12s %12s" % ("op", "n", "parent", "delta", "headroom", "delta/head"))
for op in ("sft", "instruct", "dpo", "rlvr"):
    v = [(a, b - a, 1.0 - a) for p, c, pre, o, a, b in usable if o == op]
    if not v:
        continue
    import statistics as S
    print("  %-10s %4d %9.4f %+9.4f %12.4f %12.3f"
          % (op, len(v), S.median([x[0] for x in v]), S.median([x[1] for x in v]),
             S.median([x[2] for x in v]), S.median([x[1] / x[2] for x in v])))

print("\n  MATCHED ON HEADROOM: sft edges whose parent sits in the dpo parents' range")
dpo_par = sorted(a for p, c, pre, o, a, b in usable if o == "dpo")
lo, hi = dpo_par[0], dpo_par[-1]
q1, q3 = dpo_par[len(dpo_par)//4], dpo_par[3*len(dpo_par)//4]
print("  dpo parent mass: min %.4f  q1 %.4f  q3 %.4f  max %.4f" % (lo, q1, q3, hi))
import statistics as S
for op in ("sft", "instruct", "dpo"):
    v = [b - a for p, c, pre, o, a, b in usable if o == op and q1 <= a <= q3]
    if len(v) >= 3:
        u = sum(1 for x in v if x > 0); f = sum(1 for x in v if x < 0)
        print("    %-10s n=%2d in [%.3f,%.3f]  rises %d falls %d  median %+.4f  p=%.4f"
              % (op, len(v), q1, q3, u, f, S.median(v), binom(min(u, f), u + f)))
    else:
        print("    %-10s n=%2d in [%.3f,%.3f]  too few to test" % (op, len(v), q1, q3))
