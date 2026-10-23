from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset


class GeminiTTSProvider(TTSProvider):
    id = "gemini"
    name = "Gemini TTS"
    icon = "icons/gemini.png"

    def is_ready(self) -> bool:
        return bool(self.settings.gemini_api_key)

    def setup_hint(self) -> str:
        return "在 Workflow 配置中填写 GEMINI_API_KEY"

    def default_voice(self, text: str = "") -> str:
        return "Kore"

    def resolved_model(self, request: SynthesizeRequest) -> str:
        return request.model or self.settings.gemini_model

    def resolved_style(self, request: SynthesizeRequest) -> str:
        return request.style or self.settings.gemini_style

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset("Kore", "Kore"),
            VoicePreset("Puck", "Puck"),
            VoicePreset("Aoede", "Aoede"),
            VoicePreset("Charon", "Charon"),
            VoicePreset("Fenrir", "Fenrir"),
            VoicePreset("Leda", "Leda"),
            VoicePreset("Orus", "Orus"),
            VoicePreset("Zephyr", "Zephyr"),
        ]

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        from google import genai
        from google.genai import types

        dest = dest.with_suffix(".wav")
        dest.parent.mkdir(parents=True, exist_ok=True)
        voice = self.resolved_voice(request)
        model = self.resolved_model(request)
        style = self.resolved_style(request)
        proxy = self.settings.proxy_url or None

        http_options = None
        if proxy:
            http_options = types.HttpOptions(
                client_args={"proxy": proxy, "trust_env": False},
                async_client_args={"proxy": proxy, "trust_env": False},
            )

        client_kwargs: dict[str, Any] = {"api_key": self.settings.gemini_api_key}
        if http_options is not None:
            client_kwargs["http_options"] = http_options
        client = genai.Client(**client_kwargs)

        annotations = []
        if style:
            annotations.append({"type": "speech_metadata", "style": style})
        content: dict[str, Any] = {"type": "text", "text": request.text}
        if annotations:
            content["annotations"] = annotations

        interaction = client.interactions.create(
            model=model,
            input=[{"type": "user_input", "content": [content]}],
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": voice}]},
        )
        audio = _extract_audio_bytes(interaction)
        dest.write_bytes(audio)
        return dest


def _extract_audio_bytes(interaction: Any) -> bytes:
    output_audio = getattr(interaction, "output_audio", None)
    if output_audio is not None:
        data = getattr(output_audio, "data", output_audio)
        return _coerce_audio(data)
    outputs = getattr(interaction, "outputs", None) or getattr(interaction, "output", None) or []
    for item in outputs:
        data = getattr(item, "data", None) or (item.get("data") if isinstance(item, dict) else None)
        if data:
            return _coerce_audio(data)
        content = getattr(item, "content", None) or (item.get("content") if isinstance(item, dict) else None)
        if isinstance(content, list):
            for part in content:
                pdata = getattr(part, "data", None) or (part.get("data") if isinstance(part, dict) else None)
                if pdata:
                    return _coerce_audio(pdata)
    raise RuntimeError("Gemini TTS 未返回音频数据")


def _coerce_audio(data: Any) -> bytes:
    if isinstance(data, bytes):
        raw = data
    elif isinstance(data, str):
        raw = base64.b64decode(data)
    else:
        raise RuntimeError("Gemini TTS 音频格式无法解析")
    if len(raw) < 16:
        raise RuntimeError("Gemini TTS 返回空音频")
    return raw
