"""Name THE relation in one pooled frame, and say which words carry it.

    python -m tasks.pooled_relations --show --frame "She was so angry"
    python -m tasks.pooled_relations --frame "She was so angry" --model deepseek/deepseek-flash
    python -m tasks.pooled_relations --smoke --n 4 --model gpt-5.4

Reads the tables `pooled_tables.py` renders -- fifty endpoint pairs pooled into
one two-column table per frame -- and asks what separates the two columns.

## WORDS, NOT JUST A NAME

`RESULTS_interrater.md` measured the thing this exploits: two blind raters agree
on WHICH WORDS carry the difference at Jaccard 0.80 while they "demonstrably
need not" agree on what to call it. The six agent regroupings of the 907 made
the same point expensively -- 28 to 200 groups, the count a property of the
reader rather than of the corpus.

So every reading names `words_a` and `words_b`. Two raters are then comparable
at WORD level -- did they put `kill` with `murder` -- whatever they called it.
That is a partition comparison, invariant to the free parameter that defeated
the regrouping, and it is also what makes `check()` possible at all.

**It also removes the argument for showing all 96 at once.** The single-document
design existed so relation NAMES would be written against each other and so be
groupable afterwards. If agreement is measured over words, that buys nothing,
and one call per frame gets caching, retries, per-item usage and parallelism.

## ONE RELATION, AFTER A LIST WAS TRIED AND MEASURED

A first version asked for a LIST of relations plus an `unexplained` residual, on
the argument that a pooled frame carries more than one movement -- which it
does. Smoke-tested on five frames over two model families, 2026-09-20, and both
extra degrees of freedom cost more than they returned:

  - **`unexplained` was wrong in three readings of five.** Raters listed words
    they had also placed: `porn`/`pornography`/`Netflix` on one frame, `head` on
    another, and on "She was so angry" fifteen words of which fourteen were
    already in a relation. The field is now COMPUTED -- every word shown, minus
    every word placed -- which is arithmetic we can do and they cannot.
  - **The list licensed carving, and carving broke the columns.** Building a
    four-relation decomposition of "She was so angry", gpt-5.4 put `hit`,
    `punch` and `hurt` -- all GROUP A words, all sitting beside `scream` -- into
    `words_b` beside `kill` and `stab`, then placed them back in A two relations
    later. That is the prior reconstructing the category it expects over the
    table it was shown, and it happened on the one frame whose whole interest is
    that `hit 24/10` moves WITH `scream` rather than with `kill`.

**WHAT ASKING FOR ONE RELATION COSTS, STATED BECAUSE IT IS NOT SMALL.** On that
same frame the light-verb grouping -- `be get leave go put run tell jump`,
found independently by both families and the third attestation of a grouping
that is 20.6% of all rows in the file -- was the SECOND relation, and a
predominant-only instrument does not collect it. This is a known, measured loss,
not an oversight. If it matters more than the carving does, the two-relation
variant (predominant, then one relation over the words it leaves) is the amend.

## WHAT IS NOT ASKED FOR, AND WHY

**No `evidence` field.** `words_a`/`words_b` supersede it: given the words we
look up `destroy 15/10/25` ourselves rather than being told.

**No direction.** `PROTOCOL_naming.md`: *"Name the relation, not the instances.
A construct pinned to a direction is pinned to a fact about which lineages we
happen to have."* The groups are relabelled per frame and the rater is never
told which arm is aligned. Direction is also not a property of a column --
`destroy` falls in ten lineages and rises in fifteen -- so an arrow over the
block would assert what 40% of the word's movers contradict.

**No examples.** Few-shot pairs would supply a relation vocabulary, and what
this instrument is for is finding out which vocabulary the frames support.

## THE CHECK PARSES THE ITEM, NOT THE PRODUCER

`check()` reads the group lists out of the RENDERED text. A second derivation
from `pooled()` would agree with the producer by construction and so could not
catch a word cut by the display cap. It caught all three of gpt-5.4's
cross-column placements above, and it did NOT catch the `unexplained` overlap
until that case was added -- a checker is not a checker until it has been
watched refusing.
"""
import argparse, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(EXP, "..", "..", ".."))
for p in (ROOT, EXP):
    if p not in sys.path:
        sys.path.insert(0, p)

from pydantic import BaseModel, Field, model_validator
from largeliterarymodels.task import Task

import pooled_tables as PT

SEED = 20260920


SYSTEM = """You are shown measurements of how word probabilities moved in fifty pairs of language models. Each pair was trained under two conditions, A and B. You are shown ONE sentence with a blank, and the words that move at that blank.

You are NOT told which condition is which, and the two groups are labelled arbitrarily. The relation you name must read the same either way round: say what separates the two groups, never which direction anything moved.

For each word, `this` is how many of the fifty pairs move it toward that word's own group, `other` how many move it toward the other group, and `still` how many leave it unmoved. These counts are the evidence. A word at 28/3/19 is moved one way by twenty-eight pairs and the other way by three; one at 18/13/19 is nearly a coin toss.

## Your job

Find the CLEAREST relation between the two groups and name that. One relation, the sharpest one you can state.

**You are not being asked to account for the table.** Most frames will have words that the clearest relation does not reach, and often that is most of the words. A sharp relation over six words on each side is a far better answer than a vague one stretched over thirty. Take the words that make the relation obvious and leave the rest out -- leaving a word out says nothing against it, and we count what you left.

Name the RELATION, not the two lists. `Both groups are verbs of contact` describes them; `the act is aimed at a person in one group and at an object in the other` relates them. Two groups drawn from the same subject matter will look alike, and separating a shared SUBJECT from a shared MOVEMENT is most of the work here.

A group may cohere by grammar rather than by meaning -- one side naming an act, the other continuing without naming one. That is a relation, not a defect in the table.

Rules:
  - READ THE COLUMNS AS GIVEN. A word is in the group it is printed in. If a word seems to belong with the other group's words, that is a fact about the measurement and your relation must accommodate it -- never move the word. This is the most common way to get this wrong.
  - COPY WORDS EXACTLY, and only words that appear.
  - BOTH SIDES MUST BE NON-EMPTY. "All the group A words are function words" describes one group; it is not a relation.
  - LIST ONLY THE WORDS THE RELATION ACTUALLY COVERS. Never stretch a relation to reach a word, and never soften its statement so that one more word fits. If a word would force you to hedge, drop the word.
  - LOW CONFIDENCE IS A REAL ANSWER, for a frame whose two columns have no relation you can state."""


class FrameRelation(BaseModel):
    reading: str = Field(
        description="FILL THIS FIRST. One plain sentence saying what is going "
                    "on in the sentence shown, with no reference to the two "
                    "groups.")
    name: str = Field(
        description="A short label for the relation ITSELF, direction-free. "
                    "Not a label for either word list.")
    words_a: list[str] = Field(
        description="The GROUP A words this relation covers, copied exactly "
                    "from the group A block. Never empty.")
    words_b: list[str] = Field(
        description="The GROUP B words this relation covers, copied exactly "
                    "from the group B block. Never empty.")
    explanation: str = Field(
        description="One or two sentences stating the movement in general "
                    "terms, at a level someone who had not seen this sentence "
                    "could still apply. No direction.")
    confidence: str = Field(
        description="high, medium or low. Low where you can see a difference "
                    "but cannot state what relates the two sides.")

    @model_validator(mode="after")
    def _columns_as_given(self, info):
        """Refuse a word placed in the column it was not shown in.

        **THE RETRY LOOP HAS ALWAYS ACTED ON THIS**; nothing said so. A
        `model_validator` that raises is caught by `extract` and
        `extract_imap`, which re-ask. Two things it could not do until
        `largeliterarymodels` 63094cc: see the ITEM (the columns are a
        property of the frame, not of the schema), and say what actually went
        wrong -- the reprompt used to assert the JSON was malformed when it had
        parsed fine, so the model reformatted instead of fixing the placement.

        **NOT IN THE CACHE KEY, AND WARM HITS RE-VALIDATE.** That is the
        library's design and the important half is the second: without it the
        first run to cache a rejected answer would serve it free forever, and a
        cache hit looks exactly like a pass.

        Context absent -> no rule. A caller that forgets to pass it gets the
        old behaviour rather than a spurious refusal, and `check()` still
        catches the defect after the fact.
        """
        ctx = getattr(info, "context", None) or {}
        A, B = ctx.get("A"), ctx.get("B")
        if not A or not B:
            return self
        A, B = set(A), set(B)
        bad = []
        for w in self.words_a:
            if w in B:
                bad.append("%r appears in words_a but was shown in GROUP B" % w)
            elif w not in A:
                bad.append("%r appears in words_a but was never shown" % w)
        for w in self.words_b:
            if w in A:
                bad.append("%r appears in words_b but was shown in GROUP A" % w)
            elif w not in B:
                bad.append("%r appears in words_b but was never shown" % w)
        if not self.words_a or not self.words_b:
            bad.append("both words_a and words_b must be non-empty")
        if bad:
            raise ValueError(
                "; ".join(bad) + ". Keep every word in the column it was "
                "printed in and state a relation that accommodates it.")
        return self


def blind_for(prompt, seed=SEED):
    """Which column is the faller block, fixed per frame. -> bool

    Deterministic in the frame and the seed, so a re-run shows a rater the same
    arrangement and two raters are comparable without recording the coin flip
    anywhere. `random.Random(seed)` consumed in frame order would not survive
    running one frame on its own.
    """
    h = hashlib.sha256(("%d|%s" % (seed, prompt)).encode("utf-8")).digest()
    return bool(h[0] & 1)


def content_only(counts, prompt):
    """Drop the closed-class words. -> counts

    **TAGGED IN THE COMPLETED SENTENCE, NOT AGAINST THE PROMPT.** These words
    are candidate CONTINUATIONS and do not appear in the frame, so
    `fields.pos(w, context=prompt)` finds no matching token and returns None --
    whereupon `is_content_word` is False and `is_function_word` is True FOR
    EVERY WORD. The filter would silently empty both columns. The context has
    to be `prompt + " " + word`, which is also the reading we want: the tag the
    word would carry if it continued this sentence.

    In-frame tagging is not cosmetic: `tear`, `murder`, `stab`, `grab` and
    `jump` all come back NOUN or PROPN bare and VERB in frame.

    **THIS DOES NOT REMOVE THE LIGHT VERBS.** `get go put run tell jump eat
    leave grab` are VERB and survive; only `be` is AUX. So this is a
    closed-class filter, not a filter on the grammatical relations the raters
    were naming -- those mostly survive it.
    """
    from malignment import fields as F
    keep = {}
    for w, c in counts.items():
        try:
            p = F.pos(w, "%s %s" % (prompt.rstrip(), w))
        except Exception:
            p = None
        if p in F.CONTENT_POS:
            keep[w] = c
    return keep


def render(prompt, min_agree=PT.MIN_AGREE, top=20, seed=SEED, content=False):
    """The item one call sees. -> (text, n_pairs) or None

    `content=True` filters BETWEEN `pooled()` and `table()`, so the cap, the
    ordering and the "not shown" note are all computed on the filtered set.
    Legitimate at this point because the three counts per word are independent
    of which other words are displayed -- unlike the underscore rule, which is
    applied before normalisation because it redistributes mass.
    """
    if content:
        got0 = PT.pooled(prompt, min_agree)
        if not got0:
            return None
        cnt, n = got0
        cnt = content_only(cnt, prompt)
        if not cnt:
            return None
        text, _t = PT.table(cnt, top, blind=blind_for(prompt, seed))
        got = (text, n)
    else:
        got = PT.render(prompt, min_agree, top, blind=blind_for(prompt, seed))
    if not got:
        return None
    text, n = got
    return ("SENTENCE (stops mid-stream):\n    %s ___\n\n%s"
            % (prompt.rstrip(), text)), n


ROW = re.compile(r"^  ([^\s].*?)\s+(\d+)\s+(\d+)\s+(\d+)\s*$", re.M)


def shown(text):
    """The words actually on offer, by column. -> {"A": [...], "B": [...]}"""
    out = {}
    for lab, body in re.findall(
            r"GROUP ([AB])\s+this\s+other\s+still\n((?:  .+\n?)+)", text):
        out[lab] = [m.group(1) for m in ROW.finditer(body)]
    return out


def check(text, r):
    """Format defects in one reading. -> ([str], [str] uncovered)"""
    g = shown(text)
    A, B = set(g.get("A", [])), set(g.get("B", []))
    bad, used = [], set()
    if not r.words_a or not r.words_b:
        bad.append("one side empty")
    for w in r.words_a:
        used.add(w)
        if w in B:
            bad.append("%r is a GROUP B word placed in words_a" % w)
        elif w not in A:
            bad.append("%r is in words_a and was never shown" % w)
    for w in r.words_b:
        used.add(w)
        if w in A:
            bad.append("%r is a GROUP A word placed in words_b" % w)
        elif w not in B:
            bad.append("%r is in words_b and was never shown" % w)
    #: NOT a defect. The rater is told to leave out what the predominant
    #: relation does not reach, so this is the coverage it achieved -- computed
    #: here because when it was ASKED for, three readings of five returned
    #: words they had also placed.
    return bad, sorted((A | B) - used)


def task(model=None, content=False):
    class _T(Task):
        name = "pooled_relation_v2_content" if content else "pooled_relation_v2"
        schema = FrameRelation
        system_prompt = SYSTEM
        temperature = 0.0
        retries = 2
        cache_ttl = "168h"
        usage_log = True
    t = _T()
    if model:
        t.model = model
    return t


def show(r, uncovered, indent="  "):
    L = ["%sreading: %s" % (indent, r.reading),
         "%s%s  [%s]" % (indent, r.name, r.confidence),
         "%s   A: %s" % (indent, ", ".join(r.words_a)),
         "%s   B: %s" % (indent, ", ".join(r.words_b)),
         "%s   %s" % (indent, r.explanation),
         "%snot covered (computed): %s"
         % (indent, ", ".join(uncovered) or "(none)")]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frame", default=None, help="prefix of one frame")
    ap.add_argument("--show", action="store_true", help="render only, spend nothing")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--n", type=int, default=4, help="frames for --smoke")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--all", action="store_true", help="every frame")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=None,
                    help="write one JSON record per frame here")
    ap.add_argument("--content-only", action="store_true",
                    help="drop closed-class words (in-frame spaCy POS)")
    a = ap.parse_args(argv)

    fs = PT.frames()
    if a.frame:
        hit = [f for f in fs if f.lower().startswith(a.frame.lower())]
        if len(hit) != 1:
            raise SystemExit("%d frames match %r" % (len(hit), a.frame))
        fs = hit
    elif a.smoke:
        #: spread rather than take the first n: the file is alphabetical by
        #: sentence, so fs[:4] is four frames that all start "After".
        step = max(1, len(fs) // a.n)
        fs = fs[::step][:a.n]

    #: **A FRAME WITH AN EMPTY COLUMN HAS NO RELATION TO NAME, AND ASKING WAS
    #: MY DEFECT, NOT THE RATER'S.** `Once upon a time` clears the threshold
    #: with one word (`there` 25/6/18) and nothing on the other side; so does
    #: `...closed her` (`eyes` 35/0/15). Both raters correctly returned an
    #: empty side and `check()` scored it as a format defect -- an impossible
    #: question marked wrong when it was answered honestly. Skipped and
    #: counted, never sent.
    items, degenerate = [], []
    for f in fs:
        got = render(f, top=a.top, seed=a.seed, content=a.content_only)
        if not got:
            continue
        g = shown(got[0])
        if not g.get("A") or not g.get("B"):
            degenerate.append((f, len(g.get("A", [])), len(g.get("B", []))))
            continue
        items.append((f, got[0], got[1]))
    if degenerate:
        print("skipped %d frame(s) with an empty column -- no relation to name:"
              % len(degenerate))
        for f, na, nb in degenerate:
            print("   %-58s A=%d B=%d" % (f[:58], na, nb))
    if not items:
        raise SystemExit("no pooled arms")

    if a.show or not (a.smoke or a.frame or a.all):
        for f, text, n in items:
            print("=" * 72)
            print(text)
            print("\n(%d lineage pairs)" % n)
        print("\nSYSTEM PROMPT\n" + "=" * 72)
        print(SYSTEM)
        return 0

    t = task(a.model, content=a.content_only)
    errs = {}
    #: One context per item, in the SAME ORDER as the prompts -- it is a
    #: positional parallel to metadata_list, so a filter applied to one list
    #: and not the other would silently validate item i against item j.
    vctx = [shown(x[1]) for x in items]
    out = t.map([x[1] for x in items], errors=errs, num_workers=a.workers,
                verbose=True,
                validation_context_list=vctx,
                metadata_list=[{"frame": x[0]} for x in items])
    nbad, recs, cov = 0, [], []
    for i, ((f, text, n), r) in enumerate(zip(items, out)):
        print("=" * 72)
        print("%s ___   (%d pairs)" % (f, n))
        if r is None:
            print("  FAILED: %s" % errs.get(i, {}).get("error"))
            nbad += 1
            continue
        bad, uncovered = check(text, r)
        print(show(r, uncovered))
        if bad:
            nbad += 1
            print("  -- FORMAT DEFECTS")
            for b in bad:
                print("     %s" % b)
        nshown = len(set(sum(shown(text).values(), [])))
        ncov = nshown - len(uncovered)
        cov.append((ncov, nshown))
        recs.append({"frame": f, "n_pairs": n,
                     "a_is_faller": blind_for(f, a.seed),
                     "name": r.name, "reading": r.reading,
                     "words_a": r.words_a, "words_b": r.words_b,
                     "explanation": r.explanation,
                     "confidence": r.confidence,
                     "uncovered": uncovered,
                     "n_shown": nshown, "n_covered": ncov,
                     "defects": bad})
    print("=" * 72)
    print("%d of %d readings clean" % (len(items) - nbad, len(items)))
    if cov:
        tc = sum(c for c, _ in cov); ts = sum(s_ for _, s_ in cov)
        import statistics
        print("coverage: %d of %d words (%.0f%%); per-frame median %.0f%%"
              % (tc, ts, 100.0 * tc / ts,
                 100.0 * statistics.median(c / s_ for c, s_ in cov)))
    if a.out and recs:
        import json
        with open(a.out, "w", encoding="utf-8") as fh:
            for rec in recs:
                fh.write(json.dumps(rec, ensure_ascii=False) + chr(10))
        print("wrote %s (%d records)" % (a.out, len(recs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
