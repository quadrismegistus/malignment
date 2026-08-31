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
DATA = os.environ.get('MALIGNMENT_DATA', os.path.expanduser('~/malignment-data'))
#: moved out of the repo 2026-08-31: 51.7 MB, and it is generated data, not source.
#: renamed off `judged_corpus_for_propp` because Propp was abandoned and the file
#: is now the text source for every instrument here.
CORPUS = os.path.join(DATA, 'national_story', 'judged_stories_v2.jsonl')


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
    #: v1 of the corpus prefixed the judge fields (`judge_pure_story`), v2 does
    #: not (`pure_story`). Reading v2 with the v1 key returned 0 STORIES AND NO
    #: ERROR -- a filter that matches nothing looks identical to a corpus with
    #: nothing in it. Resolve the key once, up front, and refuse loudly if
    #: neither is present rather than reporting an empty run as a result.
    first = json.loads(open(CORPUS, encoding='utf-8').readline())
    GATE = ('pure_story' if 'pure_story' in first else
            'judge_pure_story' if 'judge_pure_story' in first else None)
    if GATE is None:
        raise SystemExit('%s carries neither `pure_story` nor `judge_pure_story`;'
                         ' refusing to run a gate that cannot fire.' % CORPUS)
    for line in open(CORPUS, encoding='utf-8'):
        r = json.loads(line)
        if not r.get(GATE):
            continue
        n = r.get('n_words') or 0
        if not (min_words <= n <= max_words):
            continue
        #: KEYED BY MODEL, NOT LINEAGE. A lineage can carry several aligned
        #: rungs -- Llama-3.1-8B has six Tulu-3 ablation checkpoints under it --
        #: and a lineage-keyed quota gives all of them ONE shared allocation,
        #: sampled in whatever order the file happens to be in. The rungs then
        #: appear at wildly uneven n or not at all, which is indistinguishable
        #: from them not existing.
        cells[(r['model'], r['arm'], r['frame'])].append(r)
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

    sys.path.insert(0, HERE)
    import tropes
    from malignment.tasks.code_story_conflict_v1 import (StoryConflictTask,
                                                         check_spans, TROPE_MAP)
    task = StoryConflictTask()
    errs = {}
    res = task.map([r['text'] for r in rows], num_workers=a.workers,
                   verbose=True, errors=errs)

    ok_s = tot_s = 0
    F = collections.defaultdict(collections.Counter)
    N = collections.Counter()
    #: per-trope 2x2 against the regexes: (llm, regex) -> count
    AGREE = collections.defaultdict(collections.Counter)
    T = collections.defaultdict(collections.Counter)
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
                  'protagonist_change', 'setting', 'homecoming', 'threat',
                  'temporality', 'romance', 'mood', 'genre',
                  'nostalgia', 'elder_informant', 'resolution_means',
                  'community_role', 'tradition', 'community_constrains'):
            F[(k, f)][getattr(o, f)] += 1
        #: present() returns ALL SIX keys with bool values, so `name in rx` is a
        #: key-membership test that is always True. It ran once that way and put
        #: every regex column at 100%.
        rx = tropes.annotate(r['text']).present(min_votes=2)
        tro = {}
        for name, fn in TROPE_MAP.items():
            llm, reg = bool(fn(o)), bool(rx[name])
            tro[name] = dict(llm=llm, regex=reg)
            AGREE[name][(llm, reg)] += 1
            T[(k, name)]['llm'] += llm
            T[(k, name)]['regex'] += reg
        fh.write(json.dumps(dict(
            id=r['id'], model=r['model'], lineage=r['lineage'],
            arm=r['arm'], frame=r['frame'],
            demonym=r['demonym'], n_words=r['n_words'],
            looks_complete=looks_complete(r['text']),
            spans_ok=ok, spans_total=tot,
            spans_missing=[f for f, _ in miss], tropes=tro,
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
              'resolution_scale', 'setting', 'homecoming', 'threat',
              'temporality', 'romance', 'mood', 'genre',
              'nostalgia', 'elder_informant', 'resolution_means',
              'community_role', 'tradition', 'community_constrains'):
        print('\n%s' % f.upper())
        for k in sorted(N):
            c = F[(k, f)]
            print('  %-16s n=%-5d %s' % ('%s/%s' % k, N[k],
                  '  '.join('%s %.0f%%' % (kk, 100 * vv / N[k])
                            for kk, vv in c.most_common())))

    tot = sum(N.values())
    print('\n== THE SIX, LLM AGAINST REGEX (n=%d) ==' % tot)
    print('%-11s %6s %6s   %5s %5s %5s %5s  %s'
          % ('trope', 'llm', 'regex', 'both', 'llm', 'rx', 'nei', 'agree'))
    for name in ('SMALLTOWN', 'RETURN', 'THREAT', 'SPIRIT', 'ORGANISE',
                 'RENEWAL'):
        c = AGREE[name]
        both, lo, ro, nei = (c[(1, 1)], c[(1, 0)], c[(0, 1)], c[(0, 0)])
        print('%-11s %5.0f%% %5.0f%%   %5d %5d %5d %5d  %4.0f%%'
              % (name, 100 * (both + lo) / tot, 100 * (both + ro) / tot,
                 both, lo, ro, nei, 100 * (both + nei) / tot))
    print('\n== THE SIX BY ARM (llm / regex) ==')
    for name in ('SMALLTOWN', 'RETURN', 'THREAT', 'SPIRIT', 'ORGANISE',
                 'RENEWAL'):
        print('%-11s %s' % (name, '  '.join(
            '%s/%s %.0f%%/%.0f%%' % (k[0][:3], k[1][:3],
                                     100 * T[(k, name)]['llm'] / N[k],
                                     100 * T[(k, name)]['regex'] / N[k])
            for k in sorted(N) if N[k])))
    print('\nwrote %s' % a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
