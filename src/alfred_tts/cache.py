from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from alfred_tts.config import MAX_CACHE_ITEMS, cache_dir
from alfred_tts.models import SynthesizeRequest


def audio_dir() -> Path:
    path = cache_dir() / "audio"
    path.mkdir(parents=True, exist_ok=True)
    return path


def index_path() -> Path:
    return audio_dir() / "index.json"


def cache_key(request: SynthesizeRequest) -> str:
    payload = "|".join(
        [
            request.provider,
            request.model or "",
            request.voice or "",
            f"{float(request.speed):.3f}",
            request.style or "",
            request.text.strip(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_index() -> list[dict[str, str]]:
    path = index_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def _save_index(entries: list[dict[str, str]]) -> None:
    path = index_path()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def lookup(request: SynthesizeRequest) -> Path | None:
    key = cache_key(request)
    directory = audio_dir()
    for suffix in (".mp3", ".wav", ".m4a"):
        candidate = directory / f"{key}{suffix}"
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return None


def store(request: SynthesizeRequest, source: Path) -> Path:
    key = cache_key(request)
    dest = audio_dir() / f"{key}{source.suffix or '.mp3'}"
    dest.write_bytes(source.read_bytes())
    entries = [item for item in _load_index() if item.get("key") != key]
    entries.append({"key": key, "path": dest.name, "ts": str(time.time())})
    overflow = entries[:-MAX_CACHE_ITEMS] if len(entries) > MAX_CACHE_ITEMS else []
    for item in overflow:
        stale = audio_dir() / item.get("path", "")
        if stale.exists():
            stale.unlink()
    _save_index(entries[-MAX_CACHE_ITEMS:])
    return dest


def clear() -> int:
    removed = 0
    directory = audio_dir()
    for path in directory.iterdir():
        if path.is_file():
            path.unlink()
            removed += 1
    return removed
