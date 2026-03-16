"""Path configuration for importing local repository libraries.

This module adds the local ``codecarbon/``, ``AIOpsLab/``, and
``dagger/sdk/python/src/`` directories to ``sys.path`` so that
modules inside ``greenpipeline/`` can directly import from them
without installing them as packages.

Usage (at the top of any greenpipeline module that needs local repos)::

    import greenpipeline._paths  # noqa: F401  — activates path setup
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent  # gitlab_hackathon/

_LOCAL_LIB_ROOTS = [
    _REPO_ROOT / "codecarbon",           # → import codecarbon
    _REPO_ROOT / "AIOpsLab",             # → import aiopslab
    _REPO_ROOT / "dagger" / "sdk" / "python" / "src",  # → import dagger
]

for lib_root in _LOCAL_LIB_ROOTS:
    lib_str = str(lib_root)
    if lib_root.is_dir() and lib_str not in sys.path:
        sys.path.insert(0, lib_str)
