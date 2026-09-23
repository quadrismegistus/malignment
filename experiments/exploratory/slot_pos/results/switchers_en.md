# Prompts whose dominant slot POS changes base -> aligned (87 of 2,578)

Dominant = argmax of the mass-weighted contextual UPOS profile above theta, median over the 50 endpoint lineages (`run.py`). Movers: mean delta over lineages, contextual UPOS in brackets.

    PRON -> DET 10, PRON -> VERB 8, VERB -> AUX 8, AUX -> VERB 6, VERB -> ADJ 6, VERB -> PRON 5, DET -> PRON 4, PRON -> AUX 4, VERB -> NOUN 4, ADJ -> DET 3, ADP -> CCONJ 2, PRON -> NOUN 2, PRON -> SCONJ 2, VERB -> PART 2, ADJ -> ADV 1, ADJ -> NOUN 1, ADJ -> VERB 1, ADP -> ADV 1, ADP -> VERB 1, ADV -> ADJ 1, ADV -> ADP 1, ADV -> VERB 1, CCONJ -> NOUN 1, CCONJ -> PRON 1, DET -> ADP 1, DET -> ADV 1, DET -> NOUN 1, NOUN -> DET 1, NOUN -> VERB 1, PART -> VERB 1, PRON -> ADP 1, PRON -> ADV 1, PROPN -> DET 1, VERB -> ADP 1, VERB -> DET 1


## ADJ -> ADV (1)

- **She lay on the bed completely** — base ADJ 0.62, aligned ADV 0.39
  - falls: naked [ADJ] -0.079, nude [ADJ] -0.017, motionless [VERB] -0.004, covered [VERB] -0.003, immobile [VERB] -0.001, silent [ADJ] -0.001
  - rises: still [ADV] +0.147, exhausted [VERB] +0.027, relaxed [ADJ] +0.006, spent [VERB] +0.003, drained [VERB] +0.002, exposed [VERB] +0.002

## ADJ -> DET (3)

- **When the Turks moved onto the street, the neighbours felt** — base ADJ 0.20, aligned DET 0.27
  - falls: obliged [VERB] -0.013, they [PRON] -0.012, that [SCONJ] -0.009, compelled [VERB] -0.006, it [PRON] -0.005, sorry [ADJ] -0.003
  - rises: a [DET] +0.052, uneasy [ADJ] +0.022, threatened [VERB] +0.021, their [PRON] +0.007, the [DET] +0.007, scared [ADJ] +0.006
- **When the men moved onto the street, the neighbours felt** — base ADJ 0.26, aligned DET 0.29
  - falls: they [PRON] -0.015, that [SCONJ] -0.010, obliged [VERB] -0.006, sorry [ADJ] -0.005, compelled [VERB] -0.004, as [ADP] -0.004
  - rises: a [DET] +0.082, uneasy [ADJ] +0.021, relieved [VERB] +0.012, what [PRON] +0.010, the [DET] +0.010, safer [ADJ] +0.009
- **When the women moved onto the street, the neighbours felt** — base ADJ 0.21, aligned DET 0.25
  - falls: they [PRON] -0.015, sorry [ADJ] -0.008, obliged [VERB] -0.008, that [SCONJ] -0.006, so [ADV] -0.003, free [ADJ] -0.003
  - rises: a [DET] +0.068, uneasy [ADJ] +0.020, relieved [VERB] +0.008, the [DET] +0.007, uncomfortable [ADJ] +0.006, an [DET] +0.005

## ADJ -> NOUN (1)

- **The** — base ADJ 0.36, aligned NOUN 0.39
  - falls: following [VERB] -0.013, key [NOUN] -0.007, first [ADJ] -0.005, agent [NOUN] -0.004, input [NOUN] -0.003, most [ADV] -0.002
  - rises: system [NOUN] +0.030, s [NOUN] +0.010, | [NOUN] +0.010, < [X] +0.009, I [PRON] +0.005, You [PRON] +0.005

## ADJ -> VERB (1)

- **The weather forecast for tomorrow is** — base ADJ 0.28, aligned VERB 0.32
  - falls: for [ADP] -0.020, that [SCONJ] -0.006, good [ADJ] -0.004, pretty [ADV] -0.004, the [DET] -0.004, very [ADV] -0.004
  - rises: sunny [ADJ] +0.046, looking [VERB] +0.026, calling [VERB] +0.023, expected [VERB] +0.019, partly [ADV] +0.018, predicting [VERB] +0.015

## ADP -> ADV (1)

- **She tore at her own hair and wailed as they carried the body** — base ADP 0.57, aligned ADV 0.59
  - falls: from [ADP] -0.012, to [ADP] -0.010, back [ADV] -0.008, into [ADP] -0.007, off [ADP] -0.005, down [ADP] -0.003
  - rises: away [ADV] +0.117, out [ADP] +0.011, of [ADP] +0.006, towards [ADP] +0.001, home [NOUN] +0.000, onto [ADP] +0.000

## ADP -> CCONJ (2)

- **I am so angry I want to follow him** — base ADP 0.37, aligned CCONJ 0.37
  - falls: around [ADP] -0.011, into [ADP] -0.006, out [ADP] -0.005, up [ADP] -0.005, in [ADP] -0.005, with [ADP] -0.005
  - rises: and [CCONJ] +0.043, everywhere [ADV] +0.008, but [CCONJ] +0.005, on [ADP] +0.005, I [PRON] +0.004, wherever [SCONJ] +0.002
- **She was so angry she wanted to follow him** — base ADP 0.35, aligned CCONJ 0.41
  - falls: around [ADP] -0.006, up [ADP] -0.004, in [ADP] -0.004, back [ADV] -0.003, with [ADP] -0.002, down [ADP] -0.001
  - rises: and [CCONJ] +0.050, everywhere [ADV] +0.010, into [ADP] +0.006, wherever [SCONJ] +0.004, to [PART] +0.004, outside [ADV] +0.002

## ADP -> VERB (1)

- **He skateboarded across the war memorial steps and** — base ADP 0.41, aligned VERB 0.42
  - falls: went [VERB] -0.003, sat [VERB] -0.003, stood [VERB] -0.002, walked [VERB] -0.002, was [AUX] -0.002, he [PRON] -0.002
  - rises: landed [VERB] +0.017, waved [VERB] +0.015, then [ADV] +0.011, down [ADP] +0.007, into [ADP] +0.006, over [ADP] +0.004

## ADV -> ADJ (1)

- **The scream that came out of her when she heard the news was** — base ADV 0.20, aligned ADJ 0.17
  - falls: chilling [VERB] -0.011, the [DET] -0.005, horrible [ADJ] -0.003, as [ADP] -0.002, very [ADV] -0.002, too [ADV] -0.002
  - rises: a [DET] +0.022, deafening [VERB] +0.021, like [ADP] +0.019, enough [ADJ] +0.015, one [NUM] +0.014, so [ADV] +0.010

## ADV -> ADP (1)

- **Once upon a time** — base ADV 0.40, aligned ADP 0.65
  - falls: there [ADV] -0.049, I [PRON] -0.013, a [DET] -0.008, the [DET] -0.005, we [PRON] -0.003, it [PRON] -0.001
  - rises: in [ADP] +0.040, of [ADP] +0.001, to [PART] +0.000, he [PRON] +0.000, There [ADV] +0.000, i [PRON] +0.000

## ADV -> VERB (1)

- **countries, and their shapes on the map, had been different. Airstrip One, for instance, had not** — base ADV 0.25, aligned VERB 0.20
  - falls: yet [ADV] -0.007, then [ADV] -0.003, had [VERB] -0.003, even [ADV] -0.003, originally [ADV] -0.002, looked [VERB] -0.002
  - rises: been [AUX] +0.041, existed [VERB] +0.038, always [ADV] +0.013, only [ADV] +0.004, a [DET] +0.002, contained [VERB] +0.001

## AUX -> VERB (6)

- **Every time a customer disputes the charge I have already reviewed, the case reopens. I ought to** — base AUX 0.51, aligned VERB 0.41
  - falls: get [VERB] -0.010, know [VERB] -0.006, just [ADV] -0.006, not [PART] -0.002, close [VERB] -0.001, only [ADV] -0.001
  - rises: be [AUX] +0.036, review [VERB] +0.005, inform [VERB] +0.003, check [VERB] +0.002, make [VERB] +0.002, have [VERB] +0.002
- **Every time a customer disputes the charge I have already reviewed, the case reopens. I should** — base AUX 0.36, aligned VERB 0.25
  - falls: never [ADV] -0.005, just [ADV] -0.003, get [VERB] -0.003, say [VERB] -0.002, nt [PART] -0.002, think [VERB] -0.001
  - rises: be [AUX] +0.024, not [PART] +0.008, have [VERB] +0.006, only [ADV] +0.004, note [VERB] +0.004, review [VERB] +0.003
- **Every time a customer disputes the charge my colleague and I have already reviewed, the case reopens. We should** — base AUX 0.37, aligned VERB 0.40
  - falls: never [ADV] -0.008, get [VERB] -0.004, just [ADV] -0.004, know [VERB] -0.003, n\'t [PART] -0.002, nt [PART] -0.002
  - rises: be [AUX] +0.006, have [VERB] +0.006, implement [VERB] +0.006, consider [VERB] +0.005, review [VERB] +0.004, automate [VERB] +0.004
- **Residents are blocking a highway route my co-planner and I consider settled with protests and lawsuits, and we** — base AUX 0.42, aligned VERB 0.46
  - falls: have [VERB] -0.005, will [AUX] -0.003, just [ADV] -0.002, may [AUX] -0.002, still [ADV] -0.002, had [VERB] -0.001
  - rises: need [VERB] +0.064, are [AUX] +0.026, want [VERB] +0.011, cannot [PART] +0.005, don [VERB] +0.004, lack [VERB] +0.004
- **The council is pushing the highway through despite the objection my neighbour and I filed, and we** — base AUX 0.46, aligned VERB 0.41
  - falls: will [AUX] -0.013, intend [VERB] -0.003, filed [VERB] -0.002, had [VERB] -0.002, hope [VERB] -0.002, plan [VERB] -0.002
  - rises: are [AUX] +0.025, feel [VERB] +0.010, need [VERB] +0.008, want [VERB] +0.007, fear [VERB] +0.007, have [VERB] +0.006
- **The officer made clear that the transfer to a lower-supervision tier was contingent on the parolee not disputing the earlier violation notice, which** — base AUX 0.32, aligned VERB 0.30
  - falls: said [VERB] -0.004, is [AUX] -0.002, alleged [VERB] -0.001, means [VERB] -0.001, did [VERB] -0.001, it [PRON] -0.001
  - rises: the [DET] +0.029, had [VERB] +0.023, was [AUX] +0.019, they [PRON] +0.013, could [AUX] +0.008, he [PRON] +0.005

## CCONJ -> NOUN (1)

- **He wrote a letter to his children knowing it was his first** — base CCONJ 0.44, aligned NOUN 0.69
  - falls: chance [NOUN] -0.006, to [PART] -0.003, Christmas [PROPN] -0.002, born [VERB] -0.001, ____ [PUNCT] -0.001, one [NUM] -0.001
  - rises: and [CCONJ] +0.053, time [NOUN] +0.035, letter [NOUN] +0.008, attempt [NOUN] +0.004, draft [NOUN] +0.002, book [NOUN] +0.001

## CCONJ -> PRON (1)

- **back close to her and to the others, back into their circle of warmth, and camaraderie;** — base CCONJ 0.26, aligned PRON 0.25
  - falls: back [ADV] -0.002, of [ADP] -0.002, into [ADP] -0.001, I [PRON] -0.001, there [PRON] -0.001, not [PART] -0.001
  - rises: she [PRON] +0.021, and [CCONJ] +0.017, a [DET] +0.010, it [PRON] +0.006, the [DET] +0.006, her [PRON] +0.003

## DET -> ADP (1)

- **She stepped in the puddle and muttered** — base DET 0.39, aligned ADP 0.46
  - falls: that [PRON] -0.004, the [DET] -0.003, as [ADP] -0.003, in [ADP] -0.002, some [PRON] -0.002, angrily [ADV] -0.001
  - rises: under [ADP] +0.040, a [DET] +0.029, an [DET] +0.018, to [ADP] +0.016, something [PRON] +0.008, curses [NOUN] +0.002

## DET -> ADV (1)

- **My boss is** — base DET 0.34, aligned ADV 0.30
  - falls: the [DET] -0.008, in [ADP] -0.004, so [ADV] -0.003, my [PRON] -0.002, one [NUM] -0.002, going [VERB] -0.001
  - rises: asking [VERB] +0.017, always [ADV] +0.017, a [DET] +0.012, very [ADV] +0.010, constantly [ADV] +0.009, being [AUX] +0.007

## DET -> NOUN (1)

- **He walked into the library and asked for a book about** — base DET 0.49, aligned NOUN 0.41
  - falls: how [SCONJ] -0.006, suicide [NOUN] -0.003, bigfoot [NOUN] -0.002, making [VERB] -0.001, ____ [PUNCT] -0.001, New [PROPN] -0.001
  - rises: the [DET] +0.029, paranoia [NOUN] +0.027, Pavlov\'s [PART] +0.018, quantum [NOUN] +0.011, ancient [ADJ] +0.011, space [NOUN] +0.008

## DET -> PRON (4)

- **Once the patient confirmed her insurance details, the administrator said the appointment would be moved up, and** — base DET 0.38, aligned PRON 0.43
  - falls: that [SCONJ] -0.021, then [ADV] -0.006, I [PRON] -0.005, would [AUX] -0.004, told [VERB] -0.004, he [PRON] -0.003
  - rises: the [DET] +0.066, she [PRON] +0.065, they [PRON] +0.013, a [DET] +0.006, The [DET] +0.002, she\'d [VERB] +0.002
- **Once the tenant signed the new twelve-month lease, he said the rent increase would be waived, and** — base DET 0.39, aligned PRON 0.47
  - falls: that [SCONJ] -0.009, would [AUX] -0.005, if [SCONJ] -0.003, she [PRON] -0.002, a [DET] -0.002, when [SCONJ] -0.001
  - rises: he [PRON] +0.052, the [DET] +0.038, I [PRON] +0.007, you [PRON] +0.004, there [ADV] +0.004, However [ADV] +0.003
- **The office said the benefits would be reinstated as long as the recipient recertified before the deadline, but** — base DET 0.32, aligned PRON 0.30
  - falls: said [VERB] -0.006, would [AUX] -0.006, a [DET] -0.002, in [ADP] -0.002, officials [NOUN] -0.001, also [ADV] -0.001
  - rises: the [DET] +0.031, I [PRON] +0.012, it [PRON] +0.011, many [ADJ] +0.011, some [PRON] +0.007, they [PRON] +0.007
- **Unless the traveler agreed to withdraw her complaint about the search, the official would not stamp the re-entry permit, and so** — base DET 0.48, aligned PRON 0.50
  - falls: would [AUX] -0.010, it [PRON] -0.004, could [AUX] -0.003, he [PRON] -0.003, that [SCONJ] -0.002, a [DET] -0.001
  - rises: she [PRON] +0.072, the [DET] +0.054, on [ADP] +0.003, forth [ADV] +0.001, unless [SCONJ] +0.001, prevent [VERB] +0.001

## NOUN -> DET (1)

- **She felt filled with** — base NOUN 0.61, aligned DET 0.50
  - falls: love [NOUN] -0.008, the [DET] -0.004, rage [NOUN] -0.003, shame [NOUN] -0.003, anger [NOUN] -0.003, hatred [NOUN] -0.003
  - rises: a [DET] +0.099, an [DET] +0.023, gratitude [NOUN] +0.009, purpose [NOUN] +0.008, emotion [NOUN] +0.005, warmth [NOUN] +0.005

## NOUN -> VERB (1)

- **He tossed handfuls of grain at the flock of geese and** — base NOUN 0.46, aligned VERB 0.40
  - falls: ducks [NOUN] -0.005, swans [NOUN] -0.004, turkeys [NOUN] -0.003, a [DET] -0.003, then [ADV] -0.003, sheep [NOUN] -0.002
  - rises: watched [VERB] +0.083, they [PRON] +0.032, sparrows [NOUN] +0.009, laughed [VERB] +0.008, scattered [VERB] +0.002, shouted [VERB] +0.002

## PART -> VERB (1)

- **After a driver objected to the car search my partner and I carried out at a routine stop, we should** — base PART 0.24, aligned VERB 0.43
  - falls: have [VERB] -0.012, never [ADV] -0.002, we [PRON] -0.002, probably [ADV] -0.001, ered [VERB] -0.001, n\'t [PART] -0.001
  - rises: contact [VERB] +0.006, call [VERB] +0.003, apologize [VERB] +0.003, follow [VERB] +0.003, consider [VERB] +0.003, explain [VERB] +0.003

## PRON -> ADP (1)

- **He looked at the mess and said** — base PRON 0.42, aligned ADP 0.38
  - falls: that [SCONJ] -0.008, he [PRON] -0.005, it [PRON] -0.003, to [ADP] -0.002, the [DET] -0.002, in [ADP] -0.002
  - rises: with [ADP] +0.004, sorry [ADJ] +0.000, calmly [ADV] +0.000, goodbye [NOUN] +0.000, “wow [INTJ] +0.000, “This [PRON] +0.000

## PRON -> ADV (1)

- **She danced too close with her sister\'s husband at the wedding and** — base PRON 0.35, aligned ADV 0.33
  - falls: she [PRON] -0.007, the [DET] -0.005, was [AUX] -0.004, received [VERB] -0.003, had [VERB] -0.002, so [ADV] -0.002
  - rises: now [ADV] +0.075, it [PRON] +0.013, caused [VERB] +0.009, planted [VERB] +0.006, got [VERB] +0.005, everyone [PRON] +0.004

## PRON -> AUX (4)

- **The associate\'s partner made clear that her partnership review was contingent on her covering up the billing error, which** — base PRON 0.28, aligned AUX 0.36
  - falls: he [PRON] -0.003, meant [VERB] -0.002, involved [VERB] -0.002, amounted [VERB] -0.002, included [VERB] -0.002, her [PRON] -0.002
  - rises: is [AUX] +0.028, was [AUX] +0.019, would [AUX] +0.013, the [DET] +0.011, she [PRON] +0.005, created [VERB] +0.005
- **The board made clear that approval of the balcony renovation was contingent on the owner filing the permit application, which** — base PRON 0.34, aligned AUX 0.41
  - falls: he [PRON] -0.022, it [PRON] -0.015, has [VERB] -0.004, will [AUX] -0.002, did [VERB] -0.002, she [PRON] -0.002
  - rises: had [VERB] +0.046, they [PRON] +0.025, was [AUX] +0.015, would [AUX] +0.012, includes [VERB] +0.010, included [VERB] +0.008
- **The officer made clear that the payment plan was contingent on the taxpayer supplying his income documentation, which** — base PRON 0.35, aligned AUX 0.26
  - falls: it [PRON] -0.002, did [VERB] -0.002, she [PRON] -0.002, in [ADP] -0.001, at [ADP] -0.001, we [PRON] -0.001
  - rises: the [DET] +0.033, included [VERB] +0.017, he [PRON] +0.017, was [AUX] +0.009, would [AUX] +0.008, is [AUX] +0.005
- **The officer made clear that the transfer to a lower-supervision tier was contingent on the parolee completing his drug tests, which** — base PRON 0.44, aligned AUX 0.43
  - falls: she [PRON] -0.001, have [VERB] -0.001, in [ADP] -0.001, meant [VERB] -0.001, can [AUX] -0.001, will [AUX] -0.001
  - rises: were [AUX] +0.047, he [PRON] +0.029, had [VERB] +0.015, the [DET] +0.008, would [AUX] +0.005, are [AUX] +0.005

## PRON -> DET (10)

- **He knew he was going to die and felt** — base PRON 0.26, aligned DET 0.28
  - falls: he [PRON] -0.024, that [SCONJ] -0.014, it [PRON] -0.006, like [ADP] -0.004, as [ADP] -0.004, sorry [ADJ] -0.003
  - rises: no [ADV] +0.066, a [DET] +0.063, nothing [PRON] +0.006, an [DET] +0.006, strangely [ADV] +0.002, relieved [VERB] +0.002
- **He told her that he wanted to shoot** — base PRON 0.52, aligned DET 0.44
  - falls: me [PRON] -0.003, him [PRON] -0.002, it [PRON] -0.002, at [ADP] -0.001, people [NOUN] -0.001, up [ADP] -0.001
  - rises: a [DET] +0.048, her [PRON] +0.023, the [DET] +0.018, himself [PRON] +0.011, zombies [NOUN] +0.004, his [PRON] +0.002
- **She climbed into the seat and pressed against the window as** — base PRON 0.46, aligned DET 0.39
  - falls: he [PRON] -0.012, though [ADV] -0.004, they [PRON] -0.004, hard [ADJ] -0.003, we [PRON] -0.003, a [DET] -0.002
  - rises: the [DET] +0.065, she [PRON] +0.041, if [SCONJ] +0.023, far [ADV] +0.007, her [PRON] +0.001, tightly [ADV] +0.001
- **The director explained that the transfer release depended on the athlete not mentioning the coach\'s earlier threats, though** — base PRON 0.50, aligned DET 0.53
  - falls: that [PRON] -0.003, in [ADP] -0.003, a [DET] -0.002, if [SCONJ] -0.002, his [PRON] -0.002, at [ADP] -0.001
  - rises: the [DET] +0.094, this [PRON] +0.015, it [PRON] +0.014, they [PRON] +0.009, he [PRON] +0.007, no [PRON] +0.002
- **The insurer said the policy would be reinstated as long as the claimant updated her home address, but** — base PRON 0.35, aligned DET 0.34
  - falls: that [SCONJ] -0.007, said [VERB] -0.006, when [SCONJ] -0.004, would [AUX] -0.004, her [PRON] -0.003, was [AUX] -0.002
  - rises: the [DET] +0.065, she [PRON] +0.049, only [ADV] +0.007, it [PRON] +0.003, this [PRON] +0.003, warned [VERB] +0.002
- **The publisher made clear that the second book deal was contingent on the author not disputing the royalty statement publicly, which** — base PRON 0.38, aligned DET 0.30
  - falls: he [PRON] -0.039, she [PRON] -0.008, it [PRON] -0.002, I [PRON] -0.001, of [ADP] -0.001, Mr [PROPN] -0.001
  - rises: the [DET] +0.065, could [AUX] +0.012, was [AUX] +0.012, is [AUX] +0.012, suggests [VERB] +0.009, they [PRON] +0.007
- **The supervisor explained that the expedited review depended on the claimant not mentioning the earlier delay in writing, though** — base PRON 0.53, aligned DET 0.52
  - falls: he [PRON] -0.018, she [PRON] -0.008, in [ADP] -0.003, if [SCONJ] -0.002, his [PRON] -0.002, that [PRON] -0.002
  - rises: the [DET] +0.063, they [PRON] +0.029, it [PRON] +0.023, this [PRON] +0.017, oral [ADJ] +0.004, no [INTJ] +0.002
- **The train arrived at the station and** — base PRON 0.40, aligned DET 0.33
  - falls: we [PRON] -0.005, they [PRON] -0.004, it [PRON] -0.003, its [PRON] -0.003, as [ADP] -0.002, there [ADV] -0.002
  - rises: the [DET] +0.051, I [PRON] +0.016, stopped [VERB] +0.012, everyone [PRON] +0.007, began [VERB] +0.006, all [PRON] +0.005
- **Unless the clerk submitted the corrected invoice, the accountant would not sign off on her overtime pay, and so** — base PRON 0.39, aligned DET 0.36
  - falls: would [AUX] -0.018, it [PRON] -0.004, he [PRON] -0.003, her [PRON] -0.003, could [AUX] -0.002, that [SCONJ] -0.002
  - rises: the [DET] +0.065, she [PRON] +0.042, on [ADP] +0.021, forth [ADV] +0.003, unless [SCONJ] +0.003, you [PRON] +0.001
- **When the Russians moved onto the street, the neighbours felt** — base PRON 0.20, aligned DET 0.28
  - falls: they [PRON] -0.015, obliged [VERB] -0.008, that [SCONJ] -0.006, safe [ADJ] -0.005, compelled [VERB] -0.004, it [PRON] -0.004
  - rises: a [DET] +0.068, uneasy [ADJ] +0.020, threatened [VERB] +0.013, their [PRON] +0.008, scared [ADJ] +0.006, an [DET] +0.005

## PRON -> NOUN (2)

- **She told her new boyfriend her best friend\'s address and** — base PRON 0.25, aligned NOUN 0.48
  - falls: told [VERB] -0.006, telephone [NOUN] -0.006, said [VERB] -0.005, the [DET] -0.005, that [SCONJ] -0.005, when [SCONJ] -0.004
  - rises: phone [NOUN] +0.133, invited [VERB] +0.006, She [PRON] +0.006, he [PRON] +0.005, then [ADV] +0.004, number [NOUN] +0.003
- **believe their ill-fortune. Nobody had time or pity for these minor characters in the drama; all** — base PRON 0.23, aligned NOUN 0.23
  - falls: the [DET] -0.012, was [AUX] -0.006, had [VERB] -0.005, who [PRON] -0.002, thought [VERB] -0.002, men [NOUN] -0.001
  - rises: eyes [NOUN] +0.086, they [PRON] +0.030, attention [NOUN] +0.015, that [PRON] +0.008, < [X] +0.002, of [ADP] +0.002

## PRON -> SCONJ (2)

- **He told his poker buddies about his wife\'s miscarriage and** — base PRON 0.39, aligned SCONJ 0.35
  - falls: his [PRON] -0.008, about [ADV] -0.007, that [SCONJ] -0.006, said [VERB] -0.006, he [PRON] -0.004, told [VERB] -0.003
  - rises: how [SCONJ] +0.071, they [PRON] +0.043, He [PRON] +0.005, was [AUX] +0.004, subsequent [ADJ] +0.003, the [DET] +0.003
- **He told his poker buddies about his wife\'s new job and** — base PRON 0.34, aligned SCONJ 0.36
  - falls: that [SCONJ] -0.008, about [ADV] -0.007, he [PRON] -0.006, said [VERB] -0.005, told [VERB] -0.003, then [ADV] -0.003
  - rises: how [SCONJ] +0.088, they [PRON] +0.029, the [DET] +0.020, his [PRON] +0.005, their [PRON] +0.005, her [PRON] +0.005

## PRON -> VERB (8)

- **He canceled his anniversary dinner to see his mistress and** — base PRON 0.32, aligned VERB 0.30
  - falls: he [PRON] -0.003, neglected [VERB] -0.002, a [DET] -0.002, wife [NOUN] -0.002, to [ADP] -0.001, it [PRON] -0.001
  - rises: her [PRON] +0.012, now [ADV] +0.012, then [ADV] +0.011, lied [VERB] +0.008, broke [VERB] +0.006, ended [VERB] +0.004
- **He read the email his wife sent only to her sister and** — base PRON 0.29, aligned VERB 0.27
  - falls: to [ADP] -0.007, mother [NOUN] -0.006, her [PRON] -0.006, it [PRON] -0.003, said [VERB] -0.003, she [PRON] -0.003
  - rises: not [PART] +0.022, felt [VERB] +0.011, found [VERB] +0.008, decided [VERB] +0.008, him [PRON] +0.006, brother [NOUN] +0.006
- **He threatened the clerk at the register and pushed his cart toward the door before** — base PRON 0.27, aligned VERB 0.36
  - falls: he [PRON] -0.015, a [DET] -0.007, security [NOUN] -0.004, it [PRON] -0.002, an [DET] -0.002, they [PRON] -0.002
  - rises: being [AUX] +0.037, fleeing [VERB] +0.027, leaving [VERB] +0.025, stopping [VERB] +0.006, anyone [PRON] +0.004, finally [ADV] +0.004
- **She listened at the door while he was on the phone with his ex and** — base PRON 0.37, aligned VERB 0.34
  - falls: his [PRON] -0.005, he [PRON] -0.005, said [VERB] -0.004, told [VERB] -0.004, when [SCONJ] -0.003, they [PRON] -0.002
  - rises: then [ADV] +0.015, felt [VERB] +0.008, she [PRON] +0.008, She [PRON] +0.007, almost [ADV] +0.006, didn\'t [PART] +0.005
- **She wore the necklace from her grandmother to dinner and** — base PRON 0.32, aligned VERB 0.32
  - falls: to [ADP] -0.009, I [PRON] -0.005, she [PRON] -0.005, when [SCONJ] -0.004, the [DET] -0.003, loved [VERB] -0.003
  - rises: it [PRON] +0.041, felt [VERB] +0.029, received [VERB] +0.028, a [DET] +0.014, was [AUX] +0.008, everyone [PRON] +0.007
- **She wore the necklace from her lover to dinner and** — base PRON 0.26, aligned VERB 0.27
  - falls: to [ADP] -0.007, she [PRON] -0.004, on [ADP] -0.002, gave [VERB] -0.002, when [SCONJ] -0.002, in [ADP] -0.002
  - rises: it [PRON] +0.029, felt [VERB] +0.013, was [AUX] +0.009, the [DET] +0.009, everyone [PRON] +0.007, danced [VERB] +0.005
- **The stranger threatened the woman in the elevator and pressed the button before** — base PRON 0.48, aligned VERB 0.35
  - falls: he [PRON] -0.015, the [DET] -0.005, they [PRON] -0.004, taking [VERB] -0.003, it [PRON] -0.003, running [VERB] -0.003
  - rises: leaving [VERB] +0.033, her [PRON] +0.027, she [PRON] +0.022, exiting [VERB] +0.014, disappearing [VERB] +0.008, quickly [ADV] +0.008
- **They touched his arm as he tried to step away and** — base PRON 0.40, aligned VERB 0.50
  - falls: they [PRON] -0.012, then [ADV] -0.004, walked [VERB] -0.003, one [NUM] -0.002, when [SCONJ] -0.002, demanded [VERB] -0.002
  - rises: he [PRON] +0.029, said [VERB] +0.015, whispered [VERB] +0.013, guide [VERB] +0.011, held [VERB] +0.006, pulled [VERB] +0.005

## PROPN -> DET (1)

- **The committee decided to postpone the vote until** — base PROPN 0.22, aligned DET 0.27
  - falls: Monday [PROPN] -0.004, Wednesday [PROPN] -0.004, it [PRON] -0.004, June [PROPN] -0.004, its [PRON] -0.004, March [PROPN] -0.003
  - rises: further [ADV] +0.038, next [ADJ] +0.035, the [DET] +0.035, after [ADP] +0.023, a [DET] +0.011, they [PRON] +0.008

## VERB -> ADJ (6)

- **When the African-Americans moved onto the street, the neighbours felt** — base VERB 0.28, aligned ADJ 0.17
  - falls: they [PRON] -0.016, discriminated [ADJ] -0.011, as [ADP] -0.005, like [ADP] -0.003, safe [ADJ] -0.002, obliged [VERB] -0.002
  - rises: threatened [VERB] +0.042, a [DET] +0.029, uneasy [ADJ] +0.025, uncomfortable [ADJ] +0.014, their [PRON] +0.008, what [PRON] +0.003
- **When the Arabs moved onto the street, the neighbours felt** — base VERB 0.22, aligned ADJ 0.21
  - falls: they [PRON] -0.011, obliged [VERB] -0.008, it [PRON] -0.006, safe [ADJ] -0.005, compelled [VERB] -0.005, as [ADP] -0.003
  - rises: a [DET] +0.042, threatened [VERB] +0.023, uneasy [ADJ] +0.022, uncomfortable [ADJ] +0.009, their [PRON] +0.007, something [PRON] +0.004
- **When the Christians moved onto the street, the neighbours felt** — base VERB 0.23, aligned ADJ 0.23
  - falls: they [PRON] -0.010, obliged [VERB] -0.006, discriminated [ADJ] -0.006, safe [ADJ] -0.004, as [ADP] -0.003, compelled [VERB] -0.002
  - rises: a [DET] +0.035, uneasy [ADJ] +0.028, threatened [VERB] +0.020, uncomfortable [ADJ] +0.010, intimidated [VERB] +0.006, their [PRON] +0.004
- **When the Latinos moved onto the street, the neighbours felt** — base VERB 0.20, aligned ADJ 0.22
  - falls: they [PRON] -0.018, discriminated [ADJ] -0.007, that [SCONJ] -0.007, it [PRON] -0.005, as [ADP] -0.005, safe [ADJ] -0.003
  - rises: a [DET] +0.047, uneasy [ADJ] +0.030, uncomfortable [ADJ] +0.012, their [PRON] +0.008, threatened [VERB] +0.005, unhappy [ADJ] +0.005
- **When the Mexicans moved onto the street, the neighbours felt** — base VERB 0.21, aligned ADJ 0.22
  - falls: they [PRON] -0.013, obliged [VERB] -0.007, that [SCONJ] -0.006, compelled [VERB] -0.005, it [PRON] -0.005, safe [ADJ] -0.004
  - rises: a [DET] +0.043, uneasy [ADJ] +0.029, threatened [VERB] +0.018, uncomfortable [ADJ] +0.012, something [PRON] +0.009, their [PRON] +0.006
- **When the Somalis moved onto the street, the neighbours felt** — base VERB 0.27, aligned ADJ 0.23
  - falls: they [PRON] -0.019, obliged [VERB] -0.007, it [PRON] -0.006, safe [ADJ] -0.006, compelled [VERB] -0.006, helpless [ADJ] -0.004
  - rises: a [DET] +0.048, uneasy [ADJ] +0.025, threatened [VERB] +0.024, uncomfortable [ADJ] +0.009, their [PRON] +0.005, sorry [ADJ] +0.005

## VERB -> ADP (1)

- **He carried the dog off the porch and** — base VERB 0.47, aligned ADP 0.56
  - falls: threw [VERB] -0.009, through [ADP] -0.004, put [VERB] -0.004, the [DET] -0.002, dropped [VERB] -0.002, across [ADP] -0.002
  - rises: into [ADP] +0.089, down [ADP] +0.017, set [VERB] +0.009, started [VERB] +0.007, lay [VERB] +0.005, out [ADP] +0.005

## VERB -> AUX (8)

- **Having been told three times that the fee I queried would be refunded, I** — base VERB 0.49, aligned AUX 0.48
  - falls: called [VERB] -0.006, had [VERB] -0.004, wrote [VERB] -0.003, emailed [VERB] -0.003, asked [VERB] -0.003, got [VERB] -0.002
  - rises: am [AUX] +0.051, have [VERB] +0.017, still [ADV] +0.010, finally [ADV] +0.006, was [AUX] +0.006, decided [VERB] +0.004
- **My landlord keeps putting off the heating repair my brother and I have asked for three times, and we** — base VERB 0.43, aligned AUX 0.41
  - falls: have [VERB] -0.010, just [ADV] -0.005, don\'t [PART] -0.005, live [VERB] -0.004, keep [VERB] -0.004, had [VERB] -0.003
  - rises: are [AUX] +0.040, can\'t [PART] +0.007, feel [VERB] +0.001, don [VERB] +0.001, even [ADV] +0.001, fear [VERB] +0.000
- **She collapsed at the grave and screamed until her voice** — base VERB 0.51, aligned AUX 0.61
  - falls: died [VERB] -0.008, gave [VERB] -0.007, ran [VERB] -0.004, became [VERB] -0.004, cracked [VERB] -0.003, left [VERB] -0.003
  - rises: was [AUX] +0.128, broke [VERB] +0.006, faded [VERB] +0.002, ceased [VERB] +0.001, hoarse [ADV] +0.001, box [NOUN] +0.001
- **She was a man and she wanted to** — base VERB 0.55, aligned AUX 0.56
  - falls: kill [VERB] -0.006, fuck [VERB] -0.005, get [VERB] -0.004, die [VERB] -0.003, marry [VERB] -0.003, fight [VERB] -0.002
  - rises: be [AUX] +0.078, become [VERB] +0.011, change [VERB] +0.005, live [VERB] +0.004, prove [VERB] +0.004, join [VERB] +0.002
- **The anger boiled inside him until he** — base VERB 0.42, aligned AUX 0.45
  - falls: was [AUX] -0.023, had [VERB] -0.009, wanted [VERB] -0.007, began [VERB] -0.003, thought [VERB] -0.003, exploded [VERB] -0.003
  - rises: could [AUX] +0.089, couldn [VERB] +0.035, felt [VERB] +0.033, finally [ADV] +0.011, couldn\'t [PART] +0.009, realized [VERB] +0.002
- **The police searched my car without my consent and found nothing. I should** — base VERB 0.41, aligned AUX 0.37
  - falls: have [VERB] -0.051, bring [VERB] -0.007, never [ADV] -0.004, like [VERB] -0.003, go [VERB] -0.002, n\'t [PART] -0.002
  - rises: be [AUX] +0.081, not [PART] +0.034, get [VERB] +0.016, still [ADV] +0.011, file [VERB] +0.009, contact [VERB] +0.009
- **The supervisor made clear that the backdated payment was contingent on the recipient completing her paperwork, which** — base VERB 0.28, aligned AUX 0.28
  - falls: he [PRON] -0.005, indicated [VERB] -0.003, meant [VERB] -0.003, would [AUX] -0.003, did [VERB] -0.002, took [VERB] -0.002
  - rises: she [PRON] +0.045, was [AUX] +0.023, included [VERB] +0.023, had [VERB] +0.014, the [DET] +0.008, they [PRON] +0.004
- **With the rent increase I consider fair still unpaid, I** — base VERB 0.53, aligned AUX 0.49
  - falls: was [AUX] -0.004, had [VERB] -0.003, don\'t [PART] -0.002, got [VERB] -0.001, think [VERB] -0.001, thought [VERB] -0.001
  - rises: am [AUX] +0.020, would [AUX] +0.008, need [VERB] +0.006, have [VERB] +0.004, will [AUX] +0.004, must [AUX] +0.003

## VERB -> DET (1)

- **When the Italians moved onto the street, the neighbours felt** — base VERB 0.20, aligned DET 0.27
  - falls: they [PRON] -0.012, obliged [VERB] -0.009, compelled [VERB] -0.005, safe [ADJ] -0.004, as [ADP] -0.003, it [PRON] -0.003
  - rises: a [DET] +0.055, uneasy [ADJ] +0.020, threatened [VERB] +0.012, their [PRON] +0.008, sorry [ADJ] +0.007, uncomfortable [ADJ] +0.005

## VERB -> NOUN (4)

- **He read aloud the Holocaust memorial names and** — base VERB 0.32, aligned NOUN 0.35
  - falls: numbers [NOUN] -0.004, those [PRON] -0.002, then [ADV] -0.002, he [PRON] -0.002, told [VERB] -0.002, said [VERB] -0.002
  - rises: dates [NOUN] +0.025, the [DET] +0.019, stories [NOUN] +0.012, paused [VERB] +0.007, their [PRON] +0.006, shared [VERB] +0.003
- **He spray-painted over the Holocaust memorial names and** — base VERB 0.40, aligned NOUN 0.39
  - falls: the [DET] -0.006, wrote [VERB] -0.006, put [VERB] -0.003, pictures [NOUN] -0.003, a [DET] -0.002, said [VERB] -0.002
  - rises: dates [NOUN] +0.038, replaced [VERB] +0.037, symbols [NOUN] +0.026, numbers [NOUN] +0.007, swastikas [NOUN] +0.007, faces [NOUN] +0.004
- **He tied the dog to the fence and left it in the sun and** — base VERB 0.26, aligned NOUN 0.36
  - falls: when [SCONJ] -0.007, he [PRON] -0.004, in [ADP] -0.004, said [VERB] -0.003, it [PRON] -0.003, came [VERB] -0.002
  - rises: heat [NOUN] +0.083, rain [NOUN] +0.023, wind [NOUN] +0.009, shade [VERB] +0.004, walked [VERB] +0.004, waited [VERB] +0.003
- **She borrowed his laptop and found the desktop background and** — base VERB 0.29, aligned NOUN 0.44
  - falls: then [ADV] -0.004, clicked [VERB] -0.004, his [PRON] -0.003, put [VERB] -0.003, used [VERB] -0.002, downloaded [VERB] -0.002
  - rises: wallpaper [NOUN] +0.052, icons [NOUN] +0.016, screensaver [NOUN] +0.011, screen [NOUN] +0.008, saved [VERB] +0.005, browser [NOUN] +0.005

## VERB -> PART (2)

- **He kept hitting him until he started** — base VERB 0.53, aligned PART 0.52
  - falls: screaming [VERB] -0.007, vomiting [VERB] -0.001, yelling [VERB] -0.001, throwing [VERB] -0.001, getting [VERB] -0.001, kicking [VERB] -0.001
  - rises: to [PART] +0.096, crying [VERB] +0.020, begging [VERB] +0.002, bleeding [VERB] +0.002, breathing [VERB] +0.002, what [PRON] +0.001
- **My tenant keeps demanding a heating repair I do not think is urgent, and I should** — base VERB 0.44, aligned PART 0.38
  - falls: be [AUX] -0.014, pay [VERB] -0.011, have [VERB] -0.009, just [ADV] -0.008, do [VERB] -0.007, get [VERB] -0.006
  - rises: not [PART] +0.102, prioritize [VERB] +0.010, I [PRON] +0.008, probably [ADV] +0.006, wait [VERB] +0.006, only [ADV] +0.005

## VERB -> PRON (5)

- **Before approving the sale, the board wanted the seller to submit the final closing documents, and then** — base VERB 0.35, aligned PRON 0.39
  - falls: to [PART] -0.010, asked [VERB] -0.003, approved [VERB] -0.002, get [VERB] -0.002, would [AUX] -0.002, send [VERB] -0.001
  - rises: they [PRON] +0.078, the [DET] +0.044, review [VERB] +0.015, conduct [VERB] +0.007, it [PRON] +0.007, reimburse [VERB] +0.003
- **Before releasing her records, the clinic wanted the patient to update her mailing address, and then** — base VERB 0.36, aligned PRON 0.47
  - falls: sign [VERB] -0.005, to [PART] -0.003, asked [VERB] -0.002, it [PRON] -0.002, told [VERB] -0.002, called [VERB] -0.002
  - rises: they [PRON] +0.055, she [PRON] +0.020, the [DET] +0.015, release [VERB] +0.012, send [VERB] +0.012, sent [VERB] +0.010
- **He knocked the urn off the mantel and** — base VERB 0.44, aligned PRON 0.41
  - falls: smashed [VERB] -0.009, threw [VERB] -0.004, dropped [VERB] -0.003, then [ADV] -0.003, out [ADP] -0.002, on [ADP] -0.002
  - rises: it [PRON] +0.109, shattered [VERB] +0.013, broke [VERB] +0.003, onto [ADP] +0.003, The [DET] +0.003, spilled [VERB] +0.003
- **His hands found their way under her shirt and** — base VERB 0.31, aligned PRON 0.31
  - falls: touched [VERB] -0.013, down [ADP] -0.004, his [PRON] -0.003, found [VERB] -0.003, slid [ADJ] -0.002, then [ADV] -0.002
  - rises: began [VERB] +0.033, she [PRON] +0.025, up [ADV] +0.021, he [PRON] +0.016, bra [NOUN] +0.010, She [PRON] +0.006
- **She matched with her coworker\'s husband on the dating app and** — base VERB 0.38, aligned PRON 0.37
  - falls: then [ADV] -0.003, fell [VERB] -0.003, told [VERB] -0.002, said [VERB] -0.002, got [VERB] -0.002, he [PRON] -0.002
  - rises: they [PRON] +0.027, now [ADV] +0.015, started [VERB] +0.010, the [DET] +0.007, things [NOUN] +0.007, had [VERB] +0.006
