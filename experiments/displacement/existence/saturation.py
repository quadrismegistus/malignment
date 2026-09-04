"""Is the same-kind landing result conditional on what the prompt makes available?

`adjacency.py` finds freed mass landing on same-kind words rather than NONE-kind
ones, 47 of 49 lineages. Its population already guards the obvious artifact: a
cell qualifies only if BOTH a same-kind and a none-kind riser exist, so a fully
saturated prompt -- one whose candidate field is all one kind -- never enters the
comparison.

**But that guard requires PRESENCE, not BALANCE.** A prompt with 60 VIOLENT
candidates and 3 NONE ones qualifies. So this stratifies the same comparison by
how much of the field is one kind:

    saturation = share of a prompt's rated words carried by its top non-NONE kind

Saturation is a FRAME property, not a lift one: corr(saturation, frame) = +0.826,
corr(saturation, lift) = -0.025. So this is not the same cut as the dose work.

Faithful to `adjacency.py` on the three things that moved the answer when they
were done loosely: the population is `roster.endpoints()` (50 pairs, NOT every
raw edge in the store -- ladder rungs and transitive edges are pseudo-replication),
deltas are POOLED per lineage before one median is taken (not a median per cell
then a median of those), and the top faller is the most negative delta among
words carrying a rating.

**AND IT IS CROSSED WITH LIFT, because not doing so hid a mixture.** Part 1 of
this folder stratifies by dose and by lift; `adjacency.py` stratifies by neither,
and no reason for the difference is written down. A first pass here stratified by
saturation alone and reported the low-saturation band as an exact null (24/24).
That band decomposes: within it the effect runs monotonically with lift, from
13/33 REVERSED at low lift to 25/19 and 24/15. The null was two opposite things
averaged.

Saturation is a frame property and lift is orthogonal to it
(corr(saturation, frame) = +0.826, corr(saturation, lift) = -0.025), so the two
cuts are independent and the cross-tabulation is not a partition of one variable.

Bands: saturation at equal thirds; lift at 0.5 and 1.2. Neither was
pre-declared. Nine cells, so the one p of 0.0045 is 0.04 after Bonferroni.

    python -m experiments.displacement.existence.saturation
"""
import collections, statistics as st, math
from malignment import ch, charge, roster
eps = roster.endpoints()[0]
kc={}
def kinds(q):
    if q not in kc: kc[q]=charge.kinds(q) or {}
    return kc[q]
def sat(q):
    kk=kinds(q)
    if len(kk)<5: return None
    cc=collections.Counter(kk.values()); tot=sum(cc.values())
    c2=[(a,b) for a,b in cc.items() if a!="NONE"]
    return (max(b for a,b in c2)/tot) if c2 else 0.0
def sband(s): return "lo" if s<0.33 else ("mid" if s<0.66 else "hi")
def lband(l): return "L-lo" if l<0.5 else ("L-mid" if l<1.2 else "L-hi")
by=collections.defaultdict(lambda: {"same":[], "none":[], "n":0})
for b,a in sorted(eps.items()):
    lift={p:float(v) for (p,bb),v in charge.lifts_per_lineage(b).items()}
    if not lift: continue
    rows=ch.query("SELECT prompt, word, (p_aligned-p_base) AS delta, cls "
        "FROM movement_v4 WHERE base='%s' AND aligned='%s' "
        "AND frame_base='' AND frame_aligned=''"
        %(b.replace("'","\\'"),a.replace("'","\\'")), limit_bytes=None)
    cells=collections.defaultdict(list)
    for r in rows: cells[r['prompt']].append(r)
    for q,wr in cells.items():
        kd=kinds(q); s=sat(q); L=lift.get(q)
        if not kd or s is None or L is None: continue
        fl=[(r['word'],float(r['delta'])) for r in wr if r['cls']=='faller' and r['word'] in kd]
        if not fl: continue
        tf=max(fl,key=lambda x:-x[1]); fk=kd.get(tf[0])
        if not fk or fk=="NONE": continue
        same=[float(r['delta']) for r in wr if r['cls']=='riser' and kd.get(r['word'])==fk]
        none=[float(r['delta']) for r in wr if r['cls']=='riser' and kd.get(r['word'])=="NONE"]
        if not same or not none: continue
        rec=by[(b+">"+a, sband(s), lband(L))]
        rec["same"]+=same; rec["none"]+=none; rec["n"]+=1
print("SAME-KIND vs NONE-KIND, crossed by SATURATION and LIFT")
print("endpoint pairs, pooled per lineage, >=10 cells per lineage-cell\n")
print("%-6s %-7s %9s %8s %10s %10s %8s %9s"
      %("sat","lift","lineages","cells","same med","none med","up/dn","p"))
for sb in ("lo","mid","hi"):
    for lb in ("L-lo","L-mid","L-hi"):
        up=dn=0; nc=0; sm=[]; nm=[]
        for (lin,s2,l2),rec in by.items():
            if (s2,l2)!=(sb,lb) or rec["n"]<10: continue
            nc+=rec["n"]; ms=st.median(rec["same"]); mn=st.median(rec["none"])
            sm.append(ms); nm.append(mn)
            if ms>mn: up+=1
            elif mn>ms: dn+=1
        t=up+dn
        if t<8: 
            print("%-6s %-7s %9d %8d   (too few lineages)"%(sb,lb,t,nc)); continue
        k=min(up,dn)
        p=min(1.0,2*sum(math.comb(t,i) for i in range(k+1))/2**t)
        print("%-6s %-7s %9d %8d %10.5f %10.5f %8s %9.5f"
              %(sb,lb,t,nc,st.median(sm),st.median(nm),"%d/%d"%(up,dn),p))
    print()
