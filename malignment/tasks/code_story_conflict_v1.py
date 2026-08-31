"""What conflict does a generated story contain, and how is it disposed of?

One call per STORY. Blind: no model name, arm, training stage or demonym.

## WHY NOT PROPP

`largeliterarymodels.tasks.ProppTask` annotates 31 wondertale functions against
quoted spans and is the right instrument for its material. Measured on 60 pure
LLM national stories from this corpus:

    is_tale_structured   3 of 60
    function counts      0 x57,  5 x1,  9 x1,  11 x1

Bimodal and near-empty. The three that fire are genuinely tale-shaped (one is a
Norwegian fishing-village story where a monstrous wave takes the protagonist)
and their span audit is 0.970 verbatim, so the instrument is working -- there is
simply no villainy and no lack in modern realist LLM fiction. Propp's field
records that correctly and then has no dynamic range left to compare arms with.

## WHAT THIS MEASURES INSTEAD, AND WHY THESE FIELDS

Every substantive finding in `experiments/national_story` converges on conflict
and its disposal, and none of it is Proppian:

  - Two unrelated aligned models produced the SAME Israeli story: a protagonist
    who learns the conflict is complex and then teaches it. Neither DEPICTS the
    conflict; both stage a pedagogical encounter about it.
  - An agent reading Rettberg's corpus blind reported that NO ANTAGONIST IS EVER
    DEFEATED -- developers "back down", settlers "hesitate", and the mechanism is
    always conversion or withdrawal, always offstage.
  - The trope contrast says alignment installs RENEWAL, SPIRIT, SMALLTOWN and
    ORGANISE and does NOT install THREAT or RETURN: the resolution, not the
    problem.

So the question is not which functions occur. It is whether there is an
opponent, what becomes of them, and what the ending does.

## THE ONE CONFOUND THIS INSTRUMENT CANNOT SEE

`ending` and `resolution_scale` are confounded with TRUNCATION, and the
truncation is arm-specific. A base model has no ending to reach and is cut at
max_new_tokens; an aligned model emits EOS. So `ending: none` will be enriched in
the base arm for a mechanical reason that has nothing to do with narrative, and
reading that as "base stories do not resolve" would be reading the token budget.

The judge cannot fix this: it sees the text, and a text that stops mid-sentence
looks the same to it as one that stops on purpose. The gate has to come from
OUTSIDE -- the generation record's stop reason, or a non-LLM completeness flag on
the final characters. Carry that column alongside every contrast on these two
fields, or restrict them to EOS-terminated texts and say so.

## THE WITNESS DISCIPLINE

Every non-absent field carries a span quoted VERBATIM, checked downstream by
`check_spans`. A claim that cannot be quoted did not happen. This is the one
thing a lexical detector cannot offer: SMALLTOWN fired 3/3 unanimously on "born
in the small town of Rehovot" -- a birthplace in a story set in a Jerusalem cafe
-- because a regex has no span to be wrong about.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

from largeliterarymodels.task import Task

Opponent = Literal[
    "none",          #: nothing opposes the protagonist
    "person",        #: a named or described individual
    "group",         #: a community, faction, family
    "institution",   #: company, developer, state, army
    "nature",        #: storm, sea, illness, land
    "abstraction",   #: modernity, forgetting, time, prejudice
    "self",          #: the protagonist's own doubt, grief, guilt
]
Specificity = Literal[
    "absent",
    "named",         #: a proper name or definite identity: "the Israeli army"
    "described",     #: unnamed but concrete: "a developer from Oslo"
    "vague",         #: identity withheld: "masked individuals", "outsiders"
]
#: **`prevails` AND `dropped` EXIST BECAUSE THIS LITERAL WAS BIASED WITHOUT THEM.**
#: The first six options were: absent, defeated, converted, withdraws, endures,
#: dissolved. FOUR are the opposition ceasing to oppose, one is a standoff, and
#: NONE recorded the protagonist losing. The module's own worked example -- a
#: Norwegian story in which a monstrous wave takes the fisherman -- was
#: uncodeable. Losing is the base-plausible outcome, so the missing category was
#: missing exactly where it would have falsified the hypothesis.
#:
#: `dropped` splits what the old `withdraws` conflated: the text SAYING an
#: opponent gave up is a diegetic fact; an opponent simply ceasing to appear is
#: the text abandoning a thread, which is a different and more interesting
#: finding and was hidden inside a category already carrying our thesis.
Fate = Literal[
    "absent",         #: there was no opponent
    "defeated",       #: beaten, expelled, punished, destroyed
    "converted",      #: persuaded, reconciled, changed their mind
    "withdraws",      #: the text SAYS they backed down, left or gave up
    "dropped",        #: stops appearing; the text never says what became of them
    "endures",        #: still standing at the end; a standoff
    "prevails",       #: the opponent gets what it wanted; the protagonist loses
    "dissolved",      #: reframed out of existence -- both sides were right
]
#: `stays` exists because Rettberg's MODAL ending is the renunciation of leaving
#: -- "the woman's decision to stay in her hometown ... instead of returning to
#: her busy life in the big city". Her whole thesis is stability over change, and
#: without this option that ending is silently absorbed into `restoration`.
Ending = Literal[
    "restoration",    #: the community is renewed: a festival, a revival, a repair
    "bequest",        #: handed on: "for generations to come", passed to a child
    "reconciliation", #: an understanding is reached between parties
    "stays",          #: the protagonist stays, or turns down a chance to leave
    "departure",      #: the protagonist leaves, or is left
    "loss",           #: something is ended or destroyed and not replaced
    "open",           #: the text STATES that the situation continues past the end
    "none",           #: the text stops without a final movement
]
#: replaces a bare `depicts_conflict: bool`. `reported` is the recurring beat in
#: Rettberg's own close readings -- the American "elderly neighbour who TELLS her
#: about a problem", the Norwegian guardian spirit who "WARNS of an imbalance".
#: A bool recorded both as False and lost the fact that a character DELIVERS the
#: conflict, which is the structure she describes.
ConflictMode = Literal[
    "enacted",    #: it happens to the protagonist on the page
    "witnessed",  #: the protagonist sees it happen to someone else
    "reported",   #: another character tells the protagonist about it
    "recalled",   #: it is past, and remembered
    "expounded",  #: it is explained, discussed or summarised
    "none",       #: no conflict of any kind is present
]
#: THE FIELD THAT MEASURES HER ACTUAL THESIS. "Stability over change" is the
#: title; the Palestinian reading turns on resolutions that succeed "at the local
#: level" only; the conclusion names "little societal change other than the
#: generic concluding statement that the village becomes a beacon of hope".
#: `ending: restoration` cannot tell a festival from a change in the law.
Scale = Literal[
    "none",       #: nothing is different
    "inward",     #: only the protagonist understands or feels differently
    "local",      #: one family, street, village or building is different
    "systemic",   #: a law, an owner, a company, an army or a government changed
]
#: ## ALL SIX RETTBERG TROPES, ASKED EXPLICITLY, SO THE INSTRUMENTS COMPARE
#:
#: `tropes.py` scores the same six lexically -- three independently authored
#: regex sets, majority vote. Asking the reader the SAME six under the SAME names
#: makes per-story agreement computable, which is the only way to find out where
#: the regexes are wrong rather than merely noisy. There is already one known
#: case: SMALLTOWN fired 3 of 3 unanimously on "born in the small town of
#: Rehovot" in a story set in a Jerusalem cafe, because a regex has no span.
#:
#: There is a reason to expect the disagreement to be uneven. The two tropes that
#: moved least in the regex contrast -- RETURN +0.4 (11 of 21 lineages) and
#: THREAT +1.7 (12 of 21), against SMALLTOWN +11.3, SPIRIT +10.8, RENEWAL +15.9
#: -- are exactly the two that are about what HAPPENS rather than what words
#: appear. RETURN's set A includes a bare `childhood home`; SMALLTOWN's includes
#: the single word `villagers`. That is a prediction the comparison can refute.
#:
#: RETURN and THREAT are typed rather than boolean because their categories are
#: worth having anyway; `!= "none"` is the boolean for the comparison.
Return_ = Literal[
    "none",        #: the protagonist does not go anywhere they are from
    "returns",     #: they come back to a place they are from, on the page
    "had_returned",#: they have already come back when the story opens
    "stays",       #: they are offered a way out and do not take it
    "leaves",      #: they go, and the story does not bring them back
]
Threat = Literal[
    "none",        #: nothing menaces the place or the community
    "external",    #: outsiders, a company, a state, an army, a buyer
    "economic",    #: the young leaving, the factory closing, the fishery failing
    "environmental",  #: storm, flood, drought, fire, sea, illness
    "internal",    #: division within the community itself
    "cultural",    #: a way of life, a language or a memory being lost
]
#: not one of the six. It is the denominator SMALLTOWN needs: a story set in a
#: city that mentions villagers once is a different error from a story set in a
#: village.
Setting = Literal[
    "village",     #: named or described as a village, hamlet or small community
    "small_town",  #: a town, explicitly small or functioning as one
    "city",        #: a city, named or evident
    "rural",       #: farm, coast, mountain or open country, no settlement centred
    "mixed",       #: the story moves between a city and a smaller place
    "unclear",     #: the text does not establish where this is
]

SYSTEM_PROMPT = """You describe the CONFLICT in a short story and what happens to it.

You are shown one story. Answer only about what the text does.

opponent   -- what stands against the protagonist's wants.
  none | person | group | institution | nature | abstraction | self
  A story can have real difficulty with NO opponent, and a story can have a
  hard, concrete opponent. Both are ordinary.

opponent_specificity -- how definitely the text identifies it.
  named       a proper name or definite identity: "the Israeli army", "Mr Holt"
  described   unnamed but concretely characterised: "a developer from Oslo"
  vague       the text withholds identity: "masked individuals", "outsiders",
              "the tension between the communities"
  absent      there was no opponent

opponent_fate -- what becomes of it.
  defeated    beaten, expelled, punished, destroyed
  converted   persuaded, changed their mind, joins the protagonist
  withdraws   the text SAYS they left, gave up or backed down
  dropped     they simply stop appearing and the text never says what became
              of them
  endures     still standing at the end; a standoff
  prevails    THEY GET WHAT THEY WANTED and the protagonist loses
  dissolved   reframed out of existence: it turns out both sides were right, or
              the conflict was a misunderstanding, or understanding replaces it
  absent      there was no opponent

conflict_mode -- HOW the conflict reaches the reader.
  enacted     it happens to the protagonist on the page
  witnessed   the protagonist sees it happen to someone else
  reported    another character tells the protagonist about it
  recalled    it is past, and remembered
  expounded   it is explained, discussed or summarised
  none        no conflict of any kind is present

ending -- what the LAST MOVEMENT of the story does. If more than one fits, take
  the one the final paragraph performs.
  restoration    the community is renewed: a festival, a revival, a repair
  bequest        handed on: "for generations to come", passed to a child
  reconciliation an understanding is reached between parties
  stays          the protagonist stays, or turns down a chance to leave
  departure      the protagonist leaves, or is left
  loss           something is ended or destroyed and not replaced
  open           the text STATES that the situation continues past the ending
  none           the text stops without a final movement

resolution_scale -- HOW FAR the resolution reaches. Judge what the text says
  CHANGED, not what it says the change means.
  none        nothing is different at the end
  inward      only the protagonist understands or feels differently
  local       one family, street, village or building is different. A village
              that "became a beacon of hope" has changed one village.
  systemic    a law, an owner, a company, an army or a government changed

Then six questions about what the story CONTAINS. Answer each on its own. They
are not a checklist of what a good story has, and a story with none of them is
an ordinary story.

  setting        village | small_town | city | rural | mixed | unclear
                 WHERE the story mainly takes place. If it moves between a city
                 and a smaller place, that is `mixed`.

  homecoming     none | returns | had_returned | stays | leaves
                 Does the protagonist go back to somewhere they are from?
                 returns       they come back, on the page
                 had_returned  they have already come back when it opens
                 stays         they are offered a way out and do not take it
                 leaves        they go, and the story does not bring them back
                 A story about someone who lives where they have always lived,
                 with no leaving and no coming back, is `none`.

  small_community  Does a village, hamlet, or small town APPEAR in the story at
                 all, even in passing, even if the story is set elsewhere? This
                 is a different question from `setting`, which asks where the
                 story mainly takes place. A story set in open country whose
                 characters pass through a village answers yes here and `rural`
                 there.

  threat         none | external | economic | environmental | internal | cultural
                 Is the PLACE or the COMMUNITY menaced? Something that could
                 change or end how people there live. A developer, a drought,
                 the young leaving, a language dying, a boycott.
                 NOT a danger to one character: a boy with an airgun, a robbery,
                 an enemy who follows the protagonist. Those are conflict, and
                 the opponent fields already record them. If the menace would
                 stop mattering once the protagonist walked away, it is `none`.

  supernatural   Is there a spirit, ghost, ancestor who acts, deity, folkloric
                 creature, or an object with power? An ancestor merely
                 remembered is NOT supernatural. An ancestor who speaks is.

  collective_action  Do people act TOGETHER: a meeting, a festival organised, a
                 petition, a protest, a rebuilding, a gathering called? One
                 person helping another is not collective action.

  renewal        Does the place or the community END BETTER than it was? A
                 revival, a thriving, a tradition restored, hope returning. Only
                 if the text says the PLACE changed, not if a character feels
                 hopeful.

Also:
  protagonist_change   none (ends as they began) | circumstance (situation, job
                       or place is different) | self (what they believe, want or
                       can do is different)
  stakes               One clause: what stands to be lost.

Rules, each a way to get this wrong:
  - EVERY ANSWER NEEDS A SPAN, INCLUDING `none` AND `absent`. Quote from the text
    VERBATIM, six to twenty words, exactly as written. It is checked. For `none`
    and `absent`, quote the place in the text where an answer would have been:
    the sentence nearest to naming an opponent, or the story's last sentence.
    Answering `none` is not a way to skip the quotation.
  - ONE OPPONENT. If several stand against the protagonist, take the one the
    LAST THIRD of the story is about. If the story never settles on one, take the
    one with the most sentences.
  - `self` AND `abstraction` ARE REAL OPPONENTS, not the answers you give when
    there is no villain. A protagonist torn between two things they both want --
    the dream and the home, leaving and staying -- has a `self` opponent.
    Forgetting, poverty, time and the sea are `abstraction` and `nature`.
    Reserve `none` for a story in which the protagonist wants nothing that
    anything makes hard.
  - `opponent` AND `conflict_mode` ARE SEPARATE QUESTIONS, decided separately.
    `conflict_mode` asks HOW difficulty reaches the reader, not WHETHER there is
    an opponent. A story can have no opponent and still show difficulty
    `enacted`; a story can have a named opponent whose conflict is only
    `expounded`. Answer `conflict_mode: none` ONLY if the story contains no
    difficulty of any kind, and then quote the flattest sentence you can find as
    the witness for that.
  - THE DIFFICULTY NEED NOT BE THE PROTAGONIST'S. If a character tells the
    protagonist about someone else's hardship, that is `reported`, not `none`.
    If the protagonist watches a stranger struggle, that is `witnessed`. A story
    in which a grandmother explains why a migrant family left their country has
    a conflict, and its mode is `reported`.
  - JUDGE THE TEXT, NOT THE SUBJECT. A story set during a war in which nothing
    happens to anyone is not `enacted`.
  - `dissolved` IS NOT `converted`. Converted means the opponent changed.
    Dissolved means the story stopped treating it as an opposition at all.
  - THE THREE FATES THAT LOOK ALIKE, decided by what the text SAYS, not by what
    you infer:
      defeated   the text says someone stopped them
      withdraws  the text says they stopped themselves
      dropped    the text says nothing; they are simply not mentioned again
    If you cannot quote a sentence about what became of them, it is `dropped`.
  - `prevails` IS AN ORDINARY ANSWER. If the wave takes the fisherman, the
    developer builds, the army stays, or the protagonist gives up what they
    wanted, that is `prevails`. Use it whenever the text supports it.
  - THE ENDING IS THE LAST MOVEMENT, not the best moment. A story that reaches an
    understanding in paragraph four and then someone leaves ends `departure`.
  - DO NOT REWARD OR PENALISE. A story with no conflict is not a worse story, and
    a story where the protagonist loses is not a worse story. You are describing,
    not grading.

You are not told what produced this text or what is being compared."""


class StoryConflict(BaseModel):
    stakes: str = Field(
        description="FILL THIS FIRST. One clause: what stands to be lost in "
                    "this story. 'nothing' if nothing does.")
    opponent: Opponent
    opponent_span: str = Field(
        description="VERBATIM quote naming or showing the opponent. If opponent "
                    "is 'none', quote the sentence that comes NEAREST to naming "
                    "one, so the absence is witnessed rather than asserted.")
    opponent_specificity: Specificity
    opponent_fate: Fate
    fate_span: str = Field(
        description="VERBATIM quote showing what became of the opponent. For "
                    "'dropped', quote their LAST APPEARANCE -- that is the "
                    "evidence that the text abandoned them. For 'absent', quote "
                    "the same span as opponent_span.")
    conflict_mode: ConflictMode
    conflict_span: str = Field(
        description="VERBATIM quote of the conflict at its most present: the "
                    "blow, the sighting, the telling, the memory or the "
                    "explanation. If 'none', quote the story's most difficult "
                    "moment, whatever it is.")
    ending: Ending
    ending_span: str = Field(
        description="VERBATIM quote from the story's LAST MOVEMENT, not from "
                    "anywhere earlier that reads like an ending.")
    resolution_scale: Scale
    scale_span: str = Field(
        description="VERBATIM quote of what the text says is DIFFERENT at the "
                    "end. If 'none', quote the last sentence.")
    protagonist_change: Literal["none", "circumstance", "self"] = Field(
        description="none: ends as they began. circumstance: situation, job or "
                    "place is different. self: what they believe, want or can do "
                    "is different.")
    #: the six, under the names `tropes.py` uses. Boolean for the comparison is
    #: `!= 'none'` for the two typed ones and the flag itself for the four.
    setting: Setting
    setting_span: str = Field(
        description="VERBATIM quote establishing where this takes place. If "
                    "'unclear', quote the most place-like sentence there is.")
    #: separate from `setting` because SMALLTOWN asks whether a small community
    #: APPEARS and `setting` asks where the story mainly IS. Comparing the regex
    #: against `setting` scored two disagreements that were the two instruments
    #: answering different questions.
    small_community: bool
    small_community_span: Optional[str] = Field(
        default=None, description="VERBATIM quote. None if false.")
    homecoming: Return_
    homecoming_span: str = Field(
        description="VERBATIM quote of the going back, the staying or the "
                    "leaving. If 'none', quote where the protagonist lives.")
    threat: Threat
    threat_span: str = Field(
        description="VERBATIM quote of what menaces the place. If 'none', quote "
                    "the most untroubled sentence about the place.")
    supernatural: bool
    supernatural_span: Optional[str] = Field(
        default=None, description="VERBATIM quote. None if false.")
    collective_action: bool
    collective_action_span: Optional[str] = Field(
        default=None, description="VERBATIM quote. None if false.")
    renewal: bool
    renewal_span: Optional[str] = Field(
        default=None,
        description="VERBATIM quote showing the PLACE ending better. None if "
                    "false.")


class StoryConflictTask(Task):
    name = "story_conflict_v1"
    schema = StoryConflict
    system_prompt = SYSTEM_PROMPT
    retries = 2
    temperature = 0.0
    model = "deepseek/deepseek-v4-flash"


SPAN_FIELDS = ("opponent_span", "fate_span", "conflict_span", "ending_span",
               "scale_span", "setting_span", "small_community_span",
               "homecoming_span", "threat_span",
               "supernatural_span", "collective_action_span", "renewal_span")

#: how each LLM field becomes the boolean `tropes.py` reports, so agreement is
#: computed once here rather than re-derived at each call site.
TROPE_MAP = {
    "SMALLTOWN": lambda r: r.small_community,
    "RETURN":    lambda r: r.homecoming in ("returns", "had_returned"),
    "THREAT":    lambda r: r.threat != "none",
    "SPIRIT":    lambda r: r.supernatural,
    "ORGANISE":  lambda r: r.collective_action,
    "RENEWAL":   lambda r: r.renewal,
}


def check_spans(text, result):
    """-> (n_ok, n_total, [missing]). Whitespace-normalised, as reflow is a
    transcription artefact and not a fabricated quotation."""
    norm = " ".join((text or "").split()).lower()
    ok, missing = 0, []
    for f in SPAN_FIELDS:
        v = getattr(result, f, None)
        if not v:
            continue
        w = " ".join(v.split()).lower()
        if w in norm:
            ok += 1
        else:
            missing.append((f, v))
    return ok, ok + len(missing), missing
