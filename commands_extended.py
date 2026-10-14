"""
扩展命令处理器 - 包括 GitHub 账号绑定、Fork、Actions 等
"""

import re
import json
from typing import Optional, Tuple, List
from telegram import Update, InlineKeyboardButton
from telegram.ext import ContextTypes

from commands import CommandHandler as BaseHandler
from database_extended import DatabaseExtended, GitHubAccount
from github_oauth import GitHubOAuth
from github_advanced import GitHubAdvanced, GitHubActions


class ExtendedCommandHandler(BaseHandler):
    """扩展命令处理器"""
    
    def __init__(self, db: DatabaseExtended, monitor, oauth: GitHubOAuth = None):
        super().__init__(db, monitor)
        self.db = db
        self.oauth = oauth
    
    def _get_advanced_client(self, chat_id: int) -> Optional[GitHubAdvanced]:
        """获取高级 GitHub 客户端"""
        account = self.db.get_github_account(chat_id)
        if not account:
            return None
        return GitHubAdvanced(account.access_token)
    
    def _get_actions_client(self, chat_id: int) -> Optional[GitHubActions]:
        """获取 Actions 客户端"""
        account = self.db.get_github_account(chat_id)
        if not account:
            return None
        return GitHubActions(account.access_token)
    
    def _check_github_bound(self, update: Update) -> bool:
        """检查是否绑定了 GitHub 账号"""
        if not self.db.is_github_bound(update.effective_chat.id):
            update.message.reply_text(
                "⚠️ 请先绑定 GitHub 账号！\n\n"
                "使用 /bind 命令开始绑定流程",
                parse_mode="Markdown"
            )
            return False
        return True
    
    # ==================== GitHub 账号绑定命令 ====================
    
    async def bind_github(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /bind 命令 - 绑定 GitHub 账号"""
        chat_id = update.effective_chat.id
        
        # 检查是否已经绑定
        account = self.db.get_github_account(chat_id)
        if account:
            await update.message.reply_text(
                f"✅ 您已经绑定了 GitHub 账号：\n\n"
                f"👤 **@{account.github_login}**\n"
                f"📛 {account.name or 'N/A'}\n"
                f"📝 {account.bio or 'N/A'}\n"
                f"⭐ {account.public_repos} 公开仓库\n"
                f"👥 {account.followers}  followers\n\n"
                f"使用 `/unbind` 解绑",
                parse_mode="Markdown"
            )
            return
        
        # 检查 OAuth 是否配置
        if not self.oauth or not self.oauth.is_configured():
            await update.message.reply_text(
                "⚠️ OAuth 功能未配置\n\n"
                "请联系机器人管理员设置 GitHub OAuth App\n"
                "或手动通过 Token 方式绑定（开发中）"
            )
            return
        
        # 生成授权链接
        state = self.oauth.generate_state(chat_id)
        auth_url = self.oauth.get_authorization_url(state)
        
        # 保存 chat_id 到上下文
        context.user_data['pending_oauth'] = chat_id
        
        keyboard = [
            [InlineKeyboardButton("🔗 授权 GitHub", url=auth_url)],
            [InlineKeyboardButton("🔄 我已完成授权", callback_data="oauth_complete")],
            [InlineKeyboardButton("❌ 取消", callback_data="oauth_cancel")]
        ]
        
        from telegram import InlineKeyboardMarkup
        await update.message.reply_text(
            "🔐 **GitHub 授权绑定**\n\n"
            "点击下方按钮授权机器人访问您的 GitHub 账号：",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def unbind_github(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /unbind 命令 - 解绑 GitHub 账号"""
        chat_id = update.effective_chat.id
        
        if not self.db.is_github_bound(chat_id):
            await update.message.reply_text("ℹ️ 您还没有绑定 GitHub 账号")
            return
        
        from keyboards import Keyboards
        await update.message.reply_text(
            "⚠️ 确定要解绑 GitHub 账号吗？\n\n"
            "解绑后您将无法使用高级功能（如 Fork、Actions 等）",
            reply_markup=Keyboards.confirm_keyboard("unbind", str(chat_id))
        )
    
    async def github_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /github 命令 - 查看绑定的 GitHub 信息"""
        chat_id = update.effective_chat.id
        
        account = self.db.get_github_account(chat_id)
        if not account:
            await update.message.reply_text(
                "❌ 您还没有绑定 GitHub 账号\n\n"
                "使用 /bind 开始绑定",
                parse_mode="Markdown"
            )
            return
        
        info_msg = f"""
👤 **GitHub 账号信息**

🔗 登录名: **@{account.github_login}**
🆔 User ID: `{account.github_user_id}`
📛 名称: {account.name or 'N/A'}
📝 简介: {account.bio or 'N/A'}
📧 邮箱: {account.email or 'N/A'}

📊 **统计**
• 公开仓库: **{account.public_repos}**
• Followers: **{account.followers}**
• Following: **{account.following}**

📅 绑定时间: {account.created_at[:10]}
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📦 我的仓库", callback_data="github_repos"),
                InlineKeyboardButton("🍴 Fork 历史", callback_data="github_forks")
            ],
            [
                InlineKeyboardButton("🔔 通知", callback_data="github_notifications")
            ]
        ]
        
        from telegram import InlineKeyboardMarkup
        await update.message.reply_text(
            info_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # ==================== Fork 命令 ====================
    
    async def fork_repo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /fork 命令 - 一键 Fork"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            await update.message.reply_text(
                "🍴 **一键 Fork 仓库**\n\n"
                "请使用：`/fork owner/repo`\n\n"
                "例如：\n"
                "`/fork facebook/react`\n"
                "`/fork microsoft/vscode`",
                parse_mode="Markdown"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        # 获取高级客户端
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text(
                "⚠️ 需要先绑定 GitHub 账号！\n使用 /bind 命令绑定"
            )
            return
        
        msg = await update.message.reply_text(f"🍴 正在 Fork `{owner}/{repo}`...")
        
        result = client.fork_repository(owner, repo)
        
        if result.success:
            # 记录 Fork 历史
            self.db.add_fork_history(chat_id, owner, repo, result.full_name)
            
            success_msg = f"""
🍴 **Fork 成功！**

📦 源仓库: `{owner}/{repo}`
📦 Fork 到: [{result.full_name}]({result.html_url})

⏳ Fork 可能需要几秒钟完成，请在 GitHub 上刷新查看
"""
            await msg.edit_text(success_msg, parse_mode="Markdown")
        else:
            await msg.edit_text(result.message, parse_mode="Markdown")
    
    async def list_forks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /forks 命令 - 查看 Fork 历史"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        history = self.db.get_fork_history(chat_id)
        
        if not history:
            await update.message.reply_text("📭 暂无 Fork 历史")
            return
        
        msg = f"🍴 **Fork 历史** (共 {len(history)} 个)\n\n"
        
        for item in history[:10]:
            msg += f"📦 [{item['source_owner']}/{item['source_repo']}](https://github.com/{item['source_owner']}/{item['source_repo']})\n"
            msg += f"   ⬇️ fork 到 [{item['forked_repo']}](https://github.com/{item['forked_repo']})\n"
            msg += f"   📅 {item['forked_at'][:10]}\n\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
    
    # ==================== Actions 命令 ====================
    
    async def workflows(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /workflows 命令 - 查看 workflows"""
        if not context.args:
            await update.message.reply_text(
                "📝 **查看 Workflows**\n\n"
                "请使用：`/workflows owner/repo`\n\n"
                "例如：`/workflows microsoft/vscode`"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        # 获取高级客户端（用于获取 workflows）
        client = self._get_advanced_client(update.effective_chat.id)
        if not client:
            await update.message.reply_text(
                "⚠️ 需要先绑定 GitHub 账号！\n使用 /bind 命令绑定"
            )
            return
        
        msg = await update.message.reply_text(f"📥 正在获取 Workflows...")
        
        workflows = client.actions.get_workflows(owner, repo)
        
        if not workflows:
            await msg.edit_text(f"📭 仓库 `{owner}/{repo}` 没有 Workflows")
            return
        
        wf_msg = f"📝 **{owner}/{repo}** Workflows：\n\n"
        
        for wf in workflows[:10]:
            status_emoji = "🟢" if wf.state == "active" else "🔴"
            wf_msg += f"{status_emoji} **{wf.name}**\n"
            wf_msg += f"   📄 {wf.path}\n"
            wf_msg += f"   🔗 [打开]({wf.html_url})\n\n"
        
        await msg.edit_text(wf_msg, parse_mode="Markdown")
    
    async def actions_run(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /run 命令 - 触发 workflow"""
        chat_id = update.effective_chat.id
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "🚀 **触发 Workflow**\n\n"
                "请使用：`/run owner/repo workflow_name`\n\n"
                "例如：\n"
                "`/run microsoft/vscode CI`\n"
                "`/run facebook/react tests`",
                parse_mode="Markdown"
            )
            return
        
        repo_input = context.args[0]
        workflow_name = " ".join(context.args[1:])
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text(
                "⚠️ 需要先绑定 GitHub 账号！\n使用 /bind 命令绑定"
            )
            return
        
        msg = await update.message.reply_text(
            f"🚀 正在触发 workflow: **{workflow_name}**..."
        )
        
        # 先获取 workflows 找到对应的 ID
        workflows = client.actions.get_workflows(owner, repo)
        
        workflow_id = None
        for wf in workflows:
            if workflow_name.lower() in wf.name.lower():
                workflow_id = str(wf.id)
                break
        
        if not workflow_id:
            await msg.edit_text(
                f"❌ 未找到 workflow: **{workflow_name}**\n\n"
                f"使用 `/workflows {owner}/{repo}` 查看可用 workflows",
                parse_mode="Markdown"
            )
            return
        
        success, response = client.actions.trigger_workflow(owner, repo, workflow_id)
        
        if success:
            await msg.edit_text(response, parse_mode="Markdown")
        else:
            await msg.edit_text(response, parse_mode="Markdown")
    
    async def run_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /run_status 命令 - 查看 workflow 运行状态"""
        if not context.args:
            await update.message.reply_text(
                "📊 **查看 Workflow 运行状态**\n\n"
                "请使用：`/run_status owner/repo`\n\n"
                "例如：`/run_status microsoft/vscode`"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        client = self._get_advanced_client(update.effective_chat.id)
        if not client:
            await update.message.reply_text(
                "⚠️ 需要先绑定 GitHub 账号！\n使用 /bind 命令绑定"
            )
            return
        
        msg = await update.message.reply_text("📥 正在获取运行状态...")
        
        runs = client.actions.get_workflow_runs(owner, repo, limit=10)
        
        if not runs:
            await msg.edit_text(f"📭 暂无运行记录：`{owner}/{repo}`")
            return
        
        status_msg = f"📊 **{owner}/{repo}** Workflow 运行状态：\n\n"
        
        for run in runs[:5]:
            # 状态图标
            if run.status == "completed":
                if run.conclusion == "success":
                    emoji = "✅"
                elif run.conclusion == "failure":
                    emoji = "❌"
                elif run.conclusion == "cancelled":
                    emoji = "⚠️"
                else:
                    emoji = "❓"
            elif run.status == "in_progress":
                emoji = "🔄"
            else:
                emoji = "⏳"
            
            time_str = run.created_at.strftime("%m-%d %H:%M")
            duration = f"({run.duration // 60}m {run.duration % 60}s)" if run.duration else ""
            
            status_msg += f"{emoji} **{run.name}**\n"
            status_msg += f"   🌿 {run.head_branch}\n"
            status_msg += f"   📅 {time_str} {duration}\n"
            status_msg += f"   🔗 [查看]({run.html_url})\n\n"
        
        await msg.edit_text(status_msg, parse_mode="Markdown")
    
    async def rerun_workflow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /rerun 命令 - 重新运行 workflow"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            await update.message.reply_text(
                "🔄 **重新运行 Workflow**\n\n"
                "请使用：`/rerun owner/repo run_id`\n\n"
                "使用 `/run_status owner/repo` 查看 run_id",
                parse_mode="Markdown"
            )
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ 请提供仓库和 run_id！")
            return
        
        repo_input = context.args[0]
        try:
            run_id = int(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ run_id 必须是数字！")
            return
        
        parsed = self._parse_repo_input(repo_input)
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text(
                "⚠️ 需要先绑定 GitHub 账号！\n使用 /bind 命令绑定"
            )
            return
        
        msg = await update.message.reply_text("🔄 正在重新运行...")
        
        success, response = client.actions.rerun_workflow(owner, repo, run_id)
        
        if success:
            await msg.edit_text(response + f"\n🔗 [查看运行](https://github.com/{owner}/{repo}/actions/runs/{run_id})", parse_mode="Markdown")
        else:
            await msg.edit_text(response, parse_mode="Markdown")
    
    # ==================== Pull Request 命令 ====================
    
    async def create_pr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /pr 命令 - 创建 PR"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        if not context.args:
            await update.message.reply_text(
                "🔀 **创建 Pull Request**\n\n"
                "请使用：`/pr owner/repo`\n\n"
                "机器人会引导您填写 PR 标题和描述",
                parse_mode="Markdown"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        # 保存上下文
        context.user_data['pr_creating'] = {
            'owner': owner,
            'repo': repo
        }
        
        await update.message.reply_text(
            f"🔀 **创建 PR: {owner}/{repo}**\n\n"
            f"请回复 PR 的标题：",
            parse_mode="Markdown"
        )
    
    async def quick_pr(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /qpr 命令 - 快速创建 PR"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        # 解析参数: /qpr owner/repo title | head:base
        if not context.args:
            await update.message.reply_text(
                "⚡ **快速创建 PR**\n\n"
                "请使用：`/qpr owner/repo title --head owner:branch`\n\n"
                "示例：\n"
                "`/qpr facebook/react Fix bug --head me:fix-branch`",
                parse_mode="Markdown"
            )
            return
        
        # 简单解析
        text = " ".join(context.args)
        parts = text.split("--head")
        
        if len(parts) != 2:
            await update.message.reply_text("❌ 请使用 `--head` 指定源分支！")
            return
        
        repo_title = parts[0].strip()
        head = parts[1].strip()
        
        # 解析仓库和标题
        repo_parts = repo_title.split(" ", 1)
        if len(repo_parts) != 2:
            await update.message.reply_text("❌ 格式错误！")
            return
        
        repo_input, title = repo_parts
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        # 解析 head
        if ":" in head:
            head_parts = head.split(":", 1)
            head = f"{head_parts[0].strip()}:{head_parts[1].strip()}"
        else:
            # 使用用户的登录名
            account = self.db.get_github_account(chat_id)
            if account:
                head = f"{account.github_login}:{head}"
        
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text("⚠️ 需要先绑定 GitHub 账号！")
            return
        
        msg = await update.message.reply_text("🔀 正在创建 PR...")
        
        result = client.create_pr(
            owner=owner,
            repo=repo,
            title=title,
            body=f"由 Telegram Bot 自动创建\n\n原始标题: {title}",
            head=head
        )
        
        if result.success:
            await msg.edit_text(result.message, parse_mode="Markdown")
        else:
            await msg.edit_text(result.message, parse_mode="Markdown")
    
    # ==================== 分支命令 ====================
    
    async def create_branch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /branch 命令 - 创建分支"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        if not context.args:
            await update.message.reply_text(
                "🌿 **创建分支**\n\n"
                "请使用：`/branch owner/repo branch_name`\n\n"
                "例如：\n"
                "`/branch facebook/react feature/new-feature`\n"
                "`/branch microsoft/vscode bugfix/issue-123 --from main`",
                parse_mode="Markdown"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        # 获取分支名
        if len(context.args) < 2:
            await update.message.reply_text("❌ 请提供分支名！")
            return
        
        branch_name = context.args[1]
        
        # 检查是否有 --from 参数
        from_branch = "main"
        if "--from" in context.args:
            idx = context.args.index("--from")
            if idx + 1 < len(context.args):
                from_branch = context.args[idx + 1]
        
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text("⚠️ 需要先绑定 GitHub 账号！")
            return
        
        msg = await update.message.reply_text(f"🌿 正在创建分支 `{branch_name}`...")
        
        success, response = client.create_branch(owner, repo, branch_name, from_branch)
        
        await msg.edit_text(response, parse_mode="Markdown")
    
    async def delete_branch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /deletebranch 命令 - 删除分支"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        if not context.args:
            await update.message.reply_text(
                "🗑️ **删除分支**\n\n"
                "请使用：`/deletebranch owner/repo branch_name`",
                parse_mode="Markdown"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ 请提供分支名！")
            return
        
        branch_name = context.args[1]
        
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text("⚠️ 需要先绑定 GitHub 账号！")
            return
        
        msg = await update.message.reply_text(f"🗑️ 正在删除分支 `{branch_name}`...")
        
        success, response = client.delete_branch(owner, repo, branch_name)
        
        await msg.edit_text(response, parse_mode="Markdown")
    
    # ==================== Star 命令 ====================
    
    async def star_repo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /star 命令"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        if not context.args:
            await update.message.reply_text(
                "⭐ **Star 仓库**\n\n"
                "请使用：`/star owner/repo`"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text("⚠️ 需要先绑定 GitHub 账号！")
            return
        
        success, response = client.star_repo(owner, repo)
        
        await update.message.reply_text(response, parse_mode="Markdown")
    
    async def unstar_repo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /unstar 命令"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        if not context.args:
            await update.message.reply_text(
                "👎 **取消 Star**\n\n"
                "请使用：`/unstar owner/repo`"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo_input(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text("⚠️ 需要先绑定 GitHub 账号！")
            return
        
        success, response = client.unstar_repo(owner, repo)
        
        await update.message.reply_text(response, parse_mode="Markdown")
    
    # ==================== 搜索命令 ====================
    
    async def search_repos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /search 命令 - 搜索仓库"""
        if not context.args:
            await update.message.reply_text(
                "🔍 **搜索 GitHub 仓库**\n\n"
                "请使用：`/search <关键词>`\n\n"
                "示例：\n"
                "`/search python telegram bot`\n"
                "`/search javascript react`"
            )
            return
        
        query = " ".join(context.args)
        
        msg = await update.message.reply_text(f"🔍 正在搜索: **{query}**...")
        
        # 使用基础客户端搜索
        results = self.monitor.search_repos(query, limit=10)
        
        if not results:
            await msg.edit_text(f"📭 未找到相关仓库: **{query}**")
            return
        
        search_msg = f"🔍 **搜索结果: {query}**\n\n"
        
        for i, repo in enumerate(results[:5], 1):
            search_msg += f"**{i}. {repo['full_name']}**\n"
            search_msg += f"   📝 {repo['description'] or '无描述'}\n"
            search_msg += f"   ⭐ {repo['stars']} ⭐"
            if repo.get('language'):
                search_msg += f" • 💻 {repo['language']}"
            search_msg += "\n\n"
        
        search_msg += "[在 GitHub 上搜索更多结果](https://github.com/search?q=" + query.replace(" ", "+") + ")"
        
        await msg.edit_text(search_msg, parse_mode="Markdown", disable_web_page_preview=True)
    
    # ==================== 我的仓库命令 ====================
    
    async def my_repos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /myrepos 命令 - 查看我的仓库"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        account = self.db.get_github_account(chat_id)
        if not account:
            return
        
        client = self._get_advanced_client(chat_id)
        if not client:
            return
        
        msg = await update.message.reply_text("📥 正在获取您的仓库...")
        
        # 使用 OAuth 获取仓库
        if self.oauth:
            repos = self.oauth.get_user_repos(account.access_token, limit=20)
        else:
            repos = []
        
        if not repos:
            await msg.edit_text("📭 您还没有公开仓库")
            return
        
        repos_msg = f"📦 **@{account.github_login} 的仓库** (共 {account.public_repos} 个)\n\n"
        
        for repo in repos[:10]:
            private_emoji = "🔒" if repo.get('private') else "📢"
            repos_msg += f"{private_emoji} **{repo['name']}**\n"
            repos_msg += f"   📝 {repo.get('description') or '无描述'}\n"
            repos_msg += f"   ⭐ {repo.get('stargazers_count', 0)} ⭐"
            if repo.get('language'):
                repos_msg += f" • 💻 {repo['language']}"
            repos_msg += "\n\n"
        
        await msg.edit_text(repos_msg, parse_mode="Markdown")
    
    # ==================== 通知命令 ====================
    
    async def notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /notifications 命令 - 查看通知"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        account = self.db.get_github_account(chat_id)
        if not account:
            return
        
        msg = await update.message.reply_text("🔔 正在获取通知...")
        
        if self.oauth:
            notifications = self.oauth.get_notifications(account.access_token)
        else:
            notifications = []
        
        if not notifications:
            await msg.edit_text("✅ 您没有未读通知")
            return
        
        notif_msg = f"🔔 **GitHub 通知** (共 {len(notifications)} 条)\n\n"
        
        for notif in notifications[:10]:
            reason_map = {
                'mention': '💬 提及',
                'review_requested': '👀 请求 review',
                'assign': '📌 被分配',
                'author': '✍️ 作者',
                'subscribed': '📢 订阅'
            }
            reason = reason_map.get(notif['reason'], notif['reason'])
            
            notif_msg += f"**{reason}**\n"
            notif_msg += f"📄 {notif['subject']['title']}\n"
            notif_msg += f"📦 {notif['repository']['full_name']}\n\n"
        
        await msg.edit_text(notif_msg, parse_mode="Markdown")
    
    # ==================== Gist 命令 ====================
    
    async def create_gist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /gist 命令 - 创建 Gist"""
        chat_id = update.effective_chat.id
        
        if not self._check_github_bound(update):
            return
        
        # 解析参数
        if not context.args:
            await update.message.reply_text(
                "📝 **创建 Gist**\n\n"
                "请使用：`/gist filename content --public`\n\n"
                "示例：\n"
                "`/gist test.py \"print('hello')\" --public`\n"
                "`/gist notes.txt \"some notes\"`",
                parse_mode="Markdown"
            )
            return
        
        # 简单解析
        text = " ".join(context.args)
        is_public = "--public" in text
        text = text.replace("--public", "").strip()
        
        parts = text.split(" ", 1)
        if len(parts) != 2:
            await update.message.reply_text("❌ 格式错误！")
            return
        
        filename, content = parts
        
        client = self._get_advanced_client(chat_id)
        if not client:
            await update.message.reply_text("⚠️ 需要先绑定 GitHub 账号！")
            return
        
        msg = await update.message.reply_text("📝 正在创建 Gist...")
        
        success, response = client.create_gist(
            files={filename: content},
            description=f"Created via Telegram Bot",
            public=is_public
        )
        
        await msg.edit_text(response, parse_mode="Markdown")
    
    # ==================== 快捷命令 ====================
    
    async def quick_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /quick 命令 - 快捷命令"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            # 显示快捷命令列表
            commands = self.db.get_quick_commands(chat_id)
            
            if not commands:
                await update.message.reply_text(
                    "⚡ **快捷命令**\n\n"
                    "暂无快捷命令\n\n"
                    "使用 `/quick add <名称> <命令>` 添加",
                    parse_mode="Markdown"
                )
                return
            
            msg = "⚡ **快捷命令列表**\n\n"
            for cmd in commands:
                msg += f"`/quick {cmd['name']}` - {cmd['command'][:30]}...\n"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
            return
        
        subcommand = context.args[0]
        
        if subcommand == "add" and len(context.args) >= 3:
            # 添加快捷命令
            name = context.args[1]
            command = " ".join(context.args[2:])
            
            if self.db.add_quick_command(chat_id, name, command):
                await update.message.reply_text(
                    f"✅ 已添加快捷命令: `/quick {name}`",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ 添加失败！")
        
        elif subcommand == "del" and len(context.args) >= 2:
            # 删除快捷命令
            name = context.args[1]
            
            if self.db.delete_quick_command(chat_id, name):
                await update.message.reply_text(f"✅ 已删除快捷命令: `{name}`")
            else:
                await update.message.reply_text("❌ 删除失败！")
        
        else:
            # 执行快捷命令
            name = subcommand
            commands = self.db.get_quick_commands(chat_id)
            
            for cmd in commands:
                if cmd['name'] == name:
                    # 执行命令
                    command = cmd['command']
                    # 这里可以解析并执行命令
                    await update.message.reply_text(
                        f"⚡ 执行: `{command}`\n\n"
                        f"(快捷命令执行功能开发中)",
                        parse_mode="Markdown"
                    )
                    return
            
            await update.message.reply_text(f"❌ 未找到快捷命令: `{name}`")


# 导出
from enum import Enum
