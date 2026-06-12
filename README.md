# Agent Learning Hub - MiMo

基于 [Agent Learning Hub](https://github.com/datawhalechina/Agent-Learning-Hub) 学习路线，使用小米 MiMo 模型完成 Stage 0-8 实践，并构建生产级 Agent Harness。

## 模型配置

| 配置项 | 值 |
|--------|-----|
| Base URL | `https://token-plan-cn.xiaomimimo.com/v1` |
| Model | `mimo-v2.5-pro` |

## 阶段概览

| Stage | 主题 | 交付物 |
|-------|------|--------|
| 0 | 理论基础 | 学习笔记 |
| 1 | 最小 Agent | ~220 行 Python agent |
| 2 | RAG 研究助手 | 研究助手 agent |
| 3 | Agent Harness | Harness 演示 |
| 4 | 多 Agent 协作 | 多 agent 写作系统 |
| 5 | Skill 框架 | Code Review Skill |
| 6 | 浏览器自动化 | 浏览器研究 agent |
| 7 | 评估框架 | 评估运行器 |
| 8 | 生产级 DevOps Agent | DevOps agent |

## Agent Hub

基于 Stage 0-8 经验构建的生产级模型无关 Agent Harness，参考 Claude Code 架构。

**核心特性**：Agent Loop、30 个工具、权限管线、安全管线、上下文管理、记忆系统、会话管理、Hook 系统、SubAgent、Skills、MCP 支持、TUI、CLI、自定义智能体、后台任务、@文件引用、目标管理

详见 [agent-hub/README.md](agent-hub/README.md)。

## 快速开始

```bash
git clone https://github.com/csxq0605/Agent-Learning-Hub-MiMo.git
cd Agent-Learning-Hub-MiMo/agent-hub
pip install -e .

# 配置 .env
echo 'MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1' > .env
echo 'MIMO_API_KEY=your-api-key-here' >> .env
echo 'MIMO_MODEL=mimo-v2.5-pro' >> .env

ah          # 进入交互模式
```

## 测试

| 类型 | 数量 |
|------|------|
| 单元测试 | 928 |
| E2E 测试 | 73（57 fast + 16 slow） |
| Stage 测试 | 83 |

```bash
cd agent-hub
pip install -e ".[dev]"
python -m pytest tests/ --ignore=tests/test_e2e.py -v  # 单元测试
python -m pytest tests/test_e2e.py -v                    # E2E fast
python -m pytest tests/test_e2e.py -v --run-slow         # E2E fast + slow
python run_tests.py --all                                 # 全部
```

## CI/CD

- **unit-tests**: push/PR 自动运行，Python 3.10-3.13
- **e2e-fast/e2e-full**: 仅手动触发

## License

MIT License
