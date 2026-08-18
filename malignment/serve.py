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

## THIS PROCESS SHARES A DEVICE WITH WHATEVER ELSE IS MEASURING

**`/slot` is not the only thing on the card.** On 2026-08-16 this server was
holding two 360M models while `python -m malignment.runners Alchan/mpt-7b-chat
--all-prompts` was 51 minutes into a fleet on the same MPS device. Nothing went
wrong at those sizes, and nothing in either process would have noticed if it had.

The campaign has already paid for this once. `twp.free`'s docstring books the
2026-07-30 32B OOM that was recorded as *"32B at fp16 is marginal on 80 GB"* --
a single 32B is 64 GB and fits; **two at once do not**, and the second one was
the same code holding a model it had finished with.

Two things follow, and neither is a detection mechanism -- sniffing for other
processes is fragile and would be wrong the first time someone runs a fleet on a
different box:

- **`_SLOT_TTL` is the mitigation that works without anyone deciding anything.**
  A model this app loaded is gone ten minutes later whether or not the person who
  loaded it remembered a fleet was running.
- **`--no-slot` is the deliberate one.** Serving the app during a large run with
  `--no-slot` makes every other route work exactly as before and removes any
  possibility of this process touching the device. That is the right way to read
  results while something big is measuring.

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
import sys
import threading
from time import monotonic as _monotonic
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

#: ── IS THIS PROCESS RUNNING THE CODE ON DISK?
#:
#: **A PYTHON SERVER DOES NOT HOT-RELOAD, AND A STALE ONE IS INVISIBLE.** On
#: 2026-08-17 a `/slot/save` route was added, committed and tested, and the
#: running server answered `no POST route /slot/save` for as long as it took
#: someone to notice the process had been up six hours. That reads as a missing
#: feature, not as a stale process, and it is the second failure of this shape:
#: the symptom describes the wrong object.
#:
#: **AND IT IS NOT ONLY THIS FILE.** A lazy `from .slots import x` inside a
#: handler defers the FIRST import; it does not re-read the file afterwards,
#: because `sys.modules` caches it. Verified rather than assumed: edit a module
#: after its first use and the handler keeps returning the old value until
#: `importlib.reload`. So every `.py` in the package is equally stale, and the
#: check covers all of them.
#:
#: CONTENT HASHES, NOT MTIMES. A `touch`, a save with no edit, or a checkout that
#: rewrites a file identically are not changes, and reporting them as such trains
#: the reader to ignore the badge. 23 files, 534 KB, 0.7 ms to hash the lot --
#: measured, and `/health` is polled every 15 s, so the cheap-looking stat
#: optimisation would buy 0.7 ms and cost the distinction.
#:
#: This DETECTS staleness and does not fix it. Reloading is the thing that cannot
#: be done safely here: `_SLOT_MODELS` lives in this module's globals, so
#: reloading `serve` drops the resident weights, which is the expense the reload
#: would exist to avoid.
def _source_files():
    import glob
    here = os.path.dirname(os.path.abspath(__file__))
    return sorted(glob.glob(os.path.join(here, "*.py")))


def _source_state():
    import hashlib
    out = {}
    for f in _source_files():
        try:
            with open(f, "rb") as fh:
                out[os.path.basename(f)] = hashlib.sha1(fh.read()).hexdigest()
        except OSError:
            #: A file that cannot be read is NOT reported as changed. It is
            #: reported as missing, which is a different fact.
            out[os.path.basename(f)] = None
    return out


_SOURCE_AT_BOOT = _source_state()
_BOOTED_AT = None


def _source_status():
    now = _source_state()
    changed = sorted(k for k in set(now) | set(_SOURCE_AT_BOOT)
                     if now.get(k) != _SOURCE_AT_BOOT.get(k))
    return {"stale": bool(changed), "changed": changed,
            "n_files": len(now), "pid": os.getpid(), "booted_at": _BOOTED_AT}


#: Returned by a route that has already written its own response. `None` means
#: "not an API route, try static", so a binary route cannot use it.
_SENT = object()

_SLOT_LOCK = threading.Lock()
#: See `/plot/render`: plotnine's backend is not reentrant across threads.
_PLOT_LOCK = threading.Lock()
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
#: **AND A MODEL IS RELEASED AFTER THIS MANY SECONDS UNUSED** (RH, 2026-08-16:
#: *"why does server need to hold any resident at all? ... until then this is a
#: markdown reader"*).
#:
#: The count cap alone was the wrong shape. It bounds the WORST case and does
#: nothing about the common one: a single Slot excursion left a model resident
#: for the life of the process, so an app that is a reader 95% of the time held
#: gigabytes for the 5%.
#:
#: **BUT NOT ZERO RESIDENCY, WHICH WAS THE OTHER OPTION AND IS WORSE.** Measured
#: here: SmolLM2-360M is 5.7s cold against 0.95s warm, OLMo-2-1B ~10s cold.
#: Slot is an authoring loop -- type, look, retag, retype -- and dropping after
#: every call makes every iteration pay the load. The residency is not a
#: convenience, it is what makes the panel usable at all.
#:
#: So: hold while someone is working, release when they are not. Ten minutes is
#: long enough to cover thinking about a prompt and short enough that a session
#: someone walked away from does not hold a 3B overnight.
_SLOT_TTL = float(os.environ.get("MALIGNMENT_SLOT_TTL", 600))
#: {model_id: monotonic seconds at last use}. Separate from `_SLOT_MODELS` so the
#: eviction order (LRU) and the eviction TRIGGER (idle) stay independent -- they
#: answer different questions and conflating them is how a cache starts evicting
#: a model that is in active use because something else is old.
_SLOT_USED = {}
_ALLOW_SLOT = True
#: Filled by `serve()` after `slots.check_diagnostic_pair` passes. Empty until
#: then, so a route cannot serve an unverified pair.
_DIAGNOSTIC_PAIR = ()


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
        _SLOT_USED.pop(mid, None)
        dropped.append(mid)
    if dropped:
        #: No arguments. See above.
        twp.free()
        print("  slot: evicted %s (cap %d)" % (", ".join(dropped), _SLOT_MAX),
              flush=True)
    return dropped


def _reap_idle():
    """Release any model unused for `_SLOT_TTL`, so the process goes back to zero.

    A DAEMON THREAD AND NOT A CHECK ON THE NEXT REQUEST, which was the cheaper
    design and does not work: the whole point is to free memory during a period
    when NO request arrives. A lazily-evaluated TTL frees the model at the moment
    someone comes back to use it, which is precisely backwards.
    """
    import time as _time
    from . import twp
    while True:
        _time.sleep(30)
        try:
            with _SLOT_LOCK:
                now = _time.monotonic()
                stale = [m for m, t in _SLOT_USED.items()
                         if now - t > _SLOT_TTL and m in _SLOT_MODELS]
                for mid in stale:
                    _SLOT_MODELS.pop(mid, None)
                    _SLOT_USED.pop(mid, None)
                if stale:
                    twp.free()
                    print("  slot: released %s after %.0fs idle (now %d resident)"
                          % (", ".join(stale), _SLOT_TTL, len(_SLOT_MODELS)),
                          flush=True)
        except Exception as e:                             # noqa: BLE001
            #: A reaper that dies takes the whole TTL with it and leaves no trace,
            #: which reads exactly like a TTL that is working.
            print("  slot: reaper error (models stay resident): %s: %s"
                  % (type(e).__name__, e), flush=True)


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
        #: **`plot.py` IS A DISCOVERY KEY TOO** (2026-08-17). It was already
        #: reported in `has` and was not admitting anything, so a folder whose
        #: only producer is a plot was invisible -- `exploratory/prompt_slopes`
        #: is exactly that shape: RH put the DATA producer in `movement.py` and
        #: left the folder holding the figure producer alone. A walk keyed on
        #: `run.py` assumes every folder computes its own data, which stopped
        #: being true the moment a producer was shared.
        if not ({"run.py", "registration.md", "plot.py"} & fs):
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


#: ── WHICH MODELS MARK CJK PUNCTUATION AS A BOUNDARY.
#:
#: **READ FROM A COMMITTED CALIBRATION, NOT RE-DERIVED.**
#: `numeric_boundary/results/cjk_boundary.csv` is lacan's, and it classifies
#: every model that has CJK punctuation tokens by whether `boundary_mask` marks
#: them: 49 do, 84 do not, 0 partial. `marked_boundary == 0` is the affected set.
#:
#: WHY THE APP NEEDS IT. On an affected model `，` is in NEITHER the static
#: `PUNCT` lookup (byte-level BPE hands the mask `ï`, not `，`) NOR
#: `cjk_vocab`'s ids, so it survives as a CONTINUATION and `expand` walks
#: through it -- crediting `一个` at depth 1 and again at depth 2 via `一个，`,
#: which `clean_surface` then strips back to `一个`. The stored SURFACE is clean
#: and the probability behind it is double-counted (malign, [6435]).
#:
#: The shape is what makes this a panel problem rather than a footnote
#: (malign, [6437], one model / two prompts, so a shape and not a roster
#: magnitude): 2-4% of keys affected, those keys carrying 17-33% of all resolved
#: mass because they are the TOP words, aggregate error under 2%, per-word
#: inflation to 1.43x, and an English control of exactly zero. **A total barely
#: moves; a ranking moves a lot, and only on some models.** This panel puts 50
#: pairs side by side on one prompt, which is where a family-dependent
#: reordering is displayed as a comparison.
_CJK_MASK = {"at": 0.0, "affected": None, "clean": None, "source": None}


def _cjk_mask_status():
    now = _monotonic()
    if _CJK_MASK["affected"] is None or now - _CJK_MASK["at"] > 900:
        path = os.path.join(EXPERIMENTS, "instrument_calibrations",
                            "numeric_boundary", "results", "cjk_boundary.csv")
        affected, clean = [], []
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    if r.get("loaded") != "1":
                        continue
                    try:
                        n = int(r.get("cjk_punct_tokens") or 0)
                        marked = int(r.get("marked_boundary") or 0)
                    except ValueError:
                        continue
                    if n <= 0:
                        continue
                    (clean if marked == n else affected).append(r["model"])
        _CJK_MASK.update(at=now, affected=sorted(affected), clean=sorted(clean),
                         source=os.path.relpath(path, ROOT)
                         if os.path.exists(path) else None)
    return _CJK_MASK


#: ── PROMPTS: the frames, and how much each one moves.
#:
#: **THE ARITHMETIC IS IN `views.py`, NOT HERE.** `prompt_movement` and
#: `prompt_coverage` are VIEWS; this selects from them and joins the metadata.
#: The module rule holds: the server is not deriving a median, it is reading one
#: a view defines, and the view is versioned in a file with the rest of them.
#:
#: **CACHED BECAUSE IT IS MEASURED SLOW, NOT BECAUSE IT FELT SLOW.** The rollup
#: is 13.9 s over 4,484 prompts and 400,267 cells. `views.py` says materialise
#: only on a measured reason -- that is one, and a MATERIALISED TABLE was still
#: the wrong answer: it needs a refresh discipline, and a stale one is invisible.
#: This repo lost a day to exactly that when `{db}.pairs` went stale and every
#: row count stayed plausible. A cache with a TTL and a `computed_at` the panel
#: shows is the version whose staleness is on screen.
_PROMPTS = {"at": 0.0, "rows": None, "computed_at": None, "undeclared": None}
_PROMPTS_TTL = 900


def _prompt_rows():
    from . import ch
    now = _monotonic()
    if _PROMPTS["rows"] is None or now - _PROMPTS["at"] > _PROMPTS_TTL:
        import datetime
        rows = ch.query("""
SELECT p.prompt AS prompt, p.prompt_id AS prompt_id, p.domain AS domain,
       p.subdomain AS subdomain, p.family AS family, p.language AS language,
       p.contrast_type AS contrast_type, p.pair_id AS pair_id,
       p.pair_role AS pair_role, p.source AS source, p.finding AS finding,
       p.status AS status, p.slot AS slot,
       cov.n_models AS n_models, cov.resid_median AS resid_median,
       pm.n_pairs AS n_pairs, pm.js_median AS js_median,
       pm.departed_median AS departed_median, pm.arrived_median AS arrived_median,
       pm.net_median AS net_median
FROM {db}.prompts p
LEFT JOIN {db}.prompt_coverage cov ON cov.prompt = p.prompt
LEFT JOIN (SELECT * FROM {db}.prompt_movement WHERE rule = 'canonical') pm
       ON pm.prompt = p.prompt
""")
        #: **DECLARED AGAINST MEASURED, COUNTED.** The `prompts` table declares
        #: 3,120; `twp_words` holds 4,484 distinct, so ~1,760 measured prompts
        #: are not in the roster's table. A panel that showed only the declared
        #: ones without saying so would present a 3,120-row table as the corpus.
        _PROMPTS["undeclared"] = ch.scalar(
            "SELECT count() FROM (SELECT DISTINCT prompt FROM {db}.twp_words "
            "WHERE prompt NOT IN (SELECT prompt FROM {db}.prompts))", 0)
        _PROMPTS["rows"] = rows
        _PROMPTS["at"] = now
        _PROMPTS["computed_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    return _PROMPTS["rows"], _PROMPTS["computed_at"]


#: ── PLOTS: the producers declare, this reads the declaration.
#:
#: **THIS IS THE ONE PLACE THE SERVER RUNS SOMETHING THAT MAKES A NEW ARTIFACT**,
#: and it is not an exception to the module rule. The rule is that the server
#: does not COMPUTE -- no mean, no share, no re-filtered population -- because a
#: number with no producer is not a result. A plot route computes nothing: it
#: calls a producer that lives in `experiments/`, with parameters that producer
#: declared, and the producer owns every line of the arithmetic. The app is
#: choosing which registered thing to run, not doing the work.
#:
#: **EVERY PARAMETER IS VALIDATED AGAINST THE DECLARED SPEC**, by membership for
#: choices and by clamping for ints. The `prompt` type is validated against the
#: set of prompts the STORE holds, which is the security boundary: a prompt
#: reaches a ClickHouse query, and this repo's rule is that nothing a client
#: sends does. Membership makes an injection attempt simply not a member.
_PLOTS = {}
_PLOT_PROMPTS = {"at": 0.0, "set": None}
#: Re-read after this many seconds. The prompt set grows when a fleet lands, and
#: a server that cached it at boot would refuse a prompt that now has cells.
_PLOT_PROMPTS_TTL = 300


def _plot_specs():
    """{id: (spec, module)} for every `experiments/**/plot.py` exposing `PLOT`."""
    if _PLOTS:
        return _PLOTS
    import importlib
    import importlib.util
    for dirpath, dirnames, filenames in os.walk(EXPERIMENTS):
        dirnames[:] = [d for d in dirnames
                       if d not in ("__pycache__", "results", "figures",
                                    "workflows", "sandbox")]
        if "plot.py" not in filenames:
            continue
        path = os.path.join(dirpath, "plot.py")
        rel = os.path.relpath(dirpath, EXPERIMENTS).replace(os.sep, "/")
        #: BY PATH, UNDER A UNIQUE NAME. Every experiment folder may hold a
        #: `plot.py`, so a bare import would resolve to whichever won the path
        #: race -- the same collision `rank_vs_cardinal` already documents.
        name = "plot_" + rel.replace("/", "_")
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
        except Exception as e:
            #: A producer that will not import is REPORTED, not skipped. A plot
            #: silently missing from the list is indistinguishable from one that
            #: was never written.
            _PLOTS["!" + rel] = ({"id": "!" + rel, "name": rel,
                                  "error": "%s: %s" % (type(e).__name__, e),
                                  "params": []}, None)
            continue
        p = getattr(mod, "PLOT", None)
        if not isinstance(p, dict) or not p.get("id"):
            continue
        p = dict(p)
        p["experiment"] = rel
        p["has_render"] = callable(getattr(mod, "render", None))
        #: **CHECKED AT DISCOVERY, NOT AT RENDER.** A producer's heavy imports
        #: are usually lazy, so the module imports fine and the missing package
        #: only surfaces when someone presses the button. Import-checking what
        #: the spec DECLARES it needs turns that into a fact the list can carry.
        missing = []
        for req in (p.get("requires") or []):
            try:
                importlib.import_module(req)
            except Exception:
                missing.append(req)
        p["missing_requires"] = missing
        _PLOTS[p["id"]] = (p, mod)
    return _PLOTS


def _plot_prompt_set():
    """Prompts the store holds. Cached, and FILTERED IN PYTHON.

    Loaded once and filtered here rather than with a `LIKE` on the client's
    text, because a substring filter in SQL is client text reaching SQL by a
    politer route. 4,484 strings is nothing to hold.
    """
    from . import ch
    now = _monotonic()
    if _PLOT_PROMPTS["set"] is None or now - _PLOT_PROMPTS["at"] > _PLOT_PROMPTS_TTL:
        rows = ch.query("SELECT DISTINCT prompt FROM {db}.twp_words")
        _PLOT_PROMPTS["set"] = sorted(r["prompt"] for r in rows)
        _PLOT_PROMPTS["at"] = now
    return _PLOT_PROMPTS["set"]


def _plot_coerce(spec, one):
    """Declared params -> validated kwargs. Raises with what it would accept."""
    kw = {}
    for f in spec.get("params", []):
        raw = one(f["name"])
        t = f.get("type", "text")
        if raw is None or raw == "":
            if f.get("required"):
                raise ValueError("%r is required" % f["name"])
            kw[f["name"]] = f.get("default", "")
            continue
        if t == "choice":
            if raw not in f["choices"]:
                raise ValueError("%r must be one of %s, got %r"
                                 % (f["name"], ", ".join(f["choices"]), raw))
            kw[f["name"]] = raw
        elif t == "int":
            try:
                v = int(raw)
            except ValueError:
                raise ValueError("%r must be a whole number, got %r"
                                 % (f["name"], raw))
            lo, hi = f.get("min", -10 ** 9), f.get("max", 10 ** 9)
            #: CLAMPED AND SAID SO, not refused. A top-N of 500 is a legible
            #: request for "lots"; silently drawing 30 is the lie, so the caller
            #: is told in the payload.
            kw[f["name"]] = max(lo, min(hi, v))
        elif t == "prompt":
            if raw not in _plot_prompt_set():
                raise ValueError(
                    "that prompt has no cells in the store, so the figure would "
                    "be empty. Ask /plot/prompts for the %d it holds."
                    % len(_plot_prompt_set()))
            kw[f["name"]] = raw
        else:
            kw[f["name"]] = raw
    return kw


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

#: **THE DEFAULT SCREENING PAIR** (RH, 2026-08-17). Rank 19 of 56 on
#: `instrument_calibrations/screening_base`, max_dev 28.6 -- just outside the
#: candidate band, so middling rather than typical, and chosen on availability
#: and size rather than on the ranking.
#:
#: NOT `stablelm-2-1_6b`, which ranks 6/56 and was withdrawn: its lineage graph
#: is wrong. `models.yaml` books `chat -dpo-> zephyr` where both HF cards say
#: each is finetuned FROM THE BASE, so they are siblings; correcting it makes
#: the lineage UNRESOLVED and the endpoint a ruling for RH. Filed at [6371].
#: Defaulting an authoring tool to a pair whose graph is wrong would bake the
#: error into every item authored with it.
DEFAULT_PAIR_BASE = "HuggingFaceTB/SmolLM3-3B-Base"


def _pairs():
    """The 50 declared (base, endpoint) pairs, with the PATH between them.

    **`n_steps` IS NOT COSMETIC AND IS WHY THIS IS NOT JUST TWO IDS.** 17 of the
    50 are multi-step: the default is `SmolLM3-3B-Base -> checkpoints ->
    @it-soup-APO -> SmolLM3-3B`, three ops (`sft`, `apo`, `instruct`). Pooling
    the two ENDS of that is a legitimate screening distribution, but "aligned"
    then means the far end of three operations, not one, and an item stamped
    without the path records a claim it cannot support.
    """
    from . import roster
    ep, unresolved = roster.endpoints()
    paths = {p["base"]: p for p in roster.paths()}
    out = []
    for b, a in sorted(ep.items()):
        pa = paths.get(b, {})
        out.append({"base": b, "endpoint": a,
                    "n_steps": pa.get("n_steps"), "ops": pa.get("ops") or [],
                    "label": "%s -> %s" % (b.split("/")[-1], a.split("/")[-1])})
    #: RETURNED EVEN WHEN EMPTY. `docs/HOWTO.md`: a caller that ignores
    #: `unresolved` is choosing by accident. A dropdown that silently omitted an
    #: unresolvable lineage would be that caller.
    return {"pairs": out, "unresolved": {k: v for k, v in unresolved.items()},
            "default": DEFAULT_PAIR_BASE}


#: **A TTL CACHE OVER SCREENING, BECAUSE `axis` AND `save` BOTH RE-SCREEN.**
#: The client re-screens on purpose -- masses must come from the run the tags
#: were made against -- but that makes an author's loop pay a full forward pass
#: on both checkpoints per call, and an agent reading one section at a time pays
#: it once per section. An authoring agent was measured running five identical
#: `axis` calls to grep five different headings: five poolings of one prompt.
#:
#: **This does not weaken the guarantee the re-screening exists for, it enforces
#: it.** Screening is a forward pass with no sampling, so it is deterministic in
#: (prompt, pair, k); the hazard the comment in `slot_client` names is a caller
#: supplying words from a DIFFERENT prompt, which a key containing the prompt
#: cannot do. Cached, `axis` and `save` provably share one screening rather than
#: two runs that happen to agree.
#:
#: Keyed on `rule_version` and `dict_sha` so a rule change cannot be served from
#: a pool computed under the old one -- the failure that would otherwise be
#: invisible, since a stale pool is well-formed.
#: **THE SLOT PATH PINS ITS RULE EXPLICITLY (RH, 2026-08-18).** It reached v3 by
#: importing `twp` and nothing else, which is correct and accidental: the label
#: came from a module constant while the instrument came from whichever module
#: happened to be imported, and those are two independent choices that agreed.
#:
#: malign hit the same shape in malign-logits ([6456]) -- a shared loader printed
#: `rule_version 3` on every caller while a v4 run stamped its cells 4. Their fix
#: is the one copied here: **the version selects the module, so nothing can pick
#: a version without also picking where the numbers come from.**
#:
#: This matters more here than it looks. `screened_by` on every saved item, and
#: both cache keys, read this. The corpus ALREADY holds two screening
#: provenances that no item declares (round3 on Llama-3.1-8B, the rest on
#: SmolLM3), so a second silent instrument change is the one thing this data
#: cannot absorb.
SLOT_RULE_VERSION = 3


def _slot_rule():
    """The rule module the slot path uses, chosen with its version. -> module

    Lazy import so selecting v3 never loads v4. The assert is the point: a
    module whose `RULE_VERSION` disagrees with the version that selected it is
    exactly the mislabelling this exists to prevent, and it fires whether anyone
    remembers this comment or not.
    """
    if SLOT_RULE_VERSION == 3:
        from . import twp as m
    elif SLOT_RULE_VERSION == 4:
        from . import twp_v4 as m
    else:
        raise ValueError(
            "SLOT_RULE_VERSION is %r; the slot path knows 3 and 4. Add the "
            "module here rather than importing it at a call site, so the "
            "version and the numbers cannot be chosen separately."
            % (SLOT_RULE_VERSION,))
    if getattr(m, "RULE_VERSION", None) != SLOT_RULE_VERSION:
        raise AssertionError(
            "%s.RULE_VERSION is %r but the slot path selected %r. Every "
            "`screened_by` block and both cache keys read this, so the label "
            "and the instrument have diverged."
            % (m.__name__, getattr(m, "RULE_VERSION", None), SLOT_RULE_VERSION))
    return m


_SCREEN_CACHE = {}
_SCREEN_CACHE_LOCK = threading.Lock()
#: **THE AXIS IS THE WHOLE REMAINING COST ONCE SCREENING IS CACHED.** Measured
#: on an identical repeated call: screen alone 0.10s, full axis 2.93s and 5.38s.
#: The variance is `cross_corpus` reading ClickHouse across ~1,591 frames, so the
#: first cache moved the bottleneck rather than removing it -- and the caller
#: that re-runs to read one section pays the new bottleneck exactly as it paid
#: the old one.
#:
#: Cacheable on the same argument as screening: bge vectors are themselves
#: cached and deterministic, `stability` is static, `held_out` and `purity` are
#: functions of inputs already in the key. `cross_corpus` is the one moving part
#: -- it sees more frames as the store grows -- and the TTL is what bounds that.
_AXIS_CACHE = {}
_AXIS_CACHE_LOCK = threading.Lock()
_SCREEN_TTL = float(os.environ.get("MALIGNMENT_SCREEN_TTL", 1800))
_SCREEN_CACHE_MAX = int(os.environ.get("MALIGNMENT_SCREEN_MAX", 512))


def _screen_cached(prompt, pair_base, k, compute):
    """Memoise `_slot` for `_SCREEN_TTL` seconds. -> (payload, hit)"""
    _T = _slot_rule()
    key = (prompt, pair_base, int(k), _T.RULE_VERSION, _T.dict_sha())
    #: `_monotonic`, not wall clock: a TTL measured against a clock that can step
    #: backwards over an NTP correction would serve a stale pool for the size of
    #: the step, and nothing about the payload would look wrong.
    now = _monotonic()
    with _SCREEN_CACHE_LOCK:
        hit = _SCREEN_CACHE.get(key)
        if hit is not None and now - hit[0] < _SCREEN_TTL:
            return hit[1], True
    #: Computed OUTSIDE the cache lock. `_slot` takes `_SLOT_LOCK` and can run for
    #: seconds against a cold pair; holding a second lock across it would serialise
    #: every reader behind one writer and turn a cache into a bottleneck.
    val = compute()
    with _SCREEN_CACHE_LOCK:
        _SCREEN_CACHE[key] = (now, val)
        if len(_SCREEN_CACHE) > _SCREEN_CACHE_MAX:
            for dead in sorted(_SCREEN_CACHE, key=lambda x: _SCREEN_CACHE[x][0]
                               )[:len(_SCREEN_CACHE) - _SCREEN_CACHE_MAX]:
                _SCREEN_CACHE.pop(dead, None)
    return val, False


def _slot(prompt, pair_base, k):
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
    from . import twp, roster
    _T = _slot_rule()
    from .checkpoint import Checkpoint

    #: MEMBERSHIP, not a pattern -- the same rule as every other parameter here.
    #: `endpoints()` is the declared population; a base it does not contain is
    #: not a screening pair, and naming the alternatives beats a 404.
    ep, _unresolved = roster.endpoints()
    if pair_base not in ep:
        raise ValueError(
            "%r is not a declared base. Screening takes a pair from "
            "endpoints(); ask /slot/pairs for the %d available."
            % (pair_base, len(ep)))
    paths = {p["base"]: p for p in roster.paths()}
    pa = paths.get(pair_base, {})
    model_ids = [pair_base, ep[pair_base]]

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
            _SLOT_USED[mid] = _monotonic()
            try:
                #: **THROUGH `Checkpoint.probs`, NOT A LOCAL COMPOSITION.** This
                #: was `twp.expand(ld.model, ld.tok, ...)` inline, which made the
                #: server a second place the instrument is reached and a second
                #: place the surface-summing rule lives. `loaded=ld` reuses the
                #: resident model, so the LRU cache above still owns residency.
                w1, r1 = Checkpoint(mid).probs(prompt, loaded=ld)
            except twp.SkipPrompt as sk:
                #: THE INSTRUMENT'S REFUSAL IS THE ANSWER, not an error. twp
                #: refuses a prompt that does not survive the model's own
                #: tokenizer, and a prompt being unmeasurable on a checkpoint is
                #: exactly what an author writing prompts needs to be told.
                skipped = str(sk)
                continue
            n_ok += 1
            #: `probs()` already summed across token paths, so `w1` is keyed on
            #: the surface. The local re-sum that used to live here was the
            #: duplicated half of that rule.
            #:
            #: **ONLY THE TWO ENDS ARE LOADED** (RH: "we just want the endpoints
            #: for SmolLM3-3B"). The default pair's path runs through
            #: `SmolLM3-3B-checkpoints` and `@it-soup-APO`; neither is expanded.
            #: Pooling the ends is a legitimate screening distribution, and the
            #: intermediate rungs are recorded in `pair.ops` rather than loaded.
            for surface, mass in w1.items():
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
                "rule_version": _T.RULE_VERSION, "dict_sha": _T.dict_sha(),
                "theta": _T.THETA, "skipped": skipped or "no model produced a cell",
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
        #: **THE PAIR AND ITS PATH.** Stamped onto the saved item, because
        #: "aligned" means the far end of `n_steps` operations and an item that
        #: records only two ids records a claim it cannot support -- the default
        #: pair is three ops (sft, apo, instruct).
        #:
        #: `per_arm` and `edge` were removed with the diagnostic. They existed
        #: only to feed a movement split, and unused payload is debt: the next
        #: reader has to work out whether anything depends on it.
        "pair": {"base": pair_base, "endpoint": ep[pair_base],
                 "n_steps": pa.get("n_steps"), "ops": pa.get("ops") or []},
        "rule_version": _T.RULE_VERSION,
        "dict_sha": _T.dict_sha(),
        "theta": _T.THETA,
        "skipped": skipped,
    }


# ---------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------

#: Separate from `_SLOT_LOCK`, which exists for `twp._BATCH`. This one guards
#: the SentenceTransformer, whose thread-safety is not guaranteed and whose lazy
#: init is a module-level list. Two locks because they protect two things: an
#: axis build must not queue behind an 8-second model load it does not need, and
#: a twp expansion must not queue behind a bge encode.
_AXIS_LOCK = threading.Lock()


def _axis_cached(prompt, naughty, nice, compute):
    """Memoise the axis payload for `_SCREEN_TTL`. -> (payload, hit)

    Keyed on the POLES AS TAGGED, order-insensitively: `--naughty kill,punch`
    and `--naughty punch,kill` are the same axis and must not be two entries.
    Sorted rather than de-duplicated, because a word repeated in a pole is a
    caller error `build_item` should still see rather than one this silently
    repairs.
    """
    _T = _slot_rule()
    key = (prompt, tuple(sorted(naughty or ())), tuple(sorted(nice or ())),
           _T.RULE_VERSION, _T.dict_sha())
    now = _monotonic()
    with _AXIS_CACHE_LOCK:
        hit = _AXIS_CACHE.get(key)
        if hit is not None and now - hit[0] < _SCREEN_TTL:
            return hit[1], True
    val = compute()
    with _AXIS_CACHE_LOCK:
        _AXIS_CACHE[key] = (now, val)
        if len(_AXIS_CACHE) > _SCREEN_CACHE_MAX:
            for dead in sorted(_AXIS_CACHE, key=lambda x: _AXIS_CACHE[x][0]
                               )[:len(_AXIS_CACHE) - _SCREEN_CACHE_MAX]:
                _AXIS_CACHE.pop(dead, None)
    return val, False


def _slot_axis(prompt, naughty, nice, words, probs=None,
               base_probs=None, aligned_probs=None):
    """The author's poles as an axis, and every candidate's position on it.

    **THE GUARANTEE IS REAL AND IT IS NOT WHERE THIS DOCSTRING USED TO PUT IT.**
    It read *"this route computes no movement and cannot -- `Axis.split` is not
    reachable from here"*, and that stopped being true when `base_probs`/
    `aligned_probs` were added: the handler accepts both (both-or-neither, see
    `do_POST`) and `split` below returns dN whenever they arrive. A docstring
    asserting a blinding the code does not enforce is worse than none, because it
    tells a reader the outcome is unreachable when it is one field away.

    **WHAT ACTUALLY WITHHOLDS dN IS THE CALLER.** The panel pools its two
    checkpoints into ONE distribution and sends that, so `split` is null and no
    movement exists to display -- and `_slot` never reveals which checkpoint
    offered a word, which is the half that stops frames being chosen by how large
    the effect looks. The reasoning for keeping it that way is unchanged (malign,
    [6361]): showing dN beside the screening controls makes looking at the outcome
    the default, and the default is where a population choice hides.

    So the accurate statement is that movement is OPT-IN, by sending two arms
    instead of one, which makes choosing it an act rather than a default. That is
    a weaker guarantee than the old wording claimed and it is the one in force.
    """
    from . import slot_axis
    from .slot_axis import Axis
    with _AXIS_LOCK:
        ax = Axis(prompt, naughty, nice)
        if not ax.ok:
            #: A DEGENERATE AXIS IS AN ANSWER, NOT AN ERROR. The poles embed to
            #: the same point, so there is no direction -- which is a fact about
            #: the tagging, reported as one.
            return {"ok": False, "norm": ax.norm, "scores": [],
                    "note": "the two poles are identical in embedding space"}
        vocab = set(words) | set(naughty) | set(nice)
        #: THE SPLIT IS SCORED OVER THE UNION OF BOTH ARMS, not over the pooled
        #: word list. A word the aligned model invents and the base never offers
        #: is the ARRIVAL side of a substitution -- exactly what the diagnostic
        #: exists to see -- and scoring only the pooled list would drop it if the
        #: caller trimmed to top-k.
        if base_probs and aligned_probs:
            vocab |= set(base_probs) | set(aligned_probs)
        S = ax.score(sorted(vocab))
        st = ax.stats(probs, S) if probs else {}
        #: **dN NEVER TRAVELS WITHOUT `leverage`** (malign, [6361]). The axis
        #: scores substitutions near-neutral, so ΔN can cancel while something
        #: large happens -- `argue` x3.3 for Jews, `rob` x2.1 for Black men, at a
        #: dN near zero. `stats()` above is the companion, and the split is
        #: computed here so the two can only be returned together.
        split = (ax.split(base_probs, aligned_probs, S)
                 if base_probs and aligned_probs else None)
    #: **THE ADMISSIBILITY GATE, WHICH EXISTED AND WAS NEVER REACHABLE.**
    #: `slot_axis.separates` had a selftest and no caller: the route returned
    #: `purity`, `pole_gap` and `defectors` -- every input the gate consumes --
    #: and left the verdict uncomputed, so the one question an automated author
    #: most needs to branch on ("can this axis see the contrast it is about to
    #: weigh?") could not be asked over HTTP.
    #:
    #: **IT IS COMPUTED BEFORE `split` IS READ, and that ordering is the whole
    #: guarantee** (its own docstring): a gate consulted after the result is a
    #: rationalisation, and only the ordering makes "it would have excluded this
    #: axis whichever way its number fell" a claim a reader can check. So it is
    #: returned BESIDE dN rather than instead of it -- a caller that ignores it
    #: gets the same payload as before, and a caller that honours it can say when
    #: it decided.
    sep_ok, sep_gap, sep_correct, sep_total = slot_axis.separates(S, naughty, nice)
    #: **WITHIN-POLE COHERENCE, WHICH `separates` STRUCTURALLY CANNOT ASK.** That
    #: gate tests whether the two poles separate FROM EACH OTHER and says nothing
    #: about whether one pole holds together. An incoherent pole produces an axis
    #: measuring something other than what was tagged and passes every check:
    #: `quit resign kill die` yields a DEATH axis and `separates` is content.
    #:
    #: Returned BESIDE `separates`, never inside it, because it is NOT A GATE -- a
    #: broad pole is a legitimate authoring choice, and `min_pair` is the finding
    #: while the mean is only context (see `coherence`). Both the Svelte panel and
    #: `malign-slot axis` read this route, so one wiring serves the human and the
    #: agent.
    coh = {"naughty": slot_axis.coherence(prompt, naughty, other=nice),
           "nice": slot_axis.coherence(prompt, nice, other=naughty)}
    #: **THE TWO CHECKS THAT NEEDED A VECTOR STORE, now that there is one.**
    #: Both are best-effort: a store that is unreachable makes the report thinner,
    #: never wrong, which is the same contract as the caches.
    cross = stability = None
    try:
        from . import vectors as _V
        #: **k=20 RATHER THAN THE DEFAULT 8.** This is now the ONLY diagnostic
        #: the axis report prints (sections 2-4 and 6 were removed 2026-08-18),
        #: so it carries the whole "are my poles pointing where I think" job on
        #: its own and eight words a side was sized for a report with five other
        #: sections. The cost is `LIMIT 20` instead of `LIMIT 8` in one already-
        #: aggregated query.
        cross = _V.cross_corpus(prompt, naughty, nice, k=20)
    except Exception as e:
        cross = {"error": "%s: %s" % (type(e).__name__, e)}
    try:
        from . import vectors as _V
        stability = _V.pole_stability(naughty, nice)
    except Exception as e:
        stability = {"error": "%s: %s" % (type(e).__name__, e)}
    #: Held-out sibling of `purity`/`defectors`, which score each word against an
    #: axis it helped build. Best-effort on the same contract as the two above:
    #: thinner report, never a wrong one.
    try:
        heldout = slot_axis.held_out(prompt, naughty, nice)
        #: **THE MASS BELONGS BESIDE THE MARGIN**, and its absence was the whole
        #: defect opus-institutional-pilot reported: `withhold` at p=0.0035 and
        #: `demanded` at p=0.128 were printed identically, so a flag on a word
        #: carrying nothing looked exactly like a flag on the pole's main word.
        #: Without it the section offers two actions, do-nothing and delete, and
        #: the brief forbids delete -- "a section whose only reachable action is
        #: the forbidden one will get the forbidden one taken." With it there is a
        #: third: see that the flag cannot be evidence about anything and say so.
        if isinstance(heldout, dict) and heldout.get("words") and probs:
            for d in heldout["words"]:
                d["p"] = float(probs.get(d["word"], 0.0) or 0.0)
    except Exception as e:
        heldout = {"error": "%s: %s" % (type(e).__name__, e)}
    #: **THE MASSES BELONG IN THE AXIS PAYLOAD, NOT ONLY ON THE SAVED ITEM.**
    #: `share` decided 18 quarantines and an author could not see it until after
    #: saving -- the one number that would have caught RH's own `She had big`
    #: tagging (0.024, meaning 98% of tagged mass on the nice side) was computed
    #: at save time and nowhere before it. Same definition as `build_item`:
    #: naughty's portion of the TAGGED mass, not of the distribution.
    _pr = probs or {}
    _gm = sum(float(_pr.get(w, 0.0) or 0.0) for w in naughty)
    _nm = sum(float(_pr.get(w, 0.0) or 0.0) for w in nice)
    _tt = _gm + _nm
    #: **TAGS THE MODEL NEVER OFFERED.** bge embeds any string, so a pole word
    #: absent from the distribution still contributes geometry and the gate
    #: passes on it -- opus-identity scored a pole containing `kill` when `kill`
    #: was absent entirely, got PASS at gap 0.4430 with 16/16 orderings, and the
    #: only trace was a zero it would have had to derive by hand. `save` refuses
    #: these; `axis` said nothing. Named here so the panel can.
    _zero = sorted(w for w in list(naughty) + list(nice)
                   if not float((probs or {}).get(w, 0.0) or 0.0))
    return dict({
        "zero_mass": _zero,
        "naughty_mass": round(_gm, 6),
        "nice_mass": round(_nm, 6),
        "share": round(_gm / _tt, 6) if _tt else None,
        "coherence": coh,
        "cross_corpus": cross,
        "stability": stability,
        "held_out": heldout,
        "separates": {"ok": bool(sep_ok), "gap": float(sep_gap),
                      "correct": int(sep_correct), "total": int(sep_total),
                      "floor": slot_axis.SEPARATION_FLOOR,
                      #: Named so a caller does not have to infer WHICH floor
                      #: refused it from three numbers.
                      "reason": (None if sep_ok else
                                 "a pole is empty after scoring" if not sep_total
                                 else "gap %.4f below floor %.2f" % (sep_gap, slot_axis.SEPARATION_FLOOR)
                                 if sep_gap < slot_axis.SEPARATION_FLOOR
                                 else "%d of %d pairwise orderings correct"
                                      % (sep_correct, sep_total))},
        "split": split,
        "ok": True,
        "norm": ax.norm,
        "pole_gap": ax.pole_gap,
        "purity": ax.purity,
        "defectors": ax.defectors,
        "n_poles": [len(naughty), len(nice)],
        #: **WHAT THE AXIS SELECTS FOR, ON WORDS NOBODY TAGGED** (RH, 2026-08-17:
        #: "compute the subtraction of centroids and then see if the extremes of
        #: untagged words relate?").
        #:
        #: This is a stronger validity check than `coherence` and it supersedes it as
        #: the thing to read first. Coherence measures how a pole's INPUTS are
        #: arranged, and measurement showed it does not rank incoherent poles below
        #: coherent ones -- an undressing pole scored 0.497 against 0.640 for the
        #: pole that produced a death axis. These extremes show what the axis
        #: actually DOES, which is where that defect was visible: `He told his boss
        #: he wanted to` tagged `quit resign kill die` puts `die, perish, killed,
        #: hanged` at its top, and a labour frame selecting for dying is legible in
        #: one glance where 0.640 is not.
        #:
        #: **UNTAGGED ONLY, because the tagged words are there by construction.** A
        #: pole word scoring extremely on its own axis is arithmetic, not evidence;
        #: it is the held-out words that can disagree.
        #:
        #: Shown and not scored, for the same reason as `min_pair`: whether `perish`
        #: belongs beside `quit` is a judgement about what the author meant, and a
        #: number asserting it would be this route inventing the answer.
        "neighbours": {
            "naughty_end": [{"word": w, "s": v} for w, v in
                            sorted(((w, v) for w, v in S.items()
                                    if w not in set(naughty) | set(nice)),
                                   key=lambda x: -x[1])[:10]],
            "nice_end": [{"word": w, "s": v} for w, v in
                         sorted(((w, v) for w, v in S.items()
                                 if w not in set(naughty) | set(nice)),
                                key=lambda x: x[1])[:10]],
        },
        "scores": [{"word": w, "s": v}
                   for w, v in sorted(S.items(), key=lambda x: -x[1])],
    }, **st)


class Handler(BaseHTTPRequestHandler):
    server_version = "malignment"

    def do_POST(self):
        """`/slot/axis` and `/slot/save`. Only the second has side effects.

        `/slot/axis` is a POST for PAYLOAD SIZE, not side effects: it takes the
        candidate word list, which at `k=500` is several kilobytes -- past what a
        URL can carry reliably, and the archive's GET version of this endpoint
        was sized for `k=40` and would have truncated silently rather than failed.

        **`/slot/save` IS THE ONE ROUTE HERE THAT WRITES, AND THE RULE IT LOOKS
        LIKE AN EXCEPTION TO IS NOT THE ONE IT TOUCHES.** The module rule is that
        the server READS AND DOES NOT COMPUTE, the danger being a seventh
        definition of a population growing quietly inside a UI. Saving computes
        nothing: the tags are the author's, the masses come from the run the
        author is already looking at, and every derivation (`item_id`, the mass
        ordering, `share`) lives in `slots.py` beside the rule that owns it.

        What it writes is AUTHORED data, and it writes OUTSIDE THE REPO to
        `$MALIGNMENT_DATA/slots/`. A saved item carries its prompt verbatim from
        the transgressive battery, so it sits behind the same fence as `runners`
        output and the bge vectors.
        """
        parsed = urlparse(self.path)
        if parsed.path == "/slot/save":
            return self._save()
        if parsed.path != "/slot/axis":
            return self._json(404, {"error": "no POST route %s" % parsed.path})
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            prompt = (body.get("prompt") or "").strip()
            naughty = [w for w in (body.get("naughty") or []) if w]
            nice = [w for w in (body.get("nice") or []) if w]
            if not prompt or not naughty or not nice:
                raise ValueError("prompt, naughty and nice all required")
            words = [w for w in (body.get("words") or []) if w]
            probs = body.get("probs") or None
            #: BOTH OR NEITHER. A split needs two distributions; one arm alone
            #: would silently become a diff against an empty dict, which is a
            #: perfectly finite number describing nothing.
            bp, ap = body.get("base_probs"), body.get("aligned_probs")
            if bool(bp) != bool(ap):
                raise ValueError("base_probs and aligned_probs must be sent "
                                 "together or not at all -- one alone diffs "
                                 "against an empty distribution")
            #: **NOT CACHED WHEN MOVEMENT IS REQUESTED.** `bp`/`ap` change the
            #: payload (`split` returns dN) and are NOT in the key, so serving a
            #: cached no-movement axis to a caller that asked for movement would
            #: silently answer a different question. Opt-in movement stays opt-in
            #: by bypassing the cache entirely rather than by growing the key,
            #: because a key that carries two whole distributions is not a key.
            if bp or ap:
                self._json(200, _slot_axis(prompt, naughty, nice, words, probs,
                                           bp, ap))
            else:
                payload, was_hit = _axis_cached(
                    prompt, naughty, nice,
                    lambda: _slot_axis(prompt, naughty, nice, words, probs))
                if isinstance(payload, dict):
                    payload = dict(payload, cached=bool(was_hit))
                self._json(200, payload)
        except ValueError as e:
            self._json(400, {"error": str(e)})
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._json(500, {"error": "%s: %s" % (type(e).__name__, e)})

    def _save(self):
        """Persist one authored item. 200 created/overwritten/unchanged, 409 on collision.

        **THE CLIENT SENDS TAGS AND A DISTRIBUTION, NEVER A COMPUTED FIELD.**
        `item_id`, the mass ordering and `share` are all derived in `slots.py`
        from the words it sends, for the same reason `item_id` is not computed in
        JavaScript: a client-supplied `naughty_mass` that disagreed with the tags
        beside it would be undetectable and permanent.

        A 409 is a REFUSAL TO CLOBBER, not a failure. Re-saving an id with
        different tags means the author retagged, and the previous tagging would
        otherwise vanish with nothing on screen to say so. The client is expected
        to ask and retry with `overwrite`.
        """
        try:
            from .slots import build_item, save_item
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            words = body.get("words") or {}
            if not isinstance(words, dict) or not words:
                raise ValueError("`words` must be a non-empty {word: p} map from "
                                 "the run being saved -- the masses are derived "
                                 "from it here, not accepted from the client")
            #: **`target` NAMES A CORPUS FROM A CLOSED SET, NEVER A PATH.** An
            #: automated author writes its own file (RH, 2026-08-17), and the
            #: obvious way to say which -- a path or a filename from the client --
            #: is a write-anywhere primitive on a route that writes. So the client
            #: sends a KEY and the server owns the mapping, which is the same
            #: membership-not-pattern rule every other parameter here follows.
            from .slots import SLOT_CLIENT_YAML, SLOT_YAML
            targets = {"slot-explorer": SLOT_YAML, "slot-client": SLOT_CLIENT_YAML}
            tgt = (body.get("target") or "slot-explorer").strip()
            if tgt not in targets:
                raise ValueError("target must be one of %s; got %r"
                                 % (", ".join(sorted(targets)), tgt))
            #: **`reviewed` IS ONLY ACCEPTED AS FALSE, and that is not pedantry.**
            #: The field exists to mark what a human has not yet checked, so a
            #: writer that could set it true would be attesting to a review on
            #: behalf of the reviewer. Marking something reviewed is an act for
            #: the panel or the yaml, not for the tool that authored it.
            rev = body.get("reviewed")
            if rev not in (None, False):
                raise ValueError(
                    "reviewed may only be sent as false -- an authoring tool "
                    "cannot attest to its own review; clear the flag by editing "
                    "the yaml or from the panel")
            #: **THE GATE'S VERDICT IS COMPUTED HERE, NOT ACCEPTED, AND NOT
            #: OPTIONAL.** opus-institutional-pilot: a reviewer opening the yaml
            #: cannot tell whether `separates` passed at save time or which
            #: diagnostics were even available -- and that stopped being
            #: hypothetical the same run, when a ClickHouse outage silently
            #: removed two checks from the report an author was reading.
            #:
            #: `leverage` in particular was computed and DISCARDED: it appears in
            #: none of the three corpora, while the brief and the axis report both
            #: told authors it "is recorded on the item". The design is
            #: record-it-never-chase-it and only the second half was built.
            #:
            #: Recomputed server-side from the same `words` the masses derive
            #: from, for the reason in this method's own docstring: a
            #: client-supplied `gap` disagreeing with the tags beside it would be
            #: undetectable and permanent.
            axis_rec = None
            try:
                ws = list(words.keys())
                a = _slot_axis(body.get("prompt"), body.get("naughty"),
                               body.get("nice"), ws, probs=words)
                sep = (a or {}).get("separates") or {}
                axis_rec = {
                    "separates": bool(sep.get("ok")),
                    "gap": round(float(sep.get("gap") or 0.0), 6),
                    "correct": int(sep.get("correct") or 0),
                    "total": int(sep.get("total") or 0),
                    "purity": round(float(a.get("purity") or 0.0), 6),
                    "defectors": list(a.get("defectors") or []),
                    #: Recorded, never surfaced to the author while deciding.
                    "leverage": (round(float(a["leverage"]), 6)
                                 if a.get("leverage") is not None else None),
                    #: **WHICH REFEREES ACTUALLY RAN.** A check that did not run
                    #: must not be reconstructible as a check that passed, and
                    #: after the fact the yaml is the only witness.
                    #: **WHAT THE AXIS FLAGGED, ON THE ITEM** (opus-inst-edulegal,
                    #: 2026-08-18). The brief tells an author to save through a
                    #: warning and say so IN THEIR REPORT -- which makes a chat
                    #: message the only record of a decision that lives in a yaml
                    #: forever. Its words: "if the rule matters enough to be in
                    #: the brief twice, `save` should write `flags` into the item."
                    "flags": list(a.get("flags") or []),
                    "checks_ran": sorted(
                        k for k in ("cross_corpus", "stability", "held_out")
                        if isinstance(a.get(k), dict) and not a[k].get("error")),
                }
            except Exception as e:
                axis_rec = {"error": "%s: %s" % (type(e).__name__, e)}
            item = build_item(
                body.get("prompt"), body.get("naughty"), body.get("nice"), words,
                provenance=body.get("provenance") or {},
                domain=(body.get("domain") or "").strip(),
                writer=(body.get("writer") or "slot-explorer").strip(),
                note=(body.get("note") or "").strip(),
                authored_by=(body.get("authored_by") or "").strip() or None,
                reviewed=rev, axis=axis_rec,
                untagged=body.get("untagged") or ())
            path, action = save_item(item, overwrite=bool(body.get("overwrite")),
                                     path=targets[tgt])
            return self._json(200, {"item_id": item["item_id"], "action": action,
                                    "path": path, "item": item})
        except FileExistsError as e:
            return self._json(409, {"error": str(e), "conflict": True})
        except ValueError as e:
            return self._json(400, {"error": str(e)})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._json(500, {"error": "%s: %s" % (type(e).__name__, e)})

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
        if payload is _SENT:
            return
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
                    #: **WHETHER THIS PROCESS IS RUNNING THE CODE ON DISK.** See
                    #: `_source_status`: the server cannot reload itself, so the
                    #: most it can do is refuse to look current when it is not.
                    "source": _source_status(),
                    "slot_enabled": _ALLOW_SLOT,
                    "slot_loaded": list(_SLOT_MODELS),
                    "slot_max": _SLOT_MAX,
                    "slot_ttl": _SLOT_TTL,
                    #: SERVED AS A CONSTANT, VERIFIED AT BOOT. The check reads
                    #: the whole roster, and /health is polled every 15s by an
                    #: open tab -- so the verification runs once in `serve()`
                    #: where a stale declaration stops the server, and this is
                    #: just the value.
                    "diagnostic_pair": list(_DIAGNOSTIC_PAIR),
                    #: **THE FLAG IS SERVED BECAUSE A FLAG NOTHING READS IS NOT
                    #: A FLAG.** It sat in `slots.py` unread for an hour while
                    #: the panel presented an untested-on-this-machine pair as
                    #: simply "declared" -- the same defect as the declared
                    #: constant nobody could reach. True means no `local_mps`
                    #: observation is booked and a load may fail after the
                    #: reader has waited for 38 GB.
                    "diagnostic_pair_provisional": _dp_provisional(),
                    #: SO THE CLIENT CAN SAY "loading" RATHER THAN "running".
                    #: A 6-second load and a 1-second expansion under one spinner
                    #: are indistinguishable to the user, and the 6-second one is
                    #: where they wonder whether it has hung.
                    "slot_idle": {m: round(_monotonic() - t, 1)
                                  for m, t in _SLOT_USED.items()}}
        if path == "/store/inventory":
            return _store_inventory()
        if path == "/roster":
            return _roster_summary()
        if path == "/slot/pairs":
            return _pairs()
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
        if path == "/cjk_boundary":
            st = _cjk_mask_status()
            return {"source": st["source"],
                    #: **`null` SOURCE MEANS "CANNOT TELL YOU", NOT "NONE
                    #: AFFECTED".** The client checks for the file's absence
                    #: explicitly rather than reading an empty list as a clean
                    #: bill of health -- the same distinction the stale-server
                    #: badge makes.
                    "affected": st["affected"], "clean": st["clean"],
                    "n_affected": len(st["affected"] or []),
                    "n_clean": len(st["clean"] or []),
                    "note": "models whose boundary_mask does not mark CJK "
                            "punctuation. On a CJK prompt, expand walks through "
                            "it and credits a word at more than one depth; "
                            "clean_surface strips the punctuation so the stored "
                            "surface looks correct. Magnitude is unmeasured at "
                            "roster scale: see docket [6435], [6437]."}
        if path == "/prompts":
            rows, computed = _prompt_rows()
            return {"n": len(rows), "computed_at": computed,
                    "ttl_seconds": _PROMPTS_TTL,
                    #: Prompts with cells that this table does NOT declare. The
                    #: panel says so, because a declared-only table read as the
                    #: corpus is the population defect one level up.
                    "n_measured_undeclared": _PROMPTS.get("undeclared"),
                    #: **THE WHOLE TABLE, UNCAPPED, AND THAT IS DELIBERATE.**
                    #: 4,484 rows is ~1 MB of JSON and the point of the panel is
                    #: to sort over all of it. A cap here would make every sort a
                    #: sort of an arbitrary window -- the windowed-view-beside-an
                    #: -unwindowed-statistic defect, with the sort as the
                    #: statistic.
                    "rows": rows}
        if path == "/prompt":
            rows, _ = _prompt_rows()
            text = one("text", "")
            #: MEMBERSHIP, as everywhere else: the text reaches a ClickHouse
            #: query, so it has to be one of the prompts the table declares.
            by = {r["prompt"]: r for r in rows}
            if text not in by:
                raise KeyError("no such prompt. Ask /prompts for the %d declared."
                               % len(by))
            from . import ch
            esc = text.replace("\\", "\\\\").replace("'", "\\'")
            per = ch.query(
                "SELECT mc.base AS base, mc.aligned AS aligned, "
                "mc.relation AS relation, mc.depth AS depth, "
                "mc.js_total AS js_total, mc.departed AS departed, "
                "mc.arrived AS arrived, mc.n_fall AS n_fall, mc.n_rise AS n_rise, "
                "mc.resid_base AS resid_base, mc.resid_aligned AS resid_aligned "
                "FROM {db}.movement_cells mc INNER JOIN {db}.endpoints e "
                "ON e.base = mc.base AND e.endpoint = mc.aligned "
                "WHERE mc.rule = 'canonical' AND mc.prompt = '" + esc + "' "
                "ORDER BY js_total DESC")
            movers = ch.query(
                "SELECT word, sum(delta) AS d, count() AS n "
                "FROM {db}.movement m INNER JOIN {db}.endpoints e "
                "ON e.base = m.base AND e.endpoint = m.aligned "
                "WHERE m.rule = 'canonical' AND m.prompt = '" + esc + "' "
                "GROUP BY word ORDER BY d DESC LIMIT 8")
            fallers = ch.query(
                "SELECT word, sum(delta) AS d, count() AS n "
                "FROM {db}.movement m INNER JOIN {db}.endpoints e "
                "ON e.base = m.base AND e.endpoint = m.aligned "
                "WHERE m.rule = 'canonical' AND m.prompt = '" + esc + "' "
                "GROUP BY word ORDER BY d ASC LIMIT 8")
            #: THE PARTNER, if this frame is half of a declared contrast. The
            #: `prompts` table carries `pair_id`/`pair_role`, so the partner is
            #: the OTHER row with the same `pair_id` -- looked up in the cached
            #: rows rather than re-queried.
            meta = by[text]
            partners = []
            if meta.get("pair_id"):
                partners = [
                    {k: r[k] for k in ("prompt", "pair_role", "domain",
                                       "js_median", "departed_median",
                                       "arrived_median", "n_pairs", "n_models")}
                    for r in rows
                    if r.get("pair_id") == meta["pair_id"] and r["prompt"] != text]
            return {"prompt": text, "meta": meta, "endpoints": per,
                    "top_risers": movers, "top_fallers": fallers,
                    "partners": partners,
                    #: Summed across endpoints, so it is a total and not a rate.
                    #: Said here because a reader will otherwise take it for a
                    #: per-pair number the same size as `departed_median`.
                    "movers_note": "delta summed over the %d endpoint pairs "
                                   "measured at this prompt" % len(per)}
        if path == "/pair_words":
            #: Every word this pair puts at this prompt, both arms and the
            #: delta. The grain `{db}.movement` already stores, so nothing is
            #: derived: `|delta|` is added by the CLIENT for sorting, because a
            #: column that is a function of another column in the same row is
            #: not a measurement and does not need a producer.
            rows, _ = _prompt_rows()
            text = one("text", "")
            if text not in {r["prompt"] for r in rows}:
                raise KeyError("no such prompt. Ask /prompts for the %d declared."
                               % len(rows))
            from . import ch
            base, aligned = one("base", ""), one("aligned", "")
            #: MEMBERSHIP IN THE DECLARED ENDPOINTS, not a free model string.
            #: The pair reaches a query, and an arbitrary (base, aligned) would
            #: also let a caller ask for a contrast the roster does not declare
            #: -- which is a population choice made by a URL.
            pairs = {(r["base"], r["endpoint"]) for r in
                     ch.query("SELECT base, endpoint FROM {db}.endpoints")}
            if (base, aligned) not in pairs:
                raise ValueError(
                    "%r -> %r is not a declared endpoint pair. Ask /prompt for "
                    "the pairs measured at this prompt." % (base, aligned))
            e = lambda x: x.replace("\\", "\\\\").replace("'", "\\'")
            words = ch.query(
                "SELECT word, p_base, p_aligned, delta, cls FROM {db}.movement "
                "WHERE rule = 'canonical' AND prompt = '" + e(text) + "' "
                "AND base = '" + e(base) + "' AND aligned = '" + e(aligned) + "' "
                "ORDER BY delta ASC")
            #: THE RESIDUALS TRAVEL WITH THE WORDS. Both arms are truncated at
            #: theta and by different amounts, so a table of visible words
            #: without the invisible mass beside it invites the reader to treat
            #: the columns as summing to 1. They do not, and the gap is the
            #: aperture this campaign keeps paying attention to.
            cells = ch.query(
                "SELECT model, total, n_words FROM {db}.twp_cells WHERE prompt = '"
                + e(text) + "' AND model IN ('" + e(base) + "','" + e(aligned) + "')")
            resid = {c["model"]: c for c in cells}
            return {"prompt": text, "base": base, "aligned": aligned,
                    "n_words": len(words), "words": words,
                    "residual_base": (resid.get(base) or {}).get("total"),
                    "residual_aligned": (resid.get(aligned) or {}).get("total"),
                    "sum_p_base": sum(w["p_base"] for w in words),
                    "sum_p_aligned": sum(w["p_aligned"] for w in words)}
        if path == "/plots":
            specs = _plot_specs()
            return {"plots": [dict(sp, error=sp.get("error"))
                              for sp, _ in specs.values()]}
        if path == "/plot/prompts":
            #: FILTERED IN PYTHON over a cached set -- see `_plot_prompt_set`.
            allp = _plot_prompt_set()
            needle = (one("q") or "").strip().lower()
            hits = [x for x in allp if needle in x.lower()] if needle else allp
            lim = _int(one("limit"), 200, 1, 2000)
            return {"n_total": len(allp), "n_matched": len(hits),
                    "limit": lim, "prompts": hits[:lim]}
        if path == "/plot/render":
            specs = _plot_specs()
            pid = one("plot", "")
            if pid not in specs:
                raise KeyError("no plot %r. Ask /plots for the %d available."
                               % (pid, len(specs)))
            spec, mod = specs[pid]
            if mod is None or not spec.get("has_render"):
                raise ValueError("%r declares no `render`; it is CLI-only" % pid)
            if spec.get("missing_requires"):
                raise ValueError(
                    "%r needs %s, which this interpreter does not have. Install "
                    "with `pip install -e '.[plots]'` in the venv running this "
                    "server." % (pid, ", ".join(spec["missing_requires"])))
            kw = _plot_coerce(spec, one)
            #: SERIALISED. A render is a ClickHouse read plus a matplotlib-backed
            #: draw, and plotnine's backend is not reentrant across threads --
            #: the same reason `_SLOT_LOCK` exists for `_BATCH`, one level up.
            with _PLOT_LOCK:
                t0 = _monotonic()
                out, info = mod.render(**kw)
                took = _monotonic() - t0
            return {"plot": pid, "experiment": spec["experiment"],
                    "params": kw, "seconds": round(took, 2),
                    "figure": os.path.basename(out),
                    #: SERVER-RELATIVE, and named so. A client that mounts this
                    #: API under a prefix -- the dev server proxies `/api` --
                    #: must build its own URL from `experiment` and `figure`.
                    #: Handing this string straight to an `<img src>` is how the
                    #: first version drew a broken image beside a successful
                    #: render and correct numbers.
                    "url_server_relative": "/experiment/figure?id=%s&name=%s"
                                           % (spec["experiment"], os.path.basename(out)),
                    "info": info}
        if path == "/experiment/figure":
            #: **VALIDATED BY MEMBERSHIP IN THE MANIFEST THIS PROCESS WALKED,
            #: never by path.** The name has to be in the `figures` list the
            #: walk built off disk, which is what makes `../../etc/passwd`
            #: uninteresting rather than filtered: it is simply not in the set.
            #: Same rule the result files follow.
            qs = _manifest()
            eid = one("id", "")
            if eid not in qs:
                raise KeyError("no experiment %r. Ask /experiments." % eid)
            #: **NOT `q`.** `one` is a closure over the enclosing `q`, the parsed
            #: QUERY dict, so rebinding `q` to the manifest entry silently
            #: re-points every later `one(...)` at the wrong mapping. The first
            #: draft did exactly that and `one("name")` returned `"p"` -- the
            #: first character of the entry's `name` field, because `[0]` of a
            #: string is a character and nothing raises. It read as a missing
            #: figure rather than as a shadowed variable.
            entry = qs[eid]
            name = one("name", "")
            if name not in entry["figures"]:
                raise ValueError(
                    "%r has no figure %r. It has: %s"
                    % (eid, name, ", ".join(entry["figures"]) or "none"))
            target = os.path.join(entry["_dir"], "figures", name)
            ctype = {".png": "image/png", ".svg": "image/svg+xml",
                     ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                     ".pdf": "application/pdf",
                     ".webp": "image/webp"}.get(
                         os.path.splitext(name)[1].lower(),
                         "application/octet-stream")
            with open(target, "rb") as fh:
                body = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            #: A figure is a file on disk that changes only when a producer is
            #: re-run, and these are 300 dpi PNGs of a megabyte or so. Letting
            #: the browser keep one for a minute is the difference between a
            #: panel that flickers on every click and one that does not.
            self.send_header("Cache-Control", "max-age=60")
            self.end_headers()
            self.wfile.write(body)
            #: SENTINEL: `_route` returning a payload would double-write.
            return _SENT
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
        if path == "/slot/saved":
            #: **A WRITE NOBODY CAN READ BACK IS NOT A SAVE, IT IS A DISCARD
            #: WITH A CONFIRMATION MESSAGE.** The button is only trustworthy if
            #: the panel can show what is already stored, so this ships with it
            #: rather than after it.
            from .slots import SLOT_DIR, SLOT_YAML, saved_items
            items = saved_items()
            return {"dir": SLOT_DIR, "file": SLOT_YAML, "n": len(items),
                    #: The stamp is dropped from the LISTING only -- it is the
                    #: bulkiest field and the list exists to answer "what have I
                    #: made", not "how was it screened". It is in the file.
                    "items": [{k: v for k, v in d.items() if k != "screened_by"}
                              for d in items]}
        if path == "/slot/domains":
            #: **THE ZEROS ARE THE PAYLOAD.** RH, 2026-08-17: "show how many
            #: prompts we currently have per domain to help me organise making a
            #: balanced set." A `GROUP BY` answers the first clause and not the
            #: second -- it cannot emit a row for a domain with no items, and a
            #: domain at zero is the one an author building a balanced set most
            #: needs to see. `slots.domain_census` unions the suggestion list in
            #: so an unused domain reads as 0 rather than as absent.
            #:
            #: **AND IT RETURNS THE DOMAIN LIST**, which the client had its own
            #: copy of. Two hand-maintained lists of the same ten strings drift,
            #: and the drift is invisible: an author picks from the client's
            #: datalist while the census groups by the server's.
            from .slots import domain_census
            return domain_census()
        if path == "/slot/item_id":
            #: **THE ID IS DERIVED HERE AND NOT IN THE CLIENT.** It is a pure
            #: function of one string, and that is the argument for not letting
            #: the client have it: a JavaScript port gets the character classes
            #: wrong for free (Python's `\w` is Unicode-aware, JavaScript's is
            #: ASCII-only) and would now also need a matching sha256 over the
            #: same byte encoding. Two ways to diverge silently, producing ids
            #: that look right and do not match what is written.
            #:
            #: **`nice` AND `naughty` ARE GONE.** The id is a function of the
            #: PROMPT ALONE since 2026-08-17; see `slots.item_id`. They are still
            #: accepted and ignored, with a note in the payload, because the
            #: alternative is a 400 for a caller whose only crime is being the
            #: version of the app that was open when the server restarted.
            from .slots import item_id
            prompt = one("prompt", "")
            if not prompt.strip():
                raise ValueError("prompt required")
            out = {"item_id": item_id(prompt, variant=one("variant") or None)}
            if one("nice") or one("naughty"):
                out["note"] = ("nice/naughty are ignored: the id is a function "
                               "of the prompt alone since 2026-08-17, because "
                               "the pole words made it unstable under re-screening "
                               "and let two items swap ids")
            return out
        if path == "/slot":
            if not _ALLOW_SLOT:
                raise ValueError("this server was started with --no-slot")
            prompt = one("prompt", "")
            if not prompt.strip():
                raise ValueError("prompt required")
            #: **A DECLARED PAIR, NOT A MODEL LIST** (RH, 2026-08-17). The
            #: panel pools base+endpoint and shows no movement, so pooling is a
            #: property of the INSTRUMENT rather than a per-query choice. A free
            #: model list let an author screen on one arm and not know it, which
            #: is the failure the pooled design exists to prevent: the arrival
            #: side of a displacement often does not exist in the base at all.
            #: **A RETIRED PARAMETER IS REFUSED, NOT IGNORED.** `model=` used to
            #: take a comma-separated pool. Silently dropping it would hand the
            #: caller the DEFAULT pair while they believed they had named their
            #: own -- which is precisely the archive's failure, where a client
            #: default silently overrode the server's and the app ran a
            #: population the server's own test never exercised.
            if one("model"):
                raise ValueError(
                    "`model=` was replaced by `pair=<base id>`. Screening pools "
                    "a declared (base, endpoint) pair, so naming loose models is "
                    "no longer possible; ask /slot/pairs for the 50 available.")
            base = one("pair") or DEFAULT_PAIR_BASE
            kk = _int(one("k"), 50, 5, 500)
            #: `cached` is reported so a reader can tell a served pool from a
            #: computed one. A cache whose hits are indistinguishable from misses
            #: cannot be audited, and this one sits under a measurement.
            payload, was_hit = _screen_cached(
                prompt, base, kk, lambda: _slot(prompt, base, kk))
            if isinstance(payload, dict):
                payload = dict(payload, cached=bool(was_hit))
            return payload
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
        #: Needed for the POST: a JSON content-type makes it non-simple, so the
        #: browser preflights, and a preflight refused reads to the app as the
        #: endpoint being down.
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        #: **DO NOT INSERT ANYTHING BETWEEN `end_headers()` AND THIS LINE.**
        #: On 2026-08-16 a CORS edit appended a new method right here, which put
        #: `do_OPTIONS` between the headers and the write. `_json` then ended at
        #: `end_headers()` and EVERY response in the server -- GET and POST alike
        #: -- returned a correct Content-Length and an empty body.
        #:
        #: It presented as a POST-only fault for an hour because the GET checks
        #: were piped to /dev/null and the one visible symptom, a JSON decode
        #: error on /health, got blamed on a dead server. The server was fine.
        #: **A response with valid headers and no body reads as a transport
        #: problem, which is the most expensive thing it could have looked like.**
        self.wfile.write(body)

    def do_OPTIONS(self):
        """The CORS preflight. 204, and NO BODY -- a 204 must not carry one.

        Not routed through `_json`, which always writes a body: sending one here
        is malformed, and reusing the helper is how it would happen.
        """
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

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


def _dp_provisional():
    """Whether the declared pair is unverified on THIS machine.

    Read from `slots` on every call rather than captured at boot: it flips when
    a seat books an observation, and a value frozen at start-up would keep
    warning after the thing it warns about was fixed.
    """
    try:
        from .slots import DIAGNOSTIC_PAIR_PROVISIONAL
        return bool(DIAGNOSTIC_PAIR_PROVISIONAL)
    except Exception:
        #: Unknown reads as PROVISIONAL. An import failure must not silently
        #: promote an unverified pair to verified.
        return True


def _db_name():
    try:
        from . import ch
        return ch.DB
    except Exception as e:
        return "unavailable: %s" % e


def serve(port=8431, host="127.0.0.1", slot=True):
    global _BOOTED_AT
    import datetime
    _BOOTED_AT = datetime.datetime.now().isoformat(timespec="seconds")
    global _ALLOW_SLOT, _DIAGNOSTIC_PAIR
    _ALLOW_SLOT = slot
    #: **VERIFIED AT BOOT, NOT PER REQUEST.** `check_diagnostic_pair` reads the
    #: whole roster; /health is polled every 15 s by an open tab. Once here is
    #: the right frequency for a fact that only changes when the roster does.
    #:
    #: A FAILURE IS REPORTED AND DOES NOT STOP THE SERVER. Every other route --
    #: the register, the roster, the result grains -- is unaffected by a
    #: diagnostic pair that has drifted into a population, and refusing to serve
    #: a markdown reader because of it would be the wrong trade. `_DIAGNOSTIC_PAIR`
    #: stays empty, so nothing can quietly use an unverified pair.
    try:
        from .slots import check_diagnostic_pair
        _DIAGNOSTIC_PAIR = check_diagnostic_pair()
        _dp_note = "%s -> %s" % tuple(m.split("/")[-1] for m in _DIAGNOSTIC_PAIR)
    except Exception as e:                                     # noqa: BLE001
        _DIAGNOSTIC_PAIR = ()
        _dp_note = "UNAVAILABLE -- %s: %s" % (type(e).__name__, str(e)[:150])
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
    say("  diagnostic  %s" % _dp_note)
    if slot:
        say("  slot        lazy: 0 resident until a /slot call. At most %d, "
            "released after %.0fs idle" % (_SLOT_MAX, _SLOT_TTL))
        #: DAEMON, so a Ctrl-C is not held open by the reaper. Started only when
        #: slot is enabled -- there is nothing to reap under `--no-slot`, and a
        #: thread that exists to manage a thing that cannot happen is a thread
        #: someone later reads as evidence that it can.
        threading.Thread(target=_reap_idle, daemon=True,
                         name="slot-reaper").start()
    else:
        say("  slot        REFUSED (--no-slot); no route here can load weights")
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
