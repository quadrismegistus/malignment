# Type-norm coverage over arc_fiction (EXPLORATORY)

Producer `arc_norm_coverage.py`. Share of a text's content tokens (alphabetic, expanded stopwords out) whose form a norm source covers; `raw` = the source's own forms, `exp` = plus MorphAdorner variants and long-s readings. Decade median over texts with >= 2000 content tokens (75,974 texts). Set sizes: warriner_raw 13,780, warriner_exp 65,947, brysbaert_raw 36,914, brysbaert_exp 154,936, k_raw 24,497, k_exp 102,683. Warriner's three scales share one word set; the k lexicon's scales share another.

| decade | texts | warriner_raw | warriner_exp | brysbaert_raw | brysbaert_exp | k_raw | k_exp |
|---|---|---|---|---|---|---|---|
| 1600 | 45 | 47.1% | 50.6% | 72.0% | 76.6% | 78.6% | 80.3% |
| 1610 | 28 | 40.2% | 50.2% | 59.0% | 76.9% | 62.4% | 81.0% |
| 1620 | 25 | 46.1% | 50.9% | 71.5% | 77.9% | 77.2% | 81.2% |
| 1630 | 38 | 46.4% | 51.3% | 70.1% | 76.9% | 75.0% | 81.3% |
| 1640 | 21 | 42.6% | 48.6% | 66.5% | 74.8% | 67.2% | 78.3% |
| 1650 | 40 | 49.4% | 50.7% | 76.9% | 77.6% | 80.4% | 80.8% |
| 1660 | 32 | 49.0% | 50.1% | 75.7% | 77.1% | 79.1% | 80.8% |
| 1670 | 35 | 51.6% | 52.0% | 78.1% | 79.2% | 82.1% | 82.8% |
| 1680 | 78 | 51.1% | 52.3% | 77.6% | 78.4% | 81.8% | 82.6% |
| 1690 | 51 | 51.3% | 51.8% | 77.1% | 78.7% | 80.7% | 82.0% |
| 1700 | 18 | 50.5% | 51.7% | 75.7% | 77.6% | 78.9% | 81.0% |
| 1710 | 23 | 50.2% | 51.9% | 73.3% | 76.0% | 77.4% | 80.3% |
| 1720 | 58 | 51.7% | 53.4% | 76.6% | 78.5% | 81.4% | 82.5% |
| 1730 | 29 | 50.7% | 52.3% | 74.6% | 77.1% | 78.5% | 80.1% |
| 1740 | 35 | 51.3% | 52.4% | 77.1% | 78.3% | 81.6% | 82.7% |
| 1750 | 70 | 51.9% | 52.7% | 76.8% | 77.8% | 81.4% | 82.5% |
| 1760 | 86 | 51.3% | 52.5% | 76.0% | 77.1% | 80.1% | 81.1% |
| 1770 | 78 | 52.1% | 52.8% | 76.0% | 77.0% | 80.7% | 82.0% |
| 1780 | 89 | 51.9% | 52.7% | 75.6% | 76.8% | 80.6% | 81.4% |
| 1790 | 214 | 51.4% | 52.1% | 75.6% | 76.4% | 80.5% | 81.3% |
| 1800 | 483 | 49.5% | 50.2% | 73.0% | 73.9% | 78.9% | 79.7% |
| 1810 | 796 | 50.5% | 51.2% | 74.4% | 75.1% | 80.3% | 80.9% |
| 1820 | 1288 | 51.0% | 51.5% | 75.7% | 76.3% | 81.9% | 82.4% |
| 1830 | 1825 | 51.4% | 51.9% | 76.3% | 76.8% | 82.6% | 83.0% |
| 1840 | 2813 | 51.4% | 51.9% | 76.4% | 77.0% | 83.2% | 83.6% |
| 1850 | 3733 | 51.8% | 52.3% | 77.2% | 77.7% | 84.5% | 84.9% |
| 1860 | 3826 | 51.5% | 52.0% | 76.9% | 77.4% | 84.6% | 84.9% |
| 1870 | 4870 | 51.6% | 52.0% | 77.1% | 77.7% | 85.0% | 85.3% |
| 1880 | 7073 | 51.6% | 52.1% | 77.3% | 77.8% | 85.2% | 85.5% |
| 1890 | 11378 | 51.7% | 52.1% | 77.4% | 77.9% | 85.4% | 85.7% |
| 1900 | 11282 | 51.7% | 52.1% | 77.8% | 78.3% | 86.3% | 86.6% |
| 1910 | 10861 | 51.6% | 52.1% | 78.1% | 78.6% | 87.0% | 87.3% |
| 1920 | 3612 | 51.5% | 51.9% | 77.8% | 78.3% | 86.9% | 87.2% |
| 1930 | 1113 | 51.1% | 51.4% | 77.8% | 78.2% | 87.1% | 87.4% |
| 1940 | 955 | 50.9% | 51.3% | 78.2% | 78.6% | 87.9% | 88.1% |
| 1950 | 797 | 51.4% | 51.7% | 78.6% | 79.0% | 88.1% | 88.4% |
| 1960 | 756 | 51.5% | 51.8% | 78.3% | 78.7% | 88.1% | 88.2% |
| 1970 | 1059 | 51.2% | 51.6% | 77.8% | 78.2% | 87.8% | 88.0% |
| 1980 | 1775 | 50.8% | 51.1% | 77.4% | 77.8% | 88.0% | 88.2% |
| 1990 | 3390 | 50.6% | 51.0% | 77.0% | 77.3% | 88.9% | 89.1% |
| 2000 | 1196 | 50.5% | 50.9% | 76.2% | 76.5% | 88.7% | 88.9% |

## Most frequent content forms that no source covers after expansion, per century

- C17: hath, quoth, princes, lest, desires, thither, withal, humour, judgement, valour, durst, lovers, leagues, affections, subjects, degrees, wherewith, shalt, pleasures, fortunes, honourable, polexander, sancho, insomuch, mansoul, thereupon, defence, misfortunes, favours, lysis, thine, endeavour, desiring, occasions, dost, commands, countries, endeavoured, christians, amadis, miseries, morrow, discourses, soever, etc, melintus, obar, wives, ebar, charms, entreat, wars, islands, nations, virtues, abar, colours, endeavours, qualities, husbands
- C18: ihe, sentiments, hath, behaviour, charms, fhe, fie, cecilia, misfortunes, virtues, wou, pleasures, dearest, affections, occasioned, louisa, thither, lest, chevalier, desires, humour, sussex, endeavour, wblank, favourable, endeavoured, occasions, endeavored, sancho, lovers, apprehensions, iii, camilla, commands, subjects, qualities, inclinations, motives, sufferings, sorrows, degrees, arguments, beauties, advantages, afforded, quixote, delvile, ay, nations, talents, leonora, views, obligations, suspicions, quoth, duties, fellows, ast, opinions, graces
- C19: quot, apos, yon, avas, iii, ay, hath, tones, duties, fellows, lest, dearest, lt, tbe, hugh, avith, gt, bis, tion, slightest, habits, remarks, subjects, herbert, thle, views, occasions, tl, affections, europe, opinions, lhe, lovers, qualities, tlie, von, sentiments, svo, charms, thither, thine, pleasures, humour, wives, ef, afforded, baronet, maud, suspicions, cecil, etc, motives, defence, attentions, horace, rector, gerald, alfred, maurice, vou
- C20: quot, apos, fellows, hugh, tones, lest, slightest, europe, von, duties, hath, boston, chances, sylvia, dearest, wives, remarks, ay, francis, occasions, howard, lovers, glances, views, nicholas, intervals, blows, cents, judith, maurice, pierre, hats, wid, constance, iii, comrades, subjects, ef, finest, fools, humour, habits, gerald, islands, herr, offices, qualities, dresses, julian, francisco, belongs, gregory, owen, tricks, possibilities, opinions, alfred, flowed, desires, suspicions
- C21: langdon, lorn, judith, hugh, whandall, angie, evers, owen, donovan, toussaint, kahlan, kenny, jada, antonio, kent, anita, ronnie, rosalind, khalil, kamoj, norman, cora, jefferson, adele, conrad, anakin, drouillard, dagnarus, boston, elisabeth, gabriel, nathaniel, peyton, spencer, stuart, gareth, vyrl, yonah, entreri, mao, jesselynn, lan, circles, terry, nicci, wives, edmund, emerson, ramses, mattie, abe, russell, connie, howard, melanie, marlowe, rutledge, maud, francis, celeste
