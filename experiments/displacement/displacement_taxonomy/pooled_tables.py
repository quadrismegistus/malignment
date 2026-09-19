"""One two-column table per frame, pooled over the 50 endpoints. Not per lineage.

    python -u pooled_tables.py --frame "She was so angry"    render one
    python -u pooled_tables.py --export                      -> results/pooled_frames.md

## THE UNIT CHANGES, AND THAT IS THE POINT

`crosslineage` puts ONE sentence and ALL its lineages in front of a reader, so a
reading is (frame x rater) and the corpus is 337 of them over 95 frames. That
design exists for a stated reason -- "the fact that seventeen lineages perform an
operation and one runs it backwards is invisible at annotation time" -- and it
worked: reversals are 322 of 337 readings.

It also produced 907 near-duplicate operations, because a frame was read 2 to 16
times and every reading names the same few movements again. Both agents given
those spent most of their groups merging them back: 158 of gpt6's 200 and 62 of
opus5's 107 sat inside a single frame.

This pools the fifty arms FIRST and renders one table per frame. 95 entries, no
duplicates, and every word carries its own roster support.

## WHAT POOLING BUYS AND WHAT IT COSTS

**Buys.** The corroboration stops being a proxy. A component is currently "two
raters cited at least two of the same models", which approximates roster support;
here `kill 28/31` IS the support, printed on the row. And the deduplication
problem disappears with the duplicates.

**Costs, and it is the thing `crosslineage` was built for.** A reversal is
invisible in a pooled column. `punch 22/33` means eleven lineages move it the
other way, and the pooled rank shows only the net. Two of the ten relations are
reversals. The support column is the mitigation -- a reader can see 22/33 is not
33/33 -- but it is a number where the old design gave a visible split.

## RENDERED BY `run._table_two_column`, NOT BY A NEW FORMAT

The same function the r4, r5 and crosslineage instruments all declare, so a
pooled table and a per-lineage table are the same object with a different input
and can be read by one rater without relearning a layout. Its rules come with
it: membership and order are both MASS, ordering is by mass difference rather
than own-arm rank, a 1% floor inside the favouring arm, positions rather than
probabilities, and words whose rank contradicts their column are withheld and
counted rather than dropped.

## HOW THE ARMS ARE POOLED

Each lineage's arm is normalised to sum to 1 -- exactly as `crosslineage.tables`
does before rendering -- and the pooled arm is the MEAN of those across the 50.
A word absent from a lineage contributes 0 to that mean, which is correct: it is
absent from that field, and imputing anything else would turn a coverage
difference into a movement.

## NO UNDERSCORES

`crosslineage.BLANK` (`^_+$`) is applied BEFORE pooling and before
normalisation. Six of fifty models emit runs of underscores and on 27 of 35
frames at least one reached a rater's table; all six annotators then named a
"blank placeholder versus word" relation, and it is one of the twelve unanimous
clusters -- six readers, two families, three effort levels, agreeing on a
measurement artefact. Stripping before normalisation rather than at display time
means the mass is redistributed, so this is a different measurement of the same
surface and must not be pooled with an unstripped one.
"""
import argparse, collections, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "results", "pooled_frames.md")
BLANK = re.compile(r"^_+$")
#: a word moving in fewer lineages than this is a near-singleton whose pooled
#: rank is an accident of two or three models; `A(2/3)` and `place(1/2)` came
#: back in the first sample and are what this exists to remove
MIN_LINEAGES = 5


def frames():
    """Every frame carrying a blind crosslineage reading. -> [str]"""
    import json
    seen = set()
    stash = os.path.join(HERE, "results", "crosslineage_stash",
                         "jsonl.hashstash.raw", "data.jsonl")
    for line in open(stash, encoding="utf-8"):
        seen.add(json.loads(line)["__key__"]["frame_prompt"])
    return sorted(seen)


def pooled(prompt, min_lineages=MIN_LINEAGES, top=40):
    """(pre, post, support, n_units, n_below_theta) for one frame. -> tuple

    ## SOURCED FROM `movement.contrast`, NOT FROM A HAND-WRITTEN QUERY

    A first version copied `crosslineage.tables()`'s query, `merged=1` included.
    That is a PROVENANCE filter -- `merged` is `max(topup)`, so it means "a topup
    exists for this cell" -- and on "She was so angry she wanted to" it silently
    cut the roster from 50 endpoint pairs to 43. Six of the seven lost pairs have
    no topup on EITHER arm, so they were internally consistent and measured; they
    were dropped for having been measured once rather than twice. `crosslineage`
    at least names the exclusion in its output; this reported "43 lineages" and
    left a reader to assume that was the roster. RH: use movement.py.

    `movement.contrast` returns all 50, and two of its properties matter here:
    selection is DECLARED and blind to movement (`select_union` ranks each rung
    by its own mass, never by the difference), and a word missing from a rung
    comes back as a measured ZERO with `below_theta` counting how many -- "below
    theta" means smaller than 0.001, not absent, and a table that cannot tell
    those apart draws a truncation at the floor.

    `support[w]` is (falls, rises) over the units where the word moves at all --
    the evidence the per-lineage design made a reader look for, reduced to a
    number and printed beside the word.
    """
    from malignment import roster, movement as M
    ep, _ = roster.endpoints()
    units = [(a.split("/")[-1], [b, a]) for b, a in sorted(ep.items())]
    rows, meta = M.contrast(prompt, units, top=top, select_union=True)
    by = collections.defaultdict(dict)
    for r in rows:
        if BLANK.match(r["word"]):
            continue
        by[r["unit"]][(r["position"], r["word"])] = r["p"]
    pre = collections.defaultdict(float)
    post = collections.defaultdict(float)
    sup = collections.defaultdict(lambda: [0, 0])
    n = 0
    for unit, d in by.items():
        #: **NORMALISED WITHIN THE UNIT BEFORE POOLING**, as
        #: `crosslineage.tables` does before rendering: a lineage that happens to
        #: put more total mass on the selected words would otherwise weigh more
        #: in the mean for that reason alone.
        tb = sum(v for (pos, _w), v in d.items() if pos == 0)
        ta = sum(v for (pos, _w), v in d.items() if pos == 1)
        if tb <= 0 or ta <= 0:
            continue
        n += 1
        ws = {w for _pos, w in d}
        for w in ws:
            x = d.get((0, w), 0.0) / tb
            y = d.get((1, w), 0.0) / ta
            pre[w] += x
            post[w] += y
            if x != y:
                sup[w][0 if y < x else 1] += 1
    if not n:
        return None
    pre = {w: v / n for w, v in pre.items()}
    post = {w: v / n for w, v in post.items()}
    keep = {w for w in sup if sum(sup[w]) >= min_lineages}
    return ({w: v for w, v in pre.items() if w in keep},
            {w: v for w, v in post.items() if w in keep},
            {w: tuple(sup[w]) for w in keep}, n, meta.get("below_theta", 0))


def table(pre, post, sup, top=12):
    """The consistency-led table. -> (text, n_withheld)

    ## WHY NOT `run._table_two_column`, WHICH THIS FILE USED YESTERDAY

    That renderer places and orders by MASS, and its docstring gives the reason
    its two rules must agree: "filtering on one quantity and sorting on another
    makes a column whose own ordering contradicts its heading."

    Pooled, mass is the wrong quantity, and it is wrong in a measurable way.
    Correlation between |rank move| and lineage agreement, over three frames:
    -0.02, +0.11, +0.14. They are ORTHOGONAL, and they order different words:
    ranked by mass loss "She was so angry" gives kill, go, beat; ranked by
    falling lineages it gives shoot, beat, kill -- and `shoot` falls in 45 of 50
    while moving from rank 36 to 41, invisible under mass. Meanwhile `kill`
    moves ONE position while 44 of 50 lineages push it down, because a pooled
    rank is the rank of a MEAN and the mean flattens when lineages disagree
    about absolute order.

    So membership and order are both AGREEMENT here, which is the same rule the
    original states, applied to the quantity that now carries the signal. The
    headings say so: a column headed by mass whose rows are sorted by agreement
    is the defect that rule exists to prevent.

    ## RANK IS KEPT, DEMOTED

    At r ~ 0 it is independent information, not redundancy: `balls` (41/45, rank
    24 -> 43) and `big` (40/49, rank 26 -> 29) are both near-unanimous and only
    one is a large movement. Dropping it would lose that.

    ## AND STILL NO PROBABILITIES

    `_table_two_column` withholds them on measured grounds -- percentages
    produced 155 uses of the mass vocabulary over 29 cells against 2 under
    ranks. A count of LINEAGES is not a percentage; it is a count of models,
    which is this campaign's unit of independence everywhere else.
    """
    rb = {w: i + 1 for i, w in enumerate(sorted(pre, key=lambda w: -pre[w]))}
    ra = {w: i + 1 for i, w in enumerate(sorted(post, key=lambda w: -post[w]))}
    fall, rise, tied = [], [], 0
    for w, (f, r) in sup.items():
        if f == r:
            #: **A TIE IS NOT A DIRECTION.** Half the lineages each way is the
            #: one case where a pooled column would be inventing a sign, so it
            #: is counted and dropped rather than assigned.
            tied += 1
            continue
        (fall if f > r else rise).append(w)

    def block(ws, head, idx):
        ws = sorted(ws, key=lambda w: (-sup[w][idx], -(sup[w][0] + sup[w][1]), w))
        out = ["%-16s %10s   %s" % (head, "lineages", "rank")]
        for w in ws[:top]:
            f, r = sup[w]
            a = "%3d" % rb[w] if w in rb else "  -"
            b = "%3d" % ra[w] if w in ra else "  -"
            d = ("%+5d" % (rb[w] - ra[w])) if (w in rb and w in ra) else "    -"
            out.append("  %-14s %6d/%-3d   %s -> %s %s"
                       % (w, sup[w][idx], f + r, a, b, d))
        return "\n".join(out)

    txt = "%s\n\n%s" % (block(fall, "FALLS IN MOST", 0),
                        block(rise, "RISES IN MOST", 1))
    if tied:
        txt += ("\n\n%d word(s) omitted: the lineages split evenly on which way "
                "they move." % tied)
    return txt, tied


def render(prompt, min_lineages=MIN_LINEAGES, top=12):
    """The consistency table for one pooled frame. -> (text, n_units) or None"""
    got = pooled(prompt, min_lineages)
    if not got:
        return None
    pre, post, sup, n, _bt = got
    text, _tied = table(pre, post, sup, top)
    return text, n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frame", default=None, help="prefix of one frame")
    ap.add_argument("--min-lineages", type=int, default=MIN_LINEAGES)
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    fs = frames()
    if a.frame:
        hit = [f for f in fs if f.lower().startswith(a.frame.lower())]
        if len(hit) != 1:
            raise SystemExit("%d frames match %r" % (len(hit), a.frame))
        got = render(hit[0], a.min_lineages)
        if not got:
            raise SystemExit("no pooled arms for %r" % hit[0])
        text, n = got
        print("%s ___\n\n%s" % (hit[0], text))
        print("\n(%d lineages. `lineages` is how many of those in which the word "
              "moves at all\n move it the way its column says; `rank` is its "
              "position in each pooled arm.)" % n)
        return 0
    if a.export:
        L = ["# %d frames, pooled over the endpoint lineages" % len(fs), "",
             "Each table is ONE sentence with the fifty base->aligned pairs "
             "pooled. A word is placed by WHICH WAY MOST LINEAGES MOVE IT and "
             "ordered by how many agree.",
             "",
             "`lineages` is n/m: of the m lineages in which the word moves at "
             "all, n move it the way its column says. 44/50 is near-unanimous; "
             "27/50 means twenty-three lineages run it the other way.",
             "",
             "`rank` is the word's position in each pooled arm, and it is "
             "independent of agreement -- a word can be near-unanimous and "
             "barely move (`kill 44/50, 1 -> 2`) or move far on less agreement "
             "(`shout 31/50, 25 -> 14`).",
             "",
             "Words moving in fewer than %d lineages are omitted, words whose "
             "lineages split evenly are counted and omitted, and runs of "
             "underscores are stripped before pooling." % a.min_lineages,
             "", "---", ""]
        kept = 0
        for f in fs:
            got = render(f, a.min_lineages)
            if not got:
                continue
            kept += 1
            text, n = got
            L += ["## %s ___" % f, "", "```", text, "```", ""]
        txt = "\n".join(L)
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        open(a.out, "w").write(txt)
        print("%d of %d frames -> %s" % (kept, len(fs), a.out))
        print("  %s chars, ~%s tokens" % (format(len(txt), ","),
                                          format(int(len(txt) / 3.6), ",")))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
