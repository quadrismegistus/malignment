"""Conservative hand vetting of the USAS E precision keeps, the X vetting's rule. (RH: "same procedure more or less for both")

    .venv/bin/python -u interiority_vetting_e.py   -> $SHARED/precision_e_keep_v2_vetted.csv, INTERIORITY_VETTING_E.md

WHAT WAS READ: the 676 base words interiority_precision_e.py's consensus keeps, in order of their own
surface-form token mass over arc_fiction, the first 300 (95% of their tokens); every removal took its kept
inflectional siblings, found by stem over all 676.

THE RULE is interiority_vetting.py's: remove a word if any COMMON sense of it in English prose 1600-2000 is
not a subject's mental state, or if surface counting cannot separate the mental use from a routine
non-mental one. For an emotion list that adds two classes the X vetting barely met: bodily pain words
(agony, suffering) and dispositions or virtues rather than feelings (kindness, fortitude, meekness). The
abstraction seat's three flagged tails (E3's violent action, E5's martial bravery, E2's judgement verbs)
were checked by name: the rater had already rejected every one (brutal, valiant, dauntless, condemn...),
so they need no line here beyond E2's disapprove family.

The consensus file is not modified. EXPLORATORY.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
KEEP_CSV = os.path.join(SHARED, "precision_e_keep_v2.csv")
VETTED_CSV = os.path.join(SHARED, "precision_e_keep_v2_vetted.csv")

REMOVE = {
    "bodily pain or physical condition (suffering, agony; depression of ground or trade; mortification as gangrene)": """
        suffering agony agonies agonise agonised agonize agonized depression depress depresses depressingly
        mortification mortified mortifies mortify mortifying languished""",
    "tending, possessing or physical ease (take care of; enjoy an estate; comforts as amenities; relish the condiment)": """
        care caring enjoy enjoyed enjoying comfort relish treasured bereft""",
    "evaluative adjectives of things and conditions (a miserable hut, a wretched road, a cheerful fire, a pitiful sum)": """
        miserable miserably wretched wretchedness cheerful cheery pitiful pitifully disgusting disgustful galling
        harrowing upsetting endearing plaintive sentimental""",
    "another common non-mental sense (composed a letter, upset the cup, relieved the guard, calm sea, political "
    "agitation, provoked a war, pacify a province, fret of a lute, the console, financial embarrassments)": """
        composed upset relieved calmer calming calmness agitation provoked pacify pacified appeased unruffled fret
        frets console embarrassments blessedness estrangement amity enmity mourning""",
    "dispositions, virtues and vices rather than feelings": """
        kindness kindliness benevolence sincerity fortitude forbearance forbearing meekness magnanimous amiability
        avarice reticence""",
    "speech, judgement and outward acts (E2's judgement verbs among them)": """
        blaming disapproved disapproves disapproving disagreed deprecate deprecating hesitated acquiesced
        acquiescent spurned condolence condoling expectantly""",
    "a modal, a person noun, a truncation or an arrest (durst = dared; wits; lov; apprehensions)": """
        durst wits lov apprehensions""",
}


def main():
    K = pd.read_csv(KEEP_CSV)
    kept = set(K[K.spelling_of.isna() & K.keep].form)
    assert len(kept) == 676, len(kept)                 # INTERIORITY_PRECISION_E.md
    why, seen = {}, set()
    for reason, ws in REMOVE.items():
        for w in ws.split():
            assert w not in seen, ("listed twice", w)
            seen.add(w)
            why[w] = reason
    missing = sorted(w for w in why if w not in kept)
    assert not missing, ("not a kept base word", missing)
    K["vet_removed"] = K.form.map(lambda f: f in why)
    K["vet_reason"] = K.form.map(why)
    K["keep_vetted"] = K.keep & ~K.vet_removed
    assert not os.path.exists(VETTED_CSV), "refusing to overwrite " + VETTED_CSV
    K.to_csv(VETTED_CSV, index=False)
    base = K[K.spelling_of.isna()]
    L = ["# Conservative vetting of the USAS E precision keeps (EXPLORATORY)", "",
         "Producer `interiority_vetting_e.py` (rule and reading in its docstring). Input %s; output %s, adding "
         "`keep_vetted` and `vet_reason`." % (os.path.basename(KEEP_CSV), VETTED_CSV), "",
         "- base words kept by consensus: %d; removed in vetting: %d; kept after vetting: %d" % (
             int(base.keep.sum()), int(base.vet_removed.sum()), int(base.keep_vetted.sum())),
         "- kept after vetting, by kind: " + ", ".join("%s %d" % (k, int(v)) for k, v in base[base.keep_vetted].kind.value_counts().items()),
         "", "## Removed, by reason", ""]
    for reason, ws in REMOVE.items():
        L.append("- **%s** (%d): %s" % (reason, len(ws.split()), ", ".join(ws.split())))
    L += ["", "## Judgment calls kept", "",
          "comforted, comforting (consoling, not ease); cheerfulness and composure (states of a person, where "
          "cheerful and calmness also describe fires and seas); mournful, doleful (expression of a feeling, kept as with X's "
          "`sorrowful`); torment family (kept in X); repentance and penitence (religious but felt); hate family; "
          "happier, happiest, sadder (comparatives of kept or pending words). RH's interiority removals (happy, fear, "
          "love, loved) were rated in the X run and are NOT decided here."]
    open(os.path.join(HERE, "INTERIORITY_VETTING_E.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:6]))


if __name__ == "__main__":
    main()
