"""TEMPLATE_ARM's coding draw, passC's rule with RH's 40-word amendment (2026-09-25).

    python select_for_coding.py            # plan
    python select_for_coding.py --write    # selection parquet + batch files

Per (model, arm) cell, f11 stems only (Figure 5's population):
  1. STRIP a leading assistant preamble in the continue arm, one declared regex
     (PREAMBLE: a first line opening "Sure/Certainly/Of course/Here's/Here is/
     Absolutely/Okay/OK" and ending in ":" within 160 chars). Measured before this
     rule was written: 525 of 79,700 continue passages (0.7%), almost all MiniCPM5-1B;
     0 in every other arm. `stripped` is carried on every row.
  2. KEEP passages of >= 40 words after the strip (RH: "only 40+"); shorter ones can
     never be placed by the Scorer, so coding them buys nothing.
  3. RANK by passC's classifier (triage.py, recovered verbatim) and take the TOP 200,
     or all of them where fewer than 200 qualify. The eligible count per cell goes
     in the survival table, so a thin cell is visible rather than padded.
Cells whose generation is incomplete are left out and listed.

Batches: 45 passages per file, {id: {f: stem, c: continuation}} -- passC's format.
The coder sees the STEM as the fragment in every arm; frame and arm are not shown.
"""
import argparse, hashlib, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
SRC = os.path.join(DATA, "template_arm", "passages.parquet")
OUT = os.path.join(DATA, "template_arm", "coding")
PREAMBLE = re.compile(r"^\s*(sure|certainly|of course|here'?s|here is|absolutely|okay|ok)\b[^\n]{0,160}?:\s*\n", re.I)
N_TOP, BATCH, MIN_WORDS = 200, 45, 40
FULL = {"base": 2000, "raw": 2000, "prefill": 2000, "continue": 2000}


def pid(m, arm, stem, i):
    return "t" + hashlib.sha256(("%s|%s|%s|%d" % (m, arm, stem, i)).encode()).hexdigest()[:11]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    import pyarrow as pa, pyarrow.parquet as pq, collections
    t = pq.read_table(SRC).to_pydict()
    cells = collections.defaultdict(list)
    for j in range(len(t["model"])):
        if t["set"][j] != "f11":
            continue
        cells[(t["model"][j], t["arm"][j])].append(j)
    import triage
    clf = None
    sel, survival, skipped = [], [], []
    for (m, arm), js in sorted(cells.items()):
        if len(js) < FULL[arm]:
            skipped.append((m, arm, len(js)))
            continue
        rows = []
        for j in js:
            x = t["text"][j]; st = False
            if arm == "continue":
                mm = PREAMBLE.match(x)
                if mm:
                    x, st = x[mm.end():], True
            if len(x.split()) >= MIN_WORDS:
                rows.append((j, x, st))
        survival.append(dict(model=m, base=t["base"][js[0]], arm=arm, generated=len(js), ge40=len(rows),
                             stripped=sum(r[2] for r in js and rows)))
        if not rows:
            continue
        if clf is None:
            clf = triage.train()
        sc = clf.predict_proba([r[1] for r in rows])[:, 1]
        order = np.argsort(-sc)[:N_TOP]
        for k in order:
            j, x, st = rows[k]
            sel.append(dict(id=pid(m, arm, t["stem"][j], t["sample_idx"][j]), model=m, base=t["base"][j], arm=arm,
                            stem=t["stem"][j], sample_idx=t["sample_idx"][j], text=x, stripped=st,
                            n_words=len(x.split()), score=float(sc[k])))
    print("cells coded %d | skipped (incomplete) %d: %s" % (len(survival), len(skipped), skipped))
    print("passages selected %d | cells under 200 eligible: %d" % (len(sel), sum(s["ge40"] < N_TOP for s in survival)))
    for s in sorted(survival, key=lambda s: s["ge40"])[:12]:
        print("   thin: %-40s %-9s ge40 %4d" % (s["model"].split("/")[-1], s["arm"], s["ge40"]))
    if not a.write:
        return
    os.makedirs(os.path.join(OUT, "batches"), exist_ok=True)
    pq.write_table(pa.Table.from_pylist(sel), os.path.join(OUT, "selection.parquet"), compression="zstd")
    pq.write_table(pa.Table.from_pylist(survival), os.path.join(OUT, "survival_generation.parquet"))
    import random
    order = list(range(len(sel))); random.Random(20260925).shuffle(order)   #: mixed batches: arms and models interleaved
    batches = []
    for b in range(0, len(order), BATCH):
        ids = [sel[k]["id"] for k in order[b:b + BATCH]]
        fn = os.path.join(OUT, "batches", "ta-%04d.json" % (b // BATCH))
        json.dump({sel[k]["id"]: {"f": sel[k]["stem"], "c": sel[k]["text"]} for k in order[b:b + BATCH]},
                  open(fn, "w"), ensure_ascii=False)
        batches.append({"file": fn, "ids": ids})
    json.dump(batches, open(os.path.join(OUT, "batches.json"), "w"))
    print("wrote %d batches -> %s" % (len(batches), OUT))


if __name__ == "__main__":
    main()
