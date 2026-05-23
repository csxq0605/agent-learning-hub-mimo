# Code Review — Agent-Learning-Hub-MiMo 全仓库（第三轮）

> 审查范围：config.py, stage-1~8, mimo-harness（共 20 个 Python 文件）
> 审查日期：2026-05-23
> 前两轮已修复：23 项（P0×8, P1×9, P2×6）

---

## 前轮修复验证

| 修复项 | 状态 |
|--------|------|
| stage-1 model_dump() content=None | ✅ 已修复 |
| stage-3 read_file 路径校验 | ✅ 已修复 |
| stage-8 hashlib 导入 | ✅ 已修复 |
| stage-8 read_log_file 权限检查 | ✅ 已修复 |
| shell.py echo 移除 | ✅ 已修复 |
| doc_tools.py 路径沙箱 | ✅ 已修复 |
| context.py 死代码删除 | ⚠️ 见下方 P2-1 |
| README.md 重复内容 | ✅ 已修复 |
| setup.py Path 修复 | ✅ 已修复 |

---

## 本轮发现（3 项 P2）

### P2-1: context.py build_system_prompt 未完全删除

**文件**: `mimo-harness/mimo_harness/context.py:72-100`

上轮删除了 `import platform`，但 `build_system_prompt()` 函数本身仍在文件中。该函数引用了 `platform.system()` 等，如果被调用会抛出 `NameError`。虽然当前没有代码调用它（agent.py 使用自己的 `_build_system_prompt`），但保留一个必定崩溃的函数是隐患。

**建议**: 删除整个 `build_system_prompt()` 函数。

---

### P2-2: stage-1 未使用的 os 导入

**文件**: `stage-1/minimal_agent.py:8`

```python
import os, sys, json, time, ast, operator, math
```

`os` 在整个文件中没有被使用。这是前轮修复时遗留的（之前可能在某处使用过）。

**建议**: 从 import 中移除 `os`。

---

### P2-3: cli.py 重复导入 hashlib 和 time

**文件**: `mimo-harness/mimo_harness/cli.py:82-83`

```python
from .context import Session
import hashlib, time
```

`hashlib` 和 `time` 在函数内部再次导入，而它们已经在 `agent.py` 的模块级别导入。虽然 Python 的导入缓存机制不会造成性能问题，但在函数体内导入标准库模块不够整洁。

**建议**: 将 `import hashlib, time` 移到文件顶部，或直接使用 `agent.py` 中已有的导入。

---

## 安全审查

经过三轮修复，安全状况良好：

| 安全项 | 状态 |
|--------|------|
| eval()/exec() 替换 | ✅ 全部使用 AST 沙箱 / subprocess 隔离 |
| 路径遍历防护 | ✅ read_file / write_file / edit_file 均有校验 |
| 输出目录沙箱 | ✅ doc_tools 已添加校验 |
| Shell 注入防护 | ✅ chaining 检测 + echo 移除 |
| SSRF 防护 | ✅ web_fetch URL 校验（scheme + private IP） |
| 权限门控 | ✅ 三级权限 + 交互确认 |
| API Key 暴露 | ✅ 全部使用 `***configured***` |

---

## 代码质量总览

| 模块 | 行数 | 质量 | 备注 |
|------|------|------|------|
| config.py | 23 | ✅ | 清晰简洁 |
| stage-1 | 195 | ✅ | P2-2 有未用 import |
| stage-2 | 282 | ✅ | 完整的 RAG 流程 |
| stage-3 | 322 | ✅ | Harness 模式良好 |
| stage-4 | 177 | ✅ | 多 Agent pipeline |
| stage-5 | 166 | ✅ | Skill 框架 |
| stage-6 | 163 | ✅ | Playwright 集成 |
| stage-7 | 242 | ✅ | 评估框架 |
| stage-8 | 278 | ✅ | 生产级特性 |
| mimo-harness | ~1200 | ✅ | 完整 harness |

**总体评估**: 代码库在经过三轮审查和修复后，已达到生产可用水平。剩余 3 个 P2 项均为代码整洁度问题，不影响功能或安全。

---

## 总结

| 轮次 | P0 | P1 | P2 | 总计 |
|------|----|----|----|----|
| 第一轮 | 6 | 6 | 6 | 18 |
| 第二轮 | 4 | 4 | 3 | 11 |
| 第三轮 | 0 | 0 | 3 | 3 |
| **累计** | **10** | **10** | **12** | **32** |

当前未修复：3 项 P2（代码整洁度）。
