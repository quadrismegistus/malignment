"""Export the 2,466 blind relations for grouping, with the axis and the direction separated.

    python -u relation_group_input.py            -> results/relations_for_grouping.jsonl
    python -u relation_group_input.py --shards 16  also writes shard files

## WHY THE AXIS AND THE DIRECTION COME FROM DIFFERENT PLACES

RH asked how a grouping deals with Group A and Group B meaning different things
from frame to frame. The corpus answers it:

    a_is_faller             True 1,269   False 1,197
    names naming A or B                          0 of 2,466
    explanations naming A or B                   8 of 2,466
    explanations "one group ... the other"   2,426 of 2,466

**THE READING IS DIRECTION-FREE BY CONSTRUCTION AND THE WORDS ARE NOT.** The
coder was blinded and wrote "one group names a specific medium, while the other
names a generic one" 98% of the time. So `name` and `explanation` describe a
CONTRAST with no direction in it, and `a_is_faller` recovers the direction with
certainty from the pair counts. Two different kinds of evidence, and the mistake
would be to mix them.

**AND THE NAME'S POLE ORDER IS NOISE.** 2,216 of the names are shaped "X vs Y",
and which of `words_a`/`words_b` comes first is not stable -- of the first three
rows, two put `words_a` first and one puts `words_b` first. So "action vs
speech" and "speech vs action" are the same axis written twice, and a grouping
that reads direction off the name order is reading the coder's sentence habits.

So: **group on the axis, count the direction.** The axis is a judgement made from
direction-free text; the direction is an arithmetic fact about which words lost
probability. A group then reports "187 of 210 ran concrete -> abstract", which
is a claim that can be wrong, instead of inheriting a direction from word order,
which cannot.

## WHAT EACH STAGE IS ALLOWED TO SEE

    propose   name + explanation ONLY -- no words, so the axis vocabulary
              cannot be contaminated by which side fell
    assign    name + explanation + ORIENTED words, and two answers: which axis,
              and which of its two poles the BASE words sit on

`base_pole` is the whole point. It is asked per frame, over a vocabulary fixed
before any direction was visible, so the direction count is not the thing that
built the categories.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CJK = re.compile(r"[一-鿿]")
SRC = os.path.join(HERE, "results", "relations_charge_corpus.jsonl")
#: how many words of each side to show. The lists are agreement-ranked, so the
#: head is what the roster is surest about; the tail of a 17-word list is one
#: pair's opinion and would cost the agent context for noise.
TOP = 8


def items(path=SRC):
    out = []
    for i, line in enumerate(open(path, encoding="utf-8")):
        r = json.loads(line)
        #: **THE ONLY PLACE DIRECTION ENTERS.** `a_is_faller` is not a judgement:
        #: the faller is the side that lost probability base -> aligned, verified
        #: 867/867 on the movement rows. Everything downstream inherits it.
        base = r["words_a"] if r["a_is_faller"] else r["words_b"]
        algn = r["words_b"] if r["a_is_faller"] else r["words_a"]
        out.append({
            "id": i,
            "lang": "zh" if CJK.search(r["frame"]) else "en",
            "frame": r["frame"],
            "name": r["name"],
            "explanation": r["explanation"],
            "base": base[:TOP],
            "aligned": algn[:TOP],
            "confidence": r["confidence"],
            "n_pairs": r["n_pairs"],
        })
    return out


def propose_md(rows):
    """What a PROPOSE agent sees: no words, no direction, no frame."""
    L = []
    for r in rows:
        L.append("[%d] %s\n     %s" % (r["id"], r["name"], r["explanation"]))
    return "\n".join(L)


def assign_md(rows):
    """What an AXIS agent sees: name + explanation, no words.

    **THE AXIS AND THE POLE ARE NOW TWO AGENTS, NOT ONE** (RH). In run 1 the
    assign stage saw the text AND the oriented words, and used the words: on
    `force_of_handling` rows task 1's own names are "Continuation type:
    transitive action vs. non-transitive response" and the like, and none
    mentions force. So stage three was partly RE-CODING from the words rather
    than grouping the named relations -- which is not what "group the named
    relations" means, and it let one agent's reading of the words decide both
    which axis a relation is on and which way it runs.

    Split: this file places the relation on an axis from the NAMED CONTRAST
    alone, and `pole_md`'s reader decides the direction from the WORDS alone,
    never seeing the name. Neither can do the other's job.
    """
    L = []
    for r in rows:
        L.append("[%d] %s\n     %s" % (r["id"], r["name"], r["explanation"]))
    return "\n".join(L)


def flip(rid, seed=1):
    """Is the BASE list shown second? SHA-256 of the id, so it is reproducible.

    **THE POLE READER IS BLINDED TOO.** Telling it "base:" and "aligned:" hands
    it a route to the answer that does not pass through the words: a model knows
    what alignment training does, so "which pole is the aligned list on" can be
    answered from prior belief and the words never consulted. It sees LIST 1 and
    LIST 2 in an order drawn per relation, exactly as `pooled_relations`'
    `blind_for` blinded the coder who wrote the names in the first place.

    The direction is restored afterwards from this same function. The reader
    supplies which pole LIST 1 sits on; the mapping is arithmetic.
    """
    import hashlib
    h = hashlib.sha256(("%d|%d" % (seed, rid)).encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 2 == 1


def pole_md(rows, seed=1):
    """What a POLE agent sees: two unlabelled word lists and nothing else.

    No name, no explanation, no frame, and no clue which list fell.
    """
    L = []
    for r in rows:
        one, two = (r["aligned"], r["base"]) if flip(r["id"], seed) \
            else (r["base"], r["aligned"])
        L.append("[%d]\n     LIST 1: %s\n     LIST 2: %s"
                 % (r["id"], ", ".join(one), ", ".join(two)))
    return "\n".join(L)


def shard(rows, n, seed=0):
    """Deterministic round-robin over a seeded shuffle.

    Round-robin rather than contiguous blocks: the corpus is in frame order, so
    a contiguous shard is a topic, and an agent shown 154 frames about one
    subject proposes 154 axes about that subject. A second run with a different
    seed is the replicate -- if the vocabulary is a property of the data it
    survives reshuffling, and the memory on this folder says the group COUNT is
    a property of the reader, so that check is the point rather than a courtesy.
    """
    import random
    rs = random.Random(seed)
    idx = list(range(len(rows)))
    rs.shuffle(idx)
    return [[rows[i] for i in idx[k::n]] for k in range(n)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--shards", type=int, default=0)
    #: **SEED 1 IS THE RUN OF RECORD.** Seed 0 is the leaked run; see
    #: `AXIS_RUN.md`. The default is the decision.
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--lang", choices=("en", "zh", "both"), default="both")
    a = ap.parse_args(argv)
    rows = items()
    if a.lang != "both":
        rows = [r for r in rows if r["lang"] == a.lang]
    out = os.path.join(HERE, "results", "relations_for_grouping.jsonl")
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("%d relations -> %s" % (len(rows), out))
    print("  en %d, zh %d"
          % (sum(1 for r in rows if r["lang"] == "en"),
             sum(1 for r in rows if r["lang"] == "zh")))
    if a.shards:
        d = os.path.join(HERE, "results", "grouping_shards_seed%d" % a.seed)
        os.makedirs(d, exist_ok=True)
        for k, sh in enumerate(shard(rows, a.shards, a.seed)):
            open(os.path.join(d, "propose_%02d.md" % k), "w",
                 encoding="utf-8").write(propose_md(sh) + "\n")
            open(os.path.join(d, "assign_%02d.md" % k), "w",
                 encoding="utf-8").write(assign_md(sh) + "\n")
            open(os.path.join(d, "pole_%02d.md" % k), "w",
                 encoding="utf-8").write(pole_md(sh, a.seed) + "\n")
        print("  %d shards of ~%d -> %s" % (a.shards, len(rows) // a.shards, d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
