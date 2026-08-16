#!/usr/bin/env python
"""Execute every claim in HOWTO.md. A doc that cannot fail is a doc that drifts.

    python docs/test_howto.py

Not a unit-test suite. It asserts the SPECIFIC NUMBERS the howto quotes, because
those are what a reader will act on: if `corpus.panel()` starts returning 2,100
prompts, the howto's "2,189" is wrong and someone should be told by a failure
rather than by a result that quietly moved.

Every number here appears verbatim in HOWTO.md. Changing one means changing both.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from malignment import corpus, roster                      # noqa: E402
from malignment.wordfield import paired_stats, sign_mde    # noqa: E402

FAIL = []


def check(name, got, want):
    ok = got == want
    print("  %-52s %-22s %s" % (name, got, "ok" if ok else "EXPECTED %s" % (want,)))
    if not ok:
        FAIL.append(name)


def main():

    print("\nbase -> endpoint pairs")
    ep, un = roster.endpoints()
    check("lineages resolved", len(ep), 50)
    check("unresolved (must be empty)", len(un), 0)
    inv = {e for e in ep.values() if "dolphin" in e.lower() or "zephyr-7b-beta" in e}
    check("no inverted endpoint survives", len(inv), 0)
    #: THE INVERTED FILTER IS UNREACHABLE TODAY, and this test is what
    #: established it. First it asserted "attestations change the answer"
    #: (false: 0 of 48 differ), then "removing the mistral ruling exposes it"
    #: (also false: same-publisher picks the same endpoint). Two independent
    #: rules mask it. Asserted as a KNOWN PROPERTY rather than quietly dropped,
    #: so that if the roster grows a lineage where it does bite, this line
    #: fails and the howto's claim gets revisited.
    ep_no, _ = roster.endpoints(attested={})
    check("attestations change no endpoint (filter unreachable)", ep_no == ep, True)
    import malignment.roster as R
    real = R.load
    doc = json.loads(json.dumps(real()))
    doc["families"]["mistral"].pop("representative", None)
    R.load = lambda: doc
    try:
        masked, _ = R.endpoints(attested={})
    finally:
        R.load = real
    check("even without the ruling, same-publisher still masks it",
          masked.get("mistralai/Mistral-7B-v0.1"),
          "mistralai/Mistral-7B-Instruct-v0.1")

    print("\npaths")
    ps = roster.paths()
    check("paths", len(ps), 50)
    import collections
    dist = collections.Counter(p["n_steps"] for p in ps)
    check("one-step paths", dist[1], 33)
    check("two-step", dist[2], 12)
    check("three-step", dist[3], 5)
    check("ops line up with nodes",
          all(len(p["ops"]) == len(p["nodes"]) - 1 == p["n_steps"] for p in ps), True)
    #: THE PATH AND THE CHAIN ARE DIFFERENT ROUTES and both are 16 lineages.
    #: Asserted so nobody reads the equal counts as the same set.
    multi = {p["base"] for p in ps if p["n_steps"] >= 2}
    chain = {c["base"] for c in roster.chains()}
    check("multi-step lineages", len(multi), 17)
    check("chain lineages", len(chain), 16)
    check("...and they are NOT the same 16", multi == chain, False)

    print("\npopulations")
    for kind, want in (("all", 160), ("bases", 50), ("aligned", 101),
                       ("endpoints", 50), ("chain_rungs", 52),
                       ("representative", 10), ("unavailable", 6)):
        check("population(%r)" % kind, len(roster.population(kind)), want)
    check("population('aligned', measured=True)",
          len(roster.population("aligned", measured=True)), 97)

    print("\nthe same populations in SQL")
    from malignment import ch
    check("{db}.endpoints rows", ch.scalar("SELECT count() FROM {db}.endpoints"), 50)
    check("{db}.populations rows", ch.scalar("SELECT count() FROM {db}.populations"), 429)
    check("{db}.prompts is current",
          ch.scalar("SELECT count() FROM {db}.prompts WHERE admitted AND upper(status) IN ('ACTIVE','')"),
          2783)

    print("\nchains")
    cs = roster.chains()
    check("chains", len(cs), 18)
    check("distinct bases", len({c["base"] for c in cs}), 16)

    print("\ndirection")
    check("sft -> dpo", roster.direction("sft", "dpo"), "forward")
    check("dpo -> sft", roster.direction("dpo", "sft"), "reverse")
    check("kto -> dpo", roster.direction("kto", "dpo"), "incomparable")
    #: `distill_align` is in the PREFERENCE tier so that MiniCPM5's released
    #: order (sft THEN opd) reads forward. Asserted because the alternative --
    #: filing it beside `distill` in the sft tier -- makes that edge
    #: "incomparable" and silently drops the lineage from anything ordered.
    check("sft -> distill_align", roster.direction("sft", "distill_align"), "forward")

    print("\npanel")
    n, prompts = corpus.panel()
    check("models crossed", n, 154)
    check("prompts after the live gate", len(prompts), 2189)

    print("\ndomains")
    check("prompts carrying a domain", len(corpus.domains(prompts)), 2189)
    check("texts whose rows disagree", len(corpus.domain_conflicts()), 47)
    check("conflicted prompts IN the panel",
          len(corpus.domains(prompts)) - len(corpus.domains(prompts, on_conflict="drop")), 13)

    print("\nreporting")
    d = [-0.311, -0.144, -0.129, -0.069, -0.063, -0.029, 0.005, 0.022,
         0.042, 0.071, 0.089, 0.100, 0.104, 0.116, 0.117, 0.164]
    s = paired_stats(d)
    check("n", s["n"], 16)
    check("sign test needs 13/16, so this is null", s["sign_p"] > 0.05, True)
    check("MDE exceeds the effect it is asked to see", sign_mde(d) > abs(s["mean"]), True)

    print("\nenvironment")
    check("every checkpoint declares env:",
          sum(1 for n in roster.load()["nodes"].values() if n.get("env")), 160)
    check("check_environments is clean", roster.check_environments(), [])
    #: THE NAME COLLISION IS ASSERTED so that renaming either one breaks here
    #: rather than on a rented box: `--profile default` is a 300GB A100 and a
    #: model whose requirement profile is `default` goes to a 48GB `dense`.
    E = roster.load_environments()
    check("profile 'default' launches on box 'dense'",
          E["profiles"]["default"]["launch"], "dense")
    check("...and box 'default' is a DIFFERENT, bigger machine",
          E["boxes"]["default"]["provides_vram_gb"] >
          E["boxes"]["dense"]["provides_vram_gb"], True)
    f = roster.fleet(roster.population("all"))
    check("fleet assigns every checkpoint", len(f["unassigned"]), 0)
    check("fleet boxes for the full roster", len(f["boxes"]), 7)
    #: Aquila is NOT broken; vLLM deleted it. Same model, two verdicts.
    check("Aquila unusable on 0.27.1",
          roster.environment("BAAI/Aquila2-7B", engine="0.27.1")["engine"]["usable"], False)
    check("...and usable on 0.22.1",
          roster.environment("BAAI/Aquila2-7B", engine="0.22.1")["engine"]["usable"], True)
    #: unknown size must NOT resolve to the smallest box.
    from malignment.roster import _sizing
    check("unknown params size to (None, None)", _sizing(None), (None, None))

    print("\nimport contract")
    #: **README PROMISES "three lines suffice to ANALYSE" AND checkpoint.py
    #: PROMISES "no torch import".** Both were false for months: __init__ pulls
    #: Checkpoint eagerly, checkpoint pulled twp, twp imports transformers. Run
    #: in a SUBPROCESS on this same interpreter and assert transformers never
    #: enters sys.modules -- that works whether or not it is installed, which a
    #: try/except ImportError here would not.
    import subprocess
    for mod in ("ch", "corpus", "roster", "checkpoint"):
        r = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r); import malignment.%s as _; "
             "print('torch' in sys.modules or 'transformers' in sys.modules)"
             % (ROOT, mod)],
            capture_output=True, text=True)
        check("malignment.%s pulls no torch/transformers" % mod,
              r.stdout.strip(), "False")

    print("\nclickhouse guard")
    #: THE GUARD THIS COMMENT ONCE ONLY CLAIMED TO HAVE. Each case is the case
    #: where it fires, or the alias case where it must NOT: a guard that
    #: rejects `t.column` gets switched off within a day.
    from malignment import ch as _ch
    def refused(sql):
        try:
            _ch._guard(sql.replace("{db}", _ch.DB))
            return False
        except _ch.ClickHouseError:
            return True
    check("passes an ordinary query", refused("SELECT 1 FROM {db}.movement"), False)
    check("passes system introspection", refused("SELECT * FROM system.tables"), False)
    check("passes a TABLE ALIAS", refused("SELECT t.base FROM {db}.pairs AS t"), False)
    check("REFUSES the 409GiB neighbour", refused("SELECT count() FROM lltk.texts"), True)
    check("REFUSES the archive db", refused("SELECT 1 FROM malign_logits.twp_cells"), True)
    check("REFUSES a DROP on a neighbour", refused("DROP TABLE lltk.texts"), True)

    print("\nroster integrity")
    check("models.yaml parses strictly", roster.check_authored(), [])

    print()
    if FAIL:
        print("  %d HOWTO CLAIMS ARE WRONG: %s" % (len(FAIL), ", ".join(FAIL)))
        print("  Fix the code or fix HOWTO.md -- they are not allowed to disagree.")
        return 1
    print("  every number in HOWTO.md reproduces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
