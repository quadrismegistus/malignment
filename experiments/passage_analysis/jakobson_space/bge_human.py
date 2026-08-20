"""bge-m3 sentence vectors for the human anchor, on the model passages' splitter.

    python .../bge_human.py --input $MALIGNMENT_DATA/jakobson_space/human_anchor.jsonl \
        --out $MALIGNMENT_DATA/jakobson_space/bge_human

The drift half of the axis. Supplies the same object the model side has: one
L2-normalized 1024-d vector per sentence, in a `.f32` sidecar, with `row`/`n`
pointing into it, so any drift statistic can be recomputed later without
re-embedding.

## NLTK-EN, NOT STANZA (RH, 2026-08-20)

The parquet's vectors live under `BAAI/bge-m3|nltk-en|refuse-untrunc-2026-08-14`.
`../drift_geometry/embed_passages.py` uses stanza-en, and the two agree closely
enough to look interchangeable -- r=0.961 on sentence counts, 62.3% of passages
split identically -- which is exactly what makes substituting one dangerous. The
remaining 37.7% would put a share of the human corpus on a second instrument
while the label said one, and every drift metric here is a function of the
sentence sequence. Same reason the BLT scoring was copied verbatim rather than
rewritten: an axis is only an axis if both sides were measured by one rule.

Copied from `malign-logits/scripts/bge_cloud.py`, which produced the model-side
vectors. The archive is read-only, so this is a copy rather than an import.

## What is dropped from the fleet version, and why it is safe here

The fleet routed by script and carried a `--mixed-policy` for passages mixing
Latin and CJK. The human anchor is all-English by construction -- six English
corpora, no generation, no code-switching -- so the route is fixed to nltk-en and
`script` is recorded as `en` rather than inferred. `stanza-zh` is therefore never
built, which is why `warm()` here probes ONE splitter where the fleet probed two.

## THE WARM PROBE IS NOT CEREMONY

Built lazily, a splitter failure on the first passage leaves the handle None, the
caller's except turns that passage into a refusal, and every later passage
repeats it -- the whole corpus quietly becoming refusals while the run reports a
normal rate and exits 0. Proving the splitter splits before the loop turns that
into a first-second crash. The probe is three unambiguous sentences: a probe
whose failure is ambiguous cannot gate a run.
"""

import argparse, hashlib, json, os, sys, time
import numpy as np

BGE = "BAAI/bge-m3"
DIM = 1024
SPLITTER = "nltk-en"


def done_keys(*paths):
    """(id, text_sha) already handled -- embedded OR refused. -> set

    Refusals are included deliberately. If `done` covered only successes, a
    resumed run would retry every refusal forever and the printed count would
    describe a different quantity from the one it names.
    """
    got = set()
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                got.add((r.get("id"), r.get("text_sha")))
    return got


class Sentences:
    """nltk punkt, built once and probed before use."""

    def __init__(self):
        self._f = None

    def en(self, text):
        if self._f is None:
            import nltk
            try:
                nltk.data.find("tokenizers/punkt_tab")
            except LookupError:
                nltk.download("punkt_tab", quiet=True)
            self._f = nltk.sent_tokenize
        return [s for s in self._f(text) if s.strip()]

    def warm(self):
        n = len(self.en("A sentence. And a second one. Then a third one."))
        assert n >= 3, "nltk-en split a three-sentence probe into %d" % n
        print("  splitter warm: nltk-en -> %d on the probe" % n, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--batch", type=int, default=32)
    a = ap.parse_args()

    import torch
    from sentence_transformers import SentenceTransformer

    #: CPU IS THE REFEREE. mps corrupts short-sequence embeddings on this
    #: machine, and the model-side vectors were produced on cpu/cuda; a device
    #: delta between the two sides is a scorer difference wearing the costume of
    #: a speedup.
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print("device %s | shard %d/%d | splitter %s" % (dev, a.shard, a.of, SPLITTER),
          flush=True)

    model = SentenceTransformer(BGE, device=dev)
    sp = Sentences()
    sp.warm()

    os.makedirs(a.out, exist_ok=True)
    jl = os.path.join(a.out, "bge_human%02d.jsonl" % a.shard)
    fb = os.path.join(a.out, "bge_human%02d.f32" % a.shard)
    rp = os.path.join(a.out, "bge_human%02d.refused.jsonl" % a.shard)
    done = done_keys(jl, rp)
    #: ROW COUNTER FROM THE FILE'S OWN SIZE, never a remembered count.
    row = os.path.getsize(fb) // 4 if os.path.exists(fb) else 0
    assert row % DIM == 0, (
        "sidecar holds %d floats, not a multiple of dim %d -- a previous run was "
        "killed mid-write and the file is torn; truncate to %d before resuming"
        % (row, DIM, (row // DIM) * DIM))
    print("resuming: %d already handled (embedded + refused), %d vectors in the "
          "sidecar" % (len(done), row // DIM), flush=True)

    n_seen = n_new = n_sent = 0
    refused = []
    t0 = time.time()
    with open(a.input) as src, open(jl, "a") as out, open(fb, "ab") as sb:
        for i, line in enumerate(src):
            line = line.strip()
            if not line:
                continue
            if i % a.of != a.shard:
                continue
            r = json.loads(line)
            n_seen += 1
            if a.limit and n_seen > a.limit:
                break
            text = r.get("text") or ""
            pid = r.get("id")
            #: RAW text, matching the BLT pass so the two tables join on the sha.
            sha = hashlib.sha256(text.encode()).hexdigest()[:16]
            if (pid, sha) in done:
                continue
            try:
                sents = sp.en(text)
            except Exception as e:
                refused.append({"id": pid, "text_sha": sha, "splitter": SPLITTER,
                                "why": "split failed: %s" % e})
                continue
            if not sents:
                refused.append({"id": pid, "text_sha": sha, "splitter": SPLITTER,
                                "why": "no sentences"})
                continue

            vecs = model.encode(sents, batch_size=a.batch, convert_to_numpy=True,
                                normalize_embeddings=True,
                                show_progress_bar=False).astype(np.float32)
            assert vecs.shape == (len(sents), DIM), vecs.shape
            sb.write(vecs.tobytes())

            out.write(json.dumps({
                "id": pid, "corpus": r.get("corpus"), "text_sha": sha,
                "script": "en", "splitter": SPLITTER,
                #: THE KEY, namespaced by the splitter ACTUALLY used on this row,
                #: so a later reader can tell which instrument produced it.
                "ref": "%s|%s" % (BGE, SPLITTER),
                "n_chars": len(text), "n_sentences": len(sents),
                "sent_chars": [len(s) for s in sents],
                "row": row, "n": int(vecs.size), "dim": DIM,
                "normalized": True}) + "\n")
            row += int(vecs.size)
            n_sent += len(sents)
            n_new += 1
            if n_new % 100 == 0:
                out.flush(); sb.flush()
                el = (time.time() - t0) / 60
                print("  %d embedded, %d sentences  %.1f min  %.1f/s"
                      % (n_new, n_sent, el, n_new / max(el * 60, 1)), flush=True)

    if refused:
        with open(rp, "a") as fh:
            for r in refused:
                fh.write(json.dumps(r) + "\n")
        print("  REFUSED %d passage(s); recorded in %s"
              % (len(refused), os.path.basename(rp)), flush=True)
    print("shard %d done: %d seen, %d embedded, %d sentences, %d refused, %.1f min"
          % (a.shard, n_seen, n_new, n_sent, len(refused), (time.time() - t0) / 60),
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
