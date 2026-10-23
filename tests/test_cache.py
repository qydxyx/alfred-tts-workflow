from pathlib import Path

from alfred_tts.cache import cache_key, clear, lookup, store
from alfred_tts.models import SynthesizeRequest


def test_lookup_miss_then_store(tmp_path: Path) -> None:
    request = SynthesizeRequest(provider="edge", text="hello", voice="Aria", model="neural")
    assert lookup(request) is None
    source = tmp_path / "clip.mp3"
    source.write_bytes(b"ID3fake")
    stored = store(request, source)
    assert stored.exists()
    hit = lookup(request)
    assert hit == stored
    assert cache_key(request) in stored.name


def test_cache_key_stable_for_stripped_text() -> None:
    a = SynthesizeRequest(provider="edge", text="  hi  ", voice="Aria")
    b = SynthesizeRequest(provider="edge", text="hi", voice="Aria")
    assert cache_key(a) == cache_key(b)


def test_clear_removes_files(tmp_path: Path) -> None:
    request = SynthesizeRequest(provider="edge", text="bye")
    source = tmp_path / "a.mp3"
    source.write_bytes(b"xx")
    store(request, source)
    assert clear() >= 1
    assert lookup(request) is None
