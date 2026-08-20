"""THE standard population filter for `passages.parquet`. Import, do not re-derive.

    from population import standard, fluency_rates, contrast_models

RH's rule, 2026-08-20: an analysis on this parquet runs on

    ALL-LATIN passages, OR
    ALL-CHINESE passages FROM A CHINESE-FLUENT MODEL

with degenerate output excluded from both.

## Why the Chinese clause exists

Blind Opus judges (kappa 0.776, `zh_fluency_and_ordering.md`) found **12% of
Chinese continuations fluent**, 71% broken or flawed. And it does not spread
evenly: **31 of 58 models have ZERO fluent verdicts.** The competent set is almost
entirely Chinese-origin -- Qwen, Yi, GLM, MiniCPM, CT-LLM, neo -- plus bloom.

So the "Chinese corpus" is two populations: models writing the language, and models
failing at it. Pooling them makes `bits_per_byte` a measure of how a model breaks
rather than how it writes.

## AND A CONTRAST NEEDS BOTH ARMS FLUENT, WHICH IS STRICTER

Requiring only "the model is fluent" still admits lineages where the arms differ in
CAPABILITY, and then an arm contrast measures that instead of register:

    bloom-7b1     base 25.0%  ->  aligned  0.0%    bloomz LOST Chinese
    MiniCPM5-1B   base  0.0%  ->  aligned 45.0%    alignment GAVE it Chinese
    Falcon3-7B    base  0.0%  ->  aligned 20.0%
    Falcon3-10B   base  5.0%  ->  aligned 25.0%
    neo_7b        base 20.0%  ->  aligned 15.0%

`contrast_models()` therefore requires BOTH arms over the threshold. Five lineages
qualify at 20%, seven at 10%, eight at 5% -- small, and honestly small: those
capability shifts are findings in their own right and belong in their own analysis,
not inside a register contrast.

## Degeneracy, with the archive's rule FIXED for Chinese

`_is_degenerate`'s first clause is `len(text.split()) < 5`, which on unspaced
Chinese returns one token for a whole passage and flags **41.2% of the zh corpus**.
Counting characters for zh brings that to 0.5%, en unchanged at 3.6%.

## What this cannot reach

Non-degenerate is not fluent. These rules catch repetition loops, near-empty output
and script mixing; they cannot catch single-script non-repetitive incoherence, which
the judges called broken in 71% of Chinese. The fluency verdicts cover 1,319 items
over 58 models -- use `verdicts()` where per-passage quality matters.
"""

import collections, json, os, re
from collections import Counter

ARCHIVE = "/Users/rj416/github/malign-logits/meta/M06_generation/results"
PARQUET = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                     os.path.expanduser("~/malignment-data")),
                       "jakobson_space", "passages.parquet")
CJK = re.compile(r"[㐀-鿿]")
LAT = re.compile(r"[A-Za-z]")
FLUENT_MIN = 20.0          # percent of judged continuations rated `fluent`
PURE_MIN = 0.90            # a passage is single-script outside (0.02, 0.90) cjk share


def verdicts():
    """(model, prompt, sample_idx) -> fluent|flawed|broken|not_chinese."""
    out = {}
    for vf, sf in (("zh_fluency_verdicts.json", "zh_fluency_sample.json"),
                   ("zh_fluency_verdicts_r2.json", "zh_fluency_sample_r2.json")):
        try:
            vd = json.load(open(os.path.join(ARCHIVE, vf)))
            tr = (json.load(open(os.path.join(ARCHIVE, sf))) or {}).get("truth") or {}
        except FileNotFoundError:
            continue
        for r in (vd if isinstance(vd, list) else vd.get("verdicts") or []):
            t = tr.get(r.get("key"))
            if t:
                out[(t["model"], t["prompt"], t["sample_idx"])] = r.get("verdict")
    return out


def fluency_rates():
    """model -> percent of its judged continuations rated `fluent`."""
    c = collections.defaultdict(Counter)
    for (m, _, _), v in verdicts().items():
        c[m][v] += 1
    return {m: 100.0 * x["fluent"] / sum(x.values()) for m, x in c.items() if sum(x.values())}


def zh_fluent(threshold=FLUENT_MIN):
    """Models that can write Chinese. UNJUDGED MODELS ARE NOT FLUENT: absence of a
    verdict is not evidence of competence, and 36 of the parquet's 94 models were
    never judged."""
    r = fluency_rates()
    return {m for m, v in r.items() if v >= threshold}


def contrast_models(threshold=FLUENT_MIN):
    """Aligned models whose lineage has BOTH arms Chinese-fluent. -> {aligned: base}"""
    from malignment import roster
    r = fluency_rates()
    out = {}
    for b, ms in roster.lineages().items():
        for m in ms:
            if m != b and r.get(m, 0) >= threshold and r.get(b, 0) >= threshold:
                out[m] = b
    return out


def cjk_share(text):
    nc, nl = len(CJK.findall(text)), len(LAT.findall(text))
    return nc / (nc + nl) if (nc + nl) else 0.0


def single_script(text):
    s = cjk_share(text)
    return s < 0.02 or s > PURE_MIN


def degenerate(text, script):
    """The archive's rule with its first clause made script-aware."""
    text = str(text)
    units = list(re.sub(r"\s+", "", text)) if script == "zh" else text.split()
    if len(units) < 5:
        return True
    if Counter(units).most_common(1)[0][1] / len(units) > 0.3:
        return True
    ch = [c for c in text if not c.isspace()]
    return bool(ch and Counter(ch).most_common(1)[0][1] / len(ch) > 0.3)


def standard(model, text, script, threshold=FLUENT_MIN, fluent=None):
    """RH's rule: all-Latin, or all-Chinese from a Chinese-fluent model. -> bool"""
    if degenerate(text, script) or not single_script(text):
        return False
    if cjk_share(text) < 0.02:
        return True                                   # all-Latin: kept
    return model in (zh_fluent(threshold) if fluent is None else fluent)


def describe(threshold=FLUENT_MIN):
    r = fluency_rates()
    f = zh_fluent(threshold)
    cm = contrast_models(threshold)
    return dict(models_judged=len(r), zero_fluent=sum(1 for v in r.values() if v == 0),
                fluent_at_threshold=sorted(f), threshold=threshold,
                contrast_lineages=len(cm), contrast_models=cm)


if __name__ == "__main__":
    import pyarrow.parquet as pq
    d = describe()
    print("fluency: %d models judged | %d with ZERO fluent | %d at >=%g%%"
          % (d["models_judged"], d["zero_fluent"], len(d["fluent_at_threshold"]),
             d["threshold"]))
    print("contrast lineages (BOTH arms fluent): %d" % d["contrast_lineages"])
    t = pq.read_table(PARQUET, columns=["model", "text", "script", "arm"])
    c = {k: t.column(k).to_pylist() for k in t.schema.names}
    f = zh_fluent()
    keep = [standard(c["model"][i], c["text"][i], c["script"][i], fluent=f)
            for i in range(len(c["text"]))]
    print("\npassages.parquet: %d rows -> %d kept (%.1f%%)"
          % (len(keep), sum(keep), 100 * sum(keep) / len(keep)))
    for s in ("en", "zh"):
        idx = [i for i in range(len(keep)) if c["script"][i] == s]
        print("  %-3s %7d -> %7d (%.1f%%)"
              % (s, len(idx), sum(keep[i] for i in idx),
                 100 * sum(keep[i] for i in idx) / len(idx)))
