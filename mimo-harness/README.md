# MiMo Harness

基于 Claude Code 架构的生产级 AI Agent Harness，使用小米 MiMo 模型。

## 核心特性

- **Agent Loop**: 依赖注入、熔断器、Token 预算、并行工具调度、流式输出
- **30 个工具**: 文件操作、Shell、代码执行、Web、文档、数学、笔记本、任务、LSP、调度器、计划、监控、交互、子代理
- **权限管线**: 6 种模式，4 阶段管线，TUI 内联提示
- **安全管线**: 2 层防御（regex + 模型分类器），敏感数据脱敏
- **上下文管理**: 1M token 窗口，4 级渐进压缩
- **记忆系统**: 4 类型记忆，分层加载，CLAUDE.md 发现
- **会话管理**: JSONL 自动保存、检查点回滚、会话分叉
- **Hook 系统**: 18 种生命周期事件
- **SubAgent**: 并行/Pipeline 执行，资源限制
- **Skills**: SKILL.md 格式、动态上下文注入、参数替换
- **MCP**: Model Context Protocol 集成，多协议支持
- **TUI**: 全屏 Textual 界面，队列输出架构
- **CLI**: 30+ 斜杠命令，管道输入，多输出格式

## 快速开始

```bash
pip install -e .
cp .env.example .env  # 配置 API key
mimo-harness          # 交互模式
```

## 常用命令

```bash
mimo-harness                          # 交互模式
mimo-harness --task "问题"            # 单次任务
cat file | mimo-harness -p "分析"     # 管道输入
mimo-harness --continue               # 恢复会话
```

## 斜杠命令

| 命令 | 说明 |
|------|------|
| `/help` | 帮助 |
| `/tools` | 列出工具 |
| `/compact` | 压缩上下文 |
| `/rewind` | 回退检查点 |
| `/fork` | 分叉会话 |
| `/stats` | 会话统计 |
| `!<cmd>` | 执行 shell |

## 架构

```
mimo_harness/
├── agent.py          # 核心循环
├── cli.py            # REPL、命令
├── context.py        # 上下文管理
├── permissions.py    # 权限管线
├── security_pipeline.py  # 安全管线
├── memory.py         # 记忆系统
├── hooks.py          # Hook 系统
├── subagent.py       # SubAgent
├── skills.py         # Skills 系统
├── mcp.py            # MCP 支持
├── tui.py            # TUI 界面
├── display.py        # 显示层
└── tools/            # 14 个工具模块
```

## 测试

```bash
pip install -e ".[dev]"
python -m pytest tests/ --ignore=tests/test_e2e.py -v
```

861 单元测试 + 46 E2E 测试，覆盖安全、权限、上下文、工具等。

## License

MIT License
