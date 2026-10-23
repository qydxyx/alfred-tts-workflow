from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Action(StrEnum):
    PLAY = "play"
    COPY_FILE = "copy_file"
    SAVE = "save"
    STOP = "stop"
    SETUP = "setup"
    INSTALL_KOKORO = "install_kokoro"
    REMOVE_KOKORO = "remove_kokoro"
    SET_DEFAULT = "set_default"
    SET_VOICE = "set_voice"
    CLEAR_CACHE = "clear_cache"
    OPEN_CONFIG = "open_config"


@dataclass(slots=True)
class SynthesizeRequest:
    provider: str
    text: str
    voice: str = ""
    model: str = ""
    speed: float = 1.0
    style: str = ""


@dataclass(slots=True)
class SynthesizeResult:
    path: Path
    provider: str
    cached: bool = False
    suffix: str = ".mp3"


@dataclass(slots=True)
class AlfredModifier:
    subtitle: str
    arg: str = ""
    valid: bool = True
    variables: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "subtitle": self.subtitle,
            "valid": self.valid,
        }
        if self.arg:
            payload["arg"] = self.arg
        if self.variables:
            payload["variables"] = self.variables
        return payload


@dataclass(slots=True)
class AlfredItem:
    title: str
    subtitle: str = ""
    arg: str = ""
    valid: bool = True
    icon: str | None = None
    mods: dict[str, AlfredModifier] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)
    autocomplete: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": self.title,
            "subtitle": self.subtitle,
            "valid": self.valid,
        }
        if self.arg:
            payload["arg"] = self.arg
        if self.icon:
            payload["icon"] = {"path": self.icon}
        if self.mods:
            payload["mods"] = {key: mod.to_dict() for key, mod in self.mods.items()}
        if self.variables:
            payload["variables"] = self.variables
        if self.autocomplete is not None:
            payload["autocomplete"] = self.autocomplete
        return payload


@dataclass(slots=True)
class AlfredResponse:
    items: list[AlfredItem]
    skipknowledge: bool = True
    rerun: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "skipknowledge": self.skipknowledge,
            "items": [item.to_dict() for item in self.items],
        }
        if self.rerun is not None:
            payload["rerun"] = self.rerun
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
