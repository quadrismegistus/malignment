"""Directedness by kind of frame, within verb slots. -> results/directedness_frames.md

    python -u directedness_frames.py

**WHAT THIS IS, HONESTLY.** On 2026-09-23 the paper seat found, by grouping
prompts with keywords AFTER seeing per-prompt results, that `v6:directedness`
nets to zero on the Figure 4 plate because it moves in opposite directions by
kind of frame: down in drive frames, up in "I should" frames and in intimacy
frames. Keywords chosen after looking are not a test. This file fixes the
grouping by a rule stated before this run (agreed with malign, same day), drops
the intimacy set (its keywords were picked from the results), and adds the
controls malign asked for:

    grievance   the frame ends "I should"
    drive       the frame ends "wanted to", "began to" or "started to"
    other       everything else

    strata      all prompts; VERB slots only (base-side dominant POS = VERB at
                purity >= 0.6, from slot_pos/results/prompt_pos_en.csv); and
                grievance frames split at the median of their base VERB share,
                since they are the least verbal rated slots (malign)
    charge      each family again by lift third (RH), cut at the tertiles of
                the lift of this table's rated rows

It is a REPLICATION of a pattern already seen, under a declared rule and a
control, not a blind test. The drive and grievance directions were known when
the rule was written.

## THE STATISTIC IS THE PLATE'S

Per (lineage, prompt), the move `aligned_level - base_level` on the contextual
table behind Figure 4 (`gated_levels.SRC % "contextual"`, the same coverage gate
`GATE`), averaged over the family's prompts within a lineage; the median over the
50 endpoint lineages; a sign test on the lineage means (ties dropped).
"""
import csv, gzip, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "displacement", "norm_change"))
SLOT_POS = os.path.join(ROOT, "experiments", "exploratory", "slot_pos", "results",
                        "prompt_pos_en.csv")
OUT = os.path.join(HERE, "results", "directedness_frames.md")
SCALE = "v6:directedness"
PURITY = 0.6


def family(p):
    s = p.rstrip()
    if s.endswith("I should"):
        return "grievance"
    if s.endswith(("wanted to", "began to", "started to")):
        return "drive"
    return "other"


def main():
    from scipy.stats import binomtest
    from gated_levels import GATE, SRC
    from malignment import roster, charge
    lpl = charge.lifts_per_lineage()
    keep = {"%s>%s" % (b, a) for b, a in roster.endpoints()[0].items()}
    pos = {}
    with open(SLOT_POS, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            pos[r["prompt"]] = (r["pos_base"], float(r["purity_base"]), float(r["base_VERB"]))
    griev_verb = sorted(v[2] for p, v in pos.items() if family(p) == "grievance")
    gmed = st.median(griev_verb) if griev_verb else None

    strata = {
        "all prompts": lambda p: True,
        "verb slots": lambda p: p in pos and pos[p][0] == "VERB" and pos[p][1] >= PURITY,
    }
    acc = {}   # (stratum, family) -> lineage -> [moves]
    prompts = {}
    rows = []
    with gzip.open(SRC % "contextual", "rt") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if f[ix["lang"]] != "en" or f[ix["scale"]] != SCALE:
                continue
            lin = "%s>%s" % (f[ix["base"]], f[ix["aligned"]])
            if lin not in keep:
                continue
            try:
                b = float(f[ix["base_level"]]); a = float(f[ix["aligned_level"]])
                if min(float(f[ix["base_cov"]]), float(f[ix["aligned_cov"]])) < GATE:
                    continue
            except ValueError:
                continue
            p = f[ix["prompt"]]
            rows.append((lin, p, a - b, lpl.get((p, f[ix["base"]]))))
            fam = family(p)
            groups = [(s, fam) for s, test in strata.items() if test(p)]
            if fam == "grievance" and p in pos and gmed is not None:
                groups.append(("grievance by verb share",
                               "more verbal" if pos[p][2] >= gmed else "less verbal"))
            for g in groups:
                acc.setdefault(g, {}).setdefault(lin, []).append(a - b)
                prompts.setdefault(g, set()).add(p)

    lifts = sorted(r[3] for r in rows if r[3] is not None)
    lo, hi = lifts[len(lifts) // 3], lifts[2 * len(lifts) // 3]
    for lin, p, mv, lf in rows:
        if lf is None:
            continue
        band = "low lift" if lf <= lo else ("mid lift" if lf <= hi else "high lift")
        fam = family(p)
        for s, test in strata.items():
            if test(p):
                g = (s + ", " + band, fam)
                acc.setdefault(g, {}).setdefault(lin, []).append(mv)
                prompts.setdefault(g, set()).add(p)
    lines = ["# %s by kind of frame" % SCALE, "",
             "Declared grouping and strata: see the producer's docstring. A REPLICATION "
             "under a declared rule, not a blind test. Move = aligned minus base level, "
             "mean over the family's prompts within a lineage; median over lineages; "
             "sign test over lineages.", "",
             "| stratum | family | prompts | lineages | median move | up | down | p |",
             "|---|---|---|---|---|---|---|---|"]
    for g in sorted(acc):
        per = [st.fmean(v) for v in acc[g].values()]
        up = sum(x > 0 for x in per); dn = sum(x < 0 for x in per)
        p = binomtest(min(up, dn), up + dn).pvalue if up + dn else 1.0
        lines.append("| %s | %s | %d | %d | %+.3f | %d | %d | %.2g |"
                     % (g[0], g[1], len(prompts[g]), len(per), st.median(per), up, dn, p))
    if gmed is not None:
        lines += ["", "Grievance frames split at their median base VERB share, %.3f." % gmed]
    lines += ["Lift thirds cut at %+.3f and %+.3f over this table's rated rows; a family's"
              " prompt can sit in more than one third across lineages." % (lo, hi)]
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
