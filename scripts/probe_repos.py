#!/usr/bin/env python
"""Is the repo REACHABLE? Measured against the HF API, anonymously and with the token.

    python scripts/probe_repos.py                 # dry run, prints the table
    python scripts/probe_repos.py --write         # -> measurements.json `repos`

## WHY THIS IS A SECTION OF ITS OWN

`observations.json` is keyed on (model x environment) because whether a model
LOADS is a property of the pair. **Whether its repo still exists is not.** A
404 is true on every box, in every venv, forever, and writing it as an
observation would state a global fact in a local shape.

It had no home at all: the only record that a repo was dead lived in
`model_requirements.json`'s `blocked_reason`, in the READ-ONLY archive, as five
hand-typed strings with no producer. So the fact could not be refreshed, and a
repo that came back would have stayed "dead" until someone noticed.

## THE STATUS CODE ON /api/models IS NOT THE GATE, AND THE FIRST DRAFT BELIEVED IT

The metadata endpoint returns **200 for gated repos**. Measured 2026-08-22:

    google/gemma-2-9b               anon 200, gated=manual
    inceptionai/jais-family-6p7b    anon 200, gated=auto
    Zyphra/Zamba2-7B                anon 200, gated=auto

so a probe reading only the code called all three PUBLIC -- and the first draft
of this file did exactly that, reporting 159/160 public and would have sent a
tokenless box after three repos that need one. Gating bites on FILE ACCESS, not
on the card.

Two things are therefore read, and they answer different questions:

    body["gated"]     the repo's DECLARED policy: false | "auto" | "manual"
    HEAD on
    resolve/main/     what a BOX actually gets, anonymously and with our token.
    config.json       This is the operational fact; the flag above is the
                      explanation for it.

## ANONYMOUS **AND** TOKENED, BECAUSE THE PAIR IS THE FACT

    file anon 200                     public
    file anon 401/403 + token 200     GATED, and we hold access -- usable, and
                                      the fleet MUST ship the token
    file anon 401/403 + token 401/403 GATED AND REFUSED -- RH applied for
                                      gpt-sw3 and was turned down; no fleet
                                      fixes that
    404 either way                    REPO DEAD -- `mosaicml/mpt-7b` is 401
                                      anonymously and 404 WITH the token

Collapsing gated-and-held into "gated" is what makes a box fail at 3am for want
of a token it was never told to carry, and collapsing gated-and-refused into
"gated" is what makes someone retry a permanent refusal every fleet.

## THE TOKEN IS A HEADER AND NOTHING ELSE

Read from `~/.cache/huggingface/token`, sent as `Authorization: Bearer`. Never
placed in argv, never printed, never written to the output. Provisioning
scripts that carried an inline token were archived and thereby published once;
that is in `provisioning_lessons`.
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys
import urllib.error
import urllib.request
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

MEAS = os.path.join(ROOT, "roster", "models", "measurements.json")
API = "https://huggingface.co/api/models/%s"


def _token():
    p = os.path.expanduser("~/.cache/huggingface/token")
    return open(p).read().strip() if os.path.exists(p) else None


#: A revision is not a repo. `HuggingFaceTB/SmolLM3-3B-checkpoints@it-soup-APO`
#: is a branch of a repo, and asking the API for it 401s in a way that reads as
#: gating. Strip it before probing and record the repo's answer.
def repo_of(model_id):
    return model_id.split("@")[0].split("/at/")[0]


def _meta(model, token=None):
    """(status, gated_flag). `gated` is the repo's DECLARED policy."""
    req = urllib.request.Request(API % model)
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.load(r).get("gated")
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:                                            # noqa: BLE001
        return None, None


def _file(model, token=None):
    """What a BOX gets. HEAD on config.json is the cheapest real download."""
    url = "https://huggingface.co/%s/resolve/main/config.json" % model
    req = urllib.request.Request(url, method="HEAD")
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:                                            # noqa: BLE001
        return None


def classify(api_tok, f_anon, f_tok, gated):
    """(state, note). EXISTENCE from the API, ACCESS from the file, gated explains.

    **THREE QUESTIONS, AND ONE ANSWER CANNOT CARRY THEM.** Does the repo exist;
    does `main` hold a model; may we download it. Collapsing the first two is
    what made the first draft call `SmolLM3-3B-checkpoints` DEAD: the repo is
    alive and public, and its `main` branch holds exactly `.gitattributes` and
    `README.md` -- the checkpoints live on 133 BRANCHES. Anything resolving that
    id without a revision gets no model at all, which is a revision trap, not a
    dead repo, and the two want opposite responses.
    """
    if api_tok in (401, 403, 404) or (f_tok == 404 and api_tok != 200):
        return "dead", ("API %s with our token -- the id does not resolve"
                        % api_tok)
    if f_tok == 404 and api_tok == 200:
        return "revision_required", (
            "repo is alive but main/config.json 404s -- main carries no model. "
            "PIN A REVISION; resolving this id bare gets nothing.")
    if f_anon == 200:
        return "public", "gated=%s" % gated
    if f_anon in (401, 403):
        if f_tok == 200:
            return "gated_held", ("gated=%s; anonymous %s, 200 with our token -- "
                                  "THE BOX MUST CARRY IT" % (gated, f_anon))
        if f_tok in (401, 403):
            return "gated_refused", ("gated=%s; %s even with our token -- access "
                                     "is not ours to grant" % (gated, f_tok))
        return "gated_unknown", "gated=%s; token request inconclusive" % gated
    return "unknown", "anon=%s token=%s gated=%s" % (f_anon, f_tok, gated)


def probe(models, token, workers=12):
    def one(m):
        repo = repo_of(m)
        api, gated = _meta(repo, token)
        fa = _file(repo)
        ft = _file(repo, token) if fa != 200 else 200
        state, note = classify(api, fa, ft, gated)
        return m, OrderedDict([("repo", repo), ("gated", gated),
                               ("api_token", api),
                               ("file_anon", fa), ("file_token", ft),
                               ("state", state), ("note", note)])
    out = OrderedDict()
    with cf.ThreadPoolExecutor(workers) as ex:
        for m, rec in ex.map(one, models):
            out[m] = rec
    return OrderedDict(sorted(out.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--models", nargs="*", default=None)
    a = ap.parse_args()
    import yaml
    nodes = yaml.safe_load(open(os.path.join(ROOT, "roster", "models",
                                             "models.yaml")))["nodes"]
    models = a.models or sorted(nodes)
    token = _token()
    if not token:
        print("NOTE no HF token found -- gated_held and gated_refused cannot be "
              "distinguished, and every gated repo will read gated_unknown.")
    res = probe(models, token)
    by = {}
    for m, r in res.items():
        by.setdefault(r["state"], []).append(m)
    #: **ITERATE THE STATES FOUND, NEVER A LIST OF THE STATES EXPECTED.** This
    #: was a fixed tuple and `revision_required` was not in it, so two models
    #: vanished from the report while sitting correctly in the output file --
    #: 147 + 11 printed against 160 probed, and the only clue was arithmetic
    #: nobody does. A category the display cannot name reads as a category that
    #: does not occur.
    order = ["public", "gated_held", "gated_refused", "revision_required",
             "dead", "gated_unknown", "unknown"]
    for state in order + sorted(set(by) - set(order)):
        ms = by.get(state) or []
        if not ms:
            continue
        print("%-16s %3d" % (state, len(ms)))
        if state != "public":
            for m in ms:
                print("      %-52s %s" % (m, res[m]["note"][:44]))
    if not a.write:
        print("\nDRY RUN -- pass --write to store in measurements.json `repos`.")
        return 0
    doc = json.load(open(MEAS), object_pairs_hook=OrderedDict)
    doc["sections"]["repos"] = OrderedDict([
        ("_why", "Repo reachability is a property of the REPO, true on every box "
                 "forever, so it is not an (model x environment) observation. "
                 "Anonymous AND tokened, because the pair distinguishes "
                 "gated-and-held from gated-and-refused, and only the second is "
                 "permanent."),
        ("measured_by", "scripts/probe_repos.py"),
        ("n", len(res)),
        ("models", res),
    ])
    with open(MEAS, "w") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("\nwrote `repos` for %d models to %s" % (len(res), MEAS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
