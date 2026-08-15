# Psycholinguistic norms — public, cited, committed

Both are supplementary material published with their papers and freely available
for research use. They are the only two files `fields.py` reads out of a 76 MB
external collection, so the rest stays out.

| file | norms | cite |
|---|---|---|
| `BRM-emot-submit.csv` | valence, arousal, dominance for 13,915 English lemmas | Warriner, A.B., Kuperman, V., & Brysbaert, M. (2013). Norms of valence, arousal, and dominance for 13,915 English lemmas. *Behavior Research Methods* 45, 1191–1207. |
| `Concreteness_ratings_Brysbaert_et_al_BRM.txt` | concreteness for 40,000 English lemmas | Brysbaert, M., Warriner, A.B., & Kuperman, V. (2014). Concreteness ratings for 40 thousand generally known English word lemmas. *Behavior Research Methods* 46, 904–911. |

**Cite them where their numbers are used.** A norm set is data someone collected
from human raters; using it without citation is the ordinary academic failure,
and it is easier to get right when the citation sits beside the file.

## What is deliberately NOT here

`~/Dropbox/Prof/Articles/TheoryMachines/norms_sources/` also holds SUBTLEX-US and
SUBTLEX-CH, `chantse.zip`, `brooke_formality`, `llm_martinez` and Chinese
concreteness ratings. **Nothing reads them.** They are not excluded on licence
grounds — they are excluded because an unused 70 MB in a repository is how a
directory stops being readable.

`lexicons/external/` (gitignored) holds `worddb.byu.txt`, which IS licensed —
BYU corpora are purchased access. It is used only as a lemmatiser and is being
replaced by spaCy, which is free, already a dependency, and contextual rather
than type-level.
