"""Final-position residual streams for a FROZEN prompt list. A producer.

    python -m malignment.produce_hidden --freeze          write the prompt list
    python -m malignment.produce_hidden --scan            what would run
    python -m malignment.produce_hidden --run [--device mps]

Writes `$MALIGNMENT_DATA/hidden/<model>.hidden.<dtype>` plus `manifest.json`,
in the shape `malignment.lens` reads: `(rows, n_layers+1, d_model)`, one row per
prompt, the FINAL POSITION only.

## THE PROMPT LIST IS FROZEN BEFORE ANY MODEL RUNS

`--freeze` writes `prompts.json` and every model then reads that file. This is
not tidiness. The v2 archive's sidecars were written per-run, and three of its
sixteen pairs are unusable today for exactly this reason -- `bloom-7b1` and
`Falcon-H1-7B-Base` hold prompt lists their aligned arms do not, so no swap
between the arms is possible at all. A pair whose two arms disagree about the
population cannot be compared, and the disagreement is invisible until someone
tries.

The frozen list is hashed into the manifest. A model dumped against a different
list is detectable rather than silently mixed in.

## WHY THIS BATTERY

Two sources, both already annotated by `task_charge`:

    H2's 231     the matched minimal pairs behind H2_alignment_depth
                 ("squeezed the rabbit in her grip" / "cradled the rabbit in
                 her grip"). 218 of 231 carry ratings. The neutral halves are a
                 built-in control arm, and 23 roster pairs already have PATCH
                 numbers on these exact prompts.
    a top-up     stratified over frame_kind x dose from the rated corpus, to
                 give the categories the minimal pairs are thin on.

**The v2 sidecars are the f11 contradiction set and share NOTHING with H2's
battery.** That is why the lens result and the patch result could not be joined:
not a disagreement between instruments, a disjoint population. Running the lens
on H2's prompts is what makes the two comparable, because the patch holds the
readout at base by construction and so cannot see the quantity the lens
measures. Complementary, not competing.

## WHAT IS STORED, AND WHAT THAT FORECLOSES

Final position, all layers, the model's native dtype.

**ONE STATE PER PROMPT, AND THE TOKEN PATH IS RESOLVED IN CONTEXT.** A word is
reachable from a single state when the model spells it as ONE token *after this
prompt*, which is not what `encode(" " + word)` answers. Measured over 150 frozen
prompts and 12,000 rated words:

    tokenizer        1-tok by encode(" "+w)    1-tok in context    mass in context
    Llama-3.1-8B                        97%                 97%                98%
    gemma-2-9b                          99%                 99%                99%
    CT-LLM-Base                         92%                 92%                93%
    llm-jp-3-7.2b                        0%                 92%                94%
    neo_7b                               0%                 86%                88%
    CroissantLLMBase                    74%                 74%                76%

**Two models read as 0% and neither had a coverage problem.** `llm-jp` encodes
`" kill"` standalone as `[279, 4024]` -- a word-boundary token then the word --
but after `"...turned over and"` it emits `[4024]` alone, one token. The isolated
encode measures the tokenizer's space convention; the in-context diff measures
what the model actually has to emit. `lens.single_token` takes the prompt for
this reason, and the round-trip decode check is `twp`'s, not new here.

I built a two-state store first -- prompt, and prompt plus a space token -- and it
recovered exactly the same 92% and 86% at twice the disk, because the extra state
was compensating for a tokenisation error rather than a missing factor. It is
recorded because the wrong fix reproduced the right numbers, which is the kind of
agreement that stops an investigation early.

**The residue is genuinely multi-token.** CroissantLLM at 74% splits those words
however they are tokenised, and that needs the full chain rule,
`prod_i p_L(t_i | prompt + t_1..t_{i-1})`, as
`malign-logits/scripts/twp_word_depth.py` does it. Measured on this battery that
is 88-120 DISTINCT PREFIXES per prompt after dedup across words -- ~46x the
forward passes, ~2.1TB if stored -- so it is a compute-per-pair job in the shape
of `twp_head_swap.py`, not a store, and this file deliberately does not attempt
it. What is left uncovered is a 1-24% tail of mass, named per model, instead of
two models at zero.

**All layers, not the readable top quarter.** The lens can see nothing below
~0.75 depth, but that is a fact about this lens on these words, and a probe that
does not go through the unembedding would want the rest. The saving was ~3x on a
store that is already small.
"""

import argparse
import collections
import hashlib
import json
import os
import sys

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
OUT = os.path.join(DATA, "hidden")
PROMPTS = os.path.join(OUT, "prompts.json")
MANIFEST = os.path.join(OUT, "manifest.json")

#: H2's actual battery, read from its results rather than from its producer's
#: default -- the producer's default prefixes select 60 prompts and H2 ran 231.
H2_RESULTS = "/Users/rj416/github/malign-logits/data/h2_depth"
BANDS = ((1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 8.0))
KINDS = ("SEXUAL", "VIOLENT", "COERCIVE", "DEGRADING", "ILLICIT", "OTHER", "NONE")


def h2_prompts():
    """The 231 distinct prompts H2 actually scored. Read the results, not the spec."""
    import glob
    seen = {}
    for f in glob.glob(os.path.join(H2_RESULTS, "*.canonical.jsonl")):
        for line in open(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("prompt"):
                seen[r["prompt"]] = None
    return sorted(seen)


def freeze(topup=380, seed=0):
    """Write the frozen prompt list. Idempotent given the same charge index."""
    import random
    from malignment import charge
    base = h2_prompts()
    have = set(base)
    ix = charge.index()["prompts"]
    #: a cell is (kind, band); draw round-robin so no category is crowded out by
    #: whichever one the corpus happens to be largest in.
    cells = collections.defaultdict(list)
    for p, d in ix.items():
        if p in have or d["dose"] is None or len(d["scene"]) < 8:
            continue
        k = d["frame_kind"] or "NONE"
        for lo, hi in BANDS:
            if lo <= d["dose"] < hi:
                cells[(k, (lo, hi))].append(p)
    rng = random.Random(seed)
    for v in cells.values():
        v.sort()
        rng.shuffle(v)
    keys = [(k, b) for k in KINDS for b in BANDS if cells.get((k, b))]
    extra, i = [], 0
    while len(extra) < topup and keys:
        k = keys[i % len(keys)]
        if cells[k]:
            extra.append(cells[k].pop())
        else:
            keys.remove(k)
            continue
        i += 1
    allp = base + sorted(extra)
    os.makedirs(OUT, exist_ok=True)
    doc = dict(
        n=len(allp), n_h2=len(base), n_topup=len(extra),
        charge_sha=charge.index()["source_sha"], seed=seed,
        sha=hashlib.sha256("\x00".join(allp).encode()).hexdigest()[:16],
        prompts=allp)
    json.dump(doc, open(PROMPTS, "w"), indent=1, ensure_ascii=False)
    return doc


def load_frozen():
    if not os.path.exists(PROMPTS):
        raise SystemExit("no frozen prompt list; run --freeze first")
    return json.load(open(PROMPTS))


def todo(manifest):
    """[(model_id,)] for every arm of every cached endpoint pair not yet dumped."""
    from malignment import roster
    from malignment.checkpoint import Checkpoint
    eps, _ = roster.endpoints()

    def cached(m):
        #: **A SNAPSHOT DIRECTORY IS NOT WEIGHTS, AND NEITHER IS A CONFIG.**
        #: `snapshot_dir()` resolves on `config.json` alone -- correct for its own
        #: job, wrong as a cache test. Using it here passed 13 metadata-only
        #: entries as cached, and `load_for_twp` then DOWNLOADED them: 400GB
        #: including Llama-3.1-70B-Instruct and two 32B Olmo-3s, onto a disk with
        #: 196GB free. A producer must never turn a missing input into a network
        #: fetch it was not asked for. The files are checked with `os.path.exists`
        #: because a snapshot holds SYMLINKS into ../../blobs and a half-fetched
        #: revision leaves them dangling.
        try:
            ck = Checkpoint(m)
            d = ck.snapshot_dir()
            if not d:
                return False
            import glob as _g
            files = (ck.shard_paths()
                     or _g.glob(os.path.join(d, "*.safetensors"))
                     or _g.glob(os.path.join(d, "*.bin")))
            return any(os.path.exists(f) for f in files)
        except Exception:
            return False

    out = []
    for b, a in sorted(eps.items()):
        if not (cached(b) and cached(a)):
            continue
        for m in (b, a):
            if m not in manifest and m not in out:
                out.append(m)
    return out


def venv_of(mid):
    """The venv this checkpoint's declaration requires, by basename."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "scripts"))
    import venvs
    return os.path.basename(venvs.venv_for(mid))


def current_venv():
    import sys
    return os.path.basename(os.path.dirname(os.path.dirname(sys.executable)))


#: **A MODEL CAN OVERFLOW ITS OWN COMPUTE DTYPE AND SAY NOTHING.** `BAAI/Aquila2-7B`
#: and `AquilaChat2-7B` run in float16 by `compute_dtype` and produce nan from
#: layer 19 up, in 565 of 611 rows. Nothing raised: the file is the right size,
#: the manifest is well-formed, and the defect surfaced only as `cov nan` in a
#: downstream table. Any model listed here is dumped in the named dtype instead,
#: and the manifest records what was actually used so the exception is visible
#: rather than folded into the store.
DTYPE_OVERRIDE = {
    "BAAI/Aquila2-7B": "float32",
    "BAAI/AquilaChat2-7B": "float32",
}


def dump(mid, prompts, batch=16):
    """(filename, manifest entry) for one model, loaded through the runner.

    **THE LOADER IS `runners.load_for_twp`, NOT `from_pretrained`.** A second
    loader is a second instrument -- that is `load_for_twp`'s own docstring, and
    the archive's `server.py._get_slot_model` is the case it is written against:
    a parallel load path that never grew the MPT override, the rate-limit retry
    or the mask guard, so the app could load a model the runner refuses. Going
    through it gets the revision pin, `compute_dtype`, `LOADER_OVERRIDE`, the mpt
    `trust_remote_code` refusal and the chat-template override for free, and
    cannot drift from what produced every other cell in the store.
    """
    import numpy as np
    import torch
    from . import runners
    from .checkpoint import Checkpoint
    L = runners.load_for_twp(Checkpoint(mid))
    m, tok, dev = L.model, L.tok, L.dev
    ov = DTYPE_OVERRIDE.get(mid)
    if ov:
        m = m.to(getattr(torch, ov))
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    dt = next(m.parameters()).dtype
    #: read off the loader BEFORE the model is dropped -- these are the stamps
    #: that say which instrument produced the file, and `del L` is three lines
    #: below.
    loader_id = getattr(L, "loader_id", None)
    rows = []
    with torch.no_grad():
        for i in range(0, len(prompts), batch):
            enc = tok(prompts[i:i + batch], return_tensors="pt",
                      padding=True).to(dev)
            o = m(**enc, output_hidden_states=True)
            #: final position, every layer. `hidden_states` is (n_layers+1)
            #: tensors of (batch, seq, d_model); LEFT padding means index -1 is
            #: the last REAL token for every row, which is why padding_side is
            #: set above rather than assumed.
            h = torch.stack([x[:, -1, :] for x in o.hidden_states], 1)
            rows.append(h.to(torch.float32).cpu().numpy())
            del o
    del m, L
    try:
        torch.mps.empty_cache()
    except Exception:
        pass
    A = np.concatenate(rows, 0)
    #: **STORED AS f32 WHATEVER THE COMPUTE DTYPE WAS, AND THE DTYPE IS RECORDED
    #: SEPARATELY.** bf16 has no numpy dtype, and narrowing a bf16 activation to
    #: fp16 is a silent precision change rather than a size saving -- they differ
    #: in exponent range, not only mantissa. `compute_dtype` says what the model
    #: actually ran in; the file says what the bytes are.
    fn = mid.replace("/", "__") + ".hidden.f32"
    A.tofile(os.path.join(OUT, fn))
    return fn, dict(file=fn, dtype="f32", rows=int(A.shape[0]),
                    rows_per_prompt=1,
                    shape_per_row=[int(A.shape[1]), int(A.shape[2])],
                    compute_dtype=str(dt), dtype_override=ov, device=str(dev),
                    loader_id=loader_id,
                    venv=current_venv())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--topup", type=int, default=380)
    ap.add_argument("--models", nargs="*")
    a = ap.parse_args(argv)

    if a.freeze:
        d = freeze(a.topup)
        print("frozen %d prompts (%d from H2, %d topup) sha %s -> %s"
              % (d["n"], d["n_h2"], d["n_topup"], d["sha"], PROMPTS))
        return

    doc = load_frozen()
    os.makedirs(OUT, exist_ok=True)
    man = {}
    if os.path.exists(MANIFEST):
        m = json.load(open(MANIFEST))
        #: a manifest built against a different prompt list is not a partial
        #: result to resume, it is a different store. Refuse rather than mix.
        if m.get("prompts_sha") != doc["sha"]:
            raise SystemExit("manifest was built against prompt list %s, frozen "
                             "list is %s -- move it aside or re-freeze"
                             % (m.get("prompts_sha"), doc["sha"]))
        man = m.get("models", {})

    want = a.models or todo(man)
    #: **A MODEL DECLARES ITS ENVIRONMENT AND 10 OF THE 68 ARE NOT THIS ONE.**
    #: `.venv-tf457` pins transformers 4.57.1 for checkpoints that break on 5.x
    #: (OLMoE's tie_word_embeddings bool/int, among others). Loading one of those
    #: here would fail, or worse succeed differently, so they are partitioned out
    #: and named rather than attempted -- the run says what it did not do.
    cur = current_venv()
    mine, theirs = [], collections.defaultdict(list)
    for m in want:
        try:
            v = venv_of(m)
        except KeyError:
            v = cur
        (mine if v == cur else theirs[v]).append(m)
    print("frozen prompts %d sha %s | already dumped %d | to do %d"
          % (doc["n"], doc["sha"], len(man), len(want)))
    print("  this venv (%s): %d" % (cur, len(mine)))
    for v, ms in sorted(theirs.items()):
        print("  %s: %d  ->  %s/bin/python -m malignment.produce_hidden --run"
              % (v, len(ms), v))
    if a.scan or not a.run:
        for m in mine:
            print("   %s" % m)
        return
    want = mine

    import time
    for i, mid in enumerate(want, 1):
        t = time.time()
        try:
            fn, e = dump(mid, doc["prompts"])
        except Exception as ex:
            print("  %3d/%d %-44s FAILED %s: %s"
                  % (i, len(want), mid[:44], type(ex).__name__, str(ex)[:60]),
                  flush=True)
            continue
        man[mid] = e
        json.dump(dict(prompts_sha=doc["sha"], n_prompts=doc["n"],
                       prompts=doc["prompts"], models=man),
                  open(MANIFEST, "w"), ensure_ascii=False)
        print("  %3d/%d %-44s %s %s %.0fs"
              % (i, len(want), mid[:44], e["dtype"],
                 tuple(e["shape_per_row"]), time.time() - t), flush=True)
    print("\n-> %s  (%d models)" % (OUT, len(man)))


if __name__ == "__main__":
    main()
