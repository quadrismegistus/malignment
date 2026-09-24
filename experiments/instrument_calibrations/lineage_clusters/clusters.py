"""The 50 endpoint lineages grouped by the post-training data they declare.

    from clusters import grouping          # {lineage key: cluster}, key = "base>aligned"
    python clusters.py                      # print the three groupings and their sizes

WRITTEN 2026-09-24 at the paper seat's request (outside review of the draft: the
"X of 50 lineages" sign tests treat lineages as independent, but many share SFT
data). The assignments below were made from `roster/models/attestations.json`
(`post_training_dataset` / `datasets` claims on each endpoint), before any
per-lineage test value was joined to them. The pooled counts being re-tested
(40/50, 44/50, 42/50) had been seen; per-cluster values had not.

THREE GROUPINGS, from least to most conservative. None is "right"; the point is
whether a direction survives all three.

    PRETRAIN   the pretraining developer of the BASE. Catches lineages that share
               a base family (the two Qwen2.5 sizes, Llama-3.1 8B/70B), not SFT.
    SFT        the DOMINANT declared SFT source family where one is named, else the
               endpoint's developer (unnamed in-house data from one developer is
               assumed shared). One label per lineage.
    UNION      connected components: two lineages are joined if they share EITHER
               a named SFT family (any, not only the dominant one) OR a developer.
               The upper bound on dependence this record can support.

THE FENCE. The IN-HOUSE endpoints (count printed by `python clusters.py`) name
no public dataset: "in-house", "unnamed", "publicly available instruction
datasets", or a developer's own mix. For those, developer is a proxy, and two
developers' unnamed data may overlap in ways no card says (most 2023-24 in-house
mixes contain ShareGPT-style GPT distillation). Unnamed data can only be grouped
by who made it, so cross-developer sharing among them is INVISIBLE here, and UNION cannot bound it either.
"""
import collections

#: lineage key -> (dominant SFT family, every declared family, endpoint developer, why)
#: families: TULU (AI2 Tulu-3 / Dolci mixtures), H4 (UltraChat + UltraFeedback,
#: the Zephyr recipe), DISTILL (ShareGPT / GPT4All / Alpaca-GPT / OpenHermes /
#: Orca / Baize: GPT-output distillation), CROWD (human-written: oasst, dolly,
#: hh-rlhf, SHP), PKU (PKU-SafeRLHF), XP3, SMOLTALK, NEMOTRON, ALPACA (tatsu).
#: IN-HOUSE means no dataset named; the dominant label is then the developer.
L = {
    "01-ai/Yi-1.5-9B>01-ai/Yi-1.5-9B-Chat": ("IN-HOUSE", [], "01-ai", "no dataset named"),
    "BAAI/Aquila2-7B>BAAI/AquilaChat2-7B": ("IN-HOUSE", [], "BAAI", "unknown"),
    "BSC-LT/salamandra-7b>BSC-LT/salamandra-7b-instruct": ("CROWD", ["CROWD", "DISTILL", "ALPACA"], "BSC", "oasst2, dolly, no-robots, aya lead; also alpaca-cleaned, open-orca"),
    "EleutherAI/pythia-2.8b>ContextualAI/archangel_sft-dpo_pythia2-8b": ("CROWD", ["CROWD"], "ContextualAI", "SHP, hh-rlhf, oasst1"),
    "EleutherAI/pythia-6.9b>lomahony/eleuther-pythia6.9b-hh-dpo": ("CROWD", ["CROWD"], "lomahony", "hh-rlhf only"),
    "HuggingFaceTB/SmolLM2-360M>HuggingFaceTB/SmolLM2-360M-Instruct": ("SMOLTALK", ["SMOLTALK", "H4"], "HuggingFaceTB", "smol-smoltalk SFT, UltraFeedback DPO"),
    "HuggingFaceTB/SmolLM3-3B-Base>HuggingFaceTB/SmolLM3-3B": ("SMOLTALK", ["SMOLTALK", "TULU", "NEMOTRON"], "HuggingFaceTB", "OpenThoughts3 + Nemotron traces mid-training, Tulu3 preference for APO"),
    "LLM360/Amber>LLM360/AmberSafe": ("PKU", ["PKU"], "LLM360", "PKU-SafeRLHF only"),
    "OpenLLM-France/Lucie-7B>OpenLLM-France/Lucie-7B-Instruct-v1.1": ("DISTILL", ["DISTILL", "TULU", "CROWD"], "OpenLLM-France", "Open Hermes 2.5, FLAN, Tulu3 personas, Wildchat-fr"),
    "Qwen/Qwen2.5-0.5B>Qwen/Qwen2.5-0.5B-Instruct": ("IN-HOUSE", [], "Qwen", "in-house SFT, unnamed"),
    "Qwen/Qwen2.5-7B>Qwen/Qwen2.5-7B-Instruct": ("IN-HOUSE", [], "Qwen", "in-house SFT, unnamed"),
    "Qwen/Qwen3-8B-Base>Qwen/Qwen3-8B": ("IN-HOUSE", [], "Qwen", "distilled from Qwen3-32B/235B outputs"),
    "RWKV/rwkv-4-7b-pile>RWKV/rwkv-raven-7b": ("DISTILL", ["DISTILL", "ALPACA"], "RWKV", "Alpaca, CodeAlpaca, Guanaco, GPT4All, ShareGPT"),
    "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T>TinyLlama/TinyLlama-1.1B-Chat-v1.0": ("H4", ["H4"], "TinyLlama", "ultrachat_200k SFT, UltraFeedback DPO"),
    "Zyphra/Zamba2-7B>Zyphra/Zamba2-7B-Instruct": ("DISTILL", ["DISTILL", "H4"], "Zyphra", "OpenHermes, UltraChat, Infinity-Instruct, Magpie; UltraFeedback DPO"),
    "allenai/OLMo-2-0425-1B>allenai/OLMo-2-0425-1B-Instruct": ("TULU", ["TULU"], "allenai", "tulu-3-sft-olmo-2-mixture"),
    "allenai/OLMoE-1B-7B-0125>allenai/OLMoE-1B-7B-0125-Instruct": ("TULU", ["TULU"], "allenai", "tulu-3-sft-olmo-2-mixture"),
    "allenai/Olmo-3-1025-7B>allenai/Olmo-3-7B-Instruct": ("TULU", ["TULU"], "allenai", "Dolci-Instruct-SFT (Tulu successor)"),
    "allenai/Olmo-3-1125-32B>allenai/Olmo-3.1-32B-Instruct": ("TULU", ["TULU"], "allenai", "Dolci-Instruct-SFT"),
    "allenai/Olmo-Hybrid-7B>allenai/Olmo-Hybrid-Instruct-DPO-7B": ("TULU", ["TULU"], "allenai", "Dolci-Instruct-SFT-7B"),
    "baichuan-inc/Baichuan2-7B-Base>baichuan-inc/Baichuan2-7B-Chat": ("IN-HOUSE", [], "baichuan-inc", "proprietary human-annotated"),
    "bigscience/bloom-7b1>bigscience/bloomz-7b1": ("XP3", ["XP3"], "bigscience", "xP3 only"),
    "croissantllm/CroissantLLMBase>croissantllm/CroissantLLMChat-v0.1": ("H4", ["H4", "CROWD"], "croissantllm", "UltraChat, Wildchat, translation"),
    "deepseek-ai/deepseek-llm-7b-base>deepseek-ai/deepseek-llm-7b-chat": ("IN-HOUSE", [], "deepseek-ai", "internally collected"),
    "gl198976/mpt-7b>gl198976/mpt-7b-instruct": ("CROWD", ["CROWD"], "mosaicml", "dolly_hhrlhf"),
    "google/gemma-2-9b>google/gemma-2-9b-it": ("IN-HOUSE", [], "google", "unnamed synthetic + human"),
    "google/recurrentgemma-9b>google/recurrentgemma-9b-it": ("IN-HOUSE", [], "google", "follows the Gemma recipe"),
    "huggyllama/llama-7b>PKU-Alignment/beaver-7b-v1.0": ("PKU", ["PKU", "ALPACA"], "PKU-Alignment", "Alpaca SFT then PKU-SafeRLHF"),
    "ibm-granite/granite-3.0-8b-base>ibm-granite/granite-3.0-8b-instruct": ("IN-HOUSE", [], "ibm-granite", "permissive public + internal synthetic, unnamed"),
    "inceptionai/jais-family-6p7b>inceptionai/jais-family-6p7b-chat": ("IN-HOUSE", [], "inceptionai", "no dataset named"),
    "internlm/internlm2-base-7b>internlm/internlm2-chat-7b": ("IN-HOUSE", [], "internlm", "unnamed in-house"),
    "kakaocorp/kanana-1.5-8b-base>kakaocorp/kanana-1.5-8b-instruct-2505": ("IN-HOUSE", [], "kakaocorp", "Kanana SFT mixture, not itemised"),
    "kakaocorp/kanana-2-3b-base>kakaocorp/kanana-2-3b-instruct": ("NEMOTRON", ["NEMOTRON"], "kakaocorp", "Nemotron plus unenumerated open sets"),
    "llm-jp/llm-jp-3-7.2b>llm-jp/llm-jp-3-7.2b-instruct3": ("IN-HOUSE", [], "llm-jp", "ichikara, AnswerCarefully: Japanese, own"),
    "m-a-p/CT-LLM-Base>m-a-p/CT-LLM-SFT-DPO": ("DISTILL", ["DISTILL", "PKU"], "m-a-p", "alpaca-gpt4, comparison_gpt4, beavertails"),
    "m-a-p/neo_7b>m-a-p/neo_7b_instruct_v0.1": ("DISTILL", ["DISTILL"], "m-a-p", "OpenHermes 2.5, Nectar"),
    "meta-llama/Llama-3.1-70B>meta-llama/Llama-3.1-70B-Instruct": ("IN-HOUSE", [], "meta-llama", "unnamed public + synthetic"),
    "meta-llama/Llama-3.1-8B>meta-llama/Llama-3.1-8B-Instruct": ("IN-HOUSE", [], "meta-llama", "internally collected"),
    "mistralai/Mistral-7B-v0.1>mistralai/Mistral-7B-Instruct-v0.1": ("IN-HOUSE", [], "mistralai", "unnamed public HF datasets"),
    "openGPT-X/Teuken-7B-base-v0.6>openGPT-X/Teuken-7B-instruct-v0.6": ("IN-HOUSE", [], "openGPT-X", "benchmark-train splits, own mix"),
    "openbmb/MiniCPM5-1B-Base>openbmb/MiniCPM5-1B": ("IN-HOUSE", [], "openbmb", "UltraData-SFT (own)"),
    "stabilityai/stablelm-2-1_6b>stabilityai/stablelm-2-1_6b-chat": ("H4", ["H4", "DISTILL"], "stabilityai", "ultrachat_200k first, then MetaMath, WizardLM, SlimOrca, ShareGPT4, Capybara"),
    "team-hatakeyama-phase2/Tanuki-8B-base-v1.0>weblab-GENIAC/Tanuki-8B-dpo-v1.0": ("DISTILL", ["DISTILL", "NEMOTRON"], "weblab-GENIAC", "synthetic dialogue from Calm3, WizardLM2, Nemotron-4"),
    "tiiuae/Falcon-H1-1.5B-Base>tiiuae/Falcon-H1-1.5B-Instruct": ("TULU", ["TULU"], "tiiuae", "Tulu3 ~50% of SFT"),
    "tiiuae/Falcon-H1-7B-Base>tiiuae/Falcon-H1-7B-Instruct": ("TULU", ["TULU", "SMOLTALK"], "tiiuae", "Tulu3 most repeated; Smoltalk, OpenMathInstruct"),
    "tiiuae/Falcon3-7B-Base>tiiuae/Falcon3-7B-Instruct": ("IN-HOUSE", [], "tiiuae", "categories only"),
    "tiiuae/falcon-7b>tiiuae/falcon-7b-instruct": ("DISTILL", ["DISTILL"], "tiiuae", "Baize 65%, GPT4All 25%, GPTeacher"),
    "tiiuae/falcon-mamba-7b>tiiuae/falcon-mamba-7b-instruct": ("IN-HOUSE", [], "tiiuae", "unnamed"),
    "togethercomputer/RedPajama-INCITE-Base-7B-v0.1>togethercomputer/RedPajama-INCITE-7B-Chat": ("CROWD", ["CROWD"], "togethercomputer", "oasst1, dolly"),
    "zai-org/glm-4-9b-hf>zai-org/glm-4-9b-chat-hf": ("IN-HOUSE", [], "zai-org", "in-house + proprietary"),
}

#: base developer, for PRETRAIN; the endpoint developer is in L
PRETRAIN_ALIAS = {"huggyllama": "meta-llama", "gl198976": "mosaicml",
                  "team-hatakeyama-phase2": "weblab-GENIAC"}


def _check(keys):
    missing = set(keys) - set(L)
    extra = set(L) - set(keys)
    if missing or extra:
        raise SystemExit("cluster table does not match the roster: missing %s, extra %s"
                         % (sorted(missing)[:3], sorted(extra)[:3]))


def grouping(name, keys=None):
    """{lineage key: cluster label} under PRETRAIN, SFT or UNION."""
    if keys is not None:
        _check(keys)
    if name == "PRETRAIN":
        out = {}
        for k in L:
            dev = k.split("/")[0]
            out[k] = PRETRAIN_ALIAS.get(dev, dev)
        return out
    if name == "SFT":
        return {k: (v[0] if v[0] != "IN-HOUSE" else "dev:" + v[2]) for k, v in L.items()}
    if name == "UNION":
        parent = {k: k for k in L}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        by = collections.defaultdict(list)
        for k, (_dom, fams, dev, _why) in L.items():
            for f in fams:
                by["fam:" + f].append(k)
            by["dev:" + dev].append(k)
            by["dev:" + PRETRAIN_ALIAS.get(k.split("/")[0], k.split("/")[0])].append(k)
        for members in by.values():
            for m in members[1:]:
                parent[find(m)] = find(members[0])
        roots = {}
        return {k: roots.setdefault(find(k), "U%d" % (len(roots) + 1)) for k in L}
    raise ValueError(name)


if __name__ == "__main__":
    for g in ("PRETRAIN", "SFT", "UNION"):
        m = grouping(g)
        c = collections.Counter(m.values())
        print("%-9s %2d clusters; largest %s" % (g, len(c), c.most_common(4)))
    print("IN-HOUSE (no public dataset named): %d of %d"
          % (sum(1 for v in L.values() if v[0] == "IN-HOUSE"), len(L)))
