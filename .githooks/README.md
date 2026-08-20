# .githooks

    git config core.hooksPath .githooks     # <- REQUIRED, PER CLONE

**These hooks do nothing until that line is run.** `core.hooksPath` is local git
config, not a tracked file, so a fresh clone has the hooks on disk and inactive.
That is the failure mode to watch for: the guard is visible in the tree, reads as
installed, and refuses nothing.

Checked here on 2026-08-20 and `.git/hooks/` was EMPTY with `core.hooksPath`
unset -- so nothing would have refused the 240 MB `words_flipties.jsonl` sitting
untracked-and-unignored at the time, and a manual checker existed
(`scripts/check_staged_size.py`) that only runs when someone remembers it.

## pre-commit -- size

Blocks any staged blob over **50 MiB**; warns over 20. GitHub hard-blocks at 100
MiB and warns at 50, and this repo stops at GitHub's warning line because nothing
here legitimately needs a 50 MB blob in git: `words.jsonl` is 240 MB and ignored,
and the largest single file in the `p_on_passages` copy is 9 MB.

Measures the STAGED BLOB (`git cat-file -s :<path>`), not the working copy. The
archive's version used `wc -c` on disk, which is wrong twice -- a file staged then
truncated is waved through, a file staged then grown is refused for bytes not in
the commit.

Escape hatch, for when you mean it: `ALLOW_BIG=1 git commit ...`

## pre-push -- session links

Blocks a push whose commits carry `claude.ai/code/session` or `Claude-Session:`.
RH's standing rule is that these never reach anything public. Scoped to the
commits being pushed, deliberately: a full-history check would block every push
forever, since a rewrite does not unpublish.

## Both were watched refusing before being committed

A guard nobody has seen fail is a belief, not a check. On 2026-08-20: a 60 MB blob
was BLOCKED and confirmed absent from HEAD; `ALLOW_BIG=1` let the same blob
through; a 30 MB blob warned and landed; and a commit carrying a
`Claude-Session:` trailer had its push refused with a non-zero exit.
