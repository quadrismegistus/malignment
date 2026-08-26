"""Three wordings against 60 hand-tagged prompts. Which reproduces human tagging?

Scored on what the dose actually uses:

  RECALL     of the author's tagged words -- a missed loaded word underestimates
             the dose, and that is the failure mode of a search task.
  PRECISION  extra words are not automatically wrong (the author tagged a median 5
             of ~500 candidates and was not trying to be exhaustive), so precision
             is reported and NOT optimised.
  MASS r     correlation between hand-derived and model-derived base_naughty_mass.
             THIS IS THE ONE THAT MATTERS: two different word sets can give the
             same dose, and the dose is the quantity every downstream test uses.
  EMPTY      share of prompts returned with any_loaded false. The hand-tagged 255
             are all frames an author thought worth tagging, so a wording that
             returns empty on many of them is failing, not being conservative.
"""
import argparse, base64, json, os, random, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--cands", type=int, default=200)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--wordings", default="A,B,C")
    a = ap.parse_args(argv)

    from malignment import ch, roster
    from malignment.slots import corpora, read_items
    from task import task_for, render
    import numpy as np

    m = roster.endpoints(); m = m[0] if isinstance(m, tuple) else m
    inb = ",".join("'" + b.replace("'", "''") + "'" for b in sorted(m))
    items = [d for _, p in corpora() for d in read_items(p) if not d.get("quarantined")]
    tagged = {}
    for d in items:
        if d.get("naughty"):
            tagged.setdefault(d["prompt"], set()).update(d["naughty"])
    mv4 = {r["prompt"] for r in ch.query("SELECT DISTINCT prompt FROM movement_v4")}
    pool = sorted(p for p in tagged if p in mv4)
    random.Random(20260826).shuffle(pool)
    pool = pool[:a.n]
    print("hand-tagged prompts in movement_v4: %d | piloting on %d" % (len(tagged), len(pool)))

    #: candidates AND per-model mass, one query per prompt
    CAND, MASS = {}, {}
    for p in pool:
        b64 = base64.b64encode(p.encode()).decode()
        rows = ch.query("SELECT word, sum(p) s FROM twp_words_v4 WHERE base64Encode(prompt)='%s' "
                        "AND model IN (%s) GROUP BY word ORDER BY s DESC LIMIT %d"
                        % (b64, inb, a.cands))
        CAND[p] = [r["word"] for r in rows]
        MASS[p] = {r["word"]: float(r["s"]) for r in rows}
    tot = {p: sum(MASS[p].values()) or 1.0 for p in pool}
    print("candidates: median %d per prompt\n"
          % int(np.median([len(CAND[p]) for p in pool])))

    print("%-4s %8s %8s %8s %8s %8s   %s"
          % ("word", "recall", "prec", "mass r", "empty", "n_words", "note"))
    for key in a.wordings.split(","):
        t = task_for(key)
        errs = []
        out = t.map([render(p, CAND[p]) for p in pool], num_workers=a.workers, errors=errs)
        rec, prec, hm, mm, empty, nw, bad = [], [], [], [], 0, [], 0
        for p, r in zip(pool, out):
            if r is None:
                continue
            got = [w for w in (r.words or [])]
            #: a returned word not in the candidate list cannot carry mass
            inlist = [w for w in got if w in MASS[p]]
            bad += len(got) - len(inlist)
            if not r.any_loaded or not inlist:
                empty += 1
            nw.append(len(inlist))
            g, h = set(inlist), tagged[p] & set(MASS[p])
            if h:
                rec.append(len(g & h) / len(h))
            if g:
                prec.append(len(g & h) / len(g))
            hm.append(sum(MASS[p].get(w, 0) for w in h) / tot[p])
            mm.append(sum(MASS[p].get(w, 0) for w in g) / tot[p])
        r_ = float(np.corrcoef(hm, mm)[0, 1]) if len(hm) > 3 else float("nan")
        print("%-4s %8.3f %8.3f %8.3f %7.0f%% %8.1f   %d errors, %d off-list words"
              % (key, float(np.mean(rec)) if rec else float("nan"),
                 float(np.mean(prec)) if prec else float("nan"), r_,
                 100.0 * empty / max(1, len(pool)),
                 float(np.mean(nw)) if nw else 0, len(errs), bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
