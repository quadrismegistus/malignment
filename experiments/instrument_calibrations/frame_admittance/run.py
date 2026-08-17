#!/usr/bin/env python
"""Does a frame admit a transgressive continuation at all? Store-only triage.

    python experiments/instrument_calibrations/frame_admittance/run.py --domain institutional
    ... --domain institutional --axis        # add the bge pass (slow, embeds per frame)

## THE QUESTION

RH has ~276 institutional prompts already measured on ~406 checkpoints, none of
them pole-tagged. Tagging is the expensive part, so this ranks frames by whether
tagging them could produce anything: a frame whose base distribution offers only
`contact/consider/discuss` has foreclosed the naughty pole, and no tagging
recovers it.

**IT READS `twp_words` AND RUNS NO MODEL.** The distributions are already in the
store; that is the whole reason this is cheap enough to run over everything.

## WHY NOT THE 12 GENERIC naughty/nice PAIRS

Measured, and they fail at exactly this task. The pooled 12-pair lexical axis
scores r = 0.740 against a 0.828 split-half ceiling -- 89% of achievable
reliability, which **licenses a POOLED use and this is a PER-ITEM use.** On
`nn_shewantedto_scream-kill` it returned 17/50 where a declared axis returned
41/50, gap +0.0290 against +0.3904, because it ranked `yell 0.080` and
`shout 0.073` above `die 0.046`. Scream is not nice in any general sense; it is
nice relative to killing. A cross-domain axis inverts inside a domain.

So the seeds are PER DOMAIN, from RH's own glosses (2026-08-17).

## TWO INSTRUMENTS, REPORTED SIDE BY SIDE, NEVER AVERAGED

`share`  mass on a declared word list. Cheap, auditable, and blind to any word
         not on the list.
`axis`   bge position of the frame's own mass on the domain seeds. Generalises to
         unlisted words, and can invert on a particular frame.

Where they disagree the frame needs reading, not arithmetic. Averaging two
instruments of different construction asserts a commensurability neither claims.

## SCORES ARE WITHIN-DOMAIN ONLY

Different seeds are different axes. A sexual frame's 0.31 and an institutional
frame's 0.31 are not the same quantity, so the output refuses to rank across
domains rather than leaving it to the reader to remember.
"""
import argparse, collections, csv, json, os, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
from malignment import ch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results")

#: **THE SEEDS ARE RH's OWN TAGS, POOLED PER DOMAIN -- NOT A LIST I WROTE.**
#:
#: The first version seeded each domain from RH's prose gloss as I understood it,
#: and `sexual` came back at median 0.0000 over 127 frames. That was my seeds, not
#: the frames: I used anatomical profanity, and this corpus's sexual pole is
#: GARMENT REMOVAL -- `She slowly took off her` -> `bra, panties`. Wrong register
#: entirely, and it is the same failure this file's header warns about one
#: paragraph earlier: a general notion of the category inverts inside it.
#:
#: RH has tagged 86 items by hand. Those tags ARE the domain's poles, instantiated
#: rather than described, so they are the instrument. Derived at import so a new
#: authored item widens the seeds automatically -- and so no gloss of mine sits
#: between his judgement and the measurement.
def _seeds_from_corpora(min_count=1):
    """Pooled naughty/nice words per domain, from every tagged slot item. -> dict"""
    from malignment.slots import corpora, read_items
    import collections
    g = collections.defaultdict(collections.Counter)
    n = collections.defaultdict(collections.Counter)
    for _name, path in corpora():
        if not os.path.exists(path):
            continue
        for d in read_items(path):
            dom = (d.get("domain") or "").strip()
            if not dom:
                continue
            for w in (d.get("naughty") or []):
                g[dom][str(w).lower()] += 1
            for w in (d.get("nice") or []):
                n[dom][str(w).lower()] += 1
    out = {}
    for dom in set(g) | set(n):
        #: A word tagged into BOTH poles somewhere in the corpus is dropped from
        #: both: it cannot orient an axis and it would inflate `share` on whichever
        #: side kept it. `scream` is naughty against `talk` and nice against
        #: `kill`, and pooling a domain is exactly where that collides.
        gg = {w for w, c in g[dom].items() if c >= min_count}
        nn = {w for w, c in n[dom].items() if c >= min_count}
        both = gg & nn
        out[dom] = {"naughty": sorted(gg - both), "nice": sorted(nn - both),
                    "dropped_ambiguous": sorted(both)}
    return out


SEEDS = _seeds_from_corpora()

#: Function words carry no severity and dominate a "should ___" frame, where the
#: modal takes an auxiliary. Excluded from BOTH instruments so they agree about
#: their denominator.
STOP = set("be have has had not no just do does did to the a an i we you it that this "
           "and or probably also only never always like get got been being am is are "
           "was were will would can could should shall may might must of in on at for "
           "with as so if then than there he she they him her them my our your his "
           "their its me us one two some any all more most very really quite too now "
           "still yet even much many".split())

esc = lambda s: s.replace("\\", "\\\\").replace("'", "\\'")


def prompts_for(domain, subdomains=None):
    """Declared prompts in a domain, from the store. -> {prompt: prompt_id}"""
    q = ("SELECT prompt_id, prompt FROM malignment.prompts WHERE domain = '%s' "
         "FORMAT TabSeparated" % esc(domain))
    out = {}
    for line in ch.execute(q).strip().splitlines():
        if not line.strip():
            continue
        pid, txt = line.split("\t", 1)
        out[txt] = pid
    return out


def base_words(texts, model):
    """Base-arm word probabilities, from the store. -> {prompt: {word: p}}

    Chunked because a 252-way `IN` list of long prompts is a large statement and
    a truncated one would return a SUBSET SILENTLY -- the failure that looks like
    a finding about coverage.
    """
    out = collections.defaultdict(dict)
    texts = list(texts)
    for i in range(0, len(texts), 60):
        lst = ",".join("'%s'" % esc(t) for t in texts[i:i + 60])
        q = ("SELECT prompt, word, p FROM malignment.twp_words WHERE model = '%s' "
             "AND prompt IN (%s) FORMAT TabSeparated" % (esc(model), lst))
        for line in ch.execute(q).strip().splitlines():
            if not line.strip():
                continue
            pr, w, p = line.rsplit("\t", 2)
            out[pr][w] = float(p)
    return out


import re as _re
_LATIN = _re.compile(r"[A-Za-z]")


def measurable(ws):
    """Can an English seed list see this frame's candidates at all? -> bool

    **A SCRIPT THE SEEDS CANNOT REACH IS UNMEASURABLE, NOT FORECLOSED.** The first
    run ranked ten Chinese frames at exactly 0.0000 and printed them under
    "tagging these buys nothing" -- but the seeds are English, so a zero there is
    a fact about the word list stated as a fact about the frame. The axis pass
    already refuses to emit a low number when it cannot measure; `share` did not,
    and that asymmetry inside one producer was the defect.

    True when at least 60% of content MASS sits on words containing a Latin
    letter. Mass rather than count: a frame whose top word is Chinese and whose
    tail is English loanwords is not measurable by these seeds, and a count would
    call it mixed. Tested on the CANDIDATES, not the prompt -- an English prompt
    with Chinese continuations is the same problem.
    """
    c = {w: p for w, p in ws.items() if w.lower() not in STOP and len(w) > 1}
    tot = sum(c.values())
    if not tot:
        return False
    return sum(p for w, p in c.items() if _LATIN.search(w)) / tot >= 0.60


def content(ws):
    return {w: p for w, p in ws.items()
            if w.lower() not in STOP and w.isalpha() and len(w) > 1}


def share(ws, seeds):
    """Mass on the naughty seeds as a fraction of content mass. -> (share, tot)"""
    c = content(ws)
    tot = sum(c.values())
    if not tot:
        return None, 0.0
    g = set(w.lower() for w in seeds["naughty"])
    return sum(p for w, p in c.items() if w.lower() in g) / tot, tot


def axis_score(prompt, ws, seeds):
    """bge position of the frame's mass on the domain seeds. -> (N, separates_ok)

    **`separates` FIRST, AND ITS ANSWER GATES THE SCORE.** Its docstring is
    explicit that a gate consulted after the result is a rationalisation. If the
    seeds do not separate in this frame's own embedding context, the frame is
    UNRANKABLE and gets no number -- not a low number, which would read as a
    finding about the frame rather than about the instrument.
    """
    from malignment.slot_axis import Axis, separates
    ax = Axis(prompt, seeds["naughty"], seeds["nice"])
    if not ax.ok:
        return None, False
    c = content(ws)
    if not c:
        return None, False
    S = ax.score(sorted(set(c) | set(seeds["naughty"]) | set(seeds["nice"])))
    ok, _gap, _corr, _tot = separates(S, seeds["naughty"], seeds["nice"])
    if not ok:
        return None, False
    tot = sum(c.values())
    return sum(c[w] * S.get(w, 0.0) for w in c) / tot, True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--domain", required=True, choices=sorted(SEEDS),
                    help="one at a time: scores are not comparable across domains")
    ap.add_argument("--model", default="HuggingFaceTB/SmolLM3-3B-Base")
    ap.add_argument("--axis", action="store_true",
                    help="add the bge pass (embeds per frame; minutes, not seconds)")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    seeds = SEEDS[a.domain]

    pm = prompts_for(a.domain)
    if a.limit:
        pm = dict(list(pm.items())[:a.limit])
    wm = base_words(pm, a.model)
    missing = [p for p in pm if p not in wm]
    print("domain %s: %d declared, %d with base-arm words in the store, %d missing"
          % (a.domain, len(pm), len(wm), len(missing)))
    if missing:
        #: Named, not counted. A prompt absent from the store is a coverage fact
        #: and the next reader will want to know WHICH.
        print("  missing (first 5): %s" % [pm[p] for p in missing[:5]])

    rows, unmeasurable = [], []
    for pr, ws in wm.items():
        if not measurable(ws):
            unmeasurable.append(pm[pr])
            continue
        sh, tot = share(ws, seeds)
        if sh is None:
            continue
        c = content(ws)
        top = sorted(c.items(), key=lambda x: -x[1])[:6]
        rows.append({"prompt_id": pm[pr], "prompt": pr, "domain": a.domain,
                     "n_words": len(ws), "content_mass": round(tot, 6),
                     "naughty_share": round(sh, 6),
                     "top_content": " ".join(w for w, _ in top),
                     "axis_N": "", "axis_ok": ""})
    if a.axis:
        for i, r in enumerate(rows, 1):
            N, ok = axis_score(r["prompt"], wm[r["prompt"]], seeds)
            r["axis_N"] = "" if N is None else round(N, 6)
            r["axis_ok"] = int(bool(ok))
            if i % 25 == 0:
                print("  axis %d/%d" % (i, len(rows)), flush=True)

    if unmeasurable:
        print("  UNMEASURABLE by English seeds -- EXCLUDED, not scored 0: %d" % len(unmeasurable))
        print("    %s%s" % (", ".join(unmeasurable[:4]), " ..." if len(unmeasurable) > 4 else ""))
    rows.sort(key=lambda r: -r["naughty_share"])
    os.makedirs(OUT, exist_ok=True)
    csv_p = os.path.join(OUT, "admittance_%s.csv" % a.domain)
    with open(csv_p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    v = [r["naughty_share"] for r in rows]
    summ = {"domain": a.domain, "model": a.model, "n_frames": len(rows),
            "n_declared": len(pm), "n_missing_from_store": len(missing),
            "n_unmeasurable_by_seeds": len(unmeasurable),
            "unmeasurable_ids": unmeasurable,
            "naughty_share": {"median": st.median(v), "mean": st.fmean(v),
                              "p10": v[int(.9 * len(v))], "p90": v[int(.1 * len(v))],
                              "min": min(v), "max": max(v)},
            "seeds": seeds, "axis_pass": a.axis,
            "note": ("naughty_share and axis_N are DIFFERENT INSTRUMENTS and are not "
                     "averaged. Scores are within-domain only: the seeds differ per "
                     "domain, so cross-domain comparison is not defined.")}
    with open(os.path.join(OUT, "admittance_%s.json" % a.domain), "w") as fh:
        json.dump(summ, fh, indent=1)

    print("\nnaughty_share over %d frames: median %.4f  (p10 %.4f .. p90 %.4f)"
          % (len(rows), st.median(v), summ["naughty_share"]["p10"],
             summ["naughty_share"]["p90"]))
    print("\nTOP 10 -- the frames worth tagging first")
    for r in rows[:10]:
        print("  %.4f  %-34s %s" % (r["naughty_share"], r["prompt_id"][:34], r["top_content"]))
    print("\nBOTTOM 10 -- foreclosed; tagging these buys nothing (measurable frames only)")
    for r in rows[-10:]:
        print("  %.4f  %-34s %s" % (r["naughty_share"], r["prompt_id"][:34], r["top_content"]))
    print("\nwrote %s" % os.path.relpath(csv_p, os.getcwd()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
