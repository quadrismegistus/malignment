"""Cheap text features against the coded narrative_A label. Calibration, not a claim.

Ground truth: 13,557 passages carrying a coder's `narrative_A`, of which 13,557
have text recoverable from passC (triage + sample). No LLM is called here; every
feature is arithmetic over the string, which is the whole point -- the corpus is
~500K passages and coded annotation does not scale to it.
"""
import csv, collections, json, math, re, statistics as S, bisect, zlib
import pyarrow.parquet as pq

ROOT = 'experiments/passage_analysis'
lab = {}
for r in csv.DictReader(open(ROOT + '/drift_geometry/results/drift_by_passage.csv')):
    lab[r['pid']] = (r['narrative_A'], r['arm'], r['pair'], int(r['n_sents'] or 0))

text = {}
for f in ('triage', 'sample'):
    t = pq.read_table(ROOT + '/interiority_in_passages/results/passC/%s.parquet' % f).to_pydict()
    for i, pid in enumerate(t['id']):
        if pid in lab and pid not in text:
            text[pid] = t['text'][i] or ''
print('labelled: %d   with text: %d' % (len(lab), len(text)))

W = re.compile(r"[A-Za-z']+")
NONASCII = re.compile(r'[^\x00-\x7F]')
PUNCT = re.compile(r'[^\w\s]')

def feats(s):
    w = W.findall(s.lower())
    n = len(w) or 1
    c = collections.Counter(w)
    top = c.most_common(1)[0][1] / n if c else 0.0
    ttr = len(c) / n
    nonascii = len(NONASCII.findall(s)) / max(len(s), 1)
    punct = len(PUNCT.findall(s)) / max(len(s), 1)
    digit = sum(ch.isdigit() for ch in s) / max(len(s), 1)
    upper = sum(ch.isupper() for ch in s) / max(len(s), 1)
    nl = s.count('\n') / max(len(s), 1)
    # repeated bigrams
    bg = collections.Counter(zip(w, w[1:]))
    bgrep = (sum(v for v in bg.values() if v > 1) / max(len(w) - 1, 1)) if len(w) > 1 else 0.0
    # gzip compressibility: junk repeats, so it compresses
    b = s.encode('utf8', 'ignore')
    comp = len(zlib.compress(b, 6)) / max(len(b), 1)
    # mean word length, and share of very long "words" (mangling signal)
    mwl = sum(len(x) for x in w) / n
    longw = sum(1 for x in w if len(x) > 14) / n
    return dict(top_word_share=top, ttr=ttr, nonascii=nonascii, punct=punct,
                digit=digit, upper=upper, newline=nl, bigram_rep=bgrep,
                gzip_ratio=comp, mean_word_len=mwl, long_word_share=longw,
                n_words=float(n))

def auc(pos, neg):
    neg = sorted(neg); tot = 0.0
    for p in pos:
        lo = bisect.bisect_left(neg, p); hi = bisect.bisect_right(neg, p)
        tot += lo + 0.5 * (hi - lo)
    return tot / (len(pos) * len(neg))

rows = []
for pid, s in text.items():
    nar, arm, pair, nsent = lab[pid]
    d = feats(s); d['n_sents'] = float(nsent)
    rows.append((pid, nar, arm, pair, d))
print('featurised: %d' % len(rows))

FE = sorted(rows[0][4])
print()
print('%-18s %8s %8s %8s' % ('feature', 'AUC', 'AUC base', 'AUC align'))
res = []
for f in FE:
    pos = [r[4][f] for r in rows if r[1] == 'False']
    neg = [r[4][f] for r in rows if r[1] == 'True']
    a = auc(pos, neg)
    ab = auc([r[4][f] for r in rows if r[1] == 'False' and r[2] == 'base'],
             [r[4][f] for r in rows if r[1] == 'True' and r[2] == 'base'])
    aa = auc([r[4][f] for r in rows if r[1] == 'False' and r[2] == 'aligned'],
             [r[4][f] for r in rows if r[1] == 'True' and r[2] == 'aligned'])
    res.append((abs(a - 0.5), f, a, ab, aa))
res.sort(reverse=True)
for _, f, a, ab, aa in res:
    print('%-18s %8.3f %8.3f %8.3f' % (f, a, ab, aa))

json.dump([{'pid': p, 'narrative_A': n, 'arm': ar, 'pair': pr, **d}
           for p, n, ar, pr, d in rows],
          open('experiments/instrument_calibrations/junk_passages/results/features.json', 'w'))
print()
print('-> results/features.json  (%d rows)' % len(rows))
