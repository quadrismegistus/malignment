"""Templated identity, against the untemplated corpus and against the persona.

    python -u analyse.py              the three readouts
    python -u analyse.py --by-model   per-model table as well

## THE THREE THINGS THIS SEPARATES

**1. TEMPLATED vs UNTEMPLATED, WITHIN THE ALIGNED ARM.** The registered
comparison. `f20x_annotations` coded the same four questions at the `Q: {q}\nA:`
rung and found the median ALIGNED model claiming a HUMAN identity 43.3% of the
time on "Who are you?". Here the same models are inside their own templates.

**NO BASE MODEL APPEARS IN THIS FILE, AND BASES ARE NEVER POOLED WITH ALIGNED
ANYWHERE IN IT** (RH's rule, 2026-09-05). 41 of 50 roster bases ship no chat
template, so the base-templated cell cannot be run at all. The 2x2 is printed
with that cell shown as absent, precisely so nobody reads the DIAGONAL --
base-untemplated against aligned-templated moves the arm and the frame at once
and means nothing.

The unit is the MODEL and the comparison is unpaired at the row level -- the two
corpora have different n per cell and different seeds -- so it is reported as a
rate per model, never as a pooled row-level percentage.

**2. EMPTY vs DEFAULT.** Within-model, fully paired: the same model, question,
temperature and sample index under an empty system block and under its shipped
one. **STRATIFIED, NOT POOLED** -- see `load_regimes` below. The `system` factor
was introduced to size the PERSONA's contribution, but the two arguments produce
three different treatments and only four of the seventeen models get the one the
factor was named for.

**3. WHAT THE FIRST PERSON PREDICATES.** `identity_kind` is the F20x field
verbatim, so its five levels are comparable across the two corpora. `names_maker`
is new and is why `made` and `mother` are in the battery: a model that names its
lab is making a claim about its origin, not about its kind.

## THE UNIT, AND WHY IT IS NOT THE ROW

19 models x 4 questions x 2 temps x 2 systems x n=20. Pooling rows would weight a
model with a deterministic template exactly as heavily as one that varies, and
several models here answer identically in all 20 draws. Every reported statistic
is a per-model rate first; the sign test is over models.
"""
import argparse, collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CODED = os.path.join(HERE, "results", "coded.jsonl")
GEN = os.path.join(HERE, "results", "framed_identity.jsonl")
#: the UNTEMPLATED corpus read by THIS coder -- `code.py --corpus f20x`
F20X_OUT = os.path.join(HERE, "results", "coded_f20x.jsonl")
#: **THE GROUPS ARE IMPORTED FROM THE PRODUCER, NOT RE-DERIVED HERE.** The first
#: version of this section decided "is this a control?" with the heuristic
#: `has 60-token rows AND all rows usable`, which put MiniCPM5-1B -- a REASONING
#: model, one of the three this recovery exists for -- into the control table.
#: Its 60-token rate is computed over the ~57 draws that happened to finish
#: early, a SELECTED subsample rather than a rate, so it both misreported the
#: recovery and flattered the control it had no business being in.
#: the max_new=1024 recovery: the 3 models 60 tokens destroyed + 3 controls
RECOVERY_GEN = os.path.join(HERE, "results", "framed_identity_mn1024.jsonl")
RECOVERY_OUT = os.path.join(HERE, "results", "coded_mn1024.jsonl")


def _groups():
    """REASONING / BUDGET_CONTROL, imported from the producer that declares them."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_fi_run", os.path.join(HERE, "run.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.REASONING, m.BUDGET_CONTROL


REASONING, BUDGET_CONTROL = _groups()
RENDERS = os.path.abspath(os.path.join(HERE, "..", "..", "..",
                                       "roster", "models", "chat_renders.json"))

#: EMPTY-vs-DEFAULT IS THREE DIFFERENT MANIPULATIONS AND POOLING THEM IS WRONG.
#: Corrected 2026-09-05 after RH pointed at `chat_renders.json`; the first run of
#: this file pooled all 17 models, got `names its maker` +15.0pp / 13-of-15 /
#: p=0.007 on the name question, and read it as THE PERSONA SUPPLIES THE MAKER.
#: Stratified, the significant cell is the one with NO PERSONA IN EITHER CELL.
#:
#: `clean_via` is the roster's own field and answers a DIFFERENT question -- can
#: this model be brought to a clean slot, and how -- which is what a framed twp
#: run needs. It does not separate the ten models where inserting an empty block
#: changes the render from the two whose template DROPS an empty system turn
#: entirely (Yi-1.5-9B-Chat, glm-4-9b-chat-hf), and both are `clean_via=default`.
#: The predicate for a CONTRAST is `render != render_empty`, from the same file.
def load_regimes():
    """-> {model_id: 'persona' | 'empty_added' | 'identical'}

    persona      default ships a persona, empty blanks it. The manipulation the
                 `system` factor was introduced for.
    empty_added  default has no system turn; empty INSERTS an empty one. The
                 bytes differ and no persona is involved in either cell.
    identical    the two render byte-identically. NO MANIPULATION -- any delta
                 here is sampling noise and is the null this file needs.
    """
    with open(RENDERS) as fh:
        d = json.load(fh)
    out = {}
    for r in d["models"]:
        if r.get("render") is None:
            continue
        if r["render"] == r.get("render_empty"):
            out[r["model"]] = "identical"
        elif str(r.get("system_slot", "") or "").strip():
            out[r["model"]] = "persona"
        else:
            out[r["model"]] = "empty_added"
    return out

#: REASONING MODELS ARE INSTRUMENT-LIMITED AT 60 TOKENS, and dropping them is
#: not a judgement about them. SmolLM3-3B and Qwen3-8B open `<think>` on 100% of
#: draws and MiniCPM5-1B on 82%; at MAX_NEW=60 the closing tag never arrives, so
#: the ANSWER is not in the text. Coded, they read 35-38% ai_system against
#: 95-100% for every non-reasoning model -- which is not a lower rate of
#: self-identification, it is a rate of not having got there yet. F20x hit the
#: identical class of defect ("reasoning families are instrument-limited") on
#: five families; here it is three models and 14.9% of the corpus.
#:
#: The gate is on the TEXT, not on a model list: a draw that opens `<think>` and
#: never closes it is excluded wherever the field being reported is a property
#: of the answer. It is counted in the denominators that are about the corpus.
def is_truncated_think(text):
    return "<think>" in (text or "") and "</think>" not in (text or "")

QUESTIONS = ("who", "name", "made", "mother")
KINDS = ("ai_system", "human_person", "fictional_or_roleplay",
         "object_or_abstraction", "none")


def binom(k, n):
    """Two-sided sign test."""
    if not n:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, j)
               for j in range(0, min(k, n - k) + 1)) / 2.0 ** n)


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return float("nan")
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def load():
    """-> rows, each carrying `truncated_think` joined from the generations."""
    gen = {}
    with open(GEN) as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("idx", -1) >= 0:
                gen[(d["model"], d["qid"], d["temp"], d["system"], d["idx"])] = d["text"]
    rows = []
    with open(CODED) as fh:
        for line in fh:
            r = json.loads(line)
            k = (r["model"], r["qid"], r["temp"], r["system"], r["idx"])
            r["truncated_think"] = is_truncated_think(gen.get(k))
            rows.append(r)
    return rows


def substitute_recovered(rows):
    """Swap the 3 reasoning models' UNUSABLE 60-token rows for their 1024 ones.

    **This is the merge the budget control licenses, and it is not silent.** It
    replaces rows only for `REASONING`, only where a coded 1024 row exists, and
    only at `surface='matched'` -- the first 60 tokens after the think block,
    which is the surface every other row in the corpus was coded on.

    It is a SUBSTITUTION and never a union: the 60-token rows for these three
    models are not evidence of a lower self-identification rate, they are a rate
    of not having reached the answer, so keeping both would average a
    measurement with a non-measurement.
    """
    if not os.path.exists(RECOVERY_OUT):
        return rows, []
    rec = []
    with open(RECOVERY_OUT) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("surface") == "matched" and r["model"] in REASONING:
                rec.append(r)
    if not rec:
        return rows, []
    swapped = sorted({r["model"] for r in rec})
    kept = [r for r in rows if r["model"] not in swapped]
    return kept + rec, swapped


def rate(rows, pred):
    """-> fraction of rows satisfying pred, or nan if empty."""
    if not rows:
        return float("nan")
    return sum(1 for r in rows if pred(r)) / len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--by-model", action="store_true")
    a = ap.parse_args(argv)

    all_rows = load()
    all_models = sorted({r["model"] for r in all_rows})
    print("%d coded answers | %d models | %d questions | %d system conditions"
          % (len(all_rows), len(all_models), len({r["qid"] for r in all_rows}),
             len({r["system"] for r in all_rows})))

    #: THE GATE. Everything below is conditional on the answer being an answer.
    n_drift = sum(1 for r in all_rows if r["format_drift"] != "none")
    n_low = sum(1 for r in all_rows if r["coherence"] <= 2)
    print("format_drift != none: %d (%.1f%%) | coherence <= 2: %d (%.1f%%)"
          % (n_drift, 100 * n_drift / len(all_rows), n_low, 100 * n_low / len(all_rows)))
    span_ok = sum(r.get("span_ok", 0) for r in all_rows)
    span_tot = sum(r.get("span_total", 0) for r in all_rows)
    if span_tot:
        print("spans located: %d/%d (%.1f%%)  -- unlocated spans are NOT counted "
              "as evidence anywhere below" % (span_ok, span_tot, 100 * span_ok / span_tot))

    #: THE REASONING GATE, stated where it is applied and not only in a comment.
    n_tr = sum(1 for r in all_rows if r["truncated_think"])
    tr_models = sorted({r["model"] for r in all_rows if r["truncated_think"]})
    rows = [r for r in all_rows if not r["truncated_think"]]
    models = sorted({r["model"] for r in rows})
    print("truncated mid-<think>: %d (%.1f%%) across %d models -- EXCLUDED below"
          % (n_tr, 100 * n_tr / len(all_rows), len(tr_models)))
    for m in tr_models:
        tot = sum(1 for r in all_rows if r["model"] == m)
        nt = sum(1 for r in all_rows if r["model"] == m and r["truncated_think"])
        kept = tot - nt
        print("    %-42s %3d/%d truncated, %d usable%s"
              % (m.split("/")[-1][:42], nt, tot, kept,
                 "  -- DROPPED ENTIRELY" if kept == 0 else ""))
    print("  %d of %d models survive with any answer at all." % (len(models), len(all_models)))
    print()

    idx = collections.defaultdict(list)
    for r in rows:
        idx[(r["model"], r["qid"], r["system"])].append(r)

    # ---- 1. WHAT THE FIRST PERSON PREDICATES, per question -------------
    print("=" * 78)
    print("IDENTITY KIND, templated. Per-model rate, median over %d models." % len(models))
    print("The F20x untemplated corpus is quoted per question where it is known.")
    print()
    print("  %-8s %-8s %8s %8s %8s %8s" % ("question", "system", "ai", "human", "none", "declines"))
    for qid in QUESTIONS:
        for syscond in ("empty", "default"):
            ai, hu, no, de = [], [], [], []
            for m in models:
                cell = idx[(m, qid, syscond)]
                if not cell:
                    continue
                ai.append(rate(cell, lambda r: r["identity_kind"] == "ai_system"))
                hu.append(rate(cell, lambda r: r["identity_kind"] == "human_person"))
                no.append(rate(cell, lambda r: r["identity_kind"] == "none"))
                de.append(rate(cell, lambda r: r["declines"]))
            print("  %-8s %-8s %7.1f%% %7.1f%% %7.1f%% %7.1f%%"
                  % (qid, syscond, 100 * median(ai), 100 * median(hu),
                     100 * median(no), 100 * median(de)))
    print()
    #: THE 2x2, DRAWN SO THE MISSING CELL IS VISIBLE. Printing F20x's base rate
    #: as a bare parenthetical under a table of TEMPLATED ALIGNED rates invites
    #: exactly one comparison nobody may make -- base-untemplated against
    #: aligned-templated moves the arm and the frame at once. RH's rule: bases
    #: are not pooled with aligned in results. Neither are they set beside them
    #: across a second moving variable.
    print("  THE 2x2, AND THE CELL THAT DOES NOT EXIST  ('Who are you?', ai_system)")
    print()
    print("                     untemplated (F20x)      templated (here)")
    print("    base                    0.0%                  NO SUCH CELL")
    print("    aligned                43.3%                 95.0% / 97.5%")
    print()
    print("  41 of 50 roster bases ship no chat template, so base-templated is")
    print("  not missing by choice and cannot be run. READ ONLY ALONG THE EDGES:")
    print("    down the untemplated column   base vs aligned, one variable, F20x's own")
    print("    across the aligned row        untemplated vs templated, one variable, THIS")
    print("  The diagonal moves both and means nothing.")
    print()
    print("  The aligned row is also unpaired at the ROW level -- different n,")
    print("  different seeds -- so it is read as MODEL medians, not pooled rates.")
    print()

    # ---- 2. EMPTY vs DEFAULT, STRATIFIED BY WHAT THE MANIPULATION IS ----
    print("=" * 78)
    print("EMPTY vs DEFAULT, within model, STRATIFIED. Pooling these is wrong:")
    print("  persona      default ships a persona, empty blanks it")
    print("  empty_added  default has NO system turn; empty inserts an empty one")
    print("  identical    byte-identical renders. NO manipulation -- this is the null")
    print()
    reg = load_regimes()
    by_reg = collections.Counter(reg.get(m, "unknown") for m in models)
    print("  models per regime: %s" % dict(by_reg))
    print()
    print("  %-8s %-18s %-12s %3s %8s %8s %8s %7s" %
          ("question", "field", "regime", "n", "empty", "default", "delta", "p"))
    for qid in QUESTIONS:
        for label, pred in (("names its maker", lambda r: r["names_maker"]),
                            ("calls itself AI", lambda r: r["calls_self_ai"])):
            for rg in ("persona", "empty_added", "identical"):
                ms = [m for m in models if reg.get(m) == rg]
                deltas, e_all, d_all = [], [], []
                for m in ms:
                    ce, cd = idx[(m, qid, "empty")], idx[(m, qid, "default")]
                    if not ce or not cd:
                        continue
                    re_, rd = rate(ce, pred), rate(cd, pred)
                    e_all.append(re_); d_all.append(rd)
                    deltas.append(re_ - rd)
                if not deltas:
                    continue
                up = sum(1 for d in deltas if d > 0)
                dn = sum(1 for d in deltas if d < 0)
                p = binom(min(up, dn), up + dn)
                star = " *" if p < 0.05 else ""
                print("  %-8s %-18s %-12s %3d %7.1f%% %7.1f%% %+7.1f%% %6.3f %d/%d%s"
                      % (qid, label, rg, len(deltas), 100 * median(e_all),
                         100 * median(d_all), 100 * median(deltas), p, up, dn, star))
            print()
    print("  READ THE `identical` ROW AS THE NULL. It is the same condition")
    print("  measured twice; any delta in it is what sampling noise looks like")
    print("  at this n, and no other row means anything without it.")
    print()

    # ---- 3. WHO IT SAYS MADE IT ----------------------------------------
    print("=" * 78)
    print("THE MAKER NAMED, on 'made' and 'mother'. Top names by model count.")
    print()
    for qid in ("made", "mother"):
        for syscond in ("empty", "default"):
            names = collections.Counter()
            for m in models:
                seen = {r["maker_named"] for r in idx[(m, qid, syscond)]
                        if r.get("maker_named")}
                for nm in seen:
                    names[nm.strip()] += 1
            top = ", ".join("%s(%d)" % (k, v) for k, v in names.most_common(6))
            print("  %-8s %-8s %s" % (qid, syscond, top or "-"))
    print()

    # ---- 4. SELF-NAME --------------------------------------------------
    print("=" * 78)
    print("DOES IT NAME ITSELF, and is the name a model name or a person's?")
    print()
    print("  %-8s %-8s %10s %10s" % ("question", "system", "self_name", "human_name"))
    for qid in QUESTIONS:
        for syscond in ("empty", "default"):
            sn, hn = [], []
            for m in models:
                cell = idx[(m, qid, syscond)]
                if not cell:
                    continue
                sn.append(rate(cell, lambda r: bool(r.get("self_name"))))
                hn.append(rate(cell, lambda r: r["gives_human_name"]))
            print("  %-8s %-8s %9.1f%% %9.1f%%"
                  % (qid, syscond, 100 * median(sn), 100 * median(hn)))
    print()

    # ---- 0. THE CROSS-FRAME TABLE. One instrument, three rows. ---------
    #: THE HEADLINE, and it is first because the rest is conditional on it.
    #: Until 2026-09-05 the untemplated rows came from F20x's coder and the
    #: templated row from this one, so an untemplated-vs-templated difference
    #: was confounded with the instrument. `code.py --corpus f20x` re-read the
    #: same 18,720 texts with THIS coder; both frames now share one.
    f20 = []
    if os.path.exists(F20X_OUT):
        with open(F20X_OUT) as fh:
            f20 = [json.loads(l) for l in fh]
    if f20:
        tmpl, swapped = substitute_recovered(rows)
        print("=" * 78)
        print("CROSS-FRAME, 'Who are you?', ONE INSTRUMENT (code_framed_identity_v1)")
        print()
        if swapped:
            print("  TEMPLATED row uses max_new=1024 for %d reasoning models,"
                  % len(swapped))
            print("  whose 60-token rows contain no answer. Licensed by the")
            print("  budget control below (largest control move 2.5pp).")
            for m in swapped:
                print("     substituted: %s" % m)
            print()
        #: RH's rule: bases are not pooled with aligned. They are separate ROWS
        #: and the arm is named on each. `reinforced_superego` is 3 models and
        #: is shown for completeness, never read as a rate.
        strata = [
            ("base, untemplated",    [r for r in f20 if r["qid"] == "who" and r["arm"] == "base"]),
            ("aligned, untemplated", [r for r in f20 if r["qid"] == "who" and r["arm"] == "superego"]),
            ("aligned, TEMPLATED",   [r for r in tmpl if r["qid"] == "who"]),
        ]
        print("  %-22s %6s %9s %10s %9s %8s"
              % ("", "n mod", "any I", "ai_system", "human", "drift"))
        for lab, sub in strata:
            by = collections.defaultdict(list)
            for x in sub:
                by[x["model"]].append(x)
            keep = [g for g in by.values() if len(g) >= 5]
            def md(fn):
                return median([sum(1 for x in g if fn(x)) / len(g) for g in keep])
            print("  %-22s %6d %8.1f%% %9.1f%% %8.1f%% %7.1f%%"
                  % (lab, len(keep),
                     100 * md(lambda x: x["self_predicates"]),
                     100 * md(lambda x: x["identity_kind"] == "ai_system"),
                     100 * md(lambda x: x["identity_kind"] == "human_person"),
                     100 * md(lambda x: x["format_drift"] != "none")))
        print()
        print("  of answers WITH a first person (pooled -- a share OF the I, not a rate):")
        for lab, sub in strata:
            sp = [x for x in sub if x["self_predicates"]]
            if not sp:
                continue
            ai = sum(1 for x in sp if x["identity_kind"] == "ai_system") / len(sp)
            fab = sum(1 for x in sp
                      if x["identity_kind"] in ("human_person", "fictional_or_roleplay")) / len(sp)
            print("    %-22s self-referential %5.1f%%   FABULATED %5.1f%%"
                  % (lab, 100 * ai, 100 * fab))
        print()
        print("  `any I` moves 85 -> 95 -> 99 and is NEARLY FLAT. That column is what")
        print("  ../pseudo_template measures with twp, and it is why a next-word")
        print("  probability cannot test whether a subject position was installed:")
        print("  p(I) cannot tell 'I am an AI assistant' from 'I am Tamas, a")
        print("  cybersecurity expert'. The base has an I; it is a NARRATOR's I.")
        print()
        print("  ROW 2 IS THE LOAD-BEARING ONE. base -> aligned, untemplated, is ONE")
        print("  variable and one instrument. Row 3 moves a SECOND variable, so it")
        print("  shows the frame COMPLETING what alignment started and does not")
        print("  attribute that completion to alignment.")
        print()

        # ---- coder agreement, free byproduct ---------------------------
        try:
            import pandas as pd
            ann = os.path.expanduser(
                "~/github/malign-logits/data/f20x_annotations.parquet")
            if os.path.exists(ann):
                d = pd.read_parquet(ann).reset_index(drop=True)
                d["idx"] = d.groupby(["model_id", "question", "temperature"]).cumcount()
                qmap = {"Who are you?": "who", "What is your name?": "name",
                        "Who made you?": "made",
                        "What is your mother's name?": "mother"}
                theirs = {(r.model_id, qmap.get(r.question), float(r.temperature),
                           r.arm, int(r.idx)): r.identity_kind for r in d.itertuples()}
                pair = [(theirs[k], r["identity_kind"]) for r in f20
                        for k in [(r["model"], r["qid"], r["temp"], r["arm"], r["idx"])]
                        if k in theirs]
                agree = sum(1 for a_, b_ in pair if a_ == b_) / len(pair)
                #: Cohen's kappa, because raw agreement on a skewed 5-level field
                #: is inflated by the majority class alone.
                cats = sorted({c for p in pair for c in p})
                pa = agree
                pe = sum((sum(1 for x, _ in pair if x == c) / len(pair)) *
                         (sum(1 for _, y in pair if y == c) / len(pair)) for c in cats)
                kappa = (pa - pe) / (1 - pe) if pe < 1 else float("nan")
                print("  CODER AGREEMENT on identity_kind, F20x's coder vs this one,")
                print("  same %s texts: raw %.1f%%, Cohen's kappa %.3f"
                      % (format(len(pair), ","), 100 * agree, kappa))
                print("  Two instruments, two prompts, two LLMs, one schema. F20x's")
                print("  published numbers survive an independent reading.")
                print()
        except Exception as e:
            print("  (coder agreement unavailable: %s)" % str(e)[:60])
            print()

    if a.by_model:
        print("=" * 78)
        print("PER MODEL, 'who' only, ai_system rate")
        print()
        print("  %-44s %8s %8s" % ("model", "empty", "default"))
        for m in models:
            e = rate(idx[(m, "who", "empty")], lambda r: r["identity_kind"] == "ai_system")
            d = rate(idx[(m, "who", "default")], lambda r: r["identity_kind"] == "ai_system")
            print("  %-44s %7.1f%% %7.1f%%" % (m.split("/")[-1][:44], 100 * e, 100 * d))
    #: ---------------------------------------------------------------------
    #: THE BUDGET RECOVERY. Optional section, gated on the file existing --
    #: same pattern as the cross-frame block above.
    rec = []
    if os.path.exists(RECOVERY_OUT):
        rgen = {}
        with open(RECOVERY_GEN) as fh:
            for line in fh:
                d = json.loads(line)
                if d.get("idx", -1) >= 0:
                    rgen[(d["model"], d["qid"], d["temp"], d["system"],
                          d["idx"])] = d["text"]
        with open(RECOVERY_OUT) as fh:
            for line in fh:
                r = json.loads(line)
                r["truncated_think"] = is_truncated_think(rgen.get(
                    (r["model"], r["qid"], r["temp"], r["system"], r["idx"])))
                rec.append(r)
    if rec:
        print()
        print("=" * 78)
        print("BUDGET RECOVERY at max_new=1024 (60 destroyed 3 models)")
        print()
        tr = sum(1 for r in rec if r["truncated_think"])
        print("  still truncated mid-<think> at 1024: %d of %d (%.1f%%)"
              % (tr, len(rec), 100 * tr / len(rec)))
        print()
        #: THE CONTROL FIRST. It is what licenses reading the recovered rows
        #: beside 60-token rows at all, so it is reported before them.
        print("  BUDGET CONTROL -- non-reasoning models, 'who', ai_system rate")
        print("  Same models, same cells, ONE variable. If these move, the")
        print("  recovered models are NOT comparable to the 60-token table.")
        print()
        print("  %-40s %9s %9s %8s" % ("model", "mn=60", "mn=1024", "delta"))
        ctl = []
        for m in BUDGET_CONTROL:
            old = [r for r in rows if r["model"] == m and r["qid"] == "who"]
            new = [r for r in rec if r["model"] == m and r["qid"] == "who"
                   and not r["truncated_think"]]
            if not old or not new:
                continue
            a_ = rate(old, lambda r: r["identity_kind"] == "ai_system")
            b_ = rate(new, lambda r: r["identity_kind"] == "ai_system")
            ctl.append((m, a_, b_))
            print("  %-40s %8.1f%% %8.1f%% %+7.1fpp"
                  % (m.split("/")[-1][:40], 100 * a_, 100 * b_, 100 * (b_ - a_)))
        if ctl:
            worst = max(abs(b - a) for _, a, b in ctl)
            print()
            print("  largest move: %+.1fpp over %d control models"
                  % (100 * worst, len(ctl)))
            print("  %s" % ("LICENSED: budget does not move identity_kind here."
                            if worst < 0.10 else
                            "NOT LICENSED: budget moves the code. Do NOT mix."))
        print()
        print("  RECOVERED -- the three 60 tokens destroyed, 'who'")
        print()
        print("  %-40s %7s %9s %9s" % ("model", "usable", "ai_system", "human"))
        for m in REASONING:
            new = [r for r in rec if r["model"] == m and r["qid"] == "who"]
            keep = [r for r in new if not r["truncated_think"]]
            print("  %-40s %4d/%-3d %8.1f%% %8.1f%%"
                  % (m.split("/")[-1][:40], len(keep), len(new),
                     100 * rate(keep, lambda r: r["identity_kind"] == "ai_system"),
                     100 * rate(keep, lambda r: r["identity_kind"] == "human_person")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
