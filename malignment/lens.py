"""A logit lens over stored residual streams, without loading the models.

    from malignment import lens
    W, nw, nb, used, cfg = lens.head("meta-llama/Llama-3.1-8B")
    H, prompts = lens.hidden("meta-llama/Llama-3.1-8B")
    R = lens.Readout(W, nw, nb, cfg)          # build ONCE per readout
    P = R.probs(H[0], ids)                    # (n_layers+1, len(ids))

Both stores hold final-position residual streams, `(n_layers+1, d_model)` float32
per prompt. A lens over them is `unembed(final_norm(h_L))`, which gives
`p_L(first token | prompt)` at every depth for a model that is never run.

## THE MODEL IS NEVER LOADED, AND THE REVISION IS STILL THE KEY

safetensors memory-maps, so pulling the unembedding out of gemma-2-9b's 37GB
checkout takes 0.0s and touches no other shard. **Model size is irrelevant here**
-- a 70B checkout costs the same as a 1B one.

**But WHICH checkout is not a filesystem question.** `head()` resolves through
`Checkpoint`, whose `snapshot_dir()` uses the hub's `try_to_load_from_cache` to
map (repo, revision) to a directory. This module previously globbed
`snapshots/*` and picked one, which is wrong in two directions and I shipped
both: alphabetical order takes `openbmb/MiniCPM5-1B`'s EMPTY snapshot over its
populated one, and mtime takes `allenai/Olmo-3-1025-7B`'s `stage1-step10000` ref
over `main` -- an intermediate pretraining checkpoint loaded as the released
model. `BAAI/Aquila2-7B` is pinned in the roster because its main branch was
replaced with a RE-TOKENISED model, vocab 143,973 against the pin's 100,008, so
a glob there pairs a 100k model with a 144k tokenizer.

Four things vary by architecture, and every one produces a plausible wrong number
rather than an error if guessed:

    the unembedding   gemma has NO lm_head and reuses model.embed_tokens.weight;
                      bloom uses word_embeddings.weight with no `model.` prefix.
    the final norm    a logit lens is unembed(final_norm(h_L)), not unembed(h_L).
                      Skipping it is silently wrong at EVERY layer.
    the norm's form   RMSNorm for Llama/gemma/glm; gemma stores its weight as
                      w-1 and the forward pass adds 1. LayerNorm where a bias
                      exists.
    two config scalars  gemma-2 caps output logits at 30
                      (`final_logit_softcapping`); without it the softmax
                      collapses onto one token and the lens reports full coverage
                      with a confident peak at layer 0. granite DIVIDES its
                      logits by 16 (`logits_scaling`); skipping that gave zero
                      coverage. Both raised nothing and produced full trajectories.

**AND ONE THAT ALREADY BIT.** Llama-3.1-8B carries BOTH `lm_head.weight` and
`model.embed_tokens.weight` and is NOT tied, so a first-match scan shard-by-shard
unembedded with the INPUT embedding: a diffuse softmax, near-zero mass on the
words carrying the distribution, and base/aligned trajectories differing by 0.04
where the output layer differs by 2.5. `head()` reads the safetensors index and
applies the preference order across the whole name space, so the choice is exact
rather than order-dependent.

## COVERAGE IS NOT OPTIONAL, AND IT IS DEPTH-DEPENDENT

`Readout.probs` returns the full probability vector over `ids` at every layer, so
`P.sum(-1)` IS the coverage at each depth and the caller cannot avoid seeing it.
**Below roughly three-quarters of the stack that share is ~0 on every model
measured** (0.000-0.044 across six pairs), and on recurrentgemma-9b it is exactly
0.000 until the final layer. A difference computed there is a difference between
two normalisations of nothing. Any statistic over depth needs a coverage floor or
it reports lens noise as an early effect: unfloored, an onset statistic put
Llama-3.1-8B at 0.20 of the stack; with a 0.20 floor the same data gives 0.92.

## WHAT ONE STATE PER PROMPT REACHES

`p_L(word)` is available from a single stored state when the model spells the
word as ONE token AFTER THIS PROMPT. That is what `single_token(words, tok,
prompt=...)` tests, by diffing `encode(prompt + " " + word)` against
`encode(prompt)`.

**It is NOT what `encode(" " + word)` tests, and the difference excluded two
models entirely.** `llm-jp-3-7.2b` encodes `" kill"` standalone as `[279, 4024]`
-- a word-boundary token then the word -- but after a real prompt emits `[4024]`
alone. On the isolated test it and `m-a-p/neo_7b` score 0% for EVERY word and
were dropped from a sweep as "fewer than 8 single-token rated words", which reads
as a property of the corpus and was a property of the test. In context they are
92% and 86% of words, 94% and 88% of mass.

    tokenizer          isolated   in context   mass in context
    Llama-3.1-8B            97%          97%               98%
    gemma-2-9b              99%          99%               99%
    CT-LLM-Base             92%          92%               93%
    llm-jp-3-7.2b            0%          92%               94%
    neo_7b                   0%          86%               88%
    CroissantLLMBase        74%          74%               76%

**THE RESIDUE IS SELECTIVE, AND AGAINST THE MEASURE.** Words a tokenizer splits
average 0.47-0.82 HIGHER on scene than words it does not, in all six tokenizers:
the excluded tail is the marked tail. Within a pair this cancels, because both
arms share a tokenizer and all four cells of a swap use one word set. **Across
pairs it does not**, and a cross-model comparison needs a common vocabulary --
which costs its whole price at N=2 (88% of cells to 69%) and then plateaus, 55%
still standing at 27 tokenizers.

A common vocabulary EQUALISES the bias; only the chain rule removes it.
`prod_i p_L(t_i | prompt + t_1..t_{i-1})` needs a forward pass at every proper
prefix -- measured on this battery, 4.4x the states for gemma up to 42x for
CroissantLLM, scaling with the multi-token fraction. That is a compute-per-pair
job in the shape of `malign-logits/scripts/twp_word_depth.py`, not a store.
"""

import glob
import json
import os

HUB = os.path.expanduser("~/.cache/huggingface/hub")

#: **TWO STORES, AND THE LIVE ONE WINS.** `produce_hidden` writes the current
#: store under `$MALIGNMENT_DATA/hidden` against a FROZEN prompt list; the v2
#: archive is the older `f11_twp` sidecars, read-only, and its per-model prompt
#: lists disagree with each other (115 / 62 / 60 / 33), which is why three of its
#: sixteen pairs cannot be swapped at all. A model present in both resolves to
#: the live store. `manifest()` says which store each entry came from so a
#: consumer can refuse to mix them.
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
STORE = os.path.join(DATA, "hidden")
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
    """Local snapshot directory for a model id, or None. Delegates to Checkpoint.

    **THE REVISION IS THE KEY, AND ONLY `Checkpoint` KNOWS IT.** This function
    used to glob `snapshots/*` and pick one, which is wrong in two directions at
    once and I shipped both: alphabetical order takes `openbmb/MiniCPM5-1B`'s
    EMPTY `c1838b52` over its populated `87179e5c`, and mtime takes
    `allenai/Olmo-3-1025-7B`'s `stage1-step10000` over `main` -- loading an
    intermediate pretraining checkpoint as the released model, weights that are
    real, loadable and wrong. Neither key means what the caller means, and a
    third guess would have been a third bug.

    `Checkpoint.snapshot_dir()` resolves (repo, revision) through the hub's own
    `try_to_load_from_cache`, so it honours the roster's pins -- `BAAI/Aquila2-7B`
    is pinned to `9c76e143` because main was replaced with a RE-TOKENISED model,
    vocab 143,973 against the pin's 100,008, and a glob pairs a 100k model with a
    144k tokenizer.
    """
    from .checkpoint import Checkpoint
    return Checkpoint(mid).snapshot_dir()


def head(mid):
    """(W_unembed, norm_weight, norm_bias, name_used, cfg) without loading the model.

    Resolves through `Checkpoint`, so the revision pin is honoured, and uses the
    safetensors index to go straight to the shard holding each tensor.

    **THE PREFERENCE ORDER IS APPLIED ACROSS ALL SHARDS, NEVER WITHIN ONE.**
    Llama-3.1-8B carries BOTH `model.embed_tokens.weight` (shard 1) and
    `lm_head.weight` (last shard) and is NOT tied, so a first-match scan
    unembedded with the INPUT embedding. It raised nothing: a diffuse softmax,
    near-zero mass on the words carrying the distribution, and base/aligned
    trajectories differing by 0.04 where the output layer differs by 2.5. Reading
    the index makes the choice exact rather than order-dependent.

    **NOT safetensors ONLY.** Three of the sixteen archived pairs are cached as
    `pytorch_model.bin` and the first sweep lost them to a missing branch rather
    than to anything about the models. `torch.load(mmap=True)` keeps it a partial
    read: the tensors stay on disk until indexed.
    """
    import torch
    from safetensors import safe_open
    from .checkpoint import Checkpoint
    ck = Checkpoint(mid)
    snap = ck.snapshot_dir()
    if not snap:
        raise FileNotFoundError("not cached: %s" % mid)
    cfg = {}
    cp = os.path.join(snap, "config.json")
    if os.path.exists(cp):
        cfg = json.load(open(cp))

    want = set(UNEMBED) | set(FINALNORM) | set(NORMBIAS)
    where = {}
    idx = ck.weight_index()
    if idx:
        for k, shard in idx.items():
            if k in want:
                where[k] = os.path.join(snap, shard)
    else:
        #: no index -- a single-file or sharded-without-index checkout. Enumerate
        #: through Checkpoint so the shard list is this revision's, not a glob's.
        for f in ck.shard_paths() or glob.glob(os.path.join(snap, "*.safetensors")):
            with safe_open(f, framework="pt") as g:
                for k in g.keys():
                    if k in want:
                        where.setdefault(k, f)

    if where:
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
                if k in want:
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


def _read_store(root, name):
    p = os.path.join(root, name)
    if not os.path.exists(p):
        return {}, None
    d = json.load(open(p))
    return d.get("models", {}), d.get("prompts")


def manifest(store=None):
    """{model_id: entry} across both stores, live winning, each tagged `store`.

    `store="live"` or `"archive"` restricts to one. Entries carry `prompts`
    either per-model (archive) or once for the whole store (live, frozen), and
    `hidden()` resolves that difference so callers do not have to.
    """
    live, lp = _read_store(STORE, "manifest.json")
    arch, _ = _read_store(ARCHIVE, "hidden_manifest.json")
    out = {}
    if store in (None, "archive"):
        for k, v in arch.items():
            out[k] = dict(v, store="archive", _root=ARCHIVE)
    if store in (None, "live"):
        for k, v in live.items():
            out[k] = dict(v, store="live", _root=STORE,
                          prompts=v.get("prompts") or lp)
    return out


def hidden(mid, store=None):
    """(array (rows, n_layers+1, d_model), prompts) for one model.

    **THE PROMPT LIST COMES FROM THE STORE, NEVER FROM THE CALLER.** Row `i` is
    prompt `i` of that store's list and nothing else keys them together; a caller
    that supplies its own ordering is asserting an alignment it cannot check.
    """
    import numpy as np
    man = manifest(store)
    if mid not in man:
        raise KeyError("no hidden states for %s" % mid)
    e = man[mid]
    a = np.fromfile(os.path.join(e["_root"], e["file"]), dtype="float32")
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

    def full(self, h):
        """(n_layers+1, vocab) probabilities. The whole distribution, not a slice.

        Only for the shape checks that need the full support -- entropy, top-1 --
        because this materialises `(n_layers+1) x vocab`, which is 43 x 256000
        for gemma. `probs()` is what analysis should call.
        """
        torch = self.torch
        x = apply_norm(h.to(self.device), self.nw, self.nb, self.gemma, torch)
        lg = x @ self.Wt
        if self.scale:
            lg = lg / self.scale
        if self.cap:
            lg = torch.tanh(lg / self.cap) * self.cap
        return torch.softmax(lg, -1)

    def shape_at(self, h, layer=-1):
        """(entropy_bits, top1_id, top1_p) of the full distribution at one layer.

        **THIS IS THE VALIDITY CHECK FOR A SWAPPED READOUT.** Applying one
        model's unembedding to another's residual stream is out of distribution
        for that stream, and the failure is not an error -- it is a distribution
        that is simply the wrong SHAPE. H1 (`meta/M01_displacement/findings/`)
        excluded a pair on exactly this: Amber's cross-read came out 5x sharper
        than its native read, so the decomposition was not interpretable, while
        Llama's passed. A swap reported without this number is a swap whose
        premise was never tested.
        """
        torch = self.torch
        P = self.full(h)[layer]
        p = P[P > 0]
        ent = float(-(p * torch.log2(p)).sum())
        top = int(P.argmax())
        return ent, top, float(P[top])

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


def single_token(words, tok, prompt=None, vocab=None):
    """(ids, kept_words) for words this tokenizer spells with ONE token here.

    **THE TOKEN PATH IS A PROPERTY OF (PROMPT, WORD), NOT OF THE WORD.** With
    `prompt`, this diffs `encode(prompt + " " + word)` against `encode(prompt)`
    and keeps the word when the continuation is a single token -- what the model
    actually has to emit. Without it, it falls back to `encode(" " + word)`,
    which answers a different question: whether the tokenizer has a space-prefixed
    token for the word.

    The difference is not marginal. `llm-jp-3-7.2b` and `m-a-p/neo_7b` score 0%
    on the isolated test for EVERY word, because they spell a leading space as
    its own token in isolation and drop it in context; in context they are 92%
    and 86%. Both models were excluded from a sweep as "fewer than 8 single-token
    rated words", which reads as a property of the corpus and was a property of
    my test.

    `vocab`, if given, drops ids at or above it -- needed when two arms'
    unembeddings are truncated to a common prefix.
    """
    ids, keep = [], []
    base = tok.encode(prompt, add_special_tokens=False) if prompt is not None else None
    for w in words:
        if base is not None:
            full = tok.encode(prompt + " " + w, add_special_tokens=False)
            t = full[len(base):] if full[:len(base)] == base else None
            #: a prompt whose tokens are not a prefix of the extended string means
            #: the boundary re-tokenised; that word is not reachable from this
            #: prompt's stored state and is dropped rather than approximated.
            if t is None:
                continue
        else:
            t = tok.encode(" " + w, add_special_tokens=False)
        if len(t) == 1 and (vocab is None or t[0] < vocab):
            ids.append(t[0])
            keep.append(w)
    return ids, keep
