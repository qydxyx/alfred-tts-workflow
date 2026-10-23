from __future__ import annotations

from pathlib import Path

from alfred_tts.http import audio_bytes, httpx_client
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset

ELEVENLABS_MODEL_DEFAULT = "eleven_flash_v2_5"
# Premade library voices (public IDs).
_RACHEL = "21m00Tcm4TlvDq8ikWAM"
_SARAH = "EXAVITQu4vr4xnSDxMaL"
_GEORGE = "JBFqnCBsd6RMkjVDRZzb"
_DANIEL = "onwK4e9ZLuTAKqWW03F9"
_LILY = "pFZP5JQG7iQjIQuC4Bku"
_ADAM = "pNInz6obpgDQGcFmaJgB"


class ElevenLabsTTSProvider(TTSProvider):
    id = "elevenlabs"
    name = "ElevenLabs"
    icon = "icons/elevenlabs.png"

    def is_ready(self) -> bool:
        return bool(self.settings.elevenlabs_api_key)

    def setup_hint(self) -> str:
        return "在 Workflow 配置中填写 ELEVENLABS_API_KEY"

    def default_voice(self, text: str = "") -> str:
        return _RACHEL

    def resolved_model(self, request: SynthesizeRequest) -> str:
        return request.model or self.settings.elevenlabs_model or ELEVENLABS_MODEL_DEFAULT

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset(_RACHEL, "Rachel"),
            VoicePreset(_SARAH, "Sarah"),
            VoicePreset(_GEORGE, "George"),
            VoicePreset(_DANIEL, "Daniel"),
            VoicePreset(_LILY, "Lily"),
            VoicePreset(_ADAM, "Adam"),
        ]

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
        payload = {"text": request.text, "model_id": self.resolved_model(request)}
        with httpx_client(self.settings, overseas=True) as client:
            response = client.post(url, headers=headers, json=payload)
            dest.write_bytes(audio_bytes(response, "ElevenLabs"))
        return dest
