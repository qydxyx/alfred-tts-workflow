from __future__ import annotations

import re
from dataclasses import dataclass

_PROVIDER_RE = re.compile(r"^@([a-zA-Z0-9_-]+)(?:\s+|$)")
_CJK_RE = re.compile(r"[\u3400-\u9fff\U00020000-\U0002a6df]")


_VOICE_RE = re.compile(r"^(?:voice:|v:|#)([A-Za-z0-9_-]+)(?:\s+|$)")
_STANDALONE_VOICE_RE = re.compile(r"^(?:(?:voice:|v:)([A-Za-z0-9_-]+)|#([A-Za-z0-9_-]{15,}))(?:\s+|$)")


@dataclass(slots=True)
class ParsedQuery:
    raw: str
    text: str
    provider: str | None = None
    voice: str | None = None
    is_stop: bool = False


def parse_query(query: str) -> ParsedQuery:
    raw = query or ""
    stripped = raw.strip()
    if not stripped:
        return ParsedQuery(raw=raw, text="")
    if stripped.lower() in {"stop", "tts stop"}:
        return ParsedQuery(raw=raw, text="", is_stop=True)

    provider = None
    rest = stripped
    match = _PROVIDER_RE.match(stripped)
    if match:
        provider = match.group(1).lower()
        rest = stripped[match.end() :].strip()

    voice = None
    if provider:
        voice_match = _VOICE_RE.match(rest)
        if voice_match:
            voice = voice_match.group(1)
            rest = rest[voice_match.end() :].strip()
    else:
        standalone_match = _STANDALONE_VOICE_RE.match(rest)
        if standalone_match:
            voice = standalone_match.group(1) or standalone_match.group(2)
            rest = rest[standalone_match.end() :].strip()
    return ParsedQuery(raw=raw, text=rest, provider=provider, voice=voice)


def has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def slug(text: str, limit: int = 24) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\s]+', "_", text.strip())
    cleaned = cleaned.strip("._") or "tts"
    return cleaned[:limit]
