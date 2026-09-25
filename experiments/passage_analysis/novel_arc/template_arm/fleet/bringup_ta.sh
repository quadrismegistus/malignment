#!/bin/bash
# Local. Usage: bringup_ta.sh <host> <port> vllm <shard_file> [tp]
#                bringup_ta.sh <host> <port> hf "<base> <endpoint> [pip specs]"
# Sends the HF token over ssh stdin (never on a command line), installs, launches detached.
H=$1; PT=$2; KIND=$3; ARG=$4; TP=${5:-1}
S="ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=20 -p $PT root@$H"
until $S -n true 2>/dev/null; do sleep 5; done
(source ~/.bash_profile >/dev/null 2>&1; printf %s "$HF_TOKEN") | $S 'mkdir -p ~/.cache/huggingface && cat > ~/.cache/huggingface/token'
$S 'bash -s' < setup.sh > /tmp/bringup_ta_$PT.log 2>&1
if [ "$KIND" = vllm ]; then
  scp -o StrictHostKeyChecking=no -q -P $PT box_ta.sh "$ARG" root@$H:/root/
  $S -n -f "cd /root && TP=$TP nohup setsid bash box_ta.sh /root/$(basename $ARG) > /dev/null 2>&1 < /dev/null &"
else
  scp -o StrictHostKeyChecking=no -q -P $PT box_hf.sh root@$H:/root/
  $S -n -f "cd /root && nohup setsid bash box_hf.sh $ARG > /dev/null 2>&1 < /dev/null &"
fi
echo "$H:$PT $KIND $ARG tp=$TP: $(tail -1 /tmp/bringup_ta_$PT.log)"
