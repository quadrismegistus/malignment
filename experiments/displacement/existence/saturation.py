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

    python -m experiments.displacement.existence.saturation
"""
import collections, statistics as st, math
from malignment import ch, charge, roster
eps = roster.endpoints()
eps = eps[0] if isinstance(eps, tuple) else eps
print("endpoint pairs: %d"%len(eps))
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
def band(s): return "lo <0.33" if s<0.33 else ("mid .33-.66" if s<0.66 else "hi >=0.66")
by=collections.defaultdict(lambda: {"same":[], "none":[], "n":0})
for b,a in sorted(eps.items()):
    rows=ch.query("SELECT prompt, word, (p_aligned-p_base) AS delta, cls "
        "FROM movement_v4 WHERE base='%s' AND aligned='%s' "
        "AND frame_base='' AND frame_aligned=''"
        %(b.replace("'","\\'"),a.replace("'","\\'")), limit_bytes=None)
    cells=collections.defaultdict(list)
    for r in rows: cells[r['prompt']].append(r)
    for q,wr in cells.items():
        kd=kinds(q); s=sat(q)
        if not kd or s is None: continue
        fl=[(r['word'],float(r['delta'])) for r in wr if r['cls']=='faller' and r['word'] in kd]
        if not fl: continue
        tf=max(fl,key=lambda x:-x[1]); fk=kd.get(tf[0])
        if not fk or fk=="NONE": continue
        same=[float(r['delta']) for r in wr if r['cls']=='riser' and kd.get(r['word'])==fk]
        none=[float(r['delta']) for r in wr if r['cls']=='riser' and kd.get(r['word'])=="NONE"]
        if not same or not none: continue
        rec=by[(b+">"+a, band(s))]
        rec["same"]+=same; rec["none"]+=none; rec["n"]+=1
print("\nSAME-KIND vs NONE-KIND, STRATIFIED BY PROMPT SATURATION")
print("faithful to adjacency.py: endpoint pairs, deltas POOLED per lineage,")
print("then one median each. raw edge. >=10 qualifying cells per lineage.\n")
print("%-14s %9s %8s %10s %10s %8s %10s"%("sat band","lineages","cells","same med","none med","up/dn","p"))
for bd in ("lo <0.33","mid .33-.66","hi >=0.66"):
    up=dn=0; nc=0; sm=[]; nm=[]
    for (lin,b2),rec in by.items():
        if b2!=bd or rec["n"]<10: continue
        nc+=rec["n"]
        ms=st.median(rec["same"]); mn=st.median(rec["none"])
        sm.append(ms); nm.append(mn)
        if ms>mn: up+=1
        elif mn>ms: dn+=1
    t=up+dn; k=min(up,dn)
    p=min(1.0,2*sum(math.comb(t,i) for i in range(k+1))/2**t) if t else 1.0
    print("%-14s %9d %8d %10.5f %10.5f %8s %10.5f"
          %(bd,t,nc,st.median(sm) if sm else 0,st.median(nm) if nm else 0,
            "%d/%d"%(up,dn),p))
