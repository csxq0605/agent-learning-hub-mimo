# Code Review — Agent-Learning-Hub-MiMo 全仓库

> 审查范围：config.py, stage-1~8, mimo-harness（共 20 个 Python 文件）
> 审查日期：2026-05-23
> 分级标准：P0 = 必须修复, P1 = 强烈建议, P2 = 改善项

---

## P0 — 必须修复（4 项）

### 1. stage-1: model_dump() content=None 导致 MiMo API 报错

**文件**: `stage-1/minimal_agent.py:155`

```python
messages.append(message.model_dump())
```

当 LLM 返回 tool_calls 时，`content` 为 None，MiMo API 要求 content 必须是字符串。Stage-2/3/8 已修复此问题，但 Stage-1 遗漏。

**修复**:
```python
msg_dump = message.model_dump()
if msg_dump.get("content") is None:
    msg_dump["content"] = ""
messages.append(msg_dump)
```

---

### 2. stage-3: read_file 无路径校验（任意文件读取）

**文件**: `stage-3/harness_demo.py:224-229`

```python
def _read_file(self, path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return json.dumps({"content": f.read()[:5000]})
```

`write_file` 有路径沙箱校验，但 `read_file` 没有。Stage-1 和 Stage-2 的 read_file 都已加了路径校验，Stage-3 遗漏。

**修复**: 添加与 `_write_file` 相同的 `Path.resolve()` + `cwd` 校验。

---

### 3. stage-8: hashlib 未导入导致启动崩溃

**文件**: `stage-8/devops-agent/src/agent.py:39`

```python
self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
```

`hashlib` 未在 import 列表中，`TraceLogger.__init__()` 会抛出 `NameError: name 'hashlib' is not defined`。

**修复**: 在文件顶部 `import hashlib`。

---

### 4. stage-8: read_log_file 权限检查结果被忽略

**文件**: `stage-8/devops-agent/src/agent.py:142-146`

```python
def read_log_file(params: dict) -> str:
    path = params.get("path", "")
    perms.check(Permission.READ, f"Read log file: {path}")  # 结果被丢弃
    # ... 继续执行读取
```

`perms.check()` 返回 `bool`，但返回值没有被检查。如果用户拒绝，读取仍会继续。应改为：

```python
if not perms.check(Permission.READ, f"Read log file: {path}"):
    return json.dumps({"error": "Permission denied"})
```

---

## P1 — 强烈建议修复（4 项）

### 5. mimo-harness/shell.py: echo 被列为只读命令

**文件**: `mimo-harness/mimo_harness/tools/shell.py:14`

```python
READONLY_PREFIXES = [
    "ls", "dir", "cat", "type", "head", "tail", "wc", "echo", "pwd",
    ...
]
```

`echo` 可通过重定向写文件：`echo hacked > /etc/passwd`。虽然 `_CHAINING_PATTERN` 会检测 `>`，但 `>` 不在 pattern 中（只检测 `;|&`$()`）。`>` 是 shell 重定向，应被检测或从只读列表中移除。

**修复**: 从 `READONLY_PREFIXES` 中移除 `"echo"`，或将 `>` 加入 `_CHAINING_PATTERN`。

---

### 6. mimo-harness/doc_tools.py: 输出路径无沙箱校验

**文件**: `mimo-harness/mimo_harness/tools/doc_tools.py`

`create_doc` 和 `create_spreadsheet` 接受 `output_dir` 参数，但没有校验是否在允许目录内。用户（或 LLM）可以指定 `output_dir="/etc"` 写入任意位置。

**修复**: 添加与 `file_ops._validate_write_path` 相同的路径校验。

---

### 7. mimo-harness/context.py: build_system_prompt 函数未被使用

**文件**: `mimo-harness/mimo_harness/context.py:72-100`

定义了 `build_system_prompt()` 函数，但 `agent.py` 中使用的是 `MiMoHarness._build_system_prompt()` 方法（内联了相同的逻辑）。两个实现不一致，维护时容易不同步。

**修复**: 删除 `context.py` 中的 `build_system_prompt()`，或让 `agent.py` 调用它。

---

### 8. README.md 快速开始有重复内容

**文件**: `README.md:90-97`

```bash
# 4. 运行任意 Stage
python stage-1/minimal_agent.py
python stage-2/research_assistant.py
...
# 5. 或者直接使用完整 Harness（推荐）
cd mimo-harness
pip install -e .
mimo-harness --task "What is 247 * 893?"
python stage-1/minimal_agent.py    # ← 重复
python stage-2/research_assistant.py  # ← 重复
```

Step 5 末尾重复了 Step 4 的 Stage 运行命令。

---

## P2 — 改善项（4 项）

### 9. stage-8: lambda 闭包变量捕获问题

**文件**: `stage-8/devops-agent/src/agent.py:203-212`

```python
response = retry_with_backoff(
    lambda: client.chat.completions.create(
        model=MIMO_MODEL,
        messages=messages,  # messages 在循环中被修改
        ...
    )
)
```

`lambda` 捕获的是 `messages` 的引用，不是值。在 `retry_with_backoff` 重试时，`messages` 可能已经被后续代码修改。实际上在当前代码中，lambda 在下一次迭代前就执行完毕了，所以不会出问题，但这是潜在隐患。

---

### 10. stage-4/5: extract_json 重复定义

`stage-4/multi_agent_writer.py` 和 `stage-5/code-review-skill/review.py` 各自定义了相同的 `extract_json()` 函数。如果未来需要修改，需要改两处。

**建议**: 提取到 `config.py` 或共享工具模块中。

---

### 11. mimo-harness/logging_utils.py: 未使用的 import

**文件**: `mimo-harness/mimo_harness/logging_utils.py:5`

```python
import hashlib
```

`hashlib` 被导入但在 `TraceLogger.__init__` 中使用的是 `hashlib.md5()`。实际上是在用的，只是写在了文件顶部。不过 `logging_utils.py` 中没有其他地方使用 `hashlib`。这是正常的。

（注：此条经复核无问题，撤回。）

---

### 12. setup.py: open("README.md") 使用相对路径

**文件**: `mimo-harness/setup.py:7`

```python
long_description=open("README.md", encoding="utf-8").read(),
```

如果 `pip install` 从其他目录执行，相对路径会找不到文件。且文件句柄未关闭。

**修复**:
```python
from pathlib import Path
long_description=(Path(__file__).parent / "README.md").read_text(encoding="utf-8"),
```

---

## 总结

| 级别 | 数量 | 关键问题 |
|------|------|----------|
| P0 | 4 | API 兼容性、路径遍历、启动崩溃、权限绕过 |
| P1 | 4 | 命令注入、路径沙箱、死代码、文档错误 |
| P2 | 3 | 闭包隐患、代码重复、路径处理 |

**需修复文件**:
- `stage-1/minimal_agent.py` — model_dump content
- `stage-3/harness_demo.py` — read_file 路径校验
- `stage-8/devops-agent/src/agent.py` — hashlib import + 权限检查
- `mimo-harness/mimo_harness/tools/shell.py` — echo 移除
- `mimo-harness/mimo_harness/tools/doc_tools.py` — 路径沙箱
- `mimo-harness/mimo_harness/context.py` — 删除死代码
- `README.md` — 删除重复内容
- `mimo-harness/setup.py` — Path 修复
