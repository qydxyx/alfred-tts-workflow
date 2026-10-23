from __future__ import annotations

from pathlib import Path

from alfred_tts.http import audio_bytes, httpx_client
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset

OPENAI_BASE_DEFAULT = "https://api.openai.com/v1"
OPENAI_MODEL_DEFAULT = "gpt-4o-mini-tts"


class OpenAITTSProvider(TTSProvider):
    id = "openai"
    name = "OpenAI TTS"
    icon = "icons/openai.png"

    def is_ready(self) -> bool:
        return bool(self.settings.openai_api_key)

    def setup_hint(self) -> str:
        return "在 Workflow 配置中填写 OPENAI_API_KEY"

    def default_voice(self, text: str = "") -> str:
        return "coral"

    def resolved_model(self, request: SynthesizeRequest) -> str:
        return request.model or self.settings.openai_model or OPENAI_MODEL_DEFAULT

    def resolved_style(self, request: SynthesizeRequest) -> str:
        return request.style or self.settings.openai_instructions

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset("coral", "coral"),
            VoicePreset("marin", "marin"),
            VoicePreset("cedar", "cedar"),
            VoicePreset("alloy", "alloy"),
            VoicePreset("nova", "nova"),
            VoicePreset("sage", "sage"),
            VoicePreset("verse", "verse"),
            VoicePreset("ash", "ash"),
        ]

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        dest = dest.with_suffix(".mp3")
        dest.parent.mkdir(parents=True, exist_ok=True)
        model = self.resolved_model(request)
        payload: dict[str, object] = {
            "model": model,
            "voice": self.resolved_voice(request),
            "input": request.text,
            "response_format": "mp3",
        }
        instructions = self.resolved_style(request)
        if instructions and "tts-1" not in model:
            payload["instructions"] = instructions
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        with httpx_client(self.settings, overseas=True) as client:
            response = client.post(_speech_url(self.settings.openai_base_url), headers=headers, json=payload)
            dest.write_bytes(audio_bytes(response, "OpenAI TTS"))
        return dest


def _speech_url(base: str) -> str:
    root = (base or OPENAI_BASE_DEFAULT).rstrip("/")
    if root.endswith("/v1"):
        return f"{root}/audio/speech"
    return f"{root}/v1/audio/speech"
