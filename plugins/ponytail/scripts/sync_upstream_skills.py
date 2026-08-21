#!/usr/bin/env python3
"""Copy pinned upstream skills into the installable Codex plugin contract path."""

from pathlib import Path
import shutil


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PLUGIN_ROOT / "upstream" / "skills"
TARGET = PLUGIN_ROOT / "skills"


if not SOURCE.is_dir():
    raise SystemExit("initialize plugins/ponytail/upstream before syncing skills")
if TARGET.is_symlink():
    TARGET.unlink()
elif TARGET.exists():
    shutil.rmtree(TARGET)
shutil.copytree(SOURCE, TARGET)
