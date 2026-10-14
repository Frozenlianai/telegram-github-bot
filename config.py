"""
GitHub 仓库监控 Telegram 机器人
配置文件
"""

import os
from dataclasses import dataclass
from typing import Set


@dataclass
class Config:
    """应用配置"""
    
    # Telegram 配置
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
    
    # GitHub 配置
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN")
    
    # 数据库配置
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/bot_database.db")
    
    # 监控配置
    DEFAULT_CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "5"))  # 分钟
    MIN_CHECK_INTERVAL: int = 1  # 最小检查间隔（分钟）
    MAX_CHECK_INTERVAL: int = 60  # 最大检查间隔（分钟）
    
    # 通知配置
    NOTIFY_STARS: bool = True
    NOTIFY_FORKS: bool = True
    NOTIFY_COMMITS: bool = True
    NOTIFY_PRS: bool = True
    NOTIFY_ISSUES: bool = True
    NOTIFY_RELEASES: bool = True
    NOTIFY_BRANCHES: bool = True
    
    # GitHub API 配置
    GITHUB_API_PER_PAGE: int = 30
    MAX_EVENTS_PER_CHECK: int = 10  # 每次检查最多处理的事件数
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")
    
    def get_env_template(self) -> str:
        """返回环境变量模板"""
        return """# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# GitHub Personal Access Token (需要 repo 权限)
GITHUB_TOKEN=your_github_token_here

# 检查间隔（分钟）
CHECK_INTERVAL=5

# 日志级别
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# 数据库路径
DATABASE_PATH=data/bot_database.db
"""


# 全局配置实例
config = Config()


def validate_config() -> tuple[bool, list[str]]:
    """验证配置是否正确"""
    errors = []
    
    if config.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        errors.append("❌ 请设置 TELEGRAM_BOT_TOKEN")
    
    if config.GITHUB_TOKEN == "YOUR_GITHUB_TOKEN":
        errors.append("❌ 请设置 GITHUB_TOKEN")
    
    if config.DEFAULT_CHECK_INTERVAL < config.MIN_CHECK_INTERVAL:
        errors.append(f"❌ 检查间隔不能小于 {config.MIN_CHECK_INTERVAL} 分钟")
    
    if config.DEFAULT_CHECK_INTERVAL > config.MAX_CHECK_INTERVAL:
        errors.append(f"❌ 检查间隔不能大于 {config.MAX_CHECK_INTERVAL} 分钟")
    
    return len(errors) == 0, errors


def get_env_template() -> str:
    """返回环境变量模板"""
    return """# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# GitHub Personal Access Token (需要 repo 权限)
GITHUB_TOKEN=your_github_token_here

# 检查间隔（分钟）
CHECK_INTERVAL=5

# 日志级别
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# 数据库路径
DATABASE_PATH=data/bot_database.db
"""
