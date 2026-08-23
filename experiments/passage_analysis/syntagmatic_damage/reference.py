"""Add a THIRD-PARTY reader to the syntagmatic result.

    python .../reference.py --plan            # what it would score, no GPU
    python .../reference.py --run             # score, resumable
    python .../reference.py --analyse         # the word-grain regression

`run.py` established, on 42 lineages, that a forced word's MOVEMENT predicts
the aligned model's SELF-surprisal over the following clause -- peak at token
bin [5,10), 38 of 42 lineages, with the opening word's probability controlled in
the same fit. That is the aligned model registering a trace of its own demotion.

**This asks a DIFFERENT question, not a validation of that one.** Does a reader
who never trained on either arm see the same disturbance? If yes, the trace is
in the text. If no, the self-surprisal result stands unchanged and gets sharper:
the trace is in the model's relation to what it was made to say.

## WORD GRAIN, AND IT IS NOT OPTIONAL

The self-surprisal effect sits at TOKEN positions [5,10), and token positions are
tokenizer-specific -- deepseek's token 5 is not Yi's token 5. `score.word_bits`
gives per-WORD surprisal, which is tokenizer-independent, so both sides are
re-expressed at word grain and the bin is stated in words. At ~1.3 tokens/word
the token bin [5,10) is roughly words [4,8); the word-grain self result is
recomputed here rather than assumed to land in the same place.

## THE JOIN IS DONE ONCE, AND CARRIED

`score.surprisal` is content-addressed on `sha(text)` and its `ids=` parameter is
accepted and never used, so the store cannot say where a text came from. This
producer therefore writes its own `ids.jsonl` mapping
`sha -> (corpus, model, prompt_full, forced_word, sample_idx)`.

Rows are selected by JOINING `gen_scores` to `gen_sequences` on
`(prompt_full, forced_word, sample_idx)`, verified 1:1 with
`length(logprobs) = n_tokens` on every row inspected. Sampling the two tables
independently would silently pair a passage with another passage's logprobs.

## SAMPLING

`--per-pair` rows per lineage, STRATIFIED BY ROLE so faller / matched / riser /
riser_matched are represented at the same rate. An unstratified sample populates
the `delta` axis unevenly per lineage and makes the per-pair coefficients
incomparable. Seeded and recorded.

**No junk screen.** `instrument_calibrations/junk_passages` measured that a
surface screen tops out at AUC 0.73, and f15 measured that retention is
arm-independent to within 0.7% -- so junk enters the faller-vs-riser contrast as
noise, not bias, and screening would cost more power than it removes.
"""
import argparse, base64, collections, hashlib, json, math, os, random, statistics as S, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.expanduser("~/github/malign-logits")
ARMS_JSON = os.path.join(ARCHIVE, "data/forced_arms_46reps_drmatch.json")
OUT = os.path.join(HERE, "results")
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))

WORD_BIN = (4, 8)          # words; the token [5,10) peak at ~1.3 tok/word
MIN_TOKENS = 60


def _q(v):
    return "'" + str(v).replace("'", "''") + "'"


def _ch():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_archive_ch", os.path.join(ARCHIVE, "malign_logits", "ch.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def arms():
    cells = json.load(open(ARMS_JSON))["cells"]
    role, delt, prob = {}, {}, {}
    for c in cells:
        for r, qk, dk in (("faller", "faller_q", "faller_delta"),
                          ("matched", "matched_q", "matched_delta"),
                          ("riser", "riser_q", "riser_delta"),
                          ("riser_matched", "riser_matched_q", "riser_matched_delta")):
            w = c.get(r)
            if not w:
                continue
            k = (c["pair"], c["prompt"], w)
            role[k] = r
            if c.get(dk) is not None:
                delt[k] = float(c[dk])
            if c.get(qk) is not None:
                prob[k] = float(c[qk])
    return role, delt, prob, sorted({c["pair"] for c in cells})


def select(a):
    """The joined, stratified sample. -> [dict] with text and the CH key."""
    ch = _ch()
    role, delt, prob, pairs = arms()
    rng = random.Random(a.seed)
    picked = []
    for pr in pairs:
        al = pr.split(">")[1]
        #: text comes back BASE64. ch.query parses JSONEachRow by splitting the
        #: response with Python's splitlines(), which breaks on \x0b \x0c \x1c
        #: \x1d \x1e \x85 U+2028 U+2029 -- none of which ClickHouse escapes. A
        #: passage holding one becomes two lines and the JSON string is left
        #: unterminated, so the whole lineage raised and was swallowed by the
        #: except below. Yi alone has U+2028 in 2,104 rows and U+2029 in 2,114
        #: of 11,872. Four lineages died this way (Yi, SmolLM3-3B, internlm2,
        #: Llama-3.1-8B) and that is exactly the 42-vs-38 gap. Encoding in
        #: transit keeps every such byte out of the line-splitting path.
        q = ("SELECT s.prompt_full AS prompt, s.forced_word AS forced_word, "
             "s.sample_idx AS sample_idx, base64Encode(s.text) AS text_b64, "
             "s.n_tokens AS n_tokens "
             "FROM (SELECT prompt_full, forced_word, sample_idx, text, n_tokens "
             "      FROM malign_logits.gen_sequences WHERE corpus='passage' "
             "      AND model=%s AND forced_word != '' AND n_tokens >= %d) s "
             #: g.prompt is TRUNCATED AT 60 CHARS. Joining s.prompt_full to it
             #: dropped every long-prompt row (25.2% of the store) and was the
             #: source of the kanana UNMAPPED jump, 160 -> 1552. Worse, 9 arms
             #: keys collide at 60 chars and each collision is a MINIMAL PAIR --
             #: a coercive stem against its own neutral control. gen_scores keeps
             #: both under prompt_full, so nothing was lost at write time.
             "INNER JOIN (SELECT prompt_full, forced_word, sample_idx FROM malign_logits.gen_scores "
             "            WHERE corpus='passage' AND model=%s AND scorer=%s "
             "            AND forced_word != '' AND scorable=1) g "
             "ON s.prompt_full = g.prompt_full AND s.forced_word = g.forced_word "
             "AND s.sample_idx = g.sample_idx"
             % (_q(al), MIN_TOKENS, _q(al), _q(al)))
        try:
            rows = ch.query(q)
        except Exception as e:
            print("  %-40s JOIN FAILED %s" % (al[:40], str(e)[:44]), flush=True)
            continue
        byrole = collections.defaultdict(list)
        for r in rows:
            k = (pr, r["prompt"], r["forced_word"])
            ro = role.get(k)
            if ro:
                byrole[ro].append((r, k))
        #: KEEP EVERY LINEAGE THAT HAS ANY JOINED ROWS. A lineage short of the
        #: per-role quota contributes what it has rather than dropping out --
        #: the population must match the self-surprisal run's, and a lineage
        #: silently absent is the difference between 42 and "38" that an
        #: earlier version of this file reported without explaining.
        want = max(a.per_pair // 4, 1)
        n_before = len(picked)
        for ro, lst in byrole.items():
            rng.shuffle(lst)
            for r, k in lst[:want]:
                txt = base64.b64decode(r["text_b64"]).decode("utf-8", "replace")
                picked.append(dict(pair=pr, model=al, prompt=r["prompt"],
                                   forced_word=r["forced_word"],
                                   sample_idx=r["sample_idx"], text=txt,
                                   role=ro, delta=delt.get(k), q=prob.get(k)))
        got = len(picked) - n_before
        short = "" if got >= a.per_pair else "   SHORT (has %d joined rows)" % sum(len(v) for v in byrole.values())
        if got == 0:
            short = "   NO JOINED ROWS -- lineage absent from this run"
        print("  %-40s roles %s -> %d%s" % (al.split("/")[-1][:40],
              {k: len(v) for k, v in byrole.items()}, got, short), flush=True)
    return picked


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-pair", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)

    if a.plan or a.run:
        rows = select(a)
        words = sum(len((r["text"] or "").split()) for r in rows)
        print()
        bypair = collections.Counter(r["pair"] for r in rows)
        print("SELECTED %d passages over %d lineages, %d words (~%.1fM)"
              % (len(rows), len(bypair), words, words / 1e6))
        thin = sorted((n, p) for p, n in bypair.items())[:6]
        print("  thinnest lineages: %s" % ", ".join("%s %d" % (p.split(">")[1].split("/")[-1][:22], n) for n, p in thin))
        print("  by role: %s" % dict(collections.Counter(r["role"] for r in rows)))
        if a.plan:
            json.dump(dict(n=len(rows), words=words, per_pair=a.per_pair, seed=a.seed,
                           by_role=dict(collections.Counter(r["role"] for r in rows))),
                      open(os.path.join(OUT, "reference_plan.json"), "w"), indent=1)
            print("-> results/reference_plan.json   (nothing scored)")
            return 0
        from malignment import score
        idp = os.path.join(OUT, "reference_ids.jsonl")
        with open(idp, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(dict(sha=score.sha(r["text"]), pair=r["pair"],
                                         model=r["model"], prompt=r["prompt"],
                                         forced_word=r["forced_word"],
                                         sample_idx=r["sample_idx"], role=r["role"],
                                         delta=r["delta"], q=r["q"]),
                                    ensure_ascii=False) + "\n")
        print("-> %s" % idp, flush=True)
        B = 64
        for i in range(0, len(rows), B):
            score.surprisal([r["text"] for r in rows[i:i + B]])
            if (i // B) % 10 == 0:
                print("  scored %d/%d" % (min(i + B, len(rows)), len(rows)), flush=True)
        print("scoring complete; store is content-addressed, rerun is free")
        return 0

    if a.analyse:
        print("analyse: not yet written -- word-grain regression over "
              "results/reference_ids.jsonl and the score store")
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
