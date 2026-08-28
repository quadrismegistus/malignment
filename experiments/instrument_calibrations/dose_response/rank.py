"""Which prompts displace, and by what relation? multi v6 over English, five lineages.

    .venv/bin/python -u rank.py --plan
    .venv/bin/python -u rank.py --task multi
    .venv/bin/python -u rank.py --report

This is the thing the calibration was for. `task_multi` sorts a frame's real
competitors into every RELATION that holds among them -- displacement,
substitution, vocalisation, rationalisation, deferral, intensity, valence,
specificity -- blind to the arm; this runs it over every English prompt with
cells, on five lineages, and computes

    displacement = base mass on the marked words - aligned mass on them

per (prompt, lineage). The prompt-level figure is the MEDIAN over lineages, and
the number of lineages that displace is reported beside it, because a prompt
that moves on one arm of five is a different object from one that moves on all
five and a median alone cannot tell them apart.

Each row also carries `splits`, one entry per relation with its OWN poles and
masses. The per-relation sign is computable only from those: the reduced
`naughty` field pools splits that can point in opposite directions.

## THE FIVE, AND WHY NOT THE OBVIOUS FIVE

Chosen to span behaviour already measured, not at random and not by convenience:

    Amber -> AmberSafe        moves DOWN (author-tagged -0.0232), safety-DPO only
    SmolLM3-3B-Base -> 3B     moves UP   (author-tagged +0.0050)
    Llama-3.1-8B -> Instruct  the deferral case: took/had/tried/were/would rise
    Qwen2.5-7B -> Instruct    strong mover, and the bridge to any later zh run
    gemma-2-9b -> it          a fifth lab with no prior read on this instrument

**NOT the five judged Chinese-fluent pairs**, though they would have cost the
same and covered zh too. Those are Yi, Qwen2.5, Qwen3, CT-LLM and glm-4 -- five
Chinese labs. Lineage is being used here as a REPLICATE, and replicates drawn
from one training culture are not replicates. Chinese runs separately, on the
only lineages that can carry it, as its own declared population.

## WHAT IS FIXED BEFORE THE RUN

    instrument     task_multi v6, 10 shots, sha256 06b0b4295a986138. Chosen on
                   the 251 hand-authored slots against the authors' own poles:
                   recall 0.840, precision 0.929, recovered displacement -0.0159
                   against the hand poles' -0.0236. The predecessors are at
                   f238e97 and before; nothing reads two versions as one
                   population.
    reduction      `unanimous` -- marked in at least one split and unmarked in
                   none. Overlap is the schema's premise (`shouted` is unmarked
                   against `punched`, marked against `said`) and 48 of 250
                   calibration cells held a word the rater contradicted across
                   splits, so summing the union is unsound.
    candidates     union of words >= 1% mass in EITHER arm, content words only,
                   ADV stoplist applied (`so`, `very`, `out`, `there` are ADV in
                   these frames and survived the old CONTENT filter)
    threshold      a prompt "displaces" on a lineage at displacement > 0.02

The threshold is declared here rather than chosen from the output, because the
count of displacing prompts is a direct function of it. **It was calibrated on
the OLD tagger** (45% of slots against 14% of neutral prompts) and has not been
recomputed for v6, whose firing and mass profile differ; treat it as a declared
cut, not a measured separation, until it is redone.

## THE SUPERORDINATE BIAS IS NOT KNOWN TO SURVIVE, AND IS NOT KNOWN TO BE GONE

The old tagger put the generic term in `naughty` -- `clothes` on the undressing
frame, `衣服` in Chinese, so it was not an English quirk. That word is where
displacement goes TO, so including it cancelled part of the fall: on the worked
case it halved the effect, -0.1693 to -0.0844, and every figure in
`rank_en5.jsonl` is an understatement by an amount varying with how
superordinate-heavy the frame is.

v6 has SPECIFICITY as its own relation, running at +0.0073 over 22 calibration
splits, which is exactly where a generic term should now land instead. Whether
that removes the bias, reduces it, or moves it somewhere else HAS NOT BEEN
MEASURED on this instrument. Do not read these figures as unbiased and do not
read them as corrected.
"""

import argparse
import base64
import collections
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
sys.path.insert(0, HERE)

from malignment import ch, pos                                       # noqa: E402
from malignment.prompts import Prompts                               # noqa: E402
import score_slots as S                                              # noqa: E402
import task_by_model as T                                            # noqa: E402
import task_multi as M                                               # noqa: E402

PAIRS = [("LLM360/Amber", "LLM360/AmberSafe"),
         ("HuggingFaceTB/SmolLM3-3B-Base", "HuggingFaceTB/SmolLM3-3B"),
         ("meta-llama/Llama-3.1-8B", "meta-llama/Llama-3.1-8B-Instruct"),
         ("Qwen/Qwen2.5-7B", "Qwen/Qwen2.5-7B-Instruct"),
         ("google/gemma-2-9b", "google/gemma-2-9b-it")]
WORDING, SHOTS = "B", 4
DISPLACES = 0.02
OUT = os.path.join(HERE, "results", "rank_en5_multi.jsonl")


def prompts(lang="en"):
    L = {p.text: p.language for p in Prompts.all()}
    rows = ch.query("SELECT DISTINCT prompt FROM twp_words_v4 WHERE frame=''")
    return sorted(r["prompt"] for r in rows if L.get(r["prompt"]) == lang)


def cells(prompt, base, aligned):
    """([content words], {word: (p_base, p_aligned)}) or None."""
    b64 = base64.b64encode(prompt.encode()).decode()
    rows = ch.query(
        "SELECT model, word, argMax(p,(topup,prompt_cache,mtime)) p FROM twp_words_v4 "
        "WHERE base64Encode(prompt)='%s' AND frame='' AND model IN ('%s','%s') "
        "GROUP BY model, word" % (b64, base, aligned))
    if not rows:
        return None
    d = collections.defaultdict(dict)
    for r in rows:
        d[r["model"]][r["word"]] = float(r["p"])
    if base not in d or aligned not in d:
        return None
    ws = sorted({w for m in (base, aligned) for w, p in d[m].items() if p >= S.THETA},
                key=lambda w: -max(d[base].get(w, 0), d[aligned].get(w, 0)))
    if not ws:
        return None
    tag = pos.get_pos(ws, prompt)
    #: `S.is_content`, not `tag in S.CONTENT` -- the ADV stoplist lives there and
    #: this producer must not diverge from the one the calibration was scored on.
    ws = [w for w in ws if S.is_content(w, tag.get(w))]
    if len(ws) < S.MIN_CONTENT:
        return None
    return ws, {w: (d[base].get(w, 0.0), d[aligned].get(w, 0.0)) for w in ws}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--task", default="multi", choices=("multi", "tagger"))
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)

    if a.report:
        return report(a.out)

    ps = prompts(a.lang)
    if a.limit:
        ps = ps[:a.limit]
    print("%s prompts with cells: %d | lineages: %d" % (a.lang, len(ps), len(PAIRS)),
          flush=True)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    #: RESUMABLE BY (prompt, base). The tagger's own stash makes a repeat call
    #: free, but building the candidate list is one ClickHouse query per cell
    #: and that is the slow half -- 12,880 of them is not something to redo.
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try:
                r = json.loads(line)
                done.add((r["prompt"], r["base"]))
            except Exception:
                pass
    print("already written: %d" % len(done), flush=True)

    #: **THE DEFAULT IS `multi` v6, NOT THE TAGGER THIS FILE WAS WRITTEN FOR.**
    #: `rank_en5.jsonl` (11,309 cells, 28 Aug) was produced by `task_by_model`
    #: before any of the calibration, and it carries that instrument's defects:
    #: a marked pole defined negatively, which fills with ordinary words, and a
    #: superordinate bias that signs every figure downward. It also has no
    #: `relations` field, because that instrument returns no typology. Its
    #: candidate lists are pre-ADV-stoplist as well, so `so`, `very`, `out` and
    #: `there` are in them.
    #:
    #: v6 is chosen on the 251 hand-authored slots: recall 0.840, precision
    #: 0.929, recovered displacement -0.0159 against the hand poles' -0.0236,
    #: instrument_sha256 06b0b4295a986138. `--task tagger` reproduces the old
    #: run for comparison; nothing reads the two as one population.
    t = (M.task(shots=M.EXAMPLES) if a.task == "multi"
         else T.task(WORDING, shots=T.EXAMPLES[:SHOTS]))
    for b, al in PAIRS:
        todo = [p for p in ps if (p, b) not in done]
        print("\n=== %s -> %s : %d to do"
              % (b.split("/")[-1], al.split("/")[-1], len(todo)), flush=True)
        if a.plan or not todo:
            continue
        built, skipped = [], 0
        for p in todo:
            c = cells(p, b, al)
            if c is None:
                skipped += 1
                continue
            built.append((p, c))
        print("    built %d candidate lists, %d skipped (no cells or <%d content words)"
              % (len(built), skipped, S.MIN_CONTENT), flush=True)
        res = t.map([T.render(p, c[0]) for p, c in built], num_workers=a.workers)
        with open(a.out, "a", encoding="utf-8") as fh:
            for (p, (ws, m)), r in zip(built, res):
                if r is None:
                    continue
                #: `S._poles` reduces EITHER schema. Under multi the default mode
                #: is `unanimous`: a word marked in one split and unmarked in
                #: another is dropped from both poles rather than assigned to
                #: either, because markedness belongs to the pair and 48 of 250
                #: calibration cells contained such a word.
                mk, un, ch = S._poles(r)
                real = [w for w in mk if w in m]
                row = dict(
                    prompt=p, base=b, aligned=al, lang=a.lang,
                    charged=bool(ch), n_cand=len(ws),
                    naughty=mk, nice=un,
                    invented=len(mk) - len(real),
                    mass_base=sum(m[w][0] for w in real),
                    mass_aligned=sum(m[w][1] for w in real))
                if hasattr(r, "splits"):
                    #: the typology, one entry per split, WITH its own poles and
                    #: mass. The per-relation sign is only computable from these:
                    #: the reduced `naughty` above pools splits that can point in
                    #: opposite directions.
                    row["relations"] = [s.relation for s in r.splits]
                    row["splits"] = [dict(
                        relation=s.relation, axis=s.axis,
                        marked=list(s.marked), unmarked=list(s.unmarked),
                        mass_base=sum(m[w][0] for w in s.marked if w in m),
                        mass_aligned=sum(m[w][1] for w in s.marked if w in m))
                        for s in r.splits]
                    row["reading"] = r.reading
                else:
                    row["axis"] = r.axis
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("    wrote %d" % len(built), flush=True)
    report(a.out)


def report(path):
    if not os.path.exists(path):
        print("nothing at %s" % path)
        return
    rows = [json.loads(l) for l in open(path) if l.strip()]
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["prompt"]][r["base"]] = r["mass_base"] - r["mass_aligned"]
    print("\ncells: %d over %d prompts x %d lineages"
          % (len(rows), len(by), len({r["base"] for r in rows})))
    full = {p: v for p, v in by.items() if len(v) == len(PAIRS)}
    print("prompts measured on ALL %d lineages: %d" % (len(PAIRS), len(full)))
    if not full:
        return
    rank = sorted(((st.median(v.values()), sum(1 for x in v.values() if x > DISPLACES), p)
                   for p, v in full.items()), reverse=True)
    print("\nTOP 25 by median displacement (n_up = lineages above %.2f)" % DISPLACES)
    for med, up, p in rank[:25]:
        print("   %+.4f  %d/%d  %r" % (med, up, len(PAIRS), p[:64]))
    print("\nBOTTOM 10")
    for med, up, p in rank[-10:]:
        print("   %+.4f  %d/%d  %r" % (med, up, len(PAIRS), p[:64]))
    c = collections.Counter(up for _, up, _ in rank)
    print("\nlineages displacing, per prompt: %s"
          % {k: c[k] for k in sorted(c)})


if __name__ == "__main__":
    main()
