from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import httpx

from alfred_tts.config import data_dir, models_dir, update_state, venv_python
from alfred_tts.player import notify

CORE_PACKAGES = [
    "httpx[socks]>=0.28.0",
    "edge-tts>=7.3.1",
    "google-genai>=2.30.1",
]
KOKORO_PACKAGES = [
    "kokoro-onnx>=0.4.0",
    "misaki[zh]>=0.8.0",
    "soundfile>=0.13.0",
]
KOKORO_RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1"
KOKORO_FILES = {
    "fp32": {
        "model": "kokoro-v1.1-zh.onnx",
        "voices": "voices-v1.1-zh.bin",
        "size_label": "~379MB",
    },
    "int8": {
        "model": "kokoro-v1.1-zh.int8.onnx",
        "voices": "voices-v1.1-zh.bin",
        "size_label": "~167MB",
    },
}


def which_uv() -> Path | None:
    found = shutil.which("uv")
    if found:
        return Path(found)
    for candidate in (
        Path.home() / ".local/bin/uv",
        Path("/opt/homebrew/bin/uv"),
        Path("/usr/local/bin/uv"),
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def core_venv_ready() -> bool:
    python = venv_python()
    if python.is_file() and os.access(python, os.X_OK):
        return True
    try:
        import edge_tts  # noqa: F401
        import google.genai  # noqa: F401
        import httpx  # noqa: F401
    except ImportError:
        return False
    return True


def kokoro_model_paths(variant: str = "fp32") -> tuple[Path, Path]:
    spec = KOKORO_FILES[variant]
    directory = models_dir()
    return directory / spec["model"], directory / spec["voices"]


def kokoro_files_ready(variant: str | None = None) -> str | None:
    variants = [variant] if variant else ["fp32", "int8"]
    for name in variants:
        model, voices = kokoro_model_paths(name)
        if model.exists() and model.stat().st_size > 0 and voices.exists() and voices.stat().st_size > 0:
            return name
    return None


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def setup_core_venv() -> Path:
    uv = which_uv()
    if uv is None:
        raise RuntimeError("未找到 uv。请先安装：curl -LsSf https://astral.sh/uv/install.sh | sh")
    venv = data_dir() / ".venv"
    _run([str(uv), "venv", str(venv), "--python", "3.11"])
    python = venv / "bin" / "python"
    _run([str(uv), "pip", "install", "--python", str(python), *CORE_PACKAGES])
    return python


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as response:
        response.raise_for_status()
        with part.open("wb") as handle:
            for chunk in response.iter_bytes(1024 * 256):
                handle.write(chunk)
    if part.stat().st_size <= 0:
        part.unlink(missing_ok=True)
        raise RuntimeError(f"下载为空: {url}")
    part.replace(dest)


def install_kokoro(variant: str = "fp32") -> None:
    if variant not in KOKORO_FILES:
        raise ValueError(f"未知 Kokoro 变体: {variant}")
    update_state(kokoro={"install_status": "installing", "installed_variant": ""})
    notify("Alfred TTS", f"正在后台安装 Kokoro（{KOKORO_FILES[variant]['size_label']}）…")
    try:
        if not core_venv_ready():
            setup_core_venv()
        uv = which_uv()
        if uv is None:
            raise RuntimeError("未找到 uv")
        _run([str(uv), "pip", "install", "--python", str(venv_python()), *KOKORO_PACKAGES])
        spec = KOKORO_FILES[variant]
        model_dest, voices_dest = kokoro_model_paths(variant)
        _download(f"{KOKORO_RELEASE}/{spec['model']}", model_dest)
        _download(f"{KOKORO_RELEASE}/{spec['voices']}", voices_dest)
        update_state(kokoro={"install_status": "idle", "installed_variant": variant})
        notify("Alfred TTS", "Kokoro 已就绪，可输入 tts @kokoro 使用")
    except Exception as exc:
        update_state(kokoro={"install_status": "error", "last_error": str(exc)})
        notify("Alfred TTS", f"Kokoro 安装失败: {exc}")
        raise


def remove_kokoro_models() -> int:
    removed = 0
    directory = models_dir()
    if directory.exists():
        for path in directory.iterdir():
            if path.is_file():
                path.unlink()
                removed += 1
    update_state(kokoro={"install_status": "idle", "installed_variant": ""})
    return removed


def spawn_install_kokoro(variant: str) -> None:
    update_state(kokoro={"install_status": "installing"})
    log = data_dir() / "install-kokoro.log"
    with log.open("ab") as handle:
        subprocess.Popen(
            [sys.executable, "-m", "alfred_tts", "install-kokoro", "--variant", variant],
            stdout=handle,
            stderr=handle,
            start_new_session=True,
        )
