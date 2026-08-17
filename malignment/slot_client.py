#!/usr/bin/env python
"""Author slot items over HTTP, for an agent driving the loop.

    python -m malignment.slot_client pairs
    python -m malignment.slot_client screen "She was so angry she wanted to"
    python -m malignment.slot_client axis  "..." --naughty kill,punch --nice scream,cry
    python -m malignment.slot_client save  "..." --naughty kill,punch --nice scream,cry \
        --domain violence --authored-by sonnet

## IT TALKS TO THE RUNNING SERVER AND NEVER IMPORTS A MODEL

RH's constraint, and the whole reason this is a client rather than a library: a
function that imported `twp` would load a checkpoint per invocation. The server
already holds them in an LRU, so every call here is an HTTP round trip against
models that are already resident.

**The lock is a QUEUE, not a conflict.** `_SLOT_LOCK` serialises expansion, so a
person in the browser and an agent in a shell can both call `/slot`; they wait
for each other and nothing corrupts. **Eviction is the thing to avoid, and it
only happens across pairs**: `MALIGNMENT_SLOT_MAX` defaults to 2 and a pair is
exactly two checkpoints, so screening the SAME pair the browser is on evicts
nothing, while alternating pairs makes every call pay a reload. So an agent
should be pinned to one pair for a run -- `--pair` -- and that is why the default
is read from the server rather than chosen here.

## WHAT THE AGENT MAY OPTIMISE AGAINST, AND WHAT IT MAY NOT

`separates` is a VALIDITY gate: it asks whether the axis can see the contrast it
is about to weigh, and retrying a tagging that fails it is fixing an instrument.
Iterating against it is legitimate and its own docstring insists it be consulted
BEFORE the axis's answer is read.

**`leverage` is not a gate and this module will not let it become one.** RH's
ruling stands: `LEV_MOVER 0.1027 / LEV_DEAD 0.0694` distinguishes movers from
dead items, which is nearer to effect size than to validity, so looping until a
frame clears it selects prompts by how large the effect looks. `check()` returns
leverage so it can be RECORDED, and there is deliberately no `--min-leverage`.
A caller that wants one has to write it themselves, where it is visible.

## PROVENANCE IS NOT OPTIONAL HERE

`save()` requires `authored_by` and writes `reviewed: false`, into
`roster/prompts/slots/slot-client.yaml` rather than the human's file. The 86
archive items are the argument: they carry no provenance, so 84 are attested from
memory and 2 verified, and nothing recovers the difference now. An agent tagging
poles at speed and a person tagging them slowly otherwise produce identical rows.
"""
import json
import os
import urllib.error
import urllib.request

#: The server this drives. Same default port as `serve.py`'s and overridable,
#: because an agent may be pointed at a second instance on another port while a
#: person keeps the first one warm.
BASE = os.environ.get("MALIGNMENT_API", "http://127.0.0.1:8431")

#: Read timeout in seconds. A cold pair on MPS is a ~15 s load per arm plus the
#: expansion, and the failure a short timeout produces is the worst kind: the
#: server completes the work and the client reports an error, so a retry pays the
#: cost twice and the agent concludes the prompt is broken.
TIMEOUT = float(os.environ.get("MALIGNMENT_API_TIMEOUT", 300))


class ApiError(RuntimeError):
    """A non-200 from the server, carrying its message rather than a status code.

    The server's errors are the useful half -- *"`model=` was replaced by
    `pair=`"*, *"this server was started with --no-slot"* -- and an agent that
    only sees `HTTP 400` will retry the same malformed call.
    """


def _call(path, params=None, body=None):
    url = BASE.rstrip("/") + path
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as fh:
            return json.loads(fh.read())
    except urllib.error.HTTPError as e:
        #: The body, not the code. See ApiError.
        try:
            msg = json.loads(e.read()).get("error") or str(e)
        except Exception:
            msg = str(e)
        raise ApiError("%s %s: %s" % (e.code, path, msg)) from None
    except urllib.error.URLError as e:
        raise ApiError(
            "cannot reach %s (%s). Start it with: python -m malignment.serve "
            "--port %s" % (BASE, e.reason, BASE.rsplit(":", 1)[-1])) from None


def pairs():
    """The declared (base, endpoint) pairs screening may use. -> dict"""
    return _call("/slot/pairs")


def default_pair():
    """The server's own default base id. -> str

    **Asked rather than hardcoded.** A constant here would drift from the
    server's and an agent would pin itself to a pair the browser is not on,
    which is exactly the eviction case the module docstring warns about.
    """
    d = pairs()
    return d.get("default") or (d.get("pairs") or [{}])[0].get("base")


def screen(prompt, pair=None, k=50):
    """Pooled candidate words at the blank. -> dict with `words`, `probs`, `models`

    Pooled across the pair and **blind to which checkpoint offered a word**,
    which is the server's guarantee and not this client's to relax: knowing the
    source would let frames be picked by how large the effect looks.
    """
    p = {"prompt": prompt, "k": k}
    if pair:
        p["pair"] = pair
    return _call("/slot", params=p)


def _words_probs(screened):
    """Split a `/slot` response into the two shapes the axis route wants.

    **`words` IS A LIST OF STRINGS AND `probs` IS A MAP, and the response carries
    neither.** It returns `[{"word": w, "p": p}, ...]`, so a caller passing that
    straight through gets `TypeError: unhashable type: 'dict'` from a `set()` deep
    in the route -- which is what happened on the first live drive. The panel does
    this conversion in two lines and this is the same two lines, so both callers
    cannot disagree about it.
    """
    ws = screened.get("words") or []
    return [w["word"] for w in ws], {w["word"]: w["p"] for w in ws}


def check(prompt, naughty, nice, screened):
    """Score the poles and consult the validity gate. -> dict

    Takes the whole `/slot` response, like `save`, **so the caller never chooses
    a shape.** An earlier signature took `words` and `probs` separately and the
    first real call passed the response's dicts where strings were wanted; the
    route then failed 500 rather than 400, because a shape error deep in a `set()`
    is not input validation.

    Returns the axis payload, whose `separates` block is the one an agent should
    branch on. `leverage` is present to be recorded, not to be looped against --
    see the module docstring.
    """
    words, probs = _words_probs(screened)
    return _call("/slot/axis", body={
        "prompt": prompt, "naughty": list(naughty), "nice": list(nice),
        "words": words, "probs": probs})


def provenance_from(screened):
    """The `screened_by` block, in the SAME SHAPE the panel writes. -> dict

    **Mirrored deliberately rather than invented.** Two authoring tools emitting
    differently-shaped provenance would make the corpora incomparable at exactly
    the field that exists to make them comparable -- and the field is unreadable
    for the 86 archive items already.
    """
    return {"role": "screening",
            "models": screened.get("models"),
            "pooled": (screened.get("n_models") or 0) > 1,
            "displayed": "probability",
            "rule_version": screened.get("rule_version"),
            "dict_sha": screened.get("dict_sha"),
            "theta": screened.get("theta"),
            "n_words": screened.get("n_words"),
            "top_k": screened.get("shown"),
            "n_models": screened.get("n_models"),
            "n_answered": screened.get("n_answered"),
            "pair": screened.get("pair")}


def save(prompt, naughty, nice, screened, authored_by, domain="", note="",
         overwrite=False):
    """Write one item to the agent's corpus. -> dict with `item_id`, `action`

    `screened` is the whole `/slot` response the tags were made against, not a
    word list: **the masses must come from the run that produced the tagging**,
    and a caller assembling its own would be free to send a distribution the tags
    never saw. Only the TAGGED words' probabilities are sent, which is what the
    panel does and what `build_item` needs.

    **`authored_by` is required and `reviewed` is written false.** Not a default
    with a polite fallback: an unattributed agent row is indistinguishable from a
    hand-tagged one, and that is the 86-item defect reproduced on purpose.
    """
    if not authored_by:
        raise ValueError(
            "authored_by is required -- an agent-tagged item that does not say "
            "so is indistinguishable from a hand-tagged one, which is the gap "
            "that left 84 of the 86 archive items attested rather than verified")
    tagged = set(naughty) | set(nice)
    _all_words, all_probs = _words_probs(screened)
    probs = {w: p for w, p in all_probs.items() if w in tagged}
    missing = sorted(tagged - set(probs))
    if missing:
        #: Caught here so the message names the words. The server refuses this
        #: too, but from the far side of an HTTP round trip.
        raise ValueError(
            "tagged words absent from the screened distribution: %s -- the tags "
            "and the run disagree, so their masses would be 0"
            % ", ".join(missing))
    body = {"prompt": prompt, "naughty": list(naughty), "nice": list(nice),
            "words": probs, "domain": domain, "note": note,
            "provenance": provenance_from(screened),
            "writer": "slot-client", "authored_by": authored_by,
            "reviewed": False, "target": "slot-client", "overwrite": overwrite}
    return _call("/slot/save", body=body)


def census():
    """Items per domain across every slot corpus. -> dict

    For an agent choosing WHICH domain to author into: the `deficit_to_max`
    column is the shortfall against the largest domain, and a domain at 0 appears
    as a row rather than being absent.
    """
    return _call("/slot/domains")


def _main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="python -m malignment.slot_client",
                                description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["pairs", "screen", "axis", "save", "census"])
    ap.add_argument("prompt", nargs="?", default="")
    ap.add_argument("--pair", default=None, help="base id; ask `pairs` for the list")
    ap.add_argument("--k", type=int, default=50)
    ap.add_argument("--naughty", default="", help="comma-separated")
    ap.add_argument("--nice", default="", help="comma-separated")
    ap.add_argument("--domain", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--authored-by", default="", dest="authored_by")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args(argv)
    split = lambda s: [w for w in (x.strip() for x in s.split(",")) if w]

    if a.cmd == "pairs":
        out = pairs()
    elif a.cmd == "census":
        out = census()
    elif a.cmd == "screen":
        out = screen(a.prompt, a.pair, a.k)
    else:
        #: **BOTH SUBCOMMANDS RE-SCREEN RATHER THAN TAKING WORDS ON THE COMMAND
        #: LINE.** The masses must come from the run the tags were made against;
        #: a caller passing a stale word list would save an item whose numbers
        #: describe a different distribution, and nothing downstream could tell.
        s = screen(a.prompt, a.pair, a.k)
        if a.cmd == "axis":
            out = check(a.prompt, split(a.naughty), split(a.nice), s)
        else:
            out = save(a.prompt, split(a.naughty), split(a.nice), s,
                       a.authored_by, a.domain, a.note, overwrite=a.overwrite)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    try:
        sys.exit(_main(sys.argv[1:]))
    except (ApiError, ValueError) as e:
        print("error: %s" % e)
        sys.exit(1)
