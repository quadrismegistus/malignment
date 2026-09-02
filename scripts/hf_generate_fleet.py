"""HF generate for models that don't work on vLLM.

    python -u scripts/hf_generate_fleet.py \
        --models-file models.txt \
        --prompts-file prompts.jsonl \
        --n 10 --seed 42

Uses Checkpoint.generate() — same stash, same keys as vllm_generate.py.
One model at a time, sequential. Slow (~50 tok/s) but works with any
transformers-supported architecture.
"""
import argparse, json, os, sys, time

def main():
    ap = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models-file", required=True)
    ap.add_argument("--models", nargs="*")
    ap.add_argument("--prompts-file", required=True)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--max-new-tokens", type=int, default=3000)
    a = ap.parse_args()

    models = list(a.models or [])
    if a.models_file:
        with open(a.models_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    models.append(line)

    with open(a.prompts_file) as f:
        conditions = [json.loads(line) for line in f if line.strip()]

    decoder = {
        "temperature": a.temperature,
        "top_p": a.top_p,
        "max_new_tokens": a.max_new_tokens,
    }

    from malignment.checkpoint import Checkpoint

    total_generated = 0
    total_failed = 0

    for i, model_id in enumerate(models, 1):
        print("[%d/%d] %s" % (i, len(models), model_id), flush=True)
        t0 = time.time()
        try:
            ckpt = Checkpoint(model_id)
            n_written = 0
            for cond in conditions:
                prompt = cond["prompt"]
                system = cond.get("system", None)
                prefill = cond.get("prefill", False)
                user_msg = cond.get("user_msg", "Hi.")
                passages = ckpt.generate(
                    prompt, n=a.n, system=system,
                    prefill=prefill, user_msg=user_msg,
                    seed=a.seed, decoder=decoder,
                )
                n_written += len(passages)
            elapsed = time.time() - t0
            print("    generated %d passages in %.1fs" % (n_written, elapsed), flush=True)
            total_generated += 1
            try:
                ckpt.unload()
            except AttributeError:
                del ckpt
            import gc, glob, shutil, torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            safe = model_id.replace("/", "--").replace("@", "--")
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            for d in glob.glob(os.path.join(cache_dir, "models--" + safe)):
                try:
                    shutil.rmtree(d)
                except Exception:
                    pass
        except Exception as e:
            import gc, glob, shutil, traceback, torch
            print("    FAILED: %s: %s" % (type(e).__name__, e), flush=True)
            traceback.print_exc()
            total_failed += 1
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            safe = model_id.replace("/", "--").replace("@", "--")
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            for d in glob.glob(os.path.join(cache_dir, "models--" + safe)):
                try:
                    shutil.rmtree(d)
                except Exception:
                    pass

    print("\ndone: %d generated, %d failed across %d models"
          % (total_generated, total_failed, len(models)))

if __name__ == "__main__":
    main()
