"""Stitch relations ACROSS frames, on the statement rather than on the roster.

    python cross_frame.py --doc          # write the blind grouping document
    python cross_frame.py --ari          # the measurement that rules out the alternative

## WHY NOT THE ROSTER, WHICH WOULD HAVE BEEN FREE

The obvious stitch is arithmetic: two operations from different frames are the
same relation if the same lineages perform them. Measured, label-free, with the
adjusted Rand index over the models both readings place:

    same frame, two raters        13 pairs   median ARI +0.361, max +0.741
    different frames             336 pairs   median ARI +0.000, max +0.701
      within one domain           68 pairs   median ARI +0.000
      across domains             268 pairs   median ARI +0.000
      identity template only      24 pairs   median ARI +0.000

Two raters reading the SAME frame carve the roster the same way. Two frames do
not, and the four identity prompts -- which differ by one noun -- do not either.
So membership is a property of the FRAME, not of the model: which lineages
displace is re-drawn from scratch on every prompt. That extends the direction
result rather than repeating it. Direction was already known not to be a model
property; this says membership is not either.

The consequence is the method. There is no roster signature to stitch on, so
the stitch has to be made on what the operation SAYS, and the arithmetic is
demoted from criterion to control.

## WHY THE DOCUMENT CARRIES STATEMENTS AND NOTHING ELSE

Words would leak the frame, and worse, they would supply an easier grouping than
the real one: give a rater `cock -> beard` beside `dick -> chin` and it can sort
by domain without ever considering the relation. Domain similarity is exactly
the confound, because the question is which relations SURVIVE a change of
domain. So the entries carry an id, the name the original rater chose, and the
statement it wrote -- which was written to describe a transformation, not a
topic -- and no frame, domain, model, or word.
"""
import argparse, collections, itertools, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import operation_graph as OG
import reversal_table as RT


def blind_readings():
    dom = RT.domains()
    out = []
    for prompt, n in sorted(RT.blind_prompts().items()):
        pairs, _ = OG.readings(prompt, n)
        for tag, v in pairs:
            if not tag.split(".")[0].endswith("b"):
                continue
            out.append(dict(prompt=prompt, domain=dom.get(prompt), tag=tag, v=v,
                            part={m["model"]: o["name"]
                                  for o in v.get("operations") or []
                                  for m in o.get("members") or []},
                            rev={r["model"] for r in v.get("reversed") or []}))
    return out


def ari(a, b):
    ks = sorted(set(a) & set(b))
    if len(ks) < 4:
        return None
    t = collections.Counter((a[k], b[k]) for k in ks)
    ra = collections.Counter(a[k] for k in ks)
    rb = collections.Counter(b[k] for k in ks)
    C = lambda n: n * (n - 1) / 2.0
    idx = sum(C(x) for x in t.values())
    ea, eb = sum(C(x) for x in ra.values()), sum(C(x) for x in rb.values())
    exp, mx = ea * eb / C(len(ks)), (ea + eb) / 2.0
    return (idx - exp) / (mx - exp) if mx != exp else 0.0


def ops(min_n=2):
    """Every blind operation with at least `min_n` members, newest id order stable."""
    out = []
    for r in blind_readings():
        rev = collections.defaultdict(set)
        for x in r["v"].get("reversed") or []:
            rev[x["operation"]].add(x["model"])
        for o in r["v"].get("operations") or []:
            mem = {m["model"] for m in o.get("members") or []}
            if len(mem) < min_n:
                continue
            out.append(dict(prompt=r["prompt"], domain=r["domain"], reading=r["tag"],
                            name=o["name"], statement=o.get("statement") or "",
                            members=sorted(mem), _members=o.get("members") or [],
                            reversers=sorted(rev.get(o["name"], set()))))
    #: SORTED BY STATEMENT so the id order carries no frame information. Sorting
    #: by prompt would put every sexual entry first and hand the rater the
    #: grouping it is being asked to discover.
    out.sort(key=lambda o: (o["statement"], o["name"]))
    for i, o in enumerate(out, 1):
        o["id"] = "O%02d" % i
    return out


TASK = """You will read %d entries. Each is ONE transformation, found in one body of
material, and named independently by one or two readers who could not see each
other. Each entry gives the sentence the material came from, how many systems
showed the transformation, every reader's name and description for it, and the
words cited on each side.

A word is written `word (n | a>b)`: `n` systems cited it, and it sat at rank `a`
before the change and rank `b` after, as a median over those systems. Rank 1 is
the most likely word. A FROM word lost ground; a TO word gained it.

Where an entry carries two names, two readers described that one transformation
independently, and you are seeing both of their words for it.

Your job is to say which of them are describing THE SAME transformation.

Group the entries. A group is a set of entries that name one underlying
transformation, however differently they word it and whatever material the
reader was looking at. Two entries belong together only if the MOVEMENT is the
same. They do NOT belong together merely because their words come from a
similar subject area: entries drawn from the same subject matter will look
alike, and separating a shared SUBJECT from a shared MOVEMENT is most of the
work here. A transformation that appears in several different subject areas is
more interesting than one confined to a single area, so look for those in
particular.

For each group give:
  name        a short label for the transformation itself
  statement   one or two sentences stating the movement in general terms, in
              your own words, at a level that covers every member
  members     the ids in it
  spans       whether its members appear to be drawn from one subject area or
              several, and which
  why         what makes these one transformation and not several

Then list, as `singletons`, the ids you could not place with anything.

Every id must appear exactly once, in a group or in singletons. Be willing to
return many small groups: a wrong merge destroys more than a missed one.

ENTRIES

%s
"""


def components(k=2):
    """Per frame, the k=2 components over its blind operations -- the unit to group.

    ## THE COMPONENT IS THE META-RELATION, NOT THE OPERATION

    Two raters read each frame and name the same relation differently:
    `Restraint Bleaching` and `Coercion Recedes Into Talk` are one thing, and
    `operation_graph` already establishes that by joining operations sharing at
    least k models. Handing the 59 raw operations to a grouping pass would ask it
    to rediscover across frames a merge already made WITHIN each frame on roster
    evidence, and to redo it on prose, which is the weaker evidence of the two.

    So the unit is the component, and it arrives carrying EVERY name its raters
    gave it. Multiple names per unit is the point rather than an inconvenience:
    it is the annotator's first signal that a relation survived being described
    twice by readers who could not see each other.
    """
    out, dom = [], RT.domains()
    for prompt, n in sorted(RT.blind_prompts().items()):
        pairs, _ = OG.readings(prompt, n)
        pairs = [(t, v) for t, v in pairs if t.split(".")[0].endswith("b")]
        if not pairs:
            continue
        G = OG.build(pairs)
        OPS = {x for x in G if G.nodes[x].get("kind") == "op"}
        ocs, _, _ = OG.op_components(G, OPS, k)
        info = {"OP[%s] %s" % (t, o["name"]): (t, o)
                for t, v in pairs for o in v.get("operations") or []}
        for oc in ocs:
            ent = [info[x] for x in sorted(oc, key=lambda x: -G.nodes[x]["n"]) if x in info]
            if not ent:
                continue
            mem = [m for _, o in ent for m in o.get("members") or []]
            out.append(dict(prompt=prompt, domain=dom.get(prompt), k=k,
                            names=[(t, o["name"], o.get("statement") or "",
                                    len(o.get("members") or [])) for t, o in ent],
                            n_models=len({m["model"] for m in mem}), _members=mem))
    out.sort(key=lambda c: (c["prompt"], -c["n_models"]))
    for i, c in enumerate(out, 1):
        c["id"] = "C%02d" % i
    return out


def pooled_words(members, side, sc, cap=16):
    """Pooled cited words: how many systems cited it, and its MEDIAN rank each arm.

    Ordered by number of systems citing, so a word 23 of them put on one side
    leads and one system's idiosyncratic pick does not. The bracketed pair is the
    convention used everywhere else here -- base rank then aligned rank, the
    arrow meaning time -- taken as a median over the systems that cited it,
    because a pooled word has no single rank.
    """
    import statistics as st
    cnt = collections.Counter()
    ra, rb = collections.defaultdict(list), collections.defaultdict(list)
    for m in members:
        rows = sc.get(m["model"]) or {}
        for w in {x.lower() for x in (m.get(side + "_words") or [])}:
            cnt[w] += 1
            r = rows.get(w) or rows.get(w.capitalize()) or {}
            if r.get("rank_a") is not None:
                ra[w].append(r["rank_a"])
            if r.get("rank_b") is not None:
                rb[w].append(r["rank_b"])
    med = lambda xs: "%d" % round(st.median(xs)) if xs else "-"
    return [(w, cnt[w], med(ra[w]), med(rb[w]))
            for w in sorted(cnt, key=lambda w: (-cnt[w], w))[:cap]]


def document(min_n=2):
    """One entry per COMPONENT: its sentence, every name its raters gave it, its words.

    The prompt is SHOWN. Hiding it was my choice and RH's correction is right: a
    grouping pass is being asked whether a relation survives a change of
    material, and it cannot judge that without knowing what the material was.
    Hiding it was also failing anyway, since the cited words name their own
    subject; the instruction to separate subject from movement is what actually
    does that work.
    """
    cs = components()
    sc = {p: (OG.sidecar(p) or {}) for p in {c["prompt"] for c in cs}}
    blocks = []
    for c in cs:
        f = lambda ps: "; ".join("%s (%d | %s>%s)" % x for x in ps) or "-"
        names = "\n".join("     [%s]  %s  (%d systems)\n           %s" % (t, nm, k, stx)
                          for t, nm, stx, k in c["names"])
        blocks.append("%s   sentence: %s\n     %d systems\n%s\n     FROM  %s\n     TO    %s"
                      % (c["id"], c["prompt"], c["n_models"], names,
                         f(pooled_words(c["_members"], "a", sc[c["prompt"]])),
                         f(pooled_words(c["_members"], "b", sc[c["prompt"]]))))
    return cs, TASK % (len(cs), "\n\n".join(blocks))


AX = ("concreteness", "valence", "arousal", "dominance")


def feature_shift(min_members=8, min_cov=5):
    """Per operation, the mean shift from FROM words to TO words on four norms.

    ## THE POINT: THIS STITCHES WHERE WORDS AND ROSTERS BOTH FAIL

    Frames share no vocabulary (`beat`/`strapped` against `cock`/`dick` against
    `sue`/`file`), so lexical overlap across frames is zero by construction, and
    the ARI above rules out the roster. What DOES cross is the PROPERTIES of the
    words: two operations can be the same relation while sharing no word, if both
    move from concrete to abstract, or from high to low arousal.

    Computable from cited public norms (Warriner valence/arousal/dominance,
    Brysbaert concreteness), so unlike a statement grouping it is not a language
    model describing language models, and it can CHECK a semantic grouping rather
    than echo it.

    ## TWO LIMITS THAT ARE NOT SMALL

    Unweighted over word TYPES, not mass. The rater's citations carry ranks and a
    rank-1 word counts the same here as a rank-60 one.

    And these are the words the RATER CHOSE TO CITE, so this measures the shift in
    the cited set rather than in the distribution. The stronger version computes
    the same four axes over the full twp table per (model, prompt) and asks
    whether the rater's named operation predicts it; that needs no annotation at
    all and is the honest form of this measurement.
    """
    import statistics as st
    sys.path.insert(0, "/Users/rj416/github/malignment")
    from malignment import fields as F
    N = F._norms()

    def lem(w):
        if w in N:
            return w
        try:
            l = F.lemma(w)
        except Exception:
            return w
        return l if l in N else w

    out = []
    dom = RT.domains()
    for r in blind_readings():
        for o in r["v"].get("operations") or []:
            if len(o.get("members") or []) < min_members:
                continue
            a, b = collections.Counter(), collections.Counter()
            for m in o.get("members") or []:
                for w in m.get("a_words") or []:
                    a[lem(w.lower())] += 1
                for w in m.get("b_words") or []:
                    b[lem(w.lower())] += 1
            d, cov = {}, {}
            for ax in AX:
                xa = [N[w][ax] for w in a if ax in N.get(w, {})]
                xb = [N[w][ax] for w in b if ax in N.get(w, {})]
                if len(xa) >= min_cov and len(xb) >= min_cov:
                    d[ax] = st.mean(xb) - st.mean(xa)
                    cov[ax] = (len(xa), len(a), len(xb), len(b))
            if len(d) == len(AX):
                out.append(dict(prompt=r["prompt"], domain=dom.get(r["prompt"]),
                                reading=r["tag"], name=o["name"], d=d, cov=cov,
                                n=len(o.get("members") or [])))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", action="store_true")
    ap.add_argument("--ari", action="store_true")
    ap.add_argument("--features", action="store_true")
    ap.add_argument("--min-n", type=int, default=2)
    a = ap.parse_args()
    if a.ari:
        R = blind_readings()
        same, cross = [], []
        for x, y in itertools.combinations(R, 2):
            v = ari(x["part"], y["part"])
            if v is None:
                continue
            (same if x["prompt"] == y["prompt"] else cross).append(v)
        med = lambda z: sorted(z)[len(z) // 2]
        print("  same frame      %3d pairs  median ARI %+.3f  max %+.3f"
              % (len(same), med(same), max(same)))
        print("  different frame %3d pairs  median ARI %+.3f  max %+.3f"
              % (len(cross), med(cross), max(cross)))
        return
    if a.features:
        import statistics as st
        fs = feature_shift()
        print("  %-14s %-32s %6s %6s %6s %6s" % ("domain", "operation", "conc", "val", "arou", "domi"))
        for o in sorted(fs, key=lambda x: (x["domain"], -abs(x["d"]["concreteness"]))):
            print("  %-14s %-32s %+6.2f %+6.2f %+6.2f %+6.2f"
                  % (o["domain"], o["name"][:32], o["d"]["concreteness"], o["d"]["valence"],
                     o["d"]["arousal"], o["d"]["dominance"]))
        print("\n  %d operations, >=8 members and >=5 covered types per side" % len(fs))
        for ax in AX:
            xs2 = [o["d"][ax] for o in fs]
            print("    %-13s median %+.3f   %d of %d positive"
                  % (ax, st.median(xs2), sum(1 for x in xs2 if x > 0), len(xs2)))
        return
    xs, txt = document(a.min_n)
    p = os.path.join(HERE, "results", "inputs", "crossframe_ops.txt")
    open(p, "w").write(txt)
    json.dump([{k: v for k, v in o.items() if k != "_members"} for o in xs],
              open(os.path.join(HERE, "results", "crossframe_ops.json"), "w"), indent=1)
    #: A COPY WHERE RH READS. The repo is the record; this is the reading copy.
    dbx = "/Users/rj416/Dropbox/Prof/Articles/TheoryMachines/agents/dario/crossframe_ops.md"
    open(dbx, "w").write("# Cross-frame operations, for grouping\n\n"
                         "%d components from %d frames x 2 blind raters, each carrying every\n"
                         "name its raters gave it. The sentence is shown; the domain label and\n"
                         "model identity are not.\n\n"
                         "```\n%s\n```\n" % (len(xs), len({o["prompt"] for o in xs}), txt))
    print("  reading copy %s" % dbx)
    dom = collections.Counter(o["domain"] for o in xs)
    print("%d components from %d frames x 2 raters (%d carry more than one name)"
          % (len(xs), len({o["prompt"] for o in xs}),
             sum(1 for o in xs if len(o["names"]) > 1)))
    print("  by domain (not shown; the sentence IS shown): %s" % dict(dom))
    print("  %d chars (~%d tokens)\n  wrote %s" % (len(txt), len(txt) // 4, p))
    for probe in ("C01", "THE SAME transformation", "singletons", "word (n | a>b)"):
        assert probe in txt, probe
    #: THE PROMPT IS METADATA AND MUST NOT APPEAR. A DOMAIN WORD MAY.
    #: `sexual` and `violence` turn up inside 15 of 59 statements because the
    #: RATER used them describing what it saw, and stripping those would be
    #: editing the evidence to make the blind look better than it is. So the
    #: assert covers what I control and the leak I cannot remove is declared:
    #: a grouping agent can sort roughly a quarter of the entries by topic, and
    #: any group that turns out to be domain-pure has to be read with that in
    #: mind rather than as a discovery.
    #: The sentence is shown now, so there is no prompt leak to assert against.
    #: What still must not appear is the DOMAIN label, which is my metadata and
    #: would hand the grouping pass the very partition it is being asked to test.
    for o in xs:
        assert o["prompt"] in txt, "component %s lost its sentence" % o["id"]
    for d in ("domain", "identity frame", "institutional frame"):
        assert d not in txt, "domain metadata leaked: %r" % d
    assert "align" not in txt.lower(), "the word alignment leaked into the task"


if __name__ == "__main__":
    main()
