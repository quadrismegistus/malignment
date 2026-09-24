#!/bin/bash
# superego_stages new rungs, Y settings (n=50, t=1, top_p=1, 256, raw, float16). Usage: bash box_ss.sh <jobs_file>
# jobs lines: "<model> <prompts_file> <dtype> [pip spec to install first]". /root/DONE_SS at end; /root/SS_STATUS per model.
set -u
export MALIGNMENT_DATA=/root/malignment-data VLLM_USE_V1=0 HF_HUB_ENABLE_HF_TRANSFER=1 PIP_BREAK_SYSTEM_PACKAGES=1 PIP_ROOT_USER_ACTION=ignore
#: MULTI-GPU A40 (PCIe): vLLM's NCCL init HANGS at 100% util with nothing loaded unless P2P is off.
#: Cost 30 min on the 4xA40 pod, 2026-09-24; GPU utilisation read as health the whole time.
[ "${TP:-1}" -gt 1 ] && export NCCL_P2P_DISABLE=1 NCCL_IB_DISABLE=1
cd /root/malignment && git pull -q
#: internlm2: sentencepiece 0.2.2 breaks the converter and tiktoken lets the WRONG converter succeed silently
pip uninstall -y -q tiktoken 2>/dev/null; pip install -q "sentencepiece==0.2.1" 2>&1 | tail -1
while read -r M PF DT PIPSPEC; do
  [ -z "$M" ] && continue
  [ -n "${PIPSPEC:-}" ] && pip install -q "$PIPSPEC" >> /root/ss.log 2>&1
  echo "=== $(date +%T) $M $DT ${PIPSPEC:-}" >> /root/ss.log
  python3 -u -m malignment.vllm_generate --models "$M" --prompts-file "$PF" --n 50 --temperature 1.0 --top-p 1.0 \
    --max-new-tokens 256 --max-model-len 1024 --seed 42 --dtype "$DT" --tp "${TP:-1}" >> /root/ss.log 2>&1 \
    && echo "OK $M" >> /root/SS_STATUS || echo "FAILED $M" >> /root/SS_STATUS
done < "$1"
touch /root/DONE_SS
