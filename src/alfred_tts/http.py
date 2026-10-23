from __future__ import annotations

from typing import Any

import httpx

from alfred_tts.config import Settings

# 海外云走 PROXY_URL；国内云与本地回环直连。
OVERSEAS_PROVIDERS = frozenset({"edge", "gemini", "openai", "elevenlabs", "deepgram", "xai"})


def httpx_client(settings: Settings, *, overseas: bool, timeout: float = 60.0) -> httpx.Client:
    kwargs: dict[str, Any] = {"timeout": timeout, "trust_env": False, "follow_redirects": True}
    if overseas and settings.proxy_url:
        kwargs["proxy"] = settings.proxy_url
    return httpx.Client(**kwargs)


def body_error(response: httpx.Response) -> str:
    try:
        data = response.json()
    except Exception:
        text = (response.text or "")[:400].strip()
        return text or f"HTTP {response.status_code}"
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict) and err.get("message"):
            return str(err["message"])
        for key in ("message", "msg", "detail", "error"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return str(data)[:400]


def audio_bytes(response: httpx.Response, label: str) -> bytes:
    content = response.content or b""
    if response.status_code >= 400:
        raise RuntimeError(f"{label} HTTP {response.status_code}: {body_error(response)}")
    if content[:1] in (b"{", b"[") or "json" in (response.headers.get("content-type") or "").lower():
        raise RuntimeError(f"{label}: {body_error(response)}")
    if len(content) < 16:
        raise RuntimeError(f"{label} 返回空音频")
    return content
