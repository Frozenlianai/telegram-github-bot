"""
完整菜单系统 - 按钮式交互
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode


class CompleteMenu:
    """完整菜单系统"""
    
    # ==================== 主菜单 ====================
    
    @staticmethod
    def main_menu(has_github: bool = False, has_tracked: bool = False) -> InlineKeyboardMarkup:
        """主菜单 - 顶部按钮"""
        keyboard = [
            # 第一行：主要功能
            [
                InlineKeyboardButton("🔥 Trending", callback_data="menu:trending"),
                InlineKeyboardButton("📊 热门排行", callback_data="menu:hot"),
            ],
            [
                InlineKeyboardButton("🚀 爆发项目", callback_data="menu:exploding"),
                InlineKeyboardButton("📈 Stars追踪", callback_data="menu:track"),
            ],
            # 第二行：仓库管理
            [
                InlineKeyboardButton("➕ 添加监控", callback_data="menu:add"),
                InlineKeyboardButton("📋 我的仓库", callback_data="menu:list"),
            ],
            # 第三行：高级功能
            [
                InlineKeyboardButton("🍴 Fork", callback_data="menu:fork"),
                InlineKeyboardButton("🔀 PR操作", callback_data="menu:pr"),
            ],
            [
                InlineKeyboardButton("🚀 Actions", callback_data="menu:actions"),
                InlineKeyboardButton("🌿 分支", callback_data="menu:branch"),
            ],
            # 第四行：账号和设置
            [
                InlineKeyboardButton("🔗 GitHub账号", callback_data="menu:github"),
                InlineKeyboardButton("⚙️ 设置", callback_data="menu:settings"),
            ],
            # 第五行：其他
            [
                InlineKeyboardButton("🔍 搜索", callback_data="menu:search"),
                InlineKeyboardButton("📖 帮助", callback_data="menu:help"),
            ],
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== Trending 子菜单 ====================
    
    @staticmethod
    def trending_menu() -> InlineKeyboardMarkup:
        """Trending 菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🐍 Python", callback_data="trending:python"),
                InlineKeyboardButton("🟨 JavaScript", callback_data="trending:javascript"),
                InlineKeyboardButton("🔵 TypeScript", callback_data="trending:typescript"),
            ],
            [
                InlineKeyboardButton("🐹 Go", callback_data="trending:go"),
                InlineKeyboardButton("🦀 Rust", callback_data="trending:rust"),
                InlineKeyboardButton("☕ Java", callback_data="trending:java"),
            ],
            [
                InlineKeyboardButton("🌐 所有语言", callback_data="trending:all"),
            ],
            [
                InlineKeyboardButton("🔥 今日最热", callback_data="menu:hot"),
                InlineKeyboardButton("🚀 爆发项目", callback_data="menu:exploding"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def trending_results_menu(language: str, since: str = "daily") -> InlineKeyboardMarkup:
        """Trending 结果菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🐍 Python", callback_data=f"trending:python"),
                InlineKeyboardButton("🟨 JS", callback_data="trending:javascript"),
                InlineKeyboardButton("🔵 TS", callback_data="trending:typescript"),
            ],
            [
                InlineKeyboardButton("🐹 Go", callback_data="trending:go"),
                InlineKeyboardButton("🦀 Rust", callback_data="trending:rust"),
                InlineKeyboardButton("🌐 全部", callback_data="trending:all"),
            ],
            [
                InlineKeyboardButton("📅 本周", callback_data=f"trending:{language}:weekly"),
                InlineKeyboardButton("📅 本月", callback_data=f"trending:{language}:monthly"),
            ],
            [
                InlineKeyboardButton("🔄 刷新", callback_data=f"trending:{language}:{since}"),
                InlineKeyboardButton("◀️ 返回", callback_data="menu:trending"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== 热门排行子菜单 ====================
    
    @staticmethod
    def hot_menu() -> InlineKeyboardMarkup:
        """热门排行菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🥇 Top 10", callback_data="hot:top10"),
                InlineKeyboardButton("🥈 Top 25", callback_data="hot:top25"),
            ],
            [
                InlineKeyboardButton("📊 语言分布", callback_data="hot:languages"),
                InlineKeyboardButton("📈 增长趋势", callback_data="hot:trend"),
            ],
            [
                InlineKeyboardButton("🔄 刷新排行", callback_data="hot:refresh"),
                InlineKeyboardButton("◀️ 返回", callback_data="menu:hot"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== Stars 追踪子菜单 ====================
    
    @staticmethod
    def track_menu() -> InlineKeyboardMarkup:
        """Stars 追踪菜单"""
        keyboard = [
            [
                InlineKeyboardButton("➕ 添加追踪", callback_data="track:add"),
                InlineKeyboardButton("📋 我的追踪", callback_data="track:list"),
            ],
            [
                InlineKeyboardButton("🔥 最热追踪", callback_data="track:hot"),
                InlineKeyboardButton("📈 增长排行", callback_data="track:rank"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def tracked_repo_menu(owner: str, repo: str, is_tracked: bool = False) -> InlineKeyboardMarkup:
        """已追踪仓库的操作菜单"""
        keyboard = [
            [
                InlineKeyboardButton("📊 详情", callback_data=f"watch:{owner}/{repo}"),
                InlineKeyboardButton("📈 Stars图表", callback_data=f"stars_chart:{owner}/{repo}"),
            ],
            [
                InlineKeyboardButton("🍴 Fork", callback_data=f"fork:{owner}/{repo}"),
                InlineKeyboardButton("⭐ Star", callback_data=f"star:{owner}/{repo}"),
            ],
            [
                InlineKeyboardButton("🔍 类似项目", callback_data=f"similar:{owner}/{repo}"),
                InlineKeyboardButton("📝 最近活动", callback_data=f"recent:{owner}/{repo}"),
            ],
        ]
        
        if is_tracked:
            keyboard.append([
                InlineKeyboardButton("🗑️ 取消追踪", callback_data=f"untrack:{owner}/{repo}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("📈 加入追踪", callback_data=f"track:{owner}/{repo}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ 返回", callback_data="menu:track")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== 仓库管理子菜单 ====================
    
    @staticmethod
    def repo_management_menu() -> InlineKeyboardMarkup:
        """仓库管理菜单"""
        keyboard = [
            [
                InlineKeyboardButton("➕ 添加仓库", callback_data="add:prompt"),
                InlineKeyboardButton("📋 仓库列表", callback_data="list:show"),
            ],
            [
                InlineKeyboardButton("📊 监控状态", callback_data="status:show"),
                InlineKeyboardButton("⚙️ 通知设置", callback_data="settings:notifications"),
            ],
            [
                InlineKeyboardButton("⏱️ 检查间隔", callback_data="settings:interval"),
                InlineKeyboardButton("🗑️ 移除仓库", callback_data="remove:prompt"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def repo_list_menu(repos: list, page: int = 1) -> InlineKeyboardMarkup:
        """仓库列表菜单（带分页和操作）"""
        per_page = 5
        total = len(repos)
        total_pages = (total + per_page - 1) // per_page
        
        keyboard = []
        
        # 仓库按钮
        start = (page - 1) * per_page
        end = min(start + per_page, total)
        
        for repo in repos[start:end]:
            keyboard.append([
                InlineKeyboardButton(
                    f"📦 {repo['owner']}/{repo['repo']}",
                    callback_data=f"watch:{repo['owner']}/{repo['repo']}"
                )
            ])
        
        # 分页导航
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f"list:page:{page-1}"))
        nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="list:noop"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f"list:page:{page+1}"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([
            InlineKeyboardButton("➕ 添加仓库", callback_data="add:prompt"),
            InlineKeyboardButton("◀️ 返回", callback_data="menu:add"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== Fork 子菜单 ====================
    
    @staticmethod
    def fork_menu() -> InlineKeyboardMarkup:
        """Fork 操作菜单"""
        keyboard = [
            [
                InlineKeyboardButton("➕ Fork 仓库", callback_data="fork:prompt"),
                InlineKeyboardButton("📋 Fork 历史", callback_data="forks:history"),
            ],
            [
                InlineKeyboardButton("🔍 搜索仓库", callback_data="fork:search"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def fork_result_menu(owner: str, repo: str) -> InlineKeyboardMarkup:
        """Fork 结果操作菜单"""
        keyboard = [
            [
                InlineKeyboardButton("📦 查看 Fork", callback_data=f"watch:{owner}/{repo}"),
                InlineKeyboardButton("🔀 创建 PR", callback_data=f"pr:create:{owner}/{repo}"),
            ],
            [
                InlineKeyboardButton("⭐ Star", callback_data=f"star:{owner}/{repo}"),
                InlineKeyboardButton("📈 加入追踪", callback_data=f"track:{owner}/{repo}"),
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data="menu:fork"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== PR 子菜单 ====================
    
    @staticmethod
    def pr_menu() -> InlineKeyboardMarkup:
        """PR 操作菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🔀 创建 PR", callback_data="pr:create:prompt"),
                InlineKeyboardButton("⚡ 快速创建", callback_data="pr:quick"),
            ],
            [
                InlineKeyboardButton("📋 我的 PRs", callback_data="pr:mine"),
                InlineKeyboardButton("🔍 查看 PR", callback_data="pr:view:prompt"),
            ],
            [
                InlineKeyboardButton("✅ 合并 PR", callback_data="pr:merge:prompt"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== Actions 子菜单 ====================
    
    @staticmethod
    def actions_menu() -> InlineKeyboardMarkup:
        """Actions 操作菜单"""
        keyboard = [
            [
                InlineKeyboardButton("📋 查看 Workflows", callback_data="actions:workflows:prompt"),
                InlineKeyboardButton("📊 运行状态", callback_data="actions:status:prompt"),
            ],
            [
                InlineKeyboardButton("🚀 触发 Workflow", callback_data="actions:run:prompt"),
                InlineKeyboardButton("🔄 重新运行", callback_data="actions:rerun:prompt"),
            ],
            [
                InlineKeyboardButton("⏹️ 取消运行", callback_data="actions:cancel:prompt"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def workflow_menu(owner: str, repo: str, workflows: list) -> InlineKeyboardMarkup:
        """Workflow 列表菜单"""
        keyboard = []
        
        for wf in workflows[:10]:
            keyboard.append([
                InlineKeyboardButton(
                    f"⚡ {wf['name']}",
                    callback_data=f"workflow:run:{owner}/{repo}:{wf['id']}"
                )
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("🔄 刷新", callback_data=f"workflows:refresh:{owner}/{repo}"),
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data="menu:actions"),
            ],
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== 分支子菜单 ====================
    
    @staticmethod
    def branch_menu() -> InlineKeyboardMarkup:
        """分支操作菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🌿 查看分支", callback_data="branch:list:prompt"),
                InlineKeyboardButton("➕ 创建分支", callback_data="branch:create:prompt"),
            ],
            [
                InlineKeyboardButton("🛡️ 保护分支", callback_data="branch:protect:prompt"),
                InlineKeyboardButton("🗑️ 删除分支", callback_data="branch:delete:prompt"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== GitHub 账号子菜单 ====================
    
    @staticmethod
    def github_menu(is_bound: bool = False) -> InlineKeyboardMarkup:
        """GitHub 账号菜单"""
        keyboard = []
        
        if is_bound:
            keyboard.extend([
                [
                    InlineKeyboardButton("👤 账号信息", callback_data="github:info"),
                    InlineKeyboardButton("📦 我的仓库", callback_data="github:repos"),
                ],
                [
                    InlineKeyboardButton("🍴 Fork 历史", callback_data="github:forks"),
                    InlineKeyboardButton("🔔 通知", callback_data="github:notifications"),
                ],
                [
                    InlineKeyboardButton("🔄 刷新信息", callback_data="github:refresh"),
                    InlineKeyboardButton("🔓 解绑账号", callback_data="github:unbind"),
                ],
            ])
        else:
            keyboard.extend([
                [
                    InlineKeyboardButton("🔗 绑定账号", callback_data="github:bind"),
                ],
                [
                    InlineKeyboardButton("📖 了解绑定", callback_data="github:about"),
                ],
            ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== 设置子菜单 ====================
    
    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """设置菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🔔 通知设置", callback_data="settings:notifications"),
                InlineKeyboardButton("⏱️ 检查间隔", callback_data="settings:interval"),
            ],
            [
                InlineKeyboardButton("📊 监控统计", callback_data="settings:stats"),
                InlineKeyboardButton("🗑️ 清除数据", callback_data="settings:clear"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def notification_settings_menu(settings: dict) -> InlineKeyboardMarkup:
        """通知设置菜单"""
        keyboard = []
        
        items = [
            ("⭐ Stars 变化", "notify_stars", "⭐"),
            ("🍴 Forks 变化", "notify_forks", "🍴"),
            ("📝 新提交", "notify_commits", "📝"),
            ("🔀 Pull Requests", "notify_prs", "🔀"),
            ("🐛 Issues", "notify_issues", "🐛"),
            ("🚀 Releases", "notify_releases", "🚀"),
            ("🌿 分支变化", "notify_branches", "🌿"),
        ]
        
        for name, key, emoji in items:
            status = "✅" if settings.get(key, True) else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {name} {status}",
                    callback_data=f"settings:toggle:{key}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ 返回设置", callback_data="menu:settings"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== 搜索子菜单 ====================
    
    @staticmethod
    def search_menu() -> InlineKeyboardMarkup:
        """搜索菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🔍 搜索仓库", callback_data="search:repos"),
                InlineKeyboardButton("💻 搜索代码", callback_data="search:code"),
            ],
            [
                InlineKeyboardButton("📦 搜索用户", callback_data="search:users"),
                InlineKeyboardButton("🔥 热门搜索", callback_data="search:popular"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== 帮助子菜单 ====================
    
    @staticmethod
    def help_menu() -> InlineKeyboardMarkup:
        """帮助菜单"""
        keyboard = [
            [
                InlineKeyboardButton("📖 命令列表", callback_data="help:commands"),
                InlineKeyboardButton("💡 使用技巧", callback_data="help:tips"),
            ],
            [
                InlineKeyboardButton("🔗 快捷链接", callback_data="help:links"),
                InlineKeyboardButton("📝 示例", callback_data="help:examples"),
            ],
            [
                InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # ==================== 通用操作 ====================
    
    @staticmethod
    def confirm_action(action: str, item_id: str, confirm_text: str = "确认") -> InlineKeyboardMarkup:
        """确认操作"""
        keyboard = [
            [
                InlineKeyboardButton(f"✅ {confirm_text}", callback_data=f"confirm:{action}:{item_id}"),
                InlineKeyboardButton("❌ 取消", callback_data="cancel:action"),
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_menu() -> InlineKeyboardMarkup:
        """返回主菜单"""
        keyboard = [
            [InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def loading(message_id: str = None) -> InlineKeyboardMarkup:
        """加载中"""
        keyboard = [
            [InlineKeyboardButton("⏳ 加载中...", callback_data="noop")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def repo_quick_actions(owner: str, repo: str) -> InlineKeyboardMarkup:
        """仓库快捷操作"""
        keyboard = [
            [
                InlineKeyboardButton("📊 详情", callback_data=f"watch:{owner}/{repo}"),
                InlineKeyboardButton("📈 追踪", callback_data=f"track:{owner}/{repo}"),
            ],
            [
                InlineKeyboardButton("🍴 Fork", callback_data=f"fork:{owner}/{repo}"),
                InlineKeyboardButton("⭐ Star", callback_data=f"star:{owner}/{repo}"),
            ],
            [
                InlineKeyboardButton("🔀 PRs", callback_data=f"prs:{owner}/{repo}"),
                InlineKeyboardButton("🐛 Issues", callback_data=f"issues:{owner}/{repo}"),
            ],
            [
                InlineKeyboardButton("🚀 Releases", callback_data=f"releases:{owner}/{repo}"),
                InlineKeyboardButton("🌿 分支", callback_data=f"branches:{owner}/{repo}"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)


# ==================== 辅助格式化函数 ====================

def format_trending_list(repos: list, title: str = "🔥 Trending") -> str:
    """格式化 Trending 列表"""
    lines = [f"{title}\n"]
    
    for repo in repos[:10]:
        # 增长指示器
        if repo.stars_today >= 500:
            indicator = "🚀"
        elif repo.stars_today >= 100:
            indicator = "🔥"
        elif repo.stars_today >= 50:
            indicator = "📈"
        else:
            indicator = "⭐"
        
        lines.append(f"{indicator} **{repo.full_name}**")
        lines.append(f"   {repo.description[:50]}..." if len(repo.description) > 50 else f"   {repo.description}")
        lines.append(f"   ⭐ {repo.stars:,} | 🍴 {repo.forks:,}" + 
                    (f" | 📈 +{repo.stars_today:,}" if repo.stars_today else ""))
        lines.append("")
    
    return "\n".join(lines)


def format_hot_list(repos: list, title: str = "🔥 热门排行") -> str:
    """格式化热门列表"""
    lines = [f"{title}\n"]
    lines.append("=" * 40)
    lines.append("")
    
    for i, repo in enumerate(repos[:10], 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        
        lines.append(f"{medal} **{repo.full_name}**")
        lines.append(f"   {repo.description[:60]}..." if len(repo.description) > 60 else f"   {repo.description}")
        
        if repo.language:
            lines.append(f"   💻 {repo.language}")
        
        lines.append(f"   ⭐ {repo.stars:,} | 📈 +{repo.stars_today:,} 今天")
        
        # 热度评分
        score = calculate_heat_score(repo)
        lines.append(f"   🔥 热度: {score:,.0f}")
        lines.append(f"   🔗 {repo.url}")
        lines.append("")
    
    return "\n".join(lines)


def format_tracked_list(tracked: list) -> str:
    """格式化追踪列表"""
    if not tracked:
        return "📭 暂无追踪的项目\n\n点击下方按钮添加追踪："
    
    lines = ["📈 **追踪的项目**\n"]
    
    for item in tracked[:10]:
        growth = item.get('current_stars', 0) - item.get('initial_stars', 0)
        growth_rate = (growth / item.get('initial_stars', 1) * 100) if item.get('initial_stars', 0) > 0 else 0
        
        emoji = "🚀" if growth > 1000 else ("🔥" if growth > 100 else "📈")
        
        lines.append(f"{emoji} **{item['owner']}/{item['repo']}**")
        lines.append(f"   ⭐ {item.get('current_stars', 0):,}")
        lines.append(f"   📈 增长: +{growth:,} ({growth_rate:.1f}%)")
        lines.append("")
    
    return "\n".join(lines)


def format_repo_card(repo_info: dict) -> str:
    """格式化仓库卡片"""
    lines = [
        f"📦 **{repo_info.get('full_name', 'Unknown')}**\n",
    ]
    
    if repo_info.get('description'):
        lines.append(f"📝 {repo_info['description'][:80]}...\n")
    
    lines.append("📊 **统计**")
    lines.append(f"⭐ Stars: **{repo_info.get('stars', 0):,}**")
    lines.append(f"🍴 Forks: **{repo_info.get('forks', 0):,}**")
    lines.append(f"👁️ Watchers: **{repo_info.get('watchers', 0):,}**")
    
    if repo_info.get('language'):
        lines.append(f"💻 语言: **{repo_info['language']}**")
    
    if repo_info.get('topics'):
        topics = " ".join([f"`{t}`" for t in repo_info['topics'][:5]])
        lines.append(f"🏷️ 主题: {topics}")
    
    return "\n".join(lines)


def calculate_heat_score(repo) -> float:
    """计算热度评分"""
    stars = getattr(repo, 'stars', 0)
    stars_today = getattr(repo, 'stars_today', 0)
    forks = getattr(repo, 'forks', 0)
    
    # 综合评分公式
    score = (stars * 0.1) + (stars_today * 5) + (forks * 0.2)
    
    return round(score, 2)


def format_user_profile(account: dict) -> str:
    """格式化用户资料"""
    lines = [
        "👤 **GitHub 账号信息**\n",
        f"🔗 登录: **@{account.get('login', 'N/A')}**",
    ]
    
    if account.get('name'):
        lines.append(f"📛 名称: {account['name']}")
    
    if account.get('bio'):
        lines.append(f"📝 简介: {account['bio']}")
    
    lines.append("\n📊 **统计**")
    lines.append(f"📦 公开仓库: **{account.get('public_repos', 0)}**")
    lines.append(f"👥 Followers: **{account.get('followers', 0)}**")
    lines.append(f"➡️ Following: **{account.get('following', 0)}**")
    
    return "\n".join(lines)


# 导出
Menu = CompleteMenu
