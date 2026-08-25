"""Bare-word vectors for our vocabulary, gated the way Findings P gates them.

    python -u embed.py --lang en --encoder glove
    python -u embed.py --lang en --encoder bge
    python -u embed.py --lang zh --encoder bge

Writes `~/malignment-data/named_under_dose/embed_<lang>_<encoder>.npz` with
`words`, `E`, and the gate statistics. `predict.py` consumes it.

## THE GATE, AND WHY IT REFUSES RATHER THAN WARNS

P's `k_embed.py` gates every encoder on BARE WORDS before it is allowed to write,
because docket [459] had gate-checked bge-m3 on `prompt + " " + word` -- a SENTENCE --
and **a gate passed for one use is not evidence about another**. Near-synonyms must
embed closer than unrelated pairs on single-word input; if they do not, any
downstream null is a fact about the encoder rather than about alignment. The pairs
below are P's, verbs, chosen before any embedding was computed, and are copied
verbatim so the two studies are gated identically.

P's measured gate, which this should reproduce:

    encoder        synonym gap   anisotropy   dims
    GloVe 300d        +0.400        0.037      300     <- P's PRIMARY
    bge-m3 en         +0.138        0.529     1024
    bge-m3 zh         +0.319        0.472     1024

**bge-m3 on bare English words is the weak instrument here** -- a +0.138 gap against
GloVe's +0.400 -- so English leads with GloVe and reads bge as a second opinion.
GloVe is English-only: `glove-wiki-gigaword-300` has no Chinese, and a zh/bge number
must never be compared to an en/GloVe one.

## UNCOVERED WORDS ARE DROPPED, NEVER ZERO-VECTORED

P's reason, kept because it is exactly right: a zero vector puts every uncovered word
at the same location, **which manufactures structure in a study whose headline is a
number near zero.** A dropped word costs coverage and is visible; a zero-vectored one
costs validity and is not.

## CPU, ALWAYS, FOR WORD STORES

Large multi-batch mps encodes corrupt some single-CJK-character embeddings
deterministically -- 576 of 3,978 zh rows in the archive, and re-auditing down the
same path read as clean. Word stores are small enough that CPU costs minutes.
"""

import argparse, collections, gzip, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
DATA = os.path.expanduser("~/malignment-data/named_under_dose")
GLOVE = os.path.expanduser(
    "~/gensim-data/glove-wiki-gigaword-300/glove-wiki-gigaword-300.gz")
SEED = 20260825

#: P's pairs, verbatim from meta/M01_displacement/scripts/k_embed.py
SYN_EN = [("kill", "murder"), ("shout", "yell"), ("begin", "start"),
          ("hit", "strike"), ("grab", "seize"), ("look", "gaze"),
          ("hate", "despise"), ("fix", "repair"), ("cry", "weep"),
          ("throw", "hurl"), ("break", "shatter"), ("laugh", "chuckle")]
UNREL_EN = [("kill", "bake"), ("shout", "knit"), ("begin", "swim"),
            ("hit", "read"), ("grab", "sing"), ("look", "digest"),
            ("hate", "plough"), ("fix", "dance"), ("cry", "compute"),
            ("throw", "spell"), ("break", "whisper"), ("laugh", "measure")]
SYN_ZH = [("杀", "杀害"), ("喊", "叫喊"), ("开始", "起始"), ("打", "击打"),
          ("抓", "抓住"), ("看", "注视"), ("恨", "憎恨"), ("修", "修理")]
UNREL_ZH = [("杀", "烤"), ("喊", "编织"), ("开始", "游泳"), ("打", "阅读"),
            ("抓", "唱歌"), ("看", "消化"), ("恨", "耕种"), ("修", "跳舞")]


def cos(a, b):
    import numpy as np
    return float(a @ b / max(1e-12, (a @ a) ** 0.5 * (b @ b) ** 0.5))


def vocabulary(lang, min_cells):
    """Words with at least `min_cells` moving cells in our own corpus."""
    p = os.path.join(DATA, "cells_%s.csv.gz" % lang)
    if not os.path.exists(p):
        sys.exit("no %s -- run run.py --lang %s first" % (p, lang))
    c = collections.Counter()
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) == len(head):
                c[v[ix["word"]]] += 1
    return sorted(w for w, n in c.items() if n >= min_cells)


def glove_encoder(want):
    """Read the word2vec-text GloVe dump directly; gensim is not installed here.

    The file is `<n> <dim>` then one `word f1 .. fdim` line per word, gzipped.
    Only the words asked for are materialised -- 400,000 x 300 floats is 480 MB
    and we need a few thousand rows of it.
    """
    import numpy as np
    if not os.path.exists(GLOVE):
        sys.exit("no GloVe at %s" % GLOVE)
    lower = {w.strip().lower() for w in want}
    got = {}
    with gzip.open(GLOVE, "rt", encoding="utf-8", errors="replace") as fh:
        fh.readline()
        for line in fh:
            sp = line.find(" ")
            w = line[:sp]
            if w in lower and w not in got:
                got[w] = np.fromstring(line[sp + 1:], sep=" ", dtype=np.float32)

    def enc(ws):
        keep, rows = [], []
        for w in ws:
            v = got.get(w.strip().lower())
            if v is not None and v.size:
                keep.append(w)
                rows.append(v)
        if not rows:
            return [], np.zeros((0, 300), np.float32)
        E = np.array(rows, np.float32)
        E /= np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-9)
        return keep, E
    return enc


def bge_encoder():
    from sentence_transformers import SentenceTransformer
    #: CPU, always -- see the module docstring.
    m = SentenceTransformer("BAAI/bge-m3", device="cpu")

    def enc(ws):
        ws = list(ws)
        if not ws:
            import numpy as np
            return [], np.zeros((0, 1024), "float32")
        return ws, m.encode(ws, normalize_embeddings=True, batch_size=64,
                            show_progress_bar=False)
    return enc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", choices=("en", "zh"))
    ap.add_argument("--encoder", default="glove", choices=("glove", "bge"))
    ap.add_argument("--min-cells", type=int, default=10)
    a = ap.parse_args(argv)
    import numpy as np

    if a.encoder == "glove" and a.lang != "en":
        sys.exit("glove-wiki-gigaword-300 is English. Use bge for Chinese, and "
                 "do not compare a zh/bge number to an en/glove one.")

    words = vocabulary(a.lang, a.min_cells)
    print("[%s/%s] %d words with >=%d moving cells"
          % (a.lang, a.encoder, len(words), a.min_cells))

    syn, unrel = (SYN_EN, UNREL_EN) if a.lang == "en" else (SYN_ZH, UNREL_ZH)
    probe = sorted({w for p in syn + unrel for w in p})
    encode = (glove_encoder(set(words) | set(probe)) if a.encoder == "glove"
              else bge_encoder())

    pk, P = encode(probe)
    if len(pk) < len(probe):
        print("  gate probe: %d of %d probe words in vocabulary" % (len(pk), len(probe)))
    pv = dict(zip(pk, P))
    syn = [p for p in syn if p[0] in pv and p[1] in pv]
    unrel = [p for p in unrel if p[0] in pv and p[1] in pv]
    if not syn or not unrel:
        sys.exit("  REFUSING: the gate probe did not survive the vocabulary")
    s = float(np.median([cos(pv[x], pv[y]) for x, y in syn]))
    u = float(np.median([cos(pv[x], pv[y]) for x, y in unrel]))
    print("  GATE on BARE WORDS: synonyms %.4f, unrelated %.4f, gap %+.4f"
          % (s, u, s - u))
    if s - u <= 0:
        print("  REFUSING TO WRITE: this encoder does not separate near-synonyms "
              "from unrelated words on bare input, so any downstream null would be "
              "a fact about the encoder.")
        return 1

    kept, E = encode(words)
    print("  coverage: %d of %d words embedded (%.1f%%); uncovered words are "
          "DROPPED, never zero-vectored" % (len(kept), len(words),
                                            100.0 * len(kept) / max(1, len(words))))
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(E), size=min(400, len(E)), replace=False)
    S = E[idx] @ E[idx].T
    iu = np.triu_indices(len(idx), 1)
    aniso = float(np.median(S[iu]))
    print("  anisotropy (median pairwise cosine, %d sampled): %.4f" % (len(idx), aniso))

    os.makedirs(DATA, exist_ok=True)
    out = os.path.join(DATA, "embed_%s_%s.npz" % (a.lang, a.encoder))
    np.savez_compressed(out, words=np.array(kept, dtype=object), E=E,
                        syn_median=s, unrel_median=u, syn_gap=s - u,
                        anisotropy=aniso)
    print("  -> %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
