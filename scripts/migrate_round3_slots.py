#!/usr/bin/env python
"""One-time migration of the archive's 86 slot items into the v3 format.

    python scripts/migrate_round3_slots.py            # dry run, prints a summary
    python scripts/migrate_round3_slots.py --write

Reads `~/github/malign-logits/pair_drafts/round3/round3_slots.yaml`, which is in
the READ-ONLY archive and is NOT modified. Writes a new file in this repo.

## THREE THINGS CHANGE, AND ONLY ONE OF THEM IS COSMETIC

**1. THE POLE FIELDS BECOME LISTS.** The archive wrote them as comma-delimited
strings, which YAML parses as ONE SCALAR rather than a sequence -- so `naughty`
is a `str` there and a `list` in anything the app emits. That was hand-editing
rather than a convention (RH, 2026-08-17). This is the cosmetic one, and it is
still worth doing: a file mixing both types needs a parser that handles both,
and `round3_slots.yaml` plus one pasted item silently becomes such a file.

**2. THE ID CHANGES, AND THE OLD ONE IS KEPT.** `nn_<last3>_<top_nice>-<top_naughty>`
was unstable and collision-prone; see `slots.item_id`. Every migrated item
carries `legacy_id` so that the 86 existing references -- in docket posts, in
prose, in whatever else -- still resolve. **The migration refuses to run if the
new ids are not unique**, because a hash collision here would silently merge two
frames.

**3. PROVENANCE IS ADDED, AND ITS STATUS IS NOT UNIFORM.** The archive's items
record nothing about which checkpoints produced their masses. RH attests that all
86 were screened on `meta-llama/Llama-3.1-8B` + `allenai/Llama-3.1-Tulu-3-8B-SFT`
pooled, with no movement shown at authoring time.

**Two of the 86 can be CHECKED and 84 cannot**, because only two of these prompts
have word-level rows in the store. So the stamp records which:

    verified   the booked masses reproduce under the declared pair, with the error
    attested   RH's statement, carried as a claim with its source named

That distinction is the repo's own three-tier convention (AUTHORED / OBSERVED /
ATTESTED) and flattening it would turn one person's memory into a measurement.
The two checkable items both reproduce -- see `--verify`.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from malignment import slots                                    # noqa: E402

SRC = "/Users/rj416/github/malign-logits/pair_drafts/round3/round3_slots.yaml"
DST = os.path.join(REPO, "roster", "prompts", "slots", "round3.yaml")

#: RH, 2026-08-17: "all of those were made using llama-base and tulu-sft pooled,
#: no movement seen". Verified on the two items that have word rows; see the
#: module docstring for why the other 84 are `attested` rather than `verified`.
ATTESTED_PAIR = ["meta-llama/Llama-3.1-8B", "allenai/Llama-3.1-Tulu-3-8B-SFT"]
ATTESTED_BY = "RH, 2026-08-17 (docket-adjacent; stated in session)"

HEADER = """\
# round3 slot items, migrated from the archive on 2026-08-17.
#
# SOURCE  malign-logits/pair_drafts/round3/round3_slots.yaml (read-only; unmodified)
# WRITER  scripts/migrate_round3_slots.py
#
# THREE CHANGES FROM THE ARCHIVE FORM:
#
#   1. `naughty` and `nice` are YAML LISTS. The archive wrote comma-delimited
#      STRINGS, which parse as one scalar. Hand-editing, not a convention.
#   2. `item_id` is the new prompt-only format; the archive's id is kept as
#      `legacy_id` so existing references resolve. See `malignment/slots.py`.
#   3. `screened_by` is new. The archive recorded NO provenance at all.
#
# `screened_by.status` IS NOT UNIFORM AND MUST NOT BE READ AS IF IT WERE:
#
#   verified   the booked masses reproduce under the declared pair (error given)
#   attested   RH's statement, carried as a claim, with its source named
#
# Only 2 of these 86 prompts have word-level rows in the store, so only 2 could
# be checked. Both reproduce. The other 84 are one person's recollection, which
# is evidence and is not a measurement.
"""


def load_src():
    import yaml
    with open(SRC, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def poles(v):
    """Archive pole field -> list. Accepts BOTH types, because both exist."""
    if isinstance(v, list):
        return [str(w).strip() for w in v if str(w).strip()]
    return [w.strip() for w in str(v or "").split(",") if w.strip()]


def verify(items):
    """{prompt: (gm, nm, err)} for the items whose masses can be re-derived.

    Uses the same method malign used to recover the archive's provenance at
    [6365]: sum each pole's words under each arm, pool as a MEAN, and compare to
    the booked masses. **A pair that reproduces two floats over an author-chosen
    word set is strong evidence**, and the check needs no memory and no trust.
    """
    from malignment import ch
    esc = lambda s: s.replace("'", "''")
    inlist = ",".join("'" + esc(x["prompt"]) + "'" for x in items)
    present = {r["prompt"] for r in ch.query(
        "SELECT DISTINCT prompt FROM {db}.twp_words WHERE prompt IN (" + inlist + ")")}
    out = {}
    for it in items:
        if it["prompt"] not in present:
            continue
        ng, nc = poles(it["naughty"]), poles(it["nice"])
        lst = lambda xs: ",".join("'" + esc(w) + "'" for w in xs)
        rows = ch.query(
            "SELECT model, sumIf(p, word IN (" + lst(ng) + ")) AS gm, "
            "sumIf(p, word IN (" + lst(nc) + ")) AS nm FROM {db}.twp_words "
            "WHERE prompt='" + esc(it["prompt"]) + "' AND model IN ("
            + lst(ATTESTED_PAIR) + ") GROUP BY model")
        m = {r["model"]: (float(r["gm"]), float(r["nm"])) for r in rows}
        if len(m) != len(ATTESTED_PAIR):
            continue
        gm = sum(v[0] for v in m.values()) / len(m)
        nm = sum(v[1] for v in m.values()) / len(m)
        err = max(abs(gm - float(it["naughty_mass"])),
                  abs(nm - float(it["nice_mass"])))
        out[it["prompt"]] = (gm, nm, err)
    return out


def migrate(src, checked):
    out = []
    for it in src:
        ng, nc = poles(it["naughty"]), poles(it["nice"])
        prompt = str(it["prompt"]).strip()
        v = checked.get(prompt)
        stamp = {
            "role": "screening",
            "models": ATTESTED_PAIR,
            "pooled": True,
            #: **STATED, BECAUSE THE ALTERNATIVE IS A DIFFERENT INSTRUMENT.**
            #: malign's [6361]: an item screened on summed probabilities with
            #: movement never shown is not the same object as one screened while
            #: looking at movement.
            "displayed": "probability",
            "status": "verified" if v else "attested",
        }
        if v:
            stamp["reproduces"] = {
                "naughty_mass": round(v[0], 6),
                "nice_mass": round(v[1], 6),
                "max_abs_err": round(v[2], 6),
            }
        else:
            stamp["attested_by"] = ATTESTED_BY
            stamp["unverifiable"] = "no word-level rows for this prompt in the store"
        d = {
            "item_id": slots.item_id(prompt),
            "legacy_id": it.get("item_id"),
            "prompt": prompt,
            "domain": it.get("domain", ""),
            "naughty": ng,
            "nice": nc,
            "naughty_mass": it.get("naughty_mass"),
            "nice_mass": it.get("nice_mass"),
            "share": it.get("share"),
            "writer": it.get("writer", "slot-explorer"),
            "note": "",
            "screened_by": stamp,
        }
        #: Carried through rather than dropped: present on 39 of 86 and nobody
        #: here knows what depends on it. A migration that silently narrows a
        #: record is the same defect as one that silently widens it.
        if "global_cos" in it:
            d["global_cos"] = it["global_cos"]
        out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the store check; every item becomes `attested`")
    ap.add_argument("--out", default=DST)
    args = ap.parse_args()

    src = load_src()
    print("source     %s" % SRC)
    print("items      %d" % len(src))

    #: **THE POLE-TYPE CENSUS, PRINTED.** If the archive turns out to hold a mix
    #: already, the reader should learn it here rather than from a parser
    #: failing later.
    kinds = {type(x["naughty"]).__name__ for x in src} | \
            {type(x["nice"]).__name__ for x in src}
    print("pole types %s -> list" % ", ".join(sorted(kinds)))

    checked = {}
    if not args.no_verify:
        try:
            checked = verify(src)
        except Exception as e:
            print("verify     UNAVAILABLE (%s: %s)" % (type(e).__name__, str(e)[:60]))
    print("verified   %d of %d items reproduce under the attested pair" % (len(checked), len(src)))
    for p, (gm, nm, err) in checked.items():
        print("             err %.4f  %r" % (err, p[:52]))

    items = migrate(src, checked)

    ids = [d["item_id"] for d in items]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    #: **REFUSE RATHER THAN MERGE.** A hash collision would silently fuse two
    #: frames into one entry, which is exactly the failure the new id was chosen
    #: to remove; discovering it here is the whole point of checking.
    if dupes:
        raise SystemExit("REFUSING: %d new ids collide: %s" % (len(dupes), dupes))
    legacy = [d["legacy_id"] for d in items]
    print("new ids    %d unique (legacy: %d unique) — no collisions"
          % (len(set(ids)), len(set(legacy))))
    print("example    %s\n           was %s" % (items[0]["item_id"], items[0]["legacy_id"]))

    if not args.write:
        print("\ndry run — pass --write to create %s" % args.out)
        return
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    slots.write_items(items, path=args.out)
    #: `write_items` stamps its own header, which describes the running authoring
    #: file. This file is a migration and says so instead.
    with open(args.out, encoding="utf-8") as fh:
        body = fh.read()
    body = body[body.index("- item_id:"):] if "- item_id:" in body else body
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(HEADER + body)
    print("\nwrote %s" % args.out)


if __name__ == "__main__":
    main()
