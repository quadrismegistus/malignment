#!/usr/bin/env python
"""Does path aggregation close the CJK gap? -> compares BOTH scorers against `expand`.

    python experiments/instrument_calibrations/path_aggregation/run.py \
        --model gl198976/mpt-7b

`expand` is the instrument of record: it discovers surfaces by walking a beam and
accumulates `mass x term` at EVERY token path that lands on one. `twp.score_words`
goes the other way -- it encodes a named word once and scores that single path --
so it is exact wherever a surface is reachable one way and a lower bound wherever
it is not. In English that is essentially always; in CJK it is not, because
byte-level tokenizers spell one character by several routes.

**THE COMPARISON IS AGAINST `expand`, ON THE SURFACES `expand` ITSELF FOUND.**
Scoring a list of words chosen by anything else would compare two instruments on
a population neither one produced, and would silently reward whichever scorer
happened to like the chosen words.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

from malignment import models as M                        # noqa: E402
from malignment import twp as T                           # noqa: E402
from malignment import twp_v4 as V4                       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

PROMPTS = [
    ("en", "She was so angry she wanted to"),
    ("zh", "那个自由的人选择了"),
]


def rel(a, b):
    return abs(a - b) / b if b else (0.0 if a == b else float("inf"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gl198976/mpt-7b")
    ap.add_argument("--device", default="mps")
    #: **SCORE A SUBSET FIRST.** The full surface set is ~400 words and the
    #: first run of this file printed nothing for 80 CPU-minutes because
    #: every stage reported only after all three had finished a prompt. A
    #: cost question needs a per-stage number, and a correctness question
    #: needs ten words, not four hundred.
    ap.add_argument("--limit", type=int, default=0,
                    help="score only the N highest-probability surfaces")
    a = ap.parse_args()

    tok, loader = T.load_tokenizer(a.model)
    #: `load_model` returns (model, tokenizer). Binding the tuple to `model`
    #: fails later at `model.config`, not here -- and the MPS hang got there
    #: first, so three runs died before this line could.
    model, _tok2 = M.load_model(a.model)
    dev = a.device
    bmask = T.boundary_mask(tok, model.config.vocab_size)
    trie = T.load_prefix_trie()
    cids, cstrs, lids, pids = T.cjk_vocab(tok, model.config.vocab_size)
    cjk = (trie, cids, cstrs, lids, pids) if len(cids) else None
    print("%s  loader=%s  cjk tokens=%d" % (a.model, loader, len(cids)))

    out = {"model": a.model, "loader": loader, "rows": []}
    for lang, prompt in PROMPTS:
        t0 = time.time()
        ref = T.expand(model, tok, prompt, dev, bmask, cjk=cjk)
        ref = ref[0] if isinstance(ref, tuple) else ref
        t_expand = time.time() - t0
        #: `expand` keys on (surface, first_token); the scorers take SURFACES and
        #: return the same key shape, so the population is expand's own surfaces.
        by_p = {}
        for k, v in ref.items():
            by_p[k[0]] = by_p.get(k[0], 0.0) + v
        surfaces = sorted(by_p, key=lambda w: -by_p[w])
        if a.limit:
            surfaces = surfaces[:a.limit]
        print("  %s expand: %d keys, %d surfaces, %.0fs -- scoring %d"
              % (lang, len(ref), len(by_p), t_expand, len(surfaces)), flush=True)
        keep = set(surfaces)
        want = {k: v for k, v in ref.items() if k[0] in keep}

        t0 = time.time()
        g1, r1, tot1 = T.score_words(model, tok, prompt, surfaces, dev, bmask, cjk=cjk)
        t_single = time.time() - t0
        print("     score_words done %.0fs" % t_single, flush=True)

        t0 = time.time()
        g2, r2, tot2, diag = V4.score_words_paths(model, tok, prompt, surfaces,
                                                  dev, bmask, cjk=cjk)
        t_paths = time.time() - t0

        row = {"lang": lang, "prompt": prompt, "surfaces": len(surfaces),
               "expand_keys": len(want), "seconds": {
                   "expand": round(t_expand, 1), "score_words": round(t_single, 1),
                   "score_words_paths": round(t_paths, 1)},
               "diag": {k: (v if not isinstance(v, dict) else len(v))
                        for k, v in diag.items()}}
        for name, got, refused in (("score_words", g1, r1),
                                   ("score_words_paths", g2, r2)):
            shared = [k for k in want if k in got]
            exact = sum(1 for k in shared if got[k] == want[k])
            worst = max((rel(got[k], want[k]) for k in shared), default=0.0)
            #: UNDER-counting is the failure mode a single path has; OVER-counting
            #: would mean double-adding a path, which is the failure mode
            #: enumeration risks. Both directions are reported.
            under = sum(1 for k in shared if got[k] < want[k] * (1 - 1e-9))
            over = sum(1 for k in shared if got[k] > want[k] * (1 + 1e-9))
            row[name] = {"matched": len(shared), "exact": exact,
                         "max_rel": worst, "under": under, "over": over,
                         "refused": len(refused)}
            print("  %-3s %-18s matched %3d/%3d  exact %3d  under %3d  over %3d"
                  "  max_rel %.1e  %.0fs"
                  % (lang, name, len(shared), len(want), exact, under, over,
                     worst, row["seconds"][name]))
        print("       diag: %s" % row["diag"])
        out["rows"].append(row)

    path = os.path.join(HERE, "results_%s.json" % a.model.replace("/", "__"))
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote %s" % path)


if __name__ == "__main__":
    main()
