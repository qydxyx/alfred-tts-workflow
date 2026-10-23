from __future__ import annotations

import time
from pathlib import Path

import httpx

from alfred_tts.config import KOKORO_API_PROBE_TTL_S, load_state, models_dir, update_state
from alfred_tts.installer import kokoro_files_ready, kokoro_model_paths
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset
from alfred_tts.query import has_cjk


class KokoroProvider(TTSProvider):
    id = "kokoro"
    name = "Kokoro"
    icon = "icons/kokoro.png"

    def is_ready(self, eager_probe: bool = False) -> bool:
        if self.settings.kokoro_mode in {"onnx", "auto"} and kokoro_files_ready():
            return True
        if self.settings.kokoro_mode in {"api", "auto"}:
            return self._cached_api_ready(probe=eager_probe or self.settings.kokoro_mode == "api")
        return False

    def needs_install(self) -> bool:
        if self.settings.kokoro_mode == "api":
            return not self._cached_api_ready(force=True)
        if kokoro_files_ready():
            return False
        if self.settings.kokoro_mode == "onnx":
            return True
        return not self._cached_api_ready(force=True)

    def setup_hint(self) -> str:
        if self.settings.kokoro_install_status == "installing":
            return "正在安装 Kokoro 模型…"
        return "输入 tts @kokoro 按需安装本地模型，或启动本地 Kokoro API"

    def default_voice(self, text: str = "") -> str:
        if has_cjk(text):
            return "zf_001"
        return "af_heart"

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset("zf_001", "zf_001 · 中文女声"),
            VoicePreset("zm_010", "zm_010 · 中文男声"),
            VoicePreset("af_heart", "af_heart · English"),
            VoicePreset("af_bella", "af_bella · English"),
            VoicePreset("am_adam", "am_adam · English"),
        ]

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        dest = dest.with_suffix(".wav")
        dest.parent.mkdir(parents=True, exist_ok=True)
        mode = self.settings.kokoro_mode
        if mode == "api" or (mode == "auto" and self._cached_api_ready()):
            return self._synthesize_api(request, dest)
        if mode == "onnx" or kokoro_files_ready():
            return self._synthesize_onnx(request, dest)
        if self._cached_api_ready(force=True):
            return self._synthesize_api(request, dest)
        raise RuntimeError("Kokoro 未就绪：请先安装本地模型或启动本地 API")

    def _cached_api_ready(self, force: bool = False, probe: bool = True) -> bool:
        state = load_state()
        kokoro = state.get("kokoro") if isinstance(state.get("kokoro"), dict) else {}
        last_ok = float(kokoro.get("last_api_ok_at") or 0)
        last_fail = float(kokoro.get("last_api_fail_at") or 0)
        now = time.time()
        if not force and last_ok and now - last_ok < KOKORO_API_PROBE_TTL_S:
            return True
        if not force and last_fail and now - last_fail < KOKORO_API_PROBE_TTL_S:
            return False
        if not probe and not force:
            return bool(last_ok)
        ok = self._probe_api()
        if ok:
            update_state(kokoro={"last_api_ok_at": now, "last_api_fail_at": 0})
        else:
            update_state(kokoro={"last_api_fail_at": now})
        return ok

    def _probe_api(self) -> bool:
        base = self.settings.kokoro_api_base.rstrip("/")
        try:
            with httpx.Client(timeout=0.1, trust_env=False) as client:
                for path in ("/models", "/audio/speech"):
                    try:
                        response = client.get(f"{base}{path}")
                        if response.status_code < 500:
                            return True
                    except httpx.HTTPError:
                        continue
        except httpx.HTTPError:
            return False
        return False

    def _synthesize_api(self, request: SynthesizeRequest, dest: Path) -> Path:
        base = self.settings.kokoro_api_base.rstrip("/")
        voice = self.resolved_voice(request)
        with httpx.Client(timeout=60.0, trust_env=False) as client:
            response = client.post(
                f"{base}/audio/speech",
                json={
                    "model": "kokoro",
                    "input": request.text,
                    "voice": voice,
                    "response_format": "wav",
                    "speed": request.speed,
                },
            )
            response.raise_for_status()
            dest.write_bytes(response.content)
        if dest.stat().st_size == 0:
            raise RuntimeError("Kokoro API 返回空音频")
        return dest

    def _synthesize_onnx(self, request: SynthesizeRequest, dest: Path) -> Path:
        try:
            import soundfile as sf
            from kokoro_onnx import Kokoro
            from misaki import zh
        except ImportError as exc:
            raise RuntimeError("Kokoro 依赖未安装，请先执行按需安装") from exc

        variant = kokoro_files_ready() or self.settings.kokoro_variant or "fp32"
        model_path, voices_path = kokoro_model_paths(variant)
        if not model_path.exists():
            # int8 vs fp32 filename; scan directory
            found = next(models_dir().glob("kokoro-v1.1-zh*.onnx"), None)
            if found is None:
                raise RuntimeError("未找到 Kokoro ONNX 模型文件")
            model_path = found
        voice = self.resolved_voice(request)
        kokoro = Kokoro(str(model_path), str(voices_path))
        if has_cjk(request.text):
            g2p = zh.ZHG2P(version="1.1")
            phonemes, _ = g2p(request.text)
            samples, sample_rate = kokoro.create(
                phonemes, voice=voice, speed=request.speed, is_phonemes=True
            )
        else:
            samples, sample_rate = kokoro.create(request.text, voice=voice, speed=request.speed)
        sf.write(str(dest), samples, sample_rate)
        return dest
