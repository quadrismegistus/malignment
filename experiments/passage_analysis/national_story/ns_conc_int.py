"""National stories on novel_arc's two literary-history instruments, bare and prefilled.

    ~/github/lltk/.venv/bin/python experiments/passage_analysis/national_story/ns_conc_int.py

Producer for the paper seat's note 59 (TheoryMachines/paper/theory-machines-v6-notes.md) and for
the national-stories prior named in novel_arc/TEMPLATE_ARM.md. Read-only on the corpus; prints
its tables and writes them to results/ns_conc_int.md. Runs in the lltk venv (novel_arc's Scorer).

SOURCE. `conflict.sqlite`, table `stories`: the judged corpus (pure stories only; see
conflict.py), frames `raw` and `prefill`. The prefill cell used each model's DEFAULT system
prompt, not framed_empty's `system_mode`, so it is not the chat-template condition of
TEMPLATE_ARM.md.

POPULATION. Endpoint lineages only (`roster.endpoints()`): the base model bare, and the
lineage's aligned endpoint bare and prefilled. Qwen3-8B's prefill cell is dropped (its passages
carry reasoning traces).

MEASURES. novel_arc's Scorer (`measure_lltk`): `rh_absconc_median` (z, HIGH = concrete) and
`usas_x` (share of content words in the psychological field). Each story is cut into 200-word
chunks (a last chunk under 100 words is dropped), and its value is the median over its chunks,
as novel_arc takes a text's median over its passages.

CONTRASTS. Per lineage, the median story value per condition (at least 5 stories). ARM = base
bare -> aligned bare; FRAME = aligned bare -> aligned prefilled; sign tests over lineages, ties
dropped. Groups: stories naming a nationality (eight demonyms), the control naming none, and all.

Paper seat (TheoryMachines), 2026-09-25.
"""
import collections, math, os, sqlite3, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "passage_analysis", "novel_arc"))
from malignment import roster  # noqa: E402
from measure_lltk import Scorer  # noqa: E402

DB = os.path.join(HERE, "conflict.sqlite")
OUT = os.path.join(HERE, "results", "ns_conc_int.md")
EPS = roster.endpoints()[0]          # {base: aligned endpoint}
DROP_PREFILL = {"Qwen/Qwen3-8B"}
MEAS = ("rh_absconc_median", "usas_x")
FLOOR = 5


def sign_p(k, n):
    if n == 0:
        return float("nan")
    k = min(k, n - k)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def cell(rs, m):
    by = collections.defaultdict(list)
    for r in rs:
        by[r["lin"]].append(r[m])
    return {l: st.median(v) for l, v in by.items() if len(v) >= FLOOR}


def main():
    db = sqlite3.connect(DB)
    rows = db.execute("SELECT id, model, lineage, arm, frame, demonym, text FROM stories "
                      "WHERE frame IN ('raw','prefill')").fetchall()
    S = Scorer()
    recs = []
    for sid, model, lin, arm, frame, dem, text in rows:
        if lin not in EPS:
            continue
        if arm == "base" and (model != lin or frame != "raw"):
            continue
        if arm == "aligned" and model != EPS[lin]:
            continue
        if frame == "prefill" and model in DROP_PREFILL:
            continue
        w = (text or "").split()
        chunks = [w[i:i + 200] for i in range(0, len(w), 200)]
        chunks = [c for c in chunks if len(c) >= 100]
        vals = collections.defaultdict(list)
        for c in chunks:
            r = S.score(" ".join(c))
            if not r:
                continue
            for m in MEAS:
                if r.get(m) is not None:
                    vals[m].append(r[m])
        if not all(vals[m] for m in MEAS):
            continue
        cond = "base_raw" if arm == "base" else ("aligned_%s" % frame)
        recs.append(dict(lin=lin, cond=cond, grp=("none" if dem == "none" else "demonym"),
                         **{m: st.median(vals[m]) for m in MEAS}))

    L = ["stories scored: %d | lineages: %d" % (len(recs), len({r["lin"] for r in recs}))]
    for grp in ("demonym", "none", "all"):
        G = [r for r in recs if grp == "all" or r["grp"] == grp]
        L.append("")
        L.append("==== %s stories" % grp.upper())
        for m in MEAS:
            scale = 100 if m == "usas_x" else 1
            L.append("  %s%s" % (m, " (percent of content words)" if m == "usas_x" else " (z, high = concrete)"))
            cells = {}
            for c in ("base_raw", "aligned_raw", "aligned_prefill"):
                rs = [r for r in G if r["cond"] == c]
                per = cell(rs, m)
                cells[c] = per
                if rs:
                    L.append("    %-16s pooled median %8.4f | lineage mean %8.4f, median %8.4f | %4d stories, %2d lineages"
                             % (c, st.median(r[m] for r in rs) * scale,
                                st.mean(per.values()) * scale if per else float("nan"),
                                st.median(per.values()) * scale if per else float("nan"), len(rs), len(per)))
            for lab, a, b in (("ARM   base -> aligned, bare", "base_raw", "aligned_raw"),
                              ("FRAME aligned bare -> prefilled", "aligned_raw", "aligned_prefill")):
                common = sorted(set(cells[a]) & set(cells[b]))
                d = [cells[b][l] - cells[a][l] for l in common]
                if d:
                    up = sum(1 for x in d if x > 0)
                    dn = sum(1 for x in d if x < 0)
                    L.append("    %-32s median diff %+8.4f | up %2d / down %2d of %2d | sign p %.3g"
                             % (lab, st.median(d) * scale, up, dn, len(d), sign_p(up, up + dn)))
    print("\n".join(L))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    head = ["# National stories on the literary-history instruments, bare and prefilled", "",
            "Producer `ns_conc_int.py` (paper seat, 2026-09-25; read-only). Judged pure stories from "
            "`conflict.sqlite`, endpoint lineages, frames raw and prefill (the prefill cell used each "
            "model's DEFAULT system prompt), Qwen3-8B's prefill cell dropped; novel_arc's Scorer over "
            "200-word chunks, a story's value the median over its chunks; per-lineage medians over at "
            "least %d stories; sign tests over lineages, ties dropped." % FLOOR, "", "```"]
    open(OUT, "w").write("\n".join(head + L + ["```", ""]))


if __name__ == "__main__":
    main()
