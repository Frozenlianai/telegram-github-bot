#!/usr/bin/env python3
"""
安装脚本 - 初始化项目并安装依赖
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def print_step(step, message):
    """打印步骤"""
    print(f"\n{'='*50}")
    print(f"  [{step}] {message}")
    print(f"{'='*50}\n")


def check_python():
    """检查 Python 版本"""
    print_step("1", "检查 Python 环境")
    
    version = sys.version_info
    print(f"当前 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return False
    
    print("✅ Python 版本符合要求")
    return True


def install_dependencies():
    """安装依赖"""
    print_step("2", "安装依赖包")
    
    try:
        print("正在安装...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False


def setup_env_file():
    """设置环境变量文件"""
    print_step("3", "配置环境变量")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ 已创建 .env 文件")
        print("\n⚠️  请编辑 .env 文件填入您的配置：")
        print("   - TELEGRAM_BOT_TOKEN")
        print("   - GITHUB_TOKEN")
        return False
    elif env_file.exists():
        print("✅ .env 文件已存在")
    else:
        print("⚠️  未找到 .env.example 文件")
    
    return True


def create_directories():
    """创建必要目录"""
    print_step("4", "创建目录")
    
    dirs = ["data", "logs"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        print(f"  ✅ {d}/")
    
    print("\n✅ 目录创建完成")
    return True


def print_next_steps():
    """打印下一步说明"""
    print_step("5", "下一步")
    
    print("""
🎉 安装完成！

📝 请按以下步骤配置：

1️⃣  获取 Telegram Bot Token
   • 访问 https://t.me/BotFather
   • 发送 /newbot 创建新机器人
   • 复制获得的 Token

2️⃣  获取 GitHub Token
   • 访问 https://github.com/settings/tokens
   • 点击 "Generate new token (classic)"
   • 勾选 'repo' 权限
   • 生成并复制 Token

3️⃣  编辑 .env 文件
   • 填入 TELEGRAM_BOT_TOKEN
   • 填入 GITHUB_TOKEN

4️⃣  启动机器人
   • Windows: 双击 start.bat 或运行 python main.py
   • Linux/Mac: 运行 ./start.sh 或 python3 main.py

📚 使用命令：
   /start  - 开始使用
   /add    - 添加监控仓库
   /list   - 查看仓库列表
   /help   - 查看所有命令
""")


def main():
    """主函数"""
    print("\n" + "="*50)
    print("  GitHub 仓库监控 Telegram 机器人")
    print("  安装脚本")
    print("="*50)
    
    # 切换到脚本所在目录
    os.chdir(Path(__file__).parent)
    
    # 执行安装步骤
    if not check_python():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    env_ready = setup_env_file()
    create_directories()
    print_next_steps()
    
    if not env_ready:
        sys.exit(1)


if __name__ == "__main__":
    main()
