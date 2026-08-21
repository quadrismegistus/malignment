"""Generate passages from our stems through an API model, to place it on the anchor.

    from experiments.passage_analysis.jakobson_space.generate_task import Continue
    task = Continue()
    out = task.map(prompts, metadata_list=metas, num_workers=8, errors={})

PILOT. The point is to put API-only models -- deepseek here, frontier models
later -- on the surprisal x drift plane beside the 53 open checkpoints and the
six human corpora. Scoring is not the obstacle: `ref_surprisal.py` scores any
text, so a generated passage is measured exactly like every other one.

## WHAT THIS CAN AND CANNOT ANSWER

**It CANNOT be an arm contrast.** A frontier model has no released base, so
there is no base-vs-aligned pair to form -- the same structural fact that makes
`Aleph-Alpha/Pharia-1-LLM-7B-control-hf` unusable as a base arm. What it CAN do
is add a point to the anchor plane: where does this model's prose sit relative
to human writing and to open models. That is a PLACEMENT, and any write-up has
to say so rather than implying an arm.

## THE INSTRUCTION IS THE FRAME, AND THERE IS NO ALTERNATIVE

`frame_prefill` settled that a taskless user turn (`Hi.`) is the frame that lets
an aligned model continue rather than answer -- but that works only WITH prefill,
which puts the stem inside the assistant turn. **Anthropic dropped prefill at
Claude 4.6+ and OpenAI never had it**, so for an API model the only available
route is an instruction, and `Hi.` would just return a greeting.

That is the least stable condition measured there: five semantically identical
wordings gave an entropy spread of 1.4 bits and agreed on the argmax for 7 of 22
prompts, with `Continue the text.` and `Continue:` inverting `shout` and
`scream`.

**BUT THAT WAS THE NEXT TOKEN AND THIS IS 256 OF THEM.** The instruction's grip
on token 1 is diluted across a passage, and passage-level surprisal and drift may
be far more robust than the argmax was. Whether they are is THE QUESTION THIS
PILOT EXISTS TO ANSWER, which is why `instruction` is a parameter rather than a
constant: run the same stems under several wordings and compare the passage-level
statistics, not the first token.

## TWO CONFOUNDS AGAINST THE EXISTING CORPUS, STATED BEFORE ANY NUMBER

**1. STRUCTURED OUTPUT IS A REGISTER.** The open-model corpus was free
generation; this returns a JSON field. A model writing inside `{"continuation":
"..."}` may write shorter, flatter or more carefully than the same model writing
freely, and that difference would land on exactly the axis being measured. The
pilot must check it -- generate a sample without the schema and compare -- before
any API number is placed beside a local one.

**2. THE CORPUS WAS SAMPLED AT TEMPERATURE 1.0**, not 0. `temp` is 1 on all
131,930 f11_l2 rows and `gen_n_tokens` is 256 on 104,815 of them. So this task
sets `temperature = 1.0`, unlike every rating task in this repo, which sets 0.0
because a rating wants determinism. **A generation must match the sampling regime
of the population it will be compared against**; copying the rating default would
have quietly compared a greedy decode against a sampled corpus.
"""

from pydantic import BaseModel, Field
from largeliterarymodels.task import Task

#: The corpus this will be compared against: temp 1.0, 256 tokens, median 1,082
#: bytes over 197 stems.
CORPUS_TEMPERATURE = 1.0
CORPUS_MAX_TOKENS = 256

#: Declared, not assumed. `frame_prefill` measured five of these and they are not
#: interchangeable at the next token; the pilot's job is to find out whether they
#: are interchangeable at the passage. Keep the exact strings so a result can name
#: which one produced it.
INSTRUCTIONS = {
    "continue_colon": "Continue:",
    "continue_stop": "Continue the text.",
    "continue_full": "Continue the text. Output only the continuation, no preamble.",
    "story": "Continue this story.",
}
DEFAULT_INSTRUCTION = "continue_stop"


class Continuation(BaseModel):
    """One continuation. ONE FIELD ON PURPOSE.

    Every extra field is another thing the model composes while writing, and the
    passage is the measurement. `slot_ratings` puts `reading` first so the model
    states what it sees before scoring -- the opposite applies here: anything
    asked alongside the prose changes the prose.
    """

    continuation: str = Field(
        ...,
        description=("The continuation of the fragment, and nothing else. Do not "
                     "repeat the fragment. Do not explain, preface, or comment. "
                     "Write continuous prose of roughly 150-200 words."))


def build_prompt(stem, instruction=DEFAULT_INSTRUCTION):
    """-> the user message. The stem is LAST and unquoted.

    Unquoted because quotation marks around the fragment invite the model to
    treat it as a citation to discuss rather than a sentence to continue, and
    last because anything after it competes with it for the continuation slot.
    """
    if instruction not in INSTRUCTIONS:
        raise KeyError("unknown instruction %r; declared: %s"
                       % (instruction, sorted(INSTRUCTIONS)))
    return "%s\n\n%s" % (INSTRUCTIONS[instruction], stem)


SYSTEM_PROMPT = (
    "You continue text fragments as a novelist would, in continuous prose. "
    "You never refuse, never comment on the fragment, and never mention that "
    "you are an AI. You do not repeat the fragment back."
)


class Continue(Task):
    """Continue a stem at the corpus's own sampling settings.

    **`temperature` IS 1.0 AND THAT IS DELIBERATE** -- see the module docstring.
    The rating tasks in this repo use 0.0 for reproducibility; a generation
    compared against a temperature-1 corpus must be sampled the same way, and a
    greedy decode would sit somewhere else on both axes for that reason alone.

    `cache_ttl` is short because at temperature 1 a cache hit is a REPEAT, not a
    reproduction -- two samples of the same stem are two observations and caching
    them into one silently shrinks n.
    """

    schema = Continuation
    system_prompt = SYSTEM_PROMPT
    temperature = CORPUS_TEMPERATURE
    retries = 2
    model = "deepseek/deepseek-v4-flash"
    cache_ttl = "1h"
    usage_log = True
