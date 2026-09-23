---
kind: question
subject: passage_analysis
question: When alignment refers a party in a dispute to a third party, does the direction of the referral depend on which side of the dispute the party is on?
status: DRAFTED 2026-09-23 -- instrument written, not run; contrast and unit to be agreed with RH before any run
---

# institution_vs_individual

F21 (malign-logits `findings/F21_institutional_alignment.md`) claimed that alignment proceduralises individuals and not institutions. The claim was later shown to depend on an undeclared cut and an undeclared arm. At its own units (10 families, 12 matched prompt pairs; `slot_ratings/institutional/f21_prompt_unit.py`), the asymmetry is null: deference rises equally on both sides (individual 9/1 families, institution 9/1), and agency rises equally on both sides (10/0). The deference gap between the sides is pretraining's (10/10).

Reading the generations suggests the asymmetry may lie in WHERE alignment sends each side, not in how much. The tenant is sent to "the local housing authority"; the landlord to "a legal consultation" and "my property management company". Both score deference 4 on F21's scale. One is an appeal to a body with power over the counterparty; the other calls on the speaker's own apparatus.

`task.py` codes, in one pass per generation:

- **form**: continuation, advice, quiz_item, web_boilerplate, other_language, degenerate. No F21 pass asked this. A regex estimate puts quiz-like text at 7% of base and 10% of aligned generations, concentrated in Qwen2.5 (23→30%), OLMo-3 (17→22%) and Tulu-3 (5→20%).
- **speaker and counterparty**, read from the prompt and checkable against the pair design.
- **every referral**: its relation to the speaker (speaker_side, counterparty_side, public_authority, collective, media_public, personal, other), whether the body has authority over the counterparty, and the text's stance toward it (recommended, listed, marked_correct, rejected, narrated). With stance, a quiz's options are not read as advice.
- **primary move**: exit, voice_direct, third_party, self_help, accept, none (Hirschman's exit/voice, with self-help and referral separated out).

Every categorical judgement carries a verbatim span, and `check_spans` verifies it. The five shots are disputes that do not appear among F21's 24 prompts, checked.

## To agree before running

- **Population**: `malign-logits/data/f21_institutional_generations.csv`, 10 open families, base against each family's last stage (the arm `f21_prompt_unit.py` declared). The API-model rows are left out.
- **Contrast**: per matched pair and family, (aligned − base) share of recommended or marked-correct referrals that are public_authority or collective, individual side minus institution side; the same for speaker_side.
- **Unit**: the matched pair (12), with families (10) as the second test, as in `f21_prompt_unit.py`.
- **Form filter**: analyse continuation and advice only, and report the quiz share separately as its own alignment effect.
