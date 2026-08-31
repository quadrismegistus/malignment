"""Batched generation via vLLM, writing to the same stash as generate.py.

    from malignment.vllm_generate import run

    run(models, prompts, n=10, max_new_tokens=1800)

or from the command line:

    python -m malignment.vllm_generate --models model1 model2 \\
           --prompts-file prompts.jsonl --n 10

## WHY THIS EXISTS ALONGSIDE generate.py

`generate.py` is correct (pinned decoder, frame rendering, provenance) but slow:
single-stream HF generate, ~50 tok/s on CUDA. vLLM batches hundreds of sequences
concurrently at ~600 tok/s. For 100 models x 10 prompts x 10 passages x 1800
tokens, that is 8 hours against 100.

## WHAT IS SHARED WITH generate.py, AND WHAT IS NOT

    SHARED    DECODER (the pinned parameters)
              render() (frame/template handling)
              gen_key() (the key identity)
              Passage (the record type, with full provenance)
              GEN_OUT / gen_stash() (the write path)

    NOT       the inference engine (vLLM LLM, not HF model.generate)
              the batch structure (all prompts x n at once, not one at a time)
              gpu_memory_utilization sizing (from vllm_y_run.py's lesson)

A passage written by this module is INDISTINGUISHABLE from one written by
generate.py in the stash: same key, same Passage fields. Checkpoint.generate()
reads both. The only marker is `engine` in the value dict.

## PROMPTS FILE FORMAT

JSONL, one condition per line:

    {"prompt": "She was so angry she wanted to"}
    {"prompt": "She was so angry she wanted to", "system": "", "prefill": true}
    {"prompt": "She was so angry she wanted to", "system": "You are helpful."}

Or plain text (one prompt per line, all raw frame).

Fields:
    prompt      the stem text (required)
    system      system message: omit for DEFAULT (template's own), "" for empty,
                or a string. A base model with no template ignores this.
    user        user-turn prefix (rare; for multi-turn setups)
    prefill     true/false: wrap in the template's prefill format
    user_msg    the user message for prefill mode (default "Hi.")

**A base model cannot enter chat mode.** If the model has no template and
system/prefill are requested, the prompt is generated RAW and `frame_refused`
is set on the passage record. This is generate.py's `FrameRefused` path,
applied per-prompt rather than aborting the batch.

## GOTCHAS FROM THE OLD REPO (vllm_y_run.py, vllm_generate.py)

1. **VLLM_USE_V1=0 for mamba.** V1 engine has no SSM support.
2. **dtype="float16" not "auto".** "auto" picks bf16 per-checkpoint, introducing
   a per-vendor covariate aligned with the arm contrast.
3. **gpu_memory_utilization sized from card and model, not a constant.**
4. **top_k=-1 disables it in vLLM.** (top_k=0 in HF.)
5. **Per-sample seeds.** seed + i, so n samples are n observations.
6. **MPS sampling is broken** (lacan [6570]). 1/400 draws return out-of-range
   tokens. This module is CUDA-only by design. Do not port it to MPS.
"""
import json
import os
import sys
import time

os.environ.setdefault("VLLM_USE_V1", "0")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")

from . import generate as G
from .generate import DECODER, gen_key, _passage, frame_label, DEFAULT


def _gpu_frac(model_gb):
    """gpu_memory_utilization sized from card and model.

    Needs weights + KV cache + activations inside the fraction. At
    max_model_len=3500, the KV cache alone is ~2-4 GB for a 7B model.
    The old formula was too conservative (0.67 for 9B on 24GB, leaving
    no room for the cache). Floor at 0.85 — vLLM manages the split
    between weights and cache internally.
    """
    import torch
    total = torch.cuda.mem_get_info()[1] / 1e9
    want = model_gb * 1.3 + 8.0
    frac = max(0.90, min(0.95, want / total))
    return frac


def _model_gb(model_id):
    try:
        from huggingface_hub import model_info
        info = model_info(model_id)
        if info.safetensors and info.safetensors.total:
            return info.safetensors.total / 1e9
    except Exception:
        pass
    return 14.0


def _build_llm(model_id, max_model_len=2048, tp=1, dtype="float16"):
    from vllm import LLM
    gb = _model_gb(model_id)
    frac = _gpu_frac(gb)
    # cap max_model_len to what the model supports
    actual_len = max_model_len
    try:
        from transformers import AutoConfig
        cfg = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
        model_max = (getattr(cfg, "max_position_embeddings", None)
                     or getattr(cfg, "seq_length", None)
                     or getattr(cfg, "n_positions", None)
                     or getattr(cfg, "max_sequence_length", None))
        if model_max and max_model_len > int(model_max):
            actual_len = int(model_max)
            print("  capped max_model_len %d -> %d (model's max_position_embeddings)"
                  % (max_model_len, actual_len), flush=True)
    except Exception:
        pass
    print("  vLLM: %s | ~%.0f GB | frac %.2f | dtype %s | ctx %d"
          % (model_id, gb, frac, dtype, actual_len), flush=True)
    return LLM(model=model_id, dtype=dtype, max_model_len=actual_len,
               gpu_memory_utilization=frac, tensor_parallel_size=tp,
               trust_remote_code=True, enforce_eager=False)


def _free_llm(llm, model_id=None):
    """Explicit teardown — vLLM leaks KV reservation without it.

    Also clears the HF cache for this model to free disk. On a 50 GB
    container disk, two 7B models' weights (14 GB each) plus the vLLM
    install (11 GB) fill the disk. Clearing after each model keeps it
    under control. The next model re-downloads (~2 min on a fast link),
    which is cheap against the generation time.
    """
    import gc, glob, os, shutil, torch
    try:
        llm.llm_engine.shutdown()
    except Exception:
        pass
    del llm
    gc.collect()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        torch.cuda.reset_peak_memory_stats()
    if model_id:
        safe = model_id.replace("/", "--")
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        for d in glob.glob(os.path.join(cache_dir, "models--" + safe)):
            try:
                shutil.rmtree(d)
            except Exception:
                pass


def _vllm_version():
    try:
        import vllm
        return getattr(vllm, "__version__", "unknown")
    except ImportError:
        return "not installed"


# ---------------------------------------------------------------------------
# Prompt conditions
# ---------------------------------------------------------------------------

def load_prompts(path):
    """Load a prompts file. -> list of condition dicts.

    JSONL: each line is {"prompt": "...", "system": "...", "prefill": true, ...}
    Plain text: one prompt per line, all raw frame.
    """
    conditions = []
    with open(path, encoding="utf-8") as fh:
        first = fh.readline()
        fh.seek(0)
        is_jsonl = first.strip().startswith("{")
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if is_jsonl:
                d = json.loads(line)
                conditions.append({
                    "prompt": d["prompt"],
                    "system": d.get("system", "_DEFAULT_"),
                    "user": d.get("user"),
                    "prefill": bool(d.get("prefill", False)),
                    "user_msg": d.get("user_msg", "Hi."),
                })
            else:
                conditions.append({
                    "prompt": line,
                    "system": "_DEFAULT_",
                    "user": None,
                    "prefill": False,
                    "user_msg": "Hi.",
                })
    return conditions


def _resolve_system(s):
    """Convert the prompts-file system field to generate.py's convention."""
    if s == "_DEFAULT_":
        return DEFAULT
    return s


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def _needs_template(cond):
    """Whether this condition requires a chat template."""
    s = cond.get("system", "_DEFAULT_")
    return s != "_DEFAULT_" or cond.get("prefill", False) or cond.get("user")


def _has_template(model_id):
    """Whether this model has a chat template, from the roster."""
    try:
        from . import roster
        oh = roster.template_overhead()
        v = oh.get(model_id)
        if v is not None:
            return v.get("overhead_chars", 0) > 0
    except Exception:
        pass
    return None


def generate_model(model_id, conditions, n=10, seed=42, decoder=None,
                   max_model_len=2048, tp=1, dtype="float16",
                   stash=None, dry_run=False):
    """Generate n passages per condition for one model via vLLM. -> int

    `conditions` is a list of dicts from `load_prompts()`.
    Conditions requiring a chat template are SKIPPED on models without one,
    rather than generating a raw passage for the wrong condition.
    """
    from vllm import SamplingParams
    from .checkpoint import Checkpoint

    dec = dict(DECODER)
    dec.update(decoder or {})
    max_tok = dec.get("max_new_tokens", 256)

    ck = Checkpoint(model_id)
    if stash is None:
        stash = ck.gen_stash()
    existing_stashes = ck.gen_stashes()

    has_tpl = _has_template(model_id)
    model_conditions = []
    n_skipped_frame = 0
    for cond in conditions:
        if _needs_template(cond) and has_tpl is False:
            n_skipped_frame += 1
            continue
        model_conditions.append(cond)
    if n_skipped_frame:
        print("    %s: skipped %d conditions (no template)"
              % (model_id, n_skipped_frame))

    todo = []
    for cond in model_conditions:
        system = _resolve_system(cond["system"])
        user = cond.get("user")
        prefill = cond.get("prefill", False)
        user_msg = cond.get("user_msg", "Hi.")
        prompt = cond["prompt"]

        frame = frame_label(system, user, prefill, None)
        sysk = "" if system is DEFAULT else (system or "")

        for i in range(n):
            k = dict(gen_key(model_id, prompt, frame, sysk, dec,
                             None if seed is None else seed + i, i,
                             system_set=(system is not DEFAULT)),
                     user=user, prefill=bool(prefill),
                     user_msg=(user_msg if prefill else None))
            already = False
            for st in existing_stashes:
                try:
                    if st.get(k):
                        already = True
                        break
                except Exception:
                    pass
            if not already:
                todo.append((prompt, i, k, cond))

    if not todo:
        print("    %s: all %d conditions x %d cached"
              % (model_id, len(conditions), n))
        return 0

    print("    %s: %d to generate (%d cached)"
          % (model_id, len(todo), len(conditions) * n - len(todo)))
    if dry_run:
        return 0

    llm = _build_llm(model_id, max_model_len=max_model_len, tp=tp, dtype=dtype)
    tok = llm.get_tokenizer()

    # inject chat template override for models with no shipped template
    from .runners import _chat_template_override
    if not getattr(tok, "chat_template", None):
        override = _chat_template_override(model_id)
        if override:
            tok.chat_template = override
            print("    chat template override applied", flush=True)

    vllm_texts = []
    render_info = []
    for prompt, i, k, cond in todo:
        system = _resolve_system(cond["system"])
        user = cond.get("user")
        prefill = cond.get("prefill", False)
        user_msg = cond.get("user_msg", "Hi.")

        frame_refused = False
        if system is not DEFAULT or prefill or user:
            messages = []
            if system is not DEFAULT:
                sys_text = system if system else ""
                if sys_text:
                    messages.append({"role": "system", "content": sys_text})
            if prefill:
                # build turns UP TO the assistant, get generation prompt,
                # then concatenate the stem AFTER — keeping the turn OPEN.
                # DO NOT pass the stem as an assistant message: that closes
                # the turn with <|im_end|> and the model generates nothing.
                messages.append({"role": "user", "content": user_msg or ""})
                try:
                    rendered = tok.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True)
                    rendered = rendered + prompt
                    vllm_texts.append(rendered)
                    render_info.append((True, False))
                    continue
                except Exception:
                    frame_refused = True
            else:
                messages.append({"role": "user", "content": prompt})
                try:
                    rendered = tok.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True)
                    vllm_texts.append(rendered)
                    render_info.append((True, False))
                    continue
                except Exception:
                    frame_refused = True
        vllm_texts.append(prompt)
        render_info.append((False, frame_refused))

    sp_list = []
    for prompt, i, k, cond in todo:
        sp_list.append(SamplingParams(
            temperature=dec.get("temperature", 1.0),
            top_p=dec.get("top_p", 1.0),
            top_k=-1,
            max_tokens=max_tok,
            seed=None if seed is None else seed + i,
        ))

    t0 = time.time()
    outputs = llm.generate(vllm_texts, sp_list)
    elapsed = time.time() - t0
    total_tokens = sum(len(o.outputs[0].token_ids) for o in outputs)
    print("    generated %d passages, %d tokens in %.1fs (%.0f tok/s)"
          % (len(outputs), total_tokens, elapsed,
             total_tokens / elapsed if elapsed else 0))

    n_written = 0
    vv = _vllm_version()
    for (prompt, i, k, cond), output, (templated, refused) in zip(
            todo, outputs, render_info):
        system = _resolve_system(cond["system"])
        user = cond.get("user")
        prefill = cond.get("prefill", False)
        user_msg = cond.get("user_msg", "Hi.")
        comp = output.outputs[0]

        p = _passage(
            text=comp.text,
            prompt=prompt,
            model=model_id,
            frame=frame_label(system, user, prefill,
                              templated if not refused else False),
            seed=None if seed is None else seed + i,
            decoder=dict(dec, max_new_tokens=max_tok),
            n_new_tokens=len(comp.token_ids),
            finish=("length" if comp.finish_reason == "length" else "eos"),
            sys_supported=not refused,
            system=(None if system is DEFAULT else system),
            system_default=(system is DEFAULT),
            user=user, prefill=bool(prefill),
            user_msg=(user_msg if prefill else None),
            template=templated,
            engine="vllm",
            engine_version=vv,
        )
        stash[k] = p._asdict()
        n_written += 1

    _free_llm(llm, model_id=model_id)
    return n_written


def run(models, conditions, n=10, seed=42, decoder=None,
        max_new_tokens=1800, max_model_len=2048, tp=1, dtype="float16",
        dry_run=False, prompts_file=None, subprocess_per_model=True):
    """Generate for every model in `models`. -> total passages written.

    **SUBPROCESS PER MODEL.** vLLM leaks GPU memory between LLM() calls —
    the KV cache reservation from model N survives _free_llm and the engine
    init for model N+1 fails with "No available memory for cache blocks."
    The only reliable way to reclaim 100% of GPU memory is to exit the
    process. So each model runs as a subprocess calling this same CLI with
    `--models <single_model>`. The subprocess loads vLLM, generates, writes
    to the stash, and exits. Full GPU cleanup guaranteed.

    Set `subprocess_per_model=False` to run in-process (for debugging).
    """
    if conditions and isinstance(conditions[0], str):
        conditions = [{"prompt": p, "system": "_DEFAULT_", "user": None,
                       "prefill": False, "user_msg": "Hi."} for p in conditions]

    dec = dict(DECODER)
    dec["max_new_tokens"] = max_new_tokens
    if decoder:
        dec.update(decoder)

    if subprocess_per_model and prompts_file:
        import subprocess as sp
        total = 0
        for i, mid in enumerate(models, 1):
            print("[%d/%d] %s" % (i, len(models), mid), flush=True)
            cmd = [sys.executable, "-u", "-m", "malignment.vllm_generate",
                   "--models", mid,
                   "--prompts-file", prompts_file,
                   "--n", str(n),
                   "--temperature", str(dec.get("temperature", 1.0)),
                   "--top-p", str(dec.get("top_p", 0.95)),
                   "--max-new-tokens", str(max_new_tokens),
                   "--max-model-len", str(max_model_len),
                   "--seed", str(seed),
                   "--tp", str(tp),
                   "--dtype", dtype,
                   "--no-subprocess"]
            if dry_run:
                cmd.append("--dry-run")
            env = dict(os.environ)
            env["VLLM_USE_V1"] = "0"
            result = sp.run(cmd, env=env)
            if result.returncode == 0:
                print("    subprocess OK", flush=True)
            else:
                print("    subprocess FAILED (exit %d)" % result.returncode, flush=True)
        print("\ndone across %d models (subprocess mode)" % len(models))
        return 0

    # in-process fallback
    total = 0
    for i, mid in enumerate(models, 1):
        print("[%d/%d] %s" % (i, len(models), mid), flush=True)
        try:
            w = generate_model(
                mid, conditions, n=n, seed=seed, decoder=dec,
                max_model_len=max_model_len, tp=tp, dtype=dtype,
                dry_run=dry_run)
            total += w
        except Exception as e:
            import traceback
            print("    FAILED: %s: %s" % (type(e).__name__, e), flush=True)
            traceback.print_exc()
    print("\ndone: %d passages written across %d models" % (total, len(models)))
    return total


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="Batched generation via vLLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Prompts file format (JSONL):
  {"prompt": "She was so angry she wanted to"}
  {"prompt": "She was so angry she wanted to", "system": "", "prefill": true}

Or plain text (one prompt per line, all raw frame).
""")
    mg = ap.add_mutually_exclusive_group(required=True)
    mg.add_argument("--models", nargs="+", help="model IDs on the command line")
    mg.add_argument("--models-file",
                    help="file with one model ID per line")
    ap.add_argument("--prompts-file", required=True)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--temperature", type=float, default=1.0,
                    help="sampling temperature (default 1.0; Rettberg uses 0.8)")
    ap.add_argument("--top-p", type=float, default=0.95,
                    help="nucleus sampling threshold (default 0.95; 1.0 disables)")
    ap.add_argument("--max-new-tokens", type=int, default=1800)
    ap.add_argument("--max-model-len", type=int, default=3300,
                    help="vLLM model context length (must exceed prompt + max-new-tokens)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tp", type=int, default=1)
    ap.add_argument("--dtype", default="float16")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-subprocess", action="store_true",
                    help="run in-process (used by subprocess-per-model internally)")
    a = ap.parse_args(argv)

    if a.models_file:
        models = [l.strip() for l in open(a.models_file) if l.strip()
                  and not l.strip().startswith("#")]
    else:
        models = a.models

    conditions = load_prompts(a.prompts_file)
    frames = set()
    for c in conditions:
        s = c["system"]
        frames.add("raw" if s == "_DEFAULT_" and not c["prefill"]
                    else "prefill" if c["prefill"] else "framed")
    print("models: %d | conditions: %d | frames: %s | n: %d | max_new_tokens: %d | t=%.1f p=%.2f"
          % (len(models), len(conditions), sorted(frames), a.n, a.max_new_tokens,
             a.temperature, a.top_p))
    run(models, conditions, n=a.n, seed=a.seed,
        decoder={"temperature": a.temperature, "top_p": a.top_p},
        max_new_tokens=a.max_new_tokens, max_model_len=a.max_model_len,
        tp=a.tp, dtype=a.dtype, dry_run=a.dry_run,
        prompts_file=a.prompts_file,
        subprocess_per_model=not a.no_subprocess)


if __name__ == "__main__":
    main()
