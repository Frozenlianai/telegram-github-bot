"""
GitHub 仓库监控 Telegram 机器人
主程序入口
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 加载 .env 文件
load_dotenv()

from config import config, validate_config
from database_extended import DatabaseExtended
from github_monitor import GitHubMonitor
from bot_extended import ExtendedGitHubMonitorBot
from scheduler import MonitorScheduler


# 配置日志
def setup_logging():
    """设置日志"""
    log_dir = Path(config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def check_environment():
    """检查环境配置"""
    logger = logging.getLogger(__name__)
    
    # 检查必要的环境变量
    issues = []
    
    if config.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        issues.append("❌ 未设置 TELEGRAM_BOT_TOKEN")
        issues.append("   请从 https://t.me/BotFather 获取 Telegram Bot Token")
    
    if config.GITHUB_TOKEN == "YOUR_GITHUB_TOKEN":
        issues.append("❌ 未设置 GITHUB_TOKEN")
        issues.append("   请从 https://github.com/settings/tokens 生成 Personal Access Token")
        issues.append("   需要勾选 'repo' 权限")
    
    if issues:
        logger.error("=" * 50)
        logger.error("配置检查失败:")
        for issue in issues:
            logger.error(f"  {issue}")
        logger.error("=" * 50)
        logger.error("\n请创建 .env 文件或设置环境变量:\n")
        logger.error(config.get_env_template())
        return False
    
    return True


async def run_with_scheduler():
    """运行机器人和调度器"""
    logger = logging.getLogger(__name__)
    
    # 创建数据目录
    data_dir = Path(config.DATABASE_PATH).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化组件
    db = DatabaseExtended()
    monitor = GitHubMonitor()
    
    # 创建扩展版机器人
    bot = ExtendedGitHubMonitorBot()
    
    # 创建调度器
    scheduler = MonitorScheduler(db, monitor, bot.app.bot)
    
    logger.info("=" * 60)
    logger.info("🤖 GitHub 仓库监控 Telegram 机器人 V2")
    logger.info("   (扩展版 - 支持 Fork/Actions/PR)")
    logger.info("=" * 60)
    
    # 启动调度器作为后台任务
    scheduler_task = asyncio.create_task(scheduler.start())
    logger.info("⏰ 定时检查调度器已启动")
    
    # 运行机器人
    try:
        logger.info("📡 机器人启动中...")
        await bot.app.initialize()
        await bot.app.start()
        await bot.app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("✅ 机器人运行中，按 Ctrl+C 停止")
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️ 收到停止信号...")
    finally:
        # 清理
        scheduler.stop()
        scheduler_task.cancel()
        
        await bot.app.updater.stop()
        await bot.app.stop()
        await bot.app.shutdown()
        
        logger.info("👋 机器人已停止")


def run_simple():
    """简单运行（无定时调度）"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("🤖 GitHub 仓库监控 Telegram 机器人 V2")
    logger.info("=" * 60)
    
    # 直接运行扩展版机器人
    bot = ExtendedGitHubMonitorBot()
    bot.run()


def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 检查配置
    if not check_environment():
        sys.exit(1)
    
    # 检查是否启用调度模式
    if "--with-scheduler" in sys.argv or os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        logger.info("🔄 启动调度模式")
        asyncio.run(run_with_scheduler())
    else:
        logger.info("🔄 启动简单模式")
        run_simple()


if __name__ == "__main__":
    main()
