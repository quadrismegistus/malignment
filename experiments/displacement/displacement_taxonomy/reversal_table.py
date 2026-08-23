"""One row per (rater, prompt, model): the relation named, and whether reversed.

    python reversal_table.py            # write the CSV, print the aggregates
    python reversal_table.py --csv PATH

## BLIND ONLY

Sighted and blind readings of one prompt are different populations -- blinding
changed rater agreement on every frame it was measured on -- so pooling them
would average an instrument change into a result. `version` carries the `b`
suffix for blind, and that is the filter.

## RATER IS A COLUMN, AND IT IS NOT OPTIONAL

Two raters read each prompt, so without it a model appears twice per prompt
with nothing to say why. It is also the only thing that makes the reversal
count readable: the same 50 tables gave one rater 13 reversals and another 5,
so a pooled rate with no rater term hides its own largest source of variance.

## THE DENOMINATOR IS PRINTED, NOT ASSUMED

`unassigned` models are carried as rows with no relation. A reversal rate over
placed+reversed answers "of the models the rater committed on, how many run it
backwards"; over all shown it answers something else. Both are printed because
neither is the obvious one.
"""
import argparse, collections, csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import operation_graph as OG


def domains():
    """`{prompt: domain}` from the SLOT CORPUS first, stage-1 codings second.

    Read the corpus that defines prompts, not the stash of an older experiment.
    Taking domains only from stage-1 returned None for every frame outside the
    ~40 it happened to annotate, which would have quietly labelled 262 of 302
    prompts as domain `None` the moment the instrument was unblocked.
    """
    import crosslineage as X
    import run as R
    out = {}
    st = R._stash()
    for k in st.keys():
        m = (st[k].get("meta") or {})
        if m.get("batch") and m.get("frame_prompt"):
            out[m["frame_prompt"]] = m.get("domain")
    #: The corpus WINS on conflict: it is current, and a stage-1 label is
    #: whatever that item's domain was when the older run went out.
    for d, p in X.slot_items():
        out[p] = d
    return out


def blind_prompts():
    """`{prompt: n_lineages}` for every prompt with a blind reading, at its largest roster."""
    import crosslineage as X
    best = {}
    for k in X._stash():
        if not isinstance(k, dict) or k.get("stage") != "crosslineage":
            continue
        #: `x1b` and `x1bn` are both blind; the second is blanks-stripped. Both
        #: are in scope here and `arm_for` picks between them downstream.
        if not str(k.get("version") or "").endswith(("b", "bn")):
            continue
        p, n = k["frame_prompt"], k.get("n_lineages") or 0
        best[p] = max(best.get(p, 0), n)
    return best


def rows():
    dom, out = domains(), []
    for prompt, n in sorted(blind_prompts().items()):
        pairs, _ = OG.readings(prompt, n)
        pairs = [(t, v) for t, v in pairs if t.split(".")[0].endswith("b")]
        SC = OG.sidecar(prompt) or {}

        def words(model, ws, side):
            #: Rank-ordered on the cited side, printed base->aligned, matching the
            #: table the rater read. Alphabetical order would put a rank-3 word
            #: carrying 7% beside a rank-60 word carrying 0.02%.
            rk = (SC.get(model) or {})
            key = "rank_a" if side == "a" else "rank_b"
            xs = []
            for w in [x.lower() for x in ws or []]:
                r = rk.get(w) or rk.get(w.capitalize()) or {}
                xs.append((r.get(key), w, r.get("rank_a"), r.get("rank_b")))
            xs.sort(key=lambda x: (x[0] is None, x[0] or 0))
            return "; ".join("%s (%s->%s)" % (w, a if a is not None else "-",
                                              b if b is not None else "-")
                             for _, w, a, b in xs)

        for tag, v in pairs:
            rater = tag.rsplit(".r", 1)[-1]
            for o in v.get("operations") or []:
                for m in o.get("members") or []:
                    out.append(dict(model=m["model"], prompt=prompt, domain=dom.get(prompt),
                                    rater=rater, relation=o["name"], is_reversed=0,
                                    from_words=words(m["model"], m.get("a_words"), "a"),
                                    to_words=words(m["model"], m.get("b_words"), "b")))
            for r in v.get("reversed") or []:
                out.append(dict(model=r["model"], prompt=prompt, domain=dom.get(prompt),
                                rater=rater, relation=r["operation"], is_reversed=1,
                                from_words=words(r["model"], r.get("a_words"), "a"),
                                to_words=words(r["model"], r.get("b_words"), "b")))
            for u in v.get("unassigned") or []:
                out.append(dict(model=u["model"], prompt=prompt, domain=dom.get(prompt),
                                rater=rater, relation="", is_reversed="",
                                from_words="", to_words=""))
    return out


def report(rs):
    judged = [r for r in rs if r["is_reversed"] != ""]
    rev = [r for r in judged if r["is_reversed"] == 1]
    print("\n%d rows: %d judged (placed or reversed), %d abstentions\n"
          % (len(rs), len(judged), len(rs) - len(judged)))
    print("  OVERALL  %d of %d judged model-readings are REVERSED  (%.1f%%)"
          % (len(rev), len(judged), 100.0 * len(rev) / len(judged)))
    print("           %d of %d over ALL shown, abstentions included  (%.1f%%)\n"
          % (len(rev), len(rs), 100.0 * len(rev) / len(rs)))

    print("  BY PROMPT (per rater, because the two disagree)\n")
    by = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for r in judged:
        c = by[(r["domain"], r["prompt"])][r["rater"]]
        c[0] += r["is_reversed"] == 1
        c[1] += 1
    print("    %-14s %-46s %-12s %-12s %s" % ("domain", "prompt", "rater 1", "rater 2", "spread"))
    for (d, p), rr in sorted(by.items()):
        cs = [rr.get(str(i), [0, 0]) for i in (1, 2)]
        pc = [100.0 * c[0] / c[1] if c[1] else float("nan") for c in cs]
        print("    %-14s %-46s %-12s %-12s %.0fpp"
              % (d, p[:46], "%d/%d (%.0f%%)" % (cs[0][0], cs[0][1], pc[0]),
                 "%d/%d (%.0f%%)" % (cs[1][0], cs[1][1], pc[1]), abs(pc[0] - pc[1])))

    print("\n  BY DOMAIN\n")
    bd = collections.defaultdict(lambda: [0, 0])
    for r in judged:
        bd[r["domain"]][0] += r["is_reversed"] == 1
        bd[r["domain"]][1] += 1
    for d, (a, b) in sorted(bd.items(), key=lambda x: -x[1][0] / max(x[1][1], 1)):
        print("    %-16s %3d of %4d  (%.1f%%)" % (d, a, b, 100.0 * a / b))

    print("\n  MODELS MOST OFTEN CALLED REVERSED  (distinct prompts, either rater)\n")
    mp = collections.defaultdict(set)
    tot = collections.defaultdict(set)
    for r in judged:
        tot[r["model"]].add(r["prompt"])
        if r["is_reversed"] == 1:
            mp[r["model"]].add(r["prompt"])
    for m, ps in sorted(mp.items(), key=lambda x: -len(x[1]))[:12]:
        print("    %-34s %2d of %2d prompts" % (m, len(ps), len(tot[m])))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--csv", default=os.path.join(HERE, "results", "reversal_table.csv"))
    a = ap.parse_args()
    rs = rows()
    cols = ["model", "prompt", "domain", "rater", "relation", "is_reversed",
            "from_words", "to_words"]
    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rs)
    report(rs)
    print("\n  wrote %s" % a.csv)


if __name__ == "__main__":
    main()
