# Agent-Learning-Hub-MiMo 代码审查报告

> 审查日期: 2026-06-03
> 审查范围: 全仓库所有源码、测试、配置文件
> 对标: Claude Code、OpenAI Codex CLI、Aider 等行业标杆

---

## 一、项目概述

本项目是一个学习型 Agent 实现，遵循 datawhalechina/Agent-Learning-Hub 课程，使用小米 MiMo 模型（`mimo-v2.5-pro`）通过 OpenAI 兼容 API 实现了 9 个阶段（Stage 0-8），最终产出一个生产级 Agent Harness（`mimo-harness`），对标 Claude Code 架构。

**代码规模**: ~6000 行 Python（harness 核心）+ ~3000 行测试 + ~1500 行 stage 实现

---

## 二、整体架构评价

### 2.1 架构设计 — 优秀

项目对标 Claude Code 的架构设计非常系统化，覆盖了以下核心模块：

| 模块 | 实现质量 | 对标 Claude Code |
|------|---------|-----------------|
| Agent Loop (状态机) | ★★★★☆ | 完整实现 while(true) 循环 + 7 种终止原因 |
| 工具系统 (ToolDef) | ★★★★★ | fail-closed 默认、输入验证、磁盘溢出 |
| 权限管线 (4 阶段) | ★★★★☆ | deny > ask > allow 优先级、6 种模式 |
| 安全管线 (2 层防御) | ★★★★☆ | regex 预过滤 + 模型分类器 |
| 上下文管理 (4 级压缩) | ★★★★☆ | snip → microcompact → LLM 压缩 → 激进截断 |
| 记忆系统 (4 类型) | ★★★★☆ | 分层加载、路径作用域规则 |
| Hook 系统 (18 事件) | ★★★☆☆ | 命令/HTTP/Prompt 三种类型 |
| SubAgent 系统 | ★★★★☆ | 并行/Pipeline 执行、资源限制 |
| CLI (25+ 命令) | ★★★★☆ | 会话管理、管道输入、多输出格式 |

### 2.2 与行业标杆对比

| 特性 | mimo-harness | Claude Code | Codex CLI | 评价 |
|------|-------------|-------------|-----------|------|
| Agent Loop | Python while(true) | 多层循环+sub-agent | Rust 核心 | 基础实现完整，缺少 extended thinking |
| 沙箱安全 | 应用层权限检查 | 平台原生沙箱 | Seatbelt/Bubblewrap | 缺少 OS 级沙箱，仅应用层过滤 |
| Hook 系统 | 命令/HTTP/Prompt | 5 种 handler + MCP | 通知脚本 | 缺少 MCP tool 和 agent handler |
| MCP 集成 | 无 | 完整支持 | Client+Server | 未实现，可作为后续增强 |
| 配置管理 | 4 级层次 | 5 级层次+实时生效 | TOML+Profile | 接近完整 |
| 工具集成 | 内置 15 个工具 | 内置+MCP 动态发现 | 内置+MCP | 缺少动态工具发现 |

---

## 三、发现的问题

### 3.1 确认的 Bug（需修复）

#### BUG-1: `_handle_tool_call` 中未定义变量 `command` — ✅ 已修复

**文件**: `mimo-harness/mimo_harness/agent.py:418`
**严重性**: 高 — `run_command` 工具调用必然失败

```python
# 修复前 (有 bug):
if func_name == "run_command":
    perm = self._check_shell_permission(command)  # ← 'command' 未定义！

# 修复后:
if func_name == "run_command":
    perm = self._check_shell_permission(func_args.get("command", ""))
```

**影响**: 每次 LLM 调用 `run_command` 工具时，都会抛出 `NameError`。由于外层有 `except Exception` 捕获，不会导致程序崩溃，但所有 shell 命令都会返回错误 JSON 给 LLM，导致 agent 无法执行任何 shell 命令。

**为什么测试未发现**: 测试直接调用 `shell.run_command(handler)` 而非通过 `_handle_tool_call` 方法。`test_agent.py` 中没有测试 `_handle_tool_call` 的用例。

**修复验证**: 独立测试确认修复后 `run_command` 正常工作。所有 agent、shell、security 测试通过（15 + 15 + 89 = 119 测试）。

---

### 3.2 设计层面的关注点（非 Bug，但值得改进）

#### DESIGN-1: 安全分类器 Fail-Open 策略

**文件**: `mimo-harness/mimo_harness/security_pipeline.py:557-565`

```python
except Exception as e:
    # Fail open: when the model classifier API is unavailable
    logging.getLogger(__name__).warning(...)
    return None  # ← 返回 None，导致默认 ALLOW
```

**分析**: 当模型分类器 API 不可用时（超时、限流、网络错误），系统会默认放行。这是有意为之的设计决策，代码中有清晰的注释解释了原因："Blocking ALL tool calls when the classifier API is down is too aggressive — it makes the agent completely unusable."

**客观评价**: 这是合理的工程权衡。regex 预过滤层（Layer 1）仍然有效，会拦截 `rm -rf /`、凭据访问等明显危险操作。Claude Code 也采用类似策略。但如果需要更高安全级别，可以考虑将 fail-open 改为 fail-closed 并提供降级模式。

#### DESIGN-2: Shell 命令使用 `shell=True`

**文件**: `mimo-harness/mimo_harness/tools/shell.py:262-310`

所有 shell 命令通过 `subprocess.run(command, shell=True, ...)` 执行。虽然有 `_is_readonly` 检测和权限管线，但 `shell=True` 本身就存在命令注入风险。

**客观评价**: 这是 Python shell 工具的标准做法（Claude Code 的 Bash 工具也使用 shell 执行）。项目已通过多层防御缓解风险：
1. `_is_readonly` 检测反引号和 `$()`（`shell.py:60`）
2. 权限管线的危险命令检测（`permissions.py:358-373`）
3. 安全管线的 regex 硬拒绝（`security_pipeline.py:113-137`）
4. 环境变量清洗（`shell.py:134-146`）

这是可接受的，但如果要达到 Codex CLI 的安全级别，需要引入 OS 级沙箱。

#### DESIGN-3: 全局可变状态 — ✅ 已修复

**文件**: `mimo-harness/mimo_harness/tools/file_ops.py`

**修复方案**: 使用 Python `contextvars` 将全局 `_read_files` / `_write_allowed_files` 改为 session-scoped 的 `FileOpsState` 对象。每个 `MiMoHarness.run()` 调用和每个 SubAgent 都会创建独立的 `FileOpsState`，通过 `contextvars.ContextVar` 实现线程隔离。

```python
# 修复后:
@dataclass
class FileOpsState:
    """Per-session tracking of read/write file state."""
    read_files: set = field(default_factory=set)
    write_allowed_files: set = field(default_factory=set)

_file_ops_state_var: contextvars.ContextVar[FileOpsState] = contextvars.ContextVar(
    "file_ops_state", default=FileOpsState()
)
```

#### DESIGN-4: 模型分类器使用主模型

**文件**: `mimo-harness/mimo_harness/security_pipeline.py:504`

```python
response = client.chat.completions.create(
    model=model or "mimo-v2.5-pro",  # 使用主模型做分类
```

Claude Code 使用**独立的分类器模型**来评估安全性，而非主模型。使用主模型做安全分类有两个问题：
1. 主模型可能被 prompt injection 操纵（如果攻击者控制了对话上下文）
2. 增加了延迟和成本（每次工具调用都需要额外的 LLM 调用）

**客观评价**: 对于学习项目来说这是合理的简化。在生产环境中，应使用独立的、更小的分类模型。

---

### 3.3 代码质量问题（轻微）

#### QUALITY-1: 版本号不一致

- `setup.py` 中版本为 `0.2.0`
- `__init__.py` 中版本为 `0.3.0`
- CLI banner 显示 `v0.2.0`

#### QUALITY-2: `review_action` 中的硬编码默认模型

**文件**: `security_pipeline.py:647`

```python
model=model or "gpt-4o-mini",  # ← 硬编码了 OpenAI 模型名
```

而 `classify_action_model` 使用 `model or "mimo-v2.5-pro"`。两处默认模型不一致。

#### QUALITY-3: 测试覆盖的盲区 — ✅ 已修复

测试直接调用工具 handler 函数（如 `shell.run_command(params)`），但不测试通过 `_handle_tool_call` → `registry.execute` → `handler` 的完整调用链。这导致 BUG-1 未被发现。

**修复方案**: 在 `test_agent.py` 中新增 `TestHandleToolCallIntegration` 测试类，包含 7 个集成测试：
- `test_run_command_dispatch`: 验证 `run_command` 通过完整链路工作（BUG-1 回归测试）
- `test_read_file_dispatch`: 验证 `read_file` 完整链路
- `test_write_file_dispatch`: 验证 `write_file` 完整链路
- `test_edit_file_requires_read`: 验证 `edit_file` 的 read-before-edit 检查
- `test_calculator_dispatch`: 验证 `calculator` 完整链路
- `test_unknown_tool_rejected`: 验证未知工具被拒绝（fail-closed）
- `test_malformed_args_handled`: 验证畸形参数被正确处理

---

## 四、安全审查

### 4.1 安全亮点（做得好的地方）

1. **AST 安全求值**: 所有数学计算使用 AST 遍历而非 `eval()`（`math_tools.py`）
2. **路径遍历防护**: 文件操作验证路径在允许目录内（`file_ops.py:37-43`）
3. **SSRF 防护**: Web 工具包含 DNS 解析检查、私有 IP 阻止、DNS rebinding 检测（`web_tools.py:40-78`）
4. **凭据清洗**: Shell 命令执行前移除环境变量中的凭据模式（`shell.py:63-67`）
5. **敏感数据自动脱敏**: 输出过滤器检测并脱敏 API key、token、密码等（`security_pipeline.py:48-68`）
6. **Prompt injection 检测**: 工具输出中的注入模式会被标记警告（`security_pipeline.py:92-110`）
7. **Read-before-write/edit**: 文件修改前必须先读取（`file_ops.py:90-95, 117-120`）
8. **受保护路径**: `.git`、`.env`、`.ssh` 等目录/文件禁止写入（`permissions.py:40-41`）

### 4.2 安全风险点

1. **无 OS 级沙箱**: 所有安全检查都在应用层，绕过 Python 代码即可突破。Codex CLI 使用 Seatbelt (macOS)、Bubblewrap (Linux)、Restricted Token (Windows) 提供 OS 级隔离。
2. **`code_exec` 无网络/文件系统限制**: `execute_python` 在子进程中执行任意 Python 代码，仅有的限制是 10 秒超时。
3. **Hook 命令注入**: `HookRunner._run_command_hook` 使用 `shell=True` 执行 hook 命令，hook 配置来自 JSON 文件，如果配置文件被篡改可能导致命令注入。

---

## 五、测试审查

### 5.1 测试策略评价

项目采用**真实 API 测试**策略（禁止 mock），这是值得肯定的。测试分为：

- **单元测试** (test_stage_unit.py): 40+ 测试，纯逻辑，无 API 调用
- **E2E 测试** (test_e2e.py): 真实 MiMo API 调用，有重试逻辑
- **Harness 单元测试**: 21 个测试文件，覆盖所有模块
- **Harness E2E 测试**: 端到端工具调用

### 5.2 测试改进

1. **集成测试**: ✅ 已补充 `TestHandleToolCallIntegration`（7 个测试覆盖 `_handle_tool_call` 完整链路）
2. **并发测试**: SubAgent 并行执行的线程安全性已有 44 个测试覆盖
3. **错误恢复测试**: Circuit breaker 和 thrashing 检测的测试可进一步增强

---

## 六、总结

### 6.1 总体评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构设计 | ★★★★☆ | 对标 Claude Code 架构完整，模块化清晰 |
| 代码质量 | ★★★★☆ | 文档充分，命名规范，有 1 个确认 bug |
| 安全性 | ★★★★☆ | 多层防御，但缺少 OS 级沙箱 |
| 测试覆盖 | ★★★☆☆ | 真实 API 测试策略好，但集成测试不足 |
| 工程实践 | ★★★★☆ | CI/CD 完整，配置管理规范 |

### 6.2 需要修复的问题

| 编号 | 问题 | 严重性 | 状态 |
|------|------|--------|------|
| BUG-1 | `_handle_tool_call` 中 `command` 变量未定义 | **高** | ✅ 已修复 |
| DESIGN-3 | 全局 `_read_files` / `_write_allowed_files` 改为 session-scoped | 中 | ✅ 已修复 |
| QUALITY-1 | 版本号不一致 (setup.py=0.2.0, __init__.py=0.3.0) | 低 | ✅ 已修复 |
| QUALITY-2 | `review_action` 硬编码 `gpt-4o-mini` 默认模型 | 低 | ✅ 已修复 |
| QUALITY-3 | 缺少 `_handle_tool_call` 集成测试 | 中 | ✅ 已修复 |

### 6.3 建议改进项（按优先级）

1. **[高]** ~~修复 BUG-1~~ ✅ 已修复
2. **[中]** ~~补充集成测试~~ ✅ 已修复（7 个集成测试）
3. **[中]** ~~统一版本号~~ ✅ 已修复
4. **[低]** ~~修复 `review_action` 中硬编码的 `gpt-4o-mini` 默认模型~~ ✅ 已修复
5. **[低]** ~~将全局 `_read_files` / `_write_allowed_files` 改为 session-scoped~~ ✅ 已修复
6. **[远期]** 引入 MCP 协议支持
7. **[远期]** 引入 OS 级沙箱（参考 Codex CLI 的 Seatbelt/Bubblewrap）

### 6.4 结论

这是一个**高质量的学习项目**，架构设计对标 Claude Code 非常系统化，覆盖了 Agent Harness 的所有核心模块。代码文档充分，安全防御多层叠加，测试策略（真实 API 调用）值得肯定。

审查发现并修复了 5 个问题：
1. **BUG-1** (高): `_handle_tool_call` 中 `command` 变量未定义，导致 `run_command` 工具无法工作
2. **DESIGN-3** (中): 全局文件操作状态改为 session-scoped，避免 SubAgent 并行时交叉污染
3. **QUALITY-1** (低): 版本号不一致，统一为 0.3.0
4. **QUALITY-2** (低): `review_action` 硬编码 `gpt-4o-mini`，改为 `mimo-v2.5-pro`
5. **QUALITY-3** (中): 补充 7 个集成测试覆盖 `_handle_tool_call` 完整调用链

与行业标杆相比，主要差距在于：缺少 OS 级沙箱、MCP 协议支持、以及独立的安全分类模型。但考虑到这是一个学习项目而非生产系统，当前的实现水平已经非常出色。
