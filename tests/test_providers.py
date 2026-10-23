from __future__ import annotations

import base64
from pathlib import Path
from types import SimpleNamespace

from alfred_tts.config import load_settings
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.edge import EdgeTTSProvider
from alfred_tts.providers.gemini import GeminiTTSProvider
from alfred_tts.providers.kokoro import KokoroProvider


def test_edge_voice_auto_cjk() -> None:
    provider = EdgeTTSProvider(load_settings())
    assert provider.default_voice("你好") == "zh-CN-XiaoxiaoNeural"
    assert provider.default_voice("hello") == "en-US-AriaNeural"


def test_edge_synthesize_mocked(monkeypatch, tmp_path: Path) -> None:
    class FakeCommunicate:
        def __init__(self, text: str, voice: str, **kwargs) -> None:
            self.text = text
            self.voice = voice

        async def save(self, path: str) -> None:
            Path(path).write_bytes(b"ID3FAKEAUDIO")

    monkeypatch.setattr("edge_tts.Communicate", FakeCommunicate)
    dest = tmp_path / "out"
    path = EdgeTTSProvider(load_settings()).synthesize(
        SynthesizeRequest(provider="edge", text="hi", voice="en-US-AriaNeural"), dest
    )
    assert path.exists()
    assert path.read_bytes().startswith(b"ID3")


def test_gemini_not_ready_without_key() -> None:
    assert GeminiTTSProvider(load_settings()).is_ready() is False


def test_gemini_synthesize_mocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "abc")
    wav = b"RIFF" + b"\x00" * 40
    captured: dict[str, object] = {}

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            captured["kwargs"] = kwargs
            self.interactions = self

        def create(self, **kwargs):
            captured["create"] = kwargs
            return SimpleNamespace(output_audio=SimpleNamespace(data=base64.b64encode(wav).decode()))

    monkeypatch.setattr("google.genai.Client", FakeClient)
    monkeypatch.setattr("google.genai.types", SimpleNamespace(HttpOptions=lambda **k: k), raising=False)
    settings = load_settings()
    path = GeminiTTSProvider(settings).synthesize(
        SynthesizeRequest(provider="gemini", text="Have a wonderful day!", voice="Kore"),
        tmp_path / "out",
    )
    assert path.read_bytes().startswith(b"RIFF")
    assert captured["create"]["model"] == "gemini-3.8-flash-lite-tts"


def test_kokoro_api_synthesize(monkeypatch, tmp_path: Path) -> None:
    class FakeResponse:
        content = b"RIFF" + b"\x00" * 24
        status_code = 200

        def raise_for_status(self) -> None:
            return None

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def post(self, url: str, json: dict):
            assert url.endswith("/audio/speech")
            assert json["input"] == "hello"
            return FakeResponse()

    monkeypatch.setattr("alfred_tts.providers.kokoro.httpx.Client", FakeClient)
    monkeypatch.setattr(KokoroProvider, "_cached_api_ready", lambda self, force=False, probe=True: True)
    settings = load_settings()
    settings.kokoro_mode = "api"
    path = KokoroProvider(settings).synthesize(
        SynthesizeRequest(provider="kokoro", text="hello", voice="af_heart"),
        tmp_path / "out",
    )
    assert path.suffix == ".wav"
    assert path.read_bytes().startswith(b"RIFF")
