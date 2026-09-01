"""Surprisal and drift over every pure story, plus Rettberg's. -> results/*.jsonl

    python embed_score.py --what surprisal
    python embed_score.py --what drift
    python embed_score.py --what both --limit 20      smoke

Both metrics cache by sha in `score.py`, so a re-run costs only the new texts and
this can be stopped and restarted without losing work.

## THE TWO SETTINGS THAT ARE NOT DEFAULTS

**Surprisal is measured on the first 193 WORDS, clipped before the call.** That
matches the human anchor's own construction. It is not a cost decision and the
`m` parameter is not a substitute: `score.surprisal`'s `m` does not bound the
computation -- it runs the reference over the whole text and slices the result,
and `if v.size < m: return None` silently drops anything shorter, which at m=256
once dropped 149 of 150 anchor passages and returned a confident mean over n=1.

**Only the three length-free drift metrics are kept.** `mean_drift`,
`mean_pairwise` and `ordering`. The cumulative ones grow with sentence count by
construction, and the arms differ in length, so keeping them would manufacture an
arm difference out of a length difference.

bge runs on CPU by rule (score.py's own note); the surprisal reference may use
mps. Both are provenance-stamped in the cache.
"""
import argparse
import collections
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('MALIGNMENT_DATA', os.path.expanduser('~/malignment-data'))
DATA_DIR = os.path.join(DATA, 'national_story')
CORPUS = os.path.join(DATA_DIR, 'judged_stories_v2.jsonl')
RETT = os.path.join(HERE, 'rettberg_conflict.jsonl')
KEEP = ('mean_drift', 'mean_pairwise', 'ordering', 'n_sents')


def load(limit=0):
    """-> [row] with a `text`, ours and hers, tagged by source."""
    out = []
    for line in open(CORPUS, encoding='utf-8'):
        r = json.loads(line)
        if r['pure_story'] and r['n_words'] >= 200:
            out.append(dict(id=r['id'], source='ours', model=r['model'],
                            lineage=r['lineage'], arm=r['arm'], frame=r['frame'],
                            demonym=r['demonym'], n_words=r['n_words'],
                            text=r['text']))
    if os.path.exists(RETT):
        import csv
        G = os.path.expanduser('~/Downloads/dataverse_files/gpt-stories')
        want = {json.loads(l)['id']: json.loads(l) for l in open(RETT)}
        for d in sorted(os.listdir(G)):
            p = os.path.join(G, d, '%s_stories.csv' % d)
            if not os.path.exists(p):
                continue
            for r in csv.DictReader(open(p, encoding='utf-8')):
                k = 'rettberg:%s' % r['Story_ID']
                if k in want:
                    w = want[k]
                    out.append(dict(id=k, source='rettberg',
                                    model='gpt-4o-mini', lineage='gpt-4o-mini',
                                    arm='aligned', frame='rettberg_chat',
                                    demonym=w['demonym'], n_words=w['n_words'],
                                    text=r['Story']))
    return out[:limit] if limit else out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--what', default='both',
                    choices=('surprisal', 'drift', 'both'))
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--batch', type=int, default=50)
    ap.add_argument('--clip-words', type=int, default=193)
    a = ap.parse_args(argv)

    from malignment import score
    rows = load(a.limit)
    c = collections.Counter(r['source'] for r in rows)
    print('%d texts: %s' % (len(rows), dict(c)))
    #: outputs go to the DATA DIR, not the checkout -- these are 2-3 MB files
    #: regenerated wholesale. Writing them to HERE after the move produced a
    #: newer copy in the repo that no reader resolved.
    os.makedirs(DATA_DIR, exist_ok=True)

    for what in (('surprisal', 'drift') if a.what == 'both' else (a.what,)):
        out = os.path.join(DATA_DIR, 'story_%s.jsonl' % what)
        done = set()
        if os.path.exists(out):
            done = {json.loads(l)['id'] for l in open(out)}
        todo = [r for r in rows if r['id'] not in done]
        print('\n%s: %d done, %d to do' % (what, len(done), len(todo)))
        fh = open(out, 'a')
        t0 = time.time()
        for i in range(0, len(todo), a.batch):
            chunk = todo[i:i + a.batch]
            if what == 'surprisal':
                #: clip BEFORE the call -- see the module docstring
                txt = [' '.join(r['text'].split()[:a.clip_words]) for r in chunk]
                vals = score.surprisal(txt)
                recs = [dict(v=None if v is None else float(v)) for v in vals]
            else:
                vals = score.drift([r['text'] for r in chunk])
                recs = [{k: (float(d[k]) if k in d else None) for k in KEEP}
                        for d in vals]
            for r, rec in zip(chunk, recs):
                fh.write(json.dumps(dict(
                    {k: r[k] for k in ('id', 'source', 'model', 'lineage',
                                       'arm', 'frame', 'demonym', 'n_words')},
                    **rec)) + '\n')
            fh.flush()
            el = time.time() - t0
            n = i + len(chunk)
            print('   %5d/%d  %.1f/s  eta %.0f min'
                  % (n, len(todo), n / el, (len(todo) - n) / max(n / el, 1e-9) / 60),
                  flush=True)
        fh.close()
        print('   wrote %s' % out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
