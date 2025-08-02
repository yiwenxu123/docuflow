@echo off
REM DocuFlow Windows 启动脚本

cd /d "%~dp0"

echo 🚀 启动 DocuFlow...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 安装依赖（如果需要）
if not exist ".deps_installed" (
    echo 📦 首次运行，安装依赖...
    python -m pip install -r requirements.txt --user --quiet
    echo. > .deps_installed
    echo ✅ 依赖安装完成
)

REM 启动应用
set mode=%1
if "%mode%"=="" set mode=web

if "%mode%"=="gui" (
    echo 🖥️  启动GUI版本...
    python main_pyside.py
) else if "%mode%"=="web" (
    echo 🌐 启动Web版本...
    echo 📱 访问地址: http://localhost:5003
    python main_web.py
) else if "%mode%"=="cli" (
    echo 💻 启动命令行版本...
    shift
    python main_cli.py %*
) else (
    echo 用法: %0 [gui^|web^|cli] [参数...]
    echo   gui - 图形界面
    echo   web - 网页界面  
    echo   cli - 命令行
)

pause
