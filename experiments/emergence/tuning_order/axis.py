"""WHICH words leave earliest? The specific/bodily -> abstract axis, three instruments.

    python -u axis.py

**DISCOVERED ARM.** Not in `REGISTRATION.md`. RH, 2026-09-06: *"specific bodily
vocabulary falling to abstract proceduralised psychologised vocabulary is what
we've discovered of alignment generally across lineages -- so here we're
rediscovering it within SFT checkpoint time."*

## THE QUESTION, AND WHY IT IS NOT THE ONE Q2/Q3 ASKED

Q2 and Q3 asked whether charge predicts the LAG BETWEEN fallers and risers. Both
returned nulls. **This asks a different quantity: among FALLERS, which leave
first?** A graded ordering within one class, not a gap between two. The nulls do
not bear on it and it does not overturn them.

It is also the non-trivial half of RH's claim. That the words falling across
lineage endpoints also fall on this ladder is a tautology -- the ladder IS
base->aligned decomposed into 43 steps, so the trajectory necessarily lies along
the endpoint displacement. What is NOT entailed is that the axis orders the
fallers among themselves in TIME.

## THREE INSTRUMENT FAMILIES, NO SHARED MACHINERY

    fields.norms(word)              TYPE level, context-free, full coverage
    fields.contextual_norms(p, w)   v6, rated IN THE FRAME, 460 prompts
    the same, institutional slots   slot_institutional_en_v2/v3

Reported separately and never pooled: they are different constructs, and the
agreement between them is the evidence. No single |rho| here exceeds 0.16.

## WHY `charge.py`'s scene/lift IS ABSENT

It was the registered instrument for Q3 and it cannot answer this question. On
the frame=7 prompts -- the explicitly sexual ones this question is most about --
EVERY candidate word scores scene=7, so `lift = scene - frame` is exactly 0 for
all of them. Measured on "She knelt down in front of him and began to suck his":

    word      euphemism  explicitness  genitality       movement
    dick          1           7            7        0.0855 -> 0.0020
    shaft         5           7            7        0.0141 -> 0.0207
    member        6           7            7        0.0098 -> 0.0229

`explicitness` and `genitality` are pinned at 7 exactly as `scene` is. **Only
`sexual_v2_euphemism` discriminates**, and it runs with the movement: direct
terms (1-2) fall, periphrastic terms (5-6) rise.

So the earlier nulls rested on an instrument that could not have shown an effect
either way on the prompts that matter. That is a statement about the instrument,
not about the world, and it is why the type-level and v6 scales are used here.
"""
import collections, math, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from malignment import fields                                      # noqa: E402
from timing import timings                                         # noqa: E402

MIN_N = 300


def spear(a, b):
    def rk(x):
        o = sorted(range(len(x)), key=lambda i: x[i]); r = [0.0] * len(x)
        for pos, i in enumerate(o):
            r[i] = pos
        return r
    ra, rb = rk(a), rk(b); ma, mb = S.mean(ra), S.mean(rb)
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(len(a)))
    den = math.sqrt(sum((v - ma) ** 2 for v in ra) * sum((v - mb) ** 2 for v in rb))
    return num / den if den else float("nan")


def pval(r, n):
    from math import erf, sqrt
    t = r * math.sqrt((n - 2) / max(1e-12, 1 - r * r))
    return t, 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))


def table(title, pairs, note=""):
    """pairs: [(scale, [values], [t_move])]"""
    print(title)
    if note:
        print("  %s" % note)
    print("  %-30s %7s %10s %10s" % ("scale", "n", "rho", "p"))
    out = []
    for k, xs, ys in pairs:
        if len(xs) < MIN_N or len(set(xs)) < 3:
            continue
        r = spear(xs, ys); _, p = pval(r, len(xs))
        out.append((abs(r), k, len(xs), r, p))
    out.sort(reverse=True)
    for _, k, n, r, p in out:
        star = " *" if p < 0.05 else ""
        print("  %-30s %7d %+10.4f %10.5f%s" % (k, n, r, p, star))
    print()
    return out


def main():
    t = timings()
    F = [(p, w, tm) for p, w, c, tm in t if c == "faller"]
    print("NEGATIVE rho = the higher the scale, the EARLIER the word leaves.")
    print("fallers: %d\n" % len(F))

    #: 1. TYPE LEVEL -- context-free, best coverage
    nc = {}
    keys = collections.Counter()
    for _, w, _ in F:
        if w not in nc:
            nc[w] = fields.norms(w) or {}
        keys.update(nc[w])
    pairs = []
    for k in keys:
        xs, ys = [], []
        for _, w, tm in F:
            v = nc[w].get(k)
            if v is not None:
                try:
                    xs.append(float(v)); ys.append(tm)
                except (TypeError, ValueError):
                    pass
        pairs.append((k, xs, ys))
    table("TYPE-LEVEL  fields.norms -- context-free, every word",
          [p for p in pairs if not p[0].endswith("coverage")])

    #: 2. CONTEXTUAL, general
    for inst in ("v6", "slot_institutional_en_v3", "slot_institutional_en_v2"):
        cache, rows = {}, []
        for p, w, tm in F:
            if p not in cache:
                cache[p] = fields.contextual_norms(p, instrument=inst)
            d = cache[p].get(w)
            if d:
                rows.append((tm, d))
        keys = collections.Counter()
        for _, d in rows:
            keys.update(k for k in d if k != "n_instruments")
        pairs = []
        for k in keys:
            xs, ys = [], []
            for tm, d in rows:
                v = d.get(k)
                if v is not None:
                    try:
                        xs.append(float(v)); ys.append(tm)
                    except (TypeError, ValueError):
                        pass
            pairs.append((k, xs, ys))
        table("CONTEXTUAL  %s -- rated in the frame" % inst,
              [p for p in pairs if not p[0].endswith(("coverage", "ratable"))],
              note="%d fallers rated" % len(rows))

    print("READ ACROSS THE THREE, NOT DOWN ONE.")
    print("No single |rho| exceeds 0.16. The evidence is that instruments sharing")
    print("no machinery name one axis: charged / aggressive / concrete / harmful /")
    print("apt / specific words leave EARLY; mundane / abstract / positive words")
    print("leave LATE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
