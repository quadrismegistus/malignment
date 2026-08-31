"""Variance decomposed FIELD BY FIELD: within, between, overall, demonym share.

    python field_variance.py conflict_nocap.jsonl
    python field_variance.py FILE --contrast frame

## THE MEASURE

For a single field, mean pairwise Hamming distance is just the probability that
two randomly drawn stories give DIFFERENT answers -- the Gini-Simpson diversity,
1 - sum(p_i^2). One number per field, bounded [0,1), 0 when every story answers
the same way.

    within    P(two SAME-demonym stories differ)
    between   P(two DIFFERENT-demonym stories differ)
    overall   P(any two differ)
    share     (between - within) / overall, the part attributable to nationality

## WHY PER FIELD AND NOT PER GROUP

The WORLD/OUTCOME split was mine, and grouping hides two things. It hides which
individual fields carry a group's effect -- and it hides that the OUTCOME fields
are not independent: 64% of base stories sit at the null on
resolution_means, resolution_scale AND protagonist_change simultaneously, so a
group mean over ten coupled fields counts one fact repeatedly. Per field, a
reader can see the coupling for themselves and weight accordingly.

Equal stories per demonym per arm, resampled, so no nationality dominates and
both arms are measured identically.
"""
import argparse
import collections
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ('mood', 'setting', 'genre', 'temporality', 'opponent',
          'opponent_specificity', 'threat', 'romance', 'small_community',
          'supernatural', 'tradition', 'nostalgia', 'elder_informant',
          'community_constrains', 'opponent_fate', 'conflict_mode', 'ending',
          'resolution_scale', 'resolution_means', 'protagonist_change',
          'community_role', 'collective_action', 'renewal', 'homecoming')
WORLD = set(FIELDS[:14])


def decompose(by_dem, f):
    """-> (within, between, overall) for ONE field."""
    dems = sorted(by_dem)
    wn = wd = bn = bd = 0
    allr = [r for g in by_dem.values() for r in g]
    for i, da in enumerate(dems):
        A = by_dem[da]
        for x in range(len(A)):
            for y in range(x + 1, len(A)):
                wd += A[x][f] != A[y][f]; wn += 1
        for db in dems[i + 1:]:
            for ra in A:
                for rb in by_dem[db]:
                    bd += ra[f] != rb[f]; bn += 1
    od = on = 0
    for i in range(len(allr)):
        for j in range(i + 1, len(allr)):
            od += allr[i][f] != allr[j][f]; on += 1
    if not wn or not bn or not on:
        return None
    return wd / wn, bd / bn, od / on


def main(argv=None):
    from scipy.stats import wilcoxon

    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('--contrast', default='arm', choices=('arm', 'frame'))
    ap.add_argument('--per-demonym', type=int, default=3)
    ap.add_argument('--min-demonyms', type=int, default=4)
    ap.add_argument('--draws', type=int, default=300)
    a = ap.parse_args(argv)

    path = a.results if os.path.exists(a.results) else \
        os.path.join(HERE, a.results)
    rows = [json.loads(l) for l in open(path, encoding='utf-8')]
    if a.contrast == 'arm':
        la, lb = 'base', 'aligned'
        pa = lambda r: r['arm'] == 'base' and r['frame'] == 'raw'
        pb = lambda r: r['arm'] == 'aligned' and r['frame'] == 'raw'
    else:
        la, lb = 'raw', 'prefill'
        pa = lambda r: r['arm'] == 'aligned' and r['frame'] == 'raw'
        pb = lambda r: r['arm'] == 'aligned' and r['frame'] == 'prefill'
    cells = collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict(list)))
    for r in rows:
        g = 'a' if pa(r) else ('b' if pb(r) else None)
        if g:
            cells[r['lineage']][g][r['demonym']].append(r)

    rng = random.Random(20260901)
    acc = {f: {'a': [[], [], []], 'b': [[], [], []]} for f in FIELDS}
    nlin = 0
    for lin, d in sorted(cells.items()):
        if 'a' not in d or 'b' not in d:
            continue
        dems = [x for x in sorted(set(d['a']) & set(d['b']))
                if len(d['a'][x]) >= a.per_demonym
                and len(d['b'][x]) >= a.per_demonym]
        if len(dems) < a.min_demonyms:
            continue
        nlin += 1
        tot = {f: {'a': [0.0] * 3, 'b': [0.0] * 3} for f in FIELDS}
        for _ in range(a.draws):
            sub = {g: {x: rng.sample(d[g][x], a.per_demonym) for x in dems}
                   for g in ('a', 'b')}
            for f in FIELDS:
                for g in ('a', 'b'):
                    v = decompose(sub[g], f)
                    for j in range(3):
                        tot[f][g][j] += v[j]
        for f in FIELDS:
            for g in ('a', 'b'):
                for j in range(3):
                    acc[f][g][j].append(tot[f][g][j] / a.draws)

    print('PER-FIELD VARIANCE DECOMPOSITION  --  %s -> %s' % (la, lb))
    print('%d lineages, %d stories per demonym, %d draws. Diversity = P(two '
          'stories differ).' % (nlin, a.per_demonym, a.draws))
    print()
    print('%-22s %s %s %s' % ('', '   OVERALL diversity  ',
                              '  WITHIN demonym  ', ' DEMONYM SHARE'))
    print('%-22s %6s %6s %7s %5s %6s %6s %7s %6s %6s'
          % ('field', la[:6], lb[:6], '%chg', 'u/d', la[:6], lb[:6], '%chg',
             la[:6], lb[:6]))
    print('-' * 96)
    out = []
    for f in FIELDS:
        A, B = acc[f]['a'], acc[f]['b']
        n = len(A[0])
        if not n:
            continue
        ov_a, ov_b = sum(A[2]) / n, sum(B[2]) / n
        wi_a, wi_b = sum(A[0]) / n, sum(B[0]) / n
        sh_a = sum((b - w) / t if t else 0
                   for w, b, t in zip(A[0], A[1], A[2])) / n
        sh_b = sum((b - w) / t if t else 0
                   for w, b, t in zip(B[0], B[1], B[2])) / n
        d = [y - x for x, y in zip(A[2], B[2])]
        up = sum(1 for x in d if x > 0); dn = sum(1 for x in d if x < 0)
        p = wilcoxon(d).pvalue if n > 5 and any(d) else float('nan')
        out.append((ov_b - ov_a, f, ov_a, ov_b, wi_a, wi_b, sh_a, sh_b, up, dn, p))
    for _, f, oa, ob, wa, wb, sa, sb, up, dn, p in sorted(out):
        star = '*' if p == p and p < 0.05 else ' '
        print('%s%-21s %6.3f %6.3f %+6.1f%% %2d/%-2d %6.3f %6.3f %+6.1f%% %5.1f%% %5.1f%%%s'
              % ('W' if f in WORLD else 'O', f, oa, ob,
                 100 * (ob - oa) / oa if oa else 0, up, dn, wa, wb,
                 100 * (wb - wa) / wa if wa else 0, 100 * sa, 100 * sb, star))
    print()
    print('W = world field, O = outcome field. * = overall change significant '
          'at p_wilcoxon < 0.05')
    print('u/d = lineages where overall diversity rose / fell.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
