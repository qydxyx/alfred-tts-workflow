# Alfred TTS

Alfred 5 多引擎语音合成 Workflow。输入 `tts <文本>`，或对任意应用里选中的文字使用 Universal Action **Speak with Alfred TTS**。

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

`tts @edge` / `@gemini` / `@kokoro` 可指定引擎。未配置的引擎不会出现在日常列表里。

## 引擎

- **Edge TTS**：开箱即用，中文默认晓晓，英文默认 Aria。
- **Gemini TTS**：在 Workflow 配置里填写 `GEMINI_API_KEY`。默认 `gemini-3.8-flash-lite-tts`。
- **Kokoro**：按需安装本地 ONNX（FP32 ~379MB / INT8 ~167MB），或直连本地 `http://127.0.0.1:8880/v1`。

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
