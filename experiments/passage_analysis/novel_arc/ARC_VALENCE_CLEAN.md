# Valence components on the cleaned lexicon (EXPLORATORY)

Producer `arc_valence_clean_components.py` (method in its docstring). Lexicon sizes (scoring forms): human 15,975, +vector 18,996. History: 9,922 Chadwyck and Chicago texts.

| component | lexicon | history range | base | aligned raw / prefill / asked | lineages unpartialled | lineages, within-condition concreteness partial |
|---|---|---|---|---|---|---|
| Negative words per content word | human | 0.0558 to 0.0831 | 0.0495 (below all) | 0.0334 (below all) / 0.0386 (below all) / 0.0429 (below all) | down 27/32 (p 0.000) / down 18/23 (p 0.011) / down 16/20 (p 0.012) | down 27/32 (p 0.000) / down 18/23 (p 0.011) / down 15/20 (p 0.041) |
| Negative words per content word | +vector | 0.0594 to 0.0914 | 0.0517 (below all) | 0.0353 (below all) / 0.0398 (below all) / 0.0443 (below all) | down 27/32 (p 0.000) / down 18/23 (p 0.011) / down 15/20 (p 0.041) | down 27/32 (p 0.000) / down 18/23 (p 0.011) / down 15/20 (p 0.041) |
| Negative intensity | human | 2.0256 to 2.1062 | 2.1287 (above all) | 2.0011 (below all) / 1.9617 (below all) / 1.9872 (below all) | down 26/32 (p 0.001) / down 18/23 (p 0.011) / down 17/20 (p 0.003) | down 28/32 (p 0.000) / down 20/23 (p 0.000) / down 19/20 (p 0.000) |
| Negative intensity | +vector | 2.0637 to 2.1531 | 2.1456 (inside) | 2.0112 (below all) / 1.9777 (below all) / 2.0029 (below all) | down 26/32 (p 0.001) / down 19/23 (p 0.003) / down 17/20 (p 0.003) | down 29/32 (p 0.000) / down 20/23 (p 0.000) / down 19/20 (p 0.000) |
| Positive words per content word | human | 0.0895 to 0.1571 | 0.1176 (inside) | 0.1881 (above all) / 0.1817 (above all) / 0.1821 (above all) | up 29/32 (p 0.000) / up 22/23 (p 0.000) / up 18/20 (p 0.000) | up 28/32 (p 0.000) / up 21/23 (p 0.000) / up 16/20 (p 0.012) |
| Positive words per content word | +vector | 0.0895 to 0.1571 | 0.1176 (inside) | 0.1881 (above all) / 0.1817 (above all) / 0.1821 (above all) | up 29/32 (p 0.000) / up 22/23 (p 0.000) / up 18/20 (p 0.000) | up 28/32 (p 0.000) / up 21/23 (p 0.000) / up 16/20 (p 0.012) |
| Positive intensity | human | 2.0277 to 2.1045 | 2.0614 (inside) | 2.0724 (inside) / 2.0448 (inside) / 1.9875 (below all) | up 18/32 (p 0.597) / down 14/23 (p 0.405) / down 16/20 (p 0.012) | up 18/32 (p 0.597) / down 14/23 (p 0.405) / down 16/20 (p 0.012) |
| Positive intensity | +vector | 2.0277 to 2.1045 | 2.0614 (inside) | 2.0724 (inside) / 2.0448 (inside) / 1.9875 (below all) | up 18/32 (p 0.597) / down 14/23 (p 0.405) / down 16/20 (p 0.012) | up 18/32 (p 0.597) / down 14/23 (p 0.405) / down 16/20 (p 0.012) |
