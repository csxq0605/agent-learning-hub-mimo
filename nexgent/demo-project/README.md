# Demo — Nexgent Feature Showcase

一个 FastAPI 认证服务。用 Nexgent 来审查代码、修复问题、实现功能。

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

## 手动体验

```
nexgent> Read AGENTS.md
nexgent> Run the tests
nexgent> Review src/auth/admin.py for security issues
nexgent> /parallel Review admin.py | Review rate_limit.py | Review roles.py
nexgent> Fix the most critical bug you found
nexgent> Implement the refresh feature in service.py
nexgent> /goal All tests pass and no NotImplementedError stubs remain
nexgent> /workflow run examples/workflow-full-review.py
nexgent> Remember: we use bcrypt for passwords, never plaintext
nexgent> /mode plan
nexgent> Refactor the admin routes to extract a service layer
```

## 项目结构

```
src/auth/
├── models.py          # SQLAlchemy ORM 模型
├── routes.py          # FastAPI 路由
├── service.py         # 业务逻辑
├── admin.py           # 用户管理接口
├── rate_limit.py      # 限流器
├── audit.py           # 审计日志
├── roles.py           # 权限控制
├── password_reset.py  # 密码重置
├── email_verify.py    # 邮箱验证
└── ...
tests/
└── ...                # 测试套件
```

## 运行测试

```bash
python -m pytest demo-project/tests/ -v
```
