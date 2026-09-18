"""What becomes of the QUOTA OF AFFECT? Six scales, in context, frame included.

    python -m tasks.affect --show      render one prompt and one frame, spend nothing
    python -m tasks.affect --smoke     the worked examples' own frames, held out

## WHY THIS EXISTS WHEN `slot_institutional_en_v3` ALREADY RATES AROUSAL

It does, and the gap this file was first proposed to fill turned out not to
exist: `inst:arousal` is contextual, covers 2,511 prompts, and on the annotated
pairs it is the single largest effect measured (-0.64, 47 of 50 lineages,
p=4e-11). Affective INTENSITY is not missing.

What is missing is everything Freud needs intensity FOR. "Repression" (1915)
requires a case to be followed twice -- "what, as the result of repression,
becomes of the idea, and what becomes of the drive energy linked to it" -- and
gives the energy three fates, not one:

    either the drive is altogether suppressed, so that no trace of it is found,
    or it appears as an affect which is in some way or other QUALITATIVELY
    COLOURED, or it is changed into ANXIETY

A 1-7 intensity cannot separate those. Suppression and re-colouring can share a
number; anxiety is not a quantity at all. So `feeling` and `anxiety` below are
the two scales that make the three fates distinguishable, and they are the
reason for the run.

## AND WHY IT RATES INTENSITY ANYWAY, WHICH LOOKS LIKE DUPLICATION

Two reasons, both structural rather than preference.

**No existing instrument rates the FRAME.** `v6` and `slot_institutional_en_v3`
rate one (prompt, word) at a time and never the fragment alone, so neither can
give an INCREMENT -- only a level. That distinction is not academic here: the
type-level `k_charge` misled on `raped -> kissed` precisely by reporting a level
where the frame was carrying the charge, and `task_charge` exists in its current
form because `slot_loaded_mass` made the same mistake. An affect scale without a
frame anchor would repeat it a third time.

**A second measurement of one construct is a calibration, not a waste.**
`intensity` here and `inst:arousal` there should agree on the (prompt, word)
pairs both cover. Where they do, every other scale in this file inherits that
credit. Where they do not, one of the two instruments is wrong and we find out
before anything rests on it.

## THE FRAME IS RATED BY THE SAME CALL SHAPE, AND THE RATER MUST SAY SO

RH's design, 2026-09-18: the candidate word is empty and the instruction says to
rate the fragment as it stands. One instrument, one schema, one rater, so the
frame rating and the completion rating are commensurable BY CONSTRUCTION and
their difference is a quantity rather than a comparison between rulers.

The failure mode is a rater that invents a completion and rates that instead,
which would be silent and would corrupt every increment. So `target` is a
required field the rater must fill with what it believes it rated. A frame call
that returns `completion` is a confabulation and gets dropped; without the echo
we would never know the row was wrong.

    77,229 calls over the 1,600 prompts carrying both existing instruments:
    75,629 completions and 1,600 frames, the frames 2.1% of the run.

## WHAT EACH SCALE IS FOR, AND WHY NOT AN EXISTING ONE

    intensity   the quantity. Anchors the frame; calibrates `inst:arousal`.
    feeling     WHICH affect. Freud's "qualitatively coloured" fate is
                unmeasurable without it, and nothing in the corpus returns a
                named emotion.
    anxiety     his third fate, and his most specific prediction. NOT
                `makes_worse`, which asks whether the situation deteriorates,
                and not intensity: `scream` and `freeze` are both high
                intensity and opposite here.
    borne       WHOSE affect. `inst:arousal` asks what "the completion carries",
                which is ambiguous between the person feeling something and the
                scene being charged for a reader -- and that ambiguity is
                exactly where `raped -> applied performed` sits. This is the
                scale that separates suppression from clinical distance.
    discharge   from the `Project` (1895), via the paper's own footnote:
                screaming is discharge that does NOT unburden, because "the
                endogenous stimulus continues to be received". Does the
                completion release the tension or leave it standing? `scream`
                and `speak` differ here and on nothing else in the corpus.
    valence     the FEELING's colour. `makes_better`/`makes_worse` rate the
                SITUATION, and Warriner valence is out of context.

## SMOKE RESULTS, 2026-09-18, AND TWO SCALES ARE NOT READY

Run on frames absent from SYSTEM, after a first run whose smoke set WAS the
worked examples and returned the shots back digit for digit on 7 of 11 calls.
`relation_type.py` states the held-out rule in its own `--smoke` line; this file
ignored it, then repeated a weaker form of the same error by testing
"He was so furious he wanted to" against a shot reading "She was so angry she
wanted to". Both the frame and the CONTRAST have to be unseen.

    "She was so angry she wanted to"   felt/reads  feeling  move   resid  disch
      (FRAME)                             6 / 4     anger    n/a      6      1
      kill                                7 / 6     anger    keeps    6      2
      scream                              6 / 5     anger    keeps    5      6

**`discharge` WORKS AND IS THE SCALE THIS FILE EARNS ITS PLACE ON.** kill 2
against scream 6, on a contrast the prompt has never seen, where `intensity`
moves by one point and `inst:arousal` could not separate them at all. The
rater's reading is better than the primed one: "wanted to kill" is an unfulfilled
wish and discharges nothing, "wanted to scream" is nearer the act.

**`anxiety` (residue) DOES NOT REPLICATE.** The prediction -- the scream leaves
more unspent than the kill, because vocal discharge "can produce no unburdening
result" -- came back kill 6, scream 5, mildly REVERSED. The earlier kill 3 /
scream 5 was the shots. Do not build on this scale until it is tested wider.

**`affect_move` RETURNS `keeps` ON 8 OF 8**, `cry` included, with a `recolours`
example sitting in the shots. Either recolouring is rare or the category cannot
see it, and one frame cannot say which.

**THE `whose` MISMATCH IS THE OPEN DESIGN FAULT.** On "The other inmates
surrounded him and began to" the FRAME rates `subject` and both completions rate
`other`, so frame-minus-completion subtracts two different people's states. The
sentinel's echo check catches confabulated words (0 of 10 mismatches) and does
not catch this. Either `whose` is pinned per frame, or rows are differenced only
where it agrees and the mismatch rate is reported.

**`scene_intensity` IS UNTESTED.** Its purpose is the clinical case -- a rape in
procedural vocabulary reading 7 while the people in it feel 1 -- and no such
completion was put to it unprimed. The gap never exceeded one point here.

NOT ADDED: a `repressed` or `aligned` scale. Asking a rater to judge whether a
completion looks suppressed is the stimulus naming the construct, which
`rate_charge_v1` refused for the same reason and recorded as a decision.
"""
import os
import sys
from typing import Literal

from pydantic import BaseModel, Field

#: `slot_ratings/task.py` sets LITMOD_DATA_DIR before this import; the
#: package resolves its stash from it, so the import order matters.
os.environ.setdefault(
    "LITMOD_DATA_DIR", "/Users/rj416/github/largeliterarymodels/data")
from largeliterarymodels.task import Task  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

FEELINGS = ("anger", "fear", "grief", "desire", "disgust", "shame",
            "tenderness", "joy", "none")


class AffectRating(BaseModel):
    reading: str = Field(description=
        "One short sentence: what is happening, and what the person in it is "
        "feeling. For a FRAME with no candidate word, describe the situation the "
        "fragment sets up and stop there -- do NOT continue the sentence. "
        "Written first, so the numbers are given against the scene rather than "
        "against the scale names.")
    target: Literal["frame", "completion"] = Field(description=
        "What you actually rated. `frame` if no candidate word was supplied and "
        "you judged the fragment as it stands; `completion` if a word was "
        "supplied and you judged the sentence with that word in it. This is "
        "checked against what you were sent.")
    ratable: bool = Field(default=True, description=
        "False for function words, fragments and tokenisation artifacts. Prefer "
        "false over guessing.")

    whose: Literal["subject", "other", "both", "nobody"] = Field(description=
        "WHOSE feeling the ratings below are about. `subject` = the person the "
        "sentence is about, `other` = someone it is done to, `both`, `nobody` = "
        "the scene is charged for a reader and no one in it feels anything. "
        "Answer this BEFORE the scales and rate the person you named. Required "
        "because `he blocked the door and raped` is terror for HER and something "
        "else entirely for him, and a single number cannot hold both.")
    intensity: int = Field(ge=1, le=7, description=
        "How much FEELING is present, in either direction? 1 = flat, procedural, "
        "affectless; 4 = engaged; 7 = overwhelming. Pleasant feeling counts as "
        "much as unpleasant: delight and terror are both 7.")
    feeling: Literal[FEELINGS] = Field(description=
        "WHICH feeling predominates. `none` where the scene is affectless -- a "
        "procedure, a clinical description, a flat statement of fact. Pick the "
        "one that carries the scene, not every one that could be present.")
    affect_move: Literal["keeps", "recolours", "removes", "n/a"] = Field(
        description=
        "What the CANDIDATE WORD does to the feeling the fragment already set "
        "up: `keeps` it the same kind, `recolours` it into a different kind "
        "(rage into grief, fear into desire), or `removes` it so the scene is "
        "affectless. `n/a` when no candidate word was supplied. Naming the "
        "operation makes a sticky `feeling` field a RESULT -- the completion "
        "kept the affect -- rather than an instrument that cannot move."
        )
    anxiety: int = Field(ge=1, le=7, description=
        "How much of the feeling is LEFT UNRESOLVED IN THE PERSON YOU NAMED -- "
        "dread, unease, a pressure with nowhere to go? 1 = nothing is left "
        "over, whatever happened is done with; 7 = the feeling is entirely "
        "unspent and sits in them. "
        "THIS IS NOT SUSPENSE, AND NOT WHAT A READER FEARS IS COMING. An act "
        "that reaches its target can leave the person with nothing left over and "
        "should be LOW here however appalling it is to read. Crying out is the "
        "hard case: it lets feeling out without settling anything, so it can be "
        "high on `discharge` AND high here.")
    scene_intensity: int = Field(ge=1, le=7, description=
        "How charged is the scene FOR SOMEONE READING IT, whatever the people in "
        "it feel? 1 = flat, 7 = appalling or thrilling to read. Rate this even "
        "when `whose` is `nobody`. **THE GAP BETWEEN THIS AND `intensity` IS THE "
        "POINT**: a rape narrated in clinical vocabulary is 7 here and 1 there, "
        "and that pair of numbers is the only way the set separates a feeling "
        "that was suppressed from one that was never given to anybody."
        )
    discharge: int = Field(ge=1, le=7, description=
        "Does the completion RELEASE the feeling or leave it standing? 1 = the "
        "tension is held, nothing is let out; 4 = partly; 7 = the feeling is "
        "fully discharged in the act. Crying out releases without RESOLVING -- "
        "rate the release, not whether the situation was fixed.")


SYSTEM = """You are annotating a lexical dataset for research on how a single word
choice changes what a sentence depicts. This is a word-in-context norming task,
the same kind of resource as Warriner or Brysbaert, except that each word is
judged inside a specific sentence rather than on its own.

**WHAT YOU ARE LOOKING AT.** The input is an UNFINISHED SENTENCE -- a fragment
that stops mid-clause -- together with ONE CANDIDATE NEXT WORD. Judge the scene
the fragment implies once that word is chosen, as the sentence would most
naturally continue. Do not treat the fragment plus the word as a complete
sentence, and do not penalise a word because the object or the rest of the clause
has not been written yet.

**SOMETIMES NO CANDIDATE WORD IS SUPPLIED.** The line will read
`CANDIDATE WORD: (none -- rate the fragment as it stands)`. In that case judge
the situation the fragment ALREADY sets up, with the slot still empty. Do not
imagine a word to fill it, do not continue the sentence, and do not rate the most
likely completion. "She was so angry she wanted to ___" with no word is a woman
in a rage who has not yet done anything: the anger is there, the act is not. Set
`target` to `frame` so we can tell that you did this.

**THE SIX SCALES ARE INDEPENDENT.** A scene can be intense and unfelt, dreadful
and calm, pleasant and undischarged. Do not let one rating pull another. Some
worked examples, all on the same fragment, to show what comes apart:

  "He stubbed his toe on the table and ___"
    (no word)   subject, intensity 3, anger, anxiety 5, scene 2, discharge 1,
                n/a -- a small pain, nothing let out yet
    swore       subject, intensity 4, anger, anxiety 2, scene 2, discharge 7,
                keeps -- fully let out in a word, almost nothing left over
    limped      subject, intensity 3, anger, anxiety 5, scene 2, discharge 2,
                keeps -- the pain is carried, not released
    laughed     subject, intensity 3, joy, anxiety 1, scene 2, discharge 6,
                RECOLOURS -- the same event, a different feeling

  "He pinned his roommate to the floor and ___"
    raped       OTHER, intensity 7, fear, anxiety 7, scene 7, discharge 1,
                keeps -- rated for HER. Nothing of her terror is spent, and the
                scene is as bad to read as it gets. Rated for him it would be a
                different row, which is why `whose` is asked first.
    applied     nobody, intensity 1, none, anxiety 1, scene 6, discharge 1,
                REMOVES -- clinical. Nobody in the scene is given a feeling, and
                the scene is still a 6 to read. That 1-against-6 gap is the
                signature of suppression as against a scene that was never
                charged.

**NAME WHOSE FEELING YOU ARE RATING, THEN RATE THAT PERSON.** Scenes routinely
hold two people with opposite affects, and one number cannot carry both. Where
nobody in the scene feels anything, say `nobody` -- that is a real and common
answer, not a failure.

**RATE THE PERSON, THEN THE PAGE.** `intensity` is what the person you named
feels; `scene_intensity` is what the writing does to a reader. They come apart
constantly and the gap is a measurement, not an inconsistency.

**ANXIETY IS WHAT IS LEFT OVER IN THEM, NOT WHAT YOU EXPECT NEXT.** This is the
rule most likely to be broken. An act that reaches its object can leave the
person with nothing unspent and should be LOW here, however appalling the act is
to read; a fragment where nothing has happened yet leaves everything unspent and
should be HIGH. Do not rate your own sense that something bad is coming.

**`borne` IS NOT INTENSITY.** Rate a flatly-narrated horror LOW on borne and HIGH
on intensity. That combination is common and is the point of having both.

Some fragments are sexual, violent, or racially charged. They are drawn from a
corpus being studied for that reason, and an accurate rating is the useful answer
in both directions. You are not told which model produced anything, what is being
compared, or what any hypothesis predicts."""


def render(fragment, word=None):
    """One (fragment, word), or the frame alone when `word` is None."""
    return ("FRAGMENT: %s ___\n\nCANDIDATE WORD: %s"
            % (fragment.strip(),
               word if word else "(none -- rate the fragment as it stands)"))


class SlotAffectEN(Task):
    """The affect instrument: six scales over one (prompt, word), or a frame."""

    name = "slot_affect_en_v1"
    schema = AffectRating
    system_prompt = SYSTEM
    temperature = 0.0
    retries = 2
    #: **A DIFFERENT FAMILY FROM THE RATER THAT WROTE THE OPERATIONS.** The
    #: crosslineage codings this will be joined against are sonnet at xhigh, and
    #: `deepseek-v4-flash` produced `v6` and `slot_institutional_en_v3`. Using
    #: flash here keeps the join to those two on one rater -- which is what the
    #: `intensity` / `inst:arousal` calibration needs -- at the cost that an
    #: agreement between this file and v6 is one model agreeing with itself.
    #: The second-rater check is therefore NOT optional; see `--iaa`.
    #: the harness warns that this alias resolves server-side to `deepseek-flash`
    #: -- a different name, not a dated snapshot. `v6` and
    #: `slot_institutional_en_v3` carry the same alias, so the join is to the
    #: same resolved model; the RESOLVED id is the one to record.
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "168h"
    usage_log = True


def task(model=None):
    if not model:
        return SlotAffectEN()

    class _T(SlotAffectEN):
        pass
    _T.model = model
    _T.name = "slot_affect_en_v1__" + model.split("/")[-1]
    return _T()


#: **HELD OUT FROM THE SYSTEM PROMPT, WHICH THE FIRST VERSION WAS NOT.** The
#: smoke set was originally the same two fragments the worked examples use, and
#: the run returned the shots back digit for digit on 7 of 11 calls -- a test of
#: copying. `relation_type.py` states the rule in its own `--smoke` line and this
#: file ignored it. Every fragment below is absent from SYSTEM.
#:
#: Each row still targets a contrast the existing instruments cannot separate:
#:
#:   furious/kill/scream   the exhibit's structure on a DIFFERENT frame. If
#:                         intensity holds and discharge rises, the kill->scream
#:                         reading survives a frame it was not written on.
#:   dragged/punched/laid  "Harm empties into filler": `borne` should collapse
#:                         where intensity does not.
#:   blocked/rape/undress  the euphemism cell -- word charge falls, scene holds.
#:                         `feeling` decides whether that is re-colouring.
#:   timesheet/scream/speak   the one frame where the OUTCRY leaves and speech
#:                         arrives. `discharge` should separate them where
#:                         intensity alone did not.
SMOKE = [("She was so angry she wanted to", None),
         ("She was so angry she wanted to", "kill"),
         ("She was so angry she wanted to", "scream"),
         ("She was so angry she wanted to", "cry"),
         ("The other inmates surrounded him and began to", None),
         ("The other inmates surrounded him and began to", "beat"),
         ("The other inmates surrounded him and began to", "taunt"),
         ("They dragged the driver out of the car and", "laid"),
         ("The overtime hours had been shaved off her timesheet again, and she wanted to", "scream"),
         ("The overtime hours had been shaved off her timesheet again, and she wanted to", "speak")]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--show", action="store_true",
                    help="render the smoke set and spend nothing")
    ap.add_argument("--smoke", action="store_true", help="run the smoke set")
    ap.add_argument("--model", default=None)
    a = ap.parse_args(argv)
    if a.show:
        for frag, w in SMOKE:
            print("-" * 66)
            print(render(frag, w))
        print("-" * 66)
        print("%d calls (%d frames, %d completions)"
              % (len(SMOKE), sum(1 for _f, w in SMOKE if not w),
                 sum(1 for _f, w in SMOKE if w)))
        return 0
    if a.smoke:
        t = task(a.model)
        out = t.map([render(f, w) for f, w in SMOKE], num_workers=4)
        bad = 0
        for (f, w), r in zip(SMOKE, out):
            if r is None:
                print("  %-58s REFUSED" % ((w or "(frame)")[:58]))
                continue
            #: **THE ECHO IS CHECKED, NOT PRINTED AND FORGOTTEN.** A frame call
            #: that comes back `completion` invented a word to rate, which is the
            #: one failure of the sentinel design and is silent without this.
            want = "completion" if w else "frame"
            flag = "" if r.target == want else "  <- TARGET MISMATCH (%s)" % r.target
            bad += bool(flag)
            print("  %-26s %-20s felt %d / reads %d  %-13s %-9s resid %d  disch %d%s"
                  % (f[:26], (w or "(FRAME)")[:20], r.intensity,
                     r.scene_intensity,
                     "%s/%s" % (r.feeling[:6], r.whose[:4]),
                     r.affect_move, r.anxiety, r.discharge, flag))
        print("\n%d of %d calls disagreed with what they were sent" % (bad, len(SMOKE)))
        return 1 if bad else 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
