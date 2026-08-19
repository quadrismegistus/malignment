"""The institutional instrument over EVERY slot frame of a domain.

    python run_slotdomain.py --domain institutional          # 62 frames
    python run_slotdomain.py --domain institutional --dry

`run_slotpov.py` covers the 6 institutional frames that carry a `matched_set`
perspective pair. The other 56 have no POV structure at all, so this is a
MAIN-EFFECT run on an independent population -- not another position test.

Worth having because the position asymmetry turned out to be one collinear
cluster (agency/specificity/assertiveness/arousal, pairwise 0.62-0.83) and is
absent from M03 arm A entirely. The main effects -- `termination`, `mediation`,
`abstraction`, `procedural`, `deference` -- are what replicate, and they have
been measured on 252 M03 prompts, 24 F21 prompts and 12 slot prompts. These 62
are a fourth population with a different prompt shape again: short slot frames,
author-declared naughty/nice poles, no speaker contrast.

Movement is computed with `movement.movement()` over `twp_words_v4_best`, pairs
and residuals from pilot3's cells -- the same path `run.py` and `run_slotpov.py`
use. Two arms, never pooled.
"""

import argparse, collections, json, os, sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
RESULTS = os.path.join(HERE, "results", "slotdomain")
from run_slotpov import population, CELLS      # same gating, same source


def frames(domain):
    import yaml
    out = []
    repo = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
    for f in ("round3.yaml", "slot-explorer.yaml", "slot-client.yaml"):
        p = os.path.join(repo, "roster", "prompts", "slots", f)
        if not os.path.exists(p):
            continue
        for it in (yaml.safe_load(open(p, encoding="utf-8")) or []):
            if isinstance(it, dict) and it.get("prompt") and it.get("domain") == domain:
                out.append(it)
    seen, uniq = set(), []
    for i in out:
        if i["prompt"] not in seen:
            seen.add(i["prompt"]); uniq.append(i)
    return uniq


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="institutional")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    fs = frames(a.domain)
    ps = [i["prompt"] for i in fs]
    print("%s: %d slot frames" % (a.domain, len(fs)))
    pops = {arm: population(ps, arm=arm) for arm in ("A", "B")}
    for arm in "AB":
        n = sum(len(pops[arm][p]["words"]) for p in ps)
        cov = sum(1 for p in ps if pops[arm][p]["verdicts"])
        print("  arm %s: %d words over %d frames with pairs" % (arm, n, cov))
    if a.dry:
        return

    os.environ.setdefault("INST_V3", "1")
    from task import (InstitutionalSupplementENv3 as T, SCALES_INST_V3 as SCALES,
                      render)
    from scipy import stats
    task = T()
    os.makedirs(RESULTS, exist_ok=True)
    for arm in ("A", "B"):
        jobs = [(p, w) for p in ps for w in pops[arm][p]["words"]]
        if not jobs:
            continue
        errs = {}
        res = task.map([render(p, w) for p, w in jobs],
                       metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                       num_workers=32, errors=errs)
        rat = collections.defaultdict(dict)
        for (p, w), r in zip(jobs, res):
            if r is not None and r.ratable:
                rat[p][w] = {s: getattr(r, s) for s in SCALES}
        print("\narm %s: %d words rated, errors %d" % (arm, len(jobs), len(errs)))
        json.dump({"domain": a.domain, "arm": arm, "instrument": task.name,
                   "frames": [dict(i, ratings=rat.get(i["prompt"], {})) for i in fs]},
                  open(os.path.join(RESULTS, "rated_%s_%s_arm%s.json"
                                    % (a.domain, task.name, arm)), "w"), indent=1)
        per = collections.defaultdict(lambda: collections.defaultdict(list))
        for p in ps:
            for pk, vd in pops[arm][p]["verdicts"].items():
                if arm == "A":
                    e = [w for w in rat.get(p, {}) if w in vd]
                    if len(e) < 10:
                        continue
                    mv = [vd[w] for w in e]
                    if len(set(mv)) < 2:
                        continue
                    for s in SCALES:
                        xs = [rat[p][w][s] for w in e]
                        if len(set(xs)) < 2:
                            continue
                        r = stats.spearmanr(xs, mv).correlation
                        if r == r:
                            per[pk][s].append(r)
                else:
                    ris = [w for w in rat.get(p, {}) if vd.get(w) == 1]
                    sti = [w for w in rat.get(p, {}) if vd.get(w) == 0]
                    if len(ris) < 2 or len(sti) < 2:
                        continue
                    for s in SCALES:
                        per[pk][s].append(st.mean(rat[p][w][s] for w in ris)
                                          - st.mean(rat[p][w][s] for w in sti))
        print("  MAIN EFFECT, unit = lineage  (%s)"
              % ("rho vs signed verdict" if arm == "A" else "mean(riser) - mean(still)"))
        print("  %-14s %9s %9s %11s" % ("scale", "stat", "lin up", "wilcoxon"))
        rows = []
        for s in SCALES:
            v = [st.mean(per[pk][s]) for pk in per if len(per[pk][s]) >= 3]
            if len(v) < 8:
                print("  %-14s (only %d lineages)" % (s, len(v))); continue
            p_ = stats.wilcoxon(v).pvalue
            rows.append((abs(st.median(v)), s, st.median(v), sum(1 for x in v if x > 0),
                         len(v), p_))
        for _, s, m, u, n, p_ in sorted(rows, reverse=True):
            print("  %-14s %+9.3f %6d/%-3d %11.2g%s"
                  % (s, m, u, n, p_, "*" if p_ < 0.05 else ""))


if __name__ == "__main__":
    main()
