"""
Telegram 命令处理器
"""

import re
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes

from database import Database, MonitoredRepo, UserSettings
from github_monitor import GitHubMonitor
from keyboards import Keyboards, format_repo_list, format_settings_display
from config import config


class CommandHandler:
    """命令处理器"""
    
    def __init__(self, db: Database, monitor: GitHubMonitor):
        self.db = db
        self.monitor = monitor
    
    # ==================== 基础命令 ====================
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        welcome_message = """
🤖 **GitHub 仓库监控机器人**

欢迎使用！我可以帮助您监控 GitHub 仓库的各种活动。

**主要功能：**
• ⭐ 监控 Stars 和 Forks 变化
• 📝 跟踪新提交和代码更新
• 🔀 监控 Pull Requests
• 🐛 跟踪 Issues
• 🚀 第一时间获取 Releases

**常用命令：**
/add - 添加监控仓库
/list - 查看监控列表
/help - 获取帮助

点击下方按钮开始使用：
"""
        
        await update.message.reply_text(
            welcome_message,
            parse_mode="Markdown",
            reply_markup=Keyboards.quick_actions_keyboard()
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        help_text = """
📖 **命令列表**

**仓库管理：**
`/add <owner/repo>` - 添加监控仓库
`/remove <owner/repo>` - 移除监控仓库
`/list` - 查看监控列表

**仓库信息：**
`/watch <owner/repo>` - 查看仓库详情
`/recent <owner/repo>` - 查看最近活动

**设置：**
`/status` - 查看监控状态
`/settings` - 通知设置
`/interval <分钟>` - 设置检查间隔

**快捷操作：**
点击仓库列表中的按钮可直接查看详情
"""
        
        await update.message.reply_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=Keyboards.help_keyboard()
        )
    
    # ==================== 仓库管理命令 ====================
    
    async def add_repo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /add 命令"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            await update.message.reply_text(
                "📝 **添加监控仓库**\n\n"
                "请使用以下格式：\n"
                "`/add owner/repo`\n\n"
                "例如：\n"
                "`/add facebook/react`\n"
                "`/add microsoft/vscode`",
                parse_mode="Markdown"
            )
            return
        
        # 解析仓库名
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text(
                "❌ 仓库格式错误！\n\n"
                "请使用：`/add owner/repo`\n"
                "例如：`/add facebook/react`"
            )
            return
        
        owner, repo = parsed
        
        # 验证仓库是否存在
        status, message = self.monitor.validate_repo(owner, repo)
        
        if not status:
            await update.message.reply_text(message)
            return
        
        # 检查是否已存在
        if self.db.repo_exists(chat_id, owner, repo):
            await update.message.reply_text(
                f"ℹ️ 仓库 `{owner}/{repo}` 已经在监控列表中",
                parse_mode="Markdown"
            )
            return
        
        # 添加仓库
        if self.db.add_repo(chat_id, owner, repo):
            # 获取初始统计
            stats = self.monitor.get_repo_stats(owner, repo)
            
            success_msg = f"""
✅ **成功添加监控**

📦 `{owner}/{repo}`

"""
            if stats:
                success_msg += f"⭐ {stats.stars} stars\n"
                success_msg += f"🍴 {stats.forks} forks\n"
                success_msg += f"👁️ {stats.watchers} watchers\n"
                if stats.language:
                    success_msg += f"💻 {stats.language}\n"
            
            success_msg += "\n我将定期检查此仓库的更新！"
            
            await update.message.reply_text(
                success_msg,
                parse_mode="Markdown",
                reply_markup=Keyboards.repo_inline_keyboard(owner, repo)
            )
        else:
            await update.message.reply_text("❌ 添加失败，请重试")
    
    async def remove_repo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /remove 命令"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            # 显示仓库列表让用户选择
            repos = self.db.get_user_repos(chat_id)
            if not repos:
                await update.message.reply_text("📭 您还没有添加任何监控仓库")
                return
            
            # 显示删除选择
            keyboard = []
            for repo in repos[:10]:  # 最多显示10个
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {repo.owner}/{repo.repo}",
                        callback_data=f"remove_confirm:{repo.owner}/{repo.repo}"
                    )
                ])
            
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            
            await update.message.reply_text(
                "选择要移除的仓库：",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # 解析仓库名
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！请使用：`/remove owner/repo`")
            return
        
        owner, repo = parsed
        
        if self.db.remove_repo(chat_id, owner, repo):
            await update.message.reply_text(f"✅ 已移除监控：`{owner}/{repo}`")
        else:
            await update.message.reply_text(f"ℹ️ 仓库 `{owner}/{repo}` 不在监控列表中")
    
    async def list_repos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /list 命令"""
        chat_id = update.effective_chat.id
        repos = self.db.get_user_repos(chat_id)
        
        text, reply_markup = format_repo_list(repos)
        
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    # ==================== 信息查看命令 ====================
    
    async def watch_repo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /watch 命令 - 查看仓库详情"""
        if not context.args:
            await update.message.reply_text(
                "📝 **查看仓库详情**\n\n"
                "请使用：`/watch owner/repo`\n\n"
                "例如：`/watch facebook/react`"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        # 显示加载状态
        msg = await update.message.reply_text("🔍 正在获取仓库信息...")
        
        info = self.monitor.get_repo_info(owner, repo)
        
        if not info:
            await msg.edit_text(f"❌ 无法获取仓库 `{owner}/{repo}` 的信息", parse_mode="Markdown")
            return
        
        # 构建详情消息
        detail_msg = f"""
📦 **{info['full_name']}**

**描述：** {info['description']}

⭐ Stars: **{info['stars']:,}**
🍴 Forks: **{info['forks']:,}**
👁️ Watchers: **{info['watchers']:,}**
🐛 Open Issues: **{info['open_issues']:,}**

💻 语言: **{info['language']}**
📄 License: **{info['license']}**

📅 创建: {info['created_at']}
🔄 更新: {info['updated_at']}
⬆️ 最后推送: {info['pushed_at']}
"""
        
        if info.get('topics'):
            topics_str = " ".join([f"`{t}`" for t in info['topics'][:5]])
            detail_msg += f"\n🏷️ 主题: {topics_str}"
        
        if info.get('homepage'):
            detail_msg += f"\n🌐 主页: {info['homepage']}"
        
        await msg.edit_text(
            detail_msg,
            parse_mode="Markdown",
            reply_markup=Keyboards.repo_inline_keyboard(owner, repo)
        )
    
    async def recent_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /recent 命令 - 查看最近活动"""
        if not context.args:
            await update.message.reply_text(
                "📝 **查看最近活动**\n\n"
                "请使用：`/recent owner/repo`"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        msg = await update.message.reply_text("📥 正在获取最近活动...")
        
        # 获取事件
        events = self.monitor.get_events(owner, repo, limit=10)
        
        if not events:
            await msg.edit_text(f"📭 暂无最近活动：`{owner}/{repo}`")
            return
        
        messages = []
        for event in events[:5]:
            event_msg = event.to_message()
            messages.append(event_msg)
        
        full_msg = f"📋 **{owner}/{repo}** 最近活动：\n\n"
        full_msg += "\n\n---\n\n".join(messages)
        
        await msg.edit_text(
            full_msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    
    # ==================== 设置命令 ====================
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令"""
        chat_id = update.effective_chat.id
        
        # 获取统计数据
        stats = self.db.get_stats(chat_id)
        repos = self.db.get_user_repos(chat_id)
        settings = self.db.get_user_settings(chat_id)
        
        status_msg = f"""
📊 **监控状态**

📦 监控仓库数: **{stats['repo_count']}**
📝 活动记录数: **{stats['activity_count']}**

⚙️ **检查设置**
⏱️ 检查间隔: **{settings.check_interval} 分钟**
"""
        
        if repos:
            status_msg += "\n📋 **监控的仓库：**\n"
            for repo in repos[:5]:
                status_msg += f"• `{repo.owner}/{repo.repo}`\n"
            if len(repos) > 5:
                status_msg += f"\n... 还有 {len(repos) - 5} 个仓库"
        
        await update.message.reply_text(
            status_msg,
            parse_mode="Markdown"
        )
    
    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /settings 命令"""
        chat_id = update.effective_chat.id
        settings = self.db.get_user_settings(chat_id)
        
        settings_dict = {
            'notify_stars': settings.notify_stars,
            'notify_forks': settings.notify_forks,
            'notify_commits': settings.notify_commits,
            'notify_prs': settings.notify_prs,
            'notify_issues': settings.notify_issues,
            'notify_releases': settings.notify_releases,
            'notify_branches': settings.notify_branches,
        }
        
        text = format_settings_display(settings_dict)
        
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=Keyboards.notification_toggle_keyboard(settings_dict)
        )
    
    async def set_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /interval 命令"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            settings = self.db.get_user_settings(chat_id)
            await update.message.reply_text(
                f"📝 **设置检查间隔**\n\n"
                f"当前间隔：{settings.check_interval} 分钟\n\n"
                f"请使用：`/interval <分钟>`\n"
                f"范围：{config.MIN_CHECK_INTERVAL} - {config.MAX_CHECK_INTERVAL} 分钟",
                parse_mode="Markdown"
            )
            return
        
        try:
            interval = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ 请输入有效的数字！")
            return
        
        if interval < config.MIN_CHECK_INTERVAL or interval > config.MAX_CHECK_INTERVAL:
            await update.message.reply_text(
                f"❌ 间隔必须在 {config.MIN_CHECK_INTERVAL} - {config.MAX_CHECK_INTERVAL} 分钟之间"
            )
            return
        
        settings = self.db.get_user_settings(chat_id)
        settings.check_interval = interval
        self.db.save_user_settings(settings)
        
        await update.message.reply_text(
            f"✅ 已将检查间隔设置为 **{interval} 分钟**",
            parse_mode="Markdown"
        )
    
    # ==================== 辅助方法 ====================
    
    def _parse_repo_input(self, repo_input: str) -> Optional[Tuple[str, str]]:
        """解析仓库输入"""
        # 清理输入
        repo_input = repo_input.strip().strip('/')
        
        # 支持多种格式
        patterns = [
            r'^([^/]+)/([^/]+)$',  # owner/repo
            r'^https?://github\.com/([^/]+)/([^/]+)/?$',  # https://github.com/owner/repo
        ]
        
        for pattern in patterns:
            match = re.match(pattern, repo_input)
            if match:
                return match.group(1), match.group(2)
        
        return None


from telegram import InlineKeyboardButton
