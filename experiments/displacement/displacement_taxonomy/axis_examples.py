"""Two exemplar words per pole, chosen by paper-claude from the ranked candidates.

Frequency ranking returns the corpus head -- `said` 469, `told` 397, `went` 395
-- so the two most common words on a pole are often just the two most common
words, and the figure repeated them across rows. These are picked instead:
semantically representative, rhetorically efficient, and **no word used twice
anywhere in the figure**, with inflections counted as one word (kill/killed,
file/filed, say/said, take/took, call/called, add/added, leave/left) because a
reader sees the repeat.

Keyed by axis id, in the figure's ORIENTED order: the first pair is the left
pole and the second the right, where the right pole is the high-lift
destination.

Three departures from the "prefer a high-lift-attested word" rule, his
reasoning kept because each is about what the row means:

  specificity_vs_generality  `file, sue` at lift 0 -- on a REVERSING row that
                             pole is the LOW-lift destination, so a high-lift
                             word there would misdescribe the reversal
  illocutionary_type         lift 0 throughout; the row lives in the advice
                             battery and its labels can only come from there
  same_event_vs_new_event    `checked, replaced` at lift 1 and 0 because its
                             better words (stabbed, hit, cut, killed) do more
                             work on other rows
"""

PICKS = {
    "bluntness_vs_euphemism":          (("fuck", "dick"), ("held", "placed")),
    "force_and_abruptness":            (("beat", "shoved"), ("kissed", "pressed")),
    "handling_vs_no_contact":          (("punched", "pulled"), ("watched", "looked")),
    "inner_state_vs_outward_act":      (("told", "got"), ("feel", "believe")),
    "evaluative_polarity":             (("hit", "smashed"), ("live", "gave")),
    "engagement_vs_withdrawal":        (("leave", "quit"), ("confront", "examined")),
    "deliberation_vs_decisive_act":    (("pay", "sell"), ("consider", "probably")),
    "creation_vs_destruction":         (("kill", "die"), ("make", "create")),
    "sexual_or_transgressive_content": (("breasts", "penis"), ("face", "hair")),
    "same_event_vs_new_event":         (("then", "called"), ("checked", "replaced")),
    "constitution_vs_construal":       (("stabbed", "cut"), ("said", "demanded")),
    "speech_vs_physical_act":          (("pushed", "threw"), ("shouted", "screamed")),
    "specificity_vs_generality":       (("file", "sue"), ("began", "take")),
    "locomotion_vs_object_act":        (("kicked", "address"), ("ran", "came")),
    "illocutionary_type":              (("contact", "provide"), ("note", "mention")),
    "act_vs_outcome":                  (("asked", "wrote"), ("found", "realized")),
    "argument_structure":              (("interrogate", "report"), ("argue", "discuss")),
    "compliance_vs_resistance":        (("never", "dispute"), ("talk", "dear")),
    "concrete_vs_abstract":            (("father", "mother"), ("understand", "decided")),
    "target_person_vs_thing":          (("shot", "handed"), ("phone", "poured")),
    "act_vs_state":                    (("sent", "added"), ("there", "now")),
    "manner_vs_act":                   (("put", "rubbed"), ("whispered", "gently")),
    "realis_vs_irrealis":              (("know", "point"), ("need", "want")),
    "means_vs_end":                    (("use", "saw"), ("discovered", "receive")),
    "institutional_vs_personal":       (("get", "stop"), ("appeal", "seek")),
    "ritual_vs_ordinary":              (("went", "sat"), ("offered", "recited")),
}

#: inflections a reader reads as one word, so they may not both appear
_FAMILY = [("kill", "killed"), ("file", "filed"), ("say", "said"),
           ("take", "took"), ("call", "called"), ("add", "added"),
           ("leave", "left")]


def stem(w):
    for fam in _FAMILY:
        if w in fam:
            return fam[0]
    return w
