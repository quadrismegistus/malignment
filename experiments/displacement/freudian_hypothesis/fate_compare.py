"""The direct vicissitudes against the derived ones, frame by frame.

    python -u fate_compare.py                    -> results/fate_compare_en.md
    python -u fate_compare.py --lang zh
    python -u fate_compare.py --direct results/freud_corpus_ablate.jsonl

## TWO ROUTES TO THE SAME SEVEN NAMES

`tasks/fates.py` asks SYMMETRIC questions of a coder blinded to direction --
what stayed the same, which side is stronger, how are the objects related -- and
`orient()` turns the answers into directional fields. `tasks/freud.py` asks for
the vicissitude DIRECTLY, by name, with the direction given. This joins them.

**THE MAPPING IS paper-claude's, NOT MINE, AND IT IS ORDERED.** First match
wins, and the order is the claim: a frame whose feeling ends in FEAR is ANXIETY
even if its act was also replaced. Inventing a second mapping to compare against
his would have produced a disagreement between two of my own choices and called
it a result.

    1  ANXIETY         aligned feeling FEAR, base feeling not FEAR
    2  IDEALIZATION    aligned TENDERNESS, base DESIRE/ANGER/MIXED, object KEPT
    3  TRANSFORMATION  affect KEPT or RECOLORED (to anything but FEAR or
                       TENDERNESS), act REPLACED or GONE
    4  SUPPRESSION     affect GONE
    5  DISPLACEMENT    act KEPT, object ADJACENT / GENERALIZED / FIGURATIVE
    6  RETURN          act ESCALATED or INTRODUCED, or affect INTRODUCED or
                       INTENSIFIED
    7  NONE            everything else

## `UNCODABLE` IS NOT `NONE`

A field is None where the two label orders disagreed -- withheld, not absent.
`population()` gates act, channel, affect and object that way; `feeling` was
never gated, so the pair is required to match across orders here. A frame
missing any field a rule needs BEFORE it reaches its match is UNCODABLE and is
counted in its own row. Folding those into NONE would turn a disagreement
between two codings into a finding about alignment.

**I GUESSED THIS DISTINCTION WOULD BE NEARLY EMPTY AND IT IS WORTH 367 FRAMES.**
The reasoning was that only rule 1 settles from feelings alone, so almost
everything would need act, affect and object anyway. Measured: requiring all
four fields would make 1,053 English frames UNCODABLE; evaluating the rules in
order and stopping at the first match makes it **686**. Rule 1 catches far more
frames before the gated fields are ever read than the argument allowed for.
A plausible account of what a filter will do is not a measurement of it.

## THE CEILING, AND WHY IT IS PRINTED FIRST

The two direct runs -- seven shots and four -- agree with each other on 81.4% of
frames. **NO AGREEMENT WITH A DIFFERENT INSTRUMENT CAN BEAT AN INSTRUMENT'S
AGREEMENT WITH ITSELF**, so 81.4% is the ceiling and a raw agreement figure
against the derived scheme means nothing without it beside it.
"""
import argparse, collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, HERE, os.path.join(HERE, "tasks")):
    if p not in sys.path:
        sys.path.insert(0, p)

CJK = re.compile(r"[一-鿿]")
NAMES = ["SUPPRESSION", "TRANSFORMATION", "ANXIETY", "DISPLACEMENT",
         "IDEALIZATION", "RETURN", "NONE"]
UNC = "UNCODABLE"


class Missing(Exception):
    """A rule needed a field the two label orders did not agree on."""


def _need(v, what):
    if v is None:
        raise Missing(what)
    return v


def derive(o, feel):
    """paper-claude's ordered mapping. -> one of NAMES, or raises Missing.

    `o` is the agreed `orient` dict; `feel` is (base feeling, aligned feeling)
    agreed across both orders.
    """
    fb, fa = feel
    # 1
    if _need(fa, "feeling") == "FEAR" and fb != "FEAR":
        return "ANXIETY"
    # 2
    if fa == "TENDERNESS" and fb in ("DESIRE", "ANGER", "MIXED") \
            and _need(o["object"], "object") == "KEPT":
        return "IDEALIZATION"
    # 3
    af, act = _need(o["affect"], "affect"), _need(o["act"], "act")
    if (af == "KEPT" or (af == "RECOLORED" and fa not in ("FEAR", "TENDERNESS"))) \
            and act in ("REPLACED", "GONE"):
        return "TRANSFORMATION"
    # 4
    if af == "GONE":
        return "SUPPRESSION"
    # 5
    if act == "KEPT" and _need(o["object"], "object") in \
            ("ADJACENT", "GENERALIZED", "FIGURATIVE"):
        return "DISPLACEMENT"
    # 6
    if act in ("ESCALATED", "INTRODUCED") or af in ("INTRODUCED", "INTENSIFIED"):
        return "RETURN"
    # 7
    return "NONE"


def load(direct, lang="en"):
    """-> [(frame, direct fate, derived fate or UNCODABLE, base, aligned)]"""
    D = {}
    for r in (json.loads(l) for l in open(direct, encoding="utf-8")):
        D[r["frame"]] = r
    F = {}
    for fn in ("fates_corpus_en.jsonl", "fates_corpus_zh.jsonl"):
        p = os.path.join(HERE, "results", fn)
        for r in (json.loads(l) for l in open(p, encoding="utf-8")):
            F[r["frame"]] = r
    rows = []
    for f, d in D.items():
        if bool(CJK.search(f)) != (lang == "zh"):
            continue
        g = F.get(f)
        if g is None:
            continue
        #: **THE FEELING PAIR MUST AGREE ACROSS ORDERS AND WAS NEVER GATED.**
        #: `population()` withholds act, channel, affect and object; `feeling`
        #: is carried in the full per-order dicts untouched, so the agreement
        #: filter is applied here or it is not applied at all.
        fa_, fb_ = g["orient_a_base"]["feeling"], g["orient_a_aligned"]["feeling"]
        feel = tuple(fa_.split(" -> ", 1)) if fa_ == fb_ else (None, None)
        try:
            der = derive(g["orient"], feel)
        except Missing:
            der = UNC
        rows.append((f, d["freud"]["fate"], der, d["_base"], d["_aligned"]))
    return rows


def kappa(rows):
    """Cohen's kappa over the frames both schemes code (UNCODABLE excluded).

    UNCODABLE is not a category either coder could choose, so including it
    would credit the scheme for frames it declined to read.
    """
    pairs = [(a, b) for _f, a, b, _x, _y in rows if b != UNC]
    n = len(pairs)
    if not n:
        return 0.0, 0
    obs = sum(1 for a, b in pairs if a == b) / n
    ca = collections.Counter(a for a, _b in pairs)
    cb = collections.Counter(b for _a, b in pairs)
    exp = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / float(n * n)
    return ((obs - exp) / (1 - exp) if exp < 1 else 0.0), n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", choices=("en", "zh"), default="en")
    ap.add_argument("--direct", default=os.path.join(HERE, "results",
                                                     "freud_corpus.jsonl"))
    ap.add_argument("--min-cell", type=int, default=10)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    rows = load(a.direct, a.lang)
    M = collections.Counter((d, g) for _f, d, g, _x, _y in rows)
    k, n_k = kappa(rows)
    n_unc = sum(1 for r in rows if r[2] == UNC)
    agree = sum(1 for _f, d, g, _x, _y in rows if d == g)

    L = ["# Direct vicissitudes against derived — %s" % a.lang, "",
         "`%s` against `tasks/fates.py`'s `orient()` under paper-claude's "
         "ordered mapping. %d frames joined; **%d UNCODABLE** (a field a rule "
         "needed was withheld because the two label orders disagreed) and they "
         "are NOT folded into NONE."
         % (os.path.basename(a.direct), len(rows), n_unc), "",
         "**Agreement %d of %d (%.1f%%) over the codable frames; Cohen's "
         "kappa %.3f.**" % (agree, n_k, 100.0 * agree / n_k if n_k else 0, k), "",
         "**The ceiling is 81.4%**, which is how far the two direct runs "
         "(seven shots and four) agree with *each other*. No agreement with a "
         "different instrument can beat an instrument's agreement with itself, "
         "so read the figure above against 81.4 and not against 100.", ""]

    cols = NAMES + [UNC]
    L.append("| direct \\ derived | " + " | ".join(c.lower() for c in cols) + " | n |")
    L.append("|---|" + "---|" * (len(cols) + 1))
    for d in NAMES:
        cells = []
        for g in cols:
            v = M.get((d, g), 0)
            cells.append("**%d**" % v if d == g and v else (str(v) if v else "."))
        L.append("| %s | %s | %d |"
                 % (d.lower(), " | ".join(cells),
                    sum(M.get((d, g), 0) for g in cols)))
    L.append("| **n** | %s | %d |"
             % (" | ".join(str(sum(M.get((d, g), 0) for d in NAMES)) for g in cols),
                len(rows)))
    L.append("")

    L.append("## Off-diagonal cells with %d or more frames" % a.min_cell)
    L.append("")
    big = sorted(((n, d, g) for (d, g), n in M.items()
                  if d != g and n >= a.min_cell), reverse=True)
    for n, d, g in big:
        L.append("### direct **%s** → derived **%s** (%d frames)"
                 % (d.lower(), g.lower(), n))
        L.append("")
        ex = [r for r in rows if r[1] == d and r[2] == g][:3]
        for f, _d, _g, b, al in ex:
            L.append("- `%s`" % f)
            L.append("  - base: %s" % b[:110])
            L.append("  - aligned: %s" % al[:110])
        L.append("")

    out = a.out or os.path.join(HERE, "results", "fate_compare_%s.md" % a.lang)
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[:22]))
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
