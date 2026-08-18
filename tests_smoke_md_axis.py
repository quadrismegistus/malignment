import sys; sys.path.insert(0,"/Users/rj416/github/malignment")
from malignment.slot_client import md_axis
base = {"separates":{"ok":True,"gap":0.42,"correct":16,"total":16,"floor":0.05,"reason":None},
        "coherence":{"naughty":{"n":4,"mean_pairwise":0.66,"min_pair":["a","b",0.60]},
                     "nice":{"n":4,"mean_pairwise":0.51,"min_pair":["c","d",0.33]}},
        "purity":1.0,"defectors":[],"N":-0.22,"leverage":0.10,
        "held_out":{"words":[{"word":"a","pole":"naughty","margin":-0.1,"p":0.01}],
                    "weakest":"a","margin":-0.1,"n_negative":1,"thin":False},
        "neighbours":{"naughty_end":[{"word":"x","s":0.1}],"nice_end":[{"word":"y","s":-0.1}]},
        "cross_corpus":{"scored_prompts":1591,"naughty_end":[{"word":"p","s":0.1,"prompts":5}],
                        "nice_end":[{"word":"q","s":-0.1,"prompts":5}]},
        "stability":{"vocab":135000,"neighbours":{"a":[{"word":"z"}]},"missing":[]}}
cases = {
 "all present": base,
 "cross_corpus ERROR": {**base,"cross_corpus":{"error":"boom"}},
 "gate FAILS": {**base,"separates":{**base["separates"],"ok":False,"correct":15,"reason":"r"}},
 "negative min_pair": {**base,"coherence":{**base["coherence"],
        "naughty":{"n":4,"mean_pairwise":0.2,"min_pair":["a","b",-0.05]}}},
 "held_out ERROR": {**base,"held_out":{"error":"nope"}},
 "defectors present": {**base,"defectors":["a"],"purity":0.75},
 "tiny poles": base,
}
ok=True
for name,payload in cases.items():
    g = ["a","b"] if name=="tiny poles" else ["a","b","c","d"]
    try:
        out = md_axis("A test frame", g, ["e","f","g","h"], payload)
        print("%-22s OK  %d lines" % (name, out.count("\n")))
    except Exception as e:
        ok=False; print("%-22s FAIL %s: %s" % (name, type(e).__name__, e))
sys.exit(0 if ok else 1)
