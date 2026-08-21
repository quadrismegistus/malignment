"""Is `Hi.` a representative of a CLASS, or is the frame resting on one string?

    python .../scripts/taskless_class.py --models allenai/Olmo-3-7B-Instruct-DPO ...

The templated frame this instrument would report is `presence`: an empty system
and the user turn set to `Hi.`. Everything establishing that frame rests on that
one string. The boundaries on either side are measured --

    a SPACE does not work         Olmo-3-DPO fill 0.526 against bare's 0.530
    an INSTRUCTION overshoots     a task, and its own five-member family whose
                                  members disagree about the argmax

-- but between them there is exactly one tested point, and "a contentful,
taskless turn restores the word paradigm" is a claim about a class that has been
sampled once.

## THE FOURTH STRING IS THE TEST

    Hi.                    the current representative
    Hello.                 a second greeting, should be near-identical
    Good morning.          longer, still phatic
    The weather is nice.   contentful, taskless, NOT a greeting

The first three are all phatic openers, so if only they cluster, the class is
narrower than "contentful and taskless" and the frame carries a conversational-
role assumption nobody declared. `The weather is nice.` is the discriminating
case: it asks for nothing and opens nothing, so it belongs to the class if the
class is real and does not if the class is really "greeting".

## THE REFERENCES ARE IN THE SAME RUN, NOT QUOTED FROM ANOTHER ONE

`empty`, `space` and one instruction are re-measured here rather than carried
over, so the comparison does not straddle two runs, two dtypes and two devices.
A number that has to be quoted from elsewhere to be interpreted is a number whose
population nobody can check.
"""

import argparse, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), "results")
sys.path.insert(0, HERE)
from conditions import _render, context_sha                          # noqa: E402

TURNS = [
    ("empty",    "",                     "reference: fails"),
    ("space",    " ",                    "reference: fails"),
    ("hi",       "Hi.",                  "taskless"),
    ("hello",    "Hello.",               "taskless"),
    ("morning",  "Good morning.",        "taskless"),
    ("weather",  "The weather is nice.", "taskless, NOT a greeting"),
    ("instruct", "Continue the text.",   "reference: overshoots"),
]

FILL_CHARS = set("_-–—=.·•*~^ ")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--topk", type=int, default=50)
    ap.add_argument("--out", default=os.path.join(RESULTS, "taskless_class.jsonl"))
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

    fh = open(a.out, "a")
    for mid in a.models:
        try:
            tok = AutoTokenizer.from_pretrained(mid, trust_remote_code=True)
            mdl = AutoModelForCausalLM.from_pretrained(
                mid, dtype=torch.float32, low_cpu_mem_usage=True,
                trust_remote_code=True).eval().to(a.device)
        except Exception as e:
            print("  LOAD FAILED %s: %s" % (mid, str(e)[:110])); continue
        print("\n%s" % mid, flush=True)
        print("  %-9s %8s %8s %8s   %s" % ("turn", "H", "fill", "top1", "user string"))
        seen = {}
        for name, user, note in TURNS:
            rows = []
            for p in prompts:
                r = _render(tok, "", user)
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
                sha = context_sha(text)
                row = dict(model=mid, turn=name, user=user, note=note,
                           prompt_id=p.prompt_id, prompt=p.text, context_sha=sha,
                           entropy=float(-(lp.exp()*lp).sum() / 0.6931471805599453),
                           top1=float(lp.max().exp()),
                           fill=sum(v for t, v in pairs
                                    if t.strip() and set(t) <= FILL_CHARS),
                           topk=[[t, round(v, 6)] for t, v in pairs])
                fh.write(json.dumps(row) + "\n")
                rows.append(row)
            fh.flush()
            if not rows:
                continue
            dup = seen.get(rows[0]["context_sha"])
            seen.setdefault(rows[0]["context_sha"], name)
            print("  %-9s %8.3f %8.4f %8.3f   %s%r"
                  % (name, statistics.mean(r["entropy"] for r in rows),
                     statistics.mean(r["fill"] for r in rows),
                     statistics.mean(r["top1"] for r in rows),
                     ("[RENDERS AS %s] " % dup) if dup else "", user))
        del mdl
    fh.close()
    print("\n-> %s" % a.out)


if __name__ == "__main__":
    main()
