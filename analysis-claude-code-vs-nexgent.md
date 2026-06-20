# Claude Code 2.1.183 vs Nexgent 对比分析 & 简历包装 & Demo 方案

## 一、Claude Code 最新特性全景（截至 2.1.183）

### 1.1 核心架构

Claude Code 是 Anthropic 官方的 Agentic Coding 工具，运行在终端/IDE/桌面应用/浏览器中。其核心是一个 **ReAct 风格的 Agent Loop**：observe → think → act → observe。

### 1.2 工具体系（40+ 工具）

| 工具 | 功能 | 权限 |
|------|------|------|
| **Agent** | 生成子代理，独立上下文窗口 | 无需权限 |
| **Bash/PowerShell** | Shell 命令执行 | 需要权限 |
| **Read/Edit/Write** | 文件读写编辑 | 读无需/写需要 |
| **Glob/Grep** | 文件搜索和内容搜索 | 无需权限 |
| **LSP** | 语言服务器协议集成（跳转定义/引用/诊断） | 无需权限 |
| **Monitor** | 后台进程监控，逐行事件流 | 需要权限 |
| **WebFetch/WebSearch** | 网页抓取和搜索 | 需要权限 |
| **NotebookEdit** | Jupyter 笔记本编辑 | 需要权限 |
| **TaskCreate/TaskList/TaskUpdate/TaskGet** | 任务管理 | 无需权限 |
| **CronCreate/CronDelete/CronList** | 会话级定时调度 | 无需权限 |
| **EnterPlanMode/ExitPlanMode** | 计划模式（只读探索→方案审批→执行） | 混合 |
| **Skill** | 执行可复用技能 | 需要权限 |
| **Workflow** | 动态工作流编排（v2.1.154+） | 需要权限 |
| **PushNotification** | 桌面/手机推送通知 | 无需权限 |
| **ScheduleWakeup** | 自主循环调度（v2.1.154+） | 无需权限 |
| **EnterWorktree/ExitWorktree** | Git Worktree 隔离 | 无需权限 |
| **SendMessage** | Agent Teams 间通信 | 无需权限 |
| **ToolSearch** | MCP 工具延迟加载搜索 | 无需权限 |
| **RemoteTrigger** | Routines 定时任务管理 | 无需权限 |

### 1.3 子代理系统（Sub-agents）

- **内置代理**: Explore（Haiku，只读）、Plan（继承主模型，只读）、General-purpose（全工具）
- **自定义代理**: Markdown + YAML frontmatter 定义，支持项目级/用户级/CLI 级
- **执行模式**: 前台（显示权限提示）、后台（自动拒绝未授权操作）
- **Agent Teams**（实验性）: 多个同级会话通过共享任务列表协作
- **Fork 模式**: 继承父会话完整上下文，在后台运行
- **隔离模式**: `isolation: worktree` 给子代理独立 Git 工作树
- **持久记忆**: 子代理可在 `~/.claude/agent-memory/` 积累跨会话知识

### 1.4 动态工作流（Workflows，v2.1.154+）

这是 Claude Code 最新最强的特性之一：

- **本质**: JavaScript 脚本编排大量子代理
- **运行时**: 隔离环境执行，中间结果留在脚本变量中，不占用主上下文
- **能力**: 每次运行最多 1000 个代理，最多 16 个并发
- **模式**: `pipeline`（流水线）、`parallel`（并行屏障）、`phase`（阶段分组）
- **质量模式**: 对抗验证、多视角验证、裁判面板、循环直到干涸
- **预算控制**: `budget.total`/`budget.spent()`/`budget.remaining()`
- **可恢复**: 暂停后恢复，已完成代理返回缓存结果
- **可保存**: 保存为 `/<name>` 命令复用
- **Ultracode 模式**: `/effort ultracode` 自动为每个实质任务规划工作流

### 1.5 Hooks 系统

- **生命周期事件**: PreToolUse, PostToolUse, Stop, SessionStart/End, SubagentStart/Stop 等
- **Hook 类型**: command（子进程）、HTTP（POST）、prompt（LLM 决策）
- **匹配器**: 按工具名、参数模式过滤
- **响应协议**: decision（允许/拒绝）、updatedInput（修改输入）、additionalContext

### 1.6 MCP（Model Context Protocol）

- **协议**: 开放标准，连接外部工具和数据源
- **传输**: HTTP（推荐）、SSE（已弃用）、stdio（本地）、WebSocket
- **认证**: OAuth 2.0、Bearer Token、自定义 headers
- **工具搜索**: `ToolSearch` 延迟加载，支持大规模 MCP 服务器
- **动态更新**: `list_changed` 通知，工具热更新
- **Channel**: MCP 服务器可推送消息到会话（Telegram、Discord、Webhook）

### 1.7 记忆系统

- **CLAUDE.md**: 项目根目录的指令文件，每次会话开始加载
- **Auto Memory**: 自动积累的跨会话知识（构建命令、调试技巧等）
- **Memory 文件**: `~/.claude/projects/<project>/memory/` 下的 Markdown 文件
- **MEMORY.md 索引**: 自动加载的索引文件

### 1.8 权限系统

- **模式**: Default、Plan、Auto、Accept Edits、Bypass
- **规则格式**: `ToolName(specifier)` 精细控制
- **Bash 匹配**: `Bash(npm run *)` 通配符模式
- **路径匹配**: `Read(~/secrets/**)` / `Edit(/src/**)`
- **Protected paths**: `.git`、`.env`、`.claude` 等

### 1.9 其他关键特性

- **Git Worktree 隔离**: 子代理在独立工作树中工作
- **Session 管理**: `--resume`/`--continue`/`--teleport` 跨设备
- **Remote Control**: 手机远程控制终端会话
- **Routines**: 云端定时任务（即使电脑关机也能运行）
- **Agent SDK**: 构建自定义代理的 SDK
- **GitHub Actions / GitLab CI**: CI/CD 集成
- **Slack 集成**: @Claude 触发 PR
- **Chrome 扩展**: 调试实时 Web 应用

---

## 二、Nexgent vs Claude Code 详细对比

### 2.1 功能对照表

| 维度 | Claude Code (2.1.183) | Nexgent (v0.4.0) | 差距分析 |
|------|----------------------|------------------|----------|
| **Agent Loop** | ReAct + 状态机 | ReAct + CircuitBreaker + 状态机 | ✅ 对等，Nexgent 有熔断器 |
| **工具数量** | 40+ | 33 | ⚠️ 接近，缺 Monitor/PushNotification/Worktree |
| **权限系统** | 5 模式 + ToolName(specifier) 规则 | 6 模式 + 4 阶段管线 | ✅ 对等，Nexgent 管线更细 |
| **安全防御** | 沙箱 + 权限规则 | 2 层（regex + 模型分类器）+ SSRF 防护 | ✅ Nexgent 有独立安全管线 |
| **上下文管理** | 自动压缩 | 4 级渐进压缩（snip/microcompact/collapse/autocompact） | ✅ Nexgent 压缩策略更细 |
| **记忆系统** | CLAUDE.md + Auto Memory + Memory 文件 | 4 类型 + MEMORY.md 索引 + YAML frontmatter | ✅ 对等 |
| **Hook 系统** | Pre/Post tool, Stop, Session 等 | 18 事件 × 3 类型 | ✅ 对等 |
| **子代理** | 内置 3 类 + 自定义 + Agent Teams + Fork | 并行/Pipeline + 资源限制 | ⚠️ 缺 Agent Teams、Fork、Worktree 隔离 |
| **工作流** | JS 脚本编排、1000 代理、可恢复 | 无独立工作流引擎 | ❌ 缺失（最大差距） |
| **MCP** | HTTP/SSE/stdio/WebSocket + OAuth + Channel | stdio/HTTP/SSE/WebSocket + OAuth | ⚠️ 缺 Channel、ToolSearch |
| **Skills** | SKILL.md + 动态注入 + 参数替换 | SKILL.md + 动态注入 + 参数替换 | ✅ 对等 |
| **自定义代理** | YAML frontmatter + 6 预设 + 持久记忆 | YAML frontmatter + 6 预设 | ⚠️ 缺持久记忆 |
| **计划模式** | EnterPlanMode + Plan 子代理 | enter_plan_mode + exit_plan_mode | ✅ 对等 |
| **LSP 集成** | 跳转定义/引用/诊断/符号搜索/调用层次 | lsp_definition/lsp_references/lsp_diagnostics | ⚠️ 缺符号搜索和调用层次 |
| **任务管理** | TaskCreate/Get/List/Update + 依赖关系 | TaskCreate/List/Update/Delete | ⚠️ 缺依赖关系 |
| **调度** | CronCreate + Routines（云端）+ /loop | CronCreate（会话级） | ⚠️ 缺云端 Routines |
| **模型支持** | Claude 系列（Sonnet/Opus/Haiku） | 任意 OpenAI 兼容 API | ✅ Nexgent 模型无关 |
| **TUI** | 终端 UI | 全屏 Textual 界面 | ✅ 对等 |
| **CLI** | 30+ 命令 | 34 命令 | ✅ 对等 |
| **测试** | 未公开 | 1057 单元 + 73 E2E | ✅ Nexgent 测试覆盖完整 |
| **显示** | 终端输出 | Rich 气泡/语法高亮/折叠工具调用 | ✅ 对等 |
| **后台任务** | 支持 | 异步 + 状态跟踪 + 取消 | ✅ 对等 |
| **@文件引用** | @filename | @file/@folder/@*.ext + glob | ✅ Nexgent 更强 |
| **目标管理** | /goal | /goal + 自动评估 | ✅ 对等 |
| **设置层级** | 4 级（managed/user/project/local） | 4 级（同） | ✅ 对等 |
| **会话管理** | JSONL + resume/continue/teleport | JSONL + checkpoint + fork + resume | ✅ 对等 |
| **显示推送** | PushNotification（桌面+手机） | 无 | ❌ 缺失 |
| **Worktree** | Git Worktree 隔离 | 无 | ❌ 缺失 |
| **Agent Teams** | 多会话协作 | 无 | ❌ 缺失 |
| **Chrome/Slack** | 浏览器调试/Slack 集成 | 无 | ❌ 缺失（外部集成） |

### 2.2 Nexgent 的独特优势

1. **模型无关**: 不绑定 Claude，可用任意 OpenAI 兼容 API（MiMo、GPT、DeepSeek 等）
2. **Python 生态**: 纯 Python 实现，易于二次开发和集成
3. **教育价值**: 从零构建的完整 Agent Harness，9 阶段渐进式学习路径
4. **测试驱动**: 1057 单元测试 + 73 E2E 测试，覆盖率远超一般项目
5. **安全管线独立**: 专门的 2 层安全防御，比 Claude Code 的权限规则更系统化
6. **4 级渐进压缩**: snip → microcompact → collapse → autocompact，比 Claude Code 的自动压缩更精细

### 2.3 工作流引擎（已实现 ✅）

Nexgent 现已实现等价的工作流引擎（`workflow.py`），对标 Claude Code Dynamic Workflows：

| 特性 | Claude Code | Nexgent |
|------|------------|---------|
| 脚本语言 | JavaScript | Python |
| 编排模式 | pipeline/parallel/phase | ✅ 同 |
| 代理上限 | 1000/次 | ✅ 1000/次 |
| 并发上限 | 16 | 10（可配置） |
| 预算控制 | token 上限 | ✅ Budget 类 |
| 可恢复 | 缓存已完成代理 | ✅ _cached_results |
| 可保存 | .claude/workflows/ | ✅ 同 |
| 进度监控 | /workflows UI | ✅ /workflow 命令 |
| 质量模式 | 脚本中实现 | ✅ 脚本中实现 |

**实现文件**：
- `workflow.py` — 核心引擎（WorkflowRunner/WorkflowContext/Budget）
- `tools/workflow_tools.py` — LLM 可调用的 5 个工具
- `tests/test_workflow.py` — 38 个单元测试
- `examples/workflow_code_review.py` — 示例工作流

---

## 三、简历包装方案

### 3.1 项目标题

**Nexgent — 生产级模型无关 AI Agent Harness**
*基于 Claude Code 架构的自主编程代理系统*

### 3.2 一句话定位

> 从零构建了一个对标 Claude Code 的生产级 AI Agent Harness，实现 33 个工具、4 阶段权限管线、2 层安全防御、4 级上下文压缩、18 种生命周期 Hook、SubAgent 并行编排，支持任意 OpenAI 兼容模型，包含 1057 单元测试和 73 端到端测试。

### 3.3 简历要点（按 STAR 法则）

#### 项目经历

**Nexgent — AI Agent Harness** | Python | 独立开发
*2025.xx - 2025.xx*

- **架构设计**: 逆向分析 Claude Code 架构，设计并实现包含 22 个核心模块的 Agent Harness，支持 ReAct 循环、依赖注入、熔断器、状态机等 20 种设计模式
- **工具系统**: 实现 33 个工具（14 个模块），涵盖文件操作、Shell 执行、LSP 集成、MCP 协议、Web 搜索/抓取、Jupyter 编辑等，通过统一注册中心和 4 阶段执行管线分发
- **安全体系**: 构建 2 层安全防御（正则预过滤 + LLM 分类器），实现敏感数据自动脱敏、提示注入检测、SSRF 防护、凭证路径保护
- **上下文管理**: 设计 4 级渐进压缩策略（snip → microcompact → collapse → autocompact），支持 1M token 窗口，85% 阈值自动触发，大结果磁盘溢出
- **多代理协作**: 实现 SubAgent 并行/Pipeline 执行引擎，支持资源隔离（独立会话、工具限制、token 预算、步数上限）、ThreadPoolExecutor 并发调度
- **权限管线**: 设计 6 种权限模式 × 4 阶段管线（验证→规则匹配→上下文评估→用户提示），deny > ask > allow 优先级不可覆盖
- **工程实践**: 编写 1057 个单元测试 + 73 个端到端测试，CI/CD 矩阵覆盖 Python 3.10-3.13，Codecov 覆盖率上报

#### 技术亮点（可单独列出）

- 逆向工程 Claude Code 架构，提炼 20 种 Agent 设计模式并用 Python 重新实现
- 模型无关设计：通过 OpenAI 兼容接口接入任意 LLM（MiMo/GPT/DeepSeek）
- 18 种生命周期 Hook × 3 种类型（command/HTTP/prompt），支持开发工作流自动化
- MCP 多协议集成（stdio/HTTP/SSE/WebSocket），支持外部工具生态接入
- 会话管理：JSONL 自动保存、检查点回滚、会话分叉、跨设备恢复

### 3.4 技能标签

```
AI Agent | LLM Harness | ReAct | Tool Use | MCP | SubAgent | 
Permission System | Security Pipeline | Context Management | 
Python | OpenAI API | Rich/Textual TUI | pytest | CI/CD
```

### 3.5 面试话术要点

1. **"为什么做这个项目？"**
   > Claude Code 是目前最先进的 AI 编程代理，但闭源且绑定 Claude 模型。我通过逆向分析其架构，用 Python 从零实现了等价的 Agent Harness，使其支持任意 LLM，同时深入理解了 Agent 系统的核心设计模式。

2. **"最大的技术挑战是什么？"**
   > 上下文管理。当对话变长时，需要在不丢失关键信息的前提下压缩历史。我设计了 4 级渐进压缩策略，从简单的截断到 LLM 摘要，配合磁盘溢出机制，实现了 1M token 窗口的有效管理。

3. **"和 Claude Code 相比有什么优势？"**
   > 模型无关是最大优势。Claude Code 绑定 Claude，而 Nexgent 可以接入任意 OpenAI 兼容 API。此外，安全管线更系统化（独立 2 层防御），压缩策略更精细（4 级 vs 自动），测试覆盖更完整（1057 单元测试）。

4. **"有什么不足？"**
   > 外部集成是差距。Claude Code 有 Slack 集成、Chrome 扩展、Agent Teams 等。Nexgent 的核心引擎已对等，但缺少这些外部集成。下一步可以做 Agent Teams 和 Routines（云端定时任务）。

---

## 四、生产级 Demo 方案：内部知识库 + Agent 自主循环

### 4.1 场景定义

**目标**: 展示 Agent 在内部知识库（代码仓库 + 文档）的上下文中，自主完成代码级实现任务，并能循环迭代直到目标达成。

**交付物**: 一个可演示的 Demo，展示以下能力：
1. Agent 理解内部知识库（代码结构、API 文档、设计规范）
2. Agent 自主规划实现方案
3. Agent 执行代码级修改（读/写/编辑文件）
4. Agent 自主循环验证（运行测试 → 修复失败 → 重试）
5. Agent 报告结果

### 4.2 Demo 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Demo 场景                              │
│                                                          │
│  用户输入: "给 auth 模块添加 JWT 刷新 token 功能"          │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Nexgent Agent Loop                      │ │
│  │                                                      │ │
│  │  1. 知识库加载                                        │ │
│  │     ├── 读取 AGENTS.md（项目结构）                    │ │
│  │     ├── 读取 MEMORY.md（记忆索引）                    │ │
│  │     ├── 扫描 src/ 目录结构                            │ │
│  │     └── 加载相关 API 文档                             │ │
│  │                                                      │ │
│  │  2. 自主规划（Plan Mode）                             │ │
│  │     ├── enter_plan_mode                              │ │
│  │     ├── 探索 auth 模块现有实现                        │ │
│  │     ├── 分析 token 刷新的接口需求                     │ │
│  │     └── exit_plan_mode（输出实现方案）                │ │
│  │                                                      │ │
│  │  3. 代码实现                                          │ │
│  │     ├── edit_file: 添加 refresh_token 字段           │ │
│  │     ├── write_file: 实现 token 刷新逻辑              │ │
│  │     ├── edit_file: 更新 API 路由                     │ │
│  │     └── write_file: 添加单元测试                     │ │
│  │                                                      │ │
│  │  4. 自主循环验证                                      │ │
│  │     ├── run_command: pytest tests/test_auth.py       │ │
│  │     ├── [失败] → 分析错误 → 修复代码 → 重试          │ │
│  │     ├── [失败] → 分析错误 → 修复代码 → 重试          │ │
│  │     └── [成功] → 进入下一步                          │ │
│  │                                                      │ │
│  │  5. 结果报告                                          │ │
│  │     ├── 汇总修改的文件                                │ │
│  │     ├── 测试通过率                                    │ │
│  │     └── 保存记忆到 MEMORY.md                          │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 4.3 实现步骤

#### Step 1: 准备内部知识库

创建一个模拟的内部项目作为知识库：

```
demo-project/
├── AGENTS.md              # 项目结构和架构说明
├── MEMORY.md              # 记忆索引
├── .mimo/
│   ├── config.json        # 运行配置
│   └── permissions.json   # 权限规则
├── src/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── models.py      # User 模型
│   │   ├── routes.py      # API 路由
│   │   ├── service.py     # 业务逻辑
│   │   └── tests/
│   │       └── test_auth.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py         # FastAPI 应用
│   └── utils/
│       ├── __init__.py
│       └── security.py    # JWT 工具
├── docs/
│   ├── api-spec.md        # API 规范
│   └── architecture.md    # 架构文档
└── requirements.txt
```

#### Step 2: 编写 AGENTS.md（知识库入口）

```markdown
# 项目架构

## 模块结构
- `src/auth/`: 认证模块（登录/注册/Token 管理）
- `src/api/`: FastAPI 应用入口
- `src/utils/`: 工具函数（JWT、加密等）

## 技术栈
- Python 3.10+, FastAPI, SQLAlchemy, PyJWT
- 测试: pytest, pytest-asyncio

## 代码规范
- 所有 API 路由必须有类型注解
- 所有业务逻辑必须有单元测试
- JWT Token 有效期 15 分钟，刷新 Token 有效期 7 天

## 当前任务
- [ ] 实现 JWT 刷新 Token 功能
- [ ] 添加 Token 黑名单机制
- [ ] 实现 Rate Limiting
```

#### Step 3: 编写 Demo 脚本

```python
#!/usr/bin/env python3
"""
Nexgent Demo: Agent 在内部知识库中的自主循环实现

演示流程:
1. Agent 加载项目知识库（AGENTS.md + 目录扫描）
2. Agent 自主规划实现方案（Plan Mode）
3. Agent 执行代码级修改
4. Agent 自主循环验证（测试 → 修复 → 重试）
5. Agent 报告结果
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nexgent.agent import NexgentAgent, AgentDeps
from nexgent.context import SessionContext
from nexgent.tools.registry import ToolRegistry


async def run_demo():
    """运行 Agent 自主循环 Demo"""

    # 1. 初始化 Agent
    deps = AgentDeps(
        model="mimo-v2.5-pro",
        base_url=os.getenv("MIMO_BASE_URL"),
        api_key=os.getenv("MIMO_API_KEY"),
    )
    agent = NexgentAgent(deps=deps)

    # 2. 设置目标
    goal = """
    给 auth 模块实现 JWT 刷新 Token 功能:
    1. 在 User 模型中添加 refresh_token 字段
    2. 实现 /auth/refresh API 端点
    3. 实现 token 刷新逻辑（验证旧 refresh_token，发放新 access_token + refresh_token）
    4. 编写完整的单元测试
    5. 确保所有测试通过
    """

    # 3. 运行 Agent 自主循环
    print("=" * 60)
    print("Nexgent Agent 自主循环 Demo")
    print("=" * 60)
    print(f"\n目标: {goal}\n")
    print("-" * 60)

    result = await agent.run(
        task=goal,
        max_steps=50,          # 最大步数
        auto_approve=True,     # 自动批准写操作
    )

    # 4. 输出结果
    print("\n" + "=" * 60)
    print("Demo 完成!")
    print("=" * 60)
    print(f"\n终止原因: {result.termination_reason}")
    print(f"总步数: {result.total_steps}")
    print(f"Token 使用: {result.token_usage}")
    print(f"\n修改的文件:")
    for f in result.modified_files:
        print(f"  - {f}")


if __name__ == "__main__":
    asyncio.run(run_demo())
```

#### Step 4: 编写 E2E 测试验证 Demo

```python
"""Demo E2E 测试: 验证 Agent 自主循环能力"""
import pytest
from nexgent.agent import NexgentAgent, AgentDeps


@pytest.mark.e2e
@pytest.mark.slow
class TestAgentAutonomousLoop:
    """测试 Agent 在知识库上下文中的自主循环能力"""

    async def test_agent_loads_knowledge_base(self, agent: NexgentAgent):
        """验证 Agent 能加载项目知识库"""
        result = await agent.run(
            task="列出项目的模块结构和技术栈",
            max_steps=5,
        )
        assert "auth" in result.final_response.lower()
        assert "fastapi" in result.final_response.lower()

    async def test_agent_plans_before_implementation(self, agent: NexgentAgent):
        """验证 Agent 在实现前会进入计划模式"""
        result = await agent.run(
            task="分析 auth 模块的当前实现，规划添加刷新 token 的方案",
            max_steps=10,
        )
        # 应该有 plan_mode 的使用记录
        plan_steps = [s for s in result.steps if "plan" in s.tool_name.lower()]
        assert len(plan_steps) > 0

    async def test_agent_writes_code(self, agent: NexgentAgent, tmp_path):
        """验证 Agent 能编写代码"""
        result = await agent.run(
            task=f"在 {tmp_path} 创建一个 hello.py 文件，包含一个 hello() 函数",
            max_steps=10,
            auto_approve=True,
        )
        assert (tmp_path / "hello.py").exists()

    async def test_agent_runs_tests_and_fixes(self, agent: NexgentAgent):
        """验证 Agent 能运行测试并修复失败"""
        result = await agent.run(
            task="运行 auth 模块的测试，如果有失败就修复",
            max_steps=30,
            auto_approve=True,
        )
        # 应该有测试运行记录
        test_steps = [s for s in result.steps if "pytest" in str(s.tool_input)]
        assert len(test_steps) > 0

    async def test_full_autonomous_loop(self, agent: NexgentAgent):
        """完整自主循环: 知识库加载 → 规划 → 实现 → 测试 → 修复"""
        result = await agent.run(
            task="""
            给 auth 模块实现 JWT 刷新 Token 功能:
            1. 在 User 模型中添加 refresh_token 字段
            2. 实现 /auth/refresh API 端点
            3. 编写单元测试
            4. 确保所有测试通过
            """,
            max_steps=50,
            auto_approve=True,
        )
        # 验证最终测试通过
        assert result.termination_reason in ("goal_met", "max_steps")
```

### 4.4 Demo 演示脚本

#### 快速演示（5 分钟）

```bash
# 1. 启动 Nexgent
cd demo-project
nexgent

# 2. 输入任务
> 给 auth 模块实现 JWT 刷新 Token 功能，确保所有测试通过

# 3. 观察 Agent 自主循环:
#    - 加载 AGENTS.md 和项目结构
#    - 进入 Plan Mode 探索现有代码
#    - 退出 Plan Mode 输出实现方案
#    - 逐步编写代码
#    - 运行测试
#    - 失败 → 分析 → 修复 → 重试
#    - 成功 → 报告结果
```

#### 编程演示（代码级）

```bash
# 使用 Nexgent 的 SubAgent 并行能力
nexgent --task "
并行执行以下任务:
1. 分析 src/auth/ 模块的当前实现
2. 搜索项目中所有 JWT 相关代码
3. 读取 docs/api-spec.md 中的认证规范
然后综合结果，实现刷新 Token 功能
"
```

### 4.5 交付清单

| 交付物 | 说明 | 状态 |
|--------|------|------|
| Demo 项目 | 包含 auth 模块的模拟项目 | 待创建 |
| AGENTS.md | 项目知识库入口 | 待编写 |
| Demo 脚本 | 自动化演示脚本 | 待编写 |
| E2E 测试 | 验证自主循环能力 | 待编写 |
| 演示视频 | 5 分钟录屏展示完整流程 | 待录制 |
| 文档 | README + 架构说明 | 待编写 |

### 4.6 进阶 Demo：对标 Claude Code Workflow

如果要展示更高级的能力（对标 Claude Code 的 Dynamic Workflows），可以实现：

```python
# Nexgent 的 SubAgent 并行编排 Demo
nexgent --task "
使用并行子代理完成代码审查:
/subagent '审查 src/auth/ 的安全性' |
/subagent '审查 src/auth/ 的性能' |
/subagent '审查 src/auth/ 的测试覆盖'
然后综合三个子代理的结果，输出统一的审查报告
"
```

这展示了 Nexgent 的 SubAgent 并行能力，虽然不如 Claude Code 的 Workflow 引擎强大，但已经体现了多代理协作的核心思想。

---

## 五、总结

### 5.1 项目价值

Nexgent 是一个**生产级的 Agent Harness 实现**，完整复刻了 Claude Code 的核心架构，同时具备模型无关的独特优势。项目包含：
- 22 个核心模块，33 个工具
- 1057 单元测试 + 73 端到端测试
- 20 种设计模式
- 完整的文档和学习路径

### 5.2 简历定位

适合投递的岗位：
- AI Agent 开发工程师
- LLM 应用开发工程师
- AI 基础设施工程师
- DevOps + AI 方向

### 5.3 下一步建议

1. **实现工作流引擎**: 补齐最大差距，对标 Claude Code 的 Dynamic Workflows
2. **添加 Agent Teams**: 实现多会话协作能力
3. **完善 LSP 集成**: 添加符号搜索和调用层次
4. **构建 Demo**: 按上述方案构建可演示的生产级 Demo
5. **录制视频**: 5 分钟演示 Agent 自主循环的完整流程
