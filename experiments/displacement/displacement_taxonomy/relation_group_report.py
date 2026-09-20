"""Which way each contrast axis runs, base -> aligned, and whether that is a direction at all.

    python -u relation_group_report.py            -> results/relation_groups_seed0.md
    python -u relation_group_report.py --seed 1   a replicate under a different shuffle

## THE AXIS IS A JUDGEMENT AND THE DIRECTION IS A COUNT

`relation_group_input.py` exports the 2,466 blind readings with the words
oriented and the text left alone, because the coder was blinded and wrote "one
group ... the other" in 2,426 of 2,466 explanations. A workflow then did two
things in two stages that could not see each other:

    propose + consolidate   name + explanation ONLY -- no words, no direction.
                            16 readers, 280 proposals, merged to 28 axes.
    assign                  the same text PLUS the oriented words, and for each
                            relation two answers: which axis, and which POLE the
                            BASE words sit on.

So the vocabulary was fixed before any direction was visible, and `base_pole` is
the only place direction enters the grouping. **THAT SEPARATION IS WHAT MAKES
THIS TESTABLE.** If the poles had been named from the words, "the base side is
physical" would be true by construction. Here the poles were named by readers
who never saw which side fell, and the count below can come out 50/50.

## WHAT THE TEST IS, AND WHAT IT IS NOT

For each axis: of the relations on it whose base side sits on a pole at all, how
many sit on `pole_x`. Two-sided exact binomial at p=0.5, BH over the axes that
reach n>=8.

**THE NULL IS NOT "NOTHING HAPPENS".** A 50/50 split does not mean alignment
left the axis alone; it means the axis has no CONSISTENT direction across
frames -- half the frames move one way and half the other. An axis can be the
site of enormous movement and still be null here. What this measures is whether
a contrast has a preferred direction over the corpus, which is the claim the
displacement argument actually makes.

**AND THE UNIT IS THE READING, NOT THE FRAME.** One frame yields one reading, so
these are near-independent, but a slot battery (`When the <GROUP> moved onto the
street ...`) contributes as many readings as it has fillers. `templates` reports
the floor on independence the same way `feeling_matrix` does.
"""
import argparse, collections, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SLOT = re.compile(r"\bthe [A-Z][A-Za-z-]*s?\b")
MIN_N = 8


def load(seed=0):
    src = os.path.join(HERE, "results", "relations_for_grouping.jsonl")
    rel = {}
    for line in open(src, encoding="utf-8"):
        r = json.loads(line)
        rel[r["id"]] = r
    d = os.path.join(HERE, "results", "grouping_seed%d" % seed)
    vocab = json.load(open(os.path.join(d, "vocabulary.json"), encoding="utf-8"))
    got = []
    ax_files = sorted(glob.glob(os.path.join(d, "axis_*.json")))
    if ax_files:
        #: **THE TWO-STAGE LAYOUT, AND THE POLE COMES BACK BLINDED.** Run 2
        #: splits the judgement: `axis_NN.json` places each relation from the
        #: NAMED CONTRAST alone, `pole_NN.json` says which pole LIST 1 sits on
        #: from the WORDS alone -- and which list was the base was drawn per
        #: relation by `relation_group_input.flip`, so the pole reader could not
        #: apply a prior about what alignment does. The direction is restored
        #: here, by arithmetic, and nowhere else.
        from relation_group_input import flip
        #: **THE IDS COME BACK AS STRINGS FROM SOME SHARDS AND INTS FROM
        #: OTHERS.** The schema says integer and the agents wrote what they
        #: wrote; `flip` takes an int and raised on the first string it met.
        #: Coerced at the boundary rather than trusted, because a join that
        #: silently misses half its keys is the failure this file exists to
        #: catch and it would have shown up as "missing 1,200".
        poles = {}
        for f in sorted(glob.glob(os.path.join(d, "pole_*.json"))):
            for r in json.load(open(f, encoding="utf-8")):
                poles[int(r["id"])] = r.get("list1_pole", "unclear")
        for f in ax_files:
            for r in json.load(open(f, encoding="utf-8")):
                r = dict(r, id=int(r["id"]))
                lp = poles.get(r["id"], "unclear")
                #: base shown SECOND -> the pole LIST 1 sits on is the pole the
                #: ALIGNED side sits on, so the base sits on the other one
                bp = lp if not flip(r["id"], seed) else \
                    {"x": "y", "y": "x"}.get(lp, "unclear")
                got.append({"id": r["id"], "axis": r["axis"], "base_pole": bp})
    else:
        for f in sorted(glob.glob(os.path.join(d, "assign_*.json"))):
            j = json.load(open(f, encoding="utf-8"))
            got.extend(j if isinstance(j, list) else j.get("assignments", j))
    #: **VALIDATE AGAINST THE SOURCE, NOT AGAINST THE AGENTS' OWN REPORTS.**
    #: Every assign agent returned a note saying it had checked its own shard
    #: for missing ids, extras and duplicates. Sixteen self-reports of a clean
    #: pass are sixteen claims, and the population is one join away.
    seen = collections.Counter(a["id"] for a in got)
    known = {v["id"] for v in vocab["axes"]} | {"other"}
    bad = {
        "missing": sorted(set(rel) - set(seen)),
        "extra": sorted(set(seen) - set(rel)),
        "duplicated": sorted(i for i, n in seen.items() if n > 1),
        "unknown_axis": sorted({a["axis"] for a in got} - known),
        "bad_pole": sorted({a["base_pole"] for a in got} - {"x", "y", "unclear"}),
    }
    return rel, vocab, got, bad


def _norm(s):
    """Fold a proposal name to something two writers of it will agree on.

    **THREE TIMES NOW A MATCHER ARTEFACT HAS PRODUCED WRONG SUPPORT COUNTS.**
    Whole-string equality missed `Name: pole / pole` cited as `Name`; the fix
    for that missed `vs.` cited as `vs`; and both times the wrong numbers were
    quoted before anyone noticed, once into a collaborator's citation decision.
    The lesson is not "add another case" -- it is that this comparison belongs
    in the producer with a stated normalisation, not in an ad-hoc script per
    question. Lowercase, drop the pole suffix after a colon, strip punctuation,
    collapse whitespace.
    """
    s = s.strip().lower().split(":")[0]
    s = re.sub(r"[.,;/()\-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def support(seed, proposals):
    """axis id -> how many propose shards independently named it.

    `proposals` is {shard: [name]} from the run's journal. Each shard is a
    random 1/16 of the corpus, so an axis present throughout should be named by
    nearly all sixteen; this is the only replication a single run affords.
    """
    d = os.path.join(HERE, "results", "grouping_seed%d" % seed)
    vocab = json.load(open(os.path.join(d, "vocabulary.json"), encoding="utf-8"))
    idx = {k: {_norm(x) for x in v} for k, v in proposals.items()}
    out, unresolved = {}, []
    for ax in vocab["axes"]:
        sh = set()
        for m in ax.get("merged_from", []):
            head, _, name = m.partition(":")
            head = head.strip()
            if not (head[:1] == "s" and head[1:].isdigit()):
                unresolved.append((ax["id"], m))
                continue
            k = int(head[1:])
            if k in idx and _norm(name) in idx[k]:
                sh.add(k)
            else:
                unresolved.append((ax["id"], m))
        out[ax["id"]] = len(sh)
    return out, unresolved


def binom_p(k, n):
    from math import comb
    if n == 0:
        return 1.0
    lo = min(k, n - k)
    return min(1.0, 2 * sum(comb(n, i) for i in range(lo + 1)) / (2.0 ** n))


def bh(pairs):
    """[(key, p)] -> {key: q}"""
    order = sorted(range(len(pairs)), key=lambda i: pairs[i][1])
    M, q, prev = len(pairs), {}, 1.0
    for rank, i in enumerate(reversed(order), 1):
        prev = min(prev, pairs[i][1] * M / (M - rank + 1))
        q[pairs[i][0]] = prev
    return q


def report(seed=0):
    rel, vocab, got, bad = load(seed)
    axes = {v["id"]: v for v in vocab["axes"]}
    by = collections.defaultdict(list)
    for a in got:
        by[a["axis"]].append(a)

    rows = []
    for aid, hits in by.items():
        placed = [h for h in hits if h["base_pole"] in ("x", "y")]
        x = sum(1 for h in placed if h["base_pole"] == "x")
        tmpl = len({SLOT.sub(" the <SLOT>", rel[h["id"]]["frame"]) for h in hits})
        zh = sum(1 for h in hits if rel[h["id"]]["lang"] == "zh")
        rows.append({"axis": aid, "n": len(hits), "placed": len(placed),
                     "x": x, "y": len(placed) - x, "templates": tmpl, "zh": zh,
                     "p": binom_p(x, len(placed)) if len(placed) >= MIN_N else None})
    tested = [(r["axis"], r["p"]) for r in rows if r["p"] is not None]
    q = bh(tested)
    for r in rows:
        r["q"] = q.get(r["axis"])
    rows.sort(key=lambda r: (r["q"] if r["q"] is not None else 9, -r["n"]))
    return rel, axes, vocab, rows, bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    #: **SEED 1 IS THE RUN OF RECORD (RH).** Seed 0 is the LEAKED run: its
    #: propose stage was told the corpus was alignment base-vs-aligned, that a
    #: hidden direction existed, and what count to aim for. Seed 1 fixed all
    #: three, split the axis judgement from the pole judgement, and blinded the
    #: pole reader to which list fell. Both are kept -- the comparison between
    #: them is a result -- but the DEFAULT is the decision, and a default
    #: pointing at the leaked run while a document says otherwise is exactly
    #: the failure `fate_compare.py` was corrected for this morning. I then
    #: reproduced it here within the hour, which is why it is written down.
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    rel, axes, vocab, rows, bad = report(a.seed)

    L = ["# Contrast axes and which way they run — seed %d" % a.seed, ""]
    hurt = {k: v for k, v in bad.items() if v}
    L.append("**Join against the source:** %s"
             % ("; ".join("%s %d" % (k, len(v)) for k, v in hurt.items())
                if hurt else
                "2,466 relations, none missing, none extra, none duplicated, "
                "every axis id in the vocabulary, every pole in {x, y, unclear}."))
    L.append("")
    L.append("The vocabulary was fixed by readers who saw the contrast text and "
             "**no words and no direction**; `base_pole` was supplied afterwards "
             "by readers who saw the oriented words. A 50/50 split is a real "
             "answer -- it says the axis has no consistent direction, not that "
             "nothing moved on it.")
    L.append("")
    #: **`unclear` IS A RESULT AND IT HAS ITS OWN COLUMN.** It means the reader
    #: had the oriented words in front of them and could not put the base side
    #: on either pole -- both groups sit on the same pole, or straddle. On
    #: `referent_substitution` that is 41 of 44, which is not a coding failure:
    #: it is the same-field reshuffle, a contrast that exists WITHIN one pole.
    #: Folded into a denominator it would have looked like a small null axis.
    L.append("| axis | n | base on pole_x | base on pole_y | unclear | q | reads |")
    L.append("|---|---|---|---|---|---|---|")
    for r in rows:
        ax = axes.get(r["axis"])
        if not ax:
            L.append("| `other` | %d | — | — | — | — | no axis fitted |" % r["n"])
            continue
        lead = ("%s → %s" % (ax["pole_x"], ax["pole_y"])) if r["x"] > r["y"] else \
               ("%s → %s" % (ax["pole_y"], ax["pole_x"]))
        sig = r["q"] is not None and r["q"] < 0.05
        L.append("| `%s` %s | %d | %d | %d | %d | %s | %s |"
                 % (r["axis"], ax["name"], r["n"], r["x"], r["y"],
                    r["n"] - r["placed"],
                    ("**%.2g**" % r["q"]) if sig else
                    ("%.2f" % r["q"] if r["q"] is not None else "n<%d" % MIN_N),
                    ("**%s**" % lead) if sig else "no consistent direction"))
    L.append("")

    L.append("## The axes")
    L.append("")
    for r in rows:
        ax = axes.get(r["axis"])
        if not ax:
            continue
        L.append("### `%s` — %s" % (ax["id"], ax["name"]))
        L.append("")
        L.append("**pole_x** %s · **pole_y** %s" % (ax["pole_x"], ax["pole_y"]))
        L.append("")
        L.append(ax["definition"])
        L.append("")
        L.append("%d relations (%d Chinese), %d distinct sentence templates; "
                 "base side placed on a pole in %d of them, %d on pole_x."
                 % (r["n"], r["zh"], r["templates"], r["placed"], r["x"]))
        L.append("")
        if ax.get("merged_from"):
            L.append("_merged from %d proposals: %s_"
                     % (len(ax["merged_from"]),
                        "; ".join(ax["merged_from"][:6])
                        + (" …" if len(ax["merged_from"]) > 6 else "")))
            L.append("")
    L.append("## What the consolidator said it could not do")
    L.append("")
    L.append(vocab["notes"])
    out = a.out or os.path.join(HERE, "results",
                                "relation_groups_seed%d.md" % a.seed)
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[:len(rows) + 14]))
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
