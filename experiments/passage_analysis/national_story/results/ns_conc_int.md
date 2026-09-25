# National stories on the literary-history instruments, bare and prefilled

Producer `ns_conc_int.py` (paper seat, 2026-09-25; read-only). Judged pure stories from `conflict.sqlite`, endpoint lineages, frames raw and prefill (the prefill cell used each model's DEFAULT system prompt), Qwen3-8B's prefill cell dropped; novel_arc's Scorer over 200-word chunks, a story's value the median over its chunks; per-lineage medians over at least 5 stories; sign tests over lineages, ties dropped.

```
stories scored: 4875 | lineages: 36

==== DEMONYM stories
  rh_absconc_median (z, high = concrete)
    base_raw         pooled median  -0.0113 | lineage mean   0.0086, median   0.0261 | 1344 stories, 33 lineages
    aligned_raw      pooled median  -0.2260 | lineage mean  -0.2433, median  -0.2452 | 1404 stories, 34 lineages
    aligned_prefill  pooled median  -0.1989 | lineage mean  -0.2051, median  -0.2273 | 1519 stories, 25 lineages
    ARM   base -> aligned, bare      median diff  -0.2706 | up  4 / down 27 of 31 | sign p 3.4e-05
    FRAME aligned bare -> prefilled  median diff  +0.0700 | up 17 / down  7 of 24 | sign p 0.0639
  usas_x (percent of content words)
    base_raw         pooled median  12.7907 | lineage mean  12.6726, median  12.7907 | 1344 stories, 33 lineages
    aligned_raw      pooled median  14.4258 | lineage mean  14.5063, median  14.6679 | 1404 stories, 34 lineages
    aligned_prefill  pooled median  15.0741 | lineage mean  14.9890, median  15.1791 | 1519 stories, 25 lineages
    ARM   base -> aligned, bare      median diff  +1.4960 | up 27 / down  4 of 31 | sign p 3.4e-05
    FRAME aligned bare -> prefilled  median diff  +0.2332 | up 16 / down  8 of 24 | sign p 0.152

==== NONE stories
  rh_absconc_median (z, high = concrete)
    base_raw         pooled median   0.1194 | lineage mean   0.1309, median   0.1244 |  202 stories, 21 lineages
    aligned_raw      pooled median  -0.1267 | lineage mean  -0.1080, median  -0.1369 |  182 stories, 18 lineages
    aligned_prefill  pooled median  -0.0602 | lineage mean  -0.0686, median  -0.0478 |  224 stories, 24 lineages
    ARM   base -> aligned, bare      median diff  -0.1412 | up  3 / down  7 of 10 | sign p 0.344
    FRAME aligned bare -> prefilled  median diff  +0.0564 | up 10 / down  1 of 11 | sign p 0.0117
  usas_x (percent of content words)
    base_raw         pooled median  13.4524 | lineage mean  13.7990, median  13.7089 |  202 stories, 21 lineages
    aligned_raw      pooled median  15.5556 | lineage mean  15.4196, median  15.7684 |  182 stories, 18 lineages
    aligned_prefill  pooled median  16.1453 | lineage mean  16.2849, median  16.1786 |  224 stories, 24 lineages
    ARM   base -> aligned, bare      median diff  +1.8958 | up  8 / down  2 of 10 | sign p 0.109
    FRAME aligned bare -> prefilled  median diff  +0.1906 | up  6 / down  5 of 11 | sign p 1

==== ALL stories
  rh_absconc_median (z, high = concrete)
    base_raw         pooled median   0.0079 | lineage mean   0.0223, median   0.0412 | 1546 stories, 33 lineages
    aligned_raw      pooled median  -0.2130 | lineage mean  -0.2227, median  -0.2292 | 1586 stories, 34 lineages
    aligned_prefill  pooled median  -0.1787 | lineage mean  -0.1815, median  -0.1981 | 1743 stories, 26 lineages
    ARM   base -> aligned, bare      median diff  -0.2316 | up  3 / down 28 of 31 | sign p 4.65e-06
    FRAME aligned bare -> prefilled  median diff  +0.0697 | up 18 / down  7 of 25 | sign p 0.0433
  usas_x (percent of content words)
    base_raw         pooled median  12.8229 | lineage mean  12.6883, median  12.8658 | 1546 stories, 33 lineages
    aligned_raw      pooled median  14.4578 | lineage mean  14.5628, median  14.6897 | 1586 stories, 34 lineages
    aligned_prefill  pooled median  15.1754 | lineage mean  15.1324, median  15.1076 | 1743 stories, 26 lineages
    ARM   base -> aligned, bare      median diff  +1.7957 | up 26 / down  5 of 31 | sign p 0.000192
    FRAME aligned bare -> prefilled  median diff  +0.3566 | up 15 / down 10 of 25 | sign p 0.424
```
