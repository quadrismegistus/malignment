"""One schema over every stats file the panels read. -> results/panel_stats.json

    python panel_stats.py

Three emitters grew independently and produced three shapes: `rate_a`/`rate_b`
with no per-lineage values, `base`/`aligned` with per-lineage PAIRS, and `median`
with per-lineage DELTAS. A consumer needed three parsers to draw one kind of
chart. This reads all three and writes one array.

## THE ONE DIFFERENCE THAT CANNOT BE NORMALISED AWAY

`per_lineage_kind` is `pair` or `delta`, and the distinction is real:

    pair    [base_value, aligned_value] for that lineage. A slopegraph can draw
            both endpoints.
    delta   ONE number, the lineage's median over its prompts of
            (aligned - base). There is no pair to recover, because a median of
            paired differences is NOT the difference of two medians -- computing
            median(base) and median(aligned) separately would answer a different
            question and would not be the number that was tested.

So norm_change rows can be drawn as a dot-and-interval or a distribution of
deltas, and CANNOT be drawn as a two-endpoint slopegraph without changing what
is plotted. A panel that puts them on one axis with the pair-valued rows is
mixing two quantities.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SOURCES = [
    ('annotation', 'arm', os.path.join(HERE, 'results/annotation_stats_arm.json')),
    ('annotation', 'frame', os.path.join(HERE, 'results/annotation_stats_frame.json')),
    ('fields', 'arm', os.path.join(HERE, 'results/fields_stats.json')),
    ('norms', 'arm', os.path.join(ROOT, 'experiments/displacement/norm_change/'
                                        'results/norm_stats.json')),
]


def main():
    out = []
    for family, contrast, path in SOURCES:
        if not os.path.exists(path):
            print('  MISSING %s' % path)
            continue
        d = json.load(open(path))
        for r in d['values']:
            if family == 'annotation':
                rec = dict(id='%s|%s|%s' % (family, contrast, r['key']),
                           group=r['field'], label=r['value'],
                           a=r['rate_a'], b=r['rate_b'], units='percent',
                           effect=r['mean_diff'], effect_kind='mean_diff',
                           ci=[r['ci_lo'], r['ci_hi']], dz=r['dz'],
                           n_lineages=r['n_lineages'], up=r['up'], down=r['down'],
                           ties=r['n_lineages'] - r['up'] - r['down'],
                           h_sign=r['p_sign_holm'], h_wilcoxon=r['p_wilcoxon_holm'],
                           h_t=r['p_t_holm'], per_lineage=None,
                           per_lineage_kind=None, declared=None)
            elif family == 'fields':
                rec = dict(id='%s|%s|%s' % (family, contrast, r['scale']),
                           group=r['kind'], label=r['scale'],
                           a=r['base'], b=r['aligned'], units='share_or_scale',
                           effect=r['mean_diff'], effect_kind='mean_diff',
                           ci=None, dz=r['dz'],
                           n_lineages=r['n_lineages'], up=r['up'], down=r['down'],
                           ties=r['ties'],
                           h_sign=r['h_sign'], h_wilcoxon=r['h_wilcoxon'],
                           h_t=r['h_t'], per_lineage=r['per_lineage'],
                           per_lineage_kind='pair', declared=None,
                           ratio=r['ratio'])
            else:
                rec = dict(id='%s|%s|%s|%s|%s' % (family, contrast, r['lang'],
                                                  r['table'], r['scale']),
                           group='%s / %s / %s' % (r['lang'], r['table'],
                                                   'declared' if r['declared']
                                                   else 'exploratory'),
                           label=r['scale'],
                           a=None, b=None, units='norm_delta',
                           effect=r['median'], effect_kind='median_of_deltas',
                           ci=None, dz=None,
                           n_lineages=r['n_lineages'], up=r['up'], down=r['down'],
                           ties=r['ties'],
                           h_sign=r['p_holm'], h_wilcoxon=None, h_t=None,
                           per_lineage=r['per_lineage'],
                           per_lineage_kind='delta', declared=r['declared'],
                           hypothesis=r['hypothesis'], lang=r['lang'],
                           effective_n=r['effective_n'])
            ps = [p for p in (rec['h_sign'], rec['h_wilcoxon'], rec['h_t'])
                  if p is not None]
            rec['family'] = family
            rec['contrast'] = contrast
            rec['significant'] = bool(min(ps) < 0.05) if ps else False
            rec['significant_all'] = bool(max(ps) < 0.05) if len(ps) > 1 else None
            out.append(rec)
        print('  %-12s %-6s %5d rows' % (family, contrast, len(d['values'])))

    p = os.path.join(HERE, 'results/panel_stats.json')
    tmp = p + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(dict(
            schema_version=1,
            note=('one row per tested quantity. per_lineage_kind is `pair` '
                  '[base, aligned] or `delta` (a median of paired differences, '
                  'which CANNOT be split into two endpoints). Rows with '
                  'per_lineage=None have no per-lineage values in their source.'),
            families={'annotation': 'story_conflict_v1 annotation rates',
                      'fields': 'word norms and USAS/RID field shares',
                      'norms': 'norm_change, 50 endpoint pairs, two languages'},
            n_rows=len(out), values=out), fh)
    os.replace(tmp, p)
    print('\nwrote %s  (%d rows, %.1f MB)' % (p, len(out), os.path.getsize(p) / 1e6))
    for k in ('pair', 'delta', None):
        n = sum(1 for r in out if r['per_lineage_kind'] == k)
        print('   per_lineage_kind %-6s %5d rows' % (str(k), n))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
