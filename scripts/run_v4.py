#!/usr/bin/env python
"""Re-run a model's whole prompt set under v4's ADOPTED rules, BESIDE v3.

    python scripts/run_v4.py --model mistralai/Mistral-7B-Instruct-v0.1

## NOTHING IS MOVED, AND THE SYSTEM WAS BUILT SO NOTHING HAS TO BE

`Checkpoint.key()` already carries the INSTRUMENT: `{model, prompt,
rule_version, dict_sha}`. Its own docstring says why -- *"Putting rule_version
and dict_sha IN THE KEY makes that impossible ... and the old rows remain for
comparison."* So a v4 cell writes a DIFFERENT KEY INTO THE SAME STASH and sits
beside its v3 twin in the same `data.jsonl`. No sibling tree, no rename, no
`twp/v3` directory.

**My first version of this file wrote a third format** -- a bare jsonl at a new
path, with `rows` FOLDED TO SURFACES so `t1` was discarded, and no `__key__` at
all. It would have been invisible to the ingest and incomparable with v3 in two
ways at once. The record below is v3's, field for field, because the comparison
is only meaningful if the only thing that differs is the rule.

## THE KEY GAINS ONE FIELD, DELIBERATELY

`rules` (e.g. `v4[decoded,depth=9]`) joins the key. `rule_version` alone cannot
distinguish two v4 rule SETS, and this module exists to run more than one --
without it, enabling a switch would silently overwrite the run that had it off.

## THE PROMPT SET COMES FROM v3's OWN OUTPUT

Not from `prompts`, not from a population query. **The comparison is only valid
on cells v3 actually produced**, and its stash is the record of which those were.
A prompt v3 skipped must not acquire an answer here, or the corpora differ by
more than the rule.
"""
import argparse
import json
import os
import time

import torch

from malignment import models as M
from malignment import twp as T
from malignment import twp_v4 as V4

CORPUS = os.environ.get("MALIGNMENT_CORPUS", os.path.expanduser("~/malignment-data"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--every", type=int, default=100)
    ap.add_argument("--cache", action="store_true",
                    help="prompt KV cache: ~2x, and NOT bit-identical")
    a = ap.parse_args()

    from malignment.checkpoint import Checkpoint
    from malignment.runners import PRODUCER

    #: **THE CACHE IS PART OF THE KEY, NOT AN OVERRIDE.** RH's call, and it is
    #: `Checkpoint.key()`'s own rule -- *"THE INSTRUMENT IS PART OF THE KEY"*.
    #: The prompt KV cache moves values by up to 8.25e-04, which is BELOW THETA
    #: (1e-3) and can therefore carry a word across the gate. So a cached cell
    #: and an uncached one are DIFFERENT MEASUREMENTS of the same prompt.
    #:
    #: `force=True` would have overwritten one with the other and left the
    #: corpus unattributable -- the failure `rule_version` and `dict_sha` are in
    #: the key to prevent, arriving through a flag instead of a rule bump.
    #: Keyed, they coexist, and the cache's effect at corpus scale becomes a
    #: free measurement instead of a destroyed one.
    T.USE_PROMPT_CACHE = bool(a.cache)
    rules = V4.ADOPTED
    ck = Checkpoint(a.model)
    st = ck.stash(PRODUCER)

    def v4key(prompt):
        #: v3's key plus `rules`, so two v4 rule sets cannot collide either.
        return {"model": a.model, "prompt": prompt,
                "rule_version": V4.RULE_VERSION, "dict_sha": T.dict_sha(),
                "rules": rules.label(), "prompt_cache": bool(a.cache)}

    #: the population is what v3 WROTE, read from its own keys
    v3keys = [k for k, _v in st.items() if k.get("rule_version") == 3]
    prompts = []
    seen = set()
    for k in v3keys:
        p = k.get("prompt")
        if p and p not in seen:
            seen.add(p)
            prompts.append(p)
    #: **CELLS WHERE THE RULE BITES GO FIRST.** v3's stash order put all 407 of
    #: Mistral's zh prompts at positions 2299-2705, so the first Chinese cell
    #: would have arrived 117 MINUTES INTO A 138-MINUTE RUN -- every informative
    #: cell in the last 20 minutes, and a defect in the CJK path invisible until
    #: then. Ordering by `is_cjk` costs nothing and turns a two-hour wait for the
    #: first signal into a two-minute one. RH asked for this before the run, not
    #: after, which is the only reason it was cheap.
    #:
    #: Detected from the PROMPT STRING, not from the `prompts` table, so the
    #: runner keeps working on a corpus the table does not know about.
    prompts.sort(key=lambda p: not T.is_cjk(p))
    if a.limit:
        prompts = prompts[:a.limit]
    todo = [p for p in prompts if v4key(p) not in st]
    print("%s\n  rules=%s  prompt_cache=%s  v3 cells=%d  todo=%d\n  stash=%s"
          % (a.model, rules.label(), bool(a.cache), len(prompts), len(todo),
             st.path), flush=True)
    if not todo:
        print("  nothing to do"); return

    torch.set_grad_enabled(False)
    tok, loader = T.load_tokenizer(a.model)
    model, _t = M.load_model(a.model)
    vs = model.config.vocab_size
    bmask = T.boundary_mask(tok, vs)
    trie = T.load_prefix_trie()
    cids, cstrs, lids, pi = T.cjk_vocab(tok, vs)
    cjk = (trie, cids, cstrs, lids, pi) if len(cids) else None
    print("  loader=%s vocab=%d cjk=%d decoded_ids=%d"
          % (loader, vs, len(cids), len(V4.decoded_boundary_ids(tok))), flush=True)

    stamp = dict(theta=T.THETA, rule_version=V4.RULE_VERSION, rules=rules.label(),
                 prompt_cache=bool(a.cache),
                 dict_sha=T.dict_sha(), bos_policy=T.bos_policy_for(a.model),
                 loader=loader, device=a.device, revision="",
                 compute_dtype="float16", producer=PRODUCER)
    t0 = time.time()
    for i, p in enumerate(todo, 1):
        rec = dict(stamp, model=a.model, prompt=p)
        try:
            w, res, _meta = V4.expand4(model, tok, p, a.device, bmask,
                                       cjk=cjk, rules=rules)
        except Exception as e:                                  # noqa: BLE001
            #: one prompt must not end the run -- v3's rule, kept
            with open(os.path.join(os.path.dirname(st.path), "skipped_v4.jsonl"),
                      "a", encoding="utf-8") as sf:
                sf.write(json.dumps(dict(rec, skipped="%s: %s"
                                         % (type(e).__name__, str(e)[:120])),
                                    ensure_ascii=False) + "\n")
            continue
        #: **v3's ROW SHAPE, `t1` KEPT.** Folding to surfaces would discard the
        #: first token and make the two corpora differ by more than the rule.
        rows = [{"word": s, "t1": int(t), "p": float(m)} for (s, t), m in w.items()]
        #: **`expand4`'s residual has no `total`; v3 builds that in its RETURN
        #: statement, not in the dict.** Computing it here rather than reaching
        #: for a key that does not exist -- and `term_floored` is included so a
        #: floored run still closes its books, even though ADOPTED does not floor.
        total = (res["tail"] + res["drop"] + res["open"] + res["mojibake"]
                 + res.get("term_floored", 0.0))
        rec.update(rows=rows, residual=dict(res, total=total),
                   conservation=sum(w.values()) + total)
        st[v4key(p)] = rec
        if i % a.every == 0:
            el = time.time() - t0
            print("  %5d/%d  %.2fs/cell  eta %.0f min"
                  % (i, len(todo), el / i, (len(todo) - i) * el / i / 60), flush=True)
    print("DONE %d cells in %.0f min" % (len(todo), (time.time() - t0) / 60), flush=True)


if __name__ == "__main__":
    main()
