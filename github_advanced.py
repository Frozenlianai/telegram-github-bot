"""
GitHub 高级操作模块
支持 Fork、PR、Actions、Workflow 等功能
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

from enum import Enum

from github import Github, GithubException, InputFileContent
from github.GithubObject import NotSet

from config import config
from models import (
    CommitInfo, PREvent, IssueEvent, ReleaseEvent, BranchEvent
)
from github_oauth import GitHubOAuth


class PRAction(Enum):
    """PR 操作类型"""
    OPENED = "opened"
    CLOSED = "closed"
    MERGED = "merged"
    REOPENED = "reopened"
    EDITED = "edited"


class ReviewState(Enum):
    """Review 状态"""
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    PENDING = "PENDING"


class CheckStatus(Enum):
    """检查状态"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ConclusionState(Enum):
    """结论状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"


@dataclass
class ForkResult:
    """Fork 结果"""
    success: bool
    full_name: str = ""
    html_url: str = ""
    message: str = ""


@dataclass
class PRCreateResult:
    """PR 创建结果"""
    success: bool
    number: int = 0
    title: str = ""
    html_url: str = ""
    message: str = ""


@dataclass
class WorkflowInfo:
    """Workflow 信息"""
    id: int
    name: str
    path: str
    state: str
    created_at: datetime
    updated_at: datetime
    html_url: str


@dataclass
class WorkflowRun:
    """Workflow 运行信息"""
    id: int
    name: str
    head_branch: str
    head_sha: str
    status: str
    conclusion: Optional[str]
    event: str
    created_at: datetime
    updated_at: datetime
    html_url: str
    duration: Optional[int] = None  # 秒


@dataclass
class CommitStatus:
    """提交状态"""
    state: str
    description: str
    target_url: str
    context: str


@dataclass
class CheckRun:
    """Check Run 信息"""
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    html_url: str


class GitHubActions:
    """GitHub Actions 管理"""
    
    def __init__(self, token: str):
        self.token = token
        from github import Auth
        self.github = Github(auth=Auth.Token(token))
    
    def get_workflows(self, owner: str, repo: str) -> List[WorkflowInfo]:
        """获取仓库的所有 workflows"""
        workflows = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            for wf in repository.get_workflows():
                workflows.append(WorkflowInfo(
                    id=wf.id,
                    name=wf.name,
                    path=wf.path,
                    state=wf.state,
                    created_at=wf.created_at,
                    updated_at=wf.updated_at,
                    html_url=wf.html_url
                ))
        except Exception as e:
            print(f"获取 workflows 失败: {e}")
        
        return workflows
    
    def get_workflow_runs(self, owner: str, repo: str, 
                          workflow_id: str = None, branch: str = None,
                          limit: int = 20) -> List[WorkflowRun]:
        """获取 workflow 运行记录"""
        runs = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            if workflow_id:
                # 获取特定 workflow 的运行
                workflow = repository.get_workflow(int(workflow_id)) if workflow_id.isdigit() \
                          else repository.get_workflow(workflow_id)
                runs_data = workflow.get_runs()
            else:
                # 获取所有 workflow 的运行
                runs_data = repository.get_workflow_runs()
            
            for run in runs_data[:limit]:
                # 计算持续时间
                duration = None
                if run.updated_at and run.created_at:
                    duration = int((run.updated_at - run.created_at).total_seconds())
                
                runs.append(WorkflowRun(
                    id=run.id,
                    name=run.name,
                    head_branch=run.head_branch,
                    head_sha=run.head_sha[:7],
                    status=run.status,
                    conclusion=run.conclusion,
                    event=run.event,
                    created_at=run.created_at,
                    updated_at=run.updated_at,
                    html_url=run.html_url,
                    duration=duration
                ))
                
        except Exception as e:
            print(f"获取 workflow runs 失败: {e}")
        
        return runs
    
    def trigger_workflow(self, owner: str, repo: str, 
                         workflow_id: str, ref: str = "main",
                         inputs: Dict[str, str] = None) -> Tuple[bool, str]:
        """触发 workflow 运行"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            workflow = repository.get_workflow(int(workflow_id)) if workflow_id.isdigit() \
                      else repository.get_workflow(workflow_id)
            
            # 创建 workflow dispatch
            workflow.create_dispatch(ref, inputs or {})
            
            return True, f"✅ 已触发 workflow: {workflow.name} on {ref}"
            
        except GithubException as e:
            return False, f"❌ 触发失败: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 错误: {str(e)}"
    
    def rerun_workflow(self, owner: str, repo: str, run_id: int) -> Tuple[bool, str]:
        """重新运行 workflow"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            run = repository.get_workflow_run(run_id)
            run.rerun()
            
            return True, f"✅ 已重新运行 workflow"
            
        except GithubException as e:
            return False, f"❌ 重新运行失败: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 错误: {str(e)}"
    
    def cancel_workflow(self, owner: str, repo: str, run_id: int) -> Tuple[bool, str]:
        """取消 workflow 运行"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            run = repository.get_workflow_run(run_id)
            run.cancel()
            
            return True, f"✅ 已取消 workflow 运行"
            
        except GithubException as e:
            return False, f"❌ 取消失败: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 错误: {str(e)}"
    
    def get_run_jobs(self, owner: str, repo: str, run_id: int) -> List[Dict]:
        """获取 workflow run 的 jobs"""
        jobs = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            run = repository.get_workflow_run(run_id)
            
            for job in run.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'status': job.status,
                    'conclusion': job.conclusion,
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                    'html_url': job.html_url,
                    'steps': [
                        {
                            'name': step.name,
                            'status': step.status,
                            'conclusion': step.conclusion,
                            'number': step.number
                        }
                        for step in job.get_steps()
                    ]
                })
                
        except Exception as e:
            print(f"获取 jobs 失败: {e}")
        
        return jobs
    
    def get_run_logs_url(self, owner: str, repo: str, run_id: int) -> str:
        """获取 workflow run 日志下载链接"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            run = repository.get_workflow_run(run_id)
            return run.logs_url
        except:
            return ""


class GitHubAdvanced:
    """GitHub 高级操作类"""
    
    def __init__(self, token: str):
        self.token = token
        from github import Auth
        self.github = Github(auth=Auth.Token(token))
        self.actions = GitHubActions(token)
    
    # ==================== Fork 操作 ====================
    
    def fork_repository(self, owner: str, repo: str, 
                        organization: str = None) -> ForkResult:
        """
        Fork 仓库到自己的账户或指定组织
        
        Args:
            owner: 仓库所有者
            repo: 仓库名
            organization: 可选，fork 到指定组织
        
        Returns:
            ForkResult: Fork 结果
        """
        try:
            source_repo = self.github.get_repo(f"{owner}/{repo}")
            
            # 执行 fork
            if organization:
                forked_repo = source_repo.create_fork(organization)
            else:
                forked_repo = source_repo.create_fork()
            
            return ForkResult(
                success=True,
                full_name=forked_repo.full_name,
                html_url=forked_repo.html_url,
                message=f"✅ 成功 Fork 到 {forked_repo.full_name}"
            )
            
        except GithubException as e:
            if e.status == 202:
                # Fork 已经在进行中
                return ForkResult(
                    success=True,
                    full_name=f"{self.github.get_user().login}/{repo}",
                    html_url=f"https://github.com/{self.github.get_user().login}/{repo}",
                    message=f"⏳ Fork 已在进行中"
                )
            
            error_msg = e.data.get('message', str(e))
            return ForkResult(
                success=False,
                message=f"❌ Fork 失败: {error_msg}"
            )
        except Exception as e:
            return ForkResult(
                success=False,
                message=f"❌ 错误: {str(e)}"
            )
    
    def list_my_forks(self, owner: str, repo: str) -> List[Dict]:
        """列出仓库的所有 forks"""
        forks = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            for fork in repository.get_forks():
                forks.append({
                    'owner': fork.owner.login,
                    'full_name': fork.full_name,
                    'html_url': fork.html_url,
                    'description': fork.description,
                    'stars': fork.stargazers_count,
                    'forks': fork.forks_count,
                    'pushed_at': fork.pushed_at.isoformat() if fork.pushed_at else None
                })
                
        except Exception as e:
            print(f"获取 forks 失败: {e}")
        
        return forks
    
    # ==================== Pull Request 操作 ====================
    
    def create_pr(self, owner: str, repo: str,
                  title: str, body: str, head: str, base: str = "main",
                  maintainer_can_modify: bool = True,
                  draft: bool = False) -> PRCreateResult:
        """
        创建 Pull Request
        
        Args:
            owner: 仓库所有者
            repo: 仓库名
            title: PR 标题
            body: PR 描述
            head: 源分支（包含冒号，格式: owner:branch）
            base: 目标分支
            maintainer_can_modify: 是否允许维护者修改
            draft: 是否为草稿 PR
        
        Returns:
            PRCreateResult: PR 创建结果
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            pull = repository.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
                maintainer_can_modify=maintainer_can_modify,
                draft=draft
            )
            
            return PRCreateResult(
                success=True,
                number=pull.number,
                title=pull.title,
                html_url=pull.html_url,
                message=f"✅ PR 创建成功！\n#{pull.number}: {pull.title}\n{pull.html_url}"
            )
            
        except GithubException as e:
            return PRCreateResult(
                success=False,
                message=f"❌ 创建 PR 失败: {e.data.get('message', str(e))}"
            )
        except Exception as e:
            return PRCreateResult(
                success=False,
                message=f"❌ 错误: {str(e)}"
            )
    
    def update_pr(self, owner: str, repo: str, pr_number: int,
                  title: str = None, body: str = None,
                  state: str = None, labels: List[str] = None,
                  assignees: List[str] = None) -> Tuple[bool, str]:
        """更新 PR"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)
            
            if title:
                pull.edit(title=title)
            if body:
                pull.edit(body=body)
            if state:
                pull.edit(state=state)
            if labels:
                pull.set_labels(*labels)
            if assignees:
                pull.set_assignees(*assignees)
            
            return True, f"✅ PR #{pr_number} 已更新"
            
        except Exception as e:
            return False, f"❌ 更新失败: {str(e)}"
    
    def merge_pr(self, owner: str, repo: str, pr_number: int,
                  commit_title: str = None, commit_message: str = None,
                  method: str = "merge") -> Tuple[bool, str]:
        """
        合并 PR
        
        Args:
            method: merge, squash, rebase
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)
            
            if method == "squash":
                pull.merge(commit_title=commit_title, commit_message=commit_message, squash=True)
            elif method == "rebase":
                pull.merge(commit_title=commit_title, commit_message=commit_message, merge_method="rebase")
            else:
                pull.merge(commit_title=commit_title, commit_message=commit_message)
            
            return True, f"✅ PR #{pr_number} 已合并"
            
        except GithubException as e:
            return False, f"❌ 合并失败: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 错误: {str(e)}"
    
    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """获取 PR 修改的文件"""
        files = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)
            
            for file in pull.get_files():
                files.append({
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'patch': file.patch,
                    'sha': file.sha
                })
                
        except Exception as e:
            print(f"获取 PR 文件失败: {e}")
        
        return files
    
    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """获取 PR 的 reviews"""
        reviews = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)
            
            for review in pull.get_reviews():
                reviews.append({
                    'user': review.user.login,
                    'state': review.state,
                    'submitted_at': review.submitted_at.isoformat() if review.submitted_at else None,
                    'body': review.body
                })
                
        except Exception as e:
            print(f"获取 reviews 失败: {e}")
        
        return reviews
    
    def add_pr_review_comment(self, owner: str, repo: str, pr_number: int,
                              body: str, commit_id: str = None,
                              path: str = None, line: int = None) -> Tuple[bool, str]:
        """添加 PR review 评论"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)
            
            # 通用评论
            if not path:
                pull.create_review_comment(body=body)
                return True, "✅ 评论已添加"
            
            # 文件特定评论
            if path and line:
                position = self._calculate_position(pull, path, line)
                pull.create_review_comment(body=body, commit_id=commit_id or pull.head.sha,
                                          path=path, position=position or 1)
                return True, "✅ 评论已添加"
            
            return False, "❌ 请提供文件路径和行号"
            
        except Exception as e:
            return False, f"❌ 添加评论失败: {str(e)}"
    
    def _calculate_position(self, pull, path: str, line: int) -> Optional[int]:
        """计算评论位置"""
        try:
            for file in pull.get_files():
                if file.filename == path:
                    # 简单计算，实际可能更复杂
                    return line
        except:
            pass
        return None
    
    # ==================== 分支操作 ====================
    
    def create_branch(self, owner: str, repo: str,
                      branch_name: str, from_branch: str = "main") -> Tuple[bool, str]:
        """创建新分支"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            # 获取源分支的 SHA
            source = repository.get_branch(from_branch)
            sha = source.commit.sha
            
            # 创建分支
            repository.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sha)
            
            return True, f"✅ 分支 `{branch_name}` 已创建（基于 {from_branch}）"
            
        except GithubException as e:
            return False, f"❌ 创建分支失败: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 错误: {str(e)}"
    
    def delete_branch(self, owner: str, repo: str, branch_name: str) -> Tuple[bool, str]:
        """删除分支"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            if branch_name in ["main", "master"]:
                return False, "❌ 不能删除默认分支"
            
            ref = repository.get_git_ref(f"heads/{branch_name}")
            ref.delete()
            
            return True, f"✅ 分支 `{branch_name}` 已删除"
            
        except GithubException as e:
            return False, f"❌ 删除分支失败: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 错误: {str(e)}"
    
    def protect_branch(self, owner: str, repo: str, branch_name: str,
                       required_status_checks: Dict = None,
                       enforce_admin: bool = True,
                       require_reviews: bool = True,
                       dismiss_stale_reviews: bool = True) -> Tuple[bool, str]:
        """保护分支"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            branch = repository.get_branch(branch_name)
            
            # 启用分支保护
            branch.edit_protection()
            
            # 设置要求状态检查
            if required_status_checks:
                branch.get_protection().get_required_status_checks().edit(
                    strict=required_status_checks.get('strict', False),
                    contexts=required_status_checks.get('contexts', [])
                )
            
            # 设置要求 reviews
            if require_reviews:
                protection = branch.get_protection()
                protection.get_required_pull_request_reviews().edit(
                    dismiss_stale_reviews=dismiss_stale_reviews
                )
            
            # 允许管理员绕过
            if enforce_admin:
                branch.get_protection().edit(enforce_admins=True)
            
            return True, f"✅ 分支 `{branch_name}` 已保护"
            
        except Exception as e:
            return False, f"❌ 保护分支失败: {str(e)}"
    
    # ==================== 文件操作 ====================
    
    def get_file_content(self, owner: str, repo: str, path: str,
                         branch: str = None) -> Tuple[bool, str, bytes]:
        """获取文件内容"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            contents = repository.get_contents(path, ref=branch)
            
            if isinstance(contents, list):
                return False, "❌ 这是一个目录", b""
            
            import base64
            content = base64.b64decode(contents.content)
            
            return True, "✅ 文件获取成功", content
            
        except GithubException as e:
            if e.status == 404:
                return False, "❌ 文件不存在", b""
            return False, f"❌ 获取失败: {e.data.get('message', str(e))}", b""
        except Exception as e:
            return False, f"❌ 错误: {str(e)}", b""
    
    def update_file(self, owner: str, repo: str, path: str,
                    content: str, message: str, branch: str = "main",
                    sha: str = None) -> Tuple[bool, str]:
        """更新或创建文件"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            # 如果没有 SHA，尝试获取现有文件
            if not sha:
                try:
                    existing = repository.get_contents(path, ref=branch)
                    sha = existing.sha
                except:
                    pass  # 文件不存在，将创建新文件
            
            # 创建或更新文件
            if sha:
                repository.update_file(path, message, content, sha, branch=branch)
            else:
                repository.create_file(path, message, content, branch=branch)
            
            return True, f"✅ 文件已更新: {path}"
            
        except GithubException as e:
            return False, f"❌ 更新失败: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 错误: {str(e)}"
    
    def delete_file(self, owner: str, repo: str, path: str,
                    message: str, branch: str = "main") -> Tuple[bool, str]:
        """删除文件"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            contents = repository.get_contents(path, ref=branch)
            sha = contents.sha
            
            repository.delete_file(path, message, sha, branch=branch)
            
            return True, f"✅ 文件已删除: {path}"
            
        except GithubException as e:
            return False, f"❌ 删除失败: {e.data.get('message', str(e))}"
        except Exception as e:
            return False, f"❌ 错误: {str(e)}"
    
    # ==================== Commit 操作 ====================
    
    def get_commits(self, owner: str, repo: str, 
                    branch: str = None, path: str = None,
                    since: datetime = None, until: datetime = None,
                    limit: int = 50) -> List[CommitInfo]:
        """获取提交历史"""
        commits = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            kwargs = {'per_page': 100}
            if branch:
                kwargs['sha'] = branch
            if path:
                kwargs['path'] = path
            if since:
                kwargs['since'] = since
            if until:
                kwargs['until'] = until
            
            commit_count = 0
            for commit in repository.get_commits(**kwargs):
                if commit_count >= limit:
                    break
                
                commits.append(CommitInfo(
                    sha=commit.sha[:7],
                    message=commit.commit.message.split('\n')[0] if commit.commit else "",
                    author=commit.commit.author.name if commit.commit and commit.commit.author else "unknown",
                    date=commit.commit.author.date if commit.commit else datetime.now(),
                    url=commit.html_url
                ))
                commit_count += 1
                
        except Exception as e:
            print(f"获取 commits 失败: {e}")
        
        return commits
    
    def get_commit_details(self, owner: str, repo: str, sha: str) -> Dict:
        """获取提交详情"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            commit = repository.get_commit(sha)
            
            return {
                'sha': commit.sha,
                'message': commit.commit.message,
                'author': {
                    'name': commit.commit.author.name,
                    'email': commit.commit.author.email,
                    'date': commit.commit.author.date.isoformat()
                },
                'committer': {
                    'name': commit.commit.committer.name,
                    'email': commit.commit.committer.email,
                    'date': commit.commit.committer.date.isoformat()
                },
                'parents': [p.sha[:7] for p in commit.parents],
                'stats': {
                    'additions': commit.stats.additions,
                    'deletions': commit.stats.deletions,
                    'total': commit.stats.total
                },
                'files': [
                    {
                        'filename': f.filename,
                        'status': f.status,
                        'additions': f.additions,
                        'deletions': f.deletions
                    }
                    for f in commit.get_files()
                ],
                'html_url': commit.html_url
            }
            
        except Exception as e:
            print(f"获取 commit 详情失败: {e}")
            return {}
    
    # ==================== 状态检查 ====================
    
    def get_commit_statuses(self, owner: str, repo: str, 
                            ref: str) -> List[CommitStatus]:
        """获取 commit 的 statuses"""
        statuses = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            for status in repository.get_commit(ref).get_statuses():
                statuses.append(CommitStatus(
                    state=status.state,
                    description=status.description,
                    target_url=status.target_url or "",
                    context=status.context
                ))
                
        except Exception as e:
            print(f"获取 statuses 失败: {e}")
        
        return statuses
    
    def get_check_runs(self, owner: str, repo: str, 
                       ref: str) -> List[CheckRun]:
        """获取 commit 的 check runs"""
        checks = []
        
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            for run in repository.get_commit(ref).get_check_runs():
                checks.append(CheckRun(
                    id=run.id,
                    name=run.name,
                    status=run.status,
                    conclusion=run.conclusion,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    html_url=run.html_url
                ))
                
        except Exception as e:
            print(f"获取 check runs 失败: {e}")
        
        return checks
    
    def create_status(self, owner: str, repo: str, sha: str,
                      state: str, description: str,
                      target_url: str = None, context: str = "default") -> Tuple[bool, str]:
        """创建 commit status"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            
            repository.get_commit(sha).create_status(
                state=state,
                description=description[:140],  # GitHub 限制
                target_url=target_url,
                context=context
            )
            
            return True, f"✅ 状态已创建: {state}"
            
        except Exception as e:
            return False, f"❌ 创建状态失败: {str(e)}"
    
    # ==================== 搜索 ====================
    
    def search_repos(self, query: str, limit: int = 30, 
                     sort: str = None, order: str = "desc") -> List[Dict]:
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
    
    def search_code(self, query: str, limit: int = 30) -> List[Dict]:
        """搜索代码"""
        results = []
        
        try:
            for code in self.github.search_code(query, per_page=min(limit, 100)):
                results.append({
                    'name': code.name,
                    'path': code.path,
                    'repository': code.repository.full_name,
                    'html_url': code.html_url,
                    'text_matches': code.text_matches
                })
                
        except Exception as e:
            print(f"搜索代码失败: {e}")
        
        return results
    
    # ==================== Gist 操作 ====================
    
    def create_gist(self, files: Dict[str, str],
                    description: str = "",
                    public: bool = False) -> Tuple[bool, str]:
        """创建 Gist"""
        try:
            user = self.github.get_user()
            
            gist = user.create_gist(
                public=public,
                description=description,
                files=files
            )
            
            return True, f"✅ Gist 创建成功！\n{gist.html_url}"
            
        except Exception as e:
            return False, f"❌ 创建 Gist 失败: {str(e)}"
    
    # ==================== Star 操作 ====================
    
    def star_repo(self, owner: str, repo: str) -> Tuple[bool, str]:
        """Star 仓库"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            repository.edit(has_watcher=True)  # PyGithub 的 star 方式
            
            return True, f"⭐ 已 Star {owner}/{repo}"
            
        except Exception as e:
            return False, f"❌ Star 失败: {str(e)}"
    
    def unstar_repo(self, owner: str, repo: str) -> Tuple[bool, str]:
        """取消 Star"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            repository.edit(has_watcher=False)
            
            return True, f"👎 已取消 Star {owner}/{repo}"
            
        except Exception as e:
            return False, f"❌ 取消 Star 失败: {str(e)}"
    
    def is_starred(self, owner: str, repo: str) -> bool:
        """检查是否已 Star"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            return repository.has_in_watchers
        except:
            return False


from enum import Enum
