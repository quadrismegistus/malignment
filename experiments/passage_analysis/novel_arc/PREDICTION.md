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
