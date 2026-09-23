#!/bin/bash
D=/Users/rj416/github/malignment/experiments/displacement/existence
PY=/Users/rj416/github/malignment/.venv/bin/python
cd "$D"
echo "######## COARSE config-of-record + --pos VERB"
$PY -u adjacency.py --flow --grain letter --perm 32 --min-prompts 10 \
    --senses --drop-fragments --abstain drop --max-freq 2000 --pos VERB \
    --csv results/flow_letter_verb.csv \
    --examples results/flow_letter_verb_examples.csv 2>&1 | grep -vE '^Extracting|it/s\]'
echo "######## FINE (L1-, E3-) same + --pos VERB"
$PY -u adjacency.py --flow --grain fine --perm 32 --min-prompts 10 \
    --source L1- --source E3- --senses --drop-fragments --abstain drop \
    --max-freq 2000 --pos VERB \
    --csv results/flow_fine_verb.csv \
    --examples results/flow_fine_verb_examples.csv 2>&1 | grep -vE '^Extracting|it/s\]'
echo "######## DONE"
