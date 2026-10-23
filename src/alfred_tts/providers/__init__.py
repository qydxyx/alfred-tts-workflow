from __future__ import annotations

from alfred_tts.config import Settings
from alfred_tts.providers.aliyun import AliyunTTSProvider
from alfred_tts.providers.base import TTSProvider
from alfred_tts.providers.deepgram import DeepgramTTSProvider
from alfred_tts.providers.edge import EdgeTTSProvider
from alfred_tts.providers.elevenlabs import ElevenLabsTTSProvider
from alfred_tts.providers.gemini import GeminiTTSProvider
from alfred_tts.providers.kokoro import KokoroProvider
from alfred_tts.providers.openai import OpenAITTSProvider
from alfred_tts.providers.volcengine import VolcengineTTSProvider
from alfred_tts.providers.xai import XAITTSProvider

PROVIDERS: tuple[type[TTSProvider], ...] = (
    EdgeTTSProvider,
    GeminiTTSProvider,
    OpenAITTSProvider,
    ElevenLabsTTSProvider,
    DeepgramTTSProvider,
    XAITTSProvider,
    AliyunTTSProvider,
    VolcengineTTSProvider,
    KokoroProvider,
)


class ProviderRegistry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._providers = {cls.id: cls(settings) for cls in PROVIDERS}

    def get(self, provider_id: str) -> TTSProvider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(f"未知引擎: {provider_id}") from exc

    def all(self) -> list[TTSProvider]:
        return list(self._providers.values())

    def ready(self, eager_id: str | None = None) -> list[TTSProvider]:
        result: list[TTSProvider] = []
        for provider in self.all():
            if isinstance(provider, KokoroProvider):
                eager = eager_id == "kokoro" or self.settings.default_provider == "kokoro"
                ok = provider.is_ready(eager_probe=eager)
            else:
                ok = provider.is_ready()
            if ok:
                result.append(provider)
        return result

    def ordered_ready(self, preferred: str | None = None) -> list[TTSProvider]:
        default_id = preferred or self.settings.default_provider
        ready = self.ready(eager_id=preferred)
        ready.sort(key=lambda item: (item.id != default_id, item.id))
        return ready
