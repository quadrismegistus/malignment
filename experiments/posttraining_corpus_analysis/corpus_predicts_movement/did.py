"""The paired TREATED-minus-PLACEBO contrast, per prompt. Null: median +0.0074,
sign p=0.212, Wilcoxon p=0.715.

NOTE THE IMPORT ORDER. `import run` resolves to whichever directory is first on
sys.path, and this folder ALSO has a run.py. The assert is not decoration: the
first version of this file imported itself and died on a missing k_ranks.
"""
import sys, os, json, importlib.util
HERE='experiments/posttraining_corpus_analysis/corpus_predicts_movement'
sys.path.insert(0,'.'); sys.path.insert(0,'experiments/posttraining_corpus_analysis/pku-safe-rlhf')
import numpy as np
import run as PKU          # the SIBLING: path order matters, see below
assert hasattr(PKU,'k_ranks'), "imported the wrong run.py"
spec=importlib.util.spec_from_file_location("cpm", os.path.join(HERE,"run.py"))
cpm=importlib.util.module_from_spec(spec); spec.loader.exec_module(cpm)
R=json.load(open(os.path.join(HERE,'results','run.json')))
b=np.asarray(R['beta']['safer_response_id']['beta'])
dims,ranks=PKU.k_ranks()
from malignment import vectors as V
q="SELECT prompt FROM twp_words_v4_best WHERE model={m:String} GROUP BY prompt ORDER BY prompt LIMIT {n:UInt32}"
prompts=[r['prompt'] for r in V.rows(q,m=cpm.BEAVER,n=700)]
prof=cpm.profiles([cpm.LLAMA,cpm.ALPACA,cpm.BEAVER],prompts,dims,ranks)
pl=dict(cpm.project(prof,cpm.LLAMA,cpm.ALPACA,prompts,b))
tr=dict(cpm.project(prof,cpm.ALPACA,cpm.BEAVER,prompts,b))
both=[p for p in prompts if p in pl and p in tr]
d=[tr[p]-pl[p] for p in both]
up,dn,p=cpm.sign_test(d)
print("PAIRED DiD: TREATED minus PLACEBO, per prompt")
print("  n=%d  median %+.5f  mean %+.5f  %d up / %d dn  sign p=%.3g"%(len(d),np.median(d),np.mean(d),up,dn,p))
from scipy import stats
print("  Wilcoxon p=%.3g"%stats.wilcoxon(d).pvalue)
print()
for lab,dd in (('placebo',list(pl.values())),('treated',list(tr.values()))):
    print("  %-8s median proj %+.5f   median |proj| %.5f"%(lab,np.median(dd),np.median(np.abs(dd))))
