"""F21's two surviving claims, recomputed with the design's own units. -> results/f21_prompt_unit.md

    python -u f21_prompt_unit.py

**WHY.** F21 (malign-logits, findings/F21_institutional_alignment.md) booked
p-values like 1e-194 over ~21,000 tagged generations that are 24 prompts x ~11
families x 25 completions (its rider, clause 9: "the unit of the null should be
the unit that the design replicates"). Its rider killed the proceduralisation
headline and left two claims standing: the APOLOGY asymmetry (checked, clause 5)
and the DEFERENCE GAP being pretraining's. This file recomputes those two, plus
the addendum's agency-with-deference, with honest units and a declared arm. It
re-reads the old tags; it does not re-tag, so the rider's instrument clause (8:
the tagger is deepseek-chat and deepseek-7b is in the roster) still binds, and
every result is also shown without deepseek-7b.

**DECLARED BEFORE RUNNING (paper seat, 2026-09-23):**

    aligned arm   each family's LAST released stage (rlvr > dpo > sft), the
                  endpoint convention of `roster.endpoints()`; dpo-only shown
                  beside it as the one alternative
    families      those with a base checkpoint (10; llama has none, the four
                  frontier APIs have none)
    units         (a) the FAMILY: a family's mean over its prompts' means;
                  (b) the PROMPT PAIR: the 12 domain x n pairs that put the same
                  conflict to the individual and the institution, each side
                  averaged over families
    tests         sign tests over families (n=10) and over pairs (n=12), ties
                  dropped

Individual vs institution side from the role in the prompt key, as the rider's
recheck (`INSTITUTION_ROLES`). Source table:
~/github/malign-logits/data/f21_institutional_generations.csv (read-only).
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import binomtest

SRC = os.path.expanduser("~/github/malign-logits/data/f21_institutional_generations.csv")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "f21_prompt_unit.md")
INSTITUTION_ROLES = {"agency", "landlord", "mgmt", "doctor", "officer", "party"}
ORDER = ["rlvr", "dpo", "sft"]


def load():
    df = pd.read_csv(SRC)
    df = df[df.layer != "unknown"].copy()
    parts = df.prompt_key.str.split("_")
    df["domain"] = parts.str[1]
    df["role"] = parts.str[2]
    df["n"] = parts.str[3]
    df["pair"] = df.domain + "_" + df.n
    df["side"] = np.where(df.role.isin(INSTITUTION_ROLES), "institution", "individual")
    df["apology"] = df.apology_present.astype(str).str.lower().isin(["true", "1", "1.0"]).astype(float)
    return df


def arms(df, mode):
    rows = []
    for fam, d in df.groupby("family"):
        layers = set(d.layer)
        if "base" not in layers:
            continue
        if mode == "endpoint":
            al = next((l for l in ORDER if l in layers), None)
        else:
            al = "dpo" if "dpo" in layers else None
        if al is None:
            continue
        rows.append(d[d.layer == "base"].assign(arm="base"))
        rows.append(d[d.layer == al].assign(arm="aligned"))
    return pd.concat(rows)


def sign(v):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    up, dn = int((v > 0).sum()), int((v < 0).sum())
    p = binomtest(min(up, dn), up + dn).pvalue if up + dn else 1.0
    return up, dn, p


def fmt(v):
    up, dn, p = sign(v)
    return "%+.3f | %d/%d | %.2g" % (np.nanmedian(v), up, dn, p)


def analyse(d, var):
    """Per family and per pair: side means by arm. -> dict of arrays"""
    fam = d.groupby(["family", "side", "arm", "prompt_key"])[var].mean() \
           .groupby(["family", "side", "arm"]).mean().unstack(["side", "arm"])
    pr = d.groupby(["pair", "side", "arm", "family"])[var].mean() \
          .groupby(["pair", "side", "arm"]).mean().unstack(["side", "arm"])
    out = {}
    for name, t in (("family", fam), ("pair", pr)):
        g = lambda s, a: t[(s, a)].values
        out[name] = {
            "base gap (institution - individual)": g("institution", "base") - g("individual", "base"),
            "aligned gap (institution - individual)": g("institution", "aligned") - g("individual", "aligned"),
            "change, individual side": g("individual", "aligned") - g("individual", "base"),
            "change, institution side": g("institution", "aligned") - g("institution", "base"),
            "change in individual minus change in institution":
                (g("individual", "aligned") - g("individual", "base"))
                - (g("institution", "aligned") - g("institution", "base")),
        }
    return out


def main():
    df = load()
    lines = ["# F21's surviving claims with the design's own units", "",
             "Declared arm, families, units and tests: see the producer's docstring. "
             "Cells: median | up/down | sign-test p. Family unit n=10 (9 without deepseek-7b); "
             "pair unit n=12. Re-reads F21's deepseek-chat tags; no re-tagging.", ""]
    for mode in ("endpoint", "dpo"):
        for drop in (False, True):
            d = arms(df, mode)
            if drop:
                d = d[d.family != "deepseek-7b"]
            fams = sorted(d.family.unique())
            lines += ["## arm = %s%s" % (mode, ", without deepseek-7b" if drop else ""), "",
                      "families: %s" % ", ".join(fams), ""]
            for var, label in (("apology", "apology present (share)"),
                               ("institutional_deference", "institutional deference (1-5)"),
                               ("agency", "agency (1-5)")):
                res = analyse(d, var)
                lines += ["### %s" % label, "",
                          "| quantity | family unit | pair unit |", "|---|---|---|"]
                for q in res["family"]:
                    lines.append("| %s | %s | %s |" % (q, fmt(res["family"][q]), fmt(res["pair"][q])))
                lines.append("")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
