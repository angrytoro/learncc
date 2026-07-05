# learncc — 从零构建 Claude Code 风格的 AI 编程 Agent

> 用 Python 一步步手写一个能读文件、改代码、跑命令的 AI 编程 Agent。

`learncc`（Claude Code 学习）是一个渐进式教程项目。它把一个真实可运行的 AI 编程 Agent 拆成 **5 节课**，每节课在前一节的基础上只新增一个核心概念。每节课都是一个**自包含的 `code.py`**，可以独立运行，无需依赖其它课程。

---

## ✨ 项目特点

- **5 节渐进式课程** —— 从一个 50 行的 Agent 循环，逐步长出工具、权限、钩子、规划。
- **每节可独立运行** —— 每个 `sNN_*/code.py` 自带全部上下文，单文件就能跑。
- **基于 Anthropic SDK** —— 直接调 `client.messages.create(...)`，看清工具调用（tool use）的本质。
- **支持任意 Anthropic 兼容端点** —— 官方 API、阿里云 DashScope、其它兼容服务都行，只需改 `.env`。

---

## 📚 课程目录

| 节 | 目录 | 这节课学到什么 | 入口文件 |
|----|------|---------------|---------|
| **s01** | `s01_agent_loop` | Agent 的核心秘密：`while stop_reason == "tool_use"` 循环 + 单个 `bash` 工具 | `code.py` |
| **s02** | `s02_tool_use` | 新增 `read_file` / `write_file` / `edit_file` / `glob` 四个工具，用 `TOOL_HANDLERS` 分发，加 `safe_path()` 工作区沙箱 | `code.py` |
| **s03** | `s03_permission` | 三段式权限管线：硬黑名单 → 规则匹配 → 交互式 `Allow? [y/N]` 确认 | `code.py` |
| **s04** | `s04_hooks` | 把权限重构成通用 Hook 注册表，覆盖 4 个生命周期事件（`UserPromptSubmit` / `PreToolUse` / `PostToolUse` / `Stop`） | `code.py` |
| **s05** | `s05_todo_write` | 新增 `todo_write` 规划工具 + 连续 3 轮没更新待办就提醒的 "nag" 机制 | `copy.py`（🚧 进行中） |

> 每个课程文件里都有 `# NEW in sNN` 与 `# FROM s0X (unchanged)` 注释，能一眼看出这一节新增了哪些代码。

---

## 📋 环境要求

- **Python ≥ 3.12**（仓库已用 `.python-version` 锁定 `3.12`）
- 包管理器二选一：
  - **[uv](https://docs.astral.sh/uv/)**（推荐，速度快、自带虚拟环境管理）
  - 或系统自带的 `pip` + `venv`

你还需要一个 **Anthropic 兼容的 API Key**（官方 Anthropic、阿里云 DashScope 等均可）。

---

## 🚀 快速开始（uv，推荐）

### 1. 安装 uv（一次性）

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 克隆仓库

```bash
git clone https://github.com/angrytoro/learncc.git
cd learncc
```

### 3. 安装依赖

```bash
uv sync        # 会按 .python-version 创建 .venv 并装好 anthropic / python-dotenv / httpx[socks]
```

### 4. 配置环境变量

```bash
# macOS / Linux
cp .env.example .env

# Windows (cmd)
copy .env.example .env
```

然后编辑 `.env`，填入你的 `ANTHROPIC_API_KEY`（详见下方[配置说明](#%EF%B8%8F-配置说明env)）。

### 5. 运行第一节课

```bash
uv run python s01_agent_loop/code.py
```

---

## 🐍 快速开始（pip / venv 备选）

不想装 uv 也完全可以，用标准库 `venv` + `pip`：

```bash
# 1. 克隆
git clone https://github.com/angrytoro/learncc.git
cd learncc

# 2. 建虚拟环境并激活
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows (cmd)

# 3. 装依赖
pip install anthropic python-dotenv httpx[socks]

# 4. 配置（同上）
cp .env.example .env             # Windows: copy .env.example .env
#   编辑 .env 填入 ANTHROPIC_API_KEY

# 5. 运行
python s01_agent_loop/code.py
```

---

## ⚙️ 配置说明（`.env`）

所有配置通过仓库根目录的 `.env` 文件读取（由 `python-dotenv` 加载）。模板见 `.env.example`：

| 变量 | 默认值（`.env.example`） | 说明 |
|------|------------------------|------|
| `ANTHROPIC_BASE_URL` | `https://dashscope.aliyuncs.com/apps/anthropic` | Anthropic 兼容的服务端点。默认指向**阿里云 DashScope**。 |
| `ANTHROPIC_API_KEY` | `your-anthropic-api-key` | 你的 API Key。**必填。** |
| `MODEL` | `deepseek-v4-flash` | 调用的模型名。默认配合 DashScope 用的是 deepseek 模型。 |

### 想换成 Anthropic 官方 API？

把 `.env` 改成：

```dotenv
# 注释或删掉 ANTHROPIC_BASE_URL 这一行（用官方默认端点）
ANTHROPIC_API_KEY=sk-ant-...        # 你的官方 key
MODEL=claude-sonnet-4-5             # 任意官方模型名
```

> 当 `ANTHROPIC_BASE_URL` 存在时，代码会自动清空环境里的 `ANTHROPIC_AUTH_TOKEN`，避免冲突。

---

## 🎮 每节课怎么玩

每节课都是一个**交互式 REPL**，启动后长这样：

```
s01: Agent Loop
输入问题，回车发送。输入 q 退出。

s01 >> 帮我看看当前目录有哪些文件
$ ls -la
...
s01 >> q
```

- 在 `sNN >> ` 提示符后输入你的需求，回车发送。
- 输入 `q` 或 `exit` 退出。
- 模型调用的每条工具命令会用黄色打印出来，方便你观察 Agent 在做什么。

**推荐阅读顺序**：s01 → s02 → s03 → s04，对照每节文件里的 `# NEW in sNN` 注释，看新增的那一小段代码如何带来新能力。

---

## ❓ 常见问题（FAQ）

**Q：报错提到缺少 `socksio` / 代理相关错误？**
你设置了 `HTTP_PROXY` / `HTTPS_PROXY` 但没装 SOCKS 支持。运行：

```bash
pip install httpx[socks]
# 或 uv 环境： uv add "httpx[socks]"
```

**Q：macOS 下中文输入时退格乱码？**
代码里已经内置了 `readline` 修复（`bind-tty-special-chars` 等四行），无需你做任何事。

**Q：某些 shell 命令被拦截，提示 `Dangerous command detected`？**
`run_bash` 硬封禁了一批高危命令：`rm -rf /`、`sudo`、`shutdown`、`reboot`、`> /dev/`。这是安全护栏，无法绕过。

**Q：s05 跑不通 / 文件叫 `copy.py`？**
s05（`todo_write`）**仍在开发中**，目前只有 `s05_todo_write/copy.py` 且实现尚不完整。可先学完 s01–s04。

---

## 📁 项目结构

```
learncc/
├── .env.example          # 环境变量模板（BASE_URL / API_KEY / MODEL）
├── .python-version       # 锁定 Python 3.12
├── pyproject.toml        # uv 项目清单 + 依赖声明
├── uv.lock               # 依赖锁文件
├── README.md             # 本文件
├── main.py               # uv init 生成的脚手架（"Hello from learncc"），与课程无关，可忽略
├── s01_agent_loop/
│   └── code.py           # 第 1 课：Agent 循环
├── s02_tool_use/
│   └── code.py           # 第 2 课：多工具与沙箱
├── s03_permission/
│   └── code.py           # 第 3 课：权限管线
├── s04_hooks/
│   └── code.py           # 第 4 课：Hook 系统
└── s05_todo_write/
    └── copy.py           # 第 5 课：todo_write（进行中）
```

> 命名规则：`s` = step（步骤），`NN` = 两位序号，`<topic>` = 该节主题。目录名即课程名。

---

## 📝 说明

本项目仅用于**学习与教学**，帮助你理解 Claude Code 这类 AI 编程 Agent 的工作原理。每节课都是最小可运行实现，故意保持精简，便于阅读和改造。
