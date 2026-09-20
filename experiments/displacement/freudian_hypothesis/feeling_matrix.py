"""What the FEELING becomes, base -> aligned, as a matrix and as Freud's four fates.

    python -u feeling_matrix.py                -> results/feeling_matrix_en.md
    python -u feeling_matrix.py --lang zh
    python -u feeling_matrix.py --by-lift       the same matrix in lift tertiles

## THE FIELD THIS READS IS NOT THE ONE THE FIGURE READS

`kind_flow` draws `orient["affect"]`, which is a RELATION -- KEPT, GONE,
RECOLORED, INTRODUCED, NONE. This file reads `orient["feeling"]`, which is the
pair of NAMED feelings the coder gave each side, ANGER -> NONE and so on. The
second is strictly finer and the first is derivable from it in most cells but
not all: `RECOLORED` says the feeling changed and the matrix says what it changed
into.

**`feeling` IS NOT IN THE AGREEMENT SET.** `population()` withholds `act`,
`channel`, `affect` and `object` where the two label orders disagree; `feeling`
is carried in the full per-order dicts and was never gated. So the filter is
applied here: a frame counts only where `orient_a_base["feeling"]` equals
`orient_a_aligned["feeling"]` -- the same pair recovered from both codings.
1,807 of 2,244 English frames survive that, which is a weaker agreement than any
gated field, and the matrix is worth exactly what that number says.

## WHY THE ORIENTATION IS READ AND NOT RECONSTRUCTED

paper-claude built this matrix from `raw` and `raw_flipped` and did not trust
the asymmetric cells he got. He was right not to: the direction lives in
`orient()`'s `a_is_base` argument, which decides which of `result.a`/`result.b`
is the base AND which label `stronger_*` refers to, and a reconstruction has to
get both right. `orient_a_base` and `orient_a_aligned` are that function's own
output, stored per row. Nothing here re-derives a direction.

## THE FOUR FATES ARE CELLS, AND ONE OF THEM IS A CONJUNCTION

Freud's vicissitudes of the affect, as this corpus can test them:

    SUPPRESSION     a feeling -> NONE            (and how many also REPLACE the act)
    TRANSFORMATION  a feeling kept while the channel ends VOCAL_ACT or MENTAL_STATE
    ANXIETY         any feeling -> FEAR
    IDEALIZATION    ANGER or DESIRE -> TENDERNESS, act weakened or replaced,
                    object kept

The first three are cells or unions of cells. The fourth is a three-way
conjunction and will be rare for that reason alone, which is a fact about the
definition before it is a fact about alignment -- so its denominator is printed
beside it.
"""
import argparse, collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, HERE, os.path.join(HERE, "tasks")):
    if p not in sys.path:
        sys.path.insert(0, p)

CJK = re.compile(r"[一-鿿]")
def _order():
    """The coder's `feeling` vocabulary, read off the Literal.

    **A HAND-TYPED COPY OF A VOCABULARY DROPS WHATEVER IT FORGETS, SILENTLY.**
    The first version of this list held `SHAME`, which the schema does not
    define, and omitted `CONTEMPT`, which it does -- so three `NONE -> CONTEMPT`
    frames were absent from the matrix while the introduced-feelings line below
    it, which counts from the data, printed them. A table and a sentence on the
    same page disagreeing is how the defect announced itself; nothing in the
    table said a column was missing.
    """
    import typing
    from tasks.fates import FEELING
    vals = list(typing.get_args(FEELING))
    #: printed order: the named feelings as the schema lists them, then the two
    #: non-feelings last, because they are the row and column a reader checks
    tail = [v for v in ("MIXED", "NONE") if v in vals]
    return [v for v in vals if v not in tail] + tail


ORDER = _order()


def load(path, lang="en"):
    """Rows whose FEELING PAIR agrees across the two label orders."""
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    rows = [r for r in rows if bool(CJK.search(r["frame"])) == (lang == "zh")]
    n_all = len(rows)
    ok = [r for r in rows
          if r["orient_a_base"]["feeling"] == r["orient_a_aligned"]["feeling"]]
    return ok, n_all


def pair(r):
    b, a = r["orient_a_base"]["feeling"].split(" -> ", 1)
    return b, a


def matrix(rows):
    m = collections.Counter()
    for r in rows:
        m[pair(r)] += 1
    return m


def render_matrix(m, title):
    rowk = [f for f in ORDER if any(k[0] == f for k in m)]
    colk = [f for f in ORDER if any(k[1] == f for k in m)]
    tot = collections.Counter()
    for (b, a), n in m.items():
        tot[b] += n
    L = ["### %s" % title, "",
         "Rows are the BASE feeling, columns the ALIGNED feeling. `n` is the row total.", "",
         "| base \\ aligned | " + " | ".join(c.lower() for c in colk) + " | n | diag |",
         "|---|" + "---|" * (len(colk) + 2)]
    for b in rowk:
        cells = []
        for c in colk:
            v = m.get((b, c), 0)
            cells.append("**%d**" % v if b == c and v else (str(v) if v else "."))
        d = m.get((b, b), 0)
        L.append("| %s | %s | %d | %s |"
                 % (b.lower(), " | ".join(cells), tot[b],
                    "%.0f%%" % (100.0 * d / tot[b]) if tot[b] else "-"))
    L.append("")
    return "\n".join(L)


SLOT = re.compile(r"\bthe [A-Z][A-Za-z-]*s?\b")


def templates(rows):
    """How many DISTINCT sentence templates a set of frames covers.

    **A SLOT BATTERY IS ONE SENTENCE READ MANY TIMES, AND A CELL COUNT CANNOT
    SEE THAT.** `ANXIETY` came out at 24, which reads as two dozen independent
    observations of a feeling turning into fear. 22 of them are `When the
    <GROUP> moved onto the street, the neighbours felt` with the demographic
    slot varied -- one stimulus, twenty-two fillers. The fate is not absent and
    it is not 24 either; at frame grain it is one template plus two.

    The normalisation only collapses a capitalised noun phrase after "the",
    which is what the institutional and demographic batteries vary. It will miss
    a battery that varies something else, so the count is a FLOOR on
    independence, never a certificate of it.
    """
    return len({SLOT.sub(" the <SLOT>", r["frame"]) for r in rows})


def _note(rows, extra=""):
    t = templates(rows)
    s = "%d distinct templates" % t
    if rows and t < len(rows):
        s += " (slot battery: %d readings of %d sentences)" % (len(rows), t)
    return s + ("; " + extra if extra else "")


def fates(rows):
    """-> list of (label, n, denominator, note)"""
    out = []
    feel = [r for r in rows if pair(r)[0] != "NONE"]

    sup = [r for r in feel if pair(r)[1] == "NONE"]
    sup_repl = [r for r in sup if r["orient_a_base"]["act"] == "REPLACED"]
    out.append(("SUPPRESSION  feeling -> NONE", len(sup), len(feel),
                _note(sup, "%d also REPLACE the act" % len(sup_repl))))

    #: **KEPT, NOT MERELY THE SAME NAME.** A feeling can carry the same label on
    #: both sides while the coder's own `affect` relation says it attenuated or
    #: went. The conjunction is the point of the fate: the feeling survives AND
    #: the act has become speech or thought.
    trans = [r for r in feel
             if pair(r)[0] == pair(r)[1]
             and r["orient_a_base"]["channel"].endswith(("VOCAL_ACT", "MENTAL_STATE"))]
    out.append(("TRANSFORMATION  feeling kept, channel ends in voice or mind",
                len(trans), len(feel),
                _note(trans, "%d end VOCAL_ACT"
                      % sum(1 for r in trans
                            if r["orient_a_base"]["channel"].endswith("VOCAL_ACT")))))

    anx = [r for r in feel if pair(r)[1] == "FEAR" and pair(r)[0] != "FEAR"]
    out.append(("ANXIETY  any feeling -> FEAR", len(anx), len(feel),
                _note(anx, ", ".join(
                    "%s %d" % (k.lower(), v) for k, v in
                    collections.Counter(pair(r)[0] for r in anx).most_common()))))

    ideal = [r for r in feel
             if pair(r)[0] in ("ANGER", "DESIRE") and pair(r)[1] == "TENDERNESS"]
    ideal_full = [r for r in ideal
                  if r["orient_a_base"]["act"] in ("WEAKENED", "REPLACED")
                  and r["orient_a_base"]["object"] == "KEPT"]
    elig = [r for r in feel if pair(r)[0] in ("ANGER", "DESIRE")]
    out.append(("IDEALIZATION  anger/desire -> tenderness, act weakened or "
                "replaced, object kept", len(ideal_full), len(elig),
                _note(ideal_full,
                      "%d reach tenderness at all; the conjunction costs %d"
                      % (len(ideal), len(ideal) - len(ideal_full)))))
    return out


def introduced(rows):
    """What the aligned side supplies where the base had no feeling."""
    c = collections.Counter(pair(r)[1] for r in rows if pair(r)[0] == "NONE")
    return c


def cell_detail(rows, b, a, cap=8):
    """The frames in one cell, for a cell somebody does not believe."""
    hit = [r for r in rows if pair(r) == (b, a)]
    L = []
    for r in hit[:cap]:
        o = r["orient_a_base"]
        L.append("- `%s` — act %s, %s, object %s\n  base: %s\n  aligned: %s"
                 % (r["frame"], o["act"], o["channel"].lower().replace("_", " "),
                    o["object"], r["_base"][:90], r["_aligned"][:90]))
    return hit, "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", choices=("en", "zh"), default="en")
    ap.add_argument("--by-lift", action="store_true")
    ap.add_argument("--detail", nargs=2, metavar=("BASE", "ALIGNED"),
                    default=["FEAR", "MIXED"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    src = os.path.join(HERE, "results", "fates_corpus_%s.jsonl" % a.lang)
    rows, n_all = load(src, a.lang)
    L = ["# What the feeling becomes — %s" % a.lang,
         "",
         "%d of %d frames whose FEELING PAIR agrees across both label orders "
         "(%.0f%%). `feeling` is not in the agreement set `population()` gates, "
         "so the filter is applied here and nowhere upstream."
         % (len(rows), n_all, 100.0 * len(rows) / n_all),
         "",
         render_matrix(matrix(rows), "All frames")]

    L.append("### Freud's four fates as cells of that matrix")
    L.append("")
    L.append("| fate | n | of | note |")
    L.append("|---|---|---|---|")
    for lab, n, den, note in fates(rows):
        L.append("| %s | **%d** | %d | %s |" % (lab, n, den, note))
    L.append("")

    inc = introduced(rows)
    L.append("### What the aligned side INTRODUCES where the base had none")
    L.append("")
    L.append("%d frames start at `NONE`. The aligned side supplies: %s"
             % (sum(inc.values()),
                ", ".join("**%s %d**" % (k.lower(), v)
                          for k, v in inc.most_common() if k != "NONE")))
    L.append("")

    b, c = a.detail
    hit, det = cell_detail(rows, b, c)
    L.append("### `%s -> %s` (%d frames)" % (b.lower(), c.lower(), len(hit)))
    L.append("")
    L.append(det or "_no frames in this cell_")
    L.append("")

    if a.by_lift:
        from kind_flow import base_lift
        lift = base_lift(rows)
        have = [r for r in rows if r["frame"] in lift]
        vals = sorted(lift[r["frame"]] for r in have)
        lo = vals[len(vals) // 3] if vals else 0
        hi = vals[2 * len(vals) // 3] if vals else 0
        L.append("### By lift tertile")
        L.append("")
        L.append("Lift is the base words' mean scene rating minus the frame's own "
                 "(`kind_flow.base_lift`, the single definition of this dose). "
                 "%d of %d frames carry one; cuts at %+.2f and %+.2f."
                 % (len(have), len(rows), lo, hi))
        L.append("")
        for lab, sel in (("bottom third", [r for r in have if lift[r["frame"]] <= lo]),
                         ("middle third", [r for r in have
                                           if lo < lift[r["frame"]] <= hi]),
                         ("top third", [r for r in have if lift[r["frame"]] > hi])):
            L.append(render_matrix(matrix(sel), "%s (%d frames)" % (lab, len(sel))))
            fl = [r for r in sel if pair(r)[0] != "NONE"]
            gone = sum(1 for r in fl if pair(r)[1] == "NONE")
            L.append("%d of %d frames with a base feeling lose it entirely (%.0f%%)."
                     % (gone, len(fl), 100.0 * gone / len(fl) if fl else 0))
            L.append("")

    out = a.out or os.path.join(HERE, "results", "feeling_matrix_%s.md" % a.lang)
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
