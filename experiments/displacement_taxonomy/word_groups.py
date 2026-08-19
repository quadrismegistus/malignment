"""Group by DIRECTED word overlap: A-with-A and B-with-B only.

A relation running base->aligned over one axis and a relation running the axis
the other way are NOT the same group, they are two groups. Joining them and
flagging a sign, as the previous pass did, reproduces the harmonisers' own defect
in a different notation: it treats direction as an annotation on a shared thing
rather than as what distinguishes two things.

Mirror pairs -- one group's base words matching another group's aligned words --
are reported afterwards, as a relation BETWEEN groups.
"""
import sys, collections
sys.path.insert(0, ".")
import run as R

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "He started stroking his"
MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 3

st = R._stash(); rels = []
for k in st.keys():
    m = (st[k].get("meta") or {})
    if not (m.get("batch") and m["frame_prompt"].startswith(PROMPT)): continue
    for x in st[k]["result"]["relations"]:
        if x.get("a_words") and x.get("b_words"):
            rels.append({"pair": m["pair"], "name": x["name"], "conf": x.get("confidence"),
                         "A": {w.lower().strip("'s") for w in x["a_words"]},
                         "B": {w.lower().strip("'s") for w in x["b_words"]}})
print('PROMPT: "%s"   overlap threshold %d' % (PROMPT, MIN))
print("%d two-sided relations, %d lineages\n" % (len(rels), len({r["pair"] for r in rels})))

par = list(range(len(rels)))
def find(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
for i in range(len(rels)):
    for j in range(i+1, len(rels)):
        same = len(rels[i]["A"] & rels[j]["A"]) + len(rels[i]["B"] & rels[j]["B"])
        cross = len(rels[i]["A"] & rels[j]["B"]) + len(rels[i]["B"] & rels[j]["A"])
        #: join ONLY on same-direction overlap, and only when it beats the crossed
        #: reading, so a mirror pair can never be pulled into one group.
        if same >= MIN and same > cross:
            par[find(j)] = find(i)
G = collections.defaultdict(list)
for i in range(len(rels)): G[find(i)].append(i)
groups = sorted(G.values(), key=len, reverse=True)
lab = {}
for n, g in enumerate(groups, 1):
    for i in g: lab[i] = n
for n, g in enumerate(groups, 1):
    A = collections.Counter(w for i in g for w in rels[i]["A"])
    B = collections.Counter(w for i in g for w in rels[i]["B"])
    print("=" * 76)
    print("GROUP %d -- %d relation(s), %d lineage(s)" % (n, len(g), len({rels[i]["pair"] for i in g})))
    print("  base side:    %s" % ", ".join(w for w, _ in A.most_common(11)))
    print("  aligned side: %s" % ", ".join(w for w, _ in B.most_common(11)))
    print("=" * 76)
    for i in g:
        r = rels[i]
        print("   %-44s %-26s [%s]" % (r["name"][:44], r["pair"][:26], r["conf"]))
    print()
print("=" * 76)
print("MIRROR PAIRS -- group X's BASE words are group Y's ALIGNED words")
print("=" * 76)
found = 0
for a in range(len(groups)):
    for b in range(a+1, len(groups)):
        Aa = set().union(*[rels[i]["A"] for i in groups[a]])
        Ba = set().union(*[rels[i]["B"] for i in groups[a]])
        Ab = set().union(*[rels[i]["A"] for i in groups[b]])
        Bb = set().union(*[rels[i]["B"] for i in groups[b]])
        cross = len(Aa & Bb) + len(Ba & Ab)
        if cross >= MIN:
            found += 1
            print("  GROUP %d  <->  GROUP %d   (%d words cross)" % (a+1, b+1, cross))
            print("     %d has base %s" % (a+1, ", ".join(sorted(Aa & Bb))[:66]))
            print("     %d has those same words on the ALIGNED side" % (b+1))
            print("     lineages %d: %s" % (a+1, ", ".join(sorted({rels[i]["pair"] for i in groups[a]}))[:70]))
            print("     lineages %d: %s\n" % (b+1, ", ".join(sorted({rels[i]["pair"] for i in groups[b]}))[:70]))
if not found: print("  none")
