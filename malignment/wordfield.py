#!/usr/bin/env python
"""Join a WORD-LEVEL annotation to movement. The shape of a whole class of experiment.

    from malignment.wordfield import WordField, measure, share

    f = WordField.from_lexicon("sexual/violent", ".../lexicon.json", key="category")
    f.push()
    cells = measure(pairs, f, prompts=panel)
    rows  = share(cells, chains, labels=("sexual", "violent"))

## WHY THIS IS A MODULE AND NOT A SCRIPT

The first version of this lived inside `experiments/division_of_labour/
lexical_domains/run.py`. It was going to be retyped into `register_shift/run.py`
the same afternoon, and then again for every fields.py source (RID, General
Inquirer, USAS, k-ratings, Warriner, Brysbaert), because THE QUESTION IS ALWAYS
THE SAME SHAPE: label the words, join to movement, aggregate per cell, compare
the two arms of a chain. RH stopped it. This repository has already paid for the
alternative -- `produce_movement.DERIVING` was a retyped copy missing five ops,
so the Falcon3 upscale and prune edges had NEVER been in movement, undetected
until someone diffed the two definitions.

## THE THREE THINGS THAT MUST NOT BE RETYPED

**0. `inherited`** -- the mass the aligned side STARTED from, i.e. `sum(p_base)`
of that edge. For a sequential pipeline this is the only fair denominator: the
preference stage inherits what SFT already stripped, so comparing raw amounts
punishes it for arriving second. Removal RATE = departed / inherited.

**1. The per-word JS term.** JS is a sum over words plus a tail, so a label's
contribution is EXACT, not approximate:

    js_w = 0.5 * ( p*log2(p/m) + q*log2(q/m) ),   m = (p+q)/2

with the p=0 and q=0 guards, which is where a hand-rolled version goes wrong: it
returns nan for exactly the words that entered or left the distribution, i.e.
the interesting ones. `conservation()` checks the sum against
`movement_cells.js_total - js_tail`, booked by a different producer.

**2. Same prompts on both arms.** A chain's SFT arm and endpoint arm do not hold
identical prompt sets. Taking each arm's own mean compares two populations; that
error once dropped 65% of amber's cells. `share()` intersects, always.

**3. Base-level aggregation.** Chains sharing a base are not independent -- 18
chains are 16 bases. `sft_share` declared this decisive in an amendment and then
did not compute it, so its verdict rested on arithmetic done by hand while the
producer printed the friendlier chain-level number. `share()` returns both and
names which decides.

## CATEGORICAL AND CONTINUOUS

A lexicon labels words (`sexual`/`violent`); a rating scores them (vulgarity
0-1). Both are word-level annotations joined to the same movement rows, so both
belong here, but they aggregate differently and must not be silently mixed:

    categorical   group by label; js/departed/arrived/inherited per label
    continuous    mass-weighted sums, so a weighted mean and a delta-correlation
                  can be derived downstream WITHOUT re-querying 54M rows

A continuous field with a `cuts` argument becomes categorical by binning, and the
bin edges are then part of the instrument -- record them where the field is
declared, not here.
"""
import json
import os
import re

from . import ch

#: THE per-word JS term. One definition. `%s` is the table alias.
JS_TERM = """0.5 * (
    if(%(a)s.p_base    > 0, %(a)s.p_base    * log2(%(a)s.p_base    / ((%(a)s.p_base+%(a)s.p_aligned)/2)), 0) +
    if(%(a)s.p_aligned > 0, %(a)s.p_aligned * log2(%(a)s.p_aligned / ((%(a)s.p_base+%(a)s.p_aligned)/2)), 0)
)"""

_SAFE = re.compile(r"^[a-z0-9_]+$")


class WordField:
    """A word-level annotation, materialised as a ClickHouse table for joining.

    `name` becomes the table `{db}.wf_<name>` and must be [a-z0-9_]. `sha` is
    carried on every row: registration rule 4 in more than one experiment says a
    result computed against an unrecorded instrument version is not a result, and
    a sha that lives only in a python constant is not carried by the data.
    """

    def __init__(self, name, values, kind="categorical", sha="", source=""):
        if not _SAFE.match(name):
            raise ValueError(f"field name {name!r} must be [a-z0-9_]+")
        if kind not in ("categorical", "continuous"):
            raise ValueError(f"kind {kind!r}")
        self.name, self.values, self.kind = name, values, kind
        self.sha, self.source = sha, source

    # -- constructors ------------------------------------------------------
    @classmethod
    def from_lexicon(cls, name, path, key="category"):
        """A `results/lexicon.json` written by an instrument-build experiment."""
        import hashlib
        lex = json.load(open(path))
        vals = {w: d.get(key, "") for w, d in lex.items() if d.get(key, "") != ""}
        #: DERIVED FROM CONTENT, not read from a field. The lexicon rows carry no
        #: sha -- the builder wrote it to metrics.json -- so looking for one gave
        #: an empty string that would have compared unequal to every registered
        #: value and, had the check been `if sha and sha != expected`, would have
        #: passed silently instead. Recomputing here uses the builder's own
        #: definition, so the constant in a registration is checkable against the
        #: file rather than against a copy of itself.
        #: Always over `category`, whatever `key` is extracted: the sha names the
        #: LEXICON VERSION, so a register field and a category field drawn from
        #: the same file must report the same instrument.
        sha = hashlib.sha256(
            json.dumps({w: lex[w].get("category") for w in sorted(lex)},
                       sort_keys=True).encode()).hexdigest()[:16]
        return cls(name, vals, "categorical", sha=sha, source=os.path.basename(path))

    @classmethod
    def from_fields(cls, name, source, scale=None):
        """A source declared in `fields.py` -- rid, gi, usas, k_en, warriner, ...

        Delegates to fields.py rather than reading its files, so an absent source
        RAISES there (MissingSource) instead of returning a clean empty answer
        here. Absence and emptiness must not share a shape.
        """
        from . import fields
        vals, kind = fields.as_word_map(source, scale=scale)
        return cls(name, vals, kind, source=f"fields:{source}" + (f":{scale}" if scale else ""))

    @classmethod
    def from_dict(cls, name, values, kind="categorical", sha="", source="ad hoc"):
        return cls(name, values, kind, sha=sha, source=source)

    @classmethod
    def from_sets(cls, name, sets, sha="", source="sets"):
        """{setname: iterable_of_words} -> a field where A WORD MAY BE IN SEVERAL SETS.

        `from_dict` maps each word to one label, which cannot express
        `rape` being sexual content AND violent content. That is only sound
        where the sets are never contrasted with each other: in a difference,
        a shared word is double-counting; in two INDEPENDENT tests it is simply
        true. `removal_rates` requires it, and requires it for exactly that
        reason (see its registration, section 5).
        """
        pairs = [(w, setname) for setname, ws in sets.items() for w in ws]
        f = cls(name, {}, "categorical", sha=sha, source=source)
        f._pairs = pairs
        return f

    # -- materialise -------------------------------------------------------
    @property
    def table(self):
        return "wf_" + self.name

    def push(self):
        col = "String" if self.kind == "categorical" else "Float64"
        ch.execute(f"DROP TABLE IF EXISTS {{db}}.{self.table}")
        ch.execute(f"""CREATE TABLE {{db}}.{self.table} (
            word String, label {col}, sha LowCardinality(String),
            source LowCardinality(String)
        ) ENGINE = MergeTree ORDER BY word""")
        rows = getattr(self, "_pairs", None) or list(self.values.items())
        ch.insert(self.table, [{"word": w, "label": v, "sha": self.sha,
                                "source": self.source} for w, v in rows])
        return len(rows)

    def check_sha(self, expected):
        got = ch.scalar(f"SELECT any(sha) FROM {{db}}.{self.table}")
        if got != expected:
            raise SystemExit(f"{self.table} holds sha {got!r}, registered {expected!r}. "
                             "Re-push, or re-run/withdraw every citing result.")


def _panel_table(prompts):
    ch.execute("DROP TABLE IF EXISTS {db}.wf_panel")
    ch.execute("CREATE TABLE {db}.wf_panel (prompt String) ENGINE = MergeTree ORDER BY prompt")
    ch.insert("wf_panel", [{"prompt": p} for p in prompts])


def measure(pairs, field, prompts=None):
    """{(base, aligned, prompt, label): {...}} in ONE query over `movement`.

    Aggregation is server-side: `movement` is ~54M rows and pulling them to
    aggregate in python is how a 20-second query becomes a 20-minute one.

    Categorical -> js / departed / arrived / n_words per label.
    Continuous  -> the same, plus `w_sum` (label*|delta|) and `abs_delta`, so a
                   mass-weighted mean is `w_sum/abs_delta` without re-querying.
    """
    ms = "','".join(m.replace("'", "\\'") for pr in pairs for m in pr)
    if prompts is not None:
        _panel_table(prompts)
    where_p = ("AND m.prompt IN (SELECT prompt FROM {db}.wf_panel)"
               if prompts is not None else "")
    extra = ("" if field.kind == "categorical" else
             ", sum(l.label * abs(m.delta)) AS w_sum, sum(abs(m.delta)) AS abs_delta")
    group_label = "l.label" if field.kind == "categorical" else "''"
    q = f"""
        SELECT m.base AS base, m.aligned AS aligned, m.prompt AS prompt,
               {group_label} AS label,
               sum({JS_TERM % {'a': 'm'}}) AS js,
               sum(if(m.delta < 0, -m.delta, 0)) AS departed,
               sum(if(m.delta > 0,  m.delta, 0)) AS arrived,
               sum(m.p_base) AS inherited,
               count() AS n_words,
               groupUniqArray(m.word) AS words{extra}
        FROM {{db}}.movement m
        INNER JOIN {{db}}.{field.table} l ON l.word = m.word
        WHERE m.base IN ('{ms}') AND m.aligned IN ('{ms}') {where_p}
        GROUP BY base, aligned, prompt, label"""
    out = {}
    for r in ch.query(q):
        k = (r["base"], r["aligned"], r["prompt"], r["label"])
        out[k] = {kk: r[kk] for kk in r if kk not in ("base", "aligned", "prompt", "label")}
    return out


def conservation(pair, prompts=None, limit=200):
    """Per-word js terms vs `movement_cells.js_total - js_tail`. Different producer.

    Returns (n_prompts, worst_abs_diff). This is the check that the arithmetic
    here is the arithmetic the store already booked -- not this module agreeing
    with itself. Runs over ALL words, so it validates JS_TERM, not the join.
    """
    b, a = pair
    if prompts is not None:
        _panel_table(prompts)
    wp = "AND prompt IN (SELECT prompt FROM {db}.wf_panel)" if prompts is not None else ""
    rows = ch.query(f"""
        WITH mine AS (
            SELECT prompt, sum({JS_TERM % {'a': 'movement'}}) AS js
            FROM {{db}}.movement WHERE base = '{b}' AND aligned = '{a}' {wp}
            GROUP BY prompt)
        SELECT c.prompt AS prompt, mine.js AS mine, c.js_total - c.js_tail AS booked
        FROM {{db}}.movement_cells c INNER JOIN mine ON mine.prompt = c.prompt
        WHERE c.base = '{b}' AND c.aligned = '{a}' LIMIT {limit}""")
    if not rows:
        return None
    return len(rows), max(abs(r["mine"] - r["booked"]) for r in rows)


def share(cells, chains, labels, metric="js", min_words=0):
    """Per-chain arm ratio for each label, on the prompts BOTH arms hold.

    Returns rows with `share_<label>`, plus the raw per-arm means and the L3-style
    departed/arrived so a fall-vs-rise reading is available without re-querying.
    A label whose arms share no prompt yields "" -- never a silent 0, and never a
    ratio computed across two different prompt sets.
    """
    import statistics
    out = []
    for c in chains:
        row = {"base": c["base"], "sft": c["sft"], "pref": c["pref"],
               "pref_op": c.get("pref_op", "")}
        ok = True
        for lab in labels:
            A = {p: v for (b, al, p, k), v in cells.items()
                 if b == c["base"] and al == c["sft"] and k == lab}
            B = {p: v for (b, al, p, k), v in cells.items()
                 if b == c["base"] and al == c["pref"] and k == lab}
            shared = set(A) & set(B)
            if not shared:
                ok = False
                break
            am = statistics.mean(A[p][metric] for p in shared)
            bm = statistics.mean(B[p][metric] for p in shared)
            #: DISTINCT words for the CHAIN, not the per-prompt mean. A twp cell
            #: holds ~1 sexual and ~4 violent lexicon words, so a per-prompt
            #: threshold of any useful size is unsatisfiable by construction --
            #: a criterion that can never be met is a bug wearing a power
            #: criterion's clothes. `n_words` counts distinct words seen across
            #: the panel; `n_prompts` is the denominator and carries no threshold.
            row[f"n_prompts_{lab}"] = len(shared)
            row[f"n_words_{lab}"] = len({w for p in shared
                                         for w in A[p].get("words", ()) })
            row[f"{metric}_sft_{lab}"] = round(am, 8)
            row[f"{metric}_pref_{lab}"] = round(bm, 8)
            row[f"share_{lab}"] = (round(am / bm, 6)
                                   if bm and row[f"n_words_{lab}"] >= min_words else "")
            for tag, S in (("sft", A), ("pref", B)):
                for m in ("departed", "arrived"):
                    row[f"{m}_{tag}_{lab}"] = round(statistics.mean(S[p][m] for p in shared), 8)
        if ok:
            out.append(row)
    return out


def paired_test(rows, a, b, key="share"):
    """Chain-level AND base-level sign tests on (a - b), base level decisive.

    Both are returned because reporting only one is how `sft_share` came to
    decide H3 on a number its producer never printed. Ties are DROPPED, never
    split -- the campaign rule.
    """
    import collections
    import statistics
    from math import comb

    def sign_p(pos, n):
        return min(1.0, 2 * sum(comb(n, k) for k in range(pos, n + 1)) / 2 ** n) if n else 1.0

    pairs = [(r["base"], r[f"{key}_{a}"] - r[f"{key}_{b}"]) for r in rows
             if r.get(f"{key}_{a}") != "" and r.get(f"{key}_{b}") != ""]
    if not pairs:
        return None
    d = [x for _, x in pairs if x != 0]
    per_base = collections.defaultdict(list)
    for bb, x in pairs:
        per_base[bb].append(x)
    db = [x for x in (statistics.mean(v) for v in per_base.values()) if x != 0]
    return {
        "n_chains": len(pairs), "n_bases": len(per_base),
        "chain_mean": statistics.mean(d) if d else 0.0,
        "chain_pos": sum(1 for x in d if x > 0), "chain_n": len(d),
        "chain_p": sign_p(sum(1 for x in d if x > 0), len(d)),
        "base_mean": statistics.mean(db) if db else 0.0,
        "base_pos": sum(1 for x in db if x > 0), "base_n": len(db),
        "base_p": sign_p(sum(1 for x in db if x > 0), len(db)),
        "ties_dropped": len(pairs) - len(d),
    }


def paired_stats(diffs, seed=20260816, n_boot=20000):
    """Full description of a set of paired differences, not just a p-value.

    A sign test at n=16 needs 13/16 to reach p<0.05, so it cannot distinguish
    "no effect" from "an effect this instrument cannot see". Reporting p alone
    is how a null gets called a finding. **A null is quotable only as a bound**,
    so the interval is returned alongside, and the magnitude-using tests too --
    withholding a more sensitive reading of a null is its own dishonesty.

    `sign_p` is the registered test wherever a registration says so; `t_p` and
    `wilcoxon_p` are supplementary and must be labelled as such at the call site.
    """
    import random
    import statistics
    from math import comb

    d = [x for x in diffs if x != 0]
    n = len(d)
    if n < 2:
        return None
    pos = sum(1 for x in d if x > 0)
    sign_p = min(1.0, 2 * sum(comb(n, k) for k in range(pos, n + 1)) / 2 ** n)
    rng = random.Random(seed)
    bs = sorted(statistics.mean(rng.choices(d, k=n)) for _ in range(n_boot))
    out = {"n": n, "ties_dropped": len(diffs) - n, "pos": pos,
           "mean": statistics.mean(d), "sd": statistics.stdev(d),
           "sign_p": sign_p,
           "ci_lo": bs[int(0.025 * n_boot)], "ci_hi": bs[int(0.975 * n_boot)]}
    try:
        from scipy import stats
        out["t_p"] = float(stats.ttest_1samp(d, 0).pvalue)
        out["wilcoxon_p"] = float(stats.wilcoxon(d).pvalue)
    except Exception:                                    # noqa: BLE001
        out["t_p"] = out["wilcoxon_p"] = None
    return out


def sign_mde(diffs, seed=20260816, power=0.80, n_sim=2000, grid=None):
    """Smallest uniform shift the SIGN TEST detects at `power`, by simulation.

    Registered as a test, this is what the test can see. Quoting a null without
    it leaves "we found nothing" and "we could not have found anything"
    indistinguishable, which is the failure this function exists to prevent.
    """
    import random
    import statistics
    from math import comb

    d = [x for x in diffs if x != 0]
    n = len(d)
    if n < 2:
        return None
    rng = random.Random(seed)

    def sp(pos, k):
        return min(1.0, 2 * sum(comb(k, i) for i in range(pos, k + 1)) / 2 ** k)

    for shift in (grid or [x / 100 for x in range(0, 101, 5)]):
        hits = 0
        for _ in range(n_sim):
            s = [x + shift for x in rng.choices(d, k=n)]
            s = [x for x in s if x != 0]
            if s and sp(sum(1 for x in s if x > 0), len(s)) < 0.05:
                hits += 1
        if hits / n_sim >= power:
            return shift
    return None


def matched_nonmovers(base, aligned, words, tau=0.005, tol=1.0, prompts=None):
    """For each (prompt, word), the UNMOVED word the aligned model finds equally improbable.

    Carried from the archive's `Movement.matched_nonmover`, which is the only
    part of `cell.py`/`step.py` (471 lines) that was a MEASUREMENT rather than a
    WHERE clause.

    **WHY IT IS SHARPER THAN A FREQUENCY-MATCHED CONTROL.** A faller/riser
    contrast varies two things at once: the word was DEMOTED, and it is
    IMPROBABLE TO THE ALIGNED MODEL. `removal_rates` controls the first by
    matching on corpus frequency ACROSS words; this controls the second by
    matching on `p_aligned` WITHIN the same cell. Different confounds, and the
    original spec named this one before its run: "a word matched on
    improbability-under-aligned but NOT demoted by alignment".

    `basis` is the POST arm deliberately. Matching on `p_base` controls what the
    BASE model expected, which is a different question.

    `tol` is |log2(p_candidate / p_target)|, so tol=1.0 is a factor of two.
    A non-mover is |delta| <= tau. Returns the CLOSEST qualifying word, not the
    first -- `argMin` over the log-ratio distance.

    In v3 this is a query, not a class: `movement` already carries p_base,
    p_aligned, delta and cls per (base, aligned, prompt, word).
    """
    ws = "','".join(w.replace("'", "\\'") for w in words)
    wp = ("AND m.prompt IN (SELECT prompt FROM {db}.wf_panel)"
          if prompts is not None else "")
    if prompts is not None:
        _panel_table(prompts)
    q = """
        WITH tgt AS (
            SELECT prompt, word, p_aligned FROM {db}.movement m
            WHERE base = '%s' AND aligned = '%s' AND word IN ('%s')
              AND p_aligned > 0 %s),
        still AS (
            SELECT prompt, word, p_aligned FROM {db}.movement m
            WHERE base = '%s' AND aligned = '%s' AND abs(delta) <= %g
              AND p_aligned > 0 %s)
        SELECT t.prompt AS prompt, t.word AS target, t.p_aligned AS p_target,
               argMin(s.word, abs(log2(s.p_aligned / t.p_aligned))) AS control,
               min(abs(log2(s.p_aligned / t.p_aligned))) AS log2_gap
        FROM tgt t INNER JOIN still s ON s.prompt = t.prompt
        WHERE s.word != t.word AND abs(log2(s.p_aligned / t.p_aligned)) <= %g
        GROUP BY prompt, target, p_target""" % (
        base.replace("'", "\\'"), aligned.replace("'", "\\'"), ws, wp,
        base.replace("'", "\\'"), aligned.replace("'", "\\'"), tau, wp, tol)
    return ch.query(q)
