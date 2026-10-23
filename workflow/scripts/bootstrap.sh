#!/bin/bash
set -euo pipefail

export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -d "${ROOT}/python/alfred_tts" ]]; then
  export PYTHONPATH="${ROOT}/python${PYTHONPATH:+:${PYTHONPATH}}"
elif [[ -d "${ROOT}/../src/alfred_tts" ]]; then
  export PYTHONPATH="${ROOT}/../src${PYTHONPATH:+:${PYTHONPATH}}"
fi

CMD="${1:-filter}"
shift || true

emit_setup() {
  local title="$1"
  local subtitle="$2"
  local action="$3"
  python3 -c "
import json
print(json.dumps({
  'skipknowledge': True,
  'items': [{
    'title': '''${title}''',
    'subtitle': '''${subtitle}''',
    'arg': '''${action}''',
    'valid': True,
    'variables': {'tts_action': '''${action}'''}
  }]
}, ensure_ascii=False))
"
}

if [[ -z "${alfred_workflow_data:-}" ]]; then
  if [[ "${CMD}" == "filter" || "${CMD}" == "config-filter" ]]; then
    emit_setup "Alfred 环境变量缺失" "请从 Alfred 中运行此 Workflow" "setup"
  fi
  exit 0
fi

PY="${alfred_workflow_data}/.venv/bin/python"

if [[ "${CMD}" == "filter" || "${CMD}" == "config-filter" ]]; then
  if [[ ! -x "${PY}" ]]; then
    if [[ "${CMD}" == "config-filter" ]]; then
      emit_setup "首次运行：回车初始化环境" "约 2–3 秒安装轻量核心依赖" "setup"
    else
      emit_setup "首次运行：回车 3 秒完成初始化" "仅安装轻量核心依赖，无需 API Key" "setup"
    fi
    exit 0
  fi
  exec "${PY}" -m alfred_tts "${CMD}" "$@"
fi

if [[ ! -x "${PY}" ]]; then
  if command -v uv >/dev/null 2>&1; then
    uv venv "${alfred_workflow_data}/.venv" --python 3.11
    uv pip install --python "${alfred_workflow_data}/.venv/bin/python" \
      'httpx[socks]>=0.28.0' 'edge-tts>=7.3.1' 'google-genai>=2.30.1'
    PY="${alfred_workflow_data}/.venv/bin/python"
  else
    echo "uv is required" >&2
    exit 1
  fi
fi

exec "${PY}" -m alfred_tts "${CMD}" "$@"
