#!/usr/bin/env python
"""displacement_reference — how far training moves a model, per phase, per token.

    python .../displacement_reference/run.py            # the OLMo phase profile
    python .../displacement_reference/run.py --write

## THE QUESTION, AND THE ONE IT REPLACED

*"Is a JS of 0.10 a lot?"* has no answer without a comparator, and this
directory first used the wrong one: the distance between two INDEPENDENTLY
PRETRAINED models. RH: *"why would we expect alignment to have a stronger effect
than all the many differences between separately pretrained models?"* We would
not. Two models differing in corpus, tokenizer, architecture and scale should
differ enormously; a light post-training pass on a fixed base reaching 82% of
that gap is not alignment being modest -- it is alignment doing a startling
amount for its compute. **The number was anchored to nothing and I read it in
whichever direction sounded sober, twice, in opposite directions.**

A reference means something only if it is a comparison someone would have made
anyway, and nobody was ever going to ask whether alignment exceeds the
Llama-Qwen gap.

The comparator that survives is the model's OWN TRAINING HISTORY: same lab, same
weights, same tokenizer, same prompts. **OLMo 3 is the only family that admits
it**, because it released ladders on both sides. Pythia has 154 pretraining
rungs and ZERO post-training rungs, so it offers only an endpoint against a
ladder -- the mismatch this producer exists to avoid.

## IT EMITS A PROFILE, NOT A RATIO, AND THAT IS THE FINDING

Both phases are front-loaded, though not equally. Pretraining moves 4.7x further
across stage 1 than across everything after it; SFT does 12.7% of its total in
its first 1,000 steps of 43,000. **So "alignment is N times pretraining" has no
single value** -- it is entirely a function of which stretch goes in the
denominator (1.39x against the late stretch, 0.31x against the full released
ladder). A producer emitting one number would be choosing the answer by choosing
the denominator.

**AND THE PER-TOKEN RATE INVERTS THE PICTURE.** Stage 1 moves the model 0.0793
JS per trillion tokens; the 150B of midtraining and long-context that follow move
it at 0.6680 -- **8.4x the rate**. Bulk pretraining is where the distance is;
annealing is where the efficiency is. Neither statement is available from step
counts.

## TOKENS, NOT STEPS — and the batch size revealed itself

Steps are not comparable across phases. The card states tokens per stage and our
own measured ladder gives the final step; the quotient lands on an EXACT POWER
OF TWO in all three cases and reconstructs the card's total:

    stage1  1,413,814 steps   5.93T tokens   4,194,304/step = 2^22
    stage2     47,684 steps    100B tokens   2,097,152/step = 2^21   <- HALF
    stage3     11,921 steps     50B tokens   4,194,304/step = 2^22
                                       reconstructed 6.080T vs card 6.080T

**Midtraining runs at half the batch of the stages either side of it.** That is
invisible in step counts and would silently corrupt any per-step comparison
across stages -- which is what this producer would have published a day ago.

## STATUS OF THE SFT DENOMINATOR

**SOURCED 2026-08-16 from the launch script, not the card.** The checkpoint card
states no batch size, no token count, no epochs and no steps; its Paper field
reads `[TBD]`. The number is `--global_batch_size=1048576` in
allenai/open-instruct `scripts/train/olmo3/7b_think_sft.sh`, corroborated by the
paper's A.6.1 prose and by OLMo-core's own default of `64 * 16_384`. The card was
never going to give this up; the training repo did.
"""
import argparse
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
RESULTS = os.path.join(HERE, "results")

#: STATED on https://huggingface.co/allenai/Olmo-3-1025-7B -- "5.93T tokens"
#: (stage 1), "100B tokens" (stage 2), "50B tokens" (stage 3). The 5.93T is
#: ROUNDED: 1,413,814 x 2^22 = 5.93003T, which is why the derived tokens/step
#: reads 4,194,328 rather than 4,194,304 exactly. A 24-token gap per step is the
#: card's rounding and not a discrepancy -- recorded so nobody later reads it as
#: one.
STAGE_TOKENS = {"stage1": 5.93e12, "stage2": 100e9, "stage3": 50e9}
STAGE_TOKENS_PER_STEP = {"stage1": 2 ** 22, "stage2": 2 ** 21, "stage3": 2 ** 22}

#: **STATED, and in the strongest form available: the literal launch argument.**
#: allenai/open-instruct `scripts/train/olmo3/7b_think_sft.sh` reads
#: `--global_batch_size=1048576` with `--seq_len=32768`, and OLMo-core measures
#: batch in TOKENS not instances -- paper A.6.1: "our batch size is now measured
#: in tokens instead of instances ... We train all of our 7B SFT models with a
#: batch size of 1M tokens ... for two epochs, with packing, and a 32,768
#: sequence length." Verified against the raw file, not read from a summary.
#:
#: 2^20 EXACTLY, against 2^22 / 2^21 / 2^22 for pretraining stages 1/2/3 -- the
#: SFT step is one QUARTER of a stage-1 step. Four independent figures now land
#: on powers of two.
#:
#: AND THE SCRIPT CONFIRMS THE PARENT: its base checkpoint path ends `/step11921/`
#: -- the exact rung this producer's pretraining ladder ends on. The edge we
#: measure is the edge they trained.
#:
#: Paper Table 47 gives 45.4B total tokens for 7B Thinking SFT, so the run is
#: ~43,297 steps and our 43 rungs (step1000..step43000 = 45.09B) cover ~99.3%.
#: `main` is NOT step43000 -- different LFS oids -- so a terminal checkpoint past
#: 43,000 exists without a step branch. The profile therefore measures 99.3% of
#: SFT, not all of it, and says so.
SFT_TOKENS_PER_STEP = 2 ** 20
SFT_TOTAL_TOKENS = 45.4e9

BASE = "allenai/Olmo-3-1025-7B"
SFT = "allenai/Olmo-3-7B-Think-SFT"
TAIL = "\x00TAIL"


def _esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _js(a, b):
    """Word-level JS with the residual as one extra bucket.

    **THE TAIL IS A BUCKET, NOT A ROUNDING ERROR.** `movement_cells.js_total` is
    exactly `js_fall + js_rise + js_still + js_tail` (checked: residual 0).
    Omitting it moved this producer's headline by 30%, because normalising by a
    tail-inclusive total changes every word probability. A reference computed
    without it would share a NAME with the numbers it calibrates and not a value.
    """
    ks = set(a) | set(b)
    ta, tb = sum(a.values()) or 1, sum(b.values()) or 1
    s = 0.0
    for k in ks:
        x, y = a.get(k, 0) / ta, b.get(k, 0) / tb
        m = (x + y) / 2
        if x > 0:
            s += 0.5 * x * math.log2(x / m)
        if y > 0:
            s += 0.5 * y * math.log2(y / m)
    return s


def _rungs():
    """The two OLMo ladders, restricted to the tier where they actually cross.

    **THE OLMo CHECKPOINTS DO NOT SHARE A PROMPT SET, and assuming they do was
    the last mistake here.** Across all 104 OLMo-3 checkpoints the universal
    intersection is ONE prompt; the base ladder alone spans 3, 1,199, 2,272 and
    4,428 prompts, because prompt sets are fleet-defined and do not nest. The
    2,272 tier is where both ladders live and it crosses fully: 41 pretraining
    rungs, 43 SFT rungs, 2,272 prompts held by all of them.
    """
    from malignment import ch
    rows = ch.query("""SELECT model, count(DISTINCT prompt) p FROM {db}.twp_words
        WHERE model LIKE '%s@%%' OR model LIKE '%s@%%'
        GROUP BY model""" % (_esc(BASE), _esc(SFT)))
    lad = [r["model"] for r in rows if r["p"] == 2272]

    def pkey(m):
        t = m.split("@")[1]
        return (t.split("-")[0], int(t.split("step")[-1]))

    pre = sorted((m for m in lad if m.startswith(BASE)), key=pkey)
    sft = sorted((m for m in lad if m.startswith(SFT)),
                 key=lambda m: int(m.split("step")[-1]))
    return pre, sft


def _dists(models, prompts):
    from malignment import ch
    M = "','".join(_esc(m) for m in models)
    PL = "','".join(_esc(p) for p in prompts)
    per = {}
    for r in ch.query("""SELECT prompt, model, word, p FROM {db}.twp_words
            WHERE prompt IN ('%s') AND model IN ('%s')""" % (PL, M)):
        per.setdefault(r["prompt"], {}).setdefault(r["model"], {})[r["word"]] = r["p"]
    for r in ch.query("""SELECT prompt, model, tail FROM {db}.twp_cells
            WHERE prompt IN ('%s') AND model IN ('%s')""" % (PL, M)):
        d = per.get(r["prompt"], {}).get(r["model"])
        if d is not None:
            d[TAIL] = r["tail"]
    return per


def _tokens_between(a, b):
    """Tokens of training separating two pretraining rungs, or None."""
    def parse(m):
        t = m.split("@")[1]
        return t.split("-")[0], int(t.split("step")[-1])
    (sa, na), (sb, nb) = parse(a), parse(b)
    order = ["stage1", "stage2", "stage3"]
    if sa not in order or sb not in order:
        return None
    if sa == sb:
        return (nb - na) * STAGE_TOKENS_PER_STEP[sa]
    tot = STAGE_TOKENS[sa] - na * STAGE_TOKENS_PER_STEP[sa]
    for s in order[order.index(sa) + 1:order.index(sb)]:
        tot += STAGE_TOKENS[s]
    return tot + nb * STAGE_TOKENS_PER_STEP[sb]


def _cum_tokens(m):
    """Cumulative training tokens at a rung, from the run's start."""
    t = m.split("@")[1]
    if m.startswith(SFT):
        return 6.080e12 + int(t.split("step")[-1]) * SFT_TOKENS_PER_STEP
    stage, n = t.split("-")[0], int(t.split("step")[-1])
    order = ["stage1", "stage2", "stage3"]
    return sum(STAGE_TOKENS[s] for s in order[:order.index(stage)]) + \
        n * STAGE_TOKENS_PER_STEP[stage]


def curve():
    """Consecutive-rung displacement SPEED across the whole released run.

    **THIS IS THE PLOTTABLE OBJECT AND THE SUMMARY TABLE IS NOT.** Six endpoint
    rows can only show that later phases are faster; they cannot show WHERE the
    rate changes, whether it is a step or a slope, or whether the SFT jump is one
    discontinuity or a short steep run. 82 consecutive intervals can.

    Each point is one released interval: JS between adjacent rungs, divided by
    the tokens between them. Vectorised per prompt (one models x words matrix)
    because the pure-Python pairwise loop is ~1.5 ms and this is 186k of them.
    """
    import numpy as np
    from malignment import ch
    pre, sft = _rungs()
    seq = pre + sft
    M = "','".join(_esc(m) for m in seq)
    prompts = [r["prompt"] for r in ch.query(
        """SELECT prompt FROM {db}.twp_words WHERE model IN ('%s')
           GROUP BY prompt HAVING count(DISTINCT model)=%d""" % (M, len(seq)))]
    pairs = list(zip(seq, seq[1:]))
    acc = {p: [] for p in pairs}
    B = 40
    for i in range(0, len(prompts), B):
        chunk = prompts[i:i + B]
        PL = "','".join(_esc(x) for x in chunk)
        per = {}
        for r in ch.query("""SELECT prompt, model, word, p FROM {db}.twp_words
                WHERE prompt IN ('%s') AND model IN ('%s')""" % (PL, M)):
            per.setdefault(r["prompt"], {}).setdefault(r["model"], {})[r["word"]] = r["p"]
        for r in ch.query("""SELECT prompt, model, tail FROM {db}.twp_cells
                WHERE prompt IN ('%s') AND model IN ('%s')""" % (PL, M)):
            d = per.get(r["prompt"], {}).get(r["model"])
            if d is not None:
                d[TAIL] = r["tail"]
        for pr, d in per.items():
            vocab = sorted({w for m in d for w in d[m]})
            idx = {w: k for k, w in enumerate(vocab)}
            rows_ = {}
            X = np.zeros((len(d), len(vocab)))
            for k, m in enumerate(sorted(d)):
                rows_[m] = k
                for w, v in d[m].items():
                    X[k, idx[w]] = v
            X = X / np.maximum(X.sum(1, keepdims=True), 1e-30)
            for a2, b2 in pairs:
                if a2 in rows_ and b2 in rows_:
                    x, y = X[rows_[a2]], X[rows_[b2]]
                    mid = (x + y) / 2
                    with np.errstate(divide="ignore", invalid="ignore"):
                        t1 = np.where(x > 0, x * np.log2(x / mid), 0.0)
                        t2 = np.where(y > 0, y * np.log2(y / mid), 0.0)
                    acc[(a2, b2)].append(float(0.5 * (t1.sum() + t2.sum())))
    out = []
    for a2, b2 in pairs:
        v = acc[(a2, b2)]
        if not v:
            continue
        t0, t1 = _cum_tokens(a2), _cum_tokens(b2)
        dt = t1 - t0
        phase = ("SFT" if b2.startswith(SFT)
                 else b2.split("@")[1].split("-")[0])
        if a2.startswith(BASE) and b2.startswith(SFT):
            phase = "base->SFT"
        out.append({"from": a2.split("@")[-1], "to": b2.split("@")[-1],
                    "phase": phase, "js": st.median(v), "n_prompts": len(v),
                    "tokens_from": t0, "tokens_to": t1, "tokens": dt,
                    "js_per_T": st.median(v) / (dt / 1e12) if dt else None})
    return {"_about": "Consecutive released-rung displacement SPEED across the "
                      "whole OLMo 3 7B run: pretraining stages 1-3 then Think "
                      "SFT. x = cumulative training tokens, y = JS per trillion "
                      "tokens. The plottable object.",
            "panel_prompts": len(prompts), "n_intervals": len(out),
            "stage_tokens_per_step": STAGE_TOKENS_PER_STEP,
            "sft_tokens_per_step": SFT_TOKENS_PER_STEP,
            "sft_total_tokens_stated": SFT_TOTAL_TOKENS,
            "intervals": out}


#: **THE ARCHIVE'S .f16 TIER, READ IN PLACE AND NOT INGESTED.** 63 GB of
#: full-vocabulary logits on an external volume, deliberately parked by RH at
#: docket [5886] with zero live readers. This reads it DIRECTLY through the
#: `logit_row`/`logit_dim` pointers in each dump's own `.jsonl` companion --
#: nothing is copied into ClickHouse, `logit_dir_resolution.json` is untouched,
#: and the tier stays parked. CH's own `logit_probs` is NOT the route: it is
#: itself top-k truncated (~6.6k of 100,278), which would reintroduce the
#: truncation this variant exists to measure.
ARCHIVE_VERSE = "/Users/rj416/github/malign-logits/data/raw/verse_fleet"


def fullvocab(n_prompts=400, seed=17):
    """Consecutive-rung JS at FULL vocabulary, from the .f16 dumps.

    **WHY IT EXISTS: twp IS TOP-N TRUNCATED and the direction of the bias was
    not guessable.** I predicted truncation would HIDE alignment effects spread
    across rare words. The opposite is true -- twp INFLATES post-training
    displacement by ~50% (SFT 0.0169 twp against 0.0108 full-vocab) while
    agreeing on pretraining within 8%, because alignment concentrates on exactly
    the high-probability words twp keeps and the untouched tail dilutes it at
    full vocabulary. Any twp-derived SFT/pretraining ratio is overstated by
    about a third.

    **FAILS LOUDLY IF THE VOLUME IS ABSENT.** The tier's own manifest names the
    hazard: "the failure mode is an unmounted volume, silent."
    """
    import glob
    import random
    import numpy as np
    if not os.path.isdir(ARCHIVE_VERSE):
        raise SystemExit(
            "REFUSED: %s is not present.\n"
            "The .f16 tier lives on an external volume. A silent empty result "
            "here would look exactly like a finished run." % ARCHIVE_VERSE)
    random.seed(seed)

    def rung_files(pat):
        out = {}
        for f in glob.glob(os.path.join(ARCHIVE_VERSE, "*", pat)):
            b = os.path.basename(f).replace(".jsonl", "")
            if "@" in b:
                out.setdefault(b, f)
        return out

    base = rung_files("allenai__Olmo-3-1025-7B@*.jsonl")
    sftf = rung_files("allenai__Olmo-3-7B-Think-SFT@*.jsonl")

    def bkey(b):
        t = b.split("@")[1]
        return (t.split("-")[0], int(t.split("step")[-1]))

    seq = ([(b, base[b]) for b in sorted(base, key=bkey)] +
           [(x, sftf[x]) for x in sorted(sftf, key=lambda z: int(z.split("step")[-1]))])
    meta = {}
    for name, f in seq:
        rows = [json.loads(l) for l in open(f)]
        meta[name] = ([r["prompt"] for r in rows], rows[0]["logit_dim"],
                      f.replace(".jsonl", ".f16"))
    P0 = meta[seq[0][0]][0]
    #: **ASSERTED, NOT ASSUMED.** The memmap join is by ROW INDEX, so a differing
    #: prompt order between two rungs would silently compare different prompts --
    #: real floats from the right file at the wrong offset.
    if not all(meta[n][0] == P0 for n, _ in seq):
        raise SystemExit("REFUSED: prompt order differs between rungs")
    dims = {meta[n][1] for n, _ in seq}
    if len(dims) != 1:
        raise SystemExit("REFUSED: logit_dim varies across rungs: %s" % dims)
    dim = dims.pop()
    for name, _ in seq:
        P, _d, fp = meta[name]
        if os.path.getsize(fp) != len(P) * dim * 2:
            raise SystemExit("REFUSED: %s size != rows*dim*2" % fp)

    idx = sorted(random.sample(range(len(P0)), min(n_prompts, len(P0))))

    def load(name):
        P, _d, fp = meta[name]
        m = np.memmap(fp, dtype=np.float16, mode="r").reshape(len(P), dim)
        a2 = np.asarray(m[idx], dtype=np.float32)
        if a2.max() > 1.5:                      # logits, not probabilities
            a2 = np.exp(a2 - a2.max(1, keepdims=True))
        return a2 / np.maximum(a2.sum(1, keepdims=True), 1e-30)

    out, prev, pname = [], None, None
    for name, _ in seq:
        cur = load(name)
        if prev is not None:
            mid = (prev + cur) / 2
            with np.errstate(divide="ignore", invalid="ignore"):
                t1 = np.where(prev > 0, prev * np.log2(prev / mid), 0.0)
                t2 = np.where(cur > 0, cur * np.log2(cur / mid), 0.0)
            js = 0.5 * (t1.sum(1) + t2.sum(1))
            ph = ("base->SFT" if ("1025-7B" in pname and "Think-SFT" in name)
                  else ("SFT" if "Think-SFT" in name
                        else name.split("@")[1].split("-")[0]))
            t0, t1c = _cum_tokens_name(pname), _cum_tokens_name(name)
            out.append({"from": pname.split("@")[-1], "to": name.split("@")[-1],
                        "phase": ph, "js": float(np.median(js)),
                        "n_prompts": len(idx),
                        "tokens_from": t0, "tokens_to": t1c,
                        "tokens": (t1c - t0) if (t0 and t1c) else None,
                        "js_per_T": (float(np.median(js)) / ((t1c - t0) / 1e12))
                        if (t0 and t1c and t1c > t0) else None})
        prev, pname = cur, name
    return {"_about": "Consecutive-rung JS at FULL VOCABULARY (%d), read in "
                      "place from the archive's parked .f16 tier via the "
                      "logit_row/logit_dim pointers in each dump's jsonl. "
                      "Nothing ingested." % dim,
            "vocab": dim, "n_prompts": len(idx), "n_intervals": len(out),
            "source": ARCHIVE_VERSE, "intervals": out}


def _cum_tokens_name(m):
    t = m.split("@")[1]
    if "Think-SFT" in m:
        return 6.080e12 + int(t.split("step")[-1]) * (SFT_TOKENS_PER_STEP or 0)
    stage, n = t.split("-")[0], int(t.split("step")[-1])
    order = ["stage1", "stage2", "stage3"]
    return sum(STAGE_TOKENS[s] for s in order[:order.index(stage)]) + \
        n * STAGE_TOKENS_PER_STEP[stage]


def profile():
    from malignment import ch
    pre, sft = _rungs()
    picks = [pre[0], pre[len(pre) // 2], pre[-1],
             sft[0], sft[len(sft) // 2], sft[-1]]
    M = "','".join(_esc(m) for m in picks)
    prompts = [r["prompt"] for r in ch.query(
        """SELECT prompt FROM {db}.twp_words WHERE model IN ('%s')
           GROUP BY prompt HAVING count(DISTINCT model)=%d""" % (M, len(picks)))]
    per = _dists(picks, prompts)

    def med(a, b):
        v = [_js(per[p][a], per[p][b]) for p in per if a in per[p] and b in per[p]]
        return (st.median(v), len(v)) if v else (None, 0)

    rows = []

    def add(phase, a, b, tokens):
        m, k = med(a, b)
        rows.append({"phase": phase, "from": a.split("@")[-1], "to": b.split("@")[-1],
                     "js": m, "n_prompts": k, "tokens": tokens,
                     "js_per_T": (m / (tokens / 1e12)) if (m and tokens) else None})

    mid = len(pre) // 2
    add("pretraining (full released)", pre[0], pre[-1], _tokens_between(pre[0], pre[-1]))
    add("pretraining (first half)", pre[0], pre[mid], _tokens_between(pre[0], pre[mid]))
    add("pretraining (second half)", pre[mid], pre[-1], _tokens_between(pre[mid], pre[-1]))

    #: **THE JUMP THE LADDER CANNOT SEE.** The SFT ladder starts at step1000, so
    #: base -> SFT@step1000 sits outside it -- and it is 43% of SFT's total
    #: displacement over 2.3% of its released rungs. Omitting it understates SFT,
    #: which an earlier version of this producer did. **AND THE FIRST MEASUREMENT
    #: OF IT WAS WRONG AT 43%: it ran from stage2-step47684, but STAGE 3 COMES
    #: AFTER STAGE 2, so that was a midtraining rung and not the final base. From
    #: stage3-step11921 the figure is 12.7%.** A phase boundary read as a
    #: terminus. CLAUDE.md
    #: already recorded the shape ("sexual repression is a phase transition, 70%
    #: drop by step 1000"); this is its whole-distribution form.
    tps = SFT_TOKENS_PER_STEP
    last = int(sft[-1].split("step")[-1])
    add("SFT (first 1,000 steps)", pre[-1], sft[0], 1000 * tps if tps else None)
    add("SFT (released ladder)", sft[0], sft[-1], (last - 1000) * tps if tps else None)
    add("SFT (total)", pre[-1], sft[-1], last * tps if tps else None)

    return {"_about": "How far OLMo 3 7B moves during each phase of its OWN "
                      "training. A PROFILE, not a ratio: both phases are "
                      "front-loaded, so any single ratio is chosen by choosing "
                      "a denominator.",
            "panel_prompts": len(prompts),
            "stage_tokens_per_step": STAGE_TOKENS_PER_STEP,
            "sft_tokens_per_step": SFT_TOKENS_PER_STEP,
            "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--fullvocab", action="store_true",
                    help="full-vocabulary curve from the archive .f16 tier")
    ap.add_argument("--prompts", type=int, default=400)
    ap.add_argument("--curve", action="store_true",
                    help="consecutive-rung speed across the whole run (plottable)")
    a = ap.parse_args()
    if a.fullvocab:
        c = fullvocab(a.prompts)
        print("  %d intervals, vocab %d, %d prompts" % (c["n_intervals"], c["vocab"], c["n_prompts"]))
        for r in c["intervals"][:3] + c["intervals"][-2:]:
            print("    %-11s %-20s -> %-20s JS %.4f" % (r["phase"], r["from"], r["to"], r["js"]))
        if a.write:
            os.makedirs(RESULTS, exist_ok=True)
            json.dump(c, open(os.path.join(RESULTS, "curve_fullvocab.json"), "w"), indent=1)
            print("  wrote results/curve_fullvocab.json")
        return 0
    if a.curve:
        c = curve()
        print("  %d intervals over %d prompts" % (c["n_intervals"], c["panel_prompts"]))
        for r in c["intervals"][:3] + c["intervals"][-3:]:
            print("    %-10s %-20s -> %-20s JS %.4f  %.4f/T"
                  % (r["phase"], r["from"], r["to"], r["js"], r["js_per_T"]))
        if a.write:
            os.makedirs(RESULTS, exist_ok=True)
            json.dump(c, open(os.path.join(RESULTS, "curve.json"), "w"), indent=1)
            print("  wrote results/curve.json")
        return 0
    doc = profile()
    print("  OLMo 3 7B — displacement per phase, %d shared prompts\n" % doc["panel_prompts"])
    print("  %-30s %-20s %-20s %8s %9s %9s"
          % ("phase", "from", "to", "JS", "tokens", "JS per T"))
    for r in doc["rows"]:
        print("  %-30s %-20s %-20s %8.4f %9s %9s"
              % (r["phase"], r["from"], r["to"], r["js"],
                 ("%.3fT" % (r["tokens"] / 1e12)) if r["tokens"] else "-",
                 ("%.4f" % r["js_per_T"]) if r["js_per_T"] else "-"))
    if not SFT_TOKENS_PER_STEP:
        print("\n  SFT tokens/step NOT SOURCED — SFT rows carry no per-token figure.")
    if a.write:
        os.makedirs(RESULTS, exist_ok=True)
        json.dump(doc, open(os.path.join(RESULTS, "profile.json"), "w"), indent=1)
        print("  wrote results/profile.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
