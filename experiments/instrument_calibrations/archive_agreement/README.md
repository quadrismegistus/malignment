# archive_agreement — the migration's own completion criterion

**Does an analysis that ran in the archive re-run HERE and agree?** `MANIFEST.md`
closes by saying that is the only thing that would tell us the migration is
finished — *"Not a file count. An analysis that ran in the old repo, re-run here,
agreeing."* Every other check in this repo asks whether a number is internally
consistent. This one asks whether the port PRESERVED A RESULT.

    python run.py --scope        # what the archive claimed, what we can match
    python run.py --run --write  # reproduce it

## TARGET AND RESULT

Finding N, `meta/M01_displacement/findings/N_mass_migration.md`:

    archive     91.0% negative   82,775 cells, 44 edges, 2,199 stimuli
                clusters agreeing 34/34
    here        88.1% negative   101,857 cells, 50 pairs

**MET.** The direction and the magnitude survive the port. The pooled figure here
is over a different and larger cell population than the archive's 44 edges, which
is why it is not identical and why `--scope` prints what can and cannot be
matched before anything is compared.

## THE THING TO NOT DO WITH THIS NUMBER

It is an AGREEMENT check, not an independent replication: it re-runs our code on
our store against a figure the archive published. It cannot detect an error that
exists in both. What it does detect — and what it was built for — is a port that
silently changed a result, which is the failure mode a file count cannot see.
