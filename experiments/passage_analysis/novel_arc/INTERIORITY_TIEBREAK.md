# Tie-break pass and consensus ratings (EXPLORATORY)

Producer `interiority_candidates.py --tiebreak / --consensus` (and `--seeds`). Where a word's two ratings disagreed on interior (0-3) or kind, a THIRD rating was taken in a fresh shuffle with the same task, prompt and anchors. Consensus: interior = median of the ratings; kind = the majority label, 'mixed' if all three differ. Words whose first two ratings agreed keep them. Two-pass readouts: INTERIORITY_CANDIDATES.md, USAS_X_KINDS.md.

## Candidates (period-model neighbours)

- words 5383; tie-broken 1478 (27.5%); after the third rating, kind still 'mixed' (all three differ) for 38
- pass-3 anchors: door interior [0] kind ['other'] (n=37); think interior [3] kind ['cognition'] (n=37); walk interior [0] kind ['other'] (n=37); wonder interior [3] kind ['cognition', 'emotion'] (n=37)
- consensus interior >= 2 with a mental kind: 2161 words (cognition 838, emotion 837, volition 323, perception 91, attention 72)
- consensus kinds, all words: other 2347, cognition 1011, emotion 904, argument 464, volition 387, perception 152, attention 80, mixed 38
- per word: /Users/rj416/malignment-data/interiority_norms/candidate_consensus_v1.csv

## USAS X words

- words 3225; tie-broken 964 (29.9%); after the third rating, kind still 'mixed' (all three differ) for 26
- pass-3 anchors: door interior [0] kind ['other'] (n=25); dread interior [3] kind ['emotion'] (n=25); grief interior [3] kind ['emotion'] (n=25); walk interior [0] kind ['other'] (n=25)
- consensus interior >= 2 with a mental kind: 1526 words (cognition 754, emotion 242, volition 237, perception 153, attention 140)
- consensus kinds, all words: other 1051, cognition 864, perception 393, volition 292, emotion 268, argument 175, attention 156, mixed 26
- per word: /Users/rj416/malignment-data/interiority_norms/usasx_consensus_v1.csv

