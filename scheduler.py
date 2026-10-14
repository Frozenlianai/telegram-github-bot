"""
定时任务调度器 - 定期检查 GitHub 仓库更新
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from telegram import Bot

from config import config
from database import Database, MonitoredRepo, UserSettings
from github_monitor import GitHubMonitor
from models import EventType, GitHubEvent


logger = logging.getLogger(__name__)


class MonitorScheduler:
    """监控调度器"""
    
    def __init__(self, db: Database, monitor: GitHubMonitor, bot: Bot):
        self.db = db
        self.monitor = monitor
        self.bot = bot
        self._running = False
        self._check_interval = config.DEFAULT_CHECK_INTERVAL
    
    async def start(self):
        """启动调度器"""
        self._running = True
        logger.info(f"⏰ 调度器启动，检查间隔: {self._check_interval} 分钟")
        
        while self._running:
            try:
                await self._check_all_repos()
            except Exception as e:
                logger.error(f"检查失败: {e}")
            
            # 等待下次检查
            await asyncio.sleep(self._check_interval * 60)
    
    def stop(self):
        """停止调度器"""
        self._running = False
        logger.info("⏰ 调度器已停止")
    
    def set_interval(self, minutes: int):
        """设置检查间隔"""
        self._check_interval = minutes
        logger.info(f"⏰ 检查间隔已设置为 {minutes} 分钟")
    
    async def _check_all_repos(self):
        """检查所有监控的仓库"""
        logger.info("🔍 开始检查仓库更新...")
        
        # 按用户分组获取仓库
        all_repos = self.db.get_all_monitored_repos()
        
        # 按 chat_id 分组
        repos_by_user: Dict[int, List[MonitoredRepo]] = {}
        for repo in all_repos:
            if repo.chat_id not in repos_by_user:
                repos_by_user[repo.chat_id] = []
            repos_by_user[repo.chat_id].append(repo)
        
        # 为每个用户检查
        for chat_id, repos in repos_by_user.items():
            try:
                await self._check_user_repos(chat_id, repos)
            except Exception as e:
                logger.error(f"检查用户 {chat_id} 的仓库失败: {e}")
        
        logger.info(f"✅ 完成检查，共 {len(all_repos)} 个仓库")
    
    async def _check_user_repos(self, chat_id: int, repos: List[MonitoredRepo]):
        """检查单个用户的仓库"""
        # 获取用户设置
        settings = self.db.get_user_settings(chat_id)
        
        # 更新检查间隔
        if settings.check_interval != self._check_interval:
            self._check_interval = settings.check_interval
        
        for repo in repos:
            try:
                await self._check_single_repo(chat_id, repo, settings)
            except Exception as e:
                logger.error(f"检查 {repo.owner}/{repo.repo} 失败: {e}")
    
    async def _check_single_repo(self, chat_id: int, repo: MonitoredRepo, 
                                  settings: UserSettings):
        """检查单个仓库"""
        # 获取最新的事件
        since = None
        if repo.last_check:
            try:
                since = datetime.fromisoformat(repo.last_check)
            except:
                since = datetime.utcnow() - timedelta(minutes=self._check_interval * 2)
        else:
            # 首次检查，获取最近 5 分钟的事件
            since = datetime.utcnow() - timedelta(minutes=5)
        
        # 获取事件
        events = self.monitor.get_events(
            repo.owner, repo.repo,
            limit=config.MAX_EVENTS_PER_CHECK,
            since=since
        )
        
        # 过滤已通知的事件
        notified_ids = repo.get_notified_events()
        new_events = [e for e in events if e.event_id not in notified_ids]
        
        if not new_events:
            # 更新检查时间
            self.db.update_repo_check(chat_id, repo.owner, repo.repo)
            return
        
        # 获取最新统计
        stats = self.monitor.get_repo_stats(repo.owner, repo.repo)
        
        # 检查 star/fork 变化
        if stats:
            # Star 变化
            if repo.last_stars is not None and stats.stars != repo.last_stars:
                change = stats.stars - repo.last_stars
                if settings.notify_stars and change > 0:
                    await self._send_notification(
                        chat_id,
                        f"⭐ **{repo.owner}/{repo.repo}**\n\n"
                        f"✨ Stars 增加了 **{change}** 个！\n"
                        f"📊 当前: **{stats.stars:,}** ⭐",
                        disable_notification=False
                    )
            
            # Fork 变化
            if repo.last_forks is not None and stats.forks != repo.last_forks:
                change = stats.forks - repo.last_forks
                if settings.notify_forks and change > 0:
                    await self._send_notification(
                        chat_id,
                        f"🍴 **{repo.owner}/{repo.repo}**\n\n"
                        f"🍴 Forks 增加了 **{change}** 个！\n"
                        f"📊 当前: **{stats.forks:,}** forks",
                        disable_notification=False
                    )
            
            # 更新统计
            self.db.update_repo_check(
                chat_id, repo.owner, repo.repo,
                stars=stats.stars, forks=stats.forks
            )
        
        # 发送新事件通知
        for event in new_events[:config.MAX_EVENTS_PER_CHECK]:
            if self._should_notify_event(event, settings):
                await self._send_notification(
                    chat_id,
                    event.to_message(),
                    disable_notification=False
                )
                
                # 记录已通知
                repo.add_notified_event(event.event_id)
                
                # 保存到数据库
                self.db.add_activity(
                    chat_id, repo.owner, repo.repo,
                    event.event_type.value, event.event_id,
                    event.details
                )
        
        # 更新已通知事件列表
        self.db.update_notified_events(
            chat_id, repo.owner, repo.repo,
            repo.notified_events
        )
    
    def _should_notify_event(self, event: GitHubEvent, settings: UserSettings) -> bool:
        """判断是否应该通知此事件"""
        event_type_map = {
            EventType.STAR: settings.notify_stars,
            EventType.FORK: settings.notify_forks,
            EventType.COMMIT: settings.notify_commits,
            EventType.PULL_REQUEST: settings.notify_prs,
            EventType.ISSUE: settings.notify_issues,
            EventType.RELEASE: settings.notify_releases,
            EventType.CREATE_BRANCH: settings.notify_branches,
            EventType.DELETE_BRANCH: settings.notify_branches,
        }
        
        return event_type_map.get(event.event_type, True)
    
    async def _send_notification(self, chat_id: int, message: str, 
                                 disable_notification: bool = False):
        """发送通知"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                disable_notification=disable_notification
            )
        except Exception as e:
            logger.error(f"发送消息失败 to {chat_id}: {e}")


class BackgroundScheduler:
    """后台调度器运行器"""
    
    def __init__(self, scheduler: MonitorScheduler):
        self.scheduler = scheduler
        self._task = None
    
    def start_background(self, loop):
        """在后台启动调度器"""
        self._task = loop.create_task(self.scheduler.start())
        return self._task
    
    async def stop(self):
        """停止调度器"""
        self.scheduler.stop()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
