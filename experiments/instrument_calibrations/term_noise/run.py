#!/usr/bin/env python
"""run.py — how much of a word's `term` is diffuse boundary noise?

    python run.py --models gl198976/mpt-7b --n 25 --write

**THE MEASUREMENT THAT DECIDES v4's SCOPE.** `p(word) = mass x term`, and
`term = row[b].sum()` sums over EVERY boundary token. **The count that used to
sit here — 48,197 for "a Latin surface" — was measured on a CJK SURFACE and is
withdrawn ([6390]).** For a Latin surface mpt marks 28,823 space-initial, 1,247
punct, 155 empty and 2 CJK. Nothing below depends on it; the saturation result is
about the SHARE of `term` that is diffuse, not about how many tokens carry it. On the fragment `murm` that sum is 0.5341 while no single boundary
token exceeds 0.003: the model wants `murmured` (`ured` at 0.0160) and `murm`
scores 0.060 x 0.534 anyway.

Fragments are where it is VISIBLE, not where it happens. `term` multiplies into
every stored `p`, so it is inside every `dP` any consumer weights by — dario
confirmed their calibrations read exactly `rows[].word` and `rows[].p` ([6388]).

    if a typical word's term is mostly GENUINE continuations
        -> fragments are cosmetic, v4 touches them alone, no number moves
    if sub-theta boundary noise is a MATERIAL share of ordinary words' term
        -> every p in 984,857 cells carries it and v4 is a re-derivation

Nobody has measured which. dario declined to, correctly: checking `term` by
reimplementing `term` tests two implementations against each other. So this
mirrors `expand`'s beam and decomposes the SAME `row[b]` the producer used,
rather than recomputing a boundary sum of its own.

## WHAT IT DECOMPOSES

For every word the beam emits, at the depth it is emitted:

    term_total  row[b].sum()                       what twp uses
    term_top    sum of boundary tokens >= FLOOR    plausible continuations
    term_tail   sum of boundary tokens <  FLOOR    the diffuse remainder
    n_tail      how many tokens that remainder is spread across

`FLOOR` defaults to theta (0.001), the same gate twp applies to first tokens —
deliberately, so "noise" here means exactly what twp already calls too-small-to-
resolve, rather than a threshold invented for this measurement.

**Reported mass-weighted, not per word.** A per-word mean would be dominated by
the thousands of near-zero words, which is the wrong question: what matters is
the share of the mass a consumer actually reads.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RESULTS = os.path.join(HERE, "results")
sys.path.insert(0, ROOT)

import numpy as np                                    # noqa: E402
import torch                                          # noqa: E402
from malignment import ch, runners, twp as T          # noqa: E402
from malignment.checkpoint import Checkpoint          # noqa: E402

FLOOR = T.THETA


def cell(mid, model, tok, prompt, dev, bmask, cjk):
    """Mirror `expand`'s beam, decomposing each word's `term` as it is emitted."""
    pids, _rs, _rid = T._prompt_ids(tok, prompt, T.bos_policy_for(mid))
    with torch.no_grad():
        lg = model(torch.tensor([pids], device=dev)).logits[0, -1, :].float()
    P0 = torch.softmax(lg, -1).cpu().numpy()
    del lg
    sel = np.flatnonzero(P0 >= T.THETA)
    live = [((int(t),), float(P0[t]), int(t)) for t in sel]
    out, bcache, intra = [], {}, {}
    for _ in range(T.MAX_DEPTH):
        if not live:
            break
        with torch.no_grad():
            dist = T.next_dist(model, tok, pids, [p for p, _, _ in live], dev)
        nxt = []
        for (pref, mass, t1), row in zip(live, dist):
            surf = T.clean_surface(tok.decode(list(pref)).strip())
            b = T._boundary_for(surf, bmask, cjk, bcache, intra)
            if surf and not T.is_mojibake(surf):
                bm = row[b]
                top = float(bm[bm >= FLOOR].sum())
                tot = float(bm.sum())
                out.append({"word": surf, "depth": len(pref), "mass": float(mass),
                            "term": tot, "term_top": top, "term_tail": tot - top,
                            "n_tail": int((bm < FLOOR).sum()),
                            "n_boundary": int(b.sum()), "p": float(mass) * tot})
            cont = np.flatnonzero(~b)
            m2 = mass * row[cont]
            keep = m2 >= T.THETA
            for t, mm in zip(cont[keep], m2[keep]):
                nxt.append(((*pref, int(t)), float(mm), t1))
        live = nxt
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="gl198976/mpt-7b,HuggingFaceTB/SmolLM3-3B-Base")
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    prompts = [r["prompt"] for r in ch.query("""
        WITH enp AS (SELECT prompt FROM twp_cells GROUP BY prompt
                     HAVING uniqExact(model) >= 400)
        SELECT p.prompt AS prompt FROM prompts p INNER JOIN enp USING (prompt)
        WHERE p.language='en' ORDER BY cityHash64(p.prompt) LIMIT %d""" % a.n,
        limit_bytes=None)]
    print("prompts: %d" % len(prompts), flush=True)

    allrows = {}
    for mid in a.models.split(","):
        print("\n=== %s" % mid, flush=True)
        model, tok, dev, bmask, cjk = runners.load_for_twp(Checkpoint(mid))[:5]
        rows = []
        for i, pr in enumerate(prompts, 1):
            try:
                rows.extend(cell(mid, model, tok, pr, dev, bmask, cjk))
            except T.SkipPrompt as e:
                print("   skip %d: %s" % (i, str(e)[:50]), flush=True)
            if i % 5 == 0:
                print("   %d/%d prompts, %d words" % (i, len(prompts), len(rows)), flush=True)
        allrows[mid] = rows
        report(mid, rows)
        T.free(model)
        T.purge_model(mid, enabled=False)

    if a.write:
        os.makedirs(RESULTS, exist_ok=True)
        p = os.path.join(RESULTS, "term_noise.json")
        json.dump({"floor": FLOOR, "n_prompts": len(prompts),
                   "models": {k: summarise(v) for k, v in allrows.items()}},
                  open(p, "w"), indent=1)
        print("\nwrote %s" % p)
    return 0


def summarise(rows):
    P = sum(r["p"] for r in rows) or 1.0
    #: **MASS-WEIGHTED.** The share of the probability a consumer reads that is
    #: contributed by sub-floor boundary tokens, not the share of words.
    tail_share = sum(r["mass"] * r["term_tail"] for r in rows) / P
    return {"n_words": len(rows), "total_p": P,
            "mass_weighted_tail_share": tail_share,
            "median_term": float(np.median([r["term"] for r in rows])),
            "median_tail_frac": float(np.median(
                [r["term_tail"] / r["term"] for r in rows if r["term"] > 0])),
            "mean_n_tail": float(np.mean([r["n_tail"] for r in rows])),
            "mean_n_boundary": float(np.mean([r["n_boundary"] for r in rows]))}


def report(mid, rows):
    s = summarise(rows)
    print("\n  %s   %d words" % (mid, s["n_words"]))
    print("    MASS-WEIGHTED share of p from sub-%.3f boundary tokens: %.1f%%"
          % (FLOOR, 100 * s["mass_weighted_tail_share"]))
    print("    median term %.4f | median tail fraction of term %.1f%%"
          % (s["median_term"], 100 * s["median_tail_frac"]))
    print("    boundary tokens per word %.0f, of which sub-floor %.0f"
          % (s["mean_n_boundary"], s["mean_n_tail"]))
    #: The comparison the whole question turns on: the top of the distribution
    #: is what any result rests on, the bottom is where fragments live.
    rows = sorted(rows, key=lambda r: -r["p"])
    for lab, sub in (("top 20 words by p", rows[:20]),
                     ("bottom 20% by p", rows[int(0.8 * len(rows)):])):
        if not sub:
            continue
        f = [r["term_tail"] / r["term"] for r in sub if r["term"] > 0]
        print("    %-18s tail fraction of term: median %.1f%%"
              % (lab, 100 * float(np.median(f))))
    for r in rows[:5]:
        print("       %-16s p=%.5f term=%.4f tail=%.1f%% of term"
              % (r["word"][:16], r["p"], r["term"], 100 * r["term_tail"] / r["term"]))


if __name__ == "__main__":
    sys.exit(main())
