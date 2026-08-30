"""Does alignment change the representation or the readout? The 2x2, at every layer.

    .venv/bin/python -u run.py                    every pair with both arms archived
    .venv/bin/python -u run.py --pairs meta-llama/Llama-3.1-8B
    .venv/bin/python -u run.py --top 12 --floor 0.20

Four combinations of a state and a readout, at every layer of every pair:

    h_base    x readout_base      the base model
    h_base    x readout_aligned   base state, aligned readout
    h_aligned x readout_base      aligned state, base readout
    h_aligned x readout_aligned   the aligned model

`readout` is the final norm AND the unembedding. They are also swapped
separately (`T_bw`, `T_bn`) so the unembedding's contribution can be told apart
from the normalisation's.

WRITES
    results/by_pair.csv         one row per pair: shares, dW, onset
    results/by_pair_band.csv    one row per (pair, dose band) -- THE GRAIN TO
                                READ, because pooling charged frames with
                                uncharged ones dilutes every effect
    results/by_pair_layer.csv   one row per (pair, prompt, layer): all four
                                combinations plus coverage on both arms
    population.json             the pairs, prompts, words and sidecar bytes used
"""

import argparse
import collections
import csv
import hashlib
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

from malignment import charge, lens, roster  # noqa: E402
from malignment.checkpoint import Checkpoint  # noqa: E402

RESULTS = os.path.join(HERE, "results")

#: **THE LAYER GRAIN DOES NOT GO IN GIT.** 40 pairs x 611 prompts x ~40 layers is
#: 123MB, and the repo's size guard refuses it -- correctly: it is derived, it is
#: regenerable from this script plus the frozen prompt list, and a large blob can
#: only be removed from history by rewriting it. It goes where the states and
#: generations already live, and `by_pair.csv` carries its sha so a reader can
#: tell which run a local copy belongs to.
BIG = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                  os.path.expanduser("~/malignment-data")),
                   "readout_share")

#: the depths reported in the README's tables. Dense at the top because that is
#: the only region where the lens has mass to read -- see FLOOR.
FRACTIONS = (0.0, 0.25, 0.5, 0.75, 0.875, 0.9375, 1.0)

#: **A LAYER BELOW THIS COVERAGE IS NOT ELIGIBLE TO BE AN ONSET.** The target
#: words hold ~0 of the distribution below three-quarters depth on every model
#: measured, so "the gap reached half its final value" is satisfied there by the
#: ratio of two vanishing numbers. Without the floor, Llama-3.1-8B onsets at 0.20
#: of the stack; with it, at 0.92, which is F05's SFT figure.
FLOOR = 0.20

#: below this the pair's final-layer coverage is too low to read at all.
MIN_COVERAGE = 0.30

#: **A POOLED EFFECT OVER ALL PROMPTS IS MOSTLY A STATEMENT ABOUT UNCHARGED
#: ONES.** Of the 59 rated prompts in the sidecars, the median dose is 2.11 and
#: only ~13 sit above 3.45; averaging the charged with the uncharged shrank every
#: pair's effect three- to fivefold and dropped five of seven below the gates.
#: Fixed cuts, so a band means the same thing in every pair.
BANDS = ((1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 7.0))

#: **AND A MAGNITUDE FLOOR DOES NOT PROTECT A RATIO.** `BAAI/Aquila2-7B` clears
#: MIN_FULL at -0.180 and still reports a readout share of -410%, because its
#: readout swap runs the OPPOSITE way to its full effect. A denominator large
#: enough to divide by says nothing about whether the numerator belongs to the
#: same phenomenon: a component pointing against the effect it is meant to
#: apportion is not a share of it, at any denominator. So a share is reported
#: only where the component and the full effect agree in sign, and the component
#: is still printed as a difference either way.
#:
#: **A SHARE OF A NEAR-ZERO EFFECT IS NOT A QUANTITY.** glm-4-9b-hf's full effect
#: is -0.033 and its readout swap is -0.355, which divides out to a readout share
#: of 1086%; granite's +0.073 gives 355%. Both are arithmetically correct and
#: neither is a fact about the model. A pair is eligible for a SHARE only if its
#: full effect is displacement of at least this size in the expected direction --
#: the components are still reported for every pair, as differences.
MIN_FULL = 0.15

#: **THE SHAPE GATE, FROM H1.** A swapped readout is out of distribution for the
#: other arm's residual stream, and the failure mode is a distribution of the
#: wrong shape rather than an error. H1 excluded a pair whose cross-read was 5x
#: sharper than its native read while keeping one that passed, so a swap reported
#: without this number has an untested premise. Native perplexity over cross
#: perplexity, worst of the two directions; 1.0 is identical shape.
MAX_PPL_RATIO = 2.0


def onset(gap, cov, floor):
    """F05's shape: the first ELIGIBLE layer with the final sign and >=50% of the
    final gap, as a fraction of depth. None when there is no final gap to halve."""
    fin = gap[-1]
    if fin != fin or abs(fin) < 0.05:
        return None
    n = len(gap)
    for i in range(n):
        if cov[i] < floor or gap[i] != gap[i]:
            continue
        if gap[i] * fin > 0 and abs(gap[i]) >= 0.5 * abs(fin):
            return i / (n - 1)
    return 1.0


def common_vocab(pairs, AutoTokenizer, store="live"):
    """{prompt: set(words)} single-token in EVERY pair's tokenizer, on prompts
    every pair holds.

    **CROSS-MODEL SHARES ARE OTHERWISE COMPUTED OVER DIFFERENT POPULATIONS.** A
    word is kept per model when that model spells it as one token after that
    prompt, so Llama keeps `strangle` and CroissantLLM does not -- and the
    dropped words are not a random 3%. Measured over 12,263 rated cells, words a
    tokenizer splits average 0.47-0.82 HIGHER on scene than words it does not,
    in all six tokenizers tested, and only 40% of scene>=6 cells survive the
    intersection against 58% of cells overall. The exclusion selects against the
    sharp tail, which is the tail the measure exists to see.

    Within a pair this cancels -- both arms share a tokenizer, so all four cells
    of the swap use one word set. It is the CROSS-PAIR ranking that is exposed,
    and that ranking is where the Llama result lives.
    """
    toks = {}
    for b, _ in pairs:
        try:
            from malignment import twp as _twp
            toks[b] = _twp.load_tokenizer(b, revision=Checkpoint(b).revision)[0]
        except Exception:
            pass
    plists = []
    for b, _ in pairs:
        try:
            _, pl = lens.hidden(b, store=store)
            plists.append(set(pl))
        except Exception:
            pass
    shared = set.intersection(*plists) if plists else set()
    out = {}
    for p in shared:
        sc = charge.scene(p)
        if not sc:
            continue
        keep = None
        for b, tk in toks.items():
            _, k = lens.single_token(sc, tk, prompt=p)
            keep = set(k) if keep is None else (keep & set(k))
        if keep:
            out[p] = keep
    return out


def pair(base, aligned, top, floor, torch, AutoTokenizer, device="cpu",
         verify=False, common=None, store="live"):
    """One pair's cells, or None with a reason."""
    HB, pl = lens.hidden(base, store=store)
    HA, pla = lens.hidden(aligned, store=store)
    if pl != pla:
        return None, "prompt lists differ"
    WB, nwB, nbB, usedB, cB = lens.head(base)
    WA, nwA, nbA, usedA, cA = lens.head(aligned)
    if WB.shape != WA.shape:
        if WB.shape[1] != WA.shape[1]:
            return None, "d_model differs %d vs %d" % (WB.shape[1], WA.shape[1])
        #: CroissantLLM's aligned arm appends two tokens to the END of the
        #: vocabulary. Rows 0..31999 are the same tokenizer, so truncating to the
        #: common prefix swaps over identical ids -- but ONLY because the added
        #: ids are the trailing ones, and `single_token(vocab=)` then drops any
        #: target at or above the cut rather than silently misindexing it.
        n = min(WB.shape[0], WA.shape[0])
        WB, WA = WB[:n], WA[:n]
    vocab = WB.shape[0]
    gm = lens.is_gemma(base)
    #: **THE TOKENIZER TAKES THE PIN TOO, OR THE PIN MAKES THINGS WORSE.**
    #: `lens.head` resolves BAAI/Aquila2-7B to its pinned revision, vocab
    #: 100,008; a bare `AutoTokenizer.from_pretrained` returns main's RE-TOKENISED
    #: 143,973. Pinning the weights and not the tokenizer indexes ids up to
    #: 143,972 into a 100,008-row unembedding -- which produced `nan`, not an
    #: error. twp.load_tokenizer says exactly this and I read past it.
    from malignment import twp as _twp
    tok, _loader = _twp.load_tokenizer(base, revision=Checkpoint(base).revision)
    #: every prompt in this sidecar that carries ratings. `top=0` means all of
    #: them, which is the default: the sidecars hold 115 prompts, 59 are rated,
    #: and there is no cost to using all 59 beyond compute.
    rated = [p for p in pl if charge.dose(p) is not None]
    #: **TOP-N BY DOSE SELECTS INTO THE SATURATED REGION** -- the highest-dose
    #: frames show essentially no response. When a subset IS wanted, it is a
    #: stratified draw across dose bands, not a head.
    if common is not None:
        rated = [p for p in rated if p in common]
    pick = charge.sample(top, strata=5, among=rated) if top else rated
    R = {p: charge.scene(p) for p in pick}
    if common is not None:
        R = {p: {w: v for w, v in R[p].items() if w in common[p]} for p in pick}
    dose = {p: charge.dose(p) for p in pick}

    #: **BUILT ONCE PER PAIR, NOT ONCE PER PROMPT.** Each `Readout` casts the
    #: unembedding to float32 -- 3.7GB for gemma -- so constructing them inside
    #: the prompt loop is the whole cost of the run.
    mk = lambda W, nw, nb, cfg: lens.Readout(  # noqa: E731
        W, nw, nb, cfg, gemma=gm, device=device, torch=torch)
    RB = mk(WB, nwB, nbB, cB)
    RA = mk(WA, nwA, nbA, cA)
    #: bw = base norm, ALIGNED unembedding. bn = ALIGNED norm, base unembedding.
    BW = mk(WA, nwB, nbB, cA)
    BN = mk(WB, nwA, nbA, cB)

    cells = []
    for p in pick:
        i = pl.index(p)
        ids, keep = lens.single_token(R[p], tok, prompt=p, vocab=vocab)
        if len(keep) < 8:
            continue
        #: a token id at or above the unembedding's rows cannot be scored, and
        #: indexing one yields nan rather than raising. `single_token(vocab=)`
        #: already drops them; this asserts it held, because the failure it
        #: guards against is silent and was live for two runs.
        assert not ids or max(ids) < vocab, (
            "%s: token id %d >= vocab %d -- tokenizer and unembedding disagree"
            % (base, max(ids), vocab))
        wt = torch.tensor([R[p][w] for w in keep])
        hb = torch.from_numpy(HB[i])
        ha = torch.from_numpy(HA[i])

        last = {}

        def T(h, rd, stash=None):
            P = rd.probs(h, ids)
            s = P.sum(-1)
            #: **NORMALISING BY THE COVERED MASS IS WHAT MAKES THIS COMPARABLE.**
            #: An unnormalised sum falls whenever the distribution concentrates
            #: anywhere else, so it would read every sharpening as displacement.
            v = (P * wt).sum(-1) / s
            if stash is not None:
                last[stash] = {w: float(P[-1][j]) for j, w in enumerate(keep)}
            return [float(x) for x in v], [float(x) for x in s]

        t_bb, cov_b = T(hb, RB, stash="bb")
        t_ba, _ = T(hb, RA)
        t_ab, _ = T(ha, RB)
        t_aa, cov_a = T(ha, RA)
        t_bw, _ = T(hb, BW)
        t_bn, _ = T(hb, BN)
        #: **TWO IMPLEMENTATIONS OF ONE QUANTITY IS THE DEFECT, NOT THE CHECK.**
        #: The loop above computes T over a tensor for speed; `charge.T` is the
        #: definition other seats will call. They must agree, so the first cell
        #: of every pair is computed both ways and the run stops if they do not.
        if not cells:
            ref, _ = charge.T(R[p], last["bb"])
            if abs(ref - t_bb[-1]) > 1e-4:
                raise AssertionError(
                    "%s: tensor T %.6f != charge.T %.6f on %r"
                    % (base, t_bb[-1], ref, p[:40]))
            #: **A DEVICE IS A JOINT LIKE ANY OTHER.** This repo has a recorded
            #: case of MPS silently corrupting a different computation, so an
            #: accelerated run is checked against CPU on real weights rather
            #: than assumed equivalent because the arithmetic "should" match.
            if verify and device != "cpu":
                cpu_rb = lens.Readout(WB, nwB, nbB, cB, gemma=gm,
                                      device="cpu", torch=torch)
                Pc = cpu_rb.probs(hb, ids)
                vc = float((Pc[-1] * wt).sum() / Pc[-1].sum())
                if abs(vc - t_bb[-1]) > 1e-4:
                    raise AssertionError(
                        "%s: %s T %.6f != cpu T %.6f on %r"
                        % (base, device, t_bb[-1], vc, p[:40]))
                print("     device check: %s %.6f vs cpu %.6f  (diff %.2e)"
                      % (device, t_bb[-1], vc, abs(vc - t_bb[-1])), flush=True)
        #: **THE GATE H1 APPLIED AND THIS RUN DID NOT.** A swapped readout is out
        #: of distribution for the other arm's stack, so the decomposition is
        #: only interpretable while the cross-read keeps roughly the SHAPE of the
        #: native one. H1 excluded Amber because its cross-read came out 5x
        #: sharper. `ppl_ratio` is native perplexity over cross perplexity: 1.0
        #: is identical shape, >1 means the swapped head is sharper.
        e_bb, top_bb, _ = RB.shape_at(hb)
        e_ba, top_ba, _ = RA.shape_at(hb)
        e_aa, top_aa, _ = RA.shape_at(ha)
        e_ab, top_ab, _ = RB.shape_at(ha)
        cells.append(dict(prompt=p, dose=dose[p], n_words=len(keep),
                          n_layers=len(t_bb) - 1, words=keep,
                          T_bb=t_bb, T_ba=t_ba, T_ab=t_ab, T_aa=t_aa,
                          T_bw=t_bw, T_bn=t_bn, cov_b=cov_b, cov_a=cov_a,
                          ent_bb=e_bb, ent_ba=e_ba, ent_aa=e_aa, ent_ab=e_ab,
                          ppl_ratio_b=2.0 ** (e_bb - e_ba),
                          ppl_ratio_a=2.0 ** (e_aa - e_ab),
                          top1_same_b=int(top_bb == top_ba),
                          top1_same_a=int(top_aa == top_ab)))
    if not cells:
        return None, "no cell reached 8 single-token rated words"
    dW = float((WA.float() - WB.float()).abs().mean()
               / WB.float().abs().mean())
    return dict(base=base, aligned=aligned, unembed=usedB, vocab=vocab,
                d_model=int(WB.shape[1]), dW=dW, cells=cells,
                cap=cB.get("final_logit_softcapping"),
                scale=cB.get("logits_scaling")), None


def summarise(r, floor):
    """One pair's row: the shares at the output, and the onset of the full effect."""
    last = lambda k: st.mean([c[k][-1] for c in r["cells"]])  # noqa: E731
    full = last("T_aa") - last("T_bb")
    ons = [o for c in r["cells"]
           if (o := onset([c["T_aa"][i] - c["T_bb"][i] for i in range(len(c["T_bb"]))],
                          c["cov_b"], floor)) is not None]
    cov = st.median([c["cov_b"][-1] for c in r["cells"]])
    #: a share is reported only where there is displacement to apportion AND the
    #: lens can read the output. Both gates are recorded, not just their product,
    #: so a reader can see which one excluded a pair.
    #: the shape gate, at the grain the swap is read: the base-stack cross-read
    #: is the one the READOUT share rests on, so it is the one that gates it.
    ppl_b = st.median([c["ppl_ratio_b"] for c in r["cells"]])
    ppl_a = st.median([c["ppl_ratio_a"] for c in r["cells"]])
    worst = max(max(ppl_b, 1 / ppl_b), max(ppl_a, 1 / ppl_a))
    in_dist = worst <= MAX_PPL_RATIO
    readable = cov > MIN_COVERAGE and full <= -MIN_FULL
    return dict(
        base=r["base"], aligned=r["aligned"], n_cells=len(r["cells"]),
        n_layers=r["cells"][0]["n_layers"], coverage=cov,
        dW=r["dW"], full=full,
        readout=last("T_ba") - last("T_bb"),
        state=last("T_ab") - last("T_bb"),
        unembed_only=last("T_bw") - last("T_bb"),
        norm_only=last("T_bn") - last("T_bb"),
        ppl_ratio_b=ppl_b, ppl_ratio_a=ppl_a, shape_ok=int(in_dist),
        top1_same_b=st.mean([c["top1_same_b"] for c in r["cells"]]),
        top1_same_a=st.mean([c["top1_same_a"] for c in r["cells"]]),
        share_readable=int(readable),
        #: sign-agreement is per COMPONENT: a pair can have an apportionable
        #: state term and an uninterpretable readout term, and collapsing that to
        #: one flag would discard the readable half.
        readout_share=((last("T_ba") - last("T_bb")) / full
                       if readable and (last("T_ba") - last("T_bb")) < 0
                       else float("nan")),
        state_share=((last("T_ab") - last("T_bb")) / full
                     if readable and (last("T_ab") - last("T_bb")) < 0
                     else float("nan")),
        onset=st.median(ons) if ons else float("nan"), n_onset=len(ons))


def main(argv=None):
    import torch
    from transformers import AutoTokenizer
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="*", help="base ids; default every archived pair")
    ap.add_argument("--top", type=int, default=0,
                    help="0 = every rated prompt in the sidecar; N = a "
                         "dose-stratified draw of N")
    ap.add_argument("--floor", type=float, default=FLOOR, help="onset coverage floor")
    #: CPU is the default and is already fast enough (~1 min/pair). MPS is ~2.7x
    #: faster and agrees to 1.2e-06 on probabilities, but this repo has a
    #: recorded case of MPS corrupting a different computation, so it is opt-in
    #: and `--verify-device` re-runs the first cell on CPU before trusting it.
    ap.add_argument("--device", default="cpu", choices=("cpu", "mps"))
    #: **NEVER BOTH STORES IN ONE RUN.** The live store is 611 frozen prompts;
    #: the archive is the f11 contradiction set at 115, 62, 60 and 33 depending
    #: on the pair. A run spanning them would put pairs measured on different
    #: populations in one table, which is the defect the frozen list exists to
    #: prevent and would be invisible in the output.
    ap.add_argument("--store", default="live", choices=("live", "archive"))
    ap.add_argument("--common", action="store_true",
                    help="restrict to words single-token in EVERY pair's "
                         "tokenizer, on prompts every pair holds -- the only "
                         "footing on which cross-pair shares compare")
    ap.add_argument("--verify-device", action="store_true",
                    help="recompute the first pair's final-layer T on CPU and "
                         "abort if it disagrees by more than 1e-4")
    a = ap.parse_args(argv)

    man = lens.manifest(a.store)
    eps, _ = roster.endpoints()
    todo = a.pairs or [b for b in sorted(eps) if b in man and eps[b] in man]
    print("store=%s | pairs with both arms present: %d" % (a.store, len(todo)))
    common = None
    if a.common:
        common = common_vocab([(b, eps[b]) for b in todo], AutoTokenizer,
                              store=a.store)
        nw = sum(len(v) for v in common.values())
        print("COMMON VOCABULARY: %d prompts, %d word-cells single-token in all "
              "%d tokenizers" % (len(common), nw, len(todo)))

    out, skipped = [], []
    for b in todo:
        try:
            r, why = pair(b, eps[b], a.top, a.floor, torch, AutoTokenizer,
                          device=a.device, verify=a.verify_device,
                          common=common, store=a.store)
        except Exception as e:
            r, why = None, "%s: %s" % (type(e).__name__, str(e)[:60])
        if r is None:
            skipped.append((b, why))
            print("  %-24s SKIPPED %s" % (b.split("/")[-1][:24], why), flush=True)
            continue
        s = summarise(r, a.floor)
        out.append((r, s))
        pct = lambda k: ("%3.0f%%" % (100 * s[k])) if s[k] == s[k] else "  --"  # noqa: E731
        print("  %-24s cov %.2f | dW %.3f | full %+.3f | readout %+.3f (%s) | "
              "state %+.3f (%s) | onset %.2f | ppl %.2f/%.2f %s"
              % (b.split("/")[-1][:24], s["coverage"], s["dW"], s["full"],
                 s["readout"], pct("readout_share"),
                 s["state"], pct("state_share"), s["onset"],
                 s["ppl_ratio_b"], s["ppl_ratio_a"],
                 "OK " if s["shape_ok"] else "OUT-OF-DIST"), flush=True)

    os.makedirs(RESULTS, exist_ok=True)
    cols = list(out[0][1]) if out else []
    with open(os.path.join(RESULTS, "by_pair.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for _, s in out:
            w.writerow(s)
    with open(os.path.join(RESULTS, "by_pair_band.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["base", "aligned", "dose_lo", "dose_hi", "n_prompts",
                    "coverage", "full", "readout", "state",
                    "readout_share", "state_share"])
        for r, _ in out:
            for lo, hi in BANDS:
                cs = [c for c in r["cells"] if lo <= c["dose"] < hi]
                if not cs:
                    continue
                m = lambda k: st.mean([c[k][-1] for c in cs])  # noqa: E731
                full = m("T_aa") - m("T_bb")
                rd, sta = m("T_ba") - m("T_bb"), m("T_ab") - m("T_bb")
                ok_ = full <= -MIN_FULL and rd < 0
                w.writerow([r["base"], r["aligned"], lo, hi, len(cs),
                            "%.4f" % st.median([c["cov_b"][-1] for c in cs]),
                            "%.4f" % full, "%.4f" % rd, "%.4f" % sta]
                           + (["%.4f" % (rd / full), "%.4f" % (sta / full)]
                              if ok_ else ["", ""]))
    os.makedirs(BIG, exist_ok=True)
    with open(os.path.join(BIG, "by_pair_layer.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["base", "aligned", "prompt", "dose", "n_words", "layer",
                    "frac", "T_bb", "T_ba", "T_ab", "T_aa", "T_bw", "T_bn",
                    "cov_b", "cov_a"])
        for r, _ in out:
            for c in r["cells"]:
                n = c["n_layers"]
                for L in range(n + 1):
                    w.writerow([r["base"], r["aligned"], c["prompt"],
                                "%.4f" % c["dose"], c["n_words"], L,
                                "%.4f" % (L / n)]
                               + ["%.6f" % c[k][L] for k in
                                  ("T_bb", "T_ba", "T_ab", "T_aa", "T_bw",
                                   "T_bn", "cov_b", "cov_a")])

    #: the receipt. Sidecar bytes are hashed because the archive repo is
    #: read-only but not immutable, and a rerun that silently reads different
    #: states would otherwise be indistinguishable from one that did not.
    man_path = os.path.join(lens.ARCHIVE, "hidden_manifest.json")
    ix = charge.index()
    pop = dict(
        floor=a.floor, top=a.top, device=a.device, store=a.store,
        charge=ix["source"], charge_sha=ix["source_sha"],
        instrument_sha=ix["instrument_sha"],
        manifest_sha=hashlib.sha256(open(man_path, "rb").read()).hexdigest()[:16],
        archive=lens.ARCHIVE, prompts_sha=ix["source_sha"],
        skipped=[dict(base=b, why=w) for b, w in skipped],
        pairs=[dict(base=r["base"], aligned=r["aligned"], unembed=r["unembed"],
                    vocab=r["vocab"], d_model=r["d_model"], dW=r["dW"],
                    n_layers=r["cells"][0]["n_layers"], cap=r["cap"],
                    scale=r["scale"],
                    #: counts and a digest, not the word lists themselves --
                    #: embedding them made this receipt 21MB, which is a data
                    #: file wearing a receipt's name. The digest still pins
                    #: exactly which words were scored.
                    n_prompts=len(r["cells"]),
                    words_sha=hashlib.sha256(
                        "\x00".join("%s|%s" % (c["prompt"], ",".join(c["words"]))
                                    for c in r["cells"]).encode()
                    ).hexdigest()[:16],
                    #: NOT the prompt strings. The frozen list is one shared
                    #: population by construction, so repeating it per pair is
                    #: the same 611 strings 40 times; `prompts_sha` at the top
                    #: level pins it, and a pair that used a SUBSET is caught by
                    #: n_prompts differing.
                    dose_range=[round(min(c["dose"] for c in r["cells"]), 3),
                                round(max(c["dose"] for c in r["cells"]), 3)],
                    n_words_median=sorted(c["n_words"] for c in r["cells"])[
                        len(r["cells"]) // 2])
               for r, _ in out])
    json.dump(pop, open(os.path.join(HERE, "population.json"), "w"), indent=1)

    ok = [(r, s) for r, s in out if s["coverage"] > MIN_COVERAGE]
    if not ok:
        return
    sh = [(r, s) for r, s in out if s["share_readable"]]
    if sh:
        #: **TWO AGGREGATES, BOTH REPORTED, BECAUSE PICKING ONE IS A CHOICE.**
        #: The pooled share weights by effect size, so recurrentgemma's -1.32
        #: dominates; the median treats each pair as one observation, so
        #: Llama's outlying 88% cannot carry it. They answer different
        #: questions and here they agree, which is worth being able to see.
        print("\nACROSS %d PAIRS WITH DISPLACEMENT TO APPORTION "
              "(coverage > %.2f, full <= -%.2f)" % (len(sh), MIN_COVERAGE, MIN_FULL))
        tot = sum(s["full"] for _, s in sh)
        print("  summed full effect     %+.3f" % tot)
        for k, lab in (("readout", "readout swap"), ("state", "state swap"),
                       ("unembed_only", "unembedding only"),
                       ("norm_only", "final norm only")):
            v = sum(s[k] for _, s in sh)
            print("  %-22s %+.3f  pooled %3.0f%%   median per pair %3.0f%%"
                  % (lab, v, 100 * v / tot,
                     100 * st.median([s[k] / s["full"] for _, s in sh])))

    hdr = "  ".join("%6s" % ("%.2f" % f) for f in FRACTIONS)
    for k, lab in (("T_aa", "FULL EFFECT (each arm, own readout)"),
                   ("T_ba", "READOUT SWAP (base state, aligned readout)"),
                   ("T_ab", "STATE SWAP (aligned state, base readout)")):
        print("\n%s BY DEPTH" % lab)
        print("  %-22s %s" % ("pair", hdr))
        for r, _ in ok:
            n = r["cells"][0]["n_layers"]
            row = []
            for fr in FRACTIONS:
                i = min(n, int(round(fr * n)))
                v = [c[k][i] - c["T_bb"][i] for c in r["cells"]
                     if c[k][i] == c[k][i] and c["T_bb"][i] == c["T_bb"][i]]
                row.append(st.mean(v) if v else float("nan"))
            print("  %-22s %s" % (r["base"].split("/")[-1][:22],
                                  "  ".join("%+6.2f" % v for v in row)))

    print("\nTARGET-WORD COVERAGE BY DEPTH (base arm)")
    print("  %-22s %s" % ("pair", hdr))
    for r, _ in ok:
        n = r["cells"][0]["n_layers"]
        row = [st.mean([c["cov_b"][min(n, int(round(fr * n)))] for c in r["cells"]])
               for fr in FRACTIONS]
        print("  %-22s %s" % (r["base"].split("/")[-1][:22],
                              "  ".join("%6.3f" % v for v in row)))

    #: **THE REGRESSION IS THE HEADLINE, NOT THE RATIO.** A per-pair share needs
    #: each pair to clear a floor on its own denominator and is undefined where
    #: the two components oppose; a slope across pairs needs neither. And the
    #: SIMPLE slopes are suppressed -- the components correlate about -0.7, so
    #: each masks the other when the other is omitted, which made the readout
    #: look inert at slope +0.011 when its joint coefficient is +0.59.
    if len(ok) >= 5:
        Y = [s2["full"] for _, s2 in ok]
        RD = [s2["readout"] for _, s2 in ok]
        ST = [s2["state"] for _, s2 in ok]

        def ols(y, xs):
            n, k = len(y), len(xs)
            X = [[1.0] + [x[i] for x in xs] for i in range(n)]
            A = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(k + 1)]
                 + [sum(X[r][i] * y[r] for r in range(n))] for i in range(k + 1)]
            for i in range(k + 1):
                pv = max(range(i, k + 1), key=lambda r: abs(A[r][i]))
                A[i], A[pv] = A[pv], A[i]
                for r in range(k + 1):
                    if r != i and A[i][i]:
                        f = A[r][i] / A[i][i]
                        for cc in range(i, k + 2):
                            A[r][cc] -= f * A[i][cc]
            b = [A[i][k + 1] / A[i][i] if A[i][i] else 0.0 for i in range(k + 1)]
            yh = [sum(b[j] * X[r][j] for j in range(k + 1)) for r in range(n)]
            my = st.mean(y)
            ss = sum((v - my) ** 2 for v in y)
            rs = sum((y[r] - yh[r]) ** 2 for r in range(n))
            return b, (1 - rs / ss if ss else 0.0)

        print("\nCONTRIBUTION ACROSS %d PAIRS (regression, not a per-pair ratio)" % len(ok))
        b, r2 = ols(Y, [RD])
        print("  full ~ readout           %+.3f            R2 %.3f   <- SUPPRESSED" % (b[1], r2))
        b, r2 = ols(Y, [ST])
        print("  full ~ state                      %+.3f   R2 %.3f   <- SUPPRESSED" % (b[1], r2))
        b, r2 = ols(Y, [RD, ST])
        print("  full ~ readout + state   %+.3f   %+.3f   R2 %.3f" % (b[1], b[2], r2))
        mr, ms_ = st.mean(RD), st.mean(ST)
        num = sum((a - mr) * (c - ms_) for a, c in zip(RD, ST))
        den = (sum((a - mr) ** 2 for a in RD) * sum((c - ms_) ** 2 for c in ST)) ** 0.5
        print("  corr(readout, state)     %+.3f   -- why the simple slopes mislead"
              % (num / den if den else 0.0))
        opp = sum(1 for a, c in zip(RD, ST) if (a < 0) != (c < 0))
        print("  components OPPOSE in %d of %d pairs; a share is not defined there"
              % (opp, len(ok)))

    print("\nFULL EFFECT AND READOUT SHARE BY DOSE BAND")
    print("  a pooled figure over all 59 prompts is mostly a statement about the")
    print("  46 uncharged ones; the effect lives in the top band.")
    print("  %-22s %s" % ("pair", "  ".join("%14s" % ("dose %.0f-%.0f" % b)
                                            for b in BANDS)))
    for r, _ in ok:
        row = []
        for lo, hi in BANDS:
            cs = [c for c in r["cells"] if lo <= c["dose"] < hi]
            if not cs:
                row.append("%14s" % "-")
                continue
            m = lambda k: st.mean([c[k][-1] for c in cs])  # noqa: E731
            full = m("T_aa") - m("T_bb")
            sh = ("%3.0f%%" % (100 * (m("T_ba") - m("T_bb")) / full)
                  if full <= -MIN_FULL else "  --")
            row.append("%14s" % ("%+.2f n=%-2d %s" % (full, len(cs), sh)))
        print("  %-22s %s" % (r["base"].split("/")[-1][:22], "  ".join(row)))

    print("\nONSET OF THE FULL EFFECT, BY COVERAGE FLOOR")
    print("  %-22s %s" % ("pair", "  ".join("%6s" % ("%.2f" % f)
                                            for f in (0.0, 0.05, 0.10, 0.20))))
    for r, _ in ok:
        row = []
        for fl in (0.0, 0.05, 0.10, 0.20):
            v = [o for c in r["cells"]
                 if (o := onset([c["T_aa"][i] - c["T_bb"][i]
                                 for i in range(len(c["T_bb"]))],
                                c["cov_b"], fl)) is not None]
            row.append("%.2f" % st.median(v) if v else "  -")
        print("  %-22s %s" % (r["base"].split("/")[-1][:22],
                              "  ".join("%6s" % x for x in row)))
    print("\n  F05 for comparison: SFT 0.92, DPO 0.96, RLVR 0.98")
    print("\n-> results/by_pair.csv, results/by_pair_band.csv, population.json")
    print("-> %s/by_pair_layer.csv  (derived, not in git)" % BIG)


if __name__ == "__main__":
    main()
