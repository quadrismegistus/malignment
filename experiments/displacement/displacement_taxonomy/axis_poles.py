"""Short pole names for the 38 axes, written by hand.

The consolidator's pole descriptions are one or two clauses each -- "acts
without touching it — looking, using, or leaving it alone" -- which is right
for a question put to a rater and wrong for an axis label. Mechanical
shortening truncated a third of them.

**EVERY PAIR IS <= 16 CHARACTERS AND NOTHING IS ELIDED (RH).** A label ending
in an ellipsis asks the reader to guess, and on a semantic differential the two
labels ARE the axis, so a guessed one is a missing axis.

First letter capitalised, no trailing punctuation, no articles. The pair reads
left-pole / right-pole in the vocabulary's own order, so `POLES[id][0]`
corresponds to `pole_x` and a positive value means alignment moves toward
`POLES[id][1]`.
"""

POLES = {
    "speech_vs_physical_act":          ("Speech", "Bodily act"),
    "inner_state_vs_outward_act":      ("Inner state", "Outward act"),
    "kind_of_inner_state":             ("Feeling", "Judgement"),
    "same_event_vs_new_event":         ("Same event", "New event"),
    "act_vs_outcome":                  ("Further act", "Its result"),
    "act_vs_state":                    ("Action", "State"),
    "content_vs_framing":              ("Content word", "Connective"),
    "manner_vs_act":                   ("Manner", "Bare act"),
    "modifier_time_or_degree":         ("Time or degree", "Manner or place"),
    "argument_structure":              ("Intransitive", "Object-taking"),
    "word_class_or_form":              ("One word class", "Another"),
    "act_vs_entity":                   ("Doing", "Thing"),
    "target_person_vs_thing":          ("At a person", "At an object"),
    "orientation_toward_other_party":  ("Toward the other", "Self-directed"),
    "engagement_vs_withdrawal":        ("Staying", "Leaving"),
    "locomotion_vs_object_act":        ("Own movement", "Act on a thing"),
    "transfer_vs_own_handling":        ("Handing over", "Keeping"),
    "handling_vs_no_contact":          ("Touching", "Not touching"),
    "force_and_abruptness":            ("Forceful", "Gentle"),
    "sexual_or_transgressive_content": ("Transgressive", "Ordinary"),
    "bluntness_vs_euphemism":          ("Plain", "Euphemistic"),
    "volition_and_agency":             ("Chosen", "Undergone"),
    "deliberation_vs_decisive_act":    ("Weighing", "Acting"),
    "compliance_vs_resistance":        ("Complying", "Refusing"),
    "institutional_vs_personal":       ("Procedural", "Personal"),
    "specificity_vs_generality":       ("Specific", "General"),
    "concrete_vs_abstract":            ("Concrete", "Abstract"),
    "body_referent":                   ("Intimate part", "Whole region"),
    "creation_vs_destruction":         ("Making", "Unmaking"),
    "ritual_vs_ordinary":              ("Ceremonial", "Ordinary act"),
    "evaluative_polarity":             ("Condemnatory", "Benign"),
    "spatial_configuration":           ("Bounded place", "Open extent"),
    "means_vs_end":                    ("Means", "End"),
    "illocutionary_type":              ("Directing", "Reporting"),
    "constitution_vs_construal":       ("What it is", "How it seems"),
    "realis_vs_irrealis":              ("Fact", "Want"),
    "co_member_of_same_field":         ("One member", "Another member"),
    "motion_geometry":                 ("Turning", "Driving through"),
}


def check(axes):
    """Refuse rather than fall back. -> the pairs, in the axes' order.

    A missing pole would otherwise be silently replaced by a truncated
    description, which is the thing this file exists to remove.
    """
    missing = [a["id"] for a in axes if a["id"] not in POLES]
    if missing:
        raise KeyError("no short poles for: %s" % ", ".join(missing))
    return [POLES[a["id"]] for a in axes]
