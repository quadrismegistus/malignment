"""Is the aligned arm more homogeneous in ANNOTATION space? -> paired tests.

    python homogeneity.py conflict_nocap.jsonl
    python homogeneity.py FILE --within-demonym
    python homogeneity.py FILE --draws 400 --min-per-cell 10

## THE CLAIM

Rettberg reports homogeneity lexically -- stories from one model resemble each
other. This asks the same question in the space the conflict instrument defines:
given the annotations, are aligned stories more alike than base ones?

Two measures, because they can disagree and the disagreement is informative:

  entropy    mean Shannon entropy across the annotation fields, in bits. A field
             where every story answers the same way scores 0. This is CONCENTRATION
             -- it goes down when one value takes over.
  hamming    mean pairwise Hamming distance between stories, over the same fields,
             normalised to [0,1]. This is DISPERSION -- how different two randomly
             drawn stories are, field by field.

They are related but not the same. A cell can concentrate on one value per field
(low entropy) while the fields that remain still separate the stories.

## THE BIAS THAT MAKES THE NAIVE VERSION WRONG

BOTH MEASURES ARE BIASED BY SAMPLE SIZE, AND THE ARMS HAVE DIFFERENT n.

Shannon entropy computed from counts is biased DOWNWARD in small samples: with 5
draws you cannot observe more than 5 distinct values, so a small cell looks more
homogeneous than it is. The base arm is the smaller one here (1291 raw stories
against 1954), so the naive computation would hand back "base is more
homogeneous" as an artifact of having fewer stories -- the exact opposite of the
hypothesis, which is a good way to be wrong in a direction that looks like a
finding.

Fix: for each lineage, subsample BOTH arms to the same n -- the smaller of the
two -- and average over many draws. Equal n, same estimator, same bias on both
sides, so the bias cancels in the paired difference. `--draws` controls how many
resamples; the seed is fixed so a re-run reproduces.

## WITHIN-DEMONYM

`--within-demonym` computes the measures inside each demonym and averages, which
is Rettberg's actual construct: she asks whether the Norwegian stories resemble
each other, not whether Norwegian resembles Turkish. Off by default because it
needs enough stories per demonym per cell and most lineages do not have them.
"""
import argparse
import collections
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
#: THE 24 FIELDS SPLIT INTO TWO GROUPS THAT MOVE IN OPPOSITE DIRECTIONS, and
#: pooling them averages a real effect against its opposite. The split is not by
#: how concentrated the base arm is -- the correlation between base modal share
#: and the entropy gap is only r=+0.24 -- it is by WHAT ALIGNMENT DOES:
#:
#:   WORLD   fields naming what the story IS: its mood, place, period, genre,
#:           who opposes the protagonist. Alignment CONVERGES these on one
#:           answer, so the aligned arm is MORE homogeneous.
#:   OUTCOME fields naming how it RESOLVES. Base stories overwhelmingly do not
#:           resolve at all, so base is concentrated on a single null answer and
#:           alignment, by resolving in several different ways, is MORE varied.
#:
#: Reported separately by default. `--fields all` pools them, which is what the
#: first version of this did and which returns a significant result in the
#: direction of the larger group rather than a meaningful one.
WORLD = ('mood', 'setting', 'genre', 'temporality', 'opponent',
         'opponent_specificity', 'threat', 'romance', 'small_community',
         'supernatural', 'tradition', 'nostalgia', 'elder_informant',
         'community_constrains')
OUTCOME = ('opponent_fate', 'conflict_mode', 'ending', 'resolution_scale',
           'resolution_means', 'protagonist_change', 'community_role',
           'collective_action', 'renewal', 'homecoming')
FIELDS = ('opponent', 'opponent_specificity', 'opponent_fate', 'conflict_mode',
          'ending', 'resolution_scale', 'resolution_means', 'community_role',
          'mood', 'genre', 'setting', 'homecoming', 'threat', 'temporality',
          'romance', 'protagonist_change', 'small_community', 'supernatural',
          'collective_action', 'renewal', 'nostalgia', 'elder_informant',
          'tradition', 'community_constrains')


def entropy(vals):
    """-> Shannon entropy in bits of a list of categorical values."""
    n = len(vals)
    if n < 2:
        return 0.0
    c = collections.Counter(vals)
    return -sum((k / n) * math.log2(k / n) for k in c.values())


def measures(rows):
    """-> (mean entropy in bits, mean normalised pairwise Hamming distance)."""
    ents = [entropy([r[f] for r in rows]) for f in FIELDS]
    #: all pairs is O(n^2) and n is small after subsampling, so no sampling here
    tot = pairs = 0
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            tot += sum(1 for f in FIELDS if a[f] != b[f])
            pairs += 1
    return (sum(ents) / len(ents),
            tot / (pairs * len(FIELDS)) if pairs else 0.0)


def cell_scores(rows_a, rows_b, draws, rng):
    """-> ((ent_a, ham_a), (ent_b, ham_b)) at EQUAL n, averaged over draws."""
    n = min(len(rows_a), len(rows_b))
    if n < 2:
        return None
    acc = [[0.0, 0.0], [0.0, 0.0]]
    for _ in range(draws):
        for k, rows in enumerate((rows_a, rows_b)):
            #: sample WITHOUT replacement so the estimator matches what you would
            #: get from a cell of exactly n stories, which is the thing being
            #: compared. With replacement would add its own downward bias.
            e, h = measures(rng.sample(rows, n))
            acc[k][0] += e; acc[k][1] += h
    return tuple((a / draws, b / draws) for a, b in acc)


def main(argv=None):
    from scipy.stats import binomtest, ttest_rel, wilcoxon

    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('--frame', default='raw', choices=('raw', 'prefill'))
    ap.add_argument('--min-per-cell', type=int, default=5)
    ap.add_argument('--draws', type=int, default=200)
    ap.add_argument('--within-demonym', action='store_true')
    ap.add_argument('--fields', default='split',
                    choices=('split', 'all', 'world', 'outcome'))
    a = ap.parse_args(argv)

    path = a.results if os.path.exists(a.results) else \
        os.path.join(HERE, a.results)
    rows = [json.loads(l) for l in open(path, encoding='utf-8')
            if json.loads(l)['frame'] == a.frame]
    by = collections.defaultdict(lambda: {'base': [], 'aligned': []})
    for r in rows:
        by[r['lineage']][r['arm']].append(r)

    groups = ([('WORLD  (what the story is)', WORLD),
               ('OUTCOME (how it resolves)', OUTCOME)] if a.fields == 'split'
              else [{'all': ('ALL FIELDS POOLED', FIELDS),
                     'world': ('WORLD', WORLD),
                     'outcome': ('OUTCOME', OUTCOME)}[a.fields]])

    for glabel, gfields in groups:
        #: `measures` reads the module-level FIELDS, so the group is installed
        #: there for the duration of this pass rather than threaded through.
        globals()['FIELDS'] = gfields
        rng = random.Random(20260901)     #: same draws for every group
        out = []
        for lin, d in sorted(by.items()):
            if len(d['base']) < a.min_per_cell or len(d['aligned']) < a.min_per_cell:
                continue
            if a.within_demonym:
                acc, k = [[0.0, 0.0], [0.0, 0.0]], 0
                dems = ({r['demonym'] for r in d['base']} &
                        {r['demonym'] for r in d['aligned']})
                for dem in sorted(dems):
                    ba = [r for r in d['base'] if r['demonym'] == dem]
                    al = [r for r in d['aligned'] if r['demonym'] == dem]
                    if min(len(ba), len(al)) < 3:
                        continue
                    sc1 = cell_scores(ba, al, a.draws, rng)
                    if not sc1:
                        continue
                    for i in (0, 1):
                        acc[i][0] += sc1[i][0]; acc[i][1] += sc1[i][1]
                    k += 1
                if not k:
                    continue
                sc = tuple((x / k, y / k) for x, y in acc)
            else:
                sc = cell_scores(d['base'], d['aligned'], a.draws, rng)
                if not sc:
                    continue
            out.append((lin, min(len(d['base']), len(d['aligned'])), sc))

        print('=' * 78)
        print('%s -- %d fields, %s frame, %s' % (glabel, len(gfields), a.frame,
              'WITHIN DEMONYM' if a.within_demonym else 'pooled across demonyms'))
        print('%d lineages, %d resamples at equal n per lineage.'
              % (len(out), a.draws))
        print('=' * 78)
        for lab, i in (('MEAN ENTROPY (bits)', 0), ('MEAN PAIRWISE HAMMING', 1)):
            b = [sc[0][i] for _, _, sc in out]
            al = [sc[1][i] for _, _, sc in out]
            diffs = [x - y for x, y in zip(al, b)]
            up = sum(1 for x in diffs if x > 0)
            dn = sum(1 for x in diffs if x < 0)
            p_s = binomtest(up, up + dn, 0.5).pvalue if up + dn else 1.0
            p_w = wilcoxon(diffs).pvalue if len(diffs) > 5 else 1.0
            p_t = ttest_rel(al, b).pvalue
            md = sum(diffs) / len(diffs)
            sd = (sum((x - md) ** 2 for x in diffs) / (len(diffs) - 1)) ** 0.5
            print('  %s' % lab)
            print('     base %.4f   aligned %.4f   mean diff %+.4f   dz %+.2f'
                  % (sum(b) / len(b), sum(al) / len(al), md, md / sd if sd else 0))
            print('     aligned MORE HOMOGENEOUS in %d of %d lineages'
                  % (dn, len(diffs)))
            print('     p_sign %.4g   p_wilcoxon %.4g   p_t %.4g'
                  % (p_s, p_w, p_t))
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
