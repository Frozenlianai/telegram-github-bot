"""
数据库模块 - 使用 SQLite 存储监控数据
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

from config import config


@dataclass
class MonitoredRepo:
    """监控的仓库"""
    chat_id: int
    owner: str
    repo: str
    added_at: str
    last_check: Optional[str] = None
    last_stars: Optional[int] = None
    last_forks: Optional[int] = None
    notified_events: Optional[str] = None  # JSON 字符串，存储已通知的事件ID
    
    def __post_init__(self):
        if self.notified_events is None:
            self.notified_events = "[]"
    
    def get_notified_events(self) -> List[str]:
        """获取已通知的事件ID列表"""
        try:
            return json.loads(self.notified_events)
        except:
            return []
    
    def add_notified_event(self, event_id: str, max_events: int = 100):
        """添加已通知的事件ID"""
        events = self.get_notified_events()
        events.append(event_id)
        # 保持列表在一定大小内
        if len(events) > max_events:
            events = events[-max_events:]
        self.notified_events = json.dumps(events)


@dataclass
class UserSettings:
    """用户设置"""
    chat_id: int
    check_interval: int = 5
    notify_stars: bool = True
    notify_forks: bool = True
    notify_commits: bool = True
    notify_prs: bool = True
    notify_issues: bool = True
    notify_releases: bool = True
    notify_branches: bool = True
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self._ensure_directory()
        self._init_database()
    
    def _ensure_directory(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 监控的仓库表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitored_repos (
                    chat_id INTEGER,
                    owner TEXT,
                    repo TEXT,
                    added_at TEXT,
                    last_check TEXT,
                    last_stars INTEGER,
                    last_forks INTEGER,
                    notified_events TEXT DEFAULT '[]',
                    PRIMARY KEY (chat_id, owner, repo)
                )
            """)
            
            # 用户设置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    chat_id INTEGER PRIMARY KEY,
                    check_interval INTEGER DEFAULT 5,
                    notify_stars INTEGER DEFAULT 1,
                    notify_forks INTEGER DEFAULT 1,
                    notify_commits INTEGER DEFAULT 1,
                    notify_prs INTEGER DEFAULT 1,
                    notify_issues INTEGER DEFAULT 1,
                    notify_releases INTEGER DEFAULT 1,
                    notify_branches INTEGER DEFAULT 1,
                    created_at TEXT
                )
            """)
            
            # 活动历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    owner TEXT,
                    repo TEXT,
                    event_type TEXT,
                    event_id TEXT,
                    event_data TEXT,
                    created_at TEXT
                )
            """)
            
            conn.commit()
    
    # ==================== 仓库监控操作 ====================
    
    def add_repo(self, chat_id: int, owner: str, repo: str) -> bool:
        """添加监控仓库"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO monitored_repos 
                    (chat_id, owner, repo, added_at)
                    VALUES (?, ?, ?, ?)
                """, (chat_id, owner, repo, datetime.utcnow().isoformat()))
                conn.commit()
                return True
        except Exception as e:
            print(f"添加仓库失败: {e}")
            return False
    
    def remove_repo(self, chat_id: int, owner: str, repo: str) -> bool:
        """移除监控仓库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM monitored_repos 
                WHERE chat_id = ? AND owner = ? AND repo = ?
            """, (chat_id, owner, repo))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_user_repos(self, chat_id: int) -> List[MonitoredRepo]:
        """获取用户监控的所有仓库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM monitored_repos WHERE chat_id = ?
            """, (chat_id,))
            return [MonitoredRepo(**dict(row)) for row in cursor.fetchall()]
    
    def get_all_monitored_repos(self) -> List[MonitoredRepo]:
        """获取所有监控的仓库（按 chat_id 分组）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM monitored_repos")
            return [MonitoredRepo(**dict(row)) for row in cursor.fetchall()]
    
    def update_repo_check(self, chat_id: int, owner: str, repo: str, 
                          stars: int = None, forks: int = None):
        """更新仓库检查信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            if stars is not None and forks is not None:
                cursor.execute("""
                    UPDATE monitored_repos 
                    SET last_check = ?, last_stars = ?, last_forks = ?
                    WHERE chat_id = ? AND owner = ? AND repo = ?
                """, (now, stars, forks, chat_id, owner, repo))
            elif stars is not None:
                cursor.execute("""
                    UPDATE monitored_repos 
                    SET last_check = ?, last_stars = ?
                    WHERE chat_id = ? AND owner = ? AND repo = ?
                """, (now, stars, chat_id, owner, repo))
            elif forks is not None:
                cursor.execute("""
                    UPDATE monitored_repos 
                    SET last_check = ?, last_forks = ?
                    WHERE chat_id = ? AND owner = ? AND repo = ?
                """, (now, forks, chat_id, owner, repo))
            else:
                cursor.execute("""
                    UPDATE monitored_repos 
                    SET last_check = ?
                    WHERE chat_id = ? AND owner = ? AND repo = ?
                """, (now, chat_id, owner, repo))
            
            conn.commit()
    
    def update_notified_events(self, chat_id: int, owner: str, repo: str, events: str):
        """更新已通知事件列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE monitored_repos 
                SET notified_events = ?
                WHERE chat_id = ? AND owner = ? AND repo = ?
            """, (events, chat_id, owner, repo))
            conn.commit()
    
    def repo_exists(self, chat_id: int, owner: str, repo: str) -> bool:
        """检查仓库是否已被监控"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM monitored_repos 
                WHERE chat_id = ? AND owner = ? AND repo = ?
            """, (chat_id, owner, repo))
            return cursor.fetchone() is not None
    
    # ==================== 用户设置操作 ====================
    
    def get_user_settings(self, chat_id: int) -> UserSettings:
        """获取用户设置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_settings WHERE chat_id = ?
            """, (chat_id,))
            row = cursor.fetchone()
            
            if row:
                return UserSettings(
                    chat_id=row['chat_id'],
                    check_interval=row['check_interval'],
                    notify_stars=bool(row['notify_stars']),
                    notify_forks=bool(row['notify_forks']),
                    notify_commits=bool(row['notify_commits']),
                    notify_prs=bool(row['notify_prs']),
                    notify_issues=bool(row['notify_issues']),
                    notify_releases=bool(row['notify_releases']),
                    notify_branches=bool(row['notify_branches']),
                    created_at=row['created_at']
                )
            else:
                # 返回默认设置
                return UserSettings(chat_id=chat_id)
    
    def save_user_settings(self, settings: UserSettings):
        """保存用户设置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings 
                (chat_id, check_interval, notify_stars, notify_forks, 
                 notify_commits, notify_prs, notify_issues, notify_releases,
                 notify_branches, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                settings.chat_id,
                settings.check_interval,
                int(settings.notify_stars),
                int(settings.notify_forks),
                int(settings.notify_commits),
                int(settings.notify_prs),
                int(settings.notify_issues),
                int(settings.notify_releases),
                int(settings.notify_branches),
                settings.created_at
            ))
            conn.commit()
    
    # ==================== 活动历史操作 ====================
    
    def add_activity(self, chat_id: int, owner: str, repo: str, 
                     event_type: str, event_id: str, event_data: dict):
        """记录活动历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_history 
                (chat_id, owner, repo, event_type, event_id, event_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, owner, repo, event_type, event_id, 
                  json.dumps(event_data, ensure_ascii=False),
                  datetime.utcnow().isoformat()))
            conn.commit()
    
    def get_recent_activities(self, chat_id: int, owner: str = None, 
                               repo: str = None, limit: int = 20) -> List[Dict]:
        """获取最近活动"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if owner and repo:
                cursor.execute("""
                    SELECT * FROM activity_history 
                    WHERE chat_id = ? AND owner = ? AND repo = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (chat_id, owner, repo, limit))
            else:
                cursor.execute("""
                    SELECT * FROM activity_history 
                    WHERE chat_id = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (chat_id, limit))
            
            rows = cursor.fetchall()
            return [
                {
                    **dict(row),
                    'event_data': json.loads(row['event_data'])
                }
                for row in rows
            ]
    
    # ==================== 统计操作 ====================
    
    def get_stats(self, chat_id: int = None) -> Dict[str, Any]:
        """获取统计信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if chat_id:
                # 用户统计
                cursor.execute("""
                    SELECT COUNT(*) as repo_count FROM monitored_repos WHERE chat_id = ?
                """, (chat_id,))
                repo_count = cursor.fetchone()['repo_count']
                
                cursor.execute("""
                    SELECT COUNT(*) as activity_count FROM activity_history WHERE chat_id = ?
                """, (chat_id,))
                activity_count = cursor.fetchone()['activity_count']
                
                return {
                    'repo_count': repo_count,
                    'activity_count': activity_count
                }
            else:
                # 全局统计
                cursor.execute("SELECT COUNT(*) as total FROM monitored_repos")
                total_repos = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM user_settings")
                total_users = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM activity_history")
                total_activities = cursor.fetchone()['total']
                
                return {
                    'total_repos': total_repos,
                    'total_users': total_users,
                    'total_activities': total_activities
                }
