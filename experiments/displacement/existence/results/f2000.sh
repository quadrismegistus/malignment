#!/bin/bash
D=/Users/rj416/github/malignment/experiments/displacement/existence
PY=/Users/rj416/github/malignment/.venv/bin/python
cd "$D"
echo "######## COARSE clean + --max-freq 2000"
$PY -u adjacency.py --flow --grain letter --perm 32 --min-prompts 10 \
    --senses --drop-fragments --abstain drop --max-freq 2000 \
    --csv results/flow_letter_f2000.csv \
    --examples $HOME/malignment-data/existence/flow_letter_f2000_examples.csv 2>&1 | grep -vE '^Extracting|it/s\]'
echo "######## FINE (L1-, E3-) clean + --max-freq 2000"
$PY -u adjacency.py --flow --grain fine --perm 32 --min-prompts 10 \
    --source L1- --source E3- --senses --drop-fragments --abstain drop --max-freq 2000 \
    --csv results/flow_fine_f2000.csv \
    --examples $HOME/malignment-data/existence/flow_fine_f2000_examples.csv 2>&1 | grep -vE '^Extracting|it/s\]'
echo "######## DONE"
