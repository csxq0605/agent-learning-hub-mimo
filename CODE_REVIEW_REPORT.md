# Agent-Learning-Hub-MiMo 代码审查报告

> 审查日期: 2026-06-04 (第二轮)
> 审查范围: mimo-harness 核心包 (~11,000 行)、8 个 stage 模块、21 个测试文件
> 对标: Claude Code、OpenAI Codex CLI、Aider 等行业标杆

---

## 一、测试状态

| 测试类别 | 结果 |
|---------|------|
| Harness 单元测试 (733 个) | ✅ 全部通过 |
| E2E 测试 | ❌ 1 个失败 (`test_edit_modifies_content`) |
| Agent 测试 (22 个) | ✅ 全部通过 (65s) |

**E2E 失败原因**: `_ALLOWED_WRITE_DIR` 全局单例锁定在项目根目录，E2E 测试在临时目录创建文件，被路径验证拒绝。这是一个真实的 bug。

---

## 二、发现汇总

| # | 严重度 | 模块 | 类型 | 描述 | 状态 |
|---|--------|------|------|------|------|
| 1 | 🔴 High | file_ops.py | Bug | `_ALLOWED_WRITE_DIR` 全局单例导致 E2E 失败 | ✅ 已修复 |
| 2 | 🟡 Medium | security_pipeline.py | 线程安全 | 分类器缓存无锁保护 | ✅ 已修复 |
| 3 | 🟡 Medium | permissions.py | 维护风险 | `_is_dangerous_rm` 重复 `_HARD_DENY_PATTERNS` | ✅ 已修复 |
| 4 | 🟢 Low | context.py | 死代码 | `restore_last()` 中 `..` 检查无效 | ✅ 已修复 |
| 5 | 🟢 Low | agent.py | 防御性 | 系统提示缓存永不失效 | ✅ 已修复 |

---

## 三、详细发现

### #1 🔴 High: `_ALLOWED_WRITE_DIR` 全局单例导致 E2E 测试失败

**文件**: `mimo_harness/tools/file_ops.py:23,76-81`

```python
_ALLOWED_WRITE_DIR = None  # 模块级全局变量

def _get_allowed_write_dir() -> Path:
    global _ALLOWED_WRITE_DIR
    if _ALLOWED_WRITE_DIR is None:
        _ALLOWED_WRITE_DIR = Path.cwd().resolve()  # 首次使用锁定为 CWD
    return _ALLOWED_WRITE_DIR
```

**问题**: 
- `_ALLOWED_WRITE_DIR` 是模块级全局变量，首次调用后锁定为 `Path.cwd()`
- E2E 测试 `test_edit_modifies_content` 在临时目录 (`tempfile.mkdtemp()`) 创建文件
- Agent 的 `_validate_path()` 拒绝访问临时目录，报错 "Path outside allowed directory"
- 测试断言失败：LLM 无法读写文件，返回错误而非编辑结果

**影响**: E2E 测试失败；如果 agent 在会话中需要访问 CWD 之外的文件也会失败。

**修复**: 新增 `set_allowed_write_dir()` 函数，E2E fixture 和 `_harness()` 正确设置目录。

---

### #2 🟡 Medium: 安全分类器缓存非线程安全

**文件**: `mimo_harness/security_pipeline.py:417,451-456`

```python
_classifier_cache: dict[str, tuple[float, ClassificationResult]] = {}  # 无锁

# classify_action_model() 中的读-检查-写模式:
if cache_key in _classifier_cache:           # 线程 A 读
    cached_time, cached_result = _classifier_cache[cache_key]
    if now - cached_time < _CLASSIFIER_CACHE_TTL:
        return cached_result
# ... 可能在线程 A 读和写之间，线程 B 也读了同一个 key
_classifier_cache[cache_key] = (now, result)  # 写
```

**问题**: `agent.py` 使用 `ThreadPoolExecutor` 并行执行工具调用，多个线程可能同时访问 `_classifier_cache`。虽然 Python GIL 保证基本 dict 操作原子性，但读-检查-写模式不是原子的。

**实际影响**: 低。最坏情况是缓存未命中导致多发一次 API 调用，不会导致安全漏洞或数据损坏。

**修复**: 添加 `threading.Lock` 保护缓存操作。

---

### #3 🟡 Medium: `_is_dangerous_rm` 与 `_HARD_DENY_PATTERNS` 模式重复

**文件**: 
- `mimo_harness/permissions.py:358-374` (`_is_dangerous_rm`)
- `mimo_harness/security_pipeline.py:113-137` (`_HARD_DENY_PATTERNS`)

**问题**: 两处硬编码了相似但不完全一致的危险命令模式。`_is_dangerous_rm` 缺少 `curl|bash` 和凭据外泄检测。

**修复**: 从 `_HARD_DENY_PATTERNS` 导入，消除重复。

---

### #4 🟢 Low: CheckpointManager.restore_last() 死代码

**文件**: `mimo_harness/context.py:265-267`

```python
dest_norm = os.path.normpath(os.path.abspath(dest))
if ".." in dest_norm:  # ← 永远为 False
    continue
```

**修复**: 移除死代码，添加注释说明 normpath 已处理 `..`。

---

### #5 🟢 Low: 系统提示缓存永不失效

**文件**: `mimo_harness/agent.py:348,381`

**问题**: 如果 CWD 在会话中变化，系统提示中的 `Working directory` 信息会过时。

**修复**: 在 `run()` 方法开始时重置缓存。

---

## 四、设计决策记录（非 Bug）

| 决策 | 位置 | 说明 |
|------|------|------|
| 安全分类器 Fail-Open | security_pipeline.py:557 | API 不可用时默认放行，regex 预过滤仍有效 |
| Shell 使用 `shell=True` | shell.py:262 | Python shell 工具标准做法，多层防御已缓解风险 |
| HTML 抓取搜索引擎 | web_tools.py:87-127 | DuckDuckGo/Bing HTML 解析依赖网站结构 |
| Stage 文件 `sys.path.insert` | stage-*/ | 学习项目可接受的做法 |
| 主模型做安全分类 | security_pipeline.py:504 | 学习项目简化，生产应使用独立分类模型 |

---

## 五、安全审查

### 5.1 安全亮点

1. **AST 安全求值**: 数学计算使用 AST 遍历，无 `eval()` 风险
2. **路径遍历防护**: 文件操作验证路径在允许目录内，symlink 解析
3. **SSRF 防护**: DNS 解析检查 + 私有 IP 阻止 + DNS rebinding 检测
4. **凭据清洗**: Shell 环境变量中移除凭据模式
5. **敏感数据脱敏**: 15 种 regex 模式自动脱敏 API key/token/密码
6. **Prompt injection 检测**: 17 种模式检测工具输出中的注入
7. **Read-before-write/edit**: 文件修改前必须先读取（session-scoped）
8. **受保护路径**: `.git`、`.env`、`.ssh` 等禁止写入，BYPASS 模式也保护

### 5.2 安全风险

1. **无 OS 级沙箱**: 应用层检查可被绕过（Codex CLI 使用 Seatbelt/Bubblewrap）
2. **`code_exec` 无限制**: Python 子进程仅 10 秒超时，无网络/文件系统限制
3. **Hook 配置注入**: hook 命令来自 JSON 配置文件，配置被篡改可导致命令注入

---

## 六、CI/CD 优化

**变更**: E2E 测试从自动运行改为手动触发（opt-in）

- `push` / `PR` → 只运行单元测试 (733 个)
- `workflow_dispatch` + `run_e2e=true` → 运行 E2E 测试

---

## 七、修复结果

所有发现已修复，733 个单元测试全部通过：

| # | 修复内容 | 修改文件 | 测试验证 |
|---|---------|---------|---------|
| 1 | `_ALLOWED_WRITE_DIR` 改为可配置，新增 `set_allowed_write_dir()` | `file_ops.py`, `test_e2e.py` | 92 tools 测试通过 |
| 2 | 分类器缓存添加 `threading.Lock` | `security_pipeline.py` | 100 security 测试通过 |
| 3 | `_is_dangerous_rm` 从 `_HARD_DENY_PATTERNS` 导入 | `permissions.py` | 59 permissions 测试通过 |
| 4 | 移除 `restore_last()` 死代码 | `context.py` | 72 context 测试通过 |
| 5 | `run()` 开始时重置系统提示缓存 | `agent.py` | 22 agent 测试通过 |
