"""Single source of truth for runtime path resolution.

Both the SDK (``bioresearch/__init__.py``) and the CLI (``bioresearch/cli.py``)
import their paths from here so the two can never drift apart.

Resolution is relative to this file. Under an editable install
(``pip install -e .``, which is what CI uses) ``__file__`` points into the
source tree, so ``PROJECT_ROOT`` resolves to the repository root and
``DEMO_DIR`` / ``MAIN_PY`` are found correctly.

NOTE: for a fully install-mode-independent layout the demo scripts would need
to live *inside* the ``bioresearch`` package (e.g. ``bioresearch/demos/``) and
be declared as ``package_data``. With the current structure (demos are a
sibling of the package under ``bio-research-os/``) a non-editable install
(``pip install .``) would not resolve these paths — that is a separate, larger
refactor and is intentionally out of scope here.
"""

from pathlib import Path

# This file lives at bioresearch/core/paths.py
PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # .../bioresearch

# Repository root — sibling of the bio-research-os/ directory
PROJECT_ROOT = PACKAGE_ROOT.parent

DEMO_DIR = PROJECT_ROOT / "bio-research-os" / "demos"
MAIN_PY = PROJECT_ROOT / "bio-research-os" / "main.py"
