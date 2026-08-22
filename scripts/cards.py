"""Can this card run this model? Compute capability against the declared need.

    python scripts/cards.py                       the table, and what it refuses
    python scripts/cards.py --offer "Q RTX 8000" --model google/gemma-2-9b

## bfloat16 IS NOT A PROPERTY OF THE MODEL ALONE

`requirements.json` stores `compute_dtype: bfloat16` per model. It is really a
property of **(model x card generation)**: bf16 arrives with Ampere, cc 8.0.
`Baichuan2` auto-selects bf16 and FAILS TO LOAD on a Turing Quadro RTX 8000
(cc 7.5) while loading fine on Ampere.

**WE HAVE BEEN LUCKY RATHER THAN CAREFUL.** The Quadro RTX 8000 is the most-
rented card in the corpus (48 of 116 gpu-labelled rate observations), the
`dense` box deliberately carries no `gpu_name` filter, offers sort by price, and
the cheapest 48 GB offer on the board is a `Q RTX 8000`. Twelve models declare
bfloat16 and none has landed on Turing yet. Nothing was stopping it.

## FAIL CLOSED ON A CARD WE CANNOT NAME

An unrecognised `gpu_name` is REFUSED for a bf16 requirement, never allowed.
The cost of refusing a good offer is one more search; the cost of accepting a
Turing card is a load failure after paying for the download -- and the failure
arrives late, on the box, wearing a dtype error that names neither the card nor
the reason.

The names are also spelled differently by different feeds -- the vast search
feed says `Q RTX 8000` where the rate store says `Quadro RTX 8000` -- so match
is normalised, and both spellings are declared.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

ENVS = os.path.join(ROOT, "roster", "environments.yaml")
BF16_MIN_CC = 8.0


def _norm(name):
    """Lowercase, strip vendor words and punctuation. `NVIDIA GeForce RTX 4090`
    and `RTX 4090` are one card; the feeds disagree about the prefix."""
    s = (name or "").lower()
    for w in ("nvidia", "geforce", "generation", "quadro"):
        s = s.replace(w, " ")
    return re.sub(r"[^a-z0-9]+", "", s)


def table():
    import yaml
    doc = yaml.safe_load(open(ENVS))
    raw = doc.get("cards") or {}
    return {_norm(k): v for k, v in raw.items()
            if not k.startswith("_") and isinstance(v, dict)}


def capability(gpu_name, cards=None):
    """(cc, arch) or (None, None) when the card is not declared."""
    c = (cards or table()).get(_norm(gpu_name))
    if not c:
        return None, None
    return c.get("compute_capability"), c.get("arch")


def ok_for(gpu_name, compute_dtype, cards=None):
    """(bool, why). Fails closed on an unknown card when bf16 is required."""
    if (compute_dtype or "") != "bfloat16":
        return True, "no bf16 requirement"
    cc, arch = capability(gpu_name, cards)
    if cc is None:
        return False, ("card %r is not declared in environments.yaml `cards:` -- "
                       "REFUSED because an unnamed card may be Turing. Add it "
                       "there once identified." % gpu_name)
    if cc < BF16_MIN_CC:
        return False, ("%s is %s, compute capability %.1f -- bfloat16 needs "
                       ">= %.1f (Ampere)" % (gpu_name, arch, cc, BF16_MIN_CC))
    return True, "%s cc %.1f >= %.1f" % (gpu_name, cc, BF16_MIN_CC)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offer", default=None, help="gpu_name from an offer")
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    cards = table()
    if a.offer:
        dt = None
        if a.model:
            import json
            req = {r["model"]: r for r in json.load(open(os.path.join(
                ROOT, "roster", "models", "requirements.json")))["requirements"]}
            dt = (req.get(a.model) or {}).get("compute_dtype")
            print("%s declares compute_dtype=%s" % (a.model, dt))
        good, why = ok_for(a.offer, dt or "bfloat16", cards)
        print("%s  %s" % ("OK   " if good else "REFUSE", why))
        return 0 if good else 1
    print("declared cards: %d" % len(cards))
    for k, v in sorted(cards.items(), key=lambda kv: kv[1]["compute_capability"]):
        bad = v["compute_capability"] < BF16_MIN_CC
        print("   %-22s cc %-5s %-8s%s" % (k, v["compute_capability"],
                                           v["arch"],
                                           "  <-- REFUSED for bf16" if bad else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
