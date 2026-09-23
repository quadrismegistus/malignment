#!/bin/bash
D=/Users/rj416/github/malignment/experiments/displacement/existence
PY=/Users/rj416/github/malignment/.venv/bin/python
cd "$D"
for arm in off on; do
  extra=""; [ $arm = on ] && extra="--senses"
  echo "################ COARSE arm=$arm $extra"
  $PY -u adjacency.py --flow --grain letter --perm 32 --min-prompts 10 $extra \
      --csv results/flow_letter_nofreq_$arm.csv 2>&1 | grep -vE '^Extracting|it/s\]'
done
for arm in off on; do
  extra=""; [ $arm = on ] && extra="--senses"
  echo "################ FINE arm=$arm $extra  (sources L1-, E3-)"
  $PY -u adjacency.py --flow --grain fine --perm 32 --min-prompts 10 \
      --source L1- --source E3- $extra \
      --csv results/flow_fine_nofreq_$arm.csv 2>&1 | grep -vE '^Extracting|it/s\]'
done
echo "################ ALL DONE"
