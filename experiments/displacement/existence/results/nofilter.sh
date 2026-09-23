#!/bin/bash
D=/Users/rj416/github/malignment/experiments/displacement/existence
PY=/Users/rj416/github/malignment/.venv/bin/python
cd "$D"
echo "######## COARSE senses+fragments+abstain-drop, NO --max-freq"
$PY -u adjacency.py --flow --grain letter --perm 32 --min-prompts 10 \
    --senses --drop-fragments --abstain drop \
    --csv results/flow_letter_clean.csv \
    --examples results/flow_letter_clean_examples.csv 2>&1 | grep -vE '^Extracting|it/s\]'
echo "######## FINE (L1-, E3-) same flags"
$PY -u adjacency.py --flow --grain fine --perm 32 --min-prompts 10 \
    --source L1- --source E3- --senses --drop-fragments --abstain drop \
    --csv results/flow_fine_clean.csv \
    --examples results/flow_fine_clean_examples.csv 2>&1 | grep -vE '^Extracting|it/s\]'
echo "######## DONE"
