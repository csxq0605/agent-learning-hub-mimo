# Agent Learning Hub - 代码审查报告

> 对 Stage 1-8 全部代码的逐文件审查，按严重级别分类（Critical / Warning / Info），并给出具体修复建议。

---

## 通用问题（跨 Stage）

### [CRITICAL] `eval()` / `exec()` 安全风险

**涉及文件：** Stage 1 `minimal_agent.py:64`、Stage 2 `research_assistant.py:160`、Stage 3 `harness_demo.py:166`

```python
# Stage 1 & 3
result = eval(params["expression"], {"__builtins__": {}}, {})

# Stage 2
exec(params["code"], {"__builtins__": __builtins__}, {})
```

**问题：**
- `eval()` 即使限制了 `__builtins__`，仍可通过 `().__class__.__bases__[0].__subclasses__()` 获取任意类，实现沙箱逃逸
- Stage 2 的 `exec()` 更严重——直接传入了完整的 `__builtins__`，LLM 生成的代码可以 `import os; os.system("rm -rf /")`

**修复建议：**

```python
# 方案 1：使用 ast.literal_eval（仅支持字面量，不支持表达式）
import ast
result = ast.literal_eval(params["expression"])

# 方案 2：使用受限数学求值器
import operator, math
SAFE_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
SAFE_FUNCS = {"abs": abs, "round": round, "min": min, "max": max}

def safe_eval(expr: str):
    tree = ast.parse(expr, mode='eval')
    return _eval_node(tree.body)

# 方案 3：对 exec() 使用 subprocess 隔离 + 超时
import subprocess
result = subprocess.run(
    ["python", "-c", code],
    capture_output=True, timeout=5,
    text=True
)
```

---

### [WARNING] 每次调用都创建新的 OpenAI Client

**涉及文件：** Stage 1 `minimal_agent.py:90`、Stage 2 `research_assistant.py:193`、Stage 4 `multi_agent_writer.py:43`、Stage 7 `eval_runner.py:67`

```python
client = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL)
```

**问题：** 每次调用 `agent_loop` / `call_agent` / `ask_agent` 都创建新的 client 对象，重复建立 HTTP 连接池。

**修复建议：**

```python
# 使用模块级单例
_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=MIMO_API_KEY, base_url=MIMO_BASE_URL)
    return _client
```

---

### [WARNING] `temperature=1.0` 不适合所有场景

**涉及文件：** 所有 Stage

```python
temperature=1.0, top_p=0.95
```

**问题：** `temperature=1.0` 是最高随机性设置。对于需要精确输出的场景（代码审查、数学计算、JSON 生成），高温度会导致输出不稳定。

**修复建议：**

```python
# 需要创造性的场景（写文章、头脑风暴）
temperature=1.0, top_p=0.95

# 需要精确性的场景（代码审查、数学、JSON）
temperature=0.0, top_p=1.0

# 通用场景
temperature=0.7, top_p=0.9
```

---

## Stage 1: minimal_agent.py

### [WARNING] `search` 工具是空壳

```python
elif name == "search":
    return json.dumps({"summary": f"Search results for '{params['query']}': [placeholder]"})
```

**问题：** `search` 工具返回固定占位文本，LLM 会认为这是真实搜索结果并基于此回答用户，导致幻觉。

**修复建议：** 要么实现真实的搜索（接入 API），要么从 TOOLS 中移除，不要给 LLM 一个"假工具"。

### [INFO] 缺少 API 错误处理

```python
response = client.chat.completions.create(...)
```

**问题：** 没有 try/except 处理网络超时、API 限流、认证失败等异常。

**修复建议：**

```python
try:
    response = client.chat.completions.create(...)
except Exception as e:
    return f"[ERROR] API call failed: {e}"
```

---

## Stage 2: research_assistant.py

### [CRITICAL] `execute_code` 工具无任何安全限制

```python
elif name == "execute_code":
    exec(params["code"], {"__builtins__": __builtins__}, {})
```

**问题：** 这是最严重的安全漏洞。LLM 生成的代码拥有完全的系统权限：
- `import os; os.system("rm -rf /")` — 删除文件
- `import socket; socket.connect(...)` — 网络外联
- `open("/etc/passwd").read()` — 读取敏感文件

**修复建议：**

```python
# 方案：使用 subprocess + 超时 + 资源限制
import subprocess, tempfile

def execute_code_sandboxed(code: str, timeout: int = 5) -> str:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        try:
            result = subprocess.run(
                [sys.executable, f.name],
                capture_output=True, text=True,
                timeout=timeout,
                # 可选：使用 Docker 容器进一步隔离
            )
            return json.dumps({"stdout": result.stdout[:2000], "stderr": result.stderr[:500]})
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Code execution timed out"})
        finally:
            os.unlink(f.name)
```

### [WARNING] `web_search` 返回假数据

```python
if name == "web_search":
    results = [
        {"title": f"Result for '{params['query']}'", "url": f"https://example.com/search?q=..."}
    ]
```

**问题：** 与 Stage 1 的 `search` 工具相同——LLM 会基于假数据生成看似可信但实际虚假的回答。

### [BUG] `chunk_text` 在 `chunk_size <= overlap` 时死循环

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # 如果 chunk_size=50, overlap=50 → start 永远不变
```

**修复建议：**

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

### [INFO] `rag_retrieve` 是无意义的包装函数

```python
def rag_retrieve(memory: Memory, query: str) -> list:
    return memory.search_long_term(query)
```

这个函数只做了一次转发，增加了调用链复杂度但没有增加价值。可以直接调用 `memory.search_long_term()`。

---

## Stage 3: harness_demo.py

### [CRITICAL] `PermissionGate` 对 WRITE 自动批准

```python
class PermissionGate:
    def __init__(self, auto_approve: set = None):
        self.auto_approve = auto_approve or {Permission.NONE, Permission.READ}

    def check(self, required: Permission) -> bool:
        if required in self.auto_approve:
            return True
        if required == Permission.DESTRUCTIVE:
            return False
        # WRITE 和 EXECUTE 走到这里，直接返回 True
        return True  # ← 问题所在
```

**问题：** WRITE 和 EXECUTE 权限没有实际拦截，任何操作都被批准。这使得权限系统形同虚设。

**修复建议：**

```python
def check(self, required: Permission) -> bool:
    if required in self.auto_approve:
        self.log.append(f"  [AUTO] {required.value}")
        return True
    if required == Permission.DESTRUCTIVE:
        self.log.append(f"  [BLOCKED] {required.value}")
        return False
    # 需要人工确认的操作
    self.log.append(f"  [CONFIRM_REQUIRED] {required.value}")
    # 在交互模式下提示用户确认
    response = input(f"  Allow {required.value}? (y/n): ").strip().lower()
    approved = response in ("y", "yes")
    self.log.append(f"  [{'APPROVED' if approved else 'DENIED'}] {required.value}")
    return approved
```

### [WARNING] `_write_file` 无路径验证

```python
def _write_file(self, path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
```

**问题：** 可以写入任意路径，包括系统关键文件（如 `C:\Windows\System32\...`）。

**修复建议：**

```python
def _write_file(self, path: str, content: str) -> str:
    resolved = Path(path).resolve()
    allowed_dir = Path.cwd().resolve()
    if not str(resolved).startswith(str(allowed_dir)):
        return json.dumps({"error": "Path outside allowed directory"})
    # ... 写入文件
```

### [BUG] `compact_context` 导致 tool_calls 孤儿引用

```python
def compact_context(messages: list, max_messages: int = 20) -> list:
    return [messages[0]] + messages[-(max_messages - 1):]
```

**问题：** 当 assistant 消息包含 `tool_calls` 时，压缩后对应的 `tool` 消息可能被删除，导致 API 报错（tool_call_id 找不到对应的 tool_calls）。

**修复建议：**

```python
def compact_context(messages: list, max_messages: int = 20) -> list:
    if len(messages) <= max_messages:
        return messages

    result = [messages[0]]  # 保留 system prompt
    tail = messages[-(max_messages - 1):]

    # 过滤掉没有对应 tool_calls 的 tool 消息
    valid_tool_call_ids = set()
    for msg in tail:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                valid_tool_call_ids.add(tc.id)

    for msg in tail:
        if msg.get("role") == "tool":
            if msg.get("tool_call_id") in valid_tool_call_ids:
                result.append(msg)
        else:
            result.append(msg)

    return result
```

---

## Stage 4: multi_agent_writer.py

### [WARNING] JSON 提取逻辑脆弱

```python
if "```json" in text:
    text = text.split("```json")[1].split("```")[0]
elif "```" in text:
    text = text.split("```")[1].split("```")[0]
```

**问题：**
- 如果 LLM 输出多个 ` ```json ` 块，只取第一个
- 如果 LLM 输出 ` ```JSON `（大写），匹配失败
- 如果 LLM 输出不带 ` ``` ` 的 JSON 但前面有说明文字，`json.loads` 会失败

**修复建议：**

```python
import re

def extract_json(text: str) -> dict:
    # 尝试从 markdown 代码块提取
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试直接解析整个文本
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 尝试找到第一个 { 到最后一个 }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass

    return {"raw_text": text, "parse_error": "Failed to parse JSON"}
```

### [INFO] 无重试逻辑

`call_agent` 中的 API 调用没有重试机制。在 Stage 8 中实现了 `retry_with_backoff`，但 Stage 1-7 都没有使用。

---

## Stage 5: review.py

### [WARNING] SKILL.md 描述的功能未完全实现

SKILL.md 中描述了：
```bash
python review.py --file src/auth.py
python review.py --dir src/ --extensions .py,.ts
```

但实际实现只支持：
```python
filepath = sys.argv[1]  # 只支持单文件，不支持 --dir
```

**修复建议：** 要么更新 SKILL.md 匹配实际功能，要么实现 `--dir` 和 `--extensions` 参数。

### [WARNING] `smoke_test` 不测试 `format_report`

```python
def smoke_test() -> bool:
    result = review_code(test_code, "test.py")
    # 只检查 issues 是否存在，不检查 format_report
```

**修复建议：** 添加 `format_report` 的测试。

### [INFO] 缺少退出码语义

```python
sys.exit(0 if success else 1)
```

这是正确的，但 `review_code` 在 JSON 解析失败时返回 `{"raw": text, "parse_error": True}`，调用者无法区分"没有问题"和"解析失败"。

---

## Stage 6: browser_agent.py

### [WARNING] API 返回类型不一致

```python
async def navigate(self, url: str) -> dict:     # 返回 dict
async def extract_text(self, selector) -> dict:  # 返回 dict
async def extract_links(self) -> list:           # 返回 list ← 不一致
async def screenshot(self, path) -> dict:        # 返回 dict
async def click(self, selector) -> dict:         # 返回 dict
```

**问题：** `extract_links` 返回 `list`，其他方法返回 `dict`。调用者需要不同的处理逻辑。

**修复建议：** 统一返回 `dict`：

```python
async def extract_links(self) -> dict:
    try:
        links = await self._page.eval_on_selector_all(...)
        self._log("extract_links", {"count": len(links)})
        return {"links": links[:50], "count": len(links)}
    except Exception as e:
        return {"error": str(e)}
```

### [WARNING] `click` 不阻止 submit 按钮

```python
if tag in ("form",):
    return {"error": "Refusing to submit forms for safety"}
```

**问题：** 只阻止了 `<form>` 标签，但 `<button type="submit">` 和 `<input type="submit">` 不在阻止列表中。

**修复建议：**

```python
async def click(self, selector: str) -> dict:
    element = await self._page.query_selector(selector)
    if not element:
        return {"error": f"Element not found: {selector}"}
    tag = await element.evaluate("el => el.tagName.toLowerCase()")
    button_type = await element.evaluate("el => el.type || ''")
    if tag in ("form",) or (tag == "button" and button_type == "submit"):
        return {"error": "Refusing to submit forms for safety"}
    # ...
```

### [INFO] 浏览器未在异常时清理

如果 `navigate` 或 `extract_text` 抛出异常，`stop()` 可能不会被调用，导致 Chromium 进程泄漏。

**修复建议：** 在 `research_topic` 中已经用了 `try/finally`，但 `BrowserAgent` 类本身应该实现 `__aenter__` / `__aexit__` 以支持 `async with`。

---

## Stage 7: eval_runner.py

### [WARNING] 评判系统的假阴性问题

```python
def judge_response(question, expected, actual):
    if expected_lower in actual_lower:
        return True
```

**问题：** 期望 `220571`，实际 `220,571`。`"220571" in "220,571"` 为 `False`，导致假阴性。

**修复建议：** 在清理阶段移除数字中的千位分隔符：

```python
import re
actual_clean = re.sub(r'(?<=\d),(?=\d{3}\b)', '', actual_lower)  # 移除千位分隔符
expected_clean = re.sub(r'(?<=\d),(?=\d{3}\b)', '', expected_lower)
```

### [WARNING] LLM Judge 的 `temperature=1.0`

```python
response = client.chat.completions.create(
    model=MIMO_MODEL,
    messages=[{"role": "user", "content": prompt}],
    max_completion_tokens=10,
    temperature=1.0  # ← 判断任务应该用低温度
)
```

**修复建议：** `temperature=0.0` 确保评判结果一致。

### [INFO] 测试用例串行执行

15 个测试用例串行执行，每个需要 1-5 秒。可以使用 `asyncio` 或 `concurrent.futures` 并行执行以加速。

---

## Stage 8: agent.py

### [WARNING] `retry_with_backoff` 重试所有异常

```python
def retry_with_backoff(fn, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:  # ← 所有异常都重试
            last_error = e
```

**问题：** 认证失败（401）、参数错误（400）等非瞬时错误也会被重试，浪费时间和 API 配额。

**修复建议：**

```python
RETRYABLE_ERRORS = (TimeoutError, ConnectionError)

def retry_with_backoff(fn, max_retries=3, base_delay=1.0):
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            last_error = e
            # 只重试瞬时错误
            if not isinstance(e, RETRYABLE_ERRORS):
                # 对于 OpenAI 错误，检查状态码
                status = getattr(e, 'status_code', None)
                if status and status not in (429, 500, 502, 503, 504):
                    raise  # 4xx 错误（除 429）不重试
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
    raise last_error
```

### [WARNING] `PermissionGate.check` 在非交互环境会阻塞

```python
if self.dry_run:
    return False
print(f"\n  [CONFIRM] Agent wants to: {action_desc}")
response = input("  Allow? (y/n): ")  # ← 非交互环境会 EOFError
```

**修复建议：**

```python
def check(self, permission: Permission, action_desc: str) -> bool:
    # ...
    try:
        response = input("  Allow? (y/n): ").strip().lower()
    except EOFError:
        self._log(permission, action_desc, "denied_no_input")
        return False
```

### [WARNING] `list_services` 硬编码 PowerShell

```python
result = subprocess.run(["powershell", "-Command", "Get-Process | ..."], ...)
```

**问题：** 只能在 Windows 上运行。跨平台应使用 `psutil` 或条件判断。

**修复建议：**

```python
import platform

def list_services(params: dict) -> str:
    try:
        if platform.system() == "Windows":
            cmd = ["powershell", "-Command", "Get-Process | Select-Object -First 20 Name,CPU"]
        else:
            cmd = ["ps", "aux", "--sort=-%cpu"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return json.dumps({"output": result.stdout[:2000]})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

### [INFO] `deploy_service` 是空操作

```python
def deploy_service(params: dict) -> str:
    return json.dumps({"status": "deployed", "service": service, "timestamp": ...})
```

这是 demo 代码，但应该在注释中明确说明这是模拟实现。

---

## 改进优先级排序

### P0 — 必须修复（安全/正确性）

| 问题 | 文件 | 行号 |
|------|------|------|
| `exec()` 无沙箱 | stage-2 | :160 |
| `eval()` 沙箱可逃逸 | stage-1, stage-3 | :64, :166 |
| PermissionGate 形同虚设 | stage-3 | :82 |
| `_write_file` 无路径限制 | stage-3 | :148 |

### P1 — 应该修复（可靠性）

| 问题 | 文件 |
|------|------|
| `chunk_text` 死循环风险 | stage-2 |
| `compact_context` 孤儿引用 | stage-3 |
| JSON 提取脆弱 | stage-4, stage-5 |
| 评判假阴性（千位分隔符） | stage-7 |
| `retry_with_backoff` 重试所有异常 | stage-8 |

### P2 — 建议改进（工程质量）

| 问题 | 文件 |
|------|------|
| Client 重复创建 | 全部 Stage |
| `temperature=1.0` 不适合精确任务 | 全部 Stage |
| API 返回类型不一致 | stage-6 |
| `search`/`web_search` 假数据 | stage-1, stage-2 |
| 跨平台兼容性 | stage-8 |

### P3 — 可选优化

| 问题 | 文件 |
|------|------|
| 测试用例并行执行 | stage-7 |
| 浏览器 `async with` 支持 | stage-6 |
| `rag_retrieve` 冗余函数 | stage-2 |
