# LLM triage of period-model interiority candidates (EXPLORATORY)

Producer `interiority_candidates.py`. 5383 candidates (USAS X period-model neighbours, count >= 500, >= 5 non-perception seeds), each rated twice by deepseek-v4-flash at temperature 0 in independently shuffled batches of 40, with four anchors in every batch. Ratings: /Users/rj416/malignment-data/interiority_norms/candidate_ratings_v1.parquet. A triage aid for RH's vetting, not a norm; the interiority panel is validated against an LLM coder, so this list is not independent of that check. The API resolves the requested deepseek-v4-flash to a model it names deepseek-flash; that resolved id is the model of record.

## Robustness

- words rated in both passes: 5383 of 5383
- interior (0-3): exact agreement 78.9%, within one point 99.3%, Spearman 0.898
- kind: agreement 88.0%
- anchors (should never move): door interior [0] kind ['other'] (n=270); think interior [3] kind ['cognition'] (n=270); walk interior [0] kind ['other'] (n=270); wonder interior [3] kind ['cognition', 'emotion'] (n=270)

## Distribution (pass 1)

| interior | argument | attention | cognition | emotion | other | perception | volition |
|---|---|---|---|---|---|---|---|
| 0 | 330 | 0 | 0 | 0 | 1468 | 8 | 0 |
| 1 | 134 | 7 | 190 | 64 | 776 | 51 | 74 |
| 2 | 22 | 52 | 525 | 406 | 63 | 60 | 209 |
| 3 | 0 | 30 | 332 | 437 | 0 | 29 | 116 |

## Shortlist for vetting

Both passes rate interior >= 2 AND a mental kind (cognition, emotion, volition, perception, attention) in both: 1952 words. Kind 'mixed' where the two passes chose different mental kinds. 164 of them are forms modern English does not use (zipf 0: period spellings or OCR errors). Full list, with that flag: /Users/rj416/malignment-data/interiority_norms/candidate_shortlist_v1.csv.

- **cognition** (711): accept, accepts, acknowledge, acknowledging, acquainting, acquaints, anticipates, anticipations, apprehend, apprehended, apprised, apprized, ascertained, ascertaining, assented, assumes, assured, averred, avouch, avow, beavildered, beheve, beliefs, believ, certainty, circumspection, cogitating, cogitative, cognizant, cognized, communing, communings, comprehended, conceiving, conceptions, conceptualization, concludes, confide, confided, confident, confuses, conjeaure, conjectured, conjecturing, conjecure, conjedures, conjeeture, conjeture, consciousness, considers, construing, consults, contemplates, contemplations, convince, convinced, convinces, credulity, daresay, deceive ...
- **emotion** (770): abashed, abominate, admiration, admiring, adore, adored, affect, affection, affectionate, affections, affective, affright, affrighted, affrights, afraid, aftonifiment, aftoniflment, aftoniihment, aftonilhment, aghast, alarmed, ambivalence, ambivalent, amuse, amused, anger, angered, angry, anguish, animosity, annoyance, annoyed, antipathy, anxiety, anxious, anxiously, appalled, appreciating, appreciative, apprehension, apprehensive, apprehensively, ardency, ardors, ardours, ashamed, astonishes, averseness, aversion, awe, awed, awestruck, bemoaned, blissful, brooding, cared, cares, chagrin, charmed, cherish ...
- **volition** (260): acquiesce, aims, ambitions, ask, asking, aspirations, aspired, attempts, beseeching, besought, chooses, chuse, chusing, compulsion, consent, consented, consenting, coveted, dare, dared, decides, decisions, defer, determining, eagerness, endeavored, endeavoring, entreated, forgo, hesitancy, hesitant, hesitate, hoped, indecision, insisted, insisting, intends, intentions, irresolute, irresolutely, irresolution, longed, longings, motivate, motivation, motives, need, persevere, prefer, preference, preferences, preferred, preferring, promptings, propension, proposing, purposed, purposes, purposing, refusal ...
- **perception** (78): clairvoyance, descry, discerned, espied, espy, espying, eying, feels, gazed, gazing, glimpses, looking, observed, observing, perceiv, perceptions, percipient, sensa, sensed, senses, stared, detecting, drowsily, drowsiness, drowsy, illusions, impressions, insensibility, sentient, visions, appear, attune, attuned, awake, awoke, clairvoyant, dazzle, dazzled, detect, discernible, doze, dozing, foretaste, giddy, glared, illusion, illusive, insensible, insensitive, look, looked, observers, painfully, reconnoitring, searchingly, seeming, sensible, sensorial, sensorium, sensory ...
- **attention** (63): adverted, attend, disregarding, distracts, distrait, fascinations, focussing, heedful, heedlessness, ignores, inattentive, intentness, mesmerized, minding, noting, scrutinize, scrutinizing, tedium, unheeding, unmindful, watchfulness, absorbed, concentred, disregarded, regardful, terested, unobservant, vacantly, vigilancy, vigilantly, absorbing, absorbs, advert, careful, carefully, carelessness, concentrated, divert, diverting, engaged, fixedly, heedless, heedlessly, inadvertence, inadvertency, inadvertent, inadvertently, incurious, interests, neglect, neglected, neglectful, overlook, overlooked, responsive, scrutinised, studiously, tediously, unguardedly, unregarded ...
- **mixed** (70): approve, beware, covetous, foreboded, inquisitively, listlessness, meant, nightmares, persuading, quisitive, reticence, suffer, tranced, wariness, wearies, whimsies, wonderingly, approving, expectant, incouraged, instincts, reluaance, allow, allured, askance, assuring, awaked, awaking, bewddered, bewitched, bigoted, compelling, compulsive, concealing, conspire, curiously, defign, designing, disowning, dulness, earnest, engage, examines, exploring, greedy, impetuously, impresses, indolence, induce, keenness, mean, mysticism, overborne, persuade, perusal, perused, plotters, presumptuously, purblind, reconcile ...
