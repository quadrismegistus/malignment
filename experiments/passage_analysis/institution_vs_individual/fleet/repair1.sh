#!/bin/bash
# Repair pass 1 (on a pod that has finished its shard). Logs to /root/repair1.log; /root/DONE_R1 at end.
export PIP_BREAK_SYSTEM_PACKAGES=1 PIP_ROOT_USER_ACTION=ignore MALIGNMENT_DATA=/root/malignment-data VLLM_USE_V1=0 HF_HUB_ENABLE_HF_TRANSFER=1
cd /root/malignment && git pull -q && pip install -q sentencepiece tiktoken 2>&1 | tail -1
P=experiments/passage_analysis/institution_vs_individual/prompts
g() { python3 -u -m malignment.vllm_generate --models "$1" --prompts-file "$2" --n 10 --temperature 1.0 --top-p 1.0 \
      --max-new-tokens 256 --max-model-len 1024 --seed 42 ${3:+--dtype $3} >> /root/repair1.log 2>&1 && echo "OK $1" >> /root/R1_STATUS || echo "FAILED $1" >> /root/R1_STATUS; }
# gemma2 refuses float16 ("numerical instability"): the one bf16 exception
g google/gemma-2-9b $P/raw.jsonl bfloat16
g google/gemma-2-9b-it $P/chat.jsonl bfloat16
# roster wrongly said no template; vllm_generate now asks the tokenizer
g allenai/OLMo-2-0425-1B-Instruct $P/chat.jsonl
g allenai/OLMoE-1B-7B-0125-Instruct $P/chat.jsonl
g allenai/Olmo-3-7B-Instruct $P/chat.jsonl
# tokenizer conversion needed sentencepiece
g internlm/internlm2-base-7b $P/raw.jsonl
g internlm/internlm2-chat-7b $P/chat.jsonl
touch /root/DONE_R1
