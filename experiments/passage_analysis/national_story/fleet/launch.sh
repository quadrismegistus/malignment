#!/bin/bash
# Usage: launch.sh <models_file> <box_label>
# Runs on the remote box via SSH. Installs deps, clones repo, starts generation.
#
# Two runs per box:
#   1. prompts_compare.jsonl at t=1.0, top_p=0.95
#   2. prompts_rettberg.jsonl at t=0.8, top_p=1.0 (aligned only — base skipped by template gate)
set -e

MODELS=$1
LABEL=${2:-box}

echo "=== national_story fleet: $LABEL ==="
echo "models: $MODELS"
date

# install deps
pip install -q torch transformers accelerate sentencepiece protobuf 2>&1 | tail -3
python3 -c 'import torch; print("torch:", torch.__version__, "cuda:", torch.cuda.is_available(), torch.cuda.get_device_name(0))'

# clone malignment
if [ ! -d /root/malignment ]; then
    git clone --depth 1 https://github.com/quadrismegistus/malignment.git /root/malignment 2>&1 | tail -2
    cd /root/malignment && pip install -q -e . 2>&1 | tail -2
fi
cd /root/malignment

# HF token
export HF_TOKEN=$(cat /root/.cache/huggingface/token 2>/dev/null || echo "")

echo ""
echo "=== RUN 1: compare (t=1.0, p=0.95) ==="
python3 -m malignment.vllm_generate \
    --models-file /root/$MODELS \
    --prompts-file experiments/national_story/prompts_compare.jsonl \
    --n 10 --temperature 1.0 --top-p 0.95 \
    --max-new-tokens 3000 --max-model-len 3500 \
    --seed 42

echo ""
echo "=== RUN 2: rettberg (t=0.8, p=1.0) ==="
python3 -m malignment.vllm_generate \
    --models-file /root/$MODELS \
    --prompts-file experiments/national_story/prompts_rettberg.jsonl \
    --n 10 --temperature 0.8 --top-p 1.0 \
    --max-new-tokens 3000 --max-model-len 3500 \
    --seed 42

echo ""
echo "=== DONE ==="
date
touch /root/DONE
