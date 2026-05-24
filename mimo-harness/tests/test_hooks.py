"""Tests for the hook system (Ch8 patterns)."""

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


class TestHookEvent:
    def test_core_events(self):
        assert HookEvent.PRE_TOOL_USE.value == "PreToolUse"
        assert HookEvent.POST_TOOL_USE.value == "PostToolUse"
        assert HookEvent.STOP.value == "Stop"
        assert HookEvent.SESSION_START.value == "SessionStart"
        assert HookEvent.SESSION_END.value == "SessionEnd"
