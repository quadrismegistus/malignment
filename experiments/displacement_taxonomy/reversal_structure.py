"""Does anything GROUP the reversals? Domain, template, named group, prompt.

    python experiments/displacement_taxonomy/reversal_structure.py
    python experiments/displacement_taxonomy/reversal_structure.py --json

`crosslineage_rows.csv` marks each (prompt, lineage) reading member / reversed /
unassigned against that prompt's dominant operation. The reversals concentrate on
prompts at chi2=103.7 over 39 df. This asks what the concentration is ON.

## The answer is nothing nameable, and the near-miss is the point

Domain looks like the answer -- identity twice the others, Kruskal-Wallis
p=0.0423 with the prompt as the unit -- and it is an artifact of how the corpus
was written. The ten identity prompts are TWO templates with the group name
swapped, so identity's n=10 is n=2. Collapse near-duplicates on the corpus's own
`matched_set` and the effect goes to p=0.282.

Inside one template, across seven named groups in an otherwise identical
sentence, the spread is 3.4% to 20.7% and chi2=5.12 on 6 df, p=0.529: exactly
what n=29 produces at a common rate. A reading that the named group drives
reversal has no support here.

## Why both chi-square forms are computed

[6474] reported 90.2 and this file computes 103.7 on the same data. The
difference is exact: the first is the POISSON one-cell form, scoring the
reversed count against its expectation and never scoring the not-reversed count
against its own. For binomial counts both cells belong in the statistic, and
because (n-r) - n(1-p) = -(r - np) the two-cell total is the one-cell value
divided by (1-p) exactly. `assert_estimators` pins that identity, so an estimator
that is wrong by a fixed factor -- the kind that survives every sanity check
because it moves nothing a reader looks at -- fails here instead.

## Fence carried onto every output

`matched_set` is EMPTY on all ten violence prompts and on eight of ten
institutional ones. Empty means unmatched, not unique. So the template counts are
an UPPER bound on independence wherever the field is blank, and the template-level
test is conservative for identity and permissive everywhere else.
"""

import argparse, json, os, sys
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
#: The root, found by walking up from `malignment` itself, so this file does
#: not encode how deep under `experiments/` it sits. A wrong root makes the
#: globs below return [] instead of raising; `repo_root` refuses instead.
from malignment.paths import REPO
CSV = os.path.join(HERE, "results", "crosslineage_rows.csv")
OUT = os.path.join(HERE, "results", "reversal_structure.json")


def load():
    """Readings joined to the slot corpus's own domain and matched_set."""
    sys.path.insert(0, REPO)
    from malignment.slots import read_items, corpora
    meta = {}
    for _, p in corpora():
        for it in read_items(p):
            meta.setdefault(it["prompt"], it)
    d = pd.read_csv(CSV)
    miss = sorted(set(d.prompt) - set(meta))
    assert not miss, "prompts absent from the slot corpora: %s" % miss[:3]
    d["domain"] = d.prompt.map(lambda p: meta[p]["domain"])
    #: A blank `matched_set` is UNMATCHED, not unique -- it gets a per-prompt key
    #: so the collapse is a no-op there rather than pooling every unlabelled
    #: prompt in a domain into one fictional template.
    d["mset"] = d.prompt.map(lambda p: meta[p].get("matched_set") or ("solo:" + p[:24]))
    return d


def grids(d):
    g = (d.groupby(["domain", "mset", "prompt"]).status
           .value_counts().unstack(fill_value=0).reset_index())
    for c in ("member", "reversed", "unassigned"):
        if c not in g:
            g[c] = 0
    g["n"] = g[["member", "reversed", "unassigned"]].sum(axis=1)
    g["rate"] = g["reversed"] / g["n"]
    t = (g.groupby(["domain", "mset"])
           .agg(prompts=("prompt", "size"), reversed=("reversed", "sum"), n=("n", "sum"))
           .reset_index())
    t["rate"] = t["reversed"] / t["n"]
    return g, t


def booked(d, g):
    """Categorical first: a label cannot be approximately right."""
    assert set(d.status) == {"member", "reversed", "unassigned"}, "status values moved"
    assert d.prompt.nunique() == 40, "prompts: booked 40, got %d" % d.prompt.nunique()
    assert d.model.nunique() == 29, "lineages: booked 29, got %d" % d.model.nunique()
    assert (d.status == "reversed").sum() == 150, "reversed: booked 150"
    assert dict(g.domain.value_counts()) == {"identity": 10, "institutional": 10,
                                             "sexual": 10, "violence": 10}, \
        "the 10/10/10/10 domain balance moved"
    #: The design fact the whole finding turns on. If identity ever gets more
    #: templates this file's conclusion needs re-deriving, not re-running.
    ident = g[g.domain == "identity"].mset.nunique()
    assert ident == 2, "identity templates: booked 2, got %d -- re-derive, do not re-run" % ident


def chi(counts, ns, p, two_cell=True):
    exp = ns * p
    c1 = (((counts - exp) ** 2) / exp).sum()
    if not two_cell:
        return c1
    return c1 + ((((ns - counts) - ns * (1 - p)) ** 2) / (ns * (1 - p))).sum()


def assert_estimators(g):
    """two-cell / one-cell == 1/(1-p), exactly. See the module docstring."""
    p = g["reversed"].sum() / g["n"].sum()
    one = chi(g["reversed"], g["n"], p, two_cell=False)
    two = chi(g["reversed"], g["n"], p, two_cell=True)
    assert abs(two / one - 1 / (1 - p)) < 1e-9, \
        "chi-square forms do not stand in the 1/(1-p) relation: %.6f vs %.6f" % (two / one, 1 / (1 - p))
    return one, two, p


def main(write=False):
    d = load()
    g, t = grids(d)
    booked(d, g)
    one, two, p = assert_estimators(g)
    df = len(g) - 1
    res = {"n_readings": len(d), "n_reversed": int((d.status == "reversed").sum()),
           "pooled_rate": p,
           "dispersion": {"chi2_two_cell": two, "chi2_one_cell": one, "df": df,
                          "p": float(1 - stats.chi2.cdf(two, df))}}

    print("PROMPT-LEVEL DISPERSION")
    print("  two-cell (binomial, correct)  chi2=%.1f df=%d p=%.2e" % (two, df, res["dispersion"]["p"]))
    print("  one-cell (Poisson)            chi2=%.1f  -- understates by 1/(1-p) = %.5f"
          % (one, 1 / (1 - p)))

    print("\nBY DOMAIN")
    print("  %-14s %8s %8s %8s %10s" % ("domain", "pooled", "median", "prompts", "templates"))
    for dom, s in g.groupby("domain"):
        print("  %-14s %7.1f%% %7.1f%% %8d %10d"
              % (dom, 100 * s["reversed"].sum() / s["n"].sum(), 100 * s["rate"].median(),
                 len(s), s.mset.nunique()))
    H1, p1 = stats.kruskal(*[s["rate"].values for _, s in g.groupby("domain")])
    H2, p2 = stats.kruskal(*[s["rate"].values for _, s in t.groupby("domain")])
    res["domain"] = {"kruskal_prompt": {"H": H1, "p": p1},
                     "kruskal_template": {"H": H2, "p": p2}}
    print("\n  Kruskal-Wallis, prompt as unit    H=%.2f p=%.4f   <- artifact" % (H1, p1))
    print("  Kruskal-Wallis, TEMPLATE as unit  H=%.2f p=%.4f   <- the test that counts" % (H2, p2))
    print("  identity's ten prompts are two templates, so its n=10 is n=2.")

    print("\nINSIDE ONE TEMPLATE, only the group name changes")
    s = g[g.mset == "identity_action_violence"].sort_values("reversed", ascending=False)
    for _, r in s.iterrows():
        grp = r["prompt"].replace("Three ", "").replace(" came into the room and started to", "")
        print("    %-18s %2d/%2d  %5.1f%%" % (grp, r["reversed"], r["n"], 100 * r["rate"]))
    pb = s["reversed"].sum() / s["n"].sum()
    c = chi(s["reversed"], s["n"], pb, two_cell=True)
    gp = float(1 - stats.chi2.cdf(c, len(s) - 1))
    res["group_within_template"] = {"chi2": c, "df": len(s) - 1, "p": gp,
                                    "lo": float(s["rate"].min()), "hi": float(s["rate"].max())}
    print("    chi2=%.2f df=%d p=%.3f -- one rate with binomial noise; the named"
          % (c, len(s) - 1, gp))
    print("    group explains nothing here.")

    print("\n  FENCE: matched_set is empty on all 10 violence prompts and 8 of 10")
    print("  institutional. Empty is UNMATCHED, not unique, so template counts are")
    print("  an upper bound on independence wherever the field is blank.")

    if write:
        json.dump(res, open(OUT, "w"), indent=1, default=float)
        print("\n-> %s" % os.path.relpath(OUT, HERE))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="also write results/reversal_structure.json")
    main(write=ap.parse_args().json)
