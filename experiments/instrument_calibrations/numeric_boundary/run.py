#!/usr/bin/env python
"""numeric_boundary — may the boundary rule read context? Stage 1: tokenizers.

    python run.py --stage tokenizers            -> results/by_tokenizer.csv

**STAGE 1 LOADS NO WEIGHTS.** The question it answers is entirely about how a
tokenizer splits a string, and `twp.intra_word` is a pure function, so nothing
here needs a GPU, a fleet or a spend. Stages 2 and 3 do and are not implemented.

## WHAT IT ASKS, AND WHY THAT IS THE DECIDING FACT

`twp.intra_word` ALREADY implements the numeric rule at character level -- its
own docstring names `100` + `,000` -- and it is unreachable in practice:

    return len(tok_str) > 1 and tok_str[1].isalnum()

**It needs the separator to arrive INSIDE a token with something after it.** A
tokenizer that emits `,` alone hands it a one-character string and the test
fails at `len(tok_str) > 1`. So the rule is not missing; it is starved. This
stage measures how often it is starved, across the roster, per character class.

## THE CJK ARM IS THE SAME QUESTION WITH THE SIGN FLIPPED

Full-width `，` and `。` end a Chinese sentence and are NOT in the intra set, so
they behave correctly ONLY IF the mask treats them as boundaries. @malign's
[6423] reports it does not. Both arms are here because a patch to one that
ignores the other is how a classifier acquires two incompatible exceptions.

## FAILURES ARE RECORDED, NEVER DROPPED

A tokenizer that will not load is a row with a reason, not an absence. Roughly a
dozen roster entries are gated or need transformers 4.57, and a silently shorter
table would read as a cleaner result.
"""
import argparse, csv, json, math, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS_FROM = None
RESULTS = os.path.join(HERE, "results")

#: Chosen so each isolates ONE decision. The salary case is the one that
#: motivated the commission; the decimal is the case `intra_word`'s own
#: docstring admits it fails; the CJK pair is the opposite-sign arm.
PROBES = [
    ("thousands", "a salary of $150,000 a year", ",", "150,000"),
    ("decimal",   "the value of pi is 3.14 exactly", ".", "3.14"),
    ("cjk_comma", "他很高兴，因为下雨了", "，", None),
    ("cjk_stop",  "他很高兴。下雨了", "。", None),
]


def probe(tok, sep, surface):
    """How does this tokenizer present `sep`, and can intra_word act on it?

    Returns (sep_alone, intra_fires, sample). `sep_alone` is the condition that
    starves the rule; `intra_fires` is measured by asking `intra_word` about
    every token of the string rather than reasoning about which one matters.
    """
    from malignment import twp
    ids = tok.encode(PROBE_TEXT, add_special_tokens=False)
    pieces = [tok.decode([i]) for i in ids]
    hits = [p for p in pieces if sep in p]
    if not hits:
        return None, None, ""
    sep_alone = any(p.strip() == sep for p in hits)
    intra = False
    if surface:
        intra = any(twp.intra_word(surface, p) for p in pieces)
    return sep_alone, intra, " | ".join(repr(p) for p in hits[:3])


CJK_TEXT = "他很高兴，因为下雨了。她说：这很好！"
CJK_MARKS = "，。！：、；？"


def _is_boundary(raw):
    """`boundary_mask`'s test, reproduced so this stage needs no vocab size.

    Copied deliberately rather than imported: `boundary_mask` allocates an array
    of n and walks every id, which needs the MODEL's vocab size and is 150k
    iterations to answer a question about 8 tokens. This asks the same predicate
    of the tokens actually present. If the two ever disagree that is a defect in
    this file, and the predicate is four lines so it can be diffed by eye.
    """
    from malignment import twp
    if raw is None:
        return True
    if raw.startswith(("\u0120", "\u2581", " ")):
        return True
    if raw and (raw[0] in twp.PUNCT or raw.strip() == ""):
        return True
    return raw.startswith("<") and raw.endswith(">")


def stage_mask(limit=None):
    """The CJK arm: is the RAW token string the wrong key for PUNCT?

    **`，` and `。` ARE in PUNCT.** The set is correct and the failure is not a
    missing member -- it is that `boundary_mask` tests `s[0]` of the token as the
    tokenizer REPRESENTS it, and a byte-level BPE represents `，` as the mojibake
    `ï¼Į`, whose first character is `ï`. The right set, the wrong key.
    """
    from malignment import roster, twp
    models = sorted(roster.population("all"))
    if limit:
        models = models[:limit]
    if MODELS_FROM:
        want = set(l.strip() for l in open(MODELS_FROM) if l.strip())
        models = [m for m in models if m in want]
    rows = []
    for i, mid in enumerate(models, 1):
        try:
            tok, _ = twp.load_tokenizer(mid)
        except Exception as e:
            rows.append({"model": mid, "loaded": 0,
                         "reason": type(e).__name__ + ": " + str(e)[:80]})
            continue
        tot = correct = glued = wrongkey = 0
        for tid in tok.encode(CJK_TEXT, add_special_tokens=False):
            raw = tok.convert_ids_to_tokens(tid)
            dec = tok.decode([tid])
            if not any(m in dec for m in CJK_MARKS):
                continue
            tot += 1
            if _is_boundary(raw):
                correct += 1
            if raw and raw[0] not in twp.PUNCT:
                wrongkey += 1
            #: punctuation and a word in ONE token -- no boundary FLAG can
            #: represent this, whichever way it is set.
            if len(dec.strip()) > 1:
                glued += 1
        rows.append({"model": mid, "loaded": 1, "reason": "",
                     "cjk_punct_tokens": tot, "marked_boundary": correct,
                     "wrong_key": wrongkey, "glued_to_word": glued})
        del tok
        if i % 20 == 0:
            print("  %d/%d" % (i, len(models)), file=sys.stderr)
    return rows, sum(1 for r in rows if not r.get("loaded"))


def stage_tokenizers(limit=None):
    from malignment import roster, twp
    #: sorted() because population() returns a SET -- iteration order would be
    #: unstable between runs and the csv would diff for no reason.
    models = sorted(roster.population("all"))
    if limit:
        models = models[:limit]
    #: `--models-from` exists because the 24 failures of the first sweep were NOT
    #: a random 24: 23 were transformers-5 validation errors, i.e. the `tf457`
    #: cohort, which this repo keeps a second venv for. A sweep that drops a
    #: systematically-selected subset and reports 136/136 is reporting the venv.
    if MODELS_FROM:
        want = [l.strip() for l in open(MODELS_FROM) if l.strip()]
        models = [m for m in models if m in set(want)]
    rows, failed = [], 0
    for i, mid in enumerate(models, 1):
        try:
            tok, loader = twp.load_tokenizer(mid)
        except Exception as e:
            failed += 1
            rows.append({"model": mid, "loaded": 0,
                         "reason": type(e).__name__ + ": " + str(e)[:80]})
            continue
        row = {"model": mid, "loaded": 1, "reason": ""}
        for name, text, sep, surface in PROBES:
            global PROBE_TEXT
            PROBE_TEXT = text
            try:
                alone, intra, sample = probe(tok, sep, surface)
                row[name + "_sep_alone"] = "" if alone is None else int(alone)
                row[name + "_intra_fires"] = "" if intra is None else int(intra)
                row[name + "_sample"] = sample
            except Exception as e:
                row[name + "_sep_alone"] = "ERR"
                row[name + "_sample"] = str(e)[:50]
        rows.append(row)
        del tok
        if i % 20 == 0:
            print("  %d/%d" % (i, len(models)), file=sys.stderr)
    return rows, failed



#: **THE THIRD ARM: HOW BIG IS THE ERROR THE OTHER TWO DESCRIBE?**
#: The tokenizer and mask arms establish that `，` is never marked a boundary on
#: byte-level BPE (84 of 133 models). This one measures what that COSTS, and it
#: needs weights, unlike the other two.
#:
#: The mechanism, established at [6435]: `_account` continues only through
#: NON-boundary tokens, so `expand` walks through `，` precisely BECAUSE the mask
#: fails to mark it -- then `clean_surface` strips the mark, and `一个，` is
#: credited back onto `一个`, which already terminated at the previous depth.
#: **One surface, two credits.** So the mask defect and the multi-depth crediting
#: are one phenomenon, and this stage sizes it by instrumenting `_account` to
#: record every credit rather than by differencing two scorers -- which cannot
#: work, since both call the same `_boundary_for` and the defect cancels.
#:
#: **SCOPE, and it is narrow.** One model, a few prompts. The 84/49 split is
#: per-MODEL and roster-wide (`--stage mask`); these magnitudes are PER-PROMPT on
#: one byte-level model. They do not belong in one sentence, and a roster figure
#: would need this run over the roster.
MAGNITUDE_PROMPTS = [
    ("zh", "那个自由的人选择了"),
    ("zh", "她非常生气她想要"),
    ("en", "She was so angry she wanted to"),      # control: must be ZERO
]


def stage_magnitude(model_id, device="mps"):
    """-> rows. Instruments `_account` and reports the excess credit per prompt."""
    import collections
    import torch
    torch.set_grad_enabled(False)
    from malignment import models as M
    from malignment import twp as T

    tok, _loader = T.load_tokenizer(model_id)
    model, _t2 = M.load_model(model_id)
    bmask = T.boundary_mask(tok, model.config.vocab_size)
    trie = T.load_prefix_trie()
    cids, cstrs, lids, pidsi = T.cjk_vocab(tok, model.config.vocab_size)
    cjk = (trie, cids, cstrs, lids, pidsi) if len(cids) else None

    orig = T._account
    credits = collections.defaultdict(list)

    def spy(row, b, surf, pref, mass, t1, theta, words, res, nxt):
        before = words.get((surf, t1), 0.0)
        orig(row, b, surf, pref, mass, t1, theta, words, res, nxt)
        d = words.get((surf, t1), 0.0) - before
        if d > 0:
            credits[(surf, int(t1))].append(d)

    rows = []
    T._account = spy
    try:
        for lang, prompt in MAGNITUDE_PROMPTS:
            credits.clear()
            w = T.expand(model, tok, prompt, device, bmask, cjk=cjk)
            w = w[0] if isinstance(w, tuple) else w
            total = sum(w.values())
            multi = {k: v for k, v in credits.items() if len(v) > 1}
            #: the FIRST credit is the word terminating legitimately; every later
            #: one is the same surface reached again through a mark that should
            #: have ended it. So the excess is the sum of all credits after the
            #: first, and it is the error -- not the whole mass of affected keys.
            excess = sum(sum(v[1:]) for v in multi.values())
            in_multi = sum(sum(v) for v in multi.values())
            infl = sorted(sum(v) / v[0] for v in multi.values()) or [0.0]
            rows.append(dict(
                model=model_id, lang=lang, prompt=prompt,
                keys=len(credits), multi_keys=len(multi),
                resolved_mass=round(total, 6),
                mass_in_multi=round(in_multi, 6),
                mass_in_multi_pct=round(100 * in_multi / total, 3) if total else 0.0,
                excess=round(excess, 6),
                excess_pct=round(100 * excess / total, 3) if total else 0.0,
                inflation_median=round(infl[len(infl) // 2], 4),
                inflation_max=round(max(infl), 4)))
    finally:
        T._account = orig
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="tokenizers", choices=["tokenizers", "mask", "magnitude", "beam"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--models-from", default=None,
                    help="file of model ids, one per line -- for the tf457 cohort")
    ap.add_argument("--out", default="by_tokenizer.csv")
    ap.add_argument("--beam", type=int, default=100)
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--model", default="HuggingFaceTB/SmolLM2-360M",
                    help="magnitude stage only -- it needs weights")
    ap.add_argument("--device", default="mps")
    a = ap.parse_args()
    global MODELS_FROM
    MODELS_FROM = a.models_from
    os.makedirs(RESULTS, exist_ok=True)
    if a.stage == "magnitude":
        rows = stage_magnitude(a.model, a.device)
        cols = ["model","lang","prompt","keys","multi_keys","resolved_mass",
                "mass_in_multi","mass_in_multi_pct","excess","excess_pct",
                "inflation_median","inflation_max"]
        path = os.path.join(RESULTS, "magnitude.csv")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print("\nmagnitude arm: %s" % a.model)
        for r in rows:
            print("  %-4s keys=%-4d multi=%-3d  mass in multi %6.2f%%  EXCESS %5.2f%%"
                  "  inflation med %.3fx max %.3fx"
                  % (r["lang"], r["keys"], r["multi_keys"], r["mass_in_multi_pct"],
                     r["excess_pct"], r["inflation_median"], r["inflation_max"]))
        print("\n  ONE MODEL, %d PROMPTS -- not a roster figure. The 84/49 split is"
              % len(rows))
        print("  per-model (--stage mask); these are per-prompt on one model.")
        print("\n  ->", path)
        return

    if a.stage == "beam":
        stage_beam(width=a.beam, depth=a.depth)
        return
    if a.stage == "mask":
        rows, failed = stage_mask(a.limit)
        cols = ["model","loaded","reason","cjk_punct_tokens","marked_boundary",
                "wrong_key","glued_to_word"]
        path = os.path.join(RESULTS, a.out if a.out != "by_tokenizer.csv"
                            else "cjk_boundary.csv")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        ok = [r for r in rows if r.get("loaded") == 1 and r.get("cjk_punct_tokens")]
        allc = [r for r in ok if r["marked_boundary"] == r["cjk_punct_tokens"]]
        none = [r for r in ok if r["marked_boundary"] == 0]
        print("\nCJK arm: %d models carry CJK punctuation tokens" % len(ok))
        print("  ALL marks boundary  %d" % len(allc))
        print("  NONE marked         %d   <- the defect" % len(none))
        print("  partial             %d" % (len(ok)-len(allc)-len(none)))
        print("  glued punct+word    %d" % sum(1 for r in ok if r["glued_to_word"]))
        print("\n  ->", path)
        return
    rows, failed = stage_tokenizers(a.limit)

    cols = ["model", "loaded", "reason"]
    for name, _, _, _ in PROBES:
        cols += [name + "_sep_alone", name + "_intra_fires", name + "_sample"]
    path = os.path.join(RESULTS, a.out)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    ok = [r for r in rows if r.get("loaded")]
    print("\ntokenizers: %d loaded, %d failed (recorded, not dropped)"
          % (len(ok), failed))
    for name, _, _, surface in PROBES:
        k = name + "_sep_alone"
        seen = [r for r in ok if r.get(k) not in ("", None)]
        alone = sum(1 for r in seen if r.get(k) == 1)
        fires = sum(1 for r in seen if r.get(name + "_intra_fires") == 1)
        print("  %-10s separator present in %3d | emitted ALONE in %3d | "
              "intra_word fires in %3d" % (name, len(seen), alone, fires))
    print("\n  ->", path)




# --------------------------------------------------------------------------
# Stage 4 -- the beam. THE ONLY ARM THAT NEEDS WEIGHTS.
# --------------------------------------------------------------------------

#: `domain == 'class'` is the whole battery and is EXACT: 30 prompts in the
#: catalogue, all 30 salary, zero false positives (registration A3). Never the
#: prompt text, never `finding` -- F13 is on 439 prompts of which 404 are not
#: salary.
BEAM_MODELS = ["HuggingFaceTB/SmolLM2-360M", "HuggingFaceTB/SmolLM2-360M-Instruct"]


def stage_beam(width=10, depth=10, models=None):
    """What does the model SAY when allowed to write? `generate`, nothing custom.

    RH: *"why not just hf generate for 10 tokens 10 times temp=1"*. Right, and
    the first version of this was a hand-rolled beam over `twp.next_dist` --
    built to stay commensurable with `expand`, which is a comparison to make
    AFTERWARDS and not a reason to reimplement a sampler. It cost three wrong
    signature guesses in ten minutes.

    The question is whether a salary comes out whole: `$150,000` rather than the
    `150` that `expand` records once the comma terminates the word. `generate`
    answers that with no boundary rule in the way at all.

    SAMPLED, not greedy, and temp=1 on purpose: greedy returns one continuation
    and says nothing about the distribution's shape, which is what the salary
    hypotheses are about.

    WRITES AFTER EVERY PROMPT -- first arm that loads weights, so a crash at
    prompt 27 costs one row.
    """
    import torch
    from malignment import twp
    from malignment.checkpoint import Checkpoint
    from malignment.prompts import Prompts

    #: `domain == 'class'` IS the battery: 30 prompts, all salary, zero false
    #: positives (registration A3). Not the prompt text, not `finding` -- F13 is
    #: on 439 prompts of which 404 are not salary.
    prompts = [p for p in Prompts.all()
               if str(getattr(p, "domain", "") or "") == "class"]
    prompts.sort(key=lambda p: (p.language, p.prompt_id))
    mids = models or BEAM_MODELS
    print("generate: %d prompts (%d en, %d zh) x %d models, %d samples x %d tokens"
          % (len(prompts), sum(1 for p in prompts if p.language == "en"),
             sum(1 for p in prompts if p.language == "zh"), len(mids), width, depth),
          file=sys.stderr)

    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, "beam.csv")
    cols = ["model", "prompt_id", "language", "subdomain", "group_id", "prompt",
            "sample", "continuation", "numeral", "has_separator", "n_digits"]
    fresh = not os.path.exists(path)
    fh = open(path, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    if fresh:
        w.writeheader(); fh.flush()

    for mid in mids:
        L = Checkpoint(mid).load()
        for pi, p in enumerate(prompts, 1):
            ids = L.tok(p.text, return_tensors="pt").to(L.dev)
            with torch.no_grad():
                out = L.model.generate(**ids, max_new_tokens=depth,
                                       do_sample=True, temperature=1.0,
                                       num_return_sequences=width,
                                       pad_token_id=L.tok.eos_token_id)
            n_in = ids["input_ids"].shape[1]
            got = 0
            for k in range(out.shape[0]):
                cont = L.tok.decode(out[k][n_in:], skip_special_tokens=True)
                m = re.match(r"\s*([\d,\.]*\d)", cont)
                num = m.group(1) if m else ""
                sep = ("," in num) or ("." in num)
                got += bool(sep)
                w.writerow({"model": mid, "prompt_id": p.prompt_id,
                            "language": p.language,
                            "subdomain": getattr(p, "subdomain", "") or "",
                            "group_id": p._row.get("group_id") or "",
                            "prompt": p.text, "sample": k + 1,
                            "continuation": cont, "numeral": num,
                            "has_separator": int(sep),
                            "n_digits": sum(c.isdigit() for c in num)})
            fh.flush(); os.fsync(fh.fileno())
            print("  %-28s %2d/%d %-16s sep %d/%d"
                  % (mid.split("/")[-1][:26], pi, len(prompts), p.prompt_id,
                     got, width), file=sys.stderr)
        twp.free(L.model)
        del L
    fh.close()
    print("\n  ->", path)


if __name__ == "__main__":
    main()
