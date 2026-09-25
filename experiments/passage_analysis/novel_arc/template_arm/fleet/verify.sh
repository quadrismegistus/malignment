#!/bin/bash
# Local. Usage: verify.sh <pod name>. Re-syncs, then compares sha256 of every remote data.jsonl with the
# local copy and prints per-model row counts against the design (base 3,700; aligned 11,100).
N=$1; read -r _ H P <<<"$(grep "^$N	" ~/malignment-data/template_arm/ssh.tsv)"
E="ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=15 -p $P"
rsync -a -e "$E" root@$H:/root/malignment-data/generations/ ~/malignment-data/template_arm/pods/$N/ < /dev/null || { echo "SYNC FAILED"; exit 1; }
R=$($E -n root@$H 'cd /root/malignment-data/generations && find . -name data.jsonl -exec sha256sum {} \; | sort')
L=$(cd ~/malignment-data/template_arm/pods/$N && find . -name data.jsonl -exec shasum -a 256 {} \; | sort)
[ "$R" = "$L" ] && echo "BYTES MATCH ($(echo "$R" | wc -l | xargs) files)" || { echo "BYTES DIFFER"; diff <(echo "$R") <(echo "$L") | head; }
python3 - "$N" <<'PY'
import sys, json, glob, os, collections
root = os.path.expanduser("~/malignment-data/template_arm/pods/" + sys.argv[1])
c = collections.Counter()
for f in glob.glob(root + "/*/*/*/data.jsonl"):
    for l in open(f):
        c[json.loads(l)["__key__"]["model"]] += 1
bad = 0
for m, n in sorted(c.items()):
    ok = n in (3700, 11100); bad += not ok
    print("  %-50s %6d %s" % (m, n, "" if ok else "<-- UNEXPECTED"))
print("models %d, unexpected %d" % (len(c), bad))
PY
