from __future__ import annotations

import base64
import uuid
from pathlib import Path

from alfred_tts.http import body_error, httpx_client
from alfred_tts.models import SynthesizeRequest
from alfred_tts.providers.base import TTSProvider, VoicePreset

VOLC_CLUSTER_DEFAULT = "volcano_tts"


class VolcengineTTSProvider(TTSProvider):
    id = "volcengine"
    name = "火山引擎"
    icon = "icons/volcengine.png"

    def is_ready(self) -> bool:
        return bool(self.settings.volc_appid and self.settings.volc_token)

    def setup_hint(self) -> str:
        return "在 Workflow 配置中填写 VOLC_APPID 与 VOLC_TOKEN"

    def default_voice(self, text: str = "") -> str:
        return "BV001_streaming"

    def preset_voices(self) -> list[VoicePreset]:
        return [
            VoicePreset("BV001_streaming", "通用女声"),
            VoicePreset("BV002_streaming", "通用男声"),
            VoicePreset("zh_female_qingxin", "清新女声"),
            VoicePreset("zh_male_chunhou", "醇厚男声"),
            VoicePreset("ICL_zh_female_aojiaoniang_tob", "傲娇女友 · ICL"),
        ]

    def synthesize(self, request: SynthesizeRequest, dest: Path) -> Path:
        dest = dest.with_suffix(".mp3")
        dest.parent.mkdir(parents=True, exist_ok=True)
        voice = self.resolved_voice(request)
        cluster = self.settings.volc_cluster or VOLC_CLUSTER_DEFAULT
        if voice.startswith("ICL_") and cluster == VOLC_CLUSTER_DEFAULT:
            cluster = "volcano_icl"
        token = self.settings.volc_token
        payload = {
            "app": {
                "appid": self.settings.volc_appid,
                "token": token,
                "cluster": cluster,
            },
            "user": {"uid": "alfred-tts"},
            "audio": {
                "voice_type": voice,
                "encoding": "mp3",
                "speed_ratio": request.speed or 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": request.text,
                "text_type": "plain",
                "operation": "query",
            },
        }
        headers = {
            "Authorization": f"Bearer;{token}",
            "Content-Type": "application/json",
        }
        with httpx_client(self.settings, overseas=False) as client:
            response = client.post(
                "https://openspeech.bytedance.com/api/v1/tts",
                headers=headers,
                json=payload,
            )
            dest.write_bytes(_extract_audio(response))
        return dest


def _extract_audio(response) -> bytes:
    if response.status_code >= 400:
        raise RuntimeError(f"火山引擎 HTTP {response.status_code}: {body_error(response)}")
    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError("火山引擎 响应无法解析") from exc
    if not isinstance(data, dict):
        raise RuntimeError("火山引擎 响应格式异常")
    code = data.get("code")
    raw = data.get("data")
    if code not in (3000, "3000") or not raw:
        raise RuntimeError(f"火山引擎: {data.get('message') or code or '未返回音频'}")
    audio = base64.b64decode(raw)
    if len(audio) < 16:
        raise RuntimeError("火山引擎 返回空音频")
    return audio
