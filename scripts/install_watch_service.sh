#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.docuflow.watch.plist"
BOX="${DOCUFLOW_BOX:-$HOME/Documents/素材投递箱}"
VAULT="${DOCUFLOW_VAULT:-}"
INTERVAL="${DOCUFLOW_INTERVAL:-30}"
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

if [ ! -x "$ROOT/venv/bin/python" ]; then
    echo "找不到 venv/bin/python，请先在项目目录完成安装"
    exit 1
fi

if [ -z "$VAULT" ]; then
    VAULT="$("$ROOT/venv/bin/python" -c 'from converter.kb_pipeline import detect_obsidian_vault; print(detect_obsidian_vault() or "")')"
fi
if [ -z "$VAULT" ]; then
    echo "未检测到 Obsidian vault，请设置 DOCUFLOW_VAULT 后重试"
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
TMP_PLIST="$(mktemp)"
trap 'rm -f "$TMP_PLIST"' EXIT

/usr/bin/python3 - "$TMP_PLIST" "$ROOT" "$BOX" "$VAULT" "$INTERVAL" <<'PY'
import os
import plistlib
import sys

path, root, box, vault, interval = sys.argv[1:6]
args = [
    f"{root}/venv/bin/python",
    "-u",
    f"{root}/kb_cli.py",
    "watch",
    "--box", box,
    "--interval", interval,
]
if vault:
    args += ["--vault", vault]

log = os.path.expanduser("~/Library/Logs/DocuFlow-watch.log")
env = {
    "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
    "PYTHONUNBUFFERED": "1",
}
state_db = os.environ.get("DOCUFLOW_STATE_DB")
if state_db:
    env["DOCUFLOW_STATE_DB"] = state_db

data = {
    "Label": "com.docuflow.watch",
    "ProgramArguments": args,
    "WorkingDirectory": root,
    "EnvironmentVariables": env,
    "RunAtLoad": True,
    "KeepAlive": True,
    "ThrottleInterval": 10,
    "StandardOutPath": log,
    "StandardErrorPath": log,
}
with open(path, "wb") as f:
    plistlib.dump(data, f)
PY

plutil -lint "$TMP_PLIST" >/dev/null

if [ "$DRY_RUN" = "1" ]; then
    echo "dry-run: $PLIST"
    plutil -p "$TMP_PLIST"
    exit 0
fi

mv "$TMP_PLIST" "$PLIST"
trap - EXIT

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
if ! launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null; then
    launchctl load -w "$PLIST"
fi
launchctl kickstart -k "gui/$(id -u)/com.docuflow.watch" 2>/dev/null || true

echo "已安装后台监听服务：com.docuflow.watch"
echo "投递箱: $BOX"
echo "日志: ~/Library/Logs/DocuFlow-watch.log"
echo "卸载: $ROOT/scripts/uninstall_watch_service.sh"
