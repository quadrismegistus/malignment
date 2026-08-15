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
    ap.add_argument("--all", action="store_true", help="re-measure, not just gaps")
    a = ap.parse_args()
    doc, ids = load(), roster_ids()
    if not (a.weights or a.revisions or a.tokenizer):
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
    with open(OBSERVED, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    print("\n  wrote %s" % os.path.relpath(OBSERVED, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
