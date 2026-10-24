#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKFLOW="$ROOT/macos/DocuFlow-投递到知识库.workflow"
SERVICES="$HOME/Library/Services"
SUPPORT="$HOME/Library/Application Support/DocuFlow"
TARGET="$SERVICES/DocuFlow-投递到知识库.workflow"

if [ ! -d "$WORKFLOW" ]; then
    echo "找不到 Quick Action 模板: $WORKFLOW"
    exit 1
fi
if [ ! -x "$ROOT/venv/bin/python" ]; then
    echo "找不到 venv/bin/python，请先在项目目录完成安装"
    exit 1
fi

mkdir -p "$SERVICES" "$SUPPORT"

cat > "$SUPPORT/finder_ingest.sh" <<EOF
#!/bin/bash
exec "$ROOT/scripts/finder_ingest.sh" "\$@"
EOF
chmod +x "$SUPPORT/finder_ingest.sh" "$ROOT/scripts/finder_ingest.sh"

rm -rf "$TARGET"
cp -R "$WORKFLOW" "$TARGET"

plutil -lint "$TARGET/Contents/Info.plist" >/dev/null
plutil -lint "$TARGET/Contents/document.wflow" >/dev/null

echo "已安装 Finder 快捷动作：用 DocuFlow 投递到知识库"
echo "如果 Finder 右键菜单没有出现："
echo "  1. 系统设置 > 通用 > 登录项与扩展 > Finder 扩展/快捷动作，勾选 DocuFlow"
echo "  2. 或重启 Finder 后再试"
