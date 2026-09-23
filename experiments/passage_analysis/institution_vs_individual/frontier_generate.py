"""Frontier API passages on the regeneration's 36 prompts, into malignment's generation stash.

    python -u frontier_generate.py --smoke            2 prompts x 2 samples per model
    python -u frontier_generate.py --run [--models M ...]

The aligned arm's frame and decoder, as far as each API allows:

    frame    the prompt as the USER message, no system message (the vendor's own
             default) -- the same condition as `chat_sysdefault` on the open models
    decoder  temperature 1.0, 256 new tokens, 10 independent draws per prompt,
             top_p 1.0 pinned ONLY where largeliterarymodels has measured that the
             route honours it (DeepSeek). Everywhere else top_p runs at the
             vendor's undisclosed default: Haiku 4.5 rejects the parameter, and
             OpenAI's handling is unmeasured, so the library refuses to key it.
    seeds    APIs do not take ours; draws are indexed by `sample=0..9` and cached
             under that index.

THINKING IS DISABLED where the model thinks by default (DeepSeek v4): thinking
tokens count against max_tokens and would leave 256-token answers empty, and
DeepSeek ignores temperature while thinking.

`deepseek-chat` is NOT the model F21 called by that name: the API now resolves
it to `deepseek-v4-flash` (largeliterarymodels/providers.py, verified against
/models 2026-07-30). It is called and stored here as deepseek-v4-flash.

Each passage is written through `malignment.generate.gen_key` into the model's
generation stash with frame `chat_sysdefault`, `engine="api"`, `render="api"`
(in the key, so these can never collide with a local render), and the decoder
that ACTUALLY governed, so `run_regen.py` can read them unchanged.
"""
import argparse, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

#: stash id -> (largeliterarymodels model, extra LLM kwargs, pinned sampling)
MODELS = {
    "anthropic/claude-sonnet-4-6": ("claude-sonnet-4-6", {}, None),
    "anthropic/claude-haiku-4-5": ("claude-haiku-4-5", {}, None),
    "openai/gpt-4o-mini": ("gpt-4o-mini", {}, None),
    "deepseek/deepseek-v4-flash": ("deepseek/deepseek-v4-flash", {"thinking": "disabled"}, {"top_p": 1.0}),
}
#: what the vendor reports serving, where it differs from what was requested
#: (logged by largeliterarymodels on first call, 2026-09-24). deepseek-flash is
#: ALSO the coder's model: for this arm generator and coder are one model.
RESOLVED = {"deepseek/deepseek-v4-flash": "deepseek-flash"}
N = 10
MAX_NEW = 256
PROMPTS = os.path.join(HERE, "prompts", "chat.jsonl")


def run(stash_id, prompts, n, workers):
    from largeliterarymodels.llm import LLM
    from malignment import generate as G
    from malignment.checkpoint import Checkpoint
    model, kw, sampling = MODELS[stash_id]
    llm = LLM(model, temperature=1.0, max_tokens=MAX_NEW, usage_log="ivi_frontier",
              sampling=sampling)
    dec = {"do_sample": True, "temperature": 1.0, "max_new_tokens": MAX_NEW,
           "top_p": (sampling or {}).get("top_p"), "top_k": None}
    stash = Checkpoint(stash_id).gen_stash(producer="frontier_api")
    written = failed = 0
    for i in range(n):
        errors = {}
        texts = llm.map(prompts, system_prompt=None, sample=i, num_workers=workers,
                        errors=errors, **kw)
        for prompt, text in zip(prompts, texts):
            if text is None:
                failed += 1
                continue
            k = dict(G.gen_key(stash_id, prompt, "chat_sysdefault", "", dec, None, i,
                               system_set=False), render="api")
            p = G._passage(text=text, prompt=prompt, model=stash_id, frame="chat_sysdefault",
                           seed=None, decoder=dict(dec), n_new_tokens=None, finish=None,
                           sys_supported=True, system=None, system_default=True, user=None,
                           prefill=False, user_msg=None, template=True, engine="api",
                           engine_version=RESOLVED.get(model, model), render="api", sample_idx=i,
                           api_kwargs=kw, top_p_pinned=bool(sampling))
            stash[k] = p._asdict()
            written += 1
    return written, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    prompts = [json.loads(l)["prompt"] for l in open(PROMPTS)]
    if a.smoke:
        prompts, n = prompts[:2], 2
    elif a.run:
        n = N
    else:
        raise SystemExit("--smoke or --run")
    for m in a.models:
        t0 = time.time()
        try:
            w, f = run(m, prompts, n, a.workers)
            print("%s: wrote %d, failed %d, %.0fs" % (m, w, f, time.time() - t0), flush=True)
        except Exception as e:
            print("%s: FAILED %s: %s" % (m, type(e).__name__, str(e)[:300]), flush=True)


if __name__ == "__main__":
    main()
