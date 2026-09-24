"""The PAIRED test on the body-part prompts: in each lineage, is the word that gained
most further from the genitals than the word that lost most? -> results/body_paired.md

    python -u body_paired.py --rate     rate what the walk needs, then test
    python -u body_paired.py            test from what is rated

RH, 2026-09-24. `run.py`'s paired test takes each cell's top faller and top riser
and drops the cell when either is unscored -- a modifier, a fragment, `the` -- so
it loses cells to words that were never candidates. This version asks the same
question of the LARGEST VALID word on each side instead.

VALID = rated by the sexual_slot_en_v2 task as `ratable`, not `is_modifier`, and
body_distance > 0 (the word denotes or acts on a place, on or off the body; 0 is
the instrument's "action, state or manner"). The instrument's own gates, not
chosen here.

THE WALK. Per cell (endpoint lineage x prompt), fallers sorted by delta ascending,
risers descending (delta = p_aligned - p_base, `movement_v4` raw frame). Walk each
list to its first VALID word. A word met on the way that has NO rating is rated
(`--rate`), and the walk is repeated, until no cell meets an unrated word before a
valid one (at most MAX_ROUNDS). Ratings come from, in order: the slot index
(slot_ratings/), `results/body_controls_rated.json`, and this file's own
`results/body_paired_rated.json`, which is stored here for the reason
`body_controls.py` gives.

THE TEST. A cell is a HIT if out(riser) > out(faller), out = body_distance; equal
distances are TIES and dropped (the scale is 1-7 integers, so ties are common and
their count is reported). Per prompt: hits / non-tied cells, two-sided sign test.
Per group: prompts with a majority of hits, and the pooled cell count -- pooled
cells are NOT independent (one lineage appears once per prompt), so the per-prompt
count is the unit and the pooled one is description.

Groups: SEXUAL = `body.py`'s 16 tested prompts; VIOLENT, NEUTRAL, LIMINAL =
`body_controls.GROUPS`. POST HOC in the sense that the word-level results on all
of these had been seen.
"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "experiments", "slot_ratings", "sexual"))
import body_controls as BC  # noqa: E402

RATED = os.path.join(HERE, "results", "body_paired_rated.json")
MAX_ROUNDS = 6
INSTRUMENT = "sexual_slot_en_v2"
SEXUAL_MIN_WORDS = 10


def cells(prompt):
    """{(base, aligned): [(word, delta)]} over the 50 endpoint pairs."""
    from malignment import ch, roster
    eps, _ = roster.endpoints()
    pairs = {(b, a) for b, a in eps.items()}
    out = collections.defaultdict(list)
    q = ("SELECT base, aligned, word, p_base, p_aligned FROM {db}.movement_v4 "
         "WHERE frame_base='' AND frame_aligned='' AND prompt='%s'" % prompt.replace("'", "\\'"))
    for r in ch.query(q, limit_bytes=None):
        if (r["base"], r["aligned"]) in pairs:
            out[(r["base"], r["aligned"])].append((r["word"], float(r["p_aligned"]) - float(r["p_base"])))
    return out


def ratings():
    """{(prompt, word): record or None-for-invalid} from every source, later sources fill gaps only."""
    from malignment import fields as F
    R = {}
    for (p, w), by in F._slot_index().items():
        g = by.get(INSTRUMENT)
        if g is not None:
            R[(p, w)] = g
    for path in (BC.RATED, RATED):
        if os.path.exists(path):
            for r in json.load(open(path))["rows"]:
                R.setdefault((r["prompt"], r["word"]), r)
    return R


def valid(rec):
    return bool(rec and rec.get("ratable") and not rec.get("is_modifier")
                and (rec.get("body_distance") or 0) > 0)


def walk(ws, R, prompt):
    """(valid word or None, [unrated words met before it]) along one sorted list."""
    need = []
    for w, _d in ws:
        rec = R.get((prompt, w))
        if rec is None:
            need.append(w)
            continue
        if valid(rec):
            return w, need
    return None, need


def sexual_prompts(R):
    """body.py's rule: English, possessive slot, rated by the instrument, >= 10 admitted words."""
    import body
    from malignment import fields as F
    rr = body.ruler(F._slot_index())
    ps = sorted(p for p in rr if re.search(r" (his|her)$", p) and p.isascii())
    return [p for p in ps if sum(1 for w in rr[p] if "body_distance" in rr[p][w]) >= SEXUAL_MIN_WORDS]


def run(rate):
    R = ratings()
    groups = {"SEXUAL": sexual_prompts(R)}
    groups.update(BC.GROUPS)
    C = {p: cells(p) for ps in groups.values() for p in ps}
    for rnd in range(MAX_ROUNDS):
        need = set()
        for p, cs in C.items():
            for ws in cs.values():
                fl = sorted([x for x in ws if x[1] < 0], key=lambda x: x[1])
                rs = sorted([x for x in ws if x[1] > 0], key=lambda x: -x[1])
                for lst in (fl, rs):
                    _v, n = walk(lst, R, p)
                    need.update((p, w) for w in n)
        print("round %d: %d unrated words met before a valid one" % (rnd + 1, len(need)), flush=True)
        if not need or not rate:
            break
        from task import SexualSlotEN, SCALES_SEX, render
        jobs = sorted(need)
        t = SexualSlotEN()
        errs = {}
        res = t.map([render(p, w) for p, w in jobs],
                    metadata_list=[{"prompt": p, "word": w} for p, w in jobs],
                    num_workers=16, errors=errs)
        old = json.load(open(RATED))["rows"] if os.path.exists(RATED) else []
        for (p, w), r in zip(jobs, res):
            if r is None:
                continue
            rec = dict(prompt=p, word=w, ratable=bool(r.ratable), reading=r.reading,
                       referent_kind=r.referent_kind, zone_kind=r.zone_kind,
                       is_modifier=bool(r.is_modifier))
            if r.ratable:
                rec.update({s: getattr(r, s) for s in SCALES_SEX})
            old.append(rec)
            R[(p, w)] = rec
        json.dump(dict(_what="sexual_slot_en_v2 ratings for words body_paired.py's walk met unrated; "
                             "NOT filed under slot_ratings/", rows=old), open(RATED, "w"), indent=1)
        print("  rated %d, errors %d" % (len(jobs) - len(errs), len(errs)), flush=True)
    return groups, C, R


def main():
    from scipy.stats import binomtest
    groups, C, R = run("--rate" in sys.argv)
    L = ["# The paired test on the body-part prompts, largest VALID word per side", "",
         "Producer `body_paired.py` (post hoc; word-level results seen). Per cell (endpoint lineage x prompt), "
         "the largest faller and largest riser among VALID words (ratable, not a modifier, body_distance > 0, "
         "sexual_slot_en_v2); unrated words met on the walk were rated. HIT = riser's body_distance > faller's. "
         "Ties dropped. The prompt is the unit; pooled cells are description only.", "",
         "| group | prompt | cells | both valid | hits | misses | ties | hit share | p |",
         "|---|---|---|---|---|---|---|---|---|"]
    summ = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
    walked = collections.Counter()
    for g, ps in groups.items():
        for p in ps:
            h = m = t = ok = 0
            for ws in C[p].values():
                fl = sorted([x for x in ws if x[1] < 0], key=lambda x: x[1])
                rs = sorted([x for x in ws if x[1] > 0], key=lambda x: -x[1])
                f, nf = walk(fl, R, p)
                r, nr = walk(rs, R, p)
                if nf or nr:
                    walked["unrated left"] += 1
                if not f or not r:
                    continue
                ok += 1
                walked["faller not top"] += f != fl[0][0]
                walked["riser not top"] += r != rs[0][0]
                a, b = R[(p, r)]["body_distance"], R[(p, f)]["body_distance"]
                h += a > b; m += a < b; t += a == b
            pv = binomtest(h, h + m).pvalue if h + m else float("nan")
            L.append("| %s | %s | %d | %d | %d | %d | %d | %s | %.2g |" % (
                g, p, len(C[p]), ok, h, m, t, ("%.0f%%" % (100.0 * h / (h + m))) if h + m else "--", pv))
            s = summ[g]
            s[0] += 1; s[1] += h > m; s[2] += h; s[3] += m; s[4] += t
    L += ["", "| group | prompts | prompts with hits > misses | sign p over prompts | pooled hits / misses / ties |",
          "|---|---|---|---|---|"]
    for g, (n, maj, h, m, t) in summ.items():
        L.append("| %s | %d | %d | %.2g | %d / %d / %d |" % (g, n, maj, binomtest(maj, n).pvalue, h, m, t))
    L += ["", "Walk: in %d cells the largest faller was not valid and the walk went deeper; %d for the riser; "
          "%d cells still met an unrated word (0 after `--rate`)." % (
              walked["faller not top"], walked["riser not top"], walked["unrated left"])]
    open(os.path.join(HERE, "results", "body_paired.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
