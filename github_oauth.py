"""
GitHub OAuth 认证模块
"""

import os
import secrets
import hashlib
import time
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode

from github import Github, GithubException
from flask import Flask, request, redirect, session

from config import config


@dataclass
class GitHubUser:
    """GitHub 用户信息"""
    user_id: int  # Telegram chat_id
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


class GitHubOAuth:
    """GitHub OAuth 认证管理器"""
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv("GITHUB_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("GITHUB_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8080/oauth/callback")
        
        # OAuth 状态存储（生产环境应使用 Redis）
        self._oauth_states: Dict[str, Dict] = {}
        
        # Flask app for OAuth flow
        self.app = None
        self._callback_handlers: list = []
    
    def is_configured(self) -> bool:
        """检查 OAuth 是否已配置"""
        return bool(self.client_id and self.client_secret)
    
    def generate_state(self, chat_id: int) -> str:
        """生成 OAuth 状态码"""
        state = secrets.token_urlsafe(32)
        self._oauth_states[state] = {
            'chat_id': chat_id,
            'created_at': time.time(),
            'used': False
        }
        return state
    
    def validate_state(self, state: str) -> Optional[int]:
        """验证状态码并返回 chat_id"""
        if state not in self._oauth_states:
            return None
        
        state_data = self._oauth_states[state]
        
        # 检查是否已使用
        if state_data['used']:
            return None
        
        # 检查是否过期（10分钟）
        if time.time() - state_data['created_at'] > 600:
            del self._oauth_states[state]
            return None
        
        # 标记为已使用
        state_data['used'] = True
        
        return state_data['chat_id']
    
    def get_authorization_url(self, state: str) -> str:
        """获取授权 URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'repo,user,notifications,workflow',
            'state': state
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Optional[str]:
        """用授权码换取 access_token"""
        import requests
        
        url = "https://github.com/login/oauth/access_token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        headers = {'Accept': 'application/json'}
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            result = response.json()
            return result.get('access_token')
        except Exception as e:
            print(f"OAuth token exchange failed: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """获取 GitHub 用户信息"""
        import requests
        
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        try:
            # 获取用户信息
            user_response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            if user_response.status_code != 200:
                return None
            
            user_data = user_response.json()
            
            return {
                'login': user_data.get('login'),
                'id': user_data.get('id'),
                'avatar_url': user_data.get('avatar_url'),
                'name': user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'bio': user_data.get('bio', ''),
                'public_repos': user_data.get('public_repos', 0),
                'followers': user_data.get('followers', 0),
                'following': user_data.get('following', 0)
            }
        except Exception as e:
            print(f"Failed to get user info: {e}")
            return None
    
    def create_github_client(self, access_token: str) -> Github:
        """创建 GitHub 客户端"""
        return Github(access_token)
    
    def get_user_repos(self, access_token: str, limit: int = 30) -> list:
        """获取用户的仓库列表"""
        try:
            g = self.create_github_client(access_token)
            user = g.get_user()
            repos = []
            
            for repo in user.get_repos(per_page=50)[:limit]:
                repos.append({
                    'id': repo.id,
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'private': repo.private,
                    'fork': repo.fork,
                    'stargazers_count': repo.stargazers_count,
                    'forks_count': repo.forks_count,
                    'language': repo.language,
                    'default_branch': repo.default_branch
                })
            
            return repos
        except Exception as e:
            print(f"Failed to get user repos: {e}")
            return []
    
    def get_user_events(self, access_token: str, limit: int = 30) -> list:
        """获取用户的事件"""
        try:
            g = self.create_github_client(access_token)
            user = g.get_user()
            events = []
            
            for event in user.get_events()[:limit]:
                events.append({
                    'type': event.type,
                    'repo': event.repo.name if event.repo else None,
                    'created_at': event.created_at.isoformat(),
                    'payload': event.payload
                })
            
            return events
        except Exception as e:
            print(f"Failed to get user events: {e}")
            return []
    
    def get_notifications(self, access_token: str) -> list:
        """获取通知"""
        try:
            g = self.create_github_client(access_token)
            notifications = []
            
            for notif in g.get_user().get_notifications(all=False):
                notifications.append({
                    'id': notif.id,
                    'reason': notif.reason,
                    'unread': notif.unread,
                    'updated_at': notif.updated_at.isoformat(),
                    'subject': {
                        'title': notif.subject.title,
                        'type': notif.subject.type,
                        'url': notif.subject.url
                    },
                    'repository': {
                        'name': notif.repository.name,
                        'full_name': notif.repository.full_name
                    }
                })
            
            return notifications
        except Exception as e:
            print(f"Failed to get notifications: {e}")
            return []


class OAuthFlaskApp:
    """OAuth 回调 Flask 应用"""
    
    def __init__(self, oauth: GitHubOAuth, port: int = 8080):
        self.oauth = oauth
        self.port = port
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
        
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/oauth/callback')
        def callback():
            code = request.args.get('code')
            state = request.args.get('state')
            error = request.args.get('error')
            
            if error:
                return f"<h1>OAuth Error</h1><p>{error}</p><a href='/'>返回</a>"
            
            if not code or not state:
                return "<h1>Missing parameters</h1>"
            
            # 验证 state
            chat_id = self.oauth.validate_state(state)
            if not chat_id:
                return "<h1>Invalid state</h1><p>链接已过期，请重新发起授权</p>"
            
            # 交换 token
            access_token = self.oauth.exchange_code_for_token(code)
            if not access_token:
                return "<h1>Token exchange failed</h1>"
            
            # 获取用户信息
            user_info = self.oauth.get_user_info(access_token)
            if not user_info:
                return "<h1>Failed to get user info</h1>"
            
            # 调用回调处理器
            for handler in self._oauth_callback_handlers:
                handler(chat_id, user_info, access_token)
            
            return f"""
            <h1>✅ GitHub 授权成功！</h1>
            <p>欢迎 {user_info['login']}</p>
            <p>您可以关闭此页面并返回 Telegram 机器人继续使用</p>
            """
        
        @self.app.route('/')
        def index():
            return "<h1>GitHub OAuth Callback Server</h1><p>正在等待授权回调...</p>"
    
    @property
    def _oauth_callback_handlers(self):
        return self.oauth._callback_handlers
    
    def register_callback_handler(self, handler):
        """注册回调处理器"""
        self.oauth._callback_handlers.append(handler)
    
    def run(self, debug: bool = False):
        """运行服务器"""
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)
