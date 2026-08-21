"""Explode the passage table into per-WORD surprisal and per-SENTENCE drift.

    python .../explode.py
    python .../explode.py --limit 400            # smoke

Two parquets, both keyed by the passage `id` in `results/quadrants.csv`:

    words.parquet      id, word_index, word, bits, partial
    sentences.parquet  id, sent_index, sentence, step, dist_from_first,
                       is_furthest, reproduces, mean_bits, n_words

## WHY THIS EXISTS

The passage table answers "is this model surprising" and cannot answer "WHICH
WORDS were surprising" -- the selection axis read off a single passage rather
than inferred from its mean. Both sidecars already hold it. **Nothing here is
newly scored**; this only reshapes measurements that already exist, so a number
in these files must reproduce the passage-level number it decomposes, and every
row carries whether it does.

## THE SOURCES, AND WHY THE OPEN MODELS COME FROM THE OLD REPO'S STASH

              surprisal (deepseek, ours)        sentence vectors (bge, inherited)
    human     ref_pool/deepseek/               jakobson_space/bge_human/
    API       api_passages/<slug>_ref/         api_passages/<slug>_bge/
    open      ref_pool/deepseek/               malign-logits stash, key
                                               (embedder, prompt, text)

The surprisal axis is ours -- one deepseek pass, one model, one device. **The bge
sentence vectors for the open models are not**: they come from the stash in the
archived repo at `data/raw/cache/sent_embeddings`, which is the same stash
`build_population.py:233` read to compute `passages_std.parquet`'s `mean_drift`.

That provenance is the reason to use it rather than a caveat about it.
`drift_geometry/sentence_vecs` also holds per-sentence vectors for these
passages, but that producer split with **stanza** (`embed_passages.py:218`) while
the passage number beside it was computed on **nltk-en** -- on 315 passages in
both, 236 reproduce the stored `mean_drift` to 1e-6 and 9% differ by more than
0.01. The stash reproduces it on **400 of 400** sampled rows. Same instrument as
the column it decomposes, so the stanza route is not used at all.

## EVERY SENTENCE DECOMPOSITION IS CHECKED AGAINST THE PASSAGE IT DECOMPOSES

`reproduces` is `mean(step) == drift` to 1e-6, per passage, against
`quadrants.csv`. It costs one dot product and it is the only thing standing
between a sentence table and a passage number it merely sits next to. It is
computed for all three pools, not just the one that looked suspect.

The sentence TEXT is reconstructed, never assumed, and the check differs by what
each producer recorded:

    bge sidecars   `sent_chars` is stored, so the re-split lengths must match it
                   ELEMENT-WISE (3,000 of 3,000 human rows do)
    the stash      only vectors are stored, so the re-split must yield exactly
                   `len(vectors)` sentences

Both re-split with `nltk.sent_tokenize` on RAW text -- not `.strip()` --
matching `bge_human.py:150`. The source CSV is opened with `newline=""` for the
same reason: universal newline translation edits `\r` out of quoted fields, and
text that has been edited is text the stash cannot find and the sha disowns. A passage failing its check is dropped with a
counted reason rather than emitted with captions that may belong to different
vectors.

## THE TWO GRAINS ARE JOINED ONTO THE SENTENCE ROW, BY CHARACTER POSITION

`mean_bits` puts the word axis and the sentence axis on the same row, so "do the
surprising words sit in the sentences that move?" is a query rather than a
reconstruction. The join is positional: words are walked in order, each located
in the text from where the last one ended, and assigned to the sentence whose
character span contains its start.

**Position is the only honest join available.** The word producer (deepseek
tokens, attributed to words by last byte) and the sentence producer (nltk-en,
bge) share the passage text and nothing else -- no common index, no common unit.
Matching on the word STRING alone would attach every later `the` to the first
`the`, so the walk carries a cursor. `n_words` is carried beside `mean_bits`
because a mean over three words and a mean over forty are not comparable, and a
rate whose population is not stated is the defect this campaign keeps paying for.

**`mean_bits` IS LENGTH-DEPENDENT AND THE DEPENDENCE IS STATED, NOT REMOVED.**
Pooled `r(n_words, mean_bits) = -0.161` over 196,184 sentences, and the medians
run 5.78 bits at 1-3 words down to 4.26 at 13-25. A short sentence opens with an
unpredictable word and has nothing to dilute it, so ranking sentences by
`mean_bits` alone ranks short ones to the top. Nothing here corrects for it --
a correction would be a modelling choice this file has no standing to make --
which is exactly why `n_words` sits in the next column. `within_passage.py`
controls for it explicitly and reports the partial correlation beside the raw.
Words that cannot be located, and the unscored first word, are excluded from
both -- so `sum(n_words)` is at or below the passage's scored word count.

## `dist_from_first` IS NOT `step`

`step` is the local move from sentence i-1 to i and is what `mean_drift`
averages. `dist_from_first` is displacement from the opening sentence, so
`is_furthest` marks the sentence that travelled furthest from where the passage
began. A passage can have small steps and large displacement (a steady walk) or
large steps and small displacement (oscillation), and only the second column
tells them apart. `step` is null at index 0, which has no predecessor.
"""

import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
ARCHIVE = "/Users/rj416/github/malign-logits"
STASH = os.path.join(ARCHIVE, "data/raw/cache/sent_embeddings")
SRC = os.path.join(HERE, "results", "quadrants.csv")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

DIM = 1024
#: the English namespace `build_population.py` used; the `|full` and untagged
#: variants are DIFFERENT populations of the same passages (5.26 vs 11.89 mean
#: sentences), so the tag is load-bearing and not decoration.
NS_EN = "BAAI/bge-m3|nltk-en|refuse-untrunc-2026-08-14"
TOL = 1e-6


def _ref_sources():
    """-> {id: (jsonl_row, f32_path, i32_path)} across every scored pool."""
    out = {}
    roots = [os.path.join(DATA, "ref_pool", "deepseek")]
    api = os.path.join(DATA, "api_passages")
    if os.path.isdir(api):
        roots += [os.path.join(api, d) for d in sorted(os.listdir(api))
                  if d.endswith("_ref") and os.path.isdir(os.path.join(api, d))]
    for root in roots:
        jl = os.path.join(root, "ref_shard00.jsonl")
        if not os.path.exists(jl):
            continue
        f32, i32 = (os.path.join(root, "ref_shard00.f32"),
                    os.path.join(root, "ref_shard00.i32"))
        for line in open(jl):
            r = json.loads(line)
            out[r["id"]] = (r, f32, i32)
    return out


def _bge_sources():
    """-> {id: (jsonl_row, f32_path)} for the human and API pools."""
    out = {}
    roots = [os.path.join(DATA, "jakobson_space", "bge_human")]
    api = os.path.join(DATA, "api_passages")
    if os.path.isdir(api):
        roots += [os.path.join(api, d) for d in sorted(os.listdir(api))
                  if d.endswith("_bge") and os.path.isdir(os.path.join(api, d))]
    for root in roots:
        jl = os.path.join(root, "bge_human00.jsonl")
        if not os.path.exists(jl):
            continue
        f32 = os.path.join(root, "bge_human00.f32")
        for line in open(jl):
            r = json.loads(line)
            out[r["id"]] = (r, f32)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(DATA, "jakobson_space", "exploded"))
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    import csv
    import numpy as np
    import nltk
    import pyarrow as pa, pyarrow.parquet as pq
    from hashstash import HashStash
    from ref_surprisal import word_bits

    csv.field_size_limit(10 ** 7)
    #: `newline=""` IS REQUIRED, not stylistic. Without it Python's universal
    #: newline translation rewrites `\r\n` to `\n` INSIDE a quoted field, so two
    #: passages containing carriage returns came back with text that no longer
    #: hashed to their own `text_sha` -- and the stash, which keys on the text,
    #: missed them. A silent 2-in-14,414 corruption of the column the passages
    #: are read out of.
    rows = list(csv.DictReader(open(a.src, newline="")))
    if a.limit:
        rows = rows[:a.limit]
    #: `anchor_id` is the bge key for human passages; the ref key is `huma-*`.
    anchor = {}
    for line in open(os.path.join(DATA, "ref_pool", "ref_pool.jsonl")):
        j = json.loads(line)
        if j.get("anchor_id"):
            anchor[j["id"]] = j["anchor_id"]

    refs, bges = _ref_sources(), _bge_sources()
    st = HashStash(STASH, engine="lmdb", serializer="hashstash",
                   compress="lz4", b64=True, flat=True)
    mm = {}

    def block(path, dtype, off, n):
        if path not in mm:
            mm[path] = np.memmap(path, dtype=dtype, mode="r")
        return np.asarray(mm[path][off:off + n])

    W = collections.defaultdict(list)
    S = collections.defaultdict(list)
    lost = collections.Counter()
    n_repro = n_sent_pass = 0

    for r in rows:
        pid, text = r["id"], r["text"]

        # ---- words -------------------------------------------------------
        got = refs.get(pid)
        _wsrc = None
        if not got:
            lost["word: no ref row"] += 1
        else:
            jr, f32, i32 = got
            sur = block(f32, np.float32, jr["row"], jr["n"])
            ends = block(i32, np.int32, jr["row"], jr["n"])
            _wsrc = (sur, ends)
            for i, w in enumerate(word_bits(text, sur, ends)):
                W["id"].append(pid); W["word_index"].append(i)
                W["word"].append(w["word"]); W["bits"].append(float(w["bits"]))
                W["partial"].append(bool(w.get("partial", False)))

        # ---- sentences ---------------------------------------------------
        #: two routes, ONE instrument (bge-m3 | nltk-en). Which route a passage
        #: takes is decided by where its vectors were written, not by its arm.
        V = sents = None
        gb = bges.get(anchor.get(pid, pid))
        if gb:
            br, bf = gb
            sents = nltk.sent_tokenize(text)
            if [len(x) for x in sents] != list(br["sent_chars"]):
                lost["sentence: re-split does not match sent_chars"] += 1
                continue
            V = block(bf, np.float32, br["row"], br["n_sentences"] * DIM
                      ).reshape(br["n_sentences"], DIM)
        elif r["category"] in ("base", "aligned"):
            try:
                sv = st.get({"embedder": NS_EN, "prompt": r["prompt"], "text": text})
            except Exception as e:
                lost["sentence: stash raised (%s)" % type(e).__name__] += 1
                continue
            if sv is None:
                lost["sentence: not in the stash"] += 1
                continue
            V = np.asarray(sv, dtype=np.float32)
            sents = nltk.sent_tokenize(text)
            if len(sents) != len(V):
                #: the stash stores no `sent_chars`, so the count IS the check.
                lost["sentence: re-split count != vector count"] += 1
                continue
        else:
            lost["sentence: no vector source for this pool"] += 1
            continue

        if len(V) < 2:
            lost["sentence: under 2 sentences (drift undefined)"] += 1
            continue
        n_sent_pass += 1
        #: ---- join the word grain onto the sentence grain, by position.
        spans, at = [], 0
        for sent in sents:
            j = text.find(sent, at)
            j = at if j < 0 else j
            spans.append((j, j + len(sent))); at = j + len(sent)
        wb = collections.defaultdict(list)
        cur = 0
        for w in (word_bits(text, *_wsrc) if _wsrc else []):
            k = text.find(w["word"], cur)
            if k < 0:
                continue
            cur = k + len(w["word"])
            if w.get("partial"):
                continue
            for si, (s0, s1) in enumerate(spans):
                if s0 <= k < s1:
                    wb[si].append(float(w["bits"])); break
        d0 = 1.0 - V @ V[0]
        step = [None] + [1.0 - float(V[i - 1] @ V[i]) for i in range(1, len(V))]
        #: THE CHECK: does this decomposition reproduce the passage number it
        #: claims to decompose? Recorded per row, never assumed.
        repro = abs(sum(step[1:]) / (len(V) - 1) - float(r["drift"])) < TOL
        n_repro += bool(repro)
        far = int(np.argmax(d0))
        for i in range(len(V)):
            S["id"].append(pid); S["sent_index"].append(i)
            S["sentence"].append(sents[i])
            S["step"].append(step[i]); S["dist_from_first"].append(float(d0[i]))
            S["is_furthest"].append(i == far); S["reproduces"].append(repro)
            S["mean_bits"].append(sum(wb[i]) / len(wb[i]) if wb.get(i) else None)
            S["n_words"].append(len(wb.get(i, [])))

    os.makedirs(a.out_dir, exist_ok=True)
    wp = os.path.join(a.out_dir, "words.parquet")
    sp = os.path.join(a.out_dir, "sentences.parquet")
    pq.write_table(pa.table(dict(W)), wp)
    pq.write_table(pa.table(dict(S)), sp)
    print("passages in: %d" % len(rows))
    print("  words.parquet     %7d rows over %5d passages"
          % (len(W["id"]), len(set(W["id"]))))
    print("  sentences.parquet %7d rows over %5d passages"
          % (len(S["id"]), len(set(S["id"]))))
    #: SAY IT. A decomposition that does not reproduce its passage is the one
    #: defect this file can have, so it is reported whether or not it occurred.
    print("  reproduces passage drift to %g: %d of %d%s"
          % (TOL, n_repro, n_sent_pass,
             "" if n_repro == n_sent_pass else "   <-- %d DO NOT"
             % (n_sent_pass - n_repro)))
    for k, v in sorted(lost.items()):
        print("  dropped %-48s %6d" % (k, v))
    print("-> %s\n-> %s" % (wp, sp))


if __name__ == "__main__":
    main()
