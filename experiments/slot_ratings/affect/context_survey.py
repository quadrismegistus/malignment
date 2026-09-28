"""The doer feeling IN CONTEXT, as distributions, frame and frame+word. -> $MALIGNMENT_DATA/affect_proportionality/context_survey.parquet

    python context_survey.py --pilot 40      a few frames and their words, printed
    python context_survey.py                 all 56,060 (the affect task's items)

RH, 2026-09-28: the word-alone rating "doesn't totally make sense" (a word's feeling depends on
its sentence), and the in-context rater lends the scene's feeling to mild words. This rates IN
CONTEXT but makes the scene cancel: each FRAME is rated alone (the slot empty) and each word
inside the frame, both as a Jev distribution over the same nine feelings, so a word's
contribution is its SHIFT from its own frame -- lift in feeling space. The scene's feeling is
in both terms and drops out of the difference.

Items: `run_proportionality.py`'s 56,060 (1,873 charged English frames + 54,187 movers,
chosen by the coverage rule, never by what they rate). Doer reading only: the grammatical
subject's feeling (the evoked reading failed the second-rater gate word-alone).
"""
import argparse, os, sys

os.environ.setdefault("LITMOD_DATA_DIR", "/Users/rj416/github/largeliterarymodels/data")
from largeliterarymodels.survey import Survey  # noqa: E402
from largeliterarymodels.questions import Choice, Score  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from type_survey import FEELINGS  # noqa: E402

DATA = os.path.join(os.environ.get("MALIGNMENT_DATA", os.path.expanduser("~/malignment-data")), "affect_proportionality")
QUESTIONS = {
    "doer_feeling": Choice(
        instructions={"question": "This is an UNFINISHED sentence. If `word` is given, it fills the blank; if "
                                  "`word` is empty, the blank is still open -- judge the fragment as it stands and "
                                  "do not imagine a word for it. What is THE GRAMMATICAL SUBJECT of the sentence -- "
                                  "the person doing the action -- feeling at this point? Never the feeling of a "
                                  "victim, a target, or a reader.",
                      "inspect": "fragment and word"},
        criteria=FEELINGS),
    #: RH, 2026-09-28: intensity on the SAME instrument and design as the kind, so the fates and
    #: the intensity result come from one set of ratings (frame alone vs frame + word, in context).
    "doer_intensity": Score(
        instructions={"question": "This is an UNFINISHED sentence. If `word` is given, it fills the blank; if "
                                  "`word` is empty, the blank is still open -- judge the fragment as it stands. How "
                                  "INTENSE is what the GRAMMATICAL SUBJECT is feeling at this point, whatever the "
                                  "feeling is? Never a victim's, a target's or a reader's.",
                      "inspect": "fragment and word"},
        criteria=["The subject feels nothing in particular: calm, flat, going about something procedural.",
                  "A mild feeling: slight irritation, passing interest, faint unease.",
                  "A clear, engaged feeling: annoyed, worried, pleased, wanting something.",
                  "A strong feeling: furious, frightened, elated, desperate.",
                  "An overwhelming feeling: blind rage, terror, ecstasy, despair."]),
}


class ContextFeelingSurvey(Survey):
    name = "context_feeling_survey_en_v2"
    questions = QUESTIONS
    model = "jev-latest"
    usage_log = True


def items():
    import pyarrow.parquet as pq
    t = pq.read_table(os.path.join(DATA, "affect_proportionality.parquet"), columns=["prompt", "word"]).to_pylist()
    return [(r["prompt"], r["word"]) for r in t]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0)
    a = ap.parse_args()
    its = items()
    if a.pilot:
        frames = list(dict.fromkeys(p for p, _ in its))[:4]
        its = [x for x in its if x[0] in frames][:a.pilot]
    s = ContextFeelingSurvey()
    ans = s.map([{"fragment": p + " ___", "word": w or ""} for p, w in its])
    rows = []
    for (p, w), r in zip(its, ans):
        d = dict(prompt=p, word=w, ok=r is not None)
        if r is not None:
            x = r["doer_feeling"]
            d["doer_feeling"] = x.choice
            for f in FEELINGS:
                d["p_" + f] = float(x.probabilities.get(f, 0.0))
            y = r["doer_intensity"]
            d["intensity"] = float(y.score)            # 0..4, probability-weighted position
            d["intensity_conf"] = y.confidence
        rows.append(d)
    import pyarrow as pa, pyarrow.parquet as pq
    fn = os.path.join(DATA, "context_survey_pilot.parquet" if a.pilot else "context_survey.parquet")
    pq.write_table(pa.Table.from_pylist(rows), fn, compression="zstd")
    print("wrote %s | %d items, %d answered" % (fn, len(rows), sum(r["ok"] for r in rows)))
    if a.pilot:
        for d in rows:
            if d["ok"]:
                top = ", ".join("%s %.2f" % (f, d["p_" + f]) for f in sorted(FEELINGS, key=lambda f: -d["p_" + f])[:3])
                print("  %-55s %-12s int %.2f | %s" % (d["prompt"][:55], d["word"] or "(FRAME)", d["intensity"], top))


if __name__ == "__main__":
    main()
