#!/bin/bash
# Deploy and launch vllm_generate on a RunPod pod.
# Usage: ssh <pod-user>@ssh.runpod.io 'bash -s' < deploy_runpod.sh <models_url> <label>
#
# Or interactively:
#   ssh <pod-user>@ssh.runpod.io
#   # then paste the commands below

set -e

echo "=== Setup ==="
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
python3 -c 'import torch; print("torch:", torch.__version__, "cuda:", torch.cuda.is_available())'

# Install deps (torch should already be in the RunPod image)
pip install -q transformers accelerate sentencepiece protobuf 2>&1 | tail -2

# Clone malignment
if [ ! -d /root/malignment ]; then
    git clone --depth 1 https://github.com/quadrismegistus/malignment.git /root/malignment
fi
cd /root/malignment
pip install -q -e .

echo ""
echo "=== Ready. To launch: ==="
echo ""
echo "# Upload your models file and HF token, then:"
echo "cd /root/malignment"
echo ""
echo "# Run 1: compare (t=1.0, p=0.95)"
echo "nohup python3 -u -m malignment.vllm_generate \\"
echo "    --models-file /root/models.txt \\"
echo "    --prompts-file experiments/national_story/prompts_compare.jsonl \\"
echo "    --n 10 --temperature 1.0 --top-p 0.95 \\"
echo "    --max-new-tokens 3000 --max-model-len 3500 \\"
echo "    --seed 42 > /root/run1.log 2>&1 &"
echo ""
echo "# Run 2: rettberg (t=0.8, p=1.0) — after run 1 finishes"
echo "nohup python3 -u -m malignment.vllm_generate \\"
echo "    --models-file /root/models.txt \\"
echo "    --prompts-file experiments/national_story/prompts_rettberg.jsonl \\"
echo "    --n 10 --temperature 0.8 --top-p 1.0 \\"
echo "    --max-new-tokens 3000 --max-model-len 3500 \\"
echo "    --seed 42 > /root/run2.log 2>&1 &"
