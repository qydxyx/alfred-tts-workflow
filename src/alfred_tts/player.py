from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path

from alfred_tts.config import cache_dir
from alfred_tts.query import slug


def pid_path() -> Path:
    return cache_dir() / "player.pid"


def clipboard_dir() -> Path:
    path = cache_dir() / "clipboard"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _is_afplay_process(pid: int) -> bool:
    try:
        res = subprocess.run(
            ["ps", "-p", str(pid), "-o", "comm="],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return True
        comm = (res.stdout or "").strip()
        return "afplay" in comm
    except Exception:
        return True


def stop_playback() -> bool:
    path = pid_path()
    if not path.exists():
        return False
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        path.unlink(missing_ok=True)
        return False
    if not _is_afplay_process(pid):
        path.unlink(missing_ok=True)
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        path.unlink(missing_ok=True)
        return False
    except PermissionError:
        return False
    path.unlink(missing_ok=True)
    return True


def play_audio(path: Path) -> None:
    stop_playback()
    proc = subprocess.Popen(
        ["/usr/bin/afplay", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    pid_path().write_text(str(proc.pid), encoding="utf-8")


def copy_audio_file_to_clipboard(path: Path, label_text: str) -> Path:
    dest = clipboard_dir() / f"{slug(label_text)}{path.suffix}"
    dest.write_bytes(path.read_bytes())
    script = "on run argv\nset the clipboard to (POSIX file (item 1 of argv))\nend run"
    subprocess.run(
        ["/usr/bin/osascript", "-e", script, str(dest.resolve())],
        check=True,
        capture_output=True,
    )
    return dest


def save_and_reveal(path: Path, export_dir: Path, provider: str, text: str) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = export_dir / f"{stamp}-{provider}-{slug(text)}{path.suffix}"
    dest.write_bytes(path.read_bytes())
    subprocess.run(["/usr/bin/open", "-R", str(dest)], check=False)
    return dest


def notify(title: str, message: str) -> None:
    script = "on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run"
    subprocess.run(
        ["/usr/bin/osascript", "-e", script, str(title), str(message)],
        check=False,
        capture_output=True,
    )
