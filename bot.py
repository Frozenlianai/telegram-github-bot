"""
Telegram 机器人主模块
"""

import logging
from typing import Dict

from telegram import Update, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)

from config import config
from database import Database, MonitoredRepo, UserSettings
from github_monitor import GitHubMonitor
from commands import CommandHandler
from keyboards import Keyboards


# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


class GitHubMonitorBot:
    """GitHub 监控 Telegram 机器人"""
    
    def __init__(self, token: str = None):
        self.token = token or config.TELEGRAM_BOT_TOKEN
        
        # 初始化组件
        self.db = Database()
        self.monitor = GitHubMonitor()
        self.commands = CommandHandler(self.db, self.monitor)
        
        # 创建应用
        self.app = Application.builder().token(self.token).build()
        
        # 存储活跃的监控任务
        self._monitoring_jobs: Dict[int, bool] = {}
        
        # 设置处理器
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置所有处理器"""
        # 命令处理器
        self.app.add_handler(CommandHandler("start", self.commands.start))
        self.app.add_handler(CommandHandler("help", self.commands.help))
        self.app.add_handler(CommandHandler("add", self.commands.add_repo))
        self.app.add_handler(CommandHandler("remove", self.commands.remove_repo))
        self.app.add_handler(CommandHandler("list", self.commands.list_repos))
        self.app.add_handler(CommandHandler("watch", self.commands.watch_repo))
        self.app.add_handler(CommandHandler("recent", self.commands.recent_activity))
        self.app.add_handler(CommandHandler("status", self.commands.status))
        self.app.add_handler(CommandHandler("settings", self.commands.settings))
        self.app.add_handler(CommandHandler("interval", self.commands.set_interval))
        
        # 回调查询处理器
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # 错误处理器
        self.app.add_error_handler(self._error_handler)
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理回调查询"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        chat_id = query.message.chat_id
        
        # 解析回调数据
        parts = data.split(':', 2)
        
        if len(parts) < 2:
            return
        
        action = parts[0]
        sub_action = parts[1]
        
        # 处理命令快捷方式
        if action == "cmd":
            await self._handle_command(query, sub_action)
            return
        
        # 处理仓库相关操作
        if action in ["stats", "commits", "prs", "issues", "releases", "branches", "refresh"]:
            if len(parts) >= 3:
                await self._handle_repo_action(query, action, parts[2])
        
        # 处理列表分页
        elif action == "pagelist":
            await self._handle_list_pagination(query, int(sub_action))
        
        # 处理设置切换
        elif action == "toggle":
            await self._handle_settings_toggle(query, sub_action, parts)
        
        # 处理确认操作
        elif action == "confirm":
            await self._handle_confirm(query, sub_action, parts)
        
        # 处理移除确认
        elif action == "remove_confirm":
            await self._handle_remove_confirm(query, parts)
        
        # 处理返回
        elif action == "back":
            await self._handle_back(query, sub_action, parts)
    
    async def _handle_command(self, query, command: str):
        """处理命令快捷方式"""
        from telegram import InlineKeyboardMarkup
        
        commands_map = {
            "add": self.commands.add_repo,
            "list": self.commands.list_repos,
            "settings": self.commands.settings,
            "status": self.commands.status
        }
        
        if command in commands_map:
            # 创建一个假的 Update 对象
            class FakeUpdate:
                def __init__(self, message):
                    self.message = message
                    self.effective_chat = message.chat
                    self.effective_user = message.chat
                    self.effective_message = message
            
            fake_update = FakeUpdate(query.message)
            
            class FakeContext:
                args = []
            
            await commands_map[command](fake_update, FakeContext())
    
    async def _handle_repo_action(self, query, action: str, repo_path: str):
        """处理仓库相关操作"""
        owner, repo = repo_path.split('/')
        
        if action == "stats":
            await self._show_repo_stats(query, owner, repo)
        elif action == "commits":
            await self._show_commits(query, owner, repo)
        elif action == "prs":
            await self._show_prs(query, owner, repo)
        elif action == "issues":
            await self._show_issues(query, owner, repo)
        elif action == "releases":
            await self._show_releases(query, owner, repo)
        elif action == "branches":
            await self._show_branches(query, owner, repo)
        elif action == "refresh":
            await self._refresh_repo(query, owner, repo)
        elif action == "remove":
            await self._confirm_remove_repo(query, owner, repo)
    
    async def _show_repo_stats(self, query, owner: str, repo: str):
        """显示仓库统计"""
        info = self.monitor.get_repo_info(owner, repo)
        
        if not info:
            await query.edit_message_text(f"❌ 无法获取 `{owner}/{repo}` 的信息")
            return
        
        stats_msg = f"""
📊 **{owner}/{repo}** 统计

⭐ Stars: **{info['stars']:,}**
🍴 Forks: **{info['forks']:,}**
👁️ Watchers: **{info['watchers']:,}**
🐛 Open Issues: **{info['open_issues']:,}**

💻 语言: **{info['language']}**
📄 License: **{info['license']}**

🔗 [GitHub 链接]({info['url']})
"""
        
        await query.edit_message_text(
            stats_msg,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=Keyboards.repo_inline_keyboard(owner, repo)
        )
    
    async def _show_commits(self, query, owner: str, repo: str):
        """显示最近提交"""
        commits = self.monitor.get_recent_commits(owner, repo, limit=5)
        
        if not commits:
            await query.edit_message_text(f"📭 暂无提交记录：`{owner}/{repo}`")
            return
        
        commits_msg = f"📝 **{owner}/{repo}** 最近提交：\n\n"
        
        for commit in commits:
            date_str = commit.date.strftime("%m-%d %H:%M")
            commits_msg += f"• `{commit.sha}`\n"
            commits_msg += f"  {commit.message[:50]}...\n"
            commits_msg += f"  👤 {commit.author} • 📅 {date_str}\n\n"
        
        commits_msg += f"[查看更多](https://github.com/{owner}/{repo}/commits)"
        
        await query.edit_message_text(
            commits_msg,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=Keyboards.repo_inline_keyboard(owner, repo)
        )
    
    async def _show_prs(self, query, owner: str, repo: str):
        """显示 PR 列表"""
        prs = self.monitor.get_recent_prs(owner, repo, limit=5)
        
        if not prs:
            await query.edit_message_text(f"📭 暂无 PR：`{owner}/{repo}`")
            return
        
        prs_msg = f"🔀 **{owner}/{repo}** 最近 PR：\n\n"
        
        for pr in prs:
            emoji = "✅" if pr.action.value == "merged" else ("❌" if pr.action.value == "closed" else "🆕")
            prs_msg += f"{emoji} **#{pr.number}** {pr.title[:40]}...\n"
            prs_msg += f"   👤 {pr.user}\n\n"
        
        prs_msg += f"[查看更多](https://github.com/{owner}/{repo}/pulls)"
        
        await query.edit_message_text(
            prs_msg,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=Keyboards.repo_inline_keyboard(owner, repo)
        )
    
    async def _show_issues(self, query, owner: str, repo: str):
        """显示 Issues"""
        issues = self.monitor.get_recent_issues(owner, repo, limit=5)
        
        if not issues:
            await query.edit_message_text(f"📭 暂无 Issues：`{owner}/{repo}`")
            return
        
        issues_msg = f"🐛 **{owner}/{repo}** 最近 Issues：\n\n"
        
        for issue in issues:
            emoji = "✅" if issue.action.value == "closed" else "🆕"
            issues_msg += f"{emoji} **#{issue.number}** {issue.title[:40]}...\n"
            issues_msg += f"   👤 {issue.user}"
            if issue.labels:
                labels_str = " ".join([f"`{l}`" for l in issue.labels[:3]])
                issues_msg += f" • {labels_str}"
            issues_msg += "\n\n"
        
        issues_msg += f"[查看更多](https://github.com/{owner}/{repo}/issues)"
        
        await query.edit_message_text(
            issues_msg,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=Keyboards.repo_inline_keyboard(owner, repo)
        )
    
    async def _show_releases(self, query, owner: str, repo: str):
        """显示 Releases"""
        releases = self.monitor.get_recent_releases(owner, repo, limit=5)
        
        if not releases:
            await query.edit_message_text(f"📭 暂无 Releases：`{owner}/{repo}`")
            return
        
        releases_msg = f"🚀 **{owner}/{repo}** 最近 Releases：\n\n"
        
        for release in releases:
            badge = "🥚" if release.is_prerelease else "🐣"
            releases_msg += f"{badge} **{release.tag_name}**\n"
            if release.name:
                releases_msg += f"   {release.name[:50]}\n"
            releases_msg += f"   👤 {release.author}\n"
            releases_msg += f"   📅 {release.created_at.strftime('%Y-%m-%d')}\n\n"
        
        releases_msg += f"[查看更多](https://github.com/{owner}/{repo}/releases)"
        
        await query.edit_message_text(
            releases_msg,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=Keyboards.repo_inline_keyboard(owner, repo)
        )
    
    async def _show_branches(self, query, owner: str, repo: str):
        """显示分支"""
        branches = self.monitor.get_branches(owner, repo)
        default_branch = self.monitor.get_default_branch(owner, repo)
        
        if not branches:
            await query.edit_message_text(f"📭 无法获取分支：`{owner}/{repo}`")
            return
        
        branches_msg = f"🌿 **{owner}/{repo}** 分支列表：\n\n"
        branches_msg += f"📌 默认分支： `{default_branch}`\n\n"
        
        # 显示前10个分支
        for i, branch in enumerate(branches[:10], 1):
            marker = "📌" if branch == default_branch else "  "
            branches_msg += f"{marker} {i}. `{branch}`\n"
        
        if len(branches) > 10:
            branches_msg += f"\n... 还有 {len(branches) - 10} 个分支"
        
        await query.edit_message_text(
            branches_msg,
            parse_mode="Markdown",
            reply_markup=Keyboards.repo_inline_keyboard(owner, repo)
        )
    
    async def _refresh_repo(self, query, owner: str, repo: str):
        """刷新仓库信息"""
        await query.edit_message_text(f"🔄 正在刷新 `{owner}/{repo}`...")
        
        info = self.monitor.get_repo_info(owner, repo)
        
        if not info:
            await query.edit_message_text(f"❌ 刷新失败：`{owner}/{repo}`")
            return
        
        await self._show_repo_stats(query, owner, repo)
    
    async def _confirm_remove_repo(self, query, owner: str, repo: str):
        """确认移除仓库"""
        confirm_msg = f"确定要移除 `{owner}/{repo}` 的监控吗？"
        
        await query.edit_message_text(
            confirm_msg,
            parse_mode="Markdown",
            reply_markup=Keyboards.confirm_keyboard("remove", f"{owner}/{repo}")
        )
    
    async def _handle_remove_confirm(self, query, parts):
        """处理移除确认"""
        repo_path = parts[2]
        owner, repo = repo_path.split('/')
        chat_id = query.message.chat_id
        
        if self.db.remove_repo(chat_id, owner, repo):
            await query.edit_message_text(f"✅ 已移除：`{owner}/{repo}`")
        else:
            await query.edit_message_text(f"❌ 移除失败：`{owner}/{repo}`")
    
    async def _handle_list_pagination(self, query, page: int):
        """处理列表分页"""
        chat_id = query.message.chat_id
        repos = self.db.get_user_repos(chat_id)
        
        text, reply_markup = self._format_repo_list(repos, page)
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    async def _handle_settings_toggle(self, query, key: str, parts: list):
        """处理设置切换"""
        chat_id = query.message.chat_id
        
        # 获取当前设置
        settings = self.db.get_user_settings(chat_id)
        
        # 切换设置
        if hasattr(settings, key):
            current = getattr(settings, key)
            setattr(settings, key, not current)
            self.db.save_user_settings(settings)
        
        # 显示更新后的设置
        settings_dict = {
            'notify_stars': settings.notify_stars,
            'notify_forks': settings.notify_forks,
            'notify_commits': settings.notify_commits,
            'notify_prs': settings.notify_prs,
            'notify_issues': settings.notify_issues,
            'notify_releases': settings.notify_releases,
            'notify_branches': settings.notify_branches,
        }
        
        from keyboards import format_settings_display
        text = format_settings_display(settings_dict)
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=Keyboards.notification_toggle_keyboard(settings_dict)
        )
    
    async def _handle_confirm(self, query, action: str, parts: list):
        """处理确认操作"""
        # 通用确认处理
        pass
    
    async def _handle_back(self, query, sub_action: str, parts: list):
        """处理返回"""
        if sub_action in ["main", "menu"]:
            # 返回主菜单
            await query.edit_message_text(
                "⬆️ 返回主菜单\n\n使用 /help 查看所有命令",
                reply_markup=Keyboards.quick_actions_keyboard()
            )
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """错误处理器"""
        logger.error(f"错误: {context.error}")
        
        error_msg = f"⚠️ 发生错误：\n{str(context.error)[:200]}"
        
        if update and update.effective_message:
            await update.effective_message.reply_text(error_msg)
    
    def _format_repo_list(self, repos: list, page: int = 1, per_page: int = 5):
        """格式化仓库列表"""
        from keyboards import format_repo_list
        return format_repo_list(repos, page, per_page)
    
    def run(self):
        """运行机器人"""
        logger.info("🤖 GitHub 监控机器人启动中...")
        
        # 验证配置
        valid, errors = config.validate_config()
        if not valid:
            logger.error("配置错误:")
            for error in errors:
                logger.error(f"  {error}")
            logger.error("请检查 config.py 或 .env 文件")
            return
        
        logger.info("✅ 配置验证通过")
        logger.info("📡 机器人正在运行，按 Ctrl+C 停止...")
        
        # 启动轮询
        self.app.run_polling(drop_pending_updates=True)


def main():
    """主函数"""
    bot = GitHubMonitorBot()
    bot.run()


if __name__ == "__main__":
    main()
