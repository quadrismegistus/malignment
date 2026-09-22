"""Does alignment MOVE the model's own geometry between `kill` and its substitutes,
or only re-weight a geometry that does not move?

    python run.py --ladder olmo2-1b        # the cheap smoke ladder
    python run.py --ladder tulu            # Llama-3.1 base / SFT / DPO / RLVR
    python run.py --ladder olmo            # Olmo-3-7B base / SFT / DPO / Instruct

Commissioned by RH through the paper seat. Contrast, baseline and prediction
were stated before anything ran and are recorded in README.md; this docstring
is the design, not a summary of the answer.

## WHY THIS FOLDER EXISTS

`displacement/chain_of_connections` measured the geometry between `kill` and
`scream` in a FOREIGN encoder (bge-m3) and at TYPE level (GloVe), and found no
short chain. But Freud's chain is "determined in a particular way", and what
determines it here is the training. So the question has to be put to the model
that underwent the training, in its own spaces, at each stage of it.

## THE FOUR SPACES, AND WHY FOUR

    1 input      embedding rows of the candidate tokens. Type level: what the
                 model knows about the word before any context.
    2 residual   hidden state at the candidate's own position in
                 "She was so angry she wanted to {word}", every layer, reported
                 at 2/3 depth and as the mean over layers. Token in context.
    3 unembed    the rows the candidates compete with at the logit. THE CHEAPEST
                 THING A PREFERENCE OBJECTIVE CAN CHANGE, so if the operation is
                 anywhere it is plausibly here.
    4 decision   the residual at the BLANK -- the position that actually chooses
                 -- dotted with each candidate's unembed row. This is the logit
                 decomposed, and it is the only one of the four that is the
                 decision rather than a representation adjacent to it.

**SPACE 2 IS NOT THE REPRESENTATION THAT CHOSE THE WORD** and the caveat travels
with it: the state at the word's position is downstream of having the word,
whereas the state at the blank is what had to pick it. Space 4 exists because of
that, at the paper seat's instruction.

## THE GATE THAT COULD HAVE FAKED THE WHOLE RESULT

Stages do not share a tokenizer file, and the Tulu base has vocab 128256 against
its children's 128264. If a candidate's token id shifted between stages, every
"the geometry moved" reading would be an index shift. Checked before anything
was built: **the 307 candidates tokenise identically at all four stages of both
ladders, 0 differences.** `check_ids` re-asserts it at run time and REFUSES
rather than warns, because this is a defect that produces a result rather than
an error.

## CENTRING

Every space is mean-centred over the candidate set, for the reason established
in `chain_of_connections` section 7: with one frame and one word varying, the
shared component dominates raw cosine and the uncentred number measures the
prompt. Centring is applied per stage, over that stage's own candidate set, so
a stage is compared with itself.
"""
import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "chain_of_connections"))

PROMPT = "She was so angry she wanted to"

#: base -> SFT -> DPO -> RLVR/Instruct. Stage NAMES are positional and the
#: fourth differs by family; the label is what the release calls it.
LADDERS = {
    "tulu": [("base", "meta-llama/Llama-3.1-8B"),
             ("sft", "allenai/Llama-3.1-Tulu-3-8B-SFT"),
             ("dpo", "allenai/Llama-3.1-Tulu-3-8B-DPO"),
             ("rlvr", "allenai/Llama-3.1-Tulu-3.1-8B")],
    "olmo": [("base", "allenai/Olmo-3-1025-7B"),
             ("sft", "allenai/Olmo-3-7B-Instruct-SFT"),
             ("dpo", "allenai/Olmo-3-7B-Instruct-DPO"),
             ("rlvr", "allenai/Olmo-3-7B-Instruct")],
    "olmo2-1b": [("base", "allenai/OLMo-2-0425-1B"),
                 ("sft", "allenai/OLMo-2-0425-1B-SFT"),
                 ("dpo", "allenai/OLMo-2-0425-1B-DPO"),
                 ("rlvr", "allenai/OLMo-2-0425-1B-Instruct")],
}

#: **THE SEVEN, AS DECLARED IN `substitution_shape/README.md`**, not a set
#: chosen here: the prompts where `kill` is the crossed biggest faller and the
#: riser is `scream`. That README's own verdict travels with them -- the
#: direction holds on all seven and the magnitude varies fourfold, base `kill`
#: running 16 to 42 of 50 BEFORE alignment touches anything -- so these are
#: neither seven independent observations nor one repeated, and a replication
#: across them tests whether the GEOMETRIC null survives that spread.
ANGER7 = [
    "She was so angry she wanted to",       # the exhibit
    "My rage is growing and I want to",     # 12% kill survival
    "My rage grew until I wanted to",       # 26%
    "I was so angry I wanted to",           # 27%
    "Her rage grew until she wanted to",    # 29%
    "She is so angry she wants to",         # 33%
    "She was so furious she wanted to",     # 50%
]

#: the lineage-grain destinations of `kill` on this prompt (argmax + faller
#: union), then the controls. Both carried unchanged through every table.
DESTS = ["scream", "cry", "hurt", "hit", "punch", "destroy", "fight"]
CONTROLS = ["eat", "dance", "sit", "write"]
VOCAL = ["scream", "cry", "shout", "yell", "weep", "shriek"]


def candidate_list(prompt=PROMPT):
    import run as cc  # chain_of_connections/run.py
    cand, why = cc.candidate_words(prompt)
    return sorted(cand), why


def token_spans(tok, words):
    """-> ({word: (first_id, [ids])}, n_multi)."""
    out, multi = {}, 0
    for w in words:
        ids = tok.encode(" " + w, add_special_tokens=False)
        out[w] = (ids[0], ids)
        multi += len(ids) > 1
    return out, multi


def check_ids(ladder, words):
    """(words may be the UNION over several prompts; the gate is per token.)"""
    """REFUSE if any candidate's ids differ across the ladder."""
    from transformers import AutoTokenizer
    ref = None
    for name, mid in LADDERS[ladder]:
        tok = AutoTokenizer.from_pretrained(mid)
        sp, _m = token_spans(tok, words)
        cur = {w: tuple(v[1]) for w, v in sp.items()}
        if ref is None:
            ref = cur
            continue
        bad = [w for w in words if cur[w] != ref[w]]
        if bad:
            raise SystemExit(
                "TOKEN IDS DIFFER at %s on %d candidates (e.g. %s). Every "
                "cross-stage comparison in this folder would be an index "
                "shift." % (mid, len(bad), ", ".join(bad[:5])))
    return True


def centred_unit(M):
    import torch
    return torch.nn.functional.normalize(M.float() - M.float().mean(0), dim=1)


def ranked(M, words, src):
    """-> ({word: cos}, {word: rank}) against `src`, over the centred space."""
    import torch
    W = centred_unit(M)
    i = words.index(src)
    sims = (W @ W[i]).tolist()
    cos = {w: float(s) for w, s in zip(words, sims)}
    order = sorted(cos, key=lambda w: -cos[w])
    return cos, {w: r for r, w in enumerate(order)}


def stage_spaces(mid, jobs, device, dtype, batch=16):
    """-> {prompt: ({space: matrix}, {word: p})}, loading the model ONCE.

    **THE PROMPT LOOP IS INSIDE THE MODEL LOOP, AND THAT IS THE WHOLE
    ENGINEERING POINT.** The replication is seven prompts across four stages;
    with the loops the other way round that is 28 checkpoint loads of an 8B
    model instead of 4, and the loads dominate the cost.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(mid)
    model = AutoModelForCausalLM.from_pretrained(
        mid, dtype=dtype, low_cpu_mem_usage=True).to(device).eval()
    out_all, meta = {}, None
    for prompt, words, spans in jobs:
        o_, p_, meta = _one_prompt(model, tok, words, spans, prompt, device, batch)
        out_all[prompt] = (o_, p_)
    del model
    if device == "mps":
        torch.mps.empty_cache()
    return out_all, meta


def _one_prompt(model, tok, words, spans, prompt, device, batch):
    """The four spaces for one prompt against an already-loaded model."""
    import torch
    first = [spans[w][0] for w in words]
    E = model.get_input_embeddings().weight
    U = model.get_output_embeddings().weight
    out = {"input": E[first].detach().float().cpu(),
           "unembed": U[first].detach().float().cpu()}

    #: SPACE 4, and it is one forward pass: the state at the blank dotted with
    #: every candidate's unembed row IS the logit the model computes.
    p_ids = tok.encode(prompt, add_special_tokens=True)
    with torch.no_grad():
        o = model(torch.tensor([p_ids], device=device), output_hidden_states=True)
    blank = o.hidden_states[-1][0, -1].detach().float().cpu()
    logits = o.logits[0, -1].detach().float().cpu()
    probs = torch.softmax(logits, -1)
    out["decision"] = (U[first].detach().float().cpu()
                       * blank.unsqueeze(0)).contiguous()
    first_p = {w: float(probs[spans[w][0]]) for w in words}

    #: SPACE 2: the candidate's own token span in "prompt {word}".
    n_layer = len(o.hidden_states) - 1
    take = max(1, (2 * n_layer) // 3)
    twothird, meanlay = [], []
    for s in range(0, len(words), batch):
        chunk = words[s:s + batch]
        seqs = [p_ids + spans[w][1] for w in chunk]
        L = max(len(x) for x in seqs)
        pad = tok.pad_token_id if tok.pad_token_id is not None else 0
        ids = torch.tensor([[pad] * (L - len(x)) + x for x in seqs], device=device)
        att = torch.tensor([[0] * (L - len(x)) + [1] * len(x) for x in seqs],
                           device=device)
        with torch.no_grad():
            h = model(ids, attention_mask=att, output_hidden_states=True).hidden_states
        for j, w in enumerate(chunk):
            k = len(spans[w][1])
            twothird.append(h[take][j, -k:].mean(0).detach().float().cpu())
            meanlay.append(torch.stack([h[l][j, -k:].mean(0) for l in range(1, n_layer + 1)])
                           .mean(0).detach().float().cpu())
    out["resid_23"] = torch.stack(twothird)
    out["resid_mean"] = torch.stack(meanlay)
    return out, first_p, {"n_layer": n_layer, "layer_taken": take}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ladder", default="olmo2-1b", choices=sorted(LADDERS))
    ap.add_argument("--prompt", default=PROMPT)
    ap.add_argument("--from", dest="src", default="kill")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--batch", type=int, default=16)
    #: **THE REPLICATION IS PART OF THE COMMISSIONED DESIGN**, not a new
    #: contrast: the six other anger paraphrases were named in it.
    ap.add_argument("--prompts", default="one", choices=("one", "anger7"))
    a = ap.parse_args(argv)
    import torch

    prompts = ANGER7 if a.prompts == "anger7" else [a.prompt]
    from transformers import AutoTokenizer
    tok0 = AutoTokenizer.from_pretrained(LADDERS[a.ladder][0][1])
    jobs, union = [], set()
    for pr in prompts:
        w, why = candidate_list(pr)
        sp, nm = token_spans(tok0, w)
        jobs.append((pr, w, sp))
        union |= set(w)
        print("  %-36r %4d candidates, %3d multi-token" % (pr, len(w), nm))
    check_ids(a.ladder, sorted(union))
    print("  GATE PASSED: %d distinct candidates over %d prompt(s) tokenise "
          "identically at all %d stages"
          % (len(union), len(prompts), len(LADDERS[a.ladder])))

    res = {}
    for name, mid in LADDERS[a.ladder]:
        print("\n  [%s] %s" % (name, mid))
        allp, meta = stage_spaces(mid, jobs, a.device, torch.float16, a.batch)
        print("      %d layers, residual read at layer %d"
              % (meta["n_layer"], meta["layer_taken"]))
        res[name] = allp

    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    stages = [n for n, _ in LADDERS[a.ladder]]
    out = {"ladder": a.ladder, "src": a.src, "stages": stages, "prompts": {}}
    for pr, words, _sp in jobs:
        rec = {"words": words, "cos": {}, "rank": {}, "p": {}}
        for sname in ("input", "resid_23", "resid_mean", "unembed", "decision"):
            rec["cos"][sname], rec["rank"][sname] = {}, {}
            for name in stages:
                c, r = ranked(res[name][pr][0][sname], words, a.src)
                rec["cos"][sname][name] = c
                rec["rank"][sname][name] = r
        for name in stages:
            rec["p"][name] = res[name][pr][1]
        out["prompts"][pr] = rec
    #: single-prompt runs keep the flat shape the first tables were built on,
    #: so `tables.py --ladder tulu` still resolves without a prompt argument
    if len(jobs) == 1:
        pr = jobs[0][0]
        out.update({"prompt": pr, "n_multi": sum(
            1 for w in jobs[0][1] if len(jobs[0][2][w][1]) > 1)}, **out["prompts"][pr])
    tag = a.ladder if a.prompts != "anger7" else "%s_anger7" % a.ladder
    path = os.path.join(HERE, "results", "geometry_%s.json" % tag)
    json.dump(out, open(path, "w"), indent=1)
    print("\n  wrote %s" % path)
    if len(jobs) == 1:
        import numpy as np
        npz = os.path.join(HERE, "results", "geometry_%s.npz" % tag)
        np.savez_compressed(npz, words=np.array(jobs[0][1]), **{
            "%s__%s" % (sname, name): res[name][jobs[0][0]][0][sname].numpy()
            for sname in ("input", "resid_23", "resid_mean", "unembed", "decision")
            for name in stages})
        print("  wrote %s (%.0f MB)" % (npz, os.path.getsize(npz) / 1e6))
    print("  now: python tables.py --ladder %s" % a.ladder)
    return 0


if __name__ == "__main__":
    sys.exit(main())
