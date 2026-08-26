"""Rate a tier of the priority manifest with the existing v6 instrument.

    python -u rate.py --tier 0                     # UNIFORM manifest, routed by lang
    python -u rate.py --tier 1                     # Chinese      -> results/v6zh/
    python -u rate.py --tier 2                     # en high-dose -> results/v6/
    python -u rate.py --tier 0 --limit 5           # smoke

Was `rate_zh.py`. Renamed once it stopped being Chinese-specific: tier 0 mixes
languages and the instrument is chosen per prompt, so the old name described the
first thing it was used for rather than what it does.

Reads `~/malignment-data/contextual_norms/priority.csv.gz` from `priority.py`.
Its output is consumed by `experiments/displacement/named_under_dose/predict.py`
via `fields.contextual_norms`.

## WHICH DIRECTORY, AND WHY IT IS NOT COSMETIC

`_slot_index` takes the instrument name from the directory basename, so the output
path decides whether a rating merges with an existing pool or stands apart.

  tier 1 (zh) -> `results/v6zh/`.  Chinese content rated with English glosses is a
                 different measurement from English v6 until someone shows it is
                 not, and `contextual_norms(prompt, instrument="v6zh")` selects it
                 deliberately.
  tier 2/3 (en) -> `results/v6/`.  Same instrument, same language, same kind of
                 content as the 276 prompts already there. Separating these would
                 be the mirror error: every analysis written against `v6` would
                 silently not see them. Filenames carry an `en_<sha>` id so they
                 cannot collide with the pilot3 `item_id` files already present.

Writes `experiments/slot_ratings/results/v6zh/rated_v6zh_<id>.json`, one file per
prompt, in the record shape `fields._slot_index` reads: a bare list of dicts each
carrying `prompt`, `word`, and numeric scales.

## WHY v6zh AND NOT v6

`_slot_index` takes the instrument name from the directory basename, so these land
as `v6zh` rather than merging into `v6`. They are Chinese content rated with an
ENGLISH instrument -- English scale glosses, English system prompt -- and that is a
different measurement from `v6` on English content until someone shows it is not.
Keeping them separable costs nothing and means no analysis can pool them by
accident; `contextual_norms(prompt, instrument="v6zh")` selects them deliberately.

## THE INSTRUMENT WAS NOT BUILT FOR THIS AND WORKS ANYWAY

An earlier claim in `priority.py` -- that the Chinese arm was blocked because
`SlotRatingENv6` is English-only -- was inferred from the class name and was false.
Smoke test on 5 pairs, 0 errors, sane profiles, discrimination within Chinese
(`死` vs `停` moves aggression 1->5), and the one translation-matched pair agreed
with its English twin on all twelve scales.

**What that established is that the instrument RUNS, not that its output is
comparable across languages.** There is no translation key in the data -- pair_id,
kernel_id and archive_prompt_id all span zero cross-language groups -- so a matched
study needs the correspondence reconstructed first. Absence of systematic offset is
the target, never exact agreement.

## THE `reading` FIELD IS THE AUDIT

The task returns a one-line paraphrase of the completed sentence. On English it is
a nicety; here it is the check that the rater understood the Chinese at all. A
`reading` that mistranslates its own item makes every scale on that row worthless,
and it is visible without a second rater. `--audit` prints a sample.
"""

import argparse, csv, gzip, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
SLOT = os.path.abspath(os.path.join(HERE, "..", "..", "slot_ratings"))
sys.path.insert(0, SLOT)
#: tier 0 is the UNIFORM manifest and mixes languages, so the instrument is chosen
#: PER PROMPT from its own `lang` column rather than per tier. Routing a Chinese
#: prompt into `results/v6/` would pool two measurements under one instrument name,
#: which is the thing v6zh exists to prevent.
DIRS = {1: ("v6zh", "zh"), 2: ("v6", "en"), 3: ("v6", "en")}
BY_LANG = {"en": "v6", "zh": "v6zh"}

#: OTHER INSTRUMENTS. `--instrument` swaps the task and the output directory; the
#: manifest, the resume and the record shape are unchanged.
#:
#:   inst_v3   InstitutionalSupplementENv3. v2 is a STRICT SUBSET -- same 11 scales,
#:             and all 276 of its prompts sit inside v3's 462 -- so running both
#:             double-counts every shared construct. v3 only.
#:   sexual    SexualSlotEN. RESTRICTED BY DEFAULT, because a smoke test on four
#:             random non-sexual frames returned orality/tactility/genitality/
#:             incorporation at 1.0 with RANGE ZERO on every word. That is not a low
#:             value, it is no variance: it cannot produce a dose slope, cannot beat
#:             its own shuffle, and cannot contribute to anything. `--domain` keeps
#:             it to the frames it was built for, plus a documented off-domain
#:             control so the floor is recorded rather than assumed.
TASKS = {
    "v6":      ("slot_ratings/task.py",               "SlotRatingENv6",           "v6"),
    "inst_v3": ("slot_ratings/institutional/task.py", "InstitutionalSupplementENv3",
                                                      "slot_institutional_en_v3"),
    "sexual":  ("slot_ratings/sexual/task.py",        "SexualSlotEN", "sexual_slot_en_v2"),
}
MANIFEST = os.path.expanduser("~/malignment-data/contextual_norms/priority.csv.gz")


def pid(prompt, lang):
    return "%s_%s" % (lang, hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:12])


def load(tier, min_lineages, domains=None, control=0):
    """-> {prompt: [rows]} for the requested tier, biggest frame first.

    `domains` keeps only prompts in those prompt-table domains. `control` then adds
    that many OFF-domain pairs, so a floor is DOCUMENTED rather than assumed -- the
    sexual instrument returns 1.0 at range ZERO on non-sexual frames, and a constant
    is not a low value: it cannot produce a slope, cannot beat its own shuffle, and
    cannot contribute to anything. Recording it costs a few hundred calls.
    """
    import collections, random
    by = collections.defaultdict(list)
    with gzip.open(MANIFEST, "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if int(r["tier"]) != tier or int(r["n_lineages"]) < min_lineages:
                continue
            by[r["prompt"]].append(r)
    if domains:
        from malignment import ch
        dom = {x["prompt"]: x["domain"]
               for x in ch.query("SELECT prompt, domain FROM prompts")}
        want = {d.strip() for d in domains.split(",")}
        inn = {p: v for p, v in by.items() if dom.get(p) in want}
        out = {p: v for p, v in by.items() if dom.get(p) not in want}
        print("domain filter %s: %d prompts in, %d out"
              % (sorted(want), len(inn), len(out)), flush=True)
        if control and out:
            rng = random.Random(20260826)
            n = 0
            for p in rng.sample(sorted(out), min(len(out), 40)):
                if n >= control:
                    break
                inn[p] = out[p][:8]
                n += len(inn[p])
            print("  + %d off-domain CONTROL pairs over %d prompts"
                  % (n, sum(1 for p in inn if dom.get(p) not in want)), flush=True)
        by = inn
    return sorted(by.items(), key=lambda kv: -len(kv[1]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, default=1, choices=(0, 1, 2, 3))
    ap.add_argument("--instrument", default="v6", choices=sorted(TASKS),
                    help="which rating task; see TASKS")
    ap.add_argument("--domain", default=None,
                    help="comma list of prompt domains to keep (e.g. sexual)")
    ap.add_argument("--control", type=int, default=0,
                    help="ALSO rate this many off-domain pairs, so a floor is "
                         "DOCUMENTED rather than assumed")
    ap.add_argument("--min-lineages", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--audit", type=int, default=6, help="readings to print per file")
    a = ap.parse_args(argv)

    import importlib.util
    rel, clsname, outdir = TASKS[a.instrument]
    _p = os.path.abspath(os.path.join(HERE, "..", "..", rel))
    _sp = importlib.util.spec_from_file_location("task_%s" % a.instrument, _p)
    _m = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(_m)
    TaskCls, render = getattr(_m, clsname), _m.render
    SCALES = [k for k, f in TaskCls.schema.model_fields.items()
              if f.annotation is int]
    print("instrument %s -> %s, %d int scales -> results/%s"
          % (a.instrument, clsname, len(SCALES), outdir), flush=True)

    frames = load(a.tier, a.min_lineages, a.domain, a.control)
    if a.tier == 0:
        print("tier 0 (uniform): instrument chosen per prompt from its lang column",
              flush=True)
    else:
        print("tier %d -> instrument %r" % (a.tier, DIRS[a.tier][0]), flush=True)

    def route(rows):
        lg = rows[0].get("lang") or DIRS.get(a.tier, ("v6", "en"))[1]
        if a.instrument != "v6":
            return outdir, lg
        return BY_LANG.get(lg, "v6"), lg
    if a.limit:
        frames = frames[:a.limit]
    def path_for(p, rs):
        inst, lg = route(rs)
        return os.path.join(SLOT, "results", inst,
                            "rated_%s_%s.json" % (inst, pid(p, lg)))
    todo = [(p, rs) for p, rs in frames if not os.path.exists(path_for(p, rs))]
    print("tier %d: %d prompts, %d pairs | %d prompts already done | %d to run"
          % (a.tier, len(frames), sum(len(r) for _, r in frames),
             len(frames) - len(todo), len(todo)), flush=True)
    for _i in set(BY_LANG.values()) | {outdir}:
        os.makedirs(os.path.join(SLOT, "results", _i), exist_ok=True)

    t = TaskCls()
    done_pairs = n_err = 0
    for i, (prompt, rows) in enumerate(todo, 1):
        inst, lang = route(rows)
        words = [r["word"] for r in rows]
        errs = {}
        res = t.map([render(prompt, w) for w in words],
                    metadata_list=[{"prompt": prompt, "word": w} for w in words],
                    num_workers=a.workers, errors=errs)
        recs = []
        for r, out in zip(rows, res):
            if out is None:
                n_err += 1
                continue
            d = {"prompt": prompt, "word": r["word"], "item_id": pid(prompt, lang),
                 "lang": lang, "pos": r.get("pos", ""),
                 #: PROVENANCE GOES IN AS STRINGS. `_slot_index` treats EVERY
                 #: numeric field as a scale, so writing these as int/float made
                 #: them predictors: `consistency` is the share of a pair's
                 #: lineages agreeing on direction -- a function of the OUTCOME --
                 #: and it leaked into the Chinese contextual models. It also broke
                 #: the English pool, because the 303 pre-existing v6 files lack
                 #: these keys and every cell from them was then dropped for having
                 #: an incomplete scale set (coverage 19.9% -> 1.9%).
                 "_n_lineages": str(r["n_lineages"]),
                 "_consistency": str(r["consistency"]),
                 "ratable": out.ratable, "reading": out.reading}
            for s in SCALES:
                d[s] = getattr(out, s, None)
            recs.append(d)
        path = path_for(prompt, rows)
        #: written whole, never appended -- a partial file that looks complete is
        #: the failure mode the pos tables just demonstrated.
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(recs, fh, ensure_ascii=False, indent=1)
        done_pairs += len(recs)
        rat = sum(1 for d in recs if d.get("ratable"))
        print("[%4d/%-4d] %-26s %4d words | %3d ratable | %d errors | total %d"
              % (i, len(todo), prompt[:26], len(recs), rat, len(errs), done_pairs),
              flush=True)
        if a.audit and i <= 2:
            #: the audit line must not assume v6's scale names -- the
            #: institutional and sexual schemas have none of them.
            show = [x for x in SCALES if x in recs[0]][:3]
            for d in recs[:a.audit]:
                print("      %-10s %s | %s"
                      % (d["word"],
                         "  ".join("%s %s" % (k[:11], d.get(k)) for k in show),
                         (d.get("reading") or "")[:60]), flush=True)
    print("\nDONE: %d pairs rated, %d errors" % (done_pairs, n_err))
    return 0


if __name__ == "__main__":
    sys.exit(main())
