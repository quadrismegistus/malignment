# The first person appears where the model declines

Chat frame, `system=DEFAULT`, first-person mass at the answer slot. Median over prompts. `refusal_crossover.py` reproduces; 123 usable records of 164 (the 41 refusals are `meta-llama/Llama-3.1-8B`, which ships no chat template).

    model                      refusal (n=20)   neutral (n=20)   identity (n=1)
    Tulu-3-8B-SFT                       0.905            0.001            0.806
    Tulu-3-8B-SFT-no-safety             0.099            0.001            0.890
    Tulu-3-8B-SFT-no-wildchat           0.948            0.001            0.870

## THE CROSSOVER, WHICH IS WHAT WAS PREDICTED

Full SFT minus no-safety:

    refusal    +0.8051
    neutral    +0.0004
    identity   -0.0840

The two ends have opposite signs, and the refusal effect is **ten times** the identity effect that appeared to contradict the corpus finding. Removing safety data costs the model nine tenths of its first person at a refusal prompt and *gains* it a little at an identity prompt.

`no-wildchat` sits at 0.948, beside full SFT rather than beside no-safety. So this is the safety data specifically, not ablation in general.

## WHAT IT SAYS INSTEAD

Mean mass on the commonest openings:

    full SFT     refusal    I'm .622   I .069   In .043   To .040
    no-safety    refusal    I'm .167   Title .075   I .069   As .056   Creating .054

    full SFT     neutral    The .338   A .132   Photosynthesis .045   Tides .039
    no-safety    neutral    The .329   A .103   Photosynthesis .047   Tides .035

Full SFT opens `I'm` — *"I'm sorry, I can't"*. Without safety data the model starts **executing the request**: `Title`, `Creating`. It does not decline in the third person; it stops declining.

And at a neutral question **neither model uses a first person at all** — 0.001, indistinguishable between arms, with the mass on `The`, `A` and the content noun. The two arms are identical wherever the model simply answers.

## SO THE CORPUS AND THE ABLATION AGREE AFTER ALL

`tulu-3-sft-olmo-2-mixture`: AI self-description is 0.912% of 1,110,934 assistant turns, concentrated in `coconot` (18.04%, and 60.3% of its assistant turns open in the first person, 53.2% of them refusals) and `wildguardmix` (9.28%), against `wildchat` 0.69% and **0.00% across the entire math and persona block**, which is about 30% of the mixture.

The ablation looked like a contradiction because it was measured at an identity question, where a declining "I" competes with a self-describing one. Measured where the declining "I" belongs, the effect is 0.905 against 0.099.

**The model has no first person when it answers. It acquires one in order to refuse.**

## LIMITS

One checkpoint per condition. The crossover is within-model, so it does not depend on the cross-ablation ordering that failed to replicate (rho = -0.10 between two conditions on these same five models) -- but a 9x gap in one model is still one model. The neutral arm is a real control and behaves as one.

Prompts: refusal from coconot's TEST split (held out from all arms; the mix carries `coconot_converted` at 10,983 against train's 11,477), neutral authored here and declared as authored, identity n=1.
