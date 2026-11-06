from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from alfred_tts.config import Settings
from alfred_tts.models import SynthesizeRequest


@dataclass(frozen=True, slots=True)
class VoicePreset:
    id: str
    label: str


class TTSProvider(ABC):
    id: str
    name: str
    icon: str

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    def is_ready(self) -> bool:
        raise NotImplementedError

    def setup_hint(self) -> str:
        return ""

    def default_voice(self, text: str = "") -> str:
        return ""

    def preset_voices(self) -> list[VoicePreset]:
        return []

    def resolved_voice(self, request: SynthesizeRequest) -> str:
        if request.voice and request.voice != "auto":
            return request.voice
        stored = self.settings.voices.get(self.id, "")
        if stored and stored != "auto":
            return stored
        return self.default_voice(request.text)

    def resolved_model(self, request: SynthesizeRequest) -> str:
        return request.model

    def resolved_style(self, request: SynthesizeRequest) -> str:
        return request.style

    def resolved_speed(self, request: SynthesizeRequest) -> float:
        return _clamp_speed(request.speed, 0.5, 2.0)

    def speed_notice(self, request: SynthesizeRequest) -> str:
        return ""

    @abstractmethod
    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        raise NotImplementedError


def _clamp_speed(speed: float, low: float, high: float) -> float:
    try:
        value = float(speed)
    except (TypeError, ValueError):
        return 1.0
    if value <= 0:
        return 1.0
    return min(high, max(low, value))
