"""Is the homogeneous national story pretraining's or post-training's?

    .venv/bin/python -u run.py --plan
    .venv/bin/python -u run.py --run --pairs meta-llama/Llama-3.1-8B
    .venv/bin/python -u run.py --run --demonyms Norwegian American --n 4

Rettberg & Wigers (2025) generated 11,800 stories -- 50 for each of 236
countries -- by sending `"Write a 1500 word potential {demonym} story"` to
gpt-4o-mini, and found that beneath surface national symbols the stories
"overwhelmingly conform to a single narrative plot structure": a protagonist
returns to a small town and resolves a minor conflict by reconnecting with
tradition and organising a community event.

**THEY HAVE ONE ARM, AND THEY SAY SO.** Their p. 11: *"is their blandness the
result of censorship - deliberate alignment and filtering of the language
models' output - or is it rather an artefact of the model itself? Probably it is
both."* That question needs a base model, and gpt-4o-mini does not have a
published one.

## THE STEM, AND WHY IT IS NOT AN INSTRUCTION

A base model cannot be told to write a story; it continues a document. So the
prompt is PARATEXT rather than instruction:

    A {Demonym} Story\\n\\nIt was a

Measured on Llama-3.1-8B, 2026-08-30, raw (no chat template), six samples each:

    stem                                narrative   register
    "It was a"                                0/6   weather reports, sports, blogs
    "A Norwegian Story\\n\\n"                    0/5   TITLE PAGES -- byline, copyright,
                                                table of contents, author bio
    "A Norwegian Story\\n\\nShe was"            3/6   half slide back to apparatus
    "A Norwegian Story\\n\\nIt was a"           6/6   narrative, 5/6 Nordic

**The title alone is not enough and the reason is interesting**: to a base model
a title is a POSITION IN A DOCUMENT, and what follows a title is usually
apparatus. One sample answered with `qtestinfo("A Norwegian Story", "country",
"nl", "norp")` -- NORP is spaCy's entity label for nationalities, so the model
had placed the string in an NLP test fixture. `"She was"` is ambiguous between
narrative and obituary. `"It was a"` is obligatorily narrative and holds.

The title's contribution is visible at seed parity, same seed either side:

    "She was"                     -> "...a girl who never had a Christmas gift to
                                      one of Europe's last great queens...
                                      Home >> Software & Services >>"
    "A Norwegian Story / She was" -> "...a girl who never had a gala evening to
                                      one of Europe's last great beauties... she
                                      played with the Norwegian flag on the ice"

## WHAT THE PILOT ALREADY SHOWS

Same stem, same seeds, two arms of one lineage:

    BASE      granny Sonen's knitting-bag, sheaves of rye, Rosse-roed Point,
              "the wind was singing through the firs" -- 19th-century literary
    INSTRUCT  "Kari and Maria, two young friends, had decided to take a walk in
              the forest"; "Erle... early twenties, a free-spirited wanderer"
    INSTRUCT  "the small town of Willow Creek. Children's laughter filled the air
      (US)    as they rode their bikes down the sidewalk, their parents watching"

The last is Rettberg's plot verbatim, unprompted, on the fourth sample. **The
base arm has abundant national narrative and it does not look like this**, which
is the claim their design cannot reach.

## LENGTH

They asked for 1500 words. Measured on generated text of this register,
**1.24 tokens/word**, so 1500 words is ~1,900 tokens. At 8B on MPS that is ~3
minutes per story single-stream (10.6 tok/s at 2048, 18.4 at 512 -- KV growth).
The full design, 236 demonyms x 50 x 2 arms, is 23,600 stories and ~45M tokens:
a cloud vLLM job via `malignment.cloud`, not a local one. This runs the pilot.
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
#: depth-independent: malignment.paths walks up from the package itself. The
#: old dirname-dirname form was wrong at depth 2 and would NOT have raised --
#: malignment is installed in the venv, so the bad insert is simply ignored.
from malignment.paths import repo_root  # noqa: E402
sys.path.insert(0, repo_root())

from malignment import roster  # noqa: E402

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
OUT = os.path.join(DATA, "national_story", "pilot.jsonl")

#: **THE ARTICLE HAS TO AGREE.** "A American Story" is ungrammatical and would
#: perturb the continuation on its own -- the manipulation would then be article
#: agreement crossed with nationality. Rettberg never met this because their
#: prompt puts the demonym after a number ("a 1500 word potential Norwegian
#: story"), where the article always attaches to the number.
VOWEL = tuple("AEIOU")


def stem_for(dem):
    if not dem:
        return "A Story\n\nIt was a"
    art = "An" if dem[:1].upper() in VOWEL else "A"
    return "%s %s Story\n\nIt was a" % (art, dem)


#: Rettberg's own close-read four, plus cases where their account predicts
#: something specific: Ghana (their worked example of a festival resolution),
#: India (their named exception, where the protagonist LEAVES), and three large
#: non-Anglophone corpora. `None` is the no-demonym control, which they also ran.
DEMONYMS = [None, "Norwegian", "American", "Palestinian", "Israeli",
            "Ghanaian", "Indian", "Japanese", "Nigerian", "Brazilian"]

#: 1500 words at the measured 1.24 tok/word for this register.
MAX_NEW = 1900


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="*", default=["meta-llama/Llama-3.1-8B"])
    ap.add_argument("--demonyms", nargs="*")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--max-new", type=int, default=MAX_NEW)
    #: **A DELIBERATE DEVIATION FROM THE PINNED `generate.DECODER`, AND WHY.**
    #: That module pins temperature 1.0 / top_p 1.0 / top_k 0 to match the
    #: f11_l2 corpus, and top_k=0 genuinely disables truncation. Correct for
    #: NEXT-TOKEN measurement, where the true distribution is the object. Fatal
    #: for 1,900-token generation: surviving N tokens is (1-p)^N, so a per-token
    #: derailment probability of 1e-3 gives 15% survival at N=1900 and 1e-4 gives
    #: 83%. Measured on the first pilot at top_p 1.0, the last quarter of the
    #: story collapsed to token salad in 11 of 20 ALIGNED samples against 2 of 20
    #: base. Truncating the bottom 5% of mass removes the tail those derailments
    #: come from.
    #:
    #: **TEMPERATURE STAYS AT 1.0.** top_p removes the tail without reshaping the
    #: head; lowering temperature sharpens the whole distribution and would alter
    #: the model's voice, which is the thing being compared between arms.
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)

    dems = a.demonyms if a.demonyms is not None else DEMONYMS
    if a.demonyms:
        dems = [None if d.lower() == "none" else d for d in dems]
    eps, _ = roster.endpoints()
    arms = []
    for b in a.pairs:
        arms.append((b, "base"))
        if b in eps:
            arms.append((eps[b], "aligned"))

    #: **A PRODUCER MUST NEVER TURN A MISSING MODEL INTO A DOWNLOAD.** On
    #: 2026-08-30 `produce_hidden` treated `snapshot_dir()` (which resolves on
    #: config.json alone) as a cache test, passed 13 metadata-only entries, and
    #: `load_for_twp` fetched them: ~400GB queued including Llama-3.1-70B-Instruct
    #: and two 32B Olmo-3s, onto a disk with 183GB free. Caught mid-fetch. The
    #: files are checked with os.path.exists because a snapshot holds SYMLINKS
    #: into ../../blobs and a half-fetched revision leaves them dangling.
    import glob as _g
    from malignment.checkpoint import Checkpoint as _CK
    missing = []
    for m, _role in arms:
        try:
            d = _CK(m).snapshot_dir()
            files = (_CK(m).shard_paths()
                     or (_g.glob(os.path.join(d, "*.safetensors")) if d else [])
                     or (_g.glob(os.path.join(d, "*.bin")) if d else []))
            if not any(os.path.exists(f) for f in files):
                missing.append(m)
        except Exception:
            missing.append(m)
    if missing:
        raise SystemExit(
            "REFUSING: %d model(s) not cached locally, and this producer does not\n"
            "download. Fetch them deliberately or drop them from --pairs:\n  %s"
            % (len(missing), "\n  ".join(missing)))

    dec = {"max_new_tokens": a.max_new, "top_p": a.top_p}
    #: the decoder is part of the identity, per `generate.gen_key`: two draws
    #: that differ only by top_p are different measurements, and a resume keyed
    #: without it would serve one as the other.
    dkey = "top_p=%g,max_new=%d" % (a.top_p, a.max_new)
    print("decoder: %s" % dkey)
    print("demonyms %d | arms %d | n %d | max_new %d | stories %d | ~%.0f min at 3min each"
          % (len(dems), len(arms), a.n, a.max_new,
             len(dems) * len(arms) * a.n,
             len(dems) * len(arms) * a.n * 3))
    for m, role in arms:
        print("   %-8s %s" % (role, m))
    if a.plan or not a.run:
        for d in dems:
            print("   %r" % stem_for(d))
        return

    #: **APPEND PER STORY.** A 2-hour generation run that writes at the end is a
    #: 2-hour run that loses everything to one exception, and this one is long
    #: enough that it will meet one.
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try:
                r = json.loads(line)
                #: rows written before the decoder was recorded were the pinned
                #: default; name it rather than let them match anything.
                k = r.get("decoder_key") or "top_p=1,max_new=%d" % r.get("max_new", 0)
                done.add((r["model"], r["demonym"], r["sample"], k))
            except Exception:
                pass
    print("already written: %d" % len(done), flush=True)

    from malignment import Checkpoint
    from malignment import generate as G
    import gc
    import torch

    def reclaim():
        """**RETURN THE ALLOCATOR'S CACHE, NOT JUST THE PYTHON REFERENCE.**
        `del ld` drops the reference; MPS keeps the blocks. Over twenty
        load/unload cycles that is the difference between steady state and
        swapping, and this machine was at 56.1GB of 57.3GB swap when the first
        attempt was killed."""
        gc.collect()
        for fn in ("empty_cache", "synchronize"):
            try:
                getattr(torch.mps, fn)()
            except Exception:
                pass

    fh = open(a.out, "a")
    #: **DEMONYM-MAJOR, ARMS INNER.** Arm-major finishes all ten base cells
    #: before the aligned arm starts, so the first PAIR arrives at the end of the
    #: run. The comparison is the point, and a partial run should already contain
    #: some. The cost is one model load per (demonym, arm) rather than per arm --
    #: ~45s x 20 against ~45s x 2 -- which is a real 15 minutes and worth it.
    for d in dems:
        for mid, role in arms:
            need = [i for i in range(a.n) if (mid, d, i, dkey) not in done]
            if not need:
                continue
            t0 = time.time()
            ck = Checkpoint(mid)
            ld = ck.load()
            #: seeded per sample inside generate(), so `n` samples are n
            #: observations and a rerun reproduces. Seeds are shared across arms
            #: and demonyms deliberately -- the title's effect is visible at seed
            #: parity, and that is half the evidence.
            #: **`ck.generate`, NOT `G.generate`.** The module function is the
            #: machinery and stashes NOTHING. The Checkpoint method is the handle:
            #: it keys each draw by model/prompt/frame/decoder/seed/sample_idx,
            #: writes it to the generations stash, reads across every producer's,
            #: and fills only the shortfall. This producer called the bare
            #: function and so lost three things at once -- `finish`, so stopping
            #: had to be inferred from length; the cache, so every rerun
            #: regenerated from scratch; and discoverability, so no other seat
            #: could find these passages by key. `loaded=ld` reuses the load.
            ps = ck.generate(stem_for(d), n=max(need) + 1, seed=0,
                             template=False, loaded=ld,
                             decoder=dec)
            for i in need:
                if i >= len(ps):
                    continue
                p = ps[i]
                txt = p.text if hasattr(p, "text") else str(p)
                #: `finish` and `n_new_tokens` come from the generator itself.
                #: Without them, "ran to the cap" and "had not finished yet" are
                #: the same observation -- and with a cap near the comparison
                #: corpus's median that ambiguity covers most of the distribution.
                fh.write(json.dumps(dict(
                    model=mid, role=role, demonym=d, sample=i,
                    stem=stem_for(d), max_new=a.max_new,
                    decoder=dec, decoder_key=dkey,
                    finish=getattr(p, "finish", None),
                    n_new_tokens=getattr(p, "n_new_tokens", None),
                    n_words=len(txt.split()), text=txt), ensure_ascii=False) + "\n")
            fh.flush()
            print("  %-12s %-8s %d samples %5.0fs  %s words"
                  % (d or "(none)", role, len(need), time.time() - t0,
                     "/".join(str(len((ps[i].text if hasattr(ps[i], "text")
                                       else str(ps[i])).split())) for i in need)),
                  flush=True)
            del ld, ck, ps
            reclaim()
    fh.close()
    print("\n-> %s" % a.out)


if __name__ == "__main__":
    main()
