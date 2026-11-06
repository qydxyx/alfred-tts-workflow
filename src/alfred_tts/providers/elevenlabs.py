from __future__ import annotations

from pathlib import Path

from alfred_tts.http import audio_bytes, httpx_client
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset

ELEVENLABS_MODEL_DEFAULT = "eleven_flash_v2_5"
# Sarah is a Default voice that the free API accepts. Rachel is a library voice and returns 402.
_SARAH = "EXAVITQu4vr4xnSDxMaL"
_RACHEL = "21m00Tcm4TlvDq8ikWAM"
_GEORGE = "JBFqnCBsd6RMkjVDRZzb"
_DANIEL = "onwK4e9ZLuTAKqWW03F9"
_LILY = "pFZP5JQG7iQjIQuC4Bku"
_ADAM = "pNInz6obpgDQGcFmaJgB"
_PRESET_BY_LABEL = {
    "rachel": _RACHEL,
    "sarah": _SARAH,
    "george": _GEORGE,
    "daniel": _DANIEL,
    "lily": _LILY,
    "adam": _ADAM,
}


class ElevenLabsTTSProvider(TTSProvider):
    id = "elevenlabs"
    name = "ElevenLabs"
    icon = "icons/elevenlabs.png"

    def is_ready(self) -> bool:
        return bool(self.settings.elevenlabs_api_key)

    def setup_hint(self) -> str:
        return "在 Workflow 配置中填写 ELEVENLABS_API_KEY"

    def default_voice(self, text: str = "") -> str:
        configured = _canonical_voice(self.settings.elevenlabs_voice_id)
        return configured or _SARAH

    def resolved_voice(self, request: SynthesizeRequest) -> str:
        return _canonical_voice(super().resolved_voice(request)) or _SARAH

    def resolved_model(self, request: SynthesizeRequest) -> str:
        return request.model or self.settings.elevenlabs_model or ELEVENLABS_MODEL_DEFAULT

    def resolved_speed(self, request: SynthesizeRequest) -> float:
        if not _model_supports_speed(self.resolved_model(request)):
            return 1.0
        return min(1.2, max(0.7, request.speed or 1.0))

    def speed_notice(self, request: SynthesizeRequest) -> str:
        if abs((request.speed or 1.0) - 1.0) < 0.001:
            return ""
        if _model_supports_speed(self.resolved_model(request)):
            return ""
        return "Eleven v3 / v4 / v4 Turbo 不支持语速倍率，已按原速朗读。需要变速请改用 Flash v2.5。"

    def preset_voices(self) -> list[VoicePreset]:
        presets = [
            VoicePreset(_SARAH, "Sarah"),
            VoicePreset(_RACHEL, "Rachel"),
            VoicePreset(_GEORGE, "George"),
            VoicePreset(_DANIEL, "Daniel"),
            VoicePreset(_LILY, "Lily"),
            VoicePreset(_ADAM, "Adam"),
        ]
        custom = _canonical_voice(self.settings.elevenlabs_voice_id)
        if custom and custom not in {item.id for item in presets}:
            presets.insert(0, VoicePreset(custom, "自定义 Voice ID"))
        return presets

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        dest = dest.with_suffix(".mp3")
        dest.parent.mkdir(parents=True, exist_ok=True)
        voice = self.resolved_voice(request)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
        headers = {
            "xi-api-key": self.settings.elevenlabs_api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {"text": request.text, "model_id": self.resolved_model(request)}
        speed = self.resolved_speed(request)
        if abs(speed - 1.0) >= 0.001:
            payload["voice_settings"] = {"speed": speed}
        with httpx_client(self.settings, overseas=True) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code == 402:
                raise RuntimeError(_paid_plan_message(voice))
            dest.write_bytes(audio_bytes(response, "ElevenLabs"))
        return dest


def _paid_plan_message(voice: str) -> str:
    return (
        f"ElevenLabs 免费套餐不能通过 API 使用这个库音色（当前 {voice}）。"
        f"可改用 Sarah（{_SARAH}）等 Default 音色，"
        "或把你自己的 Voice ID 填到 ELEVENLABS_VOICE_ID。"
    )


def _model_supports_speed(model: str) -> bool:
    name = (model or "").lower()
    return not name.startswith("eleven_v3") and not name.startswith("eleven_v4")


def _canonical_voice(voice: str) -> str:
    cleaned = (voice or "").strip()
    if not cleaned or cleaned == "auto":
        return ""
    return _PRESET_BY_LABEL.get(cleaned.lower(), cleaned)
