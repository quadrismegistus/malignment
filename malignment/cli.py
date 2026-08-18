#!/usr/bin/env python
"""One entrypoint over the module mains. `malign <module> [args]`.

    malign                       what exists, with each module's first line
    malign roster                the roster summary
    malign cloud boxes           declared box shapes
    malign observe --vocab       measure tokenizer facts
    malign ingest --dry

## A DISPATCHER, NOT A SECOND CLI

Every module here already owns its arguments and its `--help`, and those
argument lists are where the knowledge is -- `observe`'s passes, `cloud`'s
subcommands, `ingest`'s gates. **A hand-maintained parser over the top would be a
second declaration of the same surface**, drifting the moment anyone adds a flag,
which is the failure `requirements.txt` and `models.yaml` both carry warnings
about. So this resolves a name, hands the remaining argv to that module's
`main()`, and adds nothing of its own.

Discovery is by INTROSPECTION rather than a list: a module is a command if it
defines `main()`. Add a module with a `main` and it appears here; a list would
have to be remembered.
"""
import importlib
import os
import pkgutil
import sys

_HIDE = {"cli"}


def commands():
    """{name: first docstring line} for every module exposing `main()`."""
    import ast
    here = os.path.dirname(os.path.abspath(__file__))
    out = {}
    for mod in pkgutil.iter_modules([here]):
        if mod.name in _HIDE or mod.name.startswith("_"):
            continue
        path = os.path.join(here, mod.name + ".py")
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
        except Exception:                                       # noqa: BLE001
            continue
        #: parsed, not imported -- importing every module to ask whether it has a
        #: `main` would pull torch in to answer `malign --help`.
        if any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body):
            doc = (ast.get_docstring(tree) or "").strip().split("\n")[0]
            out[mod.name] = doc
    return dict(sorted(out.items()))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cmds = commands()
    if not argv or argv[0] in ("-h", "--help", "help"):
        print("malign <command> [args]    -- each command's own --help is authoritative\n")
        for name, doc in cmds.items():
            print("  %-18s %s" % (name, doc[:70]))
        return 0
    name = argv[0]
    if name not in cmds:
        near = [c for c in cmds if c.startswith(name[:3])]
        print("no command %r%s" % (name, ("  did you mean: " + ", ".join(near)) if near else ""),
              file=sys.stderr)
        return 2
    mod = importlib.import_module("malignment." + name)
    #: **THE MODULE PARSES ITS OWN ARGV**, so `argparse` reports the real program
    #: name and every existing invocation keeps working unchanged.
    sys.argv = ["malign " + name] + argv[1:]
    return mod.main() or 0


if __name__ == "__main__":
    sys.exit(main())
