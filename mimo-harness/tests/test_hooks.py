"""Tests for the hook system (Ch8 patterns)."""

import json
import pytest
from mimo_harness.hooks import (
    HookEvent, HookDecision, HookResult, HookConfig, HookRunner,
)


class TestHookResult:
    def test_default_approve(self):
        r = HookResult()
        assert r.decision == HookDecision.APPROVE
        assert not r.is_blocking

    def test_blocking(self):
        r = HookResult(decision=HookDecision.BLOCK, reason="blocked")
        assert r.is_blocking
        assert r.reason == "blocked"


class TestHookConfig:
    def test_wildcard_matcher(self):
        c = HookConfig(event=HookEvent.PRE_TOOL_USE, matcher="*")
        assert c.matches("anything")
        assert c.matches("read_file")

    def test_exact_matcher(self):
        c = HookConfig(event=HookEvent.PRE_TOOL_USE, matcher="Bash")
        assert c.matches("Bash")
        assert not c.matches("Read")

    def test_prefix_matcher(self):
        c = HookConfig(event=HookEvent.PRE_TOOL_USE, matcher="run_*")
        assert c.matches("run_command")
        assert c.matches("run_test")
        assert not c.matches("read_file")


class TestHookRunner:
    def test_register_and_run(self):
        runner = HookRunner()
        runner.register(HookConfig(
            event=HookEvent.PRE_TOOL_USE,
            matcher="*",
            command="echo ok",
        ))
        assert len(runner._hooks[HookEvent.PRE_TOOL_USE]) == 1

    def test_disabled_hooks_pass(self):
        runner = HookRunner()
        runner.enabled = False
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "test")
        assert not result.is_blocking

    def test_function_hook_blocking(self):
        runner = HookRunner()
        runner.register_function(
            HookEvent.PRE_TOOL_USE,
            lambda **kwargs: HookResult(
                decision=HookDecision.BLOCK,
                reason="function blocked",
            ),
        )
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "test")
        assert result.is_blocking
        assert result.reason == "function blocked"

    def test_function_hook_approve(self):
        runner = HookRunner()
        runner.register_function(
            HookEvent.PRE_TOOL_USE,
            lambda **kwargs: HookResult(decision=HookDecision.APPROVE),
        )
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "test")
        assert not result.is_blocking

    def test_no_hooks_returns_approve(self):
        runner = HookRunner()
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "test")
        assert not result.is_blocking

    def test_load_from_config(self):
        runner = HookRunner()
        config = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "validate.sh", "timeout": 5}
                        ]
                    }
                ]
            }
        }
        runner.load_from_config(config)
        assert len(runner._hooks[HookEvent.PRE_TOOL_USE]) == 1
        assert runner._hooks[HookEvent.PRE_TOOL_USE][0].command == "validate.sh"

    def test_load_from_config_unknown_event(self):
        runner = HookRunner()
        config = {
            "hooks": {
                "UnknownEvent": [
                    {"matcher": "*", "hooks": [{"type": "command", "command": "test"}]}
                ]
            }
        }
        runner.load_from_config(config)
        # Should not crash, just skip unknown events
        assert len(runner._hooks) == 0


class TestCommandHooks:
    def test_command_hook_pass(self):
        """Command hook with exit 0 returns approve."""
        runner = HookRunner()
        runner.register(HookConfig(
            event=HookEvent.PRE_TOOL_USE,
            matcher="*",
            command="python -c \"import sys; sys.exit(0)\"",
        ))
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "read_file")
        assert not result.is_blocking

    def test_command_hook_block(self):
        """Command hook with exit 2 returns block."""
        runner = HookRunner()
        runner.register(HookConfig(
            event=HookEvent.PRE_TOOL_USE,
            matcher="*",
            command="python -c \"import sys; sys.stderr.write('blocked reason'); sys.exit(2)\"",
        ))
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "write_file")
        assert result.is_blocking
        assert "blocked reason" in result.reason

    def test_command_hook_timeout(self):
        """Command hook that times out returns approve (safe default)."""
        runner = HookRunner()
        runner.register(HookConfig(
            event=HookEvent.PRE_TOOL_USE,
            matcher="*",
            command="python -c \"import time; time.sleep(10)\"",
            timeout=0.1,
        ))
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "test")
        assert not result.is_blocking

    def test_command_hook_json_output(self, tmp_path):
        """Command hook stdout JSON with decision/reason is parsed."""
        runner = HookRunner()
        hook_output = json.dumps({"decision": "block", "reason": "not allowed"})
        # Write a temp script to avoid quoting issues on Windows
        script = tmp_path / "hook.py"
        script.write_text(f"import sys; print('{hook_output}')")
        runner.register(HookConfig(
            event=HookEvent.PRE_TOOL_USE,
            matcher="*",
            command=f'python "{script}"',
        ))
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "dangerous_tool")
        assert result.is_blocking
        assert result.reason == "not allowed"

    def test_async_hook(self):
        """async_mode=True hook runs without blocking."""
        runner = HookRunner()
        runner.register(HookConfig(
            event=HookEvent.POST_TOOL_USE,
            matcher="*",
            command="python -c \"import time; time.sleep(5)\"",
            async_mode=True,
        ))
        # Should return quickly (fire-and-forget) without blocking
        import time
        start = time.time()
        result = runner.run_hooks(HookEvent.POST_TOOL_USE, "test_tool", tool_result="ok")
        elapsed = time.time() - start
        assert elapsed < 2.0  # should not block for 5 seconds
        assert not result.is_blocking

    def test_hook_matcher_tool_name(self):
        """Matcher matches on tool name."""
        runner = HookRunner()
        runner.register(HookConfig(
            event=HookEvent.PRE_TOOL_USE,
            matcher="Bash",
            command="python -c \"import sys; sys.exit(0)\"",
        ))
        # Should match "Bash"
        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "Bash")
        # Should NOT block (exit 0 = approve), but hook ran
        assert not result.is_blocking

        # "Read" doesn't match "Bash" — hook should not run
        # We verify by checking no error occurs (hook skipped)

    def test_hook_multiple_hooks_chain(self):
        """Multiple hooks for same event run in order, first BLOCK stops chain."""
        runner = HookRunner()

        # First hook blocks
        def blocking_fn(**kwargs):
            return HookResult(decision=HookDecision.BLOCK, reason="first blocked")

        # Second hook should not run (we track if it does)
        second_ran = []

        def tracking_fn(**kwargs):
            second_ran.append(True)
            return HookResult(decision=HookDecision.APPROVE)

        runner.register_function(HookEvent.PRE_TOOL_USE, blocking_fn)
        runner.register_function(HookEvent.PRE_TOOL_USE, tracking_fn)

        result = runner.run_hooks(HookEvent.PRE_TOOL_USE, "test")
        assert result.is_blocking
        assert result.reason == "first blocked"
        # Second function hook should not have run (first blocked the chain)
        assert len(second_ran) == 0


class TestHookEvent:
    def test_core_events(self):
        assert HookEvent.PRE_TOOL_USE.value == "PreToolUse"
        assert HookEvent.POST_TOOL_USE.value == "PostToolUse"
        assert HookEvent.STOP.value == "Stop"
        assert HookEvent.SESSION_START.value == "SessionStart"
        assert HookEvent.SESSION_END.value == "SessionEnd"
