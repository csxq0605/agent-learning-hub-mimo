#!/usr/bin/env python3
"""
Nexgent Agent 自主循环 Demo

用法:
    cd nexgent
    python demo_run.py

展示:
    1. Agent 读取内部知识库（AGENTS.md、docs/）
    2. Agent 自主分析代码，发现 TODO
    3. Agent 实现代码级修改
    4. Agent 运行测试 → 失败 → 修复 → 重试循环
    5. 最终结果
"""

import os
import sys
import shutil
import subprocess

# ── 配置 ──────────────────────────────────────────────────
DEMO_DIR = os.path.join(os.path.dirname(__file__), "demo-project")
DEMO_COPY = os.path.join(os.path.dirname(__file__), ".demo-work")

TASK = """
你在一个 Python 项目的 demo-project/ 目录下工作（实际路径: {work_dir}）。

任务：实现 auth 模块中所有标记为 TODO 的功能。

具体要求：
1. 先读取 AGENTS.md 了解项目架构
2. 读取 docs/api-spec.md 了解 API 规范
3. 读取 docs/architecture.md 了解安全要求
4. 阅读 src/utils/security.py、src/auth/service.py、src/auth/routes.py 中的 TODO 注释
5. 实现所有 TODO 功能：
   - security.py: is_token_blacklisted(), blacklist_token(), blacklist_all_user_tokens()
   - service.py: refresh(), revoke(), logout()
   - routes.py: /refresh, /revoke, /logout 路由
6. 运行 pytest tests/test_auth.py -v 验证
7. 如果有测试失败，分析原因并修复，然后重新运行
8. 循环直到所有 15 个测试全部通过
"""


def setup_demo():
    """复制 demo 项目到工作目录（避免污染原文件）。"""
    if os.path.exists(DEMO_COPY):
        shutil.rmtree(DEMO_COPY)
    shutil.copytree(DEMO_DIR, DEMO_COPY)
    print(f"[SETUP] Demo 项目复制到 {DEMO_COPY}")
    return DEMO_COPY


def run_baseline(work_dir):
    """运行基线测试，展示 TODO 项 skip。"""
    print("\n" + "=" * 60)
    print("[基线] 运行测试 — 预期 10 passed, 5 skipped")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_auth.py", "-v", "--tb=line"],
        cwd=work_dir,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        # 只打印非 warning 的 stderr
        for line in result.stderr.split("\n"):
            if "warning" not in line.lower() and "deprecat" not in line.lower():
                print(line, file=sys.stderr)
    return result.returncode


def run_agent(work_dir):
    """运行 Nexgent Agent 自主实现 TODO。"""
    print("\n" + "=" * 60)
    print("[Agent] 启动 Nexgent Agent 自主实现...")
    print("=" * 60)

    # 切换到 demo 工作目录
    original_cwd = os.getcwd()
    os.chdir(work_dir)

    try:
        # 加载 .env
        from dotenv import load_dotenv
        load_dotenv(os.path.join(original_cwd, ".env"))

        from nexgent.agent import NexgentAgent

        harness = NexgentAgent(
            model=os.getenv("MIMO_MODEL", "mimo-v2.5-pro"),
            auto_approve=True,
            stream=False,
            bare=False,
            verbose=False,
        )

        task = TASK.format(work_dir=work_dir)
        result = harness.run(task)
        return result

    except Exception as e:
        print(f"\n[ERROR] Agent 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        os.chdir(original_cwd)


def run_final(work_dir):
    """运行最终测试，验证所有测试通过。"""
    print("\n" + "=" * 60)
    print("[验证] 运行最终测试 — 预期 15 passed")
    print("=" * 60)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_auth.py", "-v", "--tb=short"],
        cwd=work_dir,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    return result.returncode


def cleanup():
    """清理工作目录。"""
    if os.path.exists(DEMO_COPY):
        shutil.rmtree(DEMO_COPY)
        print(f"\n[CLEANUP] 已清理 {DEMO_COPY}")


def main():
    print("=" * 60)
    print("  Nexgent Agent 自主循环 Demo")
    print("  展示: Agent 在内部知识库中自主实现代码级功能")
    print("=" * 60)

    # 1. 准备工作目录
    work_dir = setup_demo()

    # 2. 基线测试
    run_baseline(work_dir)

    # 3. Agent 自主实现
    print("\n" + "─" * 60)
    print("  Agent 将读取知识库、分析代码、自主实现 TODO 功能")
    print("  这是一个真实的 Agent 自主循环，无人工干预")
    print("─" * 60)

    agent_result = run_agent(work_dir)

    # 4. 最终验证
    exit_code = run_final(work_dir)

    # 5. 总结
    print("\n" + "=" * 60)
    print("  Demo 结果")
    print("=" * 60)
    if exit_code == 0:
        print("  ✅ 所有测试通过 — Agent 自主实现成功!")
    else:
        print("  ❌ 部分测试失败 — 查看上方输出")
    print(f"  工作目录: {work_dir}")
    print(f"  Agent 返回: {str(agent_result)[:200] if agent_result else '(无)'}")
    print("=" * 60)

    # 6. 清理
    try:
        input("\n按 Enter 清理工作目录，Ctrl+C 保留...")
        cleanup()
    except KeyboardInterrupt:
        print(f"\n保留工作目录: {work_dir}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
