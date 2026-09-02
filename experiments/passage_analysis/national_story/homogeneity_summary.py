"""Homogenisation as percent change: within, between and overall, by arm and frame.

    python homogeneity_summary.py

## THE THREE QUANTITIES

    WITHIN    mean Hamming distance between two stories of the SAME demonym
    BETWEEN   ... of DIFFERENT demonyms
    OVERALL   ... of any two stories, ignoring demonym

OVERALL is the mix, so it is what a naive "is the output more homogeneous"
question measures, and it is the least informative of the three: a fall in WITHIN
and a rise in BETWEEN can leave it almost unmoved.

    DEMONYM SHARE = (between - within) / overall

How much of the distance between two stories is attributable to their being from
different nationalities. This is the "do all demonyms become one story" question
as a single number, and the honest headline is that it is SMALL in both arms --
between 1% and 8% -- so alignment multiplies a minor term.

## WHY THE POOLED ROW IS NOT A SUMMARY

WORLD and OUTCOME move in OPPOSITE directions and OUTCOME is the larger effect,
so the ALL row reports OUTCOME with the WORLD effect partly cancelled out of it.
Quoting the pooled number as "alignment makes stories more diverse" would be
true of the arithmetic and false of the phenomenon. Read the two groups.

Equal stories per demonym per group, 300 draws, fixed seed. 18 lineages qualify
for the arm contrast and 18 for the frame contrast.
"""
import json, collections, random, sys, os
sys.path.insert(0,'/Users/rj416/github/malignment/experiments/national_story')
from demonym_separation import totals, ALL, WORLD, OUTCOME
from scipy.stats import wilcoxon, binomtest
F='/Users/rj416/github/malignment/experiments/national_story/conflict_nocap.jsonl'
R=[json.loads(l) for l in open(F)]
PD, DR, MIND = 3, 300, 4

def run(pick_a, pick_b, label_a, label_b, title):
    cells=collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
    for r in R:
        g = 'a' if pick_a(r) else ('b' if pick_b(r) else None)
        if g: cells[r['lineage']][g][r['demonym']].append(r)
    rng=random.Random(20260901)
    print('='*96); print(title); print('='*96)
    print('%-9s %-24s %9s %9s %9s %8s   %s' % ('fields','measure',label_a,label_b,'change','%change','lineages'))
    for glab,FL in (('ALL',ALL),('WORLD',WORLD),('OUTCOME',OUTCOME)):
        acc={0:[[],[]],1:[[],[]],2:[[],[]]}
        for lin,d in sorted(cells.items()):
            if 'a' not in d or 'b' not in d: continue
            dems=[x for x in sorted(set(d['a'])&set(d['b']))
                  if len(d['a'][x])>=PD and len(d['b'][x])>=PD]
            if len(dems)<MIND: continue
            s=[[0.0]*3,[0.0]*3]; k=0
            for _ in range(DR):
                g=[]
                for grp in ('a','b'):
                    sub={x:rng.sample(d[grp][x],PD) for x in dems}
                    g.append(totals(sub,FL))
                if any(x is None for x in g): continue
                for gi in (0,1):
                    for j in range(3): s[gi][j]+=g[gi][j]
                k+=1
            if not k: continue
            for j in range(3):
                acc[j][0].append(s[0][j]/k); acc[j][1].append(s[1][j]/k)
        if not acc[0][0]:
            print('%-9s  nothing qualifies' % glab); continue
        n=len(acc[0][0])
        for j,mlab in ((0,'WITHIN demonym'),(1,'BETWEEN demonyms'),(2,'OVERALL (all pairs)')):
            A,B=acc[j][0],acc[j][1]
            ma,mb=sum(A)/n,sum(B)/n
            diffs=[y-x for x,y in zip(A,B)]
            up=sum(1 for x in diffs if x>0); dn=sum(1 for x in diffs if x<0)
            pw=wilcoxon(diffs).pvalue if n>5 else float('nan')
            print('%-9s %-24s %9.4f %9.4f %+9.4f %+7.1f%%   %d up %d down  p_w %.3g'
                  % (glab if j==0 else '', mlab, ma, mb, mb-ma, 100*(mb-ma)/ma, up, dn, pw))
        # demonym share of total distance
        A=[(b-w)/t for w,b,t in zip(acc[0][0],acc[1][0],acc[2][0])]
        B=[(b-w)/t for w,b,t in zip(acc[0][1],acc[1][1],acc[2][1])]
        diffs=[y-x for x,y in zip(A,B)]
        up=sum(1 for x in diffs if x>0); dn=sum(1 for x in diffs if x<0)
        print('%-9s %-24s %8.2f%% %8.2f%% %+8.2f%% %8s   %d up %d down  p_w %.3g'
              % ('', 'DEMONYM SHARE of total', 100*sum(A)/n, 100*sum(B)/n,
                 100*(sum(B)/n-sum(A)/n), '', up, dn,
                 wilcoxon(diffs).pvalue if n>5 else float('nan')))
        print('%-9s %s' % ('', '-'*86))
    print()

run(lambda r: r['arm']=='base' and r['frame']=='raw',
    lambda r: r['arm']=='aligned' and r['frame']=='raw',
    'base','aligned','ARM:  base -> aligned   (raw frame)')
run(lambda r: r['arm']=='aligned' and r['frame']=='raw',
    lambda r: r['arm']=='aligned' and r['frame']=='prefill',
    'raw','prefill','FRAME:  aligned raw -> aligned prefill')
