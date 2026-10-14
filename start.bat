@echo off
REM GitHub Monitor Bot - Windows 启动脚本

echo ========================================
echo   GitHub 仓库监控 Telegram 机器人
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未安装 Python
    echo 请从 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

REM 检查依赖
echo [1/3] 检查依赖...
pip show python-telegram-bot >nul 2>&1
if errorlevel 1 (
    echo [2/3] 安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [3/3] 检查配置...
REM 检查 .env 文件
if not exist .env (
    echo [警告] .env 文件不存在
    echo 正在创建...
    copy .env.example .env
    echo.
    echo [重要] 请编辑 .env 文件填入您的配置！
    echo.
    notepad .env
    pause
    exit /b 1
)

REM 检查配置
findstr /C "YOUR_TELEGRAM_BOT_TOKEN" .env >nul
if not errorlevel 1 (
    echo [错误] 请先配置 .env 文件！
    echo.
    notepad .env
    pause
    exit /b 1
)

echo.
echo ========================================
echo   启动机器人...
echo ========================================
echo.

REM 启动机器人
python main.py

pause
