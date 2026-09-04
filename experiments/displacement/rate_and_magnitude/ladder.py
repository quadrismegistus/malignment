"""Rate structure on SELF-EDGES, along the training ladder.

The self-edge section of the README shows the frame alone sheds risers and
concentrates arrival, on weights nobody touched. This asks WHERE ON THE LADDER
that responsiveness is installed: SFT, or DPO?

Two quantities, deliberately kept apart, because they answer differently:

    MARGINAL          how many words move under the frame at all
    DOSE-CONDITIONAL  how that count responds to the prompt's lift

The dose is `charge.lift(prompt, base) = T_base - frame`, and it exists only for
the 50 endpoint BASES -- no intermediate rung is a base of any pair, so no rung
has its own lift. Each rung is therefore dosed with ITS OWN FAMILY'S base lift,
which is the model these rungs descend from and is constant within a family. A
cross-lineage median over unrelated bases was tried first and is wrong: it is a
different, noisier instrument, and it manufactured stage structure that the
family's own lift does not show.

Two controls the bare per-rung slopes need:

  (a) TOTAL MOVERS vs lift. If high-lift prompts simply have fewer movable words,
      n_fallers and n_risers both slope down for a population reason and neither
      slope means what it looks like. Only fall-rise is free of it. This control
      FIRES -- t = -2.0 to -5.8 in all eight rungs.

  (b) THE STAGE CONTRAST TAKEN WITHIN PROMPT. Every rung sees the same prompts,
      so the SFT->DPO step is a paired difference with the dose held literally
      identical, not two independently estimated slopes compared by eye.

    python -m experiments.displacement.rate_and_magnitude.ladder
"""
import math

from malignment import ch, charge
from malignment.ch import _lit

# base -> [(rung label, model)], in ladder order. The base is the dose source.
LADDERS = {
    "Tulu-3": ("meta-llama/Llama-3.1-8B", [
        ("SFT", "allenai/Llama-3.1-Tulu-3-8B-SFT"),
        ("SFT-no-math", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-math-data"),
        ("SFT-no-persona", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-persona-data"),
        ("SFT-no-safety", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data"),
        ("SFT-no-wildchat", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data"),
        ("DPO", "allenai/Llama-3.1-Tulu-3-8B-DPO"),
    ]),
    "OLMoE": ("allenai/OLMoE-1B-7B-0125", [
        ("SFT", "allenai/OLMoE-1B-7B-0125-SFT"),
        ("DPO", "allenai/OLMoE-1B-7B-0125-DPO"),
        ("Instruct", "allenai/OLMoE-1B-7B-0125-Instruct"),
    ]),
    "OLMo-2": ("allenai/OLMo-2-0425-1B", [
        ("SFT", "allenai/OLMo-2-0425-1B-SFT"),
        ("DPO", "allenai/OLMo-2-0425-1B-DPO"),
        ("Instruct", "allenai/OLMo-2-0425-1B-Instruct"),
    ]),
    "Olmo-3": ("allenai/Olmo-3-1025-7B", [
        ("SFT", "allenai/Olmo-3-7B-Instruct-SFT"),
        ("DPO", "allenai/Olmo-3-7B-Instruct-DPO"),
        ("Instruct", "allenai/Olmo-3-7B-Instruct"),
    ]),
}
# the paired stage contrast needs exactly one SFT and one DPO; the Tulu
# ablations and the Instruct rungs are reported marginally but not contrasted.
CONTRAST = ("SFT", "DPO")


def ols_t(xs, ys):
    """(slope, t against zero). OLS standard error."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    rss = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    return b, b / math.sqrt(rss / (n - 2) / sxx)


def paired_t(d):
    n = len(d)
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    return m, m / (sd / math.sqrt(n))


def counts(model):
    """{prompt: (n_fallers, n_risers)} on the model's own self-edge."""
    rows = ch.query(
        "SELECT prompt, countIf(cls='faller') nf, countIf(cls='riser') nr "
        "FROM movement_v4 WHERE base=%s AND aligned=%s AND base=aligned "
        "GROUP BY prompt" % (_lit(model), _lit(model)))
    return {r["prompt"]: (float(r["nf"]), float(r["nr"])) for r in rows}


def main():
    seen = {}
    for fam, (base, rungs) in LADDERS.items():
        lift = {p: float(v) for (p, b), v in charge.lifts_per_lineage(base).items()}
        for rung, model in rungs:
            seen[(fam, rung)] = (counts(model), lift)

    print("SELF-EDGE RATE STRUCTURE ALONG THE LADDER")
    print("base == aligned, frame_base='' -> frame_aligned='prefill'.")
    print("dose = each family's OWN base lift, constant within a family.\n")

    print("MARGINAL -- how much moves under the frame, per prompt")
    print("%-8s %-16s %7s %8s %8s %8s" % ("family", "rung", "n", "n_fall", "n_rise", "n_tot"))
    for fam, (_, rungs) in LADDERS.items():
        for rung, _m in rungs:
            c, _ = seen[(fam, rung)]
            n = len(c)
            f = sum(v[0] for v in c.values()) / n
            r = sum(v[1] for v in c.values()) / n
            print("%-8s %-16s %7d %8.1f %8.1f %8.1f" % (fam, rung, n, f, r, f + r))
        print()

    print("(a) CONTROL -- do high-lift prompts simply have fewer movers at all?")
    print("%-8s %-16s %7s %9s %7s" % ("family", "rung", "n", "d n_tot", "t"))
    for fam, (_, rungs) in LADDERS.items():
        for rung, _m in rungs:
            c, lift = seen[(fam, rung)]
            ps = [p for p in c if p in lift]
            b, t = ols_t([lift[p] for p in ps], [c[p][0] + c[p][1] for p in ps])
            print("%-8s %-16s %7d %9.3f %7.1f" % (fam, rung, len(ps), b, t))
    print("\n    fires everywhere -- so the bare n_fall / n_rise slopes are")
    print("    mostly this, and only fall-rise is free of it.\n")

    print("(b) DOSE-CONDITIONAL, per rung (fall-rise only; see the control)")
    print("%-8s %-16s %7s %9s %7s" % ("family", "rung", "n", "d diff", "t"))
    for fam, (_, rungs) in LADDERS.items():
        for rung, _m in rungs:
            c, lift = seen[(fam, rung)]
            ps = [p for p in c if p in lift]
            b, t = ols_t([lift[p] for p in ps], [c[p][0] - c[p][1] for p in ps])
            print("%-8s %-16s %7d %9.3f %7.1f" % (fam, rung, len(ps), b, t))
        print()

    a, z = CONTRAST
    print("(c) THE %s -> %s STEP, TAKEN WITHIN PROMPT" % (a, z))
    print("    same prompts at both rungs, so the dose is identical, not matched.\n")
    print("%-8s %6s %9s %6s %9s %6s %9s %6s %9s %6s" % (
        "family", "n", "d n_tot", "t", "d dfall", "t", "d drise", "t", "d ddiff", "t"))
    for fam, (_, rungs) in LADDERS.items():
        cs, lift = seen[(fam, a)]
        cd, _ = seen[(fam, z)]
        shared = [p for p in cs if p in cd]
        m_tot, t_tot = paired_t([(cd[p][0] + cd[p][1]) - (cs[p][0] + cs[p][1])
                                 for p in shared])
        ps = [p for p in shared if p in lift]
        xs = [lift[p] for p in ps]
        cols = [ols_t(xs, [cd[p][0] - cs[p][0] for p in ps]),
                ols_t(xs, [cd[p][1] - cs[p][1] for p in ps]),
                ols_t(xs, [(cd[p][0] - cd[p][1]) - (cs[p][0] - cs[p][1]) for p in ps])]
        print("%-8s %6d %9.2f %6.1f %9.3f %6.1f %9.3f %6.1f %9.3f %6.1f" % (
            fam, len(ps), m_tot, t_tot,
            cols[0][0], cols[0][1], cols[1][0], cols[1][1], cols[2][0], cols[2][1]))
    print("\n    d n_tot is MARGINAL (unpaired n differs: it needs no lift).")
    print("    the stage claim has n=4 families, not n=%d prompts." % len(ps))


if __name__ == "__main__":
    main()
