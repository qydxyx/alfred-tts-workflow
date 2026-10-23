from __future__ import annotations

from pathlib import Path

from alfred_tts.http import audio_bytes, httpx_client
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset

DEEPGRAM_VOICE_DEFAULT = "aura-2-thalia-en"


class DeepgramTTSProvider(TTSProvider):
    id = "deepgram"
    name = "Deepgram"
    icon = "icons/deepgram.png"

    def is_ready(self) -> bool:
        return bool(self.settings.deepgram_api_key)

    def setup_hint(self) -> str:
        return "在 Workflow 配置中填写 DEEPGRAM_API_KEY"

    def default_voice(self, text: str = "") -> str:
        return DEEPGRAM_VOICE_DEFAULT

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset("aura-2-thalia-en", "Thalia · en"),
            VoicePreset("aura-2-andromeda-en", "Andromeda · en"),
            VoicePreset("aura-2-helena-en", "Helena · en"),
            VoicePreset("aura-2-apollo-en", "Apollo · en"),
            VoicePreset("aura-2-arcas-en", "Arcas · en"),
            VoicePreset("aura-2-odysseus-en", "Odysseus · en"),
        ]

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        dest = dest.with_suffix(".mp3")
        dest.parent.mkdir(parents=True, exist_ok=True)
        voice = self.resolved_voice(request)
        url = f"https://api.deepgram.com/v1/speak?model={voice}&encoding=mp3"
        headers = {
            "Authorization": f"Token {self.settings.deepgram_api_key}",
            "Content-Type": "application/json",
        }
        with httpx_client(self.settings, overseas=True) as client:
            response = client.post(url, headers=headers, json={"text": request.text})
            dest.write_bytes(audio_bytes(response, "Deepgram"))
        return dest
