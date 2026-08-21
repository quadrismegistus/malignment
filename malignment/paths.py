"""Where the repo root is, without any caller encoding how deep it sits.

    from malignment.paths import repo_root, REPO

## WHY THIS EXISTS

Sixteen producers computed the root as `os.path.dirname(os.path.dirname(HERE))`,
which is correct for `experiments/<question>/` and wrong for
`experiments/<subject>/<question>/`. Depth-2 folders already carry a third
`dirname`, so the repo held two conventions and each was right for exactly the
place it was written.

**THE FAILURE IS SILENT, WHICH IS WHY THIS IS A MODULE AND NOT A THIRD
`dirname`.** `REPO` is not only fed to `sys.path`; it builds real paths:

    glob.glob(os.path.join(REPO, "roster", "prompts", "slots", "*.yaml"))
    os.path.join(REPO, "lexicons", "norms")

A wrong root makes that glob resolve to a directory that does not exist, and a
glob that resolves nowhere returns `[]`. Measured before this was written: the
correct root globs 4 yaml files, a root one level short globs 0 -- with no
exception, no warning, and a producer that reports zero prompts instead of
failing. The `sys.path.insert` goes quiet in the same move, because `malignment`
is installed in the venv and imports fine without it.

So this function REFUSES rather than returning a plausible path. A root that does
not carry the repo's markers is not a root, and finding that out at import time
is worth more than every caller remembering its own depth.

## The markers

`pyproject.toml` AND `roster/` AND `malignment/` together, not any one of them:
a lone `pyproject.toml` is the sort of thing a stray venv or a nested package
brings with it, and the point is to identify THIS repo rather than a Python
project.
"""

import os

_MARKERS = ("pyproject.toml", "roster", "malignment")


def repo_root(start=None):
    """The repo root, found by walking up from `malignment` itself.

    Independent of the CALLER's depth by construction: it starts from this
    module's own location, so a producer at any level under `experiments/` gets
    the same answer and none of them has to know where it lives.
    """
    here = os.path.dirname(os.path.abspath(start or __file__))
    d = here
    while True:
        if all(os.path.exists(os.path.join(d, m)) for m in _MARKERS):
            return d
        up = os.path.dirname(d)
        if up == d:
            raise RuntimeError(
                "no repo root above %r: none of its parents carries all of %s. "
                "Refusing to return a plausible path -- a wrong root makes every "
                "glob under it return [] instead of raising."
                % (here, ", ".join(_MARKERS)))
        d = up


REPO = repo_root()
