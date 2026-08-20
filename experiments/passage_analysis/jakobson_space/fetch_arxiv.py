"""Fetch arXiv abstracts across categories for the human anchor.

    python experiments/passage_analysis/jakobson_space/fetch_arxiv.py --out $MALIGNMENT_DATA/jakobson_space/arxiv_raw.jsonl

The archived `arxiv_abstracts_500.csv` cannot supply this pool for two reasons.
It has 307 abstracts at >=159 words against a target of 600, and it is a narrow
slice: 98 of 500 mention `graph`, 85 `dataset`, 66 `neural` against 5 `galaxy`
and 1 `protein`. That is LLM-era cs.CL/cs.LG, not "academic abstracts", and
against philosophy and literary criticism it would confound genre with field.

So this samples ACROSS categories with an equal quota each, and the quota is the
design: an unweighted arXiv draw is mostly physics and cs, which would reproduce
the same skew more slowly.

## Rate limit

arXiv asks for one request every 3 seconds and it is a free public API run by a
library. DELAY is not tunable below that from the command line on purpose.

## What is NOT done here

No cleaning. LaTeX (`~$\\gamma$`), line wrapping and entities are left exactly as
served, because normalisation happens once for all six corpora in the same pass
and doing part of it here would put this corpus on a different footing. See
`build_human_pool.py`.
"""

import argparse, json, os, re, sys, time, urllib.parse, urllib.request

API = "http://export.arxiv.org/api/query"
DELAY = 3.0
PAGE = 100

#: Eight categories, deliberately spread across the divisions rather than
#: weighted by volume. `math.AG` and `econ.EM` are here to pull the register away
#: from the machine-learning abstract, which is its own dialect.
CATEGORIES = [
    "cs.CL", "math.AG", "astro-ph.GA", "cond-mat.stat-mech",
    "q-bio.PE", "econ.EM", "stat.ME", "hep-th",
]

NS = "{http://www.w3.org/2005/Atom}"


def fetch(cat, want, delay, verbose=True):
    """-> list of dicts. Paginates until `want` entries or the feed runs dry."""
    import xml.etree.ElementTree as ET
    out, start = [], 0
    while len(out) < want:
        q = urllib.parse.urlencode({
            "search_query": "cat:%s" % cat,
            "start": start,
            "max_results": min(PAGE, want - len(out)),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        req = urllib.request.Request(
            "%s?%s" % (API, q),
            headers={"User-Agent": "malignment-research/1.0 (academic corpus study)"})
        try:
            with urllib.request.urlopen(req, timeout=60) as fh:
                body = fh.read()
        except Exception as e:
            print("  %s: request failed at start=%d: %s" % (cat, start, e))
            break
        try:
            root = ET.fromstring(body)
        except ET.ParseError as e:
            print("  %s: unparseable feed at start=%d: %s" % (cat, start, e))
            break
        entries = root.findall(NS + "entry")
        if not entries:
            break
        for e in entries:
            summ = e.findtext(NS + "summary") or ""
            idu = e.findtext(NS + "id") or ""
            out.append(dict(
                arxiv_id=idu.rsplit("/", 1)[-1],
                category=cat,
                published=e.findtext(NS + "published") or "",
                title=" ".join((e.findtext(NS + "title") or "").split()),
                abstract=summ,
            ))
        start += len(entries)
        if verbose:
            print("  %-20s %4d fetched" % (cat, len(out)))
        time.sleep(delay)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-category", type=int, default=400,
                    help="raw abstracts to pull per category before any filter")
    ap.add_argument("--delay", type=float, default=DELAY)
    a = ap.parse_args(argv)
    if a.delay < DELAY:
        sys.exit("refusing: arXiv asks for %.1fs between requests" % DELAY)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    rows, seen = [], set()
    for cat in CATEGORIES:
        got = fetch(cat, a.per_category, a.delay)
        for r in got:
            #: cross-listed papers appear under several categories; first wins,
            #: so the quota is over DISTINCT papers rather than over listings
            if r["arxiv_id"] in seen:
                continue
            seen.add(r["arxiv_id"])
            rows.append(r)
        print("%-20s -> %d new (running total %d)" % (cat, len(got), len(rows)))

    with open(a.out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    #: report the yield against the band so the caller knows if it is enough
    import collections
    n159 = collections.Counter()
    for r in rows:
        if len(r["abstract"].split()) >= 159:
            n159[r["category"]] += 1
    print("\n%d abstracts written -> %s" % (len(rows), a.out))
    print("at >=159 words: %d" % sum(n159.values()))
    for c in CATEGORIES:
        print("  %-20s %4d" % (c, n159[c]))


if __name__ == "__main__":
    main()
