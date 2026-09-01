"""Arm contrast over a conflict results file. -> every field, paired, with signs.

    python contrast.py conflict_results_n16.jsonl
    python contrast.py FILE --frame prefill
    python contrast.py FILE --field mood --show 12   read the spans behind a field

## WHY PAIRED WITHIN LINEAGE, AND WHY SIGN COUNTS

The arms are not independent samples: each aligned model has a base it was
trained from, and the lineages differ enormously in how much story they can write
at all. A pooled percentage lets one prolific lineage carry a contrast. So every
number here is computed on lineages present in BOTH arms, and every number is
followed by how many lineages moved up and how many moved down.

The sign count is the part to read. A +47.5 with 15 lineages up and 0 down is a
different claim from a +47.5 with 8 up and 7 down, and the percentage cannot
tell them apart.

## THE LOW-DOSE STRATUM

Five lineages have "aligned" members that are third-party academic preference
runs rather than production alignment: pythia-2.8b (archangel_sft-dpo),
pythia-6.9b (lomahony hh-dpo), Amber (AmberSafe), bloom-7b1 (bloomz, which is
multitask instruction tuning and not preference at all), and llama-7b (beaver).
Pooling them in dilutes every contrast, so both strata are printed. Excluding
them is defensible on the model cards alone and is not a subgroup chosen after
looking at outcomes.
"""
import argparse
import collections
import json
import os
import sys

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


#: named for what they are, not for how they scored. See the module docstring.
LOW_DOSE = {
    'EleutherAI/pythia-2.8b',    #: ContextualAI/archangel_sft-dpo_pythia2-8b
    'EleutherAI/pythia-6.9b',    #: lomahony/eleuther-pythia6.9b-hh-dpo
    'LLM360/Amber',              #: LLM360/AmberSafe
    'bigscience/bloom-7b1',      #: bloomz-7b1, xP3 multitask, not preference
    'huggyllama/llama-7b',       #: PKU-Alignment/beaver-7b-v1.0
}

CATEGORICAL = ('opponent', 'opponent_specificity', 'opponent_fate',
               'conflict_mode', 'ending', 'resolution_scale',
               'protagonist_change', 'setting', 'homecoming', 'threat',
               'temporality', 'romance', 'mood', 'genre', 'resolution_means',
               'community_role')
BOOLEAN = ('small_community', 'supernatural', 'collective_action', 'renewal',
           'nostalgia', 'elder_informant', 'tradition', 'community_constrains',
           'looks_complete')


def paired(rows, frame, keep):
    """-> (base, aligned) restricted to lineages present in BOTH arms."""
    rows = [r for r in rows if r['frame'] == frame and keep(r['lineage'])]
    B = [r for r in rows if r['arm'] == 'base']
    A = [r for r in rows if r['arm'] == 'aligned']
    both = {r['lineage'] for r in B} & {r['lineage'] for r in A}
    return ([r for r in B if r['lineage'] in both],
            [r for r in A if r['lineage'] in both])


def signs(B, A, f, v):
    """-> (up, down) lineages. A lineage counts once however many stories it has,
    which is the point: this is the check a pooled percentage cannot do."""
    L = collections.defaultdict(lambda: [0, 0, 0, 0])
    hit = (lambda r: bool(r[f])) if v is True else (lambda r: r[f] == v)
    for r in B:
        L[r['lineage']][0] += hit(r); L[r['lineage']][1] += 1
    for r in A:
        L[r['lineage']][2] += hit(r); L[r['lineage']][3] += 1
    u = d = 0
    for x in L.values():
        if not x[1] or not x[3]:
            continue
        u += x[2] / x[3] > x[0] / x[1]
        d += x[2] / x[3] < x[0] / x[1]
    return u, d


def rate(rows, f, v):
    hit = (lambda r: bool(r[f])) if v is True else (lambda r: r[f] == v)
    return 100 * sum(1 for r in rows if hit(r)) / max(1, len(rows)), \
        sum(1 for r in rows if hit(r))


def report(rows, frame, keep, label, floor):
    B, A = paired(rows, frame, keep)
    if not B or not A:
        print('%s: nothing paired' % label)
        return
    print('== %s == %s frame, %d lineages, base n=%d aligned n=%d'
          % (label, frame, len({r['lineage'] for r in B}), len(B), len(A)))
    print('%-34s %7s %7s %8s %14s' % ('', 'base', 'aligned', 'diff', 'lineages'))
    for f in CATEGORICAL:
        if f not in B[0]:
            continue
        vals = sorted({r[f] for r in B} | {r[f] for r in A})
        shown = []
        for v in vals:
            (b, bn), (a, an) = rate(B, f, v), rate(A, f, v)
            if max(b, a) < floor:
                continue
            u, d = signs(B, A, f, v)
            shown.append('  %-32s %6.1f%% %6.1f%% %+7.1f    up %2d down %2d'
                         % (f + '=' + str(v), b, a, a - b, u, d))
        if shown:
            print('\n'.join(shown))
    print()
    for f in BOOLEAN:
        if f not in B[0]:
            continue
        (b, bn), (a, an) = rate(B, f, True), rate(A, f, True)
        u, d = signs(B, A, f, True)
        print('  %-32s %6.1f%% %6.1f%% %+7.1f    up %2d down %2d   (%d vs %d)'
              % (f.upper(), b, a, a - b, u, d, bn, an))
    print()


def show(rows, field, n):
    """Read the spans behind a field. The number is never the evidence."""
    sp = {'mood': 'mood_span', 'opponent': 'opponent_span',
          'opponent_fate': 'fate_span', 'ending': 'ending_span',
          'resolution_scale': 'scale_span', 'resolution_means': 'means_span',
          'community_role': 'community_span', 'threat': 'threat_span',
          'temporality': 'temporality_span', 'genre': 'genre_span',
          'homecoming': 'homecoming_span', 'setting': 'setting_span',
          'conflict_mode': 'conflict_span',
          'community_constrains': 'constrains_span',
          'tradition': 'tradition_span', 'nostalgia': 'nostalgia_span',
          'elder_informant': 'elder_informant_span',
          'romance': 'romance_span'}.get(field, field + '_span')
    by = collections.defaultdict(list)
    for r in rows:
        by[r[field]].append(r)
    for v in sorted(by, key=lambda k: -len(by[k])):
        print('\n%s = %r   (%d stories)' % (field, v, len(by[v])))
        for r in by[v][:n]:
            print('  %-24s %-13s %-10s %r'
                  % (r['lineage'][:24], r['arm'] + '/' + r['frame'],
                     r['demonym'][:10], (r.get(sp) or '')[:100]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('results')
    ap.add_argument('--frame', default='raw', choices=('raw', 'prefill'))
    ap.add_argument('--floor', type=float, default=3.0,
                    help='hide values below this rate in BOTH arms')
    ap.add_argument('--field', help='print the spans behind one field instead')
    ap.add_argument('--show', type=int, default=8)
    a = ap.parse_args(argv)

    path = resolve(a.results)
    rows = [json.loads(l) for l in open(path, encoding='utf-8')]
    print('%s: %d annotations, %d lineages\n' % (os.path.basename(path),
          len(rows), len({r['lineage'] for r in rows})))
    if a.field:
        show([r for r in rows if r['frame'] == a.frame], a.field, a.show)
        return 0
    report(rows, a.frame, lambda L: True, 'ALL', a.floor)
    report(rows, a.frame, lambda L: L not in LOW_DOSE, 'EXCLUDING LOW-DOSE',
           a.floor)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
