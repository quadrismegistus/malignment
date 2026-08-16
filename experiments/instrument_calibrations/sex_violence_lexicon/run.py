#!/usr/bin/env python
"""Producer for the sex/violence lexicon. One file, stages selected by --stage.

    run.py --stage assemble   stage A output -> rating items (+ controls, anchors)
    run.py --stage score      rating results -> admitted lexicon + metrics

The agent stages (A generate, D rate) run under the Workflow tool and their
briefs are recorded verbatim in workflows/. Everything a script can do
deterministically is here, so the parts that cannot be replayed are exactly the
parts that needed a model.

WHY THE RATING INPUT IS BUILT HERE AND NOT IN THE WORKFLOW. Controls only work
if the rater cannot tell a control from a candidate. That is a property of the
FILE, so it is established once, by a script, with a recorded seed -- not by a
prompt that says "do not reveal". See registration.md, "Blindness".
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(start):
    """Upward search for the directory holding `malignment/`.

    Not dirname(dirname(...)): that broke the moment an experiment moved from
    experiments/<q>/ to experiments/<subject>/<q>/. Depth is not a constant.
    """
    d = start
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, "malignment")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError(f"no malignment/ above {start}")


ROOT = _repo_root(HERE)
sys.path.insert(0, ROOT)

from malignment import ch  # noqa: E402

RESULTS = os.path.join(HERE, "results")
SEED = 20260816  # recorded, so "which sample" cannot drift between build and use

#: Registration rule 4. These motivated the build, so they cannot be cited as
#: evidence FOR it -- but they are rated, admitted and counted like every other
#: word. NOTHING is subtracted. An earlier draft struck them from the precision
#: and recall denominators, which was inert (a generator-proposed word cannot
#: reach the control or audit pool anyway) and mis-shaped (a citation rule
#: wearing the costume of an accounting rule). They are FLAGGED, not removed.
BURN_IN = {"cock", "stabbed"}

#: The seed list handed to generators (workflows/generate.md). Rule 6: a word we
#: supplied is not a word the panel found.
SEEDS = {
    "cock", "penis", "vagina", "breast", "orgasm", "arousal", "seduce", "naked",
    "kill", "stab", "strangle", "wound", "blade", "bruise", "slaughter", "choke",
}

ALPHA = re.compile(r"^[A-Za-z]+$")

#: Conservative inflectional suffixes for stage C. Deliberately NOT a lemmatiser:
#: out-of-context lemmatisation is the BYU defect fields.py was built to avoid,
#: and every expanded form is rated by the panel anyway, so a wrong expansion is
#: rejected downstream rather than admitted silently.
SUFFIXES = ("s", "es", "ed", "d", "ing", "er", "ers", "ings", "y", "ies")


def vocabulary():
    """Every distinct English word in twp_words, with its cell count.

    NO FREQUENCY CUT. registration.md, "Population": frequency correlates with
    the target (cunt 137 cells, horny 33), so a frequency cut is a selection on
    the target.
    """
    rows = ch.query(
        "SELECT word, count() AS cells FROM {db}.twp_words "
        "WHERE match(word, '^[A-Za-z]+$') GROUP BY word"
    )
    return {r["word"]: int(r["cells"]) for r in rows}


def expand(lemmas, vocab_lower):
    """Stage C: inflectional variants of confirmed lemmas that EXIST in the corpus.

    Returns {surface: lemma}. A variant is a candidate, not an admission.
    """
    out = {}
    for lemma in lemmas:
        stems = {lemma}
        if lemma.endswith("e"):
            stems.add(lemma[:-1])
        if lemma.endswith("y"):
            stems.add(lemma[:-1])
        for stem in stems:
            for suf in SUFFIXES:
                cand = stem + suf
                if cand != lemma and cand in vocab_lower and cand not in out:
                    out[cand] = lemma
            # doubled final consonant: stab -> stabbed, stabbing
            if len(stem) >= 3 and stem[-1] not in "aeiouwxy" and stem[-2] in "aeiou":
                for suf in ("ed", "ing", "er"):
                    cand = stem + stem[-1] + suf
                    if cand in vocab_lower and cand not in out:
                        out[cand] = lemma
    return out


def expansion_stems(payload):
    """Recover the stage-C {surface: stem} map from the rating file.

    Not persisted at assemble time, and deliberately RECOMPUTED rather than
    re-queried: `expand` is a pure function of (candidates, allowed-set), and
    both are recorded in rating_items.json, so this reproduces the original map
    exactly without touching ClickHouse. If expand() is ever changed, this
    recomputation changes with it -- which is correct, because a stem map that
    disagreed with the current rule would be worse than none.
    """
    cand = {it["word"] for it in payload["items"] if it["kind"] == "candidate"}
    exps = {it["word"] for it in payload["items"] if it["kind"] == "expansion"}
    return {s: l for s, l in expand(sorted(cand), exps).items() if s in exps}


def cmd_assemble(args):
    with open(args.generated) as f:
        gen = json.load(f)

    vocab = vocabulary()
    # SUM on case collision, do not overwrite. A dict comprehension keyed on
    # w.lower() lets `Rape` (4 cells) clobber `rape` (3,126) or vice versa
    # depending only on query order, so `cells` became an arbitrary pick among
    # case variants. It does NOT affect membership (presence is presence) and
    # does NOT affect the lexicon sha, which is computed over {word: category} --
    # but every frequency statement derived from `cells` was wrong.
    vocab_lower = Counter()
    for w, c in vocab.items():
        vocab_lower[w.lower()] += c

    # ---- stage B: what the panel proposed, and what the corpus actually holds
    proposed = defaultdict(lambda: {"agents": set(), "cats": Counter(), "regs": Counter(),
                                    "conf": Counter()})
    for group in ("replicates", "angles"):
        for entry in gen.get(group, []):
            for w in entry.get("words", []):
                word = str(w.get("word", "")).strip().lower()
                if not word or not ALPHA.match(word):
                    continue
                p = proposed[word]
                p["agents"].add(entry["agent"])
                p["cats"][w.get("category", "")] += 1
                p["regs"][w.get("register", "")] += 1
                p["conf"][w.get("confidence", "")] += 1

    replicate_agents = {e["agent"] for e in gen.get("replicates", [])}
    in_corpus = {w: d for w, d in proposed.items() if w in vocab_lower}

    # ---- stage C: inflections of corpus-present proposals
    expansions = expand(sorted(in_corpus), vocab_lower)
    expansions = {w: l for w, l in expansions.items() if w not in in_corpus}

    # ---- stage D input: candidates + expansions + controls + anchors, shuffled
    rng = random.Random(SEED)
    proposed_any = set(proposed)              # incl. words absent from corpus
    stems = set(in_corpus)

    def touches_stem(w):
        return any(w.startswith(s) or s.startswith(w) for s in stems if len(s) >= 4)

    # `expansions` MUST be subtracted here. It was not, in the first run, and 8
    # stage-C expansions were also drawn as controls/audit items -- `touches_stem`
    # only guards stems of >=4 chars, so rotted/hewed/woos (rot, hew, woo) walked
    # through. Effect: `mutilating` was scored as a recall MISS when it was a
    # candidate all along, inflating the audit rate 0.336% -> 0.503%. The error
    # direction was against the instrument, which is why it survived a passing
    # gate; a defect that flatters would have been caught by the gate itself.
    control_pool = [w for w in vocab_lower
                    if w not in proposed_any and w not in expansions
                    and not touches_stem(w) and len(w) > 2]
    control_pool.sort()
    n_control = max(200, int(args.control_ratio * (len(in_corpus) + len(expansions))))
    controls = rng.sample(control_pool, min(n_control, len(control_pool)))

    # stage E: the recall audit draws from the SAME remainder, disjoint from controls
    remaining = sorted(set(control_pool) - set(controls))
    audit = rng.sample(remaining, min(args.audit_n, len(remaining)))

    items = []
    for w in sorted(in_corpus):
        items.append({"word": w, "kind": "candidate", "cells": vocab_lower[w]})
    for w in sorted(expansions):
        items.append({"word": w, "kind": "expansion", "cells": vocab_lower[w]})
    for w in controls:
        items.append({"word": w, "kind": "control", "cells": vocab_lower[w]})
    for w in audit:
        items.append({"word": w, "kind": "audit", "cells": vocab_lower[w]})

    # ANCHORS: a fixed block every rater sees, for K-way agreement. Drawn from
    # all four kinds so anchor agreement is not measured on easy items only.
    rng.shuffle(items)
    by_kind = defaultdict(list)
    for it in items:
        by_kind[it["kind"]].append(it)
    anchors = []
    for kind, n in (("candidate", 60), ("expansion", 30), ("control", 40), ("audit", 20)):
        anchors += [it["word"] for it in by_kind[kind][:n]]
    anchor_set = set(anchors)

    rng.shuffle(items)
    payload = {
        "seed": SEED,
        "anchors": sorted(anchor_set),
        # `kind` is STRIPPED from what raters see. It lives only here.
        "items": items,
    }

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "rating_items.json"), "w") as f:
        json.dump(payload, f, indent=1, sort_keys=True)

    # rater-facing file: word only, no kind, no cells, no provenance
    with open(os.path.join(RESULTS, "rating_words.json"), "w") as f:
        json.dump([it["word"] for it in items], f, indent=0)

    pop = {
        "date": "2026-08-16",
        "seed": SEED,
        "vocabulary_query": "SELECT word, count() FROM twp_words WHERE match(word,'^[A-Za-z]+$') GROUP BY word",
        "vocabulary_english": len(vocab),
        "vocabulary_all": ch.scalar("SELECT count(DISTINCT word) FROM {db}.twp_words"),
        "twp_rows": ch.scalar("SELECT count() FROM {db}.twp_words"),
        "generators": {"replicates": sorted(replicate_agents),
                       "angles": sorted({e["agent"] for e in gen.get("angles", [])})},
        "proposed_total": len(proposed),
        "proposed_in_corpus": len(in_corpus),
        "proposed_absent_from_corpus": len(proposed) - len(in_corpus),
        "expansions": len(expansions),
        "controls": len(controls),
        "audit": len(audit),
        "anchors": len(anchor_set),
        "rating_items": len(items),
        "burn_in_excluded": sorted(BURN_IN),
        "seeded_words": sorted(SEEDS),
    }
    with open(os.path.join(HERE, "population.json"), "w") as f:
        json.dump(pop, f, indent=1, sort_keys=True)

    for k, v in pop.items():
        if isinstance(v, int):
            print(f"  {k:<32} {v:>8,}")
    print(f"\n  wrote results/rating_items.json  ({len(items):,} items, kind hidden)")
    print(f"  wrote results/rating_words.json  (rater-facing)")


def cmd_score(args):
    """Apply the declared admission rule and compute the declared gates."""
    with open(os.path.join(RESULTS, "rating_items.json")) as f:
        payload = json.load(f)
    # FIRST-write-wins, not last: items are emitted candidates, expansions,
    # controls, audit, so a word appearing in two kinds keeps the earlier
    # (candidate/expansion) label. A dict comprehension takes the LAST, which
    # silently relabelled 8 expansions as control/audit in the first run and put
    # one of them in the recall denominator. The collision is now also REPORTED
    # rather than resolved quietly -- a fixed precedence hides the count.
    # CELL COUNTS ARE RE-QUERIED HERE, CASE-SUMMED, rather than taken from
    # rating_items.json. The assemble stage keyed a dict on w.lower(), so a
    # collision OVERWROTE: `rape` was booked at 4 cells (the count for `Rape`)
    # against a true 3,130, and `raped` at 1 against 3,563. Which variant won
    # depended only on query order. Membership and the lexicon sha are computed
    # over {word: category} and are unaffected; every FREQUENCY statement
    # derived from `cells` was wrong.
    #
    # AND `assemble` MUST NOT BE RE-RUN TO FIX IT. Its control pool has since
    # been corrected too (expansions are now excluded), so re-running would draw
    # a different sample and orphan the 15 raters' work, which is keyed to the
    # item list they actually saw. rating_items.json is the artifact of record;
    # the assemble fixes apply to any FUTURE build.
    true_cells = {r["w"]: int(r["n"]) for r in ch.query(
        "SELECT lower(word) AS w, count() AS n FROM {db}.twp_words "
        "WHERE match(word, '^[A-Za-z]+$') GROUP BY w")}

    kind, cells = {}, {}
    collisions = defaultdict(set)
    for it in payload["items"]:
        collisions[it["word"]].add(it["kind"])
        kind.setdefault(it["word"], it["kind"])
        cells.setdefault(it["word"], true_cells.get(it["word"], it["cells"]))
    collided = {w: sorted(k) for w, k in collisions.items() if len(k) > 1}
    if collided:
        print(f"  KIND COLLISIONS  : {len(collided)} -> resolved to first kind")
        for w, k in sorted(collided.items()):
            print(f"      {w:<16} {k}")

    # REGISTER, carried through from stage A. Not decoration: v1's headline
    # displacement finding IS a register shift (cock -> penis, same referent,
    # different social class), and a lexicon that knows a word's register lets
    # that be tested at corpus scale instead of by hand on one word. Expansions
    # inherit their stem's register; controls and audit words have none.
    register = {}
    gpath = os.path.join(RESULTS, "generated.json")
    if os.path.exists(gpath):
        gen = json.load(open(gpath))
        tally = defaultdict(Counter)
        for group in ("replicates", "angles"):
            for e in gen.get(group, []):
                for w in e.get("words", []):
                    word = str(w.get("word", "")).strip().lower()
                    if word:
                        tally[word][w.get("register", "")] += 1
        register = {w: c.most_common(1)[0][0] for w, c in tally.items()}
        for surface, stem in expansion_stems(payload).items():
            register.setdefault(surface, register.get(stem, ""))

    # One file per rater, written by the stage-D agents. Read them all; a rater
    # that failed to write is a MISSING RATER, reported, never silently a zero.
    rated_dir = os.path.join(RESULTS, "rated")
    expected = [m["name"] for m in
                json.load(open(os.path.join(RESULTS, "blocks", "manifest.json")))]
    votes = defaultdict(Counter)
    raters = defaultdict(set)
    present, missing, malformed = [], [], []
    for name in expected:
        path = os.path.join(rated_dir, name + ".json")
        if not os.path.exists(path):
            missing.append(name)
            continue
        try:
            rows = json.load(open(path))
        except Exception as e:                       # noqa: BLE001
            malformed.append((name, str(e)[:60]))
            continue
        present.append(name)
        for r in rows:
            w = str(r.get("word", "")).strip().lower()
            if w not in kind:
                continue
            votes[w][r.get("category", "neither")] += 1
            raters[w].add(name)

    if missing or malformed:
        print(f"  MISSING RATERS   : {missing}")
        print(f"  MALFORMED        : {malformed}")
    print(f"  raters present   : {len(present)}/{len(expected)}")

    # An item rated by fewer than 3 cannot meet the >=2-of-3 rule as declared.
    # Count them; do not quietly admit on 1-of-1.
    thin = [w for w in votes if len(raters[w]) < 3]
    if thin:
        print(f"  items with <3 raters : {len(thin):,}")

    # RULE 1: >= 2 of 3 raters agree. Ties are excluded, not broken.
    # `most_common(1)` picks arbitrarily among ties, so check for a tie FIRST --
    # a 1/1/1 split must not become an admission because Counter ordered it.
    admitted, split = {}, []
    for w, c in votes.items():
        ranked = c.most_common()
        top, n = ranked[0]
        tied = len(ranked) > 1 and ranked[1][1] == n
        if tied:
            split.append(w)
            continue
        if n >= 2 and top in ("sexual", "violent", "both"):
            admitted[w] = {"category": top, "votes": n, "n_raters": len(raters[w]),
                           "cells": cells[w], "kind": kind[w],
                           "seeded": w in SEEDS, "burn_in": w in BURN_IN,
                           "register": register.get(w, "")}
        elif top != "neither":
            split.append(w)

    def rate(k):
        # No BURN_IN subtraction: see rule 4. Whatever landed in this pool by
        # the seeded draw is the pool.
        pool = [w for w in kind if kind[w] == k]
        pos = [w for w in pool if w in admitted]
        return len(pos), len(pool), (len(pos) / len(pool) if pool else float("nan"))

    fp_n, fp_d, fp = rate("control")
    au_n, au_d, au = rate("audit")

    n_remainder = sum(1 for w in kind if kind[w] in ("control", "audit"))
    lex = {w: d for w, d in admitted.items() if d["kind"] in ("candidate", "expansion")}

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "lexicon.json"), "w") as f:
        json.dump({w: lex[w] for w in sorted(lex)}, f, indent=1, sort_keys=True)
    sha = hashlib.sha256(
        json.dumps({w: lex[w]["category"] for w in sorted(lex)}, sort_keys=True).encode()
    ).hexdigest()[:16]

    # ANCHOR AGREEMENT: 150 words seen by all 15 raters. This is the reliability
    # number -- how much the lexicon is one model's judgment rather than the
    # categories'. Reported whatever it is; it gates nothing, because a low
    # value is a fact about the construct, not a reason to hide the instrument.
    anchors = set(payload["anchors"])
    anc = [(w, votes[w]) for w in anchors if w in votes]
    unanimous = sum(1 for _, c in anc if len(c) == 1)
    maj = sum(1 for _, c in anc if c.most_common(1)[0][1] / sum(c.values()) >= 0.8)

    def pct_agree(c):
        """Observed pairwise agreement among this item's raters (Fleiss P_i)."""
        n = sum(c.values())
        return sum(v * (v - 1) for v in c.values()) / (n * (n - 1)) if n > 1 else float("nan")

    pbar = sum(pct_agree(c) for _, c in anc) / len(anc) if anc else float("nan")
    # chance agreement from the marginal category distribution over anchors
    tot = Counter()
    for _, c in anc:
        tot.update(c)
    N = sum(tot.values())
    pe = sum((v / N) ** 2 for v in tot.values()) if N else float("nan")
    kappa = (pbar - pe) / (1 - pe) if pe not in (1.0, float("nan")) else float("nan")

    metrics = {
        "lexicon_sha": sha,
        "raters_present": len(present),
        "raters_missing": missing,
        "items_under_3_raters": len(thin),
        "anchor_n": len(anc),
        "anchor_unanimous": unanimous,
        "anchor_majority_80pct": maj,
        "anchor_pairwise_agreement": round(pbar, 4),
        "anchor_fleiss_kappa": round(kappa, 4),
        "admitted": len(lex),
        "admitted_sexual": sum(1 for d in lex.values() if d["category"] == "sexual"),
        "admitted_violent": sum(1 for d in lex.values() if d["category"] == "violent"),
        "admitted_both": sum(1 for d in lex.values() if d["category"] == "both"),
        "admitted_seeded": sum(1 for d in lex.values() if d["seeded"]),
        "split_excluded": len(split),
        "control_positive": fp_n, "control_n": fp_d, "control_fp_rate": fp,
        "audit_positive": au_n, "audit_n": au_d, "audit_positive_rate": au,
        "GATE_precision_pass": bool(fp <= 0.05),
    }
    with open(os.path.join(RESULTS, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=1, sort_keys=True)

    for k, v in metrics.items():
        print(f"  {k:<26} {v}")
    print()
    if not metrics["GATE_precision_pass"]:
        print("  GATE 2 FAILED: control false-positive rate above 5%.")
        print("  registration.md rule 2: the lexicon is NOT ADMITTED. Do not retune.")
    else:
        print(f"  GATE 2 PASSED. lexicon frozen at sha {sha}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=("assemble", "score"))
    ap.add_argument("--generated", default=os.path.join(RESULTS, "generated.json"))
    ap.add_argument("--rated", default=os.path.join(RESULTS, "rated.json"))
    ap.add_argument("--control-ratio", type=float, default=0.25)
    ap.add_argument("--audit-n", type=int, default=600)
    args = ap.parse_args()
    {"assemble": cmd_assemble, "score": cmd_score}[args.stage](args)


if __name__ == "__main__":
    main()
