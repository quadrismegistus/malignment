"""The word-alone feeling as DISTRIBUTIONS, via a Jev Survey. -> $MALIGNMENT_DATA/affect_proportionality/type_survey*.parquet

    python type_survey.py --pilot 100        30 smoke words + 70 drawn (seed 20260928) from the 7,690
    python type_survey.py                    all 7,690 (not run: RH checks the pilot's cost first)

RH, 2026-09-28: the DeepSeek label instrument (`type_task.py`) is not reliable -- its answer for
act words moved with the wording (`kill` anger/fear/none), and the fates it produced live on two
hard boundaries (none vs named; fear vs anger for vocal words). A Jev Survey returns a
PROBABILITY over the options for each Choice, so each word becomes a point in feeling space and
a boundary becomes a measured overlap: `scream` can be fear 0.5 / anger 0.35 rather than fear.

DOER = THE GRAMMATICAL SUBJECT (v2). v1 asked for "the person who performs or undergoes it" and
Jev answered `rape` fear 0.84 -- the victim's feeling. The Freudian question is about the subject
of "wanted to ___", the one who does it, so v2 names the subject and excludes the victim.

SAME NINE FEELINGS, SAME TWO READINGS as `type_task.py` (doer: the person who performs or
undergoes it; evoked: a witness or reader), word alone, no sentence.
"""
import argparse, os, random, sys

os.environ.setdefault("LITMOD_DATA_DIR", "/Users/rj416/github/largeliterarymodels/data")
from largeliterarymodels.survey import Survey  # noqa: E402
from largeliterarymodels.questions import Choice  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from type_task import SMOKE  # noqa: E402

DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "affect_proportionality")
FEELINGS = {
    "anger": "anger, rage, hostility, aggression",
    "fear": "fear, terror, anxiety, dread",
    "grief": "grief, sorrow, sadness, loss",
    "desire": "desire, lust, longing, wanting",
    "disgust": "disgust, revulsion",
    "shame": "shame, embarrassment, guilt",
    "tenderness": "tenderness, affection, fondness, care",
    "joy": "joy, delight, happiness, amusement",
    "none": "no feeling in particular -- most words: table, Tuesday, paper, seven",
}
QUESTIONS = {
    "doer_feeling": Choice(
        instructions={"question": "Judge the word ALONE, in its most common sense, with no sentence around it. "
                                  "What is THE PERSON WHO DOES IT -- the grammatical subject -- typically feeling? "
                                  "For kill, the killer, not the one killed; for die, the one who dies; for a word "
                                  "that names a feeling, that feeling. Never the feeling of a victim or target.",
                      "inspect": "word"},
        criteria=FEELINGS),
    "evoked_feeling": Choice(
        instructions={"question": "Judge the word ALONE, in its most common sense, with no sentence around it. "
                                  "What feeling does it typically PROVOKE in someone who witnesses or reads it?",
                      "inspect": "word"},
        criteria=FEELINGS),
}


class TypeFeelingSurvey(Survey):
    name = "type_feeling_survey_en_v2"
    questions = QUESTIONS
    model = "jev-latest"
    usage_log = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0)
    a = ap.parse_args()
    words = [l.strip() for l in open(os.path.join(DATA, "type_words.txt")) if l.strip()]
    if a.pilot:
        rest = [w for w in words if w not in SMOKE]
        words = list(SMOKE) + random.Random(20260928).sample(rest, a.pilot - len(SMOKE))
    s = TypeFeelingSurvey()
    ans = s.map([{"word": w} for w in words])
    rows = []
    for w, r in zip(words, ans):
        d = dict(word=w, ok=r is not None)
        if r is not None:
            for q in QUESTIONS:
                x = r[q]
                d[q] = x.choice; d[q + "_conf"] = x.confidence
                for f in FEELINGS:
                    d["%s_p_%s" % (q, f)] = float(x.probabilities.get(f, 0.0))
        rows.append(d)
    import pyarrow as pa, pyarrow.parquet as pq
    fn = os.path.join(DATA, "type_survey_pilot.parquet" if a.pilot else "type_survey.parquet")
    pq.write_table(pa.Table.from_pylist(rows), fn, compression="zstd")
    print("wrote %s | %d words, %d answered" % (fn, len(rows), sum(r["ok"] for r in rows)))
    for d in rows[:30]:
        if not d["ok"]:
            print("  %-12s FAILED" % d["word"]); continue
        top = lambda q: ", ".join("%s %.2f" % (f, d["%s_p_%s" % (q, f)]) for f in sorted(FEELINGS, key=lambda f: -d["%s_p_%s" % (q, f)])[:3])
        print("  %-10s doer: %-40s | evoked: %s" % (d["word"], top("doer_feeling"), top("evoked_feeling")))


if __name__ == "__main__":
    main()
