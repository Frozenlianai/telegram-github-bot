#!/bin/bash
# GitHub Monitor Bot - Linux/Mac 启动脚本

echo "========================================"
echo "  GitHub 仓库监控 Telegram 机器人"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未安装 Python3"
    echo "请运行: sudo apt install python3 python3-pip"
    exit 1
fi

# 检查依赖
echo "[1/3] 检查依赖..."
if ! pip3 show python-telegram-bot &> /dev/null; then
    echo "[2/3] 安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo "[3/3] 检查配置..."

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "[警告] .env 文件不存在"
    echo "正在创建..."
    cp .env.example .env
    echo ""
    echo "[重要] 请编辑 .env 文件填入您的配置！"
    nano .env
    exit 1
fi

# 检查配置
if grep -q "YOUR_TELEGRAM_BOT_TOKEN" .env; then
    echo "[错误] 请先配置 .env 文件！"
    nano .env
    exit 1
fi

echo ""
echo "========================================"
echo "  启动机器人..."
echo "========================================"
echo ""

# 启动机器人
python3 main.py
