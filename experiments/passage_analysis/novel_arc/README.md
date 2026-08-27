---
subject: novel_arc
question: Where does LLM-generated fiction sit in the formal sweep of literary history?
status: RUN. Both main effects measured; RH's registered 1880-1920 prediction resolved.
grain: page
note: |
  `results/` is EMPTY BY DESIGN and this is not an un-run folder. Outputs live in
  `$MALIGNMENT_DATA/novel_arc/` because chadwyck is 128 MB and chicago 895 MB.
  Figures and the plotted data are in `figures/`.
---

# novel_arc

Places LLM-generated fiction inside the formal sweep of literary history, using
RH's diachronic concreteness norms and the lexical instruments that survived the
base-vs-aligned contrast in `passage_norms`.

**The finding, in one sentence: alignment rewinds literary history on
abstraction and overshoots it entirely on interiority.**

## THE TWO MAIN EFFECTS

### Abstraction -- alignment rewinds to roughly 1917

`rh_absconc_median` (`Abs-Conc.Median.median` from `abslithists/abstraction`).
**HIGH = CONCRETE, negative = abstract**, which is the easiest thing here to get
backwards. Passage medians by 25-year period:

    chadwyck                     chicago
    1650   -0.5873               1875   -0.1982
    1725   -0.6572               1900   -0.0548
    1750   -0.6813   <- peak     1925   +0.0158
    1775   -0.6714               1950   +0.0761
    1800   -0.5251               1975   +0.1196
    1825   -0.2817               2000   +0.1278
    1850   -0.2306

Abstraction rises into the eighteenth century, peaks 1725-1775, and falls
monotonically for the next two hundred years. Interpolating the model arms onto
the chicago curve:

    base       +0.0957   bracketed 1962-1987   ~1973
    aligned    -0.0407   bracketed 1912-1937   ~1917
    API        -0.1039   bracketed 1887-1912   ~1903

**Alignment moves a model about fifty-six years back on this axis; the API layer
a further fourteen.** RH predicted 1880-1920 before the chicago numbers existed
(`PREDICTION.md`), and both aligned and API land inside it.

### Interiority

In chronological order, so the arc is visible: low and flat through the C17,
peaking 1775, dipping in the early C19, flat for the whole C20 -- and then the
aligned model above all of it.

    C17 low interiority    Early_English_Prose_Fiction/ee01010. (1662)
    usas_x = +0.1140  (population median +0.1140)
    | For a while therefore she gave law to her former open Licentiousness,
    | and seemingly betook her self to a civiller life; that is, to a closer
    | and cunninger way of living, not being so much in the eye of all
    | people, by whom she was already defamed beyond remedy. But there is
    | nothing so bad which thinks not by showes and pretences to impose upon
    | and deceive the Vulgar. This her sudden reclaimednesse was more
    | admired then credited by her Neighbours, who mused

    C18 interiority peak   Early_American_Fiction/brackenr.01 (1793)
    usas_x = +0.1358  (population median +0.1358)
    | And being once taken for such, what prodigy was there in his being in
    | request with the females, and all the first families of the city, who
    | might be ambitious, and vie with each other, in having him married to
    | a niece or a daughter, that so being raised above plebians by the
    | connection, they might be considered as of a pratrician degree? Let
    | the principle be what it would, whether taste, or ambition, the fact
    | was, that the bog-trotter was courted and carre

    C19 dip                Early_American_Fiction/bacondel.01 (1839)
    usas_x = +0.1176  (population median +0.1176)
    | -- Delicious! Hear that flute. It comes from among those trees by the
    | river side. It is the shower that has freshened every thing, and made
    | the birds so musical. You should stand in the door below, as I did
    | just now, to see the fort and the moistened woods stands out from that
    | black sky, with all this brightness blazing on them. 'Tis lovely --
    | all. There goes the last golden rim over the blackening woods; already
    | even a shade of tender mourning steals over

    late C20 fiction       00021234 (1975)
    usas_x = +0.1264  (population median +0.1264)
    | She has plump calves and a narrow waist, protuberant eyes, sallow
    | cheeks. Her hands are dimpled and flex slightly as she speaks. She's
    | tall. "All right," Mary says. "What is it?" "Nothing like that," the
    | woman replies. She squints her bulging eyes in a look of intelligence.
    | "You're pretty sharp." "Never mind that." "What are you here for then?
    | Nothing better to do?" "I've got enough." "You're down and out, aren't
    | you?" The woman places herself at Mary's si

    aligned model          LLM360/AmberSafe
    usas_x = +0.1684  (population median +0.1684)
    | immerse herself in the ways of Okinawan martial arts, practicing for
    | hours a day to get closer to her instructor. She was determined to be
    | the best fighter she could be, just as her instructor had taught her.
    | She also spent more time studying the ancient teachings of the school,
    | hoping that they would give her some insight into why her instructor
    | was so protective of her. She also began to pay more attention to the
    | way his instructors spoke of him, trying

## AND THE SAME AXIS SHOWS UP SYNCHRONICALLY

The historical series is not the only evidence. Correlating the eleven measures
that replicated in the alignment contrast against the abstraction axis, TEXT by
TEXT across 1,333 chadwyck texts, ten of eleven point the same way alignment
moved them:

    gi_positiv       -0.761      alignment UP    = more abstract
    gi_emot          -0.616      alignment UP
    usas_x           -0.455      alignment UP
    gi_enltot        -0.349      alignment UP
    gi_passive       -0.311      alignment UP
    k_bodily_harm    +0.265      alignment DOWN
    brysbaert_conc   +0.850      alignment DOWN
    gi_role          -0.065      alignment DOWN  <- THE EXCEPTION

Seven survive within 25-year bins, so the association is not merely the shared
time trend; `usas_n5` collapses within period and `gi_role` reverses. Stable
across all five abstraction sources (Median, PAV-Conc, MRC-Conc, LSN-Imag,
MT-Conc). **Not eleven independent tests** -- the measures correlate with each
other -- so no p-value is quoted.

## THE INTERIORITY CLAIM RESTS ON TWO INSTRUMENTS, AND ONLY ONE OF THEM IS HERE

`usas_x` is a semantic field built by linguists for tagging, and it is the one
that can be run over four million historical passages. But the arm effect it
reports was established first, and more strongly, by a completely different
instrument: `experiments/passage_analysis/interiority_in_passages` had an LLM
coder read passages and assign a 0-3 DEGREE of interiority.

    coder degree (0-3), narrative passages    +0.224   16/17 up   p=0.00015
    coder degree | interiority present        +0.145   17/20 up   p=0.0005
    usas_x, corpus A / corpus B (disjoint)    +0.0237 / +0.0141   replicated

**Nothing is shared between them** -- one is a model reading prose and judging
how much inner life is in it, the other is counting membership in a fixed
lexicon. They agree that alignment raises interiority.

**The division of labour is the point.** The coder established the arm effect
and could not be historically situated; the lexicon replicates the arm effect at
a fraction of the resolution and CAN be run over 4.75M passages of fiction from
1575 to 2000. So the historical placement above -- aligned prose more interior
than any period the novel ever reached -- is carried entirely by the weaker of
the two instruments, and is trustworthy in proportion to how well `usas_x`
stands in for what the coder measured.

**What would close the loop:** run the coder over a period-stratified sample of
chadwyck and chicago passages. That is affordable at the anchor's grain (500 per
25-year bin, ~8,500 passages) and would put the STRONG instrument on the
historical axis rather than inferring its behaviour from the weak one.

## METHOD, AND THE PARTS THAT MATTER

**Two token streams, because the instruments disagree about orthography.** RH's
norms take the RAW surface (they carry `shew` -0.693 and `vertue` -0.760 with
period-appropriate projections; modernising shifts them +0.192 z toward concrete
over the 61,551 MorphAdorner pairs where both forms have values, and that shift
is period-correlated). Everything else takes a modernised stream with a
type-level lemma fallback.

**Modernisation is guarded.** MorphAdorner applied blindly rewrote 5.93% of
tokens in an 1869 novel -- `got`->`God`, `an`->`and`, `red`->`read` -- every one
a word the lexicons already knew, so the rewrite could only destroy a correct
lookup, and it hits LATE texts hardest. A token is rewritten only when it is
absent from the lexicons AND its rewrite is present.

**Lemmas are type-level, one spaCy pass over the vocabulary.** In-context
tagging separates noun from verb, which rarely separates content word from
function word. Coverage gain from the lemma fallback: warriner +13.51pp, gi
+11.09, brysbaert +7.17, usas +3.23, k +1.66, **RH's norms +0.31** -- they hold
no function words at all (0 of the 20 commonest), so they are already a
content-word instrument.

**Coverage was read before any construct.** Across 1600-1875 Brysbaert coverage
runs .949-.965 and RH .264-.346 while `variant_rate` falls 14.3% -> 0.08%, so
the orthographic gradient inside chadwyck is handled rather than left sitting
inside the slope.

## LIMITS, STATED

- **The historical scale is not corpus-independent.** Where chadwyck and chicago
  overlap at 1875 they differ by 0.082 z (-0.2802 vs -0.1982) with adequate n on
  both sides. Every year quoted above is a CHICAGO year.
- **The interpolation is a modelling choice.** The bracketing is the
  measurement; "1917" should be read as "between 1912 and 1937, nearer the
  earlier end".
- **Direction is not mechanism.** Alignment is a within-model intervention;
  literary history is a between-text series. A formal parallel on a measured
  axis is not a shared cause, and the C18's abstraction is a specific historical
  formation (sentiment, virtue, sensibility) that alignment's corporate-safety
  register resembles only in this formal respect.
- **`gi_role` is the one component of the alignment movement that does not sit
  on this axis** -- people named by social role fall under alignment but are
  flat against abstraction (-0.065). Either noise or a second axis.

## FILES

    measure_lltk.py        chunk an lltk corpus at n=200 and score it
    place_models.py        score the quadrant corpus (base/aligned/API/human)
    arc.py                 coverage, then the RH axis, then the LLM axis
    placement.py           both corpora on one scale, models placed against it
    backfill_dialogue.py   add a column without re-running a scoring pass
    PREDICTION.md          RH's 1880-1920 prediction, registered and resolved

Outputs live in `$MALIGNMENT_DATA/novel_arc/`, not here: chadwyck is 128 MB and
chicago 895 MB.

    chadwyck   1,333 texts   551,575 passages   1582-1954
    chicago    9,089 texts 4,198,863 passages   1880-2000
