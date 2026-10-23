#!/usr/bin/env python3
"""Generate workflow/info.plist for Alfred 5."""

from __future__ import annotations

import plistlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "workflow" / "info.plist"

FILTER = "a11ed001-0001-4000-8000-000000000001"
RUN = "a11ed001-0001-4000-8000-000000000002"
CONFIG_FILTER = "a11ed001-0001-4000-8000-000000000003"
CONFIG_ACT = "a11ed001-0001-4000-8000-000000000004"
SETUP_KW = "a11ed001-0001-4000-8000-000000000005"
SETUP_RUN = "a11ed001-0001-4000-8000-000000000006"
UA = "a11ed001-0001-4000-8000-000000000007"
UA_RUN = "a11ed001-0001-4000-8000-000000000008"
HOTKEY = "a11ed001-0001-4000-8000-000000000009"


def script_filter(keyword: str, title: str, script: str, *, skip_ua: bool = True) -> dict:
    return {
        "type": "alfred.workflow.input.scriptfilter",
        "uid": FILTER if keyword == "tts" else CONFIG_FILTER,
        "version": 3,
        "config": {
            "alfredfiltersresults": False,
            "alfredfiltersresultsmatchmode": 0,
            "argumenttreatemptyqueryasnil": False,
            "argumenttype": 1,
            "escaping": 0,
            "keyword": keyword,
            "queuedelaycustom": 1,
            "queuedelayimmediatelyinitially": True,
            "queuedelaymode": 0,
            "queuemode": 2,
            "runningsubtext": "解析中…",
            "script": script,
            "scriptargtype": 1,
            "scriptfile": "",
            "skipuniversalaction": skip_ua,
            "subtext": title,
            "title": title,
            "type": 0,
            "withspace": True,
        },
    }


def run_script(uid: str, script: str) -> dict:
    return {
        "type": "alfred.workflow.action.script",
        "uid": uid,
        "version": 2,
        "config": {
            "concurrently": True,
            "escaping": 0,
            "script": script,
            "scriptargtype": 1,
            "scriptfile": "",
            "type": 0,
        },
    }


def keyword(uid: str, word: str, title: str) -> dict:
    return {
        "type": "alfred.workflow.input.keyword",
        "uid": uid,
        "version": 1,
        "config": {
            "argumenttype": 2,
            "keyword": word,
            "skipuniversalaction": True,
            "subtext": title,
            "text": title,
            "withspace": False,
        },
    }


def universal_action() -> dict:
    # Alfred stores these as accepts* (not camelCase). Wrong keys make Text Actions skip the trigger.
    return {
        "type": "alfred.workflow.trigger.universalaction",
        "uid": UA,
        "version": 1,
        "config": {
            "acceptsfiles": False,
            "acceptsmulti": 0,
            "acceptstext": True,
            "acceptsurls": True,
            "name": "Alfred TTS",
        },
    }


def selection_hotkey() -> dict:
    return {
        "type": "alfred.workflow.trigger.hotkey",
        "uid": HOTKEY,
        "version": 2,
        "config": {
            "action": 0,
            "argument": 1,
            "focusedappvariable": False,
            "focusedappvariablename": "",
            "hotkey": 0,
            "hotmod": 0,
            "hotstring": "",
            "leftcursor": False,
            "modsmode": 0,
            "relatedAppsMode": 0,
        },
    }


def popup(variable: str, label: str, description: str, default: str, pairs: list[tuple[str, str]]) -> dict:
    return {
        "variable": variable,
        "label": label,
        "description": description,
        "type": "popupbutton",
        "config": {
            "defaultvalue": default,
            "pairs": [[name, value] for name, value in pairs],
        },
    }


def textfield(variable: str, label: str, description: str, default: str = "", placeholder: str = "") -> dict:
    return {
        "variable": variable,
        "label": label,
        "description": description,
        "type": "textfield",
        "config": {
            "defaultvalue": default,
            "placeholder": placeholder,
            "required": False,
            "trim": True,
        },
    }


def filepicker(variable: str, label: str, description: str, default: str) -> dict:
    # Alfred File Picker filtermode: 0 = files and folders, 1 = folders, 2 = files.
    return {
        "variable": variable,
        "label": label,
        "description": description,
        "type": "filepicker",
        "config": {
            "defaultvalue": default,
            "filtermode": 1,
            "placeholder": "",
            "required": False,
        },
    }


def connect(src: str, dest: str) -> tuple[str, list[dict]]:
    return src, [{"destinationuid": dest, "modifiers": 0, "modifiersubtext": "", "vitoclose": False}]


def main() -> None:
    objects = [
        script_filter("tts", "用 Alfred TTS 朗读", './scripts/bootstrap.sh filter "$1"'),
        run_script(RUN, './scripts/bootstrap.sh run "$1"'),
        script_filter("tts-set", "Alfred TTS 设置", './scripts/bootstrap.sh config-filter "$1"'),
        run_script(CONFIG_ACT, './scripts/bootstrap.sh config-act "$1"'),
        keyword(SETUP_KW, "tts-setup", "修复 / 更新 Alfred TTS 环境"),
        run_script(SETUP_RUN, "./scripts/bootstrap.sh setup"),
        universal_action(),
        run_script(UA_RUN, './scripts/bootstrap.sh speak "$1"'),
        selection_hotkey(),
    ]
    connections = dict(
        [
            connect(FILTER, RUN),
            connect(CONFIG_FILTER, CONFIG_ACT),
            connect(SETUP_KW, SETUP_RUN),
            connect(UA, FILTER),
            connect(HOTKEY, UA_RUN),
        ]
    )
    plist = {
        "bundleid": "com.qydxyx.alfred-tts",
        "category": "Tools",
        "connections": connections,
        "createdby": "alfred-tts-workflow",
        "description": "Multi-provider TTS for Alfred 5",
        "disabled": False,
        "name": "Alfred TTS",
        "objects": objects,
        "readme": (
            "输入 `tts <文本>` 朗读。默认引擎为免 Key 的 Edge TTS。\n\n"
            "↩ 播放 · ⌘↩ 复制音频文件 · ⌥↩ 保存并定位 · ⌃↩ 停止。\n"
            "选中文本后打开 Text Action，输入 tts，选择 Alfred TTS。\n"
            "首次运行回车即可完成轻量初始化。Kokoro 仅在需要时按需下载。"
        ),
        "uidata": {
            FILTER: {"xpos": 60, "ypos": 50},
            RUN: {"xpos": 360, "ypos": 50},
            CONFIG_FILTER: {"xpos": 60, "ypos": 210},
            CONFIG_ACT: {"xpos": 360, "ypos": 210},
            SETUP_KW: {"xpos": 60, "ypos": 370},
            SETUP_RUN: {"xpos": 360, "ypos": 370},
            UA: {"xpos": 60, "ypos": 530},
            UA_RUN: {"xpos": 360, "ypos": 690},
            HOTKEY: {"xpos": 60, "ypos": 690},
        },
        "userconfigurationconfig": [
            popup(
                "DEFAULT_PROVIDER",
                "默认引擎",
                "日常 tts 回车使用的引擎（仍可在列表中选其他已就绪引擎）",
                "edge",
                [
                    ("Edge TTS", "edge"),
                    ("Gemini TTS", "gemini"),
                    ("OpenAI TTS", "openai"),
                    ("ElevenLabs", "elevenlabs"),
                    ("Deepgram", "deepgram"),
                    ("xAI Grok", "xai"),
                    ("阿里云百炼", "aliyun"),
                    ("火山引擎", "volcengine"),
                    ("Kokoro", "kokoro"),
                ],
            ),
            filepicker("EXPORT_DIR", "导出目录", "⌥↩ 保存音频的位置", "~/Downloads/Alfred-TTS"),
            textfield(
                "PROXY_URL",
                "海外代理",
                "例如 http://127.0.0.1:7890。海外引擎走代理；阿里云 / 火山引擎 / 本地 Kokoro 直连。",
                placeholder="http://127.0.0.1:7890",
            ),
            textfield("GEMINI_API_KEY", "Gemini API Key", "填写后列表中出现 Gemini TTS"),
            popup(
                "GEMINI_MODEL",
                "Gemini 模型",
                "lite 更低延迟；flash 表现力更强",
                "gemini-3.8-flash-lite-tts",
                [
                    ("gemini-3.8-flash-lite-tts", "gemini-3.8-flash-lite-tts"),
                    ("gemini-3.8-flash-tts", "gemini-3.8-flash-tts"),
                ],
            ),
            textfield(
                "GEMINI_STYLE",
                "Gemini 默认语气",
                "写入 speech_metadata.style，例如 natural and clear",
                placeholder="natural and clear",
            ),
            textfield("OPENAI_API_KEY", "OpenAI API Key", "填写后列表中出现 OpenAI TTS"),
            textfield(
                "OPENAI_BASE_URL",
                "OpenAI Base URL",
                "兼容 /v1/audio/speech 的网关，可留空使用官方地址",
                "https://api.openai.com/v1",
                placeholder="https://api.openai.com/v1",
            ),
            popup(
                "OPENAI_MODEL",
                "OpenAI 模型",
                "gpt-4o-mini-tts 支持语气指令；tts-1 更低延迟",
                "gpt-4o-mini-tts",
                [
                    ("gpt-4o-mini-tts", "gpt-4o-mini-tts"),
                    ("tts-1", "tts-1"),
                    ("tts-1-hd", "tts-1-hd"),
                ],
            ),
            textfield(
                "OPENAI_INSTRUCTIONS",
                "OpenAI 语气",
                "仅 gpt-4o-mini-tts 生效，例如 Speak in a calm, clear tone",
                placeholder="Speak in a calm, clear tone",
            ),
            textfield("ELEVENLABS_API_KEY", "ElevenLabs API Key", "填写后列表中出现 ElevenLabs"),
            popup(
                "ELEVENLABS_MODEL",
                "ElevenLabs 模型",
                "flash 更低延迟；multilingual_v2 更细腻",
                "eleven_flash_v2_5",
                [
                    ("eleven_flash_v2_5", "eleven_flash_v2_5"),
                    ("eleven_multilingual_v2", "eleven_multilingual_v2"),
                    ("eleven_v3", "eleven_v3"),
                ],
            ),
            textfield("DEEPGRAM_API_KEY", "Deepgram API Key", "填写后列表中出现 Deepgram Aura-2"),
            textfield("XAI_API_KEY", "xAI API Key", "填写后列表中出现 xAI Grok Voice"),
            textfield("DASHSCOPE_API_KEY", "阿里云百炼 API Key", "DashScope Key，填写后出现 CosyVoice"),
            textfield(
                "DASHSCOPE_BASE_URL",
                "百炼 Base URL",
                "国内默认北京；国际站改为 dashscope-intl.aliyuncs.com/api/v1",
                "https://dashscope.aliyuncs.com/api/v1",
            ),
            popup(
                "ALIYUN_MODEL",
                "百炼模型",
                "v3 带系统音色；v3.5 仅支持复刻/设计音色",
                "cosyvoice-v3-flash",
                [
                    ("cosyvoice-v3-flash", "cosyvoice-v3-flash"),
                    ("cosyvoice-v3-plus", "cosyvoice-v3-plus"),
                    ("cosyvoice-v2", "cosyvoice-v2"),
                ],
            ),
            textfield("VOLC_APPID", "火山引擎 AppID", "与 Token 一起填写后出现火山引擎"),
            textfield("VOLC_TOKEN", "火山引擎 Token", "openspeech HTTP 合成鉴权"),
            textfield(
                "VOLC_CLUSTER",
                "火山引擎 Cluster",
                "普通音色 volcano_tts；豆包 ICL 音色会自动切到 volcano_icl",
                "volcano_tts",
            ),
            popup(
                "KOKORO_MODE",
                "Kokoro 模式",
                "auto 优先本地 API，否则使用已安装的 ONNX 模型",
                "auto",
                [("auto", "auto"), ("onnx", "onnx"), ("api", "api")],
            ),
            textfield(
                "KOKORO_API_BASE",
                "Kokoro API",
                "本地 OpenAI 兼容端点，默认 Kokoro-FastAPI",
                "http://127.0.0.1:8880/v1",
            ),
        ],
        "version": "0.2.1",
        "webaddress": "https://github.com/qydxyx/alfred-tts-workflow",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("wb") as handle:
        plistlib.dump(plist, handle, sort_keys=False)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
