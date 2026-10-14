"""
扩展版 Telegram 机器人 - 集成所有高级功能
"""

import logging
import asyncio
import re
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler as TgCmd, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)

from config import config
from database_extended import DatabaseExtended, GitHubAccount
from github_monitor import GitHubMonitor
from github_oauth import GitHubOAuth
from github_advanced import GitHubAdvanced, GitHubActions
from github_trending import GitHubTrending, HotProjectTracker
from commands_extended import ExtendedCommandHandler
from commands_trending import TrendingCommands
from keyboards import Keyboards
from keyboards_extended import ExtendedKeyboards
from menu_system import Menu, format_trending_list, format_hot_list, format_tracked_list, format_repo_card
from menu_handler import MenuHandler


# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


class ExtendedGitHubMonitorBot:
    """扩展版 GitHub 监控 Telegram 机器人"""
    
    def __init__(self, token: str = None):
        self.token = token or config.TELEGRAM_BOT_TOKEN
        
        # 初始化组件
        self.db = DatabaseExtended()
        self.monitor = GitHubMonitor()
        self.oauth = GitHubOAuth()
        self.trending = GitHubTrending()
        self.tracker = HotProjectTracker(self.db)
        
        # 初始化命令处理器
        self.ext_commands = ExtendedCommandHandler(self.db, self.monitor, self.oauth)
        self.trending_commands = TrendingCommands(self.db)
        
        # 初始化菜单处理器
        self.menu_handler = MenuHandler(
            self.db, self.monitor, self.trending,
            self.ext_commands, self.trending_commands
        )
        
        # 创建应用
        self.app = Application.builder().token(self.token).build()
        
        # 设置处理器
        self._setup_handlers()
        
        # 设置 OAuth 回调
        self._setup_oauth_callback()
    
    def _setup_handlers(self):
        """设置所有处理器"""
        
        # 基础命令
        self.app.add_handler(TgCmd("start", self._start))
        self.app.add_handler(TgCmd("help", self._help))
        self.app.add_handler(TgCmd("add", self.ext_commands.add_repo))
        self.app.add_handler(TgCmd("remove", self.ext_commands.remove_repo))
        self.app.add_handler(TgCmd("list", self.ext_commands.list_repos))
        self.app.add_handler(TgCmd("watch", self.ext_commands.watch_repo))
        self.app.add_handler(TgCmd("recent", self.ext_commands.recent_activity))
        self.app.add_handler(TgCmd("status", self.ext_commands.status))
        self.app.add_handler(TgCmd("settings", self.ext_commands.settings))
        self.app.add_handler(TgCmd("interval", self.ext_commands.set_interval))
        
        # 扩展命令
        self.app.add_handler(TgCmd("bind", self.ext_commands.bind_github))
        self.app.add_handler(TgCmd("unbind", self.ext_commands.unbind_github))
        self.app.add_handler(TgCmd("github", self.ext_commands.github_info))
        self.app.add_handler(TgCmd("fork", self.ext_commands.fork_repo))
        self.app.add_handler(TgCmd("forks", self.ext_commands.list_forks))
        self.app.add_handler(TgCmd("workflows", self.ext_commands.workflows))
        self.app.add_handler(TgCmd("run", self.ext_commands.actions_run))
        self.app.add_handler(TgCmd("run_status", self.ext_commands.run_status))
        self.app.add_handler(TgCmd("rerun", self.ext_commands.rerun_workflow))
        self.app.add_handler(TgCmd("pr", self.ext_commands.create_pr))
        self.app.add_handler(TgCmd("qpr", self.ext_commands.quick_pr))
        self.app.add_handler(TgCmd("branch", self.ext_commands.create_branch))
        self.app.add_handler(TgCmd("deletebranch", self.ext_commands.delete_branch))
        self.app.add_handler(TgCmd("star", self.ext_commands.star_repo))
        self.app.add_handler(TgCmd("unstar", self.ext_commands.unstar_repo))
        self.app.add_handler(TgCmd("search", self.ext_commands.search_repos))
        self.app.add_handler(TgCmd("myrepos", self.ext_commands.my_repos))
        self.app.add_handler(TgCmd("notifications", self.ext_commands.notifications))
        self.app.add_handler(TgCmd("gist", self.ext_commands.create_gist))
        self.app.add_handler(TgCmd("quick", self.ext_commands.quick_cmd))
        
        # Trending 命令
        self.app.add_handler(TgCmd("trending", self.trending_commands.trending))
        self.app.add_handler(TgCmd("hot", self.trending_commands.hot))
        self.app.add_handler(TgCmd("exploding", self.trending_commands.exploding))
        self.app.add_handler(TgCmd("track", self.trending_commands.track))
        self.app.add_handler(TgCmd("stars", self.trending_commands.stars_history))
        self.app.add_handler(TgCmd("similar", self.trending_commands.similar))
        self.app.add_handler(TgCmd("rank", self.trending_commands.rank))
        
        # 回调查询处理器
        self.app.add_handler(CallbackQueryHandler(self.menu_handler.handle_callback))
        
        # 消息处理器
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # 错误处理器
        self.app.add_error_handler(self._error_handler)
    
    def _setup_oauth_callback(self):
        """设置 OAuth 回调处理"""
        pass
    
    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        chat_id = update.effective_chat.id
        has_github = self.db.is_github_bound(chat_id)
        
        welcome_message = """
🤖 **GitHub 监控机器人 V3**

👋 欢迎使用！发现、监控、管理 GitHub，尽在指尖！

🎛️ **点击下方按钮开始使用：**
"""
        
        await update.message.reply_text(
            welcome_message,
            parse_mode="Markdown",
            reply_markup=Menu.main_menu(has_github)
        )
    
    async def _help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        help_text = """
📖 **帮助**

发送 `/start` 查看完整按钮菜单

**快捷命令：**
`/trending` - Trending 榜单
`/hot` - 热门排行
`/exploding` - 爆发项目
`/track owner/repo` - 追踪 Stars
"""
        
        await update.message.reply_text(
            help_text,
            parse_mode="Markdown"
        )
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通文本消息"""
        text = update.message.text.strip()
        chat_id = update.effective_chat.id
        awaiting = context.user_data.get('awaiting')
        
        if awaiting:
            del context.user_data['awaiting']
            
            if awaiting == 'track_repo':
                await self.trending_commands.handle_track_input(update, context, text)
                return
        
        # 处理绑定 GitHub 账号
        if text.startswith('gh_'):
            await self._handle_github_binding(update, context, text)
            return
        
        # 处理搜索关键词 - 直接输入关键词搜索
        if len(text) >= 2 and not text.startswith('/'):
            await self._handle_direct_search(update, text)
            return
        
        # 默认回复
        await update.message.reply_text(
            "请使用按钮菜单或发送 `/start` 查看功能",
            parse_mode="Markdown"
        )
    
    async def _handle_direct_search(self, update: Update, query: str):
        """处理直接发送关键词搜索"""
        try:
            # 调用搜索功能 - 使用 GitHubMonitor
            results = self.monitor.search_repos(query, limit=5)
            
            if not results:
                await update.message.reply_text(
                    f"🔍 没有找到与「{query}」相关的项目\n\n"
                    f"试试其他关键词，或使用 `/start` 查看菜单",
                    parse_mode="Markdown"
                )
                return
            
            # 格式化结果
            lines = [f"🔍 搜索「{query}」的结果：\n", "=" * 35, ""]
            
            for i, repo in enumerate(results, 1):
                lines.append(f"{i}. **{repo['full_name']}**")
                lines.append(f"   ⭐ {repo.get('stars', 0):,} | {repo.get('language', 'N/A')}")
                desc = repo.get('description', '')
                if desc:
                    desc = desc[:60] + "..." if len(desc) > 60 else desc
                    lines.append(f"   📝 {desc}")
                lines.append(f"   🔗 {repo.get('html_url', '')}")
                lines.append("")
            
            keyboard = [
                [InlineKeyboardButton(f"🚀 {r['full_name'].split('/')[-1]}", url=r.get('html_url', ''))]
                for r in results[:5]
            ]
            keyboard.append([InlineKeyboardButton("🔍 在 GitHub 搜索更多", url=f"https://github.com/search?q={query.replace(' ', '+')}")])
            
            await update.message.reply_text(
                "\n".join(lines),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            await update.message.reply_text(f"❌ 搜索失败: {str(e)}")
    
    async def _handle_github_binding(self, update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
        """处理 GitHub 账号绑定"""
        try:
            user_info = await self.oauth.handle_callback(code, update.effective_chat.id)
            if user_info:
                await update.message.reply_text(
                    f"✅ GitHub 账号绑定成功！\n\n"
                    f"👤 用户名: {user_info['login']}\n"
                    f"📛 名称: {user_info.get('name', 'N/A')}\n"
                    f"📍 位置: {user_info.get('location', 'N/A')}"
                )
            else:
                await update.message.reply_text("❌ 绑定失败，请重试")
        except Exception as e:
            logger.error(f"GitHub 绑定失败: {e}")
            await update.message.reply_text(f"❌ 绑定失败: {str(e)}")
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理错误"""
        logger.error(f"错误: {context.error}")
        if update and update.message:
            await update.message.reply_text(
                f"发生错误: {str(context.error)}"
            )
    
    def run(self):
        """运行机器人"""
        logger.info("启动 Telegram 机器人...")
        logger.info("按 Ctrl+C 停止")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def run_with_scheduler(self, scheduler):
        """运行机器人和调度器"""
        logger.info("启动 Telegram 机器人（带调度器）...")
        scheduler.start()
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


# OAuth 回调处理
async def handle_oauth_callback(request):
    """处理 OAuth 回调"""
    from flask import request as flask_request
    
    code = flask_request.args.get('code')
    state = flask_request.args.get('state')
    
    if not code:
        return "No code provided", 400
    
    # 这里需要处理 token 交换和用户绑定
    return "GitHub 账号绑定成功！请返回 Telegram 机器人继续使用。", 200


# 独立的 Flask 应用（用于 OAuth）
def create_flask_app(bot_instance: ExtendedGitHubMonitorBot):
    """创建 Flask 应用用于 OAuth 回调"""
    from flask import Flask, request, redirect
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
    
    @app.route('/oauth/callback')
    async def oauth_callback():
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            return "No code provided", 400
        
        try:
            # 处理 OAuth 回调
            user_info = await bot_instance.oauth.handle_callback(code, int(state))
            if user_info:
                return f"""
                <html>
                <body>
                    <h1>✅ GitHub 账号绑定成功！</h1>
                    <p>用户名: {user_info['login']}</p>
                    <p>请返回 Telegram 机器人继续使用。</p>
                </body>
                </html>
                """
            else:
                return "绑定失败，请重试", 400
        except Exception as e:
            logger.error(f"OAuth 回调处理失败: {e}")
            return f"错误: {str(e)}", 500
    
    return app
