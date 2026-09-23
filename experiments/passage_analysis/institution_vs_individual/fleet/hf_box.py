"""Runs ON a pod, for architectures vLLM 0.22.1 will not host (recurrentgemma).

    python3 hf_box.py <base> <endpoint>

Same prompts, same decoder (generate.DECODER: t=1.0, top_p=1.0, top_k=0, 256
tokens), same seeds (42 + i) and the same stash keys as `vllm_generate`, through
`Checkpoint.generate`: base raw, endpoint chat (template=True). Slow -- one
sample at a time -- and that is accepted for the few models that need it.
"""
import json, os, sys, time

sys.path.insert(0, "/root/malignment")
from malignment.checkpoint import Checkpoint  # noqa: E402

P = "/root/malignment/experiments/passage_analysis/institution_vs_individual/prompts"


def main(base, end):
    for m, fn, tpl in ((base, "raw.jsonl", None), (end, "chat.jsonl", True)):
        ck = Checkpoint(m)
        ld = ck.load()
        t0 = time.time()
        for line in open(os.path.join(P, fn)):
            prompt = json.loads(line)["prompt"]
            ck.generate(prompt, n=10, seed=42, template=tpl, loaded=ld)
        print("%s: 36 x 10 in %.0fs" % (m, time.time() - t0), flush=True)
        del ld
        from malignment import twp
        twp.free()


if __name__ == "__main__":
    main(*sys.argv[1:3])
