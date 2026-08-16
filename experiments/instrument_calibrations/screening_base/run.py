#!/usr/bin/env python
"""Which released checkpoint is representative of the roster's transgressive mass?

    python experiments/instrument_calibrations/screening_base/run.py
    python .../run.py --floor 1500        # a declared sensitivity arm, NOT a retune

THE PRODUCER FOR `registration.md`, WHICH IS FROZEN AND GOVERNS. Every threshold,
statistic and refusal below is copied from it rather than chosen here. If this
file and the registration disagree, the registration is right and this is a bug.

## WHAT IT WRITES

    results/by_model.csv     one row per model -- LONG FORM, so the summary can
                             be re-derived and disagreements surface
    results/sensitivity.csv  the winner under each declared coverage floor
    results/summary.json     the declared screener, or the refusal that fired
    population.json          the receipt: explicit ids, counts, sha, date

## THE ONE THING THIS FILE MUST NOT DO

**Choose.** The rule has no free parameter -- minimise `max(|pct - 50|)` across
mean, breadth and intensity -- precisely so that no judgement lives here. A
future edit that adds a weighting, a tie-break or a preferred family is a
specification search, and the registration's own history records that the first
draft of the rule was one: it gated on `|pct - 50| <= 8`, chosen after seeing the
ranking, admitting four models of which one was the author's preferred one.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

from malignment import ch, roster                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

#: FROM `registration.md`, NOT CHOSEN HERE.
LEXICON_SHA = "d542e7e2bb86bd00"
DECLARED_FLOOR = 2000
#: Refusal 2: the winner is re-derived at each of these and reported as
#: floor-dependent if it changes. NOT a search for a floor that gives a nicer
#: answer -- all three are reported whatever they say.
SENSITIVITY_FLOORS = (1500, 2000, 2180)
#: Refusal 1: no screener is declared if the winner is further than this from
#: median on ANY axis.
MAX_DEV_REFUSAL = 25.0

#: **`\p{Han}`, NOT `[\x{4e00}-\x{9fff}]`.** The exploratory pass used the
#: latter and ClickHouse matched it against 2,188 of 2,189 panel prompts where
#: the true count is 1 -- a fabricated confound that was caught only because the
#: number was implausible. `\p{Han}` agrees with Python's `[一-鿿]`.
HAN = r"\\p{Han}"


def _coverage():
    """{model: panel prompts measured}. The denominator, so absent counts as 0."""
    return {r["model"]: r["n"] for r in ch.query(
        """SELECT model, count(DISTINCT prompt) AS n FROM {db}.twp_words
           WHERE prompt IN (SELECT prompt FROM {db}.wf_panel) GROUP BY model""")}


def _labelled():
    """{model: (summed labelled mass, prompts carrying any)} over the panel.

    An INNER JOIN, so a model with no labelled mass anywhere is absent rather
    than zero -- handled by the caller, which reads coverage separately. The two
    cannot be one query: this one's row count is prompts WITH mass, and using it
    as a denominator is the error that made the first attempt return 0 models.
    """
    return {r["model"]: (r["s"], r["hit"]) for r in ch.query(
        """SELECT w.model AS model, sum(w.p) AS s, count(DISTINCT w.prompt) AS hit
           FROM {db}.twp_words AS w
           INNER JOIN {db}.wf_sexviolence AS f ON w.word = f.word
           WHERE w.prompt IN (SELECT prompt FROM {db}.wf_panel)
           GROUP BY w.model""")}


def _shares():
    """{model: (labelled share of mass, CJK share of mass)} -- the SCOPE REPORT.

    `wf_sexviolence` is English-only and blind on CJK by construction, and its
    own registration requires the unlabelled share to be reported downstream.
    This is that report, per candidate, and it is not optional.
    """
    return {r["model"]: (r["lab"], r["cjk"]) for r in ch.query(
        """SELECT w.model AS model,
                  sumIf(w.p, w.word IN (SELECT word FROM {db}.wf_sexviolence))
                    / sum(w.p) AS lab,
                  sumIf(w.p, match(w.word, '%s')) / sum(w.p) AS cjk
           FROM {db}.twp_words AS w
           WHERE w.prompt IN (SELECT prompt FROM {db}.wf_panel)
           GROUP BY w.model""" % HAN)}


def _rank(models, cov, lab):
    """[(model, mean, breadth, intensity, pcts..., max_dev)] under one floor.

    Percentile is the RANK percentile within this population, so the three
    statistics are commensurable. Raw values are kept in the row as well --
    a percentile with no value behind it cannot be checked.
    """
    pop = [m for m in models if cov.get(m, 0) >= 0]          # already filtered
    rows = []
    for m in pop:
        s, hit = lab.get(m, (0.0, 0))
        n = cov[m]
        rows.append({"model": m, "n_prompts": n,
                     "mean": s / n, "breadth": hit / n,
                     "intensity": (s / hit) if hit else 0.0})
    for key in ("mean", "breadth", "intensity"):
        order = sorted(rows, key=lambda r: r[key])
        for i, r in enumerate(order):
            r[key + "_pct"] = 100.0 * i / len(order)
    for r in rows:
        r["max_dev"] = max(abs(r[k + "_pct"] - 50.0)
                           for k in ("mean", "breadth", "intensity"))
    return rows


def _untreated():
    """Models with NO aligning op anywhere in their ancestry.

    **THE SCREENER MUST BE PRE-TREATMENT** (RH, 2026-08-16: *"arent we looking
    for BASE models as the candidate?"*). The first run did not restrict this and
    14 of its 32 candidates were aligned checkpoints -- `Tulu-3-8B-SFT`,
    `zephyr-7b-beta`, `OLMoE-1B-7B-0125-SFT`. Their transgressive mass is
    measured AFTER repression, so a median reading there means *this much
    survived*, where screening asks *this much is available to be repressed*.
    Those are different quantities and only one of them answers the question.

    **NOT `roster.population("bases")`, which means pretrained ROOTS.** That
    filter is too strict in a way that matters: `Falcon3-10B-Base` is `upscale`d
    from `Falcon3-7B-Base` and `Falcon3-3B-Base` is `prune`d from it, so neither
    is a root, and `Pharia-1-LLM-7B-control-hf` is a base whose pretrained
    ancestor was never released. All three are untouched by alignment and all
    three are legitimate screeners. `upscale` and `prune` are DERIVING but not
    ALIGNING -- they are pretrained-to-pretrained operations.

    So the test is on the OPS along the ancestry, not on being a root.
    """
    #: **THE DECLARATION BEATS THE GRAPH, AND MISSING IT WAS A BUG.**
    #: The first version inferred treatment from EDGES alone: walk the ancestry,
    #: look for an ALIGNING op. That misses a model whose aligned parent is not
    #: in the roster at all -- it has no incoming edge, so the walk finds nothing
    #: and calls it untreated.
    #:
    #: Three models are exactly that, and the roster says so in a field this
    #: function did not read: `pretrained: false`.
    #:
    #:     Aleph-Alpha/Pharia-1-LLM-7B-control-hf   `-control` IS the instruction
    #:                                              -tuned release, method sft
    #:     openGPT-X/Teuken-7B-instruct-commercial-v0.4
    #:     microsoft/phi-4
    #:
    #: They are the same three `RESULTS.md` names as the excluded roots --
    #: *"aligned models whose pretrained ancestor was never released"*. Two of
    #: them reached the candidate list before this check existed.
    #:
    #: **Inference from a graph cannot see a node the graph does not contain.**
    #: Where a declaration exists it is the evidence; the walk is for the models
    #: that have no flag, which is 157 of 160.
    doc = roster.load()
    parents = {}
    for p, op, c in (doc.get("edges") or []):
        parents.setdefault(c, []).append((p, op))
    out = set()
    for m, node in (doc.get("nodes") or {}).items():
        if node.get("pretrained") is False:
            continue
        seen, stack, treated = set(), [m], False
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            for p, op in parents.get(cur, []):
                if op in roster.ALIGNING:
                    treated = True
                    break
                stack.append(p)
            if treated:
                break
        if not treated:
            out.add(m)
    return out


def _population(floor, cov, untreated):
    """At or above the floor, UNTREATED, and no `@revision` checkpoints.

    The revision exclusion is declared: a screener must be a released model
    somebody can name and load, and `pythia-6.9b@step28000` is a point in a
    trajectory. Applied here rather than in the ranking so the counts are
    reportable.
    """
    return sorted(m for m, n in cov.items()
                  if n >= floor and "@" not in m and m in untreated)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--floor", type=int, default=DECLARED_FLOOR,
                    help="coverage floor; the declared value is %d. Other values "
                         "are the registration's sensitivity arms, not retunes."
                         % DECLARED_FLOOR)
    a = ap.parse_args()
    os.makedirs(RESULTS, exist_ok=True)

    cov, lab, sh = _coverage(), _labelled(), _shares()
    untreated = _untreated()
    n_any = len(cov)

    # -- the declared run --------------------------------------------------
    pop = _population(a.floor, cov, untreated)
    rows = _rank(pop, cov, lab)
    rows.sort(key=lambda r: r["max_dev"])
    for r in rows:
        l, c = sh.get(r["model"], (0.0, 0.0))
        r["labelled_share"], r["cjk_share"] = l, c

    import csv
    cols = ["model", "n_prompts", "mean", "breadth", "intensity",
            "mean_pct", "breadth_pct", "intensity_pct", "max_dev",
            "labelled_share", "cjk_share"]
    with open(os.path.join(RESULTS, "by_model.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in cols})

    # -- refusal 2: does the winner survive the other declared floors? ------
    winners = {}
    for f in SENSITIVITY_FLOORS:
        rs = _rank(_population(f, cov, untreated), cov, lab)
        rs.sort(key=lambda r: r["max_dev"])
        winners[f] = (rs[0]["model"], rs[0]["max_dev"], len(rs)) if rs else (None, None, 0)
    with open(os.path.join(RESULTS, "sensitivity.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["floor", "winner", "max_dev", "n_models"])
        for f in SENSITIVITY_FLOORS:
            w.writerow([f, winners[f][0], winners[f][1], winners[f][2]])
    floor_dependent = len({v[0] for v in winners.values()}) > 1

    # -- AMENDMENT 1: the output is a SET, at the pre-declared ceiling ------
    #: **THE CEILING IS `MAX_DEV_REFUSAL`, WHICH WAS FROZEN BEFORE THE RUN.**
    #: Using it to ADMIT rather than only to REFUSE adds no parameter, and that
    #: is exactly why it is the boundary rather than a break read off the
    #: observed gradient -- which has none: 6.1, 8.1, 9.4, 10.6, 11.3, 11.3,
    #: 11.9, 13.2. An argmin over that manufactures a winner.
    #:
    #: The argmin result is still computed and still reported. A reader who
    #: suspects the band of being self-serving -- it moved the author's stated
    #: preference from third place to eligible -- can compare the two.
    band = [r for r in rows if r["max_dev"] <= MAX_DEV_REFUSAL]
    with open(os.path.join(RESULTS, "candidates.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in band:
            w.writerow({k: r[k] for k in cols})

    # -- refusal 1: is ANY model representative? ----------------------------
    top = rows[0]
    refused = top["max_dev"] > MAX_DEV_REFUSAL
    summary = {
        "candidate_set_size": len(band),
        "candidates": [r["model"] for r in band],
        #: KEPT, and no longer the headline. See AMENDMENT 1.
        "argmin_winner": None if refused else top["model"],
        "declared_screener": None if refused else top["model"],
        "refusal": ("winner is %.1f points from median on some axis, above the "
                    "declared ceiling of %.0f -- NO REPRESENTATIVE MODEL EXISTS "
                    "IN THIS POPULATION" % (top["max_dev"], MAX_DEV_REFUSAL))
                   if refused else None,
        "floor_dependent": floor_dependent,
        "winners_by_floor": {str(f): winners[f][0] for f in SENSITIVITY_FLOORS},
        "top": {k: top[k] for k in cols},
        #: The runner-up is reported whatever happens. A winner with no margin is
        #: a different object from a winner with one, and a summary that names
        #: only the winner cannot tell them apart.
        "runner_up": {k: rows[1][k] for k in cols} if len(rows) > 1 else None,
    }
    with open(os.path.join(RESULTS, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    with open(os.path.join(HERE, "population.json"), "w") as fh:
        json.dump({
            "date": time.strftime("%Y-%m-%d"),
            "lexicon_sha": LEXICON_SHA,
            "panel_prompts": ch.scalar("SELECT count() FROM {db}.wf_panel"),
            "coverage_floor": a.floor,
            "models_with_any_panel_cells": n_any,
            "models_in_population": len(pop),
            "excluded_below_floor": n_any - len([m for m in cov if cov[m] >= a.floor]),
            "excluded_treated": len([m for m in cov if cov[m] >= a.floor
                                     and "@" not in m and m not in untreated]),
            "excluded_revision_suffixed": len([m for m in cov
                                               if cov[m] >= a.floor and "@" in m]),
            "models": pop,
        }, fh, indent=2)

    print("population: %d models (of %d with any panel cells) at floor %d"
          % (len(pop), n_any, a.floor))
    print("scope: labelled share %.2f%%, CJK share %.3f%% for the winner"
          % (100 * top["labelled_share"], 100 * top["cjk_share"]))
    if refused:
        print("REFUSED: %s" % summary["refusal"])
    else:
        print("screener: %s (max_dev %.1f; mean %.0f%% breadth %.0f%% intensity %.0f%%)"
              % (top["model"], top["max_dev"], top["mean_pct"],
                 top["breadth_pct"], top["intensity_pct"]))
    if floor_dependent:
        print("FLOOR-DEPENDENT: %s -- reported, not broken by a third floor"
              % ", ".join("%d->%s" % (f, winners[f][0]) for f in SENSITIVITY_FLOORS))


if __name__ == "__main__":
    main()
