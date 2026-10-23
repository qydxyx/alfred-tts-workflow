from __future__ import annotations

from pathlib import Path

from alfred_tts.cli import _cmd_run
from alfred_tts.models import Action, SynthesizeRequest
from alfred_tts.payload import encode_payload
from alfred_tts.providers.edge import EdgeTTSProvider


def test_run_play_uses_cache_and_afplay(monkeypatch, tmp_path: Path) -> None:
    audio = tmp_path / "cached.mp3"
    audio.write_bytes(b"ID3xx")
    played: list[Path] = []
    monkeypatch.setattr("alfred_tts.cli.lookup", lambda request: audio)
    monkeypatch.setattr("alfred_tts.cli.play_audio", played.append)
    code = _cmd_run(encode_payload({"action": Action.PLAY, "provider": "edge", "text": "hi"}))
    assert code == 0
    assert played == [audio]


def test_run_copy_notifies(monkeypatch, tmp_path: Path) -> None:
    audio = tmp_path / "cached.mp3"
    audio.write_bytes(b"ID3xx")
    monkeypatch.setattr("alfred_tts.cli.lookup", lambda request: audio)
    monkeypatch.setattr("alfred_tts.cli.copy_audio_file_to_clipboard", lambda path, text: path)
    notes: list[tuple[str, str]] = []
    monkeypatch.setattr("alfred_tts.cli.notify", lambda title, message: notes.append((title, message)))
    code = _cmd_run(encode_payload({"action": Action.COPY_FILE, "provider": "edge", "text": "hi"}))
    assert code == 0
    assert notes and "剪贴板" in notes[0][1]


def test_edge_request_roundtrip(monkeypatch, tmp_path: Path) -> None:
    class FakeCommunicate:
        def __init__(self, text: str, voice: str, **kwargs) -> None:
            self.text = text

        async def save(self, path: str) -> None:
            Path(path).write_bytes(b"ID3FAKE")

    monkeypatch.setattr("edge_tts.Communicate", FakeCommunicate)
    from alfred_tts.config import load_settings

    provider = EdgeTTSProvider(load_settings())
    out = provider.synthesize(SynthesizeRequest(provider="edge", text="hi"), tmp_path / "x")
    assert out.stat().st_size > 0
