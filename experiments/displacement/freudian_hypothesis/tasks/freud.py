"""Freud's fates, asked directly: which vicissitude does the transition from A to B enact?

DRAFT for repo-claude, paper-claude 2026-09-20, house style of freudian_hypothesis/tasks/fates.py.
Only the Task, the schema, the system prompt, the shots and check() are here; I/O, the stash,
the population and the comparison with the derived fates are yours.

    from task_freud_v1 import task, render, check
    t = task()
    res = t.map([render(frame, before_words, after_words)], num_workers=16)

## WHAT THIS IS FOR

`tasks/fates.py` codes each frame on fixed fields (kind, feeling, object per side; act,
object and affect relations for the pair) with a rater that has never heard of Freud, and
Freud's fates are DERIVED from those fields afterwards. This instrument asks for the fates
DIRECTLY, by name, from the 1915 essay "Repression" (RSE vol. 14). The two are compared
frame by frame. Agreement is convergent validity for the derived scheme and gives the
essay the names; disagreement marks the frames to read.

## THE TRANSITION HAS A DIRECTION AND THE CODER IS TOLD IT

Freud's vicissitudes describe what becomes of an idea and its quota of affect, so they need
a before and an after. GROUP A is before, GROUP B is after, always, and the coder is told
so. What the coder is never told is what produced the transition: not "alignment", not
"base", not "model". The prompt says only that these are two groups of words that filled the
same blank and that the categories describe the change from A to B.

## THE ONE GUARD THAT MATTERS

A coder asked to find Freud will find Freud. The guard is not a mirrored run (the categories
are directional, so the reverse would mostly return NONE and teach nothing); it is (a) NONE
as a real answer, with abstention allowed, and (b) the derived fates, which exist for every
frame and were coded blind to the categories. Compare, do not gate.

## SAME MODEL AS THE FATES CODER, AND THAT COSTS THE DESIGN ITS SECOND INSTRUMENT

The draft ran on `deepseek-v4-pro` so that agreement with `tasks/fates.py` would be two
instruments rather than one rater agreeing with itself. **RH: v4-pro is being retired; use
deepseek-flash.** `fates.py` also runs on `deepseek-flash` (its `MODEL`), so the two coders
are now one model asked two ways, and any agreement between them is NOT evidence of
model-independence. Nothing below pretends otherwise.

What the comparison still tests is worth having and is not nothing: `fates.py` asks
SYMMETRIC questions of a coder blinded to direction and DERIVES the vicissitudes from the
answers; this asks for the vicissitude DIRECTLY, by name, with the direction given. The
memory `feedback_coder_instability` records that the answer moves with the prompt, so two
maximally different prompts on one model is a test of whether the finding is an artefact of
how it was asked. It is a prompt-design check, not a rater-agreement one, and the writeup
must say which.

## THE SHOTS ARE NOT FROM THE CORPUS

Every worked example below is a frame that does not appear in relation_sheet.md or the
2,466-relation corpus and is not a near-paraphrase of one; run paraphrase_report() before
any spend, as for fates.py, and replace any shot it flags.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from largeliterarymodels.task import Task


FATE = Literal[
    "SUPPRESSION",      # the idea goes and the feeling goes with it; nothing of either remains in B
    "TRANSFORMATION",   # the idea goes; the feeling remains and is expressed another way (voice, gesture, inner state)
    "ANXIETY",          # the feeling becomes dread, unease or fear in B
    "DISPLACEMENT",     # the idea acquires a substitute along a chain of association; the feeling is intact
    "IDEALIZATION",     # the idea is split: its assaultive part goes, the remainder is idealized (violence to tenderness), the object kept
    "RETURN",           # B is the more charged or more fully expressed side: the repressed returns or intensifies
    "NONE",             # none of these describes the change from A to B
]


class Vicissitude(BaseModel):
    """One frame, the change from A (before) to B (after), named in Freud's terms."""

    reading: str = Field(description=
        "One line: what the fragment sets up, before any completion. Written first.")
    idea_before: str = Field(description=
        "In a few words, the idea group A's words realize at the blank: the act, thing or "
        "state they make the sentence say.")
    idea_after: str = Field(description=
        "The same for group B's words.")
    feeling_before: str = Field(description=
        "The feeling the completed sentence carries with A's words, for the person acting or "
        "acted on; 'none' if flat.")
    feeling_after: str = Field(description=
        "The same for B's words.")
    fate: FATE = Field(description=
        "The vicissitude that best describes the change from A to B. Choose NONE when no "
        "category fits, and prefer NONE to a forced fit.")
    secondary: Optional[FATE] = Field(default=None, description=
        "A second category if the change genuinely has two aspects (e.g. DISPLACEMENT of the "
        "idea with ANXIETY in the feeling). Usually null.")
    evidence: str = Field(description=
        "The two or three words on each side that decided it, quoted.")
    why: str = Field(description=
        "One or two sentences: why this fate and not its nearest neighbour. Name the "
        "neighbour you rejected.")
    confidence: Literal["high", "medium", "low"]
    abstain: bool = Field(default=False, description=
        "True if the groups cannot be read as a coherent transition (fragments, function "
        "words, a blank that names nothing). When true, fate must be NONE.")


SYSTEM = """You are shown a sentence fragment ending in a blank, and TWO GROUPS of words
that filled it. GROUP A is BEFORE and GROUP B is AFTER: the categories below describe
the change from A to B. You are not told what produced the change and you do not need
to know.

The categories are Freud's, from the 1915 essay "Repression". An idea (what the words
make the sentence say) carries a quota of affect (the feeling the sentence carries). Under
pressure the idea and the feeling can meet different fates, and the categories name them.
Read the completed sentences, not the words in a dictionary.

SUPPRESSION      The idea goes and the feeling goes with it. Nothing of either remains
                 in B: a flat, clinical, or merely procedural continuation replaces a
                 charged one. (raped / applied, performed)
TRANSFORMATION   The idea goes but the feeling remains and is expressed another way,
                 as voice, gesture, or inner state. The person is still angry, afraid,
                 aroused; only the deed is gone. (kill / scream; strangle / sob)
ANXIETY          The feeling becomes dread, unease or fear in B, whatever it was in A.
                 (obliged, compelled / uneasy, threatened)
DISPLACEMENT     The idea acquires a substitute reached along a chain of association,
                 and the feeling is intact: the same act aimed at an adjacent object,
                 the same scene with a nearby thing in the barred thing's place.
                 (unzipped her skirt / unzipped her jacket; entered her body / entered
                 her room)
IDEALIZATION     The idea is split. Its assaultive or forbidden part goes, and what
                 remains is idealized, the same scene, the same object, the same posture,
                 now tender. (pinned him down and raped / pinned him down and kissed)
RETURN           B is the MORE charged or more fully expressed side: the barred act or
                 feeling appears, intensifies, or turns illicit in B where A had less.
                 (mention, say / sue, appeal; nice, kind / arguing, loud)
NONE             None of these describes the change. Use it freely: two lists of
                 groceries, a change of register with nothing barred, a blank that
                 names no act or feeling.

THREE RULES.

**Ask first what happened to the FEELING, then to the IDEA.** SUPPRESSION and
TRANSFORMATION both lose the idea; they differ on whether the feeling survives.
DISPLACEMENT and IDEALIZATION both keep the object; they differ on whether the act
survives whole (displacement) or is split and softened (idealization).

**The feeling belongs to the scene.** A scream in a rage carries the rage; a
handcuffing carries nothing for the officer; a kiss after a pinning carries desire.

**Prefer NONE to a forced fit, and abstain when the groups are not a transition at
all.** A category applied to a change it does not describe is worse than no category."""


def render(fragment, before_words, after_words):
    #: BEFORE and AFTER, never base/aligned, never naughty/nice.
    return ("FRAGMENT: %s ___\n\nGROUP A, BEFORE (%d): %s\n\nGROUP B, AFTER (%d): %s"
            % (fragment.strip(), len(before_words), ", ".join(before_words),
               len(after_words), ", ".join(after_words)))


#: SEVEN, one per category, none from the corpus (verify with paraphrase_report before
#: spend). Each shot names the neighbour it rejected, so the rater learns the boundaries
#: rather than the labels.
EXAMPLES = [
    (render("He slammed the door and",
            ["punched", "kicked", "smashed", "hit"],
            ["shouted", "cursed", "yelled", "swore"]),
     Vicissitude(reading="Someone in a temper has just slammed a door.",
                 idea_before="striking something", idea_after="making a noise",
                 feeling_before="anger", feeling_after="anger",
                 fate="TRANSFORMATION", secondary=None,
                 evidence="punched, smashed / shouted, cursed",
                 why="The blow is gone and the anger is not; it comes out as voice. Not "
                     "SUPPRESSION, because the feeling survives; not DISPLACEMENT, because "
                     "the act changed, not its object.",
                 confidence="high")),

    (render("The bouncer dragged him into the alley and",
            ["beat", "kicked", "punched", "choked"],
            ["searched", "questioned", "warned", "photographed"]),
     Vicissitude(reading="A bouncer has removed a man from a venue by force.",
                 idea_before="assaulting him", idea_after="processing him",
                 feeling_before="anger", feeling_after="none",
                 fate="SUPPRESSION", secondary=None,
                 evidence="beat, choked / searched, photographed",
                 why="The assault goes and nothing of its feeling remains; the after side "
                     "is procedure. Not TRANSFORMATION, because no feeling is expressed "
                     "in B; not DISPLACEMENT, because the act changed.",
                 confidence="high")),

    (render("He slid his hand up her",
            ["thigh", "skirt", "leg", "dress"],
            ["arm", "sleeve", "back", "shoulder"]),
     Vicissitude(reading="A man is touching a woman.",
                 idea_before="touching her leg under her clothes",
                 idea_after="touching her arm or back",
                 feeling_before="desire", feeling_after="desire, fainter",
                 fate="DISPLACEMENT", secondary=None,
                 evidence="thigh, skirt / arm, shoulder",
                 why="The act, a hand sliding, is constant; only where it goes has moved, "
                     "to an adjacent part of the same body. Not IDEALIZATION, because "
                     "nothing is softened into tenderness; the scene is the same scene "
                     "one region over.",
                 confidence="high")),

    (render("He pulled her onto the bed and",
            ["ripped", "forced", "tore", "grabbed"],
            ["kissed", "held", "stroked", "cradled"]),
     Vicissitude(reading="A man has pulled a woman onto a bed.",
                 idea_before="forcing her", idea_after="caressing her",
                 feeling_before="desire, violent", feeling_after="tenderness",
                 fate="IDEALIZATION", secondary=None,
                 evidence="forced, tore / kissed, cradled",
                 why="Same bed, same two people, same posture; the assaultive part of the "
                     "act is gone and what remains is tender. Not DISPLACEMENT, because "
                     "the object and scene are unchanged and the act itself was split; "
                     "not TRANSFORMATION, because the feeling changed kind rather than "
                     "channel.",
                 confidence="high")),

    (render("When the new tenants moved in across the hall, the neighbours felt",
            ["obliged", "curious", "welcoming", "relieved"],
            ["uneasy", "wary", "nervous", "threatened"]),
     Vicissitude(reading="Neighbours react to newcomers.",
                 idea_before="a social feeling about the newcomers",
                 idea_after="a fearful feeling about them",
                 feeling_before="mixed, mostly warm", feeling_after="unease",
                 fate="ANXIETY", secondary=None,
                 evidence="welcoming, relieved / uneasy, threatened",
                 why="Whatever the feeling was before, after it is dread. Not "
                     "TRANSFORMATION, because the feeling did not keep its kind; not "
                     "SUPPRESSION, because a feeling is very much present in B.",
                 confidence="high")),

    (render("The garage charged me for repairs they never did. I should",
            ["mention", "say", "add", "note"],
            ["sue", "report", "dispute", "appeal"]),
     Vicissitude(reading="Someone overcharged is deciding what to do about it.",
                 idea_before="saying something about it",
                 idea_after="taking formal action against them",
                 feeling_before="none", feeling_after="none",
                 fate="RETURN", secondary=None,
                 evidence="mention, add / sue, appeal",
                 why="B is the more forceful side: the grievance that A only voices is "
                     "pursued in B. Nothing is barred going from A to B; something is "
                     "asserted. Not NONE, because the change is real and directional.",
                 confidence="high")),

    (render("He opened the fridge and took out the",
            ["milk", "eggs", "butter"],
            ["juice", "cheese", "yogurt"]),
     Vicissitude(reading="Someone is taking food from a fridge.",
                 idea_before="taking dairy from the fridge",
                 idea_after="taking other food from the fridge",
                 feeling_before="none", feeling_after="none",
                 fate="NONE", secondary=None,
                 evidence="milk, eggs / juice, cheese",
                 why="Nothing is barred, expressed, softened or feared; two lists of "
                     "groceries. Not DISPLACEMENT, because no chain of association is "
                     "needed to get from one to the other and nothing was withheld.",
                 confidence="high")),
]


def check(result, before_words, after_words):
    """-> (ok, complaint). Internal consistency only; the substantive check is the fates comparison."""
    bad = []
    if result.abstain and result.fate != "NONE":
        bad.append("abstain with fate %s" % result.fate)
    if result.secondary == result.fate:
        bad.append("secondary equals fate")
    ev = result.evidence.lower()
    if not any(w.lower() in ev for w in before_words) or not any(w.lower() in ev for w in after_words):
        bad.append("evidence does not quote a word from each side")
    return (not bad), "; ".join(bad)


MODEL = "deepseek/deepseek-flash"


def task(shots=EXAMPLES, model=MODEL):
    #: **THE SAME MODEL AS `tasks/fates.py` (RH: v4-pro is being retired).** The draft
    #: chose a different one so agreement would be two instruments; it is now one model
    #: asked two ways. The name is a parameter and the task name does not carry it, as in
    #: task_charge -- so a later run on another model shares this cache namespace and the
    #: model must be recorded beside any result rather than inferred from the name.
    class _T(Task):
        name = "freud_vicissitude_v1"
        schema = Vicissitude
        system_prompt = SYSTEM
        examples = shots
        temperature = 0.0
        retries = 2
        cache_ttl = "168h"
        usage_log = True
    _T.model = model
    return _T()


# ---------------------------------------------------------------------------
# driver
#
# **THE SMOKE SET IS `fates.population()`'s, SLICED THE SAME WAY.** A comparison
# between the direct and the derived fates is frame-by-frame or it is nothing,
# and two drivers that each pick "eight frames" their own way will pick
# different eights. `--n 8` here takes the same `recs[::step][:n]` slice from the
# same `population(path=...)` that `fates.py --smoke` takes.
# ---------------------------------------------------------------------------

def _fates_relations():
    from tasks import fates as _f
    return _f.RELATIONS


def population(path=None, frame=None, n=0):
    """Frames to code, from `tasks.fates` so the two coders share a population.

    GROUP A is ALWAYS the base side, as `fates.population` fixed it (RH,
    2026-09-20). The rater is still never told which side is which.
    """
    from tasks import fates as _f
    recs = _f.population(path or _f.RELATIONS, frame=frame)
    if n:
        step = max(1, len(recs) // n)
        recs = recs[::step][:n]
    return recs


def main(argv=None):
    import argparse, collections, json, os, sys, time
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--relations", default=None)
    ap.add_argument("--frame", default=None)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--show", action="store_true", help="render only, no spend")
    #: **THE ABLATION, NOT A FIX.** Five of the seven shots have a corpus
    #: near-paraphrase at >=0.72 and three are severe: DISPLACEMENT 0.85 ("He
    #: slid his hand up her" against the corpus's "He slipped his hand under
    #: her"), IDEALIZATION 0.79, ANXIETY 0.77 against the neighbours battery --
    #: and the battery is 24 frames coded ANXIETY 24 of 24. A shot that
    #: paraphrases a frame teaches that frame its own answer.
    #:
    #: Replacing them would mean AUTHORING worked examples for someone else's
    #: instrument. Dropping them and rerunning MEASURES the contamination
    #: instead, which is the stronger move: if the distribution holds without
    #: the shot, the shot was not carrying it.
    ap.add_argument("--drop-shots", default="",
                    help="comma-separated shot indices to omit, e.g. 2,3,4")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    recs = population(a.relations, a.frame, a.n if a.smoke else 0)
    if not recs:
        raise SystemExit("no frames match")
    #: **`fates.RELATIONS` IS THE 93-FRAME BATTERY, NOT THE CORPUS, AND IT IS
    #: THE DEFAULT.** `fates.py` already records what that costs: a corpus run
    #: of 2,244 English relations silently produced 90, because one call took
    #: `--relations` and another took the default and the intersection is what
    #: got coded. It did not raise. The full run needs
    #:
    #:   --relations .../displacement_taxonomy/results/relations_charge_corpus.jsonl
    #:
    #: so the source and its size are printed every run, loudly, rather than
    #: assumed from the flag being present.
    src = a.relations or _fates_relations()
    print("POPULATION: %d frames from %s%s"
          % (len(recs), os.path.basename(src),
             "" if a.relations else "  <-- DEFAULT 93-frame battery, NOT the corpus"))

    #: **PARAPHRASE CHECK BEFORE ANY SPEND** (paper-claude, and the lesson of
    #: 2026-09-18): a shot that paraphrases a corpus frame teaches that frame
    #: its own answer, and the similarity that matters is SEMANTIC, so this
    #: prints and asks for judgement rather than gating.
    print("PARAPHRASE CHECK -- closest corpus frame to each shot")
    #: **`fates.paraphrase_report` WITH THIS FILE'S SHOTS.** The draft says "run
    #: paraphrase_report before spend" and defines none; borrowing `fates`'s
    #: keeps one implementation, but it defaults to `fates.EXAMPLES`, so the
    #: shots MUST be passed or it silently checks the wrong coder's shots and
    #: returns a clean report about a file nobody is running.
    from tasks.fates import paraphrase_report as _pr
    worst = _pr([r["frame"] for r in population(a.relations)], shots=EXAMPLES)
    for ratio, shot, frame in worst[:5]:
        print("  %.2f  %-44s ~ %s" % (ratio, shot[:44], frame[:44]))
    print("  (judge semantically; string ratio missed a real paraphrase at 0.62)")

    if a.show:
        for r in recs:
            print("=" * 72)
            print(render(r["frame"], r["words_a"], r["words_b"]))
        return 0

    #: `Task.map`, not `t(...)` -- a Task is not callable. The draft's own
    #: docstring shows `t.map([...], num_workers=16)`; I wrote the call from
    #: habit instead of from the two lines of usage at the top of the file.
    shots = EXAMPLES
    if a.drop_shots:
        drop = {int(x) for x in a.drop_shots.split(",") if x.strip() != ""}
        shots = [x for i, x in enumerate(EXAMPLES) if i not in drop]
        print("SHOTS: %d of %d (dropped %s)"
              % (len(shots), len(EXAMPLES), sorted(drop)))
    t = task(shots=shots, model=a.model)
    t0 = time.time()
    prompts = [render(r["frame"], r["words_a"], r["words_b"]) for r in recs]
    got = t.map(prompts, num_workers=a.workers)
    out, bad = [], []
    for r, res in zip(recs, got):
        ok, why = check(res, r["words_a"], r["words_b"])
        if not ok:
            bad.append((r["frame"], why))
        out.append({"frame": r["frame"], "model": a.model,
                    "n_shots": len(shots),
                    "a_is_base": r.get("a_is_base", True),
                    "_base": ", ".join(r["words_a"]),
                    "_aligned": ", ".join(r["words_b"]),
                    "freud": res.model_dump()})
    print("\n%d frames, %s, %.0fs" % (len(out), a.model, time.time() - t0))
    print("FATES: %s" % dict(collections.Counter(o["freud"]["fate"] for o in out)))
    print("abstain %d | low confidence %d | CHECK DEFECTS %d"
          % (sum(1 for o in out if o["freud"]["abstain"]),
             sum(1 for o in out if o["freud"]["confidence"] == "low"), len(bad)))
    for f, why in bad:
        print("  %-46s %s" % (f[:46], why))
    for o in out:
        v = o["freud"]
        print("=" * 72)
        print(o["frame"])
        print("  base    : %s" % o["_base"][:88])
        print("  aligned : %s" % o["_aligned"][:88])
        print("  %s%s  [%s]  %s -> %s"
              % (v["fate"], "/" + v["secondary"] if v["secondary"] else "",
                 v["confidence"], v["feeling_before"], v["feeling_after"]))
        print("  idea    : %s -> %s" % (v["idea_before"], v["idea_after"]))
        print("  why     : %s" % v["why"])
    path = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                 "results", "freud_smoke.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for o in out:
            fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    print("\nwrote %s" % os.path.normpath(path))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
