"""The model's own embedding matrix, restricted to whole words. -> vectors

Shared loader for this folder. Reads ONE tensor out of the safetensors shards
rather than instantiating a model: `model.embed_tokens.weight` on
Llama-3.1-8B is 128,256 x 4,096, about a gigabyte in bf16, and the other 30 GB
are not needed to ask a question about vocabulary geometry.

## THE LEADING SPACE IS NOT OPTIONAL

`kill` and ` kill` are DIFFERENT TOKENS with different vectors, and every word
this project measures sits mid-sentence after a space. Using the bare form
would answer a question about line-initial tokens, which is not the corpus.
The space-prefixed id is required and a word without one is dropped rather
than silently substituted.

## AND ONLY SINGLE-TOKEN WORDS HAVE A VECTOR AT ALL

A word that tokenises to two pieces has no embedding of its own; averaging its
pieces would invent one. Multi-token words are dropped and counted, because
the drop is a property of the tokenizer and a reader should know how much of
the vocabulary it removed.
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)

MODEL = "meta-llama/Llama-3.1-8B"


def _snapshot(model=MODEL):
    pat = os.path.expanduser(
        "~/.cache/huggingface/hub/models--%s/snapshots/*/"
        % model.replace("/", "--"))
    d = sorted(glob.glob(pat))
    if not d:
        raise SystemExit("not in the local cache: %s" % model)
    return d[-1]


def matrix(model=MODEL, which="model.embed_tokens.weight"):
    """-> (torch tensor [vocab, dim], tokenizer)"""
    import torch
    from safetensors import safe_open
    from transformers import AutoTokenizer
    d = _snapshot(model)
    idx = json.load(open(d + "model.safetensors.index.json"))
    shard = idx["weight_map"][which]
    with safe_open(d + shard, framework="pt") as f:
        W = f.get_tensor(which)
    tok = AutoTokenizer.from_pretrained(d)
    return W.to(torch.float32), tok


def words(tok, vocab):
    """-> ({word: token id}, n_multi, n_missing) for space-prefixed whole words."""
    out, multi = {}, 0
    for w in vocab:
        ids = tok.encode(" " + w, add_special_tokens=False)
        if len(ids) == 1:
            out[w] = ids[0]
        else:
            multi += 1
    return out, multi
