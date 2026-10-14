"""
Trending 和热门项目命令处理器
"""

import re
from typing import Optional, Tuple, List, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from github_trending import GitHubTrending, TrendingRepo, HotProjectTracker


class TrendingCommands:
    """Trending 相关命令处理器"""
    
    # 支持的编程语言
    LANGUAGES = {
        'python': 'Python',
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'go': 'Go',
        'rust': 'Rust',
        'java': 'Java',
        'c++': 'C++',
        'c#': 'C#',
        'ruby': 'Ruby',
        'php': 'PHP',
        'swift': 'Swift',
        'kotlin': 'Kotlin',
        'dart': 'Dart',
        'all': '全部'
    }
    
    # 时间范围
    TIME_RANGES = {
        'daily': '今日',
        'weekly': '本周',
        'monthly': '本月'
    }
    
    def __init__(self, db, token: str = None):
        self.db = db
        self.trending = GitHubTrending(token)
        self.tracker = HotProjectTracker(db)
    
    async def trending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /trending 命令 - 查看 Trending"""
        # 解析参数
        language = None
        since = "daily"
        
        if context.args:
            args = context.args
            
            # 检查是否是语言
            for lang in self.LANGUAGES.keys():
                if lang in args:
                    language = lang if lang != 'all' else None
                    args.remove(lang)
                    break
            
            # 检查是否是时间范围
            for time_range in self.TIME_RANGES.keys():
                if time_range in args:
                    since = time_range
                    args.remove(time_range)
                    break
        
        msg = await update.message.reply_text("📥 正在获取 Trending...")
        
        repos = self.trending.get_trending_repos(language=language, since=since)
        
        if not repos:
            repos = self.trending.get_trending_by_api(language=language, since=since)
        
        if not repos:
            await msg.edit_text("❌ 无法获取 Trending 数据，请稍后重试")
            return
        
        # 构建消息
        lang_text = self.LANGUAGES.get(language, '全部') if language else '全部'
        time_text = self.TIME_RANGES.get(since, '今日')
        
        trending_msg = f"🔥 **GitHub Trending** ({lang_text} - {time_text})\n\n"
        
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
            
            trending_msg += f"{indicator} **{repo.full_name}**\n"
            trending_msg += f"   📝 {repo.description[:60]}..." if len(repo.description) > 60 else f"   📝 {repo.description}\n"
            trending_msg += f"   ⭐ {repo.stars:,} | 🍴 {repo.forks:,}"
            if repo.stars_today > 0:
                trending_msg += f" | 📈 +{repo.stars_today:,} 今天"
            trending_msg += "\n\n"
        
        # 添加键盘
        keyboard = self._build_trending_keyboard(language, since)
        
        await msg.edit_text(
            trending_msg,
            parse_mode="Markdown",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    
    async def hot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /hot 命令 - 查看热门项目"""
        msg = await update.message.reply_text("🔥 正在分析热门项目...")
        
        # 获取热门项目
        hot_projects = self.trending.get_hot_projects(limit=20)
        
        if not hot_projects:
            await msg.edit_text("❌ 无法获取热门项目数据")
            return
        
        hot_msg = "🔥 **今日最热项目**\n\n"
        hot_msg += "_按热度综合评分排序_\n\n"
        
        for i, repo in enumerate(hot_projects[:10], 1):
            # 热度指示器
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            hot_msg += f"{medal} **{repo.full_name}**\n"
            hot_msg += f"   📝 {repo.description[:50]}..." if len(repo.description) > 50 else f"   📝 {repo.description}\n"
            
            if repo.language:
                hot_msg += f"   💻 {repo.language} | "
            hot_msg += f"⭐ {repo.stars:,} | 📈 +{repo.stars_today:,} 今天\n"
            
            # 计算并显示热度评分
            score = self.trending.calculate_trend_score(repo.stars, repo.stars_today, repo.forks, 30)
            hot_msg += f"   🔥 热度: {score:,.0f}\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 刷新", callback_data="trending:hot:refresh"),
                InlineKeyboardButton("➕ 追踪项目", callback_data="trending:hot:track")
            ],
            [
                InlineKeyboardButton("🔍 搜索类似", callback_data=f"trending:hot:similar:{hot_projects[0].full_name}")
            ]
        ]
        
        await msg.edit_text(
            hot_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def exploding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /exploding 命令 - 查看爆发式增长项目"""
        threshold = 500  # 默认阈值
        
        if context.args:
            try:
                threshold = int(context.args[0])
            except ValueError:
                pass
        
        msg = await update.message.reply_text("🚀 正在检测爆发项目...")
        
        # 检测爆发项目
        exploding = self.trending.detect_exploding_projects(threshold_stars_today=threshold)
        
        if not exploding:
            await msg.edit_text(
                f"❌ 当前没有发现增长超过 {threshold} Stars 的项目\n\n"
                "这些项目可能还没被发现，继续关注！",
                parse_mode="Markdown"
            )
            return
        
        exploding_msg = "🚀 **爆发式增长项目**\n\n"
        exploding_msg += f"_今日 Stars 增长超过 {threshold} 的项目_\n\n"
        
        for repo in exploding[:10]:
            exploding_msg += f"🔥 **{repo.full_name}**\n"
            exploding_msg += f"   📝 {repo.description[:60]}\n"
            exploding_msg += f"   ⭐ 总计: **{repo.stars:,}** Stars\n"
            exploding_msg += f"   📈 今日: **+{repo.stars_today:,}** 🚀\n"
            
            if repo.language:
                exploding_msg += f"   💻 {repo.language}\n"
            exploding_msg += f"   🔗 [查看]({repo.url})\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🍴 Fork", callback_data=f"fork:{exploding[0].full_name}"),
                InlineKeyboardButton("➕ 追踪", callback_data=f"track:{exploding[0].full_name}")
            ],
            [
                InlineKeyboardButton("🔄 再看一次", callback_data="trending:exploding:refresh")
            ]
        ]
        
        await msg.edit_text(
            exploding_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def track(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /track 命令 - 追踪项目"""
        if not context.args:
            await update.message.reply_text(
                "📊 **追踪项目 Stars**\n\n"
                "请使用：`/track owner/repo`\n\n"
                "例如：\n"
                "`/track cursor/cursor`\n"
                "`/trackmicrosoft/TypeScript`",
                parse_mode="Markdown"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        chat_id = update.effective_chat.id
        
        msg = await update.message.reply_text(f"📊 正在获取 {owner}/{repo} 数据...")
        
        try:
            from github import Github
            g = Github()
            r = g.get_repo(f"{owner}/{repo}")
            
            current_stars = r.stargazers_count
            
            # 开始追踪
            project = self.tracker.track_project(owner, repo, current_stars, r.description)
            
            # 构建追踪报告
            summary = self.tracker.get_project_summary(owner, repo, current_stars, current_stars)
            
            report = f"""
✅ **项目已加入追踪**

📦 **{owner}/{repo}**

📝 {r.description or '无描述'}

{summary}

💡 我会持续监控这个项目的 Stars 变化！
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 查看详情", callback_data=f"stats:{owner}/{repo}"),
                    InlineKeyboardButton("🔗 打开项目", url=r.html_url)
                ],
                [
                    InlineKeyboardButton("🗑️ 停止追踪", callback_data=f"untrack:{owner}/{repo}")
                ]
            ]
            
            await msg.edit_text(
                report,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            
        except Exception as e:
            await msg.edit_text(f"❌ 获取项目失败: {str(e)}")
    
    async def stars_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /stars 命令 - 查看 Stars 历史"""
        if not context.args:
            await update.message.reply_text(
                "📈 **查看项目 Stars 历史**\n\n"
                "请使用：`/stars owner/repo`\n\n"
                "例如：`/stars torvalds/linux`",
                parse_mode="Markdown"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        msg = await update.message.reply_text(f"📈 正在获取 {owner}/{repo} 的 Stars 历史...")
        
        history = self.trending.get_repo_stars_history(owner, repo, days=30)
        
        if not history:
            await msg.edit_text(f"❌ 无法获取 {owner}/{repo} 的历史数据")
            return
        
        # 构建 ASCII 图表
        chart = self._build_stars_chart(history)
        
        # 统计
        total_growth = history[-1]['total_stars'] - history[0]['total_stars']
        avg_daily = sum(d['new_stars'] for d in history) / len(history)
        
        history_msg = f"📈 **{owner}/{repo}** Stars 历史 (最近 30 天)\n\n"
        history_msg += f"📊 图表：\n```\n{chart}\n```\n"
        history_msg += f"\n📈 总增长: **+{total_growth:,}**\n"
        history_msg += f"📊 日均增长: **{avg_daily:.1f}**\n"
        history_msg += f"⭐ 当前 Stars: **{history[-1]['total_stars']:,}**\n"
        
        await msg.edit_text(
            history_msg,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    
    async def similar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /similar 命令 - 搜索类似项目"""
        if not context.args:
            await update.message.reply_text(
                "🔍 **搜索类似项目**\n\n"
                "请使用：`/similar owner/repo`\n\n"
                "例如：`/similar cursor/cursor`\n"
                "查找类似 Cursor 的项目",
                parse_mode="Markdown"
            )
            return
        
        repo_input = context.args[0]
        parsed = self._parse_repo(repo_input)
        
        if not parsed:
            await update.message.reply_text("❌ 仓库格式错误！")
            return
        
        owner, repo = parsed
        
        msg = await update.message.reply_text(f"🔍 正在搜索类似 {owner}/{repo} 的项目...")
        
        similar = self.trending.search_similar_projects(owner, repo, limit=10)
        
        if not similar:
            await msg.edit_text(f"❌ 未找到类似 {owner}/{repo} 的项目")
            return
        
        similar_msg = f"🔍 **类似 {owner}/{repo} 的项目**\n\n"
        
        for i, proj in enumerate(similar[:8], 1):
            similar_msg += f"**{i}. {proj['full_name']}**\n"
            similar_msg += f"   📝 {proj['description'][:50]}...\n"
            similar_msg += f"   ⭐ {proj['stars']:,}"
            if proj.get('language'):
                similar_msg += f" | 💻 {proj['language']}"
            similar_msg += "\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ 添加监控", callback_data=f"add:{similar[0]['full_name']}"),
                InlineKeyboardButton("🍴 Fork", callback_data=f"fork:{similar[0]['full_name']}")
            ]
        ]
        
        await msg.edit_text(
            similar_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def rank(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /rank 命令 - 语言排行榜"""
        if context.args and context.args[0] in self.LANGUAGES:
            language = context.args[0] if context.args[0] != 'all' else None
        else:
            language = None
        
        msg = await update.message.reply_text("🏆 正在获取语言排行榜...")
        
        repos = self.trending.get_trending_repos(language=language)
        
        if not repos:
            await msg.edit_text("❌ 无法获取排行榜数据")
            return
        
        # 按 Stars 排序
        repos.sort(key=lambda x: x.stars, reverse=True)
        
        lang_text = self.LANGUAGES.get(language, '全部') if language else '所有语言'
        rank_msg = f"🏆 **GitHub Stars 排行榜** ({lang_text})\n\n"
        
        for i, repo in enumerate(repos[:15], 1):
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"**{i}.**"
            
            rank_msg += f"{medal} **{repo.full_name}**\n"
            rank_msg += f"   ⭐ **{repo.stars:,}** Stars"
            if repo.stars_today > 0:
                rank_msg += f" | 📈 +{repo.stars_today} 今天"
            rank_msg += "\n\n"
        
        # 语言选择键盘
        keyboard = self._build_language_keyboard()
        
        await msg.edit_text(
            rank_msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    # ==================== 辅助方法 ====================
    
    def _parse_repo(self, text: str) -> Optional[Tuple[str, str]]:
        """解析仓库名"""
        text = text.strip().strip('/')
        
        # 支持多种格式
        patterns = [
            r'^([^/]+)/([^/]+)$',
            r'^https?://github\.com/([^/]+)/([^/]+)/?$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                return match.group(1), match.group(2)
        
        return None
    
    def _build_trending_keyboard(self, language: str, since: str) -> InlineKeyboardMarkup:
        """构建 Trending 键盘"""
        keyboard = []
        
        # 语言行
        lang_row = []
        for lang in ['python', 'javascript', 'go', 'rust', 'all']:
            label = self.LANGUAGES.get(lang, lang)
            if (language == lang) or (language is None and lang == 'all'):
                label = f"✅ {label}"
            lang_row.append(InlineKeyboardButton(label, callback_data=f"trending:lang:{lang}"))
        
        keyboard.append(lang_row)
        
        # 时间范围行
        time_row = []
        for t in ['daily', 'weekly', 'monthly']:
            label = self.TIME_RANGES.get(t, t)
            if since == t:
                label = f"✅ {label}"
            time_row.append(InlineKeyboardButton(label, callback_data=f"trending:time:{t}"))
        
        keyboard.append(time_row)
        
        # 操作行
        keyboard.append([
            InlineKeyboardButton("🔥 热门项目", callback_data="trending:hot"),
            InlineKeyboardButton("🚀 爆发项目", callback_data="trending:exploding")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def _build_language_keyboard(self) -> InlineKeyboardMarkup:
        """构建语言选择键盘"""
        keyboard = []
        
        row = []
        for i, lang in enumerate(['python', 'javascript', 'go', 'rust', 'java']):
            row.append(InlineKeyboardButton(
                self.LANGUAGES.get(lang, lang),
                callback_data=f"rank:lang:{lang}"
            ))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🌐 所有语言", callback_data="rank:lang:all")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def _build_stars_chart(self, history: List[Dict], width: int = 30, height: int = 10) -> str:
        """构建 ASCII Stars 图表"""
        if not history:
            return ""
        
        # 归一化数据
        values = [d['total_stars'] for d in history]
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return "=" * width
        
        # 缩放
        scale = (max_val - min_val) / height if height > 0 else 1
        
        lines = []
        for i in range(height, -1, -1):
            threshold = min_val + i * scale
            line = ""
            for val in values[-width:]:
                if val >= threshold:
                    line += "█"
                else:
                    line += " "
            lines.append(line)
        
        return "\n".join(lines)
