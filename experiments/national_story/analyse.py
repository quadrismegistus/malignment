"""Base against aligned on national stories. -> the three paired contrasts.

    python analyse.py                 all three
    python analyse.py --tropes        just the trope contrast
    python analyse.py --min-words 150 --cap 40

Reads the generations stash directly. Every contrast is PAIRED WITHIN LINEAGE and
reported per lineage before it is pooled: a pooled rate has hidden a member six
times in this campaign, and two of the three contrasts here have a lineage that
runs the other way.

## THE DUPLICATE PRODUCER RULE, WHICH IS NOT OPTIONAL

Box 1 died after 9 of 20 models. Its stash was rsynced to a replacement so the
replacement would skip completed work, but a second box had already re-run four
of those models from an empty stash (malign, docket [6591]). Both copies sit in
the stash at the SAME seeds with DIFFERENT text, because vLLM does not reproduce
a seed across boxes -- same model, same prompt, seed 46 gives 1,637 words on one
box and 2,112 on the other.

They are not independent samples: the intent was one draw and the divergence is
backend non-determinism. Keep the FIRST producer. The rule is per (producer,
model) and NOT per producer, because the later producer is the SOLE source for
five Qwen models and dropping it wholesale would delete them.

**Seed parity between arms is therefore unavailable.** Any analysis pairing base
sample i to aligned sample i is comparing unrelated draws. Nothing here does.

## WHAT IS EXCLUDED, AND WHY EACH EXCLUSION IS NOT NEUTRAL

    frame != raw        prefill rows were generated with a renderer that CLOSED
                        the assistant turn, so the model saw a finished answer
                        (fixed at 9b8465e; rows before it are a different
                        condition, not a degenerate one)
    < min_words         a stub has no plot to measure, and a near-empty
                        generation scores 0 on every lexical rate by
                        construction
    escaped             assistant boilerplate is similar across samples, so
                        leaving escapes in would inflate the ALIGNED arm's
                        homogeneity with an artifact this same script measures
                        separately

The escape exclusion is the one to watch: it removes more from one arm than the
other by design, so the homogeneity contrast is conditional on it and should be
re-run without it as a sensitivity check.
"""

import argparse
import collections
import glob
import hashlib
import importlib.util
import itertools
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KEEP_FIRST, DROP_WHEN_DUP = '7802ca3c31ae', 'b1d15d1f291d'
STASH = os.path.expanduser(
    '~/malignment-data/generations/*/*/jsonl.hashstash.raw/data.jsonl')
KEYS = ['RETURN', 'SMALLTOWN', 'SPIRIT', 'THREAT', 'ORGANISE', 'RENEWAL']
STOP = set("the a an and or but of to in on at for with from by as is was were "
           "be it its he she they that this there what which who when where how "
           "not no so if then than had has have do did does will would can "
           "could her his i you we my me him them their".split())


def _measure():
    #: story_decoder/run.py, by PATH: this directory has a run.py of its own and
    #: it shadows that one on sys.path.
    p = os.path.join(HERE, '..', 'story_decoder', 'run.py')
    spec = importlib.util.spec_from_file_location('sd_run', p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.measure


def load_raw(min_words=150, drop_escapes=True):
    """-> {(lineage, arm): [text]}, deduplicated, paired-ready."""
    sys.path.insert(0, HERE)
    from tropes import annotate                       # noqa: F401  (import check)
    from malignment import roster
    measure = _measure()
    pairs, _ = roster.endpoints()
    arm = {m: 'base' for m in pairs}
    arm.update({m: 'aligned' for m in pairs.values()})
    lin = {}
    for b, a in pairs.items():
        lin[b] = b; lin[a] = b
    by_model_prod = collections.defaultdict(set)
    rows = []
    for f in sorted(glob.glob(STASH)):
        prod = f.split('/generations/')[1].split('/')[1]
        for line in open(f, encoding='utf-8'):
            try:
                r = json.loads(line)
            except Exception:
                continue
            d = r.get('decoder') or {}
            if (d.get('max_new_tokens') or 0) < 1000 or d.get('top_p') != 0.95:
                continue
            if r.get('frame') != 'raw' or arm.get(r['model']) is None:
                continue
            r['_prod'] = prod
            by_model_prod[r['model']].add(prod)
            rows.append(r)
    dup = {m for m, ps in by_model_prod.items()
           if KEEP_FIRST in ps and DROP_WHEN_DUP in ps}
    G = collections.defaultdict(list)
    seen = collections.defaultdict(set)
    for r in rows:
        if r['model'] in dup and r['_prod'] == DROP_WHEN_DUP:
            continue
        t = r.get('text') or ''
        if len(t.split()) < min_words:
            continue
        if drop_escapes:
            m = measure(t)
            if (m['escape_address'] or m['escape_meta']
                    or m['escape_list'] or m['escape_emoji']):
                continue
        dm = re.match(r'An? (\w+) Story', r.get('prompt') or '')
        k = (lin[r['model']], arm[r['model']], dm.group(1) if dm else '?')
        h = hashlib.md5(t.encode()).hexdigest()
        if h in seen[k]:
            continue
        seen[k].add(h)
        G[k].append(t)
    return G


def _paired(G):
    lins = {L for L, _, _ in G}
    return sorted(L for L in lins
                  if any(k[:2] == (L, 'base') for k in G)
                  and any(k[:2] == (L, 'aligned') for k in G))


def texts(G, L, a):
    """Texts for one (lineage, arm), INTERLEAVED across demonyms.

    Concatenating demonyms and then taking the first N lets the cap select on
    nationality: with 8 demonyms and cap=40 the sample is the first five
    demonyms and none of the rest, and the trope rates move by several points
    depending only on dict order. Interleaving makes any prefix balanced.
    """
    cells = [v for (l, arm_, dem), v in sorted(G.items()) if l == L and arm_ == a]
    out = []
    for i in range(max((len(c) for c in cells), default=0)):
        for c in cells:
            if i < len(c):
                out.append(c[i])
    return out


def _sign(diffs, label):
    up = sum(1 for x in diffs if x > 0)
    dn = sum(1 for x in diffs if x < 0)
    print('  %-30s aligned higher in %d of %d (lower in %d), median %+.3f'
          % (label, up, len(diffs), dn, st.median(diffs)))


def tropes_contrast(G, cap=40):
    sys.path.insert(0, HERE)
    from tropes import annotate
    lins = _paired(G)
    res = {}
    for L in lins:
        for a in ('base', 'aligned'):
            anns = [annotate(t) for t in texts(G, L, a)[:cap]]
            res[(L, a)] = anns
    print('\n== TROPES (Rettberg six, >=2 of 3 independent detectors) ==')
    print('%-34s %6s %7s %7s' % ('lineage', 'base', 'aligned', 'diff'))
    d = []
    for L in lins:
        b = st.mean(x.n_present() for x in res[(L, 'base')])
        a = st.mean(x.n_present() for x in res[(L, 'aligned')])
        d.append(a - b)
        print('%-34s %6.2f %7.2f %+7.2f' % (L.split('/')[-1][:32], b, a, a - b))
    _sign(d, 'mean tropes per story')
    print('\n  %-11s %8s %8s %8s  %s' % ('trope', 'base', 'aligned', 'diff', 'higher'))
    for k in KEYS:
        rb = st.mean(100 * sum(x.present()[k] for x in res[(L, 'base')])
                     / len(res[(L, 'base')]) for L in lins)
        ra = st.mean(100 * sum(x.present()[k] for x in res[(L, 'aligned')])
                     / len(res[(L, 'aligned')]) for L in lins)
        up = sum(1 for L in lins
                 if sum(x.present()[k] for x in res[(L, 'aligned')]) / len(res[(L, 'aligned')])
                 > sum(x.present()[k] for x in res[(L, 'base')]) / len(res[(L, 'base')]))
        print('  %-11s %7.1f%% %7.1f%% %+7.1f   %d/%d' % (k, rb, ra, ra - rb, up, len(lins)))
    print('\n  Rettberg gpt-4o-mini: RETURN 40.7 SMALLTOWN 73.2 SPIRIT 75.6')
    print('                        THREAT 42.1 ORGANISE  59.5 RENEWAL 78.2')


def whisper_contrast(G):
    lins = _paired(G)
    rx = re.compile(r'\bwhisper', re.I)
    print('\n== WHISPER (top riser at both ladder rungs, malign-logits M01) ==')
    d = []
    for L in lins:
        tb, ta = texts(G, L, 'base'), texts(G, L, 'aligned')
        b = 100 * sum(1 for t in tb if rx.search(t)) / len(tb)
        a = 100 * sum(1 for t in ta if rx.search(t)) / len(ta)
        d.append(a - b)
    _sign(d, 'whisper rate')
    print('  Rettberg gpt-4o-mini: 87.2%% of stories; >=50%% in 225 of 236 countries')


def homogeneity_contrast(G, cap=8):
    """Within-DEMONYM similarity, per demonym, then averaged.

    Pooling demonyms first inflates every arm equally and measures something
    else: two Norway stories share `fjord` and `Oslo` for reasons that are not
    homogeneity of plot, and pooling lets that count as similarity between a
    Norway story and a Japan one. The comparison Rettberg's claim needs is
    WITHIN a nationality.
    """
    def bag(t, n=400):
        w = [x.lower().strip('.,!?;:"*-’\'') for x in t.split()[:n]]
        return {x for x in w if x and x not in STOP and len(x) > 3}
    def jac(a, b):
        return len(a & b) / max(1, len(a | b))
    def cell(v):
        B = [bag(t) for t in v[:cap]]
        p = [jac(x, y) for x, y in itertools.combinations(B, 2)]
        return st.mean(p) if len(B) >= 6 else None
    lins = _paired(G)
    print('\n== WITHIN-NATIONALITY HOMOGENEITY (lexical, per demonym) ==')
    d = []
    for L in lins:
        per = {}
        for a in ('base', 'aligned'):
            vals = [cell(v) for (l, arm_, dem), v in G.items()
                    if l == L and arm_ == a]
            vals = [x for x in vals if x is not None]
            per[a] = st.mean(vals) if len(vals) >= 4 else None
        if per['base'] is not None and per['aligned'] is not None:
            d.append(per['aligned'] - per['base'])
    if d:
        _sign(d, 'within-demonym jaccard')
    print('  Rettberg gpt-4o-mini: 0.116; our base median ~0.046 (16/16 below)')


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--min-words', type=int, default=150)
    ap.add_argument('--cap', type=int, default=40)
    ap.add_argument('--keep-escapes', action='store_true')
    ap.add_argument('--tropes', action='store_true')
    a = ap.parse_args(argv)
    G = load_raw(min_words=a.min_words, drop_escapes=not a.keep_escapes)
    lins = _paired(G)
    print('%d complete lineages, %d texts (escapes %s)'
          % (len(lins), sum(len(v) for v in G.values()),
             'kept' if a.keep_escapes else 'dropped'))
    tropes_contrast(G, cap=a.cap)
    if not a.tropes:
        whisper_contrast(G)
        homogeneity_contrast(G)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
