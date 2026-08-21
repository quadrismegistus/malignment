"""Measure the three frame conditions on the selected cells.

    python .../scripts/run.py --device mps                 # this venv's models
    python .../scripts/run.py --device mps --venv-only .venv-tf457

One row per (model, prompt, condition) to `results/dist.jsonl`, plus the top-k
surfaces so a later reader can see the paradigm rather than only its statistics.

## IT SHARDS BY VENV, AND IT HAS TO

38 of 160 roster nodes need `.venv-tf457` and fail in `.venv` with
`tie_word_embeddings expected int, got bool`. That is a VENV fact, not a model
fact -- I once reported 8 models as having "unknown" prefillability when 6 of
them simply needed the other interpreter. So the runner asks
`scripts/venvs.py:venv_for(model_id)` and SKIPS any model that does not belong to
the interpreter it is currently running under, rather than trying and recording a
failure. Run it once per venv; the two passes append to the same file.

## WHAT IS RECORDED PER CONDITION

    entropy, top1, top-k surfaces with probabilities   the distribution itself
    js_vs_raw, overlap50                               distance from `raw`
    attested_mass                                      mass this condition puts
                                                       on the words twp v3
                                                       attested for this cell
    word_slot                                          does the top-1 token begin
                                                       a word (leading space or
                                                       start-of-word marker)

`attested_mass` is the only quantity that touches dario's population, since his
`reversed` is defined over word lists. `word_slot` is what separates `chat` from
`prefill` mechanically: measured on Llama-3.1-8B-Instruct, `chat`'s top token is
`'...'` and its next entries are fragments with no leading space, so there is no
word slot to have a paradigm in.

## REFUSALS, RECORDED NOT SILENT

A cell is refused, with its reason, when the tokenizer does not round-trip the
stem (transformers #45488 deletes every space on some repos and returns plausible
numbers on the wreckage) or when the built string does not actually contain the
stem. Both are silent otherwise, and both change what is being measured.

## DEVICE

Default cpu. `--device mps` is 4.9x faster here and was checked against cpu
rather than assumed -- 2.4e-05 max relative error over 50 passages, 0 token-count
mismatches -- but the bge pass found mps corrupting short-sequence embeddings, so
it is opt-in and the device is recorded on every row.
"""

import argparse, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), "results")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "scripts"))
from conditions import build, check, CONDITIONS, context_sha    # noqa: E402


#: **THE STORE THE TARGETS WERE CHOSEN FROM, NAMED DELIBERATELY.** Two tables
#: called `twp_words` exist on this daemon -- `malign_logits` at 95,180,535 rows
#: and `malignment` at 94,887,319 -- and `select.py` screened against the first.
#: Reading `attested` from the second would mean the word lists and the cell
#: selection describe different populations, which is a defect no output would
#: show. Set BEFORE importing `malignment.ch`, whose `DB` binds at import.
os.environ.setdefault("MALIGNMENT_CH_DB", "malign_logits")
sys.path.insert(0, REPO)
from malignment import ch                                        # noqa: E402

#: {(model, prompt): {surface: summed p}}, filled one MODEL at a time.
_ATT = {}


def prefetch(model, rule_version=3):
    """Every attested word for one model, in ONE query. -> n cells loaded

    **THIS WAS A SUBPROCESS PER CELL.** The old version shelled out to
    `clickhouse client` once per (model, prompt) behind a cache of size one --
    1,339 process launches for this sweep -- and it carried all three of the
    defects `malignment/ch.py` was written to retire:

      it split stdout on TAB and kept rows only `if len(f) == 2`, so any prompt
      containing a tab or newline was dropped with no count and no cause;

      it wrapped the whole thing in `except Exception: pass`, so a daemon that
      was down produced an empty dict, `attested_mass=None` on every row, and a
      finished-looking file that had measured nothing against twp.

    `ch.query` raises on a line it cannot parse and returns typed dicts, so both
    disappear rather than being handled. The query filters by MODEL ONLY: model
    ids are bare ASCII and interpolate safely, whereas the prompts do not, and
    a per-model pull is ~100 rows per cell over ~2,900 cells -- small enough
    that filtering to the targets would buy nothing and cost an escaping rule.
    """
    #: ONE MODEL RESIDENT AT A TIME. 24 models x ~2,900 cells x ~100 words is
    #: ~7M dict entries if this accumulates, for a lookup that is only ever
    #: asked about the model currently loaded.
    _ATT.clear()
    rows = ch.query(
        "SELECT prompt, word, sum(p) AS m FROM {db}.twp_words "
        "WHERE rule_version = %d AND model = '%s' GROUP BY prompt, word"
        % (rule_version, model.replace("'", "''")))
    #: **A JSON `null` HERE IS NaN, NOT A MISSING VALUE.** `p` is NOT NULL for
    #: all 95,180,535 rows at rule_version=3 -- checked -- but two rows carry
    #: NaN (one each in Qwen/Qwen3-8B and Qwen3-8B-Base), and ClickHouse
    #: serialises NaN to `null` in JSONEachRow, so `float(r["m"])` raised. The
    #: rows are DROPPED and COUNTED rather than coerced to 0.0: a zero would
    #: enter `attested_mass` as a real observation of no mass.
    seen, bad = set(), 0
    for r in rows:
        if r["m"] is None:
            bad += 1
            continue
        key = (model, r["prompt"])
        _ATT.setdefault(key, {})[r["word"]] = float(r["m"])
        seen.add(key)
    if bad:
        print("    NaN mass on %d (prompt, word) group(s) -- dropped" % bad,
              flush=True)
    return len(seen)


def attested(model, prompt):
    """The words twp recorded for this cell, {surface: p}, best first. -> dict"""
    d = _ATT.get((model, prompt), {})
    return dict(sorted(d.items(), key=lambda kv: -kv[1])[:200])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default=os.path.join(RESULTS, "targets.json"))
    ap.add_argument("--out", default=os.path.join(RESULTS, "dist.jsonl"))
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--topk", type=int, default=50)
    ap.add_argument("--venv-only", help="only models whose venv_for basename matches")
    ap.add_argument("--limit-models", type=int)
    a = ap.parse_args(argv)

    import numpy as np, torch, warnings
    import torch.nn.functional as F
    warnings.filterwarnings("ignore")
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from venvs import venv_for

    tg = json.load(open(a.targets))
    by = collections.defaultdict(list)
    for t in tg["targets"]:
        by[t["model"]].append(t)

    here = a.venv_only or os.path.basename(os.path.dirname(os.path.dirname(sys.executable)))
    mine = [m for m in sorted(by) if os.path.basename(venv_for(m)) == here]
    if a.limit_models:
        mine = mine[:a.limit_models]
    print("targets %d cells / %d models | this venv (%s): %d models"
          % (len(tg["targets"]), len(by), here, len(mine)))

    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try:
                d = json.loads(line)
                done.add((d["model"], d["prompt"], d["condition"]))
            except Exception:
                pass
    print("already recorded: %d rows" % len(done))

    n_ok = n_ref = 0
    with open(a.out, "a") as fh:
        for mi, model in enumerate(mine, 1):
            cells = [c for c in by[model]
                     if any((model, c["prompt"], k) not in done for k in CONDITIONS)]
            if not cells:
                print("[%d/%d] %s -- complete" % (mi, len(mine), model)); continue
            print("[%d/%d] %s  %d cells" % (mi, len(mine), model, len(cells)), flush=True)
            #: BEFORE the weights, so a daemon that is down costs a query and
            #: not a two-minute fp32 load, and so it RAISES rather than quietly
            #: writing `attested_mass=None` across the model.
            n_att = prefetch(model, tg.get("rule_version", 3))
            print("    attested: %d cells from %s.twp_words"
                  % (n_att, ch.DB), flush=True)
            try:
                tok = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
                mdl = AutoModelForCausalLM.from_pretrained(
                    model, dtype=torch.float32, low_cpu_mem_usage=True,
                    trust_remote_code=True).eval().to(a.device)
            except Exception as e:
                fh.write(json.dumps(dict(model=model, prompt=None, condition=None,
                                         refused="load: %s" % str(e)[:200])) + "\n")
                print("    LOAD FAILED: %s" % str(e)[:120]); continue

            for c in cells:
                stem = c["prompt"]
                bad = check(tok, stem)
                if bad:
                    fh.write(json.dumps(dict(model=model, prompt=stem, condition=None,
                                             stratum=c["stratum"], refused=bad)) + "\n")
                    n_ref += 1; continue
                att = attested(model, stem)
                built, lps = build(tok, stem), {}
                for cond, (text, add_special, sys_ok) in built.items():
                    ids = tok(text, return_tensors="pt",
                              add_special_tokens=add_special)["input_ids"]
                    with torch.no_grad():
                        lg = mdl(ids.to(a.device)).logits[0, -1].float()
                    lps[cond] = torch.log_softmax(lg, -1).cpu()
                for cond, lp in lps.items():
                    top = torch.topk(lp, a.topk)
                    surf = [tok.decode([i]) for i in top.indices.tolist()]
                    probs = [float(x) for x in top.values.exp().tolist()]
                    row = dict(
                        model=model, prompt=stem, condition=cond,
                        stratum=c["stratum"], device=a.device,
                        prompt_id=c.get("prompt_id"),
                        sys_supported=built[cond][2],
                        #: THE IDENTITY OF THE MEASUREMENT IS THE RENDERED
                        #: CONTEXT, NOT THE STEM (@malign [6494]). Two
                        #: conditions that collapse to the same string on a
                        #: template with no default are then FINDABLE, instead
                        #: of being reported as a null difference between them.
                        context_sha=context_sha(built[cond][0]),
                        n_prompt_tokens=int(tok(built[cond][0], add_special_tokens=built[cond][1],
                                                return_tensors="pt")["input_ids"].shape[1]),
                        entropy=float(-(lp.exp() * lp).sum() / np.log(2)),
                        top1=float(lp.max().exp()),
                        #: a WORD SLOT is a top token that begins a word. Without
                        #: it there is no paradigm to compare, only fragments.
                        word_slot=bool(surf and (surf[0][:1] in (" ", "▁")
                                                 or surf[0][:1].isupper())),
                        topk=[[s, round(p, 6)] for s, p in zip(surf, probs)],
                        attested_mass=round(float(sum(
                            float(lp[tok(w if w.startswith(" ") else " " + w,
                                         add_special_tokens=False)["input_ids"][0]].exp())
                            for w in list(att)[:40]
                            if tok(w if w.startswith(" ") else " " + w,
                                   add_special_tokens=False)["input_ids"])), 6)
                        if att else None,
                        n_attested=len(att))
                    if cond != "raw" and "raw" in lps:
                        r_, o_ = lps["raw"], lp
                        mix = torch.logsumexp(torch.stack([r_, o_]) - np.log(2), 0)
                        row["js_vs_raw"] = float(
                            0.5 * (F.kl_div(mix, r_, log_target=True, reduction="sum")
                                   + F.kl_div(mix, o_, log_target=True, reduction="sum")))
                        row["overlap50"] = len(set(torch.topk(r_, 50).indices.tolist())
                                               & set(torch.topk(o_, 50).indices.tolist()))
                    fh.write(json.dumps(row) + "\n")
                    n_ok += 1
                fh.flush()
            del mdl
    print("\nwrote %d condition-rows, refused %d cells -> %s" % (n_ok, n_ref, a.out))


if __name__ == "__main__":
    main()
