"""What to rate next: (prompt, word) pairs in priority order, with their evidence.

    python -u priority.py                      # full manifest
    python -u priority.py --min-lineages 5
    python -u priority.py --out ~/malignment-data/contextual_norms

Writes `priority.csv.gz`, one row per unrated (prompt, word) pair that carries
enough movement to be worth a rating, ordered by tier then by how many lineages
it moves on.

## WHY A PRIORITY LIST AND NOT A COVERAGE TARGET

Full English coverage is ~480,000 unrated pairs, about 22x the 22,124 that exist.
That is the wrong target twice over. Most of the tail moves on ONE lineage and
carries a single noisy label, so a rating spent there buys an outcome that cannot
be estimated. And the matched-population run in `experiments/displacement/
named_under_dose/` already settled the headline the ratings were wanted for:
the same twelve v6 scales asked AT THE SITE reach +0.086 where word-level ratings
of the same scales reach +0.0006, on identical cells. More of the same ratings
would re-establish a resolved result.

**What is NOT resolved is the dose conditioning, and the reason is a coverage bias
in the instrument itself.** On matched cells the low-dose stratum holds 28,224
shared cells and the high-dose stratum 10,468: the 276 rated prompts skew toward
neutral frames, so the instrument is best powered exactly where the question is
least interesting. Every model's draw range overlaps between strata.

So the ordering below is by what each rating would RESOLVE, not by volume.

## THE TIERS

    1  CHINESE            zero contextual ratings exist: `slot_prompts()` returns
                          534 prompts and NONE contain CJK. Chinese word-level norms
                          are also the thin set (7 k_ratings, no Warriner, no
                          Brysbaert), so this is the one place where a rating buys a
                          measurement that currently cannot be made at all.

                          **CORRECTION.** An earlier version of this file said the
                          Chinese arm was BLOCKED because `SlotRatingENv6` is
                          "English-only by name and by content". That was inferred
                          from the class name and from the absence of CJK in
                          `slot_prompts()`, and never tested. It is FALSE. Smoke
                          test, 5 pairs through the unmodified task on
                          deepseek-v4-flash, 0 errors:

                            他反复刺那个人，直到他 + 死    harm 7 aggr 1 direct 7 mund 1
                            He stabbed the man ... + died  harm 7 aggr 1 direct 7 mund 1
                            要做...烩饭，你应该先 + 准备    harm 1 aggr 1 direct 1 mund 7
                            他反复刺那个人，直到他 + 停    harm 7 aggr 5 direct 7 mund 1

                          The instrument rates Chinese out of the box, discriminates
                          within it (死 vs 停 moves aggression 1->5), and the one
                          translation-matched pair agreed on all twelve scales.
                          `render()` is structurally language-agnostic and nothing in
                          the system prompt asserts English. **The name described the
                          corpus it had been run on, not a constraint.** Tier 1 is
                          rateable today with no new instrument.

                          NOT yet established: that ratings are COMPARABLE across
                          languages. There is no translation key in the data --
                          pair_id, kernel_id and archive_prompt_id all span zero
                          cross-language groups, and all 457 zh prompts sit in family
                          `flat` beside 811 unrelated en ones -- so a matched-prompt
                          study needs the correspondence reconstructed first. Exact
                          agreement is NOT the target; absence of systematic offset
                          is. Cheapest checks: a domain-level distributional
                          comparison (available now), and back-translation of ~100
                          pairs rated in both languages.

    2  HIGH TRANSGRESSIVE the stratum the dose question needs and the instrument
                          under-covers. Ranked by the base-arm k_transgressiveness
                          of the frame, measured BEFORE alignment, so selecting on
                          it cannot select on the outcome.

    3  GENERAL            everything else, for external validity: the existing 276
                          prompts were chosen to build an instrument for, not
                          sampled, so every contextual result so far is conditional
                          on them. This tier is what tests whether it generalises.

## THE LINEAGE FILTER IS THE POINT

A (prompt, word) pair that moves on one lineage gives one label; on twenty it gives
a stable direction and a within-pair variance. `--min-lineages` defaults to 5.
The distribution over the 50 endpoint pairs:

    >= 2 lineages   316,805 pairs        >= 10 lineages   122,113
    >= 5 lineages   188,389 pairs        >= 20 lineages    53,655

## RATABILITY COMES FROM CONTEXTUAL POS, NOT FROM THE BARE WORD

The first version of this list was topped, in every tier, by numerals and function
words -- `'年薪为$' + '60'`, `'looked' + 'out'`, `'wanted' + 'they'`, and `'大喊' +
'"'`. They rank highest because they are frequent AND consistent, which is exactly
the ranking signal, and a rating of `60` for harm or vocalisation buys nothing.

That version filtered on the BARE word via `fields.is_function_word`, which is the
unreliable path: spaCy on a bare word calls `strangle` a NOUN and `the` a PRON, and
it left `"` at the top of the Chinese tier because the word was UNKNOWN and unknowns
were kept.

**Now the filter is `pos_pass.py`'s contextual tagging** -- `pos.get_pos(words,
prompt)` over all 2,751,990 (prompt, word) pairs in `twp_words_v4`, which is the
SAME decision `named_under_dose --verbs-only` uses. One POS answer, not two, so the
manifest cannot commission ratings the analysis then drops.

**VERBS FIRST.** `--pos VERB` is the default: it is Findings P's population (its
100,958 cells were lexical verbs), it is what `named_under_dose` scores, and it is
half the corpus in both languages (50% en, 51% zh). `--pos content` widens to
NOUN/VERB/ADJ/ADV/PROPN for a more general instrument that is no longer
P-comparable. A pair with no tag is DROPPED, because after a full pass an untagged
pair means the pair is not in `twp_words_v4` at all.

## ALREADY-RATED PAIRS ARE EXCLUDED, AND ABSENCE IS CHECKED NOT ASSUMED

`contextual_norms` returns {} both for an unrated pair and for a prompt no
instrument ever saw. `slot_prompts()` is consulted first so a prompt outside the
instrument is not recorded as a rated prompt with zero rated words.
"""

import argparse, collections, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
OUT = os.path.expanduser("~/malignment-data/contextual_norms")
LEVELS = os.path.expanduser("~/malignment-data/norm_change/levels_long.csv.gz")
DOSE_SCALE = "k_transgressiveness"


def load_dose():
    """-> {prompt: (median base-arm dose, lang, n_lineages)}."""
    if not os.path.exists(LEVELS):
        sys.exit("no levels_long at %s -- run norm_change first" % LEVELS)
    acc = collections.defaultdict(list)
    lang = {}
    with gzip.open(LEVELS, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head) or v[ix["scale"]] != DOSE_SCALE:
                continue
            b = v[ix["base_level"]]
            if not b or b == "\\N":
                continue
            try:
                acc[v[ix["prompt"]]].append(float(b))
            except ValueError:
                continue
            lang[v[ix["prompt"]]] = v[ix["lang"]]
    import statistics as st
    return {p: (st.median(v), lang.get(p, "en"), len(v)) for p, v in acc.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-lineages", type=int, default=5,
                    help="a pair must MOVE on this many endpoint lineages")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--uniform", action="store_true",
                    help="ignore tiers: emit every unrated pair at >=--min-lineages, "
                         "so rating coverage is INDEPENDENT of dose. The tiered "
                         "manifest commissioned tier 2 at top-quartile dose, which "
                         "made coverage 21.8%% at low dose against 63.6%% at high, so "
                         "a low-vs-high contrast confounds dose with which prompts got "
                         "rated. Selecting on the variable you then condition on is "
                         "the same error as selecting on the outcome, one step "
                         "removed.")
    ap.add_argument("--pos", default="content",
                    help="'content' (default) = NOUN/VERB/ADJ/ADV/PROPN. 'VERB' is "
                         "P's population and is the RIGHT filter for the one table "
                         "that replicates P, and the WRONG one everywhere else: it "
                         "does not thin a noun-slot prompt, it DELETES it. 451 of "
                         "2,612 en prompts and 56 of 407 zh are under 20%% verbs -- "
                         "the salary probes in English, the sexual-domain frames in "
                         "Chinese -- and 111 already-rated en prompts fall in that "
                         "group. The POS-proxy problem that motivated verbs-only is "
                         "fixed by STRATIFYING on POS, not by discarding four fifths "
                         "of the tagset.")
    ap.add_argument("--top-quantile", type=float, default=0.75,
                    help="dose quantile above which an en prompt is tier 2")
    a = ap.parse_args(argv)

    from malignment import ch, roster, fields as F
    import numpy as np

    m = roster.endpoints()
    m = m[0] if isinstance(m, tuple) else m
    pairs = " OR ".join("(base='%s' AND aligned='%s')"
                        % (b.replace("'", "''"), al.replace("'", "''"))
                        for b, al in m.items())
    print("endpoint pairs: %d" % len(m))

    dose = load_dose()
    print("prompts with a base-arm dose: %d" % len(dose))

    #: ALREADY RATED. slot_prompts() first, so a prompt no instrument ever saw is
    #: not recorded as a rated prompt with zero rated words.
    rated_prompts = set(F.slot_prompts())
    rated = set()
    for p in rated_prompts:
        try:
            for w in F.contextual_norms(p):
                rated.add((p, w))
        except Exception:
            pass
    print("already rated: %d (prompt, word) pairs over %d prompts"
          % (len(rated), len(rated_prompts)))

    rows = ch.query(
        "SELECT prompt, word, count() AS n_lin, countIf(cls='riser') AS up, "
        "countIf(cls='faller') AS dn FROM movement WHERE (%s) AND cls != 'still' "
        "GROUP BY prompt, word HAVING n_lin >= %d" % (pairs, a.min_lineages))
    print("pairs moving on >=%d lineages: %d" % (a.min_lineages, len(rows)))

    en_dose = sorted(d for d, lg, _ in dose.values() if lg == "en")
    cut = float(np.quantile(en_dose, a.top_quantile)) if en_dose else 0.0
    print("tier-2 cut: en base-arm %s above the %.0fth percentile = %.4f"
          % (DOSE_SCALE, 100 * a.top_quantile, cut))

    #: CONTEXTUAL POS from pos_pass.py, keyed on (prompt, word). Loaded once.
    want = ({"NOUN", "VERB", "ADJ", "ADV", "PROPN"} if a.pos == "content"
            else {x.strip().upper() for x in a.pos.split(",")})
    TAG = {}
    import csv as _csv
    for lg in ("en", "zh"):
        f = os.path.join(os.path.expanduser(a.out), "pos_%s.csv.gz" % lg)
        if not os.path.exists(f):
            sys.exit("no %s -- run pos_pass.py first" % f)
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh, delimiter="\t"):
                TAG[(row["prompt"], row["word"])] = row["pos"]
    print("contextual POS loaded: %d (prompt, word) pairs | keeping %s"
          % (len(TAG), "/".join(sorted(want))))

    out = []
    skipped_nodose = drop_unratable = drop_untagged = 0
    for r in rows:
        p, w = r["prompt"], r["word"]
        if (p, w) in rated:
            continue
        d = dose.get(p)
        if d is None:
            skipped_nodose += 1
            continue
        dv, lg, nl = d
        t = TAG.get((p, w))
        if t is None:
            drop_untagged += 1
            continue
        if t not in want:
            drop_unratable += 1
            continue
        tier = 0 if a.uniform else (1 if lg == "zh" else (2 if dv >= cut else 3))
        n = int(r["n_lin"]); up = int(r["up"]); dn = int(r["dn"])
        out.append((tier, -n, p, w, lg, dv, n, up, dn))
    out.sort()
    print("skipped, no dose for the prompt: %d" % skipped_nodose)
    print("dropped, POS not in %s: %d | dropped, untagged: %d"
          % ("/".join(sorted(want)), drop_unratable, drop_untagged))

    os.makedirs(os.path.expanduser(a.out), exist_ok=True)
    path = os.path.join(os.path.expanduser(a.out), "priority.csv.gz")
    import csv
    with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t")
        #: HEADER AND ROW ARE BUILT FROM ONE LIST. They were edited separately
        #: once and drifted -- a 9-name header over 10-value rows, which csv
        #: reports as `int('VERB')` three columns later rather than as a header
        #: error. Same arity mismatch as the pos_zh table an hour earlier.
        COLS = ["tier", "lang", "prompt", "word", "pos", "n_lineages",
                "n_riser", "n_faller", "consistency", "prompt_dose"]
        wr.writerow(COLS)
        for tier, negn, p, w, lg, dv, n, up, dn in out:
            row = [tier, lg, p, w, TAG.get((p, w), ""), n, up, dn,
                   "%.3f" % (max(up, dn) / n), "%.4f" % dv]
            assert len(row) == len(COLS), "row/header arity: %d vs %d" % (
                len(row), len(COLS))
            wr.writerow(row)

    print("\n%-6s %-5s %10s %10s %12s" % ("tier", "lang", "pairs", "prompts", "words"))
    for t, name in ((0, "uniform"), (1, "zh"), (2, "en high-dose"), (3, "en general")):
        sub = [x for x in out if x[0] == t]
        if not sub:
            continue
        print("  %-4d %-5s %10d %10d %12d   %s"
              % (t, sub[0][4] if sub else "-", len(sub),
                 len({x[2] for x in sub}), len({x[3] for x in sub}), name))
    print("  %-4s %-5s %10d %10d %12d   TOTAL"
          % ("", "", len(out), len({x[2] for x in out}), len({x[3] for x in out})))
    print("\n-> %s" % path)
    print("Ordered by tier, then by lineage count descending. `consistency` is the")
    print("share of a pair's lineages agreeing on direction -- a pair at 0.5 moves")
    print("both ways and its rating buys less than the count suggests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
