"""Where in the stack does the transgressiveness fall? T(layer) for both arms.

    .venv/bin/python -u depth_lens.py --pair meta-llama/Llama-3.1-8B
    .venv/bin/python -u depth_lens.py --pair LLM360/Amber --top 6

`task_charge` gives a 1-7 rating for every candidate word in every cell. The
archive holds final-position residual streams, (n_layers+1, d_model) float32 per
prompt, for 16 endpoint pairs. Together those give

    T(arm, L) = sum(scene_w * p_L(w)) / sum(p_L(w))

a transgressiveness trajectory through depth, for base and aligned. Where the two
separate is where alignment does its work.

**NOTHING BEFORE THIS COULD ASK IT.** `twp_lens_perword.py` z-scores each word
against the others at each layer precisely because there was no per-word VALUE to
weight by -- it can say a word's gap stands out, not that the distribution became
less transgressive. The rating supplies the missing quantity.

## WHAT THE SIDECARS ALLOW, AND WHAT THEY DO NOT

They are the FINAL POSITION of the PROMPT, so the lens gives
`p_L(first token | prompt)` and nothing beyond. `twp_word_depth.py` reaches
multi-token words by the chain rule, `prod_i p_L(t_i | prompt + t_1..t_{i-1})`,
and every factor after the first needs a forward pass with the previous token
appended. One state per prompt means multi-token words are out of reach without
re-running the models.

**SO THE VOCABULARY IS SINGLE-TOKEN WORDS ONLY.** Measured on Llama-3.1-8B over
60 prompts and 462 rated words: 400 are single-token (87%), covering 87% of base
mass and 86% of aligned. That is the cost, and `covered` is printed per cell so
no trajectory is read without knowing what share of the distribution it rests on.

## THE UNEMBEDDING IS TWO TENSORS AND THE MODEL IS NEVER LOADED

safetensors memory-maps, so pulling the unembedding out of gemma-2-9b's 37GB
checkout takes 0.0s and touches no other shard. Model size is irrelevant.

Three things vary by architecture, and each produces a plausible wrong number
rather than an error if guessed:

    the unembedding   gemma has NO lm_head and reuses model.embed_tokens.weight;
                      bloom uses word_embeddings.weight with no `model.` prefix.
    the final norm    a logit lens is unembed(final_norm(h_L)), not unembed(h_L).
                      Skipping it is silently wrong at EVERY layer.
    the norm's form   RMSNorm for Llama/gemma/glm; gemma stores its weight as
                      w-1 and the forward pass adds 1. LayerNorm where a bias
                      exists.

**AND ONE THAT ALREADY BIT.** A first-match scan shard-by-shard ignores the
preference order. Llama-3.1-8B carries BOTH `model.embed_tokens.weight` (shard 1)
and `lm_head.weight` (last shard) and is NOT tied, so the scan unembedded with
the INPUT embedding. It raised nothing: it returned a diffuse softmax, near-zero
mass on the words that carry the distribution, and base/aligned trajectories
differing by 0.04 where the output layer differs by 2.5. `head()` now indexes
every shard before choosing, and `covered` at the last layer is the diagnostic
that caught it -- a lens whose rated words hold no mass at the top of the stack
is not measuring the model.
"""

import argparse
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
CHARGE = os.path.join(DATA, "dose_response", "charge_en50_flash.jsonl")
ARCHIVE = "/Users/rj416/github/malign-logits/data/f11_twp"
HUB = os.path.expanduser("~/.cache/huggingface/hub")

#: preference order, most specific first. Applied ACROSS all shards, never
#: within one -- see the docstring.
UNEMBED = ("lm_head.weight", "model.embed_tokens.weight",
           "transformer.word_embeddings.weight", "word_embeddings.weight",
           "backbone.embedding.weight")
FINALNORM = ("model.norm.weight", "transformer.ln_f.weight", "ln_f.weight",
             "model.final_layernorm.weight", "backbone.norm_f.weight")
NORMBIAS = ("transformer.ln_f.bias", "ln_f.bias")


def snapshot(mid):
    d = os.path.join(HUB, "models--" + mid.replace("/", "--"), "snapshots")
    s = sorted(glob.glob(os.path.join(d, "*")))
    return s[-1] if s else None


def head(mid):
    """(W_unembed, norm_weight, norm_bias, name_used) without loading the model."""
    from safetensors import safe_open
    snap = snapshot(mid)
    if not snap:
        raise FileNotFoundError("not cached: %s" % mid)
    files = sorted(glob.glob(os.path.join(snap, "*.safetensors")))
    if not files:
        raise FileNotFoundError("no safetensors: %s" % mid)
    where = {}
    for f in files:
        with safe_open(f, framework="pt") as g:
            for k in g.keys():
                if k in UNEMBED or k in FINALNORM or k in NORMBIAS:
                    where.setdefault(k, f)

    def pull(names):
        for k in names:
            if k in where:
                with safe_open(where[k], framework="pt") as g:
                    return g.get_tensor(k), k
        return None, None

    W, used = pull(UNEMBED)
    if W is None:
        raise KeyError("no unembedding in %s (have %s)" % (mid, sorted(where)[:8]))
    nw, _ = pull(FINALNORM)
    nb, _ = pull(NORMBIAS)
    return W, nw, nb, used


def apply_norm(h, nw, nb, gemma, torch):
    """RMSNorm unless a bias is present, in which case LayerNorm."""
    h = h.float()
    if nw is None:
        return h
    if nb is not None:
        m = h.mean(-1, keepdim=True)
        v = h.var(-1, keepdim=True, unbiased=False)
        return (h - m) / torch.sqrt(v + 1e-5) * nw.float() + nb.float()
    rms = torch.rsqrt(h.pow(2).mean(-1, keepdim=True) + 1e-6)
    return h * rms * (nw.float() + (1.0 if gemma else 0.0))


def hidden(mid):
    """(array (rows, n_layers+1, d_model), prompts) from the sidecar."""
    import numpy as np
    man = json.load(open(os.path.join(ARCHIVE, "hidden_manifest.json")))["models"]
    if mid not in man:
        raise KeyError("no hidden states for %s" % mid)
    e = man[mid]
    a = np.fromfile(os.path.join(ARCHIVE, e["file"]), dtype="float32")
    return a.reshape((e["rows"],) + tuple(e["shape_per_row"])), e["prompts"]


def rated(prompts):
    """{prompt: {base: {word: scene}}} for the cells we hold ratings on."""
    want = set(prompts)
    out = collections.defaultdict(dict)
    for line in open(CHARGE):
        r = json.loads(line)
        if r["prompt"] in want:
            out[r["prompt"]][r["base"]] = {w["word"]: w["scene"] for w in r["words"]}
    return out


def trajectory(mid, ratings, tok, torch, only=None):
    """{prompt: (T_by_layer, covered_mass_last, n_words)}."""
    A, plist = hidden(mid)
    W, nw, nb, _ = head(mid)
    gemma = "gemma" in mid.lower()
    Wt = W.float().t()
    out = {}
    for i, p in enumerate(plist):
        if only is not None and p not in only:
            continue
        sc = ratings.get(p, {})
        if not sc:
            continue
        #: ratings are per (prompt, LINEAGE); average over every lineage that
        #: rated this prompt, so the weight is a property of the word-in-frame
        #: rather than of one rater call.
        agg = collections.defaultdict(list)
        for d in sc.values():
            for w, s in d.items():
                agg[w].append(s)
        scene = {w: sum(v) / len(v) for w, v in agg.items()}
        ids, keep = [], []
        for w in scene:
            t = tok.encode(" " + w, add_special_tokens=False)
            if len(t) == 1:
                ids.append(t[0]); keep.append(w)
        if len(keep) < 4:
            continue
        wt = torch.tensor([scene[w] for w in keep])
        h = torch.from_numpy(A[i])
        Ts, cov = [], float("nan")
        for L in range(h.shape[0]):
            pr = torch.softmax(apply_norm(h[L], nw, nb, gemma, torch) @ Wt, -1)
            pw = pr[ids]
            s = float(pw.sum())
            Ts.append(float((pw * wt).sum() / s) if s > 0 else float("nan"))
            if L == h.shape[0] - 1:
                cov = s
        out[p] = (Ts, cov, len(keep))
    return out


def main(argv=None):
    import torch
    from transformers import AutoTokenizer
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="meta-llama/Llama-3.1-8B")
    ap.add_argument("--aligned")
    ap.add_argument("--top", type=int, default=6)
    a = ap.parse_args(argv)
    from malignment import roster
    eps, _ = roster.endpoints()
    aligned = a.aligned or eps[a.pair]
    print("%s -> %s" % (a.pair, aligned))

    _, plist = hidden(a.pair)
    R = rated(plist)
    #: highest-dose prompts first -- a trajectory on a frame with nothing charged
    #: is a flat line at 1.0 and says nothing about depth.
    dose = {}
    for p, cells in R.items():
        v = [s for d in cells.values() for s in d.values()]
        dose[p] = sum(v) / len(v) if v else 0.0
    pick = set(sorted(dose, key=lambda p: -dose[p])[:a.top])
    print("sidecar prompts %d | rated %d | tracing the %d highest-dose"
          % (len(plist), len(R), len(pick)))
    W, nw, nb, used = head(a.pair)
    print("unembed %s %s | norm %s | bias %s"
          % (used, tuple(W.shape), "yes" if nw is not None else "NONE",
             "yes" if nb is not None else "no"))

    tb = trajectory(a.pair, R, tok := AutoTokenizer.from_pretrained(a.pair),
                    torch, only=pick)
    ta = trajectory(aligned, R, tok, torch, only=pick)
    common = [p for p in tb if p in ta]
    print()
    for p in sorted(common, key=lambda p: -dose[p]):
        Tb, cb, n = tb[p]; Ta, ca, _ = ta[p]
        nL = len(Tb)
        idx = [0, nL // 4, nL // 2, 3 * nL // 4, nL - 1]
        print("  %r   dose %.2f" % (p[:62], dose[p]))
        print("     %d single-token words | mass at last layer: base %.3f aligned %.3f"
              % (n, cb, ca))
        print("     layer  %s" % "  ".join("%6d" % i for i in idx))
        print("     base   %s" % "  ".join("%6.2f" % Tb[i] for i in idx))
        print("     algn   %s" % "  ".join("%6.2f" % Ta[i] for i in idx))
        print("     diff   %s" % "  ".join("%+6.2f" % (Tb[i] - Ta[i]) for i in idx))
        d = [Tb[i] - Ta[i] for i in range(nL)]
        k = max(range(nL), key=lambda i: abs(d[i]))
        print("     largest separation %+.2f at layer %d of %d" % (d[k], k, nL - 1))
        print()


if __name__ == "__main__":
    main()
