"""Dose the meta-relations: does each one MOVE the scene, and by how much?

    python -u dose_relations.py                  the table
    python -u dose_relations.py --clusters       how the meta-relations are derived
    python -u dose_relations.py --example C01    one component, its words and ratings
    python -u dose_relations.py --out results/dose_relations.csv

The ten relations in `TAXONOMY.md` were built and named before `charge.py`
existed (this folder ran 21 Aug to 2 Sep; charge.py landed 29 Aug), and `charge`
is imported nowhere here -- every "charge" in these producers is the K-lexicon
axis name `k:charge`, not the module. So the ratings have never been asked what
the relations do.

They are the right second instrument precisely because the raters never saw
them. `task_charge` rated a candidate word IN ITS FRAME -- what the sentence
describes once that word is in it, on 1-7 -- with no knowledge of any grouping,
and the groupings were made from prose with no knowledge of any rating.

## THE THREE TRAPS THIS FOLDER SETS, AND WHERE THEY ARE HANDLED

**THE IDS DO NOT SURVIVE A REBUILD.** `cross_frame.components()` now returns 221
over a grown population and renumbers `C01..` from it, so frozen ids resolve to
the WRONG components: the live `C01` is "generic-to-specific escalation" on the
Torah ark frame where the frozen `C01` is "He clenched his fist and / Blow
Withheld". `cross_frame.py:517` states the rule -- the document on disk is the
authority -- so `parse_doc()` reads `results/inputs/crossframe_ops.txt` and
`join_live()` maps it to live components on (prompt, sorted operation names),
which `cross_frame.py:264` establishes as the stable key because it is content.
89 of 89 join uniquely. Nothing here reads a live id.

**THE TEN ARE NOT GROUP NAMES.** A meta-relation is a connected component of the
hub graph at `K_BRIDGE=3` (`cross_frame.py:653-680`), not a row in a rater's
file: naming is unstable by construction, and `RESULTS_interrater.md` measures
it -- two raters agree on WHICH WORDS carry a difference at Jaccard 0.80 while
they "demonstrably need not" agree what to call it. `clusters()` rebuilds the
graph. **It yields 12, not 10** (11 if all three raters must be represented),
and the gap is recorded in `--clusters` rather than smoothed over.

**`charge.scene()` IS A CROSS-LINEAGE MEAN.** Which candidates a cell even
contains is a fact about what that base arm offered, so a per-model question
takes `charge.words(prompt, base)` and each model's own list. Aligned names reach
charge's base keys through `roster.endpoints()`, 50 of 50. Using the pooled mean
instead moves ESCALATION from +1.08 to +0.68 and turns LATERAL SWAP's straddle
into a clean zero, so this is not a refinement.

## WHAT THE NUMBER IS

`delta` = mean `scene` of the words that ROSE minus mean `scene` of the words
that FELL, in points of the 1-7 completed-scene scale. Negative means alignment
promoted words that make a milder sentence.

`delta` alone confounds how high the base arm sat with where the aligned arm
landed, so `--landing` splits it against the setup using `charge.lift_per_lineage`
(`T_base - frame`, the dose displacement work wants, NOT `dose()`):

    lift     how much the base arm added over the setup
    landing  delta + lift, where the aligned arm left the scene

`landing == 0` is "declines to add"; `landing < 0` is going milder than the
setup. **This is a statement about a transgressiveness scale and does not
generalise to the others.** `norm_change/summary.py` puts `k_register_level` at
MARGINAL ONLY, p=0.67 under all three level doses, so a scale can move under
alignment with no dose structure at all and an instrument like this one cannot
see it.

BLIND TO DIRECTION BY CONSTRUCTION: the readings label their sides `a` and `b`,
never base and aligned, so `orient()` resolves which side fell against the
pooled FROM/TO lists in the frozen document, and drops a member where the two
are tied rather than guessing.
"""
import argparse, collections, csv, itertools, json, os, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)

DOC = os.path.join(HERE, "results", "inputs", "crossframe_ops.txt")
RATER_FILES = ["crossframe_groups_89_opus_%s.json" % e
               for e in ("high", "medium", "xhigh")]
_WORD = re.compile(r"([^\s;]+)\s+\((\d+)\s*\|\s*(\d+)>(\d+)\)")
_NAME = re.compile(r"^\s*\[[^\]]+\]\s+(.+?)\s+\(\d+ systems\)")
_HEAD = re.compile(r"^(C\d\d)\s+sentence:\s*(.+?)\s*$")


def parse_doc(path=DOC):
    """{id: {prompt, names, FROM, TO}} from the FROZEN document. -> dict

    The document is the authority (`cross_frame.py:517`). FROM are the words that
    fell and TO those that rose, pooled over the systems that cited them;
    `pooled_words` writes each as `word (n | base_rank>aligned_rank)`.
    """
    out, cur = {}, None
    for line in open(path):
        m = _HEAD.match(line)
        if m:
            cur = {"id": m.group(1), "prompt": m.group(2),
                   "names": [], "FROM": [], "TO": []}
            out[cur["id"]] = cur
            continue
        if cur is None:
            continue
        m = _NAME.match(line)
        if m:
            cur["names"].append(m.group(1))
            continue
        m = re.match(r"^\s*(FROM|TO)\s+(.*)$", line)
        if m:
            cur[m.group(1)] = [w for w, *_ in _WORD.findall(m.group(2))]
    return out


def join_live(frozen):
    """{frozen id: live component} on CONTENT, never on id. -> dict

    Ambiguous and missing keys are dropped rather than guessed; the caller is
    told how many, because a silent drop here would shrink the population a
    verdict is read over.
    """
    import cross_frame as CF
    idx = collections.defaultdict(list)
    for c in CF.components():
        idx[(c["prompt"], tuple(sorted(n[1] for n in c["names"])))].append(c)
    out, amb = {}, 0
    for cid, f in frozen.items():
        hits = idx[(f["prompt"], tuple(sorted(f["names"])))]
        if len(hits) == 1:
            out[cid] = hits[0]
        elif hits:
            amb += 1
    return out, amb


def clusters(min_raters=1):
    """The meta-relations: connected components of the hub graph. -> [(name, ids, nhubs, nraters)]

    Hubs are (rater file, group name); an edge joins two hubs from DIFFERENT
    raters sharing at least `K_BRIDGE` components. `cross_frame.py:653` records
    why the threshold is 3: at 2 one 17-component blob fused `Lateral swap inside
    a register` to `Harsher member of the same kind` on two shared components.
    """
    import cross_frame as CF
    import networkx as nx
    owner, mem = {}, {}
    for f in RATER_FILES:
        G = json.load(open(os.path.join(HERE, "results", f)))
        for g in G["groups"]:
            h = "%s::%s" % (f, g["name"])
            owner[h], mem[h] = f, set(g["members"])
    Q = nx.Graph()
    Q.add_nodes_from(owner)
    for a, b in itertools.combinations(sorted(owner), 2):
        if owner[a] != owner[b] and len(mem[a] & mem[b]) >= CF.K_BRIDGE:
            Q.add_edge(a, b)
    out = []
    #: same defect as `operation_graph.op_components`: an unordered set per
    #: cluster made the k=3 meta-relations differently composed on every process
    for c in sorted((sorted(x) for x in nx.connected_components(Q)),
                    key=lambda c: (-len(c), c)):
        if len(c) < 2:
            continue
        nr = len({owner[h] for h in c})
        if nr < min_raters:
            continue
        name = collections.Counter(h.split("::")[1] for h in c).most_common(1)[0][0]
        out.append((name, set().union(*[mem[h] for h in c]), len(c), nr))
    return sorted(out, key=lambda t: -len(t[1]))


def orient(member, FROM, TO):
    """(fell, rose) for one model-reading, or None if the sides tie. -> tuple

    The readings are blind: their sides are `a` and `b` and carry no arm. The
    pooled FROM/TO lists do carry it, so the side overlapping FROM is the side
    that fell. A tie is dropped -- a coin flip here would put an attenuation and
    an escalation in the same bucket with opposite signs.
    """
    aw = list(member.get("a_words") or [])
    bw = list(member.get("b_words") or [])
    sa = len(set(aw) & FROM) + len(set(bw) & TO)
    sb = len(set(bw) & FROM) + len(set(aw) & TO)
    if sa == sb:
        return None
    return (aw, bw) if sa > sb else (bw, aw)


def _aligned_to_base():
    from malignment import roster
    out = {}
    for base, endpoint in roster.endpoints()[0].items():
        out.setdefault(str(endpoint).split("/")[-1], base)
    return out


def dose_components(frozen, live, min_words=2):
    """{id: {delta, lift, landing, n, prompt}} from each model's OWN ratings.

    Per model-reading: `charge.words(prompt, base)` for that lineage's list, mean
    scene of the risen words minus mean scene of the fallen. `lift` is
    `charge.lift_per_lineage`, never recomputed from `frame()` here -- `charge`
    owns that arithmetic and a second implementation of it is how two numbers for
    one quantity get into circulation.
    """
    from malignment import charge
    a2b = _aligned_to_base()
    wcache, out = {}, {}
    skipped = collections.Counter()
    for cid, f in frozen.items():
        c = live.get(cid)
        if not c:
            skipped["unjoined"] += 1
            continue
        FROM, TO = set(f["FROM"]), set(f["TO"])
        deltas, lifts = [], []
        for m in c["_members"]:
            base = a2b.get(m["model"])
            if not base:
                skipped["model unmapped"] += 1
                continue
            key = (f["prompt"], base)
            if key not in wcache:
                try:
                    wcache[key] = charge.words(*key) or {}
                except Exception:
                    wcache[key] = {}
            w = wcache[key]
            if not w:
                skipped["cell absent from charge"] += 1
                continue
            sides = orient(m, FROM, TO)
            if sides is None:
                skipped["side tie"] += 1
                continue
            fell, rose = sides
            fv = [w[x]["scene"] for x in fell if x in w]
            rv = [w[x]["scene"] for x in rose if x in w]
            if len(fv) < min_words or len(rv) < min_words:
                skipped["too few rated words"] += 1
                continue
            deltas.append(st.mean(rv) - st.mean(fv))
            lf = charge.lift_per_lineage(f["prompt"], base)
            if lf is not None:
                lifts.append(lf)
        if deltas:
            d = st.median(deltas)
            lf = st.median(lifts) if lifts else None
            out[cid] = {"prompt": f["prompt"], "delta": d, "n": len(deltas),
                        "lift": lf,
                        "landing": (d + lf) if lf is not None else None}
    return out, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--clusters", action="store_true",
                    help="how the meta-relations are derived, and the 12-vs-10 gap")
    ap.add_argument("--landing", action="store_true",
                    help="split delta against the setup using charge.lift_per_lineage")
    ap.add_argument("--example", metavar="CID",
                    help="one component's words with their ratings")
    ap.add_argument("--min-raters", type=int, default=1,
                    help="require a cluster to carry hubs from this many raters")
    ap.add_argument("--min-words", type=int, default=2,
                    help="rated words needed on EACH side of a model-reading")
    ap.add_argument("--out", default=None, help="write the per-component CSV here")
    a = ap.parse_args(argv)

    frozen = parse_doc()
    live, amb = join_live(frozen)
    print("frozen components %d | content-joined %d | ambiguous %d"
          % (len(frozen), len(live), amb))

    if a.example:
        return _example(frozen, live, a.example)

    cls = clusters(a.min_raters)
    if a.clusters:
        print("\nTAXONOMY.md states TEN meta-relations. The hub graph at "
              "K_BRIDGE=3 gives:\n")
        print("  %-48s %5s %7s %8s" % ("name", "hubs", "raters", "members"))
        for name, ids, nh, nr in cls:
            print("  %-48s %5d %7d %8d" % (name[:48], nh, nr, len(ids)))
        three = [c for c in cls if c[3] == 3]
        print("\n  clusters with >=2 hubs        %d" % len(cls))
        print("  with all three raters         %d" % len(three))
        print("  TAXONOMY.md states            10")
        print("\n  The ten do not reproduce from the stated rule. Requiring all "
              "three raters\n  drops one; reaching ten needs at least one further "
              "merge the threshold did\n  not make -- TAXONOMY relation 9 folds "
              "`Proceduralization` and `Comment\n  instead of act`, which are "
              "separate clusters here.")
        return 0

    got, skipped = dose_components(frozen, live, a.min_words)
    print("components dosed %d | model-readings %d"
          % (len(got), sum(v["n"] for v in got.values())))
    for k, v in skipped.most_common():
        print("  dropped: %-26s %d" % (k, v))

    cols = ("%-48s %8s %7s %6s" % ("META-RELATION", "median", "mean", "n")
            if not a.landing else
            "%-48s %8s %7s %8s %6s" % ("META-RELATION", "delta", "lift", "landing", "n"))
    print("\n" + cols)
    print("-" * len(cols))
    rows = []
    for name, ids, nh, nr in cls:
        ds = [got[c]["delta"] for c in ids if c in got]
        if not ds:
            continue
        ls = [got[c]["landing"] for c in ids if c in got
              and got[c]["landing"] is not None]
        lf = [got[c]["lift"] for c in ids if c in got and got[c]["lift"] is not None]
        rows.append((st.median(ds), name, st.mean(ds), len(ds), len(ids),
                     st.median(lf) if lf else None,
                     st.median(ls) if ls else None))
    for med, name, mean, nd, nmem, lf, ld in sorted(rows):
        if a.landing:
            print("%-48s %+8.3f %+7.3f %+8.3f %3d/%-3d"
                  % (name[:48], med, lf if lf is not None else float("nan"),
                     ld if ld is not None else float("nan"), nd, nmem))
        else:
            print("%-48s %+8.3f %+7.3f %3d/%-3d" % (name[:48], med, mean, nd, nmem))

    alld = [v["delta"] for v in got.values()]
    print("\nALL %d components: median %+.3f mean %+.3f (neg %d / pos %d)"
          % (len(alld), st.median(alld), st.mean(alld),
             sum(1 for d in alld if d < 0), sum(1 for d in alld if d > 0)))
    if a.landing:
        lds = [v["landing"] for v in got.values() if v["landing"] is not None]
        print("landing: %d above the frame (+-0.25 band), %d on it, %d below"
              % (sum(1 for d in lds if d > 0.25),
                 sum(1 for d in lds if -0.25 <= d <= 0.25),
                 sum(1 for d in lds if d < -0.25)))
        print("A SPREAD, NOT A DESTINATION -- quote the three counts, not the median.")

    if a.out:
        path = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
        rel = {}
        for name, ids, _, _ in cls:
            for c in ids:
                rel.setdefault(c, name)
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(("component", "relation", "prompt", "delta", "lift",
                        "landing", "n_model_readings"))
            for cid, v in sorted(got.items()):
                w.writerow((cid, rel.get(cid, ""), v["prompt"],
                            "%.6f" % v["delta"],
                            "" if v["lift"] is None else "%.6f" % v["lift"],
                            "" if v["landing"] is None else "%.6f" % v["landing"],
                            v["n"]))
        print("\n-> %s" % path)
    return 0


def _example(frozen, live, cid):
    """One component in full: the words, their ratings, and the arithmetic."""
    from malignment import charge
    f = frozen.get(cid)
    if not f:
        print("no such component in the frozen document: %r" % cid)
        return 1
    a2b = _aligned_to_base()
    print("\n%s  %r" % (cid, f["prompt"]))
    print("  named:  %s" % "; ".join(f["names"]))
    print("  frame (the setup alone, 1-7): %s" % charge.frame(f["prompt"]))
    c = live.get(cid)
    if not c:
        print("  not joined to a live component; no member list")
        return 1
    FROM, TO = set(f["FROM"]), set(f["TO"])
    shown = 0
    for m in c["_members"]:
        base = a2b.get(m["model"])
        w = charge.words(f["prompt"], base) if base else {}
        sides = orient(m, FROM, TO)
        if not w or sides is None:
            continue
        fell, rose = sides
        fv = [(x, w[x]["scene"], w[x]["kind"]) for x in fell if x in w]
        rv = [(x, w[x]["scene"], w[x]["kind"]) for x in rose if x in w]
        if len(fv) < 2 or len(rv) < 2:
            continue
        print("\n  %s  (base %s)" % (m["model"], base))
        for lab, xs in (("FELL", fv), ("ROSE", rv)):
            print("    %s  %s" % (lab, "  ".join("%s %.2f/%s" % t for t in xs)))
            print("          mean %.3f" % st.mean([t[1] for t in xs]))
        print("    delta %+.3f" % (st.mean([t[1] for t in rv])
                                   - st.mean([t[1] for t in fv])))
        shown += 1
        if shown >= 3:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
