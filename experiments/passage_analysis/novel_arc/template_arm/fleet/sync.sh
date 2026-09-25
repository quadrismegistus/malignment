#!/bin/bash
# Local. Pull every pod's generation stash. NEVER --delete. ssh -n / </dev/null so the loop keeps its stdin.
mkdir -p ~/malignment-data/template_arm/pods
while IFS=$'\t' read -r N H P; do
  rsync -a -e "ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15 -p $P" \
    root@"$H":/root/malignment-data/generations/ ~/malignment-data/template_arm/pods/"$N"/ < /dev/null 2>/dev/null \
    || echo "sync failed: $N"
  rsync -a -e "ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15 -p $P" \
    root@"$H":/root/ta.log root@"$H":/root/TA_STATUS ~/malignment-data/template_arm/pods/"$N"/ < /dev/null 2>/dev/null
done < <(grep -v "^#" ~/malignment-data/template_arm/ssh.tsv)
