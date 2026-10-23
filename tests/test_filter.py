from __future__ import annotations

import json
from pathlib import Path

from alfred_tts.cli import main
from alfred_tts.models import Action
from alfred_tts.payload import decode_payload


def _run_filter(monkeypatch, capsys, query: str, *, venv: bool = True) -> dict:
    monkeypatch.setattr("alfred_tts.cli.which_uv", lambda: Path("/usr/bin/uv"))
    monkeypatch.setattr("alfred_tts.cli.core_venv_ready", lambda: venv)
    monkeypatch.setattr("sys.argv", ["alfred-tts", "filter", query])
    main()
    return json.loads(capsys.readouterr().out)


def test_filter_setup_card_when_venv_missing(monkeypatch, capsys) -> None:
    data = _run_filter(monkeypatch, capsys, "你好", venv=False)
    assert data["skipknowledge"] is True
    assert "初始化" in data["items"][0]["title"]
    payload = decode_payload(data["items"][0]["arg"])
    assert payload["action"] == Action.SETUP


def test_filter_lists_edge_first(monkeypatch, capsys) -> None:
    data = _run_filter(monkeypatch, capsys, "你好，欢迎使用 Alfred TTS")
    titles = [item["title"] for item in data["items"]]
    assert any("Edge TTS" in title for title in titles)
    hidden = ("Gemini", "OpenAI", "ElevenLabs", "Deepgram", "xAI", "阿里云", "火山", "Kokoro")
    assert all(all(name not in title for title in titles) for name in hidden)
    item = data["items"][0]
    assert "cmd" in item["mods"]
    assert "alt" in item["mods"]
    assert "ctrl" in item["mods"]
    payload = decode_payload(item["arg"])
    assert payload["action"] == "play"
    assert payload["provider"] == "edge"
    assert payload["text"] == "你好，欢迎使用 Alfred TTS"


def test_filter_gemini_hidden_until_key(monkeypatch, capsys) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    data = _run_filter(monkeypatch, capsys, "hello")
    titles = [item["title"] for item in data["items"]]
    assert any("Gemini" in title for title in titles)


def test_filter_openai_appears_with_key(monkeypatch, capsys) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    data = _run_filter(monkeypatch, capsys, "hello")
    titles = [item["title"] for item in data["items"]]
    assert any("OpenAI" in title for title in titles)


def test_filter_at_unknown_lists_ids(monkeypatch, capsys) -> None:
    data = _run_filter(monkeypatch, capsys, "@nope 你好")
    subtitle = data["items"][0]["subtitle"]
    assert "openai" in subtitle
    assert "volcengine" in subtitle


def test_filter_at_kokoro_shows_install_cards(monkeypatch, capsys) -> None:
    data = _run_filter(monkeypatch, capsys, "@kokoro 测试离线语音")
    titles = [item["title"] for item in data["items"]]
    assert any("FP32" in title for title in titles)
    assert any("INT8" in title for title in titles)
    payload = decode_payload(data["items"][0]["arg"])
    assert payload["action"] == Action.INSTALL_KOKORO
    assert payload["variant"] == "fp32"


def test_filter_stop(monkeypatch, capsys) -> None:
    data = _run_filter(monkeypatch, capsys, "stop")
    payload = decode_payload(data["items"][0]["arg"])
    assert payload["action"] == Action.STOP
