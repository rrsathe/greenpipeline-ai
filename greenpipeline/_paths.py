"""Path configuration for importing local repository libraries.

This module adds local dependency directories to ``sys.path`` so that
modules inside ``greenpipeline/`` can directly import from them without
installing them as packages.

Dependencies are resolved from ``external/`` first (current structure),
with fallback to legacy top-level locations for backward compatibility.

Usage (at the top of any greenpipeline module that needs local repos)::

    import greenpipeline._paths  # noqa: F401  — activates path setup
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent  # gitlab_hackathon/
_EXTERNAL_ROOT = _REPO_ROOT / "external"


def _existing_path(*candidates: Path) -> Path | None:
    """Return first existing path from candidates, else ``None``."""
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


_LOCAL_LIB_ROOTS = [
    _existing_path(_EXTERNAL_ROOT / "codecarbon", _REPO_ROOT / "codecarbon"),
    _existing_path(_EXTERNAL_ROOT / "AIOpsLab", _REPO_ROOT / "AIOpsLab"),
    _existing_path(
        _EXTERNAL_ROOT / "dagger" / "sdk" / "python" / "src",
        _REPO_ROOT / "dagger" / "sdk" / "python" / "src",
    ),
]

for lib_root in _LOCAL_LIB_ROOTS:
    if lib_root is None:
        continue
    lib_str = str(lib_root)
    if lib_str not in sys.path:
        sys.path.insert(0, lib_str)
