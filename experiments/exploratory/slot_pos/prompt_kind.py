"""Each prompt's dominant charge KIND, mass-weighted. -> results/prompt_kind_en.csv

    python -u prompt_kind.py

RH, 2026-09-23: stratify by `charge.py` kind, "mass weighted most frequent per
prompt". A word's kind is `charge.kinds(prompt)[word]`, the modal kind of that
word over the 50 lineage cells (SEXUAL, VIOLENT, DEGRADING, COERCIVE, ILLICIT,
OTHER, NONE). Mass is the BASE side, taken per lineage from `words_long_v4` and
medianed over lineages, as in `run.py`. Grouping stays on the base side.

Two columns, because NONE takes most of the mass on most prompts:

    kind_base        argmax over ALL kinds, NONE included, and its share
    kind_charged     argmax over the five charged kinds (not OTHER, not NONE),
                     its share OF THE CHARGED MASS, and `charged_share`, the
                     charged kinds' share of all kind-rated mass
Words with no kind rating are left out of the denominators; `rated_share` says
how much of the prompt's mass that leaves in.
"""
import collections, csv, gzip, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
SRC = os.path.expanduser("~/malignment-data/norm_change/words_long_v4.csv.gz")
KINDS = ["SEXUAL", "VIOLENT", "DEGRADING", "COERCIVE", "ILLICIT", "OTHER", "NONE"]
CHARGED = KINDS[:5]


def main():
    from malignment import roster, charge
    pairs = {(b, a) for b, a in roster.endpoints()[0].items()}
    kc = {}
    m = collections.defaultdict(lambda: collections.Counter())   # (prompt, base) -> kind -> mass
    tot = collections.defaultdict(float)
    with gzip.open(SRC, "rt") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["lang"] != "en" or (r["base"], r["aligned"]) not in pairs:
                continue
            pr = r["prompt"]
            if pr not in kc:
                kc[pr] = charge.kinds(pr) or {}
            pb = float(r["p_base"] or 0)
            tot[(pr, r["base"])] += pb
            k = kc[pr].get(r["word"])
            if k:
                m[(pr, r["base"])][k] += pb
    byp = collections.defaultdict(list)
    for (pr, b), c in m.items():
        byp[pr].append((c, tot[(pr, b)]))
    rows = []
    for pr, lst in sorted(byp.items()):
        sh = np.array([[c[k] / max(sum(c.values()), 1e-300) for k in KINDS] for c, _ in lst])
        rated = np.median([sum(c.values()) / t if t else 0 for c, t in lst])
        med = np.median(sh, axis=0)
        i = int(np.argmax(med))
        ch = med[:5]
        j = int(np.argmax(ch))
        rows.append({"prompt": pr, "n_lineages": len(lst), "rated_share": rated,
                     "kind_base": KINDS[i], "kind_purity": med[i],
                     "kind_charged": CHARGED[j] if ch.sum() > 0 else "",
                     "kind_charged_purity": ch[j] / ch.sum() if ch.sum() > 0 else np.nan,
                     "charged_share": ch.sum(),
                     **{"share_" + k: med[n] for n, k in enumerate(KINDS)}})
    with open(os.path.join(HERE, "results", "prompt_kind_en.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: ("%.4f" % v if isinstance(v, float) else v) for k, v in r.items()})
    print("prompts with kind ratings:", len(rows), "of", len(kc))
    print("kind_base:", collections.Counter(r["kind_base"] for r in rows).most_common())
    print("kind_charged (charged_share >= 0.2):",
          collections.Counter(r["kind_charged"] for r in rows if r["charged_share"] >= 0.2).most_common())
    print("charged_share quantiles:", np.quantile([r["charged_share"] for r in rows], [.1, .25, .5, .75, .9]).round(3))


if __name__ == "__main__":
    main()
