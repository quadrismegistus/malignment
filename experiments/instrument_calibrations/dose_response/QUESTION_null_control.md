Question about controlling for general mass concentration, and a request for a function if one does not exist.

WHAT I HAVE. dose_response now tags every English prompt with the relations holding among its candidate words, blind to arm: task_multi v6, sha 06b0b4295a986138, 10,970 cells over 2,569 prompts x 5 endpoint pairs (Amber, SmolLM3, Llama-3.1-8B, Qwen2.5-7B, gemma-2-9b), in experiments/instrument_calibrations/dose_response/results/rank_en5_multi.jsonl. Each cell carries per-relation splits with a marked and an unmarked pole of actual words.

WHAT I WANT. Whether alignment moves mass from the marked pole to the unmarked pole, per relation. Raw mass differences do not answer it: every candidate above 1% gains under alignment because the aligned arm is more peaked. Measured over 10,970 cells, marked +0.0208 and unmarked +0.0447. The differential partly cancels the concentration but not cleanly, since proportional inflation favours whichever pole started larger, and the unmarked pole does start larger (0.135 vs 0.108).

WHAT I READ. movement.py. CANONICAL's renormalisation null looks like exactly the control: null = P * (R/S) is the uniform-concentration model, so excess = Q - null is deviation from it. My plan is to reconstruct inflation per cell from movement_v4 (R = 1 - sum p_aligned over cls='faller'; S = sum p_base over non-fallers) plus resid_base from movement_cells_v4, then take mean excess over my marked words against mean excess over my unmarked words.

FOUR THINGS I WOULD RATHER ASK THAN ASSUME.

1. Is that reconstruction of inflation from movement_v4 + movement_cells_v4 correct, or is inflation stored somewhere I have not found? movement_cells_v4 has departed/arrived/mass_still/resid_* but I did not see inflation or excess as columns.

2. movement_v4 has a `rule` column. Which rules are actually built in it? cls='faller' means something different under DRAW than under CANONICAL, and I do not want to join against the wrong one.

3. decompose() computes excess only over non-fallers to keep the zero-sum identity. For a pole-mass question the fallers ARE the event -- a marked word that halved is the displacement. Is computing Q - P*inflation over all pole words including fallers a reasonable thing to do, or does it break something I am not seeing? I know it is no longer zero-sum and would say so.

4. Is there an existing function for "mass on an arbitrary word set, null-corrected"? I could not find one -- decompose() partitions by the rule's own faller/riser classes, not by a caller-supplied set. If there is not one, could you add it? Something like

    pole_excess(base, aligned, prompt, words, rule=CANONICAL) -> {mass_base, mass_aligned, null, excess, inflation, residual_share, n_fallers_in_set}

taking a caller-supplied word set. That is the primitive I need and it is likely useful beyond this -- any question of the form "did THIS set of words move beyond renormalisation" needs it.

ALSO, TWO SMALL THINGS FOUND WHILE READING.

movement.py words()/words_multi()/cells()/movement_js() all raised NameError on every call -- _resolve_words and _resolve_cells import _lit locally as `lit`, so the name was never bound in those four callers. movement_rows and endpoint_movement do their own import and were fine. Fixed in the file's local-import style and verified; that is in my commits today.

RULE_VERSION = 3 at module level and contrast() reading twp_words (v3) are stale -- the comment says v4 covers 23 models against v3's full roster, and RH says v4 is the full roster now. I have not touched those; they are yours.
