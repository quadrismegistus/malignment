"""twp jsonl on disk -> ClickHouse. The rule is the stamp, not a list.

    python -m malignment.ingest --scan            what would be ingested
    python -m malignment.ingest --create          make the database and tables
    python -m malignment.ingest --run [--limit N] ingest

## WHAT IS INCLUDABLE, AND WHY IT IS NOT A HAND-MAINTAINED LIST

RH, 2026-08-15: *"why don't we declare any twp file with explicit rule version 3
as includable in sources. Take union of most recent data for a cell."*

    INCLUDE   a record carrying rule_version == 3, `rows`, and `residual`
    EXCLUDE   anything else -- including rule_version NULL (see below)
    EXCLUDE   paths marked QUARANTINE / RETIRED- / _SUPERSEDED

**The old repo declared sources in a hand-written registry, and the registry went
stale in the direction that hides work.** Measured 2026-08-15: 32 entries
declared, 51 directories on disk carrying real twp. `twp_grid_v3` (95 models) and
`f11_twp_bf` (41) had never been listed -- not retired, not refused, simply
absent, which is the state that registry existed to prevent. A list an operator
maintains diverges the first time two operators remember differently; a stamp
the producer wrote cannot.

So inclusion is DERIVED from the payload. A new fleet directory is includable the
moment it lands, without anyone remembering to add it.

## rule_version NULL IS NOT INGESTED, AND IT COSTS SOMETHING KNOWN

`data/twp_cloud` (103 files) predates the rule stamp. It is also the SOLE source
of **104 catalogue prompts that exist nowhere else** -- roughly 9,900 cells --
including whole markedness families:

    'He held her underwater until she stopped'   249 models in the old store
    'He held her underwater until she started'     0 models, 95 in twp_cloud

**So the marked/unmarked contrast cannot presently be computed at all**, and the
missing arm has been on disk since 30 July. Ingesting it anyway would make the
pair computable as a CROSS-RULE comparison -- one arm stamped 3, one arm
unstamped -- which is the shape that voided a registration on 2026-08-15: two
checkpoints carrying identical stamps and incompatible normalisations, found
only because a pre-registration put a reference `n` beside its result.

RH: *"not sure I trust the ruleVersionNone data."* Agreed, and the cost is
recorded here rather than discovered later: **the fix is to re-measure those 104
prompts under rule 3**, ~9,900 cells and one small fleet job, not to widen the
gate. A gap you can name and price is better than a corpus you cannot trust.

## UNION, NOT PRECEDENCE -- MEASURED, NOT ASSUMED

The directories are COMPLEMENTARY, not redundant. For `Olmo-3-1025-7B`: nine
files, union 4,531 prompts, **intersection 0**. Each fleet extended coverage
rather than repeating it, so "most recent wins" has almost nothing to decide.

Where a genuine (model, prompt) collision does occur, the newest file wins and
the collision is COUNTED, so we learn whether the rule ever fires instead of
trusting that it does the right thing.

**THE GRAIN IS THE CELL, NOT THE WORD.** A twp cell is one prefix-tree walk whose
rows plus residual sum to 1. Resolving word-by-word across two runs would build a
distribution no forward pass produced and the residual would stop reconciling.
One file supplies a cell entirely, or not at all.

## THE GATE IS THE PAYLOAD'S OWN ARITHMETIC

Every record carries `conservation`. A cell that does not conserve is REFUSED and
counted by class -- never dropped silently. Ported from the old `twp_ingest`,
whose docstring is right: *"it validates before it writes, which is the whole
point of a separate step."*
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

from . import ch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#: The corpus lives in the archive repo; this reads it in place and copies
#: nothing. 22 GB of jsonl, 1,896 files.
CORPUS = os.environ.get("MALIGNMENT_CORPUS",
                        "/Users/rj416/github/malign-logits/data")
RULE_VERSION = 3
TOL = 1e-4          #: conservation is exact to ~4e-7 in practice; 1e-4 is loose
#: A path component that disqualifies a directory however good its records are.
#: These are markers the producers already wrote; this honours them rather than
#: re-deciding. `_SUPERSEDED_shard_names/` and four QUARANTINE dirs exist today.
BAD_PATH = ("QUARANTINE", "RETIRED-", "_SUPERSEDED")

#: **A WORD SURFACE THAT IS ACTUALLY A TOKEN.** Every other gate in this file
#: tests MASS, and that is exactly why this one had to be added: token
#: probabilities sum to 1.0 the same way word probabilities do, so a payload
#: assembled in token space passes conservation, passes the NaN check, passes the
#: rule_version stamp, and lands looking perfect.
#:
#: `dolphin-2.6-mistral-7b-dpo` did: 82.2% of its 301,074 rows carry the
#: SentencePiece boundary marker (`'▁the'` where every other model has `'the'`),
#: 0 conservation failures across 2,579 cells. It was found by a SIMILARITY
#: screen, not by ingest -- it agreed with its own declared parent on 2 of 473
#: prompts where unrelated families agree on 48%, because `'▁the'` joins against
#: nothing. Had its edge built it would have reported JS 0.82 where real
#: alignment runs 0.04-0.16: the largest displacement in the corpus, entirely an
#: artefact, on the roster's anti-aligned discriminator.
#:
#: The byte-fallback pattern is the one that proves the diagnosis rather than the
#: marker: a TRUE WORD PROBABILITY IS NEVER HALF A UTF-8 SEQUENCE. `<0xE5>` in a
#: word column means the prefix trie that composes tokens into words never ran.
#: So this gate refuses on ANY occurrence -- there is no rate at which a word
#: dictionary legitimately yields `▁the` or `<0x0A>`, and a threshold here would
#: only decide how much of a broken model to admit.
TOKEN_MARKERS = ("▁", "Ġ", "Ċ")   # SentencePiece ▁, GPT-2 BPE Ġ Ċ
_BYTE_FALLBACK = re.compile(r"^<0x[0-9A-Fa-f]{2}>$")


def token_space(word):
    """True if this surface is a TOKEN, not a word. See TOKEN_MARKERS."""
    return bool(word) and (word.startswith(TOKEN_MARKERS)
                           or _BYTE_FALLBACK.match(word) is not None)

#: **SUMMED AT INGEST, WITH THE PATH COUNT KEPT.** A twp payload is one row per
#: (word, FIRST TOKEN): a surface reachable by several token paths gets several
#: rows, and those rows are a PARTITION -- summed, plus the residual, they come
#: to 1.0. Measured on 10,908 source cells: **20.4% contain a duplicated
#: surface**, 10,333 extra rows, `'I'` three times in one pythia cell.
#:
#: Two ways to be wrong here and only one way to be right. Keyed on
#: (model, prompt, word) and NOT summed, the ReplacingMergeTree collapses the
#: paths on merge and drops mass. Keyed on (..., t1) and stored raw, the mass is
#: safe but **every consumer must remember to sum**, and the evidence is that
#: they do not: `movement.word_probs` exists partly to refuse the dict
#: comprehension that lost 2.7% of a Chinese distribution, and
#: `SELECT p ... WHERE word=` is the most natural query anyone would type.
#:
#: So the SUM happens once, here, and `n_paths` keeps the fact that a surface had
#: several. Nothing downstream consumes the breakdown -- the campaign's own
#: `movement` table is keyed (base, aligned, prompt, word) with no t1 -- so what
#: is dropped is a distinction no consumer makes, and what is kept is the count
#: that says the distinction existed.
DDL = ["""
CREATE TABLE IF NOT EXISTS {db}.twp_words (
    model String, prompt String, word String,
    p Float32, n_paths UInt8,
    source LowCardinality(String), mtime DateTime
) ENGINE = ReplacingMergeTree(mtime) ORDER BY (model, prompt, word)
""", """
CREATE TABLE IF NOT EXISTS {db}.twp_cells (
    model String, prompt String,
    n_words UInt32, conservation Float64,
    tail Float32, drop Float32, open Float32, mojibake Float32, total Float32,
    theta Float32, rule_version UInt16, dict_sha LowCardinality(String),
    revision LowCardinality(String), bos_policy LowCardinality(String),
    device LowCardinality(String), compute_dtype LowCardinality(String),
    torch_version LowCardinality(String), transformers_version LowCardinality(String),
    source LowCardinality(String), mtime DateTime
) ENGINE = ReplacingMergeTree(mtime) ORDER BY (model, prompt)
"""]


def scan():
    """Every includable file, with its source label and mtime.

    The label is the directory relative to the corpus root. **It is part of the
    data's identity** -- it lands in the `source` column, so renaming a directory
    re-partitions the store.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(CORPUS, "**", "*.jsonl"), recursive=True)):
        rel = os.path.relpath(p, CORPUS)
        if any(b in rel for b in BAD_PATH):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                first = fh.readline()
            if not first:
                continue
            r = json.loads(first)
        except Exception:
            continue
        if r.get("rule_version") != RULE_VERSION:
            continue
        if "rows" not in r or "residual" not in r:
            continue
        out.append({"path": p, "source": os.path.dirname(rel) or ".",
                    "mtime": os.path.getmtime(p)})
    return out


def _cells(path):
    """(model, prompt) -> record, last write winning WITHIN a file.

    A shard re-run after a kill re-emits prompts; the old ingester dedups the
    same way and counts it rather than hiding it.
    """
    seen, dups = {}, 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            k = (d.get("model"), d.get("prompt"))
            if k[0] is None or k[1] is None:
                continue
            if k in seen:
                dups += 1
            seen[k] = d
    return seen, dups


def plan(files):
    """(model, prompt) -> the winning file. Newest mtime wins; collisions counted.

    Returns (winner, stats). A collision is two DIFFERENT files offering the same
    cell -- the thing precedence exists for, and measured at ~0 because the
    fleets ran complementary prompt sets.
    """
    winner, collide = {}, 0
    for f in sorted(files, key=lambda x: x["mtime"]):
        seen, _ = _cells(f["path"])
        for k in seen:
            if k in winner:
                collide += 1
            winner[k] = f          # later mtime overwrites
    return winner, {"collisions": collide}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    files = scan()
    by_src = defaultdict(int)
    for f in files:
        by_src[f["source"]] += 1
    print("  corpus: %s" % CORPUS)
    print("  includable (rule_version == %d): %d files across %d directories\n"
          % (RULE_VERSION, len(files), len(by_src)))
    for s, n in sorted(by_src.items(), key=lambda x: -x[1])[:14]:
        print("     %-46s %4d" % (s[:46], n))
    if a.scan:
        return 0

    if a.create:
        for d in DDL:
            ch.execute(d)
        print("\n  created %s.twp_words, %s.twp_cells" % (ch.DB, ch.DB))
    if not a.run:
        return 0

    if a.limit:
        files = files[:a.limit]
    words, cells = [], []
    rej = defaultdict(int)
    #: WHICH MODEL AND WHICH SURFACE, not just a count. A rejection counter tells
    #: you something was refused; only the example tells you whether to re-measure
    #: a checkpoint or fix a producer.
    rej_examples = {}
    n_dup = 0
    win, stats = plan(files)
    print("\n  planned %s cells | collisions needing precedence: %s"
          % (format(len(win), ","), format(stats["collisions"], ",")))
    for f in files:
        seen, dups = _cells(f["path"])
        n_dup += dups
        import datetime
        mt = datetime.datetime.fromtimestamp(f["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
        for k, d in seen.items():
            if win.get(k) is not f:
                rej["superseded_by_newer"] += 1
                continue
            rows = d.get("rows") or []
            res = d.get("residual") or {}
            cons = d.get("conservation")
            #: THE PAYLOAD'S OWN ARITHMETIC IS THE GATE. Refused, not dropped.
            #: **NaN DEFEATS A COMPARISON GATE AND MUST BE TESTED FOR.**
            #: `abs(NaN - 1.0) > TOL` is False, so a NaN conservation value
            #: PASSES the check written to reject non-conserving cells. Two
            #: cells got in that way (Qwen3-8B-Base and Qwen3-8B on the
            #: `<<<LOGICAL:BOS>>>` prompt, NaN residual and NaN word probs) and
            #: killed the movement producer with `NoneType - float` -- Float32
            #: NaN serialises to JSON null, so it arrives as None downstream.
            #: A gate built from inequalities is silent on the one value that
            #: satisfies no inequality.
            if cons is None or cons != cons or abs(cons - 1.0) > TOL:
                rej["conservation"] += 1
                continue
            if any((w.get("p") is None or w["p"] != w["p"]) for w in rows):
                rej["nan_probability"] += 1
                continue
            #: SURFACE SHAPE, WHICH NO MASS GATE CAN SEE. See TOKEN_MARKERS.
            bad = [w["word"] for w in rows if token_space(w.get("word") or "")]
            if bad:
                rej["token_space"] += 1
                rej_examples.setdefault(k[0], set()).update(bad[:3])
                continue
            m, pr = k
            #: SUM THE PARTITION HERE, ONCE. Folding in SQL later would put the
            #: rule in two places, which is the failure `movement` warns about.
            fold = {}
            for w in rows:
                a = fold.setdefault(w["word"], [0.0, 0])
                a[0] += float(w["p"]); a[1] += 1
            for wd, (pp, np_) in fold.items():
                words.append({"model": m, "prompt": pr, "word": wd,
                              "p": pp, "n_paths": np_,
                              "source": f["source"], "mtime": mt})
            cells.append({"model": m, "prompt": pr, "n_words": len(rows),
                          "conservation": float(cons),
                          "tail": float(res.get("tail") or 0),
                          "drop": float(res.get("drop") or 0),
                          "open": float(res.get("open") or 0),
                          "mojibake": float(res.get("mojibake") or 0),
                          "total": float(res.get("total") or 0),
                          "theta": float(d.get("theta") or 0),
                          "rule_version": int(d.get("rule_version") or 0),
                          "dict_sha": d.get("dict_sha") or "",
                          "revision": d.get("revision") or "",
                          "bos_policy": d.get("bos_policy") or "",
                          "device": d.get("device") or "",
                          "compute_dtype": d.get("compute_dtype") or "",
                          "torch_version": d.get("torch_version") or "",
                          "transformers_version": d.get("transformers_version") or "",
                          "source": f["source"], "mtime": mt})
        if len(words) > 400_000:
            ch.insert("twp_words", words); words = []
            ch.insert("twp_cells", cells); cells = []
            print("     ... %s cells written" % format(
                ch.scalar("SELECT count() FROM {db}.twp_cells"), ","))
    if words:
        ch.insert("twp_words", words)
    if cells:
        ch.insert("twp_cells", cells)
    print("\n  duplicates WITHIN files (last write won): %s" % format(n_dup, ","))
    print("  refused / skipped, by class:")
    for k, v in sorted(rej.items(), key=lambda x: -x[1]):
        print("     %-24s %s" % (k, format(v, ",")))
    #: LOUD, AND NAMING THE MODEL. A token-space refusal is not a bad file to be
    #: skipped past -- it is a checkpoint that must be RE-MEASURED, and it will
    #: otherwise sit missing from the corpus looking like it was never run.
    if rej_examples:
        print("\n  TOKEN-SPACE REFUSALS -- these checkpoints need RE-MEASURING,"
              "\n  not a marker strip (see TOKEN_MARKERS in this file):")
        for m, ex in sorted(rej_examples.items()):
            print("     %-52s e.g. %s" % (m[:52], ", ".join(sorted(ex)[:3])))
    print("\n  %s.twp_cells: %s | twp_words: %s"
          % (ch.DB, format(ch.scalar("SELECT count() FROM {db}.twp_cells"), ","),
             format(ch.scalar("SELECT count() FROM {db}.twp_words"), ",")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
