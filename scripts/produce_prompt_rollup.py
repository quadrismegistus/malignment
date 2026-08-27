"""Materialise the /prompts rollup as a parquet, so the page loads in milliseconds.

    python scripts/produce_prompt_rollup.py
    python scripts/produce_prompt_rollup.py --check   # print stats without writing

The query takes ~90s over ClickHouse views. This runs it once, writes
~/malignment-data/prompt_rollup.parquet, and the server reads that file on
startup instead of hitting CH on every page load.

Re-run after any ingest that changes the population (new cells, new endpoints,
new framed cells). The server shows `computed_at` from the file's metadata so
staleness is visible on screen.

## WHAT IS IN IT

One row per declared prompt (3,120 from the `prompts` table), with:
- roster metadata (domain, subdomain, family, language, pair_id, etc.)
- prompt_coverage_v4 (n_models, resid_median)
- prompt_movement_v4 (n_pairs, js_median, departed/arrived/net — raw→raw)
- prompt_movement_v4_crossframe (xf_* — raw→framed, system_mode=empty)
- n_measured_undeclared: count of prompts in twp_words not in the roster
"""
import argparse
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

OUT = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                  os.path.expanduser("~/malignment-data")),
                   "prompt_rollup.parquet")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    from malignment import ch

    print("querying prompt_movement_v4 + crossframe + coverage... (this takes ~90s)")
    import time
    t0 = time.monotonic()

    rows = ch.query("""
SELECT p.prompt AS prompt, p.prompt_id AS prompt_id, p.domain AS domain,
       p.subdomain AS subdomain, p.family AS family, p.language AS language,
       p.contrast_type AS contrast_type, p.pair_id AS pair_id,
       p.pair_role AS pair_role, p.source AS source, p.finding AS finding,
       p.status AS status, p.slot AS slot,
       cov.n_models AS n_models, cov.resid_median AS resid_median,
       pm.n_pairs AS n_pairs, pm.js_median AS js_median,
       pm.departed_median AS departed_median, pm.arrived_median AS arrived_median,
       pm.net_median AS net_median,
       xf.n_pairs AS xf_n_pairs, xf.js_median AS xf_js_median,
       xf.departed_median AS xf_departed_median, xf.arrived_median AS xf_arrived_median,
       xf.net_median AS xf_net_median
FROM {db}.prompts p
LEFT JOIN {db}.prompt_coverage_v4 cov ON cov.prompt = p.prompt
LEFT JOIN (SELECT * FROM {db}.prompt_movement_v4 WHERE rule = 'canonical') pm
       ON pm.prompt = p.prompt
LEFT JOIN (SELECT * FROM {db}.prompt_movement_v4_crossframe
           WHERE rule = 'canonical' AND system_mode_aligned = 'empty') xf
       ON xf.prompt = p.prompt
""")
    elapsed = time.monotonic() - t0
    print("  %d rows in %.1fs" % (len(rows), elapsed))

    undeclared = ch.scalar(
        "SELECT count() FROM (SELECT DISTINCT prompt FROM {db}.twp_words "
        "WHERE prompt NOT IN (SELECT prompt FROM {db}.prompts))", 0)
    print("  %d measured but undeclared prompts" % undeclared)

    n_xf = sum(1 for r in rows if r.get("xf_js_median") and r["xf_js_median"] > 0)
    print("  %d with cross-frame data" % n_xf)

    if a.check:
        return

    import pandas as pd
    df = pd.DataFrame(rows)
    computed_at = datetime.datetime.now().isoformat(timespec="seconds")
    df.attrs["computed_at"] = computed_at
    df.attrs["n_measured_undeclared"] = undeclared

    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    import pyarrow as pa
    import pyarrow.parquet as pq
    table = pa.Table.from_pandas(df)
    meta = table.schema.metadata or {}
    meta[b"computed_at"] = computed_at.encode()
    meta[b"n_measured_undeclared"] = str(undeclared).encode()
    table = table.replace_schema_metadata(meta)
    pq.write_table(table, a.out)

    sz = os.path.getsize(a.out)
    print("\nwrote %s (%.1f MB, %d rows, computed_at %s)"
          % (a.out, sz / 1e6, len(df), computed_at))


if __name__ == "__main__":
    main()
