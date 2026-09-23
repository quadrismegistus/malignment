#!/bin/bash
# Runs ON a RunPod pod. Usage: bash box.sh <shard_file>
#   shard file: one lineage per line, "<base> <endpoint>".
# Base arm: raw frame (prompts/raw.jsonl). Aligned arm: chat frame (prompts/chat.jsonl).
# Decoder: generate.DECODER -- t=1.0, top_p=1.0, top_k disabled, 256 new tokens, n=10.
# Writes the generation stash under $MALIGNMENT_DATA/generations; /root/DONE_IVI when finished.
set -u
SHARD=$1
export MALIGNMENT_DATA=/root/malignment-data
export VLLM_USE_V1=0 HF_HUB_ENABLE_HF_TRANSFER=1
cd /root/malignment
P=experiments/passage_analysis/institution_vs_individual/prompts
run() {  # model prompts
  python3 -u -m malignment.vllm_generate --models "$1" --prompts-file "$2" \
    --n 10 --temperature 1.0 --top-p 1.0 --max-new-tokens 256 --max-model-len 1024 \
    --seed 42 --tp "${TP:-1}" >> /root/ivi.log 2>&1 || echo "FAILED $1" >> /root/FAILED_IVI
}
while read -r BASE END; do
  [ -z "$BASE" ] && continue
  echo "=== $(date +%T) $BASE -> $END" >> /root/ivi.log
  run "$BASE" "$P/raw.jsonl"
  run "$END" "$P/chat.jsonl"
done < "$SHARD"
touch /root/DONE_IVI
