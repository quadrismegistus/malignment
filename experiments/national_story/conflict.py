"""Run `story_conflict_v1` over the judged corpus. -> what conflict, and its fate.

    python conflict.py --per-cell 1 --dry     what it would send, no calls
    python conflict.py --per-cell 2           ~600 stories
    python conflict.py --smoke 12             a dozen, printed in full

## THE GATE IS THE JUDGE, AND THE GATE IS A CONFOUND

Only `judge_pure_story` texts go in: a text that is a story for 400 words and
instruction data for 680 has no single conflict to describe. But the story rate
is NOT equal across arms -- base 66%, aligned 82% -- so this gate selects a
different fraction of each arm, and every contrast below is conditional on
surviving it. Report the gated N per cell beside every number.

## TRUNCATION, WHICH THE JUDGE CANNOT SEE

`ending` and `resolution_scale` are confounded with truncation, and the
truncation is arm-specific: a base model has no ending to reach and is cut at
max_new_tokens, an aligned model emits EOS. `looks_complete` below is a
non-LLM flag on the final characters -- terminal punctuation, no mid-word cut --
so the contrast can be restricted to texts that stopped on purpose. It is a
proxy for the generation record's stop reason, which is not in this export.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, 'judged_corpus_for_propp.jsonl')


def looks_complete(text):
    """-> bool. Did the generation stop on purpose, as far as the bytes show?

    Not a stop reason. A model can end a sentence and still have been cut at the
    budget; this only catches the cut that lands mid-clause, which is most of
    them."""
    t = (text or '').rstrip()
    if not t:
        return False
    return bool(re.search(r'["\'”’)\]]*[.!?…]["\'”’)\]]*$', t))


def collect(per_cell=2, min_words=200, max_words=2000):
    """-> [(row, text)], pure stories only, balanced across demonyms."""
    cells = collections.defaultdict(list)
    for line in open(CORPUS, encoding='utf-8'):
        r = json.loads(line)
        if not r.get('judge_pure_story'):
            continue
        n = r.get('n_words') or 0
        if not (min_words <= n <= max_words):
            continue
        cells[(r['lineage'], r['arm'], r['frame'])].append(r)
    out = []
    for k, v in sorted(cells.items()):
        #: interleave demonyms so a per-cell cap cannot select on nationality --
        #: the sample cap that once moved RENEWAL by 1.1 points did exactly that,
        #: by concatenating demonyms and taking the first N.
        by_d = collections.defaultdict(list)
        for r in v:
            by_d[r['demonym']].append(r)
        order = sorted(by_d)
        woven = []
        for i in range(max(len(x) for x in by_d.values())):
            for d in order:
                if i < len(by_d[d]):
                    woven.append(by_d[d][i])
        out.extend(woven[:per_cell])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-cell', type=int, default=2)
    ap.add_argument('--min-words', type=int, default=200)
    ap.add_argument('--max-words', type=int, default=2000)
    ap.add_argument('--workers', type=int, default=16)
    ap.add_argument('--smoke', type=int, default=0,
                    help='run only N texts and print every answer in full')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--out', default='conflict_results.jsonl')
    a = ap.parse_args(argv)

    rows = collect(a.per_cell, a.min_words, a.max_words)
    if a.smoke:
        step = max(1, len(rows) // a.smoke)
        rows = rows[::step][:a.smoke]
    print('%d stories, %d cells, %d lineages, %.0f%% look complete'
          % (len(rows),
             len({(r['lineage'], r['arm'], r['frame']) for r in rows}),
             len({r['lineage'] for r in rows}),
             100 * sum(looks_complete(r['text']) for r in rows) / max(1, len(rows))))
    cc = collections.Counter((r['arm'], r['frame']) for r in rows)
    for k in sorted(cc):
        print('   %-16s %5d' % ('%s/%s' % k, cc[k]))
    if a.dry:
        return 0

    from malignment.tasks.code_story_conflict_v1 import (StoryConflictTask,
                                                         check_spans)
    task = StoryConflictTask()
    errs = {}
    res = task.map([r['text'] for r in rows], num_workers=a.workers,
                   verbose=True, errors=errs)

    ok_s = tot_s = 0
    F = collections.defaultdict(collections.Counter)
    N = collections.Counter()
    fh = open(os.path.join(HERE, a.out), 'w')
    for r, o in zip(rows, res):
        if o is None:
            continue
        ok, tot, miss = check_spans(r['text'], o)
        ok_s += ok; tot_s += tot
        k = (r['arm'], r['frame'])
        N[k] += 1
        for f in ('opponent', 'opponent_specificity', 'opponent_fate',
                  'conflict_mode', 'ending', 'resolution_scale',
                  'protagonist_change'):
            F[(k, f)][getattr(o, f)] += 1
        fh.write(json.dumps(dict(
            id=r['id'], lineage=r['lineage'], arm=r['arm'], frame=r['frame'],
            demonym=r['demonym'], n_words=r['n_words'],
            looks_complete=looks_complete(r['text']),
            spans_ok=ok, spans_total=tot,
            spans_missing=[f for f, _ in miss],
            **o.model_dump())) + '\n')
        if a.smoke:
            print('\n%s  %s/%s  %s  %d words  complete=%s'
                  % (r['lineage'], r['arm'], r['frame'], r['demonym'],
                     r['n_words'], looks_complete(r['text'])))
            print('   stakes      %s' % o.stakes)
            print('   opponent    %s (%s)  %r'
                  % (o.opponent, o.opponent_specificity, o.opponent_span))
            print('   fate        %-10s %r' % (o.opponent_fate, o.fate_span))
            print('   mode        %-10s %r' % (o.conflict_mode, o.conflict_span))
            print('   ending      %-10s %r' % (o.ending, o.ending_span))
            print('   scale       %-10s %r' % (o.resolution_scale, o.scale_span))
            print('   protagonist %s   spans %d/%d %s'
                  % (o.protagonist_change, ok, tot,
                     '  MISSING: %s' % [f for f, _ in miss] if miss else ''))
    fh.close()

    print('\nspans verified: %d/%d (%.1f%%)   errors: %d   no-result: %d'
          % (ok_s, tot_s, 100 * ok_s / max(1, tot_s), len(errs),
             sum(1 for x in res if x is None)))
    for f in ('opponent', 'opponent_fate', 'conflict_mode', 'ending',
              'resolution_scale'):
        print('\n%s' % f.upper())
        for k in sorted(N):
            c = F[(k, f)]
            print('  %-16s n=%-5d %s' % ('%s/%s' % k, N[k],
                  '  '.join('%s %.0f%%' % (kk, 100 * vv / N[k])
                            for kk, vv in c.most_common())))
    print('\nwrote %s' % a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
