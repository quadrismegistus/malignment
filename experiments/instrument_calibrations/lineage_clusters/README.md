---
kind: calibration
status: RUN
headline: "Grouping the 50 endpoint lineages by the SFT data they declare leaves 33, 25 or 16 units depending on how conservatively shared data is counted. kill falls and selectivity holds on cluster medians at every grouping; scream rises at 33 and 25 units but not at 16 (12/16, p=0.077). 22 of 50 endpoints name no dataset, so undeclared cross-developer sharing is invisible to all of it."
---
# lineage_clusters — are the "X of 50 lineages" counts 50 independent units?

    python clusters.py     # the three groupings and their sizes
    python test.py         # -> results/cluster_tests.md

Built 2026-09-24 for the paper seat, after an outside review of the draft pointed out that many lineages share SFT data (ShareGPT-style distillation, UltraChat, Tulu mixtures). Reanalysis only.

`clusters.py` assigns each endpoint lineage from its attestation claims (`roster/models/attestations.json`), with the reason on every row, under three groupings, least to most conservative:

- **PRETRAIN** (33 clusters): base developer.
- **SFT** (25): dominant declared SFT source family (TULU, H4, DISTILL, CROWD, PKU, SMOLTALK, NEMOTRON, XP3), else endpoint developer.
- **UNION** (16): connected components over any shared named source or developer. One component holds 32 of the 50, so this is close to the upper bound on dependence the record supports.

`test.py` reruns English content-selectivity (40/50) and the kill→scream exhibit (44/50, 42/50) with the cluster as the unit, two ways: a sign test over cluster medians, and one lineage drawn per cluster, 10,000 draws. Results in `results/cluster_tests.md`. Other consumers can import `clusters.grouping(name)`; `freudian_hypothesis/departing_arriving_ci.py` uses SFT for its cluster bootstrap.

**The fence.** 22 of 50 endpoints name no public SFT dataset. They are grouped by developer, so data shared across developers among them is invisible here. The groupings are the attestations' account of shared data, not a measurement of it; family assignment for multi-source mixes is a judgment recorded row by row.
