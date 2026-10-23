from __future__ import annotations

import base64
from pathlib import Path
from types import SimpleNamespace

from alfred_tts.config import load_settings
from alfred_tts.http import httpx_client
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.aliyun import AliyunTTSProvider
from alfred_tts.providers.deepgram import DeepgramTTSProvider
from alfred_tts.providers.edge import EdgeTTSProvider
from alfred_tts.providers.elevenlabs import ElevenLabsTTSProvider
from alfred_tts.providers.gemini import GeminiTTSProvider
from alfred_tts.providers.kokoro import KokoroProvider
from alfred_tts.providers.openai import OpenAITTSProvider
from alfred_tts.providers.volcengine import VolcengineTTSProvider
from alfred_tts.providers.xai import XAITTSProvider

MP3 = b"ID3FAKEAUDIOXXXXXX"


class FakeResponse:
    def __init__(
        self,
        content: bytes = MP3,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        json_data: dict | None = None,
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.headers = headers or {"content-type": "audio/mpeg"}
        self._json = json_data

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeClient:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.calls: list[tuple[str, str, dict]] = []
        self.response = FakeResponse()
        self.get_response = FakeResponse()

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None

    def post(self, url: str, headers=None, json=None):
        self.calls.append(("POST", url, {"headers": headers, "json": json}))
        return self.response

    def get(self, url: str, headers=None):
        self.calls.append(("GET", url, {"headers": headers}))
        return self.get_response


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


def test_new_providers_not_ready_without_keys() -> None:
    settings = load_settings()
    assert OpenAITTSProvider(settings).is_ready() is False
    assert ElevenLabsTTSProvider(settings).is_ready() is False
    assert DeepgramTTSProvider(settings).is_ready() is False
    assert XAITTSProvider(settings).is_ready() is False
    assert AliyunTTSProvider(settings).is_ready() is False
    assert VolcengineTTSProvider(settings).is_ready() is False


def test_openai_synthesize_mocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_INSTRUCTIONS", "calm")
    fake = FakeClient()
    monkeypatch.setattr("alfred_tts.providers.openai.httpx_client", lambda *a, **k: fake)
    path = OpenAITTSProvider(load_settings()).synthesize(
        SynthesizeRequest(provider="openai", text="hello", voice="coral"),
        tmp_path / "out",
    )
    assert path.read_bytes().startswith(b"ID3")
    method, url, payload = fake.calls[0]
    assert method == "POST"
    assert url.endswith("/audio/speech")
    assert payload["json"]["model"] == "gpt-4o-mini-tts"
    assert payload["json"]["instructions"] == "calm"


def test_elevenlabs_synthesize_mocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "el-test")
    fake = FakeClient()
    monkeypatch.setattr("alfred_tts.providers.elevenlabs.httpx_client", lambda *a, **k: fake)
    path = ElevenLabsTTSProvider(load_settings()).synthesize(
        SynthesizeRequest(provider="elevenlabs", text="hello"),
        tmp_path / "out",
    )
    assert path.exists()
    _, url, payload = fake.calls[0]
    assert "text-to-speech/21m00Tcm4TlvDq8ikWAM" in url
    assert payload["headers"]["xi-api-key"] == "el-test"
    assert payload["json"]["model_id"] == "eleven_flash_v2_5"


def test_deepgram_synthesize_mocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DEEPGRAM_API_KEY", "dg-test")
    fake = FakeClient()
    monkeypatch.setattr("alfred_tts.providers.deepgram.httpx_client", lambda *a, **k: fake)
    DeepgramTTSProvider(load_settings()).synthesize(
        SynthesizeRequest(provider="deepgram", text="hello"),
        tmp_path / "out",
    )
    _, url, payload = fake.calls[0]
    assert "model=aura-2-thalia-en" in url
    assert payload["headers"]["Authorization"] == "Token dg-test"


def test_xai_uses_zh_for_cjk(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    fake = FakeClient()
    monkeypatch.setattr("alfred_tts.providers.xai.httpx_client", lambda *a, **k: fake)
    XAITTSProvider(load_settings()).synthesize(
        SynthesizeRequest(provider="xai", text="你好世界"),
        tmp_path / "out",
    )
    _, url, payload = fake.calls[0]
    assert url == "https://api.x.ai/v1/tts"
    assert payload["json"]["language"] == "zh"
    assert payload["json"]["voice_id"] == "eve"


def test_aliyun_downloads_audio_url(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dash-test")
    fake = FakeClient()
    fake.response = FakeResponse(
        content=b'{"output":{"audio":{"url":"https://cdn.example/a.mp3"}}}',
        headers={"content-type": "application/json"},
        json_data={"output": {"audio": {"url": "https://cdn.example/a.mp3"}}},
    )
    fake.get_response = FakeResponse()
    monkeypatch.setattr("alfred_tts.providers.aliyun.httpx_client", lambda *a, **k: fake)
    path = AliyunTTSProvider(load_settings()).synthesize(
        SynthesizeRequest(provider="aliyun", text="你好"),
        tmp_path / "out",
    )
    assert path.read_bytes().startswith(b"ID3")
    assert fake.calls[0][1].endswith("/services/audio/tts/SpeechSynthesizer")
    assert fake.calls[1][0] == "GET"


def test_volcengine_decodes_base64(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VOLC_APPID", "app")
    monkeypatch.setenv("VOLC_TOKEN", "tok")
    fake = FakeClient()
    fake.response = FakeResponse(
        content=b"{}",
        headers={"content-type": "application/json"},
        json_data={"code": 3000, "data": base64.b64encode(MP3).decode(), "message": "Success"},
    )
    monkeypatch.setattr("alfred_tts.providers.volcengine.httpx_client", lambda *a, **k: fake)
    path = VolcengineTTSProvider(load_settings()).synthesize(
        SynthesizeRequest(provider="volcengine", text="你好", voice="ICL_zh_female_aojiaoniang_tob"),
        tmp_path / "out",
    )
    assert path.read_bytes() == MP3
    payload = fake.calls[0][2]["json"]
    assert payload["app"]["cluster"] == "volcano_icl"
    assert fake.calls[0][2]["headers"]["Authorization"] == "Bearer;tok"


def test_overseas_client_uses_proxy(monkeypatch) -> None:
    monkeypatch.setenv("PROXY_URL", "http://127.0.0.1:7890")
    settings = load_settings()
    captured: dict[str, object] = {}

    class CaptureClient:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

    monkeypatch.setattr("alfred_tts.http.httpx.Client", CaptureClient)
    httpx_client(settings, overseas=True)
    assert captured["proxy"] == "http://127.0.0.1:7890"
    captured.clear()
    httpx_client(settings, overseas=False)
    assert "proxy" not in captured
