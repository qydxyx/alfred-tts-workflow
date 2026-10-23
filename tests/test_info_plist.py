from __future__ import annotations

import plistlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _plist() -> dict:
    return plistlib.loads((ROOT / "workflow" / "info.plist").read_bytes())


def test_export_dir_filepicker_is_folders_only() -> None:
    export = next(item for item in _plist()["userconfigurationconfig"] if item["variable"] == "EXPORT_DIR")
    assert export["type"] == "filepicker"
    # 1 = folders; 2 = files (would grey out Open on a directory in Finder)
    assert export["config"]["filtermode"] == 1


def test_default_provider_includes_new_engines() -> None:
    fields = _plist()["userconfigurationconfig"]
    default = next(item for item in fields if item["variable"] == "DEFAULT_PROVIDER")
    values = [pair[1] for pair in default["config"]["pairs"]]
    for engine in ("openai", "elevenlabs", "deepgram", "xai", "aliyun", "volcengine"):
        assert engine in values


def test_api_key_fields_exist() -> None:
    variables = {item["variable"] for item in _plist()["userconfigurationconfig"]}
    for name in (
        "OPENAI_API_KEY",
        "ELEVENLABS_API_KEY",
        "DEEPGRAM_API_KEY",
        "XAI_API_KEY",
        "DASHSCOPE_API_KEY",
        "VOLC_APPID",
        "VOLC_TOKEN",
    ):
        assert name in variables
