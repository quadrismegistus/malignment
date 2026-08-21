"""Is the deployed difference the WEIGHTS or the PERSONA STRING the vendor ships?

    python .../scripts/system_swap.py --device mps

`prefill_default` is the deployed surface and it is not a controlled contrast:
Qwen2.5-7B ships `"You are a helpful assistant."` and its Instruct arm ships
`"You are Qwen, created by Alibaba Cloud. You are a helpful assistant."`, so a
base-vs-aligned difference measured there confounds the weights with a string
somebody wrote. This crosses them: every model is run under EVERY arm's default
plus an empty system, so the persona and the weights vary independently.

    base weights  x  base persona     <- what the base ships
    base weights  x  aligned persona
    aligned weights x base persona
    aligned weights x aligned persona <- what the aligned model ships

The diagonal is `prefill_default`. The off-diagonal is what makes it readable.

## THE USER TURN IS `Hi.`, NOT EMPTY, AND THAT IS NOT A DETAIL

An empty user turn is a degenerate conversational state and the model formats
instead of continuing -- measured on Olmo-3-DPO, `prefill_bare` puts 0.530 of its
mass on form punctuation with markdown `**` at 0.269, and a single space does not
fix it (0.526) while `Hi.` does (0.050). So the empty-user version of this
experiment would vary the persona on top of an artifact. The conversational state
is held VALID and the system string is the only thing that moves.

## THE DEFAULTS ARE EXTRACTED, NOT TYPED

Hard-coding the personas would make this file wrong the moment a repo updates its
template, silently, in the direction of a null. Each model's default is recovered
by rendering the template with no system message and again with an empty one, and
taking the difference -- so what is measured is what the tokenizer actually
injects today.
"""

import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), "results")
sys.path.insert(0, HERE)
from conditions import _render, PRESENCE, context_sha, SYSTEM_DEFAULT_MARK  # noqa: E402

PAIRS = [("Qwen2.5-7B", "Qwen/Qwen2.5-7B", "Qwen/Qwen2.5-7B-Instruct"),
         ("Qwen2.5-0.5B", "Qwen/Qwen2.5-0.5B", "Qwen/Qwen2.5-0.5B-Instruct")]

FILL_CHARS = set("_-–—=.·•*~^ ")


def default_system(tok):
    """The persona this template injects when no system message is passed.

    -> str, or None if the template injects nothing (then default == empty and
    the two conditions collapse, which the caller must be able to SEE).
    """
    a = _render(tok, SYSTEM_DEFAULT_MARK, "")
    b = _render(tok, "", "")
    if not a or not b:
        return None
    a, b = a[0], b[0]
    if a == b:
        return None
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[len(a)-1-j] == b[len(b)-1-j]:
        j += 1
    return a[i:len(a)-j]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="mps")
    ap.add_argument("--topk", type=int, default=50)
    ap.add_argument("--out", default=os.path.join(RESULTS, "system_swap.jsonl"))
    a = ap.parse_args(argv)

    import re, torch, warnings
    warnings.filterwarnings("ignore")
    from transformers import AutoTokenizer, AutoModelForCausalLM
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
    from malignment.prompts import Prompts

    pat = re.compile(r"^(violence|sexual)_(liminal|explicit)")
    prompts = sorted([p for p in Prompts.all()
                      if pat.match(p.prompt_id) and not p.prompt_id.endswith("_zh")],
                     key=lambda p: p.prompt_id)

    #: ---- recover every persona in play BEFORE loading any weights
    personas = {}
    for lab, b, al in PAIRS:
        for arm, mid in (("base", b), ("aligned", al)):
            tok = AutoTokenizer.from_pretrained(mid, trust_remote_code=True)
            personas[mid] = default_system(tok)
            print("%-30s default: %r" % (mid.split("/")[-1], personas[mid]))

    fh = open(a.out, "w")
    for lab, b, al in PAIRS:
        #: the two personas of THIS lineage, plus empty as the no-persona floor
        conds = [("empty", "")]
        for arm, mid in (("base", b), ("aligned", al)):
            s = personas[mid]
            if s is not None:
                conds.append(("%s_persona" % arm, s))
        seen = {}
        for name, s in conds:
            if s in seen:
                print("  NOTE %s renders identically to %s" % (name, seen[s]))
            seen.setdefault(s, name)

        for arm, mid in (("base", b), ("aligned", al)):
            tok = AutoTokenizer.from_pretrained(mid, trust_remote_code=True)
            mdl = AutoModelForCausalLM.from_pretrained(
                mid, dtype=torch.float32, low_cpu_mem_usage=True,
                trust_remote_code=True).eval().to(a.device)
            print("\n%s  (%s arm of %s)" % (mid, arm, lab), flush=True)
            for name, s in conds:
                rows = []
                for p in prompts:
                    r = _render(tok, s, PRESENCE)
                    if not r:
                        continue
                    text = r[0] + p.text
                    ids = tok(text, return_tensors="pt",
                              add_special_tokens=False)["input_ids"]
                    with torch.no_grad():
                        lg = mdl(ids.to(a.device)).logits[0, -1].float()
                    lp = torch.log_softmax(lg, -1).cpu()
                    top = torch.topk(lp, a.topk)
                    pairs = [(tok.decode([i]), float(v)) for i, v
                             in zip(top.indices.tolist(), top.values.exp().tolist())]
                    row = dict(lineage=lab, model=mid, arm=arm, persona=name,
                               system=s, prompt_id=p.prompt_id, prompt=p.text,
                               context_sha=context_sha(text),
                               entropy=float(-(lp.exp()*lp).sum() / 0.6931471805599453),
                               top1=float(lp.max().exp()),
                               fill=sum(v for t, v in pairs
                                        if t.strip() and set(t) <= FILL_CHARS),
                               topk=[[t, round(v, 6)] for t, v in pairs])
                    fh.write(json.dumps(row) + "\n")
                    rows.append(row)
                fh.flush()
                print("  %-16s H %.3f  fill %.4f  %r"
                      % (name, sum(r["entropy"] for r in rows)/len(rows),
                         sum(r["fill"] for r in rows)/len(rows), s[:52]), flush=True)
            del mdl
    fh.close()
    print("\n-> %s" % a.out)


if __name__ == "__main__":
    main()
