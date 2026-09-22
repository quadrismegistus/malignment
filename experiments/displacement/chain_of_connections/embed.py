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


GLOVE = os.path.expanduser(
    "~/gensim-data/glove-wiki-gigaword-300/glove-wiki-gigaword-300.gz")


def glove(want):
    """-> (torch [n, 300], [word]) for the requested words that GloVe has.

    **A STATIC SEMANTIC SPACE, WHICH IS THE POINT.** The Llama input embedding
    is about half orthographic -- 50% of its 3-NN pairs share a three-letter
    prefix -- because it is the table a tokenizer indexes into. GloVe is fitted
    on co-occurrence and has no tokenizer in it, so if a chain survives here it
    is a chain of contexts rather than of spellings.

    Same reader as `named_under_dose/embed.py`: the word2vec-text dump is
    streamed and only the requested rows are materialised, because 400,000 x
    300 floats is 480 MB and this needs a few thousand.
    """
    import gzip
    import numpy as np
    import torch
    if not os.path.exists(GLOVE):
        raise SystemExit("no GloVe at %s" % GLOVE)
    lower = {w.lower() for w in want}
    got = {}
    with gzip.open(GLOVE, "rt", encoding="utf-8", errors="replace") as fh:
        fh.readline()
        for line in fh:
            sp = line.find(" ")
            w = line[:sp]
            if w in lower and w not in got:
                got[w] = np.fromstring(line[sp + 1:], sep=" ", dtype=np.float32)
    ws = sorted(w for w in want if w.lower() in got)
    M = torch.tensor(np.stack([got[w.lower()] for w in ws]))
    return M, ws
