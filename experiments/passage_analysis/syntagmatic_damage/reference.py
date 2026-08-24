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
gives per-WORD surprisal, which is tokenizer-independent, so the REFERENCE side
is reported at word grain, bins stated in words. At ~1.3 tokens/word the token
bin [5,10) is roughly words [4,8).

### THE SELF SIDE CANNOT BE MOVED TO WORD GRAIN, AND THIS PLAN SAID IT WOULD

An earlier version of this docstring promised the self result would be
"recomputed here rather than assumed to land in the same place." It cannot be,
and the reason is worth keeping rather than quietly dropping.

Word boundaries need byte offsets per token. `gen_scores` stores `logprobs` and
nothing else positional; `gen_sequences` stores text and `n_tokens`. Recovering
offsets means re-tokenising the decoded text with each lineage's own tokenizer
and trusting the result to reproduce the stored token count. Measured on 40-60
rows per lineage, it does not:

    Yi-1.5-9B-Chat              36/40        salamandra-7b-instruct     5/40
    AquilaChat2-7B              36/40        SmolLM2-360M-Instruct     26/40
    eleuther-pythia6.9b-hh-dpo  34/40

and the shortfall is NOT a constant offset that could be corrected. salamandra
sits mostly at +1 but spreads over 0/+1/+2; SmolLM2 and Yi centre on 0 with a
-1/-2 tail. That is real divergence on re-encode, not a convention.

Keeping only the rows that match would drop ~87% of salamandra against ~10% of
Yi -- selection on a nuisance that varies BY LINEAGE, which is the unit of every
claim here. So the self side stays at its own token grain, where run.py measured
it, and this file reports the reference at BOTH word grain and deepseek-token
grain. Deepseek-token bins are legitimate because deepseek is one tokenizer
across every passage; the tokenizer-specificity objection was always about
comparing 42 different aligned tokenizers, never about the reference reader.

The comparison is therefore "does a third party show a delta effect in the same
early-continuation region", not "at identical indices". That is enough for the
question being asked and the shortfall is stated rather than papered over.

8 of the 46 aligned tokenizers also refuse `AutoTokenizer`; 7 load via
`PreTrainedTokenizerFast` directly and Teuken-7B needs `tiktoken`, which is not
installed. None of this is on the path any more, and it is recorded only so the
next attempt does not rediscover it.

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
MIN_ROWS = 40              # per lineage, to fit a 3-parameter OLS at all

#: WORD bins, and DEEPSEEK-TOKEN bins. The token bins mirror run.py's exactly so
#: the two sides can be read against each other; they are honest here because
#: deepseek is ONE tokenizer across every passage, which is not true of the self
#: side. See "THE SELF SIDE CANNOT BE MOVED TO WORD GRAIN" in the docstring.
WORD_BINS = [(0, 1), (1, 4), (4, 8), (8, 16), (16, 24), (24, 48)]
TOK_BINS = [(0, 1), (1, 5), (5, 10), (10, 20), (20, 30), (30, 60)]


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


def ctx_rows():
    """The SAME population as --run, rebuilt with the model's own context.

    THE ASYMMETRY THIS REPAIRS. `--run` scored the continuation ALONE, because
    `score.surprisal` is content-addressed on the text and the stored `text` is
    what follows the forced word -- no prompt, no forced word. The self-surprisal
    side had both: `gen_scores.logprobs` come from teacher-forcing over
    prompt + forced word + continuation. So the first comparison was
    self-WITH-context against reference-WITHOUT-context, and its null on `delta`
    is consistent with "no trace in the text" AND with "the reference was never
    shown the joint where the trace lives".

    RECONSTRUCTION, from the codebase's own convention rather than from the
    shape of the strings: the forced word enters as `" " + word`
    (`malign_logits/analysis.py:68` `text = prompt + " " + word`, and
    `encode(" " + word)` in models.py:243, metrics.py:368/1027, circuit.py:320,
    step_analysis.py:114, psyche.py:202). `text` is the raw decode of the
    generated tokens and keeps its own leading space, which is why 91% of rows
    in BOTH arms start with one.

        full = prompt_full + " " + forced_word + text

    `ctx_bytes` is the byte length of the prefix, so the continuation can be cut
    out of the scored array exactly. Scoring is on `sha(full)`, a different key
    from `sha(text)`, so the two runs cannot collide in the store.
    """
    from malignment import score
    rows = selected()
    idx = score._index("surprisal")
    out, missing = [], 0
    for r in rows:
        s = idx.get(r["sha"])
        if not s or not s.get("scored"):
            missing += 1
            continue
        prefix = r["prompt"] + " " + r["forced_word"]
        full = prefix + s["text"]
        out.append(dict(r, full=full, ctx_bytes=len(prefix.encode()),
                        text=s["text"], sha_full=score.sha(full)))
    if missing:
        print("  %d rows have no stored text and are skipped" % missing)
    return out


def binom(k, n):
    """Two-sided sign test. Same implementation as run.py, deliberately."""
    return (min(1.0, 2 * sum(math.comb(n, j) for j in range(0, min(k, n - k) + 1))
                / 2.0 ** n) if n else float("nan"))


def selected():
    """The rows this producer chose, from its own ids.jsonl. -> [dict]

    Deduped on the FULL cell tuple and not on `sha`. The file opens in append
    mode so a second --run doubles it, and one passage TEXT can legitimately
    belong to two cells -- deduping on sha alone would silently drop a real row.
    """
    p = os.path.join(OUT, "reference_ids.jsonl")
    if not os.path.exists(p):
        print("no %s -- run --run first" % p)
        return []
    seen, out = set(), []
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        k = (r["sha"], r["pair"], r["prompt"], r["forced_word"], r["sample_idx"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def analyse(a):
    """Per-lineage OLS of REFERENCE surprisal on (log q, delta), then a sign test.

    The fit is run.py's, term for term -- y ~ 1 + log q + delta, one fit per
    lineage, the lineage as the unit -- so the coefficient printed here and the
    one printed there are the same quantity read by two different models.
    """
    import numpy as np
    from malignment import score

    rows = selected()
    if not rows:
        return 1
    idx = score._index("surprisal")
    bypair = collections.defaultdict(list)
    unscored = 0
    for r in rows:
        s = idx.get(r["sha"])
        if not s or not s.get("scored"):
            unscored += 1
            continue
        bypair[r["pair"]].append((r, s))
    print("%d selected rows, %d not yet in the store, %d lineages present"
          % (len(rows), unscored, len(bypair)), flush=True)
    if unscored:
        print("  (--run is still going or was interrupted; this is a PARTIAL read)")

    wres = collections.defaultdict(list)
    tres = collections.defaultdict(list)
    nfit = 0
    for pr, items in sorted(bypair.items()):
        X, wy, ty = [], [], []
        for r, s in items:
            q = r.get("q")
            if not q or q <= 0:
                continue
            #: per-token bits straight from the block, and per-word bits via the
            #: committed word_bits implementation. Both are deepseek's.
            tok = score._block("surprisal", s)
            wb = score.word_bits(s["text"])
            if tok.size < TOK_BINS[-1][0] or len(wb) < WORD_BINS[-1][0]:
                continue
            X.append([1.0, math.log(q), r.get("delta") or 0.0])
            ty.append(tok)
            wy.append(np.array([w["bits"] for w in wb], dtype=np.float32))
        if len(X) < MIN_ROWS:
            continue
        nfit += 1
        Xm = np.array(X)
        for bins, ys, acc in ((WORD_BINS, wy, wres), (TOK_BINS, ty, tres)):
            for lo, hi in bins:
                #: a passage shorter than the bin contributes nothing to it
                #: rather than a truncated mean, which would be a length
                #: statistic wearing a surprisal label.
                keep = [i for i, v in enumerate(ys) if v.size >= hi]
                if len(keep) < MIN_ROWS:
                    continue
                yy = np.array([float(ys[i][lo:hi].mean()) for i in keep])
                c = np.linalg.lstsq(Xm[keep], yy, rcond=None)[0]
                lab = "[%d,%d)" % (lo, hi)
                acc[(lab, "logq")].append(c[1])
                acc[(lab, "delta")].append(c[2])
    print("fitted %d lineages (>= %d usable rows each)" % (nfit, MIN_ROWS))

    for acc, bins, title in (
            (wres, WORD_BINS, "REFERENCE (deepseek) surprisal, WORD bins after the forced word"),
            (tres, TOK_BINS, "REFERENCE (deepseek) surprisal, DEEPSEEK-TOKEN bins")):
        print()
        print(title)
        print("  %-10s %-7s %4s %10s %9s %9s" % ("bin", "term", "n", "median", "up/down", "sign p"))
        for lo, hi in bins:
            lab = "[%d,%d)" % (lo, hi)
            for term in ("logq", "delta"):
                v = acc.get((lab, term))
                if not v:
                    continue
                dn = sum(1 for x in v if x < 0)
                print("  %-10s %-7s %4d %10.5f %5d/%-3d %9.5f"
                      % (lab, term, len(v), S.median(v), len(v) - dn, dn,
                         binom(len(v) - dn, len(v))))
    print()
    print("Read `delta` against run.py's self-surprisal table. A delta effect")
    print("here means the disturbance is IN THE TEXT and a third party sees it.")
    print("Its absence, with logq present, means the trace is in the aligned")
    print("model's relation to what it was made to say -- which is the sharper")
    print("result, not the weaker one.")
    return 0


def run_ctx(a):
    """Score prompt + forced word + continuation. Resumable; the store dedupes."""
    from malignment import score
    rows = ctx_rows()
    if not rows:
        print("no rows -- run --run first")
        return 1
    words = sum(len(r["full"].split()) for r in rows)
    print("%d passages WITH CONTEXT, %d words" % (len(rows), words), flush=True)
    if a.plan:
        #: verify the reconstruction on real rows and score NOTHING. The check
        #: that matters is that the prefix ends where the continuation begins.
        #: slice the BYTES, not the characters. ctx_bytes is a byte offset and
        #: the two diverge on every non-ASCII prompt -- an earlier version of
        #: this check sliced `full[:ctx_bytes]` and reported 396 false failures,
        #: all of them Chinese. The analysis compares ctx_bytes against
        #: byte-ends, so it was never affected; only the check was.
        bad = [r for r in rows
               if r["full"].encode()[:r["ctx_bytes"]]
               [-len(r["forced_word"].encode()):] != r["forced_word"].encode()]
        print("rows whose prefix does not end in the forced word: %d" % len(bad))
        for r in rows[:3]:
            print()
            print("  prefix  %r" % r["full"][:r["ctx_bytes"]][-70:])
            print("  cont    %r" % r["full"][r["ctx_bytes"]:][:70])
        json.dump(dict(n=len(rows), words=words),
                  open(os.path.join(OUT, "reference_ctx_plan.json"), "w"), indent=1)
        print()
        print("-> results/reference_ctx_plan.json   (nothing scored)")
        return 0
    idp = os.path.join(OUT, "reference_ctx_ids.jsonl")
    with open(idp, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: r[k] for k in
                                 ("sha_full", "sha", "pair", "model", "prompt",
                                  "forced_word", "sample_idx", "role", "delta",
                                  "q", "ctx_bytes")}, ensure_ascii=False) + "\n")
    print("-> %s" % idp, flush=True)
    B = 64
    for i in range(0, len(rows), B):
        score.surprisal([r["full"] for r in rows[i:i + B]])
        if (i // B) % 10 == 0:
            print("  scored %d/%d" % (min(i + B, len(rows)), len(rows)), flush=True)
    print("scoring complete; store is content-addressed, rerun is free")
    return 0


def analyse_ctx(a):
    """The same regression, on the continuation cut out of a context-scored pass.

    Tokens are selected by BYTE END, not by index: the prefix tokenises to a
    different number of deepseek tokens for every row, so a fixed offset would
    silently mix prompt tokens into the window on some rows and drop
    continuation tokens on others.
    """
    import numpy as np
    from malignment import score
    rows = ctx_rows()
    idx = score._index("surprisal")
    bypair = collections.defaultdict(list)
    unscored = 0
    for r in rows:
        s = idx.get(r["sha_full"])
        if not s or not s.get("scored"):
            unscored += 1
            continue
        bypair[r["pair"]].append((r, s))
    print("%d rows, %d not yet scored with context, %d lineages"
          % (len(rows), unscored, len(bypair)))
    if unscored:
        print("  (PARTIAL read -- --run-ctx is still going or was interrupted)")
    if not bypair:
        return 1

    res = collections.defaultdict(list)
    nfit = 0
    for pr, items in sorted(bypair.items()):
        X, ys = [], []
        for r, s in items:
            q = r.get("q")
            if not q or q <= 0:
                continue
            bits = score._block("surprisal", s)
            ends = score._block("surprisal", s, "i32")
            if bits.size != ends.size or bits.size == 0:
                continue
            #: the first token whose byte-end passes the prefix is the first
            #: token of the continuation.
            k = int(np.searchsorted(ends, r["ctx_bytes"], side="right"))
            v = bits[k:]
            if v.size < TOK_BINS[-1][0]:
                continue
            X.append([1.0, math.log(q), r.get("delta") or 0.0])
            ys.append(v)
        if len(X) < MIN_ROWS:
            continue
        nfit += 1
        Xm = np.array(X)
        for lo, hi in TOK_BINS:
            keep = [i for i, v in enumerate(ys) if v.size >= hi]
            if len(keep) < MIN_ROWS:
                continue
            yy = np.array([float(ys[i][lo:hi].mean()) for i in keep])
            c = np.linalg.lstsq(Xm[keep], yy, rcond=None)[0]
            lab = "[%d,%d)" % (lo, hi)
            res[(lab, "logq")].append(c[1])
            res[(lab, "delta")].append(c[2])
    print("fitted %d lineages" % nfit)
    print()
    print("REFERENCE WITH CONTEXT -- deepseek reads prompt + forced word + continuation")
    print("  %-10s %-7s %4s %10s %9s %9s" % ("bin", "term", "n", "median", "up/down", "sign p"))
    for lo, hi in TOK_BINS:
        lab = "[%d,%d)" % (lo, hi)
        for term in ("logq", "delta"):
            v = res.get((lab, term))
            if not v:
                continue
            dn = sum(1 for x in v if x < 0)
            print("  %-10s %-7s %4d %10.5f %5d/%-3d %9.5f"
                  % (lab, term, len(v), S.median(v), len(v) - dn, dn,
                     binom(len(v) - dn, len(v))))
    print()
    print("Against the CONTEXT-FREE pass, whose delta was null at [5,10)")
    print("(-0.303, 17/24, p=0.35), and against run.py's SELF result at the")
    print("same bin (-0.542, 5/37, p<1e-5).")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-pair", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--analyse", action="store_true")
    ap.add_argument("--run-ctx", dest="run_ctx", action="store_true",
                    help="score prompt + forced word + continuation")
    ap.add_argument("--analyse-ctx", dest="analyse_ctx", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)

    if a.run_ctx:
        return run_ctx(a)
    if a.analyse_ctx:
        return analyse_ctx(a)

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
        return analyse(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
