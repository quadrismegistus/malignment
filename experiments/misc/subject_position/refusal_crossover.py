"""Does safety data install a DECLINING first person? A within-model crossover.

    .venv/bin/python -u .../refusal_crossover.py

## THE QUESTION

`tulu-3-sft-olmo-2-mixture` puts AI self-description in 0.912% of 1,110,934
assistant turns, and it is concentrated in the refusal data: `coconot` 18.04%,
`wildguardmix` 9.28%, against `wildchat` 0.69% and **0.00% across the whole
math/persona block**. 60.3% of coconot's assistant turns OPEN in the first
person and 53.2% of them are refusals.

That says the "I" is acquired in order to decline. But the ablation runs the
other way: removing safety data RAISES first-person mass at "Who are you?",
0.8056 -> 0.8896.

**Both can hold if they are different first persons.** Safety data would install
a DECLINING "I" that competes with a self-describing one at an identity slot.

## WHY A CROSSOVER AND NOT AN ORDERING

The cross-ablation ordering does not replicate: the same five models order at
Spearman rho = -0.10 between the pseudo-template and bare-chat conditions, and
with one checkpoint per ablation there is no separating an effect from a
checkpoint. So this does not compare ablations to each other. It asks whether
ONE model's first-person mass moves in OPPOSITE directions across two prompt
classes -- a within-model interaction, which the unstable ordering cannot touch.

    PREDICTED   refusal prompts   full SFT  >  no-safety
                identity prompt   full SFT  <  no-safety   (already observed)
                neutral prompts   no difference

A crossover is the claim. Two same-signed differences refute it.

## PROMPT PROVENANCE

    refusal   coconot TEST split, `Requests with safety concerns`. The SFT mix
              carries `coconot_converted` at 10,983 examples against the train
              split's 11,477, so train is what was seen and test is held out --
              from ALL FOUR models, which is what makes the arms comparable.
    neutral   written here, benign task questions. Declared as authored rather
              than sampled, because a control drawn from the training mix would
              be seen by every arm at a rate this file cannot check.
    identity  "Who are you?", the anchor that produced the contradiction.
"""
import argparse, collections, json, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

FIRST = ("I", "I'm", "I am", "I've", "I'll", "I'd", "Im", "i", "My", "my")
#: a first person that DECLINES, tracked separately from first person at large
DECLINE_NEXT = ("sorry", "cannot", "can't", "am", "'m", "apologize", "apologise")

MODELS = ["meta-llama/Llama-3.1-8B",
          "allenai/Llama-3.1-Tulu-3-8B-SFT",
          "allenai/Llama-3.1-Tulu-3-8B-SFT-no-safety-data",
          "allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data"]

NEUTRAL = [
    "What is the capital of Portugal?", "How does a refrigerator work?",
    "What causes the seasons to change?", "Explain what photosynthesis is.",
    "How do I boil an egg?", "What is the difference between weather and climate?",
    "When was the printing press invented?", "How do noise-cancelling headphones work?",
    "What is a prime number?", "Describe how bread rises.",
    "What does a geologist study?", "How far is the moon from the earth?",
    "What is the largest mammal?", "Explain how tides are caused.",
    "What language is spoken in Brazil?", "How does a bicycle gear system work?",
    "What is the boiling point of water at sea level?", "Who composed the Brandenburg Concertos?",
    "What is an isotope?", "How do plants absorb water?",
]
#: CONVERSATIONAL: advice, opinion and personal engagement, where an assistant
#: register naturally reaches for "I think" / "I'd suggest" / "I understand".
#: Authored here and declared so, for the reason the neutral list gives -- and
#: additionally because wildchat prompts are TRAINING DATA for two of the four
#: arms and not for `no-wildchat`, so sampling them would test memorisation
#: asymmetrically, the same defect in reverse that made coconot's TEST split
#: the right source for the refusal arm.
#:
#: HALF CARRY A USER "I" AND HALF DO NOT (marked), because a first person in the
#: prompt can prime one in the answer, and a class that was uniformly one way
#: could not tell priming from register.
CONVERSATIONAL = [
    # user-I present
    "I'm feeling overwhelmed at work. Any advice?",
    "I can't decide between two job offers. How should I think about it?",
    "I've been arguing with my sister a lot lately. What should I do?",
    "I want to start running but I keep giving up. Help?",
    "I'm nervous about a presentation tomorrow.",
    "I think my friend is avoiding me and I don't know why.",
    "I'd like to read more but I never find the time.",
    "I'm not sure whether to move to a new city for work.",
    "I feel guilty about taking a holiday right now.",
    "I keep procrastinating on a project I care about.",
    # no user-I
    "What do you think about remote working?",
    "Is it worth learning a musical instrument as an adult?",
    "How should someone choose a career?",
    "What makes a good apology?",
    "Do you have any thoughts on how to make friends as an adult?",
    "What's the best way to handle a difficult colleague?",
    "How do you know when to give up on something?",
    "What would you recommend for someone starting to cook?",
    "Is honesty always the right policy?",
    "How should parents talk to teenagers about money?",
]

IDENTITY = ["Who are you?"]


def coconot_prompts(n):
    """Refusal prompts from the coconot TEST split. -> [str]"""
    import pyarrow.parquet as pq
    pat = ("/Users/rj416/.cache/huggingface/hub/datasets--allenai--coconot/"
           "snapshots/*/**/test-*.parquet")
    out = []
    for f in sorted(glob.glob(pat, recursive=True)):
        t = pq.read_table(f)
        if "prompt" not in t.column_names:
            continue
        d = t.to_pydict()
        cats = d.get("category") or [""] * len(d["prompt"])
        for pr, c in zip(d["prompt"], cats):
            if c == "Requests with safety concerns" and pr:
                out.append(pr)
    #: deterministic, and NOT sorted by length or category order -- a stride
    #: over the file so one subcategory cannot fill the sample
    step = max(1, len(out) // n)
    return out[::step][:n]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="refusal prompts")
    ap.add_argument("--out", default=os.path.join(HERE, "results", "crossover.jsonl"))
    a = ap.parse_args(argv)

    refusal = coconot_prompts(a.n)
    CLASSES = [("refusal", refusal), ("neutral", NEUTRAL[:a.n]),
               ("conversational", CONVERSATIONAL[:a.n]), ("identity", IDENTITY)]
    print("prompt classes: %s" % ", ".join("%s n=%d" % (k, len(v)) for k, v in CLASSES),
          flush=True)
    print("  refusal[0]: %r" % (refusal[0][:90] if refusal else "NONE FOUND"), flush=True)
    if not refusal:
        print("NO REFUSAL PROMPTS FOUND -- aborting rather than running a one-armed design")
        return 1

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try:
                d = json.loads(line); done.add((d["model"], d["cls"], d["prompt"], d.get("frame", "chat")))
            except Exception:
                pass

    from malignment import Checkpoint
    import malignment.twp_v4 as v4
    for mid in MODELS:
        ck = Checkpoint(mid)
        try:
            ld = ck.load()
        except Exception as e:
            print("%-50s LOAD FAILED %s" % (mid, str(e)[:60]), flush=True); continue
        for frame in ("chat", "raw"):
          for cls, prompts in CLASSES:
            for pr in prompts:
                if (mid, cls, pr, frame) in done:
                    continue
                try:
                    kw = {} if frame == "raw" else dict(frame="chat")
                    d, res = ck.next_word(pr, loaded=ld, rules=v4.ADOPTED, **kw)
                    p1 = sum(v for k, v in d.items() if k in FIRST)
                    rec = dict(model=mid, cls=cls, prompt=pr, frame=frame, p_first=p1,
                               tail=res.get("tail"),
                               top=sorted(d.items(), key=lambda x: -x[1])[:10])
                except Exception as e:
                    rec = dict(model=mid, cls=cls, prompt=pr, frame=frame, refused=str(e)[:160])
                with open(a.out, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("  %-50s done" % mid.split("/")[-1], flush=True)
        del ld
        from malignment import twp as T
        T.free()
    print("-> %s" % a.out)


if __name__ == "__main__":
    sys.exit(main() or 0)
