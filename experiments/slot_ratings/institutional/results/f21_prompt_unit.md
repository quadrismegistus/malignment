# F21's surviving claims with the design's own units

Declared arm, families, units and tests: see the producer's docstring. Cells: median | up/down | sign-test p. Family unit n=10 (9 without deepseek-7b); pair unit n=12. Re-reads F21's deepseek-chat tags; no re-tagging.

## arm = endpoint

families: amber, deepseek-7b, olmo, olmo-tiny, pythia, qwen, qwen-tiny, smol, tulu, zephyr

### apology present (share)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.005 | 6/4 | 0.75 | +0.000 | 5/5 | 1 |
| aligned gap (institution - individual) | -0.007 | 4/6 | 0.75 | -0.012 | 3/9 | 0.15 |
| change, individual side | +0.013 | 9/1 | 0.021 | +0.010 | 10/2 | 0.039 |
| change, institution side | +0.002 | 5/4 | 1 | +0.000 | 4/4 | 1 |
| change in individual minus change in institution | +0.010 | 7/3 | 0.34 | +0.010 | 10/2 | 0.039 |

### institutional deference (1-5)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.697 | 10/0 | 0.002 | +0.592 | 12/0 | 0.00049 |
| aligned gap (institution - individual) | +0.673 | 10/0 | 0.002 | +0.504 | 12/0 | 0.00049 |
| change, individual side | +0.122 | 9/1 | 0.021 | +0.206 | 12/0 | 0.00049 |
| change, institution side | +0.066 | 9/1 | 0.021 | +0.174 | 11/1 | 0.0063 |
| change in individual minus change in institution | +0.035 | 6/4 | 0.75 | +0.042 | 7/5 | 0.77 |

### agency (1-5)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.025 | 6/4 | 0.75 | +0.234 | 8/4 | 0.39 |
| aligned gap (institution - individual) | +0.040 | 6/3 | 0.51 | +0.220 | 7/5 | 0.77 |
| change, individual side | +0.270 | 10/0 | 0.002 | +0.322 | 12/0 | 0.00049 |
| change, institution side | +0.451 | 10/0 | 0.002 | +0.428 | 12/0 | 0.00049 |
| change in individual minus change in institution | -0.040 | 4/6 | 0.75 | -0.122 | 3/9 | 0.15 |

## arm = endpoint, without deepseek-7b

families: amber, olmo, olmo-tiny, pythia, qwen, qwen-tiny, smol, tulu, zephyr

### apology present (share)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.003 | 5/4 | 1 | +0.000 | 5/5 | 1 |
| aligned gap (institution - individual) | -0.007 | 4/5 | 1 | -0.009 | 3/8 | 0.23 |
| change, individual side | +0.010 | 8/1 | 0.039 | +0.004 | 10/2 | 0.039 |
| change, institution side | +0.003 | 5/3 | 0.73 | +0.000 | 5/4 | 1 |
| change in individual minus change in institution | +0.010 | 6/3 | 0.51 | +0.007 | 8/4 | 0.39 |

### institutional deference (1-5)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.707 | 9/0 | 0.0039 | +0.598 | 12/0 | 0.00049 |
| aligned gap (institution - individual) | +0.663 | 9/0 | 0.0039 | +0.507 | 12/0 | 0.00049 |
| change, individual side | +0.100 | 8/1 | 0.039 | +0.184 | 11/1 | 0.0063 |
| change, institution side | +0.057 | 8/1 | 0.039 | +0.178 | 9/3 | 0.15 |
| change in individual minus change in institution | +0.040 | 6/3 | 0.51 | +0.038 | 7/4 | 0.55 |

### agency (1-5)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.030 | 6/3 | 0.51 | +0.242 | 8/4 | 0.39 |
| aligned gap (institution - individual) | +0.010 | 5/3 | 0.73 | +0.244 | 7/5 | 0.77 |
| change, individual side | +0.343 | 9/0 | 0.0039 | +0.389 | 11/1 | 0.0063 |
| change, institution side | +0.471 | 9/0 | 0.0039 | +0.453 | 12/0 | 0.00049 |
| change in individual minus change in institution | -0.020 | 4/5 | 1 | -0.093 | 4/8 | 0.39 |

## arm = dpo

families: amber, deepseek-7b, olmo, olmo-tiny, pythia, qwen, qwen-tiny, smol, tulu, zephyr

### apology present (share)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.005 | 6/4 | 0.75 | +0.000 | 5/5 | 1 |
| aligned gap (institution - individual) | -0.007 | 3/7 | 0.34 | -0.002 | 5/6 | 1 |
| change, individual side | +0.017 | 9/1 | 0.021 | +0.008 | 9/2 | 0.065 |
| change, institution side | +0.005 | 5/4 | 1 | +0.000 | 5/4 | 1 |
| change in individual minus change in institution | +0.012 | 7/3 | 0.34 | +0.010 | 8/4 | 0.39 |

### institutional deference (1-5)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.697 | 10/0 | 0.002 | +0.592 | 12/0 | 0.00049 |
| aligned gap (institution - individual) | +0.697 | 10/0 | 0.002 | +0.464 | 12/0 | 0.00049 |
| change, individual side | +0.172 | 9/1 | 0.021 | +0.188 | 11/1 | 0.0063 |
| change, institution side | +0.042 | 8/1 | 0.039 | +0.150 | 11/1 | 0.0063 |
| change in individual minus change in institution | +0.035 | 6/4 | 0.75 | +0.048 | 8/4 | 0.39 |

### agency (1-5)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.025 | 6/4 | 0.75 | +0.234 | 8/4 | 0.39 |
| aligned gap (institution - individual) | +0.097 | 7/2 | 0.18 | +0.274 | 7/5 | 0.77 |
| change, individual side | +0.327 | 10/0 | 0.002 | +0.364 | 12/0 | 0.00049 |
| change, institution side | +0.460 | 10/0 | 0.002 | +0.452 | 12/0 | 0.00049 |
| change in individual minus change in institution | -0.040 | 2/8 | 0.11 | -0.108 | 4/8 | 0.39 |

## arm = dpo, without deepseek-7b

families: amber, olmo, olmo-tiny, pythia, qwen, qwen-tiny, smol, tulu, zephyr

### apology present (share)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.003 | 5/4 | 1 | +0.000 | 5/5 | 1 |
| aligned gap (institution - individual) | -0.007 | 3/6 | 0.51 | +0.000 | 5/5 | 1 |
| change, individual side | +0.017 | 8/1 | 0.039 | +0.009 | 9/3 | 0.15 |
| change, institution side | +0.010 | 5/3 | 0.73 | -0.000 | 5/6 | 1 |
| change in individual minus change in institution | +0.010 | 6/3 | 0.51 | +0.004 | 7/5 | 0.77 |

### institutional deference (1-5)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.707 | 9/0 | 0.0039 | +0.598 | 12/0 | 0.00049 |
| aligned gap (institution - individual) | +0.710 | 9/0 | 0.0039 | +0.462 | 12/0 | 0.00049 |
| change, individual side | +0.143 | 8/1 | 0.039 | +0.184 | 11/1 | 0.0063 |
| change, institution side | +0.035 | 7/1 | 0.07 | +0.151 | 10/2 | 0.039 |
| change in individual minus change in institution | +0.040 | 6/3 | 0.51 | +0.104 | 9/3 | 0.15 |

### agency (1-5)

| quantity | family unit | pair unit |
|---|---|---|
| base gap (institution - individual) | +0.030 | 6/3 | 0.51 | +0.242 | 8/4 | 0.39 |
| aligned gap (institution - individual) | +0.070 | 6/2 | 0.29 | +0.304 | 7/5 | 0.77 |
| change, individual side | +0.457 | 9/0 | 0.0039 | +0.438 | 11/1 | 0.0063 |
| change, institution side | +0.490 | 9/0 | 0.0039 | +0.466 | 12/0 | 0.00049 |
| change in individual minus change in institution | -0.033 | 2/7 | 0.18 | -0.078 | 4/8 | 0.39 |

