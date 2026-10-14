"""
GitHub Trending 和热门项目监控模块
"""

import re
import time
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from dataclasses import asdict

from github import Github, GithubException

from config import config


@dataclass
class TrendingRepo:
    """Trending 仓库"""
    rank: int
    owner: str
    repo: str
    full_name: str
    description: str
    language: str
    stars: int
    forks: int
    stars_today: int
    url: str
    avatar_url: str


@dataclass
class HotProject:
    """热门项目追踪"""
    project_id: str  # 格式: owner/repo
    name: str
    description: str
    initial_stars: int
    current_stars: int
    peak_stars_today: int  # 单日最高增长
    first_seen: str
    last_updated: str
    trend_score: float = 0.0  # 热度评分
    
    def calculate_growth(self) -> int:
        """计算增长"""
        return self.current_stars - self.initial_stars
    
    def calculate_growth_rate(self) -> float:
        """计算增长率"""
        if self.initial_stars == 0:
            return 0.0
        return (self.current_stars - self.initial_stars) / self.initial_stars * 100


@dataclass
class TrendingStats:
    """Trending 统计数据"""
    date: str
    total_repos: int
    total_stars: int
    top_language: str
    top_repo: TrendingRepo


class GitHubTrending:
    """GitHub Trending 监控类"""
    
    def __init__(self, token: str = None):
        self.token = token or config.GITHUB_TOKEN
        if self.token and self.token != "YOUR_GITHUB_TOKEN":
            from github import Auth
            self.github = Github(auth=Auth.Token(self.token))
        else:
            self.github = Github()
        self._cache = {}
        self._cache_timeout = 300  # 5分钟缓存
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_timeout:
                return data
        return None
    
    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        self._cache[key] = (data, time.time())
    
    def get_trending_repos(self, language: str = None, 
                           since: str = "daily") -> List[TrendingRepo]:
        """
        获取 GitHub Trending 仓库
        
        Args:
            language: 编程语言 (python, javascript, go, etc.)
            since: 时间范围 (daily, weekly, monthly)
        
        Returns:
            List[TrendingRepo]: Trending 仓库列表
        """
        cache_key = f"trending:{language or 'all'}:{since}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        repos = []
        
        try:
            # 使用更完整的请求头模拟真实浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            # 使用 GitHub Trending 页面抓取
            url = "https://github.com/trending"
            if language:
                url += f"/{language}"
            url += f"?since={since}"
            
            response = requests.get(url, headers=headers, timeout=15)
            
            # 检查是否返回了登录页面
            if 'sign_in' in response.text.lower() or '/login' in response.url:
                print("GitHub 需要登录，尝试使用 API")
                return self.get_trending_by_api(language, since)
            
            if response.status_code == 200:
                repos = self._parse_trending_html(response.text)
        except Exception as e:
            print(f"获取 Trending 失败: {e}")
        
        self._set_cache(cache_key, repos)
        return repos
    
    def _parse_trending_html(self, html: str) -> List[TrendingRepo]:
        """解析 Trending HTML"""
        repos = []
        
        # 使用正则表达式解析
        # 每个仓库在 article class="Box-row" 中
        repo_pattern = r'<h1[^>]*class="[^"]*h3[^"]*"[^>]*>.*?<a[^>]*href="/([^"]+)"[^>]*>([^<]+)</a>.*?</h1>(.*?)</p>'
        
        matches = re.findall(repo_pattern, html, re.DOTALL)
        
        for i, match in enumerate(matches, 1):
            owner_repo = match[0].strip('/')
            parts = owner_repo.split('/')
            
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1]
                
                # 解析描述和其他信息
                details_html = match[2]
                
                # 提取描述
                desc_match = re.search(r'<p[^>]*>([^<]+)</p>', details_html)
                description = desc_match.group(1).strip() if desc_match else ""
                
                # 提取语言
                lang_match = re.search(r'<span[^>]*itemprop="programmingLanguage"[^>]*>([^<]+)</span>', details_html)
                language = lang_match.group(1).strip() if lang_match else ""
                
                # 提取 stars
                stars_match = re.search(r'(\d+[\d,]*)\s*stars?', details_html)
                stars = int(stars_match.group(1).replace(',', '')) if stars_match else 0
                
                # 提取 forks
                forks_match = re.search(r'(\d+[\d,]*)\s*forks?', details_html)
                forks = int(forks_match.group(1).replace(',', '')) if forks_match else 0
                
                # 提取今日 stars
                today_match = re.search(r'(\d+[\d,]*)\s*stars\s*today', details_html)
                stars_today = int(today_match.group(1).replace(',', '')) if today_match else 0
                
                repos.append(TrendingRepo(
                    rank=i,
                    owner=owner,
                    repo=repo_name,
                    full_name=f"{owner}/{repo_name}",
                    description=description,
                    language=language,
                    stars=stars,
                    forks=forks,
                    stars_today=stars_today,
                    url=f"https://github.com/{owner}/{repo_name}",
                    avatar_url=f"https://github.com/{owner}.png"
                ))
        
        return repos
    
    def get_trending_by_api(self, language: str = None,
                           since: str = "daily") -> List[TrendingRepo]:
        """
        使用 GitHub API 获取 Trending
        通过搜索热门项目来模拟 Trending 行为
        """
        repos = []
        
        try:
            # 计算时间范围
            days = 1 if since == "daily" else (7 if since == "weekly" else 30)
            since_date = datetime.now() - timedelta(days=days)
            
            # 搜索最近推送的热门仓库
            if language:
                query = f"language:{language} pushed:>{since_date.strftime('%Y-%m-%d')}"
            else:
                query = f"pushed:>{since_date.strftime('%Y-%m-%d')}"
            
            results = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc"
            )
            
            rank = 0
            for repo in results[:30]:
                rank += 1
                
                # 估算今日增长（基于 stars 和 fork 数）
                stars = repo.stargazers_count
                forks = repo.forks_count
                
                # 使用热度评分公式估算 stars_today
                # 这是一个估算值，不是真实数据
                estimated_today = min(stars // 100, 1000)  # 简单估算
                
                repos.append(TrendingRepo(
                    rank=rank,
                    owner=repo.owner.login,
                    repo=repo.name,
                    full_name=repo.full_name,
                    description=repo.description or "无描述",
                    language=repo.language or "",
                    stars=stars,
                    forks=forks,
                    stars_today=estimated_today,
                    url=repo.html_url,
                    avatar_url=repo.owner.avatar_url
                ))
                
        except Exception as e:
            print(f"获取 Trending API 失败: {e}")
        
        return repos
    
    def get_repo_stars_history(self, owner: str, repo: str,
                               days: int = 30) -> List[Dict]:
        """
        获取仓库 Stars 增长历史
        """
        history = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            # 获取 star 历史（通过 events）
            events = repository.get_events()
            
            current_stars = repository.stargazers_count
            stars_per_day = {}
            
            # 统计每天的 stars
            for event in events[:300]:
                if event.type == "WatchEvent":
                    date_key = event.created_at.strftime("%Y-%m-%d")
                    if date_key not in stars_per_day:
                        stars_per_day[date_key] = 0
                    stars_per_day[date_key] += 1
            
            # 构建历史数据
            current = current_stars
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_stars = stars_per_day.get(date, 0)
                history.append({
                    'date': date,
                    'total_stars': current,
                    'new_stars': daily_stars
                })
                current -= daily_stars
            
            history.reverse()
            
        except Exception as e:
            print(f"获取 Stars 历史失败: {e}")
        
        return history
    
    def calculate_trend_score(self, stars: int, stars_today: int,
                             forks: int, age_days: int) -> float:
        """
        计算项目热度评分
        
        考虑因素：
        - 当前 Stars 数量
        - 今日 Stars 增长
        - Forks 数量
        - 项目年龄
        """
        if age_days <= 0:
            age_days = 1
        
        # 各因素权重
        current_weight = 0.1
        growth_weight = 5.0  # 增长权重更高
        fork_weight = 0.2
        recency_weight = 2.0  # 新项目权重
        
        # 计算评分
        score = (
            (stars * current_weight) +
            (stars_today * growth_weight) +
            (forks * fork_weight) +
            (stars / age_days * recency_weight)
        )
        
        return round(score, 2)
    
    def get_hot_projects(self, limit: int = 20,
                        min_stars: int = 100,
                        min_growth: int = 50) -> List[TrendingRepo]:
        """
        获取当前最热门的项目
        使用 API 获取真实数据
        """
        all_repos = []
        
        # 使用 API 获取最近活跃的仓库
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            query = f"pushed:>{yesterday}"
            results = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc"
            )
            
            rank = 0
            for repo in results.get_page(0)[:100]:
                rank += 1
                
                # 计算估算的日均增长
                if repo.created_at:
                    days_old = max(1, (datetime.now() - repo.created_at.replace(tzinfo=None)).days + 1)
                    daily_avg = repo.stargazers_count / days_old
                else:
                    daily_avg = 0
                
                all_repos.append(TrendingRepo(
                    rank=rank,
                    owner=repo.owner.login,
                    repo=repo.name,
                    full_name=repo.full_name,
                    description=repo.description or "",
                    language=repo.language or "",
                    stars=repo.stargazers_count,
                    forks=repo.forks_count,
                    stars_today=int(daily_avg * 0.5),  # 估算今日
                    url=repo.html_url,
                    avatar_url=repo.owner.avatar_url
                ))
        except Exception as e:
            print(f"API 获取热门项目失败: {e}")
        
        # 如果 API 失败，回退到 Trending 页面
        if not all_repos:
            languages = [None, "python", "javascript", "go", "rust", "typescript", "java"]
            for lang in languages:
                repos = self.get_trending_repos(language=lang, since="daily")
                all_repos.extend(repos)
        
        # 去重
        seen = set()
        unique_repos = []
        for repo in all_repos:
            if repo.full_name not in seen:
                seen.add(repo.full_name)
                unique_repos.append(repo)
        
        # 过滤
        filtered = [
            r for r in unique_repos
            if r.stars >= min_stars or r.stars_today >= min_growth
        ]
        
        # 按今日增长和总 stars 综合排序
        filtered.sort(key=lambda x: (x.stars_today * 10 + x.stars / 1000), reverse=True)
        
        return filtered[:limit]
    
    def detect_exploding_projects(self, threshold_stars_today: int = 500) -> List[TrendingRepo]:
        """
        检测爆发式增长的项目（如 REA 这样的项目）
        """
        repos = self.get_hot_projects(limit=50)
        
        # 筛选今日增长超过阈值或热度评分高的
        exploding = []
        
        for repo in repos:
            score = self.calculate_trend_score(
                repo.stars, repo.stars_today, repo.forks, 30
            )
            
            # 检测条件：今日增长超过阈值 或 热度评分超过 1000
            if repo.stars_today >= threshold_stars_today or score > 1000:
                exploding.append(repo)
        
        return exploding
    
    def detect_exploding_by_search(self, min_stars: int = 100, days: int = 7, limit: int = 20) -> List[TrendingRepo]:
        """
        使用 GitHub Search API 检测爆发项目
        搜索近期创建且快速增长的项目
        """
        exploding = []
        
        try:
            # 搜索最近7天创建且超过一定stars的项目
            query = f"created:>{days}days_ago stars:>{min_stars} pushed:>2020-01-01"
            
            repos = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc"
            )
            
            results = list(repos.get_page(0))[:limit]
            
            for repo in results:
                # 检查是否为较新项目（可能是爆发项目）
                created_date = repo.created_at
                pushed_date = repo.pushed_at
                
                # 计算距离创建以来的日均增长
                if created_date:
                    days_old = (datetime.now() - created_date.replace(tzinfo=None)).days + 1
                    if days_old <= days:
                        daily_avg = repo.stargazers_count / days_old
                        # 如果日均增长超过50，可能是爆发项目
                        if daily_avg >= 50:
                            exploding.append(TrendingRepo(
                                rank=len(exploding) + 1,
                                owner=repo.owner.login,
                                repo=repo.name,
                                full_name=repo.full_name,
                                description=repo.description or "",
                                language=repo.language or "",
                                stars=repo.stargazers_count,
                                forks=repo.forks_count,
                                stars_today=int(daily_avg),
                                url=repo.html_url,
                                avatar_url=repo.owner.avatar_url
                            ))
        except Exception as e:
            print(f"Search API 检测爆发项目失败: {e}")
        
        return exploding
    
    def detect_exploding_realtime(self, threshold_stars_today: int = 500) -> List[Dict]:
        """
        实时检测真正的爆发项目
        通过分析 GitHub API 数据，找出近期快速增长的热门项目
        """
        all_exploding = []
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        try:
            # 搜索最近24小时有推送的高星仓库
            query = f"pushed:>{yesterday}"
            results = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc"
            )
            
            for repo in results.get_page(0)[:100]:
                # 计算项目年龄和日均增长
                if repo.created_at:
                    days_old = max(1, (datetime.now() - repo.created_at.replace(tzinfo=None)).days + 1)
                    daily_avg = repo.stargazers_count / days_old
                    
                    # 新项目（90天内创建）且日均增长较高
                    # 或者虽然老项目但最近特别活跃
                    if daily_avg >= threshold_stars_today / 10:
                        # 估算今日增长（取日均的一半作为今日估算）
                        est_today = int(daily_avg * 0.5)
                        
                        all_exploding.append({
                            'full_name': repo.full_name,
                            'description': repo.description or '',
                            'language': repo.language or '',
                            'stars': repo.stargazers_count,
                            'stars_today': est_today,
                            'forks': repo.forks_count,
                            'url': repo.html_url,
                            'days_old': days_old,
                            'daily_avg': int(daily_avg),
                            'growth_indicator': '🔴' if daily_avg >= 100 else ('🟠' if daily_avg >= 50 else '🟡')
                        })
                        
        except Exception as e:
            print(f"API 检测失败: {e}")
        
        # 备用：尝试获取 Trending 页面数据
        if len(all_exploding) < 3:
            try:
                repos = self.get_trending_repos(since="daily")
                for repo in repos:
                    if repo.stars_today >= 50:
                        all_exploding.append({
                            'full_name': repo.full_name,
                            'description': repo.description,
                            'language': repo.language,
                            'stars': repo.stars,
                            'stars_today': repo.stars_today,
                            'forks': repo.forks,
                            'url': repo.url,
                            'days_old': 0,
                            'daily_avg': repo.stars_today,
                            'growth_indicator': '🔴' if repo.stars_today >= 1000 else ('🟠' if repo.stars_today >= 500 else '🟡')
                        })
            except Exception as e:
                print(f"Trending 检测失败: {e}")
        
        # 按 daily_avg 排序
        all_exploding.sort(key=lambda x: x['daily_avg'], reverse=True)
        
        # 去重
        seen = set()
        unique = []
        for repo in all_exploding:
            if repo['full_name'] not in seen:
                seen.add(repo['full_name'])
                unique.append(repo)
        
        return unique[:20]
    
    def search_similar_projects(self, repo_owner: str, repo_name: str,
                               limit: int = 10) -> List[Dict]:
        """
        搜索类似项目
        """
        similar = []
        
        try:
            repository = self.github.get_repo(f"{repo_owner}/{repo_name}")
            
            # 获取仓库主题/语言
            language = repository.language or ""
            topics = repository.get_topics() if hasattr(repository, 'get_topics') else []
            
            # 搜索类似项目
            query_parts = []
            
            if language:
                query_parts.append(f"language:{language}")
            
            for topic in topics[:3]:
                query_parts.append(f"topic:{topic}")
            
            query = " ".join(query_parts)
            
            if query:
                results = self.github.search_repositories(
                    query=query,
                    sort="stars",
                    order="desc"
                )
                
                for repo in results[:limit + 1]:
                    if repo.full_name.lower() != f"{repo_owner}/{repo_name}".lower():
                        similar.append({
                            'full_name': repo.full_name,
                            'description': repo.description,
                            'stars': repo.stargazers_count,
                            'language': repo.language,
                            'url': repo.html_url
                        })
                        
        except Exception as e:
            print(f"搜索类似项目失败: {e}")
        
        return similar
    
    def get_trending_stats(self, language: str = None) -> TrendingStats:
        """获取 Trending 统计信息"""
        repos = self.get_trending_repos(language=language)
        
        if not repos:
            return None
        
        # 计算统计
        total_stars = sum(r.stars for r in repos)
        
        # 统计语言
        languages = {}
        for r in repos:
            if r.language:
                languages[r.language] = languages.get(r.language, 0) + 1
        
        top_language = max(languages, key=languages.get) if languages else "Unknown"
        
        return TrendingStats(
            date=datetime.now().strftime("%Y-%m-%d"),
            total_repos=len(repos),
            total_stars=total_stars,
            top_language=top_language,
            top_repo=repos[0]
        )


class HotProjectTracker:
    """
    热门项目追踪器
    记录项目从发现到现在的增长情况
    """
    
    def __init__(self, db):
        self.db = db
    
    def track_project(self, owner: str, repo: str,
                     current_stars: int, description: str = "") -> HotProject:
        """开始追踪一个项目"""
        project_id = f"{owner}/{repo}"
        now = datetime.utcnow().isoformat()
        
        project = HotProject(
            project_id=project_id,
            name=repo,
            description=description,
            initial_stars=current_stars,
            current_stars=current_stars,
            peak_stars_today=0,
            first_seen=now,
            last_updated=now
        )
        
        # 保存到数据库
        self._save_project(project)
        
        return project
    
    def update_project(self, owner: str, repo: str,
                      current_stars: int, stars_today: int = 0) -> HotProject:
        """更新项目数据"""
        project_id = f"{owner}/{repo}"
        project = self._get_project(project_id)
        
        if not project:
            return self.track_project(owner, repo, current_stars)
        
        now = datetime.utcnow().isoformat()
        
        # 计算今日增长
        if stars_today > project.peak_stars_today:
            project.peak_stars_today = stars_today
        
        # 更新数据
        project.current_stars = current_stars
        project.last_updated = now
        
        # 计算趋势评分
        days_since_first = (datetime.now() - datetime.fromisoformat(project.first_seen)).days
        project.trend_score = (
            project.calculate_growth() * 5 +
            project.peak_stars_today * 10 -
            days_since_first * 10
        )
        
        self._save_project(project)
        
        return project
    
    def get_tracked_projects(self, chat_id: int = None) -> List[HotProject]:
        """获取追踪的项目列表"""
        # 这里应该从数据库读取
        # 暂时返回内存中的数据
        return []
    
    def get_project_summary(self, owner: str, repo: str,
                          initial_stars: int, current_stars: int) -> str:
        """生成项目增长摘要"""
        growth = current_stars - initial_stars
        growth_rate = (growth / initial_stars * 100) if initial_stars > 0 else 0
        
        lines = [
            f"📊 **{owner}/{repo}** 增长报告\n",
            f"起始 Stars: **{initial_stars:,}**",
            f"当前 Stars: **{current_stars:,}**",
            f"📈 增长: **+{growth:,}** ({growth_rate:.1f}%)\n"
        ]
        
        if growth > 0:
            lines.append(f"🔥 这个项目正在增长！")
        
            if growth > 10000:
                lines.append("🚀 增长势头强劲！")
            elif growth > 1000:
                lines.append("⭐ 非常受欢迎！")
        
        return "\n".join(lines)
    
    def _get_project(self, project_id: str) -> Optional[HotProject]:
        """从数据库获取项目"""
        # TODO: 实现数据库读取
        return None
    
    def _save_project(self, project: HotProject):
        """保存项目到数据库"""
        # TODO: 实现数据库保存
        pass
