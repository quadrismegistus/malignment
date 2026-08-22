"""Score a generated ladder on the abstraction and interiority axes.

    ~/github/lltk/.venv/bin/python .../ladder_pilot_score.py --ladder olmo-tiny

**RUN THIS IN THE LLTK VENV**, not the one that generated the passages. The
scorer needs `lltk.tools.constants` for the modernizer and `malignment.fields`
for the lexicons; the generator needs transformers 4.57.1 for the OLMo configs.
Two environments, one reason each, and neither holds both.

## WHAT IT ANSWERS

Where each RUNG falls on the two axes `novel_arc` measured, so the base-to-
aligned move can be decomposed into its steps. Reports the per-rung median, the
step-by-step delta, and the share of the total base-to-endpoint move that each
step accounts for.

## WHY THE SHARE MATTERS MORE THAN THE SIGN

Every rung after the base will differ from the base somehow. The question is
whether one STEP carries the move, so the readout is the fraction of the total
displacement attributable to each transition, not whether each transition is
individually non-zero.

Sign, as everywhere here: `rh_absconc_median` is HIGH = CONCRETE, so a move
toward abstraction is NEGATIVE. `usas_x` is higher = more interior.
"""

import argparse, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/rj416/github/malignment")

LADDERS = {
    "olmo-tiny": ["allenai/OLMo-2-0425-1B",
                  "allenai/OLMo-2-0425-1B-SFT",
                  "allenai/OLMo-2-0425-1B-DPO",
                  "allenai/OLMo-2-0425-1B-Instruct"],
    "olmo-3": ["allenai/Olmo-3-1025-7B",
               "allenai/Olmo-3-7B-Instruct-SFT",
               "allenai/Olmo-3-7B-Instruct-DPO",
               "allenai/Olmo-3-7B-Think-SFT",
               "allenai/Olmo-3-7B-Think-DPO"],
}
STEM = "He was beautiful and disgusting and she wanted to"
COLS = ["rh_absconc_median", "usas_x", "brysbaert_concreteness",
        "gi_positiv", "k_bodily_harm"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ladder", default="olmo-tiny", choices=sorted(LADDERS))
    ap.add_argument("--stem", default=STEM)
    ap.add_argument("--min-words", type=int, default=60)
    a = ap.parse_args(argv)
    from malignment import Checkpoint
    from measure_lltk import Scorer

    S = Scorer()
    rows = {}
    for m in LADDERS[a.ladder]:
        ck = Checkpoint(m)
        got = [p for p in ck.generations(prompt=a.stem, frame="raw")]
        vals = {c: [] for c in COLS}
        for p in got:
            txt = getattr(p, "text", "") or ""
            if len(txt.split()) < a.min_words:
                continue
            r = S.score(txt)
            if not r:
                continue
            for c in COLS:
                if r.get(c) is not None:
                    vals[c].append(r[c])
        rows[m] = vals
        print("  %-42s %4d generations, %4d scored"
              % (m.split("/")[-1], len(got), len(vals[COLS[0]])), flush=True)

    order = [m for m in LADDERS[a.ladder] if rows.get(m) and rows[m][COLS[0]]]
    if len(order) < 2:
        print("too few rungs with passages to compare"); return
    print("\n%-30s %6s %s" % ("rung", "n", " ".join("%-13s" % c[:13] for c in COLS)))
    med = {}
    for m in order:
        v = rows[m]
        med[m] = {c: st.median(v[c]) for c in COLS if v[c]}
        print("%-30s %6d %s" % (m.split("/")[-1][:30], len(v[COLS[0]]),
                                " ".join("%-13s" % ("%+.4f" % med[m][c])
                                         for c in COLS)))

    base = order[0]
    print("\nSTEP DELTAS, and the share of the base-to-endpoint move each carries")
    for c in COLS:
        total = med[order[-1]][c] - med[base][c]
        print("  %s   base %+.4f -> endpoint %+.4f   total %+.4f"
              % (c, med[base][c], med[order[-1]][c], total))
        prev = base
        for m in order[1:]:
            d = med[m][c] - med[prev][c]
            #: a share is only meaningful when the total is not ~0; a tiny
            #: denominator turns noise into a large percentage.
            sh = ("%6.0f%%" % (100 * d / total)) if abs(total) > 0.01 else "    --"
            print("      %-34s %+.4f  %s"
                  % ("%s -> %s" % (prev.split("/")[-1][-12:],
                                   m.split("/")[-1][-12:]), d, sh))
            prev = m


if __name__ == "__main__":
    main()
