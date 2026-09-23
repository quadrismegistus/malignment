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

LIFT IS THE FOURTH DOSE, AND THE RULE IS NOW 2 OF 4 ACROSS FAMILIES
(RH, 2026-09-12). The three original doses are LEVELS -- how transgressive the
base arm's mass was at a prompt. `charge.lift` is `dose - frame`, how much the
candidate words ADD OVER their setup, and charge.py documents it as the dose
displacement work wants: corr(effect, level) -0.091 against corr(effect, lift)
-0.261. It was held outside the vote for one round on the grounds that adding it
would restate the threshold by arithmetic. That was backwards. The rule's whole
rationale is that THE DEFECTS MUST DIFFER, and the three level doses SHARE one:
they all read the loadedness of the setup, which is what `slot_loaded_mass`
saturates on (0.98 on `stabbed him in the ___`). Lift is built to separate
exactly that case, so holding out the one member that does not share the common
defect is the opposite of robustness.

THE BAR STAYS AT TWO, AND GAINS A FAMILY CONSTRAINT. "2 of 3" never encoded a
count; it encoded "two instruments whose defects differ agree in sign". Moving
to 3 of 4 would raise the standard with nothing behind it (it costs 20 of 55
robust field targets). Plain 2 of 4 has the opposite hole: `v6_harm_mass` and
`lift` are both LLM contextual ratings of a word in its frame, so two of those
agreeing is ONE family twice. Hence FAMILIES, and the two significant doses must
come from different ones:

    type-lexicon     k_transgressiveness
    slot-tagging     slot_loaded_mass
    llm-contextual   v6_harm_mass, lift

Cost of the family constraint against plain 2 of 4: 1 field target, 2 contextual,
0 levels.

**THIS THRESHOLD WAS CHOSEN AFTER SEEING WHAT IT DOES TO ONE CONTESTED TARGET**
(`Q2.2 Speech acts`, which passes on lexical+lift and fails at 2 of 3). That is
the wrong order and is recorded rather than hidden. The check offered at the time:
LEVELS returns 31 robust targets under 2-of-3, 2-of-4, 2-of-4-cross-family AND
3-of-4 alike, so the campaign's stable core does not depend on the choice; only
`fields` and `contextual` move.

A DOSE THAT DOES NOT COVER A TARGET ABSTAINS; IT DOES NOT VETO. The first version
took `set.intersection` over the three tables, so `v6_harm_mass` -- which covers
744 prompts against 1,944 and ~2,700 and holds 34 contextual targets against 57
-- silently decided WHICH TARGETS WERE ASSESSED AT ALL. 23 contextual targets
were never evaluated and at least one of them, `slot_rating_en_v6:vocalisation`,
is robust. A target now needs two covering doses to clear, which it could never
have done on coverage alone, so nothing is admitted by the change that the rule
would not admit anyway.

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
         ("v6_harm_mass", "v6_harm"),
         ("lift", "lift")]
#: WHICH DEFECT EACH DOSE HAS, not which file it came from. Two doses in one
#: family cannot corroborate each other, because the rule is about defects
#: differing and theirs do not.
FAMILY = {"lexical": "type-lexicon", "slot": "slot-tagging",
          "v6_harm": "llm-contextual", "lift": "llm-contextual"}
K_AGREE = 2


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
    ap.add_argument("--k", type=int, default=K_AGREE,
                    help="doses that must agree. The rule is 2; raising it is a "
                         "change of standard and belongs in the docstring with a date.")
    ap.add_argument("--same-family-ok", action="store_true",
                    help="drop the cross-family requirement. Diagnostic only: it "
                         "lets v6_harm_mass and lift corroborate each other, and "
                         "they share a defect.")
    #: The three-dose table this replaced is kept as `dose_agreement_3dose_2026-08-27.csv`.
    #: README.md quotes numbers from it, and a silently replaced file is how a
    #: README comes to describe results that no longer exist (`dose.py --out`).
    ap.add_argument("--out", default=os.path.join(HERE, "dose_agreement.csv"))
    a = ap.parse_args(argv)
    import numpy as np

    rows = []
    for table in ("levels", "fields", "contextual"):
        T = {d: load(d, table, a.lang) for d, _ in DOSES}
        #: UNION, not intersection: a dose that does not cover a target abstains.
        #: See the docstring -- the intersection let the narrowest dose decide
        #: which targets were assessed at all.
        targets = sorted(set().union(*[set(v) for v in T.values()])) if any(T.values()) else []
        for k in targets:
            have = [(d, lbl) for d, lbl in DOSES if k in T[d]]
            sig = [(d, lbl) for d, lbl in have if T[d][k][1] < a.alpha]
            slopes = [T[d][k][0] for d, _ in have]
            sigslopes = [T[d][k][0] for d, _ in sig]
            agree = len({np.sign(s) for s in sigslopes}) <= 1 if sigslopes else True
            fams = {FAMILY[lbl] for _, lbl in sig}
            cross = a.same_family_ok or len(fams) >= 2
            robust = int(len(sig) >= a.k and agree and cross)
            rows.append(dict(
                table=table, target=k,
                n_covering=len(have), n_significant=len(sig),
                families=len(fams), agree_sign=int(agree), cross_family=int(cross),
                robust=robust,
                unanimous=int(len(sig) == len(have) == len(DOSES) and agree),
                mean_slope=float(np.mean(slopes)),
                direction=("rise" if np.mean(slopes) > 0 else "fall"),
                **{("%s_slope" % lbl): (T[d][k][0] if k in T[d] else "")
                   for d, lbl in DOSES},
                **{("%s_p" % lbl): (T[d][k][1] if k in T[d] else "")
                   for d, lbl in DOSES}))
    rows.sort(key=lambda r: (-r["robust"], -r["n_significant"], -abs(r["mean_slope"])))
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    print("dose agreement, lang=%s, alpha=%.2f -- ROBUST = significant on >=%d of "
          "%d doses,\nWITH consistent sign AND from at least two families "
          "(%s)\n"
          % (a.lang, a.alpha, a.k, len(DOSES),
             "same-family allowed" if a.same_family_ok else "cross-family required"))
    print("%-12s %8s %9s %9s %9s %9s"
          % ("table", "targets", "all doses", "ROBUST", "contra", "1-dose"))
    for table in ("levels", "fields", "contextual"):
        sub = [r for r in rows if r["table"] == table]
        if not sub:
            continue
        contra = [r for r in sub if r["n_significant"] >= 2 and not r["agree_sign"]]
        blocked = [r for r in sub if r["n_significant"] >= a.k and r["agree_sign"]
                   and not r["cross_family"]]
        print("%-12s %8d %9d %9d %9d %9d"
              % (table, len(sub), sum(r["unanimous"] for r in sub),
                 sum(r["robust"] for r in sub), len(contra),
                 sum(1 for r in sub if r["n_significant"] == 1)))
        if contra:
            print("%-12s   CONTRADICTORY (>=2 sig, opposite signs): %s"
                  % ("", ", ".join(r["target"] for r in contra[:6])))
        if blocked:
            print("%-12s   BLOCKED by the family rule: %s"
                  % ("", ", ".join(r["target"] for r in blocked[:6])))
        thin = [r for r in sub if r["n_covering"] < len(DOSES)]
        if thin:
            print("%-12s   %d target(s) not covered by every dose; the missing "
                  "dose abstains" % ("", len(thin)))

    print("\n-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
