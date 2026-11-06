# Alfred TTS

Alfred 5 多引擎语音合成 Workflow。输入 `tts <文本>`，或对选中文字打开 **Text Action**，输入 `tts`，选择 **Alfred TTS**。

## 安装

从 [GitHub Releases](https://github.com/qydxyx/alfred-tts-workflow/releases) 下载 `Alfred-TTS.alfredworkflow`，双击导入 Alfred 5。

默认引擎是免 API Key 的 **Edge TTS**。首次运行只安装轻量核心依赖（约 2–3 秒），打字过程中不会调用任何合成接口。

## 动作

| 按键 | 行为 |
| --- | --- |
| `↩` | 后台朗读（自动停掉上一段） |
| `⌘↩` | 把音频文件写入剪贴板 |
| `⌥↩` | 保存到导出目录并在 Finder 中高亮 |
| `⌃↩` 或 `tts stop` | 停止播放 |

`tts @edge` / `@openai` / `@aliyun` 可指定引擎。未配置的引擎不会出现在日常列表里。

选中任意文本后打开 Alfred **Text Action**（Universal Actions），输入 `tts` 即可看到 **Alfred TTS**，回车后会带入这段文字并让你选引擎。也可以在 Workflow 画布里给左下角 Hotkey 绑定快捷键，直接朗读当前选中文本。

## 引擎

- **Edge TTS**：开箱即用，中文默认晓晓，英文默认 Aria。
- **Gemini TTS**：付费 API，`GEMINI_API_KEY`。默认 `gemini-3.8-flash-lite-tts` / `Kore`。预置音色见下文。
- **OpenAI TTS**：`OPENAI_API_KEY`。默认 `gpt-4o-mini-tts` / `coral`，可改 `OPENAI_BASE_URL`。
- **ElevenLabs**：`ELEVENLABS_API_KEY`。默认 Flash v2.5。单次覆盖音色用 `tts @elevenlabs voice:<VoiceID> 文本`（也接受 `v:` 或 `#`）。`ELEVENLABS_VOICE_ID` 是默认 Voice ID；`tts-set` 里选过的音色优先于这项配置。免费 API 不能用 Voice Library，可用音色见下文。

## ElevenLabs 免费 API 音色

2026-11-06 用免费 Key、`eleven_flash_v2_5` 实测，下列 Default 音色返回了音频。留空时工作流使用 Sarah（`EXAVITQu4vr4xnSDxMaL`）。官网 Playground 里的 Voice Library / 社区音色（例如 Lulu `itMkRQx56fOF4CJe1D0C`）会返回 402。Rachel（`21m00Tcm4TlvDq8ikWAM`）现在也算库音色，免费 API 同样 402。

官方说明：这些 Default 音色只对 2026 年 3 月前注册的账号开放，并在 2026-12-31 失效。替代音色在 Voice Library，免费 API 不能用。

| 音色 | Voice ID |
| --- | --- |
| Roger | `CwhRBWXzGAHq8TQ4Fs17` |
| Sarah | `EXAVITQu4vr4xnSDxMaL` |
| Laura | `FGY2WhTYpPnrIDTdsKH5` |
| Charlie | `IKne3meq5aSn9XLyUdCD` |
| George | `JBFqnCBsd6RMkjVDRZzb` |
| Callum | `N2lVS1w4EtoT3dr4eOWO` |
| River | `SAz9YHcvj6GT2YYXdXww` |
| Harry | `SOYHLrjzK2X1ezoPC6cr` |
| Liam | `TX3LPaxmHKxFdv7VOQHJ` |
| Alice | `Xb7hH8MSUJpSbSDYk0k2` |
| Matilda | `XrExE9yKIg1WjnnlVkGX` |
| Will | `bIHbv24MWmeRgasZH58o` |
| Jessica | `cgSgspJ2msm6clMCkdW9` |
| Eric | `cjVigY5qzO86Huf0OWal` |
| Chris | `iP95p4xoKVk53GoZ742B` |
| Brian | `nPczCjzI2devNBz1zQrb` |
| Daniel | `onwK4e9ZLuTAKqWW03F9` |
| Lily | `pFZP5JQG7iQjIQuC4Bku` |
| Bill | `pqHfZKP75CvOlQylNhV4` |
| Adam | `pNInz6obpgDQGcFmaJgB` |

## Gemini 付费 API 音色

`gemini-3.8-flash-lite-tts` 与 `gemini-3.8-flash-tts` 使用同一套预置音色名。下面是官方 30 个 studio voice。`tts-set` 里目前列出 Kore、Puck、Aoede、Charon、Fenrir、Leda、Orus、Zephyr，其余可以用 `tts @gemini voice:音色名 文本`。

| 音色 | 特点 | 音色 | 特点 | 音色 | 特点 |
| --- | --- | --- | --- | --- | --- |
| Zephyr | Bright | Puck | Upbeat | Charon | Informative |
| Kore | Firm | Fenrir | Excitable | Leda | Youthful |
| Orus | Firm | Aoede | Breezy | Callirrhoe | Easy-going |
| Autonoe | Bright | Enceladus | Breathy | Iapetus | Clear |
| Umbriel | Easy-going | Algieba | Smooth | Despina | Smooth |
| Erinome | Clear | Algenib | Gravelly | Rasalgethi | Informative |
| Laomedeia | Upbeat | Achernar | Soft | Alnilam | Firm |
| Schedar | Even | Gacrux | Mature | Pulcherrima | Forward |
| Achird | Friendly | Zubenelgenubi | Casual | Vindemiatrix | Gentle |
| Sadachbia | Lively | Sadaltager | Knowledgeable | Sulafat | Warm |
- **Deepgram**：`DEEPGRAM_API_KEY`。Aura-2 英文音色（`aura-2-thalia-en`）。
- **xAI Grok**：`XAI_API_KEY`。默认 `eve`，中文文本自动 `language=zh`。
- **阿里云百炼**：`DASHSCOPE_API_KEY`。CosyVoice `cosyvoice-v3-flash` / 龙安洋，国内直连。
- **火山引擎**：`VOLC_APPID` + `VOLC_TOKEN`。openspeech HTTP，ICL 音色自动切 `volcano_icl`。
- **Kokoro**：按需安装本地 ONNX（FP32 ~379MB / INT8 ~167MB），或直连本地 `http://127.0.0.1:8880/v1`。

海外引擎（Edge / Gemini / OpenAI / ElevenLabs / Deepgram / xAI）走 `PROXY_URL`；阿里云、火山引擎与本地 Kokoro 直连。

语速在 Workflow 配置的 **语速倍率**（`SPEECH_RATE`，默认 `1.0`）。Edge、OpenAI（0.25–4）、ElevenLabs Flash 与 Multilingual（接口上限 0.7–1.2，超出按边界取值）、阿里云 CosyVoice（0.5–2）、火山引擎、Kokoro 会按倍率合成。Eleven v3、v4、v4 Turbo、Gemini、Deepgram、xAI 没有语速参数，选了非 1.0 仍按原速朗读，并弹出说明。Gemini 只能把快慢写进 `GEMINI_STYLE`，例如 `speaking rapidly`。

设置入口：`tts-set`。环境修复：`tts-setup`。

## 开发

需要 Python 3.11+ 与 [uv](https://docs.astral.sh/uv/)。

```bash
make dev-setup
make lint
make test
make build
```

产物：`dist/Alfred-TTS.alfredworkflow`。

## 发布

版本号需同步：`pyproject.toml`、`src/alfred_tts/__init__.py`、`scripts/generate_info_plist.py`。

```bash
make build
git tag vX.Y.Z
git push origin main --tags
gh release create vX.Y.Z dist/Alfred-TTS.alfredworkflow --title "vX.Y.Z" --notes "..."
```

推送前确认没有 API Key、`prefs.plist`、本机绝对路径或 `.venv`。`.alfredworkflow` 只作为 Release 附件，不进 git。
