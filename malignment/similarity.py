"""Are any two models in the store more alike than the roster says they are?

    python -m malignment.similarity --panel     build the balanced panel
    python -m malignment.similarity --screen    argmax agreement, all pairs
    python -m malignment.similarity --report    anomalies, with controls
    python -m malignment.similarity --markers   tokenizer-space contamination

## THE QUESTION THIS ANSWERS, AND WHY IT IS NOT THE PROVENANCE AUDIT

`roster/models/attestations.json` establishes independence from DOCUMENTS: what a
lab says it did. This establishes it from BEHAVIOUR: what the checkpoints actually
emit. They fail in opposite directions, which is the point of having both.

A card can omit a derivation (Falcon3-10B is depth-upscaled from 7B and reads like
a peer of it), and no amount of careful reading recovers what was never written.
Conversely two genuinely independent models can behave alike because they ate the
same corpus, and no behavioural test should be allowed to call that a derivation.

**The measured ceiling for "similar because of data" is 0.70 / JS 0.078**:
`pythia-6.9b` and `rwkv-4-7b-pile` -- a transformer and an RNN, no shared weights,
both trained on the Pile. Anything at or below that is corpus, not lineage.

## THE PANEL IS BALANCED ON PURPOSE

473 prompts are held by all 399 models with >= 2000 cells. Every pair therefore
shares exactly the same 473, and agreement rates are directly comparable.

Ranking pairs on their own overlap instead would compare a pair sharing 50 prompts
against one sharing 2,000 and call the noisier one more similar. That is the same
error as the archive's `same_base_as` holding 84 of 175 derivable pairs: a
population that varies per row, silently.

## CHEAP SCREEN, EXPENSIVE CONFIRM

Argmax agreement over the panel is one GROUP BY and one join on (prompt, word) --
it only ever pairs models that AGREE, so the 79,401 possible pairs cost seconds.
JS over full distributions is the confirm, run on the handful that survive.

Measured, on this corpus:

    same weights, different revision name    agree 1.000   JS 0.0000
    Phi-4-reasoning-plus / phi-4-reasoning   agree 0.896   JS 0.0142   <- ANOMALY
    declared DPO edge (Tulu SFT -> DPO)      agree 0.765   JS 0.0410
    shared corpus, no shared weights         agree 0.698   JS 0.0782
    unrelated families                       agree ~0.69   JS 0.105-0.149
    declared SFT edge (Olmo base -> SFT)     agree 0.482   JS 0.1617
    ALL PAIRS median                         agree 0.481

Note the ordering: a declared SFT step moves a model FURTHER than an unrelated
family sits away. Distance alone does not imply relation and never did -- which is
why the anomaly test is *closer than any declared alignment edge*, not *close*.

## THE ANOMALY IT FOUND

`microsoft/phi-4-reasoning` and `microsoft/Phi-4-reasoning-plus` sit at JS 0.0142:
11x closer than a declared SFT edge, 3x closer than a declared DPO edge, and the
only cross-lineage pair anywhere above 0.85 agreement (next is 0.708). The roster
carried phi-4, phi-4-reasoning and Phi-4-reasoning-plus as THREE independent
lineages. Microsoft's card says reasoning-plus is reasoning further trained with
RL. One lineage, two edges; the independent count was overstated by 2.

## AND THE ONE IT FOUND BY ACCIDENT, WHICH MATTERED MORE

The LOWEST declared edge was `dolphin-2.6-mistral-7b-dpo` against its own parent
at 0.004 -- agreeing on 2 of 473 prompts where UNRELATED families agree on 48%.
Nothing is that different by alignment. Its words carry the SentencePiece
word-boundary marker (`'▁the'` where every other model has `'the'`), so it joins
against nothing.

**The marker is the symptom, not the disease, and stripping it is the wrong fix.**
17.8% of its rows are unmarked, and they are byte-fallback tokens -- `<0x0A>`,
`<0xE5>`, `<0xE6>` -- alongside bare CJK. A true word probability is never half a
UTF-8 sequence. This model's twp was assembled in TOKEN space: the prefix trie
that composes tokens into words never ran for it. Conservation still holds (0
failures of 2,579 cells) because token probabilities sum to 1 exactly as word
probabilities do, which is why nothing upstream complained.

A `replaceRegexpOne(word, '^▁', '')` would produce plausible words with token mass
underneath, collide 104 surfaces silently, and repair the view while leaving the
quantity wrong. **Quarantine and re-measure. Do not strip.**

**RESOLVED 2026-08-16, and the correction inverted the finding.** Re-measured
locally under the current instrument -- 2,663 cells, 131 min at 2.98 s/cell, 0
skipped, clean word surfaces -- which confirms the diagnosis: ONE BAD PRODUCER
RUN, not the model or its tokenizer.

    Mistral-7B-v0.1 -dpo-> dolphin-2.6
      token space   JS 0.7171   largest edge in the corpus
      re-measured   JS 0.0563   SMALLEST edge in its own branch

A 12.7x error that did not merely inflate the number: it REVERSED THE ORDERING.
The same checkpoint went from the most-displaced model held to the least-
displaced tune on its base, so anything using it as an upper bound would have
been wrong in the direction of its own conclusion.

The corrected value is a result rather than a repair. dolphin is the roster's
ANTI-ALIGNED checkpoint -- "I have filtered the dataset to remove alignment and
bias" -- and it moves its base LESS than all five ordinary tunes on Mistral
(zephyr 0.1017, Nous-Hermes 0.0681, mistral-sft-beta 0.0666, openchat 0.0653,
OpenHermes 0.0640). De-aligning displaces less than aligning, which is what the
direction of the training predicts and is now measured.

**AND THE QUARANTINE HAD TO BE DONE TWICE.** The first attempt was an INGEST
GATE, which stops new data and does nothing about rows already stored: the next
movement rebuild read them straight out of `twp_words` and wrote 588,427 rows.
A gate is a claim about the future; remediation is a fact about the past. The
rows were deleted from the store and `produce_movement.buildable()` now inspects
the `twp_words` it is about to read.

When first found it had not reached `movement` (0 of 44.5M rows), and that is
what the original note recorded. It was true when measured and stopped being true
the moment a later fix let more edges build -- which is exactly why the note is
kept rather than replaced: **"not contaminated" was a reading of one moment, not
a property of the data.** And the artefact it would have carried, JS 0.82 on the
roster's anti-aligned discriminator, is one somebody would have wanted to
believe.
"""
import argparse
import sys

from . import ch

#: Models needing this many cells to enter the panel. The bar and the resulting
#: panel size are reported by --panel; they are not free parameters to tune until
#: a pair looks the way you want.
MIN_CELLS = 2000

#: js_term with the 0*log(0) branches guarded, identical to views.py. Duplicated
#: rather than imported because views.py builds it for `movement` columns and this
#: builds it over a raw pair -- one edit to either must not silently change the
#: other's meaning.
_JS = ("0.5 * (if(pa > 0, pa * log2(2 * pa / (pa + pb)), 0)"
       "     + if(pb > 0, pb * log2(2 * pb / (pa + pb)), 0))")

MARKERS = {"sentencepiece": "▁", "gpt2_bpe": "Ġ", "leading_space": " "}


#: **WHICH CORPUS THIS MODULE READS.** Default 3 and not 4: the v4 corpus covers
#: 23 models against v3's full roster, so flipping the default would silently
#: shrink every panel rather than announce anything. Set it explicitly --
#: `similarity.RULE_VERSION = 4` -- and `report()` prints what it used.
RULE_VERSION = 3


def build_panel():
    """(model, prompt, argmax word) over prompts EVERY qualifying model holds."""
    n_models = ch.scalar(ch.retable(
        "SELECT count() FROM (SELECT model FROM {db}.twp_words "
        "GROUP BY model HAVING uniqExact(prompt) >= %d)" % MIN_CELLS, RULE_VERSION))
    ch.execute("DROP TABLE IF EXISTS {db}.panel_argmax")
    ch.execute(ch.retable("""
CREATE TABLE {db}.panel_argmax ENGINE = MergeTree ORDER BY (prompt, word) AS
WITH big AS (SELECT model FROM {db}.twp_words GROUP BY model
             HAVING uniqExact(prompt) >= %d),
     panel AS (SELECT prompt FROM {db}.twp_words WHERE model IN (SELECT model FROM big)
               GROUP BY prompt HAVING uniqExact(model) = %d)
SELECT model, prompt, argMax(word, p) AS word, max(p) AS pmax
FROM {db}.twp_words
WHERE model IN (SELECT model FROM big) AND prompt IN (SELECT prompt FROM panel)
GROUP BY model, prompt
""" % (MIN_CELLS, n_models), RULE_VERSION))
    r = ch.query("SELECT uniqExact(model) m, uniqExact(prompt) p, count() n "
                 "FROM {db}.panel_argmax")[0]
    #: FULLY CROSSED OR NOT AT ALL. If this fails the panel is ragged and every
    #: rate below is computed against a different denominator.
    assert r["n"] == r["m"] * r["p"], (
        "panel is not fully crossed: %d rows for %d models x %d prompts"
        % (r["n"], r["m"], r["p"]))
    print("  panel: %d models x %d prompts, fully crossed" % (r["m"], r["p"]))
    return r["m"], r["p"]


def screen(n_prompts):
    ch.execute("DROP TABLE IF EXISTS {db}.panel_pairs")
    ch.execute("""
CREATE TABLE {db}.panel_pairs ENGINE = MergeTree ORDER BY (agree) AS
SELECT a.model AS m1, b.model AS m2, count() AS agree, count() / %f AS rate
FROM {db}.panel_argmax a
INNER JOIN {db}.panel_argmax b ON a.prompt = b.prompt AND a.word = b.word
WHERE a.model < b.model
GROUP BY m1, m2
""" % float(n_prompts))
    q = ch.query("SELECT count() c, quantiles(0.5, 0.99, 0.999)(rate) AS q "
                 "FROM {db}.panel_pairs")[0]
    print("  pairs with >=1 agreement: %s | median %.3f | p99 %.3f | p99.9 %.3f"
          % (format(q["c"], ","), q["q"][0], q["q"][1], q["q"][2]))


def js(a, b):
    """Mean JS over the panel, residual included as one more bucket.

    The residual is an ARM of the comparison, not a footnote: without it this is a
    divergence between two truncations. `twp_cells.total` holds it.
    """
    return ch.scalar(ch.retable("""
WITH panel AS (SELECT DISTINCT prompt FROM {db}.panel_argmax)
SELECT avg(js) FROM (
  SELECT w.prompt AS prompt, sum(%s) + any(rterm) AS js FROM (
    SELECT prompt, word, sumIf(p, model='%s') AS pa, sumIf(p, model='%s') AS pb
    FROM {db}.twp_words
    WHERE model IN ('%s','%s') AND prompt IN (SELECT prompt FROM panel)
    GROUP BY prompt, word) w
  INNER JOIN (
    SELECT prompt, 0.5*(if(ra>0, ra*log2(2*ra/(ra+rb)), 0)
                      + if(rb>0, rb*log2(2*rb/(ra+rb)), 0)) AS rterm
    FROM (SELECT prompt, sumIf(total, model='%s') AS ra, sumIf(total, model='%s') AS rb
          FROM {db}.twp_cells
          WHERE model IN ('%s','%s') AND prompt IN (SELECT prompt FROM panel)
          GROUP BY prompt)) r ON r.prompt = w.prompt
  GROUP BY w.prompt)
""" % (_JS, a, b, a, b, a, b, a, b), RULE_VERSION))


def _lineage_map():
    from . import roster
    d = roster.load()
    par, decl = {}, {}
    for p, op, c in (d.get("edges") or []):
        decl[(min(p, c), max(p, c))] = op
        if op in set(roster.DERIVING):
            par[c] = p

    def root(m):
        m = m.split("@")[0]
        seen = set()
        while m in par and m not in seen:
            seen.add(m)
            m = par[m]
        return m
    return root, decl


def report(limit=25):
    """Cross-lineage pairs with no declared relation, ranked. The anomaly list."""
    root, decl = _lineage_map()
    rows = ch.query("SELECT m1, m2, rate FROM {db}.panel_pairs ORDER BY rate DESC LIMIT 8000")
    out = []
    for r in rows:
        a, b = r["m1"], r["m2"]
        ba, bb = a.split("@")[0], b.split("@")[0]
        if ba == bb:
            continue
        if (min(ba, bb), max(ba, bb)) in decl:
            continue
        if root(a) == root(b):
            continue
        out.append((r["rate"], a, b))
    print("\n  CROSS-LINEAGE, NO DECLARED RELATION -- ranked by argmax agreement")
    print("  anything at or below 0.70 / JS 0.078 is within the shared-corpus ceiling\n")
    for rate, a, b in out[:limit]:
        print("  %.3f  %-40s %-40s" % (rate, a[:40], b[:40]))
    print("\n  above 0.85: %d | above 0.90: %d"
          % (sum(1 for x in out if x[0] >= 0.85), sum(1 for x in out if x[0] >= 0.90)))
    #: The confirm. Argmax agreement is a screen and a screen's job is to be cheap
    #: and wrong in the safe direction; nothing is reported as a duplicate on it.
    for rate, a, b in out[:3]:
        print("  confirm  JS %.4f  %s / %s" % (js(a, b), a.split("/")[-1], b.split("/")[-1]))
    return out


def markers():
    """Models whose word surfaces are in TOKEN space, not word space.

    Found by accident and worth its own pass: the defect is invisible to
    conservation (token probabilities sum to 1 too), invisible to row counts, and
    presents as an enormous alignment effect rather than as an error.
    """
    rows = ch.query(ch.retable("""
SELECT model,
       countIf(startsWith(word, '%s')) AS sp,
       countIf(startsWith(word, '%s')) AS gpt2,
       countIf(startsWith(word, ' '))  AS lead_space,
       count() AS n
FROM {db}.twp_words GROUP BY model
HAVING sp > 0 OR gpt2 > 0 OR lead_space > 0
ORDER BY (sp + gpt2 + lead_space) / n DESC
""" % (MARKERS["sentencepiece"], MARKERS["gpt2_bpe"]), RULE_VERSION))
    if not rows:
        print("  no tokenizer-marker contamination")
        return []
    print("  TOKENIZER-SPACE CONTAMINATION -- these models join against nothing\n")
    for r in rows:
        frac = (r["sp"] + r["gpt2"] + r["lead_space"]) / r["n"]
        print("  %-54s %5.1f%% of %s rows" % (r["model"][:54], 100 * frac,
                                              format(r["n"], ",")))
        print("     QUARANTINE AND RE-MEASURE. Do not strip the marker: it is the"
              "\n     symptom of a token-space assembly, and stripping repairs the"
              "\n     view while leaving token mass under word-shaped labels.")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", action="store_true")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--markers", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if not any((a.panel, a.screen, a.report, a.markers, a.all)):
        ap.print_help()
        return 0
    if a.panel or a.all:
        n_models, n_prompts = build_panel()
    if a.screen or a.all:
        n_prompts = ch.scalar("SELECT uniqExact(prompt) FROM {db}.panel_argmax")
        screen(n_prompts)
    if a.report or a.all:
        report()
    if a.markers or a.all:
        print()
        markers()
    return 0


if __name__ == "__main__":
    sys.exit(main())
