#!/bin/bash
# Regeneration on the fixed render path (vllm_generate render=ids_v2). Usage: bash box2.sh <jobs_file>
# jobs file lines: "<model> <prompts_file> <dtype>". /root/DONE_R2 when finished; /root/R2_STATUS per model.
set -u
export MALIGNMENT_DATA=/root/malignment-data VLLM_USE_V1=0 HF_HUB_ENABLE_HF_TRANSFER=1 PIP_BREAK_SYSTEM_PACKAGES=1 PIP_ROOT_USER_ACTION=ignore
cd /root/malignment && git pull -q
#: internlm2: sentencepiece 0.2.2 breaks the converter and tiktoken lets the WRONG converter succeed silently
pip uninstall -y -q tiktoken 2>/dev/null; pip install -q "sentencepiece==0.2.1" 2>&1 | tail -1
while read -r M PF DT; do
  [ -z "$M" ] && continue
  echo "=== $(date +%T) $M $DT" >> /root/regen.log
  python3 -u -m malignment.vllm_generate --models "$M" --prompts-file "$PF" --n 10 --temperature 1.0 --top-p 1.0 \
    --max-new-tokens 256 --max-model-len 1024 --seed 42 --dtype "$DT" --tp "${TP:-1}" >> /root/regen.log 2>&1 \
    && echo "OK $M" >> /root/R2_STATUS || echo "FAILED $M" >> /root/R2_STATUS
done < "$1"
touch /root/DONE_R2
