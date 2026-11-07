from __future__ import annotations

from typing import Any

import httpx

from alfred_tts.config import Settings


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
    message = _error_message(data)
    return message or str(data)[:400]


def _error_message(data: Any) -> str:
    if isinstance(data, str):
        return data.strip()
    if isinstance(data, list):
        for item in data:
            message = _error_message(item)
            if message:
                return message
        return ""
    if isinstance(data, dict):
        for key in ("message", "msg", "detail", "error"):
            if key not in data:
                continue
            message = _error_message(data[key])
            if message:
                return message
    return ""


def audio_bytes(response: httpx.Response, label: str) -> bytes:
    content = response.content or b""
    if response.status_code >= 400:
        raise RuntimeError(f"{label} HTTP {response.status_code}: {body_error(response)}")
    if content[:1] in (b"{", b"[") or "json" in (response.headers.get("content-type") or "").lower():
        raise RuntimeError(f"{label}: {body_error(response)}")
    if len(content) < 16:
        raise RuntimeError(f"{label} 返回空音频")
    return content
