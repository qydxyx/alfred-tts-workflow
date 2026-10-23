from __future__ import annotations

import plistlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_export_dir_filepicker_is_folders_only() -> None:
    plist = plistlib.loads((ROOT / "workflow" / "info.plist").read_bytes())
    export = next(item for item in plist["userconfigurationconfig"] if item["variable"] == "EXPORT_DIR")
    assert export["type"] == "filepicker"
    # 1 = folders; 2 = files (would grey out Open on a directory in Finder)
    assert export["config"]["filtermode"] == 1
