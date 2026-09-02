"""Does the chat frame move the word distribution, and does it depend on alignment stage?

    python run.py --scan     the design, nothing measured
    python run.py --run

A PILOT, not a sweep. Its job is to say whether the full rung-B sweep in
`docs/prefill.md` is worth buying, and to fix the measures before it is.

## THE DESIGN

    models      the Olmo-3 ladder  base -> SFT -> DPO -> Instruct
                plus two other vendors, so a result is not one family's habit
    prompts     stratified from the DECLARED population, `corpus.domains()`,
                with NEUTRAL as a control
    conditions  raw | prefill system="" | prefill system=DEFAULT

## WHY THE LADDER

The question is not "does a template change the numbers" -- it does. It is
whether the change is a property of ALIGNMENT. A ladder answers that in one run:
if the frame effect grows from base to SFT to DPO to Instruct, it tracks
alignment; if it is flat, it is a property of chat-templated models generally.

Measured on one prompt before this existed: base entropy barely moves under
framing (5.20 -> 5.12, 5.52 -> 5.30, 5.57 -> 5.84 on three base arms) while
aligned arms collapse ~3 bits (kanana-instruct 4.33 -> 1.37). That is the
observation this pilot exists to test properly.

## WHY NEUTRAL PROMPTS ARE NOT OPTIONAL

Every transgressive prompt measured under a frame will show the distribution
move. Without a neutral arm there is no way to tell "the frame suppresses
transgression" from "the frame changes every distribution", and the first is a
finding while the second is a fact about templates. `corpus.domains()` declares
205 neutral prompts; the pilot takes its control from there rather than from an
invented string.

## WHY THE MEASURES ARE LEXICON-FREE

`kill`-counting produced two claims in one afternoon that did not survive: "the
turn structure raises kill" (3 of 4 base arms, one contradicting, n=1 prompt) and
"the vendor persona suppresses violent completions in an unaligned base" (46.6x
on Qwen2.5-7B; 1.3x on Qwen2.5-0.5B with the IDENTICAL persona string, and 1.2x
on neo_7b whose persona is the 507-character Llama-2 safety preamble).

A lexicon is a category judgement wearing a number. Entropy, tail mass, support
size and JS between conditions need no such judgement, and a lexical follow-up
can be run on whatever the lexicon-free measures single out.

## SELECTION IS DECLARED AND BLIND TO THE OUTCOME

Prompts are taken in stable-hash order within each domain -- not by coverage, not
by how interesting they look. A prompt chosen because it moves is a prompt that
conditions every later interval on the selection.
"""
import argparse
import collections
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "frame_pilot.json")

#: The ladder is first so a partial run still answers the ladder question.
MODELS = [
    ("allenai/Olmo-3-1025-7B",      "base"),
    ("allenai/Olmo-3-7B-Instruct-SFT", "sft"),
    ("allenai/Olmo-3-7B-Instruct-DPO", "dpo"),
    ("allenai/Olmo-3-7B-Instruct",     "instruct"),
    ("Qwen/Qwen2.5-7B-Instruct",       "other-vendor"),
    ("HuggingFaceTB/SmolLM2-360M-Instruct", "other-vendor-small"),
]
DOMAINS = ["neutral", "violence", "sexual", "institutional"]
PER_DOMAIN = 3


def _is_latin(p):
    """No CJK. **LANGUAGE IS HELD CONSTANT OR IT CONFOUNDS THE DOMAIN.**

    The first draft of this selection took stable-hash order within domain,
    which is outcome-blind and still produced a design where ALL THREE neutral
    controls were Chinese and every other domain was English. A neutral-vs-
    violence difference would then have been partly a script difference -- and
    v4's `decoded_boundary` rule bites on byte-level CJK surfaces and nowhere
    else, so the instrument itself differs across that split.

    Outcome-blind is not the same as confound-free. CJK deserves its own run
    with the language declared, not a third of one arm.
    """
    return not any("一" <= c <= "鿿" or "぀" <= c <= "ヿ"
                   or "가" <= c <= "힯" for c in p)


def pick_prompts():
    """N per domain, in stable-hash order. Deterministic, outcome-blind."""
    from malignment import corpus
    dom = corpus.domains()
    by = collections.defaultdict(list)
    for p, d in dom.items():
        if d in DOMAINS and _is_latin(p):
            by[d].append(p)
    out = []
    for d in DOMAINS:
        ps = sorted(by[d], key=lambda p: hashlib.sha256(p.encode()).hexdigest())
        out += [(d, p) for p in ps[:PER_DOMAIN]]
    return out


def entropy(w):
    tot = sum(w.values())
    if not tot:
        return 0.0
    return -sum((p / tot) * math.log2(p / tot) for p in w.values() if p > 0)


def js(p, q):
    """Jensen-Shannon over the union support, in bits. Residual excluded --
    the comparison here is between SCORED distributions and the tail is
    reported separately rather than folded in."""
    out = 0.0
    for k in set(p) | set(q):
        a, b = p.get(k, 0.0), q.get(k, 0.0)
        m = (a + b) / 2.0
        if a > 0:
            out += 0.5 * a * math.log2(a / m)
        if b > 0:
            out += 0.5 * b * math.log2(b / m)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    prompts = pick_prompts()
    print("  models   %d (%s)" % (len(MODELS), ", ".join(t for _, t in MODELS)))
    print("  prompts  %d across %s" % (len(prompts), ", ".join(DOMAINS)))
    for d, p in prompts:
        print("     %-14s %r" % (d, p[:58]))
    print("  conditions raw | prefill sys='' | prefill DEFAULT")
    print("  cells    up to %d" % (len(MODELS) * len(prompts) * 3))
    if not a.run:
        print("\n  --scan: nothing measured.")
        return 0

    from malignment import Checkpoint, twp as T
    from malignment.twp_v4 import ADOPTED
    from malignment.generate import DEFAULT
    CONDS = [("raw", dict(frame=None)),
             ("empty", dict(frame="prefill", system="")),
             ("default", dict(frame="prefill", system=DEFAULT))]
    rows = []
    for mid, stage in MODELS:
        try:
            ck = Checkpoint(mid)
            ld = ck.load()
        except Exception as e:                                   # noqa: BLE001
            print("  %-38s LOAD FAILED %s" % (mid, str(e)[:50]))
            continue
        try:
            for dom, p in prompts:
                cells = {}
                for cname, kw in CONDS:
                    try:
                        w, r = ck.next_word(p, loaded=ld, rules=ADOPTED, **kw)
                        cells[cname] = (w, r)
                    except Exception as e:                       # noqa: BLE001
                        cells[cname] = ("ERR", type(e).__name__)
                rec = {"model": mid, "stage": stage, "domain": dom, "prompt": p}
                for cname, v in cells.items():
                    if v[0] == "ERR":
                        rec[cname] = {"error": v[1]}
                        continue
                    w, r = v
                    rec[cname] = {"n": len(w), "tail": r["tail"],
                                  "H": entropy(w),
                                  "top": sorted(w.items(), key=lambda kv: -kv[1])[:5]}
                for a_, b_ in (("raw", "default"), ("raw", "empty"),
                               ("empty", "default")):
                    if cells[a_][0] != "ERR" and cells[b_][0] != "ERR":
                        rec["js_%s_%s" % (a_, b_)] = js(cells[a_][0], cells[b_][0])
                rows.append(rec)
                print("  %-30s %-14s H raw %.2f -> dflt %.2f  JS %.4f"
                      % (mid.split("/")[-1][:30], dom,
                         rec.get("raw", {}).get("H", float("nan")),
                         rec.get("default", {}).get("H", float("nan")),
                         rec.get("js_raw_default", float("nan"))), flush=True)
        finally:
            ld = None
            T.free()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rows, open(OUT, "w"), indent=1)
    print("\n  wrote %s (%d rows)" % (OUT, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
