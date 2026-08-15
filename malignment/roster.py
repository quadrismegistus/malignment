"""The roster: one authored file in, one ClickHouse table out.

    python -m malignment.roster            show what would be written
    python -m malignment.roster --write    build malign_logits.roster

WHAT THIS REPLACES, AND WHY IT IS ONE TABLE RATHER THAN FOUR FILES. On
2026-08-15 the question *"how do you get the representative model pairs?"* was
put to three seats and produced six answers:

    data/lineage_representative_pairs.txt        46   frozen for one experiment
    lineage.representative_pairs('frozen')       46
    lineage.representative_pairs('registry')     51   live, CH-defined
    CH movement_edges is_representative          52   over 47 bases
    Registry.base_aligned_pairs()                54   one per base CHECKPOINT
    base_aligned_pairs collapsed to lineages     48

**None of them was wrong.** Each answered a different question and the integer
did not say which. A document written the day before (`docs/model-populations.md`)
had already tried to fix this and made it worse by legitimising four defensible
numbers -- so every seat picked one correctly and reported a bare count.

The fix is not another function. It is that **the definition lives in ONE place
that consumers cannot bypass**: a view. A query returns rows, and the rows carry
the lineage they were collapsed on, so a reader can see the operation rather
than infer it from a total.

## AUTHORED vs GENERATED, WHICH IS THE DISTINCTION THE OLD LAYOUT COULD NOT MAKE

    roster/models.json          AUTHORED. hand-edited. no script writes it.
    malign_logits.roster        GENERATED from it. no human edits it.

The old repo's registry was regenerate-only -- correctly, since *"a cache that
can outrank its source is how 59 models shadowed 112 for five weeks"* -- but it
had no authored INPUT file, so declarations fled into `__init__.py` where a hand
edit survived a rebuild. 691 lines of Python dict as a data store, because the
data store had no door.

## THE TABLE IS `roster`, NOT `models`

`malign_logits.models` is the OLD repo's table, built 2026-08-11 and four days
stale by the time this was written. Writing there would break a repo that still
works. Two tables during the transition is the cost of not breaking it, and the
manifest records which is which.
"""
import argparse
import json
import os
import sys

from . import ch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTHORED = os.path.join(ROOT, "roster", "models.json")
TABLE = "roster"

#: The family slots, in ladder order. The slot IS the declared position: a
#: checkpoint named as `superego` is one, and there is no second place that says
#: otherwise. The old repo carried `position` in three files that could disagree.
SLOTS = [("base", "base"), ("ego", "sft"), ("superego", "dpo"),
         ("reinforced_superego", "rlvr"), ("reasoning", "reasoning")]

DDL = """
CREATE TABLE IF NOT EXISTS {db}.roster (
    model_id    String,
    family      Array(String),
    position    LowCardinality(String),
    stage       LowCardinality(String),
    lineage     String,
    org_type    LowCardinality(String),
    country     LowCardinality(String),
    scale       LowCardinality(String),
    open_weight UInt8,
    open_data   UInt8,
    note        String
) ENGINE = ReplacingMergeTree ORDER BY model_id
"""


def authored():
    """The hand-edited roster. Raises if absent -- never silently empty."""
    with open(AUTHORED, encoding="utf-8") as fh:
        return json.load(fh)


def rows():
    """One row per checkpoint, expanded from the families.

    LINEAGE IS DERIVED, NOT DECLARED -- it is the family's `base` checkpoint.
    That makes `llama`, `tulu` and `tulu-no-safety` collapse automatically,
    because all three declare `meta-llama/Llama-3.1-8B` as base: three alignment
    recipes on ONE pretraining run, which is the unit every cross-family
    statistic in this project claims to use and has twice been quoted wrong
    (39 base strings resampled as 39 lineages when they were 34; "23 pairs are
    20 lineages").

    **A derived lineage cannot go stale and cannot disagree with the roster**,
    which a separate `lineage_map_models.json` could and did. The one thing it
    does NOT capture is a declared union of sizes -- the old map unioned
    Llama-3.1 8B with 70B, and Falcon-H1 1.5B with 7B, on the argument that a
    size variant is not an independent pretraining run. If that union is wanted
    it belongs in `models.json` as a declared exception on the family, not in a
    fourth artifact. It is NOT implemented here, so today 8B and 70B are two
    lineages, and that is a difference from the old map, stated rather than
    discovered later.
    """
    A = authored()
    fams, cps = A["families"], A["checkpoints"]
    out, seen = [], {}
    for key, fam in sorted(fams.items()):
        base = fam.get("base")
        if not base:
            #: A family with no base cannot anchor a lineage. Refuse loudly --
            #: silently assigning it one is how a population acquires a member
            #: nobody declared.
            raise ValueError("family %r has no base checkpoint" % key)
        for slot, stage in SLOTS:
            mid = fam.get(slot)
            if not mid:
                continue
            d = dict(cps.get(mid, {}))
            row = {"model_id": mid, "family": key, "position": slot,
                   "stage": d.get("stage", stage), "lineage": base,
                   "org_type": d.get("org_type", ""), "country": d.get("country", ""),
                   "scale": d.get("scale", ""),
                   "open_weight": int(bool(d.get("open_weight"))),
                   "open_data": int(bool(d.get("open_data"))),
                   "note": d.get("position_evidence", "")}
            #: A checkpoint can be named by two families (a shared base). That is
            #: legitimate; two rows for one model_id is not. First declaration
            #: wins and the collision is REPORTED, never merged silently.
            #: FAMILY IS MANY-TO-MANY WITH CHECKPOINT and a scalar column
            #: cannot hold it. Seven families declare `meta-llama/Llama-3.1-8B`
            #: (llama, tulu, tulu-no-safety and four SFT ablations); four
            #: declare `pythia-2.8b` (the archangel method variants). Under
            #: first-declaration-wins, `tulu-sft-full` vanished ENTIRELY --
            #: every checkpoint it names was claimed by `tulu` first -- so a
            #: family disappeared from the roster while every one of its
            #: checkpoints was present. Array, and every declaring family is
            #: listed: `WHERE has(family, 'tulu-sft-full')`.
            if mid in seen:
                seen[mid]["family"].append(key)
                continue
            row["family"] = [key]
            seen[mid] = row
            out.append(row)
    return out, {r["model_id"]: r["family"] for r in out if len(r["family"]) > 1}


VIEWS = {
    #: ONE definition per question, in the only place a consumer cannot bypass.
    "lineage_representatives": """
        CREATE OR REPLACE VIEW {db}.lineage_representatives AS
        SELECT lineage, argMin(model_id, model_id) AS model_id
        FROM {db}.roster WHERE position = 'base' GROUP BY lineage
    """,
    #: A PAIR is (base, aligned) WITHIN one lineage, one row per lineage. The
    #: aligned arm is the LAST slot present in ladder order -- the endpoint of
    #: the ladder, not an arbitrary pick -- and `n_aligned` says how many arms
    #: were collapsed so a reader sees the choice rather than inferring it.
    "representative_pairs": """
        CREATE OR REPLACE VIEW {db}.representative_pairs AS
        SELECT b.lineage AS lineage, b.model_id AS base, a.model_id AS aligned,
               a.pos AS aligned_position, a.n AS n_aligned
        FROM (SELECT lineage, any(model_id) AS model_id FROM {db}.roster
              WHERE position = 'base' GROUP BY lineage) AS b
        INNER JOIN
             (SELECT lineage, argMax(model_id, rk) AS model_id,
                     argMax(position, rk) AS pos, count() AS n
              FROM (SELECT lineage, model_id, position,
                           multiIf(position = 'reinforced_superego', 3,
                                   position = 'superego', 2,
                                   position = 'ego', 1, 0) AS rk
                    FROM {db}.roster WHERE position != 'base')
              GROUP BY lineage) AS a
        ON b.lineage = a.lineage
    """,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    rs, dupes = rows()
    fams = len({k for r in rs for k in r["family"]})
    lins = len({r["lineage"] for r in rs})
    print("  authored: %s" % os.path.relpath(AUTHORED, ROOT))
    print("  %d checkpoints | %d families | %d lineages (derived from base)"
          % (len(rs), fams, lins))
    if dupes:
        print("  checkpoints named by MORE THAN ONE family: %d" % len(dupes))
        for mid, ks in list(dupes.items())[:6]:
            print("     %-50s %s" % (mid[:50], ", ".join(ks)))
    if not a.write:
        print("\n  --write to build %s.%s and its views" % (ch.DB, TABLE))
        return 0

    ch.execute(DDL)
    ch.execute("TRUNCATE TABLE {db}.roster")
    ch.insert(TABLE, rs)
    for name, sql in VIEWS.items():
        ch.execute(sql)
        print("  view %s.%s" % (ch.DB, name))
    n = ch.scalar("SELECT count() FROM {db}.roster")
    p = ch.scalar("SELECT count() FROM {db}.representative_pairs")
    print("\n  wrote %s rows to %s.%s" % (n, ch.DB, TABLE))
    print("  representative_pairs: %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
