"""Template registry for the paper builder GUI.

This indirection lets us swap the underlying HTML without touching the GUI
code, which keeps merges cleaner when upstream exam assets change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def _load_templates() -> Dict[str, str]:
    templates: Dict[str, str] = {}
    for name in ("single.html", "fill.html", "file.html"):
        path = TEMPLATE_DIR / name
        if not path.exists():
            continue
        templates[name] = path.read_text(encoding="utf-8")
    return templates


TEMPLATE_REGISTRY = _load_templates()

