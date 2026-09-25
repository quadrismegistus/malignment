#!/bin/bash
# Local. One line per pod: models OK/FAILED, current model, rows written (stash lines), GPU util, disk.
# rc 255 = the SSH connection failed (not the pod); read it as "unknown", never as "dead".
while IFS=$'\t' read -r N H P; do
  out=$(ssh -n -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15 -p "$P" root@"$H" '
    ok=$(grep -c "^OK" /root/TA_STATUS 2>/dev/null); fl=$(grep "^FAILED" /root/TA_STATUS 2>/dev/null | awk "{print \$2}" | xargs)
    cur=$(grep "^===" /root/ta.log 2>/dev/null | tail -1 | cut -d" " -f3)
    rows=$(cat /root/malignment-data/generations/*/*/*/data.jsonl 2>/dev/null | wc -l)
    g=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | xargs | tr " " ,)
    d=$(df -h /root | tail -1 | awk "{print \$5}")
    [ -f /root/DONE_TA ] && dn=DONE || dn=run
    echo "$dn ok=${ok:-0} rows=$rows gpu=$g disk=$d cur=$cur ${fl:+FAILED=$fl}"' 2>/dev/null); rc=$?
  [ $rc -eq 255 ] && out="ssh-unreachable (rc 255)"
  printf "%-16s %s\n" "$N" "$out"
done < <(grep -v "^#" ~/malignment-data/template_arm/ssh.tsv)
