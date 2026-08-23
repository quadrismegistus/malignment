#!/usr/bin/env python
"""Put the SYSTEM CONDITION into the v4 dedup key.

    python scripts/migrate_system_mode.py            # report, change nothing
    python scripts/migrate_system_mode.py --run

Adds `system_mode` and `user_msg` to `twp_cells_v4` and `twp_words_v4`, into the
SORTING KEY, then rebuilds the framed rows so their stamp is derived rather than
assumed. Idempotent: a second run finds the columns present and does nothing.

## WHY THIS IS NOT A COLUMN

Both tables are `ReplacingMergeTree(mtime)`, so **the ORDER BY is the dedup key**.
A `system=""` cell and a `system=DEFAULT` cell of one model and prompt agreed on
every key column, so the merge kept ONE by mtime -- not pooled, SILENTLY
REPLACED, with the store looking complete.

Demonstrated on a scratch table before touching anything: two `frame='prefill'`
rows differing only in the system condition, `OPTIMIZE FINAL`, **one row
survives**. After the alter, both survive. That is the whole change.

This is the `frame` defect one field further in, and `frame` was added to prevent
exactly it. `frame` says a cell was FRAMED; it does not say WHICH FRAME.

**IT HAD NOT BITTEN, AND THAT IS LUCK.** Only one system arm has ever been
written -- `--system ''`, the pilot's 16 checkpoints and box A's 40. It bites on
the very next run: the 8 checkpoints whose chat template discards an empty system
message, for which DEFAULT is the only condition their template permits.

## THE HISTORICAL ROWS ARE REBUILT, NOT PATCHED

An added key column takes the type's zero value on existing rows, so the 13,984
framed cells already in the store would sit at `system_mode=''` -- the value that
means UNFRAMED. That is not merely untidy: a later re-run of those same
checkpoints under `system=""` would stamp `empty`, miss the `''` rows in the
dedup key, and write a SECOND copy of a measurement that is already there.

A key column cannot be mutated, so the fix is delete-and-reingest, and it is safe
only because the source records are self-describing and still on this disk:

    ck.key() has carried system/system_set/user_msg since the frame landed
    13,984 pilot cells verified present locally, all (True, '', 'Hi.')

**The precondition is CHECKED, not assumed.** `--run` refuses if the local stash
cannot account for every framed cell the store is about to lose.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from malignment import ch  # noqa: E402

#: (table, the ORDER BY it must end up with). Written out rather than computed
#: from the current key: a migration that derives its target from the state it is
#: migrating cannot tell a half-applied run from a finished one.
TARGET = {
    "twp_cells_v4": ("model, prompt, rule_version, rules, prompt_cache, topup, "
                     "frame, system_mode, user_msg"),
    "twp_words_v4": ("model, prompt, word, rule_version, rules, prompt_cache, "
                     "topup, frame, system_mode, user_msg"),
}
NEW = ("system_mode", "user_msg")


def columns(table):
    return {c["name"] for c in ch.query(
        "SELECT name FROM system.columns WHERE database=currentDatabase() "
        "AND table='%s'" % table)}


def sorting_key(table):
    r = ch.query("SELECT sorting_key FROM system.tables WHERE "
                 "database=currentDatabase() AND name='%s'" % table)
    return r[0]["sorting_key"] if r else None


def local_framed():
    """{(model, prompt-count)} of framed cells on this disk, by model.

    The store is about to drop its framed rows, so this is the check that they
    can come back. Counted from the RECORDS, not from a directory listing.
    """
    base = os.path.expanduser("~/malignment-data/twp")
    out = {}
    for p in glob.glob(os.path.join(base, "*", "*", "jsonl.hashstash.raw",
                                    "data.jsonl")):
        model = None
        n = 0
        for ln in open(p, encoding="utf-8"):
            try:
                r = json.loads(ln)
            except Exception:
                continue
            k = r.get("__key__") or {}
            if k.get("frame"):
                model = k.get("model") or model
                n += 1
        if model and n:
            out[model] = out.get(model, 0) + n
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()

    todo = []
    for t, want in TARGET.items():
        have = columns(t)
        sk = sorting_key(t)
        missing = [c for c in NEW if c not in have]
        print("%s" % t)
        print("   ORDER BY   %s" % sk)
        print("   missing    %s" % (", ".join(missing) if missing else "(none)"))
        if missing:
            todo.append((t, want, missing))
        elif sk.replace(" ", "") != want.replace(" ", ""):
            #: Columns present but key not extended is the half-applied state,
            #: and it is WORSE than untouched: the fields look addressable and
            #: the merge still collapses them. Named rather than skipped.
            raise SystemExit("%s has the columns but NOT in its sorting key -- "
                             "half-applied, and no single ALTER can finish it. "
                             "Rebuild the table." % t)

    store_framed = ch.query(
        "SELECT count() AS n FROM twp_cells_v4 WHERE frame != ''")[0]["n"]
    print("\nframed cells in the store   %s" % format(store_framed, ","))

    if not todo:
        print("\nColumns already in both keys. Nothing to alter.")

    loc = local_framed()
    loc_n = sum(loc.values())
    print("framed cells on this disk   %s across %d checkpoints"
          % (format(loc_n, ","), len(loc)))
    #: **THE DELETE IS ONLY SAFE IF THE SOURCE OUTLIVES IT.** Every framed row the
    #: store holds must be reproducible from a record that is still here. Fewer
    #: locally than in the store means a re-ingest cannot restore what a delete
    #: removes, and this refuses rather than discovering it afterwards.
    recoverable = loc_n >= store_framed
    print("re-ingest can restore them  %s" % ("YES" if recoverable else "NO"))

    if not a.run:
        print("\nDRY RUN -- pass --run.")
        return 0
    if not recoverable:
        raise SystemExit("refusing: the store holds %s framed cells and this "
                         "disk accounts for %s. A delete would lose the "
                         "difference." % (format(store_framed, ","),
                                          format(loc_n, ",")))

    for t, want, missing in todo:
        #: **ONE STATEMENT OR NOTHING.** ClickHouse refuses a defaulted column in
        #: a sorting key, and refuses it again if the column was added by an
        #: earlier statement -- by then it is no longer newly added. Verified on a
        #: scratch table: the two-statement form raises, this one does not.
        sql = ("ALTER TABLE {t} {adds}, MODIFY ORDER BY ({want})".format(
            t=t, want=want,
            adds=", ".join("ADD COLUMN %s LowCardinality(String)" % c
                           for c in missing)))
        print("\n%s" % sql)
        ch.execute(sql)
        got = sorting_key(t)
        if got.replace(" ", "") != want.replace(" ", ""):
            raise SystemExit("ALTER reported success and the key is %r" % got)
        print("   ok, ORDER BY now %s" % got)

    if store_framed:
        print("\nrebuilding %s framed rows so the stamp is DERIVED"
              % format(store_framed, ","))
        for t in ("twp_cells_v4", "twp_words_v4"):
            n = ch.query("SELECT count() AS n FROM %s WHERE frame != ''"
                         % t)[0]["n"]
            ch.execute("ALTER TABLE %s DELETE WHERE frame != '' "
                       "SETTINGS mutations_sync=2" % t)
            left = ch.query("SELECT count() AS n FROM %s WHERE frame != ''"
                            % t)[0]["n"]
            print("   %-14s deleted %s, %s remain" % (t, format(n, ","),
                                                      format(left, ",")))
        print("\nNOW RE-INGEST. The framed rows are gone from the store and "
              "live only on this disk:\n"
              "   python -m malignment.ingest --run --rule-version 4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
