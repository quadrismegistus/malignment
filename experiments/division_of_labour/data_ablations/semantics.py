"""What KIND of word falls, and what KIND rises, across the SFT ablations?

`jaccard_lift.py` says WildChat's removal changes WHICH words move. It cannot say
what changes about them. `how_it_differs.py` tried, using the per-prompt `kind`
rating, and that instrument is too coarse for the question: `kind` sorts by HOW
BAD, not by WHAT ABOUT, so the campaign's own paradigm case fails it -- `kill` is
VIOLENT and `scream` is NONE, making "kill -> scream" cross-kind and scoring it
as suppression.

`malignment/fields.py` is the right instrument. It gives semantic FIELDS (USAS,
RID, WordNet supersenses) where `strangle` is aggression / "Life and living
things [-]" and `scream` is expressive_behavior / "Speech acts" -- so the move
from one to the other is representable as a field change rather than as a
category violation.

THREE NORM KINDS, KEPT SEPARATE BECAUSE THEY ANSWER DIFFERENTLY:

    TYPE, human      warriner valence/arousal/dominance, brysbaert concreteness.
                     One value per word, from human raters, no context.
    TYPE, model      the k_* scales. One value per word from ONE model at ONE
                     frozen instrument version -- `fields.k_warnings()` and NOT
                     human norms. vulgarity is a sparse indicator and
                     register_level is not established; both are printed with
                     their warnings attached.
    CONTEXTUAL       `charge.scene(prompt)[word]`, which rates the same word
                     differently in different scenes. This is the one that can
                     see that `run` is unremarkable after "she wanted to" and
                     loaded after "he told her not to".

**The type/contextual gap is itself a result**, not a robustness check: where
they disagree, the movement is about the scene rather than about the vocabulary.

THE UNIT IS THE PROMPT. Each arm is ONE checkpoint, so there is no lineage
replication to average over and the prompt is the only available replicate.
Arms are compared paired within prompt, never as two means over different
populations.

MASS-WEIGHTED, because a norm difference computed over word TYPES answers a
different question from one computed over the mass that actually moved. Fallers
are weighted by mass lost, risers by mass gained.

COVERAGE IS PRINTED. A norm mean over 40% of the moved mass is a statement about
40% of the moved mass, and the lexicons differ enormously in reach -- the General
Inquirer is a 1960s resource that does not know `raped`, `desecrated` or
`stomped`, so it silently drops the transgressive end.

    python -m experiments.division_of_labour.data_ablations.semantics
    python -m experiments.division_of_labour.data_ablations.semantics --edge framed
"""
import collections
import math
import statistics as st

from malignment import ch, charge, fields
from .jaccard_lift import edge_where, BASE, FULL, ABLATIONS

TYPE_HUMAN = ["warriner_valence", "warriner_arousal", "warriner_dominance",
              "brysbaert_concreteness"]
TYPE_MODEL = ["k_transgressiveness", "k_charge", "k_valence", "k_bodily_harm",
              "k_concreteness", "k_register_level"]


def sign_test(ds):
    up = sum(1 for d in ds if d > 0)
    dn = sum(1 for d in ds if d < 0)
    t = up + dn
    if not t:
        return up, dn, 1.0
    k = min(up, dn)
    return up, dn, min(1.0, 2 * sum(math.comb(t, i) for i in range(k + 1)) / 2 ** t)


_NORM = {}


def norm_of(w):
    if w not in _NORM:
        try:
            _NORM[w] = fields.norms(w) or {}
        except Exception:
            _NORM[w] = {}
    return _NORM[w]


def moved(model, edge):
    """{prompt: (fallers, risers)} as [(word, mass)] with mass positive."""
    rows = ch.query(
        "SELECT prompt, word, (p_aligned-p_base) AS delta, cls FROM movement_v4 "
        "WHERE %s AND cls != 'still'" % edge_where(model, edge), limit_bytes=None)
    out = collections.defaultdict(lambda: ([], []))
    for r in rows:
        d = float(r["delta"])
        f, ri = out[r["prompt"]]
        (f if r["cls"] == "faller" else ri).append((r["word"], abs(d)))
    return out


def weighted(items, key, scene=None):
    """(mass-weighted mean of `key` over items, covered mass, total mass)."""
    num = cov = tot = 0.0
    for w, m in items:
        tot += m
        v = scene.get(w) if scene is not None else norm_of(w).get(key)
        if v is None:
            continue
        num += m * float(v)
        cov += m
    return (num / cov if cov else None), cov, tot


def main(edge="raw"):
    arms = {"full": moved(FULL, edge)}
    for name, m in ABLATIONS:
        arms[name] = moved(m, edge)
    shared = set(arms["full"])
    for v in arms.values():
        shared &= set(v)
    shared = sorted(shared)

    print("SEMANTICS OF WHAT FALLS AND WHAT RISES   [edge=%s]" % edge)
    print("mass-weighted, unit = the prompt, n = %d prompts\n" % len(shared))

    scales = ([("TYPE/human", k) for k in TYPE_HUMAN]
              + [("TYPE/model", k) for k in TYPE_MODEL]
              + [("CONTEXTUAL", "scene")])

    print("RISER minus FALLER, on the FULL mix. Positive = what RISES scores")
    print("higher. MEAN not median: the k_* scales are integers 1-7, so a")
    print("median reads 0.0000 while the sign test is decisive.")
    print("%-12s %-22s %9s %9s %8s %7s"
          % ("kind", "scale", "mean d", "up/dn", "p", "cov"))
    per_arm = {}
    for kind, key in scales:
        row = {}
        for arm in ["full"] + [n for n, _ in ABLATIONS]:
            #: KEYED BY PROMPT. An earlier version zipped two lists positionally,
            #: which pairs prompt i of one arm with prompt i of another only if
            #: both arms covered exactly the same prompts in the same order.
            ds, covs = {}, []
            for p in shared:
                f, r = arms[arm][p]
                if not f or not r:
                    continue
                sc = charge.scene(p) if key == "scene" else None
                if key == "scene" and not sc:
                    continue
                fv, fc, ft = weighted(f, key, sc)
                rv, rc, rt = weighted(r, key, sc)
                if fv is None or rv is None:
                    continue
                ds[p] = rv - fv
                covs.append((fc + rc) / (ft + rt) if (ft + rt) else 0)
            row[arm] = (ds, covs)
        per_arm[key] = row
        ds, covs = row["full"]
        if not ds:
            print("%-12s %-22s   (no coverage)" % (kind, key))
            continue
        v = list(ds.values())
        up, dn, p = sign_test(v)
        print("%-12s %-22s %9.4f %9s %8.4f %6.0f%%"
              % (kind, key, st.mean(v), "%d/%d" % (up, dn), p,
                 100 * st.mean(covs)))

    print("\n\nDOES THE ABLATION CHANGE IT? arm's (riser-faller) minus full's,")
    print("paired within prompt. Positive = the arm's movement scores HIGHER.\n")
    hdr = "%-22s" % "scale"
    for n, _ in ABLATIONS:
        hdr += "%16s" % n
    print(hdr)
    for kind, key in scales:
        row = per_arm.get(key)
        if not row or not row["full"][0]:
            continue
        line = "%-22s" % key
        for n, _ in ABLATIONS:
            fd, ad = row["full"][0], row[n][0]
            both = sorted(set(fd) & set(ad))
            if len(both) < 30:
                line += "%16s" % ("n=%d" % len(both))
                continue
            diffs = [ad[q] - fd[q] for q in both]
            up, dn, p = sign_test(diffs)
            star = "*" if p < 0.01 else (":" if p < 0.05 else " ")
            line += "%15.4f%s" % (st.mean(diffs), star)
        print(line)
    print("\n  * p<0.01   : p<0.05   sign test over prompts, PAIRED BY PROMPT ID")

    #: FIELDS. Not a scale but a membership, so the summary is a share of moved
    #: mass rather than a mean. RID and USAS are reported separately because
    #: their coverage differs by a factor of several and pooling them would let
    #: the wider one set the denominator.
    print("\n\nSEMANTIC FIELDS: share of moved mass, faller vs riser.")
    print("RID is a regex lexicon of ~3,000 patterns; USAS is a 232-code")
    print("tagset. Coverage differs, so they are never pooled.\n")
    for src, fn in (("RID", fields.rid), ("USAS", fields.usas)):
        cache = {}

        def tags(w):
            if w not in cache:
                try:
                    cache[w] = set(fn(w) or ())
                except Exception:
                    cache[w] = set()
            return cache[w]

        share = {}
        for arm in ["full"] + [n for n, _ in ABLATIONS]:
            fm = collections.Counter()
            rm = collections.Counter()
            ft = rt = fcov = rcov = 0.0
            for q in shared:
                f, r = arms[arm][q]
                for w, m in f:
                    ft += m
                    t = tags(w)
                    if t:
                        fcov += m
                    for x in t:
                        fm[x] += m
                for w, m in r:
                    rt += m
                    t = tags(w)
                    if t:
                        rcov += m
                    for x in t:
                        rm[x] += m
            share[arm] = (fm, rm, ft, rt, fcov / ft if ft else 0,
                          rcov / rt if rt else 0)
        fm, rm, ft, rt, fc, rc = share["full"]
        print("  %s  faller coverage %.0f%% of mass, riser %.0f%%"
              % (src, 100 * fc, 100 * rc))
        keys = [k for k, _ in (fm + rm).most_common(8)]
        print("  %-34s %9s %9s %9s" % ("field", "faller%", "riser%", "r-f"))
        for k in keys:
            a, b = 100 * fm[k] / ft, 100 * rm[k] / rt
            print("  %-34s %9.2f %9.2f %+9.2f" % (k[:34], a, b, b - a))
        print("\n  arm minus full, on (riser%% - faller%%):")
        line = "  %-34s" % ""
        for n, _ in ABLATIONS:
            line += "%13s" % n
        print(line)
        for k in keys:
            line = "  %-34s" % k[:34]
            base = (100 * rm[k] / rt) - (100 * fm[k] / ft)
            for n, _ in ABLATIONS:
                afm, arm_, aft, art, _, _ = share[n]
                v = ((100 * arm_[k] / art) - (100 * afm[k] / aft)) - base
                line += "%13.2f" % v
            print(line)
        print()
    for w in fields.k_warnings().items():
        print("  k-warning %s: %s" % w)


if __name__ == "__main__":
    import sys
    e = "raw"
    if "--edge" in sys.argv:
        e = sys.argv[sys.argv.index("--edge") + 1]
    main(e)
