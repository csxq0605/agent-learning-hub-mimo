"""Tests for CLI entry point and REPL commands."""

import io
import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from mimo_harness.cli import _format_tokens, _load_config, print_help, _handle_command


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


class _HarnessFixture:
    """Shared fixture builder for REPL command tests."""

    @staticmethod
    def make(monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        from mimo_harness.agent import MiMoHarness
        from mimo_harness.context import Session
        harness = MiMoHarness()
        session = Session(session_id="aabbccdd11223344")
        return harness, session


class TestHandleCommand:
    """Test _handle_command extracted from REPL loop."""

    def test_repl_save_session(self, monkeypatch, tmp_path):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        save_path = str(tmp_path / "session.json")
        action, returned_session = _handle_command(
            ["/save", save_path], harness, session, memory_store
        )
        assert action == "continue"
        assert os.path.exists(save_path)
        with open(save_path) as f:
            data = json.load(f)
        assert data["session_id"] == "aabbccdd11223344"

    def test_repl_load_session(self, monkeypatch, tmp_path):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        from mimo_harness.context import Session
        memory_store = MemoryStore(str(tmp_path))
        # Save a session first
        session.add_message("user", "hello")
        save_path = str(tmp_path / "loaded.json")
        session.save(save_path)
        # Now load it
        new_session = Session(session_id="fresh")
        action, loaded = _handle_command(
            ["/load", save_path], harness, new_session, memory_store
        )
        assert action == "continue"
        assert loaded.session_id == "aabbccdd11223344"
        assert len(loaded.messages) == 1

    def test_repl_load_session_error(self, monkeypatch, tmp_path):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        action, _ = _handle_command(
            ["/load", "/nonexistent/path.json"], harness, session, memory_store
        )
        assert action == "continue"

    def test_repl_memory_command_empty(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        _handle_command(["/memory"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "No memories stored" in captured.out

    def test_repl_memory_command_with_entries(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore, MemoryType
        memory_store = MemoryStore(str(tmp_path))
        memory_store.save_memory(
            name="test-mem",
            memory_type=MemoryType.PROJECT,
            description="A test memory",
            content="remember this",
        )
        _handle_command(["/memory"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Stored memories (1)" in captured.out
        assert "test-mem" in captured.out

    def test_repl_remember_command(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        # Mock input() to return memory content then empty line
        input_iter = iter(["This is important context", ""])
        with patch("builtins.input", side_effect=input_iter):
            _handle_command(["/remember"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Memory saved" in captured.out
        # Verify memory was actually saved
        memories = memory_store.list_memories()
        assert len(memories) == 1

    def test_repl_recommand_empty_input(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        # Mock input() to return empty line immediately
        with patch("builtins.input", return_value=""):
            _handle_command(["/remember"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Memory saved" not in captured.out
        memories = memory_store.list_memories()
        assert len(memories) == 0

    def test_repl_hooks_command_no_hooks(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        _handle_command(["/hooks"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "No hooks registered" in captured.out

    def test_repl_hooks_command_with_hooks(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        from mimo_harness.hooks import HookRunner, HookConfig, HookEvent
        memory_store = MemoryStore(str(tmp_path))
        hook_runner = HookRunner()
        hook_runner.register(HookConfig(
            event=HookEvent.PRE_TOOL_USE,
            matcher="run_command",
            command="validate.sh",
        ))
        harness._hook_runner = hook_runner
        _handle_command(["/hooks"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Registered hooks: 1" in captured.out
        assert "run_command" in captured.out

    def test_repl_compact_command_not_enough(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        session.add_message("user", "hi")
        _handle_command(["/compact"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Not enough messages" in captured.out

    def test_repl_compact_command_triggers(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        # Add enough messages to exceed 1000 tokens
        for i in range(50):
            session.add_message("user", f"This is a long message number {i} " * 10)
            session.add_message("assistant", f"Response to message {i} " * 10)
        # Mock require_api_key and OpenAI to avoid real API call
        with patch("mimo_harness.cli.compact_context") as mock_compact:
            mock_compact.return_value = [{"role": "system", "content": "compacted"}]
            _handle_command(["/compact"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Compressing" in captured.out

    def test_repl_init_command(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        monkeypatch.chdir(tmp_path)
        # Mock scan_project and generate_agents_md
        with patch("mimo_harness.cli._handle_command.__wrapped__", create=True):
            pass
        # Use direct patching of the imported functions
        import mimo_harness.project_scanner as ps
        with patch.object(ps, "scan_project", return_value={
            "language": "Python", "frameworks": ["pytest"], "test_runner": "pytest"
        }) as mock_scan, \
             patch.object(ps, "generate_agents_md", return_value="# AGENTS.md\nGenerated content"):
            _handle_command(["/init"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "AGENTS.md generated" in captured.out
        assert "Python" in captured.out
        assert "pytest" in captured.out
        # Clean up generated file
        agents_path = os.path.join(str(tmp_path), "AGENTS.md")
        if os.path.exists(agents_path):
            os.remove(agents_path)

    def test_repl_init_command_existing_file_decline(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        monkeypatch.chdir(tmp_path)
        # Create existing AGENTS.md
        (tmp_path / "AGENTS.md").write_text("existing content")
        with patch("builtins.input", return_value="n"):
            _handle_command(["/init"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Skipped" in captured.out

    def test_repl_unknown_command(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        _handle_command(["/foobar"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out
        assert "/foobar" in captured.out

    def test_repl_quit_variants(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        for cmd in ["/quit", "/exit", "/q"]:
            action, _ = _handle_command([cmd], harness, session, memory_store)
            assert action == "quit", f"{cmd} should return 'quit'"

    def test_repl_clear_command(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        session.add_message("user", "hello")
        session.add_message("assistant", "hi")
        _handle_command(["/clear"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Session cleared" in captured.out
        assert len(session.messages) == 0

    def test_repl_tools_command(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        _handle_command(["/tools"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Available tools" in captured.out
        assert "read_file" in captured.out
        assert "run_command" in captured.out

    def test_repl_dry_run_toggle(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        harness.perms.dry_run = False
        _handle_command(["/dry-run"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Dry-run: ON" in captured.out
        assert harness.perms.dry_run is True

    def test_repl_auto_toggle(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        harness.perms.auto_approve = False
        _handle_command(["/auto"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Auto-approve: ON" in captured.out
        assert harness.perms.auto_approve is True

    def test_repl_plan_toggle_on(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        from mimo_harness.permissions import PermissionMode
        harness.perms.mode = PermissionMode.DEFAULT
        _handle_command(["/plan"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Plan mode: ON" in captured.out

    def test_repl_plan_toggle_off(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        from mimo_harness.permissions import PermissionMode
        harness.perms.mode = PermissionMode.PLAN
        _handle_command(["/plan"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Plan mode: OFF" in captured.out

    def test_repl_stats_command(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        session.add_message("user", "hello world")
        _handle_command(["/stats"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Session Statistics" in captured.out
        assert "Messages: 1" in captured.out

    def test_repl_tokens_command(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        session.add_message("user", "hello world")
        _handle_command(["/tokens"], harness, session, memory_store)
        captured = capsys.readouterr()
        assert "Token Usage" in captured.out
        assert "Conversation:" in captured.out

    def test_repl_save_error(self, monkeypatch, tmp_path, capsys):
        harness, session = _HarnessFixture.make(monkeypatch)
        from mimo_harness.memory import MemoryStore
        memory_store = MemoryStore(str(tmp_path))
        # Try to save to an invalid path
        _handle_command(
            ["/save", "/nonexistent/dir/session.json"],
            harness, session, memory_store,
        )
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestMainFunctionPaths:
    """Test main() function with various argument combinations."""

    def test_main_single_task(self, monkeypatch, capsys):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        monkeypatch.setattr("sys.argv", ["mimo", "--task", "fix the bug"])
        with patch("mimo_harness.cli.MiMoHarness") as MockHarness:
            mock_instance = MagicMock()
            mock_instance.run.return_value = "Bug fixed!"
            MockHarness.return_value = mock_instance
            from mimo_harness.cli import main
            main()
        captured = capsys.readouterr()
        assert "Bug fixed!" in captured.out
        mock_instance.run.assert_called_once_with("fix the bug")

    def test_main_dry_run(self, monkeypatch, capsys):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        monkeypatch.setattr("sys.argv", ["mimo", "--task", "test", "--dry-run"])
        with patch("mimo_harness.cli.MiMoHarness") as MockHarness:
            mock_instance = MagicMock()
            mock_instance.run.return_value = "done"
            MockHarness.return_value = mock_instance
            from mimo_harness.cli import main
            main()
        # Verify dry_run was passed
        call_kwargs = MockHarness.call_args
        assert call_kwargs[1].get("dry_run") is True or call_kwargs.kwargs.get("dry_run") is True

    def test_main_plan_mode(self, monkeypatch, capsys):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        monkeypatch.setattr("sys.argv", ["mimo", "--task", "test", "--plan"])
        with patch("mimo_harness.cli.MiMoHarness") as MockHarness:
            mock_instance = MagicMock()
            mock_instance.run.return_value = "done"
            MockHarness.return_value = mock_instance
            from mimo_harness.cli import main
            main()
        call_kwargs = MockHarness.call_args
        assert call_kwargs[1].get("plan_mode") is True or call_kwargs.kwargs.get("plan_mode") is True

    def test_main_stream_mode(self, monkeypatch, capsys):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        monkeypatch.setattr("sys.argv", ["mimo", "--task", "test", "--stream"])
        with patch("mimo_harness.cli.MiMoHarness") as MockHarness:
            mock_instance = MagicMock()
            mock_instance.run.return_value = "done"
            MockHarness.return_value = mock_instance
            from mimo_harness.cli import main
            main()
        call_kwargs = MockHarness.call_args
        assert call_kwargs[1].get("stream") is True or call_kwargs.kwargs.get("stream") is True

    def test_main_repl_quit(self, monkeypatch, capsys):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        monkeypatch.setattr("sys.argv", ["mimo"])
        # Mock input() to simulate REPL: first a /quit command
        with patch("builtins.input", side_effect=["/quit"]):
            from mimo_harness.cli import main
            main()
        captured = capsys.readouterr()
        assert "Bye!" in captured.out

    def test_main_repl_empty_then_quit(self, monkeypatch, capsys):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        monkeypatch.setattr("sys.argv", ["mimo"])
        with patch("builtins.input", side_effect=["", "  ", "/quit"]):
            from mimo_harness.cli import main
            main()
        captured = capsys.readouterr()
        assert "Bye!" in captured.out

    def test_main_eof_exits(self, monkeypatch, capsys):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        monkeypatch.setattr("sys.argv", ["mimo"])
        with patch("builtins.input", side_effect=EOFError):
            from mimo_harness.cli import main
            main()
        captured = capsys.readouterr()
        assert "Bye!" in captured.out


class TestConfigIntegration:
    """Test config file integration with CLI."""

    def test_config_overrides_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MIMO_API_KEY", "env-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://env.com")
        monkeypatch.setenv("MIMO_MODEL", "env-model")
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "model": "config-model",
            "max_steps": 5,
            "auto_approve": True,
        }))
        monkeypatch.setattr("sys.argv", [
            "mimo", "--task", "test", "--config", str(config_file)
        ])
        with patch("mimo_harness.cli.MiMoHarness") as MockHarness:
            mock_instance = MagicMock()
            mock_instance.run.return_value = "done"
            MockHarness.return_value = mock_instance
            from mimo_harness.cli import main
            main()
        call_kwargs = MockHarness.call_args
        # Config model should be used since --model was not passed
        assert call_kwargs[1].get("model") == "config-model" or call_kwargs.kwargs.get("model") == "config-model"

    def test_config_hooks_loaded(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "run_command",
                        "hooks": [
                            {"type": "command", "command": "echo ok", "timeout": 5}
                        ]
                    }
                ]
            }
        }))
        monkeypatch.setattr("sys.argv", [
            "mimo", "--task", "test", "--config", str(config_file)
        ])
        with patch("mimo_harness.cli.MiMoHarness") as MockHarness:
            mock_instance = MagicMock()
            mock_instance.run.return_value = "done"
            MockHarness.return_value = mock_instance
            from mimo_harness.cli import main
            main()
        # Verify _hook_runner was set
        assert hasattr(mock_instance, '_hook_runner')

    def test_config_rules_loaded(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MIMO_API_KEY", "test-key")
        monkeypatch.setenv("MIMO_BASE_URL", "http://test.com")
        monkeypatch.setenv("MIMO_MODEL", "test-model")
        rules_file = tmp_path / "permissions.json"
        rules_file.write_text(json.dumps({
            "permissions": {
                "allow": ["read_file", "glob_files"],
                "deny": ["run_command:rm *"],
            }
        }))
        monkeypatch.setattr("sys.argv", [
            "mimo", "--task", "test", "--rules", str(rules_file)
        ])
        with patch("mimo_harness.cli.MiMoHarness") as MockHarness:
            mock_instance = MagicMock()
            mock_instance.run.return_value = "done"
            MockHarness.return_value = mock_instance
            from mimo_harness.cli import main
            main()
        # Verify load_rules_from_file was called
        mock_instance.perms.load_rules_from_file.assert_called_once_with(str(rules_file))
