"""Does the WORDING of the continuation instruction matter, or only its presence?

    python .../scripts/instruct_variants.py --device mps

`prefill_presence` established that a contentful user turn ("Hi.") collapses the
fill paradigm where an empty turn and a bare space do not. `prefill_instruct`
established that an instruction does something further -- 1.28 bits of entropy
beyond presence on the Olmo arms. What neither shows is whether that further
effect is the instruction MEANING "continue", or the particular sentence I wrote.

So: five instructions that all mean continue, differing in length and in
punctuation, against the two reference frames. If they agree, the instruction is
a switch and its wording is not part of the measurement. If they spread, then
every number from `prefill_instruct` is a number about one sentence, and the
condition cannot be reported without it.

**THE TRAILING PUNCTUATION IS NOT COSMETIC AND THAT IS WHY IT IS VARIED.**
`Continue the text:` ends in a colon, which in the training distribution
introduces the thing that follows; `Continue the text.` closes. Two strings with
the same meaning and different discourse consequences are exactly the case where
"any content will do" would fail if it is going to fail.

Smoke scope: the Olmo arms that HAVE a template. `Olmo-3-1025-7B` ships none, so
no templated condition exists for it and it is not in the ladder here.
"""

import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), "results")
sys.path.insert(0, HERE)
from conditions import _render, PRESENCE, context_sha          # noqa: E402

#: Ordered longest-to-shortest so a length effect would be visible as a gradient
#: rather than having to be recovered from the labels.
VARIANTS = [
    ("mine",      "Continue the text. Output only the continuation, no preamble."),
    ("text_stop", "Continue the text."),
    ("text_colon", "Continue the text:"),
    ("colon",     "Continue:"),
    ("stop",      "Continue."),
]
REFERENCE = [("bare", ""), ("presence", PRESENCE)]

LADDER = ["allenai/Olmo-3-7B-Instruct-SFT",
          "allenai/Olmo-3-7B-Instruct-DPO",
          "allenai/Olmo-3-7B-Instruct"]

FILL_CHARS = set("_-–—=.·•*~^ ")


def fill_share(pairs):
    """Mass on surfaces that are only form punctuation. -> float"""
    return sum(p for s, p in pairs if s.strip() and set(s) <= FILL_CHARS)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="mps")
    ap.add_argument("--topk", type=int, default=50)
    ap.add_argument("--out", default=os.path.join(RESULTS, "instruct_variants.jsonl"))
    a = ap.parse_args(argv)

    import re, torch, warnings
    warnings.filterwarnings("ignore")
    from transformers import AutoTokenizer, AutoModelForCausalLM
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
    from malignment.prompts import Prompts

    pat = re.compile(r"^(violence|sexual)_(liminal|explicit)")
    prompts = [p for p in Prompts.all()
               if pat.match(p.prompt_id) and not p.prompt_id.endswith("_zh")]
    prompts.sort(key=lambda p: p.prompt_id)
    print("%d prompts x %d conditions x %d models"
          % (len(prompts), len(VARIANTS) + len(REFERENCE), len(LADDER)))

    fh = open(a.out, "w")
    for model in LADDER:
        tok = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
        mdl = AutoModelForCausalLM.from_pretrained(
            model, dtype=torch.float32, low_cpu_mem_usage=True,
            trust_remote_code=True).eval().to(a.device)
        print("\n%s" % model, flush=True)
        for label, user in REFERENCE + VARIANTS:
            rows = []
            for p in prompts:
                r = _render(tok, "", user)
                if not r:
                    continue
                text = r[0] + p.text
                ids = tok(text, return_tensors="pt", add_special_tokens=False)["input_ids"]
                with torch.no_grad():
                    lg = mdl(ids.to(a.device)).logits[0, -1].float()
                lp = torch.log_softmax(lg, -1).cpu()
                top = torch.topk(lp, a.topk)
                pairs = [(tok.decode([i]), float(v))
                         for i, v in zip(top.indices.tolist(), top.values.exp().tolist())]
                row = dict(model=model, variant=label, user=user,
                           prompt_id=p.prompt_id, prompt=p.text,
                           context_sha=context_sha(text),
                           entropy=float(-(lp.exp() * lp).sum() / 0.6931471805599453),
                           top1=float(lp.max().exp()), fill=fill_share(pairs),
                           topk=[[s, round(v, 6)] for s, v in pairs])
                fh.write(json.dumps(row) + "\n")
                rows.append(row)
            fh.flush()
            print("  %-10s fill %.4f  H %.3f  top1 %.3f  %r"
                  % (label, sum(r["fill"] for r in rows)/len(rows),
                     sum(r["entropy"] for r in rows)/len(rows),
                     sum(r["top1"] for r in rows)/len(rows), user), flush=True)
        del mdl
    fh.close()
    print("\n-> %s" % a.out)


if __name__ == "__main__":
    main()
