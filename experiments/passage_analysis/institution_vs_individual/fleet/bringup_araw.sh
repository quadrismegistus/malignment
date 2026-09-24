#!/bin/bash
# Local. Usage: bringup.sh <host> <port> <shard_file> [tp]
# Sends the HF token over ssh (never on the command line), installs, launches box_araw.sh detached.
H=$1; PT=$2; SH=$3; TP=${4:-1}
S="ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=20 -p $PT root@$H"
until $S true 2>/dev/null; do sleep 5; done
(source ~/.bash_profile >/dev/null 2>&1; printf %s "$HF_TOKEN") | $S 'mkdir -p ~/.cache/huggingface && cat > ~/.cache/huggingface/token'
$S 'bash -s' < setup.sh > /tmp/bringup_$PT.log 2>&1
scp -o StrictHostKeyChecking=no -q -P $PT box_araw.sh "$SH" root@$H:/root/
$S -n -f "cd /root && TP=$TP nohup setsid bash box_araw.sh /root/$(basename $SH) > /dev/null 2>&1 < /dev/null &"
echo "$H:$PT $(basename $SH) tp=$TP: $(tail -1 /tmp/bringup_$PT.log)"
