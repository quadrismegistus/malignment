"""Did the normalisation pass normalise, or did it rewrite?

    python .../verify_normalisation.py                       # after split_pool.py collate
    python .../verify_normalisation.py --batch batch-000     # a single batch, for a pilot

A cleaner told to fix spelling will sometimes improve the prose instead, and the
result reads BETTER, which is exactly why it needs a gate rather than a glance.
Rewriting is not a cosmetic failure here: it would replace each writer's syntax
with the cleaner's, which is the one thing the corpus is for.

## The four checks, and what each can and cannot see

  SIMILARITY   word-level ratio between raw and clean, compared on a form with
               case, punctuation and spelling-noise neutralised. Only real
               substitutions and reorderings move it. A passage that merely had
               its typography fixed sits near 1.0; a rewritten one falls away.
               THE LOAD-BEARING CHECK.
  LENGTH       words out against words in. Catches deletion and completion in
               bulk, and is blind to a same-length paraphrase, which is why it
               is not the primary.
  COMPLETION   passages are cut mid-sentence, so a clean text ending in terminal
               punctuation where the raw did not is the model finishing the
               sentence it was told to leave alone.
  RESIDUE      did the junk actually go? Curly quotes, LaTeX and non-ASCII are
               counted before and after, per corpus. A pass that left arxiv's
               LaTeX in place has not done the job even if every other check is
               clean.

## Uniformity is reported per corpus, because that is the point

RH's ruling is that all six corpora reach the SAME target state. A pass that
cleans dreams hard and fiction lightly reintroduces the confound it exists to
remove, and no aggregate number shows that. Every table here is per corpus.
"""

import argparse, collections, difflib, json, os, re, sys

DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
ROOT = os.path.join(DATA, "jakobson_space")
FINAL = os.path.join(ROOT, "human_passages.jsonl")

CURLY = "“”‘’"
DASH = "—–"
LATEX = re.compile(r"\$[^$]{1,80}\$|\\[a-zA-Z]{2,}")
WORD = re.compile(r"[a-z]+")

#: SIMILARITY FLOOR. Set from the pilot, not from taste: a passage whose only
#: changes are typographic scores far above this, so the floor separates
#: "spelling fixed" from "sentence rebuilt" rather than encoding a tolerance.
SIM_MIN = 0.93
LEN_TOL = 0.10


def canon(t):
    """Comparison form: lowercase alphabetic words only.

    Strips exactly what the pass is ALLOWED to change -- case, punctuation,
    quote style, digits -- so the ratio responds to substitution and reordering
    and not to the normalisation itself. Deliberately does NOT correct spelling,
    so a spelling fix still registers as a small, real difference.
    """
    return WORD.findall(t.lower())


#: A COMPOUND NUMBER -- one with an internal decimal point or thousands separator.
#: This is the whole check: a footnote marker is always a BARE integer, so every
#: compound number in the source must survive into the output, and any that does
#: not was eaten by the footnote rule. Both pilot rounds destroyed numbers this
#: way (`3,024` -> `3,`, `20.0` -> `20.`, `983,004` -> `983,`) and BOTH passed the
#: similarity gate at 0.98, because the edit is one word long. Similarity measures
#: how much moved; it cannot measure whether what moved was load-bearing.
COMPOUND = re.compile(r"\d+[.,]\d+")
MONEY = re.compile(r"\$\d")
#: `$` IS NOT DECIDABLE BY PATTERN, and this is reported rather than flagged.
#: Bare `\$\d` counts `$1/m_Q$` as a price and cries damage on a clean pass.
#: Stripping `$...$` math spans first fixes that and breaks the other way, because
#: `$90 to $190` -- two prices in one sentence -- matches the math-span shape
#: exactly and the check goes blind to real damage. Both versions were written
#: here and both gave a confident wrong answer.
#:
#: There is no regex that separates a price from a delimiter, so MONEY is a
#: REPORTED DELTA and not a gate. `numbers_lost` is the gate: it is exact, because
#: a footnote marker is always a bare integer and a compound number never is.
def money_count(t):
    return len(MONEY.findall(t))


def numbers_lost(raw, clean):
    """-> list of compound numbers present in raw and missing from clean."""
    have = collections.Counter(COMPOUND.findall(clean))
    lost = []
    for tok in COMPOUND.findall(raw):
        if have[tok] > 0:
            have[tok] -= 1
        else:
            lost.append(tok)
    return lost


def check(r):
    raw, clean = r.get("text_raw") or "", r.get("text") or ""
    a, b = canon(raw), canon(clean)
    sim = difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0
    dl = (len(clean.split()) - len(raw.split())) / max(len(raw.split()), 1)
    completed = (raw.rstrip()[-1:] not in ".!?\"'" and clean.rstrip()[-1:] in ".!?")
    flags = []
    lost = numbers_lost(raw, clean)
    if lost:
        flags.append("NUMBERS:" + ",".join(lost[:4]))
    if sim < SIM_MIN:
        flags.append("REWRITTEN")
    if abs(dl) > LEN_TOL:
        flags.append("LENGTH")
    if completed:
        flags.append("COMPLETED")
    if not clean.strip():
        flags.append("EMPTY")
    return sim, dl, completed, flags


def residue(t):
    return dict(curly=sum(t.count(c) for c in CURLY),
                dash=sum(t.count(c) for c in DASH),
                latex=len(LATEX.findall(t)),
                nonascii=sum(1 for c in t if ord(c) > 127))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=FINAL)
    ap.add_argument("--batch", help="verify one raw/cleaned batch pair instead")
    ap.add_argument("--dir", default="cleaned", help="which cleaned output dir to score")
    a = ap.parse_args(argv)

    if a.batch:
        raw = {d["id"]: d["text"] for d in
               (json.loads(l) for l in open(os.path.join(ROOT, "batches", a.batch + ".jsonl")))}
        rows = []
        p = os.path.join(ROOT, a.dir, a.batch + ".jsonl")
        if not os.path.exists(p):
            sys.exit("no cleaned output at %s" % p)
        for l in open(p):
            l = l.strip()
            if not l:
                continue
            d = json.loads(l)
            if d.get("id") in raw:
                rows.append(dict(id=d["id"], corpus="(pilot)", text_raw=raw[d["id"]],
                                 text=d.get("text") or "", changes=d.get("changes") or []))
        print("pilot batch %s: %d of %d ids returned" % (a.batch, len(rows), len(raw)))
        missing = set(raw) - {r["id"] for r in rows}
        if missing:
            print("  MISSING IDS: %d" % len(missing))
    else:
        rows = [json.loads(l) for l in open(a.src)]

    by = collections.defaultdict(list)
    allflags = collections.Counter()
    for r in rows:
        sim, dl, comp, flags = check(r)
        r["_sim"], r["_dl"], r["_flags"] = sim, dl, flags
        by[r["corpus"]].append(r)
        for f in flags:
            allflags[f] += 1

    import statistics as st
    print("\n%-22s %6s %8s %8s %9s %9s %9s"
          % ("corpus", "n", "sim med", "sim min", "len d", "flagged", "changed"))
    for k in sorted(by):
        g = by[k]
        sims = [x["_sim"] for x in g]
        ch = sum(1 for x in g if x.get("changes"))
        fl = sum(1 for x in g if x["_flags"])
        print("%-22s %6d %8.4f %8.4f %+8.1f%% %8.1f%% %8.1f%%"
              % (k, len(g), st.median(sims), min(sims),
                 100 * st.mean([x["_dl"] for x in g]),
                 100 * fl / len(g), 100 * ch / len(g)))

    print("\nflags: %s" % (dict(allflags) or "none"))

    #: reported, never a gate -- see the note on money_count
    print("\n$-token delta (REPORTED, not a flag; `$` is not decidable by pattern)")
    for k in sorted(by):
        g = by[k]
        d0 = sum(money_count(x["text_raw"]) for x in g)
        d1 = sum(money_count(x["text"]) for x in g)
        note = "  <- inspect" if d1 < d0 * 0.9 and d0 >= 10 else ""
        print("  %-22s %5d -> %-5d%s" % (k, d0, d1, note))

    print("\nRESIDUE, mean per passage (raw -> clean)")
    print("%-22s %14s %14s %14s %14s" % ("corpus", "curly", "dash", "latex", "nonascii"))
    for k in sorted(by):
        g = by[k]
        r0 = [residue(x["text_raw"]) for x in g]
        r1 = [residue(x["text"]) for x in g]
        cells = []
        for f in ("curly", "dash", "latex", "nonascii"):
            cells.append("%6.2f->%-6.2f" % (st.mean([d[f] for d in r0]),
                                            st.mean([d[f] for d in r1])))
        print("%-22s %s" % (k, " ".join(cells)))

    tags = collections.Counter()
    for r in rows:
        for t in (r.get("changes") or []):
            tags[str(t)] += 1
    print("\nchange tags: %s" % dict(tags.most_common(14)))

    worst = sorted(rows, key=lambda x: x["_sim"])[:3]
    print("\nLOWEST SIMILARITY (inspect these):")
    for r in worst:
        print("  %-8s sim %.4f  %s" % (r["corpus"][:8], r["_sim"], r["id"]))
        print("    RAW   %s" % r["text_raw"][:150])
        print("    CLEAN %s" % r["text"][:150])

    bad = sum(1 for r in rows if r["_flags"])
    print("\n%d of %d passages flagged (%.1f%%)" % (bad, len(rows), 100 * bad / max(len(rows), 1)))


if __name__ == "__main__":
    main()
