# USAS X words by kind (EXPLORATORY)

Producer `interiority_candidates.py --seeds`. Every primary-sense USAS X word less NLTK stopwords, 3225 words (the abstraction seat's seed list was 2,826 under a rule not reproduced here), each rated twice by deepseek-v4-flash (resolved: deepseek-flash) at temperature 0 in shuffled batches of 40, the same InteriorityCandidateTask and prompt as the candidates, anchors dread, grief, door, walk. Ratings: /Users/rj416/malignment-data/interiority_norms/usasx_ratings_v1.parquet; per word: /Users/rj416/malignment-data/interiority_norms/usasx_kinds_v1.csv.

- interior (0-3) between passes: exact 77.1%, within one 99.4%, Spearman 0.904; kind agreement 87.2%
- anchors: door interior [0] kind ['other'] (n=162); dread interior [3] kind ['emotion'] (n=162); grief interior [3] kind ['emotion'] (n=162); walk interior [0] kind ['other'] (n=162)
- mean interior over all X words: 1.44; share rated >= 2 in both passes: 44.9%

## X subfield by agreed kind (words; a word in two subfields counts in both)

| subfield | n | mean interior | cognition | emotion | volition | perception | attention | argument | other | mixed |
|---|---|---|---|---|---|---|---|---|---|---|
| X1 | 72 | 1.80 | 22 | 12 | 0 | 5 | 1 | 9 | 11 | 12 |
| X2 | 35 | 2.50 | 26 | 0 | 1 | 1 | 0 | 0 | 3 | 4 |
| X2.1 | 318 | 2.16 | 214 | 13 | 12 | 5 | 3 | 28 | 21 | 22 |
| X2.2 | 225 | 1.58 | 125 | 1 | 0 | 9 | 2 | 10 | 53 | 25 |
| X2.3 | 24 | 2.27 | 21 | 0 | 0 | 1 | 0 | 0 | 1 | 1 |
| X2.4 | 258 | 1.22 | 75 | 0 | 12 | 16 | 18 | 37 | 59 | 41 |
| X2.5 | 150 | 2.32 | 105 | 16 | 0 | 5 | 0 | 1 | 11 | 12 |
| X2.6 | 101 | 2.02 | 39 | 32 | 1 | 0 | 2 | 5 | 7 | 15 |
| X3 | 12 | 2.54 | 2 | 1 | 0 | 6 | 0 | 0 | 0 | 3 |
| X3.1 | 62 | 0.93 | 0 | 4 | 0 | 36 | 0 | 0 | 11 | 11 |
| X3.2 | 336 | 0.50 | 4 | 10 | 0 | 85 | 1 | 1 | 152 | 83 |
| X3.3 | 22 | 0.86 | 0 | 3 | 0 | 10 | 0 | 0 | 9 | 0 |
| X3.4 | 154 | 1.55 | 5 | 0 | 0 | 97 | 11 | 0 | 23 | 18 |
| X3.5 | 34 | 0.84 | 0 | 0 | 0 | 25 | 0 | 0 | 6 | 3 |
| X4.1 | 103 | 1.52 | 41 | 1 | 0 | 6 | 0 | 30 | 14 | 11 |
| X4.2 | 48 | 0.28 | 3 | 0 | 0 | 0 | 0 | 14 | 21 | 10 |
| X5.1 | 100 | 2.27 | 11 | 7 | 3 | 2 | 56 | 0 | 8 | 13 |
| X5.2 | 341 | 1.76 | 4 | 114 | 38 | 3 | 47 | 0 | 90 | 45 |
| X6 | 64 | 1.62 | 15 | 0 | 21 | 0 | 0 | 3 | 13 | 12 |
| X7 | 347 | 1.51 | 23 | 10 | 146 | 2 | 11 | 6 | 112 | 37 |
| X7.2 | 1 | 1.00 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| X8 | 43 | 1.49 | 0 | 1 | 21 | 0 | 0 | 1 | 16 | 4 |
| X9 | 2 | 1.50 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| X9.1 | 207 | 0.97 | 57 | 0 | 2 | 1 | 0 | 1 | 121 | 25 |
| X9.2 | 213 | 0.56 | 11 | 17 | 5 | 0 | 0 | 1 | 169 | 10 |

## X words the rater does not read as inner states (agreed kind argument or other, mean interior < 1.5)

1054 words, e.g.: yowl, yelp, text-analysis, intruder, intrusion, testers, tester, investigatory, irradical, ism, jack-asses, jackass, jettisoning, jumble, k-based, k-economy, k-economy-based, k-economy-driven, k-worker, k-workers, intelligentsia, knock, instantiations, inspectorate, imperialism, inconspicuous, thriller, ineffectual, inefficiency, inefficient, inefficiently, theory, themeless, themed, infamous, informants, informatician, informaticians, informatics, inquisition, inroad, inroads, insider, instantiation, knocked, knocking, tenet, take-off, meander, means, medallist, medline, mega-projects, mega-successful, tail, metadata, tactically, method, methodological, methodology, mews, milestones, mimas, mini-review, mini-topics, mode, marxism-leninism, marxism, manifesto, manhunt, landfill, landslide, last-minute-goal, technique, leaden-footed, legendary, leitmotif, leninism, litterbin, ill-fated
