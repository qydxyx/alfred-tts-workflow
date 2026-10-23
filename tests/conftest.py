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
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini-tts")
    monkeypatch.setenv("OPENAI_INSTRUCTIONS", "")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    monkeypatch.setenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")
    monkeypatch.setenv("DEEPGRAM_API_KEY", "")
    monkeypatch.setenv("XAI_API_KEY", "")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "")
    monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
    monkeypatch.setenv("ALIYUN_MODEL", "cosyvoice-v3-flash")
    monkeypatch.setenv("VOLC_APPID", "")
    monkeypatch.setenv("VOLC_TOKEN", "")
    monkeypatch.setenv("VOLC_CLUSTER", "volcano_tts")
    monkeypatch.setenv("KOKORO_MODE", "auto")
    monkeypatch.setenv("KOKORO_API_BASE", "http://127.0.0.1:8880/v1")
    monkeypatch.setattr("alfred_tts.providers.kokoro.KokoroProvider._probe_api", lambda self: False)
    return {"data": data, "cache": cache}
