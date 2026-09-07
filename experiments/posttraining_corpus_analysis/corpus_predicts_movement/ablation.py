"""THE ABLATION, and it is the folder's most important number.

K-rank profile AUC 0.5811 | LENGTH ALONE 0.5651 | UNIGRAM tf-idf 0.7135.

PKU's preference signal is substantially LEXICAL, not norm-shaped, so the
main run's transfer went through a channel explaining a minority of it. Also
partials length out of beta: K residualised on length is 0.5805 against 0.5811
raw, so beta is not a length artifact.
"""
import sys, numpy as np
sys.path.insert(0,'.'); sys.path.insert(0,'experiments/posttraining_corpus_analysis/pku-safe-rlhf')
import run as PKU
assert hasattr(PKU,'k_ranks')
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import roc_auc_score
d=PKU.load("train"); dims,ranks=PKU.k_ranks()
idx=list(range(len(d["prompt"])))
F=PKU.features(d,idx,dims,ranks)
A,B=F["texts"]
y=np.asarray([1 if d["safer_response_id"][i]==0 else 0 for i in idx])
rng=np.random.default_rng(20260907); tr=rng.random(len(y))<0.7
print("PKU, safer_response_id, n=%d, same split as the main run"%len(y))
# 1. norm profile (the beta features)
X=F["k"]; keep=np.isfinite(X).all(axis=1)
m=LogisticRegression(max_iter=3000,solver="liblinear").fit(X[tr&keep],y[tr&keep])
print("  K-rank profile (7 dims)        AUC %.4f"%roc_auc_score(y[~tr&keep],m.decision_function(X[~tr&keep])))
# 2. length alone -- the known leak
L=F["len"]
m=LogisticRegression(max_iter=3000,solver="liblinear").fit(L[tr],y[tr])
print("  LENGTH ALONE                   AUC %.4f   <- the known confound"%roc_auc_score(y[~tr],m.decision_function(L[~tr])))
# 3. unigram difference
v=TfidfVectorizer(max_features=20000,lowercase=True,sublinear_tf=True)
v.fit([t for t in A[:20000]]+[t for t in B[:20000]])
XA=v.transform(A); XB=v.transform(B); XU=XA-XB
m=LogisticRegression(max_iter=2000,solver="liblinear").fit(XU[tr],y[tr])
print("  UNIGRAM tf-idf difference      AUC %.4f"%roc_auc_score(y[~tr],m.decision_function(XU[~tr])))
