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
#: TWO ROOTS, AND THE PREFIXES ARE LOAD-BEARING. Both are read IN PLACE; nothing
#: is copied.
#:
#:   CORPUS  the ARCHIVE. Read-only legacy: 144 GB, 24.3 GB of it jsonl, holding
#:           every cell measured before this repo existed.
#:   DATA    where THIS repo's runs write. Outside both checkouts, because
#:           `malignment` is PUBLIC and a twp jsonl carries the prompts verbatim
#:           -- including the transgressive battery -- and because new data in
#:           the archive would re-entrench the dependency this repo exists to
#:           break.
#:
#: **THE ARCHIVE'S SOURCE LABELS MUST NOT CHANGE.** `scan()` sets `source` to the
#: directory relative to its root, and its own docstring says that label "is part
#: of the data's identity -- renaming a directory re-partitions the store". So the
#: archive keeps prefix "" and its labels are byte-identical to what 400,644
#: stored cells already carry; only the NEW root is prefixed, where nothing is
#: partitioned yet. Prefixing both would silently re-partition the whole store
#: while every count still looked right.
CORPUS = os.environ.get("MALIGNMENT_CORPUS",
                        "/Users/rj416/github/malign-logits/data")
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
ROOTS = ((CORPUS, ""), (DATA, "malignment-data/"))
RULE_VERSION = 3
#: **THE TARGET TABLE IS PART OF THE RULE, NOT A FLAG BESIDE IT.** v4 cells carry
#: `rules`, `prompt_cache` and `topup` in their KEY, and `twp_cells_v4` puts all
#: three in its SORTING KEY -- so a v4 record written into the v3 table would
#: collide with its own v3 twin and lose. One switch sets both, and nothing can
#: select a version without also selecting where it lands.
_RV = {"v": RULE_VERSION}
_REPLACE = {"on": False}


def _wait_for_mutations(ch, tries=60):
    """A DELETE in ClickHouse is a MUTATION and returns before it has happened.

    Inserting on top of an unfinished delete is a race whose loser is the NEW
    row, and it fails the way this whole morning has been failing -- with a
    plausible count rather than an error.
    """
    import time
    for _ in range(tries):
        n = ch.scalar("SELECT count() FROM system.mutations "
                      "WHERE database='malignment' AND is_done=0")
        if not n:
            return True
        time.sleep(2)
    raise RuntimeError("mutations still running after %ds -- refusing to insert "
                       "on top of an unfinished delete" % (2 * tries))
TABLES = {3: ("twp_words", "twp_cells"), 4: ("twp_words_v4", "twp_cells_v4")}
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
    """True if this surface is a TOKEN, not a word. See TOKEN_MARKERS.

    **A NON-STRING IS ALSO NOT A WORD.** `expand` keys its output by
    `(surface, first_token_id)`, and a producer that writes the tuple straight
    into `word` yields `{"word": ["in", 304]}` -- which made this raise
    AttributeError and take the whole ingest with it instead of refusing one
    record. A gate that CRASHES on malformed input is not a gate; refusing is
    the behaviour, and the caller counts it under `token_space`.
    """
    if not isinstance(word, str):
        return bool(word)      # malformed shape: refuse, do not crash
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
""", """
CREATE TABLE IF NOT EXISTS {db}.twp_words_v4 (
    model String, prompt String, word String,
    p Float32, n_paths UInt8, topup UInt8,
    rule_version UInt16, rules LowCardinality(String), prompt_cache UInt8,
    frame LowCardinality(String),
    source LowCardinality(String), mtime DateTime
) ENGINE = ReplacingMergeTree(mtime)
PRIMARY KEY (model, prompt, word, rule_version, rules, prompt_cache, topup)
ORDER BY (model, prompt, word, rule_version, rules, prompt_cache, topup, frame)
""", """
CREATE TABLE IF NOT EXISTS {db}.twp_cells_v4 (
    model String, prompt String,
    n_words UInt32, conservation Float64,
    tail Float32, drop Float32, open Float32, mojibake Float32, total Float32,
    theta Float32, rule_version UInt16, rules LowCardinality(String),
    prompt_cache UInt8, topup UInt8, topup_words UInt32, topup_mass Float32,
    topup_refused UInt32 DEFAULT 0,
    dict_sha LowCardinality(String), revision LowCardinality(String),
    bos_policy LowCardinality(String),
    device LowCardinality(String), compute_dtype LowCardinality(String),
    torch_version LowCardinality(String), transformers_version LowCardinality(String),
    frame LowCardinality(String),
    source LowCardinality(String), mtime DateTime
) ENGINE = ReplacingMergeTree(mtime)
PRIMARY KEY (model, prompt, rule_version, rules, prompt_cache, topup)
ORDER BY (model, prompt, rule_version, rules, prompt_cache, topup, frame)
"""]

#: **THE v4 SCHEMA WAS DECLARED NOWHERE AND EXISTED ONLY IN THE LIVE DATABASE.**
#: `--create` built `twp_words` and `twp_cells` and stopped. The v4 pair was
#: created out of band, so the shape of the tables holding 820,246 cells and
#: 108,301,814 words was not in this repo at all -- unrebuildable, and nobody
#: could read what it promised. Recovered from `SHOW CREATE TABLE` 2026-08-22.
#:
#: **`frame` IS IN THE SORTING KEY, WHICH IS THE DEDUP KEY, AND THAT IS THE
#: WHOLE POINT.** These are ReplacingMergeTree: a framed cell and its raw twin
#: agree on every other key column, so with `frame` merely PRESENT as a column
#: the merge keeps one of them by mtime -- not pooled, SILENTLY REPLACED, with
#: the store looking complete. Verified before and after: a `frame='prefill'`
#: twin of a real raw cell survives OPTIMIZE FINAL alongside it.
#:
#: It sits LAST so the PRIMARY KEY stays the historical prefix and existing
#: parts remain valid, and it carries NO DEFAULT because ClickHouse refuses a
#: defaulted column in a sorting key ("Newly added column frame has a default
#: expression, so adding expressions that use it to the sorting key is
#: forbidden"). Adding the column first and modifying the key second is refused
#: too -- by then it is no longer newly added -- so it is ONE alter or nothing.
#:
#: Existing rows take the type's zero value, which is the true statement about
#: them: everything measured before 2026-08-22 IS the raw frame. An INSERT that
#: omits `frame` -- which every current producer does -- lands as `''`, so a
#: frame-unaware ingest stays correct rather than merely not crashing.


def scan():
    """Every includable file, with its source label and mtime.

    The label is the directory relative to ITS ROOT, prefixed by the root's own
    label. **It is part of the data's identity** -- it lands in the `source`
    column, so renaming a directory re-partitions the store. That is why the
    ARCHIVE keeps prefix "" (its labels must stay byte-identical to what the
    stored cells already carry) and only the new root is prefixed.
    """
    out = []
    seen_paths = set()
    for root, prefix in ROOTS:
        if not os.path.isdir(root):
            continue
        for p in sorted(glob.glob(os.path.join(root, "**", "*.jsonl"),
                                  recursive=True)):
            #: A root nested inside another would otherwise yield the same file
            #: twice under two source labels, i.e. one measurement counted as two
            #: populations.
            if p in seen_paths:
                continue
            seen_paths.add(p)
            rel = os.path.relpath(p, root)
            if any(b in rel for b in BAD_PATH):
                continue
            out.extend(_maybe(p, prefix + (os.path.dirname(rel) or ".")))
    return out


def _maybe(p, source):
    """[{path, source, mtime}] if this file is includable, else [].

    Inclusion is decided from the PAYLOAD's own stamp, never from the path. A
    file whose producer predates rule 3 is not a file to be fixed by widening the
    gate.

    **IT SCANS THE FILE; IT USED TO READ ONE LINE.** The stash is APPEND-ONLY and
    a checkpoint measured under v3 and later under v4 has both in one file, v3
    first. Deciding the whole file from record one therefore excluded every such
    file entirely -- a sample of one, generalised to a file, at the exact place
    the campaign's own rule about (model x environment) should have been ringing.

    Measured when RH asked why mpt had failed to load "when we literally did mpt
    yesterday": 7 models and **4,583 measured v4 cells were invisible to
    ClickHouse**, among them Mistral-7B-Instruct-v0.1 (3,471) and both granite
    arms. Nothing raised. The cells existed, the run reported success, the ingest
    reported success, and the corpus simply did not contain them -- so the
    endpoint-pair count I had been reporting was an undercount and I had no way
    to see it.

    Early-exits on the first matching record, so a file that qualifies costs one
    line as before and only a file that does NOT qualify is read through.
    """
    try:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if (r.get("rule_version") == _RV["v"]
                        and "rows" in r and "residual" in r):
                    return [{"path": p, "source": source,
                             "mtime": os.path.getmtime(p)}]
    except Exception:                                           # noqa: BLE001
        return []
    return []


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
            #: **THE DEDUP KEY IS THE INSTRUMENT, NOT JUST THE CELL.** v3's
            #: identity is (model, prompt) and v4's is not: a topup cell and its
            #: pass-1 parent share both, differ in `topup`, and are DIFFERENT
            #: MEASUREMENTS. Keying on the pair silently collapsed 2,583 of
            #: CT-LLM-Base's 5,289 records into 2,706 and called them duplicates
            #: -- the topup work vanished and the count looked plausible.
            #: **PER-RECORD GATE. `_maybe` DECIDES THE FILE, NOT THE RECORD.**
            #: When `_maybe` read one line, a file was includable only if its
            #: FIRST record matched, and mixed files were excluded whole -- which
            #: hid 4,583 measured cells and was rightly fixed to scan. But the
            #: scan made a file includable if ANY record matches, and nothing
            #: here filtered the rest, so every v3 record in a mixed file poured
            #: into the v4 table: 11,916 cells across 6 models, carrying
            #: rule_version=3 and rules=''.
            #:
            #: The fix to one gate removed the guarantee the next stage was
            #: relying on without stating it. File-level includability and
            #: record-level admissibility are different questions and both have
            #: to be asked.
            if d.get("rule_version") != _RV["v"]:
                continue
            k = ((d.get("model"), d.get("prompt")) if _RV["v"] == 3 else
                 (d.get("model"), d.get("prompt"), d.get("rules"),
                  bool(d.get("prompt_cache")), bool(d.get("topup"))))
            if k[0] is None or k[1] is None:
                continue
            if k in seen:
                dups += 1
            seen[k] = d
    #: **VALIDATE THE SURVIVORS, NOT EVERY LINE.** The guard ran per line and
    #: before dedup, so a SUPERSEDED record could refuse the whole corpus --
    #: which is what happened: 546 RWKV topup records with a bad prompt_cache
    #: stamp were deleted from the stash, and the stash being APPEND-ONLY the
    #: lines stayed, so the ingest went on refusing on dead data that would never
    #: have been filed.
    #:
    #: This is a narrowing of the guard and worth being explicit about. What it
    #: still catches is unchanged: a contradictory record that WINS its key --
    #: the only kind that can reach ClickHouse. What it stops doing is blocking
    #: on records it was going to discard anyway. `path` is kept in the message
    #: so the producer is still named.
    for _k, _d in seen.items():
        _key_body_agree(_d, path)
    return seen, dups


#: Fields that identify the INSTRUMENT and must appear identically in the
#: record's `__key__` and in its body. `rule_version` and `dict_sha` were always
#: in both; `rules` and `prompt_cache` arrived with v4 and only reached the key.
INSTRUMENT_FIELDS = ("rule_version", "dict_sha", "rules", "prompt_cache")


def _key_body_agree(d, path):
    """REFUSE a record whose body disagrees with its own `__key__`.

    **THE KEY DECLARES THE INSTRUMENT AND THE INGEST READS THE BODY**, so a cell
    can be correctly keyed and ingest as something else entirely. Found 2026-08-17
    on `m-a-p/CT-LLM-Base`: 2,706 v4 cells whose `__key__` carried
    `rules: "v4[decoded,depth=9]", prompt_cache: true` and whose BODY carried
    `rules: None, prompt_cache: None`, because `run_v4.py` built a stamp with
    those fields and then became a thin wrapper around `Runner`, whose stamp does
    not know them. The measurement was sound and the provenance was half-written.

    `twp_cells_v4` and `twp_words_v4` put `rules` IN THE SORTING KEY, so every one
    of those rows would have landed under an empty string -- indistinguishable
    from a run with no rules at all, and colliding with any future one.

    **A memory would not have caught this and a guard does**, which is the whole
    argument: a rule that runs only where someone remembers it is not running.
    Refuses rather than repairing, because a body silently rewritten from its key
    is a second claim about what happened, and this file's job is to say what
    the producer wrote.
    """
    key = d.get("__key__")
    if not isinstance(key, dict):
        return
    bad = [(f, key.get(f), d.get(f)) for f in INSTRUMENT_FIELDS
           if f in key and d.get(f) != key.get(f)]
    if bad:
        raise ValueError(
            "%s: record's body disagrees with its __key__ on %s. The key is the "
            "instrument the cell was measured with; the body is what this ingest "
            "would file it as. Fix the PRODUCER's stamp -- do not repair the "
            "body here, and do not ingest a cell whose provenance is two "
            "different claims. prompt=%r"
            % (os.path.basename(path),
               ", ".join("%s key=%r body=%r" % b for b in bad),
               str(d.get("prompt"))[:40]))


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
    ap.add_argument("--rule-version", type=int, default=3, choices=[3, 4],
                    help="4 reads v4 records and writes twp_*_v4")
    ap.add_argument("--replace", action="store_true",
                    help="delete each planned model's rows at this rule_version "
                         "before inserting -- makes a re-ingest IDEMPOTENT")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    #: **A BLANKET RUN IS A POPULATION CHANGE.** `scan()` derives inclusion from
    #: the payload stamp, which is right -- and it means a new fleet directory
    #: landing on disk enters the store the next time ANYONE runs the ingest for
    #: an unrelated reason. Measured 2026-08-16: ingesting one 2,653-cell APO run
    #: would also have pulled in 213 verse-fleet files across 7 boxes, plus
    #: falcon_h1_repair and twp_fill -- a different campaign, silently, inside a
    #: command whose output says only "cells ingested".
    #:
    #: The stamp still decides what is ELIGIBLE. This decides what is being asked
    #: for right now, which is a different question and belongs to the operator.
    ap.add_argument("--source", default=None,
                    help="only sources containing this substring (a blanket run "
                         "ingests every eligible directory on disk)")
    a = ap.parse_args()
    #: **`--replace` WITH `--source` IS SOURCE-SCOPED, NOT REFUSED.** The first
    #: fix here was a refusal, and it was the wrong instrument: the per-arm ingest
    #: in `scripts/topup_lineage.py` legitimately runs `--replace --source <arm>`
    #: on RH's own instruction, and refusing it would have silently stopped the
    #: corpus tracking a sweep already 53 arms deep. What was broken was the SCOPE
    #: of the delete, not the combination. See the delete site below.
    _RV["v"] = a.rule_version
    _REPLACE["on"] = bool(a.replace)

    files = scan()
    if getattr(a, "source", None):
        keep = [f for f in files if a.source in f["source"]]
        print("  --source %r: %d of %d files" % (a.source, len(keep), len(files)))
        files = keep
    by_src = defaultdict(int)
    for f in files:
        by_src[f["source"]] += 1
    print("  corpus: %s" % CORPUS)
    #: `RULE_VERSION` is the v3 CONSTANT, so this line said "rule_version == 3"
    #: on a --rule-version 4 run whose gate had correctly admitted only v4
    #: records. Same shape as the loader announcing `rule_version 3` while
    #: stamping 4: the run right, the sentence wrong, and nothing to catch it
    #: because the artifact works. Report what the gate USED.
    print("  includable (rule_version == %d): %d files across %d directories\n"
          % (_RV["v"], len(files), len(by_src)))
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
    #: **PRECEDENCE IS ACROSS FILES; IT HAS NEVER BEEN ACROSS RUNS.** `_plan`
    #: resolves two files offering the same cell, and that is all it does -- the
    #: table is not consulted, so a second ingest of the same source INSERTS
    #: EVERY ROW AGAIN. MergeTree does not deduplicate, so CT-LLM-Base's 2,706
    #: pass-1 cells read as 5,412 after one re-run.
    #:
    #: It went unnoticed because every consumer that matters is immune by
    #: construction: `lineage_union` and `topup_todo` use groupUniqArray,
    #: `pass1_todo` uses DISTINCT. Only counts, sums and averages are wrong --
    #: which is to say only the numbers anyone would QUOTE.
    #:
    #: Opt-in rather than automatic: a delete is not recoverable from the table,
    #: and a source holding one producer's files for a model that another
    #: producer also measured would lose the other producer's rows.
    #: **AND THE HAZARD THE PARAGRAPH ABOVE NAMES IS NOW GUARDED, NOT ONLY
    #: DESCRIBED.** It said, correctly and in advance, that "a source holding one
    #: producer's files for a model that another producer also measured would lose
    #: the other producer's rows" -- and on 2026-08-19 that is exactly what
    #: happened: `--replace --source de05cd070607` took bloom-7b1 from 2,876 cells
    #: to 384 and dropped bloomz's 277 pass-2 cells, printing `planned 3,090
    #: cells` and no error. A comment that describes a defect does not prevent it.
    #:
    #: With `--source`, the delete is scoped to the (model, source) pairs actually
    #: being re-inserted -- which is what "re-ingest this producer's rows" means,
    #: and `source` is a stored column so the scoping is exact rather than
    #: inferred. Without it the blanket model-wide drop is kept, because a blanket
    #: run plans every producer on disk and the wider delete is what purges rows
    #: whose file no longer exists.
    if _REPLACE["on"] and win:
        if getattr(a, "source", None):
            pairs = sorted({(k[0], r.get("source")) for k, r in win.items()
                            if r.get("source")})
            print("  --replace: dropping %d (model, source) pair(s) at "
                  "rule_version %d first -- SOURCE-SCOPED because --source was "
                  "given" % (len(pairs), _RV["v"]))
            for m, s in pairs:
                for t in TABLES[_RV["v"]]:
                    ch.execute("ALTER TABLE {db}.%s DELETE WHERE model='%s' "
                               "AND source='%s'"
                               % (t, m.replace("'", "\\'"), s.replace("'", "\\'")))
        else:
            models = sorted({k[0] for k in win})
            print("  --replace: dropping %d model(s) at rule_version %d first"
                  % (len(models), _RV["v"]))
            for m in models:
                for t in TABLES[_RV["v"]]:
                    ch.execute("ALTER TABLE {db}.%s DELETE WHERE model='%s'"
                               % (t, m.replace("'", "\\'")))
        _wait_for_mutations(ch)
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
            m, pr = k[0], k[1]
            #: SUM THE PARTITION HERE, ONCE. Folding in SQL later would put the
            #: rule in two places, which is the failure `movement` warns about.
            fold = {}
            for w in rows:
                a = fold.setdefault(w["word"], [0.0, 0])
                a[0] += float(w["p"]); a[1] += 1
            for wd, (pp, np_) in fold.items():
                w4 = {} if _RV["v"] == 3 else {
                    "topup": int(bool(d.get("topup"))),
                    "rule_version": int(d.get("rule_version") or 0),
                    "rules": d.get("rules") or "",
                    "prompt_cache": int(bool(d.get("prompt_cache")))}
                words.append(dict({"model": m, "prompt": pr, "word": wd,
                                   "p": pp, "n_paths": np_,
                                   "source": f["source"], "mtime": mt}, **w4))
            cells.append({"model": m, "prompt": pr, "n_words": len(rows),
                          "conservation": float(cons),
                          "tail": float(res.get("tail") or 0),
                          "drop": float(res.get("drop") or 0),
                          "open": float(res.get("open") or 0),
                          "mojibake": float(res.get("mojibake") or 0),
                          #: **DERIVED, NOT COPIED, AND THAT IS DELIBERATE.**
                          #: `res["total"]` is the producer's summary of the
                          #: four-way residual, and on a merged cell written
                          #: before 2026-08-21 it is STALE: the topup path
                          #: decremented `tail` for the mass it scored and never
                          #: rebuilt `total`, so the column holds the PASS-1
                          #: residual -- wrong on 350,453 of 385,855 topup cells,
                          #: mean 0.0148 high, max 0.115.
                          #:
                          #: `runners.py` now rebuilds it, but that only fixes
                          #: records written from here on. The stash already
                          #: holds the stale ones, and re-measuring 385,855 cells
                          #: to repair a summable column would be absurd. The
                          #: COMPONENTS in those records are correct -- the
                          #: producer's own conservation gate is computed from
                          #: them, not from `total` -- so summing them here
                          #: recovers the right value from data already on disk.
                          #:
                          #: Not a divergence from the source: wherever the
                          #: producer's `total` is trustworthy it is BY
                          #: CONSTRUCTION this same sum (twp.py builds it that
                          #: way), verified equal on 434,391 of 434,391 pass-1
                          #: cells and 984,857 of 984,857 v3 cells. Where they
                          #: differ, the sum is right and the summary is stale.
                          "total": (float(res.get("tail") or 0)
                                    + float(res.get("drop") or 0)
                                    + float(res.get("open") or 0)
                                    + float(res.get("mojibake") or 0)),
                          "theta": float(d.get("theta") or 0),
                          "rule_version": int(d.get("rule_version") or 0),
                          "dict_sha": d.get("dict_sha") or "",
                          "revision": d.get("revision") or "",
                          "bos_policy": d.get("bos_policy") or "",
                          "device": d.get("device") or "",
                          "compute_dtype": d.get("compute_dtype") or "",
                          "torch_version": d.get("torch_version") or "",
                          "transformers_version": d.get("transformers_version") or "",
                          "source": f["source"], "mtime": mt,
                          **({} if _RV["v"] == 3 else {
                              "rules": d.get("rules") or "",
                              "prompt_cache": int(bool(d.get("prompt_cache"))),
                              "topup": int(bool(d.get("topup"))),
                              "topup_words": int(d.get("topup_words") or 0),
                              "topup_mass": float(d.get("topup_mass") or 0.0),
                              #: WORDS ASKED FOR AND NOT SCORED. It is 0 across
                              #: CT-LLM's 24,369 topped-up words -- a MEASURED
                              #: zero, since `topup_words` is populated in the
                              #: same records -- but it cannot stay out of the
                              #: corpus on that basis. A word `score_words4`
                              #: refuses stays missing, so a lineage with a
                              #: non-zero rate never reaches coverage 0 and the
                              #: verifier reports OPEN forever with nothing to
                              #: say why. The distinction between "asked and
                              #: refused" and "never asked" only exists here.
                              "topup_refused": int(d.get("topup_refused") or 0)})})
        if len(words) > 400_000:
            wt, ct = TABLES[_RV["v"]]
            ch.insert(wt, words); words = []
            ch.insert(ct, cells); cells = []
            print("     ... %s cells written" % format(
                ch.scalar("SELECT count() FROM {db}.%s" % ct), ","))
    wt, ct = TABLES[_RV["v"]]
    if words:
        ch.insert(wt, words)
    if cells:
        ch.insert(ct, cells)
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
