"""Which features respond to dose under 2 or 3 of the three doses?

    python -u dose_agreement.py                 # writes dose_agreement.csv, prints the table

THE RULE (RH, 2026-08-27): a feature significant under 2 of 3 doses is ROBUST;
under 3 of 3 is robust and unanimous. One dose is not enough, because each of the
three has a known defect and they are not the same defect:

    k_transgressiveness   a global type-level lexicon. 63.4% of prompts sit within
                          5% of its floor and it ranks quid-pro-quo coercion BELOW
                          knife attacks -- it sees transgression only where the
                          vocabulary is marked.
    slot_loaded_mass      per-prompt tagging from a 200-word union list. Collapses
                          where the loaded option is available but rare (0.0045 on
                          a slamming frame) and saturates where the transgression
                          is in the SETUP (0.98 on `stabbed him in the ___`).
    v6_harm_mass          contextual harm ratings that already existed. Fixes the
                          first failure -- `punched` scores high in a slamming
                          scene -- and shares the second. Covers 744 prompts
                          against 1,944 and ~2,700.

Because the defects differ, agreement across doses is evidence that a slope is
about alignment rather than about how loadedness was measured. Disagreement is not
evidence of a weak effect; it is evidence that at least one dose is measuring
something else on those targets.

SIGN IS CHECKED, NOT ASSUMED. Two doses can both clear p<0.05 pointing opposite
ways -- 10 such pairs exist in `fields` -- and that is a contradiction, not a
replication. `agree_sign` is reported separately from `n_significant`.
"""
import argparse, csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
TABLES = os.path.expanduser("~/malignment-data/norm_change/dose_tables")
DOSES = [("k_transgressiveness", "lexical"),
         ("slot_loaded_mass", "slot"),
         ("v6_harm_mass", "v6_harm")]


def load(dose, table, lang="en"):
    p = os.path.join(TABLES, "dose_%s__%s_%s.csv" % (dose, table, lang))
    if not os.path.exists(p):
        return {}
    out = {}
    with open(p) as fh:
        for r in csv.DictReader(fh):
            out[r["target"]] = (float(r["med_slope"]), float(r["p"]),
                                int(r["up"]), int(r["dn"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", default=os.path.join(HERE, "dose_agreement.csv"))
    a = ap.parse_args(argv)
    import numpy as np

    rows = []
    for table in ("levels", "fields", "contextual"):
        T = {d: load(d, table, a.lang) for d, _ in DOSES}
        common = sorted(set.intersection(*[set(v) for v in T.values() if v])) if all(T.values()) else []
        for k in common:
            sig = [d for d, _ in DOSES if T[d][k][1] < a.alpha]
            slopes = [T[d][k][0] for d, _ in DOSES]
            sigslopes = [T[d][k][0] for d in sig]
            agree = len({np.sign(s) for s in sigslopes}) <= 1 if sigslopes else True
            rows.append(dict(
                table=table, target=k, n_significant=len(sig),
                agree_sign=int(agree),
                robust=int(len(sig) >= 2 and agree),
                unanimous=int(len(sig) == 3 and agree),
                mean_slope=float(np.mean(slopes)),
                direction=("rise" if np.mean(slopes) > 0 else "fall"),
                **{("%s_slope" % lbl): T[d][k][0] for d, lbl in DOSES},
                **{("%s_p" % lbl): T[d][k][1] for d, lbl in DOSES}))
    rows.sort(key=lambda r: (-r["robust"], -r["n_significant"], -abs(r["mean_slope"])))
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    print("dose agreement, lang=%s, alpha=%.2f -- ROBUST = significant on >=2 of 3 "
          "doses WITH consistent sign\n" % (a.lang, a.alpha))
    print("%-12s %8s %9s %9s %9s" % ("table", "targets", "3 of 3", "2 of 3", "ROBUST"))
    for table in ("levels", "fields", "contextual"):
        sub = [r for r in rows if r["table"] == table]
        if not sub: continue
        print("%-12s %8d %9d %9d %9d"
              % (table, len(sub), sum(r["unanimous"] for r in sub),
                 sum(1 for r in sub if r["n_significant"] == 2 and r["agree_sign"]),
                 sum(r["robust"] for r in sub)))
        contra = [r for r in sub if r["n_significant"] >= 2 and not r["agree_sign"]]
        if contra:
            print("%-12s %s" % ("", "  CONTRADICTORY (sig on >=2, opposite signs): %d -- %s"
                                % (len(contra), ", ".join(r["target"] for r in contra[:6]))))
    print("\n-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
