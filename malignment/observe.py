"""Produce `roster/models/measurements.json` — the OBSERVED side of the roster.

    python -m malignment.observe                 what is missing, measure nothing
    python -m malignment.observe --weights       params_b from the HF API
    python -m malignment.observe --revisions     branch/tag ladders from the HF API
    python -m malignment.observe --tokenizer     vocab sizes (needs the tokenizers)

## WHERE THE PRODUCER LIVES, AND WHY NOT `scripts/`

The archive's `weights_audit.py` opens with the reason: *"It began as a live query
during the v3 grid run, which is exactly the shape the canonical model file
forbids: a measured field whose producer is a shell history. **Measured facts name
the script and commit that produced them**, or the file documents a different
object than the one that ran."*

It then sat in `scripts/` as 1 of 478, which is how it came to read a nine-day-old
roster and measure two thirds of the models while reporting success. So this lives
beside `roster.py`, the thing that consumes it.

## ONE FILE, ONE SECTION PER PASS, EACH STAMPED

Passes are INDEPENDENT and MERGE. `--weights` rewrites only the `weights` section
and its stamp; nothing else in the file is touched. A pass that cannot reach a
model records it under `unmeasured` WITH THE REASON rather than omitting it —
absence and failure are the same shape in a JSON, and telling them apart after
the fact is impossible.

## WHAT EACH PASS COSTS

    weights     one HfApi call per model, no download, no GPU. Returns None where
                a repo publishes no safetensors metadata — a real answer, not a
                failure, and recorded as such.
    revisions   one HfApi call per model. Branches + tags.
    tokenizer   needs the tokenizer files locally; the slowest and the only one
                that can be blocked by a gated repo.
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBSERVED = os.path.join(ROOT, "roster", "models", "measurements.json")


def load():
    with open(OBSERVED, encoding="utf-8") as fh:
        return json.load(fh)


def roster_ids():
    """Every declared checkpoint. The population is the AUTHORED file, so a model
    added to `models.yaml` is measurable on the next run with nothing to remember."""
    import yaml
    with open(os.path.join(ROOT, "roster", "models", "models.yaml"), encoding="utf-8") as fh:
        return sorted((yaml.safe_load(fh).get("nodes") or {}))


def _stamp(sec, by, n, unmeasured=None):
    sec["measured_by"] = by
    sec["measured_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    sec["n"] = n
    #: NAMED, NOT OMITTED. A model absent from a section is indistinguishable
    #: from one the pass could not reach, and that ambiguity is what turned
    #: `vocab_size: null` into "unmeasured" when it meant "the join dropped it".
    sec["unmeasured"] = unmeasured or {}
    return sec


def weights(doc, ids, only_missing=True):
    from huggingface_hub import HfApi
    sec = doc["sections"].setdefault("weights", {"models": {}})
    have = sec.get("models") or {}
    todo = [m for m in ids if not (only_missing and m in have)]
    print("  weights: %d to measure (%d already present)" % (len(todo), len(have)))
    api = HfApi()
    bad = dict(sec.get("unmeasured") or {})
    for i, m in enumerate(todo, 1):
        try:
            info = api.model_info(m, expand=["safetensors"])
            st = getattr(info, "safetensors", None)
            total = getattr(st, "total", None) if st else None
            if not total:
                bad[m] = "no safetensors metadata published"
                continue
            have[m] = {"params_b": round(total / 1e9, 4),
                       "n_params": int(total), "source": "hf_api:safetensors"}
            bad.pop(m, None)
        except Exception as e:
            bad[m] = "%s: %s" % (type(e).__name__, str(e)[:80])
        if i % 20 == 0:
            print("     %d/%d" % (i, len(todo)))
    sec["models"] = have
    _stamp(sec, "huggingface_hub HfApi().model_info(expand=['safetensors'])",
           len(have), bad)
    return len(todo), len(bad)


def revisions(doc, ids, only_missing=True):
    from huggingface_hub import HfApi
    sec = doc["sections"].setdefault("revision_ladders", {"models": {}})
    have = sec.get("models") or {}
    todo = [m for m in ids if not (only_missing and m in have)]
    print("  revisions: %d to survey (%d present)" % (len(todo), len(have)))
    api = HfApi(); bad = dict(sec.get("unmeasured") or {})
    for i, m in enumerate(todo, 1):
        try:
            refs = api.list_repo_refs(m)
            n = len(refs.branches or []) + len(refs.tags or [])
            #: ONLY MULTI-REVISION REPOS ARE RECORDED. A repo with one branch has
            #: no ladder, and storing 1 for it would make "has a trajectory" a
            #: property of every model.
            if n > 1:
                have[m] = n
            bad.pop(m, None)
        except Exception as e:
            bad[m] = "%s: %s" % (type(e).__name__, str(e)[:80])
        if i % 25 == 0:
            print("     %d/%d" % (i, len(todo)))
    sec["models"] = have
    _stamp(sec, "huggingface_hub HfApi().list_repo_refs (branches + tags)",
           len(have), bad)
    return len(todo), len(bad)


#: Repo files that identify the tokenizer's SURFACE CONVENTION. This is the
#: property that matters here: SentencePiece writes a word-boundary marker into
#: the token surface (`▁the`) and falls back to raw bytes (`<0xE5>`) for
#: unknown characters, so a twp producer that assembles in token space leaves
#: fingerprints. BPE-family tokenizers leave `Ġ` instead.
_SP_FILES = ("tokenizer.model", "sentencepiece.bpe.model", "spiece.model")


def tokenizers(doc, ids, only_missing=True):
    """Which tokenizer convention each checkpoint uses -- ONE API call, no download.

    ## WHY THIS IS A ROSTER FIELD AND NOT A FOOTNOTE

    `dolphin-2.6-mistral-7b-dpo` reached the store with 82.2% of its word rows in
    TOKEN space -- `'▁the'` for `'the'`, plus byte-fallback tokens -- and passed
    every gate ingest had, because all of them test mass and token probabilities
    sum to 1.0 just as word probabilities do. `ingest.token_space` now refuses
    that shape outright.

    **But the defect is in OUR producer, not in the model**, so a gate tells you a
    checkpoint failed and this tells you which checkpoints could fail. A model
    with a SentencePiece tokenizer and byte fallback is one where the twp
    assembly has something to get wrong; a BPE model without byte fallback is
    not. That is a preflight question -- the runbook's rule, paid for by the L2
    fleet -- and it wants a measured field, not a memory.

    `list_repo_files` is one call and downloads nothing.
    """
    from huggingface_hub import HfApi
    sec = doc["sections"].setdefault("tokenizers", {"models": {}})
    have = sec.get("models") or {}
    todo = [m for m in ids if not (only_missing and m in have)]
    print("  tokenizers: %d to survey (%d present)" % (len(todo), len(have)))
    api = HfApi()
    bad = dict(sec.get("unmeasured") or {})
    for i, m in enumerate(todo, 1):
        try:
            files = set(api.list_repo_files(m))
            sp = sorted(f for f in files if f in _SP_FILES)
            have[m] = {
                "sentencepiece": bool(sp),
                "sp_files": sp,
                "has_tokenizer_json": "tokenizer.json" in files,
                #: NAMED, so a later reader can tell "surveyed and found none"
                #: from "never surveyed" without consulting the stamp.
                "marker_risk": "sentencepiece" if sp else "bpe_or_unknown",
                "source": "hf_api:list_repo_files",
            }
            bad.pop(m, None)
        except Exception as e:
            bad[m] = "%s: %s" % (type(e).__name__, str(e)[:80])
        if i % 25 == 0:
            print("     %d/%d" % (i, len(todo)))
    sec["models"] = have
    _stamp(sec, "huggingface_hub HfApi().list_repo_files", len(have), bad)
    return len(todo), len(bad)



#: The archive's tiering, kept verbatim so a tier written here means what a tier
#: written there meant: `scripts/build_cjk_coverage.py`, cut on the COUNT of CJK
#: characters the vocabulary holds.
CJK_TIERS = [(3500, "FLUENT"), (2500, "MARGINAL"), (1000, "PARTIAL"), (0, "NOMINAL")]


def vocab(doc, ids, only_missing=True):
    """CJK coverage and the decoded-boundary miss, from the tokenizer itself.

    ## WHY THESE TWO TOGETHER

    `measurements.json`'s own `_why_one_file` names `cjk_coverage.csv` as one of
    the SIX archive artifacts that each defined "the set of models" separately
    and drifted. **The archive's `cjk_tier` never crossed over**, so it is
    reachable only in `malign-logits/data/model_registry.json`, which is
    read-only -- and the v4 boundary work needs it. Folding it in here rather
    than porting the CSV is the whole point of the consolidation.

    `decode_miss` joins it because it is the same KIND of fact about the same
    population, measured the same way, and a separate artifact for it would be
    the seventh drifting file.

    ## WHAT EACH IS, PRECISELY

    `cjk_chars` counts CJK characters PRESENT IN THE VOCABULARY. It is a property
    of the tokenizer, not of the model's fluency -- the tier name reads like
    capability and the measurement is composition. Anything claiming the model
    "knows Chinese" needs a different measurement than this one.

    `decode_miss` counts ids whose DECODED first character is punctuation that
    `boundary_mask` fails to mark, because it tests the raw representation:
    byte-level spells the CJK comma `ï¼Į` and sentencepiece spells a
    word-initial em dash `▁—`, so neither key is ever the mark. Measured
    2026-08-17 at 88 of 88 roster tokenizers affected, median 72 ids -- **it is
    neither a CJK defect nor a byte-level one**, which is why the CJK-range
    subcount is reported separately from the total.

    Needs the tokenizer itself, so unlike `tokenizers` this one downloads.
    """
    import re

    from . import twp as T
    from . import twp_v4 as V4

    #: **THE ARCHIVE'S REGEX, NOT A WIDER ONE.** `[一-鿿㐀-䶿]` is CJK Unified
    #: Ideographs plus Extension A. My first version used `ord(c) >= 0x2E80`,
    #: which also catches kana, CJK punctuation and radicals, and inflated every
    #: count ~3x against the archive -- a tier that agrees with theirs only if it
    #: counts what theirs counted.
    cjk_re = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")

    sec = doc["sections"].setdefault("vocab", {"models": {}})
    have = sec.get("models") or {}
    todo = [m for m in ids if not (only_missing and m in have)]
    print("  vocab: %d to measure (%d present)" % (len(todo), len(have)))
    bad = dict(sec.get("unmeasured") or {})
    for i, m in enumerate(todo, 1):
        try:
            #: **THROUGH THE LOADER TABLE, NOT AutoTokenizer.** The archive's
            #: producer says why: *"The first build measured deepseek at 0 CJK
            #: characters, which was the broken loader's output and not a fact
            #: about the model."* `load_tokenizer` honours LOADER_OVERRIDE; I
            #: used AutoTokenizer first and would have re-measured that bug.
            tok, _loader = T.load_tokenizer(m)
            chars, n_tok = set(), 0
            for j in range(len(tok)):
                try:
                    t = tok.decode([j])
                except Exception:                               # noqa: BLE001
                    continue
                found = cjk_re.findall(t or "")
                if found:
                    chars.update(found)
                    n_tok += 1
            #: **DISTINCT CHARACTERS, and the tier is cut on THESE.** Counting
            #: TOKENS and calling the field `cjk_chars` is what my first version
            #: did, and it disagreed with the archive on 12 of 45 shared models
            #: while looking like a measurement of the same thing.
            n_cjk = len(chars)
            tier = next(name for cut, name in CJK_TIERS if n_cjk >= cut)
            try:
                miss = V4.decoded_boundary_ids(tok)
                table, notation = V4.byte_table(tok)
                n_miss = int(len(miss))
                n_miss_cjk = sum(
                    1 for k in miss
                    if (table[int(k)] or b"").decode("utf-8", "ignore").lstrip(" ")[:1]
                    and ord((table[int(k)] or b"").decode("utf-8", "ignore")
                            .lstrip(" ")[0]) >= 0x2E80)
                notation_err = None
            except Exception as e:                              # noqa: BLE001
                #: a tokenizer whose byte notation cannot be VERIFIED gets a
                #: named refusal, not a zero -- absence must not read as clean.
                n_miss = n_miss_cjk = None
                notation = None
                notation_err = str(e)[:80]
            have[m] = {
                "vocab_len": len(tok),
                "cjk_chars": n_cjk,
                "cjk_tokens": n_tok,
                "cjk_tier": tier,
                "byte_notation": notation,
                "decode_miss": n_miss,
                "decode_miss_cjk": n_miss_cjk,
                "decode_miss_error": notation_err,
                "source": "AutoTokenizer + twp_v4.decoded_boundary_ids",
            }
            bad.pop(m, None)
        except Exception as e:                                  # noqa: BLE001
            bad[m] = str(e)[:120]
        if i % 20 == 0:
            print("    %d/%d" % (i, len(todo)), flush=True)
    sec["models"] = have
    _stamp(sec, "malignment.observe.vocab", len(have), bad)
    return len(todo), len(bad)


def report(doc, ids):
    print("  roster declares %d checkpoints\n" % len(ids))
    for name, sec in doc.get("sections", {}).items():
        have = set(sec.get("models") or {})
        miss = [m for m in ids if m not in have]
        bad = sec.get("unmeasured") or {}
        print("  %-18s %3d measured | %3d not | %d recorded unmeasurable"
              % (name, len(have & set(ids)), len(miss), len(bad)))
        print("     measured_at %s" % sec.get("measured_at", "(unstamped)"))
        for m in miss[:4]:
            print("       missing: %s" % m)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", action="store_true")
    ap.add_argument("--revisions", action="store_true")
    ap.add_argument("--tokenizer", action="store_true")
    ap.add_argument("--vocab", action="store_true",
                    help="cjk coverage + decoded-boundary miss (DOWNLOADS tokenizers)")
    ap.add_argument("--all", action="store_true", help="re-measure, not just gaps")
    a = ap.parse_args()
    doc, ids = load(), roster_ids()
    if not (a.weights or a.revisions or a.tokenizer or a.vocab):
        return report(doc, ids)
    if a.weights:
        n, bad = weights(doc, ids, only_missing=not a.all)
        print("  weights: attempted %d, %d unmeasurable" % (n, bad))
    if a.revisions:
        n, bad = revisions(doc, ids, only_missing=not a.all)
        print("  revisions: attempted %d, %d unmeasurable" % (n, bad))
    if a.tokenizer:
        n, bad = tokenizers(doc, ids, only_missing=not a.all)
        print("  tokenizers: attempted %d, %d unmeasurable" % (n, bad))
    if a.vocab:
        n, bad = vocab(doc, ids, only_missing=not a.all)
        print("  vocab: attempted %d, %d unmeasurable" % (n, bad))
    with open(OBSERVED, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    print("\n  wrote %s" % os.path.relpath(OBSERVED, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
