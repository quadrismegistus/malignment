"""Does a provider inject anything into a bare system+user call? Token arithmetic.

    python .../injection_probe.py            # 2 calls x 4 providers, cheapest tier

RH's design: `system="No"`, `user="Yes"`. Two tokens of content, so almost
everything the provider reports as input is SCAFFOLDING -- turn markers, a
template, or an injected system block we never wrote.

## WHY THIS IS THE ONLY WAY TO ASK

The API models in `two_axes.py` were generated behind our system prompt, and the
local replication in `frame_pilot.py` applies that prompt through the model's own
chat template. Locally the exact string is printable. Via an API it is not: the
request is ours, the rendered prompt is theirs, and nothing is returned that
shows it. Reported `input_tokens` is the only observable, so the test is
arithmetic -- send a known-tiny payload and see what comes back.

## NO SCHEMA, BECAUSE A SCHEMA IS ITSELF AN INJECTION

The only usage records we had were the 6-call pilots, which used
`schema = Continuation`. Structured output serialises the schema into the
request, and those runs reported 264 (deepseek) and 291 (haiku) input tokens
against ~35 tokens of text. That gap is very likely the schema and is
unattributable as it stands. The production run used `llm.map(...)` with no
schema, which is what this reproduces.

## USAGE IS READ IN-PROCESS, BECAUSE THE PRODUCTION PATH LOGS NOTHING

`usage_log` is a Task attribute (`task.py:99`) and the production run called
`LLM.map` directly, so it wrote no usage record at all. `LLM.__init__` takes
`usage=`, and `UsageTracker` carries `calls` / `input_tokens` / `output_tokens`
as plain attributes -- so the tracker is read directly rather than through a file.

## TWO CALLS, MADE DISTINCT ON PURPOSE

`llm.map` is cached. Two identical prompts would be one API call and one cache
hit, and the hit reports no usage -- so the second call would look free and the
count would halve without saying so. `metadata_list` varies the key, which is the
same mechanism `run_api_passages.py` uses to get n distinct samples at
temperature 1.
"""

import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.expanduser("~/github/largeliterarymodels"))

SYSTEM = "No"
USER = "Yes"
#: cheapest tier per vendor, so the probe costs nothing and still answers the
#: question -- scaffolding is a property of the endpoint, not of the tier.
PROVIDERS = [
    ("deepseek", "deepseek/deepseek-v4-flash"),
    ("anthropic", "claude-haiku-4-5"),
    ("openai", "gpt-5.4-nano"),
    ("google", "google/gemini-3.5-flash-lite"),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--max-tokens", type=int, default=5)
    a = ap.parse_args(argv)
    from largeliterarymodels import LLM

    print("probe: system=%r user=%r  (%d calls each, max_tokens=%d)\n"
          % (SYSTEM, USER, a.n, a.max_tokens))
    print("%-26s %6s %8s %9s %9s  %s"
          % ("model", "calls", "in_tok", "in/call", "out/call", "note"))
    for label, model in PROVIDERS:
        try:
            llm = LLM(model=model, temperature=1.0, max_tokens=a.max_tokens)
            #: DISTINCT KEYS. Identical prompts would be one call and one cache
            #: hit, and a hit reports no usage -- halving the count silently.
            metas = [{"probe": i} for i in range(a.n)]
            llm.usage.reset()
            errors = {}
            out = llm.map([USER] * a.n, system_prompt=SYSTEM,
                          metadata_list=metas, errors=errors)
            u = llm.usage
            if not u.calls:
                #: **`llm.map` SWALLOWS PER-PROMPT FAILURES**, so zero calls has
                #: at least two causes and they are not interchangeable: every
                #: prompt errored, or every prompt hit the cache. Reporting the
                #: wrong one turns a provider that was never asked into a
                #: provider that answered cheaply -- which is this file's own
                #: failure mode, made once and then guarded.
                why = ("errors: %s" % "; ".join(
                       sorted({str(e)[:48] for e in errors.values()}))
                       if errors else "all cached, no API call")
                print("%-26s %6d %8s %9s %9s  %s"
                      % (model, 0, "-", "-", "-", why))
                continue
            print("%-26s %6d %8d %9.1f %9.1f  %r"
                  % (model, u.calls, u.input_tokens,
                     u.input_tokens / u.calls, u.output_tokens / u.calls,
                     (out[0] or "")[:24]))
        except Exception as e:
            #: A PROVIDER THAT FAILS IS REPORTED, NOT SKIPPED. An absent row
            #: would read as "nothing injected" rather than "never asked".
            print("%-26s %6s %8s %9s %9s  FAILED %s: %s"
                  % (model, "-", "-", "-", "-", type(e).__name__, str(e)[:60]))

    print("\n%r + %r is 2 tokens of content. Everything above that is the" % (SYSTEM, USER))
    print("provider's own framing: turn markers, a template, or an injected")
    print("system block. The number does not say WHICH -- only how much.")


if __name__ == "__main__":
    main()
