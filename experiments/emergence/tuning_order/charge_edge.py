"""`task_charge` over the ONE edge this question is about: base -> Think-SFT.

    python -u charge_edge.py --plan
    python -u charge_edge.py --workers 32

## WHY A NEW ANNOTATION AND NOT `charge.py`

`charge.py` serves 109,593 cells over 50 endpoint pairs, and the Olmo lineage IS
among them -- but its rated endpoint is **`allenai/Olmo-3-7B-Instruct`**, not
`Olmo-3-7B-Think-SFT`. Different edge, different movers. Measured against the
sites this question actually uses (faller/risers at base -> Think-SFT@step43000),
the existing annotation covers:

    fallers 73.4%     risers 60.8%

**and the shortfall is asymmetric toward risers, which are the arrival side of
the lag under test.** An instrument that sees late substitutes less well than it
sees fallers would shorten the measured lag. So the edge gets its own annotation,
and the rated set becomes the site set by construction.

## ENDPOINT ARMS ONLY, AND THE COST OF THAT IS MEASURED

`task_charge` rates every word above THETA in EITHER arm. Here that is base and
the ladder END, so a word that peaks mid-ladder and has decayed by step 43000 is
never rated. Counted over the target prompts:

    words >= 1% at ANY rung but not endpoint candidates   4,043 of 13,559 (29.8%)
    their share of all >=1% ladder mass                    286.1 / 12,372.6 (2.31%)
    peak mass of those:  median 1.26%  p90 1.95%  max 7.0%
                         >=2%: 366    >=5%: 3    >=10%: 0

**30% of word TYPES carrying 2.31% of MASS**, and not one reaches a 10% peak. So
the transient tail is words hovering just over the rating threshold, not hidden
substitutes. Stated as a bound rather than guarded against.

(That also reframes the 60.8% riser coverage above: it is a TYPE count. By mass
the endpoint set is nearly complete, and reading the type number as a mass number
is the grain error `project_lexicon_construction` already records.)

## FLASH, NOT PRO, AND IT IS A CHOICE WITH A COST

`run_charge.py` argues for `deepseek-v4-pro` and the argument is real: `scene -
frame` is the increment, so a wrong frame baseline corrupts every word in the
cell, and pro reads frames better (`He stole her` -> flash 1/NONE, pro
5/ILLICIT).

**But the corpus of record is flash.** `charge.py` reads `charge_en50_flash.jsonl`
and `charge_zh50_flash.jsonl`; the only pro file on disk is a 5-lineage zh pilot.
Rating this one edge with pro would put it on a different scale from the 50 it
must sit beside -- and Q2 of this question uses flash-derived prompt-level lift,
so the two axes would carry different instruments. A known uniform weakness beats
a local incomparability. Same `task()` default, same seven English shots, same
schema.

**Comparability is asserted at the level of the code path, not proven.** Whether
`task_charge.py` is byte-identical to its state when the 50-pair corpus ran is
not knowable from here, so every row stores BOTH the declared corpus sha and a
live sha256 of the task source -- see `instrument()`.

## v3, BECAUSE THE RUNGS ARE v3

`rank.cells_bulk` reads `twp_words_v4`. The ladder exists only in `twp_words`
(v3) -- `twp_cells_v4` holds zero rungs of it -- so candidate lists drawn from v4
would describe a different word set from the curves they annotate. The query
below is `cells_bulk`'s, on v3, with the same content-word filter and the same
`MIN_CONTENT` floor so the cells are otherwise identical in construction.

## THE RESUME KEY CARRIES THE ALIGNED MODEL, AND THE UPSTREAM ONE DOES NOT

`run_charge.py` resumes on `(prompt, base)`. For a second edge on the SAME base
that key is wrong: the existing corpus already holds `(p, Olmo-3-1025-7B)` rated
against Instruct, so a shared key cannot tell the two edges apart. This file
writes `(prompt, base, aligned, rule_version)` and to its own output.

**DO NOT add this file to `charge.SOURCES` without handling that.** That index is
keyed by prompt and assumes one rating per (prompt, base); two edges on one base
would collide silently.
"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DR = os.path.join(ROOT, "experiments", "instrument_calibrations", "dose_response")
sys.path.insert(0, ROOT)
sys.path.insert(0, DR)

from malignment import ch, pos                                     # noqa: E402
from malignment.ch import _lit                                     # noqa: E402
import score_slots as S                                            # noqa: E402
import task_charge as C                                            # noqa: E402
from malignment import charge as CH                                # noqa: E402


def instrument():
    """-> (declared corpus sha, live digest of task_charge.py).

    **`charge.INSTRUMENT_SHA` is a HARDCODED LABEL, not a computed digest** -- it
    names task_charge as it stood when the 50-pair corpus ran. Copying it forward
    would ASSERT that this run used the same instrument rather than establish it.
    So both are stored: the declared sha for comparability with the corpus, and a
    sha256 of the task source as it actually is, so a later reader can tell
    whether the file drifted between the two runs.
    """
    import hashlib
    src = open(os.path.join(DR, "task_charge.py"), "rb").read()
    return CH.INSTRUMENT_SHA, hashlib.sha256(src).hexdigest()[:16]

BASE = "allenai/Olmo-3-1025-7B"
ALIGNED = "allenai/Olmo-3-7B-Think-SFT"
LADDER = "allenai/Olmo-3-7B-Think-SFT@step1000"   #: any rung; all carry the same 2,272
RULE_VERSION = 3
OUT = os.path.join(HERE, "results", "charge_olmo_thinksft_v3.jsonl")
KEY = ("prompt", "base", "aligned", "rule_version")


def targets():
    """The 512 non-verse prompts the ladder actually covers.

    2,272 prompts sit on every rung, but 1,802 are VERSE PREFIXES from the M05
    rhyme fleet -- growing prefixes of one poem, the wrong instrument here. The
    prompts registry is the discriminator: a verse prefix is not in it.
    """
    rows = ch.query(
        "SELECT prompt FROM twp_words WHERE model=%s "
        "INTERSECT SELECT DISTINCT prompt FROM prompts WHERE prompt != ''"
        % _lit(LADDER))
    return sorted(r["prompt"] for r in rows)


def cells_v3(prompt_list, base, aligned):
    """`rank.cells_bulk`, on twp_words (v3). Same filter, same floor.

    The inner sub-select filters on (prompt, word) PAIRS and not on `p`, which is
    `cells_bulk`'s reason and it carries over unchanged: filtering rows by
    `p >= THETA` directly would drop the OTHER arm's value for a word at 4% in
    one arm and 0.2% in the other, recording it as 0.0 -- and that word is
    exactly the displacement case.
    """
    keep = set(prompt_list)
    inner = ("SELECT prompt, model, word, argMax(p, mtime) p FROM twp_words "
             "WHERE model IN (%s,%s) GROUP BY prompt, model, word"
             % (_lit(base), _lit(aligned)))
    rows = ch.query(
        "SELECT prompt, model, word, p FROM (%s) WHERE (prompt, word) IN "
        "(SELECT prompt, word FROM (%s) WHERE p >= %s)" % (inner, inner, S.THETA))
    by = collections.defaultdict(lambda: collections.defaultdict(dict))
    for r in rows:
        if r["prompt"] in keep:
            by[r["prompt"]][r["model"]][r["word"]] = float(r["p"])
    out = {}
    for p, d in by.items():
        if base not in d or aligned not in d:
            continue
        ws = sorted({w for m in (base, aligned) for w, v in d[m].items()
                     if v >= S.THETA},
                    key=lambda w: -max(d[base].get(w, 0), d[aligned].get(w, 0)))
        if not ws:
            continue
        tag = pos.get_pos(ws, p)
        ws = [w for w in ws if S.is_content(w, tag.get(w))]
        if len(ws) < S.MIN_CONTENT:
            continue
        out[p] = (ws, {w: (d[base].get(w, 0.0), d[aligned].get(w, 0.0))
                       for w in ws})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--model", default="deepseek/deepseek-v4-flash")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)

    #: this task's own seven shot frames, held out. run_charge.py holds out only
    #: task_charge's, not task_multi's, and the same reasoning applies here.
    ex = {e.strip() for e in C.EXAMPLES_HELD_OUT} if hasattr(C, "EXAMPLES_HELD_OUT") else set()
    ps = [p for p in targets() if p.strip() not in ex]
    if a.limit:
        ps = ps[:a.limit]

    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try:
                r = json.loads(line)
                done.add(tuple(r[k] for k in KEY))
            except Exception:
                pass
    todo = [p for p in ps
            if (p, BASE, ALIGNED, RULE_VERSION) not in done]
    print("%s -> %s  (rule_version %d, %s)"
          % (BASE.split("/")[-1], ALIGNED.split("/")[-1], RULE_VERSION, a.model))
    print("target prompts %d | already rated %d | to do %d"
          % (len(ps), len(done), len(todo)), flush=True)
    if a.plan or not todo:
        return 0

    got = cells_v3(todo, BASE, ALIGNED)
    built = [(p, got[p]) for p in todo if p in got]
    print("%d candidate lists built, %d skipped (no cell, or under MIN_CONTENT)"
          % (len(built), len(todo) - len(built)), flush=True)
    if not built:
        return 0
    print("candidates per cell: min %d median %d max %d"
          % (min(len(c[0]) for _, c in built),
             sorted(len(c[0]) for _, c in built)[len(built) // 2],
             max(len(c[0]) for _, c in built)), flush=True)

    decl, live = instrument()
    print("instrument: declared %s | task_charge.py sha256[:16] %s"
          % (decl, live), flush=True)
    t = C.task(model=a.model)
    res = t.map([C.render(p, c[0]) for p, c in built],
                num_workers=a.workers, verbose=True)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    n = 0
    with open(a.out, "a", encoding="utf-8") as fh:
        for (p, (ws, m)), r in zip(built, res):
            if r is None:
                continue
            fh.write(json.dumps({
                "prompt": p, "base": BASE, "aligned": ALIGNED,
                "rule_version": RULE_VERSION, "model": a.model,
                "instrument_sha_declared": decl,
                "task_source_sha256_16": live,
                "frame": getattr(r, "frame", None),
                "frame_kind": getattr(r, "frame_kind", None),
                "words": [{"word": w.word, "scene": w.scene, "kind": w.kind}
                          for w in r.words if w.word in m],
                "masses": {w: list(v) for w, v in m.items()},
            }, ensure_ascii=False) + "\n")
            n += 1
    print("\nwrote %d rows -> %s" % (n, a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
