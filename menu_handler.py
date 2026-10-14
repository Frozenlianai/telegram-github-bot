"""
菜单回调查询处理器
处理所有按钮点击事件
"""

import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from github_trending import GitHubTrending
from menu_system import Menu, format_trending_list, format_hot_list, format_tracked_list, format_repo_card, calculate_heat_score


class MenuHandler:
    """菜单回调查询处理器"""
    
    def __init__(self, db, monitor, trending, ext_commands, trending_commands):
        self.db = db
        self.monitor = monitor
        self.trending = trending
        self.ext_commands = ext_commands
        self.trending_commands = trending_commands
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理所有回调查询"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        parts = data.split(':')
        action = parts[0]
        
        # 忽略 noop
        if action == "noop":
            return
        
        # 主菜单
        if action == "menu":
            await self._handle_menu(query, parts)
        
        # Trending
        elif action == "trending":
            await self._handle_trending(query, parts)
        
        # 热门排行
        elif action == "hot":
            await self._handle_hot(query, parts)
        
        # 爆发项目
        elif action == "exploding":
            await self._handle_exploding(query, parts)
        
        # 追踪
        elif action == "track":
            await self._handle_track(query, parts, context)
        
        # Stars 图表
        elif action.startswith("stars_chart"):
            await self._handle_stars_chart(query, parts)
        
        # 仓库操作
        elif action == "watch":
            await self._handle_watch(query, parts)
        
        # 添加仓库
        elif action == "add":
            await self._handle_add(query, parts, context)
        
        # 仓库列表
        elif action == "list":
            await self._handle_list(query, parts)
        
        # 移除仓库
        elif action == "remove":
            await self._handle_remove(query, parts, context)
        
        # Fork
        elif action == "fork":
            await self._handle_fork(query, parts, context)
        
        # PR
        elif action == "pr":
            await self._handle_pr(query, parts, context)
        
        # Actions
        elif action == "actions" or action == "workflow" or action == "workflows":
            await self._handle_actions(query, parts, context)
        
        # 分支
        elif action == "branch":
            await self._handle_branch(query, parts, context)
        
        # GitHub 账号
        elif action == "github":
            await self._handle_github(query, parts)
        
        # 设置
        elif action == "settings":
            await self._handle_settings(query, parts, context)
        
        # 搜索
        elif action == "search":
            await self._handle_search(query, parts, context)
        
        # 帮助
        elif action == "help":
            await self._handle_help(query, parts)
        
        # 确认操作
        elif action == "confirm":
            await self._handle_confirm(query, parts)
        
        # 取消操作
        elif action == "cancel":
            await self._handle_cancel(query, parts)
        
        # 状态显示
        elif action == "status":
            await self._handle_status(query, parts)
        
        # 仓库详情
        elif action in ["stats", "commits", "prs", "issues", "releases", "branches", "refresh"]:
            await self._handle_repo_action(query, action, parts)
    
    # ==================== 主菜单处理 ====================
    
    async def _handle_menu(self, query, parts: list):
        """处理主菜单"""
        chat_id = query.message.chat_id
        sub_action = parts[1] if len(parts) > 1 else "main"
        
        has_github = self.db.is_github_bound(chat_id)
        
        if sub_action == "main":
            text = """
🤖 **GitHub 监控机器人 V3**

欢迎使用！选择一个功能开始：
"""
            reply_markup = Menu.main_menu(has_github)
        
        elif sub_action == "trending":
            text = """
🔥 **Trending 菜单**

查看 GitHub 热门项目！
"""
            reply_markup = Menu.trending_menu()
        
        elif sub_action == "hot":
            text = """
📊 **热门排行**

今日最热项目！
"""
            reply_markup = Menu.hot_menu()
        
        elif sub_action == "exploding":
            text = """
🚀 **爆发项目检测**

发现爆发式增长的项目！
日均增长 +1000 stars 以上的项目！
"""
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔥 +1000 (超爆发)", callback_data="exploding:1000"),
                ],
                [
                    InlineKeyboardButton("🔍 +500 (大爆发)", callback_data="exploding:500"),
                    InlineKeyboardButton("🔍 +300 (中爆发)", callback_data="exploding:300"),
                ],
                [
                    InlineKeyboardButton("◀️ 返回主菜单", callback_data="menu:main"),
                ],
            ])
        
        elif sub_action == "track":
            text = """
📈 **Stars 追踪**

追踪项目 Stars 增长！
"""
            reply_markup = Menu.track_menu()
        
        elif sub_action == "add":
            text = """
➕ **添加监控**

管理您监控的仓库！
"""
            reply_markup = Menu.repo_management_menu()
        
        elif sub_action == "list":
            text = """
📋 **仓库列表**

查看所有监控的仓库！
"""
            reply_markup = Menu.repo_management_menu()
        
        elif sub_action == "fork":
            text = """
🍴 **Fork 操作**

一键 Fork 仓库！
"""
            reply_markup = Menu.fork_menu()
        
        elif sub_action == "pr":
            text = """
🔀 **PR 操作**

创建和管理 Pull Requests！
"""
            reply_markup = Menu.pr_menu()
        
        elif sub_action == "actions":
            text = """
🚀 **GitHub Actions**

管理 Workflows！
"""
            reply_markup = Menu.actions_menu()
        
        elif sub_action == "branch":
            text = """
🌿 **分支操作**

创建和管理分支！
"""
            reply_markup = Menu.branch_menu()
        
        elif sub_action == "github":
            text = """
🔗 **GitHub 账号**

绑定和管理 GitHub 账号！
"""
            reply_markup = Menu.github_menu(has_github)
        
        elif sub_action == "settings":
            text = """
⚙️ **设置**

配置机器人！
"""
            reply_markup = Menu.settings_menu()
        
        elif sub_action == "search":
            text = """
🔍 **搜索**

搜索仓库、代码、用户！
"""
            reply_markup = Menu.search_menu()
        
        elif sub_action == "help":
            text = """
📖 **帮助**

获取使用帮助！
"""
            reply_markup = Menu.help_menu()
        
        else:
            text = "未知菜单"
            reply_markup = Menu.back_to_menu()
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    # ==================== Trending 处理 ====================
    
    async def _handle_trending(self, query, parts: list):
        """处理 Trending"""
        # 解析语言和时间范围
        language = "all"
        since = "daily"
        
        if len(parts) >= 2:
            lang = parts[1]
            if lang in ['python', 'javascript', 'typescript', 'go', 'rust', 'java', 'all', 'cpp', 'csharp', 'ruby', 'php', 'swift', 'kotlin', 'dart']:
                language = lang if lang != 'cpp' else 'c++'
                if lang == 'csharp':
                    language = 'c#'
        
        if len(parts) >= 3:
            since = parts[2]
        
        # 获取 Trending 数据
        repos = self.trending.get_trending_repos(
            language=language if language != "all" else None,
            since=since
        )
        
        if not repos:
            repos = self.trending.get_trending_by_api(
                language=language if language != "all" else None,
                since=since
            )
        
        if not repos:
            await query.edit_message_text(
                "❌ 无法获取 Trending 数据\n\n请稍后重试！",
                reply_markup=Menu.back_to_menu()
            )
            return
        
        # 格式化消息
        lang_names = {
            'python': 'Python', 'javascript': 'JavaScript', 'typescript': 'TypeScript',
            'go': 'Go', 'rust': 'Rust', 'java': 'Java', 'all': '全部'
        }
        since_names = {'daily': '今日', 'weekly': '本周', 'monthly': '本月'}
        
        title = f"🔥 GitHub Trending ({lang_names.get(language, language)} - {since_names.get(since, since)})"
        text = format_trending_list(repos, title)
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=Menu.trending_results_menu(language, since),
            disable_web_page_preview=True
        )
    
    # ==================== 热门排行处理 ====================
    
    async def _handle_hot(self, query, parts: list):
        """处理热门排行"""
        sub_action = parts[1] if len(parts) > 1 else "top10"
        
        if sub_action == "refresh":
            sub_action = "top10"
        
        limit = 25 if sub_action == "top25" else 10
        
        # 获取热门项目
        hot_projects = self.trending.get_hot_projects(limit=limit)
        
        if not hot_projects:
            await query.edit_message_text(
                "❌ 无法获取热门数据",
                reply_markup=Menu.back_to_menu()
            )
            return
        
        title = f"🔥 今日最热项目 (Top {limit})"
        text = format_hot_list(hot_projects, title)
        
        # 为每个项目创建直达按钮
        keyboard = []
        for repo in hot_projects[:10]:  # 最多10个直达按钮
            keyboard.append([
                InlineKeyboardButton(f"🚀 {repo.repo}", url=repo.url)
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("🥇 Top 10", callback_data="hot:top10"),
                InlineKeyboardButton("🥈 Top 25", callback_data="hot:top25"),
            ],
            [
                InlineKeyboardButton("🔄 刷新", callback_data="hot:refresh"),
                InlineKeyboardButton("◀️ 返回", callback_data="menu:hot"),
            ],
        ])
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    # ==================== 爆发项目处理 ====================
    
    async def _handle_exploding(self, query, parts: list):
        """处理爆发项目"""
        # 解析阈值 - 调高默认值
        threshold = 500  # 默认阈值提高到500
        if len(parts) > 1:
            try:
                threshold = int(parts[1])
            except ValueError:
                threshold = 500
        
        # 获取爆发项目 - 使用实时检测
        exploding_projects = self.trending.detect_exploding_realtime(threshold_stars_today=threshold)
        
        if not exploding_projects:
            await query.edit_message_text(
                "❌ 暂未发现符合条件的爆发项目\n\n"
                "可能是因为：\n"
                "• 近期没有项目达到 +500 stars 的增长\n"
                "• 网络问题无法获取数据",
                reply_markup=Menu.back_to_menu()
            )
            return
        
        # 限制项目数量，避免消息过长
        exploding_projects = exploding_projects[:5]
        
        # 格式化消息
        title = f"🚀 爆发项目 (日均 +{threshold} stars)"
        text = self._format_exploding_list(exploding_projects, title)
        
        # 为每个项目创建直达按钮
        keyboard = []
        for repo in exploding_projects:
            name = repo.get('full_name', 'Unknown').split('/')[-1]  # 只显示仓库名
            keyboard.append([
                InlineKeyboardButton(f"🚀 {name}", url=repo.get('url', ''))
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("🔍 +1000", callback_data="exploding:1000"),
                InlineKeyboardButton("🔍 +500", callback_data="exploding:500"),
            ],
            [
                InlineKeyboardButton("🔍 +300", callback_data="exploding:300"),
                InlineKeyboardButton("🔍 +100", callback_data="exploding:100"),
            ],
            [
                InlineKeyboardButton("◀️ 返回", callback_data="menu:exploding"),
            ],
        ])
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    def _format_exploding_list(self, projects: list, title: str) -> str:
        """格式化爆发项目列表"""
        if not projects:
            return "暂未发现爆发项目\n\n可能原因：\n• 近期没有项目达到阈值增长\n• GitHub API 请求限制"
        
        lines = [f"{title}\n", "=" * 35, ""]
        
        for i, repo in enumerate(projects, 1):
            name = repo.get('full_name', 'Unknown')
            daily_avg = repo.get('daily_avg', 0)
            stars = repo.get('stars', 0)
            language = repo.get('language', '')
            days_old = repo.get('days_old', 0)
            description = repo.get('description', '')[:60]
            
            lines.append(f"{i}. **{name}**")
            lines.append(f"   📈 日均 +{daily_avg} ⭐ | {stars:,} ⭐ | {language}")
            if description:
                lines.append(f"   📝 {description}...")
            lines.append("")
        
        return "\n".join(lines)
    
    # ==================== 追踪处理 ====================
    
    async def _handle_track(self, query, parts: list, context):
        """处理追踪"""
        chat_id = query.message.chat_id
        sub_action = parts[1] if len(parts) > 1 else None
        
        if not sub_action or sub_action == "list":
            # 显示追踪列表
            tracked = self.db.get_tracked_repos(chat_id)
            text = format_tracked_list(tracked)
            
            keyboard = [
                [
                    InlineKeyboardButton("➕ 添加追踪", callback_data="track:add"),
                    InlineKeyboardButton("🔥 最热追踪", callback_data="track:hot"),
                ],
                [
                    InlineKeyboardButton("◀️ 返回", callback_data="menu:track"),
                ],
            ]
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif sub_action == "add":
            # 提示用户输入
            context.user_data['awaiting'] = 'track_repo'
            await query.edit_message_text(
                "📈 **添加追踪项目**\n\n"
                "请回复要追踪的仓库（格式：owner/repo）\n\n"
                "例如：`cursor/cursor`",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        
        elif sub_action == "hot":
            # 显示最热的追踪
            tracked = self.db.get_hot_tracked_repos(limit=10)
            text = format_tracked_list(tracked)
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=Menu.track_menu()
            )
        
        elif sub_action == "refresh":
            # 刷新追踪数据
            chat_id = query.message.chat_id
            tracked = self.db.get_tracked_repos(chat_id)
            
            updated_count = 0
            for item in tracked:
                try:
                    from github import Github
                    g = Github()
                    r = g.get_repo(f"{item['owner']}/{item['repo']}")
                    self.db.update_tracked_repo(
                        chat_id, item['owner'], item['repo'],
                        r.stargazers_count
                    )
                    updated_count += 1
                except:
                    pass
            
            await query.edit_message_text(
                f"✅ 已更新 {updated_count} 个追踪项目的数据",
                reply_markup=Menu.track_menu()
            )
        
        else:
            # 添加单个追踪
            repo_path = '/'.join(parts[1:])
            
            try:
                from github import Github
                g = Github()
                r = g.get_repo(repo_path)
                
                self.db.track_trending_repo(
                    chat_id, r.owner.login, r.name,
                    r.name, r.description, r.stargazers_count
                )
                
                await query.edit_message_text(
                    f"✅ 已添加追踪：{repo_path}\n\n"
                    f"当前 Stars: {r.stargazers_count:,}",
                    parse_mode="Markdown",
                    reply_markup=Menu.tracked_repo_menu(r.owner.login, r.name, True)
                )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ 添加追踪失败: {str(e)}",
                    reply_markup=Menu.track_menu()
                )
    
    # ==================== Stars 图表处理 ====================
    
    async def _handle_stars_chart(self, query, parts: list):
        """处理 Stars 图表"""
        repo_path = ':'.join(parts[1:])
        
        try:
            owner, repo = repo_path.split('/')
        except:
            await query.edit_message_text("❌ 仓库格式错误")
            return
        
        history = self.trending.get_repo_stars_history(owner, repo, days=30)
        
        if not history:
            await query.edit_message_text(
                f"❌ 无法获取 {owner}/{repo} 的历史数据",
                reply_markup=Menu.back_to_menu()
            )
            return
        
        # 构建图表
        chart = self.trending_commands._build_stars_chart(history)
        
        total_growth = history[-1]['total_stars'] - history[0]['total_stars']
        avg_daily = sum(d['new_stars'] for d in history) / len(history)
        
        text = (
            f"📈 **{owner}/{repo}** Stars 历史 (30天)\n\n"
            f"```\n{chart}\n```\n\n"
            f"📈 总增长: **+{total_growth:,}**\n"
            f"📊 日均增长: **{avg_daily:.1f}**\n"
            f"⭐ 当前: **{history[-1]['total_stars']:,}**\n"
        )
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=Menu.tracked_repo_menu(owner, repo, self.db.is_repo_tracked(query.message.chat_id, owner, repo))
        )
    
    # ==================== 仓库操作处理 ====================
    
    async def _handle_watch(self, query, parts: list):
        """处理仓库详情"""
        if len(parts) < 2:
            return
        
        repo_path = '/'.join(parts[1:])
        
        try:
            owner, repo = repo_path.split('/')
        except:
            await query.edit_message_text("❌ 仓库格式错误")
            return
        
        chat_id = query.message.chat_id
        is_tracked = self.db.is_repo_tracked(chat_id, owner, repo)
        
        # 获取仓库信息
        info = self.monitor.get_repo_info(owner, repo)
        
        if not info:
            await query.edit_message_text(
                f"❌ 无法获取 {owner}/{repo} 的信息",
                reply_markup=Menu.back_to_menu()
            )
            return
        
        text = format_repo_card(info)
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=Menu.repo_quick_actions(owner, repo),
            disable_web_page_preview=True
        )
    
    async def _handle_repo_action(self, query, action: str, parts: list):
        """处理仓库相关操作"""
        if len(parts) < 2:
            return
        
        repo_path = '/'.join(parts[1:])
        
        try:
            owner, repo = repo_path.split('/')
        except:
            return
        
        # 复用现有的处理逻辑
        if action == "commits":
            commits = self.monitor.get_recent_commits(owner, repo, limit=5)
            if commits:
                text = f"📝 **{owner}/{repo}** 最近提交：\n\n"
                for c in commits:
                    text += f"• `{c.sha}` {c.message[:40]}...\n"
                    text += f"  👤 {c.author}\n\n"
            else:
                text = f"📭 暂无提交记录"
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=Menu.repo_quick_actions(owner, repo),
                disable_web_page_preview=True
            )
        
        elif action == "prs":
            prs = self.monitor.get_recent_prs(owner, repo, limit=5)
            if prs:
                text = f"🔀 **{owner}/{repo}** 最近 PR：\n\n"
                for pr in prs:
                    emoji = "✅" if pr.merged else ("❌" if pr.action.value == "closed" else "🆕")
                    text += f"{emoji} **#{pr.number}** {pr.title[:40]}...\n\n"
            else:
                text = f"📭 暂无 PR"
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=Menu.repo_quick_actions(owner, repo),
                disable_web_page_preview=True
            )
        
        elif action == "issues":
            issues = self.monitor.get_recent_issues(owner, repo, limit=5)
            if issues:
                text = f"🐛 **{owner}/{repo}** 最近 Issues：\n\n"
                for issue in issues:
                    emoji = "✅" if issue.action.value == "closed" else "🆕"
                    text += f"{emoji} **#{issue.number}** {issue.title[:40]}...\n\n"
            else:
                text = f"📭 暂无 Issues"
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=Menu.repo_quick_actions(owner, repo),
                disable_web_page_preview=True
            )
        
        elif action == "releases":
            releases = self.monitor.get_recent_releases(owner, repo, limit=5)
            if releases:
                text = f"🚀 **{owner}/{repo}** 最近 Releases：\n\n"
                for r in releases:
                    text += f"🏷️ **{r.tag_name}**\n"
                    text += f"   {r.name[:50]}\n\n"
            else:
                text = f"📭 暂无 Releases"
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=Menu.repo_quick_actions(owner, repo),
                disable_web_page_preview=True
            )
        
        elif action == "branches":
            branches = self.monitor.get_branches(owner, repo)
            default = self.monitor.get_default_branch(owner, repo)
            
            text = f"🌿 **{owner}/{repo}** 分支列表：\n\n"
            text += f"📌 默认分支: `{default}`\n\n"
            
            for b in branches[:10]:
                marker = "📌" if b == default else "  "
                text += f"{marker} `{b}`\n"
            
            if len(branches) > 10:
                text += f"\n... 还有 {len(branches) - 10} 个分支"
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=Menu.repo_quick_actions(owner, repo),
                disable_web_page_preview=True
            )
        
        elif action == "refresh":
            await self._handle_watch(query, ["watch", owner, repo])
    
    # ==================== 添加仓库 ====================
    
    async def _handle_add(self, query, parts: list, context):
        """处理添加仓库"""
        sub_action = parts[1] if len(parts) > 1 else None
        
        if sub_action == "prompt":
            context.user_data['awaiting'] = 'add_repo'
            await query.edit_message_text(
                "➕ **添加监控仓库**\n\n"
                "请回复要监控的仓库（格式：owner/repo）\n\n"
                "例如：`microsoft/vscode`",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        elif sub_action == "github":
            # 快速添加追踪的项目
            trending = self.trending.get_hot_projects(limit=10)
            keyboard = []
            for repo in trending[:5]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"➕ {repo.full_name}",
                        callback_data=f"add:{repo.full_name}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("◀️ 返回", callback_data="menu:add")])
            
            await query.edit_message_text(
                "➕ **从热门项目添加**\n\n"
                "选择一个热门项目添加监控：",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # 直接添加
            repo_path = '/'.join(parts[1:])
            chat_id = query.message.chat_id
            
            try:
                owner, repo = repo_path.split('/')
                
                # 验证仓库
                valid, _ = self.monitor.validate_repo(owner, repo)
                if not valid:
                    await query.edit_message_text(
                        f"❌ 仓库不存在：{owner}/{repo}",
                        reply_markup=Menu.repo_management_menu()
                    )
                    return
                
                # 添加
                self.db.add_repo(chat_id, owner, repo)
                
                await query.edit_message_text(
                    f"✅ 已添加监控：{owner}/{repo}",
                    reply_markup=Menu.repo_quick_actions(owner, repo)
                )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ 添加失败: {str(e)}",
                    reply_markup=Menu.repo_management_menu()
                )
    
    # ==================== 仓库列表 ====================
    
    async def _handle_list(self, query, parts: list):
        """处理仓库列表"""
        chat_id = query.message.chat_id
        repos = self.db.get_user_repos(chat_id)
        
        if not repos:
            await query.edit_message_text(
                "📭 您还没有添加任何监控的仓库\n\n"
                "点击下方按钮添加：",
                parse_mode="Markdown",
                reply_markup=Menu.repo_management_menu()
            )
            return
        
        # 转换为字典列表
        repos_dict = [
            {'owner': r.owner, 'repo': r.repo}
            for r in repos
        ]
        
        page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
        
        await query.edit_message_text(
            "📋 **监控的仓库列表**\n\n选择查看详情：",
            parse_mode="Markdown",
            reply_markup=Menu.repo_list_menu(repos_dict, page)
        )
    
    # ==================== 其他处理 ====================
    
    async def _handle_remove(self, query, parts: list, context):
        """处理移除仓库"""
        sub_action = parts[1] if len(parts) > 1 else None
        
        if sub_action == "prompt":
            chat_id = query.message.chat_id
            repos = self.db.get_user_repos(chat_id)
            
            if not repos:
                await query.edit_message_text(
                    "📭 您还没有监控任何仓库",
                    reply_markup=Menu.repo_management_menu()
                )
                return
            
            keyboard = []
            for r in repos[:10]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ {r.owner}/{r.repo}",
                        callback_data=f"remove_confirm:{r.owner}/{r.repo}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("◀️ 返回", callback_data="menu:add")])
            
            await query.edit_message_text(
                "🗑️ **移除仓库**\n\n选择要移除的仓库：",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif sub_action and sub_action.startswith("confirm:"):
            repo_path = sub_action.split(':', 1)[1]
            chat_id = query.message.chat_id
            
            try:
                owner, repo = repo_path.split('/')
                self.db.remove_repo(chat_id, owner, repo)
                
                await query.edit_message_text(
                    f"✅ 已移除：{owner}/{repo}",
                    reply_markup=Menu.repo_management_menu()
                )
            except:
                pass
    
    async def _handle_fork(self, query, parts: list, context):
        """处理 Fork"""
        sub_action = parts[1] if len(parts) > 1 else None
        
        if sub_action == "prompt":
            context.user_data['awaiting'] = 'fork_repo'
            await query.edit_message_text(
                "🍴 **Fork 仓库**\n\n"
                "请回复要 Fork 的仓库（格式：owner/repo）\n\n"
                "例如：`facebook/react`",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        elif sub_action == "search":
            context.user_data['awaiting'] = 'fork_search'
            await query.edit_message_text(
                "🔍 **搜索并 Fork**\n\n"
                "请回复要搜索的关键词：",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        else:
            repo_path = '/'.join(parts[1:])
            chat_id = query.message.chat_id
            
            if not self.db.is_github_bound(chat_id):
                await query.edit_message_text(
                    "⚠️ 需要先绑定 GitHub 账号！\n\n"
                    "点击下方按钮绑定：",
                    parse_mode="Markdown",
                    reply_markup=Menu.github_menu(False)
                )
                return
            
            # 执行 Fork
            try:
                owner, repo = repo_path.split('/')
                account = self.db.get_github_account(chat_id)
                
                if not account:
                    await query.edit_message_text(
                        "⚠️ 请先绑定 GitHub 账号",
                        reply_markup=Menu.github_menu(False)
                    )
                    return
                
                await query.edit_message_text(f"🍴 正在 Fork {owner}/{repo}...")
                
                from github_advanced import GitHubAdvanced
                client = GitHubAdvanced(account.access_token)
                result = client.fork_repository(owner, repo)
                
                if result.success:
                    self.db.add_fork_history(chat_id, owner, repo, result.full_name)
                    
                    await query.edit_message_text(
                        result.message,
                        parse_mode="Markdown",
                        reply_markup=Menu.fork_result_menu(owner, repo)
                    )
                else:
                    await query.edit_message_text(
                        result.message,
                        reply_markup=Menu.fork_menu()
                    )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Fork 失败: {str(e)}",
                    reply_markup=Menu.fork_menu()
                )
    
    async def _handle_pr(self, query, parts: list, context):
        """处理 PR"""
        sub_action = parts[1] if len(parts) > 1 else None
        
        if sub_action == "create" or sub_action == "create:prompt":
            context.user_data['awaiting'] = 'pr_create'
            await query.edit_message_text(
                "🔀 **创建 Pull Request**\n\n"
                "请回复 PR 信息（格式：owner/repo | 标题）\n\n"
                "例如：`owner/repo | 修复 bug`",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        elif sub_action == "quick":
            context.user_data['awaiting'] = 'pr_quick'
            await query.edit_message_text(
                "⚡ **快速创建 PR**\n\n"
                "格式：`owner/repo 标题 --head user:branch`\n\n"
                "示例：`owner/repo 修复bug --head me:fix-branch`",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        elif sub_action == "view":
            context.user_data['awaiting'] = 'pr_view'
            await query.edit_message_text(
                "🔍 **查看 PR**\n\n"
                "请回复 PR 信息（格式：owner/repo | PR号）\n\n"
                "例如：`microsoft/vscode | 123`",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        else:
            await query.edit_message_text(
                "🔀 **PR 操作**\n\n选择一个操作：",
                parse_mode="Markdown",
                reply_markup=Menu.pr_menu()
            )
    
    async def _handle_actions(self, query, parts: list, context):
        """处理 Actions"""
        sub_action = parts[1] if len(parts) > 1 else None
        
        if sub_action == "workflows" and len(parts) > 2:
            repo_path = parts[2]
            try:
                owner, repo = repo_path.split('/')
                account = self.db.get_github_account(query.message.chat_id)
                
                if not account:
                    await query.edit_message_text(
                        "⚠️ 需要绑定 GitHub 账号",
                        reply_markup=Menu.github_menu(False)
                    )
                    return
                
                from github_advanced import GitHubActions
                actions = GitHubActions(account.access_token)
                workflows = actions.get_workflows(owner, repo)
                
                if not workflows:
                    await query.edit_message_text(
                        f"📭 仓库 {owner}/{repo} 没有 Workflows",
                        reply_markup=Menu.actions_menu()
                    )
                    return
                
                text = f"⚡ **{owner}/{repo}** Workflows：\n\n"
                keyboard = []
                
                for wf in workflows[:10]:
                    text += f"⚡ **{wf.name}**\n"
                    text += f"   📄 {wf.path}\n"
                    text += f"   🏷️ 状态: {'🟢 活跃' if wf.state == 'active' else '🔴 未激活'}\n\n"
                    
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🚀 运行 {wf.name}",
                            callback_data=f"workflow:run:{owner}/{repo}:{wf.id}"
                        )
                    ])
                
                keyboard.append([InlineKeyboardButton("◀️ 返回", callback_data="menu:actions")])
                
                await query.edit_message_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True
                )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ 获取失败: {str(e)}",
                    reply_markup=Menu.actions_menu()
                )
        
        elif sub_action == "run" and len(parts) >= 3:
            repo_path = parts[2]
            workflow_id = parts[3] if len(parts) > 3 else None
            
            if workflow_id:
                try:
                    owner, repo = repo_path.split('/')
                    account = self.db.get_github_account(query.message.chat_id)
                    
                    if not account:
                        await query.edit_message_text(
                            "⚠️ 需要绑定 GitHub 账号",
                            reply_markup=Menu.github_menu(False)
                        )
                        return
                    
                    from github_advanced import GitHubActions
                    actions = GitHubActions(account.access_token)
                    
                    success, msg = actions.trigger_workflow(owner, repo, workflow_id)
                    
                    await query.edit_message_text(
                        msg,
                        parse_mode="Markdown",
                        reply_markup=Menu.actions_menu()
                    )
                except Exception as e:
                    await query.edit_message_text(
                        f"❌ 触发失败: {str(e)}",
                        reply_markup=Menu.actions_menu()
                    )
            else:
                context.user_data['awaiting'] = 'actions_run'
                await query.edit_message_text(
                    "🚀 **触发 Workflow**\n\n"
                    "请回复信息（格式：owner/repo | workflow名）\n\n"
                    "例如：`microsoft/vscode | CI`",
                    parse_mode="Markdown",
                    reply_markup=Menu.back_to_menu()
                )
        else:
            context.user_data['awaiting'] = 'actions_repo'
            await query.edit_message_text(
                "⚡ **GitHub Actions**\n\n"
                "请回复仓库（格式：owner/repo）\n\n"
                "例如：`microsoft/vscode`",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
    
    async def _handle_branch(self, query, parts: list, context):
        """处理分支"""
        context.user_data['awaiting'] = 'branch'
        await query.edit_message_text(
            "🌿 **分支操作**\n\n"
            "请回复分支信息（格式：owner/repo | 分支名 | 操作）\n\n"
            "操作：create (创建) / delete (删除)\n\n"
            "示例：`owner/repo | feature/new --create`",
            parse_mode="Markdown",
            reply_markup=Menu.back_to_menu()
        )
    
    async def _handle_github(self, query, parts: list):
        """处理 GitHub 账号"""
        chat_id = query.message.chat_id
        sub_action = parts[1] if len(parts) > 1 else None
        is_bound = self.db.is_github_bound(chat_id)
        
        if sub_action == "info" or sub_action is None:
            if is_bound:
                account = self.db.get_github_account(chat_id)
                
                from menu_system import format_user_profile
                text = format_user_profile({
                    'login': account.github_login,
                    'name': account.name,
                    'bio': account.bio,
                    'public_repos': account.public_repos,
                    'followers': account.followers,
                    'following': account.following
                })
                
                await query.edit_message_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=Menu.github_menu(True)
                )
            else:
                await query.edit_message_text(
                    "⚠️ **未绑定 GitHub 账号**\n\n"
                    "绑定后可使用 Fork、PR 等高级功能",
                    parse_mode="Markdown",
                    reply_markup=Menu.github_menu(False)
                )
        
        elif sub_action == "bind":
            context = None
            # 调用绑定命令
            if hasattr(self.ext_commands, 'bind_github'):
                # 创建一个假的 message 对象
                class FakeMessage:
                    def __init__(self, query):
                        self.chat = query.message.chat
                        self.reply_text = query.edit_text
                
                await self.ext_commands.bind_github(FakeMessage(query), None)
        
        elif sub_action == "unbind":
            self.db.unbind_github_account(chat_id)
            await query.edit_message_text(
                "✅ 已解绑 GitHub 账号",
                reply_markup=Menu.github_menu(False)
            )
    
    async def _handle_settings(self, query, parts: list, context):
        """处理设置"""
        chat_id = query.message.chat_id
        sub_action = parts[1] if len(parts) > 1 else None
        
        if sub_action == "notifications":
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
            
            await query.edit_message_text(
                "🔔 **通知设置**\n\n点击切换开关：",
                parse_mode="Markdown",
                reply_markup=Menu.notification_settings_menu(settings_dict)
            )
        
        elif sub_action == "toggle" and len(parts) > 2:
            key = parts[2]
            settings = self.db.get_user_settings(chat_id)
            
            if hasattr(settings, key):
                current = getattr(settings, key)
                setattr(settings, key, not current)
                self.db.save_user_settings(settings)
            
            # 重新显示
            settings_dict = {
                'notify_stars': settings.notify_stars,
                'notify_forks': settings.notify_forks,
                'notify_commits': settings.notify_commits,
                'notify_prs': settings.notify_prs,
                'notify_issues': settings.notify_issues,
                'notify_releases': settings.notify_releases,
                'notify_branches': settings.notify_branches,
            }
            
            await query.edit_message_text(
                "🔔 **通知设置**\n\n点击切换开关：",
                parse_mode="Markdown",
                reply_markup=Menu.notification_settings_menu(settings_dict)
            )
        
        elif sub_action == "interval":
            settings = self.db.get_user_settings(chat_id)
            await query.edit_message_text(
                f"⏱️ **检查间隔**\n\n"
                f"当前：{settings.check_interval} 分钟\n\n"
                f"可选：1-60 分钟\n\n"
                "回复数字设置：",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        
        elif sub_action == "stats":
            stats = self.db.get_user_total_stats(chat_id)
            
            text = (
                "📊 **监控统计**\n\n"
                f"📦 监控仓库：{stats.get('repo_count', 0)}\n"
                f"🍴 Fork 数量：{stats.get('fork_count', 0)}\n"
                f"📈 追踪项目：{stats.get('workflow_monitor_count', 0)}\n"
                f"📝 PR 草稿：{stats.get('pr_draft_count', 0)}\n"
                f"📝 活动记录：{stats.get('activity_count', 0)}"
            )
            
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=Menu.settings_menu()
            )
        
        else:
            await query.edit_message_text(
                "⚙️ **设置**\n\n选择一个设置项：",
                parse_mode="Markdown",
                reply_markup=Menu.settings_menu()
            )
    
    async def _handle_search(self, query, parts: list, context):
        """处理搜索"""
        sub_action = parts[1] if len(parts) > 1 else None
        
        if sub_action == "repos":
            context.user_data['awaiting'] = 'search_repos'
            await query.edit_message_text(
                "🔍 **搜索仓库**\n\n"
                "请回复搜索关键词：",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        elif sub_action == "users":
            context.user_data['awaiting'] = 'search_users'
            await query.edit_message_text(
                "🔍 **搜索用户**\n\n"
                "请回复用户名：",
                parse_mode="Markdown",
                reply_markup=Menu.back_to_menu()
            )
        else:
            await query.edit_message_text(
                "🔍 **搜索**\n\n选择一个搜索类型：",
                parse_mode="Markdown",
                reply_markup=Menu.search_menu()
            )
    
    async def _handle_help(self, query, parts: list):
        """处理帮助"""
        sub_action = parts[1] if len(parts) > 1 else None
        
        if sub_action == "commands":
            text = """
📖 **命令列表**

**🔥 Trending：**
`/trending`, `/hot`, `/exploding`

**📦 仓库：**
`/add`, `/list`, `/watch`

**⚡ 高级：**
`/fork`, `/pr`, `/run`, `/branch`

**📈 Stars：**
`/track`, `/stars`, `/similar`

发送 /help 查看所有命令
"""
        elif sub_action == "tips":
            text = """
💡 **使用技巧**

1️⃣ **快速操作**
点击按钮比输入命令更快！

2️⃣ **追踪热门**
使用 /exploding 发现爆火项目

3️⃣ **一键 Fork**
绑定 GitHub 后，一键 Fork 仓库

4️⃣ **Stars 追踪**
追踪项目增长，抢占先机

5️⃣ **自定义设置**
设置通知类型和检查间隔
"""
        else:
            text = """
📖 **帮助**

选择一个帮助主题：
"""
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=Menu.help_menu()
        )
    
    async def _handle_confirm(self, query, parts: list):
        """处理确认"""
        await query.edit_message_text(
            "✅ 操作已完成",
            reply_markup=Menu.back_to_menu()
        )
    
    async def _handle_cancel(self, query, parts: list):
        """处理取消"""
        await query.edit_message_text(
            "❌ 操作已取消",
            reply_markup=Menu.back_to_menu()
        )
    
    async def _handle_status(self, query, parts: list):
        """处理状态"""
        chat_id = query.message.chat_id
        stats = self.db.get_user_total_stats(chat_id)
        
        text = (
            "📊 **监控状态**\n\n"
            f"📦 监控仓库：{stats.get('repo_count', 0)}\n"
            f"📝 活动记录：{stats.get('activity_count', 0)}"
        )
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=Menu.settings_menu()
        )


# 导入扩展命令（避免循环导入）
from commands_extended import ExtendedCommandHandler
from commands_trending import TrendingCommands
