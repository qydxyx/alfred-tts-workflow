from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import httpx

from alfred_tts.http import body_error, httpx_client
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset

ALIYUN_BASE_DEFAULT = "https://dashscope.aliyuncs.com/api/v1"
ALIYUN_MODEL_DEFAULT = "cosyvoice-v3-flash"


class AliyunTTSProvider(TTSProvider):
    id = "aliyun"
    name = "阿里云百炼"
    icon = "icons/aliyun.png"

    def is_ready(self) -> bool:
        return bool(self.settings.dashscope_api_key)

    def setup_hint(self) -> str:
        return "在 Workflow 配置中填写 DASHSCOPE_API_KEY"

    def default_voice(self, text: str = "") -> str:
        return "longanyang"

    def resolved_model(self, request: SynthesizeRequest) -> str:
        return request.model or self.settings.aliyun_model or ALIYUN_MODEL_DEFAULT

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset("longanyang", "龙安洋"),
            VoicePreset("longanhuan", "龙安欢"),
            VoicePreset("longxiaochun", "龙小淳"),
            VoicePreset("longshu", "龙书"),
            VoicePreset("longxiaoxia", "龙小夏"),
        ]

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        dest = dest.with_suffix(".mp3")
        dest.parent.mkdir(parents=True, exist_ok=True)
        root = (self.settings.dashscope_base_url or ALIYUN_BASE_DEFAULT).rstrip("/")
        url = f"{root}/services/audio/tts/SpeechSynthesizer"
        headers = {
            "Authorization": f"Bearer {self.settings.dashscope_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.resolved_model(request),
            "input": {
                "text": request.text,
                "voice": self.resolved_voice(request),
                "format": "mp3",
                "sample_rate": 22050,
            },
        }
        with httpx_client(self.settings, overseas=False) as client:
            response = client.post(url, headers=headers, json=payload)
            dest.write_bytes(_extract_audio(response, client))
        return dest


def _extract_audio(response: httpx.Response, client: httpx.Client) -> bytes:
    if response.status_code >= 400:
        raise RuntimeError(f"阿里云百炼 HTTP {response.status_code}: {body_error(response)}")
    content = response.content or b""
    ctype = (response.headers.get("content-type") or "").lower()
    if "json" not in ctype and content[:1] not in (b"{", b"["):
        if len(content) < 16:
            raise RuntimeError("阿里云百炼 返回空音频")
        return content
    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError("阿里云百炼 响应无法解析") from exc
    if not isinstance(data, dict):
        raise RuntimeError("阿里云百炼 响应格式异常")
    code = data.get("code")
    if code not in (None, "", 0, "0", "Success", "success"):
        raise RuntimeError(f"阿里云百炼: {data.get('message') or data.get('code')}")
    audio = _find_audio_field(data)
    if isinstance(audio, str) and audio.startswith("http"):
        fetched = client.get(audio)
        fetched.raise_for_status()
        raw = fetched.content
    elif isinstance(audio, str):
        raw = base64.b64decode(audio)
    elif isinstance(audio, dict) and audio.get("url"):
        fetched = client.get(str(audio["url"]))
        fetched.raise_for_status()
        raw = fetched.content
    elif isinstance(audio, dict) and audio.get("data"):
        raw = base64.b64decode(str(audio["data"]))
    else:
        raise RuntimeError(f"阿里云百炼 未返回音频: {str(data)[:240]}")
    if len(raw) < 16:
        raise RuntimeError("阿里云百炼 返回空音频")
    return raw


def _find_audio_field(data: dict[str, Any]) -> Any:
    output = data.get("output")
    if isinstance(output, dict):
        if "audio" in output:
            return output["audio"]
        inner = output.get("output")
        if isinstance(inner, dict) and "audio" in inner:
            return inner["audio"]
    return data.get("audio")
