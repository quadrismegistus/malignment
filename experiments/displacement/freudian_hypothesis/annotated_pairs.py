"""Paired norm contrasts over the pairs a blind coder actually linked.

    python -u annotated_pairs.py                 the contrasts
    python -u annotated_pairs.py --dose          split by the frame's charge
    python -u annotated_pairs.py --write         -> results/annotated_pairs.json

## WHY THIS IS NOT norm_change AGAIN

`norm_change` contrasts two ARMS: every word carrying mass in the base against
every word carrying mass in the aligned, mass-weighted, whatever relation holds
between them. It cannot tell a substitution from two unrelated populations that
happen to sit either side of an alignment step.

This contrasts two WORD GROUPS A BLIND READER SAID BELONG TOGETHER. The unit is
an operation -- `kill die` against `punch tear smack` at one frame in one lineage
-- so the comparison is between a departing set and the set a human-scale reader
judged to have replaced it. That is the pairing Freud's account needs and that
every instrument in this folder so far has lacked.

It may reproduce `norm_change` exactly, in which case the annotation adds
confidence and nothing else. It may not, and the interesting case is a norm that
moves here and not there: a change visible only between LINKED sets is a change
in what substitutes for what, not in what the arm contains.

## A IS THE BASE ARM, AND THIS IS CHECKED RATHER THAN ASSUMED

`crosslineage.tables()` renders `_table_two_column(nb, na)` with `nb` the base
arm and `na` the aligned one, and `--blind` relabels the MODELS (M01..M50), not
the columns. So `a_words` is the base side throughout. The coder, blind to which
was which, wrote *"Kill, whenever it moves, always moves toward condition A"* --
which is the convention holding, observed from the outside.

`--check-orientation` verifies it against `twp_words_v4` rather than trusting
either of those: for every operation it compares the arms' actual mass on the
cited words and reports how often A is the heavier side.

## THE UNIT IS THE LINEAGE, AS EVERYWHERE ELSE

An operation is one (frame, lineage, coder-reading) and there are thousands, but
they are not independent: 43 lineages read at one frame share the frame, and one
lineage appears at 96 frames. Contrasts are averaged within a lineage first and
the sign test runs over lineages, which is the denominator the rest of this
campaign uses.
"""
import argparse, collections, json, os, statistics as st, sys
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
STASH = os.path.join(ROOT, "experiments", "displacement", "displacement_taxonomy",
                     "results", "crosslineage_stash", "jsonl.hashstash.raw",
                     "data.jsonl")
OUT = os.path.join(HERE, "results", "annotated_pairs.json")

#: every continuous norm the campaign carries, by grain. The v6 scales are
#: CONTEXTUAL -- rated for a word at a prompt -- so they are looked up on
#: (frame, word) and simply absent where the frame was never rated.
K_SCALES = ("bodily_harm", "transgressiveness", "charge", "valence",
            "concreteness", "vulgarity", "register_level")
W_SCALES = ("valence", "arousal", "dominance", "concreteness")

#: **NOT NORMS, AND ONE OF THEM IS THE OUTCOME.** Some `slot_ratings` entries
#: carry movement bookkeeping beside the twelve v6 scales -- on 154 of 220 word
#: entries at the frames checked, so they are also unevenly present. `net` is
#: `rise - fall`, a count of the very movement being contrasted, and it came
#: back at the top of the first run's table (+5.15, 0/50, p=2e-15) looking like
#: the strongest result in the folder. It is the instrument reading itself.
#: Excluded by the same name list `norm_change/plot_fields.py` uses.
NOT_NORMS = {"net", "net_rate", "rise", "fall", "n_present", "n_eligible",
             "ratable"}


def operations():
    """-> (frame, lineage nick, op name, a_words, b_words) from the stash."""
    n = 0
    for line in open(STASH, encoding="utf-8"):
        r = json.loads(line)
        frame = r["__key__"]["frame_prompt"]
        for o in (r.get("operations") or []):
            for m in (o.get("members") or []):
                a, b = m.get("a_words") or [], m.get("b_words") or []
                if not a or not b:
                    continue
                n += 1
                yield frame, m.get("model"), o.get("name"), a, b
    print("%s (operation x lineage) pairs" % format(n, ","), file=sys.stderr)


_CTX = {}


def norms_for(frame, words):
    """{scale: mean over the words that carry it}. Absent scales are omitted.

    `slot_ratings` is memoised per FRAME. Without it the lookup was rebuilt for
    each of 8,646 operations over 96 frames -- ninety times the work, and slow
    enough that the first run had to be backgrounded.
    """
    from malignment import fields as F
    acc = collections.defaultdict(list)
    if frame not in _CTX:
        _CTX[frame] = F.slot_ratings(frame) if frame else {}
    ctx = _CTX[frame]
    for w in words:
        k = F.k(w)
        if k:
            for s in K_SCALES:
                acc["k_" + s].append(float(k[s]))
        wn = F.word_norms(w)
        if wn:
            for s in W_SCALES:
                if s in wn:
                    acc[("brysbaert_concreteness" if s == "concreteness"
                         else "warriner_" + s)].append(float(wn[s]))
        v6 = ((ctx.get(w) or {}).get("v6") if isinstance(ctx, dict) else None)
        if v6:
            for s, v in v6.items():
                if s in NOT_NORMS or isinstance(v, bool) \
                        or not isinstance(v, (int, float)):
                    continue
                acc["v6:" + s].append(float(v))
    return {s: st.fmean(v) for s, v in acc.items() if v}


def sign(vals):
    v = [x for x in vals if x is not None]
    n = len(v)
    below = sum(1 for x in v if x < 0)
    k = min(below, n - below)
    return {"median": st.median(v), "below_0": below, "n": n,
            "p_sign": min(1.0, sum(comb(n, i) for i in range(k + 1)) * 2 / 2 ** n)}


def collect():
    """-> per-lineage mean contrast per norm, plus the same split by frame dose."""
    from malignment import charge
    dose = charge.doses()
    #: lineage -> norm -> [aligned mean - base mean], one entry per operation
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    hi = collections.defaultdict(lambda: collections.defaultdict(list))
    lo = collections.defaultdict(lambda: collections.defaultdict(list))
    dv = sorted(v for f, v in dose.items())
    #: the frame population's own terciles, so "high dose" means high AMONG
    #: PROMPTS rather than high on an absolute 1-7 scale nobody calibrated
    cut_lo, cut_hi = dv[len(dv) // 3], dv[2 * len(dv) // 3]
    nop = ndose = 0
    for frame, lin, _name, a, b in operations():
        na, nb_ = norms_for(frame, a), norms_for(frame, b)
        shared = set(na) & set(nb_)
        if not shared or not lin:
            continue
        nop += 1
        d = dose.get(frame)
        for s in shared:
            gap = nb_[s] - na[s]
            per[lin][s].append(gap)
            #: the middle tercile is DROPPED, not assigned. A three-way split
            #: whose middle goes into one of the ends is a two-way split with a
            #: misleading cut printed beside it.
            if d is not None and d >= cut_hi:
                hi[lin][s].append(gap)
            elif d is not None and d <= cut_lo:
                lo[lin][s].append(gap)
        if d is not None:
            ndose += 1
    print("%s pairs usable, %s with a frame dose; terciles at %.2f / %.2f"
          % (format(nop, ","), format(ndose, ","), cut_lo, cut_hi), file=sys.stderr)

    def agg(d):
        scales = collections.Counter()
        for lin in d:
            for s in d[lin]:
                scales[s] += 1
        out = {}
        for s, nlin in scales.items():
            if nlin < 25:
                continue
            out[s] = sign([st.fmean(d[lin][s]) for lin in d if d[lin].get(s)])
        return out

    main = agg(per)
    #: THE DOSE ARM IS A CONTRAST OF CONTRASTS, within lineage. A lineage's
    #: high-dose frames against its own low-dose frames, so a lineage that
    #: simply moves more cannot register as dose response.
    dosed = {}
    scales = {s for lin in hi for s in hi[lin]} & {s for lin in lo for s in lo[lin]}
    for s in scales:
        use = [lin for lin in hi if hi[lin].get(s) and lo.get(lin, {}).get(s)]
        vals = [st.fmean(hi[lin][s]) - st.fmean(lo[lin][s]) for lin in use]
        if len(vals) >= 25:
            r = sign(vals)
            #: **THE GAP ALONE CANNOT SAY WHICH WAY EITHER END WENT.** A norm
            #: that falls at both doses and falls LESS when charged reads
            #: identically to one that falls flat and rises when charged. Both
            #: levels are carried so the direction is stated rather than
            #: inferred from a subtraction.
            r["at_low_dose"] = st.median([st.fmean(lo[lin][s]) for lin in use])
            r["at_high_dose"] = st.median([st.fmean(hi[lin][s]) for lin in use])
            dosed[s] = r
    return main, dosed, nop


def check_orientation(limit=400):
    """Is `a_words` really the base side? Verified against twp, not assumed."""
    from malignment import corpus, roster
    eps, _ = roster.endpoints()
    nick = {b.split("/")[-1]: (b, a) for b, a in eps.items()}
    nick.update({a.split("/")[-1]: (b, a) for b, a in eps.items()})
    ok = bad = skip = 0
    for frame, lin, _n, a, b in operations():
        pair = nick.get(lin)
        if not pair:
            skip += 1
            continue
        try:
            pb = corpus.words(pair[0], frame, rule_version=4)
            pa = corpus.words(pair[1], frame, rule_version=4)
        except Exception:
            skip += 1
            continue
        ma = sum(pb.get(w, 0.0) for w in a) - sum(pa.get(w, 0.0) for w in a)
        mb = sum(pa.get(w, 0.0) for w in b) - sum(pb.get(w, 0.0) for w in b)
        if ma > 0 and mb > 0:
            ok += 1
        else:
            bad += 1
        if ok + bad >= limit:
            break
    print("orientation: %d of %d checked pairs have A heavier in BASE and B "
          "heavier in ALIGNED (%d unresolvable)" % (ok, ok + bad, skip))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dose", action="store_true")
    ap.add_argument("--check-orientation", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.check_orientation:
        return check_orientation()
    main_, dosed, nop = collect()
    print("\nALIGNED MINUS BASE over %s annotated pairs, per lineage then median\n"
          % format(nop, ","))
    print("  %-26s %9s %10s %11s" % ("norm", "median", "below 0", "p"))
    for s, r in sorted(main_.items(), key=lambda t: -abs(t[1]["median"])):
        print("  %-26s %+9.4f %5d/%-4d %11.2g"
              % (s, r["median"], r["below_0"], r["n"], r["p_sign"]))
    if a.dose:
        print("\nDOSED BY FRAME -- a lineage's top-tercile frames minus its own "
              "bottom-tercile\n")
        print("  %-26s %10s %10s %9s %9s %10s"
              % ("norm", "flat", "charged", "gap", "below 0", "p"))
        for s, r in sorted(dosed.items(), key=lambda t: -abs(t[1]["median"])):
            print("  %-26s %+10.4f %+10.4f %+9.4f %4d/%-4d %10.2g"
                  % (s, r["at_low_dose"], r["at_high_dose"], r["median"],
                     r["below_0"], r["n"], r["p_sign"]))
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump({"n_pairs": nop, "marginal": main_, "dosed": dosed},
                  open(OUT, "w"), indent=1)
        print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
