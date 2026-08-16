#!/usr/bin/env python
"""The app's server. It READS; it does not compute.

    python -m malignment.serve                 # port 8431
    python -m malignment.serve --port 9000
    python -m malignment.serve --no-slot       # refuse to load weights at all

## THE ONE RULE, AND IT IS THE REPO'S RULE WITH A PORT ON IT

**Every number this server returns comes from ClickHouse or from a committed
`experiments/*/results/` file.** Nothing is derived here. Not a mean, not a
share, not a re-filter of a population.

That is not fastidiousness, it is the failure this repository was built as a
response to. The archive got **six different answers to "how many
representative pairs" in one afternoon** because the question had six call
sites. An app is the most seductive seventh: it is interactive, so a small
convenience computation feels like display logic rather than analysis, and it
is the copy nobody greps because it is not in `experiments/`. A rollup computed
here would be a number with no producer, no population receipt and no registered
grain -- the exact object `RESULTS.md` §3 says is *not yet a result*.

So the server's job is transport and the experiment's job is arithmetic. If a
view needs a number that does not exist, the answer is a producer in
`experiments/`, not a SELECT in this file.

**THE ONE EXCEPTION IS `/slot`, AND IT IS NOT AN EXCEPTION TO THE RULE.** It runs
the twp instrument against a resident model, which is a MEASUREMENT, not a
rollup of one. It writes nothing, books nothing, and its output is an authoring
aid. It says so on the panel.

## WHY NOTHING A CLIENT SENDS REACHES SQL

`ch.query` builds a statement by string interpolation and hands it to the
`clickhouse` binary with `--query`. There are no bound parameters anywhere in
this repo's data path. A server that interpolated a query string from a URL
would therefore be handing arbitrary SQL to a client -- against a store that
also holds `lltk` at 409 GiB on the same daemon.

**So there is no query endpoint, and no parameter is ever interpolated.** Every
route names a fixed query. The two parameters that vary -- `kind` for a
population and `id`/`grain` for a result file -- are validated by MEMBERSHIP in a
set this process derived itself (`roster.POPULATIONS`, and the manifest walked
off disk), never by pattern. Membership is what makes `../../etc/passwd` and
`'; DROP` uninteresting: they are simply not in the set.

## THE SLOT LOCK IS NOT ABOUT LOAD, IT IS ABOUT `_BATCH`

`twp.py` says so itself, under KNOWN DEFECT CARRIED OVER DELIBERATELY: `_BATCH`
is module-level mutable state that `next_dist` reads and writes for OOM backoff,
*"correct for a single-process runner, wrong for a library two callers might
drive at once."*

**A threaded HTTP server is exactly two callers.** Two concurrent expansions
share one batch ceiling, so one request's OOM backoff silently rescales the
other's -- and the result is not an error, it is a slower run and a different
batching path through the same rule. `_SLOT_LOCK` serialises expansion for that
reason and not for the GPU's.

`ThreadingHTTPServer` is still right: the store routes are I/O-bound on a
subprocess and must not queue behind an 8-second model load.

## WHY THE ROW CAP IS IN THE PAYLOAD AND NOT ONLY IN THE QUERY

`removal_rates/results/cells.csv` is 273,918 rows. Something must cap it. But a
cap the client cannot see is the *windowed view beside an unwindowed statistic*
defect: the table shows 5,000 rows, the header says what the file holds, and a
reader reasons from whichever is nearer. So every result payload carries
`n_rows_total`, `n_rows_returned` and `capped`, and the UI is required to say so
on the panel. **A count is a claim about what was DRAWN, not about what was
loaded.**
"""
import argparse
import collections
import csv
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERIMENTS = os.path.join(ROOT, "experiments")
UI_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_dist")

#: Rows returned for one result file unless the client asks for fewer. Chosen so
#: the largest committed grain (`removal_rates/results/cells.csv`, 273,918 data
#: rows) is capped rather than streamed into a browser tab.
#:
#: **273,918 AND NOT 273,919, WHICH IS WHAT `wc -l` SAYS.** The file has a header,
#: so the line count is one more than the row count. Written here because the
#: first draft of this comment quoted the `wc` figure beside a payload that
#: returns the other -- a caption disagreeing with the number under it by one,
#: which is the size of error that gets read as a rounding convention.
DEFAULT_ROW_CAP = 2000
MAX_ROW_CAP = 50000

_SLOT_LOCK = threading.Lock()
#: {model_id: runners.Loaded}, ORDERED, least-recently-used first.
#:
#: **BOUNDED, BECAUSE THE FIRST VERSION WAS NOT** (RH, 2026-08-16: *"can we not
#: load models unless necessary"*). Loading was already lazy -- nothing loads at
#: startup, and only `/slot` ever loads -- but nothing ever UNLOADED, so every
#: distinct model a caller named was held for the life of the process. An
#: afternoon of testing left four resident, including SmolLM3-3B and OLMo-2-1B,
#: none of which any later request wanted.
#:
#: That is worse in a server than in a runner. A runner processes one checkpoint
#: and exits; this process is long-lived and its memory is whatever the union of
#: everything anyone has ever asked for happens to be.
_SLOT_MODELS = collections.OrderedDict()
#: TWO BY DEFAULT because the pooled query is base + its SFT, which is the shape
#: `/slot` exists for -- so the common case never evicts, and the uncommon one
#: pays a reload rather than the machine paying for it forever.
_SLOT_MAX = int(os.environ.get("MALIGNMENT_SLOT_MAX", 2))
_ALLOW_SLOT = True


def _evict_to(n):
    """Drop least-recently-used entries until at most `n` remain.

    **CALLED BEFORE A LOAD, NEVER AFTER.** `twp.free`'s docstring is explicit
    about why: evicting after would hold the outgoing model while the incoming
    one allocates, making the peak two models rather than one. That is the exact
    defect behind the 2026-07-30 32B OOM booked as *"32B at fp16 is marginal on
    80 GB"* -- a single 32B is 64 GB and fits; two at once do not.

    **AND THE REFERENCES ARE DROPPED HERE, NOT PASSED TO `free()`.** `free(*objs)`
    accepts arguments and cannot use them: `del o` inside it unbinds the local
    parameter while the caller still holds the object. `popitem` dropping the
    dict's reference is what actually releases it; `free()` then collects the
    cycles HF modules hold and empties the allocator.

    Caller must hold `_SLOT_LOCK`.
    """
    from . import twp
    dropped = []
    while len(_SLOT_MODELS) > max(0, n):
        mid, _ld = _SLOT_MODELS.popitem(last=False)      # least recent first
        dropped.append(mid)
    if dropped:
        #: No arguments. See above.
        twp.free()
        print("  slot: evicted %s (cap %d)" % (", ".join(dropped), _SLOT_MAX),
              flush=True)
    return dropped


# ---------------------------------------------------------------------------
# the experiment manifest: walked off disk, because the disk is the declaration
# ---------------------------------------------------------------------------

def _walk_experiments():
    """{id: {...}} for every QUESTION directory under `experiments/`.

    **A QUESTION is a directory holding `run.py` or `registration.md`; a SUBJECT
    is one that holds neither and has question children.** That is
    `experiments/README.md`'s own rule -- *"Only README.md and run.py are
    required"*, and *"a second level only when a subject has two questions, and
    the subject holds nothing"* -- read off the filesystem rather than restated.

    `register_shift` is why the test is not simply `run.py`: it is a registered
    hypothesis set with a frozen registration and no producer yet. A walk that
    demanded `run.py` would report the repo as having three questions when it has
    four, and the missing one is the only one whose status is *not run*. **A
    detector keyed on the artifact of completion cannot see incomplete work**,
    which is the state most worth showing.
    """
    out = {}
    if not os.path.isdir(EXPERIMENTS):
        return out
    for dirpath, dirnames, filenames in os.walk(EXPERIMENTS):
        dirnames[:] = [d for d in dirnames
                       if d not in ("__pycache__", "results", "figures",
                                    "workflows", "sandbox")]
        rel = os.path.relpath(dirpath, EXPERIMENTS)
        if rel == ".":
            continue
        fs = set(filenames)
        if not ({"run.py", "registration.md"} & fs):
            continue
        results = []
        rdir = os.path.join(dirpath, "results")
        if os.path.isdir(rdir):
            for name in sorted(os.listdir(rdir)):
                p = os.path.join(rdir, name)
                if not os.path.isfile(p):
                    continue
                results.append({"grain": name, "bytes": os.path.getsize(p),
                                "kind": os.path.splitext(name)[1].lstrip(".")})
        figs = []
        fdir = os.path.join(dirpath, "figures")
        if os.path.isdir(fdir):
            figs = sorted(f for f in os.listdir(fdir)
                          if os.path.isfile(os.path.join(fdir, f)))
        out[rel.replace(os.sep, "/")] = {
            "id": rel.replace(os.sep, "/"),
            "name": os.path.basename(dirpath),
            "subject": (os.path.dirname(rel).replace(os.sep, "/") or None),
            #: THE PRESENCE OF EACH REQUIRED FILE, NAMED. `experiments/README.md`
            #: makes `run.py` required and `registration.md` conditional, so a
            #: question missing one is a fact about the repo the index should
            #: show rather than hide behind a uniform card.
            "has": {k: (k in fs) for k in
                    ("README.md", "registration.md", "run.py", "analyse.py",
                     "population.json", "plot.py")},
            "results": results,
            "figures": figs,
            "_dir": dirpath,
        }
    return out


def _manifest():
    """Fresh on every call, deliberately.

    An experiment directory changes while the app is open -- that is the normal
    case here, since the app is read beside the work. A cached manifest would
    show a producer's new grain only after a restart, and the failure would look
    like the producer not having written it.
    """
    return _walk_experiments()


def _read_text(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _read_csv(path, cap):
    """`{columns, rows, n_rows_total, n_rows_returned, capped}` -- strings, verbatim.

    **NOT pandas, and the values are not coerced.** A result file is the record;
    a viewer that parses `0.0894` into a float and renders `0.0894000000000001`,
    or turns an empty cell into `NaN`, is showing something the file does not
    say. The one number this function invents is a row count, which it labels.

    The total is counted by reading the whole file even when the cap truncates,
    because a total the server guessed from the cap would be the same defect the
    payload exists to prevent.
    """
    rows, total = [], 0
    with open(path, newline="", encoding="utf-8") as fh:
        r = csv.reader(fh)
        try:
            columns = next(r)
        except StopIteration:
            return {"columns": [], "rows": [], "n_rows_total": 0,
                    "n_rows_returned": 0, "capped": False}
        for rec in r:
            total += 1
            if len(rows) < cap:
                rows.append(rec)
    return {"columns": columns, "rows": rows, "n_rows_total": total,
            "n_rows_returned": len(rows), "capped": total > len(rows)}


# ---------------------------------------------------------------------------
# the store: named queries only
# ---------------------------------------------------------------------------

def _store_inventory():
    from . import ch
    return {"db": ch.DB, "tables": ch.inventory()}


def _roster_summary():
    """The populations, the endpoints, the chains and the paths, in one payload.

    **`unresolved` IS RETURNED EVEN WHEN EMPTY.** `roster.endpoints()` hands back
    lineages it refused to choose for, and `docs/HOWTO.md` says plainly: *"a
    caller that ignores it is choosing by accident."* An app that dropped the key
    when it was empty would train its reader to stop looking for it on the day it
    is not.
    """
    from . import roster
    endpoints, unresolved = roster.endpoints()
    pops = {}
    for kind in roster.POPULATIONS:
        try:
            pops[kind] = len(roster.population(kind))
        except Exception as e:
            #: NAMED, not dropped. A population that raises is a roster defect and
            #: the app is a reasonable place to notice it; a missing key reads as
            #: a population that does not exist.
            pops[kind] = {"error": "%s: %s" % (type(e).__name__, e)}
    paths = roster.paths()
    return {
        "populations": pops,
        "endpoints": [{"base": b, "endpoint": e} for b, e in sorted(endpoints.items())],
        "unresolved": {k: v for k, v in unresolved.items()},
        "chains": roster.chains(),
        "paths": paths,
        #: The distribution `docs/HOWTO.md` insists on: 33 one-step, 12 two, 5
        #: three. A single "50 lineages" hides that a 1-step path means ONE
        #: RELEASED RUNG and never one training stage.
        "path_steps": _tally(p["n_steps"] for p in paths),
    }


def _tally(it):
    out = {}
    for v in it:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items()))


def _roster_population(kind):
    from . import roster
    #: MEMBERSHIP, not a pattern. See the module docstring.
    if kind not in roster.POPULATIONS:
        raise KeyError("unknown population %r; declared: %s"
                       % (kind, ", ".join(roster.POPULATIONS)))
    members = sorted(roster.population(kind))
    return {"kind": kind, "n": len(members), "members": members}


# ---------------------------------------------------------------------------
# slot: the one route that measures
# ---------------------------------------------------------------------------

def _slot(prompt, model_ids, k):
    """Pooled word probabilities at the blank, via `twp.expand`.

    **POOLED ACROSS THE GIVEN CHECKPOINTS, AND THE SOURCE IS NOT RETURNED.**
    Inherited from the archive's endpoint with its reasoning intact, because the
    reasoning is about the measurement and not about that app: words the aligned
    model reaches for often do not exist in the base distribution at all, so an
    author who only ever sees the base cannot tag the ARRIVAL side and
    substitution is under-measured by whatever alignment invented. Withholding
    the source is the second half -- knowing which checkpoint offered a word
    would let prompts be chosen by how large the effect looks.

    Anything built on this must therefore say *"poles declared on the pooled
    vocabulary, blind to source"*. It may not say *"declared on the base"*.

    **THE POOL IS NOT A MODEL'S DISTRIBUTION** -- it is a sum then a
    renormalisation across checkpoints -- so it is never written anywhere under
    either id. This route writes nothing at all.
    """
    from . import twp
    from .checkpoint import Checkpoint

    pooled, res_sum, skipped, n_ok = {}, {}, None, 0
    with _SLOT_LOCK:
        #: **THE CAP CANNOT BE SMALLER THAN THIS REQUEST.** A pooled call over
        #: three checkpoints under a cap of 2 would evict the first model before
        #: reaching the third and then report a pool of three, which is a wrong
        #: number rather than a slow one. The request's own width is the floor.
        want = len(dict.fromkeys(model_ids))
        cap = max(_SLOT_MAX, want)
        for mid in model_ids:
            ld = _SLOT_MODELS.get(mid)
            if ld is None:
                #: EVICT FIRST, THEN LOAD -- so the peak is `cap` models and not
                #: `cap + 1`. See `_evict_to`.
                _evict_to(cap - 1)
                ld = Checkpoint(mid).load()
            #: Re-inserted on every use, not only on load, so `move_to_end`
            #: semantics hold: LRU order has to track USE or the cache evicts
            #: whichever model was loaded longest ago regardless of demand.
            _SLOT_MODELS.pop(mid, None)
            _SLOT_MODELS[mid] = ld
            try:
                w1, r1, _calls = twp.expand(
                    ld.model, ld.tok, prompt, ld.dev, ld.bmask,
                    cjk=ld.cjk, bos_policy=ld.bos_policy)
            except twp.SkipPrompt as sk:
                #: THE INSTRUMENT'S REFUSAL IS THE ANSWER, not an error. twp
                #: refuses a prompt that does not survive the model's own
                #: tokenizer, and a prompt being unmeasurable on a checkpoint is
                #: exactly what an author writing prompts needs to be told.
                skipped = str(sk)
                continue
            n_ok += 1
            for (surface, _t1), mass in w1.items():
                pooled[surface] = pooled.get(surface, 0.0) + float(mass)
            #: **THE RESIDUAL IS POOLED THE SAME WAY AS THE WORDS.** The first
            #: version kept the FIRST model's residual and paired it with a mean
            #: over all of them, so `sum(words) + residual` came to 1.0499 on a
            #: two-model pool -- measured 2026-08-16 on SmolLM2-360M and its
            #: Instruct. Nothing raised: the words were right, the residual was a
            #: real number from a real model, and only the identity between them
            #: was false.
            #:
            #: That identity is the instrument's own accounting -- `runners.run`
            #: writes `conservation = sum(w.values()) + res["total"]` into every
            #: stored cell so the ingest gate can refuse a producer that cannot
            #: close its books. A reader that breaks it silently is worse than one
            #: that never reported a residual.
            if r1:
                for key, val in r1.items():
                    if isinstance(val, (int, float)):
                        res_sum[key] = res_sum.get(key, 0.0) + float(val)

    if not n_ok:
        return {"prompt": prompt, "models": model_ids, "n_models": len(model_ids),
                "n_words": 0, "shown": 0, "words": [], "residual": None,
                "rule_version": twp.RULE_VERSION, "dict_sha": twp.dict_sha(),
                "theta": twp.THETA, "skipped": skipped or "no model produced a cell",
                "conservation": None}

    #: DIVIDED BY THE MODELS THAT ANSWERED, not by the models asked for. A
    #: checkpoint that SkipPrompt'd contributed no mass, so counting it in the
    #: denominator scales the whole pool down and breaks the identity again --
    #: the same defect one level along.
    words = [{"word": w, "p": p / n_ok} for w, p in pooled.items()]
    words.sort(key=lambda d: -d["p"])
    residual = {k: v / n_ok for k, v in res_sum.items()} if res_sum else None
    #: NON-NUMERIC FIELDS ARE DROPPED AND SAID TO BE DROPPED. `resolver` and
    #: `resolved_surface` are per-model facts; a pool has no single one, and
    #: carrying the first model's would be the bug above wearing a string.
    if residual is not None and len(model_ids) > 1:
        residual["resolver"] = None
        residual["resolved_surface"] = None

    conservation = sum(w["p"] for w in words) + (residual or {}).get("total", 0.0)
    #: ASSERTED, NOT HOPED. This is the guard that would have caught the pooling
    #: bug on the first two-model call instead of on a hand check afterwards.
    if abs(conservation - 1.0) > 1e-4:
        raise RuntimeError(
            "slot pool failed conservation: sum(words) + residual = %.6f, "
            "expected 1.0 within 1e-4, over %d model(s) that answered. The pool "
            "and its residual disagree, which means one of them is not a mean "
            "over the same set." % (conservation, n_ok))

    return {
        "prompt": prompt,
        "models": model_ids,
        "n_models": len(model_ids),
        "n_answered": n_ok,
        "n_words": len(words),
        "shown": min(k, len(words)),
        "words": words[:k],
        "residual": residual,
        #: RETURNED so the panel can show that the books close. A check whose
        #: result never leaves the server is a check the reader has to trust.
        "conservation": conservation,
        "rule_version": twp.RULE_VERSION,
        "dict_sha": twp.dict_sha(),
        "theta": twp.THETA,
        "skipped": skipped,
    }


# ---------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "malignment"

    def do_GET(self):
        parsed = urlparse(self.path)
        path, q = parsed.path, parse_qs(parsed.query)
        try:
            payload = self._route(path, q)
        except KeyError as e:
            return self._json(404, {"error": str(e)})
        except ValueError as e:
            return self._json(400, {"error": str(e)})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._json(500, {"error": "%s: %s" % (type(e).__name__, e)})
        if payload is None:
            return self._static(path)
        self._json(200, payload)

    def _route(self, path, q):
        one = lambda k, d=None: (q.get(k) or [d])[0]

        if path == "/health":
            #: `slot_loaded` IS IN LRU ORDER, not sorted. The order is
            #: information -- it says which model the next load will evict --
            #: and sorting it alphabetically threw that away for tidiness.
            return {"status": "ok", "db": _db_name(),
                    "slot_enabled": _ALLOW_SLOT,
                    "slot_loaded": list(_SLOT_MODELS),
                    "slot_max": _SLOT_MAX}
        if path == "/store/inventory":
            return _store_inventory()
        if path == "/roster":
            return _roster_summary()
        if path == "/roster/population":
            return _roster_population(one("kind", "endpoints"))
        if path == "/experiments":
            man = _manifest()
            return {
                #: THE REGISTER IS SERVED AS THE FILE, NOT PARSED INTO STATUSES.
                #: `experiments/README.md` holds THE hypothesis register, and the
                #: repo's rule is that a number in two files is a number that
                #: will disagree with itself. A status this server derived --
                #: from a README regex, from whether `results/` is populated --
                #: would be a second status, and it would be the one on screen.
                "register_md": _read_text(os.path.join(EXPERIMENTS, "README.md")),
                "questions": [{k: v for k, v in d.items() if k != "_dir"}
                              for d in sorted(man.values(), key=lambda d: d["id"])],
            }
        if path == "/experiment":
            d = _question(one("id"))
            return {
                **{k: v for k, v in d.items() if k != "_dir"},
                "readme_md": _read_text(os.path.join(d["_dir"], "README.md")),
                "registration_md": _read_text(os.path.join(d["_dir"], "registration.md")),
                #: THE POPULATION RECEIPT, VERBATIM. `RESULTS.md` §2 requires a
                #: result to name its population as a RULE and as MEMBERSHIP;
                #: `population.json` is the membership half. Served whole, so the
                #: reader checks the receipt rather than a summary of it.
                "population": _read_json(os.path.join(d["_dir"], "population.json")),
            }
        if path == "/experiment/result":
            d = _question(one("id"))
            grain = one("grain")
            names = {r["grain"] for r in d["results"]}
            if grain not in names:
                raise KeyError("no grain %r in %s; have: %s"
                               % (grain, d["id"], ", ".join(sorted(names)) or "(none)"))
            cap = _int(one("limit"), DEFAULT_ROW_CAP, 1, MAX_ROW_CAP)
            p = os.path.join(d["_dir"], "results", grain)
            if grain.endswith(".json"):
                return {"id": d["id"], "grain": grain, "json": _read_json(p)}
            if not grain.endswith(".csv"):
                raise ValueError("grain %r is neither .csv nor .json" % grain)
            return {"id": d["id"], "grain": grain, **_read_csv(p, cap),
                    "cap": cap}
        if path == "/slot":
            if not _ALLOW_SLOT:
                raise ValueError("this server was started with --no-slot")
            prompt = one("prompt", "")
            if not prompt.strip():
                raise ValueError("prompt required")
            mids = [s.strip() for s in (one("model") or "").split(",") if s.strip()]
            if not mids:
                raise ValueError(
                    "model required -- a comma-separated list of checkpoint ids. "
                    "There is deliberately no default: a default pool is a "
                    "population choice, and one made in a server is one nobody "
                    "reports.")
            return _slot(prompt, mids, _int(one("k"), 50, 5, 500))
        return None                                     # -> static

    # -- helpers -----------------------------------------------------------

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        #: The dev server proxies `/api` from another origin, so without this the
        #: app works built and fails in development -- the direction that wastes
        #: the most time, since the failure appears only where the debugging happens.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path):
        """Serve the built app, if it has been built.

        **The path is resolved and then checked to be under `UI_DIST`.** Not
        sanitised, checked: `os.path.realpath` after the join, compared with
        `os.path.commonpath`. A blacklist of `..` is a pattern, and this file's
        whole position is that membership beats patterns.
        """
        rel = path.lstrip("/") or "index.html"
        target = os.path.realpath(os.path.join(UI_DIST, rel))
        root = os.path.realpath(UI_DIST)
        if os.path.commonpath([target, root]) != root:
            return self._json(403, {"error": "outside the served root"})
        if os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.isfile(target):
            #: SPA FALLBACK, and only for a request that wants a document.
            #: Falling back for a missing .js would answer a script request with
            #: HTML, and the browser's error then names the wrong thing.
            idx = os.path.join(root, "index.html")
            if os.path.isfile(idx) and "." not in os.path.basename(rel):
                target = idx
            else:
                return self._json(404, {
                    "error": "no such asset: %s" % rel,
                    "hint": "the app is not built. `cd ui && npm install && npm run "
                            "build`, or run `npm run dev` and use the Vite server."})
        ctype = {".html": "text/html", ".js": "text/javascript",
                 ".css": "text/css", ".json": "application/json",
                 ".svg": "image/svg+xml", ".png": "image/png",
                 ".woff2": "font/woff2"}.get(os.path.splitext(target)[1],
                                             "application/octet-stream")
        with open(target, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        #: Quiet by default: an interactive app polls, and a request log at that
        #: rate buries the load messages that are worth reading.
        if os.environ.get("MALIGNMENT_SERVE_LOG"):
            super().log_message(fmt, *args)


def _question(qid):
    man = _manifest()
    if qid not in man:
        raise KeyError("no experiment %r; have: %s"
                       % (qid, ", ".join(sorted(man)) or "(none)"))
    return man[qid]


def _read_json(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _int(v, default, lo, hi):
    if v is None:
        return default
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise ValueError("expected an integer, got %r" % v)
    #: CLAMPED AND NOT REJECTED, because the bound is a resource limit rather
    #: than a correctness one -- and the payload reports what was actually used,
    #: so a clamped request is visible rather than silently honoured.
    return max(lo, min(hi, n))


def _db_name():
    try:
        from . import ch
        return ch.DB
    except Exception as e:
        return "unavailable: %s" % e


def serve(port=8431, host="127.0.0.1", slot=True):
    global _ALLOW_SLOT
    _ALLOW_SLOT = slot
    srv = ThreadingHTTPServer((host, port), Handler)
    man = _manifest()
    #: **FLUSHED, BECAUSE THIS BANNER'S WHOLE JOB IS TO BE READ FROM A LOG.**
    #: Python block-buffers stdout when it is not a terminal, so a backgrounded
    #: `> serve.log` held ZERO bytes while the server answered requests
    #: normally -- measured 2026-08-16. The banner names which database this
    #: process is pointed at, on a machine that also runs `lltk` at 409 GiB;
    #: that is precisely the line you want when you have forgotten which server
    #: is on which port, and it was invisible in the only mode where you would
    #: need to look it up.
    say = lambda m: print(m, flush=True)
    say("malignment.serve  http://%s:%d" % (host, port))
    say("  db          %s" % _db_name())
    say("  experiments %d question%s" % (len(man), "" if len(man) == 1 else "s"))
    say("  ui_dist     %s" % (UI_DIST if os.path.isdir(UI_DIST)
                              else "(not built -- use `npm run dev`)"))
    say("  slot        %s" % ("enabled, lazy, at most %d model(s) resident"
                              % _SLOT_MAX if slot else "REFUSED (--no-slot)"))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        say("\nstopped")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int,
                    default=int(os.environ.get("MALIGNMENT_API_PORT", 8431)))
    ap.add_argument("--host", default="127.0.0.1",
                    help="0.0.0.0 to reach it over Tailscale")
    ap.add_argument("--no-slot", action="store_true",
                    help="refuse /slot outright, so no route in this process "
                         "can load weights")
    ap.add_argument("--slot-max", type=int, default=_SLOT_MAX,
                    help="how many models /slot may hold resident (default %d). "
                         "A request naming more than this raises the cap for "
                         "itself rather than evicting mid-pool." % _SLOT_MAX)
    a = ap.parse_args()
    globals()["_SLOT_MAX"] = a.slot_max
    serve(port=a.port, host=a.host, slot=not a.no_slot)


if __name__ == "__main__":
    main()
