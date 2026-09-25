"""Conservative hand vetting of the precision-kept interiority lists. (RH: "vet for me, be conservative", 2026-09-25)

    .venv/bin/python -u interiority_vetting.py   -> $SHARED/precision_keep_v2_vetted.csv, INTERIORITY_VETTING.md

WHAT WAS READ: the kept base words of clean X and the candidates in order of their own surface-form token
mass over arc_fiction (arc_token_mass_{cleanx,cand}_p.csv), the first 400 of each -- 97% of clean X's
tokens, 89% of the candidates' -- plus the nine kept under kind other/speech. Every removal then took
its kept inflectional siblings with it, found by stem over the whole kept list.

THE RULE, conservative: remove a word if any COMMON sense of it in English prose 1600-2000 is not a
subject's mental state or act, or if surface counting cannot separate the mental use from a routine
non-mental one. text_freqs has no POS and no context, so a word is only as clean as its worst common
sense. The categories below are the reasons. Remaining judgment calls are listed in the readout, not
hidden: hear/heard stay (sensory perception with no common non-perceptual sense), know/think/thought stay.

Removing a base word removes its MorphAdorner variants and long-s readings downstream
(arc_interiority_precision.py keeps a variant only while a word it spells is kept). The consensus file
is not modified; the vetted file sits beside it. EXPLORATORY.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.expanduser("~/malignment-data/interiority_norms")
KEEP_CSV = os.path.join(SHARED, "precision_keep_v2.csv")
VETTED_CSV = os.path.join(SHARED, "precision_keep_v2_vetted.csv")

REMOVE = {
    "looking, watching and examining (outward acts) and see's non-perceptual senses (meet, attend to, 'you see')": """
        see seeing seen sees watch watched watching view viewed viewing views viewpoint viewpoints gaze gazed
        glanced stared staring peering eyeing scanned scanning surveyed surveying inspect inspected inspecting
        inspects behold beheld beholding glimpse glimpses observe observed observing observation observations
        observer witnessed witnessing detect detecting examin examine examines examining hearing noted noting
        vividly perceptible""",
    "bodily sensation or touch (feel the cloth, felt the wall; felt the fabric)": """
        feel feels felt sensations weary wearying wearied appetite appetites discomfort bitterness depressed
        depressing""",
    "want as lack or need (for want of, wanting in), dominant in the early period": """
        want wanted wanting wants""",
    "outward effort, action or pursuit": """
        try tries attempt attempted attempting effort efforts endeavor endeavored endeavoring endeavors endeavour
        endeavoured endeavouring endeavours strive striven strives striving strove seek seekin' seeking seeks
        pursuing pursuit persist persisted persisting resist resisted undertake undertaken select selected
        selecting aim aimed aims contrive contrives contriving devise devised devises devising invent inventing
        invents investigate investigated investigating discover discovering discovers discovery neglect attend
        await awaited awaiting reject rejected rejecting rejection rejects renounce reconcile satisfy satisfies""",
    "speech and communication acts (observed and suggested are dialogue tags)": """
        informed suggested suggesting suggestion suggestions assurance assured assuredly refusal refused refuses
        refusing consent consented consenting assented agree acknowledge acknowledged acknowledging urge urged
        propose proposing confide confiding confirm objections inquiries inquirers inquiringly questioning
        interpret interpretation interpretations interpreted interpreting vowed caution beware regards daresay""",
    "legal, financial or institutional senses": """
        trust trusts interest interests judg judge judgment judgments judgement faculty faculties wills convicted
        conviction convictions speculate speculated speculating speculation speculations speculative consideration
        considerations preferred resolution resolutions approved estimate estimated estimates estimating estimation
        reckon reckoned""",
    "another common non-mental sense (reason = cause, plan = drawing, attitude = posture, intelligence = news, "
    "sorry = poor, supposed to, conceive a child, focus a lens, inclined plane, fathom = depth...)": """
        reason reasons purpose purposes plan plans design induced determined determine determin determination
        determinations determining decided notice notices attitude intelligence experience regard regarded study
        conceive conceived conceiving conception conceptions concluded conclude concludes concluding acquaint
        acquainted acquainting acquaints confusion curiosity impressed impressions bored fathom fathomed fathoming
        focus focused focuses focusing focussed focussing concentrate concentrating concentration inclination
        inclinations inclined inclin familiarity puzzle identified identifies identify identifying identification
        sorry fancy supposed meant respect concerned cared cares troubled lonely lonesome fearful distress
        distressed distresses distressing desperate reflect reflecting affect affecting distinguish marvel
        deliberate pictured prompted prompting apprehension apprehend apprehended notions accept accepting accepts
        acceptance suspect suspects ingenious ingenuity voluntary voluntarily imaginable assume assumed assumes
        assuming assumption assumptions prized rejec""",
    "manner adverbs of action and discourse markers": """
        carefully careful humbly listlessly doubtless""",
    "evaluative adjectives of things, not states of a subject": """
        interesting exciting fascinating surprising astonishing amusing delightful annoying tempting convincing
        confusing puzzling""",
    "consistency with RH's removal of love and loved": """
        loving loves""",
}


def main():
    K = pd.read_csv(KEEP_CSV)
    assert len(K) == 15099, len(K)
    kept = set(K[K.spelling_of.isna() & K.keep].form)
    why, seen = {}, set()
    for reason, ws in REMOVE.items():
        for w in ws.split():
            assert w not in seen, ("listed twice", w)
            seen.add(w)
            why[w] = reason
    #: a removal that is not a kept base word removes nothing; a typo must fail, not pass silently
    missing = sorted(w for w in why if w not in kept)
    assert not missing, ("not a kept base word", missing)
    K["vet_removed"] = K.form.map(lambda f: f in why)
    K["vet_reason"] = K.form.map(why)
    K["keep_vetted"] = K.keep & ~K.vet_removed
    assert not os.path.exists(VETTED_CSV), "refusing to overwrite " + VETTED_CSV
    K.to_csv(VETTED_CSV, index=False)
    base = K[K.spelling_of.isna()]
    L = ["# Conservative vetting of the precision-kept interiority lists (EXPLORATORY)", "",
         "Producer `interiority_vetting.py` (the rule and what was read are in its docstring). Input %s; output %s, "
         "which adds `keep_vetted` and `vet_reason` and changes nothing else." % (
             os.path.basename(KEEP_CSV), VETTED_CSV), "",
         "| | kept by consensus | removed in vetting | kept after vetting |", "|---|---|---|---|"]
    for s, lab in (("cleanx", "clean X base words"), ("cand", "candidate base words")):
        b = base[base.source == s]
        L.append("| %s | %d | %d | %d |" % (lab, int(b.keep.sum()), int(b.vet_removed.sum()), int(b.keep_vetted.sum())))
    L += ["", "## Removed, by reason", ""]
    for reason, ws in REMOVE.items():
        L.append("- **%s** (%d): %s" % (reason, len(ws.split()), ", ".join(ws.split())))
    L += ["", "## Judgment calls kept", "",
          "hear, heard (sensory perception without a common non-perceptual sense); know, think, thought, believe, "
          "suppose, remember, understand (no common non-mental sense); doubt (no doubt is still a judgment); afraid "
          "(the politeness use still reports a stance); pleasure, pleased (the politeness uses likewise); hope, wish; "
          "mad (both senses mental); attention; studied and studying (study is gone as the room). Below the first 400 "
          "by token mass the consensus decision stands unvetted: 11% of the candidates' tokens and 3% of clean X's."]
    open(os.path.join(HERE, "INTERIORITY_VETTING.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:9]))


if __name__ == "__main__":
    main()
