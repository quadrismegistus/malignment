"""Runs ON a pod: TEMPLATE_ARM's generation for the lineages vLLM 0.22.1 cannot host.

    python3 hf_batch.py <base> <endpoint>

rwkv, recurrentgemma (refused by vLLM 0.22.1), Olmo-Hybrid (tf>=5 + fla) and internlm2
(word salad in every cell under vLLM 0.22.1). The same prompts files as the vLLM pods
(prompts/<model>.jsonl), the same decoder (generate.DECODER: t=1.0, top_p=1.0, top_k=0,
256 new tokens, no penalties), the same render (`generate.render` + `encode`, one leading
special-token run), and the same stash keys as `vllm_generate` except `render`, which is
"hf_batch" so a passage from this engine can never be served for a vLLM one.

BATCHED, and the seeding says so. `Checkpoint.generate` draws one sample per call (the
institution fleet's hf_box.py), which at 606,800 passages is days. Here each condition is
ONE `generate` call with num_return_sequences=n after torch.manual_seed(seed). Sample i
is keyed seed + i like every other passage in the design, and the record carries
`batch_seed` -- the seed actually set -- so no reader takes seed + i for a per-sample seed.
"""
import json, os, sys, time

sys.path.insert(0, "/root/malignment")
HERE = os.path.dirname(os.path.abspath(__file__))


def run(model_id):
    import torch, transformers
    from malignment.checkpoint import Checkpoint
    from malignment import generate as G
    from malignment.vllm_generate import load_prompts
    from malignment.runners import _chat_template_override
    conds = load_prompts(os.path.join(HERE, "prompts", model_id.replace("/", "__") + ".jsonl"))
    ck = Checkpoint(model_id)
    stash = ck.gen_stash()
    dec = dict(G.DECODER)
    todo = []
    for c in conds:
        system = G.DEFAULT if c["system"] == "_DEFAULT_" else c["system"]
        prefill = bool(c.get("prefill"))
        templated = bool(system is not G.DEFAULT or prefill or c.get("chat"))
        frame = G.frame_label(system, None, prefill, True if c.get("chat") else None)
        sysk = "" if system is G.DEFAULT else system
        keys = []
        for i in range(c["n"]):
            k = dict(G.gen_key(model_id, c["prompt"], frame, sysk, dec, c["seed"] + i, i,
                               system_set=(system is not G.DEFAULT)),
                     user=None, prefill=prefill, user_msg=(c["user_msg"] if prefill else None),
                     render="hf_batch")
            if c.get("template_kwargs"):
                k["template_kwargs"] = c["template_kwargs"]
            keys.append(k)
        if not all(stash.get(k) for k in keys):
            todo.append((c, system, prefill, templated, frame, keys))
    if os.environ.get("HF_BATCH_LIMIT"):                  #: smoke tests only
        todo = todo[:int(os.environ["HF_BATCH_LIMIT"])]
    print("%s: %d of %d conditions to generate" % (model_id, len(todo), len(conds)), flush=True)
    if not todo:
        return 0
    #: bf16 for this engine class, declared in TEMPLATE_ARM.md: HF sampling at fp16 hit
    #: NaN probabilities in the smoke test (SmolLM2, a templated condition), and rwkv /
    #: recurrentgemma / Olmo-Hybrid ship bf16. vLLM pods stay fp16 as f11_l2. Recorded per row.
    from malignment import runners
    _cd = runners.compute_dtype
    runners.compute_dtype = lambda m, default=None: _cd(m, default=torch.bfloat16)
    ld = ck.load()
    if not getattr(ld.tok, "chat_template", None):
        o = _chat_template_override(model_id)
        if o:
            ld.tok.chat_template = o
    tv = transformers.__version__
    t0, nw = time.time(), 0
    for j, (c, system, prefill, templated, frame, keys) in enumerate(todo):
        text_in, sys_ok = G.render(ld, c["prompt"], system=system, prefill=prefill,
                                   user_msg=c["user_msg"], template=templated,
                                   template_kwargs=c.get("template_kwargs"))
        if templated and system is not G.DEFAULT and sys_ok is False:
            raise SystemExit("%s: template dropped the system message on %s -- refusing" % (model_id, c["_key"]))
        enc = G.encode(ld, text_in, templated)
        plen = int(enc["input_ids"].shape[1])
        torch.manual_seed(c["seed"])
        with torch.no_grad():
            g = ld.model.generate(**enc, **dec, num_return_sequences=c["n"],
                                  pad_token_id=ld.tok.eos_token_id)
        for i, k in enumerate(keys):
            new = g[i][plen:]
            eos = ld.tok.eos_token_id
            #: a finished row is right-padded with eos; cut at the first eos
            ids = new.tolist()
            if eos is not None and eos in ids:
                ids = ids[:ids.index(eos)]
                fin = "eos"
            else:
                fin = "length" if len(ids) >= dec["max_new_tokens"] else "eos"
            p = G._passage(text=ld.tok.decode(ids, skip_special_tokens=True), prompt=c["prompt"],
                           model=model_id, frame=frame, seed=c["seed"] + i, decoder=dict(dec),
                           n_new_tokens=len(ids), finish=fin, sys_supported=sys_ok,
                           system=(None if system is G.DEFAULT else system),
                           system_default=(system is G.DEFAULT), user=None, prefill=prefill,
                           user_msg=(c["user_msg"] if prefill else None), template=templated,
                           engine="transformers", engine_version=tv, render="hf_batch",
                           dtype=str(ld.model.dtype).replace("torch.", ""), revision=ck.revision)
            rec = p._asdict()
            rec["batch_seed"] = c["seed"]
            if c.get("template_kwargs"):
                rec["template_kwargs"] = c["template_kwargs"]
            stash[k] = rec
            nw += 1
        if j % 20 == 0:
            print("  %s %d/%d conditions, %d passages, %.1f min" % (model_id.split("/")[-1], j + 1, len(todo), nw, (time.time() - t0) / 60), flush=True)
    del ld
    return nw


if __name__ == "__main__":
    for m in sys.argv[1:]:
        print("%s: wrote %d" % (m, run(m)), flush=True)
