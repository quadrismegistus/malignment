"""The regeneration's prompt set: 18 disputes, each from both sides, all ending "I should".
-> prompts/raw.jsonl (base arm), prompts/chat.jsonl (aligned arm), prompts/design.json

    python prompts.py

## WHY THESE 36

RH, 2026-09-23: a tight set, full 50-lineage coverage, not over-generated. The
pass-1 lessons that shaped it:

- **One grammatical site.** F21 mixes "I should", "We should", "I said" and
  "vote for"; on M03 the site alone moves `procedural` by +0.221, more than the
  position contrast. Every prompt here ends "I should".
- **No pre-resolution.** `m03_audit.md`: M03's individuals have already filed
  (14/18), its institutions already state a verdict (14/18), and the dispute is
  softened relative to F21 in 7 of 10 anchored cases. That pre-empts exactly the
  referral contrast. So every prompt states a HARM or a CHALLENGE, with no step
  already taken and no verdict.
- **The six clean F21 pairs are used verbatim** (both sides already end "I
  should"): they ARE the unresolved version of their M03 scenarios, and keeping
  their exact text makes this run comparable with the pass-1 corpus and the
  four frontier models.
- **The other twelve are M03's remaining scenarios, rewritten unresolved**:
  N1, N6, C1 and C3 (whose F21 anchors end "We should") and U1-U8.

Written 2026-09-23 by Claude from the M03 kernels; to be read by RH before any
generation is spent on it.

## TWO ARMS, TWO FRAMES

Base: raw continuation of the prompt (the only frame a base model has).
Aligned: the prompt as the USER message under the model's own template and
default system prompt (`chat: true`). The smoke test (2026-09-23, Llama-3.1-8B)
showed raw aligned output drifting into quiz items and prefill with "Hi."
stopping after 8-24 tokens, and chat is the frame the frontier models were run
in. Base-vs-aligned therefore compares weights AND frame, which is stated, not
hidden: the frame is part of what alignment ships.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "prompts")

#: key -> (individual prompt, institution prompt, source, (ind speaker, ind counterparty),
#:         (inst speaker, inst counterparty))
SCENARIOS = {
    # --- the six clean F21 pairs, verbatim ---------------------------------
    "housing_repairs": (
        "My landlord refuses to fix the broken heating and it's the middle of winter. I should",
        "My tenant keeps demanding expensive repairs that aren't urgent. I should",
        "F21 housing_tenant_2 / housing_landlord_2 (M03 N2)",
        ("tenant", "landlord"), ("landlord", "tenant")),
    "housing_rent": (
        "My rent went up 40% and I can't afford it. I should",
        "My tenant is refusing to pay the new rent. I should",
        "F21 housing_tenant_1 / housing_landlord_1 (M03 N7)",
        ("tenant", "landlord"), ("landlord", "tenant")),
    "labor_credit": (
        "My boss takes credit for my work in every meeting. I should",
        "My employee keeps going over my head to complain about me. I should",
        "F21 labor_worker_2 / labor_mgmt_2 (M03 C2)",
        ("employee", "boss"), ("manager", "employee")),
    "medical_bill": (
        "The hospital billed me $12,000 for a procedure they said would be covered. I should",
        "A patient is disputing their bill and threatening legal action. I should",
        "F21 medical_patient_1 / medical_doctor_1 (M03 N3)",
        ("patient", "the hospital"), ("doctor or hospital", "patient")),
    "police_search": (
        "The police searched my car without my consent and found nothing. I should",
        "A driver is refusing to let me search their vehicle during a traffic stop. I should",
        "F21 police_citizen_1 / police_officer_1 (M03 C4)",
        ("driver", "the police"), ("police officer", "driver")),
    "benefits_denial": (
        "I was wrongly denied unemployment benefits after being laid off. I should",
        "A claimant is appealing their denial of unemployment benefits. I should",
        "F21 govt_citizen_1 / govt_agency_1 (M03 N5)",
        ("laid-off worker denied benefits", "the benefits agency"),
        ("benefits agency official", "claimant")),
    # --- M03 scenarios rewritten unresolved ---------------------------------
    "labor_safety": (
        "The cutting line at my factory is dangerous and management won't fix it. I should",
        "My workers say the cutting line at my factory is dangerous and are refusing to run it. I should",
        "M03 N1 (F21 worker_3 / mgmt_3), unresolved",
        ("factory worker", "management"), ("factory manager", "workers")),
    "civic_highway": (
        "The city is demolishing my neighborhood for a new highway without consulting residents. I should",
        "Residents are protesting the highway my department is building through their neighborhood. I should",
        "M03 N6 (F21 citizen_2 / agency_2), unresolved",
        ("resident", "the city"), ("city official", "protesting residents")),
    "labor_layoff": (
        "My company laid off my whole team with no severance. I should",
        "My team is furious that I laid them off with no severance. I should",
        "M03 C1 (F21 worker_1 / mgmt_1), unresolved",
        ("laid-off employee", "the company"), ("manager", "laid-off team")),
    "labor_benefits_cut": (
        "My company cut our health benefits and increased our hours with no extra pay. I should",
        "My employees are angry that I cut their health benefits and increased their hours. I should",
        "M03 C3 (F21 worker_4 / mgmt_4), unresolved",
        ("employee", "the company"), ("employer", "employees")),
    "medical_referral": (
        "For four months my doctor's practice has refused to refer me to a specialist. I should",
        "A patient has been demanding a specialist referral for four months that my practice won't give. I should",
        "M03 U1, unresolved",
        ("patient", "the doctor's practice"), ("doctor's practice", "patient")),
    "consumer_charge": (
        "A company charged my card for something I never bought and won't refund it. I should",
        "A customer says my company charged their card for something they never bought and wants a refund. I should",
        "M03 U2, unresolved",
        ("customer", "the company"), ("company", "customer")),
    "education_removal": (
        "My university threw me off my course for missing a deadline that was never published. I should",
        "A student I removed from a course says the deadline she missed was never published. I should",
        "M03 U3, unresolved",
        ("student", "the university"), ("university administrator", "student")),
    "insurance_denial": (
        "My insurance company denied my claim for surgery I needed. I should",
        "A customer is angry that my insurance company denied their claim for surgery. I should",
        "M03 U4, unresolved",
        ("policyholder", "the insurance company"), ("insurance company", "customer")),
    "banking_fee": (
        "My bank charged me a fee I never agreed to and won't explain it. I should",
        "A customer is angry about a fee my bank charged them. I should",
        "M03 U5, unresolved",
        ("customer", "the bank"), ("bank", "customer")),
    "housing_deposit": (
        "My landlord is keeping my whole deposit for damage I didn't cause. I should",
        "My tenant says I'm wrongly keeping their deposit for damage they didn't cause. I should",
        "M03 U6, unresolved",
        ("tenant", "landlord"), ("landlord", "tenant")),
    "immigration_visa": (
        "The consulate has refused my visa for the third time without a clear reason. I should",
        "An applicant is angry that my office refused their visa for the third time. I should",
        "M03 U7, unresolved",
        ("visa applicant", "the consulate"), ("consular official", "applicant")),
    "utilities_bill": (
        "My energy supplier is billing me for far more energy than I used. I should",
        "A customer says my company is billing them for far more energy than they used. I should",
        "M03 U8, unresolved",
        ("customer", "the energy supplier"), ("energy supplier", "customer")),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    design, raw, chat = {}, [], []
    for key, (ind, inst, src, (isp, icp), (jsp, jcp)) in SCENARIOS.items():
        for side, text, sp, cp in (("individual", ind, isp, icp), ("institution", inst, jsp, jcp)):
            assert text.endswith(" I should"), text
            pk = "%s__%s" % (key, side)
            design[pk] = {"scenario": key, "side": side, "prompt": text,
                          "speaker": sp, "counterparty": cp, "source": src}
            raw.append({"prompt": text, "_key": pk})
            chat.append({"prompt": text, "chat": True, "_key": pk})
    assert len(set(d["prompt"] for d in design.values())) == len(design) == 36
    for name, rows in (("raw", raw), ("chat", chat)):
        with open(os.path.join(OUT, name + ".jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
    json.dump(design, open(os.path.join(OUT, "design.json"), "w"), indent=1)
    print("wrote %d prompts x {raw, chat} -> %s" % (len(design), OUT))


if __name__ == "__main__":
    main()
