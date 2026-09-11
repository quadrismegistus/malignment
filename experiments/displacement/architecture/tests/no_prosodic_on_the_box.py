"""GATE: the box's produce path must run with `import prosodic` IMPOSSIBLE.

    uv run python experiments/displacement/architecture/tests/no_prosodic_on_the_box.py

RH, 2026-09-11: *"Let's not run prosodic on the cloud though right? We can do the
prosodic analysis after we have the data."*

**A `--with prosodic`-free environment does NOT test this and I watched it fail
to.** `uv run --with transformers --with torch` still resolves the project venv,
where prosodic is pinned at the paper's commit, so the produce path imported it
happily and the run "passed" having proved nothing. The smoke said so itself.

This blocks the name at `builtins.__import__` instead, so the assertion is about
the CODE and not about whichever interpreter happened to be reachable. It is the
campaign's own rule: a checker is not a checker until you have watched it refuse.
**WATCHED IT REFUSE, and the refusal is not the one I predicted.** Dropping
`--produce-only` under this blocker does NOT raise ImportError: `rime_key`
wraps its `import prosodic` in `except Exception: key = None`, so the block is
swallowed exactly as a genuinely missing install would be. What fires is the
smoke's own assertion 0 --

    0 rime_key resolves (prosodic present)   0/6 FAIL -- every class share
                                             below is a FALSE ZERO

-- which is the whole reason that assertion exists. A guard that eats its own
exception cannot be tested by expecting one; it has to be tested by checking
what it produces. The produce path is clean either way, which is the claim.
"""
import sys, builtins
_real = builtins.__import__
def _blocked(name, *a, **k):
    if name == "prosodic" or name.startswith("prosodic."):
        raise ImportError("prosodic is BLOCKED: the box must not need it")
    return _real(name, *a, **k)
builtins.__import__ = _blocked
sys.argv = ["rhyme_smoke.py", "--n", "9", "--produce-only", "--out", "/tmp/box_path.jsonl"]
sys.path.insert(0, "/Users/rj416/github/malignment/experiments/displacement/architecture")
import rhyme_smoke
raise SystemExit(rhyme_smoke.main())
