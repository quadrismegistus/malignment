"""Sample the salary distribution across every locally-cached endpoint pair.

    .venv/bin/python       -u .../gen.py --plan       scope, loads nothing
    .venv/bin/python       -u .../gen.py              the 50 `.venv` models
    .venv-tf457/bin/python -u .../gen.py              the 6 `.venv-tf457` ones
    .venv/bin/python       -u .../gen.py --models a b just these

**RUN IT ONCE PER VENV, as `subject_position/run.py` is run once per profile.**
`scripts/venvs.py` partitions the roster by the `transformers` specifier each
node declares, and this sweep straddles the partition: 50 of the 56 models are
`.venv` (>=5), and the six allenai OLMo checkpoints declare `>=4.57,<5` and are
`.venv-tf457`. Each invocation skips what the other owns and says so; the cache
means the second pass costs only its own six models.

Replaces the two-lineage pilot behind `numeric_boundary/results/beam.csv`. The
pilot is PARKED for a reason this run is built to remove: 360M and 500M
"cannot separate a coherence effect from an alignment effect", so a base model
saying `$500` might be junk being cleaned up rather than a distribution being
narrowed. The population here is 28 lineage pairs whose bases are fluent.

## WHY THIS USES `Checkpoint.generate` AND THE PILOT DID NOT

The pilot called `L.model.generate(..., num_return_sequences=100)` directly:
one batched call per prompt, nothing stored. Fast, and it has to be redone in
full every time anyone wants a different slice.

`Checkpoint.generate` keys each draw on `(model, prompt, frame, system, RESOLVED
DECODER, seed, sample_idx)` and stores it, so a rerun fills the shortfall
instead of repeating the run, and a draw made on the other machine is not a
cache miss. The cost of that is real and is not hidden: it generates ONE sample
per `model.generate` call, because per-sample seeding is exactly what makes
sample 7 addressable as sample 7. Measured on this machine at 16 tokens --
0.223 s/sample at 360M, 0.838 s/sample at 7B.

## THE THREE CONSTANTS, EACH MEASURED RATHER THAN CHOSEN

**`MAX_NEW = 16`.** The pilot used 10 and excluded 3.5% of samples as
unparseable. 10 is exactly the worst case: `46,204,000` is 10 tokens on every
digit-splitting tokenizer in the roster (Qwen, gemma, SmolLM2; Llama and bloom
take 5), so a full numeral fills the budget and cannot be told from a truncated
one -- `36,00` is a cut `36,000` and reading it as 3600 understates by 10x. 16
leaves at least six tokens of trailing context, which is what makes completion
CHECKABLE rather than assumed.

**`N = 50`.** 1,500 samples per model over the 30-prompt battery: 1,000 en and
500 zh for the quintile shares, 50 draws behind each per-prompt median that the
G group-cells difference. RH, 2026-08-27.

**`frame = raw`, i.e. `template=False`.** RH, 2026-08-27, and it is also the
only frame the contrast can take: 19 of the roster's bases ship no chat template
at all, so a chat-framed aligned arm against a raw base arm would confound the
frame with the arm on exactly the comparison this experiment is.

## WHY THIS HOLDS THE LOAD ITSELF

`Checkpoint.generate` frees the model when it loaded it -- `own = loaded is
None` -- so calling it once per prompt without `loaded=` would load and unload
each checkpoint THIRTY TIMES. It is handed a loaded model, and the cache is
consulted BEFORE loading so a model that is already complete costs nothing.

Output is one CSV per model under `results/gen/`, not one appended file: an
append-on-resume duplicates every row of every model that already ran, and the
duplicate is invisible in a total that was never checked against a count.
"""

import argparse, csv, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
#: `has_weights` is NOT `isdir(models--X)`: a resolved ref with an empty
#: snapshot reports as cached and then downloads. Reused rather than
#: reimplemented, the way `subject_position/run.py` reuses it.
sys.path.insert(0, os.path.abspath(
    os.path.join(HERE, "..", "..", "passage_analysis", "novel_arc")))

N = 50
MAX_NEW = 16
SEED = 20260827
FRAME = "raw"
#: THE STASH IS THE RECORD; THIS CSV IS DERIVED AND REGENERABLE.
#: `Checkpoint.generations`' own docstring warns against the thing this file
#: would otherwise be -- "a run that wrote one had two stores to keep in step,
#: which is the shape of a divergence nobody notices until they disagree". So
#: it lives OUTSIDE the checkout beside the stash it comes from (17.9 MB over
#: 56 models), and anything it says can be rebuilt from
#: `ck.generations(prompt=..., frame="raw")` if the two ever disagree.
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
RESULTS = os.path.join(DATA, "salary_probe", "gen")
COLS = ["model", "arm", "base", "prompt_id", "language", "subdomain", "group_id",
        "prompt", "sample", "seed", "continuation", "numeral", "suffix",
        "has_separator", "n_digits", "n_new_tokens", "finish"]

#: the numeral, then SEPARATELY any magnitude suffix glued to it. The pilot's
#: `[\d,\.]*\d` stopped before the `K` and handed `55` to a parser that read it
#: as fifty-five dollars -- and base arms emit K/M forms 6.5x more often than
#: aligned (SmolLM2 1.30% against 0.20%), so the artifact manufactures base-arm
#: mass in Q1, which is the direction of the pilot's only headline. Captured
#: here rather than dropped, so the analysis can decide; see registration A4.
NUM = re.compile(r"\s*([\d,\.]*\d)\s*([KkMm])?")


def wrong_venv(mid):
    """The venv this checkpoint DECLARES, if it is not the one we are running.

    **THE ROSTER ALREADY DECIDES THIS AND IT IS NOT A BUG TO ROUTE AROUND.**
    `scripts/venvs.py` groups every node by the `transformers` specifier it
    declares, and the six allenai OLMo checkpoints here declare `>=4.57,<5`, so
    they belong to `.venv-tf457` and cannot run under `.venv`'s 5.4.0.

    Under 5.4.0 they fail with `Field 'tie_word_embeddings' expected int, got
    bool` -- transformers 5.4.0 annotates the field `int` while defaulting it to
    a bool, and huggingface_hub 1.28.0 validates by exact type. That error reads
    like an upstream typo worth patching, and an earlier version of this file
    patched it: it forced the field type to `bool` and all six configs then
    loaded. **That fix was wrong.** It made a checkpoint load in an environment
    its own declaration excludes, which buys a number that looks fine and cannot
    be trusted -- the load error was the environment split working, not failing.

    The split cost nothing here, which is worth recording: of the 23 models
    completed before this was understood, ZERO declared another venv. The six
    that failed were exactly the six declaring `tf457`.
    """
    sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
    from venvs import venv_for
    try:
        want = os.path.realpath(venv_for(mid))
    except KeyError:
        return None                      #: not a roster node; not our call
    here = os.path.realpath(sys.prefix)
    return None if want == here else want


def prompts():
    from malignment.prompts import Prompts
    ps = [p for p in Prompts.all()
          if str(getattr(p, "domain", "") or "") == "class"]
    ps.sort(key=lambda p: (p.language, p.prompt_id))
    return ps


def pairs():
    """[(base, aligned)] -- endpoint pairs with BOTH arms on disk.

    Both, never one: a pair with only its base local cannot enter a paired
    contrast, and counting it as available is how a run reports coverage it
    does not have.
    """
    from malignment import roster
    from ladder_sweep import has_weights
    m = roster.endpoints()
    m = m[0] if isinstance(m, tuple) else m
    return [(b, a) for b, a in m.items() if has_weights(b) and has_weights(a)]


def cached(ck, text):
    """How many of OUR draws this checkpoint already holds.

    Matched on the stored key, not guessed at: frame and the resolved decoder
    both sit in the key, so a 256-token f11_l2 passage on the same stem is a
    different cell and is not counted here.
    """
    n = 0
    for p in ck.generations(prompt=text, frame=FRAME):
        d = getattr(p, "decoder", None) or {}
        if d.get("max_new_tokens") == MAX_NEW:
            n += 1
    return n


def row(mid, arm, base, p, i, psg):
    m = NUM.match(psg.text or "")
    num = m.group(1) if m else ""
    suf = (m.group(2) or "") if m else ""
    return {"model": mid, "arm": arm, "base": base, "prompt_id": p.prompt_id,
            "language": p.language,
            "subdomain": getattr(p, "subdomain", "") or "",
            "group_id": p._row.get("group_id") or "",
            "prompt": p.text, "sample": i, "seed": SEED + i,
            "continuation": psg.text, "numeral": num, "suffix": suf,
            "has_separator": int(("," in num) or ("." in num)),
            "n_digits": sum(c.isdigit() for c in num),
            "n_new_tokens": getattr(psg, "n_new_tokens", None),
            "finish": getattr(psg, "finish", None)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--models", nargs="*")
    a = ap.parse_args(argv)

    ps = prompts()
    pr = pairs()
    todo = [(m, arm, b) for b, al in pr
            for m, arm in ((b, "base"), (al, "aligned"))]
    if a.models:
        todo = [t for t in todo if t[0] in a.models]
    en = sum(1 for p in ps if p.language == "en")
    print("%d pairs with both arms local | %d models | %d prompts (%d en, %d zh)"
          % (len(pr), len(todo), len(ps), en, len(ps) - en))
    print("%d samples x %d tokens, frame=%s, seed=%d"
          % (a.n, MAX_NEW, FRAME, SEED))
    print("total draws: %s" % "{:,}".format(len(todo) * len(ps) * a.n))
    if a.plan:
        for m, arm, b in todo:
            print("   %-8s %s" % (arm, m))
        return

    from malignment import Checkpoint
    os.makedirs(RESULTS, exist_ok=True)
    t0 = time.time()
    fails = []
    elsewhere = []
    for mi, (mid, arm, base) in enumerate(todo, 1):
        #: BEFORE ANY LOAD. A checkpoint that declares another interpreter is
        #: not this invocation's work, and attempting it produces either a
        #: crash or -- worse -- a number from an environment the roster
        #: excludes.
        other = wrong_venv(mid)
        if other:
            elsewhere.append((mid, other))
            print("  [%d/%d] %-46s NEEDS %s"
                  % (mi, len(todo), mid[:46], os.path.basename(other)), flush=True)
            continue
        safe = mid.replace("/", "__").replace("@", "__at__")
        out = os.path.join(RESULTS, safe + ".csv")
        ck = Checkpoint(mid)
        have = {p.prompt_id: cached(ck, p.text) for p in ps}
        need = [p for p in ps if have[p.prompt_id] < a.n]
        if not need and os.path.exists(out):
            print("  [%d/%d] %-46s COMPLETE, cached" % (mi, len(todo), mid[:46]),
                  flush=True)
            continue
        #: the load is skipped entirely when every draw is already stored --
        #: which is the whole point of consulting the cache before loading.
        #:
        #: AND A FAILURE HERE MUST NOT END THE SWEEP. The first run of this file
        #: had no guard and died at model 23 of 56 on
        #: `allenai/OLMo-2-0425-1B` -- `tie_word_embeddings` typed `int` against
        #: a `bool` in a strict hub dataclass, which is an environment fault and
        #: not a fact about the checkpoint. Six hours of completed work survived
        #: only because the stash had it; nothing about the design earned that.
        #: One unloadable checkpoint costs its own cell, never the run.
        try:
            ld = ck.load() if need else None
        except Exception as e:
            fails.append((mid, str(e).split("\n")[0][:160]))
            print("  [%d/%d] %-46s LOAD FAILED %s"
                  % (mi, len(todo), mid[:46], str(e).split("\n")[0][:70]),
                  flush=True)
            continue
        rows = []
        try:
            for p in ps:
                got = ck.generate(p.text, n=a.n, seed=SEED, loaded=ld,
                                  template=False,
                                  decoder={"max_new_tokens": MAX_NEW})
                rows += [row(mid, arm, base, p, i, g) for i, g in enumerate(got)]
        except Exception as e:
            #: a model that loads and then fails mid-battery leaves NO csv, so
            #: the next run retries it rather than reading a short one as done.
            fails.append((mid, str(e).split("\n")[0][:160]))
            print("  [%d/%d] %-46s GENERATE FAILED %s"
                  % (mi, len(todo), mid[:46], str(e).split("\n")[0][:70]),
                  flush=True)
            continue
        finally:
            if ld is not None:
                del ld
                from malignment import twp as T
                T.free()
        #: written whole, then moved: a partial CSV from an interrupted model
        #: is indistinguishable from a complete one on the next run.
        tmp = out + ".part"
        with open(tmp, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, out)
        print("  [%d/%d] %-46s %d rows  (%d prompts generated, %.1f min elapsed)"
              % (mi, len(todo), mid[:46], len(rows), len(need),
                 (time.time() - t0) / 60), flush=True)
    #: STATED, not left to whoever counts the CSVs. A sweep that ends without
    #: naming what it dropped reads as complete coverage, and the shards on
    #: disk cannot distinguish "never attempted" from "attempted and failed".
    print("-> %s  (%.1f min)" % (RESULTS, (time.time() - t0) / 60))
    print("%d of %d models produced a shard; %d FAILED, %d need another venv"
          % (len(todo) - len(fails) - len(elsewhere), len(todo), len(fails),
             len(elsewhere)))
    for mid, err in fails:
        print("   FAILED %-46s %s" % (mid[:46], err))
    #: named with the command that finishes them, because a deferral nobody can
    #: act on is indistinguishable from a drop.
    for v in sorted({v for _, v in elsewhere}):
        ms = [m for m, w in elsewhere if w == v]
        print("   %d models need %s -- finish them with:" % (len(ms), v))
        print("      %s/bin/python -u %s" % (v, os.path.abspath(__file__)))


if __name__ == "__main__":
    main()
