"""The aligned-raw decomposition over every lineage, as `aligned_raw.md` declares it.

    python -u aligned_raw.py                       # -> results/aligned_raw.md
    python -u aligned_raw.py --source FILE --out F # dry run on another aligned-raw file

Registration: `aligned_raw.md` (malign seat, 459f6c97), declared before any
aligned-raw passage was generated. It binds this file: the quantities, the
population and the readings are the registration's, and this producer was
written before the data it reads existed (tested only on the frame pilot's six
lineages, with output sent elsewhere).

Filter, outcomes and sign test are `analyse_regen.py`'s. The per-lineage
difference-in-differences is `frame_pilot.did`, imported, so the pilot and the
full run cannot compute it two ways.

## ORIENTATION

The declared outcomes do not all point the same way: alignment RAISES the
individual's channel, outward and authority shares relative to the institution's
(positive DiD) and gives the INSTITUTION more direct voice (negative DiD). The
readings ("weights > 0", "frame > weights") are stated for channel. For
move_voice_direct they are applied to the oriented quantity, -DiD, so that
"weights > 0" means "the weights move direct voice the declared way". Raw DiDs
are printed unoriented; only the verdict lines use the orientation, and they say so.
"""
import argparse, collections, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyse_regen as A     # noqa: E402  SRC, keep, outcomes, sign
import frame_pilot as FP      # noqa: E402  did, OUT (pilot passages, for the determinism check)

SOURCE = os.path.expanduser("~/malignment-data/institution_vs_individual/coded_aligned_raw.jsonl")
RESULT = os.path.join(HERE, "results", "aligned_raw.md")
OUTCOMES = ["channel", "outward", "authority", "move_voice_direct"]
ORIENT = {"channel": 1, "outward": 1, "authority": 1, "move_voice_direct": -1}
PRIMARY = "channel"
ARMS = ("base", "aligned_raw", "aligned_chat")


def cells(rows, unit):
    """{(unit, arm, side, outcome): [0/1 over kept passages]}, and advice counts per (unit, arm)."""
    c = collections.defaultdict(list)
    form = collections.Counter()
    for r in rows:
        if not r.get("coded"):
            continue
        arm = {"base": "base", "aligned": "aligned_chat", "aligned_raw": "aligned_raw"}[r["arm"]]
        u = r[unit]
        form[(u, arm, "_n")] += 1
        form[(u, arm, "advice")] += r["coded"]["form"] == "advice"
        if A.keep(r["coded"]):
            o = A.outcomes(r["coded"])
            for n in OUTCOMES:
                c[(u, arm, r["side"], n)].append(o[n])
    return c, form


def decompose(c, units, n):
    """Per unit: (weights, frame, total) or None where a cell is empty. Asserts the identity."""
    out = {}
    for u in units:
        w = FP.did(c, u, "base", "aligned_raw", n)
        f = FP.did(c, u, "aligned_raw", "aligned_chat", n)
        t = FP.did(c, u, "base", "aligned_chat", n)
        if None in (w, f, t):
            out[u] = None
            continue
        assert abs(w + f - t) < 1e-12, "total != weights + frame for %s" % u
        out[u] = (w, f, t)
    return out


def verdicts(dec, n):
    """The registration's three readings for outcome n, on the oriented quantity."""
    k = ORIENT[n]
    ok = [v for v in dec.values() if v is not None]
    W = [k * w for w, f, t in ok]
    D = [k * (f - w) for w, f, t in ok]
    wu, wd, wp = A.sign(W)
    du, dd, dp = A.sign(D)
    e2 = "MET" if (wu > wd and wp < 0.05) else "NOT MET"
    dec_v = ("frame-dominated" if (du > dd and dp < 0.05) else
             "weights-dominated" if (dd > du and dp < 0.05) else "mixed")
    shares = [w / t for w, f, t in ((k * a, k * b, k * c_) for a, b, c_ in ok) if t > 0]
    return dict(n=len(ok), wu=wu, wd=wd, wp=wp, e2=e2, du=du, dd=dd, dp=dp, dec=dec_v,
                med_w=float(np.median([w for w, _, _ in ok])) if ok else float("nan"),
                med_f=float(np.median([f for _, f, _ in ok])) if ok else float("nan"),
                med_t=float(np.median([t for _, _, t in ok])) if ok else float("nan"),
                share=float(np.median(shares)) if shares else float("nan"), n_share=len(shares))


def determinism(new_rows):
    """The pilot's accidental raw passages against the fresh ones on the same (model, key, seed)."""
    if not os.path.exists(FP.OUT):
        return None
    old = {(r["model"], r["key"], r["seed"]): r["text"] for r in map(json.loads, open(FP.OUT))}
    pairs = [(old[k], r["text"]) for r in new_rows
             for k in [(r.get("model"), r.get("key"), r.get("seed"))] if k in old]
    if not pairs:
        return None
    same = sum(a == b for a, b in pairs)
    return len(pairs), same


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--out", default=RESULT)
    a = ap.parse_args()
    main_rows = [json.loads(l) for l in open(A.SRC)]
    arms = collections.defaultdict(set)
    for r in main_rows:
        arms[r["lineage"]].add(r["arm"])
    lineages = sorted(l for l, s in arms.items() if s == {"base", "aligned"})
    assert len(lineages) == 43, "the registration's population is 43 lineages; found %d" % len(lineages)
    raw = [json.loads(l) for l in open(a.source)]
    for r in raw:
        r["arm"] = "aligned_raw"
    have = {r["lineage"] for r in raw if r.get("coded")}
    missing = [l for l in lineages if l not in have]
    rows = [r for r in main_rows if r["lineage"] in lineages] + [r for r in raw if r["lineage"] in lineages]
    name = {}
    for r in main_rows:
        if r["arm"] == "aligned" and r["lineage"] in lineages:
            name[r["lineage"]] = r["model"].split("/")[-1]

    L = ["# Aligned raw: weights against frame over every lineage", "",
         "Registration `aligned_raw.md` (459f6c97); producer `aligned_raw.py`, written before the data. "
         "Source `%s`: %d rows, %d coded, over %d of the %d lineages." % (
             os.path.basename(a.source), len(raw), sum(1 for r in raw if r.get("coded")), len(have & set(lineages)),
             len(lineages)), ""]
    if missing:
        L += ["**No aligned-raw cell (dropped from every contrast that needs it, not substituted):** %s" % (
            ", ".join(name.get(l, l) for l in missing)), ""]
    #: comparing the pilot with itself would report a trivially perfect check
    det = None if os.path.realpath(a.source) == os.path.realpath(FP.OUT) else determinism(raw)
    if det:
        L += ["**Determinism check (reported, not pooled):** the frame pilot's accidental raw passages against the "
              "new ones on the same model, prompt and seed: %d of %d texts identical." % (det[1], det[0]), ""]

    # ---- E1, form
    c, form = cells(rows, "lineage")
    adv = {}
    for l in lineages:
        sh = {arm: (form[(l, arm, "advice")] / form[(l, arm, "_n")]) if form[(l, arm, "_n")] else None
              for arm in ARMS}
        adv[l] = sh
    e1 = [sh["aligned_chat"] - sh["aligned_raw"] for sh in adv.values()
          if sh["aligned_chat"] is not None and sh["aligned_raw"] is not None]
    u1, d1, p1 = A.sign(e1)
    L += ["## E1: form", "",
          "Aligned-raw writes advice less often than aligned-chat in %d of %d lineages (fewer: %d; sign p %.3g) -> **%s**."
          % (u1, len(e1), d1, p1, "MET" if (u1 > d1 and p1 < 0.05) else "NOT MET"),
          "Median advice share: base %.2f, aligned raw %.2f, aligned chat %.2f." % tuple(
              float(np.median([sh[arm] for sh in adv.values() if sh[arm] is not None])) for arm in ARMS), ""]

    # ---- the decomposition, lineages
    for n in OUTCOMES:
        dec = decompose(c, lineages, n)
        v = verdicts(dec, n)
        role = "PRIMARY" if n == PRIMARY else "secondary"
        L += ["## %s (%s), lineages" % (n, role), ""]
        orient = "" if ORIENT[n] == 1 else " Verdicts on -DiD (the declared direction is negative)."
        L += ["Defined in %d lineages. Median weights %+.3f, frame %+.3f, total %+.3f (raw DiDs).%s" % (
            v["n"], v["med_w"], v["med_f"], v["med_t"], orient),
            "- weights in the declared direction: %d of %d (against %d; sign p %.3g)%s" % (
                v["wu"], v["n"], v["wd"], v["wp"], " -> **E2 %s**" % v["e2"] if n == PRIMARY else ""),
            "- frame beyond weights: %d of %d (weights beyond frame %d; sign p %.3g) -> **%s**" % (
                v["du"], v["n"], v["dd"], v["dp"], v["dec"]),
            "- median share weights / total, over the %d lineages where total moved the declared way: %.2f" % (
                v["n_share"], v["share"]), ""]
        L += ["| lineage (aligned model) | weights | frame | total | kept base i/s | kept raw i/s | kept chat i/s |",
              "|---|---|---|---|---|---|---|"]
        for l in sorted(lineages, key=lambda x: name.get(x, x)):
            d = dec[l]
            kept = ["%d/%d" % (len(c.get((l, arm, "individual", n), [])), len(c.get((l, arm, "institution", n), [])))
                    for arm in ARMS]
            L.append("| %s | %s | %s | %s | %s |" % (
                name.get(l, l), *((["%+.3f" % x for x in d]) if d else ["--", "--", "--"]), " | ".join(kept)))
        L.append("")

    # ---- disputes beside
    cd, _ = cells(rows, "scenario")
    disputes = sorted({r["scenario"] for r in rows})
    L += ["## Disputes beside (18), each cell pooled over lineages", "",
          "| outcome | defined | weights declared-way | frame beyond weights | median weights | median frame |",
          "|---|---|---|---|---|---|"]
    for n in OUTCOMES:
        v = verdicts(decompose(cd, disputes, n), n)
        L.append("| %s | %d | %d/%d (p %.3g) | %d/%d (p %.3g) -> %s | %+.3f | %+.3f |" % (
            n, v["n"], v["wu"], v["wd"], v["wp"], v["du"], v["dd"], v["dp"], v["dec"], v["med_w"], v["med_f"]))
    L += ["", "Each DiD = (individual change) - (institution change) over kept passages (continuation or advice, "
          "coherent, perspective kept). total = weights + frame exactly (asserted). A `--` is an empty cell.",
          "Limits are the registration's: aligned-raw is an instruction-tuned model continuing text it was not tuned "
          "to continue, and form gates the keep filter, so kept counts are printed per lineage."]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L[:40]))
    print("... -> %s" % a.out)


if __name__ == "__main__":
    main()
