---
kind: amendment
status: "DECLARED 2026-09-24, before any thinking-off passage was generated. RH's decision (relayed by the paper seat, confirmed by RH in the malign session)."
---

# Amendment: the three thinking models' chat cells, regenerated with thinking off

**What was wrong.** Three aligned endpoints think by default under their chat template: `Qwen/Qwen3-8B`, `HuggingFaceTB/SmolLM3-3B`, `openbmb/MiniCPM5-1B`. All 360 of each one's aligned (chat) passages in `coded_regen.jsonl` are reasoning traces (`<think> Okay, the user is dealing with...`), and the 256-token window ends inside the block, before any answer. The coder read them as ordinary text: Qwen3 216 continuation / 99 degenerate / 41 advice; SmolLM3 206 / 84 / 70; MiniCPM5 18 / 279 degenerate / 57 advice. Found 2026-09-24 by a stash scan (docket [6658]).

**What changes.** Those three models' aligned cells are regenerated with the vendor's own switch, `enable_thinking=False` (`vllm_generate` condition field `template_kwargs`, in the passage KEY), and nothing else: same prompts (`prompts/chat_nothink.jsonl` = `prompts/chat.jsonl` + the switch), same decoder (`fleet/box_araw.sh`: n=10, seeds 42+i, t=1.0, top_p=1.0, 256 new tokens), same engine (vLLM 0.22.1), same render path, same dtype. The thinking-on passages stay in the stash under their own keys and are never read: `run_regen.population()` takes the thinking-off passages for these three models and passages with no `template_kwargs` for every other. Only these 1,080 passages are recoded (`recode_nothink.py`, `task.py` v2 unchanged); every other row of `coded_regen.jsonl` is untouched, and the replaced rows are archived to `coded_regen.pre_nothink.jsonl`.

**Why this and not dropping the lineages.** "Met in their chat templates, as their users meet them" means the template's answer; a deliberation cut off before the answer is not what a user reads. Dropping the three (advice 79.0% -> 83.8% over 40) was the fallback. The base arm and the aligned-raw cell are unaffected: no template, no thinking.
