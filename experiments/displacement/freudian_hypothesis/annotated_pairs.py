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
OUT_MASS = os.path.join(HERE, "results", "annotated_pairs_mass.json")

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
_MASS = {}


def mass_for(frame):
    """{aligned nick: (base {word:p}, aligned {word:p})} for one frame, or {}.

    **RENORMALISED PER ARM, AS THE CODER'S TABLE WAS.** `crosslineage.tables()`
    divides each arm by its own total before rendering, so the coder judged
    shares of measured mass rather than raw probabilities. Weighting by anything
    else would weight the words by a quantity the reader never saw.
    """
    if frame in _MASS:
        return _MASS[frame]
    from malignment import roster, vectors as V
    ep, _ = roster.endpoints()
    try:
        rows = V.rows("SELECT model, groupArray(word) AS ws, groupArray(p) AS ps "
                      "FROM twp_words_v4_best WHERE prompt={p:String} "
                      "AND merged=1 GROUP BY model", p=frame)
    except Exception:
        _MASS[frame] = {}
        return {}
    W = {r["model"]: dict(zip(r["ws"], r["ps"])) for r in rows}
    out = {}
    for b, a in ep.items():
        if b in W and a in W and sum(W[b].values()) and sum(W[a].values()):
            tb, ta = sum(W[b].values()), sum(W[a].values())
            out[a.split("/")[-1]] = ({w: p / tb for w, p in W[b].items()},
                                     {w: p / ta for w, p in W[a].items()})
    _MASS[frame] = out
    return out


def norms_for(frame, words, weights=None):
    """{scale: mean over the words that carry it}. Absent scales are omitted.

    `slot_ratings` is memoised per FRAME. Without it the lookup was rebuilt for
    each of 8,646 operations over 96 frames -- ninety times the work, and slow
    enough that the first run had to be backgrounded.
    """
    from malignment import fields as F
    acc = collections.defaultdict(list)
    wt = collections.defaultdict(list)
    if frame not in _CTX:
        _CTX[frame] = F.slot_ratings(frame) if frame else {}
    ctx = _CTX[frame]
    for w in words:
        u = 1.0 if weights is None else float(weights.get(w, 0.0))
        k = F.k(w)
        if k:
            for s in K_SCALES:
                acc["k_" + s].append(float(k[s])); wt["k_" + s].append(u)
        wn = F.word_norms(w)
        if wn:
            for s in W_SCALES:
                if s in wn:
                    key = ("brysbaert_concreteness" if s == "concreteness"
                           else "warriner_" + s)
                    acc[key].append(float(wn[s])); wt[key].append(u)
        #: **THE INSTITUTIONAL INSTRUMENT IS NOT RESTRICTED TO INSTITUTIONAL
        #: FRAMES.** Its name says otherwise and that is why it was missed: it
        #: covers 2,511 prompts and 92 of the 96 frames here, and it carries
        #: `arousal` -- "how much emotional INTENSITY does the completion carry,
        #: regardless of whether it is positive or negative" -- which is the
        #: CONTEXTUAL affect measure this file twice reported the corpus as
        #: lacking. Prefixed `inst:` because both instruments define
        #: `vocalisation` and pooling them would put two constructs on one name.
        inst = ((ctx.get(w) or {}).get("slot_institutional_en_v3")
                if isinstance(ctx, dict) else None)
        if inst:
            for sc, v in inst.items():
                if sc in NOT_NORMS or isinstance(v, bool) \
                        or not isinstance(v, (int, float)):
                    continue
                acc["inst:" + sc].append(float(v)); wt["inst:" + sc].append(u)
        v6 = ((ctx.get(w) or {}).get("v6") if isinstance(ctx, dict) else None)
        if v6:
            for s, v in v6.items():
                if s in NOT_NORMS or isinstance(v, bool) \
                        or not isinstance(v, (int, float)):
                    continue
                acc["v6:" + s].append(float(v)); wt["v6:" + s].append(u)
    out = {}
    for s, v in acc.items():
        if not v:
            continue
        ws = wt[s]
        tot = sum(ws)
        #: a set whose words carry NO measured mass has no weighted mean, and
        #: falling back to the unweighted one would silently mix the two
        #: estimators inside one table
        if weights is not None and tot <= 0:
            continue
        out[s] = (st.fmean(v) if weights is None
                  else sum(x * y for x, y in zip(v, ws)) / tot)
    return out


def sign(vals):
    v = [x for x in vals if x is not None]
    n = len(v)
    below = sum(1 for x in v if x < 0)
    k = min(below, n - below)
    return {"median": st.median(v), "below_0": below, "n": n,
            "p_sign": min(1.0, sum(comb(n, i) for i in range(k + 1)) * 2 / 2 ** n)}


def collect(mass=False):
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
        if mass:
            mm = mass_for(frame).get(lin)
            if not mm:
                continue
            na, nb_ = norms_for(frame, a, mm[0]), norms_for(frame, b, mm[1])
        else:
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


def examples(n=8, hold=0.25, drop=1.0, mass=False):
    """Pairs where the affect survives the loss of the act, and where it does not.

    **THE TWO CELLS FREUD'S ACCOUNT SEPARATES.** The idea's fate and the affect's
    fate are independent in his scheme, so the interesting contrast is not
    "big change / small change" but the CROSS: harm gone with the charge intact
    is a transformation, harm gone with the charge gone is plain suppression.
    `hold` is how close to zero counts as intact and `drop` how far counts as
    lost; both are printed, because there is no principled cut and a reader
    should see which one produced the list.
    """
    from malignment import charge
    dose = charge.doses()
    rows = []
    for frame, lin, name, a, b in operations():
        if mass:
            mm = mass_for(frame).get(lin)
            if not mm:
                continue
            na, nb_ = norms_for(frame, a, mm[0]), norms_for(frame, b, mm[1])
        else:
            na, nb_ = norms_for(frame, a), norms_for(frame, b)
        if "k_charge" not in na or "k_charge" not in nb_:
            continue
        dc = nb_["k_charge"] - na["k_charge"]
        dh = (nb_.get("k_bodily_harm", 0) - na.get("k_bodily_harm", 0))
        rows.append({"frame": frame, "lin": lin, "name": name, "a": a, "b": b,
                     "d_charge": dc, "d_harm": dh, "dose": dose.get(frame)})
    #: only where an ACT was actually lost -- otherwise "charge held" is a
    #: statement about two sets that never differed
    #: **DEDUPED FOR DISPLAY ONLY.** A frame was read 2 to 16 times, so the same
    #: (frame, lineage, A-set, B-set) recurs across readings and the list filled
    #: with the same pair twice. The STATISTICS keep every reading -- a pair two
    #: readers both found is more evidence, not one observation.
    seen, uniq = set(), []
    for r in rows:
        k = (r["frame"], r["lin"], tuple(r["a"]), tuple(r["b"]))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    lost = [r for r in uniq if r["d_harm"] <= -drop]
    held = sorted([r for r in lost if abs(r["d_charge"]) <= hold],
                  key=lambda r: -abs(r["d_harm"]))
    fell = sorted([r for r in lost if r["d_charge"] <= -drop],
                  key=lambda r: r["d_charge"])
    print("%s pairs (%s distinct); %s lose at least %.1f of bodily harm.\n"
          "   of those: %s hold charge within +-%.2f, %s lose at least %.1f of it"
          % (format(len(rows), ","), format(len(uniq), ","),
             format(len(lost), ","), drop,
             format(len(held), ","), hold, format(len(fell), ","), drop))
    for lab, rs in (("THE ACT GOES, THE CHARGE STAYS", held),
                    ("THE ACT GOES AND THE CHARGE GOES WITH IT", fell)):
        print("\n=== %s\n" % lab)
        for r in rs[:n]:
            print("  %s   [%s, dose %s]"
                  % (r["frame"][:58], r["lin"][:26],
                     ("%.2f" % r["dose"]) if r["dose"] is not None else "-"))
            print("    %s" % r["name"][:70])
            print("    base    %s" % " ".join(r["a"][:10]))
            print("    aligned %s" % " ".join(r["b"][:10]))
            print("    harm %+.2f   charge %+.2f\n" % (r["d_harm"], r["d_charge"]))
    return held, fell


DEPOSIT = os.path.expanduser("~/malignment-data/dose_response/charge_en50_flash.jsonl")


def scene_index(frames):
    """{(frame, word): mean scene}, plus {frame: frame rating}, from task_charge.

    The completed-scene rating is IN CONTEXT: `kissed` after "pinned his roommate
    to the floor and" is a scene at 6.14 where the word alone rates 3. That gap
    is the quantity this comparison exists to measure.
    """
    want = set(frames)
    acc = collections.defaultdict(list)
    fr = collections.defaultdict(list)
    for line in open(DEPOSIT, encoding="utf-8"):
        d = json.loads(line)
        if d["prompt"] not in want:
            continue
        fr[d["prompt"]].append(d["frame"])
        for w in d["words"]:
            acc[(d["prompt"], w["word"])].append(w["scene"])
    return ({k: st.fmean(v) for k, v in acc.items()},
            {k: st.fmean(v) for k, v in fr.items()})


def affect_compare():
    """Does the type-level charge agree with the in-context scene? -> prints

    **THE SAME ERROR IN A NEW PLACE, WHICH IS WHY THIS RUNS AT ALL.** This file's
    affect axis is `k_charge`, rated on the word ALONE. On `raped -> kissed` at
    "He pinned his roommate to the floor and" it reports a 4-point collapse while
    the completed scene falls 0.86, because the frame carries the charge and the
    word only modifies it. If that generalises, today's "the affect is not
    conserved on the annotated pairs" is the type-level instrument talking.

    **`scene` IS NOT AN AFFECT MEASURE EITHER** -- it asks how transgressive the
    completed scene is, which is content in context, not affective quantity. It
    is the only IN-CONTEXT quantity the corpus has, so it can show that a
    type-level reading misses what the frame preserves; it cannot stand in for
    the affect. No contextual measure of affective intensity exists here.
    """
    from malignment import fields as F
    pairs = list(operations())
    idx, frates = scene_index({f for f, _l, _n, _a, _b in pairs})
    print("scene ratings for %s (frame, word) keys over %d frames"
          % (format(len(idx), ","), len(frates)), file=sys.stderr)

    def mean(fn, frame, ws):
        v = [fn(frame, w) for w in ws]
        v = [x for x in v if x is not None]
        return st.fmean(v) if v else None

    kf = lambda _f, w: (lambda k: float(k["charge"]) if k else None)(F.k(w))
    sf = lambda f, w: idx.get((f, w))
    per = collections.defaultdict(lambda: ([], []))
    both = []
    for frame, lin, _n, a, b in pairs:
        ka, kb = mean(kf, frame, a), mean(kf, frame, b)
        sa, sb = mean(sf, frame, a), mean(sf, frame, b)
        if None in (ka, kb, sa, sb) or not lin:
            continue
        dk, ds = kb - ka, sb - sa
        both.append((dk, ds))
        per[lin][0].append(dk)
        per[lin][1].append(ds)
    n = len(both)
    mk, ms = st.fmean(x for x, _ in both), st.fmean(y for _, y in both)
    sk, ss = st.pstdev([x for x, _ in both]), st.pstdev([y for _, y in both])
    r = (sum((x - mk) * (y - ms) for x, y in both) / n / (sk * ss)) if sk and ss else 0
    agree = sum(1 for x, y in both if (x > 0) == (y > 0))
    kneg_spos = sum(1 for x, y in both if x < 0 and y >= 0)
    print("\n%s pairs carry BOTH a type charge and an in-context scene\n"
          % format(n, ","))
    print("   mean delta, type-level k_charge     %+.4f" % mk)
    print("   mean delta, in-context scene        %+.4f" % ms)
    print("   pearson r between them              %+.3f" % r)
    print("   agree in sign                       %.1f%%" % (100 * agree / n))
    print("   k_charge FALLS while the scene does NOT: %s pairs (%.1f%%)"
          % (format(kneg_spos, ","), 100 * kneg_spos / n))
    dk = [st.fmean(v[0]) for v in per.values()]
    ds = [st.fmean(v[1]) for v in per.values()]
    print("\n   per lineage, median over %d lineages:" % len(per))
    print("      k_charge  %+.4f   (%d of %d below 0)"
          % (st.median(dk), sum(1 for x in dk if x < 0), len(dk)))
    print("      scene     %+.4f   (%d of %d below 0)"
          % (st.median(ds), sum(1 for x in ds if x < 0), len(ds)))
    return 0


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
    ap.add_argument("--mass", action="store_true",
                    help="weight each word by its share of its own arm's measured mass, as the coder's table showed it")
    ap.add_argument("--check-orientation", action="store_true")
    ap.add_argument("--examples", action="store_true")
    ap.add_argument("--affect-compare", action="store_true")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.check_orientation:
        return check_orientation()
    if a.affect_compare:
        return affect_compare()
    if a.examples:
        examples(n=a.n, mass=a.mass)
        return 0
    main_, dosed, nop = collect(mass=a.mass)
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
        out = OUT_MASS if a.mass else OUT
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump({"n_pairs": nop, "weighted": bool(a.mass),
                   "marginal": main_, "dosed": dosed},
                  open(out, "w"), indent=1)
        print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
