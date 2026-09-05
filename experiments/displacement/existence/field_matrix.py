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
from malignment import ch, charge, fields, roster
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
#: DOSED. Same accumulation keyed by lift band, so the funnel can be asked
#: whether it INTENSIFIES with charge. lift is per (prompt, base) and English
#: only, so a prompt without one is dropped from the dosed tables and kept in
#: the pooled one above.
lnum=collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
lden=collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
lcnt=collections.defaultdict(collections.Counter)
#: PER LINEAGE, so the lift trend gets a unit. The pooled ratios above are
#: descriptive; a trend over 50 lineages pooled is not a result until each
#: lineage has contributed its own value and they have been counted.
pl=collections.defaultdict(lambda: collections.defaultdict(
    lambda: collections.defaultdict(collections.Counter)))
def lband(v): return "L-lo" if v<0.5 else ("L-mid" if v<1.2 else "L-hi")
for b,a in sorted(eps.items()):
    rows=ch.query("SELECT prompt, word, p_base, (p_aligned-p_base) AS delta, cls "
        "FROM movement_v4 WHERE base='%s' AND aligned='%s' "
        "AND frame_base='' AND frame_aligned=''"
        %(b.replace("'","\\'"),a.replace("'","\\'")),limit_bytes=None)
    lift_here={q:float(v) for (q,_b),v in charge.lifts_per_lineage(b).items()}
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
        lf=lift_here.get(q)
        lb=lband(lf) if lf is not None else None
        for f in F:
            cnt[f]+=1.0/len(F)
            for t in set(obs)|set(av):
                num[f][t]+=obs[t]/len(F)
                den[f][t]+=(av[t]/at)/len(F)
            if lb:
                lcnt[lb][f]+=1.0/len(F)
                for t in set(obs)|set(av):
                    lnum[lb][f][t]+=obs[t]/len(F)
                    lden[lb][f][t]+=(av[t]/at)/len(F)
                lin=b+">"+a
                pl[lin][lb][f]["_n"]+=1.0/len(F)
                for t in set(obs)|set(av):
                    pl[lin][lb][f]["n_"+t]+=obs[t]/len(F)
                    pl[lin][lb][f]["d_"+t]+=(av[t]/at)/len(F)
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


# ---- DOSED BY LIFT: does the funnel intensify with charge? ----
print()
print("DOSED BY LIFT. Same availability baseline, split by the prompt's lift.")
print("Q enrichment is averaged over every source domain with >=100 weighted")
print("cells IN THAT BAND, so a band is never carried by one domain.\n")
print("%-8s %9s %12s %12s %12s %14s"
      % ("band", "cells", "mean Q enr", "mean X enr", "mean S enr", "L->Q"))
for lb in ("L-lo", "L-mid", "L-hi"):
    C, N, D = lcnt[lb], lnum[lb], lden[lb]
    tot = sum(C.values())
    if tot < 200:
        print("%-8s %9.0f   (too few)" % (lb, tot)); continue
    row = {}
    for tgt in ("Q", "X", "S"):
        vals = []
        for f in C:
            if C[f] < 100 or f == tgt:
                continue
            d = D[f].get(tgt, 0.0)
            if d <= 0.005 * C[f]:
                continue
            vals.append(N[f].get(tgt, 0.0) / d)
        row[tgt] = (sum(vals) / len(vals)) if vals else float("nan")
    lq = float("nan")
    if C.get("L", 0) >= 50 and D["L"].get("Q", 0) > 0:
        lq = N["L"]["Q"] / D["L"]["Q"]
    print("%-8s %9.0f %12.3f %12.3f %12.3f %14.3f"
          % (lb, tot, row["Q"], row["X"], row["S"], lq))
print()
print("  L is the domain holding kill / strangle / die; Q is linguistic acts.")
print("  L->Q printed only where the L row clears 50 weighted cells in the band.")


# ---- the lift trend, with the lineage as the unit ----
import math as _m
def _binom(k, n):
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(_m.comb(n, j)
               for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)

print()
print("THE SAME TREND WITH THE LINEAGE AS THE UNIT. Per lineage, enrichment")
print("in L-hi minus enrichment in L-lo; sign test over lineages. A lineage")
print("contributes only where BOTH bands clear 30 weighted cells for it.\n")
print("%-26s %9s %9s %11s" % ("contrast", "lineages", "up/dn", "p"))
for lab, src, tgt in (("Q enrichment, any source", None, "Q"),
                      ("L -> Q enrichment", "L", "Q"),
                      ("X enrichment, any source", None, "X"),
                      ("S enrichment, any source", None, "S")):
    up = dn = 0
    for lin, bands in pl.items():
        vals = {}
        for bd in ("L-lo", "L-hi"):
            fs = bands.get(bd, {})
            keys = [src] if src else [k for k in fs if k != tgt]
            n = d = 0.0
            tot = 0.0
            for f in keys:
                r = fs.get(f)
                if not r:
                    continue
                tot += r["_n"]
                n += r.get("n_" + tgt, 0.0)
                d += r.get("d_" + tgt, 0.0)
            if tot < 30 or d <= 0:
                vals = {}
                break
            vals[bd] = n / d
        if len(vals) != 2:
            continue
        if vals["L-hi"] > vals["L-lo"]:
            up += 1
        elif vals["L-hi"] < vals["L-lo"]:
            dn += 1
    t = up + dn
    print("%-26s %9d %9s %11.6f"
          % (lab, t, "%d/%d" % (up, dn), _binom(min(up, dn), t)))
