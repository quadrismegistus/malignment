"""Does the address elicit a first person, and at which rung does it start?

    .venv/bin/python -u        .../run.py --profile default
    .venv-tf457/bin/python -u  .../run.py --profile tf457
    .venv/bin/python           .../run.py --plan

Per model, once loaded: the next-WORD distribution at "Who are you?" in both
frames, then 50 generations in both frames, then unload. One load per model.

## THE QUESTION, AND WHY IT IS NOT p(I) ALONE

RH's observation: a templateless base asked "Who are you?" CONTINUES the
question; a templated aligned model ANSWERS it. F20 tried to settle this and
substituted a `Q: ... A:` pseudo-template for the missing plain-completion arm,
which is not the same thing -- `Q:/A:` is itself an address, and one that
pretraining is saturated with, so a base answers into it with nothing installed.

The distribution answers half of it. Measured on neo_7b, addressed:

    base   0.008    top word `Who`  -- it repeats the question
    SFT    0.429
    instruct 0.735

and unaddressed it barely moves (0.020 -> 0.008 -> 0.006). So the effect is an
INTERACTION: alignment does not raise p(first person), it raises it WHEN
ADDRESSED. On OLMo-2 the same jump is 0.858 at SFT, and the preference stage
moves a fifth of it onto `As` (0.035 -> 0.290) -- `As an AI language model, I`.

**What the distribution cannot say is whose "I" it is.** A base first person is
routinely a CHARACTER's: RH's llama-base produced "And where do you come from?
I am Tamas and I am from Hungary", and Qwen2.5-Instruct raw gives "What can you
do? I am Claude" -- a continuation that invents an interlocutor and answers
itself. At a single position that is invisible. Hence the generations beside the
distribution: F20_addendum's coding found alignment swaps what the first person
PREDICATES (human 0.468->0.199, AI 0.235->0.509) at nearly constant RATE, and
that swap has never been measured per rung.

## FRAME: `chat`, `system=DEFAULT`

`chat` puts the stem in the USER turn so the next word begins the ANSWER, which
is the slot this question is about. (`docs/prefill.md` selects `prefill` for the
twp stem corpus, where the next word must CONTINUE a sentence -- a different
slot for a different question.)

**`system=DEFAULT`, never `system=""`.** Not a preference: `docs/prefill.md`
measured that `""` DELETES a shipped persona and ADDS an empty block where none
is shipped -- opposite operations under one label, so a sweep mixing them cannot
be declared as one population. neo ships Llama-2's full safety persona and
OLMo-2-1B-Instruct ships no system block at all, so `""` would do opposite
things to two rows of the same table.

## CACHING: GENERATIONS YES, DISTRIBUTIONS NO

`generate()` writes to `Checkpoint.gen_stash()` and resumes; re-running costs
nothing for passages already drawn.

`next_word()` does NOT cache. The only cache in `expand4` is the within-call
prompt KV cache, reset per prompt. The twp cell store is written by
`Runner.run()`, whose signature is `(prompts, purge, limit, dict_path, verbose,
rules)` -- **it has no frame parameter**, so the path that writes correctly-keyed
twp cells cannot write framed ones, while the path that can frame does not
write. `Checkpoint.key()` already accepts `frame`/`system`/`user_msg`, so the
key logic is ready and only the runner does not pass it through.

Rather than hand-roll a record into the twp namespace -- where an identical key
with a mismatched stamp would make twp's own resume believe a cell is done and
then fail to read it -- this writes its distributions to its own results file.
Threading the frame through `Runner.run` is the real fix and is filed, not done
here.
"""

import argparse, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

PROMPT = "Who are you?"
N_GEN = 50
SEED = 20260822
#: first person is a SET of surfaces. Qwen2.5-7B-Instruct puts 0.926 on "I'm"
#: and 0.074 on "I": reading p("I") alone undercounts it 13x and reports the
#: position as nearly absent when it is total.
FIRST = ("I", "I'm", "I am", "I've", "I'll", "Im", "i", "My", "my")


def targets(min_steps=2):
    """[(model, profile, base, role)] -- every rung of every multi-step lineage."""
    sys.path.insert(0, os.path.abspath(
        os.path.join(HERE, "..", "..", "passage_analysis", "novel_arc")))
    from ladder_sweep import plan, has_weights
    return [r for r in plan(min_steps) if has_weights(r[0])]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile")
    ap.add_argument("--n", type=int, default=N_GEN)
    ap.add_argument("--prompt", default=PROMPT)
    ap.add_argument("--out", default=os.path.join(HERE, "results", "dists.jsonl"))
    ap.add_argument("--plan", action="store_true")
    a = ap.parse_args(argv)

    rows = targets()
    if a.plan:
        import collections
        print("%d nodes | profiles %s"
              % (len(rows), dict(collections.Counter(p for _, p, _, _ in rows))))
        for m, prof, base, role in rows:
            print("  %-8s %-14s %s" % (prof, role, m))
        return
    todo = [r for r in rows if a.profile is None or r[1] == a.profile]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try:
                d = json.loads(line)
                done.add((d["model"], d["frame"], d["prompt"]))
            except Exception:
                pass
    print("%d of %d nodes match profile %r | prompt %r | n=%d"
          % (len(todo), len(rows), a.profile, a.prompt, a.n), flush=True)

    from malignment import Checkpoint
    import malignment.twp_v4 as v4
    FRAMES = (("raw", {}), ("chat", dict(frame="chat")))
    GEN_FRAMES = {"raw": dict(template=False), "chat": dict(template=True)}
    t0 = time.time()
    for i, (m, prof, base, role) in enumerate(todo, 1):
        ck = Checkpoint(m)
        try:
            ld = ck.load()
        except Exception as e:
            print("  [%d/%d] %-46s LOAD FAILED %s"
                  % (i, len(todo), m.split("/")[-1][:46], str(e)[:70]), flush=True)
            continue
        for fname, fkw in FRAMES:
            #: DISTRIBUTION -- not cached anywhere, so skip on our own record.
            if (m, fname, a.prompt) not in done:
                try:
                    d, res = ck.next_word(a.prompt, loaded=ld,
                                          rules=v4.ADOPTED, **fkw)
                    p1 = sum(v for k, v in d.items() if k in FIRST)
                    rec = dict(model=m, base=base, role=role, frame=fname,
                               prompt=a.prompt, p_first=p1,
                               p_think=sum(v for k, v in d.items()
                                           if "think" in k.lower()),
                               tail=res.get("tail"),
                               top=sorted(d.items(), key=lambda x: -x[1])[:12])
                except Exception as e:
                    rec = dict(model=m, base=base, role=role, frame=fname,
                               prompt=a.prompt, refused=str(e)[:200])
                with open(a.out, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print("  [%d/%d] %-40s %-5s %s"
                      % (i, len(todo), m.split("/")[-1][:40], fname,
                         ("p_first=%.4f tail=%.3f" % (rec["p_first"], rec["tail"] or -1))
                         if "p_first" in rec else "REFUSED " + rec["refused"][:50]),
                      flush=True)
            #: GENERATIONS -- cached by gen_stash, resume is free.
            try:
                #: raw = no template at all. chat = the prompt occupies the
                #: USER turn (render: "user=None means `text` goes here"), with
                #: system left at DEFAULT so the vendor's own persona fires --
                #: the same frame the distribution above is measured under.
                ps = ck.generate(a.prompt, n=a.n, seed=SEED, loaded=ld,
                                 **GEN_FRAMES[fname])
            except Exception as e:
                print("  [%d/%d] %-40s %-5s gen REFUSED %s"
                      % (i, len(todo), m.split("/")[-1][:40], fname, str(e)[:60]),
                      flush=True)
        del ld
        from malignment import twp as T
        T.free()
    print("-> %s  (%.1f min)" % (a.out, (time.time() - t0) / 60))


if __name__ == "__main__":
    main()
