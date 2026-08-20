#!/usr/bin/env python3
"""Refuse to commit a file over a size cap. Run against the INDEX, before committing.

    python scripts/check_staged_size.py                 # this repo, 50 MB
    python scripts/check_staged_size.py --repo ~/github/malign-logits
    python scripts/check_staged_size.py --cap 20 --quiet

Exit 0 when every staged blob is under the cap, 1 when any is over, so it chains:

    git add <paths> && python scripts/check_staged_size.py && git commit -F msg -- <paths>

## Why it measures the BLOB and not the file on disk

The first version of this ran `du -k` over the working copy, which is the wrong
object twice: a file staged and then truncated would be waved through on its new
size, and a file staged and then GROWN would be refused for bytes that are not in
the commit. `git cat-file -s :<path>` is what the index holds, which is what a
commit would carry.

## Why it reads the index and not the working tree

The rule is about what gets committed. An enormous untracked file is not a
problem until someone stages it, and refusing on its existence would fire on
every scratch artifact in `results/`.

## Its own first test passed falsely, which is the reason it is a file

Staging an already-committed unmodified 54.9 MB file and running the check
reported "all clear": `git add` on an unmodified tracked path stages nothing, so
`--cached` never saw it and the gate was never exercised. It was re-tested by
creating a 60 MB file and watching it refuse by name. A gate that reports success
when it was never run is worse than no gate, and that is easy to do by accident.
"""

import argparse
import os
import subprocess
import sys


def staged(repo):
    """(path, bytes) for every path in the index that differs from HEAD."""
    def git(*a):
        return subprocess.run(["git", "-C", repo, *a], capture_output=True,
                              text=True, check=True).stdout
    out = []
    for p in git("diff", "--cached", "--name-only", "-z").split("\0"):
        if not p:
            continue
        try:
            #: `:path` is the index entry. A deleted path has no blob and raises,
            #: which is correct: a deletion commits nothing.
            n = int(git("cat-file", "-s", ":" + p).strip())
        except (subprocess.CalledProcessError, ValueError):
            continue
        out.append((p, n))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", help="any path inside the repo")
    ap.add_argument("--cap", type=float, default=50.0, help="megabytes")
    ap.add_argument("--quiet", action="store_true", help="print only refusals")
    a = ap.parse_args()
    try:
        root = subprocess.run(["git", "-C", os.path.expanduser(a.repo),
                               "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        print("not a git repository: %s" % a.repo, file=sys.stderr)
        return 2
    cap = int(a.cap * 1024 * 1024)
    rows = staged(root)
    over = [(p, n) for p, n in rows if n > cap]
    for p, n in sorted(over, key=lambda t: -t[1]):
        print("  REFUSE %8.1f MB  %s" % (n / 1048576, p))
    if over:
        print("  %d of %d staged file(s) over %g MB -- unstage before committing"
              % (len(over), len(rows), a.cap))
        return 1
    if not a.quiet:
        big = max((n for _, n in rows), default=0)
        print("  %d staged file(s), largest %.1f MB, cap %g MB"
              % (len(rows), big / 1048576, a.cap))
    return 0


if __name__ == "__main__":
    sys.exit(main())
