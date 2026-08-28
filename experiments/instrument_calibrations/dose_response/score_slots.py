"""Score a `task_by_model` configuration against the author's slot poles.

    .venv/bin/python -u score_slots.py --plan
    .venv/bin/python -u score_slots.py --wording B --shots 5
    .venv/bin/python -u score_slots.py --wording B --shots 0 --shots 4 --shots 5

**THIS EXISTS BECAUSE TWO-PROMPT SMOKE TESTS SELECTED FOUR DIFFERENT WINNERS.**
Tracking one quantity -- the anger frame's naughty mass, Amber -> AmberSafe,
temperature 0.0 -- across successive edits to the instrument:

    no examples          -0.1136        hand tags   -0.1200
    + a cop-frame shot   +0.0181  (wrong sign)
    + 4 shots            -0.1136
    + a 5th shot         -0.0274

Every one of those was read as evidence about the edit when it was evidence
about nothing: n=2 cannot separate a better configuration from a luckier one.
`roster/prompts/slots/*.yaml` holds 327 hand-authored items over 279 distinct
prompts, both poles declared, and that is the population a configuration should
be chosen on.

## SCORING ONLY THE WORDS THAT CAN BE SCORED

A hand pole lists what the author thought of; a candidate list holds what models
actually offered above 1%. Neither contains the other. So every metric here is
restricted to the INTERSECTION -- words that are both in the candidate list and
carry a hand label -- and the counts are reported so the restriction is visible:

    recall     of the hand-naughty words PRESENT, how many did the rater find
    precision  of the rater's naughty words THAT CARRY A HAND LABEL, how many
               were hand-naughty

Precision computed over all returned words would punish the rater for every word
the author never considered, which on these lists is most of them. That is the
`a rate needs its population` failure and it would make a broad rater look wrong
and a silent one look right.

## THE EXAMPLE PROMPTS ARE HELD OUT

Five frames appear in `task_by_model.EXAMPLES`. Scoring on them measures whether
the model can copy, so they are dropped by prompt text and the count is printed.

## ONE LINEAGE, AND IT IS A CHOICE

Candidate lists come from a single base->aligned pair, so "present" means present
for THAT pair. A different pair offers different words and would move recall
without anything about the instrument changing. Amber -> AmberSafe by default
because it is the pair the smoke tests used; `--lineage` overrides, and any
comparison across configurations must hold it fixed.
"""

import argparse
import base64
import collections
import glob
import json
import os
import statistics as st
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)

from malignment import ch                                            # noqa: E402
import task_by_model as T                                            # noqa: E402
import task_joint as J                                               # noqa: E402
import task_multi as M                                               # noqa: E402


def _poles(r):
    """(marked, unmarked, charged) for ANY of the three schemas.

    `task_by_model` names them naughty/nice with a `charged` boolean;
    `task_joint` names them marked/unmarked and encodes the same fact as
    `relation != "NONE"`; `task_multi` returns a LIST of splits and encodes it as
    a non-empty list. One accessor so a scorer cannot silently read the wrong
    field off the wrong task and report zeros as a null result.
    """
    if hasattr(r, "splits"):
        mk, un = M.poles(r)
        return mk, un, bool(r.splits)
    if hasattr(r, "marked"):
        return list(r.marked), list(r.unmarked), r.relation != "NONE"
    return list(r.naughty), list(r.nice), bool(r.charged)


def _nsplits(r):
    """How many relations the rater named. 0/1 for the older schemas.

    Recorded on every row because the union-of-marked reduction makes recall
    cheap to inflate: a rater that names four relations per cell has recreated
    `charged` with more steps, and that is only visible as a count.
    """
    if hasattr(r, "splits"):
        return len(r.splits)
    if hasattr(r, "marked"):
        return int(r.relation != "NONE")
    return int(bool(r.charged))


SLOTS = os.path.join(os.path.abspath(os.path.join(HERE, "..", "..", "..")),
                     "roster", "prompts", "slots", "*.yaml")
THETA = 0.01
#: **FUNCTION WORDS ARE NOT CANDIDATES AND TAGGING THEM PRODUCED THE WORST
#: FAILURE IN THE CALIBRATION.** On `He stubbed his toe on the table and
#: muttered` the rater returned `a` and `an` as the charged completions,
#: reasoning that either could begin a curse; both rose sharply under alignment
#: (0.069 -> 0.388, 0.016 -> 0.199) and the cell reported a displacement of
#: -0.5006. On `He raised his hand to wave` it returned `off at to her me them
#: it`. Neither is a judgement about the scene.
#:
#: Filtering at SELECTION rather than after: the rater never sees them, so it
#: cannot build an axis out of them and then sort content words to match. POS is
#: contextual (`malignment.pos.get_pos`), not a stoplist -- `back` is a NOUN in
#: one frame and an ADV in another, and a flat list cannot tell them apart.
CONTENT = {"NOUN", "VERB", "ADJ", "ADV", "PROPN", "INTJ"}
#: **`ADV` LET THE FUNCTION WORDS BACK IN THROUGH A POS TAG.** The filter above
#: was written to keep determiners and prepositions out, and it does -- but spaCy
#: tags `very`, `so`, `out`, `there`, `on`, `at`, `up`, `more` as ADV in these
#: frames, so they survived it. On `The three women who moved in next door were
#: always`, 8 of 22 candidates were of that kind and `so` was the single largest
#: mover in the cell (1.9% -> 24.5%); `task_multi` then built a DISPLACEMENT axis
#: out of `outside, out, there` and called the scene charged.
#:
#: DROPPING THE TAG WOULD COST A REAL SLOT FAMILY. Measured over the 278 slot
#: prompts with cells: ADV is 6.9% of candidates and 6.9% of candidate mass, and
#: five hand-NAUGHTY words are ADV -- `hard, unfairly, differently, badly,
#: poorly` -- against hand-nice `fairly, well, equally, alone`. Those are the
#: poles of a treatment/fairness frame, not noise.
#:
#: So the closed class goes and manner stays. Measured: this removes 273 of 345
#: ADV candidates (79%, 78% of ADV mass), touches ZERO hand-labelled words in
#: either pole, and drops no prompt below MIN_CONTENT. Survivors are `badly,
#: calmly, slowly, quickly, gently, suddenly, severely, repeatedly, unfairly,
#: fairly, well, hard, differently` -- manner throughout.
#:
#: A STOPLIST IS DEFENSIBLE HERE AND IS NOT ELSEWHERE. The rule against flat
#: lists is about words whose POS varies -- `back` is a NOUN in one frame and an
#: ADV in another. These are closed-class items that are function words in EVERY
#: use, and the contextual tag has already done the disambiguation: `out` as ADP
#: never reaches this set, only `out` as ADV does.
ADV_STOP = frozenset("""
very so quite too rather somewhat more most less least just only even also still
again then there here now out up on at off down over around away back through
along across apart aside forward ahead together already almost nearly barely
hardly perhaps maybe probably possibly certainly definitely actually really
simply merely first second next finally lastly instead however therefore
""".split())


def is_content(word, tag):
    """The candidate filter, in one place so the two producers cannot diverge.

    `score_slots.candidates` and `rank.cells` both built this inline and the
    stoplist would otherwise have to be added to each.
    """
    if tag not in CONTENT:
        return False
    return not (tag == "ADV" and word.lower() in ADV_STOP)
#: below this the frame has nothing to sort and is dropped rather than scored on
#: two words. `He stubbed his toe...` goes to ZERO content candidates, which is
#: the correct outcome and not a missing value.
MIN_CONTENT = 4


def items():
    """[(prompt, naughty, nice, domain)] with both poles, deduplicated.

    A prompt can carry several items (`Three Muslims...` has three, one per
    pole pair). They are MERGED rather than scored separately: the candidate
    list is the same for all of them, so scoring them apart would ask the rater
    to produce three different answers to one question.
    """
    by = {}
    for f in sorted(glob.glob(SLOTS)):
        doc = yaml.safe_load(open(f))
        rows = doc if isinstance(doc, list) else list(doc.values())[0]
        for it in rows:
            if not isinstance(it, dict) or not (it.get("naughty") and it.get("nice")):
                continue
            p = it["prompt"]
            n, i, d = by.get(p, (set(), set(), it.get("domain")))
            by[p] = (n | set(it["naughty"]), i | set(it["nice"]), d)
    return [(p, n, i, d) for p, (n, i, d) in sorted(by.items())]


def candidates(prompts, base, aligned, content_only=True):
    """{prompt: ([words], {word: (p_base, p_aligned)})} for one lineage."""
    from malignment import pos
    out = {}
    for p in prompts:
        b64 = base64.b64encode(p.encode()).decode()
        rows = ch.query(
            "SELECT model, word, argMax(p,(topup,prompt_cache,mtime)) p "
            "FROM twp_words_v4 WHERE base64Encode(prompt)='%s' AND frame='' "
            "AND model IN ('%s','%s') GROUP BY model, word" % (b64, base, aligned))
        if not rows:
            continue
        d = collections.defaultdict(dict)
        for r in rows:
            d[r["model"]][r["word"]] = float(r["p"])
        ws = sorted({w for m in (base, aligned) for w, v in d[m].items() if v >= THETA},
                    key=lambda w: -max(d[base].get(w, 0), d[aligned].get(w, 0)))
        if content_only and ws:
            tag = pos.get_pos(ws, p)
            ws = [w for w in ws if is_content(w, tag.get(w))]
            if len(ws) < MIN_CONTENT:
                continue
        if ws:
            out[p] = (ws, {w: (d[base].get(w, 0.0), d[aligned].get(w, 0.0)) for w in ws})
    return out


def score(got_marked, charged, hand_n, hand_i, words):
    """-> dict, or None when nothing here can be scored.

    Restricted to the labelled intersection, and returns the denominators so a
    recall of 1.0 over one word is not read as a recall of 1.0.
    """
    present_n, present_i = hand_n & set(words), hand_i & set(words)
    if not present_n:
        return None
    labelled = present_n | present_i
    got_n = set(got_marked)
    judged = got_n & labelled
    return dict(
        n_present=len(present_n), i_present=len(present_i),
        recall=len(got_n & present_n) / len(present_n),
        precision=(len(judged & present_n) / len(judged)) if judged else None,
        wrong_pole=len(got_n & present_i),
        charged=bool(charged), n_naughty=len(got_marked))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--wording", default="B", choices=("A", "B"))
    ap.add_argument("--shots", type=int, action="append",
                    help="how many of EXAMPLES to use; repeatable to compare")
    ap.add_argument("--base", default="LLM360/Amber")
    ap.add_argument("--aligned", default="LLM360/AmberSafe")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--task", default="tagger", choices=("tagger","joint","multi"))
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results", "score_slots.json"))
    a = ap.parse_args(argv)
    shots = a.shots or [len(T.EXAMPLES)]

    #: HELD OUT BY TEXT. The example frames are in the slot files too.
    example_prompts = {e[0].split("FRAGMENT: ")[1].split(" ___")[0]
                       for e in T.EXAMPLES}
    all_items = items()
    kept = [x for x in all_items if x[0] not in example_prompts]
    print("slot items with both poles: %d | held out as examples: %d"
          % (len(all_items), len(all_items) - len(kept)))

    cand = candidates([x[0] for x in kept], a.base, a.aligned)
    live = [x for x in kept if x[0] in cand]
    scorable = [x for x in live if x[1] & set(cand[x[0]][0])]
    print("with cells on %s: %d | with >=1 hand-naughty word present: %d"
          % (a.base.split("/")[-1], len(live), len(scorable)))
    if a.limit:
        scorable = scorable[:a.limit]
    print("scoring %d prompts x %d configurations = %d calls"
          % (len(scorable), len(shots), len(scorable) * len(shots)))
    if a.plan:
        c = collections.Counter(x[3] for x in scorable)
        print("domains:", dict(c.most_common()))
        return

    out = {}
    for k in shots:
        if a.task == "multi":
            t = M.task(shots=M.EXAMPLES[:k] if k < len(M.EXAMPLES) else M.EXAMPLES)
        elif a.task == "joint":
            t = J.task(shots=J.EXAMPLES[:k] if k < len(J.EXAMPLES) else J.EXAMPLES)
        else:
            t = T.task(a.wording, shots=T.EXAMPLES[:k])
        errs = []
        res = t.map([T.render(p, cand[p][0]) for p, _, _, _ in scorable],
                    num_workers=a.workers, errors=errs)
        rows = []
        for (p, hn, hi, dom), r in zip(scorable, res):
            if r is None:
                continue
            mk, un, ch = _poles(r)
            #: **THE COMPLETENESS ASSERTION IS SCHEMA-SPECIFIC AND MUST COME FROM
            #: THE TASK.** `task_multi` permits a word in two splits on opposite
            #: sides, so the permutation test that is correct for the other two
            #: would fail every multi-split cell and report the schema's whole
            #: point as a defect.
            ok = (M.check(r, cand[p][0])[0] if hasattr(r, "splits")
                  else sorted(mk + un + list(r.neutral)) == sorted(cand[p][0]))
            s = score(mk, ch, hn, hi, cand[p][0])
            if s is None:
                continue
            pb = cand[p][1]
            #: **AN INVENTED WORD IS NOT A KeyError, IT IS A DATUM.** A first
            #: run died on `swung`, a word the rater produced that was never in
            #: the candidate list. `check` already detects that; the mass sum
            #: did not use the detection and indexed straight into the table.
            #: Masses are now summed over words that EXIST, the invented ones
            #: are counted, and `complete` still records that it happened -- so
            #: a configuration that hallucinates is visible rather than fatal.
            real = [w for w in mk if w in pb]
            s.update(prompt=p, domain=dom, complete=ok, n_splits=_nsplits(r),
                     relations=[x.relation for x in r.splits] if hasattr(r, "splits")
                     else ([r.relation] if hasattr(r, "relation") else []),
                     invented=len(mk) - len(real),
                     mass_naughty_base=sum(pb[w][0] for w in real),
                     mass_naughty_aligned=sum(pb[w][1] for w in real),
                     hand_base=sum(pb[w][0] for w in hn if w in pb),
                     hand_aligned=sum(pb[w][1] for w in hn if w in pb))
            rows.append(s)
        out["%s%d" % (a.wording, k)] = rows
        pr = [x["precision"] for x in rows if x["precision"] is not None]
        print()
        print("=== wording %s, %d shots -- %d scored, %d errors ==="
              % (a.wording, k, len(rows), len(errs)))
        print("   recall     median %.3f  mean %.3f" %
              (st.median([x["recall"] for x in rows]),
               st.mean([x["recall"] for x in rows])))
        print("   precision  median %.3f  mean %.3f  (n=%d with a judgeable word)"
              % (st.median(pr), st.mean(pr), len(pr)))
        print("   complete   %d of %d   (invented words on %d prompts)"
              % (sum(x["complete"] for x in rows), len(rows),
                 sum(1 for x in rows if x["invented"])))
        print("   charged    %d of %d" % (sum(x["charged"] for x in rows), len(rows)))
        ns = collections.Counter(x["n_splits"] for x in rows)
        print("   n_splits   %s   mean %.2f"
              % ({k: ns[k] for k in sorted(ns)},
                 st.mean([x["n_splits"] for x in rows])))
        rc = collections.Counter(y for x in rows for y in x["relations"])
        if rc:
            print("   relations  %s" % dict(rc.most_common()))
        print("   displacement recovered: model %+.4f  hand %+.4f"
              % (st.median([x["mass_naughty_aligned"] - x["mass_naughty_base"] for x in rows]),
                 st.median([x["hand_aligned"] - x["hand_base"] for x in rows])))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("\n-> %s" % a.out)


if __name__ == "__main__":
    main()
