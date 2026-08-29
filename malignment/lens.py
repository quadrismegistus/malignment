"""A logit lens over archived residual streams, without loading the models.

    from malignment import lens
    W, nw, nb, used, cfg = lens.head("meta-llama/Llama-3.1-8B")
    H, prompts = lens.hidden("meta-llama/Llama-3.1-8B")
    P = lens.layer_probs(H[0], W, nw, nb, cfg, ids, gemma=False)

The archive holds final-position residual streams as `.f32` sidecars,
`(n_layers+1, d_model)` float32 per prompt, for the pairs listed in
`hidden_manifest.json`. A lens over them is `unembed(final_norm(h_L))`, which
gives `p_L(first token | prompt)` at every depth for a model that is never run.

## THE UNEMBEDDING IS TWO TENSORS AND THE MODEL IS NEVER LOADED

safetensors memory-maps, so pulling the unembedding out of gemma-2-9b's 37GB
checkout takes 0.0s and touches no other shard. **Model size is irrelevant to
this module** -- a 70B checkout costs the same as a 1B one.

Four things vary by architecture, and every one of them produces a plausible
wrong number rather than an error if guessed:

    the unembedding   gemma has NO lm_head and reuses model.embed_tokens.weight;
                      bloom uses word_embeddings.weight with no `model.` prefix.
    the final norm    a logit lens is unembed(final_norm(h_L)), not unembed(h_L).
                      Skipping it is silently wrong at EVERY layer.
    the norm's form   RMSNorm for Llama/gemma/glm; gemma stores its weight as
                      w-1 and the forward pass adds 1. LayerNorm where a bias
                      exists.
    two config scalars  gemma-2 caps output logits at 30
                      (`final_logit_softcapping`); without it the logits are
                      unbounded, the softmax collapses onto one token, and the
                      lens reports full coverage with a confident-looking peak at
                      layer 0. granite DIVIDES its logits by 16
                      (`logits_scaling`); skipping that gave zero coverage.
                      Both raised nothing and both produced full trajectories.

**AND ONE THAT ALREADY BIT.** A first-match scan shard-by-shard ignores the
preference order. Llama-3.1-8B carries BOTH `model.embed_tokens.weight` (shard 1)
and `lm_head.weight` (last shard) and is NOT tied, so the scan unembedded with
the INPUT embedding. It raised nothing: it returned a diffuse softmax, near-zero
mass on the words that carry the distribution, and base/aligned trajectories
differing by 0.04 where the output layer differs by 2.5. `head()` indexes every
shard before choosing, and coverage at the last layer is the diagnostic that
caught it -- a lens whose target words hold no mass at the top of the stack is
not measuring the model.

## COVERAGE IS NOT OPTIONAL, AND IT IS DEPTH-DEPENDENT

`layer_probs` returns the full probability vector over `ids` at every layer so
the caller can compute coverage -- the target words' share of total mass -- at
each depth rather than only at the output. **Below roughly three-quarters of the
stack that share is ~0 on every model measured** (0.000-0.044 across six pairs),
and on recurrentgemma-9b it is exactly 0.000 until the final layer. A difference
computed there is a difference between two normalisations of nothing. Any
statistic over depth needs a coverage floor or it reports lens noise as an early
effect; without one, an onset statistic put Llama-3.1-8B at 0.20 of the stack,
and with a 0.20 floor the same data puts it at 0.92.

## WHAT THE SIDECARS DO NOT ALLOW

They are the FINAL POSITION of the PROMPT, so the lens gives
`p_L(first token | prompt)` and nothing beyond. Multi-token words need the chain
rule, `prod_i p_L(t_i | prompt + t_1..t_{i-1})`, and every factor after the first
needs a forward pass with the previous token appended. One state per prompt means
**multi-token words are out of reach without re-running the models**, so callers
work with a single-token vocabulary. On Llama-3.1-8B over 60 prompts and 462
rated words, 400 are single-token (87%), covering 87% of base mass and 86% of
aligned.
"""

import glob
import json
import os

HUB = os.path.expanduser("~/.cache/huggingface/hub")

#: the `.f32` residual-stream sidecars. Written by the v2 twp runs and left in
#: the archive repo, which is READ-ONLY -- nothing here writes to it.
ARCHIVE = os.environ.get(
    "MALIGNMENT_HIDDEN",
    "/Users/rj416/github/malign-logits/data/f11_twp",
)

#: preference order, most specific first. Applied ACROSS all shards, never
#: within one -- see the docstring.
UNEMBED = ("lm_head.weight", "model.embed_tokens.weight",
           "transformer.word_embeddings.weight", "word_embeddings.weight",
           "backbone.embedding.weight")
FINALNORM = ("model.norm.weight", "transformer.ln_f.weight", "ln_f.weight",
             "model.final_layernorm.weight", "backbone.norm_f.weight")
NORMBIAS = ("transformer.ln_f.bias", "ln_f.bias")


def snapshot(mid):
    """The newest cached snapshot directory for a model id, or None."""
    d = os.path.join(HUB, "models--" + mid.replace("/", "--"), "snapshots")
    s = sorted(glob.glob(os.path.join(d, "*")))
    return s[-1] if s else None


def head(mid):
    """(W_unembed, norm_weight, norm_bias, name_used, cfg) without loading the model.

    **NOT safetensors ONLY.** Three of the sixteen archived pairs are cached as
    `pytorch_model.bin` and the first sweep lost them to a missing branch rather
    than to anything about the models. `torch.load(mmap=True)` keeps it a partial
    read: the tensors stay on disk until indexed.
    """
    import torch
    from safetensors import safe_open
    snap = snapshot(mid)
    if not snap:
        raise FileNotFoundError("not cached: %s" % mid)
    cfg = {}
    cp = os.path.join(snap, "config.json")
    if os.path.exists(cp):
        cfg = json.load(open(cp))

    st = sorted(glob.glob(os.path.join(snap, "*.safetensors")))
    if st:
        where = {}
        for f in st:
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
    else:
        bins = sorted(glob.glob(os.path.join(snap, "*.bin")))
        if not bins:
            raise FileNotFoundError("no weights (safetensors or bin): %s" % mid)
        store = {}
        for f in bins:
            try:
                sd = torch.load(f, map_location="cpu", mmap=True, weights_only=True)
            except TypeError:
                sd = torch.load(f, map_location="cpu")
            for k in sd:
                if k in UNEMBED or k in FINALNORM or k in NORMBIAS:
                    store.setdefault(k, sd[k])

        def pull(names):
            for k in names:
                if k in store:
                    return store[k], k
            return None, None

    W, used = pull(UNEMBED)
    if W is None:
        raise KeyError("no unembedding in %s" % mid)
    nw, _ = pull(FINALNORM)
    nb, _ = pull(NORMBIAS)
    return W, nw, nb, used, cfg


def is_gemma(mid):
    """gemma stores its RMSNorm weight as w-1; the forward pass adds 1 back."""
    return "gemma" in mid.lower()


def apply_norm(h, nw, nb, gemma, torch=None):
    """RMSNorm unless a bias is present, in which case LayerNorm."""
    if torch is None:
        import torch
    h = h.float()
    if nw is None:
        return h
    if nb is not None:
        m = h.mean(-1, keepdim=True)
        v = h.var(-1, keepdim=True, unbiased=False)
        return (h - m) / torch.sqrt(v + 1e-5) * nw.float() + nb.float()
    rms = torch.rsqrt(h.pow(2).mean(-1, keepdim=True) + 1e-6)
    return h * rms * (nw.float() + (1.0 if gemma else 0.0))


def manifest():
    """{model_id: entry} for every model with an archived residual stream."""
    return json.load(open(os.path.join(ARCHIVE, "hidden_manifest.json")))["models"]


def hidden(mid):
    """(array (rows, n_layers+1, d_model), prompts) from the sidecar."""
    import numpy as np
    man = manifest()
    if mid not in man:
        raise KeyError("no hidden states for %s" % mid)
    e = man[mid]
    a = np.fromfile(os.path.join(ARCHIVE, e["file"]), dtype="float32")
    return a.reshape((e["rows"],) + tuple(e["shape_per_row"])), e["prompts"]


class Readout:
    """A prepared final norm + unembedding: `unembed(final_norm(h))` for any `h`.

    **PREPARE ONCE PER READOUT, NOT ONCE PER CALL.** `W.float()` on gemma's
    256000x3584 bfloat16 unembedding allocates a 3.7GB float32 copy. The
    swap-experiment shape calls a readout six times per prompt across sixty
    prompts, so doing the cast inside the call meant 354 such allocations per
    pair -- which dominated the run and looks exactly like "the matmul is slow".

    A readout is deliberately separable from the state it is applied to: that is
    what makes swapping one model's readout onto another model's residual stream
    a two-line operation rather than a special case.
    """

    def __init__(self, W, nw, nb, cfg, gemma=False, device="cpu", torch=None):
        if torch is None:
            import torch
        self.torch = torch
        self.device = device
        self.Wt = W.float().t().to(device)
        self.nw = nw.float().to(device) if nw is not None else None
        self.nb = nb.float().to(device) if nb is not None else None
        self.gemma = gemma
        self.cap = cfg.get("final_logit_softcapping")
        self.scale = cfg.get("logits_scaling")
        self.vocab = int(W.shape[0])

    def probs(self, h, ids):
        """(n_layers+1, len(ids)) probabilities, one row per layer.

        **ALL LAYERS IN ONE MATMUL.** `h` is `(n_layers+1, d_model)` and the
        norms are per-row, so the whole stack is a single GEMM. Looping over
        layers was 15x slower on CPU for no reason other than shape.

        The softmax is over the FULL vocabulary before indexing, so `P.sum(-1)`
        IS the coverage at each depth. Callers must read it rather than assume
        it -- see the coverage note in the module docstring.
        """
        torch = self.torch
        x = apply_norm(h.to(self.device), self.nw, self.nb, self.gemma, torch)
        lg = x @ self.Wt
        if self.scale:
            lg = lg / self.scale
        if self.cap:
            lg = torch.tanh(lg / self.cap) * self.cap
        return torch.softmax(lg, -1)[:, ids].to("cpu")


def layer_probs(h, W, nw, nb, cfg, ids, gemma=False, torch=None, device="cpu"):
    """(n_layers+1, len(ids)) probabilities for `ids`, one row per layer.

    A one-shot convenience over `Readout`. **In a loop over prompts or over
    swapped readouts, build a `Readout` once instead** -- this function prepares
    the unembedding on every call, which is the cost described above.
    """
    return Readout(W, nw, nb, cfg, gemma=gemma, device=device,
                   torch=torch).probs(h, ids)


def single_token(words, tok, vocab=None):
    """(ids, kept_words) for the words this tokenizer spells with one token.

    A leading space is prepended because these are continuations, not sentence
    starts. `vocab`, if given, drops ids at or above it -- needed when two arms'
    unembeddings are truncated to a common prefix.
    """
    ids, keep = [], []
    for w in words:
        t = tok.encode(" " + w, add_special_tokens=False)
        if len(t) == 1 and (vocab is None or t[0] < vocab):
            ids.append(t[0])
            keep.append(w)
    return ids, keep
