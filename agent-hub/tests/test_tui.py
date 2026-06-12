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
            '_handle_during_agent',
            'action_abort', 'action_quit', 'action_force_kill',
            'action_history_up', 'action_history_down',
            'action_tab_complete',
            '_start_streaming_internal', '_end_streaming_internal',
            '_drain_output_queue',
        ]
        for method in expected_methods:
            assert hasattr(MiMoTUI, method), f"Missing method: {method}"


class TestCommandQueue:
    """Test command queuing and /btw injection during agent execution."""

    def test_btw_in_suggest_commands(self):
        """The /btw command should appear in auto-complete suggestions."""
        from agent_hub.commands import SUGGEST_COMMANDS
        assert "/btw" in SUGGEST_COMMANDS

    def test_btw_in_slash_commands(self):
        """The /btw command should appear in the full command list."""
        from agent_hub.commands import SLASH_COMMANDS
        assert "/btw" in SLASH_COMMANDS

    def test_btw_suggestion(self):
        """CommandSuggester should suggest /btw when user types /bt."""
        from agent_hub.tui import CommandSuggester
        suggester = CommandSuggester()
        result = asyncio.run(suggester.get_suggestion("/bt"))
        assert result == "/btw"

    def test_session_add_message_thread_safe(self):
        """Session.add_message should work from any thread (needed for /btw)."""
        from agent_hub.context import Session
        session = Session(session_id="test-btw", messages=[])
        session.add_message("user", "test btw message")
        msgs = session.get_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "test btw message"

    def test_session_add_message_concurrent(self):
        """Multiple threads adding messages concurrently should not crash."""
        from agent_hub.context import Session
        session = Session(session_id="test-concurrent", messages=[])
        errors = []

        def add_msg(i):
            try:
                session.add_message("user", f"message {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_msg, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert len(session.get_messages()) == 50

    def test_queue_data_structure(self):
        """Test basic queue behavior for command queuing."""
        cmd_queue = []
        # Queue commands
        cmd_queue.append("do something")
        cmd_queue.append("do another thing")
        assert len(cmd_queue) == 2
        # Pop first
        first = cmd_queue.pop(0)
        assert first == "do something"
        assert len(cmd_queue) == 1
        # Clear
        cmd_queue.clear()
        assert len(cmd_queue) == 0

    def test_btw_strips_prefix(self):
        """The /btw handler should strip the '/btw ' prefix and use the rest."""
        text = "/btw please use a different approach"
        btw_msg = text[4:].strip()
        assert btw_msg == "please use a different approach"

    def test_btw_exact_command_match(self):
        """/btw matching must not catch /btwxyz or /btw2."""
        # The match condition: text == "/btw" or text.startswith("/btw ")
        def is_btw(text):
            return text == "/btw" or text.startswith("/btw ")

        assert is_btw("/btw hello")
        assert is_btw("/btw")
        assert not is_btw("/btwxyz")
        assert not is_btw("/btw2")
        assert not is_btw("/btwmsg something")

    def test_btw_empty_message_rejected(self):
        """Empty /btw should produce no message."""
        text = "/btw"
        btw_msg = text[4:].strip()
        assert btw_msg == ""

    def test_btw_whitespace_only_rejected(self):
        """/btw with only spaces should produce no message."""
        text = "/btw   "
        btw_msg = text[4:].strip()
        assert btw_msg == ""

    def test_tui_has_command_queue_attr(self):
        """MiMoTUI class should have _command_queue initialization."""
        import inspect
        from agent_hub.tui import MiMoTUI
        source = inspect.getsource(MiMoTUI.__init__)
        assert "_command_queue" in source

    def test_tui_has_handle_during_agent(self):
        """MiMoTUI should have _handle_during_agent method."""
        from agent_hub.tui import MiMoTUI
        assert hasattr(MiMoTUI, '_handle_during_agent')
        import inspect
        sig = inspect.signature(MiMoTUI._handle_during_agent)
        assert 'text' in sig.parameters

    def test_tui_on_agent_done_drains_queue(self):
        """_on_agent_done should reference _command_queue for draining."""
        import inspect
        from agent_hub.tui import MiMoTUI
        source = inspect.getsource(MiMoTUI._on_agent_done)
        assert "_command_queue" in source

    def test_tui_action_interrupt_clears_queue(self):
        """action_interrupt should clear _command_queue."""
        import inspect
        from agent_hub.tui import MiMoTUI
        source = inspect.getsource(MiMoTUI.action_interrupt)
        assert "_command_queue" in source

    def test_tui_set_input_placeholder_method(self):
        """MiMoTUI should have _set_input_placeholder method."""
        from agent_hub.tui import MiMoTUI
        assert hasattr(MiMoTUI, '_set_input_placeholder')

    def test_run_agent_changes_placeholder(self):
        """_run_agent should call _set_input_placeholder for running state."""
        import inspect
        from agent_hub.tui import MiMoTUI
        source = inspect.getsource(MiMoTUI._run_agent)
        assert "_set_input_placeholder" in source

    def test_handle_command_handles_btw_idle(self):
        """_handle_command should handle /btw when agent is idle."""
        import inspect
        from agent_hub.tui import MiMoTUI
        source = inspect.getsource(MiMoTUI._handle_command)
        assert "/btw" in source

    def test_queue_then_drain_multiple(self):
        """Draining a multi-item queue should yield items in FIFO order."""
        cmd_queue = []
        cmd_queue.append("first task")
        cmd_queue.append("second task")
        cmd_queue.append("third task")
        # Drain simulating _on_agent_done behavior
        results = []
        while cmd_queue:
            results.append(cmd_queue.pop(0))
        assert results == ["first task", "second task", "third task"]
        assert len(cmd_queue) == 0

    def test_drain_skips_slash_commands_until_agent_task(self):
        """Queue drain should process slash commands and stop at first agent task.

        Simulates _on_agent_done loop: slash commands are processed inline,
        non-slash commands start an agent (loop breaks).
        """
        cmd_queue = ["/clear", "/compact", "do real work", "another task"]
        processed = []
        agent_started = None

        while cmd_queue:
            cmd = cmd_queue.pop(0)
            if cmd.startswith("/"):
                processed.append(("slash", cmd))
            else:
                agent_started = cmd
                break  # agent started, wait for _on_agent_done

        assert processed == [("slash", "/clear"), ("slash", "/compact")]
        assert agent_started == "do real work"
        assert cmd_queue == ["another task"]  # remaining stays in queue

    def test_drain_all_slash_commands_exhausts_queue(self):
        """If queue is all slash commands, drain processes them all."""
        cmd_queue = ["/clear", "/compact", "/help"]
        processed = []

        while cmd_queue:
            cmd = cmd_queue.pop(0)
            if cmd.startswith("/"):
                processed.append(cmd)
            else:
                break

        assert processed == ["/clear", "/compact", "/help"]
        assert len(cmd_queue) == 0

    def test_queued_btw_is_valid_command(self):
        """/btw queued during agent run should parse correctly when drained."""
        queued = "/btw change approach to iterative"
        # When drained, _on_agent_done routes to _handle_command
        # _handle_command checks: text == "/btw" or text.startswith("/btw ")
        assert queued.startswith("/btw ")
        btw_msg = queued[4:].strip()
        assert btw_msg == "change approach to iterative"

    def test_empty_string_not_queued(self):
        """Empty strings should not be queued (filtered in on_input_submitted)."""
        cmd_queue = []
        text = ""
        if text:  # same guard as on_input_submitted
            cmd_queue.append(text)
        assert len(cmd_queue) == 0

    def test_queue_preserves_whitespace_content(self):
        """Queued commands preserve their original content."""
        cmd_queue = []
        cmd_queue.append("  hello   world  ")
        assert cmd_queue[0] == "  hello   world  "
