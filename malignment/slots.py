#!/usr/bin/env python
"""Slot items: the derived id, and nothing else yet.

    from malignment.slots import item_id
    item_id("She slowly took off her", "coat", "dress")   # nn_tookoffher_coat-dress

## WHY THIS IS A MODULE AND NOT A LINE IN THE UI

`item_id` is a PURE FUNCTION the client could trivially reimplement, and that is
exactly the argument for not letting it. A reimplementation silently re-chooses
every rule inside it -- and this one has four, three of which are invisible
until they are wrong:

    the last THREE words, not two or four
    each word stripped to [a-z0-9] BEFORE joining, so "man's" -> "mans"
    NICE FIRST, then naughty
    CJK falls back to the last 8 characters, because `split()` on a Chinese
      prompt returns ONE token and the id would carry the whole sentence

A JavaScript port would also get the character classes wrong for free: Python's
`\\w` is Unicode-aware by default and JavaScript's is ASCII-only, so a naive port
strips accented and CJK characters that the original keeps. That is a divergence
no test in either language would notice, producing ids that look right and do
not match the ones already written.

## PORTED VERBATIM FROM `malign_logits/server.py._slot_item_id`

Logic unedited, on the `twp.py` precedent: a pure move so the rule has one home.
**86 items in `pair_drafts/round3/round3_slots.yaml` already carry ids from this
function**, so it is not a convention being chosen here -- it is one being
honoured, and a change to it orphans them.

Verified against that file on 2026-08-16: 84 of 86 decompose as
`nn_<last3>_<nice0>-<naughty0>` under a straightforward reading, and the two
that do not are an artifact of the CHECKING regex splitting `man's` into two
tokens, not of the ids. `nn_tookoffher_coat-dress`, `nn_reachedforhis_hand-belt`,
`nn_andstartedto_search-beat`.

## WHAT `item_id` IS NOT

It is not provenance. It encodes the prompt tail and the highest-mass word of
each branch -- **it says nothing about which checkpoints produced the
distribution**, and no field in those 86 items does. That is a real gap and a
narrow one; it is not the same as the items carrying nothing, which they plainly
do not: they carry both pole lists mass-ordered, `naughty_mass`, `nice_mass`,
`share`, `domain`, `writer`, and `global_cos` on 39 of 86.
"""
import re

#: The CJK block, matching the archive's `[一-鿿]` exactly. Written as an escape
#: rather than as literal characters so that a file-encoding accident cannot
#: silently narrow it.
_CJK = re.compile(r"[一-鿿]")


# ---------------------------------------------------------------------------
# the diagnostic pair
# ---------------------------------------------------------------------------

#: **`tiiuae/Falcon3-10B-Base -> tiiuae/Falcon3-10B-Instruct`** (RH, 2026-08-16).
#:
#: ## OUT OF SAMPLE IS NON-NEGOTIABLE, AND I BRIEFLY GAVE IT AWAY
#:
#: [6368] lifted the out-of-population requirement and recommended `kanana`, on
#: the grounds that contamination had been withdrawn as a hazard. **It had not.
#: TWO hazards were in play and only one was withdrawn:**
#:
#:     DIRECT         screening frames while looking at movement on a pair that
#:                    IS in the measured 50 selects frames on the outcome of a
#:                    measurement we will report. X_safety_ablation §4a, where 39
#:                    never-scored items reversed the ordering.  NEVER WITHDRAWN.
#:     CORRELATIONAL  a HELD-OUT pair's movement correlating with in-sample
#:                    pairs.  Withdrawn by RH, accepted at [6368].
#:
#: My [6366] withdrew the second. [6368] read it as the first and expanded the
#: pool to in-sample pairs. **Both arms of `kanana` and of `RedPajama` are in
#: `endpoints()`** -- verified, not assumed -- so either would have made the
#: authoring screen select on the outcome of a measured lineage.
#:
#: ## WHAT IS LEFT ONCE THE CONSTRAINT IS RESTORED
#:
#: Out of sample AND runnable on this machine leaves the unused Falcon3s. The
#: two criteria, and **note which statistic is NOT among them**:
#:
#:     pair              screener   base mass   transgressive DiD    env
#:                       max_dev     pctile      value    pctile
#:     Falcon3-10B-Base    26.8        32%      +0.0716     40%    default
#:     Falcon3-3B-Base     46.6         2%      +0.1496     70%    default
#:     Falcon3-Mamba-7B       -        50%      +0.0148     30%    ssm
#:     Falcon3-1B-Base        -         0%      +0.0060     30%    default
#:
#: **JS IS NOT THE DIAGNOSTIC CRITERION AND USING IT WAS MY MISTAKE** (malign,
#: [6370], re-ranking the pool on the lexicon). Mean JS is total distributional
#: change: it counts format and register drift equally with the vocabulary a
#: slot frame is built from. The quantity the diagnostic needs is transgressive
#: REMOVAL -- mass leaving the 1,063-word lexicon, differenced against the
#: 3,812-word matched-neutral set so that a model which simply says less of
#: everything does not read as repressing.
#:
#: **The ordering nearly inverts.** `Falcon3-Mamba` led on JS at 0.1674, 1.9x
#: the current pick, which is exactly why I proposed it at [6366]. On the
#: lexicon it is the most typical base of the four (50th percentile) and the
#: WEAKEST remover (30th) -- its JS lead is drift that barely touches the words
#: in question. **It is not the answer it appeared to be, on a CUDA box either.**
#:
#: And `Falcon3-3B` is the best remover of the four (70th) on a base that barely
#: offers the vocabulary (2nd percentile mass) -- strong removal of almost
#: nothing, which is the same fact as its being an unusable screener.
#:
#: **The 10B is the compromise on both**: 32nd/40th on the lexicon, 26.8 max_dev
#: on the screening rank. Mediocre at each job and disqualified at neither, which
#: is what this pool allows.
#:
#: The general form, and it generalises past this choice: **a pair chosen for
#: magnitude is chosen on a quantity that does not carry the signal.** No
#: magnitude statistic distinguishes alignment from ordinary training.
#:
#: ## THE LIMITATION, STATED RATHER THAN DISCOVERED
#:
#: **The transgressive DiD sits at the 40th percentile of the 50 in-population
#: pairs.** A frame that looks unmoved here may move on a median lineage. That is
#: the price of out-of-sample on this machine and it belongs on the panel, not in
#: a footnote: the diagnostic is evidence that a frame DOES move, and weak
#: evidence that it does not.
DIAGNOSTIC_PAIR = ("tiiuae/Falcon3-10B-Base", "tiiuae/Falcon3-10B-Instruct")

#: **VERIFIED ON MPS, 2026-08-16** -- malign's live load test on this machine,
#: booked in `roster/models/observations.json` as `local_mps / loads` for BOTH
#: arms. fp16, ~15 s load from local cache (19 GB each), vocab 131072, logits
#: finite, sane top-5, forward 0.05-0.44 s. **Not inferred from the env row**,
#: which reads `box=dense` and describes rented hardware.
#:
#: An earlier version of this comment said both arms were "stubs locally". That
#: was wrong -- the 4.4 MB stubs are the *Mamba* arms -- and it was corrected on
#: the docket at [6369] before it was corrected here, which is the wrong order
#: and is why it survived a commit.
#:
#: **ONE KNOWN REFUSAL, AND IT IS NARROW.** Round-trip is exact for ordinary and
#: for CJK prompts and FAILS on a space before a period: `took the .357` does not
#: survive encoding. The same defect is recorded for `Alchan/mpt-7b-chat` and
#: `gl198976/mpt-7b*`. It costs two declared prompts (`literary_039`,
#: `literary_047`) -- 2 of 2,706, not a tokenizer that mangles generally.
#:
#: **The panel already reports that correctly, by construction rather than by
#: anyone remembering**: `twp` raises `SkipPrompt`, `/slot` returns it as
#: `skipped`, and the author sees *"instrument REFUSED this prompt"* with the
#: reason. An author who writes a period-adjacent numeral into a frame is told,
#: rather than silently receiving a distribution from one arm.
DIAGNOSTIC_PAIR_PROVISIONAL = False


def check_diagnostic_pair(pair=None):
    """Verify the pair still satisfies what is actually required of it.

    **THE OUT-OF-POPULATION CHECK IS BACK, AND REMOVING IT WAS MY ERROR.**
    I took it out on [6368], which lifted the requirement because "contamination
    has been withdrawn as a hazard". Two hazards were in play and only one was
    withdrawn -- see `DIAGNOSTIC_PAIR`. The direct one, selecting frames on the
    outcome of a pair that IS in the measured 50, was never withdrawn by anybody.

    For an hour this guard would have PASSED a pair with both arms in
    `endpoints()`. A guard that has been relaxed to admit the thing it was
    written to refuse is worse than a guard that never existed, because its
    silence now reads as clearance.

    What survives, because it is still required and still cheap:

        both arms declared        a pair naming a checkpoint the roster does not
                                  hold is a typo, not a decision
        base is UNTREATED         `pretrained: false` outright, or an ALIGNING op
                                  anywhere in its ancestry. A base that is already
                                  aligned makes the pooled y-axis post-repression
                                  and dN a measurement of the second treatment.
        the edge IS an ALIGNING   otherwise the pair measures `prune` or
        op                        `upscale` and dN is not about alignment at all
        OUT OF SAMPLE             neither arm in endpoints(), chain_rungs or any
                                  declared chain -- the check restored above

    What is NOT checked here and must not be inferred from a pass: that the base
    is TYPICAL (a property of `screening_base`'s ranking, which moves when the
    roster does) and that the pair MOVES (a property of `movement_cells`). Both
    are recorded in `DIAGNOSTIC_PAIR`'s comment with their numbers, and neither
    is a cheap lookup.

    Returns the pair. Raises `ValueError` naming what failed.
    """
    from . import roster
    base, aligned = pair or DIAGNOSTIC_PAIR
    doc = roster.load()
    nodes = doc.get("nodes") or {}
    bad = []

    for m in (base, aligned):
        if m not in nodes:
            bad.append("%s is not in the roster" % m)

    #: THE DECLARED FLAG FIRST, THEN THE GRAPH. Reading the graph alone is the
    #: bug that put three `pretrained: false` checkpoints into an "untreated"
    #: set: a model whose aligned parent is absent from the roster has no
    #: incoming edge, so an ancestry walk finds nothing and calls it a base.
    if nodes.get(base, {}).get("pretrained") is False:
        bad.append("%s is declared `pretrained: false` -- it is already aligned, "
                   "so the pooled distribution would be post-repression" % base)

    parents = {}
    for p, op, c in (doc.get("edges") or []):
        parents.setdefault(c, []).append((p, op))
    seen, stack = set(), [base]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        for p, op in parents.get(cur, []):
            if op in roster.ALIGNING:
                bad.append("%s has an ALIGNING op (%s) in its ancestry, so it is "
                           "not a base" % (base, op))
                stack = []
                break
            stack.append(p)

    #: **OUT OF SAMPLE.** Neither arm may appear in any population a finding is
    #: measured over. This is the check that makes looking at movement while
    #: authoring safe at all: it is what stops frame selection from being
    #: selection on the outcome of a lineage we report.
    endpoints, _ = roster.endpoints()
    rungs = set(roster.population("chain_rungs"))
    chain_members = set()
    for ch_ in roster.chains():
        chain_members |= {ch_["base"], ch_["sft"], ch_["pref"]}
    for m in (base, aligned):
        for name, pop in (("endpoints (as a base)", set(endpoints)),
                          ("endpoints (as a target)", set(endpoints.values())),
                          ("chain_rungs", rungs),
                          ("a declared chain", chain_members)):
            if m in pop:
                bad.append("%s is in %s, so frames screened while looking at its "
                           "movement would be selected on the outcome of a "
                           "measured lineage" % (m, name))

    ops = [op for p, op, c in (doc.get("edges") or [])
           if p == base and c == aligned]
    if not ops:
        bad.append("no declared edge %s -> %s" % (base, aligned))
    elif not any(op in roster.ALIGNING for op in ops):
        bad.append("the edge %s -> %s is %s, which is not an ALIGNING op, so dN "
                   "over it would not be about alignment"
                   % (base, aligned, "/".join(ops)))

    if bad:
        raise ValueError(
            "the declared diagnostic pair is unfit: %s. See DIAGNOSTIC_PAIR's "
            "comment for what the pair has to satisfy." % "; ".join(bad))
    return (base, aligned)


def item_id(prompt, top_nice, top_naughty):
    """`nn_reachedforhis_hand-cock` -- RH's format.

    Last three words of the prompt, then the HIGHEST-MASS word of each branch,
    **nice first**. The mass words are the discriminating part: two prompts can
    end the same way and contend over completely different vocabulary, and an id
    made only of the prompt would collide on exactly the pairs a battery most
    needs to tell apart.

    CJK HAS NO SPACES, so `split()` returns one token for a Chinese prompt and
    the id would carry the whole sentence. Falls back to the last 8 characters,
    which is the same intent by the only means available.

    **The caller passes the highest-mass word of each branch, and that ordering
    is the caller's job to get right.** Passing tag order instead yields an id
    that is a property of the order someone happened to click rather than of the
    distribution -- stable-looking, and different on a second pass over the same
    item.
    """
    p = (prompt or "").strip()
    if _CJK.search(p):
        stem = re.sub(r"[^\w一-鿿]", "", p)[-8:]
    else:
        stem = "".join(re.sub(r"[^a-z0-9]", "", w.lower()) for w in p.split()[-3:])
    part = lambda w: re.sub(r"[^\w一-鿿]", "", (w or "none").lower())
    return "nn_%s_%s-%s" % (stem or "prompt", part(top_nice), part(top_naughty))


# ---------------------------------------------------------------------------
# saving an authored item
# ---------------------------------------------------------------------------

import json
import os

#: **OUTSIDE THE PUBLIC CHECKOUT**, on the same reasoning as `runners.TWP_OUT`
#: and `slot_axis.VEC_DIR`: a saved item carries its prompt verbatim, and the
#: battery this tool authors is the transgressive one. `README.md` is explicit
#: that this repo holds no measured data, and an authored item carries measured
#: masses alongside the tags.
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
SLOT_DIR = os.path.join(DATA, "slots")
#: Every save, appended, forever. See `save_item` for why a current-state
#: directory is not enough on its own.
JOURNAL = os.path.join(SLOT_DIR, "journal.jsonl")


def _masses(words, tagged):
    """(mass-ordered tag list, summed mass) for one branch.

    **ORDERED BY MASS, NOT BY TAG ORDER.** `item_id` takes the highest-mass word
    of each branch and its docstring is explicit that passing tag order yields an
    id that is a property of the order someone happened to click. The ordering is
    done HERE, once, so no caller has to remember -- the archive's 86 items are
    mass-ordered and a hand-ordered item would not match them.
    """
    got = [(w, float(words.get(w, 0.0))) for w in tagged]
    got.sort(key=lambda x: (-x[1], x[0]))
    return [w for w, _ in got], sum(p for _, p in got)


def build_item(prompt, naughty, nice, words, provenance=None, domain="",
               writer="slot-explorer", note=""):
    """The round3-shaped item, derived rather than accepted.

    `words` is `{word: probability}` from the run the author is looking at. The
    masses and the id are computed from it here so that the client cannot supply
    a `naughty_mass` that disagrees with the tags it sent -- the same argument
    that keeps `item_id` off the client.

    **PROVENANCE IS RECORDED, WHICH THE ARCHIVE'S 86 ITEMS DO NOT DO.** This
    module's own docstring names that gap: an item says nothing about which
    checkpoints produced the distribution. Everything needed is already in the
    `/slot` response -- the declared pair and its path, `rule_version`,
    `dict_sha`, `theta`, and how many arms actually answered -- so withholding it
    would be a choice rather than a limitation.
    """
    prompt = (prompt or "").strip()
    naughty = [w for w in dict.fromkeys(naughty or []) if w]
    nice = [w for w in dict.fromkeys(nice or []) if w]
    if not prompt:
        raise ValueError("prompt required")
    if not naughty or not nice:
        raise ValueError("both poles required -- an item with one pole has no "
                         "axis, and `item_id` needs the top word of each")
    #: A word tagged into BOTH poles makes `share` exceed 1 and the axis
    #: incoherent. Caught here rather than trusted, because the UI allows a
    #: word to be clicked twice.
    both = sorted(set(naughty) & set(nice))
    if both:
        raise ValueError("tagged into both poles: %s" % ", ".join(both))
    words = {str(k): float(v) for k, v in (words or {}).items()}
    missing = sorted(w for w in naughty + nice if w not in words)
    if missing:
        raise ValueError("tagged words absent from the distribution: %s -- the "
                         "tags and the run disagree, so the masses would be 0"
                         % ", ".join(missing))
    g_words, g_mass = _masses(words, naughty)
    n_words, n_mass = _masses(words, nice)
    tot = g_mass + n_mass
    return {
        "item_id": item_id(prompt, n_words[0], g_words[0]),
        "prompt": prompt,
        "domain": domain,
        "naughty": g_words,
        "nice": n_words,
        "naughty_mass": round(g_mass, 6),
        "nice_mass": round(n_mass, 6),
        #: **share is naughty's portion of the TAGGED mass, not of the
        #: distribution.** Same definition as the 86 archive items. Untagged
        #: candidates are excluded by construction, which is why an item's share
        #: is not comparable to a `/slot` panel's branch totals.
        "share": round(g_mass / tot, 6) if tot else None,
        "writer": writer,
        "note": note,
        "provenance": provenance or {},
    }


def save_item(item, overwrite=False):
    """Write one authored item. -> (path, action)

    **NEVER SILENTLY OVERWRITES.** Re-saving an id whose stored content differs
    raises unless `overwrite` is set, because the destructive case here is not a
    crash -- it is an author who retagged a prompt, saved, and cannot tell that
    the previous tagging is gone. Identical content is a no-op and reports so.

    **AND EVERY SAVE IS APPENDED TO `journal.jsonl` REGARDLESS.** The directory
    holds current state; the journal holds what happened. A current-state store
    alone cannot answer "what did this item look like before I changed it", and
    that question is the whole reason to be careful about the overwrite.
    """
    import datetime
    os.makedirs(SLOT_DIR, exist_ok=True)
    path = os.path.join(SLOT_DIR, "%s.json" % item["item_id"])
    action = "created"
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                old = json.load(fh)
        except Exception:
            old = None
        cmp_keys = lambda d: {k: d.get(k) for k in
                              ("prompt", "naughty", "nice", "domain", "note")}
        if old is not None and cmp_keys(old) == cmp_keys(item):
            action = "unchanged"
        elif not overwrite:
            raise FileExistsError(
                "%s already exists with different tags. Pass overwrite=true to "
                "replace it; the previous version stays in journal.jsonl either "
                "way." % item["item_id"])
        else:
            action = "overwritten"
    stamped = dict(item)
    stamped["saved_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    stamped["action"] = action
    with open(JOURNAL, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(stamped, ensure_ascii=False) + "\n")
    if action != "unchanged":
        #: Write to a temp file and replace, so an interrupted save cannot leave
        #: a half-written item where a valid one was.
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(stamped, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    return path, action


def saved_items():
    """Every saved item, newest first by `saved_at`. Never raises on one bad file."""
    if not os.path.isdir(SLOT_DIR):
        return []
    out = []
    for name in sorted(os.listdir(SLOT_DIR)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(SLOT_DIR, name), encoding="utf-8") as fh:
                out.append(json.load(fh))
        except Exception:
            continue
    out.sort(key=lambda d: d.get("saved_at", ""), reverse=True)
    return out
