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
    att = json.load(open(os.path.join(ROOT, "roster", "models", "attestations.json")))

    print("\nbase -> endpoint pairs")
    ep, un = roster.endpoints(attestations=att)
    check("lineages resolved", len(ep), 48)
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
    ep_no, _ = roster.endpoints(attestations=None)
    check("attestations change no endpoint (filter unreachable)", ep_no == ep, True)
    import malignment.roster as R
    real = R.load
    doc = json.loads(json.dumps(real()))
    doc["families"]["mistral"].pop("representative", None)
    R.load = lambda: doc
    try:
        masked, _ = R.endpoints(attestations=None)
    finally:
        R.load = real
    check("even without the ruling, same-publisher still masks it",
          masked.get("mistralai/Mistral-7B-v0.1"),
          "mistralai/Mistral-7B-Instruct-v0.1")

    print("\nchains")
    cs = roster.chains()
    check("chains", len(cs), 18)
    check("distinct bases", len({c["base"] for c in cs}), 16)

    print("\ndirection")
    check("sft -> dpo", roster.direction("sft", "dpo"), "forward")
    check("dpo -> sft", roster.direction("dpo", "sft"), "reverse")
    check("kto -> dpo", roster.direction("kto", "dpo"), "incomparable")

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
