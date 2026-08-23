"""Does a forced word disturb the chain that follows, and where?

    python .../run.py                    # the regression, cumulative + disjoint
    python .../run.py --examples 6       # passages, with per-token surprisal
    python .../run.py --bin 5 10         # which disjoint bin examples come from

MODEL

    self-surprisal(window) ~ log p_gen + delta          forced rows
    self-surprisal(window) ~ log p_gen                  forced AND unforced

`log p_gen` is the opening word's probability UNDER THE MODEL THAT WROTE IT --
`faller_q`/`matched_q`/`riser_q` for the aligned arm, `faller_p` for the base.
`delta = q - p` is the signed movement. Both terms enter ONE fit, so `delta` is
the movement effect at held opening probability, obtained by regression rather
than by discarding the range where fallers and risers do not overlap.

    THE MATCHED-PROBABILITY DESIGN IS NOT USED HERE, DELIBERATELY (RH). A word
    fell; falling IS becoming improbable. Restricting to the band where fallers
    and risers share a probability range removes most of the manipulation and
    asks what survives of demotion after demotion is partialled out.

UNIT IS THE LINEAGE. Coefficients are fitted within each pair and summarised
across pairs with a sign test. Row counts differ several-fold between pairs, so
a pooled fit would weight by data volume rather than by lineage.

SCORER = MODEL throughout. Self-surprisal only; cross-scored rows never enter.

WINDOWS ARE REPORTED BOTH WAYS AND THE DIFFERENCE MATTERS. A cumulative window
`lp[:w]` dilutes an effect that sits away from the joint -- `delta` reads null at
+1 and significant at +10 under cumulative windows, which says only that it is
not in the first token. Disjoint bins locate it.
"""
import argparse, collections, json, math, os, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.expanduser("~/github/malign-logits")
ARMS_JSON = os.path.join(ARCHIVE, "data/forced_arms_46reps_drmatch.json")
sys.path.insert(0, ARCHIVE)

CUM = [1, 10, 20, 30, 0]                       # 0 = whole passage
BINS = [(0, 1), (1, 5), (5, 10), (10, 20), (20, 30), (30, 60)]
MIN_ROWS, MIN_LEN = 60, 60




def _q(v):
    """SQL string literal with quotes doubled.

    `repr()` was used here and broke on the first prompt containing an
    apostrophe -- "the tourist's fanny pack" closed the literal mid-string. A
    value interpolated into SQL must be escaped for SQL, not for Python.
    """
    return "'" + str(v).replace("'", "''") + "'"


def _ch():
    """The ARCHIVE's ClickHouse client, loaded BY PATH.

    `import malign_logits.ch` pulls the archive package's `__init__`, which
    imports plotly; this repo's venv has no plotly and should not grow one to
    read a table. Loading the module file directly takes the client and nothing
    else.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_archive_ch", os.path.join(ARCHIVE, "malign_logits", "ch.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def arms():
    """-> (prob, delta) keyed (pair, prompt, word). Aligned q; base p separately."""
    cells = json.load(open(ARMS_JSON))["cells"]
    prob, delt, basep = {}, {}, {}
    for c in cells:
        for w, qk, dk in (("faller", "faller_q", "faller_delta"),
                          ("matched", "matched_q", "matched_delta"),
                          ("riser", "riser_q", "riser_delta"),
                          ("riser_matched", "riser_matched_q", "riser_matched_delta")):
            word = c.get(w)
            if not word:
                continue
            k = (c["pair"], c["prompt"], word)
            if c.get(qk) is not None:
                prob[k] = float(c[qk])
            if c.get(dk) is not None:
                delt[k] = float(c[dk])
        if c.get("faller") and c.get("faller_p") is not None:
            basep[(c["pair"], c["prompt"], c["faller"])] = float(c["faller_p"])
    return prob, delt, basep, sorted({c["pair"] for c in cells})


def role_of(cells_index, pair, prompt, word):
    return cells_index.get((pair, prompt, word))


def role_index():
    idx = {}
    for c in json.load(open(ARMS_JSON))["cells"]:
        for r in ("faller", "matched", "riser", "riser_matched"):
            if c.get(r):
                idx[(c["pair"], c["prompt"], c[r])] = r
    return idx


def fetch(ch, model, forced_only=True):
    #: `prompt` in gen_scores is TRUNCATED AT 60 CHARACTERS (max observed 61,
    #: mean 50) -- the old prompt_id defect, still present in this column. The
    #: arms table carries full prompts up to 148 chars, so keying the role
    #: lookup on `prompt` silently dropped 455,296 of 1,809,088 forced rows
    #: (25.2%), including EVERY cell of the `power` domain (549/549, all long).
    #: `prompt_full` is populated on every row. Use it.
    q = ("SELECT prompt_full AS prompt, forced_word, sample_idx, logprobs FROM malign_logits.gen_scores "
         "WHERE corpus='passage' AND scorable=1 AND scorer=model AND model=%s"
         % _q(model))
    if forced_only:
        q += " AND forced_word != ''"
    return ch.query(q)


def binom(k, n):
    return (min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1))
                / 2.0 ** n) if n else float("nan"))


def report(fits, title, keys):
    print()
    print(title)
    print("  %-10s %-7s %5s %11s %9s %10s"
          % ("window", "term", "n", "median", "up/down", "sign p"))
    for lab in keys:
        for term in ("logp", "delta"):
            v = fits.get((lab, term))
            if not v:
                continue
            up = sum(1 for x in v if x > 0); dn = sum(1 for x in v if x < 0)
            print("  %-10s %-7s %5d %11.5f %9s %10.5f"
                  % (lab, term, len(v), S.median(v), "%d/%d" % (up, dn),
                     binom(min(up, dn), up + dn)))


def regression(a):
    import numpy as np
    ch = _ch()
    prob, delt, basep, pairs = arms()
    cum = collections.defaultdict(list)
    dis = collections.defaultdict(list)
    for i, pr in enumerate(pairs, 1):
        b, al = pr.split(">")
        model = al if a.arm == "aligned" else b
        try:
            res = fetch(ch, model, forced_only=True)
        except Exception as e:
            print("  %-38s FAILED %s" % (pr.split(">")[0][:38], str(e)[:36]), flush=True)
            continue
        rows = []
        for x in res:
            lp = [v for v in (x["logprobs"] or []) if v is not None]
            if len(lp) < MIN_LEN:
                continue
            k = (pr, x["prompt"], x["forced_word"])
            p = prob.get(k) if a.arm == "aligned" else basep.get(k)
            if not p or p <= 0:
                continue
            rows.append((math.log(p), delt.get(k, 0.0), lp))
        if len(rows) < MIN_ROWS:
            continue
        X = np.array([[1.0, r[0], r[1]] for r in rows])
        for w in CUM:
            y = np.array([-sum(r[2][:w] if w else r[2]) / (w if w else len(r[2])) for r in rows])
            c = np.linalg.lstsq(X, y, rcond=None)[0]
            lab = "+%d" % w if w else "all"
            cum[(lab, "logp")].append(c[1]); cum[(lab, "delta")].append(c[2])
        for lo, hi in BINS:
            y = np.array([-sum(r[2][lo:hi]) / (hi - lo) for r in rows])
            c = np.linalg.lstsq(X, y, rcond=None)[0]
            lab = "[%d,%d)" % (lo, hi)
            dis[(lab, "logp")].append(c[1]); dis[(lab, "delta")].append(c[2])
        if i % 12 == 0:
            print("  %d/%d pairs" % (i, len(pairs)), flush=True)
    report(cum, "CUMULATIVE windows, arm=%s -- dilutes an off-joint effect" % a.arm,
           ["+%d" % w if w else "all" for w in CUM])
    report(dis, "DISJOINT bins, arm=%s -- locates it" % a.arm,
           ["[%d,%d)" % (lo, hi) for lo, hi in BINS])


def examples(a):
    """Typical passages, not extreme ones.

    **AN ILLUSTRATION HAS A SAMPLING DESIGN AND THE FIRST ONE HERE WAS WRONG.**
    Selecting `max(faller)` per prompt returned passages 500x the median effect
    whose RISER twin was equally degenerate -- i.e. junk, selected for. The
    quantity to illustrate is the CONTRAST (faller bin minus riser bin at the
    same prompt), and the case to show is one sitting at its MEDIAN, with both
    members inside the pair's own surprisal range so neither is degenerate.
    """
    ch = _ch()
    prob, delt, basep, pairs = arms()
    idx = role_index()
    lo, hi = a.bin
    shown = 0
    for pr in pairs:
        if shown >= a.examples:
            break
        b, al = pr.split(">")
        try:
            res = fetch(ch, al, forced_only=True)
        except Exception:
            continue
        #: per (prompt) collect rows by role, and the pair's own baseline
        byprompt = collections.defaultdict(lambda: collections.defaultdict(list))
        allbin = []
        for x in res:
            lp = [v for v in (x["logprobs"] or []) if v is not None]
            if len(lp) < MIN_LEN:
                continue
            r = idx.get((pr, x["prompt"], x["forced_word"]))
            if not r:
                continue
            s = -sum(lp[lo:hi]) / (hi - lo)
            allbin.append(s)
            byprompt[x["prompt"]][r].append((s, x["sample_idx"], x["forced_word"], lp))
        if not allbin:
            continue
        base_med = S.median(allbin)
        #: the prompt whose FALLER most exceeds this pair's own baseline, and which
        #: also has a riser to set beside it
        hi_cut = base_med + 2.0 * (S.pstdev(allbin) or 1.0)
        cands = []
        for prompt, d in byprompt.items():
            if not d.get("faller") or not d.get("riser"):
                continue
            #: MEDIAN sample within each role, and BOTH must be non-degenerate
            f = sorted(d["faller"])[len(d["faller"]) // 2]
            r = sorted(d["riser"])[len(d["riser"]) // 2]
            if f[0] > hi_cut or r[0] > hi_cut:
                continue
            cands.append((f[0] - r[0], prompt, f, r))
        if len(cands) < 3:
            continue
        cands.sort()
        #: --select median is the DEFAULT and is what an illustration of a
        #: typical effect must use. `top` shows the extreme of the CONTRAST --
        #: informative, never representative, and labelled as such on the face.
        pick = {"median": len(cands) // 2, "top": -1, "bottom": 0}[a.select]
        excess, prompt, f, r = cands[pick]
        txt = ch.query(
            "SELECT forced_word, sample_idx, text, token_ids FROM malign_logits.gen_sequences "
            "WHERE corpus='passage' AND model=%s AND prompt_full=%s AND forced_word IN (%s,%s)"
            % (_q(al), _q(prompt), _q(f[2]), _q(r[2])))
        tmap = {(t["forced_word"], t["sample_idx"]): t for t in txt}
        print("=" * 78)
        print("%s   [--select %s: %s]" % (al, a.select,
              {"median": "TYPICAL", "top": "EXTREME, not representative",
               "bottom": "REVERSED, not representative"}[a.select]))
        print("  PROMPT: %r" % prompt[:96])
        print("  bin [%d,%d): pair median %.3f, degeneracy cut %.3f | faller-riser contrast %+.3f (the MEDIAN of %d prompts)"
              % (lo, hi, base_med, hi_cut, excess, len(cands)))
        for lab, row in (("FALLER", f), ("RISER ", r)):
            s, sidx, word, lp = row
            d = delt.get((pr, prompt, word), float("nan"))
            q = prob.get((pr, prompt, word), float("nan"))
            print()
            print("  %s %-14r delta %+0.4f  q %0.4f   bin surprisal %.3f (%+.3f vs median)"
                  % (lab, word, d, q, s, s - base_med))
            t = tmap.get((word, sidx))
            if t:
                print("     %s" % ((t["text"] or "")[:300].replace("\n", " / ")))
            hot = sorted(range(min(len(lp), hi)), key=lambda j: lp[j])[:6]
            print("     most surprising token positions in [0,%d): %s"
                  % (hi, ", ".join("+%d (%.2f nats)" % (j, -lp[j]) for j in sorted(hot))))
        shown += 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="aligned", choices=("aligned", "base"))
    ap.add_argument("--examples", type=int, default=0)
    ap.add_argument("--bin", type=int, nargs=2, default=(5, 10))
    ap.add_argument("--select", default="median", choices=("median", "top", "bottom"),
                    help="which prompt to show: median contrast (typical), top "
                         "(faller worst relative to its riser), bottom (reverse)")
    a = ap.parse_args(argv)
    if a.examples:
        examples(a)
    else:
        regression(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
