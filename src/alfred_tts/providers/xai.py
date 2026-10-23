from __future__ import annotations

from pathlib import Path

from alfred_tts.http import audio_bytes, httpx_client
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset
from alfred_tts.query import has_cjk


class XAITTSProvider(TTSProvider):
    id = "xai"
    name = "xAI Grok"
    icon = "icons/xai.png"

    def is_ready(self) -> bool:
        return bool(self.settings.xai_api_key)

    def setup_hint(self) -> str:
        return "在 Workflow 配置中填写 XAI_API_KEY"

    def default_voice(self, text: str = "") -> str:
        return "eve"

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset("eve", "Eve"),
            VoicePreset("ara", "Ara"),
            VoicePreset("leo", "Leo"),
            VoicePreset("rex", "Rex"),
            VoicePreset("sal", "Sal"),
        ]

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        dest = dest.with_suffix(".mp3")
        dest.parent.mkdir(parents=True, exist_ok=True)
        language = "zh" if has_cjk(request.text) else "en"
        payload = {
            "text": request.text,
            "voice_id": self.resolved_voice(request),
            "language": language,
            "output_format": {"codec": "mp3", "sample_rate": 24000, "bit_rate": 128000},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.xai_api_key}",
            "Content-Type": "application/json",
        }
        with httpx_client(self.settings, overseas=True) as client:
            response = client.post("https://api.x.ai/v1/tts", headers=headers, json=payload)
            dest.write_bytes(audio_bytes(response, "xAI TTS"))
        return dest
