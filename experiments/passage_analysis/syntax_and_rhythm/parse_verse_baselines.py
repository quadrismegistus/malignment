"""Verse baselines for H2's meter windows, from generative-formalism. EXPLORATORY.

    python parse_verse_baselines.py --smoke            a few poems per source, to $TMPDIR
    python parse_verse_baselines.py --workers 6        all sources -> by_window_verse.csv

Not in the registration: an independent observation of LLM (and human) meter,
added 2026-09-24 at RH's request, to ask whether what alignment does to the
metricality of PROSE (H2) also holds in VERSE.

## SOURCES (Heuser, "Generative Aesthetics", JCA 10.3, 2025)

Data from ~/github/generative-formalism/data/data_as_in_paper/ ($GENFORM_DATA):

    human_period      corpus_sample_by_period.csv.gz: Chadwyck-Healey poems,
                      1,000 per 50-year period 1600-2000; --per-period sampled
    genai_prompt      genai_rhyme_promptings.csv.gz: poems written on request by
                      chat models (prompt_type DO_rhyme / do_NOT_rhyme /
                      MAYBE_rhyme); --per-cell sampled per (model, prompt_type)
    genai_completion  genai_rhyme_completions.csv.gz: models continue a human
                      poem after its first 5 lines. TWO BASE/INSTRUCT PAIRS on
                      shared prompts -- llama3.1:8b-text vs llama3.1:8b, and
                      mistral:text vs mistral -- plus `line_real`, the human
                      poem's own continuation OF THE SAME LINES (arm "human").
                      Only prompts every member of a pair completed are kept.

## PROTOCOL

Identical to by_window.csv (see parse_passages_prosodic.py): lineation ignored,
canonical syllables, non-overlapping 10-syllable word-boundary windows,
lowercase, unpunctuated, the 2020 constraint set, s <= 2, w <= 2. The same
functions are imported, not copied, so the two files cannot drift apart.

Output: $MALIGNMENT_DATA/syntax_and_rhythm/by_window_verse.csv, one row per
(source, model, arm, poem, win_idx), with the baseline's meter columns.
"""

import argparse
import hashlib
import os
import random
import sys
import warnings

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from parse_passages_prosodic import (TextModel, content_sylls, windows, meter_rows,  # noqa: E402
                                     INSTRUMENT, OUT_DIR, Appender, _init_worker, scramble)
import pandas as pd  # noqa: E402

GENFORM = os.environ.get("GENFORM_DATA", os.path.expanduser(
    "~/github/generative-formalism/data/data_as_in_paper"))
OUT = os.path.join(OUT_DIR, "by_window_verse.csv")
SEED = 20260924
#: base -> instruct, as named in genai_rhyme_completions
PAIRS = {"ollama/llama3.1:8b-text-q4_K_M": "ollama/llama3.1:8b",
         "ollama/mistral:text": "ollama/mistral"}
#: the other completion models (--tiers): the API tier, and one open instruct model
#: with no base partner in the data. Each carries its own poets' baseline: the
#: line_real of exactly the poems and lines it continued.
TIERS = {"claude-3-sonnet-20240229": "api", "gpt-3.5-turbo": "api",
         "deepseek/deepseek-chat": "api", "ollama/olmo2:latest": "open_aligned"}


def tier_poems():
    """-> recs for every poem each TIERS model completed, plus its poets' continuation."""
    c = pd.read_csv(os.path.join(GENFORM, "genai_rhyme_completions.csv.gz"), low_memory=False)
    c = c[c.line_gen.notna() & c.model.isin(list(TIERS))]
    out = []
    for (m, pid), g in c.groupby(["model", "id_human"]):
        g = g.sort_values(["stanza_num", "line_num"])
        out.append(dict(source="genai_completion", model=m, arm=TIERS[m], poem_id=pid, group=m,
                        text="\n".join(g.line_gen.astype(str))))
        out.append(dict(source="genai_completion", model="human:" + m, arm="human", poem_id=pid, group=m,
                        text="\n".join(g.line_real.fillna("").astype(str))))
    random.Random(SEED).shuffle(out)
    return out


def prompted_all():
    """-> recs for EVERY prompted poem (--prompted-all fills in what the per-cell sample left out).
    group = prompt_type (DO_rhyme / MAYBE_rhyme / do_NOT_rhyme); the prompt text itself is
    joined back from genai_rhyme_promptings by poem_id at analysis time."""
    p = pd.read_csv(os.path.join(GENFORM, "genai_rhyme_promptings.csv.gz"), low_memory=False)
    out = [dict(source="genai_prompt", model=r.model, arm="instruct", poem_id=str(r.id), group=r.prompt_type,
                text=str(r.txt)) for r in p.itertuples()]
    random.Random(SEED).shuffle(out)
    return out


def poems(per_period, per_cell):
    """-> list of dicts: source, model, arm, poem_id, group, text."""
    rng = random.Random(SEED)
    out = []
    h = pd.read_csv(os.path.join(GENFORM, "corpus_sample_by_period.csv.gz"), low_memory=False)
    for per, g in h.groupby("period"):
        for _, r in g.sample(min(per_period, len(g)), random_state=SEED).iterrows():
            out.append(dict(source="human_period", model="human", arm="human",
                            poem_id=str(r.id), group=str(per), text=str(r.txt)))
    p = pd.read_csv(os.path.join(GENFORM, "genai_rhyme_promptings.csv.gz"), low_memory=False)
    for (m, pt), g in p.groupby(["model", "prompt_type"]):
        for _, r in g.sample(min(per_cell, len(g)), random_state=SEED).iterrows():
            out.append(dict(source="genai_prompt", model=m, arm="instruct",
                            poem_id=str(r.id), group=pt, text=str(r.txt)))
    c = pd.read_csv(os.path.join(GENFORM, "genai_rhyme_completions.csv.gz"), low_memory=False)
    c = c[c.line_gen.notna()]
    for base, inst in PAIRS.items():
        shared = set(c[c.model == base].id_human) & set(c[c.model == inst].id_human)
        for m, arm in ((base, "base"), (inst, "instruct")):
            for pid, g in c[(c.model == m) & c.id_human.isin(shared)].groupby("id_human"):
                g = g.sort_values(["stanza_num", "line_num"])
                out.append(dict(source="genai_completion", model=m, arm=arm, poem_id=pid,
                                group=base, text="\n".join(g.line_gen.astype(str))))
                if arm == "base":                           # the human's own continuation, once per pair
                    out.append(dict(source="genai_completion", model="human:" + base, arm="human",
                                    poem_id=pid, group=base,
                                    text="\n".join(g.line_real.fillna("").astype(str))))
    rng.shuffle(out)
    return out


def work(rec):
    base = {k: rec[k] for k in ("source", "model", "arm", "poem_id", "group")}
    base["instrument"] = INSTRUMENT
    try:
        c = content_sylls(TextModel(rec["text"])._syll_df)
        return [dict(base, win_idx=i, **r) for i, r in enumerate(meter_rows(windows(c)))]
    except Exception as e:
        return [dict(base, win_idx=-1, error="%s: %s" % (type(e).__name__, str(e)[:200]))]


def work_scramble(rec):
    """The two scrambles of one text, as in the prose producer: content words permuted
    within UPOS (`shuffle_pos`, the antimetricality small data's R) and across the text
    (`shuffle_all`, its S), punctuation fixed, seeded by the text's key. The original is
    already in the file as version-less rows (read as `orig`)."""
    base = {k: rec[k] for k in ("source", "model", "arm", "poem_id", "group")}
    base["instrument"] = INSTRUMENT
    out = []
    try:
        df = TextModel(rec["text"], keep_parse=True)._syll_df
    except Exception as e:
        return [dict(base, version=v, win_idx=-1, error="%s: %s" % (type(e).__name__, str(e)[:200]))
                for v in ("shuffle_pos", "shuffle_all")]
    for v in ("shuffle_pos", "shuffle_all"):
        seed = int(hashlib.md5(("%s|%s|%s" % (rec["model"], rec["poem_id"], v)).encode()).hexdigest()[:8], 16)
        try:
            c = content_sylls(TextModel(scramble(df, v, seed))._syll_df)
            out += [dict(base, version=v, win_idx=i, **r) for i, r in enumerate(meter_rows(windows(c)))]
        except Exception as e:
            out.append(dict(base, version=v, win_idx=-1, error="%s: %s" % (type(e).__name__, str(e)[:200])))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--per-period", type=int, default=250, help="human poems per 50-year period")
    ap.add_argument("--per-cell", type=int, default=150, help="prompted poems per (model, prompt_type)")
    ap.add_argument("--tiers", action="store_true",
                    help="APPEND the API-tier and unpaired open-instruct completions (and their poets' "
                         "continuations) to the existing file, skipping any already there")
    ap.add_argument("--scramble", action="store_true",
                    help="APPEND within-POS and full scrambles of every continuation (all tiers and "
                         "the poets') and every prompted poem, skipping any already there")
    ap.add_argument("--prompted-all", action="store_true",
                    help="APPEND every prompted poem not yet parsed (the default run samples --per-cell)")
    a = ap.parse_args(argv)
    if a.prompted_all:
        a.tiers = True                                   # same append-and-skip path as --tiers
        recs = prompted_all()
    elif a.scramble:
        recs = [r for r in poems(a.per_period, a.per_cell) + tier_poems() + prompted_all()
                if r["source"] in ("genai_completion", "genai_prompt")]
        seen, uniq = set(), []                           # a poets' text shared by two recs is scrambled once
        for r in recs:
            k = (r["model"], r["poem_id"])
            if k not in seen:
                seen.add(k); uniq.append(r)
        recs = uniq
    else:
        recs = tier_poems() if a.tiers else poems(a.per_period, a.per_cell)
    out = OUT
    if a.smoke:
        seen, pick = {}, []
        for r in recs:
            k = (r["source"], r["arm"])
            if seen.get(k, 0) < 3:
                seen[k] = seen.get(k, 0) + 1
                pick.append(r)
        recs = pick
        import tempfile
        out = os.path.join(tempfile.gettempdir(), "syntax_and_rhythm_smoke_by_window_verse.csv")
    if a.scramble and os.path.exists(out):
        cols = pd.read_csv(out, nrows=0).columns
        if "version" in cols:
            have = pd.read_csv(out, usecols=["model", "poem_id", "version"], low_memory=False)
            have = set(map(tuple, have[have.version.notna()][["model", "poem_id"]].drop_duplicates().values))
            recs = [r for r in recs if (r["model"], r["poem_id"]) not in have]
    elif a.tiers and os.path.exists(out):
        have = set(map(tuple, pd.read_csv(out, usecols=["source", "model", "poem_id"]).drop_duplicates().values))
        recs = [r for r in recs if (r["source"], r["model"], r["poem_id"]) not in have]
    elif not (a.scramble or a.tiers) and os.path.exists(out):
        os.remove(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("%d poems: %s" % (len(recs), pd.Series([(r["source"], r["arm"]) for r in recs]).value_counts().to_dict()),
          file=sys.stderr)
    app = Appender(out)
    if a.workers > 1:
        from multiprocessing import get_context
        pool = get_context("spawn").Pool(a.workers, initializer=_init_worker)
        results = pool.imap(work_scramble if a.scramble else work, recs, chunksize=4)
    else:
        _init_worker()
        pool, results = None, map(work_scramble if a.scramble else work, recs)
    try:
        for i, rows in enumerate(results, 1):
            app.write(rows)
            if i % 200 == 0 or i == len(recs):
                print("  %d / %d" % (i, len(recs)), file=sys.stderr, flush=True)
    finally:
        if pool is not None:
            pool.terminate()
    if a.smoke:
        w = pd.read_csv(out)
        print(w.groupby(["source", "arm"])[["num_parses", "num_viols_allparse_sum"]].agg(["mean", "size"]).round(3))


if __name__ == "__main__":
    main()
