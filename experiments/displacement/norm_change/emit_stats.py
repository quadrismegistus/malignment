"""Per-scale stats and per-lineage values as JSON, for the web panel.

    python emit_stats.py                    -> results/norm_stats.json
    python emit_stats.py --min-effective 10

Reuses analyse.py's accumulator and its per-lineage medians, so this cannot
disagree with the printed report: same stream, same unit, same tie rule.

## FOUR THINGS A CONSUMER MUST NOT FLATTEN

**DECLARED IS NOT EXPLORATORY.** Seven hypotheses are pre-registered in
`registration.md` with a DIRECTION. Everything else is exploratory and, in the
report's own words, "NOT a headline without a re-test". Sorting all of them into
one list by p-value presents a scale nobody predicted with the same authority as
one that was. `declared` and `hypothesis` are on every row so a panel can
separate them; they should be separate facets, not one sorted column.

**HOLM IS APPLIED WITHIN FAMILY, NOT ACROSS.** The declared seven are corrected
among themselves and the exploratory scales among themselves, separately per
(language, table). Correcting a registered hypothesis against forty scales nobody
predicted would penalise it for their existence.

**LANGUAGES ARE NEVER POOLED.** en and zh are separate rows and separate
populations. The headline result of this experiment is that concreteness falls in
Chinese ONLY, which a pooled panel would erase.

**TIES ARE THE STORY ON SOME SCALES.** The test excludes ties and `n` is not the
number of lineages that moved. A sparse field carries no mass in either arm, so
its delta is exactly zero for most lineages; `effective_n` (up+down) is what the
p-value rests on and can be a small fraction of `n_lineages`. A panel showing
n=50 for a scale with effective_n=9 is claiming evidence it does not have.

The test is a two-sided SIGN test, not Wilcoxon. There is no signed-rank or
paired-t here because the per-lineage value is already a median over prompts.
"""
import argparse
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse


def holm(pairs):
    ordered = sorted(pairs, key=lambda kp: kp[1])
    m, out, run = len(ordered), {}, 0.0
    for i, (k, p) in enumerate(ordered):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-effective", type=int, default=5,
                    help="drop scales with fewer than this many non-tied lineages")
    ap.add_argument("--out", default="results/norm_stats.json")
    a = ap.parse_args(argv)

    acc = {}
    for name in ("levels", "fields", "contextual"):
        t = analyse.stream(name, None)          #: None = every scale, not just declared
        acc[name] = t if t is not None else {}
        print("  %-12s %s" % (name, "%d cells" % len(acc[name]) if t else "absent"))

    declared = {}
    for hid, direction, scales, tbl in analyse.DECLARED:
        for s in (scales if tbl == "contextual" else analyse._with_z(scales)):
            declared[(tbl, s)] = (hid, direction)

    rows = []
    for tbl, cells in acc.items():
        for lang in ("en", "zh"):
            scales = sorted({k[1] for k in cells if k[0] == lang})
            for sc in scales:
                d = analyse.per_lineage(cells, lang, sc)
                if not d:
                    continue
                v = list(d.values())
                up = sum(1 for x in v if x > 0)
                dn = sum(1 for x in v if x < 0)
                eff = up + dn
                if eff < a.min_effective:
                    continue
                #: contextual keys scales as `<instrument>:<scale>`; match the
                #: bare name against DECLARED the way analyse.py does
                key = (tbl, sc.split(":")[-1] if tbl == "contextual" else sc)
                hid, direction = declared.get(key, (None, None))
                rows.append(dict(
                    table=tbl, lang=lang, scale=sc,
                    hypothesis=hid, declared=hid is not None, direction=direction,
                    n_lineages=len(v), up=up, down=dn, ties=len(v) - eff,
                    effective_n=eff,
                    median=st.median(v),
                    median_nonzero=(st.median([x for x in v if x]) if eff else 0.0),
                    p_sign=analyse.binom(up, eff),
                    per_lineage={k: round(x, 6) for k, x in sorted(d.items())}))

    #: Holm within (declared|exploratory) x language x table -- never across
    fams = {}
    for r in rows:
        fams.setdefault(('declared' if r['declared'] else 'exploratory',
                         r['lang'], r['table']), []).append(r)
    for fam, rs in fams.items():
        adj = holm([(r['scale'], r['p_sign']) for r in rs])
        for r in rs:
            r['p_holm'] = adj[r['scale']]
            r['holm_family'] = '%s / %s / %s' % fam
            r['holm_family_size'] = len(rs)

    outp = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    payload = dict(
        experiment='norm_change', unit='lineage',
        test='two-sided sign test over lineages, TIES EXCLUDED',
        per_lineage_value='median over that lineage prompts of (aligned - base)',
        correction='holm-bonferroni within declared|exploratory x lang x table',
        warnings=[
            'declared and exploratory are different evidential classes; do not '
            'sort them into one list',
            'en and zh are separate populations and are never pooled',
            'effective_n = up+down is what the p-value rests on; n_lineages '
            'includes ties and can be much larger',
            'the three tables have different prompt populations',
        ],
        n_rows=len(rows), values=rows)
    tmp = outp + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(payload, fh)
    os.replace(tmp, outp)
    print('wrote %s  (%d scales, %.1f MB)'
          % (outp, len(rows), os.path.getsize(outp) / 1e6))
    for fam, rs in sorted(fams.items()):
        sig = sum(1 for r in rs if r['p_holm'] < 0.05)
        print('   %-34s %3d scales, %2d at holm p<0.05' % ('%s/%s/%s' % fam, len(rs), sig))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
