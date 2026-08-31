"""Run `story_segments_v1` over the corpus. -> story rate per cell.

    python judge.py --per-cell 3          ~1,700 texts
    python judge.py --per-cell 1 --dry    what it would send, no calls

## THE FULL TEXT GOES TO THE JUDGE, AND NOTHING IS PRE-FILTERED

`analyse.py` drops escapes, corpus drift and stubs before measuring. This does
NOT, except for stubs, and the exception is deliberate in both directions:

  - The judge exists to REPLACE those filters. Screening with the detectors it
    is meant to supersede would hand it a corpus already cleaned by the
    instruments whose failures motivated it, and the story rate would be
    measured on the subset my regexes happened to approve.
  - A stub under 150 words has nothing to segment. That is a missing
    generation, not a kind of writing.

Texts go WHOLE. Clipping would hide exactly the thing being looked for: a
generation that is a story for 400 words and instruction data for 680.

## WHAT THIS BUYS THAT NOTHING ELSE DOES

Every result so far -- tropes, drift, surprisal, homogeneity -- assumes the text
IS a story and measures a property of it. None can say whether the model wrote
fiction at all. An aligned description of al-Aqsa in which nothing happens passes
repetition, function-word, escape and drift detection; a base model answering
with a nineteenth-century essay passes them too. The story RATE is upstream of
every other number here.
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STASH = os.path.expanduser(
    '~/malignment-data/generations/*/*/jsonl.hashstash.raw/data.jsonl')
KEEP_FIRST, DROP_WHEN_DUP = '7802ca3c31ae', 'b1d15d1f291d'


def collect(min_words=150, per_cell=3):
    """-> [(lineage, arm, frame, demonym, text)], balanced across demonyms."""
    from malignment import roster
    pairs, _ = roster.endpoints()
    arm = {m: 'base' for m in pairs}
    arm.update({m: 'aligned' for m in pairs.values()})
    lin = {}
    for b, a in pairs.items():
        lin[b] = b; lin[a] = b
    by_mp = collections.defaultdict(set)
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
            if r.get('frame') not in ('raw', 'prefill_sysdefault'):
                continue
            if arm.get(r['model']) is None:
                continue
            r['_p'] = prod
            by_mp[r['model']].add(prod)
            rows.append(r)
    dup = {m for m, ps in by_mp.items()
           if KEEP_FIRST in ps and DROP_WHEN_DUP in ps}
    cells = collections.defaultdict(list)
    seen = collections.defaultdict(set)
    for r in rows:
        if r['model'] in dup and r['_p'] == DROP_WHEN_DUP:
            continue
        t = r.get('text') or ''
        if len(t.split()) < min_words:      #: the ONLY filter -- see docstring
            continue
        dm = re.match(r'An? (\w+) Story', r.get('prompt') or '')
        if not dm:
            continue
        fr = 'raw' if r['frame'] == 'raw' else 'prefill'
        k = (lin[r['model']], arm[r['model']], fr, dm.group(1))
        h = hashlib.md5(t.encode()).hexdigest()
        if h in seen[k]:
            continue
        seen[k].add(h)
        cells[k].append(t)
    out = []
    for k, v in sorted(cells.items()):
        for t in v[:per_cell]:
            out.append(k + (t,))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-cell', type=int, default=3)
    ap.add_argument('--min-words', type=int, default=150)
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--out', default='judge_results.jsonl')
    a = ap.parse_args(argv)

    items = collect(a.min_words, a.per_cell)
    cells = {(L, ar, fr) for L, ar, fr, _, _ in items}
    print('%d texts, %d cells, %d lineages'
          % (len(items), len(cells), len({L for L, _, _, _, _ in items})))
    print('median words %.0f, total ~%.1fM words'
          % (st.median(len(t.split()) for *_, t in items),
             sum(len(t.split()) for *_, t in items) / 1e6))
    if a.dry:
        return 0

    sys.path.insert(0, HERE)
    from malignment.tasks.code_story_segments_v1 import (StorySegmentsTask,
                                                         check_witnesses)
    task = StorySegmentsTask()
    #: the harness does `errors[i] = {...}`, so a bare [] raises IndexError on
    #: the FIRST failure and takes that item down with it. A dict indexes freely.
    errs = {}
    res = task.map([t for *_, t in items], num_workers=a.workers,
                   verbose=True, errors=errs)

    fh = open(a.out, 'w')
    ok_w = tot_w = 0
    G = collections.defaultdict(collections.Counter)
    N = collections.Counter()
    for (L, ar, fr, dem, t), r in zip(items, res):
        if r is None:
            N[(ar, fr)] += 0
            continue
        o, tw, miss = check_witnesses(t, r)
        ok_w += o; tot_w += tw
        N[(ar, fr)] += 1
        G[(ar, fr)][r.overall] += 1
        if r.opens_as_story:
            G[(ar, fr)]['_opens_story'] += 1
        fh.write(json.dumps(dict(
            lineage=L, arm=ar, frame=fr, demonym=dem,
            n_words=len(t.split()), overall=r.overall,
            opens_as_story=r.opens_as_story,
            witnesses_ok=o, witnesses_total=tw,
            segments=[dict(kind=s.kind, first_words=s.first_words, why=s.why)
                      for s in r.segments])) + '\n')
    fh.close()
    print('\nwitnesses verified: %d/%d (%.1f%%)   errors: %d   no-result: %d'
          % (ok_w, tot_w, 100 * ok_w / max(1, tot_w), len(errs),
             sum(1 for r in res if r is None)))
    print('\n%-22s %6s %8s %9s  %s'
          % ('cell', 'n', 'STORY', 'opens', 'other kinds'))
    for k in sorted(N):
        n = N[k]
        if not n:
            continue
        c = G[k]
        other = ', '.join('%s %d%%' % (kk, round(100 * vv / n))
                          for kk, vv in c.most_common()
                          if kk not in ('story', '_opens_story'))
        print('%-22s %6d %7.0f%% %8.0f%%  %s'
              % ('%s/%s' % k, n, 100 * c['story'] / n,
                 100 * c['_opens_story'] / n, other or '-'))
    print('\nwrote %s' % a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
