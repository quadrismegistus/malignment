"""One sqlite file: every story with its text and every annotation, one row.

    python export_db.py                        -> conflict.sqlite
    python export_db.py --results FILE --out X

## WHY THIS EXISTS

The annotations and the texts live in different files joined by `id`, and four
stale result files from earlier schema versions sit beside the current one. That
is fine for an analysis script that knows which is which and unusable for anyone
who wants to filter by annotation value and read the story.

One table, `stories`. Text is a column. Every annotation is a typed column.
Booleans are stored 0/1 so `WHERE tradition = 1` works. Every categorical field
is indexed, because filtering by annotation value is the whole point.

    SELECT demonym, arm, text FROM stories
     WHERE opponent = 'institution' AND opponent_specificity = 'named'
       AND demonym = 'Palestinian' ORDER BY n_words;

The six regex trope verdicts are flattened to `rx_SMALLTOWN`, `llm_SMALLTOWN`
and so on, so the instrument comparison is queryable without unpacking JSON.

`schema_version` records which results file each row came from, so a future run
with more fields can be loaded alongside rather than silently mixed in.
"""
import argparse
import collections
import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('MALIGNMENT_DATA', os.path.expanduser('~/malignment-data'))
#: moved out of the repo 2026-08-31: 51.7 MB, and it is generated data, not source.
#: renamed off `judged_corpus_for_propp` because Propp was abandoned and the file
#: is now the text source for every instrument here.
CORPUS = os.path.join(DATA, 'national_story', 'judged_stories.jsonl')

#: not stored as columns; they are re-derivable and would bloat every row
SKIP = {'tropes'}
TROPES = ('SMALLTOWN', 'RETURN', 'THREAT', 'SPIRIT', 'ORGANISE', 'RENEWAL')
#: filtering by these is the use case, so they get indices
INDEXED = ('demonym', 'arm', 'frame', 'lineage', 'opponent',
           'opponent_specificity', 'opponent_fate', 'conflict_mode', 'ending',
           'resolution_scale', 'resolution_means', 'community_role', 'mood',
           'genre', 'setting', 'homecoming', 'threat', 'temporality', 'romance',
           'protagonist_change', 'tradition', 'nostalgia', 'elder_informant',
           'supernatural', 'collective_action', 'renewal', 'small_community',
           'community_constrains', 'looks_complete')


def sqltype(v):
    if isinstance(v, bool):
        return 'INTEGER'          #: 0/1 so WHERE tradition = 1 works
    if isinstance(v, int):
        return 'INTEGER'
    if isinstance(v, float):
        return 'REAL'
    return 'TEXT'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default='conflict_results_n16.jsonl')
    ap.add_argument('--out', default='conflict.sqlite')
    ap.add_argument('--version', default=None,
                    help='schema_version label; defaults to the results filename')
    a = ap.parse_args(argv)

    rp = a.results if os.path.exists(a.results) else os.path.join(HERE, a.results)
    rows = [json.loads(l) for l in open(rp, encoding='utf-8')]
    version = a.version or os.path.basename(rp)
    want = {r['id'] for r in rows}

    text = {}
    for line in open(CORPUS, encoding='utf-8'):
        r = json.loads(line)
        if r['id'] in want:
            text[r['id']] = r
    missing = want - set(text)
    if missing:
        print('WARNING: %d annotated ids have no text in the corpus' % len(missing))

    #: column order from the first row, then the joined-in text fields
    cols = collections.OrderedDict()
    for r in rows:
        for k, v in r.items():
            if k in SKIP:
                continue
            if k not in cols or (cols[k] == 'TEXT' and v is not None):
                cols.setdefault(k, sqltype(v))
    for k in ('model', 'text'):
        cols[k] = 'TEXT'
    cols['n_chars'] = 'INTEGER'
    cols['schema_version'] = 'TEXT'
    for t in TROPES:
        cols['llm_' + t] = 'INTEGER'
        cols['rx_' + t] = 'INTEGER'

    out = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    if os.path.exists(out):
        os.remove(out)
    db = sqlite3.connect(out)
    names = list(cols)
    db.execute('CREATE TABLE stories (%s, PRIMARY KEY (id))'
               % ', '.join('"%s" %s' % (k, v) for k, v in cols.items()))

    n = 0
    for r in rows:
        t = text.get(r['id'])
        if t is None:
            continue
        rec = {}
        for k in names:
            v = r.get(k)
            if isinstance(v, bool):
                v = int(v)
            elif isinstance(v, list):
                v = json.dumps(v)
            rec[k] = v
        rec['model'] = t.get('model')
        rec['text'] = t.get('text')
        rec['n_chars'] = len(t.get('text') or '')
        rec['schema_version'] = version
        for tr in TROPES:
            d = (r.get('tropes') or {}).get(tr) or {}
            rec['llm_' + tr] = int(bool(d.get('llm')))
            rec['rx_' + tr] = int(bool(d.get('regex')))
        db.execute('INSERT INTO stories (%s) VALUES (%s)'
                   % (', '.join('"%s"' % k for k in names),
                      ', '.join('?' * len(names))),
                   [rec.get(k) for k in names])
        n += 1

    for c in INDEXED:
        if c in cols:
            db.execute('CREATE INDEX "ix_%s" ON stories ("%s")' % (c, c))
    #: full-text over the stories themselves, so the UI can search prose as well
    #: as filter on annotations
    db.execute('CREATE VIRTUAL TABLE stories_fts USING fts5(id, text)')
    db.execute('INSERT INTO stories_fts SELECT id, text FROM stories')
    db.commit()

    print('%s: %d rows, %d columns, %.1f MB'
          % (os.path.basename(out), n, len(names), os.path.getsize(out) / 1e6))
    print('\nindexed for filtering: %s' % ', '.join(c for c in INDEXED if c in cols))
    print('\ntry:')
    print("  SELECT demonym, arm, substr(text,1,60) FROM stories")
    print("   WHERE opponent='institution' AND opponent_specificity='named';")
    print("  SELECT * FROM stories WHERE mood='unsettling' AND arm='base';")
    print("  SELECT s.* FROM stories s JOIN stories_fts f ON s.id=f.id")
    print("   WHERE stories_fts MATCH 'olive grove';")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
