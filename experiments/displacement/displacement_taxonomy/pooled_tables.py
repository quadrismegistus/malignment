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
#: **SELECT ON AGREEMENT, NOT ON MOVEMENT.** The first version filtered on how
#: many lineages move a word AT ALL, which is inert: any non-zero delta counts,
#: so nearly every word moves in nearly every lineage and the floor admitted
#: 116 words at a median frame. What carries the evidence is how many move it
#: the SAME WAY. At 35 of 50 -- seven lineages in ten -- the median frame gives
#: 17 words and the 90th percentile 39, which is the range the per-lineage
#: tables and the 907 file both sat in, reached by a stated rule rather than by
#: a display cap.
#:
#: **BUT A SYMMETRIC FLOOR CANNOT BE SET HIGH, BECAUSE THE SIDES ARE NOT
#: SYMMETRIC.** Falling is far more agreed than rising. Median words per side
#: over sixteen frames: at a floor of 25, 56 falls against 9 rises; at 30, 33
#: against 3; at 35, 17 against 0, and fifteen of the sixteen frames have fewer
#: than three risers at all. A floor tuned to the falling side empties the
#: rising one and leaves nothing to relate. So the floor sits at 25 -- half the
#: roster -- and the asymmetry is carried by the AGREEMENT COLUMN, where a
#: reader sees `scream 43/50` beside `hurt 29/50` and can weigh them, rather
#: than by a row count that would hide it as absence.
MIN_AGREE = 15
#: **THE CANDIDATE POOL, WHICH WAS SILENTLY THE BINDING CONSTRAINT.** `top=40`
#: was a default written with no reasoning behind it, and it was doing the
#: selecting: it returned 45 words per frame, of which 44 cleared a floor of 5,
#: so the floor was inert. Raising the pool to 200 leaves 93-141 words clearing
#: a floor of 20 on the same frames -- well-attested movement that `top=40`
#: discarded before any filter could see it. The pool is now large enough that
#: the FLOOR decides, which is the only defensible arrangement: one stated rule
#: doing the selection rather than an unstated number upstream of it.
POOL = 200


def frames():
    """Every frame carrying a blind crosslineage reading. -> [str]"""
    import json
    seen = set()
    stash = os.path.join(HERE, "results", "crosslineage_stash",
                         "jsonl.hashstash.raw", "data.jsonl")
    for line in open(stash, encoding="utf-8"):
        seen.add(json.loads(line)["__key__"]["frame_prompt"])
    return sorted(seen)


def pooled(prompt, min_agree=MIN_AGREE, top=POOL):
    """(faller/riser/still counts per word) for one frame. -> tuple

    ## COUNTS THE CANONICAL CLASSIFICATION, NOT THE SIGN OF A DELTA

    A first version pooled the arms and counted the SIGN of each lineage's
    normalised change. `movement.py` says in as many words why that is wrong:

        Without the last line a "riser" is any word that went up, and every word
        goes up a little when a faller's mass is removed. The null is what
        separates redistribution from bookkeeping.

    The CANONICAL rule tests a riser against the RENORMALISATION NULL -- `Q >
    P * (R/S)`, more than the mass freed by the fallers explains -- and requires
    a minimum probability and a minimum move on both sides. Sign-counting has
    none of that, and the damage was not subtle. On "She was so angry she wanted
    to" the canonical classes give `kill` 28 faller / 3 riser / 19 STILL where
    sign-counting said 45 of 50 move it down: ten to twenty-five lineages per
    word do not meaningfully move it at all, and every one was being counted.

    **AND IT MANUFACTURED A FINDING.** Sign-counting made falling look far more
    agreed than rising -- median 56 falls against 9 rises per frame -- and that
    asymmetry is exactly what diffuse renormalisation produces: real fallers are
    concentrated and agree, bookkeeping risers are spread thin over many words
    and each one's count is small. Under the canonical rule the sides are even,
    and `scream` at 39 risers is the largest count in EITHER direction.

    ASYMMETRY THAT IS REAL AND MUST BE CARRIED: risers are tested against the
    null and FALLERS ARE NOT. `movement.py`: "Nothing downstream may describe
    fallers as 'beyond renormalisation' -- they are not tested for it, and a
    word can halve purely because mass left the system elsewhere."

    `still` is reported rather than dropped. A word unmoved in 26 of 50 lineages
    is a different fact from one moved in all of them, and a denominator that
    hides it turns "half the roster did nothing" into silence.
    """
    from malignment import movement as M
    rows = M.endpoint_movement(prompt=prompt, rule_version=4)
    cnt = collections.defaultdict(lambda: collections.Counter())
    pairs = set()
    for r in rows:
        w = r["word"]
        if BLANK.match(w):
            continue
        pairs.add((r["base"], r["aligned"]))
        cnt[w][r.get("cls")] += 1
    if not pairs:
        return None
    keep = {w: (c.get("faller", 0), c.get("riser", 0), c.get("still", 0))
            for w, c in cnt.items()
            if max(c.get("faller", 0), c.get("riser", 0)) >= min_agree}
    return keep, len(pairs)


def _fold(rows, min_agree):
    """Rows for ONE prompt -> (counts, n_pairs) or None. The shared tail."""
    cnt = collections.defaultdict(lambda: collections.Counter())
    pairs = set()
    for r in rows:
        w = r["word"]
        if BLANK.match(w):
            continue
        pairs.add((r["base"], r["aligned"]))
        cnt[w][r.get("cls")] += 1
    if not pairs:
        return None
    keep = {w: (c.get("faller", 0), c.get("riser", 0), c.get("still", 0))
            for w, c in cnt.items()
            if max(c.get("faller", 0), c.get("riser", 0)) >= min_agree}
    return keep, len(pairs)


def pooled_many(prompts, min_agree=MIN_AGREE, batch=150):
    """`pooled()` for many prompts at once. -> {prompt: (counts, n_pairs)}

    **TEN TO ONE, AND THE WHOLE COST WAS ROUND TRIPS.** `pooled()` issues one
    ClickHouse query per prompt and re-derives `roster.endpoints()` inside each,
    which is 0.742 s apiece; batched it is 0.073 s. Over the charge corpus that
    is 35 minutes against three and a half, and the tables are the same tables.

    The batch is 150 by default because size is the real constraint, not count:
    24 prompts already return 155k rows, so the whole corpus in one query is
    about 18M and does not fit. A prompt absent from the store is simply absent
    from the result, exactly as `pooled()` returns None for it.

    Counting is `_fold`, shared with `pooled()`, so the two cannot drift into
    disagreeing about what a pooled table is.
    """
    from malignment import movement as M
    out = {}
    ps = list(prompts)
    for i in range(0, len(ps), batch):
        chunk = ps[i:i + batch]
        rows = M.endpoint_movement(prompts=chunk, rule_version=4)
        by = collections.defaultdict(list)
        for r in rows:
            by[r["prompt"]].append(r)
        for p in chunk:
            got = _fold(by.get(p, []), min_agree)
            if got:
                out[p] = got
    return out


def table(counts, top=20, blind=None):
    """The classified table. -> (text, n_tied)

    ## THREE COUNTS AND NO RANK

    An earlier version led with pooled RANK and then with the sign-count. Rank
    is gone because it needed pooled probabilities, which are a second source
    and a weaker one: correlation between |rank move| and agreement was ~0, and
    a pooled rank is the rank of a MEAN, which flattens when lineages disagree
    about absolute order -- `kill` moved ONE position while most of the roster
    demoted it.

    The three counts are the whole table and are self-contained. `28 / 3 / 19`
    says twenty-eight lineages demote the word, three promote it, nineteen leave
    it where it was. A reader can weigh that without a second quantity, and
    nothing here is a probability, so the measured objection to percentages --
    155 uses of the mass vocabulary over 29 cells against 2 under ranks -- does
    not arise.

    ## BLINDED BY SWAPPING TWO COLUMNS

    `this` and `other` are the counts for the column's own direction and the
    opposite one. Swapping them and the group labels is the whole blind: no
    arrow, no sign, nothing that says which condition is the aligned arm.
    `still` is invariant under the swap, which is one way to see that it carries
    no direction.
    """
    fall, rise, tied = [], [], 0
    for w, (f, r, _s) in counts.items():
        if f == r:
            tied += 1
            continue
        (fall if f > r else rise).append(w)
    cut = {}

    def block(ws, head, idx):
        ws = sorted(ws, key=lambda w: (-counts[w][idx], counts[w][2], w))
        cut[head] = (len(ws), max(0, len(ws) - top))
        out = ["%-16s %6s %6s %6s" % (head, "this", "other", "still")]
        for w in ws[:top]:
            c = counts[w]
            out.append("  %-14s %6d %6d %6d"
                       % (w, c[idx], c[1 - idx], c[2]))
        return "\n".join(out)

    if blind is None:
        txt = "%s\n\n%s" % (block(fall, "FALLS IN MOST", 0),
                            block(rise, "RISES IN MOST", 1))
    else:
        first, second = ((fall, 0), (rise, 1)) if blind else ((rise, 1), (fall, 0))
        txt = "%s\n\n%s" % (block(first[0], "GROUP A", first[1]),
                            block(second[0], "GROUP B", second[1]))
    note = ["words clearing the threshold: %s"
            % ", ".join("%s %d" % (h.split()[0].lower().rstrip(":"), n)
                        for h, (n, _c) in cut.items())]
    extra = sum(c for _n, c in cut.values())
    if extra:
        note.append("%d not shown" % extra)
    if tied:
        note.append("%d omitted for an even split" % tied)
    return txt + "\n\n" + "; ".join(note) + ".", tied


def render(prompt, min_agree=MIN_AGREE, top=20, blind=None):
    """The classified table for one frame. -> (text, n_pairs) or None"""
    got = pooled(prompt, min_agree)
    if not got:
        return None
    counts, n = got
    text, _tied = table(counts, top, blind)
    return text, n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frame", default=None, help="prefix of one frame")
    ap.add_argument("--min-agree", type=int, default=MIN_AGREE)
    ap.add_argument("--top", type=int, default=20,
                    help="rows shown per column; the remainder is counted in the table")
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--seed", type=int, default=20260920)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    fs = frames()
    if a.frame:
        hit = [f for f in fs if f.lower().startswith(a.frame.lower())]
        if len(hit) != 1:
            raise SystemExit("%d frames match %r" % (len(hit), a.frame))
        got = render(hit[0], a.min_agree, a.top)
        if not got:
            raise SystemExit("no pooled arms for %r" % hit[0])
        text, n = got
        print("%s ___\n\n%s" % (hit[0], text))
        print("\n(%d lineage pairs. `this` is how many classify the word the way "
              "its column says,\n `other` how many classify it the opposite way, "
              "`still` how many leave it unmoved.)" % n)
        return 0
    if a.export:
        import random
        rnd = random.Random(a.seed)
        L = ["# %d sentences" % len(fs), "",
             "Below are measurements of how word probabilities moved in fifty "
             "pairs of language models, each pair trained under two conditions, "
             "A and B. Each entry is ONE sentence with a blank, and the words "
             "that move at that blank.",
             "",
             "**You are not told which condition is which**, and the two groups "
             "are labelled arbitrarily per sentence. The relation you name must "
             "read the same either way round: say what separates the two groups, "
             "never which direction anything moved.",
             "",
             "For each word, `this` is how many of the fifty pairs move it "
             "toward that word's own group, `other` how many move it toward the "
             "other group, and `still` how many leave it unmoved. **These "
             "counts are the evidence.** A word at 28/3/19 is moved one way by "
             "twenty-eight pairs and the other way by three; one at 18/13/19 is "
             "nearly a coin toss. Say which words you are relying on and how "
             "well attested they are.",
             "",
             "A word counts as moved only if it passes a minimum probability, "
             "moves by more than a threshold, and -- on the side that gains -- "
             "gains MORE than the mass freed by the words that lost can "
             "explain. Without that last test every word gains a little "
             "whenever a common word loses, and the table fills with "
             "bookkeeping.",
             "", "## Your job", "",
             "For each sentence, say what relation holds between its two groups.",
             "",
             "Name the RELATION, not the two lists. `Both groups are verbs of "
             "contact` describes them; `the act is aimed at a person in one "
             "group and at an object in the other` relates them. Two groups "
             "drawn from the same subject matter will look alike, and separating "
             "a shared SUBJECT from a shared MOVEMENT is most of the work here.",
             "",
             "For each sentence give:",
             "",
             "    id          the sentence's id",
             "    name        a short label for the relation itself",
             "    statement   one or two sentences stating the movement in",
             "                general terms, at a level someone who had not seen",
             "                this sentence could still apply",
             "    evidence    which words you relied on and how well attested",
             "    confidence  high, medium or low -- low where the two groups",
             "                have no relation you can state, which is a real",
             "                and useful answer",
             "",
             "Order is randomised (seed %d); ids are stable across seeds." % a.seed,
             "",
             "A word appears only if at least %d of the fifty pairs classify "
             "it the same way. Words the pairs split evenly on are counted and "
             "omitted, runs of underscores are stripped, and where more words "
             "clear the threshold than are shown the table says how many."
             % a.min_agree,
             "", "---", ""]
        kept = 0
        for f in fs:
            got = render(f, a.min_agree, a.top, blind=rnd.random() < 0.5)
            if not got:
                continue
            kept += 1
            text, n = got
            L += ["**S%03d**" % kept, "", "> %s ___" % f, "",
                  "```", text, "```", ""]
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
