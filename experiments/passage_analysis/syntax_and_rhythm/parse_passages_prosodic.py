"""Syntax, stress-grid rhythm and meter of base vs aligned passages, via prosodic.

    python parse_passages_prosodic.py --smoke          12 cells x 3 passages, to $TMPDIR
    python parse_passages_prosodic.py                  every passage, random order, resumable
    python parse_passages_prosodic.py --limit 500      stop after 500 NEW passages
    python parse_passages_prosodic.py --workers 6      parallel (one spaCy per worker)
    python parse_passages_prosodic.py --restart        discard all outputs and start over

## THREE GRAINS, THREE FILES

    $MALIGNMENT_DATA/syntax_and_rhythm/by_passage.csv   (id, version)       no text
    $MALIGNMENT_DATA/syntax_and_rhythm/by_sentence.csv  (id, version, sent_idx)
    $MALIGNMENT_DATA/syntax_and_rhythm/by_window.csv    (id, version, win_idx)   carries window text

`version` is `orig`, `shuffle_pos` or `shuffle_all` (see SCRAMBLES). Every row
carries `instrument`, so a file mixing definitions is visible.

## WHAT IS MEASURED

prosodic (github.com/quadrismegistus/prosodic) with `keep_parse=True`: a spaCy
dependency parse, and from it Liberman & Prince (1977) phrasal prominence
(Dozat's MetricalTree over the dependency projection; per-word RPPR grid stress
`gstress`, tree stress `tstress`) plus the raw parse (`dep`, `pos`, `head_num`,
`dep_depth`).

**Stress grid, per sentence** (H1). Syllable column heights follow prosodic's
own `analysis.grid.grid_data` rule: 1 every syllable, +1 lexically stressed
(primary or secondary), +1 primary, +1 phrasal (`gstress` >= 0.5, on the
word's primary syllable), +1 nuclear (`gstress` >= 0.999). Heights 1-3 are
LEXICAL, 4-5 PHRASAL. With S_j = the syllables of height >= j in order:

    clash at level k   adjacent members of S_(k-1) both of height >= k
                       (k=2: two adjacent stressed syllables; k=4: two phrasal
                       peaks with no primary stress between them)
    lapse at level k   adjacent members of S_(k-1) both of height exactly k-1
                       (k=2: two adjacent unstressed syllables)
    ibi2_cv            coefficient of variation of the intervals, in syllables,
                       between successive stressed syllables (beat regularity)

reported per level and as `clash_rate` = all clashes / syllables, `clash_lex_rate`
(levels 2-3 only, comparable across scrambles), `lapse2_rate`, `alt2` (share of
adjacent syllable pairs that alternate stressed/unstressed).

**Meter, per 10-syllable window** (H2). The antimetricality protocol (Heuser,
Kiparsky & Anttila, draft Aug 2026, s.4) so rows sit beside the human baseline
`data.2026.reparse.big_data.parquet` (468,066 lines, 1600-2015): canonical
syllables, windows cut at word boundaries holding EXACTLY 10 syllables, lowercase,
punctuation stripped, lineation ignored; the 2020 constraint set (w_peak,
w_stress, s_unstress, unres_across, unres_within), resolution s <= 2, w <= 2.
Windows here are NON-OVERLAPPING (the moving window advanced past each accepted
window), so a passage contributes each syllable at most once. Columns copy the
baseline's: num_parses (metrical UNCERTAINTY = viable scansions),
num_viols_allparse_sum (MTS, metrical tension sum), mviol_<c>_allparse_sum
(per-constraint tension), *_bestparse, num_monosylls.

**Syntax and phrase rhythm, per passage and sentence** (H3): sentence length,
dependency distance, head direction (`left_head` = share of dependents preceding
their head), tree depth, dependency-label rates per 100 words, punctuation-phrase
length in syllables (`phrase_sylls`, `phrase_cv`).

## SCRAMBLES

Each passage is also measured in two permuted versions (seed = its id), with
every punctuation token left in place, so sentence count and sentence lengths
in words are IDENTICAL to the original and length strata line up exactly:

    shuffle_pos   content words permuted within their UPOS class (the POS
                  sequence of the original is kept -- a syntactic frame refilled)
    shuffle_all   content words permuted across the passage

Only LEXICAL measures are computed on scrambles (grid levels 1-3, meter windows):
their phrasal parse would be of word salad. real - scramble isolates ARRANGEMENT
from WORD CHOICE: a base/aligned difference that survives in the scramble is a
lexical one. Follows the O/R/S (original/randomized/scrambled) design of the
antimetricality small data; which of R/S was the within-POS one is not recorded
there, so these are named for what they do.

## SUBSET

`--subset pure` (default) parses only passages the judge labelled
`overall == story` AND `pure_story` -- the registration's primary filter; 55% of
the population is drifting stories, essays or degenerate text, and parsing it
first would spend most of the run on rows the primary analysis drops.
`--subset all` parses the rest, for sensitivity analysis (b); it resumes, so
it adds only what is missing. Either way the order is the same seeded shuffle.

## ORDER, RESUMPTION, FAILURES

Passages run in a FIXED-SEED shuffle and are appended as they finish, so any
prefix of the output is a random sample of the population. A resumed run skips
ids already in by_passage.csv and first drops any sentence/window rows of ids
that never reached it (a crash mid-write). A failed passage is a row with
`error` set, never an absence.

## PROSODIC IS NOT A MALIGNMENT REQUIREMENT

Imported from `$PROSODIC_PATH` (default ~/github/prosodic) put FIRST on
sys.path, else from whatever is installed; if it, spaCy, or `keep_parse`
(prosodic PR #194) is missing, the script says how to fix it and exits. It runs
from `.venv-prosodic`, not the shared measurement `.venv` -- see the README.
"""

import argparse
import datetime
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore")

PROSODIC_PATH = os.environ.get("PROSODIC_PATH", os.path.expanduser("~/github/prosodic"))
if os.path.isdir(PROSODIC_PATH):
    sys.path.insert(0, PROSODIC_PATH)
try:
    import prosodic
    from prosodic.texts.texts import TextModel
except Exception as e:                                  # ImportError, or a missing dep inside it
    sys.exit(
        "parse_passages_prosodic: prosodic could not be imported (%s: %s).\n"
        "  prosodic is deliberately NOT in malignment's requirements. Either:\n"
        "    uv pip install -e %s     (local checkout, editable)\n"
        "    pip install prosodic     (PyPI release; needs keep_parse, i.e. >= PR #194)\n"
        "  or point PROSODIC_PATH at a checkout whose dependencies are installed here."
        % (type(e).__name__, e, PROSODIC_PATH))
try:
    import spacy
    spacy.load("en_core_web_sm")
except Exception as e:
    sys.exit("parse_passages_prosodic: prosodic imports but its syntax engine does not "
             "(%s: %s).\n  uv pip install spacy && python -m spacy download en_core_web_sm"
             % (type(e).__name__, e))
import inspect
if "keep_parse" not in inspect.signature(TextModel.__init__).parameters:
    sys.exit("parse_passages_prosodic: prosodic at %s predates keep_parse (PR #194); "
             "update it." % os.path.dirname(os.path.dirname(prosodic.__file__)))

import numpy as np
import pandas as pd

from malignment.paths import repo_root

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data"))
JUDGED = os.path.join(DATA, "national_story", "judged_stories_v2.jsonl")
OUT_DIR = os.path.join(DATA, "syntax_and_rhythm")
OUTS = {"passage": os.path.join(OUT_DIR, "by_passage.csv"),
        "sentence": os.path.join(OUT_DIR, "by_sentence.csv"),
        "window": os.path.join(OUT_DIR, "by_window.csv")}
POP = os.path.join(HERE, "population.json")
SEED = 20260924
#: bump when a feature's definition changes; rows carry it, so mixed files are visible
INSTRUMENT = "syntax_and_rhythm-v1"
#: the national_story prompt ends "It was a"; `text` is the continuation only
PROMPT_TAIL = "It was a"
#: the 2020 antimetricality constraint set and resolution (draft Aug 2026, s.3.1)
METER = dict(constraints=("w_peak", "w_stress", "s_unstress", "unres_across", "unres_within"),
             max_s=2, max_w=2)
VERSIONS = ("orig", "shuffle_pos", "shuffle_all")


# ------------------------------------------------------------------ population

NATIONAL_STORY = os.path.join(repo_root(), "experiments", "passage_analysis", "national_story")


def population(demonym=None):
    """-> DataFrame of passages to parse, and the receipt describing the rule.

    RULE: national_story's own population, imported not retyped --
    `analyse.load_raw(min_words=150, drop_escapes=True)` (raw frame, decoder
    max_new_tokens >= 1000 and top_p 0.95, deduplicated, assistant escapes and
    stubs dropped) restricted to `analyse._paired` lineages (both arms present).
    Judge labels (overall, pure_story, opens_as_story) are joined from
    judged_stories_v2.jsonl by id = md5(text)[:12] (judge.py's key) and CARRIED,
    not filtered on: the analysis chooses. The no-demonym control is demonym ''.
    """
    sys.path.insert(0, NATIONAL_STORY)
    import analyse
    from malignment import roster
    G = analyse.load_raw(min_words=150, drop_escapes=True)
    lins = set(analyse._paired(G))
    endpoint = roster.endpoints()[0]                     # {base: aligned endpoint}
    rows = []
    for (lin, arm, dem), texts in G.items():
        if lin not in lins:
            continue
        for t in texts:
            rows.append(dict(id=hashlib.md5(t.encode("utf-8")).hexdigest()[:12],
                             model=lin if arm == "base" else endpoint.get(lin, ""),
                             lineage=lin, arm=arm, frame="raw", demonym=dem or "",
                             text=t))
    d = pd.DataFrame(rows)
    n0 = len(d)
    j = pd.read_json(JUDGED, lines=True)[["id", "overall", "pure_story", "opens_as_story"]]
    d = d.merge(j.drop_duplicates("id"), on="id", how="left")
    excl = {}
    if demonym is not None:
        keep = d.demonym == ("" if demonym == "none" else demonym)
        excl["demonym != %s" % demonym] = int((~keep).sum())
        d = d[keep]
    receipt = {
        "source": "national_story/analyse.py load_raw(min_words=150, drop_escapes=True) + _paired; "
                  "judge labels from " + JUDGED,
        "rule": population.__doc__.split("RULE:")[1].strip(),
        "demonym": demonym,
        "n_load_raw_paired": n0,
        "n_unjudged": int(d.overall.isna().sum()),
        "excluded": excl,
        "n": len(d),
        "lineages": sorted(d.lineage.unique()),
        "n_by_lineage_arm": {"%s|%s" % k: int(v) for k, v in d.groupby(["lineage", "arm"]).size().items()},
        "ids": sorted(d.id),
    }
    return d, receipt


# --------------------------------------------------------------------- helpers

def clean(text):
    """Prepend the prompt tail, drop the truncated final sentence, flatten breaks."""
    t = PROMPT_TAIL + text
    ends = list(re.finditer(r'[.!?]["”’\']?(?=\s|$)', t))
    if ends:
        t = t[:ends[-1].end()]
    return re.sub(r"\s+", " ", t).strip()


def content_sylls(df):
    """Canonical, non-punctuation syllable rows in text order."""
    c = df[df.form_idx.isin([0, -1]) & ~df.is_punc.astype(bool)]
    return c.sort_values(["word_num", "syll_idx"])


def grid_heights(c, phrasal=True):
    """prosodic's grid_data height rule over _syll_df rows (see module docstring)."""
    ipa = c.syll_ipa.astype(str)
    primary = ipa.str.startswith("'").values
    h = 1 + c.is_stressed.astype(bool).values + primary
    if phrasal and "gstress" in c.columns:
        g = c.gstress.astype(float).fillna(-1).values
        h = h + (primary & (g >= 0.5)) + (primary & (g >= 0.999))
    return h.astype(int)


def grid_metrics(h, max_level):
    """Clash / lapse / alternation / beat spacing over one sentence's heights."""
    n = len(h)
    out = {"n_sylls": n}
    clashes = 0
    for k in range(2, max_level + 1):
        s = h[h >= k - 1]
        pairs = max(0, len(s) - 1)
        cl = int(np.sum((s[:-1] >= k) & (s[1:] >= k))) if pairs else 0
        la = int(np.sum((s[:-1] == k - 1) & (s[1:] == k - 1))) if pairs else 0
        out["clash%d" % k], out["lapse%d" % k] = cl, la
        clashes += cl
    out["clash_rate"] = clashes / n if n else np.nan
    out["clash_lex_rate"] = (out["clash2"] + out["clash3"]) / n if n else np.nan
    out["lapse2_rate"] = out["lapse2"] / (n - 1) if n > 1 else np.nan
    st = h >= 2
    out["alt2"] = float(np.mean(st[:-1] != st[1:])) if n > 1 else np.nan
    beats = np.flatnonzero(st)
    ibi = np.diff(beats)
    out["ibi2_mean"] = float(ibi.mean()) if len(ibi) else np.nan
    out["ibi2_cv"] = float(ibi.std() / ibi.mean()) if len(ibi) > 1 else np.nan
    return out


PUNCT_KEEP = re.compile(r"[^\w'’-]+")


def windows(c):
    """Non-overlapping 10-syllable word-boundary windows (antimetricality protocol)."""
    out, cur, n = [], [], 0
    for _, g in c.groupby("word_num", sort=True):
        w = PUNCT_KEEP.sub("", g.word_txt.iloc[0].strip().lower())
        cur.append(w)
        n += len(g)
        if n >= 10:
            if n == 10 and all(cur):
                out.append(" ".join(cur))
            cur, n = [], 0
    return out


#: pronunciation-pooling guard. prosodic pools every combination of word
#: pronunciations; a window like "is fair hon hon oh hon oh hon hon yes" ("hon" =
#: 1, 3 or 4 syllables, 5 times) is 486 combinations up to 25 syllables, and the
#: exact bounding step never returns. Such windows are recorded with `skipped`
#: set, not parsed. Deterministic (no timeout), so a rerun skips the same ones.
MAX_COMBOS = 64
MAX_VARIANT_SYLLS = 18                                  # prosodic's MAX_SYLL_IN_PARSE_UNIT


def _pooling_load(sd):
    """-> {line_num: (combos, longest variant in syllables)} from a _syll_df."""
    w = sd[~sd.is_punc.astype(bool)]
    per_form = w.groupby(["line_num", "word_num", "form_idx"]).size()
    per_word = per_form.groupby(level=[0, 1]).agg(["size", "max"])
    return {int(ln): (int(np.prod(g["size"].values, dtype=float)), int(g["max"].sum()))
            for ln, g in per_word.groupby(level=0)}


def meter_rows(lines):
    """Parse window lines with the 2020 meter -> one row per window, baseline columns."""
    if not lines:
        return []
    t = TextModel("\n".join(lines))
    sd = t._syll_df
    present = sorted(int(x) for x in sd.line_num.unique())
    if len(present) == len(lines):
        load = _pooling_load(sd)
        bad = {i for i, ln in enumerate(present)
               if load.get(ln, (1, 0))[0] > MAX_COMBOS or load.get(ln, (1, 0))[1] > MAX_VARIANT_SYLLS}
        if bad:
            ok = [l for i, l in enumerate(lines) if i not in bad]
            rows = {l: r for l, r in zip(ok, meter_rows(ok))} if ok else {}
            out = []
            for i, l in enumerate(lines):
                if i in bad:
                    c, m = load[present[i]]
                    out.append({"window": l, "skipped": "pooling: %d combos, longest %d sylls" % (c, m)})
                elif l in rows:
                    out.append(rows[l])
            return out
    t = TextModel("\n".join(lines))
    sd = t._syll_df
    present = sorted(int(x) for x in sd.line_num.unique())
    if len(present) != len(lines):                       # a window re-tokenized oddly
        return [r for l in lines for r in meter_rows_one(l)] if len(lines) > 1 else []
    pos = {ln: i for i, ln in enumerate(present)}
    canon = sd[(sd.form_idx == 0) & ~sd.is_punc.astype(bool)]
    mono = canon.groupby(["line_num", "word_num"]).size().eq(1).groupby("line_num").sum()
    pdf = t.get_parses_df(mode="unbounded", by="line", **METER)
    rows = [None] * len(lines)
    for ln, g in pdf.groupby("line_num"):
        best = g[g.is_best]
        best = best.iloc[0] if len(best) else g.sort_values("parse_score").iloc[0]
        r = {"window": lines[pos[int(ln)]], "num_sylls": int(best.num_sylls),
             "num_monosylls": int(mono.get(ln, 0)), "num_parses": int(len(g)),
             "meter": str(best.meter).translate(str.maketrans("+-", "sw")),
             "num_viols_bestparse": int(best.num_viols), "score_bestparse": float(best.parse_score),
             "num_viols_allparse_sum": int(g.num_viols.sum())}
        for cn in METER["constraints"]:
            col = "*" + cn
            r["mviol_%s_bestparse" % cn] = int(best[col]) if col in g else 0
            r["mviol_%s_allparse_sum" % cn] = int(g[col].sum()) if col in g else 0
        rows[pos[int(ln)]] = r
    return [r for r in rows if r is not None]


def meter_rows_one(line):
    return meter_rows([line]) if line else []


def scramble(df, mode, seed):
    """Permute content words (within UPOS for 'shuffle_pos'), punctuation fixed."""
    toks = df.drop_duplicates("word_num").sort_values("word_num")
    words = [w.strip() for w in toks.word_txt.astype(str)]
    isp = toks.is_punc.astype(bool).values
    pos = toks.pos.astype(str).values if "pos" in toks else np.array(["X"] * len(toks))
    rng = random.Random(seed)
    idx = [i for i in range(len(words)) if not isp[i]]
    groups = {}
    for i in idx:
        groups.setdefault(pos[i] if mode == "shuffle_pos" else "_", []).append(i)
    new = list(words)
    for members in groups.values():
        perm = members[:]
        rng.shuffle(perm)
        for dst, src in zip(members, perm):
            new[dst] = words[src]
    text = " ".join(new)
    return re.sub(r" ([,.;:!?’”)\]])", r"\1", text)


# -------------------------------------------------------------------- features

#: dependency labels whose rate per 100 content words is reported (spaCy/ClearNLP)
DEP_RATES = {
    "conj": ("conj", "cc"), "advcl": ("advcl",), "relcl": ("relcl", "acl"),
    "amod": ("amod",), "advmod": ("advmod",), "prep": ("prep",),
    "compound": ("compound",), "ccomp": ("ccomp", "xcomp"), "npadvmod": ("npadvmod",),
    "poss": ("poss",), "nsubjpass": ("nsubjpass", "auxpass"), "mark": ("mark",),
}


def syntax_of(w):
    """Syntax features over word rows (one sentence or a whole passage)."""
    rank = dict(zip(w.word_num, range(len(w))))
    hd = w[w.head_num >= 0]
    dist = (hd.word_num.map(rank) - hd.head_num.map(rank)).dropna()
    deps = w.dep.value_counts()
    out = {"dep_dist": dist.abs().mean(), "left_head": (dist < 0).mean(),
           "tree_depth": w.dep_depth.max()}
    for k, labels in DEP_RATES.items():
        out["dep_" + k] = sum(deps.get(l, 0) for l in labels) / len(w) * 100 if len(w) else np.nan
    return out


def measure(text, version, sent_of=None):
    """-> (passage_row, sentence_rows, window_rows, _syll_df) for one version.

    ``sent_of``: the ORIGINAL's sent_num per token position. A scramble keeps
    every token position (punctuation fixed), but prosodic re-segments the
    permuted text by capitalisation too, so its own sentences drift; when the
    token sequences line up one-to-one the original's sentences are imposed,
    making sentence lengths identical and length strata exact. Recorded as
    `sent_source` on each passage row."""
    orig = version == "orig"
    tm = TextModel(text, keep_parse=True) if orig else TextModel(text)
    df = tm._syll_df
    sent_source = "own"
    if sent_of is not None:
        wn = df.drop_duplicates("word_num").sort_values("word_num").word_num.tolist()
        if len(wn) == len(sent_of):
            df = df.assign(sent_num=df.word_num.map(dict(zip(wn, sent_of))))
            sent_source = "orig"
    c = content_sylls(df)
    h_all = grid_heights(c, phrasal=orig)
    c = c.assign(_h=h_all)
    toks = df.drop_duplicates("word_num").sort_values("word_num")
    w = toks[~toks.is_punc.astype(bool)]

    sents = []
    for si, (sn, g) in enumerate(c.groupby("sent_num", sort=True)):
        ws = w[w.sent_num == sn]
        r = {"sent_idx": si, "n_words": len(ws)}
        r.update(grid_metrics(g._h.values, 5 if orig else 3))
        if orig:
            r.update(syntax_of(ws))
            v = ws.tstress.astype(float).values
            r["nuc_pos"] = (float(np.nanargmax(v)) / (len(v) - 1)
                            if len(v) > 2 and not np.isnan(v).all() else np.nan)
        sents.append(r)
    S = pd.DataFrame(sents)
    wins = meter_rows(windows(c))
    W = pd.DataFrame(wins)

    phr = c.groupby("linepart_num").size()
    slen = S.n_words[S.n_words > 1] if len(S) else pd.Series(dtype=float)
    P = {"n_words": len(w), "n_sents": len(slen), "n_sylls": len(c),
         "sent_len": slen.mean(), "sent_len_cv": slen.std() / slen.mean() if len(slen) else np.nan,
         "phrase_sylls": phr.mean(), "phrase_cv": phr.std() / phr.mean(),
         "stress_density": float(np.mean(h_all >= 2)) if len(h_all) else np.nan,
         "n_windows": len(W), "sent_source": sent_source}
    for col in ("clash_rate", "clash_lex_rate", "lapse2_rate", "alt2", "ibi2_cv"):
        P[col] = S[col].mean() if len(S) else np.nan    # sentence-averaged
    if len(W):
        for col in ("num_parses", "num_viols_allparse_sum", "num_viols_bestparse", "num_monosylls",
                    "mviol_s_unstress_allparse_sum", "mviol_w_stress_allparse_sum"):
            P[col] = W[col].mean()
        P["imperfect"] = (W.num_viols_allparse_sum > 0).mean()
        P["imperfect_s_unstress"] = (W.mviol_s_unstress_allparse_sum > 0).mean()
    if orig:
        P.update(syntax_of(w))
        P["tree_depth"] = S.tree_depth.mean() if len(S) else np.nan
        P["commas_per_sent"] = (toks.word_txt.str.strip() == ",").sum() / max(1, len(slen))
        P["nuc_pos"] = S.nuc_pos.mean() if len(S) else np.nan
        P["gstress_hi"] = (w.gstress >= 0.5).mean()
        P["tstress_sd"] = w.tstress.std()
    return P, sents, wins, df


def work(rec):
    """One passage, all versions -> {grain: [rows]}. An error is a ROW with `error`
    set, not an absence: a passage that failed and one never attempted must differ."""
    key = {k: rec[k] for k in ("id", "model", "lineage", "arm", "frame", "demonym",
                               "overall", "pure_story", "opens_as_story")}
    out = {"passage": [], "sentence": [], "window": []}
    df_orig = sent_of = None
    for version in VERSIONS:
        base = dict(key, version=version, instrument=INSTRUMENT)
        try:
            if version == "orig":
                text = clean(rec["text"])
            else:
                if df_orig is None:
                    raise RuntimeError("original failed; no scramble")
                seed = int(hashlib.md5((rec["id"] + version).encode()).hexdigest()[:8], 16)
                text = scramble(df_orig, version, seed)
            P, sents, wins, df = measure(text, version, sent_of)
            if version == "orig":
                df_orig = df
                sent_of = df.drop_duplicates("word_num").sort_values("word_num").sent_num.tolist()
            out["passage"].append(dict(base, **P, error=""))
            out["sentence"] += [dict(base, **r) for r in sents]
            out["window"] += [dict(base, win_idx=i, **r) for i, r in enumerate(wins)]
        except Exception as e:
            out["passage"].append(dict(base, error="%s: %s" % (type(e).__name__, str(e)[:200])))
    return out


def _init_worker():
    warnings.filterwarnings("ignore")
    import logging
    logging.disable(logging.WARNING)


def prosodic_version():
    try:
        sha = subprocess.run(["git", "-C", PROSODIC_PATH, "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
    except Exception:
        sha = ""
    return {"version": getattr(prosodic, "__version__", ""), "path": prosodic.__file__, "git": sha}


# ------------------------------------------------------------------------ main

class Appender:
    """Append rows to a CSV, fixing the column order from the first row written."""

    def __init__(self, path):
        self.path, self.cols = path, None
        if os.path.exists(path) and os.path.getsize(path):
            self.cols = list(pd.read_csv(path, nrows=0).columns)

    def write(self, rows):
        if not rows:
            return
        d = pd.DataFrame(rows)
        header = self.cols is None
        if header:
            self.cols = list(d.columns)
        extra = [c for c in d.columns if c not in self.cols]
        if extra:                                   # e.g. an error-only passage row came first
            old = pd.read_csv(self.path)
            self.cols += extra
            old.reindex(columns=self.cols).to_csv(self.path, index=False)
        d.reindex(columns=self.cols).to_csv(self.path, mode="a", header=header, index=False)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N new passages")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--subset", choices=("pure", "all"), default="pure",
                    help="pure (default): only judge overall == story AND pure_story, the "
                         "registration's primary filter; all: every passage (sensitivity b)")
    ap.add_argument("--demonym", default=None,
                    help="restrict to one demonym ('none' = the no-demonym control)")
    ap.add_argument("--restart", action="store_true")
    a = ap.parse_args(argv)

    d, receipt = population(a.demonym)
    recs = d.to_dict("records")
    random.Random(SEED).shuffle(recs)                   # shuffle BEFORE subsetting: same order either way
    if a.subset == "pure":
        recs = [r for r in recs if r["overall"] == "story" and r["pure_story"] == True]
    receipt["parsed_subset"] = a.subset
    receipt["n_parsed_subset"] = len(recs)
    outs = dict(OUTS)
    if a.smoke:
        pick, seen = [], {}
        for r in recs:
            k = (r["lineage"], r["arm"])
            if (len(seen) < 12 or k in seen) and seen.get(k, 0) < 3:
                seen[k] = seen.get(k, 0) + 1
                pick.append(r)
        recs = pick
        import tempfile                                  # not results/: one file per grain there
        outs = {g: os.path.join(tempfile.gettempdir(), "syntax_and_rhythm_smoke_by_%s.csv" % g)
                for g in OUTS}
        a.restart = True
    else:
        receipt.update(date=datetime.date.today().isoformat(), seed=SEED, instrument=INSTRUMENT,
                       meter=METER, prosodic=prosodic_version(),
                       producer=os.path.relpath(os.path.abspath(__file__), repo_root()))
        with open(POP, "w") as f:
            json.dump(receipt, f, indent=1)

    for p in outs.values():
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if a.restart and os.path.exists(p):
            os.remove(p)
    done = (set(pd.read_csv(outs["passage"], usecols=["id"]).id)
            if os.path.exists(outs["passage"]) else set())
    for g in ("sentence", "window"):                    # drop rows of passages that never finished
        p = outs[g]
        if os.path.exists(p):
            x = pd.read_csv(p, low_memory=False)
            if (~x.id.isin(done)).any():
                x[x.id.isin(done)].to_csv(p, index=False)
    todo = [r for r in recs if r["id"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    print("population %d passages, %d lineages; %d done, %d to parse" %
          (receipt["n"], len(receipt["lineages"]), len(done), len(todo)), file=sys.stderr)

    app = {g: Appender(p) for g, p in outs.items()}
    if a.workers > 1:
        from multiprocessing import get_context
        pool = get_context("spawn").Pool(a.workers, initializer=_init_worker)
        results = pool.imap(work, todo, chunksize=2)     # imap keeps the shuffle order
    else:
        _init_worker()
        pool, results = None, map(work, todo)
    try:
        for i, res in enumerate(results, 1):
            app["sentence"].write(res["sentence"])
            app["window"].write(res["window"])
            app["passage"].write(res["passage"])         # last: its id marks the passage done
            if i % 25 == 0 or i == len(todo):
                print("  %d / %d" % (i, len(todo)), file=sys.stderr, flush=True)
    finally:
        if pool is not None:
            pool.terminate()

    if a.smoke:
        r = pd.read_csv(outs["passage"])
        print("errors: %d of %d rows" % ((r.error.fillna("") != "").sum(), len(r)))
        for g in ("sentence", "window"):
            print("%s rows: %d" % (g, len(pd.read_csv(outs[g]))))
        feats = [c for c in r.columns if r[c].dtype.kind == "f"]
        print(r.groupby(["version", "arm"])[feats].mean().T.round(3).to_string())


if __name__ == "__main__":
    main()
