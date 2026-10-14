"""
GitHub 监控核心模块
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable, Set
from dataclasses import asdict

from github import Github, GithubException
from github.GithubObject import NotSet

from config import config
from models import (
    EventType, PRAction, IssueAction, GitHubEvent, RepoStats,
    CommitInfo, PREvent, IssueEvent, ReleaseEvent, BranchEvent
)


class GitHubMonitor:
    """GitHub 仓库监控类"""
    
    def __init__(self, token: str = None):
        self.token = token or config.GITHUB_TOKEN
        if self.token and self.token != "YOUR_GITHUB_TOKEN":
            from github import Auth
            self.github = Github(auth=Auth.Token(self.token))
        else:
            self.github = Github()
        self._cache: Dict[str, Dict] = {}  # 简单的缓存
        self._cache_timeout = 60  # 缓存超时（秒）
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_timeout:
                return data
        return None
    
    def _set_cache(self, key: str, data: Any):
        """设置缓存数据"""
        self._cache[key] = (data, time.time())
    
    def _clear_cache(self, repo_full_name: str = None):
        """清除缓存"""
        if repo_full_name:
            keys_to_remove = [k for k in self._cache if k.startswith(repo_full_name)]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()
    
    def validate_repo(self, owner: str, repo: str) -> tuple[bool, str]:
        """验证仓库是否存在"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            return True, f"✅ 仓库存在: {repository.full_name}"
        except GithubException as e:
            if e.status == 404:
                return False, f"❌ 仓库不存在: {owner}/{repo}"
            elif e.status == 403:
                return False, f"⛔ 访问被拒绝，可能需要 GitHub Token"
            else:
                return False, f"❌ GitHub API 错误: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 验证失败: {str(e)}"
    
    def get_repo_stats(self, owner: str, repo: str) -> Optional[RepoStats]:
        """获取仓库统计信息"""
        cache_key = f"{owner}/{repo}/stats"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            stats = RepoStats(
                owner=owner,
                name=repo,
                full_name=repository.full_name,
                description=repository.description,
                stars=repository.stargazers_count,
                forks=repository.forks_count,
                open_issues=repository.open_issues_count,
                watchers=repository.watchers_count,
                language=repository.language,
                created_at=repository.created_at,
                updated_at=repository.updated_at,
                pushed_at=repository.pushed_at,
                homepage=repository.homepage,
                topics=repository.get_topics() if hasattr(repository, 'get_topics') else [],
                license=repository.license.name if repository.license else None
            )
            
            self._set_cache(cache_key, stats)
            return stats
            
        except GithubException as e:
            print(f"获取仓库统计失败: {e}")
            return None
        except Exception as e:
            print(f"获取仓库统计异常: {e}")
            return None
    
    def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取仓库详细信息（用于展示）"""
        stats = self.get_repo_stats(owner, repo)
        if not stats:
            return {}
        
        info = {
            "full_name": stats.full_name,
            "description": stats.description or "无描述",
            "stars": stats.stars,
            "forks": stats.forks,
            "watchers": stats.watchers,
            "open_issues": stats.open_issues,
            "language": stats.language or "未知",
            "license": stats.license or "无",
            "created_at": stats.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": stats.updated_at.strftime("%Y-%m-%d %H:%M"),
            "pushed_at": stats.pushed_at.strftime("%Y-%m-%d %H:%M"),
            "homepage": stats.homepage,
            "topics": stats.topics,
            "url": f"https://github.com/{owner}/{repo}"
        }
        
        return info
    
    def get_events(self, owner: str, repo: str, 
                   limit: int = 30, since: datetime = None) -> List[GitHubEvent]:
        """获取仓库事件"""
        events = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            for event in repository.get_events()[:limit]:
                if since and event.created_at <= since:
                    continue
                
                github_event = self._parse_event(event, owner, repo)
                if github_event:
                    events.append(github_event)
                    
        except GithubException as e:
            print(f"获取事件失败: {e}")
        except Exception as e:
            print(f"获取事件异常: {e}")
        
        return events
    
    def _parse_event(self, event, owner: str, repo: str) -> Optional[GitHubEvent]:
        """解析 GitHub 事件"""
        event_type = event.type
        actor = event.actor.login if event.actor else "unknown"
        created_at = event.created_at
        event_id = str(event.id)
        
        payload = event.raw_data.get('payload', {})
        
        # 根据事件类型生成消息
        message = ""
        url = f"https://github.com/{owner}/{repo}"
        details = {}
        
        if event_type == "WatchEvent":
            # Star 事件
            if payload.get('action') == 'started':
                message = f"⭐ 获得新 star！"
                event_type_enum = EventType.STAR
            else:
                return None
        
        elif event_type == "ForkEvent":
            # Fork 事件
            forkee = payload.get('forkee', {})
            details['forker'] = forkee.get('login', 'unknown')
            message = f"🍴 被 {details['forker']} fork 了"
            url = forkee.get('html_url', url)
            event_type_enum = EventType.FORK
        
        elif event_type == "PushEvent":
            # 提交事件
            commits = payload.get('commits', [])
            ref = payload.get('ref', '')
            branch = ref.replace('refs/heads/', '') if ref else 'unknown'
            details['branch'] = branch
            details['commits_count'] = len(commits)
            details['commits'] = [
                {
                    'sha': c.get('sha', '')[:7],
                    'message': c.get('message', '').split('\n')[0]
                }
                for c in commits[:3]  # 最多3条
            ]
            message = f"📝 推送了 {len(commits)} 个提交到 **{branch}**"
            if commits:
                latest = commits[0]
                message += f"\n• `{latest.get('sha', '')[:7]}` {latest.get('message', '').split(chr(10))[0][:50]}"
            event_type_enum = EventType.COMMIT
        
        elif event_type == "PullRequestEvent":
            # PR 事件
            pr = payload.get('pull_request', {})
            action = payload.get('action', '')
            details['pr_number'] = pr.get('number')
            details['pr_title'] = pr.get('title', '')
            details['merged'] = pr.get('merged', False)
            
            if action == 'opened':
                message = f"🔀 打开了新 PR: #{pr.get('number')} {pr.get('title', '')[:50]}"
                action_enum = PRAction.OPENED
            elif action == 'closed' and pr.get('merged'):
                message = f"🔀 合并了 PR: #{pr.get('number')} {pr.get('title', '')[:50]}"
                action_enum = PRAction.MERGED
            elif action == 'closed':
                message = f"🔀 关闭了 PR: #{pr.get('number')} {pr.get('title', '')[:50]}"
                action_enum = PRAction.CLOSED
            elif action == 'reopened':
                message = f"🔀 重新打开了 PR: #{pr.get('number')} {pr.get('title', '')[:50]}"
                action_enum = PRAction.REOPENED
            else:
                message = f"🔀 PR 更新: #{pr.get('number')} {pr.get('title', '')[:50]}"
                action_enum = PRAction.OPENED
            
            url = pr.get('html_url', url)
            event_type_enum = EventType.PULL_REQUEST
        
        elif event_type == "IssuesEvent":
            # Issue 事件
            issue = payload.get('issue', {})
            action = payload.get('action', '')
            details['issue_number'] = issue.get('number')
            details['issue_title'] = issue.get('title', '')
            details['labels'] = [l.get('name') for l in issue.get('labels', [])]
            
            if action == 'opened':
                message = f"🐛 创建了 Issue: #{issue.get('number')} {issue.get('title', '')[:50]}"
                action_enum = IssueAction.OPENED
            elif action == 'closed':
                message = f"🐛 关闭了 Issue: #{issue.get('number')} {issue.get('title', '')[:50]}"
                action_enum = IssueAction.CLOSED
            elif action == 'reopened':
                message = f"🐛 重新打开了 Issue: #{issue.get('number')} {issue.get('title', '')[:50]}"
                action_enum = IssueAction.REOPENED
            else:
                return None  # 忽略其他 action
            
            url = issue.get('html_url', url)
            event_type_enum = EventType.ISSUE
        
        elif event_type == "ReleaseEvent":
            # Release 事件
            release = payload.get('release', {})
            action = payload.get('action', 'published')
            details['tag_name'] = release.get('tag_name', '')
            details['release_name'] = release.get('name', release.get('tag_name', ''))
            details['is_prerelease'] = release.get('prerelease', False)
            
            if action == 'published':
                message = f"🚀 发布了新版本: **{release.get('tag_name', '')}**"
                if release.get('name'):
                    message += f"\n{release.get('name', '')[:50]}"
            elif action == 'created':
                message = f"🚀 创建了预发布版本: **{release.get('tag_name', '')}**"
            else:
                return None
            
            url = release.get('html_url', url)
            event_type_enum = EventType.RELEASE
        
        elif event_type == "CreateEvent":
            # 创建分支/标签
            ref = payload.get('ref', '')
            ref_type = payload.get('ref_type', '')
            
            if ref_type == 'branch':
                message = f"🌿 创建了新分支: **{ref}**"
                event_type_enum = EventType.CREATE_BRANCH
            elif ref_type == 'tag':
                message = f"🏷️ 创建了新标签: **{ref}**"
                event_type_enum = EventType.CREATE_BRANCH
            else:
                return None
            
            details['ref'] = ref
            details['ref_type'] = ref_type
        
        elif event_type == "DeleteEvent":
            # 删除分支/标签
            ref = payload.get('ref', '')
            ref_type = payload.get('ref_type', '')
            
            if ref_type == 'branch':
                message = f"🗑️ 删除了分支: **{ref}**"
                event_type_enum = EventType.DELETE_BRANCH
            elif ref_type == 'tag':
                message = f"🗑️ 删除了标签: **{ref}**"
                event_type_enum = EventType.DELETE_BRANCH
            else:
                return None
            
            details['ref'] = ref
            details['ref_type'] = ref_type
        
        elif event_type == "MemberEvent":
            # 协作者事件
            member = payload.get('member', {})
            action = payload.get('action', '')
            message = f"👤 {member.get('login', '')} 被{'添加为' if action == 'added' else '移除'}协作者"
            event_type_enum = EventType.UNKNOWN
            url = member.get('html_url', url)
        
        else:
            # 其他事件类型，暂时不处理
            return None
        
        return GitHubEvent(
            event_id=event_id,
            event_type=event_type_enum,
            repo_owner=owner,
            repo_name=repo,
            actor=actor,
            created_at=created_at,
            message=message,
            url=url,
            details=details
        )
    
    def get_recent_commits(self, owner: str, repo: str, 
                           branch: str = None, limit: int = 10) -> List[CommitInfo]:
        """获取最近的提交"""
        commits = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            if branch:
                commits_data = repository.get_commits(sha=branch)
            else:
                commits_data = repository.get_commits()
            
            for commit in commits_data[:limit]:
                try:
                    commits.append(CommitInfo(
                        sha=commit.sha[:7],
                        message=commit.commit.message.split('\n')[0] if commit.commit else "",
                        author=commit.commit.author.name if commit.commit and commit.commit.author else "unknown",
                        date=commit.commit.author.date if commit.commit else datetime.now(),
                        url=commit.html_url
                    ))
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"获取提交失败: {e}")
        
        return commits
    
    def get_recent_prs(self, owner: str, repo: str, 
                       state: str = "all", limit: int = 10) -> List[PREvent]:
        """获取最近的 PR"""
        prs = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            for pr in repository.get_pulls(state=state)[:limit]:
                merged = pr.merged
                action = PRAction.OPENED
                
                if pr.state == 'closed':
                    if merged:
                        action = PRAction.MERGED
                    else:
                        action = PRAction.CLOSED
                
                prs.append(PREvent(
                    number=pr.number,
                    title=pr.title,
                    user=pr.user.login,
                    action=action,
                    merged=merged,
                    created_at=pr.created_at,
                    url=pr.html_url
                ))
                
        except Exception as e:
            print(f"获取 PR 失败: {e}")
        
        return prs
    
    def get_recent_issues(self, owner: str, repo: str, 
                          state: str = "all", limit: int = 10) -> List[IssueEvent]:
        """获取最近的 Issues"""
        issues = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            for issue in repository.get_issues(state=state)[:limit]:
                if issue.pull_request:
                    continue  # 跳过 PR (PR 也是 Issue)
                
                action = IssueAction.OPENED
                if issue.state == 'closed':
                    action = IssueAction.CLOSED
                
                issues.append(IssueEvent(
                    number=issue.number,
                    title=issue.title,
                    user=issue.user.login,
                    action=action,
                    labels=[label.name for label in issue.labels],
                    created_at=issue.created_at,
                    url=issue.html_url
                ))
                
        except Exception as e:
            print(f"获取 Issue 失败: {e}")
        
        return issues
    
    def get_recent_releases(self, owner: str, repo: str, 
                            limit: int = 10) -> List[ReleaseEvent]:
        """获取最近的 Releases"""
        releases = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            for release in repository.get_releases()[:limit]:
                releases.append(ReleaseEvent(
                    tag_name=release.tag_name,
                    name=release.title or release.tag_name,
                    author=release.author.login if release.author else "unknown",
                    created_at=release.created_at,
                    body=release.body[:200] if release.body else "",
                    url=release.html_url,
                    is_prerelease=release.prerelease,
                    is_draft=release.draft
                ))
                
        except Exception as e:
            print(f"获取 Release 失败: {e}")
        
        return releases
    
    def get_branches(self, owner: str, repo: str) -> List[str]:
        """获取仓库的所有分支"""
        branches = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            for branch in repository.get_branches():
                branches.append(branch.name)
        except Exception as e:
            print(f"获取分支失败: {e}")
        
        return branches
    
    def get_default_branch(self, owner: str, repo: str) -> str:
        """获取默认分支"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            return repository.default_branch
        except Exception:
            return "main"
    
    def search_repos(self, query: str, limit: int = 30, 
                     sort: str = "stars", order: str = "desc") -> List[Dict]:
        """搜索仓库"""
        repos = []
        
        try:
            kwargs = {'query': query, 'per_page': min(limit, 100)}
            if sort:
                kwargs['sort'] = sort
            
            results = self.github.search_repositories(**kwargs)
            
            for repo in results:
                repos.append({
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'language': repo.language,
                    'html_url': repo.html_url
                })
                
        except Exception as e:
            print(f"搜索仓库失败: {e}")
        
        return repos
