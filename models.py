"""
GitHub API 客户端和数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class EventType(Enum):
    """GitHub 事件类型"""
    STAR = "star"
    FORK = "fork"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    RELEASE = "release"
    CREATE_BRANCH = "create_branch"
    DELETE_BRANCH = "delete_branch"
    WATCH = "watch"
    UNKNOWN = "unknown"


class PRAction(Enum):
    """PR 操作类型"""
    OPENED = "opened"
    CLOSED = "closed"
    MERGED = "merged"
    REOPENED = "reopened"


class IssueAction(Enum):
    """Issue 操作类型"""
    OPENED = "opened"
    CLOSED = "closed"
    REOPENED = "reopened"


@dataclass
class GitHubEvent:
    """GitHub 事件"""
    event_id: str
    event_type: EventType
    repo_owner: str
    repo_name: str
    actor: str
    created_at: datetime
    message: str
    url: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_message(self) -> str:
        """转换为 Telegram 消息"""
        emoji_map = {
            EventType.STAR: "⭐",
            EventType.FORK: "🍴",
            EventType.COMMIT: "📝",
            EventType.PULL_REQUEST: "🔀",
            EventType.ISSUE: "🐛",
            EventType.RELEASE: "🚀",
            EventType.CREATE_BRANCH: "🌿",
            EventType.DELETE_BRANCH: "🗑️",
            EventType.WATCH: "👀",
        }
        
        emoji = emoji_map.get(self.event_type, "📌")
        time_str = self.created_at.strftime("%Y-%m-%d %H:%M")
        
        msg = f"{emoji} **{self.repo_name}**\n"
        msg += f"👤 {self.actor}\n"
        msg += f"⏰ {time_str}\n"
        msg += f"{self.message}"
        
        if self.url:
            msg += f"\n🔗 [查看详情]({self.url})"
        
        return msg


@dataclass
class RepoStats:
    """仓库统计信息"""
    owner: str
    name: str
    full_name: str
    description: Optional[str]
    stars: int
    forks: int
    open_issues: int
    watchers: int
    language: Optional[str]
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    homepage: Optional[str]
    topics: List[str] = field(default_factory=list)
    license: Optional[str] = None
    
    @property
    def star_change(self) -> int:
        return 0  # 需要外部传入对比
    
    @property
    def fork_change(self) -> int:
        return 0  # 需要外部传入对比


@dataclass
class CommitInfo:
    """提交信息"""
    sha: str
    message: str
    author: str
    date: datetime
    url: str


@dataclass
class PREvent:
    """PR 事件"""
    number: int
    title: str
    user: str
    action: PRAction
    merged: bool
    created_at: datetime
    url: str


@dataclass
class IssueEvent:
    """Issue 事件"""
    number: int
    title: str
    user: str
    action: IssueAction
    labels: List[str]
    created_at: datetime
    url: str


@dataclass
class ReleaseEvent:
    """Release 事件"""
    tag_name: str
    name: str
    author: str
    created_at: datetime
    body: str
    url: str
    is_prerelease: bool
    is_draft: bool


@dataclass
class BranchEvent:
    """分支事件"""
    ref: str
    ref_type: str  # "branch" or "tag"
    created_by: str
    created_at: datetime
