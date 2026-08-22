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

### Interiority -- alignment leaves the historical range altogether

`usas_x`, the USAS "PSYCHOLOGICAL ACTIONS, STATES AND PROCESSES" field. Higher =
more psychological-state language.

    1575-1700   0.106-0.114   flat
    1725        0.1263
    1775        0.1358        <- historical peak
    1825        0.1176        <- dip
    1875        0.1282 / 0.1250   (chadwyck / chicago)
    1925-2000   0.1264-0.1268     FLAT for 125 years

Interiority is **not** what the novel lost after 1800 -- it plateaued. And every
model arm sits above every period from 1575 to 2000:

    aligned    +0.1667    23% above the 1775 peak
    API        +0.1491
    base       +0.1461
      historical maximum +0.1358 (1775)

Against the human anchors, aligned sits at **philosophy** (+0.1648), above
dreams (+0.1529) and waking narrative (+0.1364), and far above actual C20
fiction (+0.1138).

**So the two axes rewind differently.** Atavistic in direction on abstraction,
beyond-precedent in degree on interiority -- the same structure RH found
independently in LLM poetry, where rhyme and strict meter exceed any historical
period.

## WHAT THE NUMBERS LOOK LIKE AS PROSE

Each passage below is the one closest to its population's median, so these are
typical rather than extreme.

### Abstraction

    C18 peak abstraction   Eighteenth-Century_Fiction/fieldinz. (1754)
    rh_absconc_median = -0.6808  (population median -0.6808)
    | In reading the writings of those ancient sages, I had look'd up to
    | them as seated in the clouds, and at a vast distance; but in those
    | local accounts, where they walk'd, where they held their discourses,
    | and did as other mortals do, I in a manner confined them within
    | limited bounds, and familiarized them into my acquaintance. Nicanor
    | was so agreeable, furnish'd me with so many new ideas, and was so
    | substantial a contrast to the wearisome nothingness I had f

    late C20 fiction       00024067 (1994)
    rh_absconc_median = +0.1195  (population median +0.1195)
    | Enough, perhaps, to make even what he was seeing now seem faint and
    | faded. And if there was more, how could he possibly bear it without
    | going mad? Not even putting his eyes out would help; he understood
    | somehow that his sense of "seeing" things came mostly from his
    | lifelong acceptance of sight as his primary sense. But there was, in
    | fact, a lot more than seeing going on here. In order to prove this to
    | himself he closed his eyes . . . and went right on seei

    base model             huggyllama/llama-7b
    rh_absconc_median = +0.0833  (population median +0.0834)
    | squirm a little in his grip. His hands moved over her, laid especial
    | attention on her hands as though to make sure she understood exactly
    | what he intended. "You can choose your own diaphragm with Kaitlyn," he
    | said in a deep mellow voice. As his hand moved down, Jadeen realized
    | dawn would come soon, but she wasn't yet ready to leave Laythan. Love
    | came over her then and heart and body sang a duet. Her hands were
    | bruised where he had held them and she half ex

    aligned model          meta-llama/Llama-3.1-8B-Instruct
    rh_absconc_median = -0.0569  (population median -0.0569)
    | curse the day she met him. Almost a year and a half had passed since
    | that night when her world turned upside down. At the time she thought
    | she was over him, but now he was back, breathing down her neck and
    | putting a sour taste in her mouth. It wasn’t the first time she saw
    | him that day, though it was the first time she had seen him with fury
    | so apparent in his eyes. He was Adam, her ex-boyfriend and the worst
    | person she had ever met. Their breakup was mess

### Interiority

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
