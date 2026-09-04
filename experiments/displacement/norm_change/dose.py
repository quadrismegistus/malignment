"""Does TRANSGRESSIVE MASS IN THE BASE ARM predict what alignment changes?

    python -u dose.py                    # levels and fields, both languages
    python -u dose.py --lang en --top 25

## THE DESIGN, AND WHY IT DOES NOT SELECT ON THE OUTCOME

The predictor is the BASE arm's transgressive mass at a prompt, measured before
alignment touches anything. The outcome is how far some other scale moves,
`aligned - base`. A prompt heavy in transgressive mass could, from there, show a
rise, a fall or nothing on any given scale with equal ease -- the predictor
carries no information about the direction of the outcome, which is what makes
this a dose-response rather than a selection.

That distinction matters here because the alternative is exactly the trap this
campaign keeps booking: conditioning on words that MOVED, and then reporting
that moved words moved.

## WHY IT WAS ASKED FOR

The field table says speech mass FALLS under alignment. Restricted to movers,
speech words are net RISERS (+3272 mass, 418,323 riser rows against 379,653
faller rows) -- which is M01's kill->scream direction and the opposite reading.
Both are true and they are different quantities: a normalised SHARE of rated
mass can fall while absolute mass rises, if the denominator grows.

So the interesting question is not which way a field goes on average. It is
whether the frames carrying transgressive mass are the ones where a field like
speech moves at all. That is a slope, not a mean.

## THE STATISTIC

Per lineage, over its prompts:

    x  base-arm level of the DOSE scale (k_transgressiveness by default)
    y  aligned - base on the TARGET scale

an ordinary least-squares slope of y on x. Then the sign test over lineages,
the same unit every other test in this folder uses. A lineage needs MIN_PROMPTS
prompts with both x and y present, or it does not contribute -- a slope from
three points is not evidence and averaging it in as one would let the thinnest
lineages vote loudest.
"""

import argparse, collections, gzip, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
DATA = os.path.expanduser("~/malignment-data/norm_change")

MIN_PROMPTS = 25
DOSE_DEFAULT = "k_transgressiveness"



def endpoint_pairs():
    """The 50 base->endpoint lineages, as "base>aligned" strings.

    **THE MOVEMENT TABLE IS NOT A ROSTER.** It holds 153 edges over 85 base
    models -- RUNGS (base->SFT, SFT->DPO) and TRANSITIVE pairs as well as
    endpoints, because `produce_movement` builds both deliberately: a word can
    fall at SFT and rise at DPO, so base->DPO is not recoverable from the rungs.

    Counting those 153 as lineages is PSEUDO-REPLICATION. Llama-3.1-8B alone
    contributes 11 edges, so one pretrained model votes eleven times in a sign
    test whose unit is supposed to be the lineage. Every n=153 reported from
    this folder before 2026-08-24 has that defect (RH caught it).

    `roster.endpoints()` is the shared rule and exists precisely so this is not
    retyped per experiment -- its docstring records four shell heredocs that
    each filtered differently, one matching `"lmo" in base` and so finding 4 of
    6 OLMo lineages. It resolves 50, all present in `movement`, and applies the
    rulings: terminal under aligning ops only, no ablations, no attested
    `direction: inverted` de-aligning finetunes.
    """
    from malignment import roster
    ep, _unresolved = roster.endpoints()
    #: **MATCHED POPULATION.** The framed set covers 45 of these 50, so a raw
    #: result at n=50 set beside a framed one at n=45 differs partly by which
    #: labs ship a chat template. `--match-framed` restricts raw to the framed
    #: pairs; without it the two columns are not comparable, which is the same
    #: trap `existence` hit.
    if _MATCH["v"]:
        from malignment import movement as M
        keep = {(b, a) for b, a, _m in M.clean_frame_pairs() if ep.get(b) == a}
        ep = {b: a for b, a in ep.items() if (b, a) in keep}
    return {"%s>%s" % (b, a) for b, a in ep.items()}


def lift_dose_rows():
    """{(lang, lineage, prompt, "lift"): (dose, dose)} from charge.lift_per_lineage.

    The dose is T_base - frame for a specific (prompt, base) pair: how much
    more transgressive this model's candidates are than the setup alone. Per
    lacan [6565], this predicts displacement 3x better than the level (r=-0.261
    vs -0.091) because the level saturates above frame 5.

    ENGLISH ONLY: charge ratings cover 2,400 English prompts.
    """
    from malignment import charge, roster
    ep, _ = roster.endpoints()
    ep_set = {"%s>%s" % (b, a) for b, a in ep.items()}
    base_to_aligned = dict(ep)
    lpl = charge.lifts_per_lineage()
    out = {}
    for (pr, base), v in lpl.items():
        aligned = base_to_aligned.get(base)
        if aligned is None:
            continue
        lin = "%s>%s" % (base, aligned)
        if lin not in ep_set:
            continue
        out[("en", lin, pr, "lift")] = (v, v)
    print("lift dose: %d (lineage, prompt) cells" % len(out))
    return out


def v6_dose_rows(cut):
    """{(lang, lineage, prompt, "v6_harm_mass"): (dose, dose)} from EXISTING ratings.

    `v6_harm` asks how much harm the action causes IN THIS SCENE, so `punched` scores
    high in a slamming frame without a rater reaching for `strangled` -- which is the
    anchoring the per-model tagging pass was going to buy. It is already on 1,935
    prompts and costs nothing.

    KNOWN LIMIT, and it is the same one every completion-based dose has: where the
    transgression is in the SETUP the rating saturates. On `He raised the knife and
    stabbed him in the ___` every body part scores harm 7 -- chest, face, head, eye --
    because the stabbing has already happened, so the dose is 1.0000 and means only
    "this frame is violent".
    """
    import csv as _csv
    from malignment import fields as F
    rated = {}
    for pr in F.slot_prompts():
        try:
            d = F.contextual_norms(pr)
        except Exception:
            continue
        hot = {w for w, v in d.items()
               if isinstance(v.get("v6_harm"), (int, float)) and v["v6_harm"] >= cut}
        if hot:
            rated[pr] = hot
    print("v6 dose: %d prompts carry words at v6_harm >= %d" % (len(rated), cut))
    wl = os.path.join(DATA, "words_long%s.csv.gz" % _SFX["v"])
    if not os.path.exists(wl):
        return {}
    _csv.field_size_limit(sys.maxsize)
    tot = collections.Counter(); hit = collections.Counter()
    with gzip.open(wl, "rt", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh, delimiter="\t"):
            if r.get("lang") != "en":
                continue
            pr = r["prompt"]
            if pr not in rated:
                continue
            try:
                p = float(r["p_base"])
            except (TypeError, ValueError):
                continue
            k = (r["base"] + ">" + r["aligned"], pr)
            tot[k] += p
            if r["word"] in rated[pr]:
                hit[k] += p
    out = {}
    for k, t in tot.items():
        if t > 0:
            v = hit[k] / t
            out[("en", k[0], k[1], "v6_harm_mass")] = (v, v)
    print("v6 dose: %d (lineage, prompt) cells" % len(out))
    return out


def slot_dose_rows(lv):
    """{(lang, lineage, prompt, "slot_loaded_mass"): (dose, dose)} from tags.csv.gz.

    The dose is the BASE arm's mass on that prompt's loaded words, per lineage --
    so a frame carrying a loaded option that a given base model rarely offers is
    low-dose FOR THAT LINEAGE, which is the whole point of a per-(lineage, prompt)
    predictor. `read()` returns (base, aligned); both slots carry the same value
    here because a dose is a property of the base arm and nothing downstream reads
    the second.
    """
    import csv as _csv
    tagf = os.path.join(HERE, "..", "..", "instrument_calibrations",
                        "dose_response", "tags.csv.gz")
    if not os.path.exists(tagf):
        return {}
    loaded = collections.defaultdict(set)
    with gzip.open(tagf, "rt", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh, delimiter="\t"):
            loaded[r["prompt"]].add(r["word"])
    print("slot dose: %d prompts carry loaded words" % len(loaded))
    wl = os.path.join(DATA, "words_long%s.csv.gz" % _SFX["v"])
    if not os.path.exists(wl):
        print("no words_long -- cannot compute mass")
        return {}
    _csv.field_size_limit(sys.maxsize)
    tot = collections.Counter(); hit = collections.Counter()
    with gzip.open(wl, "rt", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh, delimiter="\t"):
            if r.get("lang") != "en":
                continue
            pr = r["prompt"]
            if pr not in loaded:
                continue
            try:
                p = float(r["p_base"])
            except (TypeError, ValueError):
                continue
            k = (r["base"] + ">" + r["aligned"], pr)
            tot[k] += p
            if r["word"] in loaded[pr]:
                hit[k] += p
    out = {}
    for k, t in tot.items():
        if t > 0:
            v = hit[k] / t
            out[("en", k[0], k[1], "slot_loaded_mass")] = (v, v)
    print("slot dose: %d (lineage, prompt) cells" % len(out))
    return out


def binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


#: **THE SAME TWO FLAGS AS run.py, AND THE SAME SUFFIX.** run.py writes
#: levels_long.csv.gz (v3), levels_long_v4.csv.gz and levels_long_v4_framed.csv.gz
#: side by side; this reader has to be told which set to open or it silently
#: analyses v3 while the caller believes it asked for framed.
_SFX = {"v": ""}
_MATCH = {"v": False}


def _suffix(rule_version, frame):
    if int(rule_version) == 3:
        if frame != "raw":
            raise SystemExit("--frame needs --rule-version 4")
        return ""
    return "_v4" if frame == "raw" else "_v4_framed"


def read(name, keep=None):
    """{(lang, lineage, prompt, scale): (base, aligned)}, streamed."""
    p = os.path.join(DATA, "%s_long%s.csv.gz" % (name, _SFX["v"]))
    if not os.path.exists(p):
        return None
    EP = endpoint_pairs()
    out = {}
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head):
                continue
            sc = v[ix["scale"]]
            if keep and sc not in keep:
                continue
            b, a = v[ix["base_level"]], v[ix["aligned_level"]]
            if not b or not a or b == "\\N" or a == "\\N":
                continue
            lin = v[ix["base"]] + ">" + v[ix["aligned"]]
            if lin not in EP:
                continue
            try:
                out[(v[ix["lang"]], lin, v[ix["prompt"]], sc)] = (float(b), float(a))
            except ValueError:
                continue
    return out


def slope(xs, ys):
    """OLS slope, or None when x has no variance."""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def index_by_scale(tbl, lang):
    """{scale: {(lineage, prompt): (base, aligned)}}, built ONCE.

    The first version rescanned the whole table for every target, which on the
    28M-row fields table is 232 full passes and does not finish. Indexing once
    turns the sweep from O(scales x rows) into O(rows + scales x prompts).
    """
    idx = collections.defaultdict(dict)
    for (lg, lin, pr, sc), v in tbl.items():
        if lg == lang:
            idx[sc][(lin, pr)] = v
    return idx


def dose_response(idx, dose_scale, target_scale):
    """{lineage: slope of (aligned-base on target) on (base level of dose)}."""
    by = collections.defaultdict(lambda: ([], []))
    doses = {k: v[0] for k, v in idx.get(dose_scale, {}).items()}
    for (lin, pr), (b, a) in idx.get(target_scale, {}).items():
        d = doses.get((lin, pr))
        if d is None:
            continue
        by[lin][0].append(d)
        by[lin][1].append(a - b)
    out = {}
    for lin, (xs, ys) in by.items():
        if len(xs) < MIN_PROMPTS:
            continue
        s = slope(xs, ys)
        if s is not None:
            out[lin] = s
    return out


def report(target, sl):
    import statistics as st
    v = list(sl.values())
    n = len(v)
    up = sum(1 for x in v if x > 0)
    dn = sum(1 for x in v if x < 0)
    if up + dn < 3:
        return None
    p = binom(up, up + dn)
    med = st.median(v)
    return (p, target, med, up, dn, n)


def magnitude(a, langs):
    """Does MORE MASS MOVE where the base arm is more transgressive?

    M01 asked this as a BINARY contrast and answered it: `F_G_rate_magnitude`
    finds the RATE null (n=33 pair-sites, p=0.148) and the MAGNITUDE confirmed
    (d=0.748, p=6e-5) -- "alignment does not displace more often at
    transgressive sites; it displaces HARDER". `Q_bridge` names the quantity:
    `departed` is "how much mass leaves words at all".

    This is the CONTINUOUS version, which had not been run. Three outcomes per
    (lineage, prompt), each regressed on the same base-arm transgressive level:

        departed   sum of p_base - p_aligned over fallers
        arrived    sum of p_aligned - p_base over risers
        n_movers   how many words moved at all -- M01's RATE, per prompt

    Reporting all three matters because they can separate: more words moving
    while less mass moves is a DISPERSAL, and a departed-only reading would
    call it a smaller effect rather than a differently-shaped one.
    """
    import gzip, statistics as st
    from malignment import ch
    EP = endpoint_pairs()
    print("MAGNITUDE DOSE: does more mass move where the base is transgressive?")
    print("unit = the lineage; slope across prompts; %d endpoint pairs" % len(EP))
    rows = ch.query(
        "SELECT base, aligned, prompt, "
        "sumIf(p_base - p_aligned, cls='faller') AS dep, "
        "sumIf(p_aligned - p_base, cls='riser') AS arr, count() AS nm "
        "FROM %s WHERE cls != 'still' GROUP BY base, aligned, prompt"
        % ("movement" if not _SFX["v"] else "nc_movement_src"))
    mag = {}
    for r in rows:
        lin = r["base"] + ">" + r["aligned"]
        if lin in EP:
            mag[(lin, r["prompt"])] = (float(r["dep"]), float(r["arr"]), int(r["nm"]))
    dose = {}
    with gzip.open(os.path.join(DATA, "levels_long%s.csv.gz" % _SFX["v"]), "rt",
                   encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head) or v[ix["scale"]] != DOSE:
                continue
            lin = v[ix["base"]] + ">" + v[ix["aligned"]]
            if lin not in EP:
                continue
            try:
                dose[(lin, v[ix["prompt"]], v[ix["lang"]])] = float(v[ix["base_level"]])
            except ValueError:
                pass
    print()
    print("  %-4s %-10s %4s %12s %8s %10s" % ("lang", "outcome", "n", "med slope", "up/dn", "p"))
    for lang in langs:
        for j, nm in ((0, "departed"), (1, "arrived"), (2, "n_movers")):
            by = collections.defaultdict(lambda: ([], []))
            for (lin, pr, lg), d in dose.items():
                if lg != lang:
                    continue
                m = mag.get((lin, pr))
                if not m:
                    continue
                by[lin][0].append(d)
                by[lin][1].append(float(m[j]))
            sl = {}
            for lin, (xs, ys) in by.items():
                if len(xs) < MIN_PROMPTS:
                    continue
                s2 = slope(xs, ys)
                if s2 is not None:
                    sl[lin] = s2
            r = report(nm, sl)
            if r:
                p_, _t, med, up, dn, n = r
                print("  %-4s %-10s %4d %+12.5f %4d/%-4d %10.6f%s"
                      % (lang, nm, n, med, up, dn, p_, "  <-" if p_ < 0.05 else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-version", type=int, default=3, choices=(3, 4),
                    help="which levels_long* set run.py wrote. 3 is the v3 "
                         "artifact, unchanged.")
    ap.add_argument("--frame", default="raw", choices=("raw", "prefill"),
                    help="prefill requires --rule-version 4")
    ap.add_argument("--match-framed", action="store_true",
                    help="restrict to the pairs the framed set covers, so raw "
                         "and prefill are the same population")
    ap.add_argument("--lang", default=None, choices=("en", "zh"))
    ap.add_argument("--dose", default=DOSE_DEFAULT)
    ap.add_argument("--v6-dose", action="store_true",
                    help="dose = base-arm mass on words whose CONTEXTUAL v6_harm is "
                         ">= --v6-cut, from ratings that already exist. The rating is "
                         "per (prompt, word) so it is prompt-level, but the MASS "
                         "WEIGHTING is per lineage -- models put different "
                         "probability on those words -- so the dose still varies by "
                         "lineage. Costs nothing: no new API calls.")
    ap.add_argument("--v6-cut", type=int, default=4)
    ap.add_argument("--lift-dose", action="store_true",
                    help="dose = per-lineage lift (T_base - frame) from "
                         "charge.lift_per_lineage(). This is the dose displacement "
                         "work wants (lacan [6565]): how much more transgressive "
                         "the candidate words are THAN THE SETUP ALONE, weighted "
                         "by this base arm's own mass distribution. Predicts "
                         "displacement 3x better than the level (r=-0.261 vs "
                         "-0.091). ENGLISH ONLY, 2,400 prompts.")
    ap.add_argument("--slot-dose", action="store_true",
                    help="use SLOT-LEVEL loaded mass instead of the global lexicon. "
                         "`k_transgressiveness` cannot know which completion is "
                         "loaded HERE: 63.4%% of prompts sit within 5%% of its floor "
                         "and it ranks quid-pro-quo coercion below knife attacks. "
                         "This reads instrument_calibrations/dose_response/"
                         "tags.csv.gz -- per-prompt loaded words, gradient-validated "
                         "against 255 hand-tagged prompts -- and computes the base "
                         "arm's mass on them, the same construct displacement_axis "
                         "uses. ENGLISH ONLY.")
    ap.add_argument("--table", default="both",
                    choices=("levels", "fields", "contextual", "both", "all"))
    ap.add_argument("--contextual", action="store_true",
                    help="run ALL THREE tables -- word norms, USAS fields, and the "
                         "contextual slot ratings -- on the SHARED PROMPT SET, i.e. "
                         "only prompts that carry contextual ratings. Without the "
                         "subset the comparison is word-level-on-everything against "
                         "contextual-on-the-rated-subset, which is a population "
                         "difference wearing a grain costume: the rated prompts were "
                         "chosen by whoever built the instrument and are not a "
                         "random sample of the corpus.")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", default=None,
                    help="write the FULL table (every target, not just --top) to "
                         "this dir. THE DOSE NAME IS IN THE FILENAME: a slot-dose "
                         "run must never overwrite a lexical-dose one, because the "
                         "lexical numbers are what README.md reports and a silently "
                         "replaced file is how a README comes to describe results "
                         "that no longer exist.")
    ap.add_argument("--magnitude", action="store_true",
                    help="does MORE MASS MOVE where the base is transgressive?")
    a = ap.parse_args(argv)
    _SFX["v"] = _suffix(a.rule_version, a.frame)
    _MATCH["v"] = bool(a.match_framed)
    if _SFX["v"]:
        print("reading *_long%s.csv.gz" % _SFX["v"])

    langs = [a.lang] if a.lang else ["en", "zh"]
    if a.magnitude:
        return magnitude(a, langs)
    if a.contextual or a.table == "all":
        tables = ["levels", "fields", "contextual"]
    elif a.table == "both":
        tables = ["levels", "fields"]
    else:
        tables = [a.table]

    print("DOSE-RESPONSE: does base-arm %s predict what alignment changes?" % a.dose)
    print("unit = the lineage; slope of (aligned-base) on base dose, across prompts")
    print("min %d prompts per lineage" % MIN_PROMPTS)

    lv = read("levels")
    if lv is None:
        print("no levels_long -- run.py --run first")
        return 1
    #: the dose ALWAYS comes from levels, even when the target is a field --
    #: transgressiveness is a continuous norm and has no field counterpart.
    if a.lift_dose:
        dose_rows = lift_dose_rows()
        a.dose = "lift"
        if not dose_rows:
            print("no lift dose -- is charge_en50_flash.jsonl present?")
            return 1
    elif a.v6_dose:
        dose_rows = v6_dose_rows(a.v6_cut)
        a.dose = "v6_harm_mass"
        if not dose_rows:
            print("no v6 dose -- are slot_ratings/results/v6 present?")
            return 1
    elif a.slot_dose:
        dose_rows = slot_dose_rows(lv)
        a.dose = "slot_loaded_mass"
        if not dose_rows:
            print("no slot dose -- run dose_response/run.py then consolidate.py")
            return 1
    else:
        dose_rows = {k: v for k, v in lv.items() if k[3] == a.dose}
        if not dose_rows:
            print("dose scale %r not present in levels_long" % a.dose)
            return 1

    #: THE SHARED PROMPT SET. Contextual ratings cover a subset of the corpus, so
    #: comparing a word-level slope computed on 2,245 prompts against a contextual
    #: slope computed on the rated ~1,800 compares two POPULATIONS, not two grains.
    #: Every table is restricted to the prompts the contextual table actually holds.
    keep_prompts = None
    if a.contextual or "contextual" in tables:
        cx = read("contextual")
        if cx is None:
            print("no contextual_long -- run.py --contextual first")
            return 1
        keep_prompts = {k[2] for k in cx}
        allp = {k[2] for k in lv}
        print("SHARED PROMPT SET: %d of %d prompts carry contextual ratings (%.0f%%)"
              % (len(keep_prompts & allp), len(allp),
                 100.0 * len(keep_prompts & allp) / max(1, len(allp))))
        lv = {k: v for k, v in lv.items() if k[2] in keep_prompts}
        dose_rows = {k: v for k, v in dose_rows.items() if k[2] in keep_prompts}

    for name in tables:
        #: with --slot-dose the dose does NOT live in levels_long, so it must be
        #: merged into EVERY table including levels -- otherwise levels tests
        #: against a dose scale that is not there and reports 0 targets.
        _ext = a.lift_dose or a.slot_dose or a.v6_dose
        tbl = dict(lv) if (name == "levels" and _ext) else (
            lv if name == "levels" else read(name))
        if name == "levels" and _ext:
            tbl.update(dose_rows)
        if tbl is None:
            print("no %s_long -- skipping" % name)
            continue
        if name != "levels":
            tbl = dict(tbl)
            if keep_prompts is not None:
                tbl = {k: v for k, v in tbl.items() if k[2] in keep_prompts}
            #: the dose ALWAYS comes from levels; fields and contextual have no
            #: transgressiveness counterpart of their own.
            tbl.update(dose_rows)
        for lang in langs:
            idx = index_by_scale(tbl, lang)
            scales = sorted(set(idx) - {a.dose})
            rows = []
            for sc in scales:
                sl = dose_response(idx, a.dose, sc)
                r = report(sc, sl)
                if r:
                    rows.append(r)
            rows.sort()
            print()
            print("=" * 78)
            print("%s / %s  --  %d targets tested, %d significant"
                  % (lang.upper(), name, len(rows), sum(1 for r in rows if r[0] < 0.05)))
            print("=" * 78)
            print("  %-34s %11s %5s %5s %5s %9s" % ("target", "med slope", "up", "dn", "n", "p"))
            for p, sc, med, up, dn, n in rows[:a.top]:
                mark = "  <-" if p < 0.05 else ""
                print("  %-34s %+11.5f %5d %5d %5d %9.5f%s"
                      % (sc[:34], med, up, dn, n, p, mark))
            if a.out:
                import csv as _c
                d_ = os.path.expanduser(a.out)
                os.makedirs(d_, exist_ok=True)
                #: **THE VARIANT IS IN THE FILENAME.** Without it, a framed run
                #: overwrites the raw run and both overwrite the v3 results the
                #: README cites -- done three times on 2026-09-04 before the
                #: pattern was fixed rather than the instance. `results/` is
                #: gitignored, so an overwrite here has no git copy to restore.
                fn = os.path.join(d_, "dose_%s%s__%s_%s.csv"
                                  % (a.dose, _SFX["v"], name, lang))
                with open(fn, "w", newline="") as _fh:
                    w_ = _c.writer(_fh)
                    w_.writerow(["dose", "table", "lang", "target", "med_slope",
                                 "up", "dn", "n", "p"])
                    for p_, sc_, med_, up_, dn_, n_ in rows:
                        w_.writerow([a.dose, name, lang, sc_, med_, up_, dn_, n_, p_])
                print("   -> %s  (%d targets, FULL table)" % (os.path.basename(fn), len(rows)))
    print()
    print("A POSITIVE slope means: the more transgressive mass the BASE arm put")
    print("at a prompt, the MORE that target rose under alignment. The dose is")
    print("measured before alignment and does not select on the outcome.")
    print()
    print("EXPLORATORY. Nothing here was registered; every row is a candidate")
    print("for a hypothesis, not a result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
