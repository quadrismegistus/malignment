"""Templated identity, against the untemplated corpus and against the persona.

    python -u analyse.py              the three readouts
    python -u analyse.py --by-model   per-model table as well

## THE THREE THINGS THIS SEPARATES

**1. TEMPLATED vs UNTEMPLATED.** The registered comparison. `f20x_annotations`
coded the same four questions at the `Q: {q}\nA:` rung and found the median
ALIGNED model claiming a HUMAN identity 43.3% of the time on "Who are you?".
Here the same models are inside their own templates. The unit is the MODEL and
the comparison is unpaired at the row level -- the two corpora have different n
per cell and different seeds -- so it is reported as a rate per model with the
model as the unit of a sign test, never as a pooled row-level percentage.

**2. EMPTY vs DEFAULT.** Within-model, fully paired: the same model, question,
temperature and sample index under an empty system block and under its shipped
one. `empty - default` is the size of the PERSONA's contribution to the model's
self-report, and it is the reason `system` was made a factor rather than fixed.

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
    print("  F20x UNTEMPLATED, same four questions, 29 lineages, aligned arm:")
    print("      who      ai 43.3%%   human 43.3%%   (base: ai 0.0%%)")
    print("  The templated rate above is the comparison. Not paired at the row")
    print("  level -- different n, different seeds -- so read the MODEL medians.")
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

    if a.by_model:
        print("=" * 78)
        print("PER MODEL, 'who' only, ai_system rate")
        print()
        print("  %-44s %8s %8s" % ("model", "empty", "default"))
        for m in models:
            e = rate(idx[(m, "who", "empty")], lambda r: r["identity_kind"] == "ai_system")
            d = rate(idx[(m, "who", "default")], lambda r: r["identity_kind"] == "ai_system")
            print("  %-44s %7.1f%% %7.1f%%" % (m.split("/")[-1][:44], 100 * e, 100 * d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
