# institutional: what alignment does to a grievance

**id:** slot_ratings/institutional **status:** three corpora rated, arm A and arm B, 2026-08-19.
Instrument `slot_institutional_en_v2`, frozen. Producers `run_m03.py`, `run_f21.py`, `run_slotpov.py`.

Rates a WORD IN ITS SLOT on eleven axes drawn from F21 and M03, then asks which words gain
probability under alignment. The unit of every test is the LINEAGE.

---

# 1. WHY THIS EXISTS: NOBODY HAS ANNOTATED A WORD IN ITS SLOT

    F21          unit = a whole generation      annotator = an LLM tagger, 12 dimensions
    M03 A        unit = a word TYPE             annotator = Warriner humans (valence/arousal)
    M03 E        unit = a word, NO annotation   pure next-word probability deltas
    k_ratings    unit = a word TYPE             annotator = deepseek, out of context
    THIS         unit = (prompt, word)          annotator = deepseek, IN CONTEXT

F21 has context but the unit is a generation, so it cannot say which word carried anything.
M03 A has word-level resolution but the values are type-level, so `phoned` scores the same
everywhere. M03 E has resolution and context implicitly but no semantic dimension at all --
it can say `assess` rose and `phoned` fell, and nothing about why.

# 2. THE THREE CORPORA, AND WHY THEY DISAGREE

    F21     24 prompts   RH-written. 12 symmetric role pairs (worker/mgmt, tenant/landlord,
                         citizen/agency, patient/doctor, citizen/officer, citizen/party).
                         Direct, material grievances. MIXED grammatical sites
                         ("I should", "We should", "I said").
    M03    252 prompts   Agent-written to a frame specification, 18 scenarios x 14 cells,
                         crossing position x person x modal. Site held fixed by construction.
                         Each scenario carries an `f21_anchor`: these are F21 REWRITTEN.
    SLOT    12 prompts   6 perspective pairs from `roster/prompts/slots/*.yaml` (`matched_set`
                         ending `_perspective`). Same event both sides, both ending at the
                         IDENTICAL site `so X decided to`. Short.

**The site matters more than the design does.** Measured on M03, changing the grammatical
site -- `I should ___` (bare infinitive) against `...and I ___` (finite verb) -- moves
`procedural` by **+0.221**, which is LARGER than the position contrast the whole design
exists to measure:

    site change      vocalisation +0.305   target +0.258   procedural +0.221
                     specificity +0.151    deference +0.141   agency +0.112
    one added word   `should` -> `should probably`:  deference +0.092, procedural +0.055,
                     arousal -0.041, and NOTHING ELSE moves

That second row is M03 finding A's hedge result on a different instrument: one word raises
deference by half the size of the entire position contrast and touches nothing else.

**And F21's prompts leave the model less decided.** Base entropy 3.599 bits against M03's
3.521, top-1 p_base 0.245 against 0.304, 15% more mass moved in two-thirds the words
(median 12 against 18). M03's relative clauses resolve the stance before the slot arrives
("a refusal I consider correct"); F21 states a predicament and resolves nothing.

# 3. WHAT REPLICATES: THE MAIN EFFECT

Unit = lineage (50 from `roster.endpoints()`; each is a distinct pretrained model, so no two
share a base). Statistic = rho(rating, mover verdict) within a lineage over its eligible
words, then Wilcoxon across lineages.

                    F21 (24 prompts)        M03 (18 scenarios)
    abstraction   +0.116  43/50  p=7e-10   +0.143  48/50  p=3e-13
    procedural    +0.082  42/50  p=6e-09   +0.125  44/50  p=7e-08
    deference     +0.037  37/50  p=3e-04   +0.066  42/50  p=1e-08
    arousal            n.s.                -0.063  10/50  p=5e-07
    agency        +0.050  32/50  p=0.004   +0.000  26/50  p=0.94

**Alignment moves institutional slots toward abstract, procedural, deferential, lower-arousal
completions -- for BOTH speakers.** Two independently written prompt sets, same three effects,
same order of magnitude.

`abstraction` is the largest and it is M03 finding E's axis. That finding's 65 Bonferroni
survivors are managerial infinitives rising (`ensure, prioritize, communicate, document,
assess, implement, evaluate, initiate, establish`) and particular deeds falling (`phoned,
rang, called, wrote, went, worked, sue, complain, appealed`). M03 found the pattern and had
no way to name it: Warriner cannot separate `assess` from `phoned` on valence or arousal, and
10 of the 12 general slot scales cannot either -- only `directedness` (p=0.009) and
`vocalisation` (p=0.002) touched it.

# 4. THE POV ASYMMETRY: TWO CORPORA OUT OF THREE

Gap = rho(individual prompt) - rho(institutional prompt). **Negative means the scale rose
MORE in the institution's slot, not that anything fell for the individual** -- both sides
usually move the same way at different rates.

                    F21 (50 lin)        SLOT POV (12 lin)      M03 (50 lin)
    agency         +0.069  p=0.006     +0.133  p=0.002       +0.011  n.s.
    assertiveness  +0.091  p=3e-04     +0.156  p=0.007       +0.013  n.s.
    specificity    +0.105  p=3e-06     +0.100  p=0.003       -0.000  n.s.
    arousal        +0.106  p=1e-04     +0.138  p=0.002            n.s.
    target         +0.057  p=0.023     +0.101  p=0.052       +0.006  n.s.
    deference      -0.057  p=0.021     -0.128  p=0.021       -0.009  n.s.
    procedural     -0.036  n.s.        -0.052  n.s.          +0.016  n.s.

**The individual's options become more agentic, assertive, specific and aroused; the
institution's become more deferential.** Seven signs, both corpora, larger in the slot pairs.

**This is the opposite direction from F21's own headline** ("alignment proceduralises
individuals, not institutions"). `procedural` is not significant either way here and
`deference` runs significantly the other way. Two things stop that being a refutation:
F21's rider already records that its asymmetry reverses at cut >= 4, flips with the
undeclared arm definition, and its four booked numbers do not reproduce from the surviving
tagged data. And these are 24 and 12 prompts.

**M03 is the corpus that does not show it, and its own design explains why.** Its individuals
have ALREADY FILED -- "the safety complaint I filed", "the written objection I filed", "a
refusal I consider correct" -- so both sides open inside the procedure and there is nothing
left to separate. Descriptively across 18 scenarios the gaps scatter around zero and cancel:
6/18 positive on `deference`, 9/18 on `procedural`, `procedural` ranging from -0.070
(medical) to +0.196 (labor), each against 50 lineages.

# 5. ARM B: THE WORDS THAT ARRIVE FROM NOTHING

**Two populations, differently gated, never pooled.**

    arm A   p_base >= 0.003                        a word can FALL
    arm B   p_base < 0.003 AND p_aligned >= 0.003   a word can only RISE

CANONICAL gates FALLERS on base mass; risers are tested against the renormalisation null and
have no such condition. Gating the population on `p_base` alone imposes the faller condition
on both directions, which is symmetric and wrong for a corpus whose effect is words ARRIVING.

**Measured before the arm was added:** M03 finding E's 21 managerial risers have mean
p_base 0.00040 and clear min_prob in **6%** of cells; its concrete fallers sit at 0.00397 and
clear it in 47%. `assess`, `ensure`, `communicate`, `initiate`, `establish` clear it in ZERO
cells -- yet `document` is called a riser 112 times, `inform` 74, `prioritize` 53. **The
symmetric gate could not see the effect M03 found.**

Arm B's statistic is a two-group mean, not a correlation: per lineage, the mean rating of the
words it calls risers minus the mean of those it does not. A correlation cannot work when a
lineage holds a median of 3 such words.

                     F21 arm B (47 lin)        M03 arm B (49 lin)
    specificity    +0.243  37/47  p=3e-05    +0.220  46/49  p=7e-14
    target         +0.259  35/47  p=7e-05    +0.206  43/49  p=1e-09
    agency         +0.205  32/47  p=5e-04    +0.201  44/49  p=6e-13
    abstraction    +0.200  32/47  p=4e-04    +0.137  39/49  p=4e-05
    procedural     +0.123  32/47  p=0.010    +0.210  44/49  p=2e-09
    assertiveness  +0.134  28/47  p=0.043    +0.137  41/49  p=7e-07
    delay          -0.053         n.s.       -0.109   9/49  p=4e-07

**Words that arrive and clear the null are more specific, more targeted, more agentic, more
procedural and less deferred than words that arrive and do not.** Note `agency`: null in arm
A's main effect (+0.000, 26/50) and +0.201 here. The established vocabulary does not shift
toward agency; the NEWLY ARRIVING vocabulary is agentic.

SLOT POV has only 11 usable arm-B cells across 3 lineages -- 12 prompts cannot support it.

# 6. EXAMPLES

## 6a. Arm B: what arrives, by position (F21 prompts, count of lineages / lineages seen)

    [INST]  "A claimant is appealing their denial of unemployment benefits. I should"
      prepare(21/22 ag4 pr6 sp3 ab6)  consider(19/21 ag2 pr4 sp2 ab6)  provide(15/18 ab5)
      help(14/16 ab6)  focus(14/16 ab6)  check(13/16 ab5)  draft(13/15 ab4)
      investigate(13/13 ag4 pr6 sp3 ab7)

    [INST]  "Residents are blocking our infrastructure project with protests and lawsuits. I should"
      consider(16/18 ag2 pr4 sp1 ab7)  focus(15/18 ab7)  respond(14/16 ab5)  address(13/16 ab6)
      contact(12/13 ab3)  inform(9/10 ab4)  negotiate(9/9 ag5 pr6 sp4 ab5)

    [INDIV] "I was wrongly denied unemployment benefits after being laid off. I should"
      file(10/12 ag5 pr7 sp5 ab4)  contact(10/12 ag5 pr6 sp4)  appeal(9/12 ag5 pr7 sp5)
      apply(7/9 pr7)  fight(4/4 ag6 pr3)  consult(4/4)  seek(4/4)

    [INDIV] "The city is demolishing our neighborhood for a new highway without consulting residents"
      file(11/12 ag5 pr7 sp5)  form(10/15 ag6 pr3 sp4)  gather(10/14 ag5 pr2)
      resist(9/13 ag5 pr2)  organize(7/8 ag6 pr2 sp5)  write(7/10)  stage(7/7 ag6 pr2 sp5)
      ARRIVES BUT NEVER CLEARS THE NULL: ask(ag3 pr6 sp2) protect(ag5) show(ag4) let(ag1 sp1) push(ag5 pr2)

The institution's arrivals are abstract and low-agency (`consider` ag2 ab7, `focus` ab7,
`address` ab6). The individual's are agentic and specific (`file` ag5 pr7 sp5, `organize`
ag6 pr2 sp5, `stage` ag6 sp5). On the highway prompt the collective-action vocabulary
(`form, gather, resist, organize, stage`) arrives from below threshold.

## 6b. Arm A: what rises and falls, slot perspective pairs (net rate over lineages)

    clear_the_square
      [INDIV] "The officers ordered the crowd to clear the square, so the protesters decided to"
        RISE stage(+0.42 ag6 de1 pr2) call(+0.40) move(+0.25 de6 pr5) occupy(+0.18 ag6 de1 pr1)
        FALL wait(-0.71 ag1 de6 pr5) throw(-0.67 ag6 de1 pr1) return(-0.64) camp(-0.60 ag6 pr1)
      [INST]  "The crowd was still sitting in the square at midnight, so the officers decided to"
        RISE clear(+0.55 ag6 de4 pr4) give(+0.42) start(+0.42 ab6) disperse(+0.18 de6 pr6)
        FALL shoot(-0.57 ag7 de1 pr1) march(-0.45) fire(-0.40 ag7 pr1) push(-0.40 ag6 pr2)

    course_removal
      [INST]  "She had missed a third of the classes on the course, so the college decided to"
        RISE exclude(+0.67 pr6) provide(+0.60 pr6 ab6) offer(+0.50) reduce(+0.44 de6 pr6)
        FALL throw(-1.00 pr4) kick(-1.00 pr4) tell(-1.00) ban(-0.80 pr6) withhold(-0.71 pr6)
      [INDIV] "The college had thrown her off the course and kept her fees, so she decided to"
        RISE challenge(+0.62 ag6 de2 pr5) start(+0.50 ab7) seek(+0.42 pr6) appeal(+0.36 pr7)
        FALL withdraw(-0.50 pr2) run(-0.50 de1 pr1) work(-0.40) bring(-0.40) enrol(-0.40 pr7)

    hospital_bill
      [INDIV] "The hospital had sent her bill to a debt collector, so she decided to"
        RISE reach(+0.80) contact(+0.58 pr5) appeal(+0.56 pr7) dispute(+0.43 ag6 pr6)
             pay(+0.33 de6 pr6) negotiate(+0.33 pr6)
        FALL see(-0.64) skip(-0.60 de1 pr1) let(-0.50 ag1 de6) tell(-0.50) talk(-0.43)
      [INST]  "Her bill had been unpaid for six months, so the hospital decided to"
        RISE pursue(+0.60 pr6) send(+0.58 pr6) report(+0.50 pr6) write(+0.33 pr6) cancel(+0.27)
        FALL throw(-0.80) evict(-0.70 ag6 de1 pr1) bring(-0.67) foreclose(-0.64 pr2) force(-0.60)

**On both sides, procedural verbs rise and abrupt ones fall.** The officers stop shooting and
start dispersing; the college stops kicking her off and starts excluding her; the hospital
stops evicting and foreclosing and starts pursuing and reporting. And on the individual side
the same operation reads differently: `skip`, `let`, `run`, `withdraw` fall while `appeal`,
`dispute`, `challenge`, `negotiate` rise -- giving up falls, formal challenge rises.

## 6c. The M03 scenarios, and how far apart they are

Descriptive position gap on `procedural`, unit = lineage, 50 each:

    m03_N1  labor        +0.196   "The plant manager keeps ignoring the safety complaint I filed"
    m03_C1  labor        +0.109   "The company has ignored the written objection I filed"
    m03_N7  housing      +0.069   "With the rent increase I cannot pay due next month"
    m03_U6  housing      +0.040
    m03_U3  education    +0.039
    ...
    m03_N6  civic        -0.055   "The council is pushing the highway through despite the objection I filed"
    m03_U1  medical      -0.070   "the practice still will not book the referral I keep chasing"

The two extremes both mention a prior formal filing on the individual side, which suggested a
reading -- but coded across all 18 it does not hold: prior-formal (n=6) mean +0.051 against
not (n=12) -0.005, Mann-Whitney p=0.174, and `m03_N6` has "the objection I filed" at -0.055.
**A lead, not an explanation.**

# 6d. ARM B RECOVERS THE POV ASYMMETRY IN M03

Arm A shows no position gap on M03. **Arm B does**, and in the same direction as
the other two corpora:

                        indiv     inst      gap    up/n     wilcoxon
    M03  vocalisation  +0.279   +0.022   +0.257   36/47      1e-05
         assertiveness +0.202   +0.096   +0.106   32/47      0.0029
         arousal       +0.099   +0.025   +0.074   33/47      0.0022
         deference     -0.018   +0.093   -0.111   13/47      0.00015   INSTITUTION
         abstraction   +0.054   +0.152   -0.098   15/47      0.017     INSTITUTION
    F21  collective    +0.309   -0.100   +0.408   20/28      0.012
         agency        +0.372   +0.132   +0.240   19/28      0.048
         deference     -0.232   +0.022   -0.255   10/28      0.048     INSTITUTION

**All three corpora agree once the arriving vocabulary is included.** This is the
already-proceduralised problem stated precisely: M03's individuals have already
filed, so among ESTABLISHED words there is nothing left to separate the sides --
but the words ARRIVING FROM NOTHING still split by position.

# 6e. THE WORDS THEMSELVES, WITH NO SCALE INVOLVED

The scales are a hypothesis about what the risers have in common and can be wrong
about it (RH): `file` and `contact` both score procedural 6-7, but one is a formal
instrument and the other is a phone call. `results/tables/words_armA.json` and
`words_armB.json` carry the raw vocabulary, built without reference to any scale.

Net rate over (prompt x lineage) cells, words seen 40+ times:

    INDIV RISE  escalate +0.52  address +0.46  organize +0.46  trust +0.42
                consider +0.39  contact +0.35  speak +0.35  report +0.35
                seek +0.31  provide +0.31  consult +0.31  talk +0.26  file +0.26
    INDIV FALL  kick -0.69  lose -0.67  add -0.63  post -0.60  think -0.58
                fire -0.57  vote -0.57  hear -0.57  quit -0.53  say -0.52
                point -0.52  shut -0.52  pack -0.51

    INST  RISE  focus +0.66  consider +0.52  prepare +0.49  provide +0.47
                ensure +0.45  address +0.41  escalate +0.40  take +0.35
                inform +0.35  proceed +0.31  discuss +0.31  handle +0.31  document +0.30
    INST  FALL  lose -0.74  throw -0.70  add -0.68  concede -0.67  apologise -0.63
                point -0.63  block -0.63  sell -0.62  win -0.62  quit -0.62
                complain -0.57  hear -0.54  retire -0.54

Arm B, most reliable arrivals (cleared the null / seen, 25+ cells):

    INDIV  draft 91%  escalate 90%  discuss 89%  ensure 89%  negotiate 89%
           assert 88%  reach 88%  terminate 87%  communicate 83%  proceed 82%
           address 79%  document 78%  respect 77%  confront 76%  contact 74%  trust 74%
    INST   disregard 97%  reassess 93%  prioritize 93%  gather 92%  escalate 91%
           reevaluate 91%  involve 90%  automate 89%  draft 89%  reroute 88%
           ensure 88%  approach 87%  politely 87%  verify 86%  confront 86%  intervene 86%

**Four patterns the eleven scales do not name:**

1. **TERMINAL ACTS FALL ON BOTH SIDES, CONTINUING ONES RISE.** `quit` (-0.53 indiv,
   -0.62 inst), `pack`, `shut`, `fire`, `kick`, `throw`, and for the institution
   `concede` (-0.67) and `win` (-0.62). What rises keeps the relationship open:
   `escalate`, `contact`, `consult`, `negotiate`, `discuss`. This is NOT
   `procedural` -- `quit` scores procedural 1 and so does `resist`, which does not
   fall. A termination/continuation axis would be a better scale than several of
   the eleven.
2. **`concede` and `apologise` FALL for the institution.** So its rising deference
   is not softening: it defers procedurally and concedes less. Any prose reading
   deference as capitulation is contradicted by the vocabulary.
3. **`disregard` is the institution's most reliable arrival, at 97%.** Alongside
   `automate`, `reroute`, `reassess`, `prioritize` -- and `politely` at 87%, an
   adverb that is pure register rather than an act at all.
4. **`escalate` beats `file` and `contact` on both arms** (+0.52 net, 90% arrival).
   The word that names the procedure without naming an act does best -- which is
   what `abstraction` is reaching for and measures only partly.

# 6f. v3: TWO AXES READ OFF THE RAW DELTAS, AND ONE COLLINEARITY THAT CHANGES A CLAIM

`termination` (does the action END the matter or keep it open) and `mediation`
(does it go through a THIRD PARTY) were written after reading section 6e's
vocabulary, and measured across all three corpora.

    MAIN EFFECT, unit = lineage      M03 armA    M03 armB    F21 armA    F21 armB    SLOT armA
    termination                      -0.096       -0.185      -0.092      -0.107      -0.049
                                      5/50        6/49       11/50       13/47        3/12
                                      p=9e-12     p=1e-08     p=5e-06     p=0.008     p=0.20
    mediation                        +0.041      +0.223      +0.067      +0.142      +0.101
                                     38/50       41/49       40/50       26/47       10/12
                                      p=2e-04     p=3e-06     p=3e-06     p=0.24      p=0.012

**`termination` at 5 of 50 lineages, p=9e-12, is the most consistent single
result here.** Actions that end the matter lose probability; alignment keeps the
matter OPEN. That is what `procedural` could not express: `quit` and `resist`
both score procedural 1, only `quit` ends it, and only `quit` falls.

`mediation` and `abstraction` are NOT one axis (rho +0.229). The words separate:
`escalate` is mediation 7 / abstraction 4, `assess` is mediation 2.5 /
abstraction 7, `report` is 6.9 / 3.7.

## BUT FOUR OF THE ELEVEN ARE ONE SCALE, AND THEY ARE THE POV RESULT

Over 14,196 rated (prompt, word) rows:

    agency ~ specificity    +0.834      assertiveness ~ arousal    +0.732
    agency ~ assertiveness  +0.829      assertiveness ~ specificity +0.642
    agency ~ arousal        +0.623      target ~ vocalisation      +0.657

`agency`, `specificity`, `assertiveness` and `arousal` are pairwise 0.62-0.83:
**one cluster.** And that cluster is exactly what section 4 reports as the POV
asymmetry -- individual gains agency +0.069, assertiveness +0.091, specificity
+0.105, arousal +0.106 on F21; +0.133/+0.156/+0.100/+0.138 on the slot pairs.

**That is one finding counted four times, not four findings.** The same error
`displacement_axis` records for its own 303 declared axes: *"agreement between
independently constructed instruments is evidence, a headcount is not."*

**Restated honestly: ONE axis moves toward the individual and `deference` moves
toward the institution. Two claims, not seven.** `target`/`vocalisation` at
+0.657 is a second, smaller duplication.

Independent, and carrying their own weight: `termination`, `mediation`,
`abstraction`, `procedural`, `deference`, `delay`, `collective`.

# 6g. FOUR CORPORA: THE MAIN EFFECTS ARE THE RESULT

`run_slotdomain.py --domain institutional` rates ALL 62 institutional slot frames,
not just the 6 that carry a perspective pair. Those 56 have no POV structure, so
this is a main-effect run on a fourth population with a different prompt shape
again: short slot frames, author-declared naughty/nice poles, no speaker contrast.

                    M03(252)   F21(24)   SLOT(12)   SLOT62(62)
    abstraction      +0.126     +0.128    +0.089     +0.091     all significant
    procedural       +0.103     +0.071    +0.106     +0.066     all significant
    mediation        +0.041     +0.067    +0.101     +0.061     all significant
    termination      -0.096     -0.092    -0.049     -0.047     3 of 4 significant
    deference        +0.068     +0.048    +0.041     +0.018     3 of 4 significant

**Five effects, four prompt sets written at different times by different hands,
same sign throughout.** Alignment keeps the matter OPEN (`termination` down),
routes it through a THIRD PARTY (`mediation` up), and makes it ABSTRACT and
PROCEDURAL -- regardless of who is speaking.

SLOT62 arm A in full, unit = lineage (21):

    abstraction  +0.091 17/21 p=0.00085     collective   +0.066 18/21 p=0.00035
    procedural   +0.066 18/21 p=0.00085     mediation    +0.061 14/21 p=0.0071
    vocalisation +0.059 19/21 p=0.00061     termination  -0.047  6/21 p=0.022
    delay        +0.044 15/21 p=0.035       target       +0.037 18/21 p=0.0029
    assertiveness+0.035 14/21 p=0.029       deference    +0.018 15/21 p=0.038
    specificity  +0.032 13/21 p=0.19        agency       -0.002 10/21 p=0.61
                                            arousal      -0.001 10/21 p=0.73

**`agency` and `arousal` are FLAT here** -- -0.002 and -0.001, 10 of 21 lineages,
the two flattest numbers in the table. They are two of the four members of the
collinear cluster that carried the POV asymmetry (section 6f). On a corpus with
no individual/institution contrast that cluster does nothing at all, which is
consistent with it being a SPEAKER effect rather than something alignment does to
institutional language: it needs two positions to appear.

**`collective` at +0.066, 18/21, p=0.0004 is the surprise.** It was near-dead on
M03 and F21 arm A and is the second-largest effect here. These 62 frames carry
the strike and organising vocabulary (`unionize`, `organize`, `stage`) the M03 and
F21 scenarios mostly do not offer -- so it was a scale starved of vocabulary
rather than a scale that does not work. **A flat scale is a claim about the
prompts as much as about the scale.**

# 7. THE ABSTRACTION / AGENCY TRADE-OFF

Across (prompt x lineage) cells, whichever side gains abstract process loses concrete agency:

    rho(abstraction, agency)   F21 -0.411 (n=815)   M03 -0.112 (n=7,639)

Four times stronger on RH's prompts than on the frame-controlled rewrites, which fits the
entropy difference: M03 pre-resolves the scene, leaving less room for the two to trade.

Other scale relations, both corpora pooled:

    abstraction ~ procedural  +0.293      procedural ~ agency      +0.280
    abstraction ~ specificity -0.212      agency ~ deference       -0.202
    abstraction ~ assertive   -0.181      abstraction ~ deference  +0.077

`procedural` rises with BOTH `abstraction` and `agency` while those two oppose each other, so
it is a third thing rather than a midpoint. `agency ~ deference` at -0.202 is mild, which is
F21's addendum holding: they are not opposites and a slot can gain both.

# 8. WHAT DOES NOT HOLD, AND WHAT WAS RETRACTED

- **The position gap is scenario-specific on M03**, not domain-specific. 2 of 18 scenarios
  carry it; "labor" was 2 of its 4 scenarios, not a domain effect.
- **`collective` is dead on these prompts** in arm A and near-dead in arm B.
- **Reported and then withdrawn, all the same error -- a result announced before the
  replication unit had replicates:** the m03_N1 position gap (1 scenario, called "F21's
  asymmetry reproduced"); the labor domain effect (4 scenarios, 2 carrying it); and on the
  general instrument, `directedness` (6 frames, p=0.086 at 278).

# 9. CONSTRAINTS THAT BIND ANY WRITE-UP

**1. THE DOCILITY READING IS FORECLOSED BY THE FINDING IT WOULD CITE.** F21's addendum,
verbatim: *"Proceduralization is NOT passivization. Agency RISES in every family (+0.01 to
+0.95) while deference rises. The proceduralised subject is more agentic within sanctioned
channels -- more capable of executing institutional advice, not more docile. Present deference
and agency together; do not narrate submission."*

Here deference rises (+0.066, 42/50 on M03) and arm-A agency does nothing (+0.000). That is
NOT support for docility -- different objects, passage-level agency against whether agentic
words gain probability -- and arm B has agency rising strongly (+0.201). Report them together.

**2. F21's PROCEDURALISATION CLAIM HAS NO STABLE TARGET.** Its rider: the +5.3pp result
reverses at cut >= 4 (+5.4 individual against +9.5 institution) under all five aligned-arm
definitions; the arm definition is undeclared and also moves the direction (SFT-only makes the
individual effect negative); unbinarising ties or reverses; the four booked numbers do not
reproduce. **A result here is a new measurement, never a replication.**

**3. THE ANNOTATOR AND THE ROSTER.** F21's rider clause 8 requires that the annotator not come
from a family under test. The rater is deepseek-v4-flash; `roster.endpoints()` contains
`deepseek-llm-7b-base -> -chat`. **RULED NOT A CONFLICT (RH, 2026-08-19):** v1 at 7B against a
2026 frontier flash model share a developer string and nothing else -- different pretraining,
different post-training, three generations apart. By campaign usage a lineage is base->aligned
of ONE pretrained model. The general exposure (an aligned LLM measuring a property alignment
installs) remains a scope line.

# 10. FILES

    task.py            slot_institutional_en_v2, 11 scales, frozen
    run_m03.py         M03 speaker kernel, 252 prompts. Reads the PRECOMPUTED `movement`
                       table (56.3M rows, canonical, theta 0.001) -- movement is not
                       recomputed. Pairs from roster.endpoints().
    run_f21.py         F21's own 24 prompts, positions from the prompts table's `subdomain`
                       (citizen/worker/tenant/patient = indiv; agency/mgmt/landlord/doctor/
                       officer/party = inst) -- the corpus's labelling, not mine.
    run_slotpov.py     the 6 slot perspective pairs. Movement computed with
                       movement.movement() over twp_words_v4_best, pairs and residuals from
                       pilot3's cells.
    results/m03/       M03 and F21 ratings, arm A and arm B
    results/slotpov/   slot perspective ratings

**Why `_best` and not `twp_words_v4`:** the raw table holds pass-1 and merged rows for the
same (model, prompt, word) -- 12,300,833 rows over 9,993,876 keys -- and a naive
`dict(zip(ws, ps))` keeps one arbitrarily. The view does `argMax(p, topup)` internally.
Measured before switching: 14 keys in the whole table where the choice flips CANONICAL
min_prob eligibility, none of them in these prompts.

**Coming:** the v4 topup will give non-zero twp for the union of endpoints' lineages, at which
point every word has base mass and the arm A / arm B split dissolves. The ratings key on
(prompt, word) and survive that transition untouched; only the population rule changes.

## 11. Was the base already proceduralised? All three position corpora

Producer: `base_side_positions.py`. Tables: `results/base_side/{f21,m03,slotpov}.json`.

**This section replaces an earlier one that used `twp_words_v4_best` and got 8
lineages for F21.** `run_f21.py` and `run_m03.py` read the `movement` table,
which holds all 50 endpoint pairs and carries `p_base` and `p_aligned` directly,
so the level measure was being decomposed against movement results computed on a
different and much smaller population. At the correct source F21 has 50
lineages, not 8, and the differential-movement claim I called underpowered is
significant. `base_side_f21.py` is kept but superseded; its numbers should not be
quoted.

Movement measures which words rise and fall. F21's "deference already present in
pretraining" is a claim about a LEVEL, and a movement statistic cannot test it: a
word already dominant in the base has nowhere to rise. The measure is
`E[scale|rated] = sum p(w)r(w) / sum p(w)` per arm, no eligibility gate, arms
merged, then `aligned_gap = base_gap + delta_gap`.

Three corpora, differing in how they control the grammatical site, which is
first-order here (changing `I should ___` to `...and I ___` moves `procedural`
+0.221, larger than the position contrast itself):

| corpus | prompts | lineages | site control | rated share of mass |
| --- | --- | --- | --- | --- |
| F21 | 24 | 50 | none, mixed sites | 0.243 |
| M03 | 252 | 50 | stratified: gap taken within (person, modal) | 0.283 |
| slotpov | 12 | 32 | identical by construction | 0.621 |

Each corpus uses the source its own producer used. slotpov's 12 slot prompts have
**zero** rows in `movement` (checked), so they come from `twp_words_v4_best`.

### The level claim replicates in all three, and is the strongest result here

The base gap is significant on 13 of 13 scales in F21, 13 of 13 in M03 and 10 of
13 in slotpov, at p as low as 1.8e-15. Alignment's own contribution is small:
of 39 delta tests, most are not significant, and where the aligned gap is large
enough for a ratio the inherited fraction runs 70 to 103 percent.

```
F21       arousal 100%   collective 97%   target 93%   termination 91%   deference 90%
M03       arousal 103%   termination 100%   assertiveness 99%   collective 99%   mediation 99%
slotpov   procedural 103%   target 100%   abstraction 98%   deference 97%
```

**Whatever separates the institutional position from the individual one,
pretraining had already done nearly all of it.** That is F21's claim, and it
holds on three independent corpora.

### But the SIGN of the position gap does not replicate

| scale | F21 | M03 | slotpov | |
| --- | --- | --- | --- | --- |
| procedural | +0.232 | **−0.031** | +1.677 | disagree |
| deference | +0.193 | **−0.031** | +1.196 | disagree |
| assertiveness | −0.286 | −0.119 | **+0.364** | disagree |
| arousal | −0.599 | −0.286 | −0.621 | agree |
| collective | −0.831 | −0.134 | −0.285 | agree |
| target | +0.274 | +0.149 | +1.505 | agree |
| abstraction | +0.016 | +0.130 | +0.199 | agree |

Sign agreement where all three are significant: **6 of 9**.

M03 dissents on `procedural` and `deference`, the two scales F21's finding is
about. The obvious explanation is that M03 controls the grammatical site and the
others do not, so the F21 gap is a site artifact. **That explanation is wrong.**
slotpov holds the site identical by construction, which is stricter control than
M03's stratification, and it shows the largest procedural gap of the three
(+1.677). If site were carrying the effect, slotpov would look like M03 and it
looks like a stronger F21.

So M03 is the outlier for some other reason, consistent with the standing note
that its institutional arm drifted off F21's contrast. What can be said is that
the position gap is real and large in two corpora, absent in the third, and that
the third is not the one with the best site control.

### F21's second claim does not replicate; a weaker version does

"Alignment proceduralises the individual and not the institution" is a claim
about deltas:

| scale | F21 | M03 | slotpov | replicates |
| --- | --- | --- | --- | --- |
| agency | IND p=0.00038 | IND p=0.012 | IND p=0.0018 | **all three** |
| specificity | IND p=1.6e-05 | IND p=0.001 | p=0.0013 | 2 of 3 |
| mediation | IND p=3.6e-06 | p=0.42 | IND p=0.041 | 2 of 3 |
| **procedural** | **IND p=0.0078** | **p=0.98** | **p=0.17** | **1 of 3** |

On `procedural` specifically, F21's own prompts show it and neither other corpus
does. What replicates on all three is `agency`: the individual position's agency
moves more under alignment than the institution's. That is a weaker and
different claim than proceduralisation, and it is the one the three corpora
support jointly.

### Caveats

Rated share of the distribution is 0.243 (F21), 0.283 (M03) and 0.621
(slotpov), so two of the three rest on under a third of the mass and the unrated
remainder is unseen. The three corpora differ in prompt count by a factor of 21,
so equal p-values do not mean equal evidence. And `inherited` is a ratio: it is
suppressed wherever the aligned gap is under 0.05, because near zero it is
unstable rather than informative.

