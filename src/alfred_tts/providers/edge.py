from __future__ import annotations

import asyncio
from pathlib import Path

from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset
from alfred_tts.query import has_cjk


class EdgeTTSProvider(TTSProvider):
    id = "edge"
    name = "Edge TTS"
    icon = "icons/edge.png"

    def is_ready(self) -> bool:
        return True

    def setup_hint(self) -> str:
        return ""

    def default_voice(self, text: str = "") -> str:
        if has_cjk(text):
            return "zh-CN-XiaoxiaoNeural"
        return "en-US-AriaNeural"

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset("auto", "自动（中文晓晓 / 英文 Aria）"),
            VoicePreset("zh-CN-XiaoxiaoNeural", "晓晓 · 女声"),
            VoicePreset("zh-CN-YunxiNeural", "云希 · 男声"),
            VoicePreset("zh-CN-YunyangNeural", "云扬 · 男声"),
            VoicePreset("zh-CN-XiaoyiNeural", "晓伊 · 女声"),
            VoicePreset("en-US-AriaNeural", "Aria · English"),
            VoicePreset("en-US-JennyNeural", "Jenny · English"),
            VoicePreset("en-US-GuyNeural", "Guy · English"),
        ]

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        import edge_tts

        voice = self.resolved_voice(request)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest = dest.with_suffix(".mp3")
        proxy = self.settings.proxy_url

        async def _run() -> None:
            communicate = edge_tts.Communicate(request.text, voice)
            if proxy:
                # edge-tts talks to Microsoft cloud; honour the same overseas proxy.
                import os

                os.environ.setdefault("HTTPS_PROXY", proxy)
                os.environ.setdefault("HTTP_PROXY", proxy)
                os.environ.setdefault("https_proxy", proxy)
                os.environ.setdefault("http_proxy", proxy)
            await communicate.save(str(dest))

        asyncio.run(_run())
        if not dest.exists() or dest.stat().st_size == 0:
            raise RuntimeError("Edge TTS 返回空音频")
        return dest
