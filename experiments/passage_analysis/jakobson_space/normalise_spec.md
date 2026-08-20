# Orthographic normalisation spec

You are normalising the ORTHOGRAPHY of a human-written passage so that six corpora can be compared on their language rather than on their typography.

## The one rule everything follows

**Fix any deviation from standard spelling and typography of the word the writer intended. Preserve every choice about WHICH words are used and in WHAT ORDER.**

The measurement downstream is byte-level. `thats` against `that's`, or a curly `”` (3 bytes) against a straight `"` (1 byte), is a difference in how fast someone typed or which publisher typeset them, not a difference in how they write. Those must go. Word choice, sentence shape, register, dialect and argument are the signal. Those must stay, exactly.

## FIX these

- **Misspellings and typos.** `teh` -> `the`, `missee` -> `missed`, `amd` -> `and`, `acar` -> `a car`, `recieve` -> `receive`, `alot` -> `a lot`, `suppose to` -> `supposed to`, `kindergarden` -> `kindergarten`.
- **Missing or wrong apostrophes.** `dont` -> `don't`, `thats` -> `that's`, `its` -> `it's` only where the possessive/contraction is unambiguous from context.
- **Curly quotes and dashes to ASCII.** `“ ” ‘ ’` -> `" " ' '`. `—` and `–` -> ` - `. Ellipsis `…` -> `...`.
- **Any other non-ASCII that is TYPOGRAPHIC**: non-breaking spaces, ligatures (`ﬁ` -> `fi`), soft hyphens. **Accented letters belonging to a word are not typographic and stay**: `Santa Fé`, `naïve`, `Foucault`, `café`. Change how a character was set, never how a word is spelled in its own language.
- **Sentence capitalisation and terminal punctuation** where a sentence plainly lacks it. A passage typed entirely in lowercase gets standard capitalisation.
- **Word-splitting and line-break damage from scanning.** `theor- ists` -> `theorists`, `conversa tion` -> `conversation`, `htde` -> `little`, `sadors` -> `sailors` where the intended word is recoverable with confidence.
- **INLINE FOOTNOTE MARKERS**, identified by ONE structural test.

  A footnote marker is a digit attached to punctuation where **the character immediately before the punctuation is a LETTER**. If the character before the punctuation is a DIGIT, it is a decimal point or a thousands separator and you must not touch it. Apply the test before every such edit:

      manifestation.27 Heidegger   ->  manifestation. Heidegger    (before "." is "n", a letter)
      villein.19 With his          ->  villein. With his           (before "." is "n", a letter)
      the right to vote,1 the      ->  the right to vote, the      (before "," is "e", a letter)
      a normative standard ."28    ->  a normative standard."      (before the quote is "d")

      20.0 pp                      ->  20.0 pp     UNCHANGED       (before "." is "0", a digit)
      raised 31.4 percentage       ->  31.4        UNCHANGED
      3,024 participants           ->  3,024       UNCHANGED
      983,004 tokens               ->  983,004     UNCHANGED
      1.3-2.9 pp                   ->  1.3-2.9     UNCHANGED

  This exact confusion has destroyed data in testing: `3,024` became `3,`, `20.0`
  became `20.`, `983,004` became `983,`. **A number that loses its decimal or its
  thousands separator is a worse outcome than a footnote marker left in place.**
  When the test is ambiguous, leave the text alone.

  Also unchanged, always: `in 1997`, `p. 25`, `Chapter 3`, `19th century`.
- **Other archive and format junk**: leading record numbers like `(59)`, `34.`, `#2675 (04/29/94)`; running heads; stray asterisks marking notes.
- **LaTeX and markup, rendered as plain reading text.** `$L_{\rm X}$--$T$` -> `L_X-T`; `~$\gamma$` -> `gamma`; `\emph{x}` -> `x`. Keep the symbol's plain name or letter; do not delete the content.
- **`--` written as two hyphens** is a typesetting convention for a dash, heavily used in LaTeX sources. Render it ` - `, the same as `—`. Applies wherever it appears.
- **Whitespace**: collapse runs of spaces, remove space before punctuation.

## DO NOT "repair" these. They look like damage and are not.

Every one of these was actually corrupted in testing, so treat them as hard stops:

- **`$` before a number is usually MONEY, not a math delimiter.** `raising the fee from $90 to $190` and `worth $7-$14 per visit` are amounts; deleting the `$` changes what the sentence says. Strip `$` only when it opens and closes a genuine math expression (`$J^P=0^+$`, `$B_s^0$`). If there is no closing `$`, leave it alone.
- **Identifiers, model names, tokenizer names, package names, technical terms.** `o200k_base` is the real name of a tokenizer and became `~200k_base`. If a token looks like a name from computing or science, it is correct as written; you cannot tell whether it is misspelled and you must not guess.
- **Suspended hyphens.** `Hispanic-, South-Asian- and Black-signaled names` is standard English, not an OCR split - the trailing hyphen carries over to a shared second element. It became `South-Asianand`. A hyphen before a space and then `and`, `or`, or `to` is suspended: keep it exactly.
- **Real numbers.** `1,500 people`, `in 1997`, `p. 25`, `Chapter 3`, `19th century`, `1.3-2.9 pp`.

The general rule: **an OCR split is a word broken across a line break, and both halves are meaningless alone** (`manu- scripts`, `decom- position`, `it- self`). If either half is a real word, a name, or a number, it is not a split and you must leave it.

Repairing genuine scan damage in a foreign word IS correct even though it adds non-ASCII: `Sch6nborner` -> `Schönborner`, `du M4ril` -> `du Méril`, `MaaB` -> `Maß`. The OCR turned `ö` into `6` and `ß` into `B`; restoring them recovers the text the page actually held. But render LaTeX commands as their PLAIN NAME, never as a Unicode symbol: `$\approx$250` -> `approx 250`, not `≈250`.

## NEVER change these

- **Word choice.** Do not replace a word with a better one. Not `got` -> `received`, not `thing` -> `object`.
- **Syntax and grammar.** `she don't`, `me and him went`, a comma splice, a run-on, a sentence fragment, a dangling modifier: all stay exactly as written. These are how the writer builds sentences and they are the object of study.
- **Dialect, idiom, register, profanity, and content.** Do not soften, formalise, censor or summarise. Dream reports may be incoherent, violent or sexual; leave every bit of that intact.
- **Written speech, which is a choice and not a slip.** `sayin`, `talkin'`, `goin`, `gonna`, `wanna`, `gotta`, `kinda`, `ain't`, `y'all`, `cos` stay exactly as written. G-dropping is how a writer puts a voice on the page; it is not a typing error, and normalising it removes register rather than noise. Contrast `didnt` and `thats`, which are the same word as `didn't` and `that's` with a key missed - those you fix.
- **Sentence order, paragraph structure, or length.** Do not merge, split, reorder, add or delete sentences.
- **Repetition.** If the writer repeated themselves, keep the repetition.

## THE PASSAGE ENDS MID-SENTENCE. LEAVE IT THAT WAY.

Every passage was cut at a fixed word count, so most stop mid-clause - `...and he`, `...by me`, `...explain`. **Do not complete the sentence, do not add a final period, do not trim back to the last complete sentence.** The cut is deliberate and matches how the model passages this is compared against were truncated. A completed ending is a corrupted passage.

## Output

One JSON object per input passage, in the same order:

```json
{"id": "<the id given>", "text": "<the normalised passage>", "changes": ["typo", "curly_quotes"]}
```

`changes` is a short list of category tags from: `typo`, `apostrophe`, `curly_quotes`, `dashes`, `nonascii`, `casing`, `terminal_punct`, `ocr_split`, `archive_junk`, `footnote_marker`, `latex`, `whitespace`. Use `[]` if nothing changed.

Every input id must appear exactly once in the output. The normalised text should be within a few words of the input length - if yours is much shorter you have deleted content, and if much longer you have completed the truncation. Both are errors.
