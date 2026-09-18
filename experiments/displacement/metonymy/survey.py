"""The garment instrument: one gate and three degree scales, two coders.

    python survey.py --pilot          # 20 words, both arms, the three checks
    python survey.py                  # the full 479

## THE INSTRUMENT

A gate (`Choice`) asked once per word, and three `Score` scales. Levels are
concrete situations that stand on their own -- the model sees the descriptions
and nothing else. Wording, its revision history and the review that produced it
are in `data/levels_draft.md`; this file is the administration.

**The gate is OFF the scales.** An earlier draft listed NOT_AN_OBJECT first on
every scale, which makes it position 0 of an ORDERED array: a Score
interpolates, so a word could come back four-tenths of the way from not being a
thing to uncovering nothing. Worse, position 0 means the opposite thing on
different scales, so the escape sat next to `bra` on two of three. One Choice,
asked once, categorical, no interpolation; the Scores are asked regardless and
masked in code where the gate fails.

**All three scales run low = intimate, high = peripheral.** The substantive
prediction is then ONE direction on all three: risers score HIGHER than fallers.
An earlier draft documented the direction backwards -- a sign inversion in the
prose, before any data -- which is the argument for fixing it in the level
array rather than tracking it downstream. Order IS the numbering and part of
the cache key.

## BOTH ARMS SEE ONE ITEM

    jev = s.map(items)
    t   = s.as_task(model=TEXT_MODEL)
    txt = t.map(s.as_task_prompts(items))

`state_text()` is the single renderer, so the cache key's state and the text
arm's prompt are byte-identical and a cross-arm check is string equality.
**The two frames are NAMED fields and the questions' `inspect` reads them by
name; flattening to prose breaks that reference SILENTLY and on the text arm
only**, so the jev arm would look correct while the text arm answered a
different question. `--pilot` asserts the identity rather than trusting it.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))

from largeliterarymodels.questions import Choice, Score          # noqa: E402
from largeliterarymodels.survey import Survey                    # noqa: E402

TEXT_MODEL = "deepseek/deepseek-flash"
#: `deepseek-v4-flash` is RETIRED. On 2026-09-16 the endpoint answers it with
#: "The supported API model names are deepseek-flash, deepseek-v4-pro", and the
#: completion's own `model` field returns `deepseek-flash`, unversioned -- so
#: the version cannot be pinned from the API. Model of record is
#: "deepseek-flash as served on the run date", and rows carry it.

FRAME_F = "She slowly took off her ___"
FRAME_M = "He slowly took off his ___"

GATE = Choice(
    instructions={
        "question": "Which of these best describes the word in the blank?",
        "inspect": ["word", "frame_female", "frame_male"],
        "focus": "What KIND of thing the word names. Not where it is worn.",
    },
    criteria={
        "GARMENT": "Clothing worn on the body.",
        "WORN_OR_CARRIED": "Worn or carried but not clothing: on the head, the "
                           "face, the wrists, or held in the hand.",
        "BODY_PART": "A part of the body itself, not a thing worn on it.",
        "OTHER_NOUN": "A real word naming something else: an activity, a place, "
                      "a material, or a group of people.",
        "NOT_A_WORD": "Not a complete English word. An incomplete fragment of "
                      "one.",
    })

S1 = Score(
    instructions={
        "question": "Assume nothing is worn over this item: it is the outermost "
                    "thing covering whatever it covers. The person removes it. "
                    "How much of the genitals or breasts is uncovered "
                    "afterwards?",
        "inspect": ["word", "frame_female", "frame_male"],
        "focus": "What removing it uncovers. Not where it sits.",
    },
    criteria=[
        {"what": "The genitals or breasts are left fully uncovered. Nothing "
                 "remains between them and the air.",
         "examples": ["loincloth", "chemise"]},
        {"what": "Part of the genital area or the breasts is uncovered, while "
                 "some of it stays covered by another garment.",
         "examples": ["sarong", "girdle"]},
        {"what": "Skin is uncovered that is ordinarily kept covered in public, "
                 "but the genitals and breasts stay covered.",
         "examples": ["smock", "chaps"]},
        {"what": "Skin is uncovered, but only skin ordinarily visible in public "
                 "anyway: arms, neck, lower legs.",
         "examples": ["surcoat", "jerkin"]},
        {"what": "Nothing that was covered becomes uncovered. The person is "
                 "dressed as before apart from this item.",
         "examples": ["anorak", "wellingtons"]},
    ])

S2 = Score(
    instructions={
        "question": "Where on the body does this item sit when worn or carried?",
        "inspect": ["word", "frame_female", "frame_male"],
        "focus": "Position alone. Do NOT consider what is worn over or under it.",
    },
    criteria=[
        {"what": "Directly over the genitals or the breasts.",
         "examples": ["loincloth", "chemise"]},
        {"what": "On the hips, waist, groin, buttocks or chest.",
         "examples": ["girdle", "codpiece"]},
        {"what": "Over the torso or the upper legs generally, not centred on "
                 "any one part.",
         "examples": ["kaftan", "anorak"]},
        {"what": "On the limbs or the extremities: lower legs, feet, arms, "
                 "hands, head, neck.",
         "examples": ["wellingtons", "earmuffs"]},
        {"what": "Not on the body at all. Carried or held.",
         "examples": ["holdall", "valise"]},
    ])

S3 = Score(
    instructions={
        "question": "A person dresses from nothing. At what point does this "
                    "item go on?",
        "inspect": ["word", "frame_female", "frame_male"],
        "focus": "The order of dressing. Interpretable only for clothing.",
    },
    criteria=[
        {"what": "First, directly onto bare skin, before any other clothing.",
         "examples": ["loincloth", "chemise"]},
        {"what": "After the first layer, and hidden by what follows. A person "
                 "fully dressed would not normally show it.",
         "examples": ["girdle", "petticoat"]},
        {"what": "Part of what a person is seen wearing in ordinary company "
                 "indoors.",
         "examples": ["smock", "kaftan"]},
        {"what": "Over what is worn indoors, adding warmth or cover without "
                 "replacing it.",
         "examples": ["surcoat", "jerkin"]},
        {"what": "Last, when leaving, and the first thing removed on arriving.",
         "examples": ["anorak", "wellingtons"]},
    ])


class GarmentSurvey(Survey):
    """One gate and three scales, asked of one word in two frames."""

    name = "garment_scales_v1"
    model = "jev-latest"
    questions = {"gate": GATE, "exposure": S1, "position": S2, "dressing": S3}

    def build_state(self, item):
        #: NAMED FIELDS. Both frames, never one -- showing only the female
        #: frame would build the gender asymmetry into the instrument meant to
        #: measure it. The questions' `inspect` reads these by name.
        return {"word": item, "frame_female": FRAME_F, "frame_male": FRAME_M}


#: deliberately half fragments, half real, and half of the real ones the words
#: the S1 baseline has to get right. `bathro` against `bathrobe` is the check
#: that matters most: a language model reads a fragment in-frame as the
#: completed word, which is the quiet failure of the whole gate.
PILOT = ["bathrobe", "bathro", "apron", "apr", "trousers", "t", "blouse", "bl",
         "sunglasses", "g", "bra", "shirt", "coat", "belt", "backpack",
         "arm", "army", "bath", "slippers", "raincoat"]

FRAMES = ("She slowly took off her", "He slowly took off his")


def candidates(min_lineages=2, pos_keep=("NOUN", "PROPN")):
    """The item list: words that MOVED, pooled over both frames. -> [str]

    **RECURRENCE, NOT MAGNITUDE.** A word enters at `min_lineages`, so the set
    is words many models move at any size rather than words one model moves
    hard. That is the original registration's rule and its argument: a claim
    about what the operation DOES wants recurrence.

    **POS IS CONTEXTUAL AND PREFILTERS, IT DOES NOT REPLACE THE GATE.**
    `pos.get_pos` tags each word at the end of its own frame. It removes the
    109 adjectives (`black`, `leather`, `wet`) cleanly, and it does NOT remove
    fragments: `t`, `bl`, `bathro` and `apr` all tag NOUN in frame, which is
    exactly why the survey carries a NOT_A_WORD gate. Prefilter and gate catch
    different things and both are needed.
    """
    from malignment import ch, roster, pos as POS
    import collections
    eps, unresolved = roster.endpoints()
    if unresolved:
        raise SystemExit("unresolved lineages: %s" % sorted(unresolved)[:3])
    pairs = {(b, x) for b, x in eps.items()}
    moved = collections.defaultdict(collections.Counter)
    for frame in FRAMES:
        q = ("SELECT base, aligned, word, p_base, p_aligned "
             "FROM {db}.movement_v4 WHERE frame_base='' AND frame_aligned='' "
             "AND prompt='%s'" % frame.replace("'", "\\'"))
        for r in ch.query(q, limit_bytes=None):
            if (r["base"], r["aligned"]) in pairs and \
                    float(r["p_aligned"]) != float(r["p_base"]):
                moved[frame][r["word"]] += 1
    nlp = POS.get_nlp(POS.LANG_MODEL.get("en", POS.SPACY_MODEL))
    stash = POS._stash()
    keep = set()
    for frame, c in moved.items():
        ws = sorted({w for w, n in c.items() if n >= min_lineages})
        tags = POS.get_pos(ws, frame, nlp=nlp, stash=stash)
        keep |= {w for w in ws if tags.get(w) in pos_keep}
    return sorted(keep)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pilot", action="store_true",
                    help="20 words, both arms, and the three checks")
    ap.add_argument("--text-model", default=TEXT_MODEL)
    ap.add_argument("--min-lineages", type=int, default=2,
                    help="a word enters the item list if it moved in this many "
                         "of the 50 endpoint lineages. Recurrence, not "
                         "magnitude; see candidates().")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="render and check the cross-arm identity, spend nothing")
    a = ap.parse_args(argv)

    s = GarmentSurvey()
    items = PILOT if a.pilot else candidates(a.min_lineages)
    print("  survey %r, %d items, %d questions" % (s.name, len(items), len(s.questions)))
    print("  jev arm: %s    text arm: %s" % (s.model, a.text_model))

    #: THE CROSS-ARM CHECK, BEFORE SPENDING ANYTHING. Both arms must see one
    #: item. `state_text` is the single renderer, so this is string equality --
    #: and it is asserted rather than trusted because a broken `inspect`
    #: reference fails silently and only on the text arm.
    prompts = s.as_task_prompts(items)
    import json as _json
    for it, txt in zip(items, prompts):
        st = s.build_state(it)
        assert txt == s.state_text(it), "state_text drifted from as_task_prompts"
        for f in ("word", "frame_female", "frame_male"):
            assert f in st, "state lost the %r field" % f
            #: ensure_ascii=False, MATCHING `_render_state`. At the default a
            #: non-ASCII word is escaped to `\\uXXXX` here and left literal
            #: there, and the check fails on a rendering that is correct --
            #: `coat．` (U+FF0E, a fullwidth stop) is the item that caught it.
            #: A check serialising differently from the thing it checks is not
            #: a check.
            assert _json.dumps(st[f], ensure_ascii=False)[1:-1] in txt, \
                "field %r did not survive rendering to the text arm" % f
    print("  cross-arm check: %d items, both frames present as NAMED fields in "
          "both arms" % len(items))
    print()
    print("  first rendered state:")
    print("    " + prompts[0].replace("\n", "\n    "))
    if a.dry_run:
        print("\n  --dry-run: checks passed, nothing spent.")
        return 0

    #: BOTH ARMS FROM ONE STATE, rendered once.
    print("\n  running the jev arm (%s)..." % s.model, flush=True)
    jev = s.map(items)
    print("  running the text arm (%s)..." % a.text_model, flush=True)
    t = s.as_task(model=a.text_model)
    txt = t.map(prompts)

    import csv as _csv
    QS = ["gate", "exposure", "position", "dressing"]
    rows = []
    for i, w in enumerate(items):
        r = {"word": w}
        #: the jev arm returns an `Answers` mapping: `.get(qid)` yields an
        #: answer carrying `.value` and `.probabilities`. A Score's value is a
        #: POSITION ON THE LEVELS and can fall between them -- `bra` comes back
        #: at 0.14, not 0 -- which is the whole reason the escape had to come
        #: off the scale. The text arm compiles Score to an int, so the two
        #: arms agree on RANK, never on value.
        ja = jev[i] if jev and i < len(jev) else None
        r["jev_model"] = getattr(ja, "model", "")
        for q in QS:
            a_ = ja.get(q) if ja is not None else None
            r["jev_" + q] = getattr(a_, "value", "")
        ta = txt[i] if txt and i < len(txt) else None
        for q in QS:
            v = getattr(ta, q, None) if ta is not None else None
            r["txt_" + q] = getattr(v, "value", v) if v is not None else ""
        #: MASKED IN CODE, not by conditioning the questions. Scores exist for
        #: every word because asking them all in one call is cheaper than a
        #: second round trip; they are interpretable only where the word is a
        #: thing worn or carried. `bathro` scores 1.93 on position and means
        #: nothing by it.
        #:
        #: **EITHER ARM MAY VETO.** A word is scorable only if BOTH accept it.
        #: Measured at 479: jev called GARMENT on 40 words deepseek called
        #: NOT_A_WORD, and deepseek did so on ZERO that jev refused -- the
        #: disagreement is one-directional. Those 40 are BPE fragments
        #: (`blaz`, `kimon`, `knick`, `legg`, `trou`, `underp`, `shir`), and
        #: jev is completing them in frame and rating the completion. That is
        #: exactly the failure this gate exists to catch, and a single-coder
        #: gate did not catch it: `underp` scored 0.18 on exposure and sat in
        #: the intimate cluster with a plausible number.
        ok = ("GARMENT", "WORN_OR_CARRIED")
        r["scored"] = int(r["jev_gate"] in ok and r["txt_gate"] in ok)
        r["gate_agree"] = int(r["jev_gate"] == r["txt_gate"])
        rows.append(r)
    out = a.out or os.path.join(
        HERE, "results", "pilot.csv" if a.pilot else "scales.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w_ = _csv.DictWriter(fh, fieldnames=list(rows[0])); w_.writeheader()
        w_.writerows(rows)
    print("-> %s  (%d words)" % (out, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
