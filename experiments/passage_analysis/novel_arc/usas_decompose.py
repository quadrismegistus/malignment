"""Where does the aligned rise in USAS X come from, and does exterior vocabulary fall? (RH, 2026-09-25)

    ~/github/lltk/.venv/bin/python -u usas_decompose.py --score   -> $MALIGNMENT_DATA/novel_arc/usas_decompose.parquet
    .venv/bin/python -u usas_decompose.py --report                -> USAS_DECOMPOSE.md (results/ is gitignored here)

`usas_x` (Figure 5's interiority panel) is the share of a passage's content words carrying a USAS tag
whose head is X, "psychological actions, states and processes". X is broad -- thought (X2), but also
sensory perception (X3), trying (X8), ability and success (X9) -- and it leaves emotion (E) out. There
is no single "exteriority" field: the world is spread over M (movement), A (general actions, getting
and giving), B (body), H (architecture), O (objects and physical attributes) and others.

So this re-scores the SAME passages with the SAME machinery and keeps the whole tally: per passage the
count of every base USAS code (modifiers stripped) over its content words, as `measure_lltk.Scorer`
counts them (every tag the lookup returns, all senses). The report then reads it at three grains -- top-
level letter, X's subfields, and a few named exterior fields -- rather than choosing an exterior set in
advance.

POPULATION. model_placement's base and aligned passages (jakobson_space quadrants.csv, >= 40 words) and
its c20_fiction human anchor. Arms as Figure 5 v7: per model the median over its passages, then the
median over the 25 matched base/aligned pairs (literary_history_v2.paired_arms, imported).

CONTROL. Each passage's X share rebuilt from the tally must EQUAL its `usas_x` in model_placement.parquet;
the score step refuses to write otherwise.

EXPLORATORY. Nothing here was registered.
"""
import collections, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)
DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "novel_arc")
OUT = os.path.join(DATA, "usas_decompose.parquet")
SRC = os.path.join(REPO, "experiments", "passage_analysis", "jakobson_space", "results", "quadrants.csv")
KEEP = ("base", "aligned", "c20_fiction")
BASE = re.compile(r"^([A-Z][0-9]+(?:\.[0-9]+)*)")


def score():
    """-> usas_decompose.parquet: id, category, model, n_content, tally (JSON {base code: count})."""
    import pandas as pd
    from measure_lltk import Scorer, TOK
    S = Scorer()
    look = S.f._lookup
    placed = pd.read_parquet(os.path.join(DATA, "model_placement.parquet"))
    placed = placed[placed.category.isin(KEEP)].set_index("id")
    csv.field_size_limit(10 ** 7)
    rows, bad = [], []
    for r in csv.DictReader(open(SRC, newline="")):
        if r["category"] not in KEEP or r["id"] not in placed.index:
            continue
        txt = r.get("text") or ""
        v = S.score(txt)                           # fills the lemma/POS caches exactly as placement did
        raw = [w.lower() for w in TOK.findall(txt)]
        mod = [S._modernise(w) for w in raw]
        lem = [S._lem.get(w, w) for w in mod]
        content = [(w, l) for w, l in zip(mod, lem) if S._pos.get(w) in ("NOUN", "VERB", "ADJ", "ADV")]
        tally = collections.Counter()
        for w, l in content:
            for t in (look("usas_codes", w, l) or ()):
                m = BASE.match(t)
                if m:
                    tally[m.group(1)] += 1
        n = len(content)
        x = sum(c for k, c in tally.items() if k.startswith("X")) / n if n else None
        want = placed.loc[r["id"], "usas_x"]
        if n and abs(x - want) > 1e-12:
            bad.append((r["id"], x, want))
        rows.append(dict(id=r["id"], category=r["category"], model=r.get("model") or "", n_content=n,
                         tally=json.dumps(tally, sort_keys=True)))
        if len(rows) % 1000 == 0:
            print("  %d scored" % len(rows), flush=True)
    if bad:
        raise SystemExit("refusing to write: X rebuilt from the tally differs from usas_x on %d passages, e.g. %s"
                         % (len(bad), bad[:3]))
    assert len(rows) == len(placed), (len(rows), len(placed))
    print("  CONTROL: X from the tally equals model_placement usas_x on all %d passages" % len(rows))
    os.makedirs(DATA, exist_ok=True)
    pd.DataFrame(rows).to_parquet(OUT, index=False)
    print("-> %s" % OUT)


def report():
    import numpy as np
    import pandas as pd
    sys.argv = [sys.argv[0]]                      # literary_history_v2 reads its version from argv
    import literary_history_v2 as LH2
    d = pd.read_parquet(OUT)
    tal = [json.loads(t) for t in d.tally]
    fields = {}
    letters = sorted({k[0] for t in tal for k in t})
    for L_ in letters:                                       # top-level categories
        fields["%s (all)" % L_] = L_
    for code in ("X1", "X2", "X2.1", "X2.2", "X2.3", "X2.4", "X2.5", "X2.6", "X3", "X3.1", "X3.2", "X3.3",
                 "X3.4", "X3.5", "X4", "X5", "X6", "X7", "X8", "X9",
                 "E1", "E2", "E3", "E4", "E5", "E6",
                 "M1", "M2", "M6", "A1.1.1", "A9", "B1", "H2", "O2", "O4", "Q2"):
        fields[code] = code
    for name, pre in fields.items():
        if len(pre) == 1:
            num = [sum(c for k, c in t.items() if k.startswith(pre)) for t in tal]
        else:
            num = [sum(c for k, c in t.items() if k == pre or k.startswith(pre + ".")) for t in tal]
        d[name] = [100.0 * a / n if n else np.nan for a, n in zip(num, d.n_content)]
    human = d[d.category == "c20_fiction"]
    L = ["# USAS decomposition of Figure 5's interiority (EXPLORATORY)", "",
         "Producer `usas_decompose.py`. Per passage: share of content words (percent) carrying each USAS code, "
         "every sense counted, as `measure_lltk` counts `usas_x` (control: X rebuilt equals usas_x on every "
         "passage). Arms as Figure 5 v7: per model the median over its passages, then the median over the 25 "
         "matched pairs. Paired: aligned minus base within each pair. Human reference: the c20_fiction anchor "
         "(%d passages), median over passages." % len(human), "",
         "| field | base | aligned | aligned - base (median) | pairs up / down | c20 fiction |",
         "|---|---|---|---|---|---|"]
    for name in fields:
        arms, info = LH2.paired_arms(d.rename(columns={name: "_v"}), "_v")
        dl = info["deltas"]
        up, dn = sum(x > 0 for x in dl), sum(x < 0 for x in dl)
        L.append("| %s | %.2f | %.2f | %+.2f | %d / %d | %.2f |" % (
            name, arms["base"], arms["aligned"], float(np.median(dl)), up, dn, float(human[name].median())))
    L += ["", "Codes: X1 general psychological; X2 mental actions (X2.1 thought/belief, X2.2 knowledge, X2.3 "
          "learn, X2.4 investigate/search, X2.5 understand, X2.6 expect); X3 sensory (X3.1 taste, X3.2 sound, "
          "X3.3 touch, X3.4 sight, X3.5 smell); X4 mental object; X5 attention; X6 deciding; X7 wanting/"
          "planning; X8 trying; X9 ability/success. E1-E6 emotion. M1 moving, M2 putting/taking/pushing, M6 "
          "location/direction; A1.1.1 general actions; A9 getting and giving; B1 body; H2 architecture parts; "
          "O2 objects; O4 physical attributes; Q2 speech acts. Shares can sum past 100: a word with two tags "
          "counts twice, as in usas_x."]
    out = os.path.join(HERE, "USAS_DECOMPOSE.md")
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    if "--score" in sys.argv:
        score()
    elif "--report" in sys.argv:
        report()
    else:
        print(__doc__)
