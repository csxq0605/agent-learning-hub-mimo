"""Tests for context management (Ch7 patterns)."""

import pytest
import json
import tempfile
import os
from unittest.mock import MagicMock, patch
from mimo_harness.context import (
    Session, compact_context, snip_compress, microcompact,
    _filter_orphan_tool_results, make_compact_boundary, load_memory,
    llm_compress, COMPRESS_MARKER, estimate_tokens,
    COMPRESS_TRIGGER_TOKENS, CONTEXT_WINDOW_TOKENS,
    STARTUP_RESERVE_TOKENS, build_system_prompt,
)


class TestSession:
    def test_create_session(self):
        s = Session(session_id="test123")
        assert s.session_id == "test123"
        assert s.messages == []
        assert s.compaction_count == 0

    def test_add_message(self):
        s = Session(session_id="test")
        s.add_message("user", "hello")
        assert len(s.messages) == 1
        assert s.messages[0]["role"] == "user"
        assert s.messages[0]["content"] == "hello"

    def test_add_message_with_kwargs(self):
        s = Session(session_id="test")
        s.add_message("tool", "result", tool_call_id="tc123")
        assert s.messages[0]["tool_call_id"] == "tc123"

    def test_save_and_load(self):
        s = Session(session_id="test", working_dir="/tmp")
        s.add_message("user", "hello")
        s.add_message("assistant", "hi")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            path = f.name

        try:
            s.save(path)
            loaded = Session.load(path)
            assert loaded.session_id == "test"
            assert len(loaded.messages) == 2
            assert loaded.working_dir == "/tmp"
        finally:
            os.unlink(path)


class TestSnipCompress:
    def test_no_compression_needed(self):
        messages = [{"role": "user", "content": "hi"}] * 5
        result = snip_compress(messages, max_age=10)
        assert len(result) == 5

    def test_snips_old_tool_results(self):
        messages = []
        for i in range(30):
            if i % 2 == 0:
                messages.append({"role": "user", "content": f"msg {i}"})
            else:
                messages.append({"role": "tool", "content": f"result {i}"})

        result = snip_compress(messages, max_age=10)
        # Old tool results should be snipped
        old_tools = [m for m in result[:20] if m.get("role") == "tool"]
        for t in old_tools:
            assert t["content"] == COMPRESS_MARKER

        # Recent messages should be preserved
        recent = result[-10:]
        for m in recent:
            if m.get("role") == "tool":
                assert m["content"] != COMPRESS_MARKER

    def test_preserves_non_tool_messages(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        result = snip_compress(messages, max_age=10)
        assert result == messages


class TestMicrocompact:
    def test_keeps_recent_tool_results(self):
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"msg {i}"})
            messages.append({
                "role": "assistant",
                "content": "ok",
                "tool_calls": [{"id": f"tc{i}", "function": {"name": "test", "arguments": "{}"}}]
            })
            messages.append({"role": "tool", "content": f"result {i}", "tool_call_id": f"tc{i}"})

        result = microcompact(messages, keep_recent=3)

        # Should keep last 3 tool results intact
        tool_msgs = [m for m in result if m.get("role") == "tool"]
        non_markers = [m for m in tool_msgs if m["content"] != COMPRESS_MARKER]
        assert len(non_markers) == 3

    def test_no_compression_if_few_results(self):
        messages = [
            {"role": "tool", "content": "r1", "tool_call_id": "tc1"},
            {"role": "tool", "content": "r2", "tool_call_id": "tc2"},
        ]
        result = microcompact(messages, keep_recent=5)
        assert result == messages


class TestOrphanFilter:
    def test_removes_orphan_tool_results(self):
        messages = [
            {"role": "assistant", "content": "ok", "tool_calls": [{"id": "tc1", "function": {"name": "f", "arguments": "{}"}}]},
            {"role": "tool", "content": "result1", "tool_call_id": "tc1"},
            {"role": "tool", "content": "orphan", "tool_call_id": "tc999"},
        ]
        result = _filter_orphan_tool_results(messages)
        assert len(result) == 2
        assert result[1]["tool_call_id"] == "tc1"

    def test_preserves_valid_tool_results(self):
        messages = [
            {"role": "assistant", "content": "ok", "tool_calls": [{"id": "tc1", "function": {"name": "f", "arguments": "{}"}}]},
            {"role": "tool", "content": "result", "tool_call_id": "tc1"},
        ]
        result = _filter_orphan_tool_results(messages)
        assert len(result) == 2


class TestEstimateTokens:
    def test_estimates_basic_messages(self):
        messages = [{"role": "user", "content": "hello world"}]
        tokens = estimate_tokens(messages)
        assert tokens > 0
        assert tokens < 20

    def test_estimates_multiple_messages(self):
        messages = [{"role": "user", "content": "x" * 400}] * 10
        tokens = estimate_tokens(messages)
        assert tokens >= 900


class TestTokenConstants:
    def test_context_window_200k(self):
        assert CONTEXT_WINDOW_TOKENS == 200_000

    def test_compress_trigger_at_85_percent(self):
        expected = int(200_000 * 0.85)
        assert COMPRESS_TRIGGER_TOKENS == expected


class TestCompactContext:
    def test_within_token_limits(self):
        messages = [{"role": "user", "content": "hi"}] * 5
        result = compact_context(messages)
        assert len(result) == 5

    def test_no_compression_when_below_trigger(self):
        messages = [{"role": "user", "content": "x" * 100}] * 100
        tokens = estimate_tokens(messages)
        assert tokens < COMPRESS_TRIGGER_TOKENS
        result = compact_context(messages, estimated_tokens=tokens)
        assert len(result) == 100

    def test_truncation_fallback_produces_few_messages(self):
        """Fallback should produce ~3 messages (marker + last 2), not 132K tokens."""
        big_content = "x" * 4000
        messages = [{"role": "user", "content": big_content}] * 200
        tokens = estimate_tokens(messages)
        assert tokens > COMPRESS_TRIGGER_TOKENS

        result = compact_context(messages, estimated_tokens=tokens)
        # Should be: system marker + last user + last assistant = 3 messages
        assert len(result) <= 4
        assert result[0]["role"] == "system"
        assert "compacted" in result[0]["content"].lower()

    def test_truncation_preserves_last_messages(self):
        """Last user + assistant messages should be preserved."""
        messages = [
            {"role": "user", "content": "old message"},
            {"role": "assistant", "content": "old reply"},
            {"role": "user", "content": "recent question"},
            {"role": "assistant", "content": "recent answer"},
        ]
        # Pad to exceed trigger
        big = [{"role": "user", "content": "x" * 8000}] * 100
        all_msgs = big + messages
        tokens = estimate_tokens(all_msgs)

        result = compact_context(all_msgs, estimated_tokens=tokens)
        # Should have system marker + last 2 messages
        contents = [m.get("content", "") for m in result]
        assert any("recent question" in c for c in contents)
        assert any("recent answer" in c for c in contents)


class TestCompactBoundary:
    def test_creates_boundary(self):
        boundary = make_compact_boundary(
            pre_tokens=50000, pre_messages=100, trigger="auto"
        )
        assert boundary["role"] == "system"
        assert "compacted" in boundary["content"]
        assert boundary["compact_metadata"]["trigger"] == "auto"


class TestLoadMemory:
    def test_loads_existing_files(self, tmp_path):
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Project rules\nBe concise.")

        result = load_memory(str(tmp_path))
        assert "CLAUDE.md" in result
        assert "Be concise" in result

    def test_respects_line_limit(self, tmp_path):
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("\n".join([f"line {i}" for i in range(300)]))

        result = load_memory(str(tmp_path))
        assert "truncated" in result

    def test_no_files(self, tmp_path):
        result = load_memory(str(tmp_path))
        assert result == ""

    def test_loads_agents_md(self, tmp_path):
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Project Instructions\nUse pytest.")

        result = load_memory(str(tmp_path))
        assert "AGENTS.md" in result
        assert "Use pytest" in result


class TestLLMCompress:
    def _make_messages(self, n):
        msgs = []
        for i in range(n):
            msgs.append({"role": "user", "content": f"question {i}"})
            msgs.append({"role": "assistant", "content": f"answer {i}"})
        return msgs

    def _mock_client(self, summary="Summary of conversation"):
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = summary
        client.chat.completions.create.return_value = response
        return client

    def test_returns_single_summary_message(self):
        """After LLM compress, result is ONE summary message."""
        messages = self._make_messages(20)
        client = self._mock_client("Test summary")

        result = llm_compress(messages, client, model="test-model")
        assert result is not None
        assert len(result) == 1  # Only summary, no recent messages
        assert result[0]["role"] == "assistant"
        assert "Conversation Summary" in result[0]["content"]
        assert "Test summary" in result[0]["content"]

    def test_returns_none_on_api_error(self):
        messages = self._make_messages(15)
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("API error")

        result = llm_compress(messages, client)
        assert result is None

    def test_returns_none_on_empty_response(self):
        messages = self._make_messages(15)
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = ""
        client.chat.completions.create.return_value = response

        result = llm_compress(messages, client)
        assert result is None

    def test_single_message_returned_as_is(self):
        messages = [{"role": "user", "content": "hi"}]
        client = self._mock_client()

        result = llm_compress(messages, client)
        assert result == messages

    def test_summary_size_is_small(self):
        """Summary should be much smaller than original conversation."""
        messages = self._make_messages(50)  # 100 messages
        original_tokens = estimate_tokens(messages)
        client = self._mock_client("Short summary of the conversation.")

        result = llm_compress(messages, client)
        summary_tokens = estimate_tokens(result)
        # Summary should be < 10% of original
        assert summary_tokens < original_tokens * 0.10


class TestCompactContextWithLLM:
    def _make_big_messages(self, n, content_size=12000):
        """Create messages large enough to exceed token threshold (~170K)."""
        msgs = []
        for i in range(n):
            msgs.append({"role": "user", "content": f"q{i}" + "x" * content_size})
            msgs.append({"role": "assistant", "content": f"a{i}" + "x" * content_size})
        return msgs

    def test_uses_llm_when_tokens_exceed_threshold(self):
        messages = self._make_big_messages(60)
        tokens = estimate_tokens(messages)
        assert tokens > COMPRESS_TRIGGER_TOKENS

        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "LLM summary"
        client.chat.completions.create.return_value = response

        with patch("mimo_harness.context.llm_compress", return_value=[
            {"role": "assistant", "content": "[Conversation Summary]\nLLM summary"}
        ]) as mock_compress:
            result = compact_context(messages, client=client, model="test", estimated_tokens=tokens)
            mock_compress.assert_called_once()

    def test_falls_back_to_truncation_on_llm_failure(self):
        messages = self._make_big_messages(60)
        tokens = estimate_tokens(messages)
        assert tokens > COMPRESS_TRIGGER_TOKENS
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("fail")

        result = compact_context(messages, client=client, model="test", estimated_tokens=tokens)
        # Fallback: system marker + last 2 messages
        assert len(result) <= 4
        assert result[0]["role"] == "system"

    def test_skips_llm_when_below_token_threshold(self):
        messages = [{"role": "user", "content": "hi"}] * 10
        tokens = estimate_tokens(messages)
        assert tokens < COMPRESS_TRIGGER_TOKENS

        with patch("mimo_harness.context.llm_compress") as mock_compress:
            result = compact_context(messages, client=MagicMock(), estimated_tokens=tokens)
            mock_compress.assert_not_called()

    def test_backward_compatible_no_client(self):
        """Without client, uses truncation fallback (aggressive)."""
        messages = self._make_big_messages(60)
        tokens = estimate_tokens(messages)
        assert tokens > COMPRESS_TRIGGER_TOKENS
        result = compact_context(messages, estimated_tokens=tokens)
        # Fallback: system marker + last 2 messages
        assert len(result) <= 4
        assert result[0]["role"] == "system"


class TestLLMCompressEdgeCases:
    """Edge cases for llm_compress."""

    def test_empty_messages(self):
        client = MagicMock()
        result = llm_compress([], client)
        assert result == []

    def test_single_message(self):
        client = MagicMock()
        msg = [{"role": "user", "content": "hi"}]
        result = llm_compress(msg, client)
        assert result == msg

    def test_messages_with_non_dict(self):
        """Non-dict messages should be skipped gracefully."""
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "summary"
        client.chat.completions.create.return_value = response

        messages = [
            {"role": "user", "content": "hello"},
            "not a dict",  # should be skipped
            {"role": "assistant", "content": "hi"},
        ]
        result = llm_compress(messages, client)
        assert result is not None
        assert len(result) == 1

    def test_messages_with_none_content(self):
        """Messages with None content should be handled."""
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "summary"
        client.chat.completions.create.return_value = response

        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": None},
        ]
        result = llm_compress(messages, client)
        assert result is not None

    def test_long_content_truncated(self):
        """Individual messages with >3000 chars should be truncated."""
        client = MagicMock()
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = "summary"
        client.chat.completions.create.return_value = response

        messages = [
            {"role": "user", "content": "x" * 10000},
            {"role": "assistant", "content": "y" * 10000},
        ]
        # Should not raise, should truncate internally
        result = llm_compress(messages, client)
        assert result is not None


class TestCompactContextEdgeCases:
    """Edge cases for compact_context."""

    def test_empty_messages(self):
        result = compact_context([])
        assert result == []

    def test_single_message_no_compress(self):
        msg = [{"role": "user", "content": "hi"}]
        result = compact_context(msg)
        assert result == msg

    def test_max_messages_legacy_path(self):
        """When max_messages is set and tokens are low, use message count."""
        messages = [{"role": "user", "content": f"msg {i}"} for i in range(100)]
        result = compact_context(messages, max_messages=10)
        assert len(result) == 10
        assert result[0]["content"] == "msg 90"
        assert result[-1]["content"] == "msg 99"

    def test_max_messages_with_orphan_filter(self):
        """Orphan tool results should be filtered in legacy path."""
        messages = [
            {"role": "assistant", "content": "ok", "tool_calls": [{"id": "tc1"}]},
            {"role": "tool", "content": "result", "tool_call_id": "tc1"},
            {"role": "tool", "content": "orphan", "tool_call_id": "tc999"},
        ]
        result = compact_context(messages, max_messages=10)
        assert len(result) == 2  # orphan filtered

    def test_token_compress_with_tool_calls(self):
        """Token-based compression should handle tool_calls messages."""
        messages = []
        for i in range(100):
            messages.append({"role": "user", "content": f"task {i} " + "x" * 8000})
            messages.append({
                "role": "assistant",
                "content": "ok",
                "tool_calls": [{"id": f"tc{i}", "function": {"name": "test", "arguments": "{}"}}]
            })
            messages.append({"role": "tool", "content": f"result {i}", "tool_call_id": f"tc{i}"})

        tokens = estimate_tokens(messages)
        assert tokens > COMPRESS_TRIGGER_TOKENS

        result = compact_context(messages, estimated_tokens=tokens)
        # Fallback: system marker + last 2 messages
        assert len(result) <= 4
        assert result[0]["role"] == "system"


class TestBuildSystemPrompt:
    def test_build_system_prompt_basic(self):
        """Contains MiMo Harness, cwd, platform info."""
        prompt = build_system_prompt(tools_desc="- read_file: read files")
        assert "MiMo Harness" in prompt
        assert os.getcwd() in prompt
        assert "Platform" in prompt or "platform" in prompt.lower()
        assert "read_file" in prompt

    def test_build_system_prompt_with_memory(self):
        """memory_content is appended to prompt."""
        prompt = build_system_prompt(
            tools_desc="- test_tool: testing",
            memory_content="This is project memory content",
        )
        assert "project memory content" in prompt.lower() or "Project Memory" in prompt

    def test_build_system_prompt_with_tools(self):
        """tools_desc is included in prompt."""
        tools_desc = "- read_file: reads files\n- write_file: writes files"
        prompt = build_system_prompt(tools_desc=tools_desc)
        assert "read_file" in prompt
        assert "write_file" in prompt
