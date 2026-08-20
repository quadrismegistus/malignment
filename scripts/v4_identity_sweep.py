#!/usr/bin/env python
"""Where is v4 BIT-IDENTICAL to v3? Measured per tokenizer, not argued from the rule.

    python scripts/v4_identity_sweep.py --limit 20
    python scripts/v4_identity_sweep.py            # every cached model

## THE QUESTION, AND WHY IT IS WORTH COMPUTE

`decoded_boundary` tests a token AS SPELLED. On SentencePiece the `▁` already
marks a Latin word boundary the same way under both rules, so there should be
nothing to correct; on byte-level BPE there is. If that holds across the roster
then for SentencePiece models the v3 Latin cells ARE the v4 Latin cells and need
no re-measuring at all -- 52 of 136 measured tokenizers, over 2,299 of 2,983
prompts, which is most of a fleet.

**That is a claim about money, so it is measured rather than reasoned.** Two
prompt classes x every cached model, `Rules()` against `ADOPTED`, same process,
same weights, prompt cache OFF so the only thing varying is the rule.

## WHAT COUNTS AS AN ANSWER

Bit-identity, `max |Δp| == 0.0` summed over the union of words -- not "small",
not "below theta". A difference below theta still moves a word across the gate
sometimes, and "small" is what the earlier effect-size framing already said. The
question here is whether the cells can be REUSED, and reuse needs exact.

## THE CONFOUND THIS CONTROLS

Comparing the stored v3 and v4 corpora cannot answer it: the v4 runs used
`--cache`, and the prompt cache is not bit-identical (up to ~8e-04). Measured
that way, 0 of 2,647 shared prompts came back identical on any model -- which
says nothing about the rule. Both arms here run in one process with the cache
off.
"""
import argparse
import gc
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

N_LATIN, N_CJK = 12, 8


def cached(m):
    pat = os.path.expanduser("~/.cache/huggingface/hub/models--%s/snapshots/*/*"
                             % m.replace("/", "--"))
    return any(f.endswith((".safetensors", ".bin")) for f in glob.glob(pat))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="/tmp/v4_identity_sweep.json")
    a = ap.parse_args()

    import torch
    from malignment import models as M
    from malignment import roster
    from malignment import twp as T
    from malignment import twp_v4 as V4
    from malignment.prompts import Prompts
    torch.set_grad_enabled(False)
    T.USE_PROMPT_CACHE = False

    meas = json.load(open(os.path.join(ROOT, "roster/models/measurements.json")))
    vocab = meas["sections"]["vocab"]["models"]
    allp = [p.text for p in Prompts.all()]
    lat = sorted(t for t in allp if not T.is_cjk(t))[:N_LATIN]
    zh = sorted(t for t in allp if T.is_cjk(t))[:N_CJK]

    todo = [m for m in sorted(roster.load()["nodes"]) if cached(m) and m in vocab]
    if a.limit:
        todo = todo[:a.limit]
    print("sweep: %d cached models | %d latin + %d cjk prompts | cache OFF\n"
          % (len(todo), len(lat), len(zh)), flush=True)

    out = []
    for i, mid in enumerate(todo, 1):
        note = vocab[mid].get("byte_notation")
        t0 = time.time()
        try:
            tok, _ = T.load_tokenizer(mid)
            model, _ = M.load_model(mid)
            bmask = T.boundary_mask(tok, model.config.vocab_size)
            trie = T.load_prefix_trie()
            cids, cstrs, lids, pi = T.cjk_vocab(tok, model.config.vocab_size)
            cjk = (trie, cids, cstrs, lids, pi) if len(cids) else None
        except Exception as e:                                  # noqa: BLE001
            print("  [%2d/%d] %-44s %-13s LOAD FAILED %s"
                  % (i, len(todo), mid.split("/")[-1][:44], note, str(e)[:40]), flush=True)
            out.append({"model": mid, "byte_notation": note, "error": str(e)[:120]})
            continue
        row = {"model": mid, "byte_notation": note}
        for name, ps in (("latin", lat), ("cjk", zh)):
            #: **`n_compared` EXISTS BECAUSE 0/12 MEANT TWO THINGS.** A prompt
            #: whose expand throws is skipped, so a model where EVERY prompt
            #: failed scored `identical=0, max_l1=0.0` -- identical output to a
            #: model measured cleanly where everything differed by nothing. Both
            #: Pharia arms landed in that state and read as "maximally different"
            #: when in fact nothing had been measured at all.
            #:
            #: Two states, one appearance, in the checker rather than the thing
            #: checked. The denominator is now what was actually COMPARED, and
            #: `errors` is carried so a silent zero cannot be read as a result.
            ident, worst, cmp_n, errs = 0, 0.0, 0, 0
            for p in ps:
                try:
                    x = V4.expand4(model, tok, p, "mps", bmask, cjk=cjk, rules=V4.Rules())[0]
                    y = V4.expand4(model, tok, p, "mps", bmask, cjk=cjk, rules=V4.ADOPTED)[0]
                except Exception:                               # noqa: BLE001
                    errs += 1
                    continue
                cmp_n += 1
                d = sum(abs(y.get(k, 0.0) - x.get(k, 0.0)) for k in set(x) | set(y))
                ident += (d == 0.0)
                worst = max(worst, d)
            row["%s_identical" % name] = ident
            row["%s_compared" % name] = cmp_n
            row["%s_errors" % name] = errs
            row["%s_n" % name] = len(ps)
            row["%s_max_l1" % name] = worst
        out.append(row)

        #: **TEARDOWN IS WHY THIS CAN SWEEP 102 MODELS.** `del model` alone leaves
        #: the tokenizer, the boundary mask and both tries live, and MPS holds its
        #: allocator pool until told otherwise -- so the resident set climbs by a
        #: fraction of every checkpoint and the run dies somewhere in the
        #: seventies with an allocation failure that reads like a bad model
        #: rather than like a leak. RH's ask, done before the first model
        #: finished rather than after the seventieth.
        #:
        #: My first attempt at this block did nothing three ways: a
        #: `for _n in (...): del _n` loop that deletes the LOOP VARIABLE and not
        #: the objects, an RSS read placed AFTER the line that prints it, and a
        #: format string one placeholder short of its arguments -- which would
        #: have raised TypeError on model one. Written out rather than patched in.
        del model, tok, bmask, cjk, trie, cids, cstrs, lids, pi
        gc.collect()
        try:
            torch.mps.empty_cache()
        except Exception:                                       # noqa: BLE001
            pass
        try:
            import resource
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 ** 3)
        except Exception:                                       # noqa: BLE001
            rss = 0.0
        row["peak_rss_gb"] = round(rss, 2)

        print("  [%2d/%d] %-40s %-13s latin %2d/%-2d (%.1e)  cjk %2d/%-2d (%.1e)"
              "  %3.0fs  peak %.1fGB%s"
              % (i, len(todo), mid.split("/")[-1][:40], note,
                 row["latin_identical"], row["latin_compared"], row["latin_max_l1"],
                 row["cjk_identical"], row["cjk_compared"], row["cjk_max_l1"],
                 time.time() - t0, rss,
                 "" if not (row["latin_errors"] + row["cjk_errors"]) else
                 "  ERRORS %d" % (row["latin_errors"] + row["cjk_errors"])), flush=True)
        json.dump(out, open(a.out, "w"), indent=1)

    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
