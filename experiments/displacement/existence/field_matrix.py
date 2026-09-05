"""WHICH semantic field substitutes for WHICH? -- with the availability control.

`adjacency.py` establishes that freed mass leaves the top faller's own USAS field
(10/38 fine, 10/39 coarse) and lands in a classified word rather than an
unclassified one (38/7, 41/5). This asks WHERE it goes.

THE BASELINE IS THE WHOLE QUESTION. Against a GLOBAL base rate the diagonal
dominates -- body->body x8.2, food->food x14.6, architecture->architecture x19.7 --
and that is prompt composition, not routing: a body-scene prompt offers mostly
body words, so its fallers and its risers are both body words. The denominator
here is instead **the base distribution's own mass over that cell's candidates**,
so the ratio asks whether mass went to a domain MORE than that prompt's own
vocabulary made likely.

Under that baseline **the diagonal disappears from every row**, which is the
availability confound removed rather than a different finding.

    python -m experiments.displacement.existence.field_matrix
"""
import collections
from malignment import ch, fields, roster
eps=roster.endpoints()[0]
_u={}
def dom(w):
    if w not in _u:
        try: _u[w]=frozenset(c[0] for c in (fields.usas(w,names=False) or ()) if c)
        except Exception: _u[w]=frozenset()
    return _u[w]
NAMES={'A':'general/abstract','B':'the body','E':'emotion','F':'food','G':'govt',
 'H':'architecture','I':'money','K':'entertainment','L':'life & living','M':'movement',
 'N':'numbers','O':'substances','P':'education','Q':'linguistic acts','S':'social',
 'T':'time','W':'world','X':'psychological','Y':'science','Z':'grammar/names','C':'arts'}
num=collections.defaultdict(collections.Counter)  # from -> to -> observed riser share
den=collections.defaultdict(collections.Counter)  # from -> to -> AVAILABLE share
cnt=collections.Counter()
for b,a in sorted(eps.items()):
    rows=ch.query("SELECT prompt, word, p_base, (p_aligned-p_base) AS delta, cls "
        "FROM movement_v4 WHERE base='%s' AND aligned='%s' "
        "AND frame_base='' AND frame_aligned=''"
        %(b.replace("'","\\'"),a.replace("'","\\'")),limit_bytes=None)
    cells=collections.defaultdict(list)
    for r in rows: cells[r['prompt']].append(r)
    for q,wr in cells.items():
        fl=[(r['word'],float(r['delta'])) for r in wr if r['cls']=='faller']
        ri=[(r['word'],float(r['delta'])) for r in wr if r['cls']=='riser']
        if not fl or not ri: continue
        F=dom(max(fl,key=lambda x:-x[1])[0])
        if not F: continue
        rt=sum(d for _,d in ri)
        # AVAILABILITY: base-distribution mass over every candidate in this cell
        av=collections.Counter(); at=0.0
        for r in wr:
            pb=float(r['p_base']); T=dom(r['word'])
            if not T: continue
            at+=pb
            for t in T: av[t]+=pb/len(T)
        if rt<=0 or at<=0: continue
        obs=collections.Counter()
        for w,d in ri:
            T=dom(w)
            if not T: continue
            for t in T: obs[t]+=(d/rt)/len(T)
        for f in F:
            cnt[f]+=1.0/len(F)
            for t in set(obs)|set(av):
                num[f][t]+=obs[t]/len(F)
                den[f][t]+=(av[t]/at)/len(F)
print("FIELD SUBSTITUTION, BASELINED ON WHAT EACH PROMPT MAKES AVAILABLE")
print("ratio = (riser mass share of domain T) / (base-distribution share of T")
print("in the SAME cell). >1 = mass goes there MORE than availability predicts.")
print("Rows with >=500 weighted cells. Diagonal marked <-- .\n")
print("%-20s %7s   %s"%("faller domain","cells","strongest destinations"))
for f,_ in sorted(cnt.items(), key=lambda x:-x[1]):
    if cnt[f]<500: continue
    en=[]
    for t in num[f]:
        d=den[f][t]
        if d<=0.005*cnt[f]: continue
        r=num[f][t]/d
        if num[f][t]/cnt[f] < 0.015: continue
        en.append((r,t,num[f][t]/cnt[f]))
    en.sort(reverse=True)
    line="%-20s %7.0f   "%(("%s %s"%(f,NAMES.get(f,'?')))[:20], cnt[f])
    line+="  ".join("%s%s x%.2f"%(t,"<--" if t==f else "",r) for r,t,_ in en[:5])
    print(line)

# ---- how much does the destination depend on the origin? ----
import collections as _c
tops = _c.Counter()
present = _c.Counter()
rows_used = 0
for f in cnt:
    if cnt[f] < 500:
        continue
    rows_used += 1
    en = []
    for t in num[f]:
        d = den[f][t]
        if d <= 0.005 * cnt[f] or num[f][t] / cnt[f] < 0.015:
            continue
        en.append((num[f][t] / d, t))
    en.sort(reverse=True)
    if en:
        tops[en[0][1]] += 1
    for _, t in en[:5]:
        present[t] += 1
print()
print("DOES THE DESTINATION DEPEND ON THE ORIGIN? %d source domains." % rows_used)
print("  in the top 5 destinations of how many source domains:")
for t, n in present.most_common(6):
    print("     %s %-18s %d of %d" % (t, NAMES.get(t, "?"), n, rows_used))
print("  is the single strongest destination for:")
for t, n in tops.most_common(5):
    print("     %s %-18s %d" % (t, NAMES.get(t, "?"), n))
