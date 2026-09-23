"""Does freed mass land on semantically adjacent words (displacement) or scatter?

    python -u adjacency.py

## THE TEST

For each cell, take the top faller and note its `kind` (SEXUAL, VIOLENT, etc).
Among the risers in the same cell, split them:

    same-kind     risers sharing the faller's kind (semantic neighbours)
    diff-kind     risers with a different non-NONE kind
    none-kind     risers tagged NONE (non-transgressive)

Displacement predicts same-kind risers gain MORE than diff/none risers —
the charge redirects within the same domain. Diffusion predicts no difference.
Suppression predicts none-kind risers gain most (mass moves to neutral words).

Unit is the lineage. Within each lineage, compare mean delta of same-kind
vs none-kind risers across prompts. Sign-test: do more lineages show
same-kind > none-kind?
"""

import collections
import json
import math
import os
import re
import sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j)
               for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def measure(frame="raw", match_framed=False):
    from malignment import ch, charge, fields, roster

    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages: %s" % sorted(unresolved)[:3])

    #: same two flags as `run.py`, same reasons. The framed contrast is
    #: base_raw -> aligned_framed and is ASYMMETRIC -- 43 of 50 bases ship no
    #: chat template, so it is the deployed arm against the bare one.
    #: `clean_slot` is not optional: `frame_aligned='prefill'` alone mixes empty
    #: system slots with personas and date blocks, because `system_mode` records
    #: the argument passed and not the treatment received.
    mode_of = {}
    self_arm = {}
    if frame == "self":
        #: SELF-EDGES: base == aligned, unframed against framed. Where does the
        #: freed mass go when only the TEMPLATE changes? Two arms, 45 aligned
        #: and 8 base, reported SEPARATELY -- see run.py for why the base arm is
        #: direction-only and why pooling defeats the question.
        from malignment import movement as M
        al, ba = set(eps.values()), set(eps)
        mode_of = {(b, a): m for b, a, m in
                   M.clean_frame_pairs(self_edges="only")}
        eps = {}
        for (b, a) in mode_of:
            eps[b] = a
            self_arm[b] = "aligned" if b in al else ("base" if b in ba else "?")
    elif match_framed or frame != "raw":
        from malignment import movement as M
        mode_of = {(b, a): m for b, a, m in M.clean_frame_pairs()
                   if eps.get(b) == a}
        eps = {b: a for b, a in eps.items() if (b, a) in mode_of}

    print("ADJACENCY: does freed mass land on same-kind words (displacement)")
    print("           or scatter to unrelated words (diffusion/suppression)?")
    print("           %d lineages  [frame=%s]" % (len(eps), frame))
    if frame != "raw":
        print("           base_raw -> aligned_framed, clean system slot only")
    print()

    scenes_cache = {}
    kinds_cache = {}
    def get_ratings(prompt):
        if prompt not in scenes_cache:
            scenes_cache[prompt] = charge.scene(prompt)
            kinds_cache[prompt] = charge.kinds(prompt)
        return scenes_cache[prompt], kinds_cache[prompt]

    #: STRATIFIED COPY, same code path. Part 1 of this folder stratifies by
    #: dose and by lift; this test stratified by neither, and no reason was ever
    #: recorded. Stratifying by saturation ALONE reported the low band as an
    #: exact null (24/24) -- which turned out to be a reversal at low lift and a
    #: recovery at high, averaged. Both cuts are taken together for that reason.
    by_strat = collections.defaultdict(lambda: {"same": [], "none": [], "n": 0})
    kinds_of = {}

    #: THE CONDITIONAL FIELD TEST. `norm_change` already gives the MARGINAL
    #: field shift over 50 lineages, raw and framed -- aggression down, speech
    #: and sensation up. A marginal shift cannot answer THIS question: "speech
    #: rises and aggression falls" is equally true whether each aggression
    #: word's mass went to speech, or whether unrelated words moved in both
    #: fields. Conditioning on the top faller's own field separates them, and
    #: that separation is displacement against suppression.
    #:
    #: USAS rather than `kind` because `kind` sorts by HOW BAD, not WHAT ABOUT:
    #: `kill` is VIOLENT and `scream` is NONE, so the campaign's paradigm case
    #: of displacement scores as CROSS-kind and reads as suppression. USAS puts
    #: `strangle` in "Life and living things [-]" and `scream` in "Speech acts",
    #: which is a field CHANGE rather than a category violation.
    by_field = collections.defaultdict(
        lambda: {"same": [], "diff": [], "none": [], "n": 0})
    by_field_c = collections.defaultdict(
        lambda: {"same": [], "diff": [], "none": [], "n": 0})
    _usas = {}

    def usas_of(w, coarse=False):
        """Fine USAS codes, or their top-level letter.

        THE GRAIN IS THE CONTROL. USAS has 232 base codes against `kind`'s six,
        so "different field" at fine grain may be nothing but resolution. The
        top-level letter (~21 domains) is comparable in coarseness to the harm
        taxonomy, and running both says whether a cross-field result is a fact
        about the move or about the ruler.
        """
        if w not in _usas:
            try:
                _usas[w] = frozenset(fields.usas(w, names=False) or ())
            except Exception:
                _usas[w] = frozenset()
        f = _usas[w]
        return frozenset(c[0] for c in f if c) if coarse else f

    def saturation(prompt, kd):
        """share of a prompt's rated words carried by its top non-NONE kind."""
        if len(kd) < 5:
            return None
        cc = collections.Counter(kd.values())
        charged = [v for k, v in cc.items() if k != "NONE"]
        return (max(charged) / sum(cc.values())) if charged else 0.0

    # per lineage: collect (same_kind_delta, none_kind_delta) pairs per cell
    by_lin = collections.defaultdict(lambda: {
        "same_deltas": [], "diff_deltas": [], "none_deltas": [],
        "same_scenes": [], "diff_scenes": [], "none_scenes": [],
        "n_cells": 0,
    })

    for b, a in sorted(eps.items()):
        lin = b + ">" + a
        #: lift is keyed by (prompt, BASE) and exists only for the 50 endpoint
        #: bases, English only. A prompt with no lift is dropped from the
        #: stratified table and kept in the headline one.
        lift_here = {q: float(v)
                     for (q, _bb), v in charge.lifts_per_lineage(b).items()}
        rows = ch.query(
            "SELECT prompt, word, p_base, p_aligned, "
            "(p_aligned - p_base) AS delta, cls "
            "FROM {db}.movement_v4 "
            "WHERE base='%s' AND aligned='%s' "
            "AND frame_base = '' AND %s"
            % (b.replace("'", "\\'"), a.replace("'", "\\'"),
               "frame_aligned = ''" if frame == "raw" else
               ("frame_aligned = 'prefill' AND system_mode_aligned = '%s'"
                % mode_of[(b, a)])),
            limit_bytes=None)

        cells = collections.defaultdict(list)
        for r in rows:
            cells[r["prompt"]].append(r)

        for prompt, word_rows in cells.items():
            sc, kd = get_ratings(prompt)
            if not sc or not kd:
                continue

            fallers = [(r["word"], float(r["delta"]), float(r["p_base"]))
                       for r in word_rows if r["cls"] == "faller"
                       and r["word"] in kd]
            if not fallers:
                continue
            top_faller = max(fallers, key=lambda x: -x[1])
            faller_kind = kd.get(top_faller[0])
            if not faller_kind or faller_kind == "NONE":
                continue

            risers = [(r["word"], float(r["delta"]))
                      for r in word_rows if r["cls"] == "riser"
                      and r["word"] in kd]
            if not risers:
                continue

            same, diff, none = [], [], []
            same_sc, diff_sc, none_sc = [], [], []
            for w, d in risers:
                k = kd.get(w, "NONE")
                s = sc.get(w, 0)
                if k == faller_kind:
                    same.append(d)
                    same_sc.append(s)
                elif k == "NONE":
                    none.append(d)
                    none_sc.append(s)
                else:
                    diff.append(d)
                    diff_sc.append(s)

            if same and none:
                rec = by_lin[lin]
                rec["same_deltas"].append(sum(same) / len(same))
                rec["none_deltas"].append(sum(none) / len(none))
                rec["same_scenes"].append(sum(same_sc) / len(same_sc))
                rec["none_scenes"].append(sum(none_sc) / len(none_sc))
                rec["n_cells"] += 1

                #: field groups for the SAME cell, so the two tests share a
                #: population and any difference between them is the instrument
                #: rather than the selection.
                for coarse, store in ((False, by_field), (True, by_field_c)):
                    ff = usas_of(top_faller[0], coarse)
                    if not ff:
                        continue
                    fsame, fdiff, fnone = [], [], []
                    for w, d in risers:
                        rf = usas_of(w, coarse)
                        if not rf:
                            fnone.append(d)
                        elif rf & ff:
                            fsame.append(d)
                        else:
                            fdiff.append(d)
                    if fsame and fdiff:
                        fr = store[lin]
                        fr["same"].append(sum(fsame) / len(fsame))
                        fr["diff"].append(sum(fdiff) / len(fdiff))
                        fr["none"].append(sum(fnone) / len(fnone) if fnone else None)
                        fr["n"] += 1

                sat = saturation(prompt, kd)
                lf = lift_here.get(prompt)
                if sat is not None and lf is not None:
                    sb = "lo" if sat < 0.33 else ("mid" if sat < 0.66 else "hi")
                    lb = "L-lo" if lf < 0.5 else ("L-mid" if lf < 1.2 else "L-hi")
                    st_rec = by_strat[(lin, sb, lb)]
                    st_rec["same"].append(sum(same) / len(same))
                    st_rec["none"].append(sum(none) / len(none))
                    st_rec["n"] += 1

                if diff:
                    rec["diff_deltas"].append(sum(diff) / len(diff))
                    rec["diff_scenes"].append(sum(diff_sc) / len(diff_sc))

    # --- sign test: same-kind vs none-kind mean delta ---
    print("  cells with rated top-faller (non-NONE) + both same-kind and")
    print("  none-kind risers: %d across %d lineages"
          % (sum(r["n_cells"] for r in by_lin.values()), len(by_lin)))
    print()

    # same vs none: does same-kind gain more?
    same_wins = 0
    none_wins = 0
    per_arm = {}
    for lin, rec in sorted(by_lin.items()):
        if rec["n_cells"] < 10:
            continue
        med_same = st.median(rec["same_deltas"])
        med_none = st.median(rec["none_deltas"])
        if med_same > med_none:
            same_wins += 1
        elif med_none > med_same:
            none_wins += 1
        if self_arm:
            k = self_arm.get(lin.split(">")[0], "?")
            w = per_arm.setdefault(k, [0, 0])
            if med_same > med_none:
                w[0] += 1
            elif med_none > med_same:
                w[1] += 1

    n = same_wins + none_wins
    p = binom(min(same_wins, none_wins), n)
    print("  SAME-KIND vs NONE-KIND risers (median delta per lineage)")
    print("  %-45s %d" % ("lineages where same-kind risers gain MORE:", same_wins))
    print("  %-45s %d" % ("lineages where none-kind risers gain MORE:", none_wins))
    print("  %-45s %.6f" % ("sign test p:", p))
    print()
    print("  CONDITIONAL FIELD TEST (USAS). Given the top faller's own field,")
    print("  where does the freed mass land? Cells need a field-carrying top")
    print("  faller AND both a same-field and a diff-field riser.")
    print()
    print("  %-46s %s" % ("comparison", "lineages   up/dn        p"))
    for grain, store in (("FINE (232 codes)", by_field),
                         ("COARSE (21 top-level domains)", by_field_c)):
      print("  -- %s" % grain)
      for lab, a, b in (("same-field vs DIFF-field", "same", "diff"),
                        ("same-field vs NO-field", "same", "none")):
        up = dn = 0
        for lin, r2 in sorted(store.items()):
            if r2["n"] < 10:
                continue
            xs = [(x, y) for x, y in zip(r2[a], r2[b])
                  if x is not None and y is not None]
            if len(xs) < 10:
                continue
            ma, mb = st.median([x for x, _ in xs]), st.median([y for _, y in xs])
            if ma > mb:
                up += 1
            elif mb > ma:
                dn += 1
        t = up + dn
        print("     %-43s %5d  %6s  %9.6f"
              % (lab, t, "%d/%d" % (up, dn), binom(min(up, dn), t)))
      print("     cells: %d across %d lineages"
            % (sum(r["n"] for r in store.values()), len(store)))
    print()

    print("  SATURATION x LIFT. saturation = share of the prompt's rated words")
    print("  in its top non-NONE kind; lift = charge.lift for that base.")
    print("  Same per-cell means and per-lineage medians as the headline.")
    print()
    print("  %-5s %-6s %9s %8s %10s %10s %8s %9s"
          % ("sat", "lift", "lineages", "cells", "same med", "none med",
             "up/dn", "p"))
    for sb in ("lo", "mid", "hi"):
        for lb in ("L-lo", "L-mid", "L-hi"):
            up = dn = 0
            nc = 0
            sm, nm = [], []
            for (l2, s2, b2), r2 in by_strat.items():
                if (s2, b2) != (sb, lb) or r2["n"] < 10:
                    continue
                nc += r2["n"]
                ms, mn = st.median(r2["same"]), st.median(r2["none"])
                sm.append(ms)
                nm.append(mn)
                if ms > mn:
                    up += 1
                elif mn > ms:
                    dn += 1
            t = up + dn
            if t < 8:
                print("  %-5s %-6s %9d %8d   (too few lineages to sign-test)"
                      % (sb, lb, t, nc))
                continue
            print("  %-5s %-6s %9d %8d %10.5f %10.5f %8s %9.5f"
                  % (sb, lb, t, nc, st.median(sm), st.median(nm),
                     "%d/%d" % (up, dn), binom(min(up, dn), t)))
        print()

    #: NEVER POOLED. The pooled row above mixes 45 aligned models with 8 base
    #: ones, and the base arm exists precisely to say whether the effect needs
    #: aligned weights. Pooled it cannot: a strong aligned signal carries a null
    #: base one to significance.
    if per_arm:
        print("  BY ARM -- reported separately, NEVER pooled")
        for want in ("aligned", "base"):
            w = per_arm.get(want)
            if not w:
                continue
            print("    %-8s n=%-3d %2d same / %2d none   p=%.6f%s"
                  % (want, w[0] + w[1], w[0], w[1], binom(min(w), sum(w)),
                     "   <- direction only, n=8 ceiling" if want == "base" else ""))
        print()

    if same_wins > none_wins:
        print("  DISPLACEMENT: freed mass preferentially lands on same-kind words.")
        print("  The charge redirects within the semantic domain.")
    elif none_wins > same_wins:
        print("  SUPPRESSION: freed mass preferentially lands on NONE words.")
        print("  The charge is extinguished, not redirected.")
    else:
        print("  NULL: no preference between same-kind and none-kind risers.")

    # --- scene ratings of the three groups ---
    print()
    print("  --- mean scene ratings of the three riser groups ---")
    all_same_sc = [s for r in by_lin.values() for s in r["same_scenes"]]
    all_diff_sc = [s for r in by_lin.values() for s in r["diff_scenes"]]
    all_none_sc = [s for r in by_lin.values() for s in r["none_scenes"]]
    if all_same_sc:
        print("  same-kind risers:  scene %.3f  (n=%d cells)"
              % (st.median(all_same_sc), len(all_same_sc)))
    if all_diff_sc:
        print("  diff-kind risers:  scene %.3f  (n=%d cells)"
              % (st.median(all_diff_sc), len(all_diff_sc)))
    if all_none_sc:
        print("  none-kind risers:  scene %.3f  (n=%d cells)"
              % (st.median(all_none_sc), len(all_none_sc)))

    # --- same vs none: delta magnitudes ---
    print()
    print("  --- median delta (mass gained) by riser group ---")
    all_same_d = [d for r in by_lin.values() for d in r["same_deltas"]]
    all_diff_d = [d for r in by_lin.values() for d in r["diff_deltas"]]
    all_none_d = [d for r in by_lin.values() for d in r["none_deltas"]]
    if all_same_d:
        print("  same-kind risers:  delta %+.6f  (n=%d)" % (st.median(all_same_d), len(all_same_d)))
    if all_diff_d:
        print("  diff-kind risers:  delta %+.6f  (n=%d)" % (st.median(all_diff_d), len(all_diff_d)))
    if all_none_d:
        print("  none-kind risers:  delta %+.6f  (n=%d)" % (st.median(all_none_d), len(all_none_d)))

    return 0



# ---------------------------------------------------------------------------
# THE FLOW TEST: is there a CHANNEL, or only two marginals?
# ---------------------------------------------------------------------------

def usas_signed(word, grain="fine", _cache={}):
    """Signed USAS codes for a word, portmanteaux split. -> set

    THE POLE IS THE POINT AND IT IS WHAT GETS DROPPED. `E3` is
    "Calm/Violent/Angry", so `E3-` is the violent end and `E3+` the calm one:
    strip the sign and `kill` and `soothe` land in one field, which is exactly
    the move this test is trying to detect. `fields.usas(names=False)` keeps the
    sign; `fields._nest` does NOT, so it is not used here.

    A tag can be a PORTMANTEAU of two (`Q2.2/X3.2++` for `shout`) and must be
    split or it resolves to nothing. `grain="letter"` keeps the top letter WITH
    its pole (`L1-` -> `L-`, `Q2.2` -> `Q`), which is the coarse control:
    `adjacency.py`'s own argument is that a cross-field result at fine grain may
    be resolution rather than movement, so both grains are run.
    """
    key = (word, grain)
    if key in _cache:
        return _cache[key]
    from malignment import fields
    out = set()
    try:
        raw = fields.usas(word, names=False) or ()
    except Exception:
        raw = ()
    for tag in raw:
        for part in str(tag).split("/"):
            part = part.strip()
            if not part:
                continue
            if grain == "letter":
                m = __import__("re").match(r"^([A-Z])[0-9.]*([+-]*)", part)
                if m:
                    out.add(m.group(1) + (m.group(2)[:1] if m.group(2) else ""))
            else:
                out.add(part)
    _cache[key] = out
    return out


SENSES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "results", "usas_sense.jsonl")

#: Contraction remnants and stray letters that reach the candidate set as
#: "words". They are a TOKENIZATION artifact, not vocabulary, and USAS codes
#: nine of them -- which is how they do damage rather than merely waste space:
#:
#:     re    -> S9 Religion, Z5        don   -> Z1m Personal names, P1, S2mf
#:     haven -> A15+ Safety, M7 Places won   -> S7.1+ Power
#:     m     -> N3.3, Q3, Z5           s     -> T1.3, Z5
#:
#: `re -> S9` and `don -> Z1m` are two of the junk channels in the fine table.
#:
#: **THE COST IS DECLARED, NOT HIDDEN.** `don`, `won`, `haven`, `ain` and `re`
#: are real English words (to don a coat, a haven, re: a memo). In THIS corpus
#: they arise from splitting "don't", "won't", "haven't"; the sense coder
#: abstained on `don` in 76 of 76 uses and on `haven` in 20 of 25, which is
#: behavioural evidence for the reading but not proof. Dropping them is a flag,
#: never a default, so any run that used it says so.
#:
#: **PROVISIONAL, 2026-09-16. A HAND-WRITTEN LIST IS THE WRONG INSTRUMENT AND
#: THIS IS A STOPGAP.** Three things are wrong with it and none is fixed here:
#:
#:   1. THE DEFECT IS UPSTREAM. These strings should not reach a candidate set
#:      as words at all. The repair belongs wherever the twp candidates are
#:      tokenized, not in a filter at the far end of the pipeline; filtering
#:      here leaves every other consumer of that vocabulary still exposed.
#:   2. THE LIST IS CLOSED AND THE CORPUS IS NOT. It covers the remnants
#:      OBSERVED in en. A new contraction, another language, or a different
#:      tokenizer produces remnants this frozenset has never heard of, and it
#:      will pass them through silently -- absence from the list is
#:      indistinguishable from "checked and kept".
#:   3. THE PRINCIPLED TEST IS UNAVAILABLE. Membership in a real-word list is
#:      what this wants, and `fields.py` records that `_byu()` was REMOVED: the
#:      BYU/COCA table lived under a Dropbox path, "is not on this machine",
#:      and was not reproducible from a clone. SUBTLEX is a frequency table,
#:      not a lexicon, and `fields.freq`'s own rule is that absent is not rare
#:      -- so it cannot answer "is this a word".
#:
#: Until one of those is addressed, a run using --drop-fragments is reporting a
#: population defined partly by this list, and the list should be read with the
#: results rather than trusted behind them.
FRAGMENTS = frozenset("""
s t m d ll ve re o y al
don didn doesn isn wasn weren won couldn wouldn shouldn ain aren hasn haven hadn mustn needn
""".split())


def _senses(path=SENSES, model="deepseek/deepseek-flash", want_empty=False, _c={}):
    """{(prompt, word): [fine codes]} from the sense annotation, or {}.

    Built by `usas_sense.py`: one deepseek-flash call per prompt, glossing each
    ambiguous candidate in context and returning the codes from that word's own
    USAS list that match the gloss. 2,389 prompts, 50,670 words, 88.7% resolved.

    **FILTERED TO ONE MODEL.** The file also holds rows from a two-prompt smoke
    on gemini-3.5-flash-lite, which is a different instrument; pooling coders
    would make a disagreement between them unattributable. Every row carries
    its own `model`, so the filter is a lookup rather than a reconstruction.

    An ABSENT key and an EMPTY list mean different things and are kept
    different: absent is "never ambiguous, USAS gave one code"; empty is "the
    coder read it and none of the offered senses fits", which downstream falls
    back to the full undisambiguated set. Neither is ever treated as "no
    senses", which would silently delete the word's mass.
    """
    key = (path, model, want_empty)
    if key in _c:
        return _c[key]
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if model and r.get("model") != model:
                    continue
                pr = r["prompt"]
                for w, v in (r.get("senses") or {}).items():
                    if v.get("codes"):
                        out[(pr, w)] = list(v["codes"])
                    elif want_empty:
                        out[(pr, w)] = []
    _c[key] = out
    return out


def _to_grain(codes, grain):
    """Fine codes down to the requested grain, pole kept. -> set"""
    if grain != "letter":
        return set(codes)
    out = set()
    for c in codes:
        m = re.match(r"^([A-Z])[0-9.]*([+-]*)", c)
        if m:
            out.add(m.group(1) + (m.group(2)[:1] if m.group(2) else ""))
    return out


def senses_of(word, grain, prompt=None, use_senses=False, abstain="fallback",
              drop_fragments=False):
    """The word's fields, disambiguated IN THIS PROMPT when we know them.

    Three outcomes and they are deliberately not the same:

      * the annotation names codes -> use exactly those
      * the annotation is ABSENT -> `usas_signed`, every sense, even division.
        USAS gave one code, or the coder never saw this pair.
      * the annotation is EMPTY -> the coder read the word and said none of the
        offered senses fits. `abstain="fallback"` then uses all of them anyway,
        which is today's behaviour and preserves every recorded number.
        `abstain="drop"` returns nothing, so the word's mass counts as UNCODED
        rather than being divided across senses the coder has just rejected.

    **`abstain="drop"` is the defensible one and it is still not the default.**
    Falling back does the single thing now known to be wrong: `don` abstained in
    76 of 76 uses and still donates a third of itself to `Z1m Personal names`.
    But it changes a recorded population, so it is asked for rather than
    assumed.
    """
    if drop_fragments and word.lower() in FRAGMENTS:
        return set()
    if use_senses and prompt is not None:
        rec = _senses(want_empty=True).get((prompt, word))
        if rec:
            return _to_grain(rec, grain)
        if rec == [] and abstain == "drop":
            return set()
    return usas_signed(word, grain)


def _spread(items, grain, prompt=None, use_senses=False, abstain="fallback",
            drop_fragments=False):
    """{field: mass} for [(word, mass)], a word's mass split over its codes.

    With `use_senses`, the codes are the ones the sense coder chose for this
    word IN THIS PROMPT, so a five-sense word stops donating a fifth of its
    movement to four domains it does not mean here. Words the coder never saw,
    or abstained on, spread exactly as before.

    A word with three codes contributes a third to each rather than a whole to
    each, so the table's total is the mass that moved and not a multiple of it.
    Returns (by_field, coded_mass, uncoded_mass) -- the uncoded share is a
    denominator and is reported, never silently dropped.
    """
    by, coded, uncoded = collections.defaultdict(float), 0.0, 0.0
    for w, m in items:
        fs = senses_of(w, grain, prompt, use_senses, abstain, drop_fragments)
        if not fs:
            uncoded += m
            continue
        coded += m
        share = m / len(fs)
        for f in fs:
            by[f] += share
    return by, coded, uncoded


def label(code, _c={}):
    """`E3-` -> "Calm/Violent/Angry [-]". -> str

    The tagset is keyed on the BASE code, so the modifier is stripped for the
    lookup and then written back, because the pole is content: `E3-` is the
    violent end and `E3+` the calm one, and a table that printed both as
    "Calm/Violent/Angry" would be unreadable in exactly the place it matters.
    """
    if code in _c:
        return _c[code]
    import re as _re
    from malignment import fields
    m = _re.match(r"^([A-Z][0-9.]*)(.*)$", code)
    base, mod = (m.group(1), m.group(2)) if m else (code, "")
    nm = fields._usas_names().get(base) or fields._usas_names().get(code) or ""
    _c[code] = ("%s [%s]" % (nm, mod)) if mod and nm else (nm or code)
    return _c[code]


def flow(frame="raw", grain="fine", drop_generic=False, top=18, perm=24, seed=7,
         sources=None, csv_out=None, examples=None, max_freq=None,
         min_prompts=5, pref_p=0.001, pref_min_prompts=25, use_senses=False,
         abstain="fallback", drop_fragments=False, pos_keep=None,
         channels=(("L1-", "Q2.2"), ("E3-", "Q2.2"), ("L1-", "Q2.1"))):
    """Does loss in one field CO-OCCUR with gain in another, above independence?

    ## WHAT THIS ANSWERS THAT A MARGINAL CANNOT

    `norm_change` establishes both marginals robustly on 50 lineages: under dose
    the violent fields FALL and speech acts RISE. Those two facts are consistent
    with three different worlds and a marginal cannot separate them --

        transfer      the mass that left `kill` arrived at `scream`, same cell
        co-movement   violence falls for one reason and speech rises for
                      another, in the same cells, nothing passing between
        composition   high-dose cells merely happen to be cells where speech
                      words were available

    Only the first is displacement, and it is the paper's claim.

    ## THE NULL IS THE OBJECTION

    Per cell, take the mass lost per field and the mass gained per field and
    accumulate their outer product, weighted by the mass that moved.

    The null has to contain "what alignment does to any distribution", so that
    `violence falls` and `speech rises` cannot themselves produce excess and the
    standing objection -- that these operations appear on flat control frames --
    is absorbed rather than argued with.

    ## AND THE MARGINAL PRODUCT IS NOT THAT NULL. THE FIRST RUN PROVED IT.

    Comparing against the product of the lineage's ACROSS-CELL marginals returns
    a diagonal: W->W at 32x, F->F at 16x, H->H at 10x, on 48 of 49 lineages.
    That is not evidence of same-field substitution. A cell's candidate words are
    constrained by its slot, so loss and gain within one cell are drawn from the
    same narrow field mix, and an across-cell marginal knows nothing about it.
    The diagonal is inflated by the cell's own vocabulary and the off-diagonals
    are deflated by the same mechanism, because the mass has to come from
    somewhere -- so `L- -> Q` at 0.77 was no more readable than `W -> W` at 32.

    **The null is a WITHIN-CELL permutation** (`--perm N`): hold each cell's moved
    words and the multiset of their masses fixed, shuffle which of them fell and
    which rose, rebuild the table. That destroys exactly one thing, the pairing
    between DIRECTION and FIELD, and preserves the cell's vocabulary, its field
    composition, its size and the lineage's marginals. Excess over it is the
    association displacement predicts and nothing else is.

    The marginal-product ratio is still printed beside it (`exp_m`) because the
    gap between the two IS the size of the confound, and hiding it would make the
    permutation look like a choice rather than a correction.

    ## `max_freq` DEFINES A DIFFERENT POPULATION; IT IS NOT A CORRECTION

    Ranked by how many lineages agree, the destinations are `take` (49), `make`
    (48), `be` (47), `go`, `do`, `have`, and `the` at 46. Most freed violent mass
    drains into the model's most frequent continuations, which is bleaching
    rather than a chain, and it swamps the reading. `max_freq` drops any word
    above F occurrences per million in SUBTLEX (`fields.freq`), so

        the 29449   be 5747   take 1891   make 1388      dropped at F=500
        understand 482   scream 26   gently 9   strangle 4.4   handcuff 1.0

    **Absent from SUBTLEX is not the same as rare** (`fields.freq`'s own
    docstring), so unlisted words are KEPT, never dropped as if frequency zero.

    The filter is applied to the permutation pool as well, so the null is built
    on the same population and stays internally valid. What it does NOT do is
    correct the unfiltered table: it answers a different question. Unfiltered
    asks where the mass goes and answers `take`; filtered asks where the
    non-generic mass goes. Both are real and a claim has to say which.

    It is also what makes the FULL source table affordable: dropping the frequent
    words shrinks the per-cell code sets that made `grain="fine"` intractable, so
    `sources` can be left unset.

    ## EXEMPLARS, AND THEIR SAMPLING RULE

    A channel is a pair of USAS codes and nobody can check it by reading, so
    `--examples` writes the words. The rule is declared because an illustration
    has a sampling design and this campaign has twice published one sorted by
    effect size:

      * per cell, the ONE faller carrying the most lost mass in the source field
        and the THREE risers carrying the most gained mass in the target field.
        That is the movement the cell actually made, not the movement that best
        fits the claim.
      * ranked by HOW MANY LINEAGES produced the same (faller, riser) pair, never
        by magnitude. A pair 30 models agree on leads; one model's large
        idiosyncratic jump does not. Same convention as `pooled_words`.
      * the prompt is carried with the pair, because a word pair out of its
        frame is unreadable -- `kill -> strangle` means one thing after "so
        furious he wanted to" and another after "pulled the pistol and".

    Capping at one faller and three risers per cell is also what makes it fit in
    memory: every faller x every riser at fine grain is ~20M keys.

    ## `sources` EXISTS BECAUSE THE FULL TABLE IS INTRACTABLE AT FINE GRAIN

    The joint is a per-cell outer product, so it costs |L| x |G| per cell per
    permutation. At `grain="letter"` a cell carries ~8 fields a side and the whole
    run is minutes. At `grain="fine"` there are 232 signed codes, a cell can carry
    30 a side, and 900 x 16 x 115,729 does not finish: the first attempt ran 84
    minutes and emitted nothing. Passing `sources` accumulates the joint only for
    those rows -- `O(|G|)` per cell -- while the row and column MARGINALS are
    still summed over everything, which is all `spec` needs from the rest of the
    table. The restriction changes no number it reports; it removes rows nobody
    asked about.

    ## AND obs/exp STILL CARRIES A ROW EFFECT, SO IT IS NOT THE HEADLINE

    The permutation destroys the pairing between direction and field, so a field
    whose words really do fall more than chance has a larger observed row total
    than a permuted one, and EVERY destination from it inflates together. That is
    visible in the first permuted run: `L-` leads into Q at 2.46 and into A at
    2.23, E at 2.32, X at 2.32, T+ at 2.20. A channel cannot be called specific
    on a number that rises for all of its siblings.

    **SPECIFICITY is the conditional profile, double-normalised** (`spec`):

        spec(fl->fg) =  [ P_obs(fg | fl) / P_obs(fg) ]
                        -------------------------------
                        [ P_null(fg | fl) / P_null(fg) ]

    P(fg | fl) sums to one over destinations, so the row effect cancels; dividing
    by P(fg) cancels the column effect, which is `speech rises` and is already
    established marginally; and dividing the observed lift by the permuted one
    cancels the cell-vocabulary confound. What survives all three is the only
    thing displacement predicts: given that a violent word fell HERE, speech is
    over-represented among what rose, beyond what this cell was ever going to do.

    spec > 1 on a majority of lineages is the result. The registered kill
    condition, recorded before the first run: if `L- -> Q` does not beat `L- -> A`
    and `L- -> Z`, the destination is "anywhere permitted" and speech only looks
    special because it is frequent.

    ## IT IS ASSOCIATION, NOT TRANSFER, AND THE WORD MATTERS

    Nothing traces a unit of probability from one word to another. Per cell we
    see a vector of losses and a vector of gains, so what is measured is
    co-occurrence within a cell. That rules out co-movement and composition,
    which is what the question needs, and it does NOT establish that a
    particular word's mass went to a particular other word. Write it up as
    association.

    ## A CHANNEL ALSO NEEDS PROMPTS, NOT ONLY LINEAGES (`min_prompts`)

    The sign test is over lineages, which is right for a channel averaged across
    many scenes and WRONG for one carried by a single scene. `H2 -> L1-` came
    back at spec 6.09 on 36 of 43 lineages, the largest effect in 51,041
    channels, and every contributing cell was the same prompt: "The funeral was
    over and he stood alone at the", where the base says `door` and the aligned
    says `graveside`. Forty-three models agreeing about one scene is one
    observation replicated forty-three times.

    Rare -- 1 of 281 strict channels -- but a defect that MAXIMISES effect size
    appears at rank 1 every time, so it cannot be left to be noticed. `n_prompts`
    is now counted exactly per channel and `min_prompts` gates on it. For scale,
    `L1- -> Q2.2` spans 276+ prompts and 196 distinct word pairs.

    UNIT OF INFERENCE IS THE LINEAGE, as everywhere in this folder: the ratio is
    computed per lineage against that lineage's own marginals, then a sign test
    over lineages. Models differ in what they reach for before any prompt
    arrives, so a pooled table would let one lineage's habits set the null for
    the rest.
    """
    import random, re
    from malignment import ch, charge, roster
    rng = random.Random(seed)

    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages: %s" % sorted(unresolved)[:3])
    mode_of = {}
    if frame != "raw":
        from malignment import movement as M
        mode_of = {(b, a): m for b, a, m in M.clean_frame_pairs()
                   if eps.get(b) == a}
        eps = {b: a for b, a in eps.items() if (b, a) in mode_of}

    #: Z is grammar and names, A is general/abstract; they carry 27,797 and
    #: 21,104 cells in this corpus's census and will dominate any table by size
    #: alone. Dropping them is a VARIANT, never the default -- if the freed mass
    #: goes to grammar, that is the finding and hiding it would manufacture the
    #: other one.
    GENERIC = ("Z", "A")

    want_src = set(sources) if sources else None
    _fq = {}
    _pm = {}

    def _warm_pos(prompt, words):
        """Tag this prompt's unseen words, once per process. -> None

        `pos.get_pos` is stashed on (tagger, prompt, word), so a warm store
        costs no spaCy call -- but 115,000 cells x ~74 words is 8.5M stash
        lookups even warm, so the answers are held in-process as well. The
        stash survives the run; this dict survives the loop.
        """
        miss = [w for w in words if (prompt, w) not in _pm]
        if not miss:
            return
        from malignment import pos as _P
        try:
            got = _P.get_pos(sorted(set(miss)), prompt, lang="en")
        except Exception:
            got = {}
        for w in set(miss):
            _pm[(prompt, w)] = got.get(w)

    def keep(word, prompt=None):
        """False for words above the frequency cut or outside `pos_keep`.

        **THE POS TEST IS CONTEXTUAL AND THE FREQUENCY TEST IS NOT**, which is
        why this takes a prompt. `gently` is ADV after "he hit her" and the
        same string is ADV everywhere, but `still`, `back`, `down` and `paced`
        are not, and a type-level tag would decide them once for the whole
        corpus. `pos.get_pos` tags the word AT THE END OF THIS PROMPT, which is
        the position the candidate actually occupies.

        An untagged word is DROPPED under `pos_keep`, not kept: unlike
        frequency, where absence from SUBTLEX means unknown rather than rare, a
        missing tag here means the tagger was not run or failed, and admitting
        it would let exactly the words the filter exists to exclude through the
        one gap nobody looks at.
        """
        if max_freq is not None:
            if word not in _fq:
                from malignment import fields as _F
                try:
                    _fq[word] = _F.freq(word)
                except Exception:
                    _fq[word] = None
            f = _fq[word]
            if not (f is None or f <= max_freq):
                return False
        if pos_keep:
            return _pm.get((prompt, word)) in pos_keep
        return True
    #: (fl, fg, faller, riser) -> [n_lineages, n_cells, {prompt: 1}]
    exemplars = collections.defaultdict(lambda: [0, 0, {}])
    seen_lin = collections.defaultdict(set)
    #: (fl, fg) -> {prompt}. EXACT, not the exemplar table's capped sample.
    chan_prompts = collections.defaultdict(set)
    print("FLOW: does loss in a field co-occur with gain in another, above the")
    print("      product of that lineage's own marginals?")
    print("      %d lineages  [frame=%s, grain=%s%s%s%s]"
          % (len(eps), frame, grain, ", generic dropped" if drop_generic else "",
             (", sources=%s" % ",".join(sorted(want_src))) if want_src else "",
             (", max_freq=%g/M" % max_freq) if max_freq else ""))
    print()

    per_lin, cov = {}, []
    for b, a in sorted(eps.items()):
        #: ORDER BY IS NOT COSMETIC HERE. Without it ClickHouse returns rows in
        #: whatever order it likes, `pool` is built in that order, and
        #: `rng.shuffle` draws a different permutation set every run -- the seed
        #: controls nothing. Caught by a regression check that should have
        #: reproduced and did not: spec(L-,Q) came back 1.16 then 1.13 on
        #: identical code, which is the same size as the margin the test was
        #: being asked to resolve.
        rows = ch.query(
            "SELECT prompt, word, (p_aligned - p_base) AS delta, cls "
            "FROM {db}.movement_v4 "
            "WHERE base='%s' AND aligned='%s' AND frame_base = '' AND %s"
            % (b.replace("'", "\\'"), a.replace("'", "\\'"),
               "frame_aligned = ''" if frame == "raw" else
               ("frame_aligned = 'prefill' AND system_mode_aligned = '%s'"
                % mode_of[(b, a)])) + " ORDER BY prompt, word",
            limit_bytes=None)
        cells = collections.defaultdict(list)
        for r in rows:
            cells[r["prompt"]].append(r)

        joint = collections.defaultdict(float)
        null = collections.defaultdict(float)
        rowm_all = collections.defaultdict(float)
        colm_all = collections.defaultdict(float)
        nrow_all = collections.defaultdict(float)
        ncol_all = collections.defaultdict(float)
        tot_all, ntot_all = [0.0], [0.0]
        cell_n, coded_t, uncoded_t = 0, 0.0, 0.0
        for prompt, wr in cells.items():
            if pos_keep:
                _warm_pos(prompt, {r["word"] for r in wr})
            lost = [(r["word"], -float(r["delta"])) for r in wr
                    if r["cls"] == "faller" and float(r["delta"]) < 0
                    and keep(r["word"], prompt)]
            gained = [(r["word"], float(r["delta"])) for r in wr
                      if r["cls"] == "riser" and float(r["delta"]) > 0
                      and keep(r["word"], prompt)]
            if not lost or not gained:
                continue
            L, cL, uL = _spread(lost, grain, prompt, use_senses, abstain, drop_fragments)
            G, cG, uG = _spread(gained, grain, prompt, use_senses, abstain, drop_fragments)
            coded_t += cL + cG
            uncoded_t += uL + uG
            if drop_generic:
                L = {k: v for k, v in L.items() if k[0] not in GENERIC}
                G = {k: v for k, v in G.items() if k[0] not in GENERIC}
            sL, sG = sum(L.values()), sum(G.values())
            if sL <= 0 or sG <= 0:
                continue
            cell_n += 1
            #: WEIGHTED OUTER PRODUCT. Each cell contributes its own loss and
            #: gain PROFILES (normalised) scaled by the mass that actually
            #: moved, so a cell where a lot moved counts for more and a cell
            #: with one tiny riser cannot set the table's shape.
            w = min(sL, sG)
            #: marginals over EVERYTHING; the joint only for rows under test.
            for fl, ml in L.items():
                rowm_all[fl] += w * (ml / sL)
            for fg, mg in G.items():
                colm_all[fg] += w * (mg / sG)
            tot_all[0] += w
            for fl, ml in L.items():
                if want_src is not None and fl not in want_src:
                    continue
                for fg, mg in G.items():
                    joint[(fl, fg)] += w * (ml / sL) * (mg / sG)
                    chan_prompts[(fl, fg)].add(prompt)

            if examples:
                #: TOP faller in the source field, TOP THREE risers in each
                #: target field -- the cell's own movement, capped so the key
                #: space stays finite. See the docstring for why not all pairs.
                lin_id = b + ">" + a
                src_w = collections.defaultdict(list)
                for wd, m in lost:
                    for f in senses_of(wd, grain, prompt, use_senses, abstain, drop_fragments):
                        if want_src is None or f in want_src:
                            src_w[f].append((m, wd))
                tgt_w = collections.defaultdict(list)
                for wd, m in gained:
                    for f in senses_of(wd, grain, prompt, use_senses, abstain, drop_fragments):
                        tgt_w[f].append((m, wd))
                for fl, fw in src_w.items():
                    top_f = max(fw)[1]
                    for fg, gw in tgt_w.items():
                        for _m, top_r in sorted(gw, reverse=True)[:3]:
                            k = (fl, fg, top_f, top_r)
                            e = exemplars[k]
                            e[1] += 1
                            if lin_id not in seen_lin[k]:
                                seen_lin[k].add(lin_id)
                                e[0] += 1
                            if len(e[2]) < 3:
                                e[2][prompt] = 1

            #: THE WITHIN-CELL NULL. Same words, same masses, same field mix --
            #: only which of them FELL is shuffled. Built from this cell's own
            #: pool so the cell's vocabulary cannot generate excess.
            pool = [(wd, m) for wd, m in lost] + [(wd, m) for wd, m in gained]
            nlost = len(lost)
            for _ in range(perm):
                rng.shuffle(pool)
                pL, _c, _u = _spread(pool[:nlost], grain, prompt, use_senses, abstain, drop_fragments)
                pG, _c, _u = _spread(pool[nlost:], grain, prompt, use_senses, abstain, drop_fragments)
                if drop_generic:
                    pL = {k: v for k, v in pL.items() if k[0] not in GENERIC}
                    pG = {k: v for k, v in pG.items() if k[0] not in GENERIC}
                psL, psG = sum(pL.values()), sum(pG.values())
                if psL <= 0 or psG <= 0:
                    continue
                pw = min(psL, psG) / perm
                for fl, ml in pL.items():
                    nrow_all[fl] += pw * (ml / psL)
                for fg, mg in pG.items():
                    ncol_all[fg] += pw * (mg / psG)
                ntot_all[0] += pw
                for fl, ml in pL.items():
                    if want_src is not None and fl not in want_src:
                        continue
                    for fg, mg in pG.items():
                        null[(fl, fg)] += pw * (ml / psL) * (mg / psG)
        if not joint:
            continue
        per_lin[b + ">" + a] = {"joint": joint, "null": null,
                                "row": rowm_all, "col": colm_all,
                                "tot": tot_all[0] or 1.0,
                                "nrow": nrow_all, "ncol": ncol_all,
                                "ntot": ntot_all[0] or 1.0,
                                "cells": cell_n}
        cov.append((coded_t, uncoded_t))

    ct, ut = sum(c for c, _ in cov), sum(u for _, u in cov)
    print("  %d lineages with a table; %d cells; USAS-coded mass %.1f%%"
          % (len(per_lin), sum(v["cells"] for v in per_lin.values()),
             100.0 * ct / (ct + ut) if ct + ut else float("nan")))

    def ratio(lin, fl, fg, how="perm"):
        """observed / expected. `perm` is the within-cell null, `marg` the
        across-cell marginal product that the first run showed to be confounded.
        NEITHER is the headline -- both carry the row effect. See `spec`."""
        d = per_lin[lin]
        if how == "marg":
            exp = d["row"].get(fl, 0.0) * d["col"].get(fg, 0.0) / d["tot"]
        else:
            exp = d["null"].get((fl, fg), 0.0) * (d["tot"] / d["ntot"])
        if exp <= 0:
            return None
        return d["joint"].get((fl, fg), 0.0) / exp

    def _lift(tab, rowm, colm, tot, fl, fg):
        """P(fg|fl) / P(fg). Row/col come from the FULL marginals, which are
        summed over every field even when the joint is restricted.

        THE ROW IS A LOOKUP, NOT A SCAN. It was written as
        `sum(v for (l,_g),v in tab.items() if l == fl)`, which is a full pass
        over the joint per channel per lineage: invisible at 400 channels and
        51k x 50 x 51k operations at fine grain with every source, where it ran
        52 minutes past the end of the data loop without emitting a row. The
        joint's row sum is identically `rowm[fl]` -- summing the outer product
        over fg gives back `w * ml/sL`, which is exactly what `rowm` accumulates
        -- so the scan was recomputing a number already held.
        """
        row = rowm.get(fl, 0.0)
        col = colm.get(fg, 0.0)
        if row <= 0 or col <= 0 or tot <= 0:
            return None
        return (tab.get((fl, fg), 0.0) / row) / (col / tot)

    def spec(lin, fl, fg):
        """Observed conditional lift over the permuted one. THE HEADLINE."""
        d = per_lin[lin]
        a = _lift(d["joint"], d["row"], d["col"], d["tot"], fl, fg)
        b = _lift(d["null"], d["nrow"], d["ncol"], d["ntot"], fl, fg)
        if a is None or b is None or b <= 0:
            return None
        return a / b

    #: RANK EVERY CHANNEL by how many lineages put it above independence, so the
    #: named channels are read against the field rather than quoted alone.
    allch = set()
    for d in per_lin.values():
        allch |= set(d["joint"])
    scored, thin = [], 0
    for (fl, fg) in allch:
        rs = [r for r in (spec(l, fl, fg) for l in per_lin) if r is not None]
        if len(rs) < 25:
            continue
        #: A channel on too few SCENES is a fact about those scenes. See the
        #: docstring: this is what put `door -> graveside` at the top of the table.
        if len(chan_prompts[(fl, fg)]) < min_prompts:
            thin += 1
            continue
        up = sum(1 for r in rs if r > 1.0)
        scored.append((up, len(rs), st.median(rs), fl, fg))
    if thin:
        print("  %d channels dropped for resting on fewer than %d distinct "
              "prompts" % (thin, min_prompts))
    #: SORTED BY EFFECT SIZE. The first version ranked on how many lineages beat
    #: 1.0, which is a consistency measure and buries a large effect that a few
    #: lineages miss under a tiny one they all share.
    scored.sort(key=lambda t: -t[2])

    print("\n  TOP CHANNELS by SPECIFICITY (conditional lift, observed over")
    print("  permuted). o/e is the same channel before the row effect is removed.")
    print("  %-8s %-8s %10s %9s %10s %8s %8s"
          % ("loses", "gains", "up/n", "spec", "p", "o/e", "marg"))
    for up, n, med, fl, fg in scored[:top]:
        rs = [r for r in (ratio(l, fl, fg) for l in per_lin) if r is not None]
        ms = [r for r in (ratio(l, fl, fg, "marg") for l in per_lin) if r is not None]
        print("  %-8s %-8s %10s %9.2f %10.4f %8s %8s"
              % (fl, fg, "%d/%d" % (up, n), med, binom(up, n),
                 "%.2f" % st.median(rs) if rs else "-",
                 "%.2f" % st.median(ms) if ms else "-"))

    print("\n  NAMED CHANNELS (registered before the run)")
    print("  %-8s %-8s %10s %9s %10s %8s %8s"
          % ("loses", "gains", "up/n", "spec", "p", "o/e", "rank"))
    order = {(fl, fg): i + 1 for i, (_, _, _, fl, fg) in enumerate(scored)}
    for fl, fg in channels:
        if grain == "letter":
            fl, fg = fl[0] + (fl[-1] if fl[-1] in "+-" else ""), fg[0]
        rs = [r for r in (spec(l, fl, fg) for l in per_lin) if r is not None]
        if not rs:
            print("  %-8s %-8s  not present at this grain" % (fl, fg))
            continue
        up = sum(1 for r in rs if r > 1.0)
        oe = [r for r in (ratio(l, fl, fg) for l in per_lin) if r is not None]
        print("  %-8s %-8s %10s %9.2f %10.4f %8s %8s"
              % (fl, fg, "%d/%d" % (up, len(rs)), st.median(rs), binom(up, len(rs)),
                 "%.2f" % st.median(oe) if oe else "-",
                 order.get((fl, fg), "-")))

    #: ── CONVERGENCE: how many destinations does a source actually prefer? ──
    #:
    #: ADDED 2026-09-14 BECAUSE THE NUMBER WAS CITED AND NOT EMITTED. Part 4 of
    #: README.md and scene_or_group.py's docstring both carried "the median
    #: source has two preferred destinations out of 306" attributed to this
    #: producer. It printed no such thing at any flag setting; it was computed
    #: ad hoc over the CSV. @malign reproduced --flow blind, could neither
    #: reproduce nor dispute it, and correctly refused to derive a lookalike
    #: (docket [6651]) on the grounds that the threshold for "preferred" would
    #: be their choice rather than a recovery. So the threshold is a FLAG and
    #: the block prints under it.
    print("\n  CONVERGENCE at p<%g, spec>1, >=%d prompts -- is the preferred set"
          % (pref_p, pref_min_prompts))
    print("  narrow and origin-specific, or shared? The AVOIDED side is the same")
    print("  question asked of what does not happen.")
    pref, avoid = [], []
    for (fl, fg) in allch:
        rs = [r for r in (spec(l, fl, fg) for l in per_lin) if r is not None]
        if len(rs) < 25 or len(chan_prompts[(fl, fg)]) < pref_min_prompts:
            continue
        up = sum(1 for r in rs if r > 1.0)
        if binom(up, len(rs)) >= pref_p:
            continue
        (pref if st.median(rs) > 1 else avoid).append((fl, fg))
    print("  %-12s %9s %9s %9s %13s %13s"
          % ("", "channels", "targets", "sources", "targets/src", "srcs/target"))
    for lab, ch in (("PREFERRED", pref), ("AVOIDED", avoid)):
        if not ch:
            print("  %-12s none at this threshold" % lab)
            continue
        bysrc = collections.Counter(a for a, _ in ch)
        bytgt = collections.Counter(b for _, b in ch)
        print("  %-12s %9d %9d %9d %13.1f %13.1f"
              % (lab, len(ch), len(bytgt), len(bysrc),
                 st.median(bysrc.values()), st.median(bytgt.values())))
    if avoid:
        bytgt = collections.Counter(b for _, b in avoid)
        print("  most-avoided targets, by how many DIFFERENT sources avoid them:")
        for t, n in bytgt.most_common(5):
            print("     %-10s %-36s %d sources" % (t, label(t)[:36], n))

    #: THE REGISTERED KILL CONDITION, recorded before the first run: a
    #: violent->speech channel must beat the GENERIC destinations, not merely
    #: beat the null.
    #:
    #: PAIRED, BECAUSE TWO INDEPENDENT MEDIANS CANNOT RESOLVE IT. The first
    #: version compared median spec(L-,Q) against median spec(L-,A) and reported
    #: 1.16 against 1.13 as a pass. A regression run of identical code returned
    #: 1.13 against the same rival: the margin was the same size as the
    #: permutation noise. Within one lineage both channels are built from the
    #: SAME permutation draw and share most of that noise, so the difference is
    #: paired per lineage and sign-tested, which is the comparison the question
    #: actually asks and the one the noise cancels out of.
    src = "L-" if grain == "letter" else "L1-"
    dst = "Q" if grain == "letter" else "Q2.2"
    print("\n  THE REGISTERED COMPARISON: does %s -> %s beat %s -> generic?" % (src, dst, src))
    print("  %-8s %-8s %10s %9s %10s" % ("loses", "gains", "up/n", "spec", "p"))
    rivals = [dst] + [g for g in sorted({g for (l, g) in allch if l == src})
                      if g[0] in GENERIC]
    for fg in rivals:
        rs = [r for r in (spec(l, src, fg) for l in per_lin) if r is not None]
        if not rs:
            continue
        up = sum(1 for r in rs if r > 1.0)
        tag = "  <- registered" if fg == dst else ""
        print("  %-8s %-8s %10s %9.2f %10.4f%s"
              % (src, fg, "%d/%d" % (up, len(rs)), st.median(rs),
                 binom(up, len(rs)), tag))

    print("\n  PAIRED WITHIN LINEAGE -- spec(%s->%s) minus spec(%s->rival), same"
          % (src, dst, src))
    print("  permutation draw, sign test over lineages. THIS is the registered test.")
    print("  %-18s %10s %11s %10s" % ("rival", "wins/n", "med diff", "p"))
    for fg in rivals[1:]:
        d = []
        for l in per_lin:
            x, y = spec(l, src, dst), spec(l, src, fg)
            if x is not None and y is not None:
                d.append(x - y)
        if len(d) < 25:
            continue
        wins = sum(1 for v in d if v > 0)
        print("  %-18s %10s %+11.3f %10.4f"
              % ("%s -> %s" % (src, fg), "%d/%d" % (wins, len(d)),
                 st.median(d), binom(wins, len(d))))
    print("\n  Of the top %d channels, %d involve Z (grammar/names) or A "
          "(general/abstract)." % (min(top, len(scored)),
                                   sum(1 for c in scored[:top]
                                       if c[3][0] in GENERIC or c[4][0] in GENERIC)))

    if csv_out:
        #: THE MAP, not the tournament. `flow` was first written to adjudicate one
        #: registered channel and kept scoring every other destination as a rival
        #: that had to lose. The question is descriptive -- where does freed mass
        #: go -- so the artifact is a ranked table of destinations with their
        #: labels, and nothing in it has to beat anything.
        import csv as _csv
        path = csv_out if os.path.isabs(csv_out) else os.path.join(HERE, csv_out)
        with open(path, "w", newline="") as fh:
            w = _csv.writer(fh)
            w.writerow(("source", "source_label", "target", "target_label",
                        "up", "n", "n_prompts", "spec", "obs_over_exp", "p",
                        "grain", "perm"))
            for up, n, med, fl, fg in scored:
                oe = [r for r in (ratio(l, fl, fg) for l in per_lin) if r is not None]
                w.writerow((fl, label(fl), fg, label(fg), up, n,
                            len(chan_prompts[(fl, fg)]),
                            "%.4f" % med,
                            "%.4f" % st.median(oe) if oe else "",
                            "%.6g" % binom(up, n), grain, perm))
        print("\n-> %s  (%d channels, sorted by specificity)" % (path, len(scored)))

    if examples:
        import csv as _csv
        path = examples if os.path.isabs(examples) else os.path.join(HERE, examples)
        rank = {(fl, fg): (up, n, med) for up, n, med, fl, fg in scored}
        rows_out = []
        for (fl, fg, wf, wr), (nlin, ncell, prompts) in exemplars.items():
            if (fl, fg) not in rank or nlin < 3:
                continue
            up, n, med = rank[(fl, fg)]
            rows_out.append((med, nlin, fl, fg, wf, wr, ncell, prompts, up, n))
        #: channel by specificity, then WITHIN a channel by lineage consensus.
        rows_out.sort(key=lambda r: (-r[0], -r[1]))
        with open(path, "w", newline="") as fh:
            w = _csv.writer(fh)
            w.writerow(("source", "source_label", "target", "target_label",
                        "channel_spec", "channel_up", "channel_n",
                        "faller", "riser", "n_lineages", "n_cells", "prompts"))
            for med, nlin, fl, fg, wf, wr, ncell, prompts, up, n in rows_out:
                w.writerow((fl, label(fl), fg, label(fg), "%.4f" % med, up, n,
                            wf, wr, nlin, ncell, " | ".join(list(prompts)[:3])))
        print("-> %s  (%d word pairs on %d channels, >=3 lineages each)"
              % (path, len(rows_out), len({(r[2], r[3]) for r in rows_out})))
    return 0


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frame", default="raw", choices=("raw", "prefill", "self"))
    ap.add_argument("--match-framed", action="store_true",
                    help="run RAW on the framed population, so the two are the "
                         "same pairs and a difference is not partly which labs "
                         "ship a chat template")
    ap.add_argument("--flow", action="store_true",
                    help="the CHANNEL test: loss-field x gain-field within a "
                         "cell against the product of that lineage's marginals")
    ap.add_argument("--grain", default="fine", choices=("fine", "letter"),
                    help="signed USAS code, or its top letter with the pole kept")
    ap.add_argument("--drop-generic", action="store_true",
                    help="exclude Z (grammar/names) and A (general/abstract). A "
                         "VARIANT, never the default: if the mass goes to "
                         "grammar that is the finding")
    ap.add_argument("--top", type=int, default=18)
    ap.add_argument("--pref-p", type=float, default=0.001,
                    help="significance cut defining a PREFERRED or AVOIDED "
                         "channel in the convergence block. A choice, so it is "
                         "a flag and it prints in the header.")
    ap.add_argument("--pref-min-prompts", type=int, default=25,
                    help="distinct prompts a channel needs to enter the "
                         "convergence block")
    ap.add_argument("--min-prompts", type=int, default=5,
                    help="a channel must span this many distinct prompts. A "
                         "channel on one scene is a fact about that scene, "
                         "however many lineages replicate it.")
    ap.add_argument("--max-freq", type=float, default=None,
                    help="drop words above this SUBTLEX frequency per million. "
                         "A DIFFERENT POPULATION, not a correction: unfiltered "
                         "asks where the mass goes and answers `take`.")
    ap.add_argument("--examples", default=None,
                    help="write the WORDS behind each channel to this CSV: top "
                         "faller and top three risers per cell, ranked by how "
                         "many lineages agree, with their prompts")
    ap.add_argument("--csv", default=None,
                    help="write every channel to this CSV with USAS labels, "
                         "sorted by specificity descending")
    ap.add_argument("--senses", action="store_true",
                    help="use the per-prompt USAS sense annotation from "
                         "results/usas_sense.jsonl instead of dividing a "
                         "word's mass evenly over all its senses. OFF by "
                         "default so every recorded number stays reproducible; "
                         "ON is a DIFFERENT POPULATION and must be said.")
    ap.add_argument("--pos", default=None,
                    help="keep only candidates whose CONTEXTUAL spaCy tag at "
                         "the end of the prompt is one of these, comma "
                         "separated, e.g. VERB. Aimed at the adverb-deferral "
                         "artifact (`hit -> gently`, `stabbed -> carefully`), "
                         "where a manner ADVERB replaces a violent VERB and "
                         "the verb arrives outside the measured slot. An "
                         "UNTAGGED word is dropped, not kept.")
    ap.add_argument("--abstain", default="fallback", choices=("fallback", "drop"),
                    help="what an EMPTY sense annotation means. fallback keeps "
                         "today's behaviour (use every sense anyway); drop "
                         "counts the word as uncoded, which is what the coder "
                         "actually said. Only meaningful with --senses.")
    ap.add_argument("--drop-fragments", action="store_true",
                    help="exclude contraction remnants (s, t, don, didn, "
                         "haven...) that reach the candidate set through "
                         "tokenization. See FRAGMENTS: nine of them are USAS-"
                         "coded, and `re` files under Religion.")
    ap.add_argument("--source", action="append", default=None,
                    help="restrict the JOINT to these loss fields (marginals "
                         "still cover everything). Required in practice at "
                         "--grain fine; see flow().")
    ap.add_argument("--perm", type=int, default=24,
                    help="within-cell permutations building the null. The "
                         "across-cell marginal product is confounded by the "
                         "cell's own field composition; see flow().")
    a = ap.parse_args(argv)
    if a.flow:
        return flow(frame=a.frame, grain=a.grain, perm=a.perm,
                    sources=a.source, drop_generic=a.drop_generic, top=a.top,
                    csv_out=a.csv, examples=a.examples, max_freq=a.max_freq,
                    min_prompts=a.min_prompts, pref_p=a.pref_p,
                    pref_min_prompts=a.pref_min_prompts,
                    use_senses=a.senses, abstain=a.abstain,
                    drop_fragments=a.drop_fragments,
                    pos_keep=tuple(x.strip().upper() for x in a.pos.split(","))
                             if a.pos else None)
    return measure(frame=a.frame, match_framed=a.match_framed)


if __name__ == "__main__":
    sys.exit(main())
