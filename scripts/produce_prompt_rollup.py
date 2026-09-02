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
- dose_k_transgr: median base-arm k_transgressiveness across endpoint lineages
- dose_v6_harm: median base-arm mass on contextually harmful words (v6_harm >= 4)
- dose_slot_loaded: median base-arm mass on slot-level loaded words
- dose_charge: annotated scene transgressiveness (1-7), from charge.dose()
- dose_frame: annotated frame transgressiveness (1-7), from charge.frame()
- dose_increment: dose_charge - dose_frame (what the words add beyond the setup)
- n_measured_undeclared: count of prompts in twp_words not in the roster
"""
import argparse
import collections
import csv as _csv
import datetime
import gzip
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

OUT = os.path.join(os.environ.get("MALIGNMENT_DATA",
                                  os.path.expanduser("~/malignment-data")),
                   "prompt_rollup.parquet")
DATA = os.path.expanduser("~/malignment-data/norm_change")
V6_CUT = 4


def _endpoint_pairs():
    from malignment import roster
    ep, _ = roster.endpoints()
    return {"%s>%s" % (b, a) for b, a in ep.items()}


def _dose_k_transgr(ep):
    """Median base-arm k_transgressiveness per prompt, over endpoint lineages."""
    p = os.path.join(DATA, "levels_long.csv.gz")
    if not os.path.exists(p):
        print("  [dose] no levels_long.csv.gz")
        return {}
    by_prompt = collections.defaultdict(list)
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(head)}
        for line in fh:
            v = line.rstrip("\n").split("\t")
            if len(v) != len(head):
                continue
            if v[ix["scale"]] != "k_transgressiveness":
                continue
            bl = v[ix["base_level"]]
            if not bl or bl == "\\N":
                continue
            lin = v[ix["base"]] + ">" + v[ix["aligned"]]
            if lin not in ep:
                continue
            try:
                by_prompt[v[ix["prompt"]]].append(float(bl))
            except ValueError:
                continue
    out = {pr: statistics.median(vs) for pr, vs in by_prompt.items() if vs}
    print("  [dose] k_transgr: %d prompts" % len(out))
    return out


def _dose_v6_and_slot(ep):
    """Median base-arm mass on v6-harmful / slot-loaded words, one pass over words_long."""
    from malignment import fields as F

    v6_hot = {}
    for pr in F.slot_prompts():
        try:
            d = F.contextual_norms(pr)
        except Exception:
            continue
        hot = {w for w, v in d.items()
               if isinstance(v.get("v6_harm"), (int, float)) and v["v6_harm"] >= V6_CUT}
        if hot:
            v6_hot[pr] = hot
    print("  [dose] v6: %d prompts with words at v6_harm >= %d" % (len(v6_hot), V6_CUT))

    tagf = os.path.join(HERE, "..", "experiments", "instrument_calibrations",
                        "dose_response", "tags.csv.gz")
    slot_loaded = collections.defaultdict(set)
    if os.path.exists(tagf):
        with gzip.open(tagf, "rt", encoding="utf-8") as fh:
            for r in _csv.DictReader(fh, delimiter="\t"):
                slot_loaded[r["prompt"]].add(r["word"])
    print("  [dose] slot: %d prompts with loaded words" % len(slot_loaded))

    wl = os.path.join(DATA, "words_long.csv.gz")
    if not os.path.exists(wl):
        print("  [dose] no words_long.csv.gz")
        return {}, {}

    relevant = set(v6_hot) | set(slot_loaded)
    _csv.field_size_limit(sys.maxsize)
    v6_tot = collections.Counter()
    v6_hit = collections.Counter()
    sl_tot = collections.Counter()
    sl_hit = collections.Counter()
    with gzip.open(wl, "rt", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh, delimiter="\t"):
            pr = r["prompt"]
            if pr not in relevant:
                continue
            try:
                p = float(r["p_base"])
            except (TypeError, ValueError):
                continue
            lin = r["base"] + ">" + r["aligned"]
            if lin not in ep:
                continue
            if pr in v6_hot:
                v6_tot[(lin, pr)] += p
                if r["word"] in v6_hot[pr]:
                    v6_hit[(lin, pr)] += p
            if pr in slot_loaded:
                sl_tot[(lin, pr)] += p
                if r["word"] in slot_loaded[pr]:
                    sl_hit[(lin, pr)] += p

    def _median_per_prompt(tot, hit):
        by_prompt = collections.defaultdict(list)
        for k, t in tot.items():
            if t > 0:
                by_prompt[k[1]].append(hit[k] / t)
        return {pr: statistics.median(vs) for pr, vs in by_prompt.items() if vs}

    v6_out = _median_per_prompt(v6_tot, v6_hit)
    sl_out = _median_per_prompt(sl_tot, sl_hit)
    print("  [dose] v6_harm_mass: %d prompts, slot_loaded_mass: %d prompts"
          % (len(v6_out), len(sl_out)))
    return v6_out, sl_out


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

    print("\ncomputing dose metrics...")
    import time as _t
    t1 = _t.monotonic()
    ep = _endpoint_pairs()
    kt = _dose_k_transgr(ep)
    v6, sl = _dose_v6_and_slot(ep)
    df["dose_k_transgr"] = df["prompt"].map(kt)
    df["dose_v6_harm"] = df["prompt"].map(v6)
    df["dose_slot_loaded"] = df["prompt"].map(sl)
    from malignment import charge
    ch_doses = charge.doses()
    ch_frames = {p: charge.frame(p) for p in ch_doses}
    df["dose_charge"] = df["prompt"].map(ch_doses)
    df["dose_frame"] = df["prompt"].map(ch_frames)
    df["dose_increment"] = df["dose_charge"] - df["dose_frame"]
    n_kt = df["dose_k_transgr"].notna().sum()
    n_v6 = df["dose_v6_harm"].notna().sum()
    n_sl = df["dose_slot_loaded"].notna().sum()
    n_ch = df["dose_charge"].notna().sum()
    print("  dose columns: k_transgr=%d, v6_harm=%d, slot_loaded=%d, charge=%d (of %d prompts)"
          % (n_kt, n_v6, n_sl, n_ch, len(df)))
    print("  dose computation: %.1fs" % (_t.monotonic() - t1))
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
