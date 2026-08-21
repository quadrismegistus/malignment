"""Both axes on one table: deepseek surprisal x bge drift, models vs human corpora.

    python .../two_axes.py                 # the summary
    python .../two_axes.py --csv OUT.csv   # and the joined rows

## THE TWO AXES COME FROM DIFFERENT PRODUCERS AND JOIN ON DIFFERENT KEYS

    surprisal   ref_pool/deepseek/ref_shard00.{jsonl,f32}   13,124 passages,
                deepseek-llm-7b-base, one model, one device, one pass
    drift       human : jakobson_space/bge_human/drift.jsonl   by `anchor_id`
                model : passages_std.parquet                   by `text_sha`

Both joins are checked and reported rather than assumed: human 2,975 of 3,000
(the 25 absent are passages under 2 sentences, where drift does not exist),
model 5,687 of 5,687.

## SURPRISAL IS TAKEN AT M = 200 TOKENS AND DRIFT IS NOT CONTROLLED

Different units, different reasons, and neither is a default:

  * **Surprisal at M=200 tokens.** deepseek sees tokens, the sidecar IS
    per-token surprisal, so the first M predictions are `sur[row:row+M]`.
    M=200 is the largest prefix at which EVERY human corpus retains 100% of its
    500 passages -- at 220 waking narrative is already 54% and length-selected.
  * **Drift uncontrolled.** `mean_drift` and `mean_pairwise` are the length-free
    pair (r with n_sents -0.126 and -0.030, against +0.941 for `path_length`),
    so a length control would cost sentences and buy nothing. The accumulating
    metrics are NOT reported here for exactly that reason.

Controlling drift on M=200 tokens would be worse than leaving it: 200 tokens
lands mid-sentence, so a partial sentence is either dropped (losing a step) or
embedded as a fragment (changing what bge sees), and a fixed token budget buys a
DIFFERENT number of sentences per corpus because sentence length varies with
prose density -- the same confound relocated.

## THE UNIT FOR AN ARM CLAIM IS THE MODEL

Passages within a model are not independent and models within a lineage share a
base. Model rows are medians of per-model medians. Human rows are over passages,
because a corpus has no such nesting.
"""

import argparse, collections, csv, json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

M_TOKENS = 200
CORPORA = ("literary_criticism", "c20_fiction", "arxiv_abstracts",
           "philosophy", "dreams", "waking_narrative")
MIN_PASSAGES_PER_MODEL = 5


def build():
    """-> [row], each with both axes. Reports what each join lost."""
    import numpy as np
    import pyarrow.parquet as pq

    pool = {}
    for line in open(os.path.join(DATA, "ref_pool", "ref_pool.jsonl")):
        r = json.loads(line)
        pool[r["id"]] = r
    ref = [json.loads(l) for l in
           open(os.path.join(DATA, "ref_pool", "deepseek", "ref_shard00.jsonl"))]
    sur = np.fromfile(os.path.join(DATA, "ref_pool", "deepseek", "ref_shard00.f32"),
                      dtype=np.float32)

    hd = {}
    for line in open(os.path.join(DATA, "jakobson_space", "bge_human", "drift.jsonl")):
        r = json.loads(line)
        hd[r["id"]] = r
    t = pq.read_table(os.path.join(DATA, "jakobson_space", "passages_std.parquet"),
                      columns=["text_sha", "mean_drift", "mean_pairwise",
                               "n_sents", "model", "arm"])
    d = {c: t.column(c).to_pylist() for c in t.column_names}
    md = {s: i for i, s in enumerate(d["text_sha"])}

    out, lost = [], collections.Counter()
    for r in ref:
        p = pool.get(r["id"])
        if not p:
            lost["no ref_pool row"] += 1
            continue
        if p["pool"] == "wrapper":
            continue                      #: a different question; see wrapper_confound
        #: surprisal FIRST, so a passage too short for the prefix is dropped for
        #: a stated reason rather than by a silent NaN downstream.
        if r["n"] < M_TOKENS:
            lost["under %d tokens" % M_TOKENS] += 1
            continue
        bits = float(sur[r["row"]:r["row"] + M_TOKENS].mean())

        if p["pool"] == "human_anchor":
            dr = hd.get(p.get("anchor_id"))
            if not dr:
                lost["human: no drift row"] += 1
                continue
            group, model, arm = p["corpus"], None, "human"
            mdr, mpw, ns = dr["mean_drift"], dr["mean_pairwise"], dr["n_sents"]
        else:
            i = md.get(r["text_sha"])
            if i is None:
                lost["model: no parquet row"] += 1
                continue
            if d["mean_drift"][i] is None:
                lost["model: drift undefined"] += 1
                continue
            group, model, arm = p.get("model"), p.get("model"), p.get("arm")
            mdr, mpw, ns = (d["mean_drift"][i], d["mean_pairwise"][i], d["n_sents"][i])

        out.append(dict(id=r["id"], pool=p["pool"], group=group, model=model,
                        arm=arm, bits_per_token=round(bits, 6),
                        mean_drift=mdr, mean_pairwise=mpw, n_sents=ns,
                        n_tokens_total=r["n"], n_bytes=r["n_bytes"]))
    return out, lost


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    a = ap.parse_args(argv)
    from malignment import roster
    rows, lost = build()
    print("joined rows: %d" % len(rows))
    for k, v in sorted(lost.items()):
        print("  dropped %-28s %d" % (k, v))

    aligned, bases = roster.population("aligned"), roster.population("bases")
    per = collections.defaultdict(list)
    for r in rows:
        if r["pool"] == "model_narrative":
            per[r["model"]].append(r)
    tab = []
    for arm, s in (("MODEL base", bases), ("MODEL aligned", aligned)):
        mods = [(statistics.median(x["bits_per_token"] for x in v),
                 statistics.median(x["mean_drift"] for x in v))
                for m, v in per.items()
                if m in s and len(v) >= MIN_PASSAGES_PER_MODEL]
        if mods:
            tab.append((arm, statistics.median(b for b, _ in mods),
                        statistics.median(dd for _, dd in mods), len(mods), "models"))
    for c in CORPORA:
        v = [r for r in rows if r["group"] == c]
        if v:
            tab.append(("human " + c,
                        statistics.median(x["bits_per_token"] for x in v),
                        statistics.median(x["mean_drift"] for x in v),
                        len(v), "passages"))

    print("\nBOTH AXES   surprisal at M=%d tokens, drift uncontrolled\n" % M_TOKENS)
    print("%-26s %12s %11s %8s %s" % ("", "bits/token", "mean_drift", "n", "unit"))
    for name, b, dd, n, u in sorted(tab, key=lambda x: -x[1]):
        print("%-26s %12.4f %11.4f %8d %s" % (name, b, dd, n, u))

    if a.csv:
        cols = ["id", "pool", "group", "model", "arm", "bits_per_token",
                "mean_drift", "mean_pairwise", "n_sents", "n_tokens_total", "n_bytes"]
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print("\n-> %s  (%d rows)" % (a.csv, len(rows)))


if __name__ == "__main__":
    main()
