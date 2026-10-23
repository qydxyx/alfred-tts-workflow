from __future__ import annotations

from pathlib import Path

from alfred_tts.player import pid_path, play_audio, stop_playback


class DummyProc:
    def __init__(self) -> None:
        self.pid = 4242


def test_play_stops_previous_and_writes_pid(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_popen(cmd, **kwargs):
        calls.append(cmd)
        return DummyProc()

    monkeypatch.setattr("alfred_tts.player.subprocess.Popen", fake_popen)
    monkeypatch.setattr("alfred_tts.player.stop_playback", lambda: True)
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"xx")
    play_audio(audio)
    assert calls[0][0] == "/usr/bin/afplay"
    assert pid_path().read_text(encoding="utf-8") == "4242"


def test_stop_playback_kills_pid(monkeypatch) -> None:
    pid_path().write_text("99999", encoding="utf-8")
    killed: list[int] = []

    def fake_kill(pid: int, sig: int) -> None:
        killed.append(pid)
        raise ProcessLookupError

    monkeypatch.setattr("alfred_tts.player.os.kill", fake_kill)
    stop_playback()
    assert killed == [99999]
    assert not pid_path().exists()
