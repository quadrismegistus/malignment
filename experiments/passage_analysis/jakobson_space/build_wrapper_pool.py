"""The wrapper confound: does "Continue this text:" move drift and surprisal?

    python .../build_wrapper_pool.py
    python .../run_wrapper.py            # scores it on both axes

Frontier models cannot be compared to open-weight ones on these axes, because a
chatbot has no completion endpoint and has to be asked to continue. Measured in
the archive: the same model given the bare stem answers ABOUT the text --
`"This sentence is incomplete. Here are some common ways it might continue:"` --
and given the wrapper produces prose. That is not a formatting difference, it is
a different act.

The confound cannot be designed away, because a base model cannot take the
wrapper at all (hand it "Continue this text:" and it continues that string). But
it CAN be estimated, on models where both conditions exist -- and they do.

## THE DESIGN WAS ALREADY RUN, and nobody put it on the axes

`data/f37_stash_generations.jsonl` carries six aligned models under a `:continue`
suffix, meaning `apply_chat_template([{user: "Continue this text: " + prompt}])`,
alongside their ordinary raw generations. Verified crossed, not ad hoc:

    all six share the SAME 61 continue prompts (identical sets)
    59 of those also have raw generations from the same model
    raw depth ~5,500 per model against 183 continue

So every continue passage has many raw siblings on its own prompt and model. The
contrast is paired within (model, prompt) rather than pooled, and the unit for
the headline is the MODEL (n=6).

BLT coverage of the `:continue` passages was 0 of 480 sampled -- the fleets
scored the unforced generation corpus, and these were never in it.

## WHAT THIS CAN AND CANNOT SUPPORT

It estimates the wrapper's effect at ~80 words (roughly 400-500 bytes). That is
the SHORT end, where the base/aligned surprisal gap is steepest -- measured
-0.3466 at 600-800 bytes against -0.1773 at 1200-1400 -- so the delta here should
not be transferred to 193-word passages without saying so.

n=6 models is a sign test with a floor of 2/2^6 = 0.031. It cannot produce a
small p-value. It can produce an effect SIZE, which is what a confound estimate
needs.
"""

import argparse, collections, hashlib, json, os, random

ARCHIVE = "/Users/rj416/github/malign-logits/data/f37_stash_generations.jsonl"
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
#: DELIBERATELY NOT under jakobson_space/ -- this is a different question with a
#: different population, and mixing it into the anchor's directory would invite a
#: later reader to collate the two (RH: save results somewhere else).
OUT = os.path.join(DATA, "wrapper_confound", "wrapper_pool.jsonl")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-per-cell", type=int, default=10,
                    help="raw draws sampled per (model, prompt); continue arm is taken whole")
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)

    cont = collections.defaultdict(lambda: collections.defaultdict(list))
    raw = collections.defaultdict(lambda: collections.defaultdict(list))
    for line in open(ARCHIVE):
        d = json.loads(line)
        m = d["model"]
        if m.endswith(":continue"):
            cont[m[:-len(":continue")]][d["prompt"]].append(d)
        else:
            raw[m][d["prompt"]].append(d)

    models = sorted(cont)
    rows = []
    for m in models:
        shared = sorted(set(cont[m]) & set(raw.get(m, {})))
        for p in shared:
            for arm, pool, take in (("continue", cont[m][p], None),
                                    ("raw", raw[m][p], a.raw_per_cell)):
                items = list(pool)
                if take is not None and len(items) > take:
                    items = rng.sample(items, take)
                for d in items:
                    t = d["text"] or ""
                    if len(t.split()) < 20:
                        continue          # too short for a drift path
                    rows.append(dict(
                        id="%s-%s" % (arm, hashlib.sha256(
                            (m + p + t).encode()).hexdigest()[:12]),
                        corpus=arm, model=m, prompt=p, idx=d.get("idx"),
                        temp=d.get("temp"), text=t))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    seen, keep = set(), []
    for r in rows:
        if r["id"] in seen:
            continue
        seen.add(r["id"]); keep.append(r)
    with open(a.out, "w") as fh:
        for r in keep:
            fh.write(json.dumps(r) + "\n")

    print("%-46s %9s %9s %9s" % ("model", "continue", "raw", "prompts"))
    by = collections.defaultdict(lambda: collections.Counter())
    pr = collections.defaultdict(set)
    for r in keep:
        by[r["model"]][r["corpus"]] += 1
        pr[r["model"]].add(r["prompt"])
    for m in models:
        print("%-46s %9d %9d %9d"
              % (m, by[m]["continue"], by[m]["raw"], len(pr[m])))
    import statistics as st
    w = [len(r["text"].split()) for r in keep]
    b = [len(r["text"].encode()) for r in keep]
    print("\n%d passages | words median %d | bytes median %d"
          % (len(keep), st.median(w), st.median(b)))
    print("-> %s" % a.out)


if __name__ == "__main__":
    main()
