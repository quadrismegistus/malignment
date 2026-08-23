"""self-surprisal ~ log p(opening) + delta, fitted PER LINEAGE, at five windows.

    M1  all rows        surprisal(w) ~ log p_gen              forced + unforced
    M2  forced only     surprisal(w) ~ log p_gen + delta      separates the two

Windows are token counts AFTER the opening word: +1, 10, 20, 30, all. Finding A
found its effect at +1 and null at every other index, so a whole-passage mean
can average a real onset effect away.

UNIT IS THE LINEAGE. Coefficients are fitted within each pair, then summarised
across pairs with a sign test -- never pooled over rows, because row counts
differ 5x across pairs and a pooled fit weights by data volume.
"""
import json, math, statistics as S, sys, collections
sys.path.insert(0, '/Users/rj416/github/malign-logits')
import numpy as np
from malign_logits import ch

A = json.load(open('/Users/rj416/github/malign-logits/data/forced_arms_46reps_drmatch.json'))['cells']
prob, delt = {}, {}
for c in A:
    for w, qk, dk in (('faller','faller_q','faller_delta'), ('matched','matched_q','matched_delta'),
                      ('riser','riser_q','riser_delta'), ('riser_matched','riser_matched_q','riser_matched_delta')):
        word = c.get(w)
        if not word: continue
        k = (c['pair'], c['prompt'], word)
        if c.get(qk) is not None: prob[k] = float(c[qk])
        if c.get(dk) is not None: delt[k] = float(c[dk])
    kb = (c['pair'], c['prompt'], c.get('faller'))
    if c.get('faller_p') is not None: prob[('B',) + kb[1:]] = float(c['faller_p'])

WIN = [1, 10, 20, 30, 0]          # 0 = all
def wmean(lp, w):
    seg = lp if w == 0 else lp[:w]
    return -sum(seg)/len(seg) if seg else None

pairs = sorted({c['pair'] for c in A})
fits = collections.defaultdict(list)     # (model, arm, win, term) -> [coef per lineage]
for i, pr in enumerate(pairs, 1):
    b, a = pr.split('>')
    q = ("SELECT model, prompt, forced_word, scorer, logprobs FROM malign_logits.gen_scores "
         "WHERE corpus='passage' AND scorable=1 AND scorer = model AND model IN (%s,%s)"
         % (repr(b).replace('"',"'"), repr(a).replace('"',"'")))
    try: res = ch.query(q)
    except Exception: continue
    rows = []
    for x in res:
        lp = [v for v in (x['logprobs'] or []) if v is not None]
        if len(lp) < 35: continue
        arm = 'aligned' if x['model'] == a else 'base'
        fw = x['forced_word']
        if fw:
            k = (pr, x['prompt'], fw)
            p = prob.get(k) if arm == 'aligned' else prob.get(('B', x['prompt'], fw))
            if not p or p <= 0: continue
            rows.append((arm, 1, math.log(p), delt.get(k, 0.0), lp))
        else:
            rows.append((arm, 0, lp[0], 0.0, lp[1:]))     # dose = own opening logprob
    for arm in ('aligned','base'):
        for w in WIN:
            sub = [r for r in rows if r[0]==arm]
            X1 = np.array([[1.0, r[2]] for r in sub])
            y1 = np.array([wmean(r[4], w) for r in sub], dtype=float)
            ok = ~np.isnan(y1)
            if ok.sum() >= 60:
                c1 = np.linalg.lstsq(X1[ok], y1[ok], rcond=None)[0]
                fits[('M1', arm, w, 'logp')].append(c1[1])
            f = [r for r in sub if r[1]==1]
            if len(f) >= 60:
                X2 = np.array([[1.0, r[2], r[3]] for r in f])
                y2 = np.array([wmean(r[4], w) for r in f], dtype=float)
                ok2 = ~np.isnan(y2)
                if ok2.sum() >= 60:
                    c2 = np.linalg.lstsq(X2[ok2], y2[ok2], rcond=None)[0]
                    fits[('M2', arm, w, 'logp')].append(c2[1])
                    fits[('M2', arm, w, 'delta')].append(c2[2])
    if i % 10 == 0: print('  %d/%d pairs' % (i, len(pairs)), flush=True)

def binom(k, n):
    return min(1.0, 2*sum(math.comb(n,j) for j in range(0, min(k, n-k)+1))/2.0**n) if n else float('nan')

def show(model, arm):
    print()
    print('%s  arm=%s   (unit = the lineage; median coefficient across pairs)' % (model, arm))
    print('  %-8s %-7s %5s %11s %9s %10s' % ('window','term','n','median','up/down','sign p'))
    for w in WIN:
        for term in ('logp','delta'):
            v = fits.get((model, arm, w, term))
            if not v: continue
            up = sum(1 for x in v if x > 0); dn = sum(1 for x in v if x < 0)
            print('  %-8s %-7s %5d %11.5f %9s %10.5f'
                  % ('+%d' % w if w else 'all', term, len(v), S.median(v),
                     '%d/%d' % (up, dn), binom(min(up,dn), up+dn)))

for m in ('M1','M2'):
    for arm in ('aligned','base'):
        show(m, arm)
