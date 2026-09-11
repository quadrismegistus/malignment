"""GATE: closure rides the REAL runner's record, on the declared prompts only.

    uv run python experiments/displacement/architecture/tests/closure_rides_the_record.py

The smoke builds its own record by hand, so it cannot tell you that
`TWPRunner.run()` produces one. This runs the actual production path on four
prompts -- three verse slots from the manifest and one that is not -- and
asserts the four things the design rests on:

    verse cells carry `closure`               it fired where asked
    the non-verse cell does NOT               it is gated, not global
    ingest's include predicate still holds    the words ingest is unaffected
    ingest._key_body_agree passes             `closure` is a BODY key, and
                                              INSTRUMENT_FIELDS does not hold it

Run 2026-09-11 on SmolLM2-360M / MPS: 4/4, and one cell scored 26 of 40 rider
words rather than 40 -- words over `MAX_WORD_TOKENS` are dropped rather than
truncated, because a truncated word is a different word and its closure is a
different quantity. `n_scored` travels so that is visible instead of silent.
"""
import json, os, sys
sys.path.insert(0, "/Users/rj416/github/malignment")
sys.path.insert(0, "/Users/rj416/github/malign-logits")
os.environ.setdefault("MALIGNMENT_PRODUCER", "e2e")
from malignment.checkpoint import Checkpoint
from malignment.runners import TWPRunner as Runner

MAN = "/Users/rj416/github/malignment/experiments/emergence/capacities/data/verse_fleet_slot_manifest.json"
cells = json.load(open(MAN))["cells"]
verse = [c["context"] for c in cells if c["slot"] == "called"][:3]
other = ["The capital of France is"]                     # NOT in the manifest
prompts = verse + other

ck = Checkpoint("HuggingFaceTB/SmolLM2-360M", out="/tmp/e2e_out")
r = Runner(ck)
res = r.run(prompts, closure_at=set(verse), verbose=True)
print("\nrun ->", {k: v for k, v in res.items() if k in ("written", "skipped", "model")})

st = ck.stash()
n_cl = n_no = 0
for k, rec in st.items():
    p = k.get("prompt") if isinstance(k, dict) else None
    has = "closure" in rec
    if has:
        n_cl += 1
        c = rec["closure"]
        assert set(c) >= {"k", "nl_ids", "n_scored", "words"}, c.keys()
        assert all(0.0 <= v <= 1.0 for v in c["words"].values())
    else:
        n_no += 1
    print("  %-42s closure=%s%s" % ((p or "?")[:42].replace("\n", "/"), has,
          "  k=%d scored=%d" % (c["k"], c["n_scored"]) if has else ""))
print()
print("ASSERTIONS")
print("  verse cells carry closure        %d/%d %s" % (n_cl, len(verse), "PASS" if n_cl == len(verse) else "FAIL"))
print("  non-verse cell does NOT          %d/%d %s" % (n_no, len(other), "PASS" if n_no == len(other) else "FAIL"))
ok = n_cl == len(verse) and n_no == len(other)
# the ingest predicate, on the REAL records
inc = sum(1 for _, rec in st.items()
          if rec.get("rule_version") == 3 and "rows" in rec and "residual" in rec)
print("  ingest include predicate holds   %d/%d %s" % (inc, n_cl + n_no, "PASS" if inc == n_cl + n_no else "FAIL"))
ok &= inc == n_cl + n_no
# key/body agreement, using the real checker
from malignment import ingest
bad = 0
for _, rec in st.items():
    try:
        ingest._key_body_agree(rec, "e2e")
    except ValueError as e:
        bad += 1; print("   KEY/BODY:", str(e)[:120])
print("  _key_body_agree passes           %d bad %s" % (bad, "PASS" if not bad else "FAIL"))
ok &= not bad
print("\n%s" % ("E2E PASSED" if ok else "E2E FAILED"))
sys.exit(0 if ok else 1)
