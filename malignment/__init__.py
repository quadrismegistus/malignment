"""malignment — alignment as secondary revision of a statistical unconscious.

The measurements live in ClickHouse (`malign_logits`, shared with the archive
repo `malign-logits`); the roster is one authored JSON. Nothing else is carried
until something needs it — see MANIFEST.md, which records why every file is here.
"""
__version__ = "0.1.0"

# The checkpoint handle. `runners` holds the machinery; import it lazily so
# `Checkpoint` costs no torch.
from .checkpoint import Checkpoint  # noqa: E402,F401
from .passage import Passage, score_all  # noqa: E402,F401
