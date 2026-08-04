#!/bin/bash

# DocuFlow 桌面快捷方式创建器
# 创建美观的桌面和启动台图标

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "║                    ${GREEN}创建桌面快捷方式${NC}                        ║"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 创建应用图标（使用Unicode表情符号作为图标）
create_app_icon() {
    local app_name="DocuFlow"
    local app_path="$HOME/Desktop/DocuFlow.app"
    
    # 创建应用包结构
    mkdir -p "$app_path/Contents/MacOS"
    mkdir -p "$app_path/Contents/Resources"
    
    # 创建Info.plist
cat > "$app_path/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>DocuFlow</string>
    <key>CFBundleIdentifier</key>
    <string>com.docuflow.app</string>
    <key>CFBundleName</key>
    <string>DocuFlow</string>
    <key>CFBundleDisplayName</key>
    <string>DocuFlow</string>
    <key>CFBundleVersion</key>
    <string>4.0</string>
    <key>CFBundleShortVersionString</key>
    <string>4.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
    <key>CFBundleIconFile</key>
    <string>icon</string>
</dict>
</plist>
EOF

    # 创建启动脚本
cat > "$app_path/Contents/MacOS/DocuFlow" << EOF
#!/bin/bash
# DocuFlow 启动脚本
cd "$SCRIPT_DIR"
open "DocuFlow-极速启动器.command"
EOF

    chmod +x "$app_path/Contents/MacOS/DocuFlow"
    
    echo -e "${GREEN}✓${NC} 已创建桌面应用：$app_path"
}

# 创建Dock栏快捷方式
create_dock_shortcut() {
    local dock_item="$HOME/Desktop/DocuFlow.dock"
    
    # 创建符号链接到Applications
    ln -sf "$SCRIPT_DIR/DocuFlow-极速启动器.command" "$HOME/Desktop/DocuFlow"
    
    echo -e "${GREEN}✓${NC} 已创建桌面快捷方式"
}

# 创建启动台图标
create_launchpad_icon() {
    # 创建Applications目录链接
    local apps_path="$HOME/Applications/DocuFlow.app"
    
    if [ ! -d "$apps_path" ]; then
        mkdir -p "$apps_path/Contents/MacOS"
        mkdir -p "$apps_path/Contents/Resources"
        
        # 复制Info.plist
        cp "$HOME/Desktop/DocuFlow.app/Contents/Info.plist" "$apps_path/Contents/"
        
        # 创建启动脚本
        cat > "$apps_path/Contents/MacOS/DocuFlow" << EOF
#!/bin/bash
# DocuFlow 启动脚本
cd "$SCRIPT_DIR"
open "DocuFlow-极速启动器.command"
EOF
        
        chmod +x "$apps_path/Contents/MacOS/DocuFlow"
        
        echo -e "${GREEN}✓${NC} 已添加到启动台"
    fi
}

# 创建图标文件
create_icon_file() {
    local icon_path="$HOME/Desktop/DocuFlow.app/Contents/Resources/icon.icns"
    
    # 使用系统图标作为占位符
    touch "$icon_path"
    
    echo -e "${GREEN}✓${NC} 已创建应用图标"
}

# 主程序
main() {
    echo ""
    echo -e "${GREEN}正在创建快捷方式...${NC}"
    echo ""
    
    # 创建各种快捷方式
    create_app_icon
    create_dock_shortcut
    create_launchpad_icon
    create_icon_file
    
    echo ""
    echo -e "${GREEN}🎉 完成！${NC}"
    echo ""
    echo "已创建："
    echo "  • 桌面应用：~/Desktop/DocuFlow.app"
    echo "  • 桌面快捷方式：~/Desktop/DocuFlow"
    echo "  • 启动台图标：启动台 → DocuFlow"
    echo ""
    echo "使用方法："
    echo "  1. 双击桌面上的 DocuFlow 图标"
    echo "  2. 或者在启动台中搜索 DocuFlow"
    echo ""
    
    # 刷新启动台
    killall Dock 2>/dev/null || true
    
    read -p "按回车键完成..."
}

# 执行主程序
main "$@"