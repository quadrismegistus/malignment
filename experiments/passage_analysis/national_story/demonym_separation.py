"""Does alignment turn every demonym into one story? -> between/within separation.

    python demonym_separation.py conflict_nocap.jsonl
    python demonym_separation.py FILE --per-demonym 4 --draws 300

## WHY POOLED ENTROPY CANNOT ANSWER THIS

Rettberg's homogeneity claim has two halves and they need different instruments:

  1. the Norwegian stories resemble EACH OTHER
  2. the Norwegian stories resemble the TURKISH ones -- every nationality
     collapses into the same story

Pooled entropy over a cell measures 1 and 2 mixed together, and cannot separate
them. A model whose Norwegian and Turkish outputs became indistinguishable while
each stayed internally varied would score UNCHANGED on pooled entropy. That is
exactly the case the claim is about, so the pooled measure is blind where it
matters most.

## THE DECOMPOSITION

Over the annotation fields, for one (lineage, arm):

    within   = mean Hamming distance between two stories of the SAME demonym
    between  = mean Hamming distance between two stories of DIFFERENT demonyms
    separation = between - within

If the demonym carries information, two stories from different nationalities
differ more than two from the same one, so separation > 0. If alignment erases
national difference, separation goes to 0 -- the demonym stops predicting
anything about the annotations, which is claim 2 stated as a number.

Separation is the right quantity rather than `between` alone because a cell that
simply became more varied overall would raise both terms. The difference cancels
that.

## THE SAMPLE-SIZE TRAP, AGAIN

Hamming distances are less n-sensitive than entropy, but the WITHIN term is not:
it is computed over same-demonym pairs, and cells have unequal stories per
demonym. A demonym with 2 stories contributes 1 pair; one with 20 contributes
190, so a cell dominated by one nationality has a `within` that is mostly that
nationality. Both arms are therefore subsampled to the same fixed number of
stories PER DEMONYM, over many draws, so every demonym contributes equally and
both arms are measured identically.

Lineages that cannot supply `--per-demonym` stories for at least 4 demonyms in
BOTH arms are dropped, and there are not many that can.
"""
import argparse
import collections
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
#: generated annotation files live OUTSIDE the checkout, in
#: $MALIGNMENT_DATA/national_story. `resolve` keeps CLI usage identical --
#: `--results conflict_nocap.jsonl` still works -- by looking in the cwd, then
#: the data dir, then here. They were moved out because they are outputs, not
#: source: conflict_nocap.jsonl alone is 30 MB and changes wholesale every run.
DATA = os.path.join(
    os.environ.get('MALIGNMENT_DATA', os.path.expanduser('~/malignment-data')),
    'national_story')


def resolve(name):
    for c in (name, os.path.join(DATA, name), os.path.join(HERE, name)):
        if os.path.exists(c):
            return c
    return os.path.join(DATA, name)

WORLD = ('mood', 'setting', 'genre', 'temporality', 'opponent',
         'opponent_specificity', 'threat', 'romance', 'small_community',
         'supernatural', 'tradition', 'nostalgia', 'elder_informant',
         'community_constrains')
OUTCOME = ('opponent_fate', 'conflict_mode', 'ending', 'resolution_scale',
           'resolution_means', 'protagonist_change', 'community_role',
           'collective_action', 'renewal', 'homecoming')
ALL = WORLD + OUTCOME


def totals(by_dem, fields):
    """-> (within, between, overall) mean Hamming distances.

    `overall` is EVERY pair regardless of demonym, so it is the mix of the other
    two weighted by how many pairs of each kind exist. Reporting all three lets a
    reader see that a fall in `within` and a rise in `between` can leave
    `overall` almost unmoved -- which is the shape of this result and the reason
    a single homogeneity number is uninformative."""
    r = separation(by_dem, fields)
    if r is None:
        return None
    w, b, _ = r
    rows = [x for g in by_dem.values() for x in g]
    tot = pairs = 0
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            tot += sum(1 for f in fields if rows[i][f] != rows[j][f]); pairs += 1
    return w, b, tot / (pairs * len(fields))


def separation(by_dem, fields):
    """-> (within, between, separation) over equal-size demonym groups."""
    dems = sorted(by_dem)
    win = wn = btw = bn = 0
    for i, da in enumerate(dems):
        A = by_dem[da]
        for x in range(len(A)):
            for y in range(x + 1, len(A)):
                win += sum(1 for f in fields if A[x][f] != A[y][f]); wn += 1
        for db in dems[i + 1:]:
            B = by_dem[db]
            for ra in A:
                for rb in B:
                    btw += sum(1 for f in fields if ra[f] != rb[f]); bn += 1
    if not wn or not bn:
        return None
    w = win / (wn * len(fields))
    b = btw / (bn * len(fields))
    return w, b, b - w


def main(argv=None):
    from scipy.stats import binomtest, ttest_rel, wilcoxon

    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('--frame', default='raw', choices=('raw', 'prefill'))
    ap.add_argument('--per-demonym', type=int, default=3,
                    help='stories sampled per demonym per arm')
    ap.add_argument('--min-demonyms', type=int, default=4)
    ap.add_argument('--draws', type=int, default=300)
    ap.add_argument('--contrast', default='arm', choices=('arm', 'frame'),
                    help='arm: base->aligned in raw. frame: aligned raw->prefill.')
    ap.add_argument('--summary', action='store_true',
                    help='compact percent-change table instead of per-lineage')
    a = ap.parse_args(argv)

    path = resolve(a.results)
    rows = [json.loads(l) for l in open(path, encoding='utf-8')
            if json.loads(l)['frame'] == a.frame]
    cells = collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict(list)))
    for r in rows:
        cells[r['lineage']][r['arm']][r['demonym']].append(r)

    rng = random.Random(20260901)
    for glabel, fields in (('ALL FIELDS', ALL), ('WORLD', WORLD),
                           ('OUTCOME', OUTCOME)):
        out = []
        for lin in sorted(cells):
            d = cells[lin]
            if 'base' not in d or 'aligned' not in d:
                continue
            #: a demonym is usable only if BOTH arms can supply the quota
            dems = [x for x in sorted(set(d['base']) & set(d['aligned']))
                    if len(d['base'][x]) >= a.per_demonym
                    and len(d['aligned'][x]) >= a.per_demonym]
            if len(dems) < a.min_demonyms:
                continue
            acc = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
            ok = 0
            for _ in range(a.draws):
                got = []
                for arm in ('base', 'aligned'):
                    sub = {x: rng.sample(d[arm][x], a.per_demonym) for x in dems}
                    got.append(separation(sub, fields))
                if any(g is None for g in got):
                    continue
                for k in (0, 1):
                    for j in (0, 1, 2):
                        acc[k][j] += got[k][j]
                ok += 1
            if not ok:
                continue
            out.append((lin, len(dems),
                        tuple(tuple(v / ok for v in acc[k]) for k in (0, 1))))

        print('=' * 84)
        print('%s -- %d fields, %s frame, %d stories per demonym, %d draws'
              % (glabel, len(fields), a.frame, a.per_demonym, a.draws))
        print('%d lineages with >= %d demonyms in both arms'
              % (len(out), a.min_demonyms))
        print('=' * 84)
        if not out:
            print('  nothing qualifies\n')
            continue
        if glabel == 'ALL FIELDS':
            print('%-34s %4s %17s %17s' % ('lineage', 'dem', 'BASE', 'ALIGNED'))
            print('%-34s %4s %5s %5s %5s %5s %5s %5s'
                  % ('', '', 'with', 'btwn', 'sep', 'with', 'btwn', 'sep'))
            for lin, nd, ((wb, bb, sb), (wa, ba, sa)) in out:
                print('%-34s %4d %5.3f %5.3f %5.3f %5.3f %5.3f %5.3f'
                      % (lin.split('/')[-1][:34], nd, wb, bb, sb, wa, ba, sa))
            print()
        for lab, i in (('WITHIN-demonym distance', 0),
                       ('BETWEEN-demonym distance', 1),
                       ('SEPARATION (between - within)', 2)):
            b = [s[0][i] for _, _, s in out]
            al = [s[1][i] for _, _, s in out]
            diffs = [x - y for x, y in zip(al, b)]
            up = sum(1 for x in diffs if x > 0)
            dn = sum(1 for x in diffs if x < 0)
            md = sum(diffs) / len(diffs)
            sd = (sum((x - md) ** 2 for x in diffs) / (len(diffs) - 1)) ** 0.5 \
                if len(diffs) > 1 else 0
            p_s = binomtest(up, up + dn, 0.5).pvalue if up + dn else 1.0
            p_w = wilcoxon(diffs).pvalue if len(diffs) > 5 else float('nan')
            p_t = ttest_rel(al, b).pvalue if len(diffs) > 1 else float('nan')
            print('  %-30s base %.4f  aligned %.4f  diff %+.4f  dz %+.2f'
                  % (lab, sum(b) / len(b), sum(al) / len(al), md,
                     md / sd if sd else 0))
            print('  %-30s aligned LOWER in %d of %d   p_sign %.3g  p_w %.3g  p_t %.3g'
                  % ('', dn, len(diffs), p_s, p_w, p_t))
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
