#!/bin/bash
# Finder Quick Action 的投递包装脚本
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export PYTHONUNBUFFERED=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/venv/bin/python"
LOG="$HOME/Library/Logs/DocuFlow-finder.log"

mkdir -p "$(dirname "$LOG")"

notify() {
    if [ "${DOCUFLOW_NO_NOTIFY:-0}" != "1" ]; then
        /usr/bin/osascript -e "display notification \"$1\" with title \"DocuFlow\"" >/dev/null 2>&1 || true
    fi
}

if [ "$#" -eq 0 ]; then
    notify "没有选中文件"
    exit 1
fi

if [ ! -x "$PY" ]; then
    notify "venv 未安装，无法投递"
    exit 1
fi

args=( "$PY" "$ROOT/kb_cli.py" ingest "$@" --json )
[ -n "${DOCUFLOW_VAULT:-}" ] && args+=( --vault "$DOCUFLOW_VAULT" )
[ -n "${DOCUFLOW_DEST:-}" ] && args+=( --dest "$DOCUFLOW_DEST" )
[ -n "${DOCUFLOW_OCR:-}" ] && args+=( --ocr "$DOCUFLOW_OCR" )
[ "${DOCUFLOW_MARKITDOWN:-0}" = "1" ] && args+=( --markitdown )

"${args[@]}" >> "$LOG" 2>&1
rc=$?

if [ "$rc" -eq 0 ]; then
    notify "已投递到知识库"
else
    notify "投递失败，查看 DocuFlow-finder.log"
fi
exit "$rc"
