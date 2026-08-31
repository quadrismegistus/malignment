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
CORPUS = os.path.join(DATA, 'national_story', 'judged_stories_v2.jsonl')

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


#: which annotation each span witnesses, so the UI can label a highlight without
#: reverse-engineering the column name
SPAN_OF = {
    'opponent_span': 'opponent', 'fate_span': 'opponent_fate',
    'conflict_span': 'conflict_mode', 'ending_span': 'ending',
    'scale_span': 'resolution_scale', 'means_span': 'resolution_means',
    'setting_span': 'setting', 'small_community_span': 'small_community',
    'homecoming_span': 'homecoming', 'threat_span': 'threat',
    'temporality_span': 'temporality', 'romance_span': 'romance',
    'mood_span': 'mood', 'genre_span': 'genre',
    'nostalgia_span': 'nostalgia', 'elder_informant_span': 'elder_informant',
    'supernatural_span': 'supernatural',
    'collective_action_span': 'collective_action', 'renewal_span': 'renewal',
    'tradition_span': 'tradition', 'community_span': 'community_role',
    'constrains_span': 'community_constrains',
}


def locate(text, span):
    """-> (start, end) into the ORIGINAL text, or None.

    The annotator quotes verbatim but reflows whitespace, so an exact find misses
    a span that is genuinely present and merely rewrapped. Match on the
    whitespace-collapsed form and carry an index map back to original offsets,
    which is the same tolerance `check_spans` applies when it verifies them --
    a highlight and a verification that disagree about what counts as present
    would be worse than having no highlight at all.

    Returns None for spans that do not verify. About 6% do not; they are the
    annotator paraphrasing, and a UI must render them as unlocatable rather than
    guess a range."""
    if not text or not span:
        return None
    #: `'İ'.lower()` is TWO characters. Lowercasing while building a 1:1 index
    #: map silently desynchronises it, and the Turkish stories in this corpus
    #: made 54 of 12,165 offsets point at the wrong range while still looking
    #: like successful matches. Fold only where folding preserves length; the
    #: handful of characters that do not are matched case-sensitively instead,
    #: which costs a rare miss and never a wrong offset.
    fold = lambda c: c.lower() if len(c.lower()) == 1 else c
    norm, idx, prev_ws = [], [], True
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_ws:
                norm.append(' '); idx.append(i)
            prev_ws = True
        else:
            norm.append(fold(ch)); idx.append(i)
            prev_ws = False
    hay = ''.join(norm)
    needle = ''.join(fold(c) for c in ' '.join(span.split()))
    if not needle:
        return None
    p = hay.find(needle)
    if p < 0:
        return None
    return idx[p], idx[min(p + len(needle) - 1, len(idx) - 1)] + 1


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

    #: ONE ROW PER HIGHLIGHT. A UI wants (start, end, label) and should never
    #: have to search the prose for a quoted string itself -- two searchers will
    #: disagree on the first reflowed span. `located` is 0 when the annotator
    #: paraphrased instead of quoting; render those as unlocatable, not as a
    #: guessed range.
    db.execute('''CREATE TABLE spans (
        story_id TEXT, source TEXT, field TEXT, annotation TEXT, value TEXT,
        start INTEGER, end INTEGER, located INTEGER, quote TEXT)''')
    nsp = nloc = 0
    for r in rows:
        t = text.get(r['id'])
        if t is None:
            continue
        body = t.get('text') or ''
        for f, ann in SPAN_OF.items():
            q = r.get(f)
            if not q:
                continue
            loc = locate(body, q)
            nsp += 1; nloc += loc is not None
            db.execute('INSERT INTO spans VALUES (?,?,?,?,?,?,?,?,?)',
                       (r['id'], 'conflict_v1', f, ann, str(r.get(ann)),
                        loc[0] if loc else None, loc[1] if loc else None,
                        int(loc is not None), q))
        #: the story judge's own segmentation, same table, different source --
        #: it marks WHERE a text stops being a story, which is the other thing
        #: worth colouring
        for seg in (t.get('judge_segments') or t.get('segments') or []):
            q = seg.get('first_words')
            if not q:
                continue
            loc = locate(body, q)
            nsp += 1; nloc += loc is not None
            db.execute('INSERT INTO spans VALUES (?,?,?,?,?,?,?,?,?)',
                       (r['id'], 'judge_v1', 'segment', 'kind', seg.get('kind'),
                        loc[0] if loc else None, loc[1] if loc else None,
                        int(loc is not None), q))
    #: A SELECTED TABLE MUST SAY SO. Every row here already passed the
    #: pure-story gate, so there is no `pure_story` column to filter on and a
    #: consumer serving all rows is correct -- but nothing in the file said that,
    #: and a reader who cannot see a filter assumes there was none. The rates in
    #: this table are conditional on a gate whose survival rate runs from 2% to
    #: 95% by model, which is exactly the kind of thing that has to travel with
    #: the data rather than in a message.
    db.execute('CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)')
    for k, v in [
        ('gate', 'pure_story: judge overall == story AND every segment == story'),
        ('gate_applied', 'upstream, in conflict.py. EVERY row here is a pure '
                         'story; there is no pure_story column and none is needed'),
        ('gate_min_words', '200'),
        ('gate_max_words', 'none (an earlier 2000-word cap was removed: it cut '
                           '34.9% of base pure stories against 9.1% of aligned)'),
        ('gate_survival_warning', 'the pure-story rate is NOT uniform -- 52% for '
                                  'aligned/raw against 73% for aligned/prefill, '
                                  'and 2% to 95% across models. Rates computed '
                                  'over this table are conditional on it'),
        ('frames', 'raw = bare paratext; prefill = same paratext inside a chat '
                   'turn wrapper. ORTHOGONAL to arm; do not pool'),
        ('arms', 'base = pretrained checkpoint; aligned = any post-trained '
                 'member of the same lineage'),
        ('model_vs_lineage', 'lineage is the BASE checkpoint; model is the '
                             'actual one. One lineage carries several aligned '
                             'rungs. Group by model when the rung matters'),
        ('source_annotations', version),
        ('source_corpus', os.path.basename(CORPUS)),
        ('n_stories', str(n)),
        ('n_spans', str(nsp)),
        ('spans_located_pct', '%.1f' % (100 * nloc / max(1, nsp))),
        ('span_located_0_means', 'the annotator paraphrased instead of quoting; '
                                 'render as unhighlightable, never as a guessed '
                                 'range'),
    ]:
        db.execute('INSERT INTO meta VALUES (?,?)', (k, v))

    db.execute('CREATE INDEX ix_spans_story ON spans (story_id)')
    db.execute('CREATE INDEX ix_spans_ann ON spans (annotation)')

    for c in INDEXED:
        if c in cols:
            db.execute('CREATE INDEX "ix_%s" ON stories ("%s")' % (c, c))
    #: full-text over the stories themselves, so the UI can search prose as well
    #: as filter on annotations
    db.execute('CREATE VIRTUAL TABLE stories_fts USING fts5(id, text)')
    db.execute('INSERT INTO stories_fts SELECT id, text FROM stories')
    db.commit()

    print('%s: %d stories, %d columns, %d spans (%.1f%% located), %.1f MB'
          % (os.path.basename(out), n, len(names), nsp, 100 * nloc / max(1, nsp),
             os.path.getsize(out) / 1e6))
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
