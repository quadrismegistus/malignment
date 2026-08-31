"""Run story_conflict_v1 over Rettberg's released corpus. -> comparable annotations.

    python rettberg.py --dry
    python rettberg.py --demonyms ours      8 demonyms + her Default control
    python rettberg.py --demonyms all --per 10

Her CC0 release: 11,800 stories, 236 countries, EXACTLY 50 each, gpt-4o-mini at
temperature 0.8. 99% fall inside the 200-2000 word band this experiment uses.

    ~/Downloads/dataverse_files/gpt-stories/<ISO>/<ISO>_stories.csv

## HER UNREPORTED CONTROL IS IN THE RELEASE

Directory `XX`, Country_Name and Demonym both `Default`, prompt "Write a 1500
word potential story." with no nationality, 50 stories. The paper says she
generated these to see what the default story looked like and never reports
them. They are included here as demonym `none`, which is the same label
`prompts_compare.jsonl` now uses for our own control cell.

## WHAT THIS COMPARISON CAN AND CANNOT SAY

Her generations differ from ours on three axes at once, and only the last is the
one under study:

    prompt       "Write a 1500 word potential Norwegian story." -- an
                 INSTRUCTION. Ours is a paratext continuation, "A Norwegian
                 Story\\n(1500 words)\\n\\nIt was a".
    decoder      t=0.8, top_p default. Ours is t=1.0/p=0.95.
    frame        hers is a chat completion, so it is closest to our prefill
                 cell, not to the raw frame the arm contrast uses.

So a difference between her numbers and our ALIGNED numbers is prompt, decoder
and frame confounded together, and is not evidence about alignment. What it IS
good for: she is a single model, so her corpus gives a within-model homogeneity
baseline that no cell of ours provides, and the annotations put her stories in
the same space as ours so the trope claims can be checked directly rather than
through her prose.
"""
import argparse
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GPT = os.path.expanduser('~/Downloads/dataverse_files/gpt-stories')
OURS = {'US': 'American', 'FR': 'French', 'IL': 'Israeli', 'JP': 'Japanese',
        'NG': 'Nigerian', 'NO': 'Norwegian', 'PS': 'Palestinian',
        'TR': 'Turkish', 'XX': 'none'}


def collect(which, per, lo, hi):
    out = []
    dirs = sorted(OURS) if which == 'ours' else sorted(
        d for d in os.listdir(GPT) if os.path.isdir(os.path.join(GPT, d)))
    for d in dirs:
        p = os.path.join(GPT, d, '%s_stories.csv' % d)
        if not os.path.exists(p):
            continue
        rows = [r for r in csv.DictReader(open(p, encoding='utf-8'))
                if lo <= len((r['Story'] or '').split()) <= hi]
        for r in rows[:per] if per else rows:
            out.append(dict(
                id='rettberg:%s' % r['Story_ID'], model='gpt-4o-mini',
                lineage='gpt-4o-mini', arm='aligned', frame='rettberg_chat',
                demonym=OURS.get(d, r['Demonym'] or d), iso=d,
                n_words=len(r['Story'].split()), text=r['Story'],
                temperature=r['Temperature'], prompt=r['Prompt']))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--demonyms', default='ours', choices=('ours', 'all'))
    ap.add_argument('--per', type=int, default=0, help='0 = every story')
    ap.add_argument('--min-words', type=int, default=200)
    ap.add_argument('--max-words', type=int, default=2000)
    ap.add_argument('--workers', type=int, default=20)
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--out', default='rettberg_conflict.jsonl')
    a = ap.parse_args(argv)

    rows = collect(a.demonyms, a.per, a.min_words, a.max_words)
    c = collections.Counter(r['demonym'] for r in rows)
    print('%d stories, %d demonyms' % (len(rows), len(c)))
    for k in sorted(c):
        print('   %-14s %4d' % (k, c[k]))
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

    ok = tot = 0
    fh = open(os.path.join(HERE, a.out), 'w')
    for r, o in zip(rows, res):
        if o is None:
            continue
        k, t, miss = check_spans(r['text'], o)
        ok += k; tot += t
        rx = tropes.annotate(r['text']).present(min_votes=2)
        fh.write(json.dumps(dict(
            {x: r[x] for x in ('id', 'model', 'lineage', 'arm', 'frame',
                               'demonym', 'iso', 'n_words')},
            spans_ok=k, spans_total=t, spans_missing=[f for f, _ in miss],
            tropes={n: dict(llm=bool(fn(o)), regex=bool(rx[n]))
                    for n, fn in TROPE_MAP.items()},
            **o.model_dump())) + '\n')
    fh.close()
    print('\nspans verified: %d/%d (%.1f%%)   errors: %d'
          % (ok, tot, 100 * ok / max(1, tot), len(errs)))
    print('wrote %s' % a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
