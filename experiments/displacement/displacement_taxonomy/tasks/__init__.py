"""Tasks for the displacement taxonomy, in the largeliterarymodels house style.

Lazy imports, matching `largeliterarymodels/tasks/__init__.py`, so importing the
package does not pull pydantic and the task base classes into a caller that only
wants the stash helpers.
"""

import importlib

_LAZY_IMPORTS = {
    'MergeTask': ('.merge_relations', 'MergeTask'),
    'MergeRelationsTask': ('.merge_relations', 'MergeRelationsTask'),
    'MergeRelationsTaskReasonFirst': ('.merge_relations', 'MergeRelationsTaskReasonFirst'),
    'ConstructRegister': ('.merge_relations', 'ConstructRegister'),
    'ChunkResult': ('.merge_relations', 'ChunkResult'),
    'Placement': ('.merge_relations', 'Placement'),
    'SameAs': ('.merge_relations', 'SameAs'),
    'format_relation': ('.merge_relations', 'format_relation'),
    'THEORY_MAP': ('.merge_relations', 'THEORY_MAP'),
}

__all__ = list(_LAZY_IMPORTS)


def __getattr__(name):
    if name in _LAZY_IMPORTS:
        mod, attr = _LAZY_IMPORTS[name]
        return getattr(importlib.import_module(mod, __name__), attr)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(__all__)
