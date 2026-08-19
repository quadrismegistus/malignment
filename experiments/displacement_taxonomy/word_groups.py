"""Pool one prompt's stage-1 annotations by shared base->aligned words.

    python word_groups.py --prompt "He entered her"      one, to stdout
    python word_groups.py --all                          all 40, to results/word_groups/
    python word_groups.py --list                         what prompts exist

## What this produces and why it is worth having

For ONE sentence, every model lineage's raters named a set of words the base arm
favours and a set the aligned arm favours. This joins those annotations wherever
they name the same words in the same direction, and prints each group's POOLED
vocabulary: what the base side looks like across all lineages at once, and what
the aligned side looks like.

That pooled view is the point. A single relation is one rater's reading of one
lineage; twenty relations pooled is the sentence's behaviour across the roster,
and it reads at a glance:

    "He started stroking his"
      base     penis, dick, cock, chest, hand, fingers, hard, face, shaft, big
      aligned  chin, beard, cock, penis, hair, hand, head, wife, cat, mustache

## It needs no harmonisation, so it covers everything

Stage 2 has run on ten prompts. This reads stage-1 annotations directly, so it
runs on all forty, and nothing in the grouping is a model's judgement: two
relations are joined iff their word sets overlap. Where the harmonisers, the
discrimination panel and the clustering pass are instruments whose reliability
had to be measured, this is arithmetic.

## Direction is a grouping criterion, not an annotation

Two relations are joined ONLY on same-direction overlap: base-with-base and
aligned-with-aligned. A relation running an axis one way and a relation running
it the other way are two groups, not one group carrying a sign.

That is not fastidiousness. Fourteen of thirty-three multi-relation constructs
from stage 2 pool members running in opposite directions, because the
harmonisation instrument asks for definitions in pole-neutral terms ("one pole
... the other") and direction is therefore unrepresentable in its output. Joining
on unsigned overlap here would reproduce that defect in a different notation.

MIRROR PAIRS are reported afterwards as a relation BETWEEN groups: group X's base
words appearing as group Y's aligned words is the same axis run both ways by
different lineages, which is a finding rather than a merge.

## What the threshold does, and what it cannot do

`--min` is how many shared words join two relations. Within one prompt every
relation draws on the same completion vocabulary, so overlap is dense and there
is NO threshold at which a clean multi-group structure appears: across four
prompts the largest group erodes monotonically (25, 20, 14, 12, 6, 3 as the
threshold rises from 2 to 8) and then shatters into singletons.

So do not read the groups as a taxonomy. Read GROUP 1 as the sentence's main
phenomenon pooled across the roster, and the singletons as the lineages that did
something else.
"""

import argparse
import collections
import os
import re

import run as R

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "results", "word_groups")
MIN_DEFAULT = 3
TOP_WORDS = 11


def _norm(w):
    #: Remove a POSSESSIVE suffix only. `str.strip("'s")` strips any leading or
    #: trailing ' or s character, which turned penis into peni, shaft into haft,
    #: said into aid and sat into at -- silently, in the one output this file
    #: exists to produce and visible nowhere else.
    w = w.lower()
    return w[:-2] if w.endswith("'s") else w


def prompts():
    st, out = R._stash(), collections.Counter()
    for k in st.keys():
        m = (st[k].get("meta") or {})
        if m.get("batch"):
            out[(m["domain"], m["frame_prompt"])] += 1
    return out


def load(prefix):
    st, rels, prompt = R._stash(), [], None
    for k in st.keys():
        m = (st[k].get("meta") or {})
        if not (m.get("batch") and m["frame_prompt"].startswith(prefix)):
            continue
        prompt = m["frame_prompt"]
        for x in st[k]["result"]["relations"]:
            if x.get("a_words") and x.get("b_words"):
                rels.append({"pair": m["pair"], "name": x["name"],
                             "conf": x.get("confidence"),
                             "A": {_norm(w) for w in x["a_words"]},
                             "B": {_norm(w) for w in x["b_words"]}})
    if prompt is None:
        raise SystemExit("no batched codings for a prompt starting %r" % prefix)
    #: Stable order so two runs produce byte-identical documents; the stash does
    #: not guarantee key order and the group numbering would otherwise drift.
    rels.sort(key=lambda r: (r["pair"], r["name"]))
    return prompt, rels


def group(rels, mn):
    par = list(range(len(rels)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(len(rels)):
        for j in range(i + 1, len(rels)):
            same = len(rels[i]["A"] & rels[j]["A"]) + len(rels[i]["B"] & rels[j]["B"])
            cross = len(rels[i]["A"] & rels[j]["B"]) + len(rels[i]["B"] & rels[j]["A"])
            if same >= mn and same > cross:
                par[find(j)] = find(i)
    G = collections.defaultdict(list)
    for i in range(len(rels)):
        G[find(i)].append(i)
    return sorted(G.values(), key=lambda g: (-len(g), rels[g[0]]["pair"]))


def render(prompt, rels, groups, mn):
    L, W = [], None
    L.append('PROMPT: "%s"   overlap threshold %d' % (prompt, mn))
    L.append("%d two-sided relations, %d lineages" % (len(rels), len({r["pair"] for r in rels})))
    L.append("")
    for n, g in enumerate(groups, 1):
        #: Ordered by how many relations name the word, so the head of each list
        #: is what the roster agrees on rather than whatever sorts first.
        A = collections.Counter(w for i in g for w in rels[i]["A"])
        B = collections.Counter(w for i in g for w in rels[i]["B"])
        L.append("=" * 76)
        L.append("GROUP %d -- %d relation(s), %d lineage(s)"
                 % (n, len(g), len({rels[i]["pair"] for i in g})))
        L.append("  base side:    %s" % ", ".join(w for w, _ in A.most_common(TOP_WORDS)))
        L.append("  aligned side: %s" % ", ".join(w for w, _ in B.most_common(TOP_WORDS)))
        L.append("=" * 76)
        for i in g:
            r = rels[i]
            L.append("   %-44s %-26s [%s]" % (r["name"][:44], r["pair"][:26], r["conf"]))
        L.append("")
    L.append("=" * 76)
    L.append("MIRROR PAIRS -- group X's BASE words are group Y's ALIGNED words")
    L.append("=" * 76)
    found = 0
    for a in range(len(groups)):
        for b in range(a + 1, len(groups)):
            Aa = set().union(*[rels[i]["A"] for i in groups[a]])
            Ba = set().union(*[rels[i]["B"] for i in groups[a]])
            Ab = set().union(*[rels[i]["A"] for i in groups[b]])
            Bb = set().union(*[rels[i]["B"] for i in groups[b]])
            cross = len(Aa & Bb) + len(Ba & Ab)
            if cross >= mn:
                found += 1
                L.append("  GROUP %d  <->  GROUP %d   (%d words cross)" % (a + 1, b + 1, cross))
                L.append("     shared: %s" % ", ".join(sorted((Aa & Bb) | (Ba & Ab))))
                L.append("     %d: %s" % (a + 1, ", ".join(sorted({rels[i]["pair"] for i in groups[a]}))))
                L.append("     %d: %s" % (b + 1, ", ".join(sorted({rels[i]["pair"] for i in groups[b]}))))
                L.append("")
    if not found:
        L.append("  none")
    return "\n".join(L)


def mirrors(rels, groups, mn):
    """{group index -> [group indices whose ALIGNED words are its BASE words]}.

    Computed over ALL groups including singletons, because a singleton is exactly
    where a lone dissenting lineage lands: on "He entered her" eighteen lineages
    move away from mouth/vagina/womb and SmolLM3-3B moves toward them, and that
    one relation is the whole finding. Dropping singleton ROWS from the csv must
    not drop them as mirror TARGETS.
    """
    out = collections.defaultdict(list)
    for a in range(len(groups)):
        for b in range(len(groups)):
            if a == b:
                continue
            Aa = set().union(*[rels[i]["A"] for i in groups[a]])
            Ba = set().union(*[rels[i]["B"] for i in groups[a]])
            Ab = set().union(*[rels[i]["A"] for i in groups[b]])
            Bb = set().union(*[rels[i]["B"] for i in groups[b]])
            if len(Aa & Bb) + len(Ba & Ab) >= mn:
                out[a].append(b + 1)
    return out


def csv_rows(prefix, mn, domain):
    """One row per relation, singleton groups omitted as rows."""
    prompt, rels = load(prefix)
    groups = group(rels, mn)
    mir = mirrors(rels, groups, mn)
    rows = []
    for n, g in enumerate(groups, 1):
        if len(g) < 2:
            continue
        for i in g:
            r = rels[i]
            rows.append({
                "prompt": prompt, "domain": domain,
                "group": n,
                "reverse_group": ";".join(str(x) for x in sorted(mir.get(n - 1, []))),
                "relation_name": r["name"], "model": r["pair"],
                "confidence": r["conf"],
                "base_words": " ".join(sorted(r["A"])),
                "aligned_words": " ".join(sorted(r["B"])),
            })
    return rows


def one(prefix, mn, write=False):
    prompt, rels = load(prefix)
    txt = render(prompt, rels, group(rels, mn), mn)
    if not write:
        print(txt)
        return prompt, None, len(rels)
    os.makedirs(OUTDIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", prompt.lower())[:44].strip("_")
    p = os.path.join(OUTDIR, "%s.txt" % slug)
    open(p, "w").write(txt + "\n")
    return prompt, p, len(rels)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prompt", metavar="PREFIX")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--min", type=int, default=MIN_DEFAULT)
    ap.add_argument("--csv", metavar="PATH", nargs="?",
                    const=os.path.join(HERE, "results", "word_groups.csv"),
                    help="every prompt, one row per relation, singleton groups omitted")
    a = ap.parse_args()
    if a.csv:
        import csv as _csv
        allrows = []
        for (dom, p), _ in sorted(prompts().items()):
            allrows += csv_rows(p[:30], a.min, dom)
        cols = ["prompt", "domain", "group", "reverse_group", "relation_name",
                "model", "confidence", "base_words", "aligned_words"]
        with open(a.csv, "w", newline="") as fh:
            w = _csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(allrows)
        n_rev = sum(1 for r in allrows if r["reverse_group"])
        print("wrote %s\n  %d rows over %d prompts, %d groups"
              % (a.csv, len(allrows), len({r["prompt"] for r in allrows}),
                 len({(r["prompt"], r["group"]) for r in allrows})))
        print("  %d rows sit in a group that has a mirror group (%.0f%%)"
              % (n_rev, 100 * n_rev / max(1, len(allrows))))
    elif a.list:
        for (dom, p), n in sorted(prompts().items()):
            print("  %-14s %3d cells  %s" % (dom, n, p))
    elif a.all:
        seen = set()
        for (dom, p), _ in sorted(prompts().items()):
            _, path, nr = one(p[:30], a.min, write=True)
            if path in seen:
                raise SystemExit("two prompts wrote the same file: %s" % path)
            seen.add(path)
            print("  %-14s %2d relations  %s" % (dom, nr, os.path.basename(path)))
        print("\nwrote %d documents to %s" % (len(seen), OUTDIR))
    elif a.prompt:
        one(a.prompt, a.min)
    else:
        ap.print_help()
