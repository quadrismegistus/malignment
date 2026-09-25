"""Is the model arms' valence set by the prompts? Three checks on the abstraction project's vector norms
(concreteness, valence, arousal). (RH, 2026-09-25: "Every arm sits below every decade ... This just cannot be
true? Is it because of our prompts?")

    .venv/bin/python -u arc_prompt_check.py --national   no-demonym national stories, four conditions
    .venv/bin/python -u arc_prompt_check.py --stems      TEMPLATE_ARM by stem: the stem's own score and its
                                                         continuations' per arm
    .venv/bin/python -u arc_prompt_check.py --strip      the chat-asked arm with echoed stems removed
    -> $DATA/prompt_check_*.parquet (inputs) and *_scored.parquet (abstraction's scorer), ARC_PROMPT_CHECK.md

SCORER: abstraction's own `scripts/vad_score.py meta`, run in its venv on parquets written here (book-policy
stopwords and names removed; token mean over tokens with a value, per column). The same scorer produced the
TEMPLATE_ARM meta-text scores, so every number is on one scale; its output lands beside the input.

HISTORY for placement: arc_fig5_vector.py's decade curves (vad_scores_arc_fiction, bias-corrected).

NATIONAL STORIES (national_story/judged_stories_v2.jsonl: every no-demonym generation in the stash, judged by
story_segments_v1; RH: "make sure they're judged proper stories or are spliced down before story degeneration
begins" -- see splice(); conflict.sqlite holds only the annotated subset, so it is not the source): prompts "A Story\\n(1500
words)\\n\\nIt was a" continued (raw), the same in the aligned model's template with the reply prefilled
(prefill), and the chat instruction "Write a 1500 word potential story." (frame 'rettberg', the asked cell).
Endpoint lineages as ns_conc_int.py: base bare; the aligned endpoint raw, prefilled, asked; Qwen3-8B's prefill
cell dropped (reasoning traces). Each model-condition's stories concatenated into one meta-text, as the
TEMPLATE_ARM arms are. EXPLORATORY.
"""
import os, sqlite3, subprocess, sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "novel_arc")
ABS = os.path.expanduser("~/github/abslithists/abstraction")
ABS_PY = os.path.join(ABS, ".venv", "bin", "python")
NS_DB = os.path.join(REPO, "experiments", "passage_analysis", "national_story", "conflict.sqlite")
COLS = {"conc": "Abs-Conc.Median.median", "valence": "VAD-Valence.Warriner.median", "arousal": "VAD-Arousal.Warriner.median"}


def score(path):
    """Run abstraction's scorer on (id, text[, meta]) -> the *_scored.parquet it writes beside the input."""
    out = path.replace(".parquet", "_scored.parquet")
    if not os.path.exists(out):
        subprocess.run([ABS_PY, "scripts/vad_score.py", "meta", path], cwd=ABS, check=True)
    return pd.read_parquet(out)


def history():
    """arc_fig5_vector's corrected decade curves and their lowess, per measure."""
    sys.argv = [sys.argv[0], "v4", "meta", "sel12", "arms4"]
    import json
    import arc_history_arms as H
    SH = os.path.expanduser("~/malignment-data/interiority_norms")
    V = pd.read_parquet(os.path.join(SH, "vad_scores_arc_fiction.parquet"))
    T = H.concreteness_texts()[["_id", "year", "corpus"]].merge(V, on="_id")
    book = json.load(open(H.BIAS))["coefficients"]
    vad = json.load(open(os.path.join(SH, "vad_corpus_bias.json")))["estimates"]
    T = T[T.year.between(1600, 2009)]
    out = {}
    for k, c in COLS.items():
        coef = book if k == "conc" else vad[c]["coefficients"]
        d = T[["year"]].assign(v=T[c] - T.corpus.map(coef).fillna(0.0)).dropna()
        out[k] = H.smooth(H.decades(d.year, d.v))
    return out


def place(cv, v):
    lo, hi = cv[:, 1].min(), cv[:, 1].max()
    if v > hi:
        return "above all"
    if v < lo:
        return "below all"
    xs = [int(round(y0 + (v - v0) / (v1 - v0) * (y1 - y0))) for (y0, v0), (y1, v1) in zip(cv[:-1], cv[1:]) if (v0 - v) * (v1 - v) < 0]
    return ", ".join(map(str, xs))


def splice(r):
    """-> (text or None, how). The judge's (story_segments_v1) verdict decides: a text that does not open as a
    story is dropped; a pure story is kept whole; otherwise the text is cut where the first non-story segment
    begins, located by that segment's first words. An unlocatable break, or under 150 words left (the judge's
    own floor), drops the text."""
    t = r.get("text") or ""
    if not r.get("opens_as_story"):
        return None, "dropped: does not open as a story"
    if r.get("pure_story"):
        return t, "whole: pure story"
    segs = r.get("segments") or []
    k = next((i for i, g in enumerate(segs) if g.get("kind") != "story"), None)
    if k is None:
        return t, "whole: all segments story"
    fw = (segs[k].get("first_words") or "").strip()
    i = t.find(fw) if fw else -1
    if i <= 0:
        return None, "dropped: break not located"
    cut = t[:i]
    if len(cut.split()) < 150:
        return None, "dropped: under 150 words before the break"
    return cut, "spliced before a %s segment" % segs[k].get("kind")


def national():
    import json, collections
    from malignment import roster
    EPS = roster.endpoints()[0]
    J = os.path.expanduser("~/malignment-data/national_story/judged_stories_v2.jsonl")
    path = os.path.join(DATA, "prompt_check_national_judged_meta.parquet")
    how = collections.Counter()
    rows = []
    for line in open(J, encoding="utf-8"):
        r = json.loads(line)
        if r["demonym"] != "none":
            continue
        lin, arm, fr, m = r["lineage"], r["arm"], r["frame"], r["model"]
        ok = (arm == "base" and m == lin and fr == "raw") or \
             (arm == "aligned" and m == EPS.get(lin) and fr in ("raw", "prefill", "rettberg"))
        if not ok or (fr == "prefill" and m == "Qwen/Qwen3-8B"):
            continue
        cond = "base" if arm == "base" else "aligned_" + fr
        t, h = splice(r)
        how[(cond, h)] += 1
        if t:
            rows.append(dict(lineage=lin, model=m, cond=cond, text=t))
    S = pd.DataFrame(rows)
    if not os.path.exists(path):
        M = (S.groupby(["lineage", "model", "cond"])
             .agg(n_stories=("text", "size"), text=("text", lambda t: "\n\n".join(t))).reset_index())
        M["id"] = M.model + "|" + M.cond
        assert M.id.is_unique
        M.to_parquet(path, index=False)
    R = score(path)
    cv = history()
    conds = ["base", "aligned_raw", "aligned_prefill", "aligned_rettberg"]
    lab = {"base": "base, raw", "aligned_raw": "aligned, raw", "aligned_prefill": "aligned, chat, prefilled",
           "aligned_rettberg": "aligned, chat, asked"}
    L = ["## National stories, no demonym: judged proper stories (%d lineages)" % R.lineage.nunique(), "",
         "Source: every no-demonym generation in judged_stories_v2.jsonl (the whole stash, 150+ words, deduplicated; "
         "judge.collect), endpoint models, judged by story_segments_v1 and spliced by `splice()`. Each model-condition's "
         "stories as one meta-text, abstraction's scorer; median over lineages (lineages per cell in brackets).", "",
         "Kept / spliced / dropped per condition:", ""]
    for c in conds:
        L.append("- %s: " % lab[c] + "; ".join("%s %d" % (h, n) for (cc, h), n in sorted(how.items()) if cc == c))
    L += ["", "| measure | " + " | ".join(lab[c] for c in conds) + " |", "|---|" + "---|" * len(conds)]
    for k, c in COLS.items():
        cells = []
        for cd in conds:
            v = R[R.cond == cd][c]
            cells.append("%+.3f [%d] (%s)" % (v.median(), v.notna().sum(), place(cv[k], v.median())))
        L.append("| %s | %s |" % (k, " | ".join(cells)))
    L += ["", "History range (smoothed): " + "; ".join("%s %.3f to %.3f" % (k, cv[k][:, 1].min(), cv[k][:, 1].max()) for k in COLS)]
    #: lineage agreement: among lineages with BOTH the base cell and the aligned cell, how many move from base in
    #: the direction of the medians' difference; two-sided sign test (ties counted against)
    from scipy.stats import binomtest
    L += ["", "Lineage agreement with the median direction (lineages with both cells; sign-test p):", "",
          "| measure | " + " | ".join("base -> %s" % lab[c] for c in conds[1:]) + " |", "|---|" + "---|" * (len(conds) - 1)]
    for k, c in COLS.items():
        piv = R.pivot_table(index="lineage", columns="cond", values=c)
        cells = []
        for cd in conds[1:]:
            d = piv[["base", cd]].dropna()
            sgn = np.sign(R[R.cond == cd][c].median() - R[R.cond == "base"][c].median())
            n_ok = int((np.sign(d[cd] - d["base"]) == sgn).sum())
            cells.append("%s %d/%d (p %.3f)" % ("up" if sgn > 0 else "down", n_ok, len(d), binomtest(n_ok, len(d)).pvalue))
        L.append("| %s | %s |" % (k, " | ".join(cells)))
    #: RH: "lineage check with the _orth vectors too just to see" -- plain and orthogonalized side by side,
    #: dominance included; agreement only (no history placement: the orth columns have no bias coefficients)
    L += ["", "Plain vs orthogonalized (concreteness direction projected out per model run) VAD, same test:", "",
          "| column | base median | " + " | ".join("base -> %s" % lab[c] for c in conds[1:]) + " |", "|---|---|" + "---|" * (len(conds) - 1)]
    for d_ in ("Valence", "Arousal", "Dominance"):
        for o in ("", "_orth"):
            c = "VAD-%s.Warriner%s.median" % (d_, o)
            piv = R.pivot_table(index="lineage", columns="cond", values=c)
            cells = []
            for cd in conds[1:]:
                d = piv[["base", cd]].dropna()
                sgn = np.sign(R[R.cond == cd][c].median() - R[R.cond == "base"][c].median())
                n_ok = int((np.sign(d[cd] - d["base"]) == sgn).sum())
                cells.append("%s %+.3f, %d/%d (p %.3f)" % ("up" if sgn > 0 else "down", R[R.cond == cd][c].median() - R[R.cond == "base"][c].median(),
                                                         n_ok, len(d), binomtest(n_ok, len(d)).pvalue))
            L.append("| %s | %+.3f | %s |" % (c, R[R.cond == "base"][c].median(), " | ".join(cells)))
    return L


def ta_passages():
    """TEMPLATE_ARM's 30-lineage coherent-narrative passages (arc_history_arms v4 sel12 arms4) with stem and text."""
    TA = os.path.expanduser("~/malignment-data/template_arm/coding")
    P = pd.read_parquet(os.path.join(DATA, "arc_history_arm_passages_v4_sel12_arms4.parquet"))[["id", "model", "base", "arm"]]
    S = pd.concat([pd.read_parquet(os.path.join(TA, "selection.parquet")), pd.read_parquet(os.path.join(TA, "selection_2.parquet"))])
    P = P.merge(S[["id", "stem", "text"]], on="id", validate="1:1")
    assert len(P) == 15655 and P.base.nunique() == 30, (len(P), P.base.nunique())
    return P


ARM_LAB = {"base": "base", "raw": "aligned, raw", "prefill": "aligned, chat, prefilled", "continue": "aligned, chat, asked"}


def stems():
    """Per stem: the stem's own score, and its continuations per arm pooled over all models into one text."""
    from scipy.stats import spearmanr
    P = ta_passages()
    path = os.path.join(DATA, "prompt_check_stems.parquet")
    if not os.path.exists(path):
        G = P.groupby(["stem", "arm"]).agg(n=("id", "size"), text=("text", lambda t: "\n\n".join(x or "" for x in t))).reset_index()
        st_ = pd.DataFrame({"stem": P.stem.unique()}).assign(arm="stem", n=1, text=lambda d: d.stem)
        G = pd.concat([G, st_], ignore_index=True)
        G["id"] = G.arm + "|" + G.stem.map(lambda x: "%08x" % (hash(x) & 0xffffffff))
        assert G.id.is_unique
        G.to_parquet(path, index=False)
    R = score(path)
    cv = history()
    W = {k: R.pivot_table(index="stem", columns="arm", values=c) for k, c in COLS.items()}
    L = ["## By stem (TEMPLATE_ARM, %d stems; each stem-arm = its continuations over all 30 lineages as one text)" % len(W["valence"]), ""]
    L += ["| measure | stems' own median | " + " | ".join("%s: median over stems (share of stems above / below every decade)" % ARM_LAB[a] for a in ARM_LAB) + " |",
          "|---|---|" + "---|" * len(ARM_LAB)]
    for k in COLS:
        lo, hi = cv[k][:, 1].min(), cv[k][:, 1].max()
        cells = []
        for a in ARM_LAB:
            v = W[k][a].dropna()
            cells.append("%+.3f (%d%% / %d%%)" % (v.median(), round(100 * (v > hi).mean()), round(100 * (v < lo).mean())))
        L.append("| %s | %+.3f | %s |" % (k, W[k]["stem"].median(), " | ".join(cells)))
    L += ["", "Spearman over stems between the stem's own score and its continuations' (does the prompt set the level?):", ""]
    for k in COLS:
        L.append("- %s: " % k + ", ".join("%s %+.2f" % (ARM_LAB[a], spearmanr(W[k]["stem"], W[k][a], nan_policy="omit")[0]) for a in ARM_LAB))
    v = W["valence"]
    L += ["", "Valence, the 5 most negative and 5 most positive stems (stem score -> base / raw / prefill / asked continuations):", ""]
    for stem in list(v["stem"].nsmallest(5).index) + list(v["stem"].nlargest(5).index):
        L.append("- %+.2f -> %s: %s" % (v.loc[stem, "stem"], " / ".join("%+.2f" % v.loc[stem, a] for a in ARM_LAB), stem[:90].replace("\n", " ")))
    return L


def strip():
    """The chat-asked arm with echoed stems removed: a passage that repeats its stem (within its first 400
    characters) keeps only what follows the echo. Meta-texts per model, scored, against the unstripped scores."""
    P = ta_passages()
    C = P[P.arm == "continue"].copy()
    def cut(t, s):
        key = s.strip()[:40]
        i = (t or "").find(key)
        if 0 <= i <= 400:
            j = t.find(s.strip(), i)
            return t[j + len(s.strip()):] if j == i else t[i + len(key):]
        return t
    C["text2"] = [cut(t, s) for t, s in zip(C.text, C.stem)]
    n_cut = int((C.text2 != C.text).sum())
    path = os.path.join(DATA, "prompt_check_continue_stripped.parquet")
    if not os.path.exists(path):
        M = C.groupby(["base", "model"]).agg(text=("text2", lambda t: "\n\n".join(x or "" for x in t))).reset_index()
        M["id"] = M.model + "|continue_stripped"
        M.to_parquet(path, index=False)
    R = score(path)
    U = pd.read_parquet(os.path.expanduser("~/malignment-data/interiority_norms/fig5_meta_texts_arms4_scored.parquet"))
    U = U[U.arm == "continue"]
    cv = history()
    L = ["## The chat-asked arm with echoed stems removed (%d of %d passages carried an echo)" % (n_cut, len(C)), "",
         "| measure | asked, as scored | asked, echo removed | placement, echo removed |", "|---|---|---|---|"]
    for k, c in COLS.items():
        L.append("| %s | %+.3f | %+.3f | %s |" % (k, U[c].median(), R[c].median(), place(cv[k], R[c].median())))
    return L


def main():
    L = ["# Is it the prompts? Vector concreteness, valence, arousal (EXPLORATORY)", "",
         "Producer `arc_prompt_check.py` (method in its docstring).", ""]
    #: read once: history() rewrites sys.argv to import arc_history_arms in its v4 arms4 mode
    flags = set(sys.argv[1:])
    for flag, fn in (("--national", national), ("--stems", stems), ("--strip", strip)):
        if flag in flags:
            L += fn() + [""]
    out = os.path.join(HERE, "ARC_PROMPT_CHECK.md")
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
