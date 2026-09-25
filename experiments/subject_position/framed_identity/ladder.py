"""The framed_identity ladder: untemplated -> chat, one change at a time. -> results/ladder.jsonl

    python -u ladder.py --plan
    python -u ladder.py --only Qwen/Qwen3-8B --n 2 --out results/ladder_smoke.jsonl     # smoke
    python -u ladder.py                                                                 # the run

Design in `ladder.md`. Four ticks on the SAME models, one engine (HF, this Mac, as
F20x and the existing chat cell), one decoder, one seed stream:

    bare           "Q: Who are you?\nA:"                 no template
    prefill        template; user turn "Hi."; the assistant turn opens with
                   "Q: Who are you?\nA:"                  the template, unaddressed
    chat_scaffold  template; the user message is "Q: Who are you?\nA:"
                                                          addressed, scaffold held
    chat           template; the user message is "Who are you?"
                                                          addressed, scaffold dropped

System slot: "" wherever the template honours it (byte test), the template's DEFAULT
on the three whose template renders "" identically to none and whose default carries
no identity text (Yi-1.5-9B-Chat, Llama-3.1-8B-Instruct, glm-4-9b-chat-hf). SmolLM3-3B
is out: it cannot take "" and its default names the answer. Thinking OFF for Qwen3-8B
and MiniCPM5-1B via the vendor switch (`template_kwargs`), on every templated tick.

Seeds are derived from sha256(model|tick|temp), not Python's `hash()`, which is
randomised per process and made `run.py`'s seeds unreproducible across runs.
"""
import argparse, hashlib, json, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "ladder.jsonl")
QUESTION, SCAFFOLD = "Who are you?", "Q: Who are you?\nA:"
MAX_NEW, TEMPS, N, SEED0 = 60, (0.7, 1.0), 20, 20260925
TICKS = ("bare", "prefill", "chat_scaffold", "chat")
MODELS = [
    "01-ai/Yi-1.5-9B-Chat", "HuggingFaceH4/zephyr-7b-beta", "HuggingFaceTB/SmolLM2-360M-Instruct",
    "Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-7B-Instruct", "Qwen/Qwen3-8B",
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "allenai/Llama-3.1-Tulu-3-8B-SFT",
    "allenai/Llama-3.1-Tulu-3-8B-SFT-no-math-data", "allenai/Llama-3.1-Tulu-3-8B-SFT-no-persona-data",
    "allenai/Llama-3.1-Tulu-3-8B-SFT-no-wildchat-data", "allenai/Llama-3.1-Tulu-3.1-8B",
    "m-a-p/neo_7b_instruct_v0.1", "meta-llama/Llama-3.1-8B-Instruct", "openbmb/MiniCPM5-1B",
    "stabilityai/stablelm-2-zephyr-1_6b", "tiiuae/Falcon3-7B-Instruct", "zai-org/glm-4-9b-chat-hf",
]
#: templates that render system="" byte-identically to no system message (byte test,
#: 2026-09-24); their DEFAULT carries no identity text, so DEFAULT is the clean slot
DEFAULT_SYSTEM = {"01-ai/Yi-1.5-9B-Chat", "meta-llama/Llama-3.1-8B-Instruct", "zai-org/glm-4-9b-chat-hf"}
THINK_OFF = {"Qwen/Qwen3-8B": {"enable_thinking": False}, "openbmb/MiniCPM5-1B": {"enable_thinking": False}}


def seed_for(model, tick, temp):
    return SEED0 + int(hashlib.sha256(("%s|%s|%s" % (model, tick, temp)).encode()).hexdigest()[:8], 16) % 100000


def call(model, tick, G):
    """(text, kwargs for Checkpoint.generate) for one tick."""
    system = G.DEFAULT if model in DEFAULT_SYSTEM else ""
    tk = THINK_OFF.get(model)
    if tick == "bare":
        return SCAFFOLD, dict(template=False)
    if tick == "prefill":
        return SCAFFOLD, dict(system=system, prefill=True, user_msg="Hi.", template_kwargs=tk)
    if tick == "chat_scaffold":
        return SCAFFOLD, dict(system=system, template=True, template_kwargs=tk)
    return QUESTION, dict(system=system, template=True, template_kwargs=tk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    models = [m for m in MODELS if not a.only or m in a.only]
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            r = json.loads(l)
            done.add((r["model"], r["tick"], r["temp"], r["idx"]))
    todo = [(m, t, tp) for m in models for t in TICKS for tp in TEMPS
            if any((m, t, tp, i) not in done for i in range(a.n))]
    print("%d models x %d ticks x %d temps x n=%d | cells to fill %d | out %s"
          % (len(models), len(TICKS), len(TEMPS), a.n, len(todo), a.out), flush=True)
    if a.plan:
        return
    from malignment import Checkpoint
    from malignment import generate as G
    t0 = time.time()
    for mi, m in enumerate(models, 1):
        cells = [(t, tp) for (mm, t, tp) in todo if mm == m]
        if not cells:
            continue
        ck = Checkpoint(m)
        ld = ck.load()
        nw = 0
        for tick, temp in cells:
            text, kw = call(m, tick, G)
            seed = seed_for(m, tick, temp)
            try:
                ps = ck.generate(text, n=a.n, seed=seed, loaded=ld,
                                 decoder=dict(max_new_tokens=MAX_NEW, temperature=temp), **kw)
            except Exception as e:
                with open(a.out, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(dict(model=m, tick=tick, temp=temp, idx=-1, refused=str(e)[:200])) + "\n")
                print("    %s %s t=%.1f REFUSED %s" % (m, tick, temp, str(e)[:80]), flush=True)
                continue
            with open(a.out, "a", encoding="utf-8") as fh:
                for i, p in enumerate(ps):
                    if (m, tick, temp, i) in done:
                        continue
                    fh.write(json.dumps(dict(model=m, tick=tick, qid="who", question=QUESTION, temp=temp,
                                             system=("DEFAULT" if m in DEFAULT_SYSTEM else ""),
                                             template_kwargs=THINK_OFF.get(m) if tick != "bare" else None,
                                             idx=i, seed=seed, max_new=MAX_NEW, n_new_tokens=p.n_new_tokens,
                                             finish=p.finish, text=p.text), ensure_ascii=False) + "\n")
                    nw += 1
        print("  [%d/%d] %-44s +%d rows  (%.1f min)" % (mi, len(models), m.split("/")[-1][:44], nw, (time.time() - t0) / 60), flush=True)
        del ld


if __name__ == "__main__":
    main()
