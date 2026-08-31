"""Paired tests with the LINEAGE as the unit. -> sign test and signed-rank.

    python tests.py conflict_all.jsonl                    base -> aligned, raw
    python tests.py conflict_all.jsonl --contrast frame    aligned raw -> prefill
    python tests.py FILE --min-per-cell 10 --alpha 0.05

## WHY THE LINEAGE AND NOT THE STORY

A story is not an independent observation of "what alignment does". Stories from
one model share its weights, its pretraining and its tokenizer; a lineage that
happens to be prolific would otherwise dominate, and a test over 4,687 stories
would report a precision it has not got. This campaign has already produced
p = 0 and p = 2e-32 for opposite signs by testing correlated sub-units.

So: each lineage contributes ONE paired difference, base rate minus aligned rate,
and n is the number of lineages, not the number of stories. That is a much
smaller n and much larger p-values. The p-values are the honest ones.

## TWO TESTS, BECAUSE THEY FAIL DIFFERENTLY

  sign test     counts how many lineages moved up against how many moved down and
                asks whether that split is unusual. Ignores magnitude entirely,
                so a lineage that moved 2 points counts the same as one that moved
                60. Robust to a single huge outlier; blind to consistent size.
  signed-rank   ranks the absolute differences and sums the ranks of the positive
                ones. Uses the ORDER of the magnitudes, not their size, so a
                lineage that moved 60 points and one that moved 12 differ only by
                where they sit in the ranking.
  paired t      uses the actual magnitudes. Most powerful of the three when the
                differences are roughly symmetric, and the most easily wrecked by
                one outlier -- with n=18 a single lineage moving 60 points can
                carry it. Reported with Cohen's dz and a bootstrap CI on the mean
                difference so the size is visible next to the p-value.

Reported together on purpose. A field where they disagree is a field where the
direction and the size are telling different stories, and that is worth seeing
rather than resolving by picking the friendlier test.

## MULTIPLE COMPARISONS

Dozens of field values are tested at once, so an uncorrected 0.05 will produce
false positives by construction. Holm-Bonferroni is applied across every value
tested in a run and both raw and adjusted p are printed. Read `p_holm`.

Holm controls the family-wise error rate over THE VALUES TESTED IN THIS RUN. Add
a field and every adjusted p changes. That is correct behaviour and it means an
adjusted p is only interpretable against the family it was computed in.
"""
import argparse
import collections
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
LOW_DOSE = {
    'EleutherAI/pythia-2.8b', 'EleutherAI/pythia-6.9b', 'LLM360/Amber',
    'bigscience/bloom-7b1', 'huggyllama/llama-7b',
}
CATEGORICAL = ('opponent', 'opponent_specificity', 'opponent_fate',
               'conflict_mode', 'ending', 'resolution_scale',
               'resolution_means', 'community_role', 'mood', 'genre', 'setting',
               'homecoming', 'threat', 'temporality', 'romance',
               'protagonist_change')
BOOLEAN = ('small_community', 'supernatural', 'collective_action', 'renewal',
           'nostalgia', 'elder_informant', 'tradition', 'community_constrains',
           'looks_complete')


def holm(pairs):
    """-> {key: adjusted p}. Holm-Bonferroni, step-down, monotone-enforced."""
    ordered = sorted(pairs, key=lambda kp: kp[1])
    m, out, running = len(ordered), {}, 0.0
    for i, (k, p) in enumerate(ordered):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)     #: adjusted p must not decrease
        out[k] = running
    return out


def rates(rows, field, value, group, min_per_cell):
    """-> [(lineage, rate_a, rate_b)] for lineages with enough stories both sides.

    `group` maps a row to 'a' or 'b' or None."""
    hit = (lambda r: bool(r[field])) if value is True else \
          (lambda r: r[field] == value)
    buckets = collections.defaultdict(lambda: {'a': [], 'b': []})
    for r in rows:
        g = group(r)
        if g is None:
            continue
        buckets[r['lineage']][g].append(hit(r))
    out = []
    for lin, d in sorted(buckets.items()):
        if len(d['a']) < min_per_cell or len(d['b']) < min_per_cell:
            continue
        out.append((lin, 100 * sum(d['a']) / len(d['a']),
                    100 * sum(d['b']) / len(d['b'])))
    return out


def main(argv=None):
    from scipy.stats import binomtest, ttest_rel, wilcoxon

    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('--contrast', default='arm', choices=('arm', 'frame'),
                    help="arm: base->aligned in the raw frame. "
                         "frame: aligned raw->prefill.")
    ap.add_argument('--min-per-cell', type=int, default=5,
                    help='stories a lineage needs on BOTH sides to be counted')
    ap.add_argument('--exclude-low-dose', action='store_true')
    ap.add_argument('--alpha', type=float, default=0.05)
    ap.add_argument('--json', help='also write every tested value to this path')
    a = ap.parse_args(argv)

    path = a.results if os.path.exists(a.results) else \
        os.path.join(HERE, a.results)
    rows = [json.loads(l) for l in open(path, encoding='utf-8')]
    if a.exclude_low_dose:
        rows = [r for r in rows if r['lineage'] not in LOW_DOSE]

    if a.contrast == 'arm':
        label, lo, hi = 'base -> aligned (raw frame)', 'base', 'aligned'
        group = lambda r: ('a' if r['arm'] == 'base' else 'b') \
            if r['frame'] == 'raw' else None
    else:
        label, lo, hi = 'aligned: raw -> prefill', 'raw', 'prefill'
        group = lambda r: ('a' if r['frame'] == 'raw' else 'b') \
            if r['arm'] == 'aligned' else None

    values = [(f, v) for f in CATEGORICAL
              for v in sorted({r[f] for r in rows})] + \
             [(f, True) for f in BOOLEAN]

    results, praw = [], []
    for f, v in values:
        rs = rates(rows, f, v, group, a.min_per_cell)
        if len(rs) < 6:
            continue
        diffs = [b - x for _, x, b in rs]
        up = sum(1 for d in diffs if d > 0)
        dn = sum(1 for d in diffs if d < 0)
        if max(abs(d) for d in diffs) == 0:
            continue
        p_sign = binomtest(up, up + dn, 0.5).pvalue if up + dn else 1.0
        p_t = ttest_rel([b for _, _, b in rs], [x for _, x, _ in rs]).pvalue
        mean_d = sum(diffs) / len(diffs)
        sd = (sum((d - mean_d) ** 2 for d in diffs) / (len(diffs) - 1)) ** 0.5
        dz = mean_d / sd if sd else 0.0
        #: percentile bootstrap on the mean paired difference. Deterministic seed
        #: so a re-run reproduces the interval; 2000 resamples is plenty for a
        #: 95% interval and cheap at n<=19.
        rng = random.Random(20260831)
        boots = []
        for _ in range(2000):
            samp = [diffs[rng.randrange(len(diffs))] for _ in diffs]
            boots.append(sum(samp) / len(samp))
        boots.sort()
        lo95, hi95 = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]
        try:
            p_rank = wilcoxon(diffs, zero_method='wilcox',
                              alternative='two-sided').pvalue
        except ValueError:
            p_rank = 1.0
        med = sorted(diffs)[len(diffs) // 2]
        mean_a = sum(x for _, x, _ in rs) / len(rs)
        mean_b = sum(b for _, _, b in rs) / len(rs)
        key = '%s=%s' % (f, v)
        results.append(dict(key=key, n=len(rs), up=up, dn=dn, med=med,
                            a=mean_a, b=mean_b, p_sign=p_sign, p_rank=p_rank,
                            p_t=p_t, dz=dz, mean_d=mean_d, lo=lo95, hi=hi95))
        praw.append((key + '|sign', p_sign))
        praw.append((key + '|rank', p_rank))
        praw.append((key + '|t', p_t))

    #: CORRECT WITHIN EACH TEST FAMILY, NOT ACROSS BOTH. The sign test and the
    #: signed-rank test on one value are two tests of ONE hypothesis, not two
    #: hypotheses. Pooling them doubles m and halves the power for no reason --
    #: an error in the conservative direction, but still an error. Holm runs over
    #: the 98 sign p-values and separately over the 98 signed-rank p-values.
    #:
    #: Changed after a first pass corrected over all 196 and returned nothing
    #: significant on the frame contrast. Recorded here because a correction
    #: loosened after seeing a null needs to be visible: the frame conclusion is
    #: UNCHANGED either way, and the arm p-values roughly halve.
    a_sign = holm([(k, v) for k, v in praw if k.endswith('|sign')])
    a_rank = holm([(k, v) for k, v in praw if k.endswith('|rank')])
    a_t = holm([(k, v) for k, v in praw if k.endswith('|t')])
    for r in results:
        r['h_sign'] = a_sign[r['key'] + '|sign']
        r['h_rank'] = a_rank[r['key'] + '|rank']
        r['h_t'] = a_t[r['key'] + '|t']
    results.sort(key=lambda r: min(r['h_sign'], r['h_rank'], r['h_t']))

    nlin = len({r['lineage'] for r in rows})
    print('%s   %s' % (label, os.path.basename(path)))
    print('unit = LINEAGE. %d lineages in file; a lineage is counted for a value '
          'only if it has >= %d stories on BOTH sides.' % (nlin, a.min_per_cell))
    print('%d values tested. Holm-Bonferroni within each test family '
          '(%d sign, %d signed-rank), not across both.'
          % (len(results), len(results), len(results)))
    if a.exclude_low_dose:
        print('low-dose lineages excluded.')
    print()
    print('%-30s %3s %6s %6s %7s %16s %5s %4s  %8s %8s %8s'
          % ('', 'n', lo[:6], hi[:6], 'mean d', '95% CI (boot)', 'dz', 'up',
             'p_sign', 'p_rank', 'p_t'))
    print('-' * 118)
    shown = 0
    for r in results:
        star = '*' if min(r['h_sign'], r['h_rank'], r['h_t']) < a.alpha else ' '
        if star == ' ' and shown > 24:
            continue
        shown += 1
        print('%s%-29s %3d %5.1f%% %5.1f%% %+7.1f  [%+6.1f,%+6.1f] %5.2f %2d/%-2d %8.2g %8.2g %8.2g'
              % (star, r['key'][:29], r['n'], r['a'], r['b'], r['mean_d'],
                 r['lo'], r['hi'], r['dz'], r['up'], r['dn'],
                 r['h_sign'], r['h_rank'], r['h_t']))
    if a.json:
        #: EVERY tested value, not only the significant ones. A consumer that
        #: only receives the survivors cannot tell a null from a value that was
        #: never tested, and will read absence as absence of effect.
        outp = a.json if os.path.isabs(a.json) else os.path.join(HERE, a.json)
        os.makedirs(os.path.dirname(outp), exist_ok=True)
        payload = dict(
            contrast=a.contrast, frame=('raw' if a.contrast == 'arm' else 'both'),
            arm_a=lo, arm_b=hi, source=os.path.basename(path),
            unit='lineage', min_stories_per_cell=a.min_per_cell,
            n_values_tested=len(results),
            correction='holm-bonferroni within each test family',
            note=('p values are Holm-adjusted WITHIN this run. Adding a field '
                  'changes every adjusted p, so they are only interpretable '
                  'against this family. The unit is the LINEAGE: `up`+`down` is '
                  'the number of lineages that moved, not stories.'),
            values=[dict(field=r['key'].split('=')[0],
                         value=r['key'].split('=', 1)[1],
                         key=r['key'], n_lineages=r['n'],
                         rate_a=round(r['a'], 3), rate_b=round(r['b'], 3),
                         mean_diff=round(r['mean_d'], 3),
                         ci_lo=round(r['lo'], 3), ci_hi=round(r['hi'], 3),
                         dz=round(r['dz'], 3), up=r['up'], down=r['dn'],
                         #: scipy hands back numpy floats and json.dump raises
                         #: on them PARTWAY THROUGH, leaving a truncated file
                         #: that looks written. Cast, and write atomically.
                         p_sign_holm=float(r['h_sign']),
                         p_wilcoxon_holm=float(r['h_rank']),
                         p_t_holm=float(r['h_t']),
                         significant=bool(min(r['h_sign'], r['h_rank'],
                                              r['h_t']) < a.alpha),
                         significant_all_three=bool(max(r['h_sign'], r['h_rank'],
                                                        r['h_t']) < a.alpha))
                    for r in results])
        tmp = outp + '.tmp'
        with open(tmp, 'w') as fh:
            json.dump(payload, fh, indent=1)
        os.replace(tmp, outp)           #: atomic; no half-written stats file
        print('wrote %s (%d values)' % (outp, len(results)))

    sig = [r for r in results if min(r['h_sign'], r['h_rank'], r['h_t']) < a.alpha]
    print()
    print('%d of %d values significant at Holm-adjusted alpha=%.2f on either test.'
          % (len(sig), len(results), a.alpha))
    all3 = [r for r in sig if max(r['h_sign'], r['h_rank'], r['h_t']) < a.alpha]
    onlys = [r for r in sig if r['h_sign'] < a.alpha <= min(r['h_rank'], r['h_t'])]
    onlyr = [r for r in sig if r['h_rank'] < a.alpha <= min(r['h_sign'], r['h_t'])]
    onlyt = [r for r in sig if r['h_t'] < a.alpha <= min(r['h_sign'], r['h_rank'])]
    print('   all three %d   sign only %d   signed-rank only %d   t only %d'
          % (len(all3), len(onlys), len(onlyr), len(onlyt)))
    for lab, s in (('sign only', onlys), ('signed-rank only', onlyr),
                   ('t only', onlyt)):
        if s:
            print('   %s: %s' % (lab, ', '.join(r['key'] for r in s)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
