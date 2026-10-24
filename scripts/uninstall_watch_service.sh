#!/bin/bash
set -u

PLIST="$HOME/Library/LaunchAgents/com.docuflow.watch.plist"

if [ -f "$PLIST" ]; then
    launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || \
        launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo "已卸载后台监听服务：com.docuflow.watch"
else
    echo "未找到监听服务：$PLIST"
fi
