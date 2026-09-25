#!/bin/bash
# TEMPLATE_ARM, HF class. Usage: bash box_hf.sh <base> <endpoint> [pip specs...]
set -u
export MALIGNMENT_DATA=/root/malignment-data HF_HUB_ENABLE_HF_TRANSFER=1 PIP_BREAK_SYSTEM_PACKAGES=1 PIP_ROOT_USER_ACTION=ignore
cd /root/malignment && git pull -q
pip uninstall -y -q tiktoken 2>/dev/null; pip install -q "sentencepiece==0.2.1" 2>&1 | tail -1
B=$1; E=$2; shift 2
[ $# -gt 0 ] && pip install -q "$@" >> /root/ta.log 2>&1
python3 -c "import transformers, torch; print('tf', transformers.__version__, 'torch', torch.__version__)" >> /root/ta.log 2>&1
for M in "$B" "$E"; do
  echo "=== $(date +%T) $M hf_batch" >> /root/ta.log
  python3 -u experiments/passage_analysis/novel_arc/template_arm/hf_batch.py "$M" >> /root/ta.log 2>&1 \
    && echo "OK $M" >> /root/TA_STATUS || echo "FAILED $M" >> /root/TA_STATUS
done
touch /root/DONE_TA
