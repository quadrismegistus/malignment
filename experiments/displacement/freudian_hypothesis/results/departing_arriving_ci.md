# An interval on the affect-intensity null

Producer `departing_arriving_ci.py` (paper seat's check 2, 2026-09-24, post hoc). 50 English endpoint lineages carrying all four scales; 25 SFT clusters. Per-lineage values from `departing_arriving.compute()`. Anchor v6:harm, median -0.1635. 10000 resamples, percentile 95% intervals.

| scale | median | lineage 95% CI | cluster 95% CI | ratio to |harm| | lineage ratio CI | cluster ratio CI | |ratio| 95th pct, lineage / cluster |
|---|---|---|---|---|---|---|---|
| k_charge | +0.0072 | [-0.0853, +0.0544] | [-0.1220, +0.0611] | +4.4% | [-46.0%, +37.0%] | [-64.6%, +37.7%] | 41.6% / 58.5% |
| inst:arousal | -0.0373 | [-0.1052, +0.0426] | [-0.1318, +0.0332] | -22.8% | [-60.7%, +28.0%] | [-72.9%, +20.7%] | 53.3% / 59.6% |
| warriner_arousal | -0.0726 | [-0.1386, -0.0431] | [-0.1386, -0.0456] | -44.4% | [-77.6%, -27.3%] | [-78.0%, -30.1%] | 69.5% / 64.1% |

Ratio = median(scale) / |median(v6:harm)| within each resample; negative means the scale fell (the same direction as harm).
