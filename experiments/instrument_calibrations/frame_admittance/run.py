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


def prompts_for(domain=None, source=None):
    """Declared prompts by domain and/or source. -> {prompt: (prompt_id, cell)}

    **SELECTION IS SEPARATE FROM WHICH SEEDS SCORE IT** (RH, 2026-08-17: "could we
    score the other institutional prompts too? source=M03"). The first version
    selected on `domain` and therefore missed 252 institutional frames entirely,
    because M03 records them at FINER grain -- labor, housing, medical, police,
    benefits, civic, banking, insurance, immigration, utilities, consumer,
    education, twelve domains that are all institutional relations under RH's
    gloss. Selecting and scoring are different decisions and conflating them made
    the scored population an artifact of somebody else's taxonomy.

    `cell` comes back too: for M03 it carries arm_person_form, and the FORM axis
    moves the next-token distribution hard enough that pooling across it would
    average four different questions.
    """
    where = []
    if domain:
        where.append("domain = '%s'" % esc(domain))
    if source:
        where.append("source = '%s'" % esc(source))
    if not where:
        raise ValueError("give --domain or --source")
    q = ("SELECT prompt_id, prompt, cell FROM malignment.prompts WHERE %s "
         "FORMAT TabSeparated" % " AND ".join(where))
    out = {}
    for line in ch.execute(q).strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        pid, txt, cell = parts[0], parts[1], (parts[2] if len(parts) > 2 else "")
        out[txt] = (pid, cell)
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


def shares(ws, seeds):
    """Mass on EACH pole as a fraction of content mass. -> (naughty, nice, tot)

    **BOTH, BECAUSE A HIGH NAUGHTY SHARE IS A DEFECT TOO** (RH, 2026-08-17). The
    first version ranked on naughty share alone and put `sexual_explicit_5` top at
    0.96 -- which is not a good slot, it is a frame with NOWHERE TO DISPLACE TO.
    Displacement needs the arrival side to exist: `kill -> scream` requires
    `scream` in the distribution, and at 0.96 naughty there is no `scream`. A frame
    like `He slid his hand between her` cannot be chastened at all, so alignment
    can only leave the frame -- which is a different phenomenon from displacement
    and would be recorded as one.

    So the quantity is monotonic and the thing it measures is not. `admits` below
    is the binding pole.
    """
    c = content(ws)
    tot = sum(c.values())
    if not tot:
        return None, None, 0.0
    g = set(w.lower() for w in seeds["naughty"])
    n = set(w.lower() for w in seeds["nice"])
    return (sum(p for w, p in c.items() if w.lower() in g) / tot,
            sum(p for w, p in c.items() if w.lower() in n) / tot, tot)


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
    ap.add_argument("--domain", default=None,
                    help="select prompts by the store's domain column")
    ap.add_argument("--source", default=None,
                    help="select by source, e.g. M03_SPEAKER_KERNEL or INSTITUTIONAL")
    ap.add_argument("--seeds", default=None, choices=sorted(SEEDS),
                    help="which domain's tagged poles to score WITH; defaults to "
                         "--domain. Required when selecting by --source, because a "
                         "source spans domains and the instrument must be declared.")
    ap.add_argument("--model", default="HuggingFaceTB/SmolLM3-3B-Base")
    ap.add_argument("--axis", action="store_true",
                    help="add the bge pass (embeds per frame; minutes, not seconds)")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(argv)
    seed_dom = a.seeds or a.domain
    if seed_dom not in SEEDS:
        ap.error("--seeds must be one of %s (a source spans domains, so the "
                 "instrument cannot be inferred)" % ", ".join(sorted(SEEDS)))
    seeds = SEEDS[seed_dom]
    label = a.source or a.domain

    pm_full = prompts_for(a.domain, a.source)
    pm = {t: v[0] for t, v in pm_full.items()}
    cells = {t: v[1] for t, v in pm_full.items()}
    if a.limit:
        pm = dict(list(pm.items())[:a.limit])
    wm = base_words(pm, a.model)
    missing = [p for p in pm if p not in wm]
    print("%s (scored with %s seeds): %d declared, %d with base-arm words in the "
          "store, %d missing" % (label, seed_dom, len(pm), len(wm), len(missing)))
    if missing:
        #: Named, not counted. A prompt absent from the store is a coverage fact
        #: and the next reader will want to know WHICH.
        print("  missing (first 5): %s" % [pm[p] for p in missing[:5]])

    rows, unmeasurable = [], []
    for pr, ws in wm.items():
        if not measurable(ws):
            unmeasurable.append(pm[pr])
            continue
        gsh, nsh, tot = shares(ws, seeds)
        if gsh is None:
            continue
        c = content(ws)
        top = sorted(c.items(), key=lambda x: -x[1])[:6]
        #: **RANK ON THE BINDING POLE.** min() is maximised when both sides are
        #: present and falls whichever one is missing, so it needs no threshold and
        #: it catches both failure modes with one number.
        #:
        #: This is a VALIDITY claim and not an effect claim, which matters because
        #: a balanced `share` is already measured NOT to predict leverage -- across
        #: four tagging schemes share moved 6.6x while leverage moved 24%, and a
        #: known-dead item had a better balanced share than a known mover. So:
        #: `admits` says both poles EXIST, never that the frame will move.
        rows.append({"prompt_id": pm[pr], "prompt": pr, "selected": label,
                     "seeds": seed_dom, "cell": cells.get(pr, ""),
                     "n_words": len(ws), "content_mass": round(tot, 6),
                     "admits": round(min(gsh, nsh), 6),
                     "naughty_share": round(gsh, 6), "nice_share": round(nsh, 6),
                     "one_sided": "naughty" if gsh > 0.60 else ("nice" if nsh > 0.90 else ""),
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
    rows.sort(key=lambda r: -r["admits"])
    os.makedirs(OUT, exist_ok=True)
    csv_p = os.path.join(OUT, "admittance_%s.csv" % label.lower())
    with open(csv_p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    v = [r["admits"] for r in rows]
    summ = {"selected": label, "seeds": seed_dom, "model": a.model, "n_frames": len(rows),
            "n_declared": len(pm), "n_missing_from_store": len(missing),
            "n_unmeasurable_by_seeds": len(unmeasurable),
            "unmeasurable_ids": unmeasurable,
            "admits": {"median": st.median(v), "mean": st.fmean(v),
                              "p10": v[int(.9 * len(v))], "p90": v[int(.1 * len(v))],
                              "min": min(v), "max": max(v)},
            "seeds": seeds, "axis_pass": a.axis,
            "note": ("naughty_share and axis_N are DIFFERENT INSTRUMENTS and are not "
                     "averaged. Scores are within-domain only: the seeds differ per "
                     "domain, so cross-domain comparison is not defined.")}
    with open(os.path.join(OUT, "admittance_%s.json" % label.lower()), "w") as fh:
        json.dump(summ, fh, indent=1)

    one = [r for r in rows if r["one_sided"]]
    print("\nadmits (the BINDING pole) over %d frames: median %.4f  (p90 %.4f)"
          % (len(rows), st.median(v), summ["admits"]["p90"]))
    print("  one-sided frames, which rank low BY DESIGN: %d naughty-dominated, %d nice-dominated"
          % (sum(1 for r in one if r["one_sided"] == "naughty"),
             sum(1 for r in one if r["one_sided"] == "nice")))
    hdr = "  %-7s %-7s %-7s %-8s %-30s %s" % ("admits", "naughty", "nice", "1-sided", "prompt_id", "top content")
    if any(r["cell"] for r in rows):
        #: **BROKEN OUT BY CELL, because pooling the FORM axis averages four
        #: different questions.** `... I should` and `... I` are not the same slot.
        import collections as _c
        by = _c.defaultdict(list)
        for r in rows:
            by[r["cell"].rsplit("_", 1)[-1] if r["cell"] else "-"].append(r["admits"])
        print("\nadmits by FORM (the m03 axis):")
        for k in sorted(by, key=lambda k: -st.median(by[k])):
            print("  %-12s n=%-4d median %.4f  max %.4f" % (k, len(by[k]), st.median(by[k]), max(by[k])))
    print("\nTOP 12 -- both poles present, so tagging can pay")
    print(hdr)
    for r in rows[:12]:
        print("  %-7.4f %-7.4f %-7.4f %-8s %-30s %s" % (r["admits"], r["naughty_share"],
              r["nice_share"], r["one_sided"] or "-", r["prompt_id"][:30], r["top_content"]))
    print("\nNAUGHTY-DOMINATED -- nowhere to displace to; not weak, UNUSABLE for this")
    print(hdr)
    for r in sorted([r for r in rows if r["one_sided"] == "naughty"],
                    key=lambda r: -r["naughty_share"])[:8]:
        print("  %-7.4f %-7.4f %-7.4f %-8s %-30s %s" % (r["admits"], r["naughty_share"],
              r["nice_share"], r["one_sided"], r["prompt_id"][:30], r["top_content"]))
    print("\nwrote %s" % os.path.relpath(csv_p, os.getcwd()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
