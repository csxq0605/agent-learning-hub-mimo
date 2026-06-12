"""Tests for the Textual TUI interface (agent_hub/tui.py).

Tests the TUI components without launching a full-screen application.
Focuses on the CommandSuggester, history, and tab completion logic.
"""

import asyncio
import threading
import pytest


class TestCommandSuggester:
    """Test the slash command auto-completion suggester."""

    @pytest.fixture
    def suggester(self):
        from agent_hub.tui import CommandSuggester
        return CommandSuggester()

    def test_no_suggestion_for_non_slash(self, suggester):
        result = asyncio.run(suggester.get_suggestion("hello"))
        assert result is None

    def test_single_match(self, suggester):
        result = asyncio.run(suggester.get_suggestion("/he"))
        assert result == "/help"

    def test_no_match(self, suggester):
        result = asyncio.run(suggester.get_suggestion("/zzzzz"))
        assert result is None

    def test_exact_match_no_suggestion(self, suggester):
        result = asyncio.run(suggester.get_suggestion("/help"))
        assert result is None

    def test_multiple_matches_returns_first(self, suggester):
        result = asyncio.run(suggester.get_suggestion("/ex"))
        assert result == "/exit"

    def test_partial_command(self, suggester):
        result = asyncio.run(suggester.get_suggestion("/qui"))
        assert result == "/quit"

    def test_single_char(self, suggester):
        result = asyncio.run(suggester.get_suggestion("/"))
        assert result is not None  # Should return first matching command

    def test_all_slash_commands_have_prefix(self, suggester):
        for cmd in suggester.COMMANDS:
            assert cmd.startswith("/"), f"Command {cmd} doesn't start with /"


class TestStreamBuffer:
    """Test the output queue mechanism."""

    def test_output_queue_exists(self):
        from agent_hub.tui import _output_queue
        import queue
        assert isinstance(_output_queue, queue.Queue)

    def test_queue_put_get(self):
        from agent_hub.tui import _output_queue
        # Drain any existing items
        while not _output_queue.empty():
            try:
                _output_queue.get_nowait()
            except Exception:
                break
        _output_queue.put(("stream", "test"))
        kind, data = _output_queue.get_nowait()
        assert kind == "stream"
        assert data == "test"


class TestTUIImports:
    """Test that TUI module imports correctly."""

    def test_import_mimo_tui(self):
        from agent_hub.tui import MiMoTUI
        assert MiMoTUI is not None

    def test_import_run_tui(self):
        from agent_hub.tui import run_tui
        assert callable(run_tui)

    def test_import_output_queue(self):
        from agent_hub.tui import _output_queue
        import queue
        assert isinstance(_output_queue, queue.Queue)

    def test_import_set_get_app(self):
        from agent_hub.tui import _get_tui_app, _set_tui_app
        assert callable(_get_tui_app)
        assert callable(_set_tui_app)

    def test_default_tui_app_is_none(self):
        from agent_hub.tui import _get_tui_app
        app = _get_tui_app()
        assert app is None


class TestTUIClass:
    """Test MiMoTUI class attributes without launching the app."""

    def test_has_command_list(self):
        from agent_hub.tui import MiMoTUI
        assert hasattr(MiMoTUI, 'COMMANDS')
        assert len(MiMoTUI.COMMANDS) > 20
        assert "/help" in MiMoTUI.COMMANDS
        assert "/quit" in MiMoTUI.COMMANDS
        assert "/effort" in MiMoTUI.COMMANDS
        assert "/mode" in MiMoTUI.COMMANDS

    def test_has_bindings(self):
        from agent_hub.tui import MiMoTUI
        binding_keys = [b.key for b in MiMoTUI.BINDINGS]
        assert "ctrl+c" in binding_keys
        assert "escape" in binding_keys
        assert "up" in binding_keys
        assert "down" in binding_keys
        assert "tab" in binding_keys

    def test_has_css(self):
        from agent_hub.tui import MiMoTUI
        assert MiMoTUI.CSS is not None
        assert "#output" in MiMoTUI.CSS
        assert "#input-area" in MiMoTUI.CSS
        assert "#streaming" in MiMoTUI.CSS
        assert "#status-bar" in MiMoTUI.CSS

    def test_has_required_methods(self):
        from agent_hub.tui import MiMoTUI
        expected_methods = [
            'compose', 'on_mount', 'on_unmount',
            'write_output', '_show_banner', '_update_status_bar',
            'on_input_submitted', 'on_input_changed',
            '_handle_command', '_run_agent',
            'action_abort', 'action_quit', 'action_force_kill',
            'action_history_up', 'action_history_down',
            'action_tab_complete',
            '_start_streaming_internal', '_end_streaming_internal',
            '_drain_output_queue',
        ]
        for method in expected_methods:
            assert hasattr(MiMoTUI, method), f"Missing method: {method}"
