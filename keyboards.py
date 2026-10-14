"""
Telegram 键盘菜单
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode


class Keyboards:
    """键盘菜单类"""
    
    # ==================== 内联键盘 ====================
    
    @staticmethod
    def repo_inline_keyboard(owner: str, repo: str) -> InlineKeyboardMarkup:
        """仓库操作内联键盘"""
        keyboard = [
            [
                InlineKeyboardButton("📊 统计", callback_data=f"stats:{owner}/{repo}"),
                InlineKeyboardButton("📝 最近提交", callback_data=f"commits:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("🔀 PR", callback_data=f"prs:{owner}/{repo}"),
                InlineKeyboardButton("🐛 Issues", callback_data=f"issues:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("🚀 Releases", callback_data=f"releases:{owner}/{repo}"),
                InlineKeyboardButton("🌿 分支", callback_data=f"branches:{owner}/{repo}")
            ],
            [
                InlineKeyboardButton("🔄 刷新", callback_data=f"refresh:{owner}/{repo}"),
                InlineKeyboardButton("❌ 取消监控", callback_data=f"remove:{owner}/{repo}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
        """设置菜单键盘"""
        keyboard = [
            [
                InlineKeyboardButton("⭐ Stars", callback_data=f"toggle:stars:{chat_id}"),
                InlineKeyboardButton("🍴 Forks", callback_data=f"toggle:forks:{chat_id}")
            ],
            [
                InlineKeyboardButton("📝 提交", callback_data=f"toggle:commits:{chat_id}"),
                InlineKeyboardButton("🔀 PRs", callback_data=f"toggle:prs:{chat_id}")
            ],
            [
                InlineKeyboardButton("🐛 Issues", callback_data=f"toggle:issues:{chat_id}"),
                InlineKeyboardButton("🚀 Releases", callback_data=f"toggle:releases:{chat_id}")
            ],
            [
                InlineKeyboardButton("🌿 分支", callback_data=f"toggle:branches:{chat_id}")
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data=f"back:menu:{chat_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirm_keyboard(action: str, item_id: str) -> InlineKeyboardMarkup:
        """确认键盘"""
        keyboard = [
            [
                InlineKeyboardButton("✅ 确认", callback_data=f"confirm:{action}:{item_id}"),
                InlineKeyboardButton("❌ 取消", callback_data=f"cancel:{action}:{item_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def pagination_keyboard(action: str, item_id: str, page: int, 
                            has_next: bool, has_prev: bool = False) -> InlineKeyboardMarkup:
        """分页键盘"""
        keyboard = []
        
        nav_row = []
        if has_prev:
            nav_row.append(InlineKeyboardButton("◀️ 上一页", 
                                                 callback_data=f"page:{action}:{item_id}:{page-1}"))
        if has_next:
            nav_row.append(InlineKeyboardButton("下一页 ▶️", 
                                                 callback_data=f"page:{action}:{item_id}:{page+1}"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([InlineKeyboardButton("🔙 返回", 
                                               callback_data=f"back:{action}:{item_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== 回复键盘 ====================
    
    @staticmethod
    def main_menu_keyboard() -> ReplyKeyboardMarkup:
        """主菜单键盘"""
        keyboard = [
            ["➕ 添加仓库", "➖ 移除仓库"],
            ["📋 我的仓库", "⚙️ 通知设置"],
            ["📊 监控状态", "🔔 帮助"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def help_keyboard() -> ReplyKeyboardMarkup:
        """帮助菜单键盘"""
        keyboard = [
            ["📖 命令列表", "💡 使用示例"],
            ["⚙️ 通知设置", "📊 监控状态"],
            ["◀️ 返回主菜单"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # ==================== 快捷键盘 ====================
    
    @staticmethod
    def quick_actions_keyboard() -> InlineKeyboardMarkup:
        """快捷操作键盘"""
        keyboard = [
            [
                InlineKeyboardButton("➕ 添加仓库", callback_data="cmd:add"),
                InlineKeyboardButton("📋 我的仓库", callback_data="cmd:list")
            ],
            [
                InlineKeyboardButton("⚙️ 设置", callback_data="cmd:settings"),
                InlineKeyboardButton("📊 状态", callback_data="cmd:status")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def notification_toggle_keyboard(current_settings: dict) -> InlineKeyboardMarkup:
        """通知开关键盘（带状态显示）"""
        def make_button(name: str, key: str, emoji: str) -> InlineKeyboardButton:
            status = "✅" if current_settings.get(key, True) else "❌"
            return InlineKeyboardButton(f"{emoji} {name} {status}", 
                                        callback_data=f"toggle:{key}:settings")
        
        keyboard = [
            [
                make_button("Stars", "notify_stars", "⭐"),
                make_button("Forks", "notify_forks", "🍴")
            ],
            [
                make_button("Commits", "notify_commits", "📝"),
                make_button("PRs", "notify_prs", "🔀")
            ],
            [
                make_button("Issues", "notify_issues", "🐛"),
                make_button("Releases", "notify_releases", "🚀")
            ],
            [
                make_button("Branches", "notify_branches", "🌿")
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data="back:main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)


def format_repo_list(repos: list, page: int = 1, per_page: int = 5) -> tuple[str, InlineKeyboardMarkup]:
    """格式化仓库列表"""
    start = (page - 1) * per_page
    end = start + per_page
    page_repos = repos[start:end]
    
    if not page_repos:
        return "📭 暂无监控的仓库", InlineKeyboardMarkup([])
    
    lines = [f"📦 **我的监控仓库** (共 {len(repos)} 个)\n"]
    
    for i, repo in enumerate(page_repos, start + 1):
        lines.append(f"{i}. `{repo.owner}/{repo.repo}`")
        lines.append(f"   ➕ {repo.added_at[:10]}")
        if repo.last_check:
            lines.append(f"   🔄 {repo.last_check[:16]}")
        lines.append("")
    
    total_pages = (len(repos) + per_page - 1) // per_page
    lines.append(f"📄 第 {page}/{total_pages} 页")
    
    keyboard = []
    nav_row = []
    
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️", callback_data=f"pagelist:{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("▶️", callback_data=f"pagelist:{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    return "\n".join(lines), InlineKeyboardMarkup(keyboard)


def format_settings_display(settings: dict) -> str:
    """格式化设置显示"""
    lines = [
        "⚙️ **通知设置**\n",
        "选择要接收的通知类型：\n"
    ]
    
    items = [
        ("⭐ Stars 变化", "notify_stars"),
        ("🍴 Forks 变化", "notify_forks"),
        ("📝 新提交", "notify_commits"),
        ("🔀 Pull Requests", "notify_prs"),
        ("🐛 Issues", "notify_issues"),
        ("🚀 Releases", "notify_releases"),
        ("🌿 分支变化", "notify_branches"),
    ]
    
    for name, key in items:
        status = "✅" if settings.get(key, True) else "❌"
        lines.append(f"{status} {name}")
    
    return "\n".join(lines)
