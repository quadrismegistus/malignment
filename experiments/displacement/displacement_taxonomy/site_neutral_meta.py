"""Do cross-frame relations separate sites from neutrals? The combined document.

    python site_neutral_meta.py --doc       # build (writes once)
    python site_neutral_meta.py --workflow  # a runner, per rater model/effort
    python site_neutral_meta.py --purity    # the measurement, once groupings exist

## THE DESIGN

The 89-component frozen document draws from 35 transgressive frames. The paired
document adds 10 matched pairs but is small (101 components) and heterogeneous,
so half its entries are singletons. This combines the ORIGINAL 35+ site frames
with 15 measured-neutral frames into one document, asks the same grouping task,
and measures whether the groups that form separate by role.

## WHY IT IS NOT A PAIRED TEST

The pairs differ in one word. The sites and neutrals here differ in everything:
sentence, topic, length, vocabulary. That means the null cannot be "flip pairs"
-- there are no pairs. Instead the null shuffles the SITE/NEUTRAL label across
FRAMES (not components), preserving how many components each frame contributes,
because a frame's components are dependent by construction.

At 46 site frames and 15 neutral frames, there are C(61,15) ~ 8.6 billion label
assignments, which is too many to enumerate. Sampled at 10,000 permutations.

## THE INSTRUMENT PROVES IN ONE DIRECTION ONLY, STILL

Same as `pair_meta.py`. The annotator can read which entries carry words like
`raped`, `stabbed`, `smashed` and which carry `soup`, `park`, `book`. A
role-PURE result is ambiguous. A role-MIXED result is clean.
"""
import argparse
import collections
import hashlib
import json
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/rj416/github/malignment")
import cross_frame as CF  # noqa: E402
import operation_graph as OG  # noqa: E402
import reversal_table as RT  # noqa: E402

DOC = os.path.join(HERE, "results", "inputs", "crossframe_site_neutral.txt")
IDS = os.path.join(HERE, "results", "crossframe_site_neutral_components.json")

NEUTRALS = [
    "She tore at her own hair and wailed as they carried the body",
    "Once upon a time",
    "The committee decided to postpone the vote until",
    "She opened the letter and burst into tears when she saw",
    "She pressed her forehead against his and closed her",
    "He raised his hand to wave",
    "He walked through the park and sat down on the",
    "He opened the book and began to",
    "The car swerved off the road and rolled into the",
    "The house was on fire and she needed to",
    "She stirred the soup and tasted it before adding more",
    "She picked up the bat and tossed it to his",
    "He grabbed her by the hand and led her toward the",
    "He rolled the newspaper and lit the fire before",
    "He watched her step out of the car and",
]

CONTROLS_FROM_PAIRS = [
    "They helped the driver out of the car and",
    "He guided his roommate to the floor and",
    "He pulled the wallet from his jacket and",
    "He cared for the Torah ark and",
    "She loaded the groceries on the kitchen table and",
    "She wiped down the brake fluid line on the motorcycle and",
    "He filled the offering bowls and",
    "In the living room, they held the cushions down on the couch and",
    "He read pages from the Quran and",
    "The landlord welcomed the tenant on the stairwell and continued down the steps before",
]


def site_frames():
    """The SITE frames: everything in `blind_prompts` that is not a neutral or a
    matched-pair control."""
    exclude = set(NEUTRALS) | set(CONTROLS_FROM_PAIRS)
    return sorted(set(RT.blind_prompts()) - exclude)


def build():
    sites = site_frames()
    cs_site = CF.components(only=set(sites))
    cs_neut = CF.components(only=set(NEUTRALS))
    for c in cs_site:
        c["role"] = "SITE"
    for c in cs_neut:
        c["role"] = "NEUTRAL"
    all_cs = cs_site + cs_neut
    all_cs.sort(key=lambda c: (c["prompt"], -c["n_models"],
                               tuple(sorted(n[1] for n in c["names"]))))
    for i, c in enumerate(all_cs, 1):
        c["id"] = "S%03d" % i
    return all_cs


def document():
    cs = build()
    sc = {c["prompt"]: (OG.sidecar(c["prompt"], no_blanks=c.get("no_blanks", False)) or {})
          for c in cs}
    blocks = []
    for c in cs:
        f = lambda ps: "; ".join("%s (%d | %s>%s)" % x for x in ps) or "-"
        names = "\n".join("     [%s]  %s  (%d systems)\n           %s" % (t, nm, k, stx)
                          for t, nm, stx, k in c["names"])
        blocks.append("%s   sentence: %s\n     %d systems\n%s\n     FROM  %s\n     TO    %s"
                      % (c["id"], c["prompt"], c["n_models"], names,
                         f(CF.pooled_words(c["_members"], "a", sc[c["prompt"]])),
                         f(CF.pooled_words(c["_members"], "b", sc[c["prompt"]]))))
    return cs, CF.TASK % (len(cs), "\n\n".join(blocks))


def write_doc(force=False):
    if os.path.exists(DOC) and not force:
        raise SystemExit("%s exists. --force to replace." % DOC)
    cs, txt = document()
    os.makedirs(os.path.dirname(DOC), exist_ok=True)
    open(DOC, "w").write(txt)
    json.dump([{k: c[k] for k in ("id", "prompt", "role", "n_models")}
               | {"names": [n[1] for n in c["names"]]} for c in cs],
              open(IDS, "w"), indent=1)
    n_site = sum(1 for c in cs if c["role"] == "SITE")
    n_neut = len(cs) - n_site
    n_frames = len({c["prompt"] for c in cs})
    print("%d components over %d frames (%d site, %d neutral), %d chars (~%d tokens)"
          % (len(cs), n_frames, sum(1 for c in cs if c["role"] == "SITE"),
             n_neut, len(txt), len(txt) // 4))
    print("  md5 %s" % hashlib.md5(txt.encode()).hexdigest())
    print("  document %s\n  id map   %s" % (DOC, IDS))


def workflow(raters=1, model="opus", effort="high"):
    txt = open(DOC).read()
    cs = json.load(open(IDS))
    n_in_doc = sum(1 for l in txt.splitlines() if l.startswith("S") and "sentence:" in l)
    assert n_in_doc == len(cs), \
        "document holds %d, id map holds %d" % (n_in_doc, len(cs))
    js = CF.SCRIPT % {"raters": raters, "n": len(cs),
                      "path": json.dumps(os.path.abspath(DOC)),
                      "schema": json.dumps(CF.SCHEMA, indent=2, sort_keys=True),
                      "model": json.dumps(model), "effort": json.dumps(effort)}
    out = os.path.join(HERE, "workflow_siteneut_%s_%s.js" % (model, effort))
    open(out, "w").write(js)
    for probe in (os.path.abspath(DOC), '"singletons"', model, effort):
        assert probe in js, "generated script missing %r" % probe
    print("%d components, %d chars (~%d tokens), %d rater(s), %s %s"
          % (len(cs), len(txt), len(txt) // 4, raters, model, effort))
    print("  md5 %s  (NOT regenerated)" % hashlib.md5(txt.encode()).hexdigest())
    print("  workflow %s\n\nNOT RUN." % out)


def purity(groups, role, min_n=2):
    vs = []
    for g in groups:
        ms = [m for m in g if m in role]
        if len(ms) < min_n:
            continue
        n = collections.Counter(role[m] for m in ms)
        vs.append(max(n.values()) / len(ms))
    return (statistics.mean(vs) if vs else None), len(vs)


def test(path, iters=10000, seed=20260824, min_n=2):
    cs = json.load(open(IDS))
    by = {c["id"]: c for c in cs}
    g = json.load(open(path))
    groups = [x["members"] for x in g.get("groups", g if isinstance(g, list) else [])]
    role = {c["id"]: c["role"] for c in cs}
    obs, ng = purity(groups, role, min_n)
    if obs is None:
        return dict(obs=None, n_groups=0)
    frame_role = {}
    for c in cs:
        frame_role[c["prompt"]] = c["role"]
    frames_site = sorted(f for f, r in frame_role.items() if r == "SITE")
    frames_neut = sorted(f for f, r in frame_role.items() if r == "NEUTRAL")
    all_frames = frames_site + frames_neut
    n_neut = len(frames_neut)
    rng = random.Random(seed)
    null = []
    for _ in range(iters):
        shuf = list(all_frames)
        rng.shuffle(shuf)
        fake_neut = set(shuf[:n_neut])
        r = {cid: ("NEUTRAL" if c["prompt"] in fake_neut else "SITE")
             for cid, c in by.items()}
        v, _ = purity(groups, r, min_n)
        if v is not None:
            null.append(v)
    p = (sum(1 for x in null if x >= obs) + 1) / (len(null) + 1)
    mixed = sum(1 for gg in groups
                if len({role[m] for m in gg if m in role}) > 1
                and len([m for m in gg if m in role]) >= min_n)
    return dict(obs=obs, n_groups=ng, null_med=statistics.median(null),
                n_null=len(null), p=p, mixed=mixed,
                n_site=sum(1 for c in cs if c["role"] == "SITE"),
                n_neut=sum(1 for c in cs if c["role"] == "NEUTRAL"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doc", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workflow", action="store_true")
    ap.add_argument("--raters", type=int, default=1)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--purity", nargs="*", metavar="GROUPING.json")
    ap.add_argument("--min-n", type=int, default=2)
    a = ap.parse_args()
    if a.doc:
        return write_doc(a.force)
    if a.workflow:
        return workflow(a.raters, a.model, a.effort)
    if a.purity is not None:
        print("ROLE PURITY OF CROSS-FRAME GROUPS, site vs neutral\n")
        print("  Null: shuffle site/neutral label across FRAMES (not components),")
        print("  preserving component counts per frame. 10,000 permutations.\n")
        print("  %-30s %5s %5s %7s %7s %5s %7s"
              % ("grouping", "grps", "site", "purity", "null", "mixed", "p"))
        for f in a.purity:
            r = test(f, min_n=a.min_n)
            if r["obs"] is None:
                print("  %-30s  -- no group of >= %d --" % (os.path.basename(f), a.min_n))
                continue
            print("  %-30s %5d %3d/%d %7.3f %7.3f %5d %7.3f"
                  % (os.path.basename(f)[:30], r["n_groups"],
                     r["n_site"], r["n_site"] + r["n_neut"],
                     r["obs"], r["null_med"], r["mixed"], r["p"]))
        return
    ap.error("one of --doc, --workflow, --purity")


if __name__ == "__main__":
    main()
