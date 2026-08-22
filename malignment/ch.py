#!/usr/bin/env python
"""One way to ask ClickHouse a question.

    from malign_logits import ch

    ch.query("SELECT model, count() AS n FROM {db}.twp_words GROUP BY model")
    ch.scalar("SELECT count() FROM {db}.twp_words")
    ch.df("SELECT * FROM {db}.gen_scores LIMIT 100")
    ch.execute("CREATE TABLE ...")
    ch.insert("vf_manifest_tmp", rows)

WHY THIS EXISTS, IN EVIDENCE RATHER THAN IN PREFERENCE. On 2026-08-14 a survey
found 85 files touching ClickHouse and 69 of them shelling out themselves, plus
TWO private `_q` helpers inside this library that had diverged from each other.
The duplication is the least of it. Every hand-rolled reader repeats the same
three defects, and all three are defects this campaign has already paid for:

  1. **SILENT ROW DROPS.** `ch_read._q`'s consumers do `if len(f) == 4:` and
     `gens._q` does `if len(f) != len(head): continue`. A row that does not
     split into the expected shape is discarded with no count, no file and no
     cause. That is the receiptless disposition booked at [6127] -- and the
     accounting identity that would have caught it cannot, because a dropped
     row enters neither side of it.

  2. **TSV ESCAPING BY HAND.** `ch_read._unesc` exists because omitting it made
     a reconciler report 88 of 250 cells as disagreeing (`didn\\'t` against
     `didn't`) on a table holding zero backslashes. `gens._q` takes an
     `unescape_cols` argument, so the guard is OPT-IN and any string column
     nobody named keeps its escaping. And at [6065] a `TSVRaw` export -- which
     does not escape newlines at all, on prompts that contain them -- returned
     1,621,740 lines against a true 964,679, manufacturing a divergence between
     two stores that did not exist.

  3. **THE FORMAT DECIDES THE POPULATION.** Which is (2) stated generally: a
     serialisation format is a population definition, and a reader that splits
     on a delimiter is asserting that the delimiter does not occur in the data.

**JSONEachRow DISSOLVES ALL THREE.** There is no delimiter to collide with, no
escaping convention to reverse, and a row that will not parse raises instead of
vanishing. It is also already what 61 of the 74 external call sites use, so this
is the majority convention rather than a new one.

**WHAT THIS MODULE DOES NOT DO.** It does not open a connection, pool anything,
or add a dependency: it shells out to the same binary every caller already
shells out to. The value is not the transport, it is that the transport is in
one place with the three lessons above already applied.

**`{db}` IN A QUERY IS SUBSTITUTED** with the configured database, so callers
stop writing `%s.twp_words % DB` and stop getting it wrong when DB is not the
default.
"""
import json
import os
import re
import subprocess

CH = os.environ.get("MALIGN_CH_BIN", "/opt/homebrew/bin/clickhouse")
#: THE NEW DATABASE. `malign_logits` belongs to the archive repo and is still
#: read by it. This machine also runs `lltk` at 409 GiB, `abstraction` and
#: `llmtasks` on the same daemon, so a statement naming one of them reaches it.
#:
#: **THIS COMMENT DESCRIBED A `_guard` THAT DID NOT EXIST.** dario found it on
#: 2026-08-16 while building a server that sends SQL to this daemon on behalf of
#: a browser: `grep _guard malignment/*.py` returned exactly one line -- this
#: comment. The wording is what made it invisible. It did not say "we should
#: guard"; it stated the guard existed AND explained a design choice ("refuses
#: ... rather than warning about it"), and a tag that argues for its own
#: implementation reads as settled. Nobody tests a decision.
#:
#: AND THE DESIGN IT CLAIMED IS NOT IMPLEMENTABLE AS WRITTEN. "Refuses any
#: statement not naming the target database" would refuse `inventory()`, which
#: must read `system.tables`. So the guard below enforces the enforceable
#: version: **no statement may name a database that is neither ours nor
#: introspection.**
DB = os.environ.get("MALIGNMENT_CH_DB", "malignment")

#: Introspection databases a statement may legitimately name besides ours.
ALLOWED_DBS = frozenset(("system", "information_schema", "INFORMATION_SCHEMA"))


def _databases():
    """Every database on this daemon. Cached; bypasses the guard by construction.

    **THE GUARD CHECKS AGAINST REAL DATABASE NAMES, NOT A REGEX FOR `x.y`.**
    A pattern cannot tell `lltk.corpus` from `t.model` where `t` is a table
    alias, and a guard that rejects ordinary aliased SQL gets switched off
    within a day. Asking the server which names are actually databases makes
    the test exact: an alias is not a database.
    """
    global _DBS
    if _DBS is None:
        r = subprocess.run([CH, "client", "--query", "SHOW DATABASES"],
                           capture_output=True, text=True)
        _DBS = frozenset(x.strip() for x in r.stdout.splitlines() if x.strip())
    return _DBS


_DBS = None
_QUALIFIER = re.compile(r"(?<![\w.])([A-Za-z_][A-Za-z0-9_]*)\s*\.", re.M)


def _guard(sql):
    """Raise if `sql` names a database other than ours or an introspection one.

    Applies to every path out of this module, `execute` and `insert` included --
    a DROP is exactly the statement you want refused against a 409 GiB
    neighbour.
    """
    named = {m.group(1) for m in _QUALIFIER.finditer(sql)}
    foreign = sorted((named & _databases()) - {DB} - ALLOWED_DBS)
    if foreign:
        raise ClickHouseError(
            "REFUSED: statement names database(s) %s. This module talks to %r "
            "only. `lltk` alone is 409 GiB on this daemon; if you mean to read "
            "another database, do it deliberately and not through malignment.ch."
            % (", ".join(foreign), DB), sql)
    return sql

#: A FORMAT CLAUSE IS A TRAILING KEYWORD, NOT A SUBSTRING. The first version
#: of this module tested `"FORMAT" not in sql.upper()`, which matches
#: `formatReadableSize(...)` -- so a perfectly ordinary system.tables query
#: silently got TSV back and the JSON parse failed on line 1. That is the same
#: name-for-a-relation defect this module was written to retire, committed
#: inside it within the hour. Match the clause where it can actually appear.
_HAS_FORMAT = re.compile(r"\bFORMAT\s+[A-Za-z0-9_]+\s*;?\s*$", re.I)


def _with_format(sql, fmt):
    if _HAS_FORMAT.search(sql):
        return sql
    return sql.rstrip().rstrip(";") + " FORMAT " + fmt


#: A query that returns more than this many bytes is almost certainly a mistake
#: of the "SELECT * FROM a 350M-row table" kind. Raise rather than fill memory;
#: pass `limit_bytes=None` to mean it.
DEFAULT_LIMIT_BYTES = 2_000_000_000


class ClickHouseError(RuntimeError):
    """A failed query, carrying the SQL that failed.

    The SQL is included because the most common cause of a ClickHouse error in
    this repo is a malformed interpolation, and an error message without the
    statement sends the reader to the wrong line.
    """

    def __init__(self, stderr, sql):
        self.sql = sql
        super().__init__("%s\n--- SQL ---\n%s" % (stderr.strip()[:400],
                                                  sql.strip()[:800]))


def _run(sql, stdin=None, limit_bytes=DEFAULT_LIMIT_BYTES):
    sql = _guard(sql.replace("{db}", DB))
    #: `--database` so an UNQUALIFIED name resolves to ours rather than to
    #: `default`. Without it the guard passes `SELECT * FROM movement` -- which
    #: names no database and so cannot be foreign -- and the daemon then looks
    #: it up somewhere we did not choose.
    r = subprocess.run([CH, "client", "--database", DB, "--query", sql],
                       input=stdin, capture_output=True, text=True)
    if r.returncode:
        raise ClickHouseError(r.stderr, sql)
    if limit_bytes is not None and len(r.stdout) > limit_bytes:
        raise ClickHouseError(
            "result exceeded limit_bytes=%d (got %d). Narrow the query or "
            "pass limit_bytes=None deliberately." % (limit_bytes, len(r.stdout)),
            sql)
    return r.stdout


def raw(sql, **kw):
    """Stdout, unparsed. The escape hatch for a FORMAT this module does not wrap.

    Prefer `query`. If you reach for this with `FORMAT TSV` and then split on
    tabs, you have re-created defect (2) in the module docstring.
    """
    return _run(sql, **kw)


def query(sql, **kw):
    """Rows as dicts, via JSONEachRow. Types survive; escaping is not your problem.

    A line that will not parse RAISES, naming the line number and the line. It
    is not skipped, because a reader that skips is a disposition with no
    receipt and this module exists partly to stop writing those.
    """
    sql = _with_format(sql, "JSONEachRow")
    out = _run(sql, **kw)
    rows = []
    #: `split("\n")`, NOT `splitlines()`. JSONEachRow puts one row per LF, but
    #: `splitlines()` also breaks on U+0085, U+2028, U+2029, \v and \f -- and
    #: JSON requires escaping none of them, since all sit at or above 0x20 in
    #: the ones that matter here. ClickHouse escapes U+2028 and U+2029 (the
    #: JS-compat convention) and leaves **U+0085 (NEL) raw**, so a row carrying
    #: a NEL was cut in half and the leading fragment raised as an unterminated
    #: string. MEASURED on malign_logits gen_sequences (the passage corpora,
    #: 1,523,015 rows): 100 rows carry U+0085, and only those broke -- the 290
    #: U+2028 and 45 U+2029 rows parse either way, which is why testing on
    #: U+2028 alone clears this fix falsely.
    for i, line in enumerate(out.split("\n"), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ClickHouseError(
                "unparseable JSONEachRow at line %d: %s\nline: %.200r"
                % (i, e, line), sql)
    return rows


def scalar(sql, default=None, **kw):
    """The single value of a one-row, one-column query, or `default` if no rows.

    Raises if the query returns more than one row or more than one column,
    because a caller asking for a scalar and silently getting the first of
    several is the shape of a wrong number that never looks wrong.
    """
    rows = query(sql, **kw)
    if not rows:
        return default
    if len(rows) > 1:
        raise ClickHouseError("scalar() got %d rows" % len(rows), sql)
    vals = list(rows[0].values())
    if len(vals) != 1:
        raise ClickHouseError("scalar() got %d columns: %s"
                              % (len(vals), list(rows[0])), sql)
    return vals[0]


def _run_bytes(sql, limit_bytes=DEFAULT_LIMIT_BYTES):
    #: **THE SECOND PATH OUT OF THIS MODULE.** `parquet()` and `df()` come
    #: through here, not `_run`, so guarding only `_run` would have left a
    #: complete bypass -- the same shape as the archive's second loader.
    sql = _guard(sql.replace("{db}", DB))
    r = subprocess.run([CH, "client", "--database", DB, "--query", sql],
                       capture_output=True)
    if r.returncode:
        raise ClickHouseError(r.stderr.decode("utf-8", "replace"), sql)
    if limit_bytes is not None and len(r.stdout) > limit_bytes:
        raise ClickHouseError("result exceeded limit_bytes=%d (got %d)"
                              % (limit_bytes, len(r.stdout)), sql)
    return r.stdout


def parquet(sql, **kw):
    """A DataFrame via `FORMAT Parquet`. Binary transport, for bulk reads.

    Prefer this over `df` when the result is large: Parquet carries types and
    compresses, where JSONEachRow spends a line of text per row. Added
    2026-08-14 because `verse_capacity` needed it and the first version of
    this module could not express it -- `_run` decodes as text, which
    corrupts a binary payload silently rather than failing.
    """
    import io as _io
    import pandas as pd
    sql = _with_format(sql, "Parquet")
    return pd.read_parquet(_io.BytesIO(_run_bytes(sql, **kw)))


def df(sql, **kw):
    """A pandas DataFrame. Empty result gives an empty frame, not an exception."""
    import pandas as pd
    return pd.DataFrame(query(sql, **kw))


def execute(sql, **kw):
    """A statement expected to return nothing: DDL, INSERT ... SELECT, DROP.

    Returns stdout, which is normally empty; a non-empty result is handed back
    rather than discarded, so a caller who used `execute` for a SELECT sees it.
    """
    return _run(sql, **kw)


def insert(table, rows, **kw):
    """Insert dicts into `table` as JSONEachRow. Returns the count inserted.

    Empty input inserts nothing and returns 0 rather than sending a statement
    with no body, which ClickHouse accepts and which reads in a log as a
    successful insert of nothing.
    """
    rows = list(rows)
    if not rows:
        return 0
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    tbl = table if "." in table else "{db}." + table
    _run("INSERT INTO %s FORMAT JSONEachRow" % tbl, stdin=body, **kw)
    return len(rows)


def inventory():
    """Every table in the database with its engine, key, rows and size.

        python -c "from malign_logits import ch; print(ch.inventory_md())"

    Exists because `docs/clickhouse-migration.md` carried a hand-written row
    table that had drifted by up to 2.9x -- it said `twp_words` held 32.67M
    against an actual 95,180,535, and `twp_residual` 283.4k against 1,019,521.
    A transcribed count is stale the day after it is written; a generated one
    is stale only until someone runs the command.
    """
    return query("""
        SELECT name, engine, sorting_key, total_rows AS rows,
               total_bytes AS bytes, formatReadableSize(total_bytes) AS size
        FROM system.tables WHERE database='{db}' ORDER BY total_bytes DESC""")


def inventory_md():
    """`inventory()` as a Markdown table, for pasting into a doc."""
    rows = inventory()
    out = ["| table | engine | rows | size | ORDER BY |",
           "|---|---|---|---|---|"]
    for r in rows:
        out.append("| `%s` | %s | %s | %s | `%s` |"
                   % (r["name"], r["engine"].replace("MergeTree", "MT"),
                      "{:,}".format(r["rows"] or 0), r["size"],
                      r["sorting_key"] or ""))
    return "\n".join(out)


def approx(col, value, tol=1e-9):
    """A float-column equality predicate that actually matches.

        ch.query("SELECT ... WHERE " + ch.approx("theta", 0.001))

    **NEVER WRITE `theta = 0.001` AGAINST A Float32 COLUMN.** 0.001 stored as
    Float32 round-trips as 0.0010000000474974513, so the literal comparison
    matches NOTHING -- measured 2026-08-14 across the whole store:

        twp_words        theta = 0.001 -> 0 rows      abs(...) < 1e-9 -> 95,180,535
        movement         theta = 0.001 -> 0 rows      abs(...) < 1e-9 -> 77,625,652
        movement_cells   theta = 0.001 -> 0 rows      abs(...) < 1e-9 ->    568,977

    **The failure is an EMPTY RESULT, not an error.** A prefetch returns zero
    prompts for a model plainly in the table and the caller reads that as "not
    scored" rather than as a broken predicate.

    This was independently discovered and written down at least twice -- in
    `ch_read.prefetch` and in `M02/contradiction_null.py` -- each time as a
    comment beside the one query its author was fixing. Encoded here so the
    next person gets it without having to have been told.
    """
    return "abs(%s - %r) < %g" % (col, value, tol)


def exists(table):
    """Whether a table exists, by name, with or without a database prefix."""
    tbl = table if "." in table else "%s.%s" % (DB, table)
    d, t = tbl.split(".", 1)
    return bool(scalar("SELECT count() FROM system.tables "
                       "WHERE database='%s' AND name='%s'" % (d, t)))


def columns(table):
    """{name: type} for a table, in position order."""
    tbl = table if "." in table else "%s.%s" % (DB, table)
    d, t = tbl.split(".", 1)
    return {r["name"]: r["type"] for r in query(
        "SELECT name, type FROM system.columns WHERE database='%s' "
        "AND table='%s' ORDER BY position" % (d, t))}
