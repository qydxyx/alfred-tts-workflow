from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BUNDLE_ID = "com.qydxyx.alfred-tts"
DEFAULT_PROVIDER = "edge"
EXPORT_DIR_DEFAULT = "~/Downloads/Alfred-TTS"
KOKORO_MODE_DEFAULT = "auto"
KOKORO_API_BASE_DEFAULT = "http://127.0.0.1:8880/v1"
GEMINI_MODEL_DEFAULT = "gemini-3.8-flash-lite-tts"
OPENAI_BASE_DEFAULT = "https://api.openai.com/v1"
OPENAI_MODEL_DEFAULT = "gpt-4o-mini-tts"
ELEVENLABS_MODEL_DEFAULT = "eleven_flash_v2_5"
ALIYUN_BASE_DEFAULT = "https://dashscope.aliyuncs.com/api/v1"
ALIYUN_MODEL_DEFAULT = "cosyvoice-v3-flash"
VOLC_CLUSTER_DEFAULT = "volcano_tts"
KOKORO_API_PROBE_TTL_S = 30.0
MAX_CACHE_ITEMS = 200


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def data_dir() -> Path:
    raw = _env("alfred_workflow_data")
    path = Path(raw) if raw else Path.home() / "Library/Application Support/Alfred/Workflow Data" / BUNDLE_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir() -> Path:
    raw = _env("alfred_workflow_cache")
    path = (
        Path(raw)
        if raw
        else Path.home() / "Library/Caches/com.runningwithcrayons.Alfred/Workflow Data" / BUNDLE_ID
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def venv_python() -> Path:
    return data_dir() / ".venv" / "bin" / "python"


def models_dir() -> Path:
    path = data_dir() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_path() -> Path:
    return data_dir() / "state.json"


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    path = state_path()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def update_state(**kwargs: Any) -> dict[str, Any]:
    state = load_state()
    for key, value in kwargs.items():
        if isinstance(value, dict) and isinstance(state.get(key), dict):
            merged = dict(state[key])
            merged.update(value)
            state[key] = merged
        else:
            state[key] = value
    save_state(state)
    return state


@dataclass(slots=True)
class Settings:
    default_provider: str = DEFAULT_PROVIDER
    export_dir: str = EXPORT_DIR_DEFAULT
    proxy_url: str = ""
    gemini_api_key: str = ""
    gemini_model: str = GEMINI_MODEL_DEFAULT
    gemini_style: str = ""
    openai_api_key: str = ""
    openai_base_url: str = OPENAI_BASE_DEFAULT
    openai_model: str = OPENAI_MODEL_DEFAULT
    openai_instructions: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_model: str = ELEVENLABS_MODEL_DEFAULT
    deepgram_api_key: str = ""
    xai_api_key: str = ""
    dashscope_api_key: str = ""
    dashscope_base_url: str = ALIYUN_BASE_DEFAULT
    aliyun_model: str = ALIYUN_MODEL_DEFAULT
    volc_appid: str = ""
    volc_token: str = ""
    volc_cluster: str = VOLC_CLUSTER_DEFAULT
    kokoro_mode: str = KOKORO_MODE_DEFAULT
    kokoro_api_base: str = KOKORO_API_BASE_DEFAULT
    voices: dict[str, str] = field(default_factory=dict)
    kokoro_variant: str = ""
    kokoro_install_status: str = "idle"

    @property
    def export_path(self) -> Path:
        return Path(self.export_dir).expanduser()


def load_settings() -> Settings:
    state = load_state()
    voices = state.get("voices") if isinstance(state.get("voices"), dict) else {}
    kokoro = state.get("kokoro") if isinstance(state.get("kokoro"), dict) else {}
    default_provider = state.get("default_provider") or _env("DEFAULT_PROVIDER", DEFAULT_PROVIDER)
    return Settings(
        default_provider=str(default_provider or DEFAULT_PROVIDER),
        export_dir=_env("EXPORT_DIR", EXPORT_DIR_DEFAULT) or EXPORT_DIR_DEFAULT,
        proxy_url=_env("PROXY_URL"),
        gemini_api_key=_env("GEMINI_API_KEY"),
        gemini_model=_env("GEMINI_MODEL", GEMINI_MODEL_DEFAULT) or GEMINI_MODEL_DEFAULT,
        gemini_style=_env("GEMINI_STYLE"),
        openai_api_key=_env("OPENAI_API_KEY"),
        openai_base_url=_env("OPENAI_BASE_URL", OPENAI_BASE_DEFAULT) or OPENAI_BASE_DEFAULT,
        openai_model=_env("OPENAI_MODEL", OPENAI_MODEL_DEFAULT) or OPENAI_MODEL_DEFAULT,
        openai_instructions=_env("OPENAI_INSTRUCTIONS"),
        elevenlabs_api_key=_env("ELEVENLABS_API_KEY"),
        elevenlabs_model=_env("ELEVENLABS_MODEL", ELEVENLABS_MODEL_DEFAULT) or ELEVENLABS_MODEL_DEFAULT,
        deepgram_api_key=_env("DEEPGRAM_API_KEY"),
        xai_api_key=_env("XAI_API_KEY"),
        dashscope_api_key=_env("DASHSCOPE_API_KEY"),
        dashscope_base_url=_env("DASHSCOPE_BASE_URL", ALIYUN_BASE_DEFAULT) or ALIYUN_BASE_DEFAULT,
        aliyun_model=_env("ALIYUN_MODEL", ALIYUN_MODEL_DEFAULT) or ALIYUN_MODEL_DEFAULT,
        volc_appid=_env("VOLC_APPID"),
        volc_token=_env("VOLC_TOKEN"),
        volc_cluster=_env("VOLC_CLUSTER", VOLC_CLUSTER_DEFAULT) or VOLC_CLUSTER_DEFAULT,
        kokoro_mode=_env("KOKORO_MODE", KOKORO_MODE_DEFAULT) or KOKORO_MODE_DEFAULT,
        kokoro_api_base=_env("KOKORO_API_BASE", KOKORO_API_BASE_DEFAULT) or KOKORO_API_BASE_DEFAULT,
        voices=dict(voices),
        kokoro_variant=str(kokoro.get("installed_variant") or ""),
        kokoro_install_status=str(kokoro.get("install_status") or "idle"),
    )


def voice_for(settings: Settings, provider: str, fallback: str = "") -> str:
    stored = settings.voices.get(provider)
    if stored:
        return stored
    return fallback
