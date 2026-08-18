# lexical_axes — does the model's alignment axis predict corpus preference?

**id:** lexical_axes **status:** step D run. **RH's pre-registered prediction
(FAIL or NARROW PASS) is CONFIRMED.** Registration `6625ec2`, A1-A2.

# THE RESULT: FOUR FAIL, ONE NARROW PASS

Zero free parameters. The word vector comes entirely from
`meta/M01_displacement/results/k/word_auc_en.tsv`; nothing is fitted on any
corpus, so overfitting is unavailable as an explanation.

    population        raw score   LENGTH alone   rho(score,len)   LENGTH-NORMALISED
    hh-harmless          45.2%        42.1%          0.843            50.8%  FAILS
    hh-helpful           56.0%        58.8%          0.856            50.1%  FAILS
    pku-unsafe           46.9%        45.0%          0.751            50.9%  FAILS
    pku-mixed            45.0%        38.5%          0.769            54.9%  NARROW
    ultrafeedback        53.3%        54.7%          0.917            47.8%  FAILS

**The raw score was LENGTH.** It correlates with token count at rho 0.75-0.92,
length alone predicts as well or better in four of five, and matched to within 20
words the raw score sits at 50.6 / 50.3 / 50.5 / 54.0 / 47.5 -- chance.

Removing the declared assistant-register words changed nothing (within 0.7pp
everywhere), so the register confound A2 guarded against never arose. **The
confound that did arise was the one A2 did not name.**

# WHY IT COULD NOT HAVE WORKED: THE VECTOR HAS NO NEGATIVE POLE

    threshold        words   aligned-leaning   base-leaning
    auc > 0.568       1223            1223              0
    auc > 0.520       1767            1764              0
    auc > 0.500       2016            1999              5

**Five base-leaning words out of 2,016 with the threshold dropped to chance.**
`k_word_auc` finds vocabulary alignment ADDS and essentially none it removes with
diagnostic power, so the artifact is an aligned-vocabulary detector and cannot
express a displacement direction. Summing it over a text is therefore a length
proxy by construction -- which is what the rho of 0.75-0.92 is.

**This is a fact about the model-side instrument, not about the corpora**, and it
is independent evidence for `U_ladder`'s gradient: removal stops while addition
continues (faller share 49.3% -> 28.6% -> 1.0% across 16 families). A second
instrument, built for a different purpose, finds the removal side empty.

# THE ONE NARROW PASS, HELD LOOSELY

`pku-mixed` at 54.9% is the only stratum where one response is LABELLED SAFE and
the other UNSAFE, rather than both being graded. Aligned-vocabulary density
weakly predicts which is the safe one -- which is close to tautological, since a
response labelled safe is likelier to be in assistant register. **Reported, not
interpreted.**

# WHAT THIS SETTLES AND WHAT IT DOES NOT

**Settles:** the axis models sort on, as this instrument measures it, does NOT
predict which response an annotator preferred, in any of five populations across
three annotation regimes, once length is controlled.

**Does not settle:** whether the axes are unrelated. The vector cannot represent
the falling half of displacement at all, so this is a null from an instrument
that can only see one direction. **A signed model-side vector with a real
negative pole would be a different test**, and building one needs cells.

**And nothing about causation either way** (A9). This compares two vectors over
words; it never claimed one produced the other, which is why it was askable at
all after yesterday's model-level attempt collapsed.
