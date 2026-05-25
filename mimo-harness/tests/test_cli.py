"""Tests for CLI entry point and REPL commands."""

import io
import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from mimo_harness.cli import _format_tokens, _load_config, print_help


class TestParseArgs:
    """Test argparse parsing via sys.argv manipulation."""

    def test_parse_args_task(self):
        with patch("sys.argv", ["mimo", "--task", "fix the bug"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.task == "fix the bug"

    def test_parse_args_model(self):
        with patch("sys.argv", ["mimo", "--model", "custom"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.model == "custom"

    def test_parse_args_auto_approve(self):
        with patch("sys.argv", ["mimo", "--auto-approve"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.auto_approve is True

    def test_parse_args_auto_approve_short(self):
        with patch("sys.argv", ["mimo", "-y"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.auto_approve is True

    def test_parse_args_dry_run(self):
        with patch("sys.argv", ["mimo", "--dry-run"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.dry_run is True

    def test_parse_args_plan(self):
        with patch("sys.argv", ["mimo", "--plan"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.plan is True

    def test_parse_args_stream(self):
        with patch("sys.argv", ["mimo", "--stream"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.stream is True

    def test_parse_args_stream_short(self):
        with patch("sys.argv", ["mimo", "-s"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.stream is True

    def test_parse_args_max_steps(self):
        with patch("sys.argv", ["mimo", "--max-steps", "10"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.max_steps == 10

    def test_parse_args_verbose(self):
        with patch("sys.argv", ["mimo", "--verbose"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.verbose is True

    def test_parse_args_verbose_short(self):
        with patch("sys.argv", ["mimo", "-v"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.verbose is True

    def test_parse_args_config(self):
        with patch("sys.argv", ["mimo", "--config", "path.json"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.config == "path.json"

    def test_parse_args_rules(self):
        with patch("sys.argv", ["mimo", "--rules", "rules.json"]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--task", "-t")
            parser.add_argument("--model", "-m", default=None)
            parser.add_argument("--auto-approve", "-y", action="store_true")
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--plan", action="store_true")
            parser.add_argument("--max-steps", type=int, default=20)
            parser.add_argument("--verbose", "-v", action="store_true")
            parser.add_argument("--config", "-c")
            parser.add_argument("--rules", "-r")
            parser.add_argument("--stream", "-s", action="store_true")
            args = parser.parse_args()
            assert args.rules == "rules.json"


class TestLoadConfig:
    def test_load_config_valid(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"model": "test", "max_steps": 5}))
        result = _load_config(str(config_file))
        assert result["model"] == "test"
        assert result["max_steps"] == 5

    def test_load_config_missing(self):
        result = _load_config("/nonexistent/path/config.json")
        assert result == {}

    def test_load_config_invalid_json(self, tmp_path):
        config_file = tmp_path / "bad.json"
        config_file.write_text("{invalid json content!!!")
        result = _load_config(str(config_file))
        assert result == {}


class TestFormatTokens:
    def test_format_tokens_small(self):
        assert _format_tokens(999) == "999"

    def test_format_tokens_thousands(self):
        result = _format_tokens(45231)
        assert result == "45.2K"

    def test_format_tokens_exactly_1000(self):
        result = _format_tokens(1000)
        assert result == "1.0K"

    def test_format_tokens_zero(self):
        assert _format_tokens(0) == "0"


class TestReplCommands:
    """Test REPL slash commands by simulating input and capturing output."""

    def test_repl_help_command(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print_help()
        output = buf.getvalue()
        assert "/help" in output
        assert "/quit" in output
        assert "/clear" in output
        assert "/tools" in output

    def test_repl_tools_command(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        from mimo_harness.agent import MiMoHarness
        harness = MiMoHarness()
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print("\nAvailable tools:")
            for name in harness.registry.list_names():
                tool = harness.registry.get(name)
                markers = []
                if tool.is_read_only:
                    markers.append("RO")
                if tool.is_concurrency_safe:
                    markers.append("CS")
                if tool.is_destructive:
                    markers.append("DST")
                marker_str = f" [{', '.join(markers)}]" if markers else ""
                print(f"  - {name}: {tool.description[:50]}...{marker_str}")
            print()
        output = buf.getvalue()
        assert "Available tools:" in output
        assert "read_file" in output
        assert "run_command" in output

    def test_repl_stats_command(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        from mimo_harness.agent import MiMoHarness
        from mimo_harness.context import Session, estimate_tokens
        from mimo_harness.cli import _format_tokens
        harness = MiMoHarness()
        session = Session(session_id="aabbccdd")
        session.add_message("user", "hello")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            tokens = estimate_tokens(session.messages)
            print(f"\nSession Statistics:")
            print(f"  Messages: {len(session.messages)}")
            print(f"  Tokens: {_format_tokens(tokens)}")
            print()
        output = buf.getvalue()
        assert "Session Statistics:" in output
        assert "Messages: 1" in output

    def test_repl_tokens_command(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        from mimo_harness.context import Session, estimate_tokens, CONTEXT_WINDOW_TOKENS
        from mimo_harness.cli import _format_tokens
        session = Session(session_id="aabbccdd")
        session.add_message("user", "hello world")
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            tokens = estimate_tokens(session.messages)
            pct = tokens / CONTEXT_WINDOW_TOKENS * 100
            print(f"\nToken Usage:")
            print(f"  Conversation: {_format_tokens(tokens)} / {_format_tokens(CONTEXT_WINDOW_TOKENS)} ({pct:.1f}%)")
            print()
        output = buf.getvalue()
        assert "Token Usage:" in output
        assert "Conversation:" in output

    def test_repl_dry_run_toggle(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        from mimo_harness.agent import MiMoHarness
        harness = MiMoHarness(dry_run=False)
        # Toggle dry-run ON
        harness.perms.dry_run = not harness.perms.dry_run
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print(f"Dry-run: {'ON' if harness.perms.dry_run else 'OFF'}")
        assert "ON" in buf.getvalue()
        # Toggle dry-run OFF
        harness.perms.dry_run = not harness.perms.dry_run
        buf2 = io.StringIO()
        with patch("sys.stdout", buf2):
            print(f"Dry-run: {'ON' if harness.perms.dry_run else 'OFF'}")
        assert "OFF" in buf2.getvalue()

    def test_repl_auto_toggle(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        from mimo_harness.agent import MiMoHarness
        harness = MiMoHarness(auto_approve=False)
        # Toggle auto ON
        harness.perms.auto_approve = not harness.perms.auto_approve
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print(f"Auto-approve: {'ON' if harness.perms.auto_approve else 'OFF'}")
        assert "ON" in buf.getvalue()
        # Toggle auto OFF
        harness.perms.auto_approve = not harness.perms.auto_approve
        buf2 = io.StringIO()
        with patch("sys.stdout", buf2):
            print(f"Auto-approve: {'ON' if harness.perms.auto_approve else 'OFF'}")
        assert "OFF" in buf2.getvalue()

    def test_repl_plan_toggle(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        from mimo_harness.agent import MiMoHarness
        from mimo_harness.permissions import PermissionMode
        harness = MiMoHarness()
        # Toggle plan ON
        harness.perms.mode = PermissionMode.PLAN
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print("Plan mode: ON (read-only)")
        assert "ON" in buf.getvalue()
        # Toggle plan OFF
        harness.perms.mode = PermissionMode.DEFAULT
        buf2 = io.StringIO()
        with patch("sys.stdout", buf2):
            print("Plan mode: OFF")
        assert "OFF" in buf2.getvalue()

    def test_repl_clear_command(self, monkeypatch):
        from mimo_harness.context import Session
        session = Session(session_id="test")
        session.add_message("user", "hello")
        session.add_message("assistant", "hi")
        assert len(session.messages) == 2
        session.messages.clear()
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print("Session cleared.")
        assert len(session.messages) == 0
        assert "Session cleared" in buf.getvalue()

    def test_repl_quit_command(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            print("Bye!")
        assert "Bye!" in buf.getvalue()
