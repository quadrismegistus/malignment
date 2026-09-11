"""Do these models differ by architecture at all? 50 models, pairwise.

    python run.py --arm base        the 50 endpoint BASES
    python run.py --arm aligned     the 50 ALIGNED endpoints

One arm, one flag, one producer. The two arms are NOT on a common scale in the
sense that matters: both are z-scored against their own pooled vocabulary, so a
base-base distance and an aligned-aligned distance are comparable to each other
(same prompts, same words, same scaling) but neither is a base-to-aligned move.

FOUR MEASURES, and they do not agree about what similarity is, which is the
point of carrying all four:

    jac     Jaccard over the above-theta vocabulary -- do they even consider
            the same words? Thresholded, so a word at 0.0011 against 0.0009
            reads as total disagreement.
    wjac    the same weighted by renormalised mass, sum min / sum max.
    type    distance between mass-weighted centroids in z-scored EXTERNAL
            type-norm space (Warriner arousal/valence/dominance, Brysbaert
            concreteness). External lexicons only: the k_* family was rated
            FOR this project's construct and k_charge is the independent
            variable in `existence`, so including it would predict
            displacement with displacement.
    ctx     the same over the 12 v6 CONTEXTUAL rating scales. The seven other
            keys that travel in that dict (fall, rise, net, net_rate,
            n_eligible, n_present, ratable) are movement outcomes and are
            excluded for the same reason.
"""
import random, itertools, collections, statistics as st, json
import numpy as np
from malignment import fields as F, movement as M, roster
THETA = 0.001
CTX = ["v6_harm","v6_aggression","v6_directedness","v6_makes_better","v6_makes_worse",
       "v6_interiority","v6_deliberation","v6_superego","v6_vocalisation","v6_hedged",
       "v6_fit","v6_mundanity"]
TYPE = ["warriner_arousal","warriner_valence","warriner_dominance","brysbaert_concreteness"]
import argparse
_ap = argparse.ArgumentParser(description=__doc__,
                              formatter_class=argparse.RawDescriptionHelpFormatter)
_ap.add_argument("--arm", default="base", choices=("base", "aligned"),
                 help="which side of the 50 endpoint pairs to compare pairwise")
_ap.add_argument("--prompts", type=int, default=200)
ARGS = _ap.parse_args()
eps, _ = roster.endpoints()
#: endpoints() is keyed by base, so both arms are 50 DISTINCT models and
#: neither side can double-count a model with two siblings.
BASES = sorted(eps) if ARGS.arm == "base" else sorted(set(eps.values()))
rated = {}
for pr in F.slot_prompts():
    d = F.contextual_norms(pr, instrument="v6") or {}
    if any(any(k.startswith("v6_") for k in v) for v in d.values()):
        rated[pr] = d
random.seed(11)
sample = sorted(random.sample(sorted(rated), ARGS.prompts))
print("arm %s: %d models, %d prompts" % (ARGS.arm, len(BASES), len(sample)), flush=True)
d = M.words_multi(BASES, sample, rule_version=4)
print("prompts returned %d" % len(d), flush=True)
tn = {}
def tv(w):
    if w not in tn:
        n = F.norms(w) or {}
        tn[w] = None if any(n.get(x) is None for x in TYPE) else np.array([n[x] for x in TYPE], float)
    return tn[w]
allw = {w for pr in d for m in d[pr] for w in d[pr][m]}
TV = np.array([v for v in (tv(w) for w in allw) if v is not None])
tmu, tsd = TV.mean(0), np.where(TV.std(0)==0,1,TV.std(0))
CV = np.array([[v[k] for k in CTX] for pr in sample for v in rated[pr].values()
               if all(isinstance(v.get(k),(int,float)) for k in CTX)], float)
cmu, csd = CV.mean(0), np.where(CV.std(0)==0,1,CV.std(0))
def cen(wp, vecs):
    ks = [w for w in wp if w in vecs]; t = sum(wp[w] for w in ks)
    return None if t <= 0 else sum(vecs[w]*(wp[w]/t) for w in ks)
acc = collections.defaultdict(lambda: collections.defaultdict(list))
for pr in sample:
    bym = d.get(pr, {})
    tvec = {w:(tv(w)-tmu)/tsd for w in {w for m in bym for w in bym[m]} if tv(w) is not None}
    cvec = {w:(np.array([v[k] for k in CTX],float)-cmu)/csd for w,v in rated[pr].items()
            if all(isinstance(v.get(k),(int,float)) for k in CTX)}
    W, Ct, Cc = {}, {}, {}
    for m in BASES:
        wp = {w:p for w,p in bym.get(m,{}).items() if p >= THETA}
        if not wp: continue
        W[m] = wp; Ct[m] = cen(wp, tvec); Cc[m] = cen(wp, cvec)
    for a, b in itertools.combinations(sorted(W), 2):
        A, B = W[a], W[b]
        k = (a, b)
        acc[k]["jac"].append(len(set(A)&set(B))/len(set(A)|set(B)))
        sa, sb = sum(A.values()), sum(B.values())
        pa = {w:A[w]/sa for w in A}; pb = {w:B[w]/sb for w in B}
        u = set(pa)|set(pb)
        acc[k]["wjac"].append(sum(min(pa.get(w,0),pb.get(w,0)) for w in u)/
                              sum(max(pa.get(w,0),pb.get(w,0)) for w in u))
        if Ct[a] is not None and Ct[b] is not None:
            acc[k]["type"].append(float(np.linalg.norm(Ct[a]-Ct[b])))
        if Cc[a] is not None and Cc[b] is not None:
            acc[k]["ctx"].append(float(np.linalg.norm(Cc[a]-Cc[b])))
out = {}
for (a, b), r in acc.items():
    if not r["jac"]: continue
    out["%s|%s" % (a, b)] = {k: st.median(v) for k, v in r.items() if v}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "results_%s.json" % ARGS.arm)
json.dump({"arm": ARGS.arm, "n_models": len(BASES), "n_prompts": len(sample),
           "theta": THETA, "pairs": out}, open(OUT, "w"), indent=0)
print("wrote %d pairs -> %s" % (len(out), os.path.basename(OUT)), flush=True)
