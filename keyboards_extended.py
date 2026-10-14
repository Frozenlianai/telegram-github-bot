"""
扩展键盘菜单
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards import Keyboards as BaseKeyboards


class ExtendedKeyboards(BaseKeyboards):
    """扩展键盘菜单类"""
    
    @staticmethod
    def github_bind_keyboard() -> InlineKeyboardMarkup:
        """GitHub 绑定键盘"""
        keyboard = [
            [InlineKeyboardButton("🔗 绑定 GitHub", callback_data="github:bind")],
            [InlineKeyboardButton("📊 查看绑定状态", callback_data="github:status")],
            [InlineKeyboardButton("🔓 解绑账号", callback_data="github:unbind")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def github_profile_keyboard(login: str) -> InlineKeyboardMarkup:
        """GitHub 个人资料键盘"""
        keyboard = [
            [
                InlineKeyboardButton("📦 我的仓库", callback_data="github:repos"),
                InlineKeyboardButton("🍴 Fork 历史", callback_data="github:forks")
            ],
            [
                InlineKeyboardButton("🔔 通知", callback_data="github:notifications"),
                InlineKeyboardButton("🔍 搜索", callback_data="github:search")
            ],
            [
                InlineKeyboardButton("🔄 刷新", callback_data="github:refresh")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def fork_keyboard(owner: str, repo: str) -> InlineKeyboardMarkup:
        """Fork 操作键盘"""
        keyboard = [
            [
                InlineKeyboardButton("🍴 Fork", callback_data=f"fork:{owner}/{repo}"),
                InlineKeyboardButton("⭐ Star", callback_data=f"star:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("📊 统计", callback_data=f"stats:{owner}/{repo}"),
                InlineKeyboardButton("🔀 PR", callback_data=f"prs:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("🔙 返回", callback_data="back:main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def workflow_keyboard(owner: str, repo: str, workflow_id: str, 
                          workflow_name: str) -> InlineKeyboardMarkup:
        """Workflow 操作键盘"""
        keyboard = [
            [
                InlineKeyboardButton("🚀 运行", callback_data=f"workflow:run:{owner}/{repo}:{workflow_id}"),
                InlineKeyboardButton("📜 运行历史", callback_data=f"workflow:runs:{owner}/{repo}:{workflow_id}")
            ],
            [
                InlineKeyboardButton("🔄 监控此 Workflow", callback_data=f"workflow:monitor:{owner}/{repo}:{workflow_id}"),
                InlineKeyboardButton("👀 详情", callback_data=f"workflow:info:{workflow_id}")
            ],
            [
                InlineKeyboardButton("🔙 返回", callback_data=f"back:workflows:{owner}/{repo}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def actions_keyboard(owner: str, repo: str) -> InlineKeyboardMarkup:
        """Actions 键盘"""
        keyboard = [
            [
                InlineKeyboardButton("📋 所有 Workflows", callback_data=f"workflows:list:{owner}/{repo}"),
                InlineKeyboardButton("📊 运行状态", callback_data=f"run_status:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("🚀 触发 Workflow", callback_data=f"workflows:trigger:{owner}/{repo}"),
                InlineKeyboardButton("🔄 重新运行", callback_data=f"workflows:rerun:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("🔙 返回", callback_data="back:main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def pr_keyboard(owner: str, repo: str, pr_number: int) -> InlineKeyboardMarkup:
        """PR 操作键盘"""
        keyboard = [
            [
                InlineKeyboardButton("🔀 查看 PR", callback_data=f"pr:view:{owner}/{repo}:{pr_number}"),
                InlineKeyboardButton("✅ 合并", callback_data=f"pr:merge:{owner}/{repo}:{pr_number}")
            ],
            [
                InlineKeyboardButton("📝 文件变更", callback_data=f"pr:files:{owner}/{repo}:{pr_number}"),
                InlineKeyboardButton("💬 Reviews", callback_data=f"pr:reviews:{owner}/{repo}:{pr_number}")
            ],
            [
                InlineKeyboardButton("🔙 返回", callback_data=f"back:prs:{owner}/{repo}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def branch_keyboard(owner: str, repo: str) -> InlineKeyboardMarkup:
        """分支操作键盘"""
        keyboard = [
            [
                InlineKeyboardButton("🌿 查看分支", callback_data=f"branches:list:{owner}/{repo}"),
                InlineKeyboardButton("➕ 创建分支", callback_data=f"branch:create:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("🗑️ 删除分支", callback_data=f"branch:delete:{owner}/{repo}"),
                InlineKeyboardButton("🛡️ 保护分支", callback_data=f"branch:protect:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("🔙 返回", callback_data="back:main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def run_status_keyboard(owner: str, repo: str, run_id: int) -> InlineKeyboardMarkup:
        """Workflow 运行状态键盘"""
        keyboard = [
            [
                InlineKeyboardButton("🔄 重新运行", callback_data=f"run:rerun:{owner}/{repo}:{run_id}"),
                InlineKeyboardButton("⏹️ 取消", callback_data=f"run:cancel:{owner}/{repo}:{run_id}")
            ],
            [
                InlineKeyboardButton("📜 查看日志", callback_data=f"run:logs:{owner}/{repo}:{run_id}"),
                InlineKeyboardButton("📋 查看 Jobs", callback_data=f"run:jobs:{owner}/{repo}:{run_id}")
            ],
            [
                InlineKeyboardButton("🔙 返回", callback_data=f"back:run_status:{owner}/{repo}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def quick_actions_keyboard(has_github: bool = False) -> InlineKeyboardMarkup:
        """快捷操作键盘（带 GitHub 状态）"""
        if has_github:
            keyboard = [
                [
                    InlineKeyboardButton("➕ 添加仓库", callback_data="cmd:add"),
                    InlineKeyboardButton("🍴 Fork", callback_data="cmd:fork")
                ],
                [
                    InlineKeyboardButton("🚀 Actions", callback_data="cmd:actions"),
                    InlineKeyboardButton("🔀 创建 PR", callback_data="cmd:pr")
                ],
                [
                    InlineKeyboardButton("📦 我的仓库", callback_data="cmd:myrepos"),
                    InlineKeyboardButton("🔍 搜索", callback_data="cmd:search")
                ],
                [
                    InlineKeyboardButton("⚙️ 设置", callback_data="cmd:settings")
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("➕ 添加仓库", callback_data="cmd:add"),
                    InlineKeyboardButton("🔗 绑定 GitHub", callback_data="cmd:bind")
                ],
                [
                    InlineKeyboardButton("🔍 搜索", callback_data="cmd:search"),
                    InlineKeyboardButton("⚙️ 设置", callback_data="cmd:settings")
                ]
            ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def main_menu_extended_keyboard() -> InlineKeyboardMarkup:
        """扩展主菜单键盘"""
        keyboard = [
            ["➕ 添加仓库", "🍴 Fork 仓库"],
            ["📋 仓库列表", "🚀 GitHub Actions"],
            ["🔗 GitHub 绑定", "⚙️ 设置"],
            ["📊 状态", "🔔 帮助"]
        ]
        from telegram import ReplyKeyboardMarkup
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def format_workflow_run(run: dict) -> str:
    """格式化 Workflow 运行信息"""
    # 状态图标
    status_emoji = {
        'queued': '⏳',
        'in_progress': '🔄',
        'completed': '✅'
    }.get(run.get('status', ''), '❓')
    
    conclusion_emoji = {
        'success': '✅',
        'failure': '❌',
        'cancelled': '⚠️',
        'timed_out': '⏰'
    }.get(run.get('conclusion', ''), '')
    
    emoji = status_emoji
    if run.get('conclusion'):
        emoji = conclusion_emoji
    
    lines = [
        f"{emoji} **{run.get('name', 'Unknown')}**",
        f"   🌿 分支: `{run.get('head_branch', '')}`",
        f"   🔖 Commit: `{run.get('head_sha', '')}`",
        f"   📅 {run.get('created_at', '')}"
    ]
    
    if run.get('duration'):
        minutes = run.get('duration', 0) // 60
        seconds = run.get('duration', 0) % 60
        lines.append(f"   ⏱️ 耗时: {minutes}m {seconds}s")
    
    if run.get('event'):
        lines.append(f"   🚀 触发: {run.get('event')}")
    
    return "\n".join(lines)


def format_pr_info(pr: dict) -> str:
    """格式化 PR 信息"""
    state_emoji = {
        'open': '🟢',
        'closed': '🔴',
        'merged': '🟣'
    }.get(pr.get('state', ''), '❓')
    
    lines = [
        f"{state_emoji} **#{pr.get('number')}: {pr.get('title', '')}**",
        f"   👤 作者: {pr.get('user', '')}",
        f"   🌿 {pr.get('head', {}).get('ref', '')} → {pr.get('base', {}).get('ref', 'main')}",
        f"   💬 {pr.get('comments', 0)} 评论"
    ]
    
    if pr.get('additions') and pr.get('deletions'):
        lines.append(f"   📝 +{pr.get('additions')} -{pr.get('deletions')}")
    
    if pr.get('draft'):
        lines.insert(1, "   📝 草稿")
    
    if pr.get('merged'):
        lines.insert(1, "   🟣 已合并")
    
    return "\n".join(lines)


def format_branch_list(branches: list, default_branch: str = "main") -> str:
    """格式化分支列表"""
    lines = ["🌿 **分支列表：**\n"]
    
    for branch in branches[:15]:
        marker = "📌" if branch['name'] == default_branch else "  "
        protected = "🔒" if branch.get('protected') else "  "
        lines.append(f"{marker}{protected} `{branch['name']}`")
        
        if branch.get('commit'):
            lines.append(f"      └ {branch['commit'][:7]}")
    
    if len(branches) > 15:
        lines.append(f"\n... 还有 {len(branches) - 15} 个分支")
    
    return "\n".join(lines)


def format_user_profile(account: dict) -> str:
    """格式化用户资料"""
    lines = [
        "👤 **GitHub 账号信息**\n",
        f"🔗 登录: **@{account.get('login', '')}**",
        f"🆔 ID: `{account.get('id', '')}`"
    ]
    
    if account.get('name'):
        lines.append(f"📛 名称: {account.get('name')}")
    
    if account.get('bio'):
        lines.append(f"📝 简介: {account.get('bio')}")
    
    if account.get('email'):
        lines.append(f"📧 邮箱: {account.get('email')}")
    
    lines.append("\n📊 **统计：**")
    lines.append(f"• 公开仓库: **{account.get('public_repos', 0)}**")
    lines.append(f"• Followers: **{account.get('followers', 0)}**")
    lines.append(f"• Following: **{account.get('following', 0)}**")
    
    return "\n".join(lines)
