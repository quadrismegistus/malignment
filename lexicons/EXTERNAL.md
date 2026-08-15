# External data this repo does NOT contain, and must not

`malignment` is a **public** repository. Two data sources `fields.py` uses are
licensed or mixed-licence, and neither may be committed here.

| source | size | status | used for |
|---|---|---|---|
| `~/Dropbox/Prof/Code/osp/worddb.byu.txt` | 10.3 MB | **LICENSED — never commit.** BYU corpora (COCA/COHA) are purchased access; redistribution is prohibited. | surface → (lemma, CLAWS pos) over 86,403 forms; 31% of forms have a lemma differing from the surface |
| `~/Dropbox/Prof/Articles/TheoryMachines/norms_sources/` | 76 MB | **MIXED — check per file before ever publishing one.** Warriner VAD and Brysbaert concreteness are generally free for research; SUBTLEX-CH, `brooke_formality`, the Chinese concreteness set and `llm_martinez` are not uniformly so. | valence/arousal/dominance, concreteness, formality |

## The rule that matters more than the paths

**A missing external source must REFUSE, not degrade.** `fields.py` in the
archive does `if not os.path.exists(BYU): return ...` — so on any machine without
Dropbox it returns *fewer counts*, not an error, and the analysis quietly measures
something else. That is the same absent-vs-zero shape this repo exists to reject:
a result computed without a lexicon is not a smaller result, it is a different
one.

So when `fields` is ported: every external source is checked at import, its
absence is NAMED, and any function depending on it raises rather than returning a
partial count. A clone of this repo either has the data and says so, or does not
and says that.
