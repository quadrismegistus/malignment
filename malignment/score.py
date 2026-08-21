"""Score any text on the two axes, into a CONTENT-ADDRESSED store.

    from malignment import score

    score.surprisal(["some text", "another"])        # -> [bits/token, ...]
    score.drift(["some text", "another"])            # -> [{mean_drift: ...}, ...]
    score.surprisal(texts, m=200)                    # the M-token prefix

## THE STORE IS KEYED ON THE TEXT AND THE INSTRUMENT, NEVER ON THE CALLER

Surprisal is a property of (text, scoring model). Drift is a property of
(text, embedder, splitter, truncation policy). Neither depends on which
experiment asked, so nothing here takes an output directory: scoring the same
sentence from two experiments hits the same cell, and the second one is free.

    $MALIGNMENT_DATA/scores/
      surprisal/<ref>/<producer>/shard00.{jsonl,f32,i32}
      drift/<embedder>__<splitter>__<policy>/<producer>/shard00.{jsonl,f32}

**THE INSTRUMENT IS IN THE PATH**, the same rule `Checkpoint.key` applies to twp:
a different reference model or a different splitter is a different measurement,
and putting it in the path makes a collision impossible rather than guarded
against. The drift path carries the TRUNCATION POLICY as well, because the
archive stash holds three variants of the same passages under
`BAAI/bge-m3|nltk-en`, `|full` and `|refuse-untrunc-2026-08-14` with mean
sentence counts of 5.26, 10.91 and 11.89 -- dropping that tag would silently
mix three populations.

**`<producer>` IS THE HOSTNAME**, as in the twp and generations stashes, so two
machines and two parallel processes append to different FILES and rsync merges
them. Reads span every producer; writes go to ours.

## bge RUNS ON CPU. NOT A DEFAULT -- A RULE.

RH, 2026-08-21: mac-CPU and cuda-GPU bge were verified identical, and the mps
pass was found corrupting short-sequence embeddings. So `device` is not a free
parameter for the drift axis and this module does not offer one. The surprisal
model may use cuda where present, since it is a different instrument with a
different history.

## THE TEXT IS STORED WITH ITS SCORE

Roughly 1.2 KB per passage against a `.f32` block that is already larger. A score
whose text cannot be recovered is a number nobody can check, and this campaign
has repeatedly paid for reading a number instead of the text under it. The store
is a CACHE and not the corpus of record: the corpus lives in ClickHouse and in
the experiment pools, and nothing here is authoritative about population.

## VALIDATED AGAINST THE COMMITTED SIDECARS BEFORE BEING USED

Not "should agree" -- checked, on rows from the artifacts the campaign already
quotes:

    drift       vs jakobson_space/bge_human/drift.jsonl     0.00e+00, EXACT
    surprisal   vs ref_pool/deepseek/ref_shard00, M=200     ~8e-05

Drift is bit-identical, which is what pinning bge to CPU buys. Surprisal agrees
to 8e-05 on values near 4 bits -- float32 accumulation, consistently signed,
and four orders of magnitude below the smallest difference this campaign quotes
(the API-aligned surprisal gap is 0.085). It is NOT zero and is not described as
identical; a number reproduced to 8e-05 is reproduced, and saying so exactly is
cheaper than someone later finding the gap and wondering what else moved.

## GUARDS MOVED AS CODE, NOT REWRITTEN

`load()` refuses a reference tokenizer that does not round-trip its probes --
transformers #45488 deletes every space on some repos and returns plausible
numbers on the wreckage. `metrics()` is imported from `drift_geometry`, never
reimplemented: cosine distance is easy to write and easy to write differently,
and a `mean_drift` computed over a different pairing is not comparable to the
337,355 model passages it exists to be compared against.
"""

import hashlib
import json
import os
import socket
import sys

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
SCORES = os.environ.get("MALIGNMENT_SCORES", os.path.join(DATA, "scores"))
PRODUCER = os.environ.get("MALIGNMENT_PRODUCER") or socket.gethostname().split(".")[0]

#: the reference model for surprisal, and the tokenizer class its own
#: LOADER_OVERRIDE demands (deepseek under AutoTokenizer eats spaces, #45488).
REF = "deepseek-ai/deepseek-llm-7b-base"
REF_TOKENIZER = "PreTrainedTokenizerFast"
PROBES = [
    "The sky was the color of television tuned to a dead channel.",
    "He lay naked in his bed and",
    "She was so angry she wanted to",
    'Then he said, "I don\'t know" -- and left.',
]

EMBEDDER = "BAAI/bge-m3"
SPLITTER = "nltk-en"
#: the archive's namespace tag. Part of the identity, see the docstring.
POLICY = "refuse-untrunc-2026-08-14"
DIM = 1024

_CACHE = {}                     #: process-level singletons; see `_ref` / `_bge`


def sha(text):
    """The content address. 16 hex of sha256 over the RAW text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _safe(s):
    return s.replace("/", "__").replace("|", "__")


def _root(kind):
    if kind == "surprisal":
        return os.path.join(SCORES, "surprisal", _safe(REF))
    return os.path.join(SCORES, "drift",
                        "%s__%s__%s" % (_safe(EMBEDDER), SPLITTER, POLICY))


def _index(kind):
    """{sha: row dict} across EVERY producer. Reads span the lot."""
    root = _root(kind)
    key = ("idx", kind, root)
    if key in _CACHE:
        return _CACHE[key]
    out = {}
    if os.path.isdir(root):
        for prod in sorted(os.listdir(root)):
            d = os.path.join(root, prod)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if not fn.endswith(".jsonl"):
                    continue
                for line in open(os.path.join(d, fn)):
                    line = line.strip()
                    if not line:
                        continue
                    r = json.loads(line)
                    r["_dir"] = d
                    #: LAST WRITE WINS on a repeated sha, and it cannot differ:
                    #: the instrument is in the path, so two rows for one sha
                    #: are the same measurement made twice.
                    out[r["sha"]] = r
    _CACHE[key] = out
    return out


def _ref():
    """The surprisal model, loaded ONCE per process. -> (tok, model, device)

    A property that loads a 7B model per call would make scoring 600 passages
    600 loads, so the singleton is not an optimisation -- it is what makes the
    friendly `Passage.surprisal` accessor usable at all.
    """
    if "ref" in _CACHE:
        return _CACHE["ref"]
    import torch, transformers
    from transformers import AutoModelForCausalLM
    tk = getattr(transformers, REF_TOKENIZER).from_pretrained(REF)
    for p in PROBES:
        back = tk.decode(tk(p, add_special_tokens=False)["input_ids"])
        if back.strip() != p.strip():
            raise RuntimeError(
                "REFUSING: %s tokenizer does not round-trip under %s.\n"
                "  sent %r\n  got  %r\nScoring would run on a corrupted string "
                "and return plausible numbers." % (REF, REF_TOKENIZER, p, back))
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    m = AutoModelForCausalLM.from_pretrained(
        REF, dtype=torch.float32, low_cpu_mem_usage=True).eval().to(dev)
    _CACHE["ref"] = (tk, m, dev)
    return _CACHE["ref"]


def _bge():
    """The embedder, loaded ONCE per process, ON CPU. See the docstring."""
    if "bge" in _CACHE:
        return _CACHE["bge"]
    from sentence_transformers import SentenceTransformer
    #: device="cpu" is the RULE, not a default. Do not parameterise it.
    _CACHE["bge"] = SentenceTransformer(EMBEDDER, device="cpu")
    return _CACHE["bge"]


def _split(text):
    if "nltk" not in _CACHE:
        import nltk
        try:
            nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            nltk.download("punkt_tab", quiet=True)
        _CACHE["nltk"] = nltk.sent_tokenize
    #: RAW text, not `.strip()` -- matches `bge_human.py:150`, and a leading
    #: newline changes the first sentence's length.
    return _CACHE["nltk"](text)


def _append(kind, rows, blocks):
    """Write rows + their float blocks to THIS producer's shard. -> None"""
    import numpy as np
    d = os.path.join(_root(kind), PRODUCER)
    os.makedirs(d, exist_ok=True)
    jl = os.path.join(d, "shard00.jsonl")
    f32 = os.path.join(d, "shard00.f32")
    i32 = os.path.join(d, "shard00.i32")
    #: the row offset is the CURRENT length of the flat file, read from disk
    #: rather than tracked, so a killed run cannot leave the two disagreeing.
    row = os.path.getsize(f32) // 4 if os.path.exists(f32) else 0
    with open(jl, "a") as jh, open(f32, "ab") as fh:
        ih = open(i32, "ab") if kind == "surprisal" else None
        try:
            for r, (vals, ends) in zip(rows, blocks):
                v = np.asarray(vals, dtype=np.float32)
                fh.write(v.tobytes())
                if ih is not None:
                    ih.write(np.asarray(ends, dtype=np.int32).tobytes())
                r["row"], r["n"] = row, int(v.size)
                row += int(v.size)
                jh.write(json.dumps(r, ensure_ascii=False) + "\n")
        finally:
            if ih is not None:
                ih.close()
    _CACHE.pop(("idx", kind, _root(kind)), None)      #: index is now stale


def _block(kind, r, which="f32"):
    import numpy as np
    p = os.path.join(r["_dir"], "shard00." + which)
    dt = np.float32 if which == "f32" else np.int32
    mm = np.memmap(p, dtype=dt, mode="r")
    return np.asarray(mm[r["row"]:r["row"] + r["n"]])


def surprisal(texts, m=None, ids=None):
    """Reference surprisal in bits/token. -> [float or None]

    `m` takes the mean over the first M scored tokens instead of all of them --
    the prefix control the corpus work uses, since passages differ in length and
    a whole-passage mean is partly a length statistic. `None` means all tokens.

    A text of fewer than two tokens has no next-token prediction and returns
    None rather than 0.0, which would average in as a very confident model.
    """
    import numpy as np
    texts = list(texts)
    idx = _index("surprisal")
    todo = [(i, t) for i, t in enumerate(texts) if sha(t) not in idx]
    if todo:
        tk, mdl, dev = _ref()
        import torch
        rows, blocks = [], []
        for _, t in todo:
            enc = tk(t, return_offsets_mapping=True)
            tid = torch.tensor([enc["input_ids"]])
            if tid.shape[1] < 2:
                rows.append(dict(sha=sha(t), text=t, n_tokens=int(tid.shape[1]),
                                 ref=REF, scored=False))
                blocks.append((np.zeros(0, np.float32), np.zeros(0, np.int32)))
                continue
            with torch.no_grad():
                lg = mdl(tid.to(dev)).logits[0]
            lp = torch.log_softmax(lg.float(), -1)
            tgt = tid[0, 1:].to(dev)
            sur = (-lp[:-1].gather(1, tgt[:, None]).squeeze(1)).cpu().numpy() / np.log(2)
            #: byte END of each scored token, which is what makes a prefix a
            #: mask rather than a guess -- see ref_surprisal.score's docstring.
            ends = np.array([len(t[:c1].encode())
                             for _, c1 in enc["offset_mapping"][1:]], dtype=np.int32)
            rows.append(dict(sha=sha(t), text=t, n_tokens=int(tid.shape[1]),
                             n_bytes=len(t.encode()), ref=REF, scored=True))
            blocks.append((sur.astype(np.float32), ends))
        _append("surprisal", rows, blocks)
        idx = _index("surprisal")

    out = []
    for t in texts:
        r = idx.get(sha(t))
        if not r or not r.get("scored"):
            out.append(None); continue
        v = _block("surprisal", r)
        if m is not None:
            if v.size < m:
                out.append(None); continue
            v = v[:m]
        out.append(float(v.mean()) if v.size else None)
    return out


def word_bits(text):
    """Per-word surprisal for one text. -> [{word, bits, partial}]

    Imported from the committed implementation rather than rewritten: a token is
    assigned to the word containing its LAST byte, and the first token is
    unscored because nothing precedes it.
    """
    idx = _index("surprisal")
    if sha(text) not in idx:
        surprisal([text])
        idx = _index("surprisal")
    r = idx.get(sha(text))
    if not r or not r.get("scored"):
        return []
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "experiments", "passage_analysis", "jakobson_space"))
    from ref_surprisal import word_bits as _wb
    return _wb(text, _block("surprisal", r), _block("surprisal", r, "i32"))


def sentence_vecs(text):
    """L2-normalised bge sentence vectors. -> (sentences, (n, DIM) array)"""
    import numpy as np
    idx = _index("drift")
    r = idx.get(sha(text))
    if r is None:
        sents = _split(text)
        if not sents:
            return [], np.zeros((0, DIM), np.float32)
        V = np.asarray(_bge().encode(sents, normalize_embeddings=True,
                                     show_progress_bar=False), dtype=np.float32)
        _append("drift", [dict(sha=sha(text), text=text, n_sents=len(sents),
                               sent_chars=[len(s) for s in sents],
                               embedder=EMBEDDER, splitter=SPLITTER,
                               policy=POLICY)], [(V.reshape(-1), None)])
        idx = _index("drift")
        r = idx[sha(text)]
    V = _block("drift", r).reshape(r["n_sents"], DIM)
    return _split(text), V


def drift(texts):
    """The drift family per text. -> [dict]

    `metrics` comes from `drift_geometry/drift_metrics.py` and is not
    reimplemented here. Only `mean_drift`, `mean_pairwise` and `ordering` are
    length-free; the cumulative ones grow with sentence count by construction.
    """
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "experiments", "passage_analysis", "drift_geometry"))
    from drift_metrics import metrics
    out = []
    for t in texts:
        _, V = sentence_vecs(t)
        out.append(metrics(V) if len(V) else {"n_sents": 0})
    return out
