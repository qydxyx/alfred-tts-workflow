from __future__ import annotations

import base64
import json
import os
from typing import Any


def encode_payload(data: dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_payload(arg: str | None) -> dict[str, Any]:
    action = os.environ.get("tts_action", "").strip()
    if action:
        payload = {
            "action": action,
            "provider": os.environ.get("tts_provider", "").strip(),
            "text": os.environ.get("tts_text", ""),
            "voice": os.environ.get("tts_voice", "").strip(),
            "variant": os.environ.get("tts_variant", "").strip(),
        }
        return {key: value for key, value in payload.items() if value != ""}

    if not arg:
        return {}
    try:
        raw = base64.urlsafe_b64decode(arg.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, json.JSONDecodeError):
        try:
            data = json.loads(arg)
            return data if isinstance(data, dict) else {"action": arg}
        except json.JSONDecodeError:
            return {"action": arg}
