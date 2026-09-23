#!/bin/bash
D=/Users/rj416/github/malignment/experiments/displacement/existence
PY=/Users/rj416/github/malignment/.venv/bin/python
cd "$D"
$PY -u adjacency.py --flow --grain fine --perm 32 --min-prompts 10 \
    --senses --drop-fragments --abstain drop --max-freq 2000 --pos VERB \
    --csv results/flow_fine_allsrc_verb.csv \
    --examples results/flow_fine_allsrc_verb_examples.csv 2>&1 | grep -vE '^Extracting|it/s\]'
echo "######## DONE"
