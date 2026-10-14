"""
数据库扩展模块 - 支持 GitHub 用户绑定
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from database import Database as BaseDatabase


@dataclass
class GitHubAccount:
    """绑定的 GitHub 账号"""
    chat_id: int
    github_login: str
    github_user_id: int
    avatar_url: str
    name: str
    email: str
    bio: str
    public_repos: int
    followers: int
    following: int
    access_token: str
    created_at: str
    updated_at: str


class DatabaseExtended(BaseDatabase):
    """扩展的数据库类"""
    
    def _init_database(self):
        """初始化数据库表"""
        super()._init_database()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # GitHub 账号绑定表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS github_accounts (
                    chat_id INTEGER PRIMARY KEY,
                    github_login TEXT NOT NULL,
                    github_user_id INTEGER NOT NULL,
                    avatar_url TEXT,
                    name TEXT,
                    email TEXT,
                    bio TEXT,
                    public_repos INTEGER DEFAULT 0,
                    followers INTEGER DEFAULT 0,
                    following INTEGER DEFAULT 0,
                    access_token TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Fork 历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fork_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    source_owner TEXT,
                    source_repo TEXT,
                    forked_repo TEXT,
                    forked_at TEXT,
                    FOREIGN KEY (chat_id) REFERENCES github_accounts(chat_id)
                )
            """)
            
            # Workflow 监控表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_monitors (
                    chat_id INTEGER,
                    owner TEXT,
                    repo TEXT,
                    workflow_id TEXT,
                    workflow_name TEXT,
                    last_run_id INTEGER,
                    notify_on_start INTEGER DEFAULT 1,
                    notify_on_complete INTEGER DEFAULT 1,
                    notify_on_failure INTEGER DEFAULT 1,
                    created_at TEXT,
                    UNIQUE(chat_id, owner, repo, workflow_id)
                )
            """)
            
            # PR 草稿表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pr_drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    owner TEXT,
                    repo TEXT,
                    title TEXT,
                    body TEXT,
                    head_branch TEXT,
                    base_branch TEXT DEFAULT 'main',
                    draft INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # 快捷命令表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quick_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    created_at TEXT,
                    UNIQUE(chat_id, name)
                )
            """)
            
            # Trending 项目追踪表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trending_tracked (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    owner TEXT NOT NULL,
                    repo TEXT NOT NULL,
                    name TEXT,
                    description TEXT,
                    initial_stars INTEGER DEFAULT 0,
                    current_stars INTEGER DEFAULT 0,
                    peak_stars_today INTEGER DEFAULT 0,
                    first_seen TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    trend_score REAL DEFAULT 0,
                    UNIQUE(chat_id, owner, repo)
                )
            """)
            
            # Trending 缓存表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trending_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE,
                    data TEXT,
                    created_at TEXT,
                    expires_at TEXT
                )
            """)
            
            conn.commit()
    
    # ==================== GitHub 账号绑定 ====================
    
    def bind_github_account(self, account: GitHubAccount) -> bool:
        """绑定 GitHub 账号"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO github_accounts 
                    (chat_id, github_login, github_user_id, avatar_url, 
                     name, email, bio, public_repos, followers, following,
                     access_token, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    account.chat_id,
                    account.github_login,
                    account.github_user_id,
                    account.avatar_url,
                    account.name,
                    account.email,
                    account.bio,
                    account.public_repos,
                    account.followers,
                    account.following,
                    account.access_token,
                    account.created_at,
                    account.updated_at
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"绑定账号失败: {e}")
            return False
    
    def get_github_account(self, chat_id: int) -> Optional[GitHubAccount]:
        """获取绑定的 GitHub 账号"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM github_accounts WHERE chat_id = ?
            """, (chat_id,))
            row = cursor.fetchone()
            
            if row:
                return GitHubAccount(**dict(row))
            return None
    
    def unbind_github_account(self, chat_id: int) -> bool:
        """解绑 GitHub 账号"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM github_accounts WHERE chat_id = ?
            """, (chat_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_github_account(self, chat_id: int, **kwargs) -> bool:
        """更新 GitHub 账号信息"""
        allowed_fields = [
            'github_login', 'github_user_id', 'avatar_url', 'name',
            'email', 'bio', 'public_repos', 'followers', 'following',
            'access_token', 'updated_at'
        ]
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [chat_id]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE github_accounts SET {set_clause} WHERE chat_id = ?
            """, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def is_github_bound(self, chat_id: int) -> bool:
        """检查是否已绑定 GitHub 账号"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM github_accounts WHERE chat_id = ?
            """, (chat_id,))
            return cursor.fetchone() is not None
    
    # ==================== Fork 历史 ====================
    
    def add_fork_history(self, chat_id: int, source_owner: str, 
                        source_repo: str, forked_repo: str) -> bool:
        """添加 Fork 记录"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO fork_history 
                    (chat_id, source_owner, source_repo, forked_repo, forked_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (chat_id, source_owner, source_repo, forked_repo,
                      datetime.utcnow().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加 fork 记录失败: {e}")
            return False
    
    def get_fork_history(self, chat_id: int, limit: int = 20) -> List[Dict]:
        """获取 Fork 历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM fork_history 
                WHERE chat_id = ?
                ORDER BY forked_at DESC
                LIMIT ?
            """, (chat_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Workflow 监控 ====================
    
    def add_workflow_monitor(self, chat_id: int, owner: str, repo: str,
                             workflow_id: str, workflow_name: str) -> bool:
        """添加 Workflow 监控"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO workflow_monitors 
                    (chat_id, owner, repo, workflow_id, workflow_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (chat_id, owner, repo, workflow_id, workflow_name,
                      datetime.utcnow().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加 workflow 监控失败: {e}")
            return False
    
    def remove_workflow_monitor(self, chat_id: int, owner: str, 
                               repo: str, workflow_id: str) -> bool:
        """移除 Workflow 监控"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM workflow_monitors 
                WHERE chat_id = ? AND owner = ? AND repo = ? AND workflow_id = ?
            """, (chat_id, owner, repo, workflow_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_workflow_monitors(self, chat_id: int) -> List[Dict]:
        """获取用户的 Workflow 监控列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workflow_monitors WHERE chat_id = ?
            """, (chat_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_workflow_monitors(self) -> List[Dict]:
        """获取所有 Workflow 监控"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflow_monitors")
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_workflow_last_run(self, chat_id: int, owner: str,
                                 repo: str, workflow_id: str, run_id: int) -> bool:
        """更新 Workflow 最后运行的 ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflow_monitors 
                SET last_run_id = ?
                WHERE chat_id = ? AND owner = ? AND repo = ? AND workflow_id = ?
            """, (run_id, chat_id, owner, repo, workflow_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== PR 草稿 ====================
    
    def save_pr_draft(self, chat_id: int, owner: str, repo: str,
                      title: str, body: str, head_branch: str,
                      base_branch: str = "main", draft_id: int = None) -> int:
        """保存 PR 草稿"""
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if draft_id:
                cursor.execute("""
                    UPDATE pr_drafts 
                    SET title = ?, body = ?, head_branch = ?, 
                        base_branch = ?, updated_at = ?
                    WHERE id = ? AND chat_id = ?
                """, (title, body, head_branch, base_branch, now, draft_id, chat_id))
                conn.commit()
                return draft_id
            else:
                cursor.execute("""
                    INSERT INTO pr_drafts 
                    (chat_id, owner, repo, title, body, head_branch, 
                     base_branch, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (chat_id, owner, repo, title, body, head_branch,
                      base_branch, now, now))
                conn.commit()
                return cursor.lastrowid
    
    def get_pr_drafts(self, chat_id: int, owner: str = None, 
                      repo: str = None) -> List[Dict]:
        """获取 PR 草稿"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if owner and repo:
                cursor.execute("""
                    SELECT * FROM pr_drafts 
                    WHERE chat_id = ? AND owner = ? AND repo = ?
                    ORDER BY updated_at DESC
                """, (chat_id, owner, repo))
            else:
                cursor.execute("""
                    SELECT * FROM pr_drafts 
                    WHERE chat_id = ?
                    ORDER BY updated_at DESC
                """, (chat_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_pr_draft(self, chat_id: int, draft_id: int) -> bool:
        """删除 PR 草稿"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM pr_drafts 
                WHERE id = ? AND chat_id = ?
            """, (draft_id, chat_id))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== 快捷命令 ====================
    
    def add_quick_command(self, chat_id: int, name: str, 
                          command: str) -> bool:
        """添加快捷命令"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO quick_commands 
                    (chat_id, name, command, created_at)
                    VALUES (?, ?, ?, ?)
                """, (chat_id, name, command, datetime.utcnow().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加快捷命令失败: {e}")
            return False
    
    def get_quick_commands(self, chat_id: int) -> List[Dict]:
        """获取快捷命令"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM quick_commands 
                WHERE chat_id = ?
                ORDER BY name
            """, (chat_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_quick_command(self, chat_id: int, name: str) -> bool:
        """删除快捷命令"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM quick_commands 
                WHERE chat_id = ? AND name = ?
            """, (chat_id, name))
            conn.commit()
            return cursor.rowcount > 0
    
    # ==================== 统计 ====================
    
    def get_user_total_stats(self, chat_id: int) -> Dict[str, Any]:
        """获取用户总统计"""
        stats = self.get_stats(chat_id)
        
        # 添加额外统计
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Fork 数量
            cursor.execute("""
                SELECT COUNT(*) FROM fork_history WHERE chat_id = ?
            """, (chat_id,))
            stats['fork_count'] = cursor.fetchone()[0]
            
            # Workflow 监控数量
            cursor.execute("""
                SELECT COUNT(*) FROM workflow_monitors WHERE chat_id = ?
            """, (chat_id,))
            stats['workflow_monitor_count'] = cursor.fetchone()[0]
            
            # PR 草稿数量
            cursor.execute("""
                SELECT COUNT(*) FROM pr_drafts WHERE chat_id = ?
            """, (chat_id,))
            stats['pr_draft_count'] = cursor.fetchone()[0]
        
        return stats
    
    # ==================== Trending 追踪 ====================
    
    def track_trending_repo(self, chat_id: int, owner: str, repo: str,
                           name: str = None, description: str = None,
                           stars: int = 0) -> bool:
        """追踪 Trending 项目"""
        try:
            now = datetime.utcnow().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trending_tracked 
                    (chat_id, owner, repo, name, description, initial_stars, 
                     current_stars, peak_stars_today, first_seen, last_updated, trend_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 0)
                """, (chat_id, owner, repo, name, description, stars, stars, now, now))
                conn.commit()
                return True
        except Exception as e:
            print(f"追踪项目失败: {e}")
            return False
    
    def get_tracked_repos(self, chat_id: int = None) -> List[Dict]:
        """获取追踪的项目列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if chat_id:
                cursor.execute("""
                    SELECT * FROM trending_tracked 
                    WHERE chat_id = ?
                    ORDER BY trend_score DESC, last_updated DESC
                """, (chat_id,))
            else:
                cursor.execute("""
                    SELECT * FROM trending_tracked 
                    ORDER BY trend_score DESC, last_updated DESC
                """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_tracked_repo(self, chat_id: int, owner: str, repo: str,
                           current_stars: int, stars_today: int = 0) -> bool:
        """更新追踪项目数据"""
        try:
            now = datetime.utcnow().isoformat()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 获取当前数据
                cursor.execute("""
                    SELECT initial_stars, peak_stars_today, first_seen 
                    FROM trending_tracked 
                    WHERE chat_id = ? AND owner = ? AND repo = ?
                """, (chat_id, owner, repo))
                
                row = cursor.fetchone()
                if not row:
                    return False
                
                initial_stars = row['initial_stars']
                peak_stars_today = row['peak_stars_today']
                first_seen = row['first_seen']
                
                # 更新峰值
                if stars_today > peak_stars_today:
                    peak_stars_today = stars_today
                
                # 计算趋势评分
                days_since_first = (datetime.now() - datetime.fromisoformat(first_seen)).days
                if days_since_first <= 0:
                    days_since_first = 1
                
                growth = current_stars - initial_stars
                trend_score = (growth * 5 + stars_today * 10) / days_since_first
                
                cursor.execute("""
                    UPDATE trending_tracked 
                    SET current_stars = ?, peak_stars_today = ?, 
                        last_updated = ?, trend_score = ?
                    WHERE chat_id = ? AND owner = ? AND repo = ?
                """, (current_stars, peak_stars_today, now, trend_score,
                      chat_id, owner, repo))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"更新追踪项目失败: {e}")
            return False
    
    def untrack_repo(self, chat_id: int, owner: str, repo: str) -> bool:
        """取消追踪项目"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM trending_tracked 
                WHERE chat_id = ? AND owner = ? AND repo = ?
            """, (chat_id, owner, repo))
            conn.commit()
            return cursor.rowcount > 0
    
    def is_repo_tracked(self, chat_id: int, owner: str, repo: str) -> bool:
        """检查项目是否被追踪"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM trending_tracked 
                WHERE chat_id = ? AND owner = ? AND repo = ?
            """, (chat_id, owner, repo))
            return cursor.fetchone() is not None
    
    def get_hot_tracked_repos(self, limit: int = 10) -> List[Dict]:
        """获取最热门的追踪项目"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trending_tracked 
                ORDER BY trend_score DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cache_trending_data(self, cache_key: str, data: str, ttl_seconds: int = 300) -> bool:
        """缓存 Trending 数据"""
        try:
            now = datetime.utcnow()
            expires = now + timedelta(seconds=ttl_seconds)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trending_cache 
                    (cache_key, data, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                """, (cache_key, data, now.isoformat(), expires.isoformat()))
                conn.commit()
                return True
        except Exception as e:
            print(f"缓存数据失败: {e}")
            return False
    
    def get_cached_trending(self, cache_key: str) -> Optional[str]:
        """获取缓存的 Trending 数据"""
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data FROM trending_cache 
                WHERE cache_key = ? AND expires_at > ?
            """, (cache_key, now))
            
            row = cursor.fetchone()
            return row['data'] if row else None
