#!/bin/bash
# The DEFAULT system arm for the 8 checkpoints whose chat template discards an
# empty system message. Local, sequential, one model at a time on MPS.
#
# WHY DEFAULT AND NOT "": on all 8, render() produces BYTE-IDENTICAL output for
# system=DEFAULT and system="" -- verified 8/8 through generate.render itself.
# For 5 the template silently drops an empty system; for 3 it RAISES on any
# system role and render() falls back to the bare form. So DEFAULT measures the
# same surface the failed "" run would have, and stamps it truthfully.
#
# OMITTING --system IS THE POINT. run_v4.py passes the DEFAULT sentinel when
# --system is absent; `--system ""` is a different condition and is what box A
# ran. Do not "fix" this by adding the flag.
#
# --cache MATCHES BOX A. prompt_cache is in the dedup key, so a run without it
# is a different cell and would not sit beside the other 32.

set -u
cd /Users/rj416/github/malignment || exit 1

TARGET_EPOCH=__TARGET__
LOG_DIR=__LOGDIR__
PROMPTS=roster/prompts/populations/prefill.txt
mkdir -p "$LOG_DIR"
MAIN="$LOG_DIR/default_arm.log"

# CACHED FIRST, DOWNLOADS LAST. recurrentgemma (Griffin on transformers 5.4.0)
# and Teuken (trust_remote_code, tokenizer mangling on record) are both
# uncached AND the two most likely to fail. Putting them last means a failure
# costs nothing already earned.
MODELS=(
  "HuggingFaceTB/SmolLM3-3B"
  "zai-org/glm-4-9b-chat-hf"
  "01-ai/Yi-1.5-9B-Chat"
  "google/gemma-2-9b-it"
  "meta-llama/Llama-3.1-8B-Instruct"
  "HuggingFaceTB/SmolLM3-3B-checkpoints@it-soup-APO"
  "google/recurrentgemma-9b-it"
  "openGPT-X/Teuken-7B-instruct-v0.6"
)

{
  echo "=== DEFAULT arm scheduled for $(date -r "$TARGET_EPOCH" '+%Y-%m-%d %H:%M:%S') ==="
  echo "armed at $(date '+%Y-%m-%d %H:%M:%S'), pid $$"
} >> "$MAIN"

# WALL CLOCK, NOT `sleep 18000`. macOS suspends a sleeping process when the
# machine sleeps, so a single long sleep fires late by however long the Mac was
# asleep. Looping on the actual clock survives it.
while [ "$(date +%s)" -lt "$TARGET_EPOCH" ]; do
  sleep 60
done

echo "=== STARTING $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$MAIN"

# Hold off idle sleep for the DURATION OF THE RUN ONLY, not for the 5h wait --
# caffeinating from arming time would keep the Mac awake all night to do
# nothing. -w $$ ties it to this script: when the queue ends, so does it.
caffeinate -i -w $$ &
echo "  caffeinate armed for the run (pid $!)" >> "$MAIN"

for m in "${MODELS[@]}"; do
  safe=$(echo "$m" | tr '/@' '__')
  echo "--- $m  start $(date '+%H:%M:%S')" >> "$MAIN"
  ./.venv/bin/python -u scripts/run_v4.py \
      --model "$m" \
      --cache \
      --frame prefill \
      --prompts-file "$PROMPTS" \
      > "$LOG_DIR/$safe.log" 2>&1
  rc=$?
  echo "--- $m  exit=$rc  end $(date '+%H:%M:%S')" >> "$MAIN"
  # A failure is RECORDED AND STEPPED OVER, never fatal to the queue: the two
  # risky models are last precisely so their failure cannot cost the other six.
done

echo "=== QUEUE DONE $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$MAIN"
touch "$LOG_DIR/DONE"
