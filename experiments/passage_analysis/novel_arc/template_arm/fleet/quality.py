"""Local. Per model and frame: share of empty passages, median new tokens, share with a
repeated 8-gram run (degeneration), share of non-ASCII-letter chars. A pod whose output
fails here is not verified, whatever its counts say.  python3 quality.py <pod>..."""
import sys, json, glob, os, collections, statistics as st, re
for pod in sys.argv[1:]:
    root = os.path.expanduser("~/malignment-data/template_arm/pods/" + pod)
    agg = collections.defaultdict(list)
    for f in glob.glob(root + "/*/*/*/data.jsonl"):
        for l in open(f):
            r = json.loads(l); k = r["__key__"]
            agg[(k["model"], k["frame"])].append((r["text"], r.get("n_new_tokens") or 0))
    print("==", pod)
    for (m, fr), rows in sorted(agg.items()):
        empty = sum(not t.strip() for t, _ in rows) / len(rows)
        med = st.median(n for _, n in rows)
        rep = sum(bool(re.search(r"(\b\w+\b(?:\W+\w+){3,7}?)(?:\W+\1){3,}", t[:1500])) for t, _ in rows[:400]) / min(400, len(rows))
        print("  %-42s %-18s n=%-6d empty %.3f  med_tok %5.0f  loop8 %.2f" % (m.split("/")[-1][:42], fr, len(rows), empty, med, rep))
