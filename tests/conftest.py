from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def alfred_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    data = tmp_path / "data"
    cache = tmp_path / "cache"
    data.mkdir()
    cache.mkdir()
    monkeypatch.setenv("alfred_workflow_data", str(data))
    monkeypatch.setenv("alfred_workflow_cache", str(cache))
    monkeypatch.setenv("DEFAULT_PROVIDER", "edge")
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path / "export"))
    monkeypatch.setenv("PROXY_URL", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash-lite-tts")
    monkeypatch.setenv("GEMINI_STYLE", "")
    monkeypatch.setenv("KOKORO_MODE", "auto")
    monkeypatch.setenv("KOKORO_API_BASE", "http://127.0.0.1:8880/v1")
    monkeypatch.setattr("alfred_tts.providers.kokoro.KokoroProvider._probe_api", lambda self: False)
    return {"data": data, "cache": cache}
