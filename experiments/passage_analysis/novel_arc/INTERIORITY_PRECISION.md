# Precision-first re-rating of the interiority lists (EXPLORATORY)

Producer `interiority_precision.py`. 15099 forms: 3685 base words (clean X 1526, period candidates 2159) and 11414 MorphAdorner variants rated as forms. Keep only if every common sense is mental; function words, modals, speech and generic verbs always rejected. deepseek-v4-flash (resolved deepseek-flash), temperature 0, two shuffled passes and a third where they disagree on keep; consensus = majority. RH's hand removals (33) are excluded whatever the rating. Per form: /Users/rj416/malignment-data/interiority_norms/precision_keep_v2.csv.

- pass 1 vs pass 2 agreement on keep: 80.7% (2919 forms tie-broken)
- ties (equal keep and reject ratings, the tie-break having missed the form) rejected, precision first: 232
- tie-break batches dropped because an anchor flipped: 2 of 73
- anchors stable: regretted [True], dreaded [True], bright [False], would [False]

| | forms | kept | kept % |
|---|---|---|---|
| clean X, base words | 1526 | 1054 | 69.1% |
| candidates, base words | 2159 | 1243 | 57.6% |
| MorphAdorner variants | 11414 | 6498 | 56.9% |

Rejected base words with a named competing sense (sample): abandon (to leave or give up physically; not inherently mental); abandoning (leaving or giving up physically, not a mental state); abjuration (a formal rejection or renunciation); abjuring (renouncing or rejecting formally, often in speech); absorbing (taking in liquid; engrossing attention (also physical)); absorbs (soaks up or takes in (physical)); absurd (ridiculous, contrary to reason (of things, not mental states)); acceded (agreed to a demand or request; also attained an office); accepted (to receive or take something offered); accomplish (to complete or achieve a task); accustoming (making customary by practice, not a mental state); achieve (to accomplish or bring about by effort; also to reach a goal); achieving (to accomplish a goal); acknowledgements (act of admitting or recognizing, often a speech act); acquaintance (a person one knows, not a mental state); actuate (to put into mechanical motion; to activate a device); actuated (actuated: put into action, moved physically); acuteness (sharpness of a point or angle; severity of pain); adamant (unbreakable stone or firm refusal); adamantly (in an unyielding or inflexible manner); adapt (adapt (adjust to fit)); addicted (addicted as devoted to a habit or substance, not purely mental); adeptness (skill or proficiency, not a mental state); adjudged (adjudged: to make a formal judgment or decision in a legal context); admit (to confess or acknowledge; to allow entry); admitted (to allow entry or concede in speech); admittedly (sentence adverb conceding a point in discourse); admitting (to confess or acknowledge); adopt (to adopt a child or take up physically); advise (to give advice, a speech act); advised (to give advice or counsel; speech act); advising (giving advice, a speech act); advocate (advocate = publicly support or recommend (communication)); advocated (to publicly recommend; speech act); advocating (to publicly recommend or support, a communicative act); affected (influenced or acted upon); affirm (to state or declare as fact; communication); affirmation (a statement or declaration that something is true); affirmed (to state or assert positively (communication)); affirming (stating or asserting something)

Kept base words by kind: cognition 1124, emotion 621, volition 299, attention 125, perception 119, other 8, speech 1
