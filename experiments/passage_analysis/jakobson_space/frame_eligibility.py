"""Which aligned models can actually receive the API system prompt?

    python .../frame_eligibility.py
    python .../frame_eligibility.py --csv results/frame_eligibility.csv

To test whether OUR frame -- the system message the API models were generated
behind -- moves drift, the frame has to reach the model. Three things can go
wrong and only one of them is an error:

    RAISES      the template rejects a system role outright (many do)
    DISCARDS    the template accepts it and renders it to nothing, so the
                condition is silently identical to the control
    OK          the system block appears in the rendered string

**DISCARDS is the dangerous one.** It raises no exception and produces a
perfectly good generation run whose treatment arm never received the treatment.
`frame_prefill`'s README records `neo_7b` doing exactly this -- all four personas
rendered byte-identically to empty. A frame study that did not check this would
report a null and never know it had not run the manipulation.

## THIS IS A TOKENIZER-ONLY TEST

No weights are loaded. `apply_chat_template` lives in the tokenizer, so
eligibility costs a config download at most and can be settled before any GPU is
booked.

## THE TEST IS A BYTE COMPARISON, NOT AN EXCEPTION CHECK

Rendering `[system, user]` and comparing against `[user]` alone: if the two
strings are equal, the system block contributed nothing, whatever the call
returned. Checking only for an exception would pass every DISCARD case.

The API frame is quoted verbatim from `generate_task.py` rather than retyped, so
this cannot drift from what was actually sent.
"""

import argparse, csv, collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results", "quadrants.csv")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

STEM = "She was ugly and misshapen and she wanted to"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--min-passages", type=int, default=20)
    a = ap.parse_args(argv)
    from generate_task import SYSTEM_PROMPT
    from transformers import AutoTokenizer

    csv.field_size_limit(10 ** 7)
    per = collections.defaultdict(int)
    for r in csv.DictReader(open(SRC, newline="")):
        if r["category"] == "aligned":
            per[r["model"]] += 1
    models = sorted(m for m, n in per.items() if n >= a.min_passages)
    print("aligned models with >= %d passages: %d" % (a.min_passages, len(models)))
    print("system prompt under test, from generate_task.py:\n  %r\n" % SYSTEM_PROMPT)

    out, tally = [], collections.Counter()
    for m in models:
        row = dict(model=m, n_raw=per[m], verdict="", detail="")
        try:
            tok = AutoTokenizer.from_pretrained(m, trust_remote_code=False)
        except Exception as e:
            row.update(verdict="NO TOKENIZER", detail=type(e).__name__)
            out.append(row); tally[row["verdict"]] += 1
            print("  %-46s %-12s %s" % (m.split("/")[-1], row["verdict"], row["detail"]))
            continue
        if not getattr(tok, "chat_template", None):
            row.update(verdict="NO TEMPLATE", detail="ships none")
        else:
            try:
                with_sys = tok.apply_chat_template(
                    [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": STEM}],
                    tokenize=False, add_generation_prompt=True)
            except Exception as e:
                with_sys = None
                row.update(verdict="RAISES", detail=type(e).__name__)
            if with_sys is not None:
                bare = tok.apply_chat_template(
                    [{"role": "user", "content": STEM}],
                    tokenize=False, add_generation_prompt=True)
                #: the byte test. An equal render means the system block was
                #: dropped, which no exception would have told us.
                if with_sys == bare:
                    row.update(verdict="DISCARDS",
                               detail="renders identically to no-system")
                elif SYSTEM_PROMPT[:24] not in with_sys:
                    row.update(verdict="DISCARDS",
                               detail="string differs but the prompt text is absent")
                else:
                    delta = len(with_sys) - len(bare)
                    #: A NEGATIVE delta means the bare render already carried a
                    #: DEFAULT system block and ours REPLACED it. The frame still
                    #: reaches the model, but the contrast for that model is
                    #: "our prompt vs the vendor's default", not "our prompt vs
                    #: nothing" -- a different comparison, and it has to travel
                    #: with the model rather than be discovered in the results.
                    row.update(verdict="OK",
                               detail=("+%d chars" % delta if delta >= 0 else
                                       "%d chars -- REPLACES a default system "
                                       "block" % delta))
        out.append(row); tally[row["verdict"]] += 1
        print("  %-46s %-12s %s" % (m.split("/")[-1], row["verdict"], row["detail"]))

    print("\n%s" % "  ".join("%s %d" % (k, v) for k, v in tally.most_common()))
    ok = [r for r in out if r["verdict"] == "OK"]
    print("ELIGIBLE: %d models, carrying %s existing raw passages"
          % (len(ok), "{:,}".format(sum(r["n_raw"] for r in ok))))
    rep = [r for r in out if "REPLACES" in r["detail"]]
    if rep:
        print("\n%d model(s) already ship a DEFAULT system block, which our prompt"
              % len(rep))
        print("replaces. For these the contrast is ours-vs-default, not")
        print("ours-vs-nothing, and that difference must travel with the row:")
        for r in rep:
            print("    %-40s %s" % (r["model"].split("/")[-1], r["detail"]))
    nt = [r for r in out if r["verdict"] == "NO TOKENIZER"]
    if nt:
        #: an ENVIRONMENT failure is not a model property and must not be
        #: recorded as one -- these may well be eligible under a pinned
        #: transformers, and saying "ineligible" would retire them wrongly.
        print("\n%d model(s) failed to load a tokenizer IN THIS ENVIRONMENT."
              % len(nt))
        print("That is not a statement about the model. models.yaml pins some of")
        print("these to transformers 4.57.1; retry under the pinned profile")
        print("before treating any of them as ineligible.")
    if tally.get("DISCARDS"):
        print("\n%d model(s) DISCARD the system block. They would run cleanly and"
              % tally["DISCARDS"])
        print("produce a null that means nothing. Excluded, not silently kept.")
    #: ---- POWER. Compute the MDE before booking a GPU, not after.
    import math, statistics
    per_model = statistics.median([r["n_raw"] for r in ok]) if ok else 0
    SD = 0.0430          #: within-model sd of drift, measured on the aligned arm
    TARGETS = [("the measured wrapper effect", -0.0375),
               ("the API - aligned difference", +0.0085)]
    print("\nPOWER, with %d eligible models and a median %d raw passages each"
          % (len(ok), per_model))
    print("within-model sd(drift) = %.4f (measured, aligned arm)" % SD)
    print("\n%-14s %10s %38s" % ("new per model", "SE(diff)",
                                  "P(correct sign) for an effect of"))
    print("%-14s %10s %18s %18s" % ("", "", TARGETS[0][0], TARGETS[1][0]))
    def phi(z):
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))
    for X in (50, 100, 200, 400):
        se = SD * math.sqrt(1.0 / per_model + 1.0 / X)
        ps = [phi(abs(t) / se) for _, t in TARGETS]
        print("%-14d %10.5f %18.3f %18.3f" % (X, se, ps[0], ps[1]))
    print("\nSE floors at %.5f however many are generated, because the RAW side"
          % (SD / math.sqrt(per_model)))
    print("is fixed at %d passages per model and already collected." % per_model)
    #: the sign test over models is the headline, so state ITS power, not just
    #: the per-model one -- they are different questions and only the second
    #: decides whether the run is worth buying.
    print("\nSIGN TEST over %d models, two-sided:" % len(ok))
    for X in (100, 200):
        se = SD * math.sqrt(1.0 / per_model + 1.0 / X)
        for name, t in TARGETS:
            pc = phi(abs(t) / se)
            exp = pc * len(ok)
            k = round(exp)
            pv = min(1.0, 2 * sum(math.comb(len(ok), i)
                                  for i in range(k, len(ok) + 1)) / 2 ** len(ok))
            print("  %3d new/model, %-30s expect %.1f of %d correct -> p ~ %.2g"
                  % (X, name, exp, len(ok), pv))
    print("\nTOTAL to generate: %d models x N. At 200 each that is %s passages."
          % (len(ok), "{:,}".format(200 * len(ok))))
    print("Generate on the SAME stems the model already has raw passages for, so")
    print("the contrast can be paired within (model, stem) as well as within model.")

    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["model", "n_raw", "verdict", "detail"])
            w.writeheader()
            w.writerows(out)
        print("\n-> %s" % a.csv)


if __name__ == "__main__":
    main()
