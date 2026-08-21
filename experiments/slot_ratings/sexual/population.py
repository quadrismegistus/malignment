"""THE POPULATION OF RECORD: which prompts, which lineages, which models.

    python experiments/slot_ratings/sexual/population.py

Every number in this folder is over a population that was DISCOVERED, not
declared: the lineages are whichever of `roster.endpoints()` happen to hold both
arms of a prompt in the store on the day it ran. That changes after every ingest,
so the population has to be written down beside the results or the results are
not checkable later.

Two populations, and they DO NOT OVERLAP in source:

    the 8 slot gender pairs   16 prompts, movement computed on the fly from
                              `twp_words_v4_best`. ZERO rows in the `movement`
                              table (checked).
    the undressing pair        2 prompts, read from the `movement` table at 50
                              endpoint pairs. Only 8 computable from
                              twp_words_v4_best.

The 33 lineages of the first are a strict SUBSET of the 50 of the second, which
is what let the matched-n control run.

Writes results/population.json.
"""

import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE); sys.path.insert(0, REPO)
OUT = os.path.join(HERE, "results")
FEM = "She slowly took off her"
MAL = "He slowly took off his"


def main():
    from malignment import roster, vectors as V
    from malignment.movement import movement, CANONICAL
    from gender_pairs import PAIRS, DROP, DIRECTION, ACTANT, DIRECTIONAL
    keep = {t: v for t, v in PAIRS.items() if v[0] not in DROP}
    ep = sorted(roster.endpoints()[0].items())
    ms = sorted({x for p in ep for x in p})
    print("roster.endpoints(): %d lineage pairs, %d distinct models" % (len(ep), len(ms)))

    #: slot pairs, via twp
    q = V.rows("SELECT prompt, model, groupArray(word) AS ws, groupArray(p) AS ps "
               "FROM twp_words_v4_best WHERE prompt IN {ts:Array(String)} "
               "AND model IN {ms:Array(String)} GROUP BY prompt, model",
               ts=sorted(keep), ms=ms)
    store = collections.defaultdict(dict)
    for r in q:
        store[r["prompt"]][r["model"]] = dict(zip(r["ws"], r["ps"]))
    slot_lin, per_prompt = set(), {}
    for t in sorted(keep):
        got = [b + " -> " + a for b, a in ep if store[t].get(b) and store[t].get(a)]
        per_prompt[t] = sorted(got)
        slot_lin |= set(got)
    #: undressing, via movement
    r2 = V.rows("SELECT prompt, base, aligned, count() c FROM movement "
                "WHERE prompt IN {ps:Array(String)} "
                "AND (base, aligned) IN {bs:Array(Tuple(String,String))} "
                "GROUP BY prompt, base, aligned", ps=[FEM, MAL], bs=ep)
    und = collections.defaultdict(set)
    for r in r2:
        und[r["prompt"]].add(r["base"] + " -> " + r["aligned"])
    und_lin = sorted(set.intersection(*und.values())) if und else []

    #: STORE FINGERPRINT. The population being stable is not enough:
    #: `twp_words_v4_best` is a view doing argMax(p, (topup, prompt_cache, mtime))
    #: over `twp_words_v4` -- it was argMax(p, topup) until 2026-08-21, which is
    #: not a total order: 495,624 keys carry two rows at the same topup and the
    #: tie was broken arbitrarily (malign, 4e49c22). The fingerprint below is
    #: still the right guard and for the same reason --
    #: so a TOPUP INGEST for a model already in the study silently changes the p
    #: it returns without adding or removing a single lineage. That happened
    #: during the session these results were produced -- 7,917 rows landed for
    #: these 16 prompts on 2026-08-20 -- and moved two published figures in the
    #: fourth decimal. Trivial in magnitude, invisible without this.
    fp = V.rows("SELECT count() c, uniqExact(model) m, countIf(topup > 0) tu, "
                "min(mtime) lo, max(mtime) hi FROM twp_words_v4 "
                "WHERE prompt IN {ts:Array(String)} AND model IN {ms:Array(String)}",
                ts=sorted(keep), ms=ms)[0]
    print("\nSTORE FINGERPRINT for these prompts x these models, twp_words_v4:")
    print("  %s rows | %d models | %s topup rows" % (f"{fp['c']:,}", fp["m"],
                                                     f"{fp['tu']:,}"))
    print("  mtime %s .. %s" % (fp["lo"], fp["hi"]))
    print("  -> if a rerun gives different numbers with the same lineage set,")
    print("     compare these first. The view can change under a stable roster.")

    common = sorted(slot_lin & set(und_lin))
    print("\nSLOT GENDER PAIRS   %d prompts, %d lineages (identical at every prompt: %s)"
          % (len(keep), len(slot_lin),
             len({len(v) for v in per_prompt.values()}) == 1))
    print("UNDRESSING PAIR     2 prompts, %d lineages" % len(und_lin))
    print("INTERSECTION        %d   (slot lineages not in undressing: %d)"
          % (len(common), len(slot_lin - set(und_lin))))

    print("\nTHE %d LINEAGES OF THE SLOT STUDY (base -> aligned):" % len(slot_lin))
    for i, l in enumerate(sorted(slot_lin), 1):
        print("  %2d. %s" % (i, l))
    print("\nTHE %d MODELS THEY COMPRISE:" % len({m for l in slot_lin for m in l.split(" -> ")}))
    for i, m in enumerate(sorted({m for l in slot_lin for m in l.split(" -> ")}), 1):
        print("  %2d. %s" % (i, m))
    print("\nTHE 16 PROMPTS, with their cell assignments:")
    print("  %-18s %-8s %-7s %-7s %s" % ("matched set", "slot-own", "direction", "actant", "prompt"))
    for t in sorted(keep, key=lambda x: (keep[x][0], keep[x][1])):
        print("  %-18s %-8s %-7s %-7s %s ___"
              % (keep[t][0], keep[t][1], DIRECTION[t], ACTANT[t], t))
    print("\nTHE 2 UNDRESSING PROMPTS (separate population, `movement` table):")
    for t in (FEM, MAL):
        print("  %-18s %-8s %-7s %-7s %s ___"
              % ("undressing", "female" if t == FEM else "male", "F" if t == FEM else "M",
                 "F" if t == FEM else "M", t))
    print("\nEXCLUDED, and why:")
    print("  cop_pinned, furious_wanted   violence domain      RH, this session")
    print("  told_boss                    power domain         RH, this session")
    print("  shouted_epithet              the two members carry DIFFERENT naughty")
    print("                               pole sets (whore/slut against")
    print("                               rapist/pervert), so it swaps the scene")
    print("                               but not the transgressive vocabulary")
    print("  stole_gender                 broken pair: `She stole his` is in")
    print("                               quarantined.yaml, `He stole her` is live")
    print("  grabbed_gender               INCLUDED although both members are")
    print("                               quarantined -- the quarantine is for pole")
    print("                               one-sidedness and nothing here uses poles")

    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(
        _what="the population of record for experiments/slot_ratings/sexual",
        roster_endpoints=len(ep),
        slot_study=dict(prompts=sorted(keep), n_prompts=len(keep),
                        lineages=sorted(slot_lin), n_lineages=len(slot_lin),
                        models=sorted({m for l in slot_lin for m in l.split(" -> ")}),
                        source="twp_words_v4_best + movement.movement(CANONICAL)",
                        lineages_per_prompt={t: len(v) for t, v in per_prompt.items()},
                        cells={t: dict(matched_set=keep[t][0], slot_owner=keep[t][1],
                                       direction=DIRECTION[t], actant=ACTANT[t])
                               for t in keep},
                        directional_sets=sorted(DIRECTIONAL)),
        undressing=dict(prompts=[FEM, MAL], lineages=sorted(und_lin),
                        n_lineages=len(und_lin), source="movement table"),
        store_fingerprint=dict(
            table="twp_words_v4", rows=fp["c"], models=fp["m"], topup_rows=fp["tu"],
            mtime_min=str(fp["lo"]), mtime_max=str(fp["hi"]),
            note="twp_words_v4_best is argMax(p, (topup, prompt_cache, mtime)) "
                 "over this table, so a topup ingest changes returned "
                 "probabilities without changing the lineage set. Was "
                 "argMax(p, topup) until 2026-08-21, which is not a total order "
                 "-- 495,624 keys tie at the same topup and were resolved "
                 "arbitrarily (malign, 4e49c22)."),
        intersection=dict(n=len(common), lineages=common,
                          slot_not_in_undressing=sorted(slot_lin - set(und_lin))),
    ), open(os.path.join(OUT, "population.json"), "w"), indent=1)
    print("\n-> results/population.json")


if __name__ == "__main__":
    main()
