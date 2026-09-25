#!/bin/bash
# TEMPLATE_ARM, vLLM class. Usage: bash box_ta.sh <jobs_file>
# jobs lines: "<model> <prompts_file> <dtype> [pip spec]". Per-condition n and seed come from the
# prompts file (n=20 f11 stems, n=50 Y cells; seed sha256(model|arm|stem)). /root/DONE_TA at end,
# /root/TA_STATUS per model. Each checkpoint is PURGED after its run: 12-14 checkpoints per pod.
set -u
export MALIGNMENT_DATA=/root/malignment-data VLLM_USE_V1=0 HF_HUB_ENABLE_HF_TRANSFER=1 PIP_BREAK_SYSTEM_PACKAGES=1 PIP_ROOT_USER_ACTION=ignore
[ "${TP:-1}" -gt 1 ] && export NCCL_P2P_DISABLE=1 NCCL_IB_DISABLE=1
cd /root/malignment && git pull -q
pip uninstall -y -q tiktoken 2>/dev/null; pip install -q "sentencepiece==0.2.1" 2>&1 | tail -1
while read -r M PF DT PIPSPEC; do
  [ -z "$M" ] && continue
  [ -n "${PIPSPEC:-}" ] && pip install -q "$PIPSPEC" >> /root/ta.log 2>&1
  echo "=== $(date +%T) $M $DT ${PIPSPEC:-}" >> /root/ta.log
  python3 -u -m malignment.vllm_generate --models "$M" --prompts-file "$PF" --n 20 --temperature 1.0 --top-p 1.0 \
    --max-new-tokens 256 --max-model-len 1024 --seed 0 --dtype "$DT" --tp "${TP:-1}" >> /root/ta.log 2>&1 \
    && echo "OK $M" >> /root/TA_STATUS || echo "FAILED $M" >> /root/TA_STATUS
  rm -rf "/root/.cache/huggingface/hub/models--${M//\//--}"
  [ -n "${PIPSPEC:-}" ] && pip install -q "transformers==4.57.1" >> /root/ta.log 2>&1
done < "$1"
touch /root/DONE_TA
