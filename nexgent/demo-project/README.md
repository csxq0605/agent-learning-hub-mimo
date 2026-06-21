# Demo — Nexgent Feature Showcase

一个 FastAPI 认证服务，有植入的 bug 和未实现的功能。用 Nexgent 来完成这些工作。

## 快速开始

```bash
cd nexgent && pip install -e .
cd demo-project
nexgent
```

## 一键演示

```
nexgent> /demo
```

自动展示：项目理解 → 代码审查 → 修复 bug → 实现功能 → 存储记忆 → 创建规则 → 运行工作流 → 验证结果。

## 手动体验

### 1. 理解项目
```
nexgent> Read AGENTS.md
nexgent> What does this project do?
```

### 2. 发现 bug
```
nexgent> Review src/auth/admin.py for security issues
nexgent> /parallel Review admin.py | Review rate_limit.py | Review roles.py
```

### 3. 修复 bug
```
nexgent> Fix the SQL injection in admin.py
nexgent> /rewind  # 修复错了？回滚
```

### 4. 实现功能
```
nexgent> Implement the refresh feature in service.py
nexgent> /implement password-reset
```

### 5. 自主工作
```
nexgent> /goal All tests pass and no NotImplementedError stubs remain
```

### 6. 工作流
```
nexgent> /workflow run examples/workflow-full-review.py
```

### 7. 记忆和规则
```
nexgent> Remember: we use bcrypt for passwords, never plaintext
nexgent> /memory
```

### 8. 计划模式
```
nexgent> /mode plan
nexgent> Refactor the admin routes to extract a service layer
nexgent> /mode default
```

## 项目结构

| 模块 | 功能 | 状态 |
|------|------|------|
| `auth/` | 注册、登录、JWT 令牌管理 | ✅ 已完成 |
| `admin.py` | 用户管理（列表、停用、改角色） | 🐛 有植入 bug |
| `rate_limit.py` | 滑动窗口限流器 | 🐛 有植入 bug |
| `audit.py` | 安全事件日志 | 🐛 有植入 bug |
| `roles.py` | 基于角色的访问控制 | 🐛 有植入 bug |
| `password_reset.py` | 密码重置流程 | ❌ TODO stub |
| `email_verify.py` | 邮箱验证流程 | ❌ TODO stub |

## 运行测试

```bash
python -m pytest demo-project/tests/ -v
```

46 passed, 5 skipped（TODO 功能的 skip）。

## .nexgent 配置

| 文件 | 功能 |
|------|------|
| `skills/demo.md` | `/demo` 一键演示技能 |
| `AGENTS.md` | 项目知识库（自动加载） |
| `examples/workflow-full-review.py` | 工作流引擎演示 |
