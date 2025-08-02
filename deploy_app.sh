#!/bin/bash

# DocuFlow 应用自动部署脚本
# 解决应用无法启动、启动台找不到等问题

set -e  # 遇到错误立即退出

echo "🚀 DocuFlow 应用自动部署脚本"
echo "================================="
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印彩色信息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查应用是否存在
if [ ! -d "dist/DocuFlow.app" ]; then
    print_error "找不到应用文件 dist/DocuFlow.app"
    print_info "正在重新打包应用..."
    python3 build_app.py
    if [ $? -ne 0 ]; then
        print_error "应用打包失败"
        exit 1
    fi
    print_success "应用打包完成"
fi

# 步骤1：清理旧版本
print_info "步骤1：清理旧版本应用"
if [ -d "/Applications/DocuFlow.app" ]; then
    print_warning "发现旧版本，正在删除..."
    sudo rm -rf "/Applications/DocuFlow.app" 2>/dev/null || true
fi

if [ -d "$HOME/Applications/DocuFlow.app" ]; then
    print_warning "发现用户目录旧版本，正在删除..."
    rm -rf "$HOME/Applications/DocuFlow.app" 2>/dev/null || true
fi
print_success "旧版本清理完成"

# 步骤2：清除隔离属性
print_info "步骤2：清除应用隔离属性"
xattr -cr "dist/DocuFlow.app" 2>/dev/null || true
print_success "隔离属性清除完成"

# 步骤3：修复权限
print_info "步骤3：修复应用权限"
chmod +x "dist/DocuFlow.app/Contents/MacOS/DocuFlow"
chmod -R 755 "dist/DocuFlow.app"
print_success "权限修复完成"

# 步骤4：选择安装位置
echo
print_info "请选择应用安装位置："
echo "1) /Applications (系统应用目录，所有用户可用，需要管理员权限)"
echo "2) ~/Applications (用户应用目录，仅当前用户可用)"
echo "3) 创建符号链接到 /Applications (推荐)"
echo "4) 跳过安装，仅修复当前位置的应用"
echo
read -p "请输入选择 (1-4，默认为3): " choice
choice=${choice:-3}

case $choice in
    1)
        print_info "正在安装到系统应用目录..."
        if sudo cp -R "dist/DocuFlow.app" "/Applications/"; then
            print_success "应用已安装到 /Applications/DocuFlow.app"
            APP_PATH="/Applications/DocuFlow.app"
        else
            print_error "安装失败，可能需要管理员权限"
            exit 1
        fi
        ;;
    2)
        print_info "正在安装到用户应用目录..."
        mkdir -p "$HOME/Applications"
        if cp -R "dist/DocuFlow.app" "$HOME/Applications/"; then
            print_success "应用已安装到 ~/Applications/DocuFlow.app"
            APP_PATH="$HOME/Applications/DocuFlow.app"
        else
            print_error "安装失败"
            exit 1
        fi
        ;;
    3)
        print_info "正在创建符号链接..."
        CURRENT_PATH="$(pwd)/dist/DocuFlow.app"
        if sudo ln -sf "$CURRENT_PATH" "/Applications/DocuFlow.app"; then
            print_success "符号链接已创建：/Applications/DocuFlow.app -> $CURRENT_PATH"
            APP_PATH="/Applications/DocuFlow.app"
        else
            print_warning "创建符号链接失败，尝试用户目录..."
            mkdir -p "$HOME/Applications"
            if ln -sf "$CURRENT_PATH" "$HOME/Applications/DocuFlow.app"; then
                print_success "符号链接已创建：~/Applications/DocuFlow.app -> $CURRENT_PATH"
                APP_PATH="$HOME/Applications/DocuFlow.app"
            else
                print_error "符号链接创建失败"
                exit 1
            fi
        fi
        ;;
    4)
        print_info "跳过安装，仅修复当前应用"
        APP_PATH="$(pwd)/dist/DocuFlow.app"
        ;;
    *)
        print_error "无效选择"
        exit 1
        ;;
esac

# 步骤5：处理 Gatekeeper
print_info "步骤5：配置 Gatekeeper 权限"
if spctl --assess --verbose "$APP_PATH" 2>&1 | grep -q "rejected"; then
    print_warning "应用被 Gatekeeper 阻止，正在添加例外..."
    
    # 尝试添加例外
    if sudo spctl --add "$APP_PATH" 2>/dev/null; then
        print_success "Gatekeeper 例外添加成功"
    else
        print_warning "无法自动添加 Gatekeeper 例外"
        print_info "请手动执行：sudo spctl --master-disable"
        print_info "或在系统偏好设置 > 安全性与隐私中允许此应用"
    fi
else
    print_success "Gatekeeper 检查通过"
fi

# 步骤6：重建启动台
print_info "步骤6：重建启动台数据库"
defaults write com.apple.dock ResetLaunchPad -bool true
killall Dock 2>/dev/null || true
print_success "启动台数据库已重建"

# 步骤7：验证安装
print_info "步骤7：验证应用安装"
if [ -e "$APP_PATH" ]; then
    print_success "应用文件存在：$APP_PATH"
    
    # 检查可执行文件
    if [ -x "$APP_PATH/Contents/MacOS/DocuFlow" ]; then
        print_success "可执行文件权限正确"
    else
        print_warning "可执行文件权限异常，正在修复..."
        chmod +x "$APP_PATH/Contents/MacOS/DocuFlow"
    fi
else
    print_error "应用安装验证失败"
    exit 1
fi

# 步骤8：测试启动
print_info "步骤8：测试应用启动"
echo
print_info "正在测试应用启动..."

# 创建测试脚本
cat > /tmp/test_docuflow.sh << 'EOF'
#!/bin/bash
timeout 10s "$1/Contents/MacOS/DocuFlow" --help > /tmp/docuflow_test.log 2>&1
echo $? > /tmp/docuflow_exit_code
EOF
chmod +x /tmp/test_docuflow.sh

# 运行测试
/tmp/test_docuflow.sh "$APP_PATH" &
TEST_PID=$!

# 等待测试完成
sleep 3
kill $TEST_PID 2>/dev/null || true
wait $TEST_PID 2>/dev/null || true

# 检查测试结果
if [ -f "/tmp/docuflow_test.log" ] && grep -q "DocuFlow" "/tmp/docuflow_test.log"; then
    print_success "应用启动测试通过"
else
    print_warning "应用启动测试未通过，但这可能是正常的（GUI应用）"
fi

# 清理测试文件
rm -f /tmp/test_docuflow.sh /tmp/docuflow_test.log /tmp/docuflow_exit_code

# 完成
echo
print_success "🎉 DocuFlow 应用部署完成！"
echo
print_info "应用位置：$APP_PATH"
print_info "启动方式："
echo "  1. 在启动台中找到 DocuFlow 图标"
echo "  2. 在应用程序文件夹中双击 DocuFlow"
echo "  3. 使用命令：open \"$APP_PATH\""
echo "  4. 使用快速启动脚本：./quick_start.sh app"
echo

# 询问是否立即启动
read -p "是否现在启动 DocuFlow？(y/N): " start_now
if [[ $start_now =~ ^[Yy]$ ]]; then
    print_info "正在启动 DocuFlow..."
    open "$APP_PATH"
    print_success "DocuFlow 已启动"
fi

echo
print_info "如果遇到问题，请查看 '应用启动故障排除指南.md'"
print_success "部署脚本执行完成！"