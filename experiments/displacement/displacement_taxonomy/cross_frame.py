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


TASK = """You will read %d short descriptions of a transformation. Each was written
independently by a different reader looking at different material, and each
describes how one set of words gives way to another. Each entry gives the name
that reader chose, its description, and the words it cited on each side.

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


def pooled_words(o_members, side, sc, cap=16):
    """Words cited on one side of an operation, pooled over its models.

    Ordered by HOW MANY MODELS CITED THEM, then by mean rank. A word four models
    put on that side is more characteristic of the relation than one model's
    idiosyncratic pick, and that is what pooling should surface. Capped so a
    30-member operation does not bury the reader in its own tail.
    """
    cnt, rk = collections.Counter(), collections.defaultdict(list)
    key = "rank_a" if side == "a" else "rank_b"
    for m in o_members:
        for w in {x.lower() for x in (m.get(side + "_words") or [])}:
            cnt[w] += 1
            r = (sc.get(m["model"]) or {}).get(w) or (sc.get(m["model"]) or {}).get(w.capitalize())
            if r and r.get(key) is not None:
                rk[w].append(r[key])
    xs = sorted(cnt, key=lambda w: (-cnt[w], sum(rk[w]) / len(rk[w]) if rk[w] else 999))
    return [(w, cnt[w]) for w in xs[:cap]]


def document(min_n=2):
    """One entry per operation: id, name, statement, and the pooled FROM/TO words.

    ## WORDS ARE IN, AND THE COST IS STATED

    An earlier version carried statements alone, to stop a rater sorting by
    subject matter instead of by movement. RH's call, and it matches what worked
    before: the words are the evidence, and a rater asked to judge a relation
    without them is guessing at prose. The cost is real -- `cock -> beard` names
    its own subject area -- so the task asks explicitly for the distinction and
    for which areas each group spans, which turns the leak into something the
    rater has to answer for rather than something it can quietly use.

    Frame, domain, model identity and the word `alignment` are still absent.
    """
    xs = ops(min_n)
    sc = {}
    for prompt in {o["prompt"] for o in xs}:
        sc[prompt] = OG.sidecar(prompt) or {}
    blocks = []
    for o in xs:
        fr = pooled_words(o["_members"], "a", sc[o["prompt"]])
        to = pooled_words(o["_members"], "b", sc[o["prompt"]])
        f = lambda ps: "; ".join("%s (%d)" % (w, c) for w, c in ps) or "-"
        blocks.append("%s  %s\n     %s\n     FROM  %s\n     TO    %s"
                      % (o["id"], o["name"], o["statement"], f(fr), f(to)))
    return xs, TASK % (len(xs), "\n\n".join(blocks))


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
                         "%d operations from %d frames x 2 blind raters. Frame, domain, model\n"
                         "identity and the word alignment are absent; the cited words are not.\n\n"
                         "```\n%s\n```\n" % (len(xs), len({o["prompt"] for o in xs}), txt))
    print("  reading copy %s" % dbx)
    dom = collections.Counter(o["domain"] for o in xs)
    print("%d operations from %d frames x 2 raters" % (len(xs), len({o["prompt"] for o in xs})))
    print("  by domain (NOT shown to the rater): %s" % dict(dom))
    print("  %d chars (~%d tokens)\n  wrote %s" % (len(txt), len(txt) // 4, p))
    for probe in ("O01", "THE SAME transformation", "singletons"):
        assert probe in txt, probe
    #: THE PROMPT IS METADATA AND MUST NOT APPEAR. A DOMAIN WORD MAY.
    #: `sexual` and `violence` turn up inside 15 of 59 statements because the
    #: RATER used them describing what it saw, and stripping those would be
    #: editing the evidence to make the blind look better than it is. So the
    #: assert covers what I control and the leak I cannot remove is declared:
    #: a grouping agent can sort roughly a quarter of the entries by topic, and
    #: any group that turns out to be domain-pure has to be read with that in
    #: mind rather than as a discovery.
    for o in xs:
        assert o["prompt"] not in txt, "prompt leaked into the document: %r" % o["prompt"]
    hint = sum(1 for o in xs if any(
        d in (o["statement"] + " " + o["name"]).lower()
        for d in ("sexual", "violence", "identity", "institutional")))
    print("  DECLARED LEAK: %d of %d statements name their own domain" % (hint, len(xs)))


if __name__ == "__main__":
    main()
