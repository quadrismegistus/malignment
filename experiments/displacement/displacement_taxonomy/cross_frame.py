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


def as_read(path=None):
    """`{id: component}` AS THE RATERS SAW IT, joined on content not on position.

    ## WHY A LIVE REBUILD IS NOT THE KEY

    `components()` is deterministic now, but the document the raters answered was
    built before it was, and 11 of 94 ids resolve differently under the fixed
    order. A rater's answer is a list of ids; looking those ids up in a fresh
    rebuild silently returns the WRONG COMPONENT and nothing in the lookup can
    detect it. So the saved document is the authority, and the live rebuild is
    joined onto it by (sentence, operation names), which are content.

    Refuses rather than guessing if the join is not one-to-one.
    """
    saved = json.load(open(path or os.path.join(HERE, "results", "crossframe_ops.json")))
    live = components()
    key = lambda c: (c["prompt"], tuple(sorted(n[1] for n in c["names"])))
    byk = collections.defaultdict(list)
    for c in live:
        byk[key(c)].append(c)
    dup = [k for k, v in byk.items() if len(v) > 1]
    assert not dup, "join is not unique; %d sentence/name pairs repeat: %s" % (len(dup), dup[:2])
    out, miss = {}, []
    for s in saved:
        v = byk.get(key(s))
        if not v:
            miss.append(s["id"])
            continue
        out[s["id"]] = dict(v[0], id=s["id"], domain=s.get("domain"))
    assert not miss, "%d saved components have no live match: %s" % (len(miss), miss[:4])
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


def arm_for(pairs):
    """Pick ONE arm per sentence: the blanks-stripped reading if it exists, else the original.

    ## NEVER BOTH, AND WHY IT IS A CHOICE RATHER THAN A MERGE

    Six sentences now carry two readings of the same 50 lineages: `x1b` and
    `x1bn`. They are different MEASUREMENTS -- blanks are dropped before
    renormalisation, so ranks move -- and pooling them would count one sentence
    twice and mix two instruments while doing it.

    Stripped wins where it exists. Measured across those six: 10 blank-named
    operations fall to 1, and the coverage that disappears with them was largely
    fictitious -- on `She was so furious` one rater had filed 47 of 50 models
    under `Frozen-lead reshuffle` and `Top-choice flight`, whose statements
    describe whether the top-ranked word stayed put and say nothing about the
    treatment at all. Stripped, the same rater places 18 and abstains on the
    rest, which is the honest number.
    """
    strip = [x for x in pairs if x[0].split(".")[0].endswith("bn")]
    return strip or [x for x in pairs if x[0].split(".")[0].endswith("b")]


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
        pairs = arm_for(OG.readings(prompt, n)[0])
        if not pairs:
            continue
        nb = pairs[0][0].split(".")[0].endswith("bn")
        G = OG.build(pairs)
        OPS = {x for x in G if G.nodes[x].get("kind") == "op"}
        ocs, _, _ = OG.op_components(G, OPS, k)
        info = {"OP[%s] %s" % (t, o["name"]): (t, o)
                for t, v in pairs for o in v.get("operations") or []}
        for oc in ocs:
            #: TIE BROKEN ON THE NODE ID. `oc` is a SET, so sorting on size alone
            #: leaves equal-sized operations in set-iteration order, which differs
            #: between processes. The components and their members were stable;
            #: only the ORDER names printed inside them moved, which was enough to
            #: make the document not byte-reproducible and therefore unable to
            #: prove that a later rater read what an earlier one read.
            ent = [info[x] for x in sorted(oc, key=lambda x: (-G.nodes[x]["n"], x)) if x in info]
            if not ent:
                continue
            mem = [m for _, o in ent for m in o.get("members") or []]
            out.append(dict(prompt=prompt, domain=dom.get(prompt), k=k, no_blanks=nb,
                            names=[(t, o["name"], o.get("statement") or "",
                                    len(o.get("members") or [])) for t, o in ent],
                            #: PER-OPERATION members kept beside the flattened
                            #: `_members`. A component merged several operations
                            #: because they SHARE models, but each operation still
                            #: has its own member list, and that is the level a
                            #: reader drills to: relation -> the models IT placed.
                            _ops=[(t, o) for t, o in ent],
                            n_models=len({m["model"] for m in mem}), _members=mem))
    #: THE ID IS A NAME AND IT HAS TO MEAN ONE THING. Sorting on (prompt,
    #: n_models) alone left 19 of 94 slots in TIE GROUPS -- same sentence, same
    #: model count -- broken by the iteration order of the SET that
    #: `op_components` returns, which differs between processes. C15 was "Blank
    #: Redaction" in the document the raters read and "no displacement" the next
    #: time components() ran, and C16/C17 had swapped with it.
    #:
    #: That is worse than the earlier name-ordering instability, which only made
    #: the document non-reproducible. This makes a rater's answer resolve to the
    #: WRONG COMPONENT: the ids in a returned grouping are looked up later, and
    #: nothing in the lookup can tell that the mapping moved underneath it. Any
    #: analysis that reads names from the saved document and words from a live
    #: rebuild silently mixes two populations.
    #:
    #: Tie broken on the operation names, which are content and are stable.
    out.sort(key=lambda c: (c["prompt"], -c["n_models"],
                            tuple(sorted(n[1] for n in c["names"]))))
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
    #: SIDECAR MUST MATCH THE ARM. A stripped reading's words carry stripped
    #: ranks; resolving them against the unstripped table would print numbers
    #: from a different measurement beside the right words.
    sc = {c["prompt"]: (OG.sidecar(c["prompt"], no_blanks=c.get("no_blanks", False)) or {})
          for c in cs}
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


def reversal_stability(min_readings=8, iters=2000, seed=20260822):
    """Is reversal a property of the MODEL, across frames? Permutation test.

    ## WHY THIS IS THE ONE SIGNAL HELD BACK FROM THE GROUPING

    Cross-frame membership is noise: adjusted Rand +0.000, so which relation a
    model performs is a property of the FRAME. Reversal is not. Some models run
    alignment backwards nearly everywhere and some never do, far beyond what the
    per-reading reversal counts would produce by chance.

    That makes it the only model-level quantity that survives a change of
    material, which is exactly what an independent check on a cross-frame
    grouping needs. So it stays OUT of the grouping document: if two components
    are proposed as one relation, their reverser sets are a PREDICTION, and a
    prediction cannot be tested against evidence that was fed to the predictor.
    Same circularity RH caught in grouping by word properties.

    ## THE NULL HAS TO PRESERVE THE PER-READING COUNT

    A reading that called 13 models reversed contributes 13 whatever is true, so
    the null reassigns that same 13 at random among the models THAT READING
    judged. What is being tested is whether the reversals concentrate on
    particular models, not whether there are many of them.

    A consequence for the check itself: because a few models reverse everywhere,
    ANY two components will share reversers at above-chance raw rates. The check
    must therefore compare against this same null, not against zero.
    """
    import random, statistics as st
    R = blind_readings()
    judged = {r["tag"] + "|" + r["prompt"]: set(r["part"]) | set(r["rev"]) for r in R}
    rev = {r["tag"] + "|" + r["prompt"]: set(r["rev"]) for r in R}
    obs, opp = collections.Counter(), collections.Counter()
    for k in judged:
        for m in judged[k]:
            opp[m] += 1
            if m in rev[k]:
                obs[m] += 1
    elig = [m for m in opp if opp[m] >= min_readings]
    var_obs = st.pvariance([obs[m] / opp[m] for m in elig])
    rng = random.Random(seed)
    null = []
    for _ in range(iters):
        c = collections.Counter()
        for k in judged:
            for m in rng.sample(sorted(judged[k]), len(rev[k])):
                c[m] += 1
        null.append(st.pvariance([c[m] / opp[m] for m in elig]))
    p = (sum(1 for x in null if x >= var_obs) + 1.0) / (iters + 1.0)
    rates = sorted(((obs[m] / opp[m], obs[m], opp[m], m) for m in elig), reverse=True)
    return dict(rates=rates, var_obs=var_obs, null=null, p=p, n=len(elig))


SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["groups", "singletons", "confidence"],
    "properties": {
        "groups": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "statement", "members", "spans", "why"],
            "properties": {
                "name": {"type": "string"},
                "statement": {"type": "string"},
                "members": {"type": "array", "items": {"type": "string"}},
                "spans": {"type": "string"},
                "why": {"type": "string"}}}},
        "singletons": {"type": "array", "items": {"type": "string"}},
        "confidence": {"enum": ["high", "medium", "low"]}}}

SCRIPT = """// GENERATED by cross_frame.py. Cross-frame grouping, %(raters)d rater(s).
export const meta = { name: 'crossframe-grouping',
  description: 'Group per-frame components into cross-frame relations',
  phases: [{ title: 'Group', detail: '%(n)d components' }] }
const FILE = %(path)s
const SCHEMA = %(schema)s
// The TASK is byte-identical for each rater; only the label differs, so they are
// blind replicates rather than N agents given N jobs.
const TASK = `Read the file ${FILE} with the Read tool.\n\nIts entire ` +
  `contents are your task. Follow them exactly and return ONLY the structured ` +
  `object. Do not read any other file, and do not look anything up.`
const rs = (await parallel(Array.from({ length: %(raters)d }, (_, i) => () =>
  agent(TASK, { label: `crossframe r${i + 1}`, phase: 'Group', schema: SCHEMA,
                model: %(model)s, effort: %(effort)s })))).filter(Boolean)
if (rs.length < %(raters)d)
  log(`WARNING: %(raters)d rater(s) requested, ${rs.length} returned`)
return { raters: rs.length, per_rater: rs.map((x) => ({
  groups: x.groups.length, singletons: x.singletons.length,
  confidence: x.confidence,
  names: x.groups.map((g) => `${g.name} (${g.members.length})`) })) }
"""


def workflow(raters=2, model="sonnet", effort="xhigh", regenerate=False):
    """Write a runner for an EXISTING document. Does not rewrite the document.

    ## WHY THIS NO LONGER GENERATES

    It used to call document() and write the file every time, so producing a
    runner for a third rater silently rewrote the input the first two had read.
    A later rating is only comparable if it reads the same bytes, and the thing
    that guarantees that is not determinism, which this generator does not have,
    but refusing to touch the artifact at all.

    The document is now written once by --doc and is the record. This hashes it
    and prints the hash so a run can be tied to the exact text it was given.
    """
    import hashlib
    path = os.path.join(HERE, "results", "inputs", "crossframe_ops.txt")
    if regenerate or not os.path.exists(path):
        cs, txt = document()
        open(path, "w").write(txt)
    txt = open(path).read()
    cs = components()
    digest = hashlib.md5(txt.encode()).hexdigest()
    n_in_doc = sum(1 for l in txt.splitlines() if l.startswith("C") and "sentence:" in l)
    #: THE DOCUMENT ON DISK IS THE AUTHORITY, not what components() returns now.
    #: If they disagree the ids in a returned grouping cannot be resolved, which
    #: is a silent misalignment rather than an error.
    assert n_in_doc == len(cs), \
        "document holds %d components, components() now returns %d" % (n_in_doc, len(cs))
    js = SCRIPT % {"raters": raters, "n": len(cs),
                   "path": json.dumps(os.path.abspath(path)),
                   "schema": json.dumps(SCHEMA, indent=2, sort_keys=True),
                   "model": json.dumps(model), "effort": json.dumps(effort)}
    #: NAMED BY RATER MODEL. Overwriting the file would destroy the script that
    #: produced the readings already on disk, and a third rating is only
    #: comparable if the earlier one can still be shown to have run this document.
    #: NAMED BY MODEL **AND EFFORT**. Keyed by model alone, three Opus runs at
    #: medium, high and xhigh overwrote one script, so the file on disk stopped
    #: reproducing two of the three results it had produced. The results were
    #: saved separately and nothing was lost, but a runner that cannot re-run
    #: what it ran is a provenance gap of exactly the kind this file asserts
    #: against elsewhere.
    out = os.path.join(HERE, "workflow_crossframe_%s_%s.js" % (model, effort))
    open(out, "w").write(js)
    #: The generated script has to CONTAIN what it claims to run, checked rather
    #: than assumed -- a template that silently loses its file path produces a
    #: workflow that reads nothing and returns a confident empty grouping.
    for probe in (os.path.abspath(path), '"singletons"', model, effort):
        assert probe in js, "generated script missing %r" % probe
    print("%d components, %d chars (~%d tokens), %d rater(s), model %s effort %s"
          % (len(cs), len(txt), len(txt) // 4, raters, model, effort))
    print("  document md5 %s  (NOT regenerated)" % digest)
    print("  task     %s\n  workflow %s\n\nNOT RUN." % (path, out))
    return out


DOMAIN_COLOUR = {"sexual": "#fa5252", "violence": "#e8590c",
                 "institutional": "#4dabf7", "identity": "#51cf66"}


#: WHICH GROUPINGS THE NETWORK IS BUILT FROM. One entry per rater; the hub ids
#: carry the rater so two raters' relations are distinct nodes and a component
#: links to one hub PER RATER. That is what makes this a network rather than a
#: set of disjoint stars: with one rater every component belongs to exactly one
#: group, so nothing can connect two hubs and the picture can only be 21 stars.
#: Measured on the single-rater version: 25 connected components, 0 leaves with
#: more than one hub.
RATERS = [("opus-high", "crossframe_groups_89_opus_high.json"),
          ("opus-xhigh", "crossframe_groups_89_opus_xhigh.json"),
          ("opus-med", "crossframe_groups_89_opus_medium.json")]


def emit_graph(groups_path=None, out="metagraph", cap=10, raters=None):
    """The meta-relation network, carrying all FOUR levels for the drill-down.

        meta-relation -> component -> within-prompt relation -> model + words

    ## WHY THE LEAVES ARE FAT

    The per-frame graph puts every word on the canvas as its own node, so its
    panel can recover words by walking links. Here the canvas is two levels --
    component and meta-relation -- and the two levels BELOW a component are not
    drawn at all. They still have to be readable, so they ride on the leaf.

    Words are capped per model per side and ordered by rank, so what a reader
    sees first is what led the arm rather than an alphabetical tail.
    """
    import json as _json
    rs = [(lab, _json.load(open(os.path.join(HERE, "results", f))))
          for lab, f in (raters or RATERS)]
    if groups_path:
        rs = [("rater", _json.load(open(groups_path)))]
    M = as_read()
    sc = {}
    nodes, links, seen = [], [], set()

    def words(model, ws, side, rows):
        out = []
        key = "rank_a" if side == "a" else "rank_b"
        for w in [x.lower() for x in (ws or [])]:
            r = rows.get(w) or rows.get(w.capitalize()) or {}
            out.append({"w": w, "ra": r.get("rank_a"), "rb": r.get("rank_b"),
                        "k": r.get(key)})
        out.sort(key=lambda x: (x["k"] is None, x["k"] or 0))
        return [{"w": x["w"], "ra": x["ra"], "rb": x["rb"]} for x in out[:cap]]

    def leaf(cid):
        if cid in seen or cid not in M:
            return
        seen.add(cid)
        c = M[cid]
        if c["prompt"] not in sc:
            sc[c["prompt"]] = OG.sidecar(c["prompt"], no_blanks=c.get("no_blanks", False)) or {}
        rows_by = sc[c["prompt"]]
        #: ONE ENTRY PER WITHIN-PROMPT RELATION, each carrying the models IT
        #: placed. Operations inside a component overlap by construction -- that
        #: is why they merged -- so a model can appear under two relations, and
        #: seeing it twice with two different word lists IS the evidence the
        #: merge rests on rather than a duplication to tidy away.
        rels = []
        for t, o in c["_ops"]:
            mem = []
            for m in sorted(o.get("members") or [], key=lambda m: m["model"]):
                r = rows_by.get(m["model"]) or {}
                mem.append({"model": m["model"],
                            "from": words(m["model"], m.get("a_words"), "a", r),
                            "to": words(m["model"], m.get("b_words"), "b", r)})
            rels.append({"name": o["name"], "reading": t,
                         "statement": o.get("statement") or "",
                         "n": len(o.get("members") or []), "members": mem})
        nodes.append({"id": "%s::%s" % (c["prompt"], cid), "kind": "word", "label": cid,
                      "group": c["domain"], "model": c["prompt"], "side": "to",
                      "component": 0, "cid": cid, "sentence": c["prompt"],
                      "n_models": c["n_models"], "stripped": bool(c.get("no_blanks")),
                      "relations": rels})

    for lab, G in rs:
      for g in G["groups"]:
        hid = "META[%s] %s" % (lab, g["name"])
        fr = {M[m]["prompt"] for m in g["members"] if m in M}
        ds = collections.Counter(M[m]["domain"] for m in g["members"] if m in M)
        nodes.append({"id": hid, "kind": "op", "label": g["name"], "group": None,
                      "rater": lab, "component": 0, "n": len(g["members"]),
                      "statement": g.get("statement", ""), "spans": g.get("spans", ""),
                      "why": g.get("why", ""), "sentences": len(fr),
                      "domains": dict(ds),
                      "models": sorted(m for m in g["members"] if m in M)})
        for m in g["members"]:
            leaf(m)
            if m in M:
                links.append({"source": "%s::%s" % (M[m]["prompt"], m),
                              "target": hid, "cross": len(ds) > 1})
    for lab, G in rs:
        for cid in G.get("singletons") or []:
            leaf(cid)

    from malignment.chartdata import graph, write
    dom = collections.Counter(M[c]["domain"] for c in M)
    art = graph(
        title="Cross-frame meta-relations",
        subtitle=("%d meta-relations over %d components from %d sentences, grouped by one "
                  "blind reader that saw no domain label and no model identity. A leaf is a "
                  "per-frame component coloured by the DOMAIN it came from; a hub is a "
                  "relation the reader said they share. A hub whose leaves are one colour "
                  "is confined to a domain. %d components no reader could place are drawn "
                  "unattached, because a corpus with unplaceable components should not look "
                  "tidier than it is. Click a hub, then a component, to reach the models."
                  % (len(G["groups"]), len(seen), len({M[c]["prompt"] for c in seen}),
                     len(G.get("singletons") or []))),
        nodes=nodes, links=links,
        groups=[{"key": k, "label": "%s (%d)" % (k, dom[k]), "colour": v}
                for k, v in DOMAIN_COLOUR.items() if k in dom],
        meta={"chart_hint": "metagraph", "raters": 1,
              "components": [{"operations": len(G["groups"]), "models": len(seen)}]})
    #: `graph()` VALIDATES, a different component DRAWS. Its dangling-endpoint
    #: assert is exactly what this artifact needs; its two-level op/word panel is
    #: not, so the chart NAME is overridden after validation rather than the
    #: validation being skipped.
    art["chart"] = "metagraph"
    return write(art, os.path.join(HERE, "figures"), out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", action="store_true")
    ap.add_argument("--ari", action="store_true")
    ap.add_argument("--features", action="store_true")
    ap.add_argument("--reversal", action="store_true")
    ap.add_argument("--graph", action="store_true",
                    help="write the meta-relation network as a `graph` artifact")
    ap.add_argument("--workflow", type=int, metavar="RATERS")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--effort", default="xhigh")
    ap.add_argument("--regenerate", action="store_true",
                    help="rewrite the document; breaks comparability with earlier raters")
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
    if a.graph:
        emit_graph()
        return
    if a.workflow:
        workflow(a.workflow, a.model, a.effort, a.regenerate)
        return
    if a.reversal:
        import statistics as st
        r = reversal_stability()
        print("  %d models judged on >=8 readings\n" % r["n"])
        for lab, xs in (("most reversed", r["rates"][:6]), ("never reversed", r["rates"][-6:])):
            print("  %s" % lab)
            for rate, o, n, m in xs:
                print("    %-34s %2d of %2d  (%.0f%%)" % (m, o, n, 100 * rate))
        print("\n  variance of per-model rate: observed %.4f" % r["var_obs"])
        print("  null preserving each reading's count: median %.4f, 95th %.4f"
              % (st.median(r["null"]), sorted(r["null"])[int(.95 * len(r["null"]))]))
        print("  p = %.4f" % r["p"])
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
    #: ASSERT ON THE EMITTED FIELD, NOT ON THE WORD. The first version refused
    #: whenever the bare string `domain` appeared anywhere, which at 94
    #: components matched two RATER STATEMENTS -- "the same general domain",
    #: "the domain of clothing". That is the rater's own prose, and refusing on
    #: it would have meant editing evidence to satisfy a guard. What must not
    #: appear is the label in a METADATA POSITION, which only this function can
    #: emit, so the check is on the field syntax rather than on vocabulary.
    for d in ("domain:", "domain =", "[sexual]", "[violence]", "[identity]",
              "[institutional]"):
        assert d not in txt, "domain metadata leaked: %r" % d
    assert "align" not in txt.lower(), "the word alignment leaked into the task"


if __name__ == "__main__":
    main()
