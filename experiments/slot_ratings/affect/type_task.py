"""The affect task's FEELING, rated per word TYPE -- no sentence. -> $MALIGNMENT_DATA/affect_proportionality/type_feeling.parquet

    python type_task.py --smoke           30 words, printed
    python type_task.py --words FILE      one word per line; writes the parquet

NO MOVER IN THE EXAMPLES. The first draft's shots named `kill` anger, `scream` fear and
`search`/`see` none -- the canonical displacement pair and two common arrivals, so the prompt
would have dictated the answer on exactly the words the test turns on. The shots are now
feeling NOUNS and neutral nouns, none of them a next-word mover in these slots.

WHOSE FEELING, DECIDED BY THE QUESTION. Unprimed, the rater called `kill` fear and `shoot`
fear -- the feeling an act PROVOKES -- while `scream` is the screamer's fear: two things in one
category. The Freudian question is about the affect of the one whose impulse is barred, the
subject of "wanted to ___", so an act is rated for the feeling of the person who performs or
undergoes it.

TWO FIELDS, NOT A CHOICE (RH, "yes", 2026-09-28). Under "the doer's feeling" the rater
returned `kill` none and `rape` disgust -- no wording fixed a single feeling for act words, so
both readings are rated in one call and the carry test runs on each: `doer_feeling` is the
Freudian question (the barred subject's affect), `evoked_feeling` the reader-side one.

WHY (RH, 2026-09-28). `feeling_carry.py` found that where the barred word's feeling and the
scene's differ, the substitutes take the scene's. But the contextual rater SEES the fragment,
so a mild substitute may simply be given the scene's feeling: "takes the scene's feeling"
and "has none of its own" read the same. A word rated ALONE cannot inherit a scene. If
anger words are replaced by anger words even so, the feeling travels as a property of the
words -- closer to displacement along a path than to a scene that stays angry.

SAME NINE FEELINGS as `task.py` (FEELINGS), so context is the only thing that changes
between this and the contextual result. Same rater (deepseek/deepseek-v4-flash, resolved
`deepseek-flash`), temperature 0. `ratable` false for function words and fragments, as there.
"""
import argparse, os, sys
from typing import Literal

from pydantic import BaseModel, Field

os.environ.setdefault("LITMOD_DATA_DIR", "/Users/rj416/github/largeliterarymodels/data")
from largeliterarymodels.task import Task  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from task import FEELINGS  # noqa: E402

OUT = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")),
                   "affect_proportionality", "type_feeling.parquet")


class TypeFeeling(BaseModel):
    reading: str = Field(description=
        "One short phrase: the word's most common sense. Written first.")
    ratable: bool = Field(default=True, description=
        "False for function words (the, of, and, to), fragments and tokenisation artifacts. "
        "Prefer false over guessing.")
    doer_feeling: Literal[FEELINGS] = Field(description=
        "The feeling of THE PERSON WHO PERFORMS OR UNDERGOES what the word names -- what "
        "someone doing or undergoing it is typically feeling. For a word that names a feeling, "
        "that feeling. `none` if such a person typically feels nothing in particular.")
    evoked_feeling: Literal[FEELINGS] = Field(description=
        "The feeling the word typically PROVOKES in someone who witnesses or reads it. `none` "
        "if it provokes nothing in particular.")
    intensity: int = Field(ge=1, le=7, description=
        "How much feeling the word itself carries, in either direction. 1 = none; 7 = "
        "overwhelming.")


SYSTEM = """You are annotating a lexical dataset: a word-level emotion norm, the same kind of
resource as the NRC emotion lexicon or Warriner's ratings. You are shown ONE WORD, with no
sentence. Judge the word in its most common sense. Do not invent a context.

Give TWO feelings, each from a fixed list:
anger, fear, grief, desire, disgust, shame, tenderness, joy, none.

  doer_feeling     what THE PERSON WHO PERFORMS OR UNDERGOES it is typically feeling
  evoked_feeling   what it typically PROVOKES in someone who witnesses or reads it

The two can differ, and for many acts they do; rate each on its own terms. For a word that
NAMES a feeling, both are usually that feeling: `fury` anger, `terror` fear, `mourning` grief,
`longing` desire, `revulsion` disgust, `humiliation` shame, `fondness` tenderness, `delight`
joy. MOST WORDS CARRY NO FEELING ON EITHER READING: `table`, `Tuesday`, `paper`, `seven` are
`none` and `none`.

Intensity is the word's own charge, 1-7, independent of which feeling."""


class TypeFeelingEN(Task):
    name = "type_feeling_en_v2"
    schema = TypeFeeling
    system_prompt = SYSTEM
    temperature = 0.0
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "168h"
    usage_log = True


SMOKE = ["kill", "scream", "hurt", "destroy", "see", "search", "shoot", "die", "be", "have",
         "punch", "cry", "whisper", "kiss", "rape", "penis", "hug", "weep", "blush", "laugh",
         "the", "of", "slowly", "table", "run", "beg", "confess", "sue", "report", "fuck"]


def render(w):
    return "WORD: %s" % w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--words")
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    t = TypeFeelingEN()
    words = SMOKE if a.smoke else [l.strip() for l in open(a.words) if l.strip()]
    res = t.map([render(w) for w in words], num_workers=a.workers)
    if a.smoke:
        for w, r in zip(words, res):
            print("  %-10s %s" % (w, "REFUSED" if r is None else "doer %-10s evoked %-10s %d ratable=%s" % (r.doer_feeling, r.evoked_feeling, r.intensity, r.ratable)))
        return
    import pyarrow as pa, pyarrow.parquet as pq
    rows = [dict(word=w, ok=r is not None, **({"doer_feeling": r.doer_feeling, "evoked_feeling": r.evoked_feeling, "intensity": r.intensity, "ratable": r.ratable, "reading": r.reading} if r else {}))
            for w, r in zip(words, res)]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), OUT, compression="zstd")
    print("wrote %s | %d words, %d returned" % (OUT, len(rows), sum(r["ok"] for r in rows)))


if __name__ == "__main__":
    main()
