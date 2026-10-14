# GitHub 仓库监控 Telegram 机器人 V3

一个功能强大的 Telegram 机器人，支持 **按钮式交互**、GitHub Trending、热门项目追踪和丰富的 GitHub 操作功能。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-green.svg)
![GitHub](https://img.shields.io/badge/GitHub-API-green.svg)

---

## ✨ 功能特性

### 🎛️ 按钮式交互（核心功能）

所有功能都可通过**点击按钮**操作，无需记忆命令！

```
发送 /start 后显示完整按钮菜单
```

### 🔥 Trending & 热门项目

| 功能 | 描述 |
|------|------|
| 📊 Trending | 查看 GitHub 热门项目 |
| 🔥 热门排行 | 今日最热项目 Top 10/25 |
| 🚀 爆发检测 | 发现爆发式增长项目（如 REA） |
| 📈 Stars 追踪 | 追踪项目 Stars 增长 |
| 📉 历史图表 | 30天 Stars 增长 ASCII 图表 |

### 📦 仓库监控

| 功能 | 描述 |
|------|------|
| ⭐ Stars | 实时跟踪 star 变化 |
| 🍴 Forks | 监控 fork 增减 |
| 📝 Commits | 跟踪最新代码提交 |
| 🔀 PRs | 监控 PR 打开/合并/关闭 |
| 🐛 Issues | 跟踪 Issue |

### ⚡ 高级功能（需绑定 GitHub）

| 功能 | 描述 |
|------|------|
| 🍴 Fork | 一键 Fork 仓库 |
| 🚀 Actions | 触发 GitHub Actions |
| 🔀 PR | 创建 Pull Request |
| 🌿 分支 | 创建和删除分支 |

---

## 🚀 快速开始

### 1. 获取 Telegram Bot Token

1. 在 Telegram 搜索 **@BotFather**
2. 发送 `/newbot`
3. 按提示设置机器人名称和用户名
4. 复制 Bot Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2. 获取 GitHub Token 并配置权限

#### 步骤一：创建 Personal Access Token

1. 访问 [GitHub Settings > Personal access tokens](https://github.com/settings/tokens)
2. 点击 **Generate new token (classic)**
3. 设置 Token 名称（如：`telegram-bot`）
4. 设置过期时间（建议 30-90 天）

#### 步骤二：勾选所需权限

根据您需要的功能，勾选以下权限：

##### 📌 基础功能（仅查看）

只需勾选以下权限即可使用 Trending、搜索、查看仓库：

| 权限 | 作用域 | 说明 |
|------|--------|------|
| ✅ **public_repo** | 公共仓库访问 | 查看公开仓库信息（必选） |

##### ⚡ 高级功能（需要写操作）

如果需要 Fork、创建 PR、分支、Star 等操作，额外勾选：

| 权限 | 作用域 | 说明 |
|------|--------|------|
| ✅ **repo** | 完全控制私有仓库 | 完全控制所有仓库（完整权限） |
| 或 | 或 | 或 |
| ✅ **public_repo** | 公共仓库 | 只操作公开仓库 |
| ✅ **repo:status** | 仓库状态 | 读取仓库状态 |
| ✅ **repo:deployment** | 部署 | 访问部署状态 |
| ✅ **workflow** | GitHub Actions | 管理 Actions |

##### 🚀 Actions 相关功能

如果需要触发 Workflows：

| 权限 | 作用域 | 说明 |
|------|--------|------|
| ✅ **workflow** | GitHub Actions | 触发和管理 Actions |

##### 📋 推荐配置

**推荐方案（最小权限）：**
```
✅ public_repo          // 查看和操作公开仓库
✅ repo:status          // 读取仓库状态
✅ repo:deployment      // 部署状态
✅ workflow             // Actions 操作
```

**完整权限方案：**
```
✅ repo (Full control of private repositories)
// 允许所有仓库操作
```

#### 步骤三：配置 Token 环境变量

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置

创建 `.env` 文件：

```env
# Telegram Bot Token（必填）
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# GitHub Token（必填）- 推荐使用只有 public_repo 权限的 Token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# 检查间隔（分钟）- 可选，默认 5
CHECK_INTERVAL=5

# OAuth 配置（可选）- 用于 GitHub 账号绑定
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
```

### 5. 启动

```bash
python main.py
```

### 6. 使用

1. 在 Telegram 搜索您的机器人
2. 发送 `/start`
3. **点击按钮**开始使用！

---

## 🎛️ 按钮菜单

发送 `/start` 后显示完整按钮菜单：

```
┌─────────────────────────────────────┐
│  🤖 GitHub 监控机器人 V3            │
├─────────────────────────────────────┤
│  🔥 Trending    📊 热门排行         │
│  🚀 爆发项目    📈 Stars追踪         │
├─────────────────────────────────────┤
│  ➕ 添加监控    📋 我的仓库          │
├─────────────────────────────────────┤
│  🍴 Fork        🔀 PR操作           │
│  🚀 Actions     🌿 分支              │
├─────────────────────────────────────┤
│  🔗 GitHub账号  ⚙️ 设置             │
│  🔍 搜索       📖 帮助              │
└─────────────────────────────────────┘
```

### 📋 子菜单按钮

**Trending 菜单：**
- 🐍 Python / 🟨 JavaScript / 🔵 TypeScript
- 🐹 Go / 🦀 Rust / ☕ Java
- 🌐 所有语言 / 📅 本周 / 📅 本月

**Stars 追踪菜单：**
- ➕ 添加追踪 / 📋 我的追踪
- 🔥 最热追踪 / 📈 增长排行

**仓库操作菜单：**
- 📊 详情 / 📈 Stars图表
- 🍴 Fork / ⭐ Star
- 🔍 类似项目 / 📝 最近活动

---

## 🤖 命令列表

虽然有按钮，但也支持命令：

### 🔥 Trending

```
/trending              # 所有语言 Trending
/trending python       # Python Trending
/hot                   # 今日最热
/exploding 300         # 爆发项目（阈值300）
/track owner/repo      # 追踪 Stars
/stars owner/repo      # Stars 增长图表
/similar owner/repo    # 搜索类似项目
/rank python           # Python 排行榜
```

### 📦 仓库

```
/add <owner/repo>     # 添加监控
/list                  # 查看列表
/watch <owner/repo>    # 仓库详情
/recent <owner/repo>   # 最近活动
```

### ⚡ 高级

```
/fork <owner/repo>    # Fork 仓库
/workflows <owner/repo> # 查看 Workflows
/run <owner/repo> <name> # 触发 Workflow
/pr <owner/repo>       # 创建 PR
/branch <owner/repo> <name> # 创建分支
```

### 🔍 搜索

```
# 直接发送关键词搜索（新增！）
红队
red team
python telegram bot
```

---

## 🎯 使用示例

### 按钮操作流程

1. **发现热门项目**
   - 发送 `/start`
   - 点击 `🔥 Trending`
   - 选择语言（如 Python）
   - 查看结果

2. **追踪 Stars**
   - 发送 `/start`
   - 点击 `📈 Stars追踪`
   - 点击 `➕ 添加追踪`
   - 输入 `cursor/cursor`

3. **一键 Fork**
   - 发送 `/start`
   - 点击 `🍴 Fork`
   - 输入仓库名

### 命令操作

```
/hot                    # 今日最热
/exploding 500         # 爆发项目
/track cursor/cursor   # 追踪 Stars
/stars cursor/cursor   # 查看图表
```

### 直接搜索

直接在聊天框输入关键词搜索：

```
python                 # 搜索 Python 项目
红队                   # 搜索红队相关
red team tools        # 搜索红队工具
react                 # 搜索 React
```

---

## 📁 项目结构

```
github-monitor-bot/
├── main.py                    # 主程序入口
├── bot_extended.py            # 机器人核心
├── menu_system.py             # 按钮菜单系统 ⭐新
├── menu_handler.py            # 菜单处理 ⭐新
├── commands_trending.py       # Trending 命令
├── commands_extended.py       # 扩展命令
├── github_trending.py         # Trending 监控
├── github_advanced.py         # 高级操作
├── github_monitor.py          # 基础监控
├── github_oauth.py            # OAuth
├── database_extended.py       # 扩展数据库
├── scheduler.py               # 定时任务
├── config.py                  # 配置
├── models.py                  # 数据模型
├── keyboards.py               # 键盘定义
├── keyboards_extended.py      # 扩展键盘
├── requirements.txt           # 依赖
└── .env                       # 环境变量
```

---

## 🔧 配置选项

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `TELEGRAM_BOT_TOKEN` | - | Telegram Bot Token（**必填**） |
| `GITHUB_TOKEN` | - | GitHub Token（**必填**） |
| `CHECK_INTERVAL` | 5 | 检查间隔（分钟） |
| `GITHUB_CLIENT_ID` | - | OAuth App ID（可选） |
| `GITHUB_CLIENT_SECRET` | - | OAuth App Secret（可选） |

---

## 🔐 GitHub 权限详解

### 为什么需要 GitHub Token？

GitHub API 有速率限制：
- **未认证**：60 请求/小时
- **个人 Token**：5,000 请求/小时

Token 还用于识别用户身份和执行操作。

### 权限级别说明

| 权限级别 | 需要的 Scope | 可用功能 |
|---------|--------------|---------|
| **只读（推荐）** | `public_repo` | 查看 Trending、搜索、查看仓库信息 |
| **公开仓库操作** | `public_repo` + `workflow` | 以上功能 + Fork、Star、触发 Actions |
| **完全控制** | `repo` | 所有功能，包括私有仓库 |

### 安全建议

1. **使用最小权限**：只勾选必需的功能
2. **设置过期时间**：建议 30-90 天后过期
3. **定期轮换**：定期生成新 Token
4. **不要提交 Token**：确保 `.env` 在 `.gitignore` 中
5. **分开 Token**：可以为不同用途使用不同的 Token

### 常见问题

**Q: 提示 "Bad credentials"**
- 检查 Token 是否正确
- 检查 Token 是否过期
- 检查 Token 是否有 `public_repo` 权限

**Q: 提示 "Not Found"**
- 仓库可能不存在或不可见
- Token 没有访问该仓库的权限

**Q: 提示 "API rate limit exceeded"**
- Token 未正确配置
- 等待速率限制重置（通常 1 小时）

---

## 📝 功能权限对照表

| 功能 | 最低权限 | 说明 |
|------|---------|------|
| /trending | 无 Token | 公共 API |
| 搜索仓库 | `public_repo` | 基础搜索 |
| 查看仓库详情 | `public_repo` | 基本信息 |
| Fork 仓库 | `public_repo` | 公开仓库 |
| Star 仓库 | `public_repo` | 公开仓库 |
| 创建 PR | `public_repo` | 公开仓库 |
| 创建分支 | `public_repo` | 公开仓库 |
| 触发 Actions | `workflow` | 需要 workflow 权限 |
| 私有仓库操作 | `repo` | 完全控制 |

---

## 🔧 故障排除

### 机器人无响应

1. 检查 Telegram Bot Token 是否正确
2. 检查机器人是否已启动
3. 查看控制台日志

### GitHub API 错误

```bash
# 检查 Token 是否有效
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### 速率限制

```bash
# 查看当前限制
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```

---

## 📄 License

MIT License

---

## 🙏 鸣谢

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot 框架
- [PyGithub](https://github.com/PyGithub/PyGithub) - GitHub API 客户端
- [GitHub](https://github.com) - 提供 Trending 数据
