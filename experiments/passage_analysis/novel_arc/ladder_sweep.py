"""Generate one stem across every rung of every multi-step lineage.

    .venv/bin/python        .../ladder_sweep.py --profile default --n 50
    .venv-tf457/bin/python  .../ladder_sweep.py --profile tf457   --n 50
    .venv/bin/python        .../ladder_sweep.py --plan            # list, run nothing

## WHY A SWEEP AND NOT A DEEPER SINGLE LADDER

The 1B pilot needed n=150 and bootstrap CIs because ONE lineage was the whole
experiment, and even then abstraction did not resolve: passage SD is 0.36-0.38
against a total move of 0.074. The smol3 ladder at n=40 resolved nothing at all,
which is what its size predicts -- its base-to-aligned move is 0.0364 against
the 1B OLMo's 0.2595.

`roster.paths()` reports **15 lineages with 2+ released steps, every one cached
locally**. With that many, **the LINEAGE is the unit**: each contributes one
sign for "did the SFT step carry more of the move than the preference step",
and a sign test over 15 needs no single lineage to be significant -- only
unbiased. That is the unit every other arm claim in this repo uses, and it is
what makes n=50 on one stem sufficient here when it was not sufficient alone.

## THE STEM, AND WHY THIS ONE

`He was beautiful and disgusting and she wanted to` -- a real f11_l2 stem with
134 passages already in the corpus, so the sweep is comparable to the store.
Chosen mainly because the stash ALREADY holds 40-150 passages on it for
`OLMo-2-0425-1B` (4 rungs), the Olmo-3 branch, and smol3 (4 rungs); those
resume for free, and any other stem would discard them.

**One stem bounds this hard.** Stem is the largest variance component in the
corpus (ICC 0.417-0.433 for API models), so per-lineage magnitudes estimate the
effect FOR THIS SCENE. The sign test across lineages is what survives that; a
per-lineage number does not.

## THE PROFILE SPLIT IS NOT OPTIONAL

Nodes carry `env.profile` in `roster/models/models.yaml` and they DISAGREE: the
OLMo family needs `tf457` because transformers 5.4.0 raises
`TypeError: Field 'tie_word_embeddings' expected int, got bool` on its config,
while `Olmo-Hybrid` stays on `default` because 4.57.1 does not recognise model
type `olmo_hybrid` at all. One family, two environments. A single process cannot
serve both, so this filters on `--profile` and is run once per venv; `--plan`
prints the split without loading anything.

## TULU IS AN ABLATION, NOT A LADDER, AND IS INCLUDED FOR THAT

Four `Llama-3.1-Tulu-3-8B-SFT-no-*-data` arms descend from the SAME
`Llama-3.1-8B` by `sft`, each missing one data component (math, persona, safety,
wildchat). That turns "SFT does the cutting" into "WHICH SFT data does the
cutting" -- and Findings U already reports safety data is not what produces
displacement, so these test whether the same holds for abstraction and
interiority. They are siblings, not rungs: never chained, and reported against
the full-data SFT arm rather than against each other.
"""

import argparse, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

STEM = "He was beautiful and disgusting and she wanted to"
TULU_BASE = "meta-llama/Llama-3.1-8B"
#: `roster.paths()` routes Llama-3.1-8B to a DIFFERENT endpoint, so the Tulu
#: chain is not a path and its rungs never appear. Named explicitly, because
#: four `-no-*-data` ablations with no full-data SFT arm to sit against are not
#: an ablation -- they are four unanchored models.
TULU_CHAIN = [("meta-llama/Llama-3.1-8B", "base"),
              ("allenai/Llama-3.1-Tulu-3-8B-SFT", "sft"),
              ("allenai/Llama-3.1-Tulu-3-8B-DPO", "dpo"),
              ("allenai/Llama-3.1-Tulu-3.1-8B", "rlvr")]
#: the roster's smol3 SFT node is the BARE repo, which resolves to `main` and is
#: not downloaded (0 safetensors); the cached rungs are `@it-*` revisions. A
#: node that resolves to absent weights is a rung the sweep would drop silently.
REVISION_FIX = {"HuggingFaceTB/SmolLM3-3B-checkpoints":
                "HuggingFaceTB/SmolLM3-3B-checkpoints@it-SFT"}
TULU_ABLATIONS = ["allenai/Llama-3.1-Tulu-3-8B-SFT-no-math-data",
                  "allenai/Llama-3.1-Tulu-3-8B-SFT-no-persona-data",
                  "allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data",
                  "allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data"]


CACHE = os.path.expanduser("~/.cache/huggingface/hub")


def has_weights(m):
    """Are this node's weights actually on disk?

    **NOT `os.path.isdir(models--X)`.** That tests only that a directory
    exists, and many nodes here have a resolved ref with an EMPTY snapshot --
    the repo was touched, the weights never pulled. Checking the directory
    reported 61 of 61 nodes cached when 21 of them would have downloaded
    458 GB against 219 GB free, which is a disk-full failure partway through an
    overnight run rather than a refusal at the start.
    """
    repo, _, rev = m.partition("@")
    d = os.path.join(CACHE, "models--" + repo.replace("/", "--"))
    r = os.path.join(d, "refs", rev or "main")
    if not os.path.exists(r):
        return False
    snap = os.path.join(d, "snapshots", open(r).read().strip())
    return os.path.isdir(snap) and any(f.endswith(".safetensors")
                                       for f in os.listdir(snap))


def plan(min_steps=2):
    """[(model, profile, role)] -- every node of every multi-step lineage."""
    from malignment import roster
    seen, out = set(), []
    for p in sorted(roster.paths(), key=lambda x: -x["n_steps"]):
        if p["n_steps"] < min_steps:
            continue
        for i, m in enumerate(p["nodes"]):
            #: remap BEFORE the dedup check. Remapping afterwards let the bare
            #: repo and its resolved revision both survive and then collapse to
            #: one id, producing a duplicate rung in the plan.
            m = REVISION_FIX.get(m, m)
            if m in seen:
                continue
            seen.add(m)
            role = "base" if i == 0 else (p["ops"][i - 1] or "?")
            out.append((m, p["base"], role))
    for m, role in TULU_CHAIN:
        m = REVISION_FIX.get(m, m)
        if m not in seen:
            seen.add(m)
            out.append((m, TULU_BASE, role))
    for m in TULU_ABLATIONS:
        if m not in seen:
            seen.add(m)
            out.append((m, TULU_BASE, "sft_ablation"))
    rows = []
    for m, base, role in out:
        try:
            env = roster.environment(m) or {}
            prof = (env.get("profile") if isinstance(env, dict) else None) or "default"
        except Exception:
            prof = "default"
        rows.append((m, prof, base, role))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=None,
                    help="only run nodes whose roster env profile matches")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--stem", default=STEM)
    ap.add_argument("--seed", type=int, default=20260822)
    ap.add_argument("--min-steps", type=int, default=2)
    ap.add_argument("--plan", action="store_true", help="print and exit")
    ap.add_argument("--all-lineages", dest="complete_only", action="store_false",
                    default=True, help="do not drop lineages with a missing rung")
    a = ap.parse_args(argv)

    rows = plan(a.min_steps)
    if a.plan:
        import collections
        byp = collections.Counter(p for _, p, _, _ in rows)
        print("%d nodes across %d lineages | profiles: %s"
              % (len(rows), len({b for _, _, b, _ in rows}), dict(byp)))
        for m, prof, base, role in rows:
            print("  %-8s %-14s %-52s <- %s" % (prof, role, m, base.split("/")[-1]))
        return

    #: DROP INCOMPLETE LINEAGES WHOLE. A lineage missing a rung cannot
    #: contribute a sign -- the whole point of the sweep -- so generating its
    #: available rungs spends hours on data the design cannot use. Skipped
    #: lineages are NAMED, because a silently shorter population is the defect
    #: this sweep exists to avoid in the first place.
    if a.complete_only:
        import collections
        bylin = collections.defaultdict(list)
        for r in rows:
            bylin[r[2]].append(r)
        drop = {b for b, ms in bylin.items() if not all(has_weights(m) for m, _, _, _ in ms)}
        if drop:
            print("skipping %d INCOMPLETE lineages (a missing rung = no sign):"
                  % len(drop), flush=True)
            for b in sorted(drop):
                miss = [m.split("/")[-1] for m, _, _, _ in bylin[b]
                        if not has_weights(m)]
                print("    %-32s missing %s" % (b.split("/")[-1][:32],
                                                ", ".join(miss)), flush=True)
        rows = [r for r in rows if r[2] not in drop]

    todo = [r for r in rows if a.profile is None or r[1] == a.profile]
    #: a profile with no venv on this machine cannot be attempted, and a node
    #: skipped for that reason is NOT a failure of the model -- it is a hole in
    #: the environment. `torch26` has 3 nodes here and no venv, which costs
    #: pythia-6.9b both rungs and RedPajama its base.
    have = {"default", "tf457"}
    missing = [r for r in rows if r[1] not in have]
    if missing:
        print("%d nodes need a profile with NO venv here: %s"
              % (len(missing), sorted({r[1] for r in missing})), flush=True)
        for m, prof, base, role in missing:
            print("    %-8s %-52s <- %s" % (prof, m, base.split("/")[-1]),
                  flush=True)
    print("%d of %d nodes match profile %r | n=%d | stem %r"
          % (len(todo), len(rows), a.profile, a.n, a.stem[:46]), flush=True)
    from malignment import Checkpoint
    t0 = time.time()
    ok = fail = 0
    for i, (m, prof, base, role) in enumerate(todo, 1):
        t = time.time()
        try:
            ck = Checkpoint(m)
            ld = ck.load()
            ps = ck.generate(a.stem, n=a.n, seed=a.seed, loaded=ld, template=False)
            ok += 1
            print("  [%d/%d] %-52s %-14s %3d  %6.1fs"
                  % (i, len(todo), m.split("/")[-1][:52], role, len(ps),
                     time.time() - t), flush=True)
            del ld
        except Exception as e:
            #: a node that will not load is a MISSING RUNG, and a lineage with a
            #: hole in it cannot contribute a sign. Named here so the sign test
            #: can drop that lineage deliberately rather than silently.
            fail += 1
            print("  [%d/%d] %-52s %-14s FAILED: %s"
                  % (i, len(todo), m.split("/")[-1][:52], role,
                     str(e)[:100]), flush=True)
    print("-> %d ok, %d failed, %.1f min" % (ok, fail, (time.time() - t0) / 60))


if __name__ == "__main__":
    main()
