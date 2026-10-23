from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from alfred_tts.cache import clear as clear_cache
from alfred_tts.cache import lookup, store
from alfred_tts.config import load_settings, update_state, voice_for
from alfred_tts.installer import (
    KOKORO_FILES,
    core_venv_ready,
    install_kokoro,
    remove_kokoro_models,
    setup_core_venv,
    spawn_install_kokoro,
    which_uv,
)
from alfred_tts.models import Action, AlfredItem, AlfredModifier, AlfredResponse, SynthesizeRequest
from alfred_tts.payload import decode_payload, encode_payload
from alfred_tts.player import copy_audio_file_to_clipboard, notify, play_audio, save_and_reveal, stop_playback
from alfred_tts.providers import ProviderRegistry
from alfred_tts.providers.kokoro import KokoroProvider
from alfred_tts.query import ParsedQuery, parse_query

MOD_HINT = "↩ 播放  ·  ⌘↩ 复制音频  ·  ⌥↩ 保存  ·  ⌃↩ 停止"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="alfred-tts")
    sub = parser.add_subparsers(dest="command", required=True)

    filter_p = sub.add_parser("filter")
    filter_p.add_argument("query", nargs="?", default="")

    run_p = sub.add_parser("run")
    run_p.add_argument("arg", nargs="?", default="")

    speak_p = sub.add_parser("speak")
    speak_p.add_argument("text", nargs="?", default="")

    cfg_p = sub.add_parser("config-filter")
    cfg_p.add_argument("query", nargs="?", default="")

    sub.add_parser("config-act")
    sub.add_parser("setup")

    install_p = sub.add_parser("install-kokoro")
    install_p.add_argument("--variant", default="fp32", choices=("fp32", "int8"))

    sub.add_parser("remove-kokoro")
    sub.add_parser("stop")

    args = parser.parse_args(argv)
    command = args.command
    if command == "filter":
        _print_response(_cmd_filter(args.query))
        return 0
    if command == "config-filter":
        _print_response(_cmd_config_filter(args.query))
        return 0
    if command == "run":
        return _cmd_run(args.arg)
    if command == "speak":
        return _cmd_speak(args.text)
    if command == "config-act":
        return _cmd_run("")
    if command == "setup":
        return _cmd_setup()
    if command == "install-kokoro":
        install_kokoro(args.variant)
        return 0
    if command == "remove-kokoro":
        count = remove_kokoro_models()
        notify("Alfred TTS", f"已清理 {count} 个 Kokoro 模型文件")
        return 0
    if command == "stop":
        stop_playback()
        return 0
    parser.error(f"unknown command: {command}")
    return 2


def _print_response(response: AlfredResponse) -> None:
    sys.stdout.write(response.to_json())
    sys.stdout.flush()


def _cmd_filter(query: str) -> AlfredResponse:
    parsed = parse_query(query)
    if parsed.is_stop:
        return AlfredResponse(items=[_stop_item()])

    if not which_uv():
        return AlfredResponse(
            items=[
                AlfredItem(
                    title="需要先安装 uv",
                    subtitle="终端执行: curl -LsSf https://astral.sh/uv/install.sh | sh",
                    valid=False,
                )
            ]
        )

    if not core_venv_ready():
        return AlfredResponse(items=[_setup_item()])

    settings = load_settings()
    registry = ProviderRegistry(settings)

    if settings.kokoro_install_status == "installing" and (
        parsed.provider in {None, "kokoro"} or not parsed.text
    ):
        installing = AlfredItem(
            title="Kokoro 正在后台安装…",
            subtitle="完成后可直接使用。也可继续用 Edge TTS",
            valid=False,
            icon="icons/kokoro.png",
        )
        if not parsed.text:
            return AlfredResponse(items=[installing], rerun=1.0)

    if parsed.provider == "kokoro":
        kokoro = registry.get("kokoro")
        assert isinstance(kokoro, KokoroProvider)
        if kokoro.needs_install():
            return AlfredResponse(items=_kokoro_install_items(parsed))

    if not parsed.text:
        return AlfredResponse(
            items=[
                AlfredItem(
                    title="输入要朗读的文本",
                    subtitle="tts 你好  ·  tts @gemini 你好  ·  tts stop",
                    valid=False,
                )
            ]
        )

    if parsed.provider:
        try:
            provider = registry.get(parsed.provider)
        except KeyError:
            return AlfredResponse(
                items=[
                    AlfredItem(
                        title=f"未知引擎 @{parsed.provider}",
                        subtitle="可用: edge / gemini / kokoro",
                        valid=False,
                    )
                ]
            )
        ready = (
            provider.is_ready(eager_probe=True)
            if isinstance(provider, KokoroProvider)
            else provider.is_ready()
        )
        if not ready:
            return AlfredResponse(
                items=[
                    AlfredItem(
                        title=f"{provider.name} 尚未就绪",
                        subtitle=provider.setup_hint() or "请先完成配置",
                        valid=False,
                        icon=provider.icon,
                    )
                ]
            )
        providers = [provider]
    else:
        providers = registry.ordered_ready()

    if not providers:
        return AlfredResponse(items=[AlfredItem(title="没有已就绪的引擎", valid=False)])

    items = [_synth_item(provider, parsed, settings.default_provider) for provider in providers]
    return AlfredResponse(items=items)


def _cmd_config_filter(query: str) -> AlfredResponse:
    settings = load_settings()
    registry = ProviderRegistry(settings)
    needle = (query or "").strip().lower()
    items: list[AlfredItem] = []

    for provider in registry.all():
        title = f"设为默认 · {provider.name}"
        subtitle = "当前默认" if provider.id == settings.default_provider else "回车切换默认引擎"
        if needle and needle not in title.lower() and needle not in provider.id:
            continue
        items.append(
            _action_item(
                title=title,
                subtitle=subtitle,
                action=Action.SET_DEFAULT,
                extra={"provider": provider.id},
                icon=provider.icon,
            )
        )

    for provider in registry.all():
        current = voice_for(settings, provider.id, provider.default_voice())
        for voice in provider.preset_voices():
            label = f"{provider.name} 音色 · {voice.label}"
            if needle and needle not in label.lower() and needle not in voice.id.lower():
                continue
            mark = "当前 · " if voice.id == current else ""
            items.append(
                _action_item(
                    title=f"{mark}{label}",
                    subtitle=voice.id,
                    action=Action.SET_VOICE,
                    extra={"provider": provider.id, "voice": voice.id},
                    icon=provider.icon,
                )
            )

    items.extend(_kokoro_install_items(ParsedQuery(raw="", text=""), include_remove=True))
    items.append(
        _action_item(
            title="清空音频缓存",
            subtitle="删除已合成的本地缓存文件",
            action=Action.CLEAR_CACHE,
        )
    )
    return AlfredResponse(items=items)


def _cmd_run(arg: str) -> int:
    payload = decode_payload(arg)
    action = str(payload.get("action") or Action.PLAY)
    try:
        if action == Action.STOP:
            stop_playback()
            return 0
        if action == Action.SETUP:
            return _cmd_setup()
        if action == Action.INSTALL_KOKORO:
            variant = str(payload.get("variant") or "fp32")
            spawn_install_kokoro(variant)
            notify("Alfred TTS", "已开始后台安装 Kokoro")
            return 0
        if action == Action.REMOVE_KOKORO:
            count = remove_kokoro_models()
            notify("Alfred TTS", f"已清理 {count} 个 Kokoro 模型文件")
            return 0
        if action == Action.SET_DEFAULT:
            update_state(default_provider=str(payload.get("provider") or "edge"))
            notify("Alfred TTS", f"默认引擎已切换为 {payload.get('provider')}")
            return 0
        if action == Action.SET_VOICE:
            provider_id = str(payload.get("provider") or "")
            voice = str(payload.get("voice") or "")
            update_state(voices={provider_id: voice})
            notify("Alfred TTS", f"{provider_id} 音色已设为 {voice}")
            return 0
        if action == Action.CLEAR_CACHE:
            count = clear_cache()
            notify("Alfred TTS", f"已清空 {count} 个缓存文件")
            return 0
        if action == Action.OPEN_CONFIG:
            return 0

        text = str(payload.get("text") or "")
        provider_id = str(payload.get("provider") or load_settings().default_provider)
        if not text.strip():
            notify("Alfred TTS", "没有可朗读的文本")
            return 1
        result = _synthesize(provider_id, text, voice=str(payload.get("voice") or ""))
        if action == Action.COPY_FILE:
            copy_audio_file_to_clipboard(result, text)
            notify("Alfred TTS", "音频文件已复制到剪贴板")
            return 0
        if action == Action.SAVE:
            settings = load_settings()
            save_and_reveal(result, settings.export_path, provider_id, text)
            return 0
        play_audio(result)
        return 0
    except Exception as exc:
        notify("Alfred TTS", str(exc))
        return 1


def _cmd_speak(text: str) -> int:
    settings = load_settings()
    return _cmd_run(
        encode_payload({"action": Action.PLAY, "provider": settings.default_provider, "text": text})
    )


def _cmd_setup() -> int:
    try:
        setup_core_venv()
        notify("Alfred TTS", "环境已就绪，可直接 tts 朗读")
        return 0
    except Exception as exc:
        notify("Alfred TTS", f"初始化失败: {exc}")
        return 1


def _synthesize(provider_id: str, text: str, voice: str = "") -> Path:
    settings = load_settings()
    registry = ProviderRegistry(settings)
    provider = registry.get(provider_id)
    request = SynthesizeRequest(
        provider=provider.id,
        text=text,
        voice=voice or voice_for(settings, provider.id),
        model=provider.resolved_model(SynthesizeRequest(provider=provider.id, text=text)),
        style=provider.resolved_style(SynthesizeRequest(provider=provider.id, text=text)),
    )
    request.voice = provider.resolved_voice(request)
    cached = lookup(request)
    if cached is not None:
        return cached
    with tempfile.TemporaryDirectory(prefix="alfred-tts-") as tmp:
        dest = Path(tmp) / "out"
        produced = provider.synthesize(request, dest)
        return store(request, produced)


def _synth_item(provider, parsed: ParsedQuery, default_id: str) -> AlfredItem:
    settings = load_settings()
    request = SynthesizeRequest(
        provider=provider.id,
        text=parsed.text,
        voice=voice_for(settings, provider.id),
        model=provider.resolved_model(SynthesizeRequest(provider=provider.id, text=parsed.text)),
        style=provider.resolved_style(SynthesizeRequest(provider=provider.id, text=parsed.text)),
    )
    request.voice = provider.resolved_voice(request)
    cached = lookup(request) is not None
    prefix = "⚡ 已缓存 · " if cached else ""
    default_mark = "（默认）" if provider.id == default_id else ""
    payload = {
        "provider": provider.id,
        "text": parsed.text,
        "voice": request.voice,
    }
    return AlfredItem(
        title=f"{prefix}{provider.name}{default_mark}",
        subtitle=f"{request.voice}  ·  {MOD_HINT}",
        arg=encode_payload({**payload, "action": Action.PLAY}),
        icon=provider.icon,
        variables=_vars(Action.PLAY, payload),
        mods={
            "cmd": AlfredModifier(
                subtitle="复制音频文件到剪贴板",
                arg=encode_payload({**payload, "action": Action.COPY_FILE}),
                variables=_vars(Action.COPY_FILE, payload),
            ),
            "alt": AlfredModifier(
                subtitle="保存并在 Finder 中显示",
                arg=encode_payload({**payload, "action": Action.SAVE}),
                variables=_vars(Action.SAVE, payload),
            ),
            "ctrl": AlfredModifier(
                subtitle="停止播放",
                arg=encode_payload({"action": Action.STOP}),
                variables={"tts_action": Action.STOP},
            ),
        },
    )


def _setup_item() -> AlfredItem:
    return AlfredItem(
        title="首次运行：回车 3 秒完成初始化",
        subtitle="仅安装轻量核心依赖（httpx / edge-tts / google-genai），无需 API Key",
        arg=encode_payload({"action": Action.SETUP}),
        variables={"tts_action": Action.SETUP},
    )


def _stop_item() -> AlfredItem:
    return AlfredItem(
        title="停止播放",
        subtitle="立即终止当前 afplay",
        arg=encode_payload({"action": Action.STOP}),
        variables={"tts_action": Action.STOP},
    )


def _kokoro_install_items(parsed: ParsedQuery, include_remove: bool = False) -> list[AlfredItem]:
    items = [
        _action_item(
            title="安装 Kokoro 标准版 FP32",
            subtitle=f"{KOKORO_FILES['fp32']['size_label']}  ·  中英双语，质量更好",
            action=Action.INSTALL_KOKORO,
            extra={"variant": "fp32", "text": parsed.text},
            icon="icons/kokoro.png",
        ),
        _action_item(
            title="安装 Kokoro 轻量版 INT8",
            subtitle=f"{KOKORO_FILES['int8']['size_label']}  ·  体积更小，适合节省磁盘",
            action=Action.INSTALL_KOKORO,
            extra={"variant": "int8", "text": parsed.text},
            icon="icons/kokoro.png",
        ),
    ]
    if include_remove:
        items.append(
            _action_item(
                title="清理 Kokoro 本地模型",
                subtitle="删除已下载的 ONNX 与音色库，释放磁盘",
                action=Action.REMOVE_KOKORO,
                icon="icons/kokoro.png",
            )
        )
    return items


def _action_item(
    title: str,
    subtitle: str,
    action: Action,
    extra: dict[str, str] | None = None,
    icon: str | None = None,
) -> AlfredItem:
    payload = {"action": action, **(extra or {})}
    return AlfredItem(
        title=title,
        subtitle=subtitle,
        arg=encode_payload(payload),
        icon=icon,
        variables=_vars(action, extra or {}),
    )


def _vars(action: Action | str, extra: dict[str, str]) -> dict[str, str]:
    mapping = {"tts_action": str(action)}
    if extra.get("provider"):
        mapping["tts_provider"] = extra["provider"]
    if extra.get("text"):
        mapping["tts_text"] = extra["text"]
    if extra.get("voice"):
        mapping["tts_voice"] = extra["voice"]
    if extra.get("variant"):
        mapping["tts_variant"] = extra["variant"]
    return mapping
