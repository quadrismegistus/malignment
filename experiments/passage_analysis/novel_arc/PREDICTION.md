# Registered prediction, 2026-08-22, before the chicago scoring completed

**RH: "aligned fiction sits formally somewhere between 1880 and 1920."**

Registered while `measure_lltk.py --corpus chicago` was still running, so the
1880-1920 values it will produce were not available to either of us. The
chicago run covers that window with 1,098 texts (113 in the 1880s, 190 in the
1890s, 372 in the 1900s, 423 in the 1910s).

## WHAT IS ALREADY ON THE RECORD, AND WHY IT DOES NOT SETTLE IT

From the chadwyck-only placement (`placement.py`, run before this prediction):

    aligned passages        -0.041   (n=2,736)
    base passages           +0.096   (n=2,195)
    API passages            -0.104   (n=6,508)

    chadwyck 1875           -0.280   (n=37,214 passages, 66 texts)
    chadwyck 1900           -0.319   (n= 1,172 passages,  2 TEXTS)

On that scale aligned (-0.041) sits MORE CONCRETE than both, which would put it
LATER than 1920 and read as a failed prediction. **That reading should not be
trusted.** chadwyck's 1900 bin is two texts, and its 1875 bin is 66 -- against
1,098 chicago texts in the same window. The existing numbers are exactly the
thin tail chicago was run to replace, and the prediction is being tested
against the new values, not the old ones.

## WHAT WOULD CONFIRM, AND WHAT WOULD REFUTE

CONFIRMED if the chicago passage median for 1880-1920 brackets the aligned
median of -0.041 -- i.e. the 1880s/1890s value is more abstract (more negative)
and the 1910s/1920s value more concrete, or the interval contains it.

REFUTED if aligned falls outside that window on the chicago scale: more
concrete than the 1920s (later than predicted) or more abstract than the 1880s
(earlier than predicted).

Sign, once more: HIGH = CONCRETE, so a more abstract text is more NEGATIVE.

## WHY THE PREDICTION IS NOT TRIVIALLY TRUE

The abstraction series falls monotonically from the C18 peak (-0.68 at 1750)
toward the present, and the aligned median sits near the concrete end, so SOME
late period will always be nearest. The content of the prediction is the
specific window: 1880-1920 rather than 1850-75 or post-1950. A "nearest period"
answer is not evidence on its own; the test is whether the window brackets it.

---

# OUTCOME, same day, after the chicago run completed

**CONFIRMED.** chicago: 4,198,863 passages over all 9,089 texts.

chicago period medians (25-year bins, `rh_absconc_median`, HIGH = CONCRETE):

    1875   -0.1982  (n=  106,913)
    1900   -0.0548  (n=  372,326)
    1925   +0.0158  (n=  665,432)
    1950   +0.0761  (n=  566,017)
    1975   +0.1196  (n=2,304,596)
    2000   +0.1278  (n=  183,441)

Placement, linear interpolation between bin midpoints:

    base       +0.0957   bracketed 1962-1987   ~1973
    aligned    -0.0407   bracketed 1912-1937   ~1917   <-- INSIDE 1880-1920
    API        -0.1039   bracketed 1887-1912   ~1903   <-- INSIDE 1880-1920

Alignment moves a model ~56 years back on this axis and the API layer a further
~14. The prediction is confirmed for the aligned arm and also holds for API,
which was not part of it.

## WHAT THE EARLIER NUMBERS SAID, AND WHY THEY WERE WRONG

The pre-registration recorded that chadwyck-only placement put aligned MORE
CONCRETE than both its 1875 and 1900 bins, which would have refuted this. That
reading is now retired for the stated reason: **chadwyck's 1900 bin is two
texts** (1,172 passages) against chicago's 372,326. The registration named that
in advance rather than after the fact.

## THREE CAVEATS ON THE OUTCOME

**The corpora disagree where they overlap.** At 1875, chadwyck reads -0.2802
(n=37,214) and chicago -0.1982 (n=106,913) -- a gap of 0.082 z with adequate n
on both sides. The historical scale is therefore NOT corpus-independent, and
every year quoted above is a CHICAGO year. On chadwyck's scale the same
populations would place earlier.

**Linear interpolation between bin midpoints is a modelling choice.** The
BRACKETING is the measurement; "1917" carries precision the bins cannot support
and should be quoted as "between 1912 and 1937, nearer the earlier end".

**`c20_fiction` is off the top of the scale** at +0.1715, more concrete than
chicago's own 1975 (+0.1196) and 2000 (+0.1278) bins, though both are C20
fiction. Unexplained, and NOT explicable by its dialogue-light selection, which
would push the other way. Since c20_fiction anchored the earlier claim that
aligned prose is more abstract than contemporary fiction, that claim now has two
inconsistent reference points and is held pending resolution.
