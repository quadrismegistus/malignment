"""What SHAPE does alignment's change take at the top of a prompt's distribution?

    python run.py                      # 2,400 prompts, 50 endpoint lineages
    python run.py --csv results/by_prompt.csv --examples results/examples.csv

`existence` asks where the freed mass GOES, in aggregate, across USAS fields.
This asks a different question of the same store: for a given prompt, does the
most likely word CHANGE, and if it does, where did its replacement come from?
`kill -> scream` is one answer among several and this measures how common it is.

## THE UNIT IS THE PROMPT AND THE 50 LINEAGES ARE REPLICATES

**Aggregated, not per cell.** Per (prompt, word) the probabilities are averaged
over every lineage that carries the pair, and the argmax is taken on those two
averaged distributions -- which is exactly the arithmetic behind the campaign's
`kill -> scream` figure, where each arm is a mean over models. A per-cell
classification answers "what did THIS model do here" and is reported beside it
as the AGREEMENT column, never as the headline.

Both are printed because they can disagree and the disagreement is informative:
a prompt whose aggregate says SUBSTITUTION while only 12 of 50 lineages
individually substitute is a prompt where the mean is doing the work.

## THE CATEGORIES, AND THE TWO QUESTIONS THAT DEFINE THEM

Does the argmax change, and if so where did the new one come from:

    HELD_REINFORCED   top word unchanged, and MORE likely after alignment
    HELD_ERODED       top word unchanged, but less likely -- losing the slot
                      without losing it
    MOVED_PROMOTION   new top was already rank 2-3, and the old top does not
                      fall much: a reorder at the head of the shortlist
    MOVED_SUBSTITUTION  old top falls hard AND new top rises hard. The paradigm
                      case, and the only one that deserves the word
    MOVED_INTRUSION   new top ranked below 10 in base: something arrives from
                      outside what the base was considering
    MOVED_OTHER       argmax moved without either a clear trade or an intrusion

`--fall-frac` and `--rise-frac` set what "falls hard" means, and travel into
the CSV as columns, because a typology's thresholds ARE the typology.

## THE ARGMAX IS THE SURFACE AND IT HIDES THINGS. SO CHURN IS REPORTED BESIDE IT.

**A stable top word does not mean a stable distribution.** On "he raised the
weapon and", `fired` holds the top in both arms while `shot` falls 0.033 and
`aimed` rises 0.037 underneath it -- the whole event happens at ranks 2 and 3
and the argmax label says HELD. Any typology built on the top word alone will
call that no-change, which is why these columns exist:

    tv            total variation, 0.5 * sum |p_aligned - p_base| over the
                  covered content words. How much mass moved, at any rank.
    top_churn     of base's top `--churn-k` content words, the fraction NOT in
                  aligned's top k. Turnover of the shortlist itself.
    rank_shift    mean |rank change| over words in base's top k.

`surface` (the argmax label) and `subsurface` (churn band) are crossed in the
output, because the interesting cell is HELD-with-high-churn: the prompt whose
answer did not change and whose reasoning did.

## THE PRIMARY TYPOLOGY IS THE CROSSING, NOT THE ARGMAX

**`kill -> scream` names a CROSSING, and the campaign's figure draws one.** Two
lines, the biggest faller and the biggest riser, starting apart and ending
swapped. That event does not require either word to be the argmax and usually
neither is: on the weapon prompt `fired` holds the top in both arms while
`shot` falls and `aimed` rises beneath it, and an argmax classifier calls that
no-change.

So the biggest faller `f` (max `p_base - p_aligned`) and the biggest riser `r`
(max `p_aligned - p_base`) are classified on their trajectories:

    CROSSED         f began ABOVE r and ended BELOW it. The lines swap. This is
                    the shape the paradigm case is named for.
    CLOSED          f stayed above r but the gap narrowed by >= `--close-frac`.
                    A crossing that did not complete.
    PARALLEL        f stayed above r and the gap did not materially narrow.
    ALREADY_ABOVE   r was already above f in base, so no crossing was available
                    -- the strongest riser was already beating the strongest
                    faller before alignment touched it.

and carried with their POSITIONS, because a crossing at ranks 1 and 2 and a
crossing at ranks 7 and 12 are not the same event:

    rank_faller_base, rank_riser_base, rank_riser_aligned
    faller_is_base_argmax, riser_is_aligned_argmax
    gap_base, gap_aligned   the signed p(f) - p(r) at each end

The argmax typology stays as `label`, because "did the top word change" is
still worth knowing. It is no longer the headline.

## THE FATE OF THE WITHDRAWN MASS: CONCENTRATED, OR SPREAD THIN?

Conservation is true by definition -- a distribution sums to one, so what
alignment takes from one word it must put somewhere. WHERE, and across HOW
MANY words, is not settled by the definition at all: the mass could spread
thinly over thousands of candidates or land on a single substitute. These
columns answer that per prompt.

    lost / gained       total mass withdrawn and total received, over covered
                        content words. They differ because coverage is partial.
    absorb_1/3/10       share of `lost` taken by the top 1, 3, 10 risers
    n_to_half           how many risers it takes to absorb half the lost mass.
                        **This is the concentration number.** 1 or 2 means a
                        substitution; a few hundred means dispersal.
    n_gaining           how many words gained anything at all
    faller_sub_theta    did the biggest faller drop BELOW THETA in aligned?
                        `theta` is the store's own floor, 0.001 on all 86M rows
                        under `rule='canonical'`, so this is the store's
                        definition of a word vanishing rather than one chosen
                        here. A faller that goes sub-theta has not been
                        replaced by anything in particular; it has been
                        dissolved.

## COVERAGE IS A COLUMN, BECAUSE THE DISTRIBUTION IS TRUNCATED

`movement_v4` holds the candidates above a probability floor, not the whole
vocabulary: per-cell covered mass runs about 0.50 to 0.94. That is fine for an
ARGMAX, which is by construction inside the covered set, and fine for a RANK
among covered words. It is NOT fine for entropy, so no dispersion statistic is
computed here and none should be added without renormalising and saying so.
`covered_base` and `covered_aligned` are per-prompt means.
"""

import argparse
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))

OUT = os.path.join(HERE, "results", "by_prompt.csv")

#: the store's own floor: `theta` is 0.001 on all 86,068,421 rows of
#: movement_v4 under `rule='canonical'`. Read, not chosen.
THETA = 0.001


def classify(bw, aw, ranks, fall_frac, rise_frac, distant_rank):
    """-> (label, rank, provenance). `bw`/`aw` are (word, p_base, p_aligned).

    **DYNAMICS IS THE LABEL, PROVENANCE IS A COLUMN, AND AN EARLIER VERSION
    CONFUSED THEM.** `MOVED_INTRUSION` used to be a label tested BEFORE
    substitution, so a move that both traded mass AND came from rank 14 was
    filed as an intrusion and the trade disappeared. They are not alternatives:
    "did mass trade" and "where did the replacement come from" are separate
    questions and a move has an answer to each.

    So the label answers the first -- SUBSTITUTION if the old top falls hard
    and the new one rises hard, PROMOTION if the new top simply overtakes a
    top that holds, OTHER otherwise -- and `provenance` answers the second:

        adjacent   the new top was rank 2-3 in base
        mid        rank 4 to `distant_rank`
        distant    below `distant_rank`: a word the base barely weighed
    """
    if bw[0] == aw[0]:
        return ("HELD_REINFORCED" if aw[2] > bw[1] else "HELD_ERODED"), 1, "same"
    rk = ranks.get(aw[0], 10 ** 6)
    prov = "adjacent" if rk <= 3 else ("mid" if rk <= distant_rank else "distant")
    fell = (bw[1] - bw[2]) / bw[1] if bw[1] > 0 else 0.0
    rose = (aw[2] - aw[1]) / aw[2] if aw[2] > 0 else 0.0
    if fell >= fall_frac and rose >= rise_frac:
        return "MOVED_SUBSTITUTION", rk, prov
    if fell < fall_frac and rose >= rise_frac:
        return "MOVED_PROMOTION", rk, prov
    return "MOVED_OTHER", rk, prov


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default=OUT)
    ap.add_argument("--examples", default=None,
                    help="write the per-prompt top words and their probabilities")
    ap.add_argument("--fall-frac", type=float, default=0.30,
                    help="the old top must lose this FRACTION of its mass for "
                         "SUBSTITUTION. A threshold, so it is a flag and it is "
                         "written into every row.")
    ap.add_argument("--rise-frac", type=float, default=0.30)
    ap.add_argument("--distant-rank", type=int, default=10,
                    help="a new top worse than this rank in base has DISTANT "
                         "provenance. A column, not a label; see classify().")
    ap.add_argument("--all-pos", action="store_true",
                    help="keep function words. OFF by default: `have` and `be` "
                         "are AUX in `should have` / `should be`, and that one "
                         "construction accounted for most of MOVED_PROMOTION "
                         "and MOVED_OTHER in the first run -- a typology whose "
                         "two largest moved classes are one auxiliary is "
                         "describing the corpus, not the operation.")
    ap.add_argument("--verbose-tables", action="store_true",
                    help="print the full contingency table for every test "
                         "that clears p<0.05")
    ap.add_argument("--analyse", action="store_true",
                    help="read the merged CSV and test whether CHARGE alters "
                         "the distribution of crossing types. Reads, never "
                         "recomputes.")
    ap.add_argument("--both", action="store_true",
                    help="run BOTH arms and write one merged table, one row "
                         "per prompt, raw_* and framed_* columns side by side, "
                         "plus the prompt's language and every charge.py "
                         "measure. The framed arm covers only the 31 pairs "
                         "with a readable template, so framed_* is EMPTY on "
                         "prompts it could not reach -- empty, not zero.")
    ap.add_argument("--frame", default="raw", choices=("raw", "prefill"),
                    help="raw is base_raw->aligned_raw. prefill is "
                         "base_raw->aligned_FRAMED, the deployed arm against "
                         "the bare one -- ASYMMETRIC by construction, since 43 "
                         "of 50 bases ship no chat template. Population comes "
                         "from movement.clean_frame_pairs(), which reads what "
                         "each template actually RENDERED, not the argument "
                         "passed to the producer.")
    ap.add_argument("--close-frac", type=float, default=0.30,
                    help="the faller-riser gap must narrow by this fraction "
                         "for CLOSED rather than PARALLEL")
    ap.add_argument("--churn-k", type=int, default=10,
                    help="shortlist length for top_churn and rank_shift")
    ap.add_argument("--tag-top", type=int, default=60,
                    help="tag this many top candidates per arm for the "
                         "content-word filter. Tagging all ~800 per prompt is "
                         "1.9M spaCy calls for a rank nobody reads.")
    ap.add_argument("--min-carriers", type=int, default=5,
                    help="a word needs this many lineages carrying it to be "
                         "eligible for the argmax. One model is not a "
                         "prompt-level fact; see the note in main().")
    ap.add_argument("--lang", default="en",
                    help="restrict to this language's prompts. movement_v4 "
                         "holds zh too, and the first run classified 2,985 "
                         "prompts where en has 2,400.")
    ap.add_argument("--min-lineages", type=int, default=25,
                    help="a prompt needs this many lineages to be classified")
    a = ap.parse_args(argv)

    if a.analyse:
        return analyse(a)
    if a.both:
        return merged(a)
    rows = measure(a, a.frame)
    return write(rows, a.csv)


def measure(a, frame):
    """Run one arm and return its per-prompt rows. -> [dict]"""
    import collections, statistics as _st
    class _A:  # a frozen view of the args with `frame` pinned
        pass
    aa = _A()
    for k, v in vars(a).items():
        setattr(aa, k, v)
    aa.frame = frame
    a = aa
    if True:
        from malignment import ch, roster, charge, fields, pos as POS

        eps, unresolved = roster.endpoints()
        if unresolved:
            raise SystemExit("unresolved lineages: %s" % sorted(unresolved)[:3])
        mode_of = None
        if a.frame == "prefill":
            from malignment import movement as M
            mode_of = {(b, x): m for b, x, m in M.clean_frame_pairs()
                       if eps.get(b) == x}
            eps = {b: x for b, x in eps.items() if (b, x) in mode_of}
            print("  --frame prefill: %d of 50 pairs have a readable framed arm"
                  % len(eps))
        pairs = {(b, x) for b, x in eps.items()}
        want_p = set(charge.prompts(a.lang)) if a.lang else None
        print("  %d endpoint lineages, %s prompts in %s"
              % (len(pairs), len(want_p) if want_p else "all", a.lang or "any"))

        #: **DIVIDED BY THE PROMPT'S LINEAGE COUNT, NOT BY THE WORD'S.** The first
        #: version divided by the lineages that actually CARRIED each word, on the
        #: reasoning that absent is not zero. That is wrong for this aggregate and
        #: it produced a spectacular artifact: `MOVED_INTRUSION` came out at 35.5%
        #: of prompts against 0.7% at cell level, because a word in ONE lineage's
        #: covered set at p=0.246 beat a word in all fifty at p=0.175. `apologize`
        #: won a prompt on a single model.
        #:
        #: `movement_v4` keeps candidates above a probability floor, so a word
        #: missing from a lineage is BELOW THE FLOOR, not unobserved -- its
        #: probability there is approximately zero and that is the right summand.
        #: This is also the arithmetic behind the campaign's `kill -> scream`
        #: figure, where each arm is a mean over models and a model that never
        #: offers `scream` contributes ~0 rather than dropping out of the mean.
        #: `--min-carriers` additionally refuses the argmax to a word too few
        #: lineages ever produced, because one model is not a prompt-level fact.
        acc = collections.defaultdict(lambda: [0.0, 0.0, 0])
        seen_lin = collections.defaultdict(set)
        cov = collections.defaultdict(lambda: [0.0, 0.0, 0])
        #: **ONE QUERY PER LINEAGE, NOT ONE FOR THE WHOLE TABLE.** `ch.query` builds
        #: a LIST of every row before returning -- 21.8M dicts for the unrestricted
        #: scan, which took this process to 20.4 GB RSS and was killed by the OS
        #: after taking the machine down with it. There is no streaming accessor in
        #: `ch`, so the scan is chunked by (base, aligned): 50 queries of ~440k rows,
        #: each list freed before the next is fetched.
        #:
        #: Prompts are mapped to small ints as they arrive. A key of
        #: (prompt_string, word) holds a fresh ~200-character string per candidate,
        #: about 800 times per prompt; an int key holds the string once.
        pid, pstr = {}, []
        n_rows = 0
        for i, (b, x) in enumerate(sorted(pairs), 1):
            if mode_of is None:
                fa = "AND frame_aligned=''"
            else:
                fa = ("AND frame_aligned='prefill' AND system_mode_aligned='%s'"
                      % mode_of[(b, x)].replace("'", "\\'"))
            q = ("SELECT prompt, word, p_base, p_aligned FROM {db}.movement_v4 "
                 "WHERE frame_base='' %s AND base='%s' AND aligned='%s'"
                 % (fa, b.replace("'", "\\'"), x.replace("'", "\\'")))
            chunk = ch.query(q, limit_bytes=None)
            for r in chunk:
                p = r["prompt"]
                if want_p is not None and p not in want_p:
                    continue
                j = pid.get(p)
                if j is None:
                    j = pid[p] = len(pstr)
                    pstr.append(p)
                n_rows += 1
                e = acc[(j, r["word"])]
                e[0] += float(r["p_base"]); e[1] += float(r["p_aligned"]); e[2] += 1
                seen_lin[j].add((b, x))
                c = cov[(j, i)]
                c[0] += float(r["p_base"]); c[1] += float(r["p_aligned"]); c[2] = 1
            del chunk
            if i % 10 == 0:
                print("    %d/%d lineages, %d rows kept" % (i, len(pairs), n_rows),
                      flush=True)
        print("  %d rows over %d prompts" % (n_rows, len(seen_lin)))

        by_prompt = collections.defaultdict(list)
        for (j, w), (sb, sa, k) in acc.items():
            n = len(seen_lin[j]) or 1
            by_prompt[pstr[j]].append((w, sb / n, sa / n, k))
        acc.clear()
        seen_lin = {pstr[j]: v for j, v in seen_lin.items()}
        covm2 = collections.defaultdict(list)
        for (j, _i), c in cov.items():
            covm2[pstr[j]].append((c[0], c[1]))
        cov = covm2

        #: CONTENT WORDS ONLY, TAGGED IN CONTEXT, AND ONLY THE CONTENDERS.
        #: `pos.get_pos` tags a word at the end of ITS OWN prompt, which is the
        #: position a candidate occupies; a type-level tag would decide `still`,
        #: `back` and `down` once for the corpus. Tagging every candidate would be
        #: ~1.9M calls, so only the top `--tag-top` by either arm are tagged --
        #: enough for the argmax and for any rank a reader would look at, and the
        #: rank column is then a rank AMONG CONTENT WORDS, which is what it should
        #: have been anyway.
        if not a.all_pos:
            nlp = POS.get_nlp(POS.LANG_MODEL.get("en", POS.SPACY_MODEL))
            st_ = POS._stash()
            kept = 0
            for p, ws in list(by_prompt.items()):
                top = {w for w, _b, _a, _k in sorted(ws, key=lambda x: -x[1])[:a.tag_top]}
                top |= {w for w, _b, _a, _k in sorted(ws, key=lambda x: -x[2])[:a.tag_top]}
                try:
                    tg = POS.get_pos(sorted(top), p, nlp=nlp, stash=st_)
                except Exception:
                    tg = {}
                ws2 = [x for x in ws if tg.get(x[0]) in fields.CONTENT_POS]
                by_prompt[p] = ws2
                kept += len(ws2)
            print("  content-word filter: %d candidate words kept over %d prompts"
                  % (kept, len(by_prompt)))

        covm = cov

        rows, tally = [], collections.Counter()
        prov_tally = collections.Counter()
        cross = collections.Counter()
        cross_tally = collections.Counter()
        cross_by_argmax = collections.Counter()
        for p, ws in by_prompt.items():
            nlin = len(seen_lin[p])
            if nlin < a.min_lineages or len(ws) < 5:
                continue
            elig = [x for x in ws if x[3] >= a.min_carriers] or ws
            order = sorted(elig, key=lambda x: -x[1])
            ranks = {w: i + 1 for i, (w, _b, _a, _k) in enumerate(order)}
            bw = max(elig, key=lambda x: x[1])
            aw = max(elig, key=lambda x: x[2])
            k = a.churn_k
            ob = [w for w, _b, _a, _c in sorted(elig, key=lambda x: -x[1])[:k]]
            oa = [w for w, _b, _a, _c in sorted(elig, key=lambda x: -x[2])[:k]]
            churn = sum(1 for w in ob if w not in set(oa)) / float(len(ob) or 1)
            ra = {w: i for i, w in enumerate(sorted(elig, key=lambda x: -x[2]))}
            shift = (sum(abs(ra.get(w, len(elig)) - i) for i, w in enumerate(ob))
                     / float(len(ob) or 1))
            tv = 0.5 * sum(abs(x[2] - x[1]) for x in elig)
            sub = "low" if churn <= 0.2 else ("mid" if churn <= 0.5 else "high")
            #: biggest faller and biggest riser BY DELTA, which is what the
            #: slopegraph draws in full opacity and what a reader points at.
            fw = max(elig, key=lambda x: x[1] - x[2])
            rw = max(elig, key=lambda x: x[2] - x[1])
            gb, ga = fw[1] - rw[1], fw[2] - rw[2]
            if gb > 0 and ga < 0:
                cross_lab = "CROSSED"
            elif gb <= 0:
                cross_lab = "ALREADY_ABOVE"
            elif gb > 0 and (gb - ga) / gb >= a.close_frac:
                cross_lab = "CLOSED"
            else:
                cross_lab = "PARALLEL"
            #: the fate of the withdrawn mass. `lost` and `gained` are over covered
            #: content words only and will not be equal; both are reported rather
            #: than one normalised against the other, because the gap IS the
            #: uncovered tail and hiding it would assert a conservation the data
            #: cannot show.
            losses = sorted((x[1] - x[2] for x in elig if x[1] > x[2]), reverse=True)
            gains = sorted((x[2] - x[1] for x in elig if x[2] > x[1]), reverse=True)
            lost = sum(losses) or 1e-12
            gained = sum(gains)
            cum, n_half = 0.0, 0
            for gval in gains:
                cum += gval
                n_half += 1
                if cum >= 0.5 * lost:
                    break
            else:
                n_half = len(gains)
            ab1 = (gains[0] / lost) if gains else 0.0
            ab3 = (sum(gains[:3]) / lost) if gains else 0.0
            ab10 = (sum(gains[:10]) / lost) if gains else 0.0
            sub_theta = int(fw[2] < THETA)
            rb = {w: i + 1 for i, (w, _b, _a, _c) in
                  enumerate(sorted(elig, key=lambda x: -x[1]))}
            ra2 = {w: i + 1 for i, (w, _b, _a, _c) in
                   enumerate(sorted(elig, key=lambda x: -x[2]))}
            cross_tally[cross_lab] += 1
            lab, rk, prov = classify((bw[0], bw[1], bw[2]), (aw[0], aw[1], aw[2]),
                                     ranks, a.fall_frac, a.rise_frac, a.distant_rank)
            tally[lab] += 1
            prov_tally[(lab, prov)] += 1
            cross[("HELD" if lab.startswith("HELD") else "MOVED", sub)] += 1
            cross_by_argmax[(lab, cross_lab)] += 1
            cb = [c[0] for c in covm[p]]
            ca = [c[1] for c in covm[p]]
            rows.append({
                "prompt": p, "label": lab, "n_lineages": nlin, "n_words": len(ws),
                "base_top": bw[0], "p_base_top": "%.5f" % bw[1],
                "p_aligned_of_base_top": "%.5f" % bw[2],
                "aligned_top": aw[0], "p_aligned_top": "%.5f" % aw[2],
                "p_base_of_aligned_top": "%.5f" % aw[1],
                "rank_of_aligned_top_in_base": rk, "provenance": prov,
                "crossing": cross_lab,
                "faller": fw[0], "p_base_faller": "%.5f" % fw[1],
                "p_aligned_faller": "%.5f" % fw[2],
                "riser": rw[0], "p_base_riser": "%.5f" % rw[1],
                "p_aligned_riser": "%.5f" % rw[2],
                "rank_faller_base": rb.get(fw[0], -1),
                "rank_riser_base": rb.get(rw[0], -1),
                "rank_riser_aligned": ra2.get(rw[0], -1),
                "faller_is_base_argmax": int(fw[0] == bw[0]),
                "riser_is_aligned_argmax": int(rw[0] == aw[0]),
                "gap_base": "%+.5f" % gb, "gap_aligned": "%+.5f" % ga,
                "lost": "%.5f" % lost, "gained": "%.5f" % gained,
                "absorb_1": "%.3f" % ab1, "absorb_3": "%.3f" % ab3,
                "absorb_10": "%.3f" % ab10, "n_to_half": n_half,
                "n_gaining": len(gains), "faller_sub_theta": sub_theta,
                "tv": "%.4f" % tv, "top_churn": "%.2f" % churn,
                "rank_shift": "%.2f" % shift, "subsurface": sub,
                "covered_base": "%.3f" % (sum(cb) / len(cb)),
                "covered_aligned": "%.3f" % (sum(ca) / len(ca)),
                "n_carriers_aligned_top": aw[3],
                "fall_frac_cut": a.fall_frac, "rise_frac_cut": a.rise_frac,
                "distant_rank_cut": a.distant_rank,
                "min_carriers_cut": a.min_carriers, "frame": a.frame,
                "churn_k_cut": a.churn_k})

        tot = sum(tally.values())
        print()
        print("  %d prompts classified (>= %d lineages)" % (tot, a.min_lineages))
        for k, v in tally.most_common():
            print("  %-20s %6d  %5.1f%%" % (k, v, 100.0 * v / tot))
        moved = sum(v for k, v in tally.items() if k.startswith("MOVED"))
        print()
        print("  argmax HELD on %.1f%% of prompts, MOVED on %.1f%%"
              % (100.0 * (tot - moved) / tot, 100.0 * moved / tot))
        rr = collections.Counter(r["rank_of_aligned_top_in_base"] for r in rows
                                 if r["label"].startswith("MOVED"))
        print("  where it moved, the new top's rank in base: %s"
              % dict(sorted((k, v) for k, v in rr.items() if k <= 6)))
        print()
        print("  DYNAMICS x PROVENANCE (provenance is a column, not a class)")
        print("  %-20s %10s %6s %9s" % ("label", "adjacent", "mid", "distant"))
        for lab in ("MOVED_SUBSTITUTION", "MOVED_PROMOTION", "MOVED_OTHER"):
            print("  %-20s %10d %6d %9d"
                  % (lab, prov_tally[(lab, "adjacent")], prov_tally[(lab, "mid")],
                     prov_tally[(lab, "distant")]))
        print()
        ct = sum(cross_tally.values())
        print("  CROSSING -- biggest faller against biggest riser (the slopegraph)")
        for k, v in cross_tally.most_common():
            print("  %-16s %6d  %5.1f%%" % (k, v, 100.0 * v / ct))
        print()
        print("  CROSSING x ARGMAX -- the two typologies crossed")
        print("  **They are not the same cut and neither contains the other.** The")
        print("  argmax asks whether the TOP word changed; the crossing asks whether")
        print("  the biggest faller and biggest riser SWAPPED. A prompt can cross")
        print("  with the top word untouched (the event happens at ranks 2 and 6),")
        print("  and the top word can change without any crossing (the new top")
        print("  arrived from elsewhere while faller and riser never met).")
        print()
        cl = [k for k, _ in cross_tally.most_common()]
        al = ["HELD_REINFORCED", "HELD_ERODED", "MOVED_PROMOTION",
              "MOVED_SUBSTITUTION", "MOVED_OTHER"]
        print("  %-20s %s %8s" % ("argmax \\ crossing",
                                 " ".join("%13s" % c for c in cl), "total"))
        for lb in al:
            row = [cross_by_argmax[(lb, c)] for c in cl]
            if not sum(row):
                continue
            print("  %-20s %s %8d"
                  % (lb, " ".join("%13d" % v for v in row), sum(row)))
        print("  %-20s %s %8d"
              % ("total", " ".join("%13d" % cross_tally[c] for c in cl),
                 sum(cross_tally.values())))
        print()
        xs = sum(cross_by_argmax[(lb, "CROSSED")] for lb in al if lb.startswith("HELD"))
        ms = sum(cross_by_argmax[("MOVED_SUBSTITUTION", c)] for c in cl)
        agree = cross_by_argmax[("MOVED_SUBSTITUTION", "CROSSED")]
        print("  crossings with the argmax HELD: %d of %d (%.0f%%) -- invisible to"
              % (xs, cross_tally["CROSSED"],
                 100.0 * xs / max(1, cross_tally["CROSSED"])))
        print("  an argmax typology.")
        print("  MOVED_SUBSTITUTION prompts: %d, of which %d also CROSSED (%.0f%%)."
              % (ms, agree, 100.0 * agree / max(1, ms)))
        import statistics as _st2
        cr = [r for r in rows if r["crossing"] == "CROSSED"]
        if cr:
            print()
            print("  of the %d CROSSED: faller was the base argmax in %d, riser the "
                  "aligned argmax in %d" % (len(cr),
                     sum(int(r["faller_is_base_argmax"]) for r in cr),
                     sum(int(r["riser_is_aligned_argmax"]) for r in cr)))
            print("  median ranks -- faller %d in base, riser %d in base, %d in aligned"
                  % (_st2.median(int(r["rank_faller_base"]) for r in cr),
                     _st2.median(int(r["rank_riser_base"]) for r in cr),
                     _st2.median(int(r["rank_riser_aligned"]) for r in cr)))
        import statistics as _st3
        print()
        print("  THE FATE OF THE WITHDRAWN MASS")
        nh = sorted(int(r["n_to_half"]) for r in rows)
        print("  risers needed to absorb HALF the lost mass:")
        print("    median %d   quartiles %d / %d   90th pct %d   max %d"
              % (nh[len(nh) // 2], nh[len(nh) // 4], nh[3 * len(nh) // 4],
                 nh[int(0.9 * len(nh))], nh[-1]))
        for k in ("absorb_1", "absorb_3", "absorb_10"):
            v = sorted(float(r[k]) for r in rows)
            print("  %-10s median %.3f  (top riser takes this share of lost mass)"
                  % (k, v[len(v) // 2]) if k == "absorb_1" else
                  "  %-10s median %.3f" % (k, v[len(v) // 2]))
        stv = sum(int(r["faller_sub_theta"]) for r in rows)
        print("  biggest faller drops BELOW THETA (%.3f) in aligned: %d of %d (%.1f%%)"
              % (THETA, stv, len(rows), 100.0 * stv / len(rows)))
        print("  words gaining anything: median %d"
              % sorted(int(r["n_gaining"]) for r in rows)[len(rows) // 2])
        bycross = collections.defaultdict(list)
        for r in rows:
            bycross[r["crossing"]].append(int(r["n_to_half"]))
        print("  n_to_half by crossing type: %s"
              % ", ".join("%s %d" % (k, sorted(v)[len(v) // 2])
                          for k, v in sorted(bycross.items())))
        print()
        print("  SURFACE x SUBSURFACE -- the argmax against what moved beneath it")
        print("  %-8s %8s %8s %8s   (top_churn over top %d content words)"
              % ("", "low", "mid", "high", a.churn_k))
        for srf in ("HELD", "MOVED"):
            print("  %-8s %8d %8d %8d"
                  % (srf, cross[(srf, "low")], cross[(srf, "mid")], cross[(srf, "high")]))
        import statistics as _st
        for srf in ("HELD", "MOVED"):
            v = [float(r["tv"]) for r in rows
                 if r["label"].startswith(srf)]
            if v:
                print("  median total variation, %-5s %.4f" % (srf, _st.median(v)))
        top_pairs = collections.Counter(
            (r["base_top"], r["aligned_top"]) for r in rows if r["label"].startswith("MOVED"))
        print()
        print("  most common moved pairs: %s"
              % ", ".join("%s->%s %d" % (b, g, n) for (b, g), n in top_pairs.most_common(6)))


    return rows


def charge_cols(prompt, lang):
    """Every per-prompt measure `charge.py` exposes. -> dict

    `dose` is the mean scene rating over the prompt's candidate words, `frame`
    the setup alone on the same 1-7 scale, and `lift` their difference -- what
    the candidates ADD over their setup, which is the quantity `existence`
    found selectivity scales with. `kinds` are the modal deepseek labels over
    the same candidates, reported as the modal kind plus the share of each,
    because a single modal label hides a 40/60 split.
    """
    from malignment import charge
    import collections as _c
    out = {"lang": lang}
    try:
        out["dose"] = charge.dose(prompt)
        out["frame_charge"] = charge.frame(prompt)
        out["lift"] = charge.lift(prompt)
        out["frame_kind"] = charge.frame_kind(prompt)
    except Exception:
        out.setdefault("dose", None)
    sc = {}
    try:
        sc = charge.scene(prompt) or {}
    except Exception:
        pass
    out["n_rated_words"] = len(sc)
    out["max_scene"] = max(sc.values()) if sc else None
    kd = {}
    try:
        kd = charge.kinds(prompt) or {}
    except Exception:
        pass
    cnt = _c.Counter(kd.values())
    tot = sum(cnt.values()) or 1
    out["modal_kind"] = cnt.most_common(1)[0][0] if cnt else ""
    for k in ("SEXUAL", "VIOLENT", "DEGRADING", "COERCIVE", "ILLICIT",
              "OTHER", "NONE"):
        out["share_" + k.lower()] = "%.3f" % (cnt.get(k, 0) / tot)
    return out


def merged(a):
    """Both arms, one row per prompt, with language and charge. -> int"""
    from malignment import charge
    keep = ("label", "crossing", "provenance", "subsurface",
            "base_top", "aligned_top", "rank_of_aligned_top_in_base",
            "faller", "riser", "p_base_faller", "p_aligned_faller",
            "p_base_riser", "p_aligned_riser", "rank_faller_base",
            "rank_riser_base", "rank_riser_aligned", "faller_is_base_argmax",
            "riser_is_aligned_argmax", "gap_base", "gap_aligned",
            "lost", "gained", "absorb_1", "absorb_3", "absorb_10",
            "n_to_half", "n_gaining", "faller_sub_theta", "tv", "top_churn",
            "rank_shift", "n_lineages", "n_words", "covered_base",
            "covered_aligned")
    arms = {}
    for frame in ("raw", "prefill"):
        print("\n################ %s" % frame.upper())
        arms[frame] = {r["prompt"]: r for r in measure(a, frame)}
    lang_of = {}
    for lg in ("en", "zh"):
        try:
            for pr in charge.prompts(lg):
                lang_of[pr] = lg
        except Exception:
            pass
    out = []
    for pr, rr in arms["raw"].items():
        row = {"prompt": pr}
        row.update(charge_cols(pr, lang_of.get(pr, a.lang or "")))
        for pre, src in (("raw_", rr), ("framed_", arms["prefill"].get(pr))):
            for k in keep:
                row[pre + k] = (src or {}).get(k, "")
        #: does the frame CHANGE the verdict? The single most useful derived
        #: column: a prompt that CLOSED raw and CROSSED framed is one the
        #: deployment wrapper pushed over the line.
        row["crossing_changed"] = int(
            bool(row["framed_crossing"]) and row["framed_crossing"] != row["raw_crossing"])
        row["argmax_changed"] = int(
            bool(row["framed_label"]) and row["framed_label"] != row["raw_label"])
        out.append(row)
    print()
    n_f = sum(1 for r in out if r["framed_crossing"])
    print("  merged: %d prompts, %d with a framed arm" % (len(out), n_f))
    ch_ = sum(r["crossing_changed"] for r in out)
    print("  crossing verdict differs raw vs framed: %d of %d framed (%.0f%%)"
          % (ch_, n_f, 100.0 * ch_ / max(1, n_f)))
    import collections as _c2
    mv = _c2.Counter((r["raw_crossing"], r["framed_crossing"]) for r in out
                     if r["framed_crossing"] and r["crossing_changed"])
    print("  most common raw -> framed transitions: %s"
          % ", ".join("%s->%s %d" % (x, y, n) for (x, y), n in mv.most_common(5)))
    return write(out, a.csv)


def analyse(a):
    """Does charge alter the distribution of crossing types? -> int

    **The types are counts, so the test is a permutation on the table, not a
    correlation.** Prompts are binned by a charge measure, the crossing
    distribution is tabulated per bin, and the chi-square statistic of that
    table is compared against shuffling the bin labels. A chi-square p from the
    asymptotic distribution would assume expected counts nobody has checked;
    the permutation makes no such assumption and costs a second.

    Reported for `dose` (how charged the scene is), `lift` (what the candidate
    words ADD over the setup, which is the quantity `existence` found
    selectivity scales with) and `modal_kind` (the deepseek label).
    """
    import csv as _csv, collections as _c, random as _r
    rows = list(_csv.DictReader(open(a.csv, encoding="utf-8")))
    if not rows:
        print("nothing at %s" % a.csv)
        return 1
    print("  %d prompts from %s" % (len(rows), a.csv))

    def chi2(tab, rk, ck):
        n = sum(tab.values()) or 1
        rt = _c.Counter(); ct = _c.Counter()
        for (r_, c_), v in tab.items():
            rt[r_] += v; ct[c_] += v
        s2 = 0.0
        for r_ in rk:
            for c_ in ck:
                e = rt[r_] * ct[c_] / n
                if e > 0:
                    s2 += (tab.get((r_, c_), 0) - e) ** 2 / e
        return s2

    def test(name, band_of, arm="raw_crossing"):
        pairs = [(band_of(r), r[arm]) for r in rows if r.get(arm) and band_of(r)]
        if len(pairs) < 50:
            print("  %-22s too few prompts" % name)
            return
        rk = sorted({b for b, _ in pairs}); ck = sorted({c for _, c in pairs})
        tab = _c.Counter(pairs)
        obs = chi2(tab, rk, ck)
        rng = _r.Random(7)
        bands = [b for b, _ in pairs]; cs = [c for _, c in pairs]
        hits = 0
        for _ in range(5000):
            rng.shuffle(bands)
            if chi2(_c.Counter(zip(bands, cs)), rk, ck) >= obs:
                hits += 1
        p = (hits + 1) / 5001.0
        star = "*" if p < 0.05 else " "
        print("  %s %-10s %-18s n=%-5d chi2 %6.1f   p %.4f"
              % (star, name, arm, len(pairs), obs, p))
        if p < 0.05 and a.verbose_tables:
            print("      %-14s %s" % ("", " ".join("%12s" % c for c in ck)))
            for b in rk:
                tot = sum(tab[(b, c)] for c in ck) or 1
                print("      %-14s %s  n=%d"
                      % (b, " ".join("%11.1f%%" % (100.0 * tab[(b, c)] / tot)
                                     for c in ck), tot))

    def band(field, cuts):
        def f(r):
            try:
                v = float(r[field])
            except (TypeError, ValueError):
                return None
            for lo, hi, lab in cuts:
                if lo <= v < hi:
                    return lab
            return None
        return f

    #: **THE FULL GRID, BECAUSE A NULL ON ONE CELL IS NOT A NULL.** The first
    #: version tested lift against `raw_crossing` only and reported it as the
    #: null. Three of the four typologies had not been asked.
    DOSE = band("dose", [(1, 2.5, "1 dose<2.5"), (2.5, 3.5, "2 2.5-3.5"),
                         (3.5, 4.5, "3 3.5-4.5"), (4.5, 8, "4 dose>=4.5")])
    LIFT = band("lift", [(-9, 0, "1 lift<0"), (0, 0.4, "2 0-0.4"),
                         (0.4, 0.8, "3 0.4-0.8"), (0.8, 9, "4 lift>=0.8")])
    KIND = lambda r: r.get("modal_kind") or None
    for nm, fn in (("DOSE", DOSE), ("LIFT", LIFT), ("KIND", KIND)):
        for arm in ("raw_crossing", "framed_crossing", "raw_label",
                    "framed_label"):
            test("by %s" % nm, fn, arm=arm)
    print()
    print("  mean dose by crossing type (raw):")
    g = _c.defaultdict(list)
    for r in rows:
        try:
            g[r["raw_crossing"]].append(float(r["dose"]))
        except (TypeError, ValueError, KeyError):
            pass
    import statistics as _s
    for k, v in sorted(g.items(), key=lambda kv: -_s.mean(kv[1])):
        print("    %-16s %.3f   n=%d" % (k, _s.mean(v), len(v)))
    return 0


def write(rows, path):
    import csv as _csv, os as _os
    if not rows:
        print("no rows")
        return 1
    _os.makedirs(_os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        rows.sort(key=lambda r: (r.get("label", ""), r["prompt"]))
        w.writerows(rows)
    print("\n-> %s  (%d prompts)" % (path, len(rows)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
