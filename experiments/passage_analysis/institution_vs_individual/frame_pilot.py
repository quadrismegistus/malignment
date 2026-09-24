"""Frame pilot: code the eight aligned models' accidental RAW passages, and decompose.

    python -u frame_pilot.py --plan       # count the population, code nothing
    python -u frame_pilot.py --run        # code -> $MALIGNMENT_DATA/.../coded_frame_pilot.jsonl
    python -u frame_pilot.py --analyse    # -> results/frame_pilot.md

Registration: `frame_pilot.md`, committed before any passage here was coded.

The coder, its rendering and the span check are `task.py`'s, called exactly as
`run_regen.py` calls them. The filter and outcomes are `analyse_regen.py`'s. This
file only chooses a different population: aligned passages in the `raw` frame,
which `run_regen.population()` exists to exclude.
"""
import argparse, collections, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import analyse_regen as A  # noqa: E402  SRC, keep, outcomes, sign
import run_regen as R      # noqa: E402  DESIGN, BY_PROMPT
import task as T           # noqa: E402

OUT = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_frame_pilot.jsonl")
RESULT = os.path.join(HERE, "results", "frame_pilot.md")
#: the eight aligned models the first fleet silently ran RAW (README, "Frame and decoder")
EIGHT = ["LLM360/AmberSafe", "PKU-Alignment/beaver-7b-v1.0",
         "ContextualAI/archangel_sft-dpo_pythia2-8b", "lomahony/eleuther-pythia6.9b-hh-dpo",
         "togethercomputer/RedPajama-INCITE-7B-Chat", "BAAI/AquilaChat2-7B",
         "bigscience/bloomz-7b1", "m-a-p/CT-LLM-SFT-DPO"]
OUTCOMES = ["channel", "outward", "authority", "move_voice_direct"]


def population():
    from malignment import roster
    from malignment.checkpoint import Checkpoint
    eps, _ = roster.endpoints()
    base_of = {end: base for base, end in eps.items()}
    rows = []
    for m in EIGHT:
        assert m in base_of, "%s is not a declared endpoint" % m
        seen = set()
        for st in Checkpoint(m).gen_stashes():
            for v in st.values():
                hit = R.BY_PROMPT.get(v.get("prompt"))
                if not hit or (v.get("decoder") or {}).get("max_new_tokens") != 256:
                    continue
                #: the accidental cell, and only it: raw frame, no template, not the fixed render
                if v.get("frame") != "raw" or v.get("template") or v.get("render") == "ids_v2":
                    continue
                key = (hit[0], v.get("seed"))
                if key in seen:
                    continue
                seen.add(key)
                d = hit[1]
                rows.append({"lineage": base_of[m], "arm": "aligned_raw", "model": m, "key": hit[0],
                             "scenario": d["scenario"], "side": d["side"], "prompt": d["prompt"],
                             "seed": v.get("seed"), "frame": v.get("frame"), "finish": v.get("finish"),
                             "engine_version": v.get("engine_version"), "text": v.get("text") or ""})
    per = collections.Counter(r["model"] for r in rows)
    #: the registration's population, categorically: every model, 360 each
    assert set(per) == set(EIGHT) and set(per.values()) == {360}, dict(per)
    return rows


def run(workers):
    rows = population()
    prompts = [T.render(r["prompt"], r["text"], R.DESIGN[r["key"]]["speaker"],
                        R.DESIGN[r["key"]]["counterparty"]) for r in rows]
    errors = {}
    res = T.task().map(prompts, num_workers=workers, errors=errors)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        for r, x in zip(rows, res):
            r = dict(r, coded=x.model_dump() if x else None)
            if x:
                r["spans_ok"], r["spans_total"], _ = T.check_spans(r["text"], x)
            fh.write(json.dumps(r) + "\n")
    print("coded %d of %d; failures %d -> %s" % (len(rows) - len(errors), len(rows), len(errors), OUT))


def did(c, l, a, b, n):
    """(individual change) - (institution change), arm a -> arm b, outcome n. None if a cell is empty."""
    v = [c.get((l, arm, s, n)) for arm in (a, b) for s in ("individual", "institution")]
    if not all(v):
        return None
    ai, as_, bi, bs = (np.mean(x) for x in v)
    return (bi - ai) - (bs - as_)


def analyse():
    main = [json.loads(l) for l in open(A.SRC)]
    pilot = [json.loads(l) for l in open(OUT)]
    lineages = {r["lineage"] for r in pilot}
    rows = [r for r in main if r["lineage"] in lineages] + pilot
    form = collections.Counter()
    c = collections.defaultdict(list)
    for r in rows:
        if not r.get("coded"):
            continue
        arm = {"base": "base", "aligned": "aligned_chat", "aligned_raw": "aligned_raw"}[r["arm"]]
        form[(r["lineage"], arm, r["coded"]["form"])] += 1
        form[(r["lineage"], arm, "_n")] += 1
        if A.keep(r["coded"]):
            o = A.outcomes(r["coded"])
            for n in OUTCOMES:
                c[(r["lineage"], arm, r["side"], n)].append(o[n])
    name = {r["lineage"]: r["model"].split("/")[-1] for r in pilot}
    L = ["# Frame pilot: decomposition of the base-to-aligned shift", "",
         "Registration `frame_pilot.md`; producer `frame_pilot.py`. Aligned-raw passages: %d coded of %d." % (
             sum(1 for r in pilot if r.get("coded")), len(pilot)), ""]

    L += ["## Form: share of passages in advice form", "",
          "| lineage (aligned model) | base raw | aligned raw | aligned chat |", "|---|---|---|---|"]
    e1 = []
    for l in sorted(lineages, key=lambda x: name[x]):
        sh = {a: (form[(l, a, "advice")] / form[(l, a, "_n")] if form[(l, a, "_n")] else None)
              for a in ("base", "aligned_raw", "aligned_chat")}
        L.append("| %s | %s | %s | %s |" % (name[l], *("%.2f" % sh[a] if sh[a] is not None else "--"
                                                      for a in ("base", "aligned_raw", "aligned_chat"))))
        if sh["aligned_chat"] is not None:
            e1.append(sh["aligned_raw"] < sh["aligned_chat"])
    L += ["", "**E1** (aligned-raw writes advice less often than aligned-chat, declared >= 5 of 6): %d of %d -> %s" % (
        sum(e1), len(e1), "MET" if sum(e1) >= 5 else "NOT MET"), ""]

    for n in OUTCOMES:
        L += ["## %s%s" % (n, " (PRIMARY)" if n == "channel" else ""), "",
              "| lineage | weights (raw -> raw) | frame (raw -> chat, aligned) | total (base raw -> aligned chat) |",
              "|---|---|---|---|"]
        W_, F_, T_ = [], [], []
        for l in sorted(lineages, key=lambda x: name[x]):
            w = did(c, l, "base", "aligned_raw", n)
            f = did(c, l, "aligned_raw", "aligned_chat", n)
            t = did(c, l, "base", "aligned_chat", n)
            if w is not None and f is not None and t is not None:
                assert abs((w + f) - t) < 1e-12, "decomposition does not add up for %s" % l
            fmt = lambda x: "%+.3f" % x if x is not None else "--"
            L.append("| %s | %s | %s | %s |" % (name[l], fmt(w), fmt(f), fmt(t)))
            if w is not None:
                W_.append(w)
            if f is not None and w is not None:
                F_.append((w, f))
            if t is not None:
                T_.append(t)
        up, dn, p = A.sign(W_)
        L += ["", "weights > 0 in %d of %d lineages (sign p %.3g); median weights %+.3f." % (up, len(W_), p, np.median(W_))]
        if F_:
            fd = sum(1 for w, f in F_ if f > w)
            L.append("frame > weights in %d of %d three-cell lineages; median frame %+.3f." % (
                fd, len(F_), np.median([f for _, f in F_])))
        if n == "channel":
            v = ("frame-dominated" if fd >= 5 else "weights-dominated" if len(F_) - fd >= 5 else "mixed")
            L += ["", "**E2** (channel weights > 0, declared >= 6 of 8): %d of %d -> %s" % (
                up, len(W_), "MET" if up >= 6 else "NOT MET"),
                "**Decomposition verdict (declared rule, 5 of 6):** %s." % v]
        L.append("")
    L += ["Cells: mean of the outcome over kept passages (continuation or advice, coherent, perspective kept).",
          "Each DiD = (individual change) - (institution change). total = weights + frame exactly (asserted).",
          "Six lineages for the decomposition, eight for weights: descriptive; see the registration's limits."]
    open(RESULT, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    if a.plan or not (a.run or a.analyse):
        rows = population()
        print("aligned-raw passages %d over %d models (360 each), engine %s"
              % (len(rows), len({r["model"] for r in rows}), sorted({r["engine_version"] for r in rows})))
    if a.run:
        run(a.workers)
    if a.analyse:
        analyse()


if __name__ == "__main__":
    main()
